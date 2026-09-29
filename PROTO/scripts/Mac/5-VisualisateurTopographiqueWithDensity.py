# Fichier : 7-VisualisateurTopographique.py
# Fait par Pr Samuel Bassetto, Août 2026. samuel-jean.bassetto@polymtl.ca
import sys
import os
import json
import textwrap
import numpy as np
import open3d as o3d
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image, ImageTk, ImageDraw
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore
from scipy.ndimage import gaussian_filter
from scipy.spatial.transform import Rotation as R

# Dictionnaire de traduction (i18n) pour la reconfiguration dynamique de l'interface
TR = {
    'fr': {
        'app_title': "Analyse Topographique 3D",
        'viewer_title': "Visionneur d'enregistrements",
        'path_label': "Chemin du répertoire d'enregistrement ROS 2 :",
        'btn_browse': "Parcourir",
        'btn_load': "Charger la matrice géométrique",
        'cam_export': "Contrôle de la Caméra & Exportation",
        'btn_iso': "Isométrique",
        'btn_xy': "Plan X-Y",
        'btn_xz': "Plan X-Z",
        'btn_yz': "Plan Y-Z",
        'btn_export_pdf': "Exporter le plan cartographique (PDF)",
        'pt_size': "Taille matérielle des points :",
        'bg_color': "Matrice colorimétrique de fond :",
        'hm_frame': "Analyse et Heatmap de Densité",
        'hm_res': "Résolution spatiale (mètres) :",
        'hm_min': "Densité Minimale (Ignorer le bruit/vide) :",
        'hm_max': "Densité Maximale (Saturation Rouge) :",
        'btn_gen_hm': "Générer Heatmap",
        'btn_purge_hm': "Purger",
        'annot_frame': "Inspecteur d'Anomalies (Cliquer pour cibler)",
        'btn_toggle_annot': "Afficher/Masquer Heatmap et Annotations",
        'no_sel': "Aucune sélection active (Cliquez dans la liste)",
        'obs_label': "Observation technique sur la zone ciblée :",
        'btn_save_annot': "Enregistrer l'annotation",
        'btn_close': "Fermer le visualiseur",
        'pdf_success_title': "Exportation Réussie",
        'pdf_success_msg': "Le plan topographique a été généré :\n",
        'warn_title': "Avertissement",
        'warn_sel': "Veuillez sélectionner un point via la liste avant de sauvegarder.",
        'succ_title': "Succès",
        'succ_annot': "Annotation sauvegardée avec succès.",
        'lang': "FR",
        'state_carence': "Carence",
        'state_surcharge': "Surcharge",
        'state_standard': "Standard",
        'list_dens': "Densité",
        'list_pos': "Pos",
        'sel_active': "Sélection",
        'pdf_main_title': "Relevé Topographique de la Cavité",
        'pdf_dim': "Dimensions",
        'pdf_plan_xy': "Plan X-Y (Vue de dessus)",
        'pdf_plan_xz': "Plan X-Z (Vue de face)",
        'pdf_plan_yz': "Plan Y-Z (Vue de profil)",
        'pdf_iso': "Projection Isométrique",
        'pdf_axis_x': "Axe X (m)",
        'pdf_axis_y': "Axe Y (m)",
        'pdf_axis_z': "Axe Z (m)",
        'pdf_axis_px': "Axe Projeté X'",
        'pdf_axis_py': "Axe Projeté Y'",
        'pdf_reg_title': "Registre des Annotations",
        'pdf_no_annot': "Aucune annotation n'a été enregistrée pour cette cavité.",
        'pdf_pts': "points",
        'pdf_coord': "Coordonnées",
        'pdf_obs': "Observation :"
    },
    'en': {
        'app_title': "3D Topographic Analysis",
        'viewer_title': "Recording Viewer",
        'path_label': "ROS 2 recording directory path:",
        'btn_browse': "Browse",
        'btn_load': "Load Geometric Matrix",
        'cam_export': "Camera Control & Export",
        'btn_iso': "Isometric",
        'btn_xy': "X-Y Plane",
        'btn_xz': "X-Z Plane",
        'btn_yz': "Y-Z Plane",
        'btn_export_pdf': "Export Cartographic Plan (PDF)",
        'pt_size': "Hardware point size:",
        'bg_color': "Background color matrix:",
        'hm_frame': "Density Analysis & Heatmap",
        'hm_res': "Spatial resolution (meters):",
        'hm_min': "Minimum Density (Ignore noise/void):",
        'hm_max': "Maximum Density (Red Saturation):",
        'btn_gen_hm': "Generate Heatmap",
        'btn_purge_hm': "Purge",
        'annot_frame': "Anomaly Inspector (Click to target)",
        'btn_toggle_annot': "Show/Hide Heatmap and Annotations",
        'no_sel': "No active selection (Click in the list)",
        'obs_label': "Technical observation on the targeted zone:",
        'btn_save_annot': "Save Annotation",
        'btn_close': "Close Viewer",
        'pdf_success_title': "Export Successful",
        'pdf_success_msg': "The topographic plan has been generated:\n",
        'warn_title': "Warning",
        'warn_sel': "Please select a point from the list before saving.",
        'succ_title': "Success",
        'succ_annot': "Annotation successfully saved.",
        'lang': "EN",
        'state_carence': "Deficit",
        'state_surcharge': "Overload",
        'state_standard': "Standard",
        'list_dens': "Density",
        'list_pos': "Pos",
        'sel_active': "Selection",
        'pdf_main_title': "Topographic Survey of the Cavity",
        'pdf_dim': "Dimensions",
        'pdf_plan_xy': "X-Y Plane (Top view)",
        'pdf_plan_xz': "X-Z Plane (Front view)",
        'pdf_plan_yz': "Y-Z Plane (Side view)",
        'pdf_iso': "Isometric Projection",
        'pdf_axis_x': "X Axis (m)",
        'pdf_axis_y': "Y Axis (m)",
        'pdf_axis_z': "Z Axis (m)",
        'pdf_axis_px': "Projected X' Axis",
        'pdf_axis_py': "Projected Y' Axis",
        'pdf_reg_title': "Annotations Registry",
        'pdf_no_annot': "No annotation has been recorded for this cavity.",
        'pdf_pts': "points",
        'pdf_coord': "Coordinates",
        'pdf_obs': "Observation:"
    },
    'es': {
        'app_title': "Análisis Topográfico 3D",
        'viewer_title': "Visor de Grabaciones",
        'path_label': "Ruta del directorio de grabación ROS 2:",
        'btn_browse': "Explorar",
        'btn_load': "Cargar Matriz Geométrica",
        'cam_export': "Control de Cámara y Exportación",
        'btn_iso': "Isométrico",
        'btn_xy': "Plano X-Y",
        'btn_xz': "Plano X-Z",
        'btn_yz': "Plano Y-Z",
        'btn_export_pdf': "Exportar Plano Cartográfico (PDF)",
        'pt_size': "Tamaño material de los puntos:",
        'bg_color': "Matriz colorimétrica de fondo:",
        'hm_frame': "Análisis y Mapa de Calor de Densidad",
        'hm_res': "Resolución espacial (metros):",
        'hm_min': "Densidad Mínima (Ignorar ruido/vacío):",
        'hm_max': "Densidad Máxima (Saturación Roja):",
        'btn_gen_hm': "Generar Mapa de Calor",
        'btn_purge_hm': "Purgar",
        'annot_frame': "Inspector de Anomalías (Clic para apuntar)",
        'btn_toggle_annot': "Mostrar/Ocultar Mapa de Calor y Anotaciones",
        'no_sel': "Sin selección activa (Clic en la lista)",
        'obs_label': "Observación técnica sobre la zona objetivo:",
        'btn_save_annot': "Guardar Anotación",
        'btn_close': "Cerrar Visor",
        'pdf_success_title': "Exportación Exitosa",
        'pdf_success_msg': "El plano topográfico ha sido generado:\n",
        'warn_title': "Advertencia",
        'warn_sel': "Seleccione un punto de la lista antes de guardar.",
        'succ_title': "Éxito",
        'succ_annot': "Anotación guardada con éxito.",
        'lang': "ES",
        'state_carence': "Carencia",
        'state_surcharge': "Sobrecarga",
        'state_standard': "Estándar",
        'list_dens': "Densidad",
        'list_pos': "Pos",
        'sel_active': "Selección",
        'pdf_main_title': "Levantamiento Topográfico de la Cavidad",
        'pdf_dim': "Dimensiones",
        'pdf_plan_xy': "Plano X-Y (Vista superior)",
        'pdf_plan_xz': "Plano X-Z (Vista frontal)",
        'pdf_plan_yz': "Plano Y-Z (Vista lateral)",
        'pdf_iso': "Proyección Isométrica",
        'pdf_axis_x': "Eje X (m)",
        'pdf_axis_y': "Eje Y (m)",
        'pdf_axis_z': "Eje Z (m)",
        'pdf_axis_px': "Eje Proyectado X'",
        'pdf_axis_py': "Eje Proyectado Y'",
        'pdf_reg_title': "Registro de Anotaciones",
        'pdf_no_annot': "No se ha registrado ninguna anotación para esta cavidad.",
        'pdf_pts': "puntos",
        'pdf_coord': "Coordenadas",
        'pdf_obs': "Observación:"
    }
}

