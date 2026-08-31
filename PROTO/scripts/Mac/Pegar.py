# (c) Pr. Samuel Bassetto ; samuel-jean.bassetto@polymtl.ca
# Fichier : Pegar.py
import os
import shutil
import math
import open3d as o3d
import numpy as np
import sys
import copy
import threading
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore
from rosbags.rosbag2 import Writer
from scipy.spatial.transform import Rotation as R
from serveur_alignement import obtenir_matrice_manuelle
import traceback

# Paramétrage de la résolution spatiale dissociée pour affichage et assemblage
TAILLE_VOXEL_ASSEMBLAGE = 0.02
TAILLE_VOXEL_AFFICHAGE = 0.01

def obtenir_duree_totale(chemin_bag):
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    fichiers_db3 = sorted([
        f for f in Path(chemin_bag).glob("*.db3")
        if not f.name.startswith("._")
    ])
    if not fichiers_db3: 
        return 10
        
    horodatages = []
    with AnyReader(fichiers_db3, default_typestore=typestore) as reader:
        conns = [x for x in reader.connections if x.topic == '/kf_cloud']
        if not conns: return 10
        for connection, timestamp, rawdata in reader.messages(connections=conns):
            horodatages.append(timestamp)
            
    if not horodatages: return 10
    return (horodatages[-1] - horodatages[0]) / 1_000_000_000

def extraire_nuage_temporel(chemin_bag, mode="complet", duree_secondes=10, taille_voxel=TAILLE_VOXEL_AFFICHAGE):
    duree_ns = duree_secondes * 1_000_000_000
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    points_liste = []
    horodatages = []
    
    fichiers_db3 = sorted([
        f for f in Path(chemin_bag).glob("*.db3")
        if not f.name.startswith("._")
    ])
    if not fichiers_db3:
        return None
    
    with AnyReader(fichiers_db3, default_typestore=typestore) as reader:
        conns = [x for x in reader.connections if x.topic == '/kf_cloud']
        if not conns:
            return None
            
        for connection, timestamp, rawdata in reader.messages(connections=conns):
            msg = reader.deserialize(rawdata, connection.msgtype)
            data = np.frombuffer(msg.data, dtype=np.uint8)
            points_bruts = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)
            points_valides = points_bruts[np.isfinite(points_bruts[:, :3]).all(axis=1)][:, :3]
            
            if len(points_valides) > 0:
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
    
    nuage_echantillonne = nuage_o3d.voxel_down_sample(taille_voxel)
    nom_dossier = f"{Path(chemin_bag).parent.name}_{Path(chemin_bag).name}"
    print(f"Extraction [{mode.upper()} - {duree_secondes}s] de {nom_dossier} : {len(nuage_echantillonne.points)} points retenus.")
    
    return nuage_echantillonne

# Extraction par lots avec indicateur de progression dynamique
def extraire_pcd_massif(chemin_bag, taille_voxel, callback_progression=None):
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    fichiers_db3 = sorted([
        f for f in Path(chemin_bag).glob("*.db3")
        if not f.name.startswith("._")
    ])
    if not fichiers_db3: 
        return None
    
    nuage_global = o3d.geometry.PointCloud()
    points_tampon = []
    limite_tampon = 2_000_000
    
    with AnyReader(fichiers_db3, default_typestore=typestore) as reader:
        conns = [x for x in reader.connections if x.topic == '/kf_cloud']
        if not conns: 
            return None
            
        total_msgs = sum(c.msgcount for c in conns)
        msgs_lus = 0
        
        for connection, timestamp, rawdata in reader.messages(connections=conns):
            msg = reader.deserialize(rawdata, connection.msgtype)
            data = np.frombuffer(msg.data, dtype=np.uint8)
            points_bruts = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)
            points_valides = points_bruts[np.isfinite(points_bruts[:, :3]).all(axis=1)][:, :3]
            
            if len(points_valides) > 0:
                points_tampon.append(points_valides)
                
                if sum(len(p) for p in points_tampon) > limite_tampon:
                    pts_vstack = np.vstack(points_tampon)
                    temp_cloud = o3d.geometry.PointCloud()
                    temp_cloud.points = o3d.utility.Vector3dVector(pts_vstack)
                    temp_cloud = temp_cloud.voxel_down_sample(taille_voxel)
                    
                    nuage_global += temp_cloud
                    nuage_global = nuage_global.voxel_down_sample(taille_voxel)
                    points_tampon = []
                    
            msgs_lus += 1
            if callback_progression and msgs_lus % 20 == 0:
                pourcentage = int((msgs_lus / total_msgs) * 100)
                callback_progression(pourcentage)
                    
    if points_tampon:
        pts_vstack = np.vstack(points_tampon)
        temp_cloud = o3d.geometry.PointCloud()
        temp_cloud.points = o3d.utility.Vector3dVector(pts_vstack)
        temp_cloud = temp_cloud.voxel_down_sample(taille_voxel)
        nuage_global += temp_cloud
        nuage_global = nuage_global.voxel_down_sample(taille_voxel)
        
    if callback_progression:
        callback_progression(100)
        
    print(f"Extraction massive terminée : {len(nuage_global.points)} points retenus à {taille_voxel}m de résolution.")
    return nuage_global

