# Fichier : EditeurReseau.py
import os
import re
import copy
import shutil
import numpy as np
import open3d as o3d
import hashlib
from pathlib import Path
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore
from rosbags.rosbag2 import Writer
from scipy.spatial.transform import Rotation as R
from serveur_edition import lancer_edition_multicouche

# Résolution de la grille de voxels pour alléger le modèle PCD final unifié
TAILLE_VOXEL_ASSEMBLAGE = 0.05

def determiner_prochaine_version(dossier_parent, nom_base):
    # Analyse par expression régulière pour incrémenter automatiquement le suffixe de version du dossier
    motif = re.compile(rf"^{re.escape(nom_base)}(?:_V(\d+))?$")
    version_max = 0
    
    for dossier in dossier_parent.iterdir():
        if dossier.is_dir():
            correspondance = motif.match(dossier.name)
            if correspondance:
                version = int(correspondance.group(1)) if correspondance.group(1) else 0
                version_max = max(version_max, version)
                
    nouvelle_version = version_max + 1
    return f"{nom_base}_V{nouvelle_version}"

def reconstruire_chaine_cinematique(dossier_reseau, dossier_fragments):
    # Rétro-ingénierie de l'ordre d'assemblage séquentiel par résolution cryptographique des empreintes MD5
    fichiers_matrices = list(dossier_reseau.glob("matrice_*.txt"))
    if not fichiers_matrices:
        raise ValueError("Aucun fichier de matrice de transformation détecté dans le répertoire cible.")

    empreintes_cibles = {}
    for chemin in fichiers_matrices:
        # Extraction stricte de la chaîne hexadécimale du fichier
        hash_nom = chemin.stem.replace("matrice_", "")
        empreintes_cibles[hash_nom] = chemin

    # Extraction des objets Path pour cibler les dossiers contenant les données ROS 2
    segments_disponibles = [d for d in dossier_fragments.iterdir() if d.is_dir()]
    noms_segments = [d.name for d in segments_disponibles]
    
    liens = {}
    segments_cibles = set()
    segments_sources = set()
    chemins_matrices_ordonnes = {}

    # Extraction de tous les fragments du chemin absolu pour alimenter le dictionnaire de force brute
    composants_chemin = list(dossier_fragments.parts) + list(dossier_reseau.parts)
    mots_courants = ["results", "connected", "fragments", "lt_fragments", "bag", "ros2_ws", "Expedition_Data"]
    candidats_parents = list(set(composants_chemin + mots_courants))
    candidats_parents = [p for p in candidats_parents if p.strip() and p != '/']

    # Attaque par force brute pour retrouver la nomenclature exacte générée par l'algorithme d'assemblage
    for source_name in noms_segments:
        for cible_name in noms_segments:
            if source_name == cible_name:
                continue
            
            match_trouve = False
            for parent_source in candidats_parents:
                for parent_cible in candidats_parents:
                    nom_source_pegar = f"{parent_source}_{source_name}"
                    nom_cible_pegar = f"{parent_cible}_{cible_name}"
                    
                    identifiant_liaison = f"{nom_source_pegar}_vers_{nom_cible_pegar}"
                    hash_liaison = hashlib.md5(identifiant_liaison.encode('utf-8')).hexdigest()
                    
                    if hash_liaison in empreintes_cibles:
                        liens[source_name] = cible_name
                        segments_sources.add(source_name)
                        segments_cibles.add(cible_name)
                        chemins_matrices_ordonnes[source_name] = empreintes_cibles[hash_liaison]
                        match_trouve = True
                        break
                if match_trouve:
                    break

    if not liens:
        raise ValueError("Impossible de faire correspondre les empreintes cryptographiques avec les fragments du répertoire.")

    racines = list(segments_sources - segments_cibles)
    if len(racines) != 1:
        raise ValueError("L'arborescence matricielle est fragmentée ou contient des boucles circulaires.")

    sequence = [racines[0]]
    courant = racines[0]
    matrices_relatives = []
    
    # Restitution de la séquence chronologique par parcours de graphe
    while courant in liens:
        suivant = liens[courant]
        sequence.append(suivant)
        chemin_matrice = chemins_matrices_ordonnes[courant]
        matrices_relatives.append(np.loadtxt(chemin_matrice))
        courant = suivant

    return sequence, matrices_relatives

def recalculer_poses_absolues(matrices_relatives):
    # Calcul de la chaîne cinématique par multiplication matricielle successive à partir de l'origine
    poses_absolues = [np.identity(4)]
    pose_courante = np.identity(4)
    
    for matrice_rel in matrices_relatives:
        pose_courante = np.dot(pose_courante, matrice_rel)
        poses_absolues.append(copy.deepcopy(pose_courante))
        
    return poses_absolues

