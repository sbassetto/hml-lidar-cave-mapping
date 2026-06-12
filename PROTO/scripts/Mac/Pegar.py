import os
import shutil
import math
import open3d as o3d
import numpy as np
import sys
import copy
from pathlib import Path
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore
from rosbags.rosbag2 import Writer
from serveur_alignement import obtenir_matrice_manuelle

# Paramétrage de la résolution spatiale pour l'homogénéisation des nuages
TAILLE_VOXEL = 0.1

def obtenir_duree_totale(chemin_db3):
    # Extraction de l'amplitude temporelle de la session de capture
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    horodatages = []
    with AnyReader([Path(chemin_db3)], default_typestore=typestore) as reader:
        conns = [x for x in reader.connections if x.topic == '/kf_cloud']
        if not conns: return 10
        for connection, timestamp, rawdata in reader.messages(connections=conns):
            horodatages.append(timestamp)
    if not horodatages: return 10
    return (horodatages[-1] - horodatages[0]) / 1_000_000_000

def extraire_nuage_temporel(chemin_db3, mode="complet", duree_secondes=10):
    # Isolement des nuages de points selon les bornes temporelles requises par l'interface WebGL
    duree_ns = duree_secondes * 1_000_000_000
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    points_liste = []
    horodatages = []
    
    with AnyReader([Path(chemin_db3)], default_typestore=typestore) as reader:
        conns = [x for x in reader.connections if x.topic == '/kf_cloud']
        if not conns:
            return None
            
        for connection, timestamp, rawdata in reader.messages(connections=conns):
            msg = reader.deserialize(rawdata, connection.msgtype)
            data = np.frombuffer(msg.data, dtype=np.uint8)
            points_bruts = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)
            points_valides = points_bruts[np.isfinite(points_bruts[:, :3]).all(axis=1)][:, :3]
            points_liste.append(points_valides)
            horodatages.append(timestamp)
            
    if not points_liste:
        return None
        
    t_debut = horodatages[0]
    t_fin = horodatages[-1]
    
    nuage_o3d = o3d.geometry.PointCloud()
    
    if mode == "fin":
        masque = np.array(horodatages) >= (t_fin - duree_ns)
    elif mode == "debut":
        masque = np.array(horodatages) <= (t_debut + duree_ns)
    else:
        masque = np.ones(len(horodatages), dtype=bool)
        
    points_filtres = np.vstack([points_liste[i] for i, m in enumerate(masque) if m])
    nuage_o3d.points = o3d.utility.Vector3dVector(points_filtres)
    
    nuage_echantillonne = nuage_o3d.voxel_down_sample(TAILLE_VOXEL)
    nom_dossier = Path(chemin_db3).name
    print(f"Extraction [{mode.upper()} - {duree_secondes}s] de {nom_dossier} : {len(nuage_echantillonne.points)} points retenus.")
    
    return nuage_echantillonne

def sauvegarder_parametres_6dof(matrice, nom_fichier):
    # Traduction mathématique de la matrice homogène vers un système de coordonnées polaires
    tx = matrice[0, 3]
    ty = matrice[1, 3]
    tz = matrice[2, 3]
    
    ry = math.asin(np.clip(matrice[0, 2], -1.0, 1.0))
    if abs(matrice[0, 2]) < 0.99999:
        rx = math.atan2(-matrice[1, 2], matrice[2, 2])
        rz = math.atan2(-matrice[0, 1], matrice[0, 0])
    else:
        rx = math.atan2(matrice[2, 1], matrice[1, 1])
        rz = 0
        
    with open(nom_fichier, 'w') as f:
        f.write(f"Tx: {tx:.3f}\nTy: {ty:.3f}\nTz: {tz:.3f}\n")
        f.write(f"Rx: {rx:.3f}\nRy: {ry:.3f}\nRz: {rz:.3f}\n")