def sauvegarder_parametres_6dof(matrice, chemin_fichier):
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
        
    with open(chemin_fichier, 'w') as f:
        f.write(f"Tx: {tx:.3f}\nTy: {ty:.3f}\nTz: {tz:.3f}\n")
        f.write(f"Rx: {rx:.3f}\nRy: {ry:.3f}\nRz: {rz:.3f}\n")

def exporter_bag_unifie(fichiers_db3_dossiers, matrices_absolues, chemin_export_db3):
    print("\n--- GÉNÉRATION DE L'ARCHIVE ROS 2 OPTIMISÉE ---")
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    
    if os.path.exists(chemin_export_db3):
        shutil.rmtree(chemin_export_db3)
        
    with Writer(chemin_export_db3, version=8) as writer:
        connexions_ecriture = {}
        
        for index_fichier, chemin_bag in enumerate(fichiers_db3_dossiers):
            matrice_transfo = matrices_absolues[index_fichier]
            matrice_rotation = matrice_transfo[:3, :3]
            rotation_absolue = R.from_matrix(matrice_rotation)
            
            nom_dossier = Path(chemin_bag).name
            print(f"Transcription et application géométrique pour le segment : {nom_dossier}")
            
            fichiers_internes = sorted([
                f for f in Path(chemin_bag).glob("*.db3")
                if not f.name.startswith("._")
            ])
            
            with AnyReader(fichiers_internes, default_typestore=typestore) as reader:
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
                                
                        rawdata_new = typestore.serialize_cdr(msg, connection.msgtype)
                        writer.write(connexions_ecriture[connection.topic], timestamp, rawdata_new)