def extraire_nuage_points(chemin_bag):
    chemin_source = Path(chemin_bag)
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    nuages_temporels = []
    
    dossiers_cibles = []
    for fichier_yaml in chemin_source.rglob("metadata.yaml"):
        if not fichier_yaml.name.startswith("._"):
            dossiers_cibles.append(fichier_yaml.parent)
            
    if not dossiers_cibles:
        dossiers_cibles = [chemin_source]
        
    print(f"Ciblage des archives ROS 2 : {[d.name for d in dossiers_cibles]}")
    
    with AnyReader(dossiers_cibles, default_typestore=typestore) as lecteur:
        connexions = [x for x in lecteur.connections if x.topic == '/kf_cloud']
        if not connexions:
            print("Erreur : Aucune donnée géométrique (/kf_cloud) détectée.")
            return np.empty((0, 3))
            
        print("Extraction des trames spatiales en cours...")
        for connexion, timestamp, rawdata in lecteur.messages(connections=connexions):
            msg = lecteur.deserialize(rawdata, connexion.msgtype)
            data = np.asarray(msg.data, dtype=np.uint8)
            points = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)[:, :3]
            points_valides = points[np.isfinite(points).all(axis=1)]
            if len(points_valides) > 0:
                nuages_temporels.append(points_valides)
                
    return np.vstack(nuages_temporels) if nuages_temporels else np.empty((0, 3))

def appliquer_colorimetrie_z(matrice_points, nom_palette):
    altitudes = matrice_points[:, 2]
    z_min, z_max = np.min(altitudes), np.max(altitudes)
    if z_max > z_min:
        altitudes_normalisees = (altitudes - z_min) / (z_max - z_min)
    else:
        altitudes_normalisees = np.zeros_like(altitudes)
        
    cmap = plt.get_cmap(nom_palette)
    return cmap(altitudes_normalisees)[:, :3]

def calculer_couleurs_densite(comptes, seuil_min, seuil_max, nom_palette="turbo"):
    comptes_tronques = np.clip(comptes, seuil_min, seuil_max)
    if seuil_max > seuil_min:
        densites_normalisees = (comptes_tronques - seuil_min) / (seuil_max - seuil_min)
    else:
        densites_normalisees = np.zeros_like(comptes_tronques)
        
    cmap = plt.get_cmap(nom_palette)
    return cmap(densites_normalisees)[:, :3]