def exporter_bag_unifie(fichiers_db3, matrices_absolues, chemin_export_db3):
    # Fusion des archives brutes en appliquant les matrices validées sur l'intégralité des flux cartographiques
    print("\n--- GÉNÉRATION DE L'ARCHIVE ROS 2 OPTIMISÉE ---")
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    
    if os.path.exists(chemin_export_db3):
        shutil.rmtree(chemin_export_db3)
        
    with Writer(chemin_export_db3, version=8) as writer:
        connexions_ecriture = {}
        
        for index_fichier, chemin_db3 in enumerate(fichiers_db3):
            matrice_transfo = matrices_absolues[index_fichier]
            nom_dossier = Path(chemin_db3).name
            print(f"Transcription et application géométrique pour le segment : {nom_dossier}")
            
            with AnyReader([Path(chemin_db3)], default_typestore=typestore) as reader:
                # Intégration stricte du canal de trajectoire pour la compatibilité avec lidar_to_vtopo
                conns = [x for x in reader.connections if x.topic in ['/kf_cloud', '/path']]
                
                for connection in conns:
                    if connection.topic not in connexions_ecriture:
                        connexions_ecriture[connection.topic] = writer.add_connection(connection.topic, connection.msgtype, typestore=typestore)
                        
                for connection, timestamp, rawdata in reader.messages(connections=conns):
                    msg = reader.deserialize(rawdata, connection.msgtype)
                    
                    if connection.topic == '/kf_cloud':
                        if isinstance(msg.data, np.ndarray):
                            data_array = msg.data.copy()
                        else:
                            data_array = np.frombuffer(msg.data, dtype=np.uint8).copy()
                            
                        points_bruts = data_array.view(dtype=np.float32).reshape(-1, msg.point_step // 4)
                        pts = points_bruts[:, :3]
                        masque_valide = np.isfinite(pts).all(axis=1)
                        pts_valides = pts[masque_valide]
                        
                        if len(pts_valides) > 0:
                            pts_h = np.hstack((pts_valides, np.ones((len(pts_valides), 1))))
                            pts_transformes = (matrice_transfo @ pts_h.T).T[:, :3]
                            points_bruts[masque_valide, :3] = pts_transformes
                            msg.data = data_array
                            rawdata_new = typestore.serialize_cdr(msg, connection.msgtype)
                            writer.write(connexions_ecriture[connection.topic], timestamp, rawdata_new)
                            
                    elif connection.topic == '/path':
                        # Application de la matrice de translation absolue aux coordonnées odométriques du graphe
                        if hasattr(msg, 'poses'):
                            for pose_stamped in msg.poses:
                                p = pose_stamped.pose.position
                                pt_h = np.array([p.x, p.y, p.z, 1.0])
                                pt_transf = matrice_transfo @ pt_h
                                pose_stamped.pose.position.x = pt_transf[0]
                                pose_stamped.pose.position.y = pt_transf[1]
                                pose_stamped.pose.position.z = pt_transf[2]
                                
                        rawdata_new = typestore.serialize_cdr(msg, connection.msgtype)
                        writer.write(connexions_ecriture[connection.topic], timestamp, rawdata_new)

def assembler_nuages_sequentiellement(fichiers_db3):
    # Boucle d'optimisation et d'instanciation du serveur WebGL
    odometrie_absolue = np.identity(4)
    nuage_unifie = o3d.geometry.PointCloud()
    matrices_absolues = []
    
    durees_max = []
    for i in range(len(fichiers_db3)):
        durees_max.append(obtenir_duree_totale(fichiers_db3[i]))
        nom_segment_actuel = fichiers_db3[i].name
        print(f"\n--- CHARGEMENT DU SEGMENT TOPOGRAPHIQUE : {nom_segment_actuel} ---")
        
        nuage_entier = extraire_nuage_temporel(fichiers_db3[i], mode="complet")
        
        if nuage_entier is None:
            print(f"Erreur critique : Le fichier {nom_segment_actuel} ne contient pas le topic '/kf_cloud'.")
            sys.exit(1)
            
        if i > 0:
            nom_segment_precedent = fichiers_db3[i-1].name
            duree_max_actuel = durees_max[i]
            duree_max_precedent = durees_max[i-1]
            
            ancrage_precedent = extraire_nuage_temporel(fichiers_db3[i-1], mode="fin", duree_secondes=10)
            ancrage_actuel = extraire_nuage_temporel(fichiers_db3[i], mode="debut", duree_secondes=10)
            
            if ancrage_precedent is None or ancrage_actuel is None:
                print("Erreur critique : Échec de l'extraction des fenêtres temporelles.")
                sys.exit(1)
            
            def recharger_nuages(duree_source, duree_cible):
                nouveau_actuel = extraire_nuage_temporel(fichiers_db3[i], mode="debut", duree_secondes=duree_source)
                nouveau_precedent = extraire_nuage_temporel(fichiers_db3[i-1], mode="fin", duree_secondes=duree_cible)
                return nouveau_actuel, nouveau_precedent
            
            print(f"\nDéploiement de l'interface d'alignement manuel pour la jonction : {nom_segment_precedent} -> {nom_segment_actuel}")
            print("Ouvrez votre navigateur web à l'adresse : http://127.0.0.1:5000")
            
            matrice_relative = obtenir_matrice_manuelle(ancrage_actuel, ancrage_precedent, duree_max_actuel, duree_max_precedent, recharger_nuages)
            
            if matrice_relative is None:
                print("Erreur critique : Échec de la communication avec le processus navigateur.")
                sys.exit(1)

            nom_sauvegarde_matrice = f"matrice_{nom_segment_precedent}_vers_{nom_segment_actuel}.txt"
            np.savetxt(nom_sauvegarde_matrice, matrice_relative)
            
            nom_sauvegarde_params = f"parametres_{nom_segment_precedent}_vers_{nom_segment_actuel}.txt"
            sauvegarder_parametres_6dof(matrice_relative, nom_sauvegarde_params)
            print(f"Sauvegardes de sécurité effectuées : {nom_sauvegarde_matrice} et {nom_sauvegarde_params}")
            
            odometrie_absolue = np.dot(odometrie_absolue, matrice_relative)
            
        matrices_absolues.append(copy.deepcopy(odometrie_absolue))
        
        print(f"Intégration rigide du segment {nom_segment_actuel} dans le modèle global...")
        nuage_transforme = copy.deepcopy(nuage_entier)
        nuage_transforme.transform(odometrie_absolue)
        nuage_unifie += nuage_transforme
        
    print("\nVoxelisation finale pour homogénéisation de la densité du modèle unifié...")
    return nuage_unifie.voxel_down_sample(TAILLE_VOXEL), matrices_absolues

def main():
    dossier_script = Path(__file__).parent.resolve()
    fichiers_db3_bruts = list(dossier_script.rglob("*.db3"))
    dossiers_db3 = sorted(list(set([fichier.parent for fichier in fichiers_db3_bruts])))
    
    if len(dossiers_db3) < 2:
        print("Erreur critique : La topologie requiert au minimum deux segments odométriques consécutifs.")
        sys.exit(1)
        
    nuage_final, matrices_absolues = assembler_nuages_sequentiellement(dossiers_db3)
    
    utilisateur_local = os.environ.get('USER', 'default_user')
    chemin_export_pcd = str(Path(f"/Users/{utilisateur_local}/Desktop/Expedition_Data/results/reseau_optimise.pcd"))
    chemin_export_db3 = str(Path(f"/Users/{utilisateur_local}/Desktop/Expedition_Data/results/reseau_optimise_bag"))
    
    Path(chemin_export_pcd).parent.mkdir(parents=True, exist_ok=True)
    
    o3d.io.write_point_cloud(chemin_export_pcd, nuage_final)
    print(f"\nModèle 3D Open3D exporté : {chemin_export_pcd}")
    
    exporter_bag_unifie(dossiers_db3, matrices_absolues, chemin_export_db3)
    print(f"Archive ROS 2 séquentielle exportée : {chemin_export_db3}")

if __name__ == "__main__":
    main()