def assembler_nuages_sequentiellement(fichiers_db3, dossier_destination, callback_mise_a_jour_ui=None, limite_affichage=240):
    odometrie_absolue = np.identity(4)
    nuage_unifie = o3d.geometry.PointCloud()
    matrices_absolues = []
    fichiers_traites = []
    durees_max = []
    
    dossier_checkpoints = dossier_destination / ".checkpoints_pegar"
    dossier_checkpoints.mkdir(parents=True, exist_ok=True)
    
    for i in range(len(fichiers_db3)):
        try:
            if not (fichiers_db3[i] / "metadata.yaml").is_file():
                return None, None, None, f"Le fichier metadata.yaml de l'archive {fichiers_db3[i].name} a disparu."
                
            durees_max.append(obtenir_duree_totale(fichiers_db3[i]))
            nom_segment_actuel = f"{fichiers_db3[i].parent.name}_{fichiers_db3[i].name}"
            
            # Recalcul matriciel systématique exigé sans importation d'états sauvegardés
            print(f"\n--- RECALCUL STRICT DU SEGMENT TOPOGRAPHIQUE : {nom_segment_actuel} ---")
            
            nuage_entier = extraire_nuage_temporel(fichiers_db3[i], mode="complet", taille_voxel=TAILLE_VOXEL_ASSEMBLAGE)
            
            if nuage_entier is None:
                return None, None, None, f"Le fichier {nom_segment_actuel} ne contient aucune donnée de nuage de points valide."
                
            if i > 0:
                nom_segment_precedent = f"{fichiers_db3[i-1].parent.name}_{fichiers_db3[i-1].name}"
                duree_max_actuel = durees_max[i]
                duree_max_precedent = durees_max[i-1]
                
                identifiant_liaison = f"{nom_segment_precedent}_vers_{nom_segment_actuel}"
                hash_liaison = hashlib.md5(identifiant_liaison.encode('utf-8')).hexdigest()
                chemin_sauvegarde_matrice = dossier_destination / f"matrice_{hash_liaison}.txt"
                chemin_sauvegarde_params = dossier_destination / f"parametres_{hash_liaison}.txt"
                
                ancrage_precedent = extraire_nuage_temporel(fichiers_db3[i-1], mode="fin", duree_secondes=10)
                ancrage_actuel = extraire_nuage_temporel(fichiers_db3[i], mode="debut", duree_secondes=10)
                
                if ancrage_precedent is None or ancrage_actuel is None:
                    return None, None, None, "Impossible d'extraire les nuages d'ancrage. La fenêtre temporelle est vide ou corrompue."

                def recharger_nuages(duree_source, duree_cible, taille_voxel_dynamique=0.02):
                     nouveau_actuel = extraire_nuage_temporel(fichiers_db3[i], mode="debut", duree_secondes=duree_source, taille_voxel=taille_voxel_dynamique)
                     nouveau_precedent = extraire_nuage_temporel(fichiers_db3[i-1], mode="fin", duree_secondes=duree_cible, taille_voxel=taille_voxel_dynamique)
                     return nouveau_actuel, nouveau_precedent
                
                print(f"\nDéploiement de l'interface d'alignement manuel pour : {nom_segment_precedent} -> {nom_segment_actuel}")
                
                matrice_relative = obtenir_matrice_manuelle(
                    ancrage_actuel,
                    ancrage_precedent,
                    duree_max_actuel,
                    duree_max_precedent,
                    recharger_nuages,
                    limite_affichage
                )

                # RevA: "Exclure et Finaliser" returns the sentinel "IGNORER".
                # Finalize the already validated network instead of trying to
                # write/multiply that string as if it were a 4x4 matrix.
                if isinstance(matrice_relative, str) and matrice_relative == "IGNORER":
                    print(
                        f"Segment {nom_segment_actuel} exclu par l'opérateur. "
                        "Finalisation du réseau avec les segments déjà validés."
                    )
                    break

                if matrice_relative is None:
                    return None, None, None, (
                        "Le serveur WebGL a échoué ou a été interrompu "
                        "sans retourner de matrice."
                    )

                matrice_relative = np.asarray(matrice_relative, dtype=float)
                if matrice_relative.shape != (4, 4) or not np.isfinite(matrice_relative).all():
                    return None, None, None, (
                        f"La transformation retournée pour {nom_segment_actuel} "
                        "n'est pas une matrice homogène 4x4 valide."
                    )

                np.savetxt(chemin_sauvegarde_matrice, matrice_relative)
                sauvegarder_parametres_6dof(
                    matrice_relative,
                    chemin_sauvegarde_params
                )

                odometrie_absolue = np.dot(
                    odometrie_absolue,
                    matrice_relative
                )

            hash_segment = hashlib.md5(nom_segment_actuel.encode('utf-8')).hexdigest()
            fichier_matrice_abs = dossier_checkpoints / f"matrice_abs_{i}_{hash_segment}.txt"
            fichier_nuage_trans = dossier_checkpoints / f"nuage_trans_{i}_{hash_segment}.pcd"
            
            np.savetxt(fichier_matrice_abs, odometrie_absolue)
            nuage_transforme = copy.deepcopy(nuage_entier)
            nuage_transforme.transform(odometrie_absolue)
            o3d.io.write_point_cloud(str(fichier_nuage_trans), nuage_transforme)
            
            matrices_absolues.append(copy.deepcopy(odometrie_absolue))
            fichiers_traites.append(fichiers_db3[i])
            
            print(f"Intégration rigide du segment {nom_segment_actuel} dans le modèle global...")
            nuage_unifie += nuage_transforme

            if callback_mise_a_jour_ui:
                callback_mise_a_jour_ui()
                    
        except Exception as e:
            traceback.print_exc()
            return None, None, None, f"Exception Python sur le segment {fichiers_db3[i].name} :\n{str(e)}"
        
    if not fichiers_traites:
        return None, None, None, "Aucun fichier n'a été traité."
        
    print("\nVoxelisation finale pour homogénéisation du modèle...")
    return nuage_unifie.voxel_down_sample(TAILLE_VOXEL_ASSEMBLAGE), matrices_absolues, fichiers_traites, None