def generer_lineset_boites(centres, taille_voxel, couleurs_rgb):
    if len(centres) == 0:
        return o3d.geometry.LineSet()
    
    rayon = taille_voxel / 2.0
    sommets_relatifs = np.array([
        [-rayon, -rayon, -rayon], [rayon, -rayon, -rayon], [rayon, rayon, -rayon], [-rayon, rayon, -rayon],
        [-rayon, -rayon, rayon], [rayon, -rayon, rayon], [rayon, rayon, rayon], [-rayon, rayon, rayon]
    ])
    
    lignes_relatives = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7]
    ]
    
    sommets_compiles = []
    lignes_compilees = []
    couleurs_compilees = []
    decalage_index = 0
    
    for i, centre in enumerate(centres):
        sommets_compiles.append(sommets_relatifs + centre)
        lignes_compilees.append(np.array(lignes_relatives) + decalage_index)
        couleurs_compilees.extend([couleurs_rgb[i]] * 12)
        decalage_index += 8
        
    lineset = o3d.geometry.LineSet()
    lineset.points = o3d.utility.Vector3dVector(np.vstack(sommets_compiles))
    lineset.lines = o3d.utility.Vector2iVector(np.vstack(lignes_compilees))
    lineset.colors = o3d.utility.Vector3dVector(np.array(couleurs_compilees))
    return lineset