def extraire_nuage_complet(chemin_dossier_bag):
    # Extraction géométrique lourde sur l'intégralité d'un segment odométrique
    chemin_db3 = list(Path(chemin_dossier_bag).glob("*.db3"))[0]
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    points_liste = []
    
    with AnyReader([chemin_db3], default_typestore=typestore) as reader:
        conns = [x for x in reader.connections if x.topic == '/kf_cloud']
        if not conns: return None
        for connection, timestamp, rawdata in reader.messages(connections=conns):
            msg = reader.deserialize(rawdata, connection.msgtype)
            data = np.frombuffer(msg.data, dtype=np.uint8)
            points_bruts = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)
            points_valides = points_bruts[np.isfinite(points_bruts[:, :3]).all(axis=1)][:, :3]
            points_liste.append(points_valides)
            
    if not points_liste: return None
    
    nuage = o3d.geometry.PointCloud()
    nuage.points = o3d.utility.Vector3dVector(np.vstack(points_liste))
    return nuage.voxel_down_sample(TAILLE_VOXEL_ASSEMBLAGE)

def exporter_bag_unifie(sequence, matrices_absolues, dossier_fragments, chemin_export_db3):
    # Compilation d'une archive ROS 2 globale en réécrivant les nuages et les trajectoires avec les nouvelles poses
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    
    if os.path.exists(chemin_export_db3):
        shutil.rmtree(chemin_export_db3)
        
    with Writer(chemin_export_db3, version=8) as writer:
        connexions_ecriture = {}
        
        for index_fichier, nom_segment in enumerate(sequence):
            matrice_transfo = matrices_absolues[index_fichier]
            matrice_rotation = matrice_transfo[:3, :3]
            rotation_absolue = R.from_matrix(matrice_rotation)
            
            print(f"Transcription odométrique pour le segment : {nom_segment}")
            chemin_db3 = list((Path(dossier_fragments) / nom_segment).glob("*.db3"))[0]
            
            with AnyReader([chemin_db3], default_typestore=typestore) as reader:
                conns = [x for x in reader.connections if x.topic in ['/kf_cloud', '/path']]
                
                for connection in conns:
                    if connection.topic not in connexions_ecriture:
                        connexions_ecriture[connection.topic] = writer.add_connection(connection.topic, connection.msgtype, typestore=typestore)
                        
                for connection, timestamp, rawdata in reader.messages(connections=conns):
                    msg = reader.deserialize(rawdata, connection.msgtype)
                    
                    if connection.topic == '/kf_cloud':
                        data_array = msg.data.copy() if isinstance(msg.data, np.ndarray) else np.frombuffer(msg.data, dtype=np.uint8).copy()
                        points_bruts = data_array.view(dtype=np.float32).reshape(-1, msg.point_step // 4)
                        pts = points_bruts[:, :3]
                        masque_valide = np.isfinite(pts).all(axis=1)
                        pts_valides = pts[masque_valide]
                        
                        if len(pts_valides) > 0:
                            pts_h = np.hstack((pts_valides, np.ones((len(pts_valides), 1))))
                            pts_transformes = (matrice_transfo @ pts_h.T).T[:, :3]
                            points_bruts[masque_valide, :3] = pts_transformes
                            msg.data = data_array
                            writer.write(connexions_ecriture[connection.topic], timestamp, typestore.serialize_cdr(msg, connection.msgtype))
                            
                    elif connection.topic == '/path':
                        if hasattr(msg, 'poses'):
                            for pose_stamped in msg.poses:
                                p = pose_stamped.pose.position
                                pt_h = np.array([p.x, p.y, p.z, 1.0])
                                pt_transf = matrice_transfo @ pt_h
                                pose_stamped.pose.position.x = pt_transf[0]
                                pose_stamped.pose.position.y = pt_transf[1]
                                pose_stamped.pose.position.z = pt_transf[2]
                                
                                q = pose_stamped.pose.orientation
                                rotation_pose = R.from_quat([q.x, q.y, q.z, q.w])
                                rotation_finale = rotation_absolue * rotation_pose
                                q_nouveau = rotation_finale.as_quat()
                                
                                pose_stamped.pose.orientation.x = q_nouveau[0]
                                pose_stamped.pose.orientation.y = q_nouveau[1]
                                pose_stamped.pose.orientation.z = q_nouveau[2]
                                pose_stamped.pose.orientation.w = q_nouveau[3]
                                
                        writer.write(connexions_ecriture[connection.topic], timestamp, typestore.serialize_cdr(msg, connection.msgtype))

def exporter_nouvelle_version(dossier_reseau_original, sequence, matrices_relatives, nouvelles_poses_absolues, dossier_fragments):
    # Compilation de l'arborescence, assemblage global du nuage Open3D et de la base SQLite
    nom_base = re.sub(r'_V\d+$', '', dossier_reseau_original.name)
    nom_nouveau_dossier = determiner_prochaine_version(dossier_reseau_original.parent, nom_base)
    dossier_export = dossier_reseau_original.parent / nom_nouveau_dossier
    dossier_export.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGénération de l'arborescence : {nom_nouveau_dossier}")
    
    # Validation cryptographique du réseau : application de la nomenclature dynamique pour les nouveaux exports
    for i in range(len(sequence) - 1):
        source_dir = dossier_fragments / sequence[i]
        cible_dir = dossier_fragments / sequence[i+1]
        nom_source_pegar = f"{source_dir.parent.name}_{source_dir.name}"
        nom_cible_pegar = f"{cible_dir.parent.name}_{cible_dir.name}"
        
        identifiant_liaison = f"{nom_source_pegar}_vers_{nom_cible_pegar}"
        hash_liaison = hashlib.md5(identifiant_liaison.encode('utf-8')).hexdigest()
        nom_fichier_matrice = f"matrice_{hash_liaison}.txt"
        np.savetxt(dossier_export / nom_fichier_matrice, matrices_relatives[i])
        
    print("\nRecompilation du nuage de points global (PCD)...")
    nuage_unifie = o3d.geometry.PointCloud()
    
    for i, nom_segment in enumerate(sequence):
        nuage_segment = extraire_nuage_complet(dossier_fragments / nom_segment)
        if nuage_segment:
            nuage_segment.transform(nouvelles_poses_absolues[i])
            nuage_unifie += nuage_segment
            
    chemin_pcd = dossier_export / f"{nom_nouveau_dossier}.pcd"
    o3d.io.write_point_cloud(str(chemin_pcd), nuage_unifie.voxel_down_sample(TAILLE_VOXEL_ASSEMBLAGE))
    print(f"Modèle 3D Open3D exporté : {chemin_pcd}")
    
    print("\nRecompilation de l'archive ROS 2 unifiée...")
    chemin_export_db3 = dossier_export / f"{nom_nouveau_dossier}_bag"
    exporter_bag_unifie(sequence, nouvelles_poses_absolues, dossier_fragments, str(chemin_export_db3))
    
    print("\nProcessus d'édition et de compilation achevé avec succès.")

def editer_jonction_reseau(sequence, matrices_relatives, dossier_fragments):
    print("\n--- ÉDITEUR MANUEL DE GRAPHES ODOMÉTRIQUES ---")
    print("Révision manuelle des jonctions Pegar dans l'environnement WebGL...")
    
    matrices_corrigees = lancer_edition_multicouche(sequence, matrices_relatives, dossier_fragments)
    
    if not matrices_corrigees:
        return None
        
    print("\nPropagation mathématique de la nouvelle chaîne cinématique aval...")
    nouvelles_poses_absolues = recalculer_poses_absolues(matrices_corrigees)
    
    return matrices_corrigees, nouvelles_poses_absolues

def main():
    nom_reseau = input("Indiquez le nom exact du dossier contenant le réseau à éditer (ex: reseau_optimise) : ").strip()
    chemin_fragments = input("Indiquez le chemin absolu du dossier contenant les fragments : ").strip()
    
    # RevA : chemin configurable sans modifier le code.
    # Le comportement fonctionnel de l'éditeur reste inchangé :
    # il révise manuellement les jonctions produites par Pegar.
    dossier_racine = Path(
        os.environ.get(
            "HML_RESULTS_DIR",
            str(Path.home() / "Desktop" / "Expedition_Data" / "results")
        )
    ).expanduser()
    dossier_reseau = dossier_racine / nom_reseau
    dossier_fragments = Path(chemin_fragments)
    
    if not dossier_reseau.exists():
        print("Erreur critique : Le répertoire du réseau cible est introuvable.")
        return
        
    if not dossier_fragments.exists():
        print("Erreur critique : Le répertoire des fragments est introuvable.")
        return
        
    try:
        sequence, matrices_relatives = reconstruire_chaine_cinematique(dossier_reseau, dossier_fragments)
    except Exception as e:
        print(f"Échec de l'analyse du graphe de pose : {e}")
        return
        
    resultat_edition = editer_jonction_reseau(sequence, matrices_relatives, dossier_fragments)
    
    if resultat_edition:
        nouvelles_matrices, nouvelles_poses = resultat_edition
        exporter_nouvelle_version(dossier_reseau, sequence, nouvelles_matrices, nouvelles_poses, dossier_fragments)

if __name__ == "__main__":
    main()