class InterfacePegar(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PEGAR - Sélection Visuelle et Assemblage des Archives ROS 2")
        self.geometry("950x950")
        self.configure(bg="#2d2d2d")
        
        # RevA: processing directory configurable without editing the source.
        # This matches docker-compose and 2_traiter_bag.command.
        chemin_defaut = os.environ.get(
            "HML_RESULTS_DIR",
            str(Path.home() / "Desktop" / "Expedition_Data" / "results")
        )
        self.dossier_source = tk.StringVar(value=chemin_defaut)
        self.dossier_destination = tk.StringVar(value=chemin_defaut)
        self.nom_archive_sortie = tk.StringVar(value="reseau_connecte")
        self.limite_affichage = tk.IntVar(value=3600)
        
        # Variables d'exportation isolée PCD
        self.voxel_export = tk.DoubleVar(value=0.005) 
        self.bag_export_source = tk.StringVar(value="")
        self.dossier_export_pcd = tk.StringVar(value=chemin_defaut)
        self.nom_export_pcd = tk.StringVar(value="export_haute_densite")
        self.statut_export = tk.StringVar(value="En attente de sélection")
        
        self.chemins_disponibles = []
        self.chemins_selectionnes = []
        
        self.en_cours_assemblage = False
        self.protocol("WM_DELETE_WINDOW", self.fermer_application_securisee)
        
        self.image_logo_tk = None
        
        self.construire_interface()
        self.charger_archives_disponibles()

    def fermer_application_securisee(self):
        if self.en_cours_assemblage:
            messagebox.showwarning(
                "Fermeture verrouillée", 
                "Le processeur est en cours d'exécution.\n\nLa fermeture logicielle est bloquée pour interdire la corruption de la base de données ROS 2."
            )
            return
            
        self.quit()
        self.destroy()
        sys.exit(0)

    def construire_interface(self):
        couleur_fond = "#2d2d2d"
        couleur_texte = "#ffffff"
        couleur_liste = "#1e1e1e"
        police = ("Menlo", 12)
        
        cadre_en_tete = tk.Frame(self, bg=couleur_fond)
        cadre_en_tete.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        chemin_logo = "LABAC.jpg"
        if os.path.exists(chemin_logo):
            try:
                image_brute = Image.open(chemin_logo)
                image_redimensionnee = image_brute.resize((150, 45), Image.Resampling.LANCZOS)
                self.image_logo_tk = ImageTk.PhotoImage(image_redimensionnee)
                label_logo = tk.Label(cadre_en_tete, image=self.image_logo_tk, bg=couleur_fond)
                label_logo.pack(side=tk.LEFT, padx=(0, 20))
            except Exception as e:
                print(f"Erreur d'allocation de l'image {chemin_logo} : {e}")
        
        cadre_titre = tk.Frame(cadre_en_tete, bg=couleur_fond)
        cadre_titre.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(cadre_titre, text="Pegar Las Cuevas", bg=couleur_fond, fg="#00aaff", font=("Arial", 22, "bold")).pack(anchor="w")
        tk.Label(
            cadre_titre, 
            text="(c) Pr. Samuel Bassetto ; samuel-jean.bassetto@polymtl.ca\nSoftware under M.I.T. License", 
            bg=couleur_fond, fg=couleur_texte, font=("Arial", 10), justify="left"
        ).pack(anchor="w", pady=(2, 0))
        
        cadre_chemins = tk.Frame(self, bg=couleur_fond)
        cadre_chemins.pack(pady=15, fill=tk.X, padx=10)
        
        tk.Label(cadre_chemins, text="Dossier Source :", bg=couleur_fond, fg=couleur_texte, font=police, width=18, anchor="e").grid(row=0, column=0, pady=5, sticky="e")
        tk.Entry(cadre_chemins, textvariable=self.dossier_source, font=police, bg=couleur_liste, fg="#00aaff", insertbackground="white").grid(row=0, column=1, sticky="ew", padx=5)
        tk.Button(cadre_chemins, text="Parcourir...", command=self.choisir_source).grid(row=0, column=2, padx=5)

        tk.Label(cadre_chemins, text="Dossier Cible :", bg=couleur_fond, fg=couleur_texte, font=police, width=18, anchor="e").grid(row=1, column=0, pady=5, sticky="e")
        tk.Entry(cadre_chemins, textvariable=self.dossier_destination, font=police, bg=couleur_liste, fg="#00aaff", insertbackground="white").grid(row=1, column=1, sticky="ew", padx=5)
        tk.Button(cadre_chemins, text="Parcourir...", command=self.choisir_destination).grid(row=1, column=2, padx=5)

        tk.Label(cadre_chemins, text="Nom de sortie :", bg=couleur_fond, fg=couleur_texte, font=police, width=18, anchor="e").grid(row=2, column=0, pady=5, sticky="e")
        tk.Entry(cadre_chemins, textvariable=self.nom_archive_sortie, font=police, bg=couleur_liste, fg="#00aaff", insertbackground="white").grid(row=2, column=1, sticky="ew", padx=5)

        tk.Label(cadre_chemins, text="Fenêtre max (s) :", bg=couleur_fond, fg=couleur_texte, font=police, width=18, anchor="e").grid(row=3, column=0, pady=5, sticky="e")
        tk.Entry(cadre_chemins, textvariable=self.limite_affichage, font=police, bg=couleur_liste, fg="#00aaff", insertbackground="white").grid(row=3, column=1, sticky="ew", padx=5)
        
        cadre_chemins.columnconfigure(1, weight=1)

        cadre_central = tk.Frame(self, bg=couleur_fond)
        cadre_central.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        cadre_gauche = tk.Frame(cadre_central, bg=couleur_fond)
        cadre_gauche.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Label(cadre_gauche, text="Archives détectées", bg=couleur_fond, fg=couleur_texte, font=police).pack()
        self.liste_disponible = tk.Listbox(cadre_gauche, bg=couleur_liste, fg=couleur_texte, font=police, selectmode=tk.EXTENDED)
        self.liste_disponible.pack(expand=True, fill=tk.BOTH)

        cadre_boutons = tk.Frame(cadre_central, bg=couleur_fond)
        cadre_boutons.pack(side=tk.LEFT, padx=15, pady=50)
        
        tk.Button(cadre_boutons, text="Ajouter ➔", command=self.ajouter_archive, width=12).pack(pady=5)
        tk.Button(cadre_boutons, text="ç Retirer", command=self.retirer_archive, width=12).pack(pady=5)
        tk.Button(cadre_boutons, text="Monter", command=self.monter_element, width=12).pack(pady=20)
        tk.Button(cadre_boutons, text="Descendre", command=self.descendre_element, width=12).pack(pady=5)

        cadre_droit = tk.Frame(cadre_central, bg=couleur_fond)
        cadre_droit.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Label(cadre_droit, text="Ordre d'assemblage (Index 0 = Base)", bg=couleur_fond, fg=couleur_texte, font=police).pack()
        self.liste_selection = tk.Listbox(cadre_droit, bg=couleur_liste, fg="#00aaff", font=police, selectmode=tk.SINGLE)
        self.liste_selection.pack(expand=True, fill=tk.BOTH)

        cadre_bas = tk.Frame(self, bg=couleur_fond)
        cadre_bas.pack(pady=10, fill=tk.X, padx=10)
        self.btn_fusion = tk.Button(cadre_bas, text="LANCER L'ASSEMBLAGE (PEGAR)", command=self.executer_traitement, bg="#28a745", fg="black", font=("Arial", 14, "bold"))
        self.btn_fusion.pack(fill=tk.X, ipady=10)
        
        # Interface d'extraction asynchrone isolée
        cadre_export = tk.Frame(self, bg=couleur_fond)
        cadre_export.pack(pady=10, fill=tk.X, padx=10)
        
        tk.Label(cadre_export, text="Export PCD Indépendant Haute Densité", bg=couleur_fond, fg="#f39c12", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))
        
        sous_cadre_source = tk.Frame(cadre_export, bg=couleur_fond)
        sous_cadre_source.pack(fill=tk.X, pady=2)
        tk.Label(sous_cadre_source, text="Archive source :", bg=couleur_fond, fg=couleur_texte, font=police, width=18, anchor="e").pack(side=tk.LEFT)
        tk.Entry(sous_cadre_source, textvariable=self.bag_export_source, font=police, bg=couleur_liste, fg="#00aaff", insertbackground="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(sous_cadre_source, text="Parcourir...", command=self.choisir_bag_export).pack(side=tk.LEFT, padx=5)

        sous_cadre_dest = tk.Frame(cadre_export, bg=couleur_fond)
        sous_cadre_dest.pack(fill=tk.X, pady=2)
        tk.Label(sous_cadre_dest, text="Dossier cible :", bg=couleur_fond, fg=couleur_texte, font=police, width=18, anchor="e").pack(side=tk.LEFT)
        tk.Entry(sous_cadre_dest, textvariable=self.dossier_export_pcd, font=police, bg=couleur_liste, fg="#00aaff", insertbackground="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(sous_cadre_dest, text="Parcourir...", command=self.choisir_dest_export).pack(side=tk.LEFT, padx=5)

        sous_cadre_nom = tk.Frame(cadre_export, bg=couleur_fond)
        sous_cadre_nom.pack(fill=tk.X, pady=2)
        tk.Label(sous_cadre_nom, text="Nom du fichier :", bg=couleur_fond, fg=couleur_texte, font=police, width=18, anchor="e").pack(side=tk.LEFT)
        tk.Entry(sous_cadre_nom, textvariable=self.nom_export_pcd, font=police, bg=couleur_liste, fg="#00aaff", width=30, insertbackground="white").pack(side=tk.LEFT, padx=5)
        tk.Label(sous_cadre_nom, text=".pcd", bg=couleur_fond, fg=couleur_texte, font=police).pack(side=tk.LEFT)

        sous_cadre_param = tk.Frame(cadre_export, bg=couleur_fond)
        sous_cadre_param.pack(fill=tk.X, pady=2)
        tk.Label(sous_cadre_param, text="Taille Voxel (m) :", bg=couleur_fond, fg=couleur_texte, font=police, width=18, anchor="e").pack(side=tk.LEFT)
        tk.Entry(sous_cadre_param, textvariable=self.voxel_export, font=police, bg=couleur_liste, fg="#00aaff", width=10, insertbackground="white").pack(side=tk.LEFT, padx=5)
        
        self.btn_lancer_export = tk.Button(cadre_export, text="LANCER L'EXPORT PCD", command=self.lancer_export_pcd, bg="#f39c12", fg="black", font=("Arial", 12, "bold"))
        self.btn_lancer_export.pack(pady=5, fill=tk.X)
        
        self.label_statut_export = tk.Label(cadre_export, textvariable=self.statut_export, bg=couleur_fond, fg="#28a745", font=("Arial", 12, "bold"))
        self.label_statut_export.pack(pady=2)

    def choisir_source(self):
        dossier = filedialog.askdirectory(initialdir=self.dossier_source.get(), title="Sélectionner le répertoire source")
        if dossier:
            self.dossier_source.set(dossier)
            self.charger_archives_disponibles()

    def choisir_destination(self):
        dossier = filedialog.askdirectory(initialdir=self.dossier_destination.get(), title="Sélectionner le répertoire cible")
        if dossier:
            self.dossier_destination.set(dossier)

    def choisir_bag_export(self):
        dossier = filedialog.askdirectory(initialdir=self.dossier_source.get(), title="Sélectionner l'archive ROS 2 (Bag) à exporter")
        if dossier:
            self.bag_export_source.set(dossier)

    def choisir_dest_export(self):
        dossier = filedialog.askdirectory(initialdir=self.dossier_export_pcd.get(), title="Sélectionner le répertoire d'enregistrement PCD")
        if dossier:
            self.dossier_export_pcd.set(dossier)

    def charger_archives_disponibles(self):
        self.liste_disponible.delete(0, tk.END)
        self.chemins_disponibles.clear()
        
        racine = Path(self.dossier_source.get())
        if not racine.exists():
            return
            
        fichiers_db3_bruts = list(racine.rglob("*.db3"))
        
        for fichier in fichiers_db3_bruts:
            if fichier.name.startswith("._"):
                continue
            dossier_bag = fichier.parent
            if (dossier_bag / "metadata.yaml").is_file():
                if dossier_bag not in self.chemins_disponibles:
                    self.chemins_disponibles.append(dossier_bag)
                    chemin_relatif = dossier_bag.relative_to(racine)
                    self.liste_disponible.insert(tk.END, str(chemin_relatif))

    def ajouter_archive(self):
        indices = self.liste_disponible.curselection()
        for i in indices:
            chemin_absolu = self.chemins_disponibles[i]
            texte_affiche = self.liste_disponible.get(i)
            self.chemins_selectionnes.append(chemin_absolu)
            self.liste_selection.insert(tk.END, texte_affiche)

    def retirer_archive(self):
        indice = self.liste_selection.curselection()
        if indice:
            idx = indice[0]
            self.liste_selection.delete(idx)
            self.chemins_selectionnes.pop(idx)

    def monter_element(self):
        indice = self.liste_selection.curselection()
        if indice and indice[0] > 0:
            idx = indice[0]
            texte = self.liste_selection.get(idx)
            chemin = self.chemins_selectionnes[idx]
            
            self.liste_selection.delete(idx)
            self.chemins_selectionnes.pop(idx)
            
            self.liste_selection.insert(idx - 1, texte)
            self.chemins_selectionnes.insert(idx - 1, chemin)
            self.liste_selection.selection_set(idx - 1)

    def descendre_element(self):
        indice = self.liste_selection.curselection()
        if indice and indice[0] < self.liste_selection.size() - 1:
            idx = indice[0]
            texte = self.liste_selection.get(idx)
            chemin = self.chemins_selectionnes[idx]
            
            self.liste_selection.delete(idx)
            self.chemins_selectionnes.pop(idx)
            
            self.liste_selection.insert(idx + 1, texte)
            self.chemins_selectionnes.insert(idx + 1, chemin)
            self.liste_selection.selection_set(idx + 1)

    def executer_traitement(self):
        if self.en_cours_assemblage:
            return
            
        if len(self.chemins_selectionnes) < 2:
            messagebox.showerror("Erreur", "L'assemblage nécessite au minimum deux segments topologiques.")
            return
            
        nom_sortie = self.nom_archive_sortie.get().strip()
        if not nom_sortie:
            messagebox.showerror("Erreur", "Veuillez définir un nom pour l'archive de sortie.")
            return
            
        dossier_sortie = Path(self.dossier_destination.get()) / nom_sortie
            
        try:
            limite_sec = self.limite_affichage.get()
        except ValueError:
            messagebox.showerror("Erreur", "La valeur saisie pour la fenêtre max doit être un entier.")
            return
            
        self.btn_fusion.config(state=tk.DISABLED)
        self.btn_lancer_export.config(state=tk.DISABLED)
        threading.Thread(target=self.processus_assemblage, args=(self.chemins_selectionnes, dossier_sortie, nom_sortie, limite_sec)).start()

    def processus_assemblage(self, liste_chemins, dossier_sortie, nom_sortie, limite_sec):
        self.en_cours_assemblage = True
        
        try:
            dossier_sortie.mkdir(parents=True, exist_ok=True)
            dossier_connected = Path(self.dossier_source.get()) / "connected"
            dossier_connected.mkdir(parents=True, exist_ok=True)
            
            print("=== CAVE EXPLORER : ASSEMBLAGE ODOMÉTRIQUE ===")
            
            def maj_interface():
                self.after(0, lambda: self.liste_selection.delete(0))

            nuage_final, matrices_absolues, fichiers_traites, erreur_msg = assembler_nuages_sequentiellement(
                liste_chemins, dossier_sortie, callback_mise_a_jour_ui=maj_interface, limite_affichage=limite_sec
            )
            
            if erreur_msg:
                print(f"\nL'assemblage a été interrompu. Erreur : {erreur_msg}")
                self.after(0, lambda: messagebox.showerror("Erreur d'assemblage", f"L'intégration a échoué.\n\nDétails :\n{erreur_msg}"))
                return
                
            if nuage_final is None or not fichiers_traites:
                self.after(0, lambda: messagebox.showerror("Erreur critique", "Le processus n'a retourné aucune donnée."))
                return
                
            chemin_export_pcd = str(dossier_sortie / f"{nom_sortie}.pcd")
            chemin_export_db3 = str(dossier_sortie / f"{nom_sortie}_bag")
            
            o3d.io.write_point_cloud(chemin_export_pcd, nuage_final)
            print(f"\nModèle 3D Open3D exporté : {chemin_export_pcd}")
            
            exporter_bag_unifie(fichiers_traites, matrices_absolues, chemin_export_db3)
            print(f"Archive ROS 2 séquentielle exportée : {chemin_export_db3}")

            print("\n--- CLASSEMENT DES ARCHIVES TRAITÉES ---")
            for dossier_bag in fichiers_traites:
                destination = dossier_connected / dossier_bag.name
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.move(str(dossier_bag), str(destination))
                print(f"Segment archivé vers : {destination}")
                
            print("\nNettoyage des points de contrôle temporaires...")
            dossier_checkpoints = dossier_sortie / ".checkpoints_pegar"
            if dossier_checkpoints.exists():
                shutil.rmtree(dossier_checkpoints)
                
            print("\nLe répertoire source a été purgé des fichiers fusionnés.")
            
        finally:
            self.en_cours_assemblage = False
            self.after(0, lambda: self.btn_fusion.config(state=tk.NORMAL))
            self.after(0, lambda: self.btn_lancer_export.config(state=tk.NORMAL))

    def lancer_export_pcd(self):
        if self.en_cours_assemblage:
            return
            
        dossier_bag = self.bag_export_source.get().strip()
        if not dossier_bag or not Path(dossier_bag).exists():
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier d'archive valide avant de lancer l'exportation.")
            return
            
        nom_sortie = self.nom_export_pcd.get().strip()
        if not nom_sortie:
            messagebox.showerror("Erreur", "Veuillez spécifier un nom pour le fichier PCD.")
            return
            
        try:
            voxel_size = self.voxel_export.get()
        except ValueError:
            messagebox.showerror("Erreur", "La taille de voxel doit être un nombre décimal valide.")
            return
            
        dossier_dest = Path(self.dossier_export_pcd.get())
        dossier_dest.mkdir(parents=True, exist_ok=True)
        
        self.statut_export.set("Initialisation de l'extraction...")
        self.btn_lancer_export.config(state=tk.DISABLED)
        self.btn_fusion.config(state=tk.DISABLED)
        
        threading.Thread(target=self.processus_export_pcd, args=(dossier_bag, dossier_dest, nom_sortie, voxel_size)).start()

    def processus_export_pcd(self, dossier_bag, dossier_dest, nom_sortie, voxel_size):
        self.en_cours_assemblage = True
        try:
            print(f"\n=== EXPORT PCD HAUTE DENSITÉ : {Path(dossier_bag).name} ===")
            print(f"Extraction ciblée sur un voxel de {voxel_size} m")
            
            def maj_progression(pct):
                self.after(0, lambda: self.statut_export.set(f"Traitement en cours : {pct}% achevé"))
                
            nuage = extraire_pcd_massif(Path(dossier_bag), taille_voxel=voxel_size, callback_progression=maj_progression)
            
            if nuage is None or len(nuage.points) == 0:
                self.after(0, lambda: messagebox.showerror("Erreur", "Aucune coordonnée valide extraite de l'archive."))
                self.after(0, lambda: self.statut_export.set("Échec de l'extraction."))
                return
                
            nom_complet = f"{nom_sortie}.pcd"
            chemin_export = dossier_dest / nom_complet
            
            self.after(0, lambda: self.statut_export.set("Écriture du binaire PCD sur le disque..."))
            o3d.io.write_point_cloud(str(chemin_export), nuage)
            
            print(f"Écriture binaire finalisée : {chemin_export}")
            self.after(0, lambda: self.statut_export.set("Exportation terminée avec succès."))
            self.after(0, lambda: messagebox.showinfo("Succès", f"Fichier PCD généré avec succès :\n{chemin_export}"))
            
        except Exception as e:
            traceback.print_exc()
            self.after(0, lambda: self.statut_export.set("Arrêt critique lors de l'exportation."))
            self.after(0, lambda: messagebox.showerror("Erreur critique", f"L'exportation a échoué :\n{str(e)}"))
        finally:
            self.en_cours_assemblage = False
            self.after(0, lambda: self.btn_lancer_export.config(state=tk.NORMAL))
            self.after(0, lambda: self.btn_fusion.config(state=tk.NORMAL))

if __name__ == "__main__":
    app = InterfacePegar()
    app.mainloop()