class VisualiseurInteractif(tk.Tk):
    def __init__(self):
        super().__init__()
        # Initialisation de la langue par défaut
        self.lang = 'fr'
        
        self.geometry("650x280")
        self.configure(bg="#2d2d2d")
        self.protocol("WM_DELETE_WINDOW", self.fermer_application)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#2d2d2d", foreground="white", font=("Arial", 11))
        
        self.matrice_brute = None
        self.nuage_o3d = None
        self.nuage_densite = None
        self.marqueur_selection = None
        self.geometries_bulles = []
        
        self.donnees_annotations = []
        self.centres_voxels_actifs = []
        self.comptes_voxels_actifs = []
        
        self.coordonnees_cibles_courantes = None
        self.compte_cible_courant = None
        
        self.etat_affichage_heatmap = True
        self.vis = None
        self.en_cours = False
        self.image_logo_tk = None
        
        self.construire_interface_selection()
        self.actualiser_textes_interface()

    def construire_interface_selection(self):
        couleur_fond = "#2d2d2d"
        cadre_en_tete = tk.Frame(self, bg=couleur_fond)
        cadre_en_tete.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        chemin_logo = "LABAC.jpg"
        if os.path.exists(chemin_logo):
            try:
                image_brute = Image.open(chemin_logo)
                image_redimensionnee = image_brute.resize((150, 45), Image.Resampling.LANCZOS)
                self.image_logo_tk = ImageTk.PhotoImage(image_redimensionnee)
                tk.Label(cadre_en_tete, image=self.image_logo_tk, bg=couleur_fond).pack(side=tk.LEFT, padx=(0, 20))
            except Exception:
                pass
        
        cadre_titre = tk.Frame(cadre_en_tete, bg=couleur_fond)
        cadre_titre.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_viewer_title = tk.Label(cadre_titre, bg=couleur_fond, fg="#00aaff", font=("Arial", 22, "bold"))
        self.lbl_viewer_title.pack(anchor="w")
        tk.Label(cadre_titre, text="(c) Pr. Samuel Bassetto ; samuel-jean.bassetto@polymtl.ca", bg=couleur_fond, fg="white", font=("Arial", 10)).pack(anchor="w", pady=(2, 0))

        # Intégration du commutateur linguistique dans l'en-tête
        self.btn_lang = tk.Button(cadre_en_tete, command=self.basculer_langue, bg="#f39c12", fg="black", font=("Arial", 10, "bold"))
        self.btn_lang.pack(side=tk.RIGHT, padx=10)

        self.cadre_selection = tk.Frame(self, bg=couleur_fond)
        self.cadre_selection.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        self.lbl_path = ttk.Label(self.cadre_selection)
        self.lbl_path.pack(anchor=tk.W, pady=(0, 10))
        
        cadre_saisie = tk.Frame(self.cadre_selection, bg=couleur_fond)
        cadre_saisie.pack(fill=tk.X, pady=(0, 20))
        
        self.variable_chemin = tk.StringVar()
        ttk.Entry(cadre_saisie, textvariable=self.variable_chemin, width=60).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        
        self.btn_browse = tk.Button(cadre_saisie, command=self.parcourir_dossier, bg="white", fg="black", highlightbackground="white")
        self.btn_browse.pack(side=tk.RIGHT)
        
        self.btn_load = tk.Button(self.cadre_selection, command=self.initialiser_moteur, bg="#00aaff", fg="black", highlightbackground="#00aaff", font=("Arial", 12, "bold"))
        self.btn_load.pack(fill=tk.X)

    def basculer_langue(self):
        # Rotation cyclique de l'index linguistique
        langues = ['fr', 'en', 'es']
        idx = langues.index(self.lang)
        self.lang = langues[(idx + 1) % len(langues)]
        self.actualiser_textes_interface()

    def actualiser_textes_interface(self):
        # Routine de rafraîchissement asynchrone des labels d'interface selon le référentiel TR
        t = TR[self.lang]
        self.title(t['app_title'])
        self.btn_lang.config(text=t['lang'])
        
        if hasattr(self, 'lbl_viewer_title') and self.lbl_viewer_title.winfo_exists():
            self.lbl_viewer_title.config(text=t['viewer_title'])
        if hasattr(self, 'lbl_path') and self.lbl_path.winfo_exists():
            self.lbl_path.config(text=t['path_label'])
        if hasattr(self, 'btn_browse') and self.btn_browse.winfo_exists():
            self.btn_browse.config(text=t['btn_browse'])
        if hasattr(self, 'btn_load') and self.btn_load.winfo_exists():
            self.btn_load.config(text=t['btn_load'])
            
        if hasattr(self, 'lf_cam') and self.lf_cam.winfo_exists():
            self.lf_cam.config(text=t['cam_export'])
            self.btn_iso.config(text=t['btn_iso'])
            self.btn_xy.config(text=t['btn_xy'])
            self.btn_xz.config(text=t['btn_xz'])
            self.btn_yz.config(text=t['btn_yz'])
            self.btn_export_pdf.config(text=t['btn_export_pdf'])
            
            self.lbl_pt_size.config(text=t['pt_size'])
            self.lbl_bg_color.config(text=t['bg_color'])
            
            self.lf_hm.config(text=t['hm_frame'])
            self.lbl_hm_res.config(text=t['hm_res'])
            self.lbl_hm_min.config(text=t['hm_min'])
            self.lbl_hm_max.config(text=t['hm_max'])
            self.btn_gen_hm.config(text=t['btn_gen_hm'])
            self.btn_purge_hm.config(text=t['btn_purge_hm'])
            
            self.lf_annot.config(text=t['annot_frame'])
            self.btn_toggle_annot.config(text=t['btn_toggle_annot'])
            self.lbl_obs.config(text=t['obs_label'])
            self.btn_save_annot.config(text=t['btn_save_annot'])
            self.btn_close.config(text=t['btn_close'])
            
            if self.coordonnees_cibles_courantes is None:
                self.label_coord.config(text=t['no_sel'])
            else:
                self.label_coord.config(text=f"{t['sel_active']} : {np.round(self.coordonnees_cibles_courantes, 2)} | {t['list_dens']} : {self.compte_cible_courant}")
            
            # Réinjection textuelle dans la liste dynamique
            self.peupler_liste_anomalies()

    def parcourir_dossier(self):
        dossier = filedialog.askdirectory(initialdir=str(Path.home() / "Desktop"))
        if dossier:
            self.variable_chemin.set(dossier)

    def initialiser_moteur(self):
        chemin_bag = self.variable_chemin.get()
        if not chemin_bag or not Path(chemin_bag).exists():
            return
            
        self.matrice_brute = extraire_nuage_points(chemin_bag)
        if self.matrice_brute.size == 0:
            return
            
        self.cadre_selection.pack_forget()
        self.construire_interface_controle()
        self.actualiser_textes_interface()
        
        self.nuage_o3d = o3d.geometry.PointCloud()
        self.nuage_o3d.points = o3d.utility.Vector3dVector(self.matrice_brute)
        self.nuage_o3d.colors = o3d.utility.Vector3dVector(appliquer_colorimetrie_z(self.matrice_brute, self.variable_palette.get()))
        
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(width=1400, height=900, left=480, top=50)
        self.vis.add_geometry(self.nuage_o3d)
        
        options = self.vis.get_render_option()
        options.background_color = np.asarray([0.02, 0.02, 0.02])
        options.point_size = self.variable_taille.get()
        
        self.charger_annotations_existantes()
        self.en_cours = True
        self.boucle_rendu()
        
        if len(self.donnees_annotations) > 0:
            self.executer_analyse_densite()

    def construire_interface_controle(self):
        self.geometry("450x880")
        
        cadre_principal = tk.Frame(self, bg="#2d2d2d")
        cadre_principal.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.lf_cam = tk.LabelFrame(cadre_principal, bg="#2d2d2d", fg="#e67e22", font=("Arial", 10, "bold"))
        self.lf_cam.pack(fill=tk.X, pady=(0, 10), ipady=5, ipadx=5)
        
        cadre_grille_vues = tk.Frame(self.lf_cam, bg="#2d2d2d")
        cadre_grille_vues.pack(fill=tk.X, padx=5, pady=5)
        self.btn_iso = tk.Button(cadre_grille_vues, command=lambda: self.changer_vue("ISO"))
        self.btn_iso.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.btn_xy = tk.Button(cadre_grille_vues, command=lambda: self.changer_vue("XY"))
        self.btn_xy.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.btn_xz = tk.Button(cadre_grille_vues, command=lambda: self.changer_vue("XZ"))
        self.btn_xz.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self.btn_yz = tk.Button(cadre_grille_vues, command=lambda: self.changer_vue("YZ"))
        self.btn_yz.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.btn_export_pdf = tk.Button(self.lf_cam, command=self.exporter_pdf, bg="#8e44ad", fg="black", highlightbackground="#8e44ad", font=("Arial", 10, "bold"))
        self.btn_export_pdf.pack(fill=tk.X, padx=5, pady=(5, 0))

        self.lbl_pt_size = ttk.Label(cadre_principal)
        self.lbl_pt_size.pack(anchor=tk.W, pady=(0, 5))
        self.variable_taille = tk.DoubleVar(value=1.5)
        ttk.Scale(cadre_principal, from_=0.1, to=15.0, orient=tk.HORIZONTAL, variable=self.variable_taille, command=self.actualiser_taille).pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_bg_color = ttk.Label(cadre_principal)
        self.lbl_bg_color.pack(anchor=tk.W)
        self.variable_palette = tk.StringVar(value="turbo")
        selecteur_palette = ttk.Combobox(cadre_principal, textvariable=self.variable_palette, values=["turbo", "viridis", "plasma", "terrain"], state="readonly")
        selecteur_palette.pack(fill=tk.X, pady=(0, 10))
        selecteur_palette.bind("<<ComboboxSelected>>", self.actualiser_couleurs_fond)
        
        self.lf_hm = tk.LabelFrame(cadre_principal, bg="#2d2d2d", fg="#00aaff", font=("Arial", 10, "bold"))
        self.lf_hm.pack(fill=tk.X, pady=(5, 10), ipady=5, ipadx=5)
        
        self.lbl_hm_res = ttk.Label(self.lf_hm)
        self.lbl_hm_res.pack(anchor=tk.W, padx=5)
        self.variable_res = tk.DoubleVar(value=1.0)
        ttk.Scale(self.lf_hm, from_=0.1, to=5.0, orient=tk.HORIZONTAL, variable=self.variable_res).pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.lbl_hm_min = ttk.Label(self.lf_hm)
        self.lbl_hm_min.pack(anchor=tk.W, padx=5)
        self.variable_min = tk.IntVar(value=10)
        ttk.Scale(self.lf_hm, from_=1, to=500, orient=tk.HORIZONTAL, variable=self.variable_min).pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.lbl_hm_max = ttk.Label(self.lf_hm)
        self.lbl_hm_max.pack(anchor=tk.W, padx=5)
        self.variable_max = tk.IntVar(value=500)
        ttk.Scale(self.lf_hm, from_=50, to=5000, orient=tk.HORIZONTAL, variable=self.variable_max).pack(fill=tk.X, padx=5, pady=(0, 10))
        
        cadre_boutons_hm = tk.Frame(self.lf_hm, bg="#2d2d2d")
        cadre_boutons_hm.pack(fill=tk.X, padx=5, pady=5)
        self.btn_gen_hm = tk.Button(cadre_boutons_hm, command=self.executer_analyse_densite, bg="#e67e22", fg="black", highlightbackground="#e67e22", font=("Arial", 10, "bold"))
        self.btn_gen_hm.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.btn_purge_hm = tk.Button(cadre_boutons_hm, command=self.effacer_heatmap)
        self.btn_purge_hm.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        self.lf_annot = tk.LabelFrame(cadre_principal, bg="#2d2d2d", fg="#2ecc71", font=("Arial", 10, "bold"))
        self.lf_annot.pack(fill=tk.BOTH, expand=True, pady=(5, 10), ipady=5, ipadx=5)
        
        self.btn_toggle_annot = tk.Button(self.lf_annot, command=self.basculer_heatmap, bg="#f39c12", fg="black", highlightbackground="#f39c12", font=("Arial", 10, "bold"))
        self.btn_toggle_annot.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.boite_liste = tk.Listbox(self.lf_annot, bg="#1a1a1a", fg="white", selectbackground="#00aaff", font=("Arial", 11), height=6)
        self.boite_liste.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.boite_liste.bind('<<ListboxSelect>>', self.cibler_zone_et_afficher)
        
        self.label_coord = ttk.Label(self.lf_annot, foreground="#e74c3c", font=("Arial", 10, "italic"))
        self.label_coord.pack(anchor=tk.W, padx=5, pady=(0, 5))

        self.lbl_obs = ttk.Label(self.lf_annot)
        self.lbl_obs.pack(anchor=tk.W, padx=5)
        
        self.champ_texte = tk.Text(self.lf_annot, height=4, bg="#1a1a1a", fg="white", font=("Arial", 11), insertbackground="white")
        self.champ_texte.pack(fill=tk.X, padx=5, pady=5)
        
        self.btn_save_annot = tk.Button(self.lf_annot, command=self.valider_annotation, bg="#27ae60", fg="black", highlightbackground="#27ae60", font=("Arial", 10, "bold"))
        self.btn_save_annot.pack(fill=tk.X, padx=5, pady=5)

        self.btn_close = tk.Button(cadre_principal, command=self.fermer_application, bg="#ff4444", fg="black", highlightbackground="#ff4444", font=("Arial", 12, "bold"))
        self.btn_close.pack(side=tk.BOTTOM, fill=tk.X)

    def basculer_heatmap(self):
        self.etat_affichage_heatmap = not self.etat_affichage_heatmap
        
        if not self.vis: return
        
        if self.etat_affichage_heatmap:
            if self.nuage_densite is not None:
                self.vis.add_geometry(self.nuage_densite, reset_bounding_box=False)
            if self.marqueur_selection is not None:
                self.vis.add_geometry(self.marqueur_selection, reset_bounding_box=False)
            for geom in self.geometries_bulles:
                self.vis.add_geometry(geom, reset_bounding_box=False)
        else:
            if self.nuage_densite is not None:
                self.vis.remove_geometry(self.nuage_densite, reset_bounding_box=False)
            if self.marqueur_selection is not None:
                self.vis.remove_geometry(self.marqueur_selection, reset_bounding_box=False)
            for geom in self.geometries_bulles:
                self.vis.remove_geometry(geom, reset_bounding_box=False)

    def changer_vue(self, plan):
        if not self.vis: return
        controle_camera = self.vis.get_view_control()
        if plan == "XY":
            controle_camera.set_front([0, 0, 1])
            controle_camera.set_up([0, 1, 0])
        elif plan == "XZ":
            controle_camera.set_front([0, -1, 0])
            controle_camera.set_up([0, 0, 1])
        elif plan == "YZ":
            controle_camera.set_front([-1, 0, 0])
            controle_camera.set_up([0, 0, 1])
        elif plan == "ISO":
            controle_camera.set_front([1, -1, 1])
            controle_camera.set_up([0, 0, 1])
        self.vis.update_renderer()

    def exporter_pdf(self):
        if self.matrice_brute is None: return
        t = TR[self.lang]
        
        dossier_cible = Path(self.variable_chemin.get())
        nom_grotte = dossier_cible.name
        chemin_export = dossier_cible / f"Rapport_Topographique_{nom_grotte}.pdf"
        
        points_3d = np.asarray(self.nuage_o3d.points)
        if len(points_3d) == 0: return

        boite_englobante = self.nuage_o3d.get_axis_aligned_bounding_box()
        dimensions = boite_englobante.get_extent()
        
        try:
            with PdfPages(chemin_export) as pdf:
                def dessiner_page(pts_3d, axes_idx, titre, xlabel, ylabel, is_iso=False):
                    fig, ax = plt.subplots(figsize=(11.69, 8.27))
                    fig.suptitle(f"{t['pdf_main_title']} : {nom_grotte}\n{t['pdf_dim']} (X, Y, Z) : {dimensions[0]:.1f}m x {dimensions[1]:.1f}m x {dimensions[2]:.1f}m", fontsize=14, fontweight='bold')

                    if is_iso:
                        rot_iso = R.from_euler('x', 35.264, degrees=True) * R.from_euler('y', 45, degrees=True)
                        pts_projetes = rot_iso.apply(pts_3d)
                        pts_2d = pts_projetes[:, [0, 1]]
                    else:
                        pts_2d = pts_3d[:, axes_idx]

                    xmin, xmax = np.min(pts_2d[:, 0]), np.max(pts_2d[:, 0])
                    ymin, ymax = np.min(pts_2d[:, 1]), np.max(pts_2d[:, 1])
                    
                    dx = (xmax - xmin) * 0.05
                    dy = (ymax - ymin) * 0.05
                    xmin, xmax = xmin - dx, xmax + dx
                    ymin, ymax = ymin - dy, ymax + dy

                    bins = 1000
                    H, xedges, yedges = np.histogram2d(pts_2d[:, 0], pts_2d[:, 1], bins=bins, range=[[xmin, xmax], [ymin, ymax]])
                    Z_mask = (H.T > 0).astype(float)
                    
                    Z_smooth = gaussian_filter(Z_mask, sigma=0.5)
                    X, Y = np.meshgrid((xedges[:-1] + xedges[1:]) / 2, (yedges[:-1] + yedges[1:]) / 2)
                    
                    ax.contour(X, Y, Z_smooth, levels=[0.1], colors='#2980b9', linewidths=1.0)
                    
                    for ann in self.donnees_annotations:
                        coord_3d = np.array(ann["coordonnees"])
                        if is_iso:
                            coord_proj = rot_iso.apply(coord_3d)[[0, 1]]
                        else:
                            coord_proj = coord_3d[axes_idx]
                            
                        ax.plot(coord_proj[0], coord_proj[1], marker='o', color='red', markersize=6)
                        ax.text(coord_proj[0] + dx*0.1, coord_proj[1] + dy*0.1, ann["id"], color='red', fontsize=9, fontweight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='red', boxstyle='round,pad=0.2'))

                    ax.set_title(titre, fontsize=12, fontweight='bold')
                    ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
                    ax.axis('equal')
                    ax.grid(True, linestyle='--', alpha=0.5)
                    
                    longueur_echelle = 10 if (xmax - xmin) < 100 else 50
                    pos_x = xmin + dx
                    pos_y = ymin + dy
                    ax.plot([pos_x, pos_x + longueur_echelle], [pos_y, pos_y], color='black', linewidth=3)
                    ax.text(pos_x + longueur_echelle/2, pos_y + dy*0.2, f"{longueur_echelle} m", ha='center', va='bottom', fontsize=9, fontweight='bold')

                    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
                    pdf.savefig(fig)
                    plt.close(fig)

                dessiner_page(points_3d, [0, 1], t['pdf_plan_xy'], t['pdf_axis_x'], t['pdf_axis_y'])
                dessiner_page(points_3d, [0, 2], t['pdf_plan_xz'], t['pdf_axis_x'], t['pdf_axis_z'])
                dessiner_page(points_3d, [1, 2], t['pdf_plan_yz'], t['pdf_axis_y'], t['pdf_axis_z'])
                dessiner_page(points_3d, None, t['pdf_iso'], t['pdf_axis_px'], t['pdf_axis_py'], is_iso=True)

                fig_text = plt.figure(figsize=(11.69, 8.27))
                fig_text.suptitle(f"{t['pdf_reg_title']} - {nom_grotte}", fontsize=16, fontweight='bold')
                ax_text = fig_text.add_subplot(111)
                ax_text.axis('off')
                
                texte_complet = ""
                if not self.donnees_annotations:
                    texte_complet = t['pdf_no_annot']
                else:
                    for ann in self.donnees_annotations:
                        texte_complet += f"[{ann['id']}] - {t['list_dens']}: {ann.get('nombre_points', 'N/A')} {t['pdf_pts']}\n"
                        texte_complet += f"{t['pdf_coord']} : X={ann['coordonnees'][0]:.2f}, Y={ann['coordonnees'][1]:.2f}, Z={ann['coordonnees'][2]:.2f}\n"
                        obs = ann.get('annotation', 'N/A')
                        obs_wrap = textwrap.fill(obs, width=120)
                        texte_complet += f"{t['pdf_obs']}\n{obs_wrap}\n"
                        texte_complet += "-" * 80 + "\n\n"
                
                ax_text.text(0.05, 0.95, texte_complet, fontsize=10, va='top', ha='left', family='monospace')
                pdf.savefig(fig_text)
                plt.close(fig_text)
                
            messagebox.showinfo(t['pdf_success_title'], f"{t['pdf_success_msg']}{chemin_export}")
            print(f"Exportation achevée : {chemin_export}")
        except Exception as e:
            messagebox.showerror("Erreur d'exportation", f"Impossible de générer le PDF :\n{e}")

    def rafraichir_bulles_annotations(self):
        if self.vis:
            for geom in self.geometries_bulles:
                self.vis.remove_geometry(geom, reset_bounding_box=False)
        self.geometries_bulles.clear()
        
        if not self.vis or not getattr(self, 'afficher_bulles', True):
            return
            
        taille_voxel = self.variable_res.get()
        
        for ann in self.donnees_annotations:
            texte = ann.get("annotation", "").strip()
            if texte:
                coord = np.array(ann["coordonnees"])
                
                sphere = o3d.geometry.TriangleMesh.create_sphere(radius=taille_voxel * 0.4)
                sphere.translate(coord)
                sphere.compute_vertex_normals()
                sphere.paint_uniform_color([0.9, 0.1, 0.1])
                self.geometries_bulles.append(sphere)
                
                img_small = Image.new('L', (400, 40), color=0)
                d = ImageDraw.Draw(img_small)
                texte_affiche = texte[:35] + ("..." if len(texte)>35 else "")
                d.text((5, 5), texte_affiche, fill=255)
                
                bbox = img_small.getbbox()
                img_cropped = img_small.crop(bbox) if bbox else img_small
                
                dense_w = 400
                ratio = dense_w / float(img_cropped.width)
                dense_h = max(int(img_cropped.height * ratio), 1)
                
                img_dense = img_cropped.resize((dense_w, dense_h), Image.Resampling.NEAREST)
                arr = np.array(img_dense)
                y_idx, x_idx = np.where(arr > 127)
                
                if len(x_idx) > 0:
                    echelle_texte = taille_voxel / 50.0
                    largeur_b = taille_voxel * 4.0
                    hauteur_b = largeur_b * (dense_h / float(dense_w)) + (taille_voxel * 0.4)
                    epaisseur_b = taille_voxel * 0.1
                    
                    decalage_z = taille_voxel * 3.5
                    centre_bulle = coord + np.array([0, 0, decalage_z])
                    
                    offset_y = (epaisseur_b / 2.0) + (taille_voxel * 0.08)
                    
                    x_c = ((x_idx / float(dense_w)) - 0.5) * (largeur_b * 0.9)
                    z_c = (0.5 - (y_idx / float(dense_h))) * (largeur_b * (dense_h / float(dense_w)) * 0.9)
                    
                    pts_front = np.vstack((-x_c, np.full_like(x_c, offset_y), z_c)).T + centre_bulle
                    pcd_front = o3d.geometry.PointCloud()
                    pcd_front.points = o3d.utility.Vector3dVector(pts_front)
                    pcd_front.paint_uniform_color([0.0, 0.0, 0.0])
                    self.geometries_bulles.append(pcd_front)
                    
                    pts_back = np.vstack((x_c, np.full_like(x_c, -offset_y), z_c)).T + centre_bulle
                    pcd_back = o3d.geometry.PointCloud()
                    pcd_back.points = o3d.utility.Vector3dVector(pts_back)
                    pcd_back.paint_uniform_color([0.0, 0.0, 0.0])
                    self.geometries_bulles.append(pcd_back)
                    
                    boite = o3d.geometry.TriangleMesh.create_box(width=largeur_b, height=epaisseur_b, depth=hauteur_b)
                    boite.translate(centre_bulle - np.array([largeur_b / 2.0, epaisseur_b / 2.0, hauteur_b / 2.0]))
                    boite.compute_vertex_normals()
                    boite.paint_uniform_color([1.0, 1.0, 1.0])
                    self.geometries_bulles.append(boite)
                    
                    points_lien = [coord, centre_bulle - np.array([0, 0, hauteur_b / 2.0])]
                    lineset_lien = o3d.geometry.LineSet(
                        points=o3d.utility.Vector3dVector(points_lien),
                        lines=o3d.utility.Vector2iVector([[0, 1]])
                    )
                    lineset_lien.colors = o3d.utility.Vector3dVector([[1.0, 1.0, 1.0]])
                    self.geometries_bulles.append(lineset_lien)
                    
        if self.etat_affichage_heatmap:
            for geom in self.geometries_bulles:
                self.vis.add_geometry(geom, reset_bounding_box=False)

    def executer_analyse_densite(self):
        if self.matrice_brute is None or not self.vis:
            return
            
        taille_voxel = self.variable_res.get()
        seuil_min = self.variable_min.get()
        seuil_max = self.variable_max.get()
        
        coordonnees_voxels = np.floor(self.matrice_brute / taille_voxel).astype(np.int32)
        voxels_uniques, comptes = np.unique(coordonnees_voxels, axis=0, return_counts=True)
        
        masque_valide = comptes >= seuil_min
        voxels_filtres = voxels_uniques[masque_valide]
        comptes_filtres = comptes[masque_valide]
        
        if len(voxels_filtres) == 0:
            self.effacer_heatmap()
            return
            
        centres_calcules = (voxels_filtres * taille_voxel) + (taille_voxel / 2.0)
        couleurs_calculees = calculer_couleurs_densite(comptes_filtres, seuil_min, seuil_max)
        
        self.effacer_heatmap()
        self.etat_affichage_heatmap = True
            
        self.nuage_densite = generer_lineset_boites(centres_calcules, taille_voxel, couleurs_calculees)
        self.centres_voxels_actifs = centres_calcules.tolist()
        self.comptes_voxels_actifs = comptes_filtres.tolist()
        
        self.vis.add_geometry(self.nuage_densite, reset_bounding_box=False)
        self.actualiser_taille()
        self.peupler_liste_anomalies()
        self.rafraichir_bulles_annotations()

    def peupler_liste_anomalies(self):
        self.boite_liste.delete(0, tk.END)
        self.champ_texte.delete("1.0", tk.END)
        
        t = TR[self.lang]
        self.label_coord.config(text=t['no_sel'], foreground="#e74c3c")
        
        seuil_critique = self.variable_max.get() * 0.8
        donnees_triees = sorted(zip(self.centres_voxels_actifs, self.comptes_voxels_actifs), key=lambda x: x[1])
        
        for coord, compte in donnees_triees:
            etat = t['state_carence'] if compte < (self.variable_min.get() * 2) else t['state_surcharge'] if compte > seuil_critique else t['state_standard']
            x_arrondi = round(coord[0], 1)
            y_arrondi = round(coord[1], 1)
            z_arrondi = round(coord[2], 1)
            entree_texte = f"[{etat}] {t['list_dens']}: {compte} | {t['list_pos']}: ({x_arrondi}, {y_arrondi}, {z_arrondi})"
            
            est_annote = False
            for ann in self.donnees_annotations:
                if np.allclose(ann["coordonnees"], coord, atol=0.1) and ann.get("annotation", "").strip():
                    est_annote = True
                    break
                    
            self.boite_liste.insert(tk.END, entree_texte)
            if est_annote:
                self.boite_liste.itemconfig(tk.END, {'bg': '#c0392b', 'fg': 'white'})

    def cibler_zone_et_afficher(self, event):
        selection = self.boite_liste.curselection()
        if not selection or not self.vis:
            return
            
        index = selection[0]
        donnees_triees = sorted(zip(self.centres_voxels_actifs, self.comptes_voxels_actifs), key=lambda x: x[1])
        coord_cible = donnees_triees[index][0]
        compte_local = donnees_triees[index][1]
        
        self.coordonnees_cibles_courantes = coord_cible
        self.compte_cible_courant = compte_local
        
        t = TR[self.lang]
        self.label_coord.config(text=f"{t['sel_active']} : {np.round(coord_cible, 2)} | {t['list_dens']} : {compte_local}", foreground="#2ecc71")
        
        if self.marqueur_selection is not None:
            self.vis.remove_geometry(self.marqueur_selection, reset_bounding_box=False)
            
        rayon_sphere = self.variable_res.get() * 0.8
        self.marqueur_selection = o3d.geometry.TriangleMesh.create_sphere(radius=rayon_sphere)
        self.marqueur_selection.translate(coord_cible)
        self.marqueur_selection.compute_vertex_normals()
        self.marqueur_selection.paint_uniform_color([0.1, 0.9, 0.1])
        
        if self.etat_affichage_heatmap:
            self.vis.add_geometry(self.marqueur_selection, reset_bounding_box=False)
        
        controle_camera = self.vis.get_view_control()
        controle_camera.set_lookat(coord_cible)
        controle_camera.set_zoom(0.15)
        
        self.champ_texte.delete("1.0", tk.END)
        
        for annotation in self.donnees_annotations:
            if np.allclose(annotation["coordonnees"], coord_cible, atol=0.1):
                self.champ_texte.insert(tk.END, annotation["annotation"])
                break

    def valider_annotation(self):
        t = TR[self.lang]
        if self.coordonnees_cibles_courantes is None:
            messagebox.showwarning(t['warn_title'], t['warn_sel'])
            return
            
        coord_cible = self.coordonnees_cibles_courantes
        compte_local = self.compte_cible_courant
        texte_saisi = self.champ_texte.get("1.0", tk.END).strip()
        
        nouvelle_entree = {
            "id": f"Annotation_{len(self.donnees_annotations) + 1}",
            "coordonnees": coord_cible.tolist() if isinstance(coord_cible, np.ndarray) else coord_cible,
            "nombre_points": compte_local,
            "annotation": texte_saisi
        }
        
        remplace = False
        for i, ann in enumerate(self.donnees_annotations):
            if np.allclose(ann["coordonnees"], coord_cible, atol=0.1):
                nouvelle_entree["id"] = ann.get("id", nouvelle_entree["id"])
                self.donnees_annotations[i] = nouvelle_entree
                remplace = True
                break
                
        if not remplace:
            self.donnees_annotations.append(nouvelle_entree)
            
        self.sauvegarder_json()
        self.rafraichir_bulles_annotations()
        self.peupler_liste_anomalies()

    def effacer_heatmap(self):
        if self.vis:
            if self.nuage_densite is not None:
                self.vis.remove_geometry(self.nuage_densite, reset_bounding_box=False)
            if self.marqueur_selection is not None:
                self.vis.remove_geometry(self.marqueur_selection, reset_bounding_box=False)
            for geom in self.geometries_bulles:
                self.vis.remove_geometry(geom, reset_bounding_box=False)
                
        self.nuage_densite = None
        self.marqueur_selection = None
        self.geometries_bulles.clear()
        
        self.centres_voxels_actifs = []
        self.comptes_voxels_actifs = []
        self.coordonnees_cibles_courantes = None
        self.compte_cible_courant = None
        
        self.boite_liste.delete(0, tk.END)
        self.champ_texte.delete("1.0", tk.END)
        
        t = TR[self.lang]
        self.label_coord.config(text=t['no_sel'], foreground="#e74c3c")

    def charger_annotations_existantes(self):
        chemin_export = Path(self.variable_chemin.get()) / "annotations_densite.json"
        if chemin_export.exists():
            try:
                with open(chemin_export, "r", encoding="utf-8") as fichier:
                    donnees = json.load(fichier)
                    if isinstance(donnees, dict) and "annotations" in donnees:
                        self.donnees_annotations = donnees["annotations"]
                        params = donnees.get("parametres", {})
                        if "resolution" in params: self.variable_res.set(params["resolution"])
                        if "min_densite" in params: self.variable_min.set(params["min_densite"])
                        if "max_densite" in params: self.variable_max.set(params["max_densite"])
                    elif isinstance(donnees, list):
                        self.donnees_annotations = donnees
            except Exception:
                self.donnees_annotations = []
        self.rafraichir_bulles_annotations()

    def sauvegarder_json(self):
        chemin_export = Path(self.variable_chemin.get()) / "annotations_densite.json"
        donnees_export = {
            "parametres": {
                "resolution": self.variable_res.get(),
                "min_densite": self.variable_min.get(),
                "max_densite": self.variable_max.get()
            },
            "annotations": self.donnees_annotations
        }
        try:
            with open(chemin_export, "w", encoding="utf-8") as fichier:
                json.dump(donnees_export, fichier, indent=4)
        except Exception as e:
            print(f"Erreur d'écriture du flux JSON : {e}")

    def actualiser_taille(self, event=None):
        if self.vis:
            options = self.vis.get_render_option()
            options.point_size = self.variable_taille.get()
            self.vis.update_renderer()

    def actualiser_couleurs_fond(self, event=None):
        if self.vis and self.nuage_o3d:
            nouvelles_couleurs = appliquer_colorimetrie_z(self.matrice_brute, self.variable_palette.get())
            self.nuage_o3d.colors = o3d.utility.Vector3dVector(nouvelles_couleurs)
            self.vis.update_geometry(self.nuage_o3d)
            self.vis.update_renderer()

    def boucle_rendu(self):
        if self.en_cours and self.vis:
            if not self.vis.poll_events():
                self.fermer_application()
                return
            self.vis.update_renderer()
            self.after(20, self.boucle_rendu)

    def fermer_application(self):
        self.en_cours = False
        if self.vis:
            self.vis.destroy_window()
        self.quit()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = VisualiseurInteractif()
    app.mainloop()