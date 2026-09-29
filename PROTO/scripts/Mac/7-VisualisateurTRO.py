# Fichier : VisualisateurTRO.py
# Fait par Pr Samuel Bassetto, Septembre 2026. samuel-jean.bassetto@polymtl.ca
import sys
import os
import math
import numpy as np
import open3d as o3d
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy.ndimage import gaussian_filter
from scipy.spatial.transform import Rotation as R

# Dictionnaire de traduction (i18n) pour la reconfiguration dynamique
TR = {
    'fr': {
        'app_title': "Rendu Topographique VTopo (LABAC)",
        'viewer_title': "Interpréteur Visual Topo (.tro)",
        'path_label': "Chemin du fichier topographique (.tro) :",
        'btn_browse': "Parcourir",
        'btn_load': "Compiler le modèle 3D",
        'ctrl_title': "Contrôles du Modèle Topographique",
        'lf_cam': "Orientation Axiale & Exportation",
        'btn_iso': "Isométrique",
        'btn_xy': "Plan X-Y (Dessus)",
        'btn_xz': "Plan X-Z (Face)",
        'btn_yz': "Plan Y-Z (Profil)",
        'btn_pdf': "Générer le PDF Topographique",
        'lf_filters': "Filtres Géométriques",
        'btn_toggle_rad': "Masquer/Afficher les Visées Radiantes",
        'btn_toggle_pcd': "Masquer/Afficher les Frontières (PCD)",
        'lf_env': "Reconstruction Surfacique (Alpha-Shape)",
        'lbl_alpha': "Paramètre géométrique Alpha (Volume) :",
        'btn_gen_env': "Générer l'Enveloppe VTopo",
        'btn_toggle_env': "Afficher/Masquer",
        'btn_close': "Fermer le visualiseur",
        'err_title': "Erreur",
        'err_not_found': "Le fichier spécifié est introuvable.",
        'err_corrupt': "Le fichier est corrompu ou illisible :",
        'err_no_data': "Aucune donnée topographique valide n'a été détectée dans le fichier.",
        'msg_pcd_found': "Fichier PCD détecté. Extraction des frontières en cours...",
        'msg_pdf_ok': "Le plan topographique a été généré avec succès :\n",
        'pdf_title_main': "Relevé Cartographique de la Cavité",
        'pdf_dim': "Dimensions de la boîte englobante",
        'pdf_plan_xy': "Plan X-Y (Vue de dessus)",
        'pdf_plan_xz': "Plan X-Z (Vue de face)",
        'pdf_plan_yz': "Plan Y-Z (Vue de profil)",
        'pdf_iso': "Projection Isométrique",
        'lang': "FR"
    },
    'en': {
        'app_title': "VTopo Topographic Render (LABAC)",
        'viewer_title': "Visual Topo Interpreter (.tro)",
        'path_label': "Topographic file path (.tro):",
        'btn_browse': "Browse",
        'btn_load': "Compile 3D Model",
        'ctrl_title': "Topographic Model Controls",
        'lf_cam': "Axial Orientation & Export",
        'btn_iso': "Isometric",
        'btn_xy': "X-Y Plane (Top)",
        'btn_xz': "X-Z Plane (Front)",
        'btn_yz': "Y-Z Plane (Side)",
        'btn_pdf': "Generate Topographic PDF",
        'lf_filters': "Geometric Filters",
        'btn_toggle_rad': "Hide/Show Splay Shots",
        'btn_toggle_pcd': "Hide/Show Boundaries (PCD)",
        'lf_env': "Surface Reconstruction (Alpha-Shape)",
        'lbl_alpha': "Alpha geometric parameter (Volume):",
        'btn_gen_env': "Generate VTopo Envelope",
        'btn_toggle_env': "Show/Hide",
        'btn_close': "Close Viewer",
        'err_title': "Error",
        'err_not_found': "The specified file cannot be found.",
        'err_corrupt': "The file is corrupted or unreadable:",
        'err_no_data': "No valid topographic data was detected in the file.",
        'msg_pcd_found': "PCD file detected. Extracting boundaries...",
        'msg_pdf_ok': "The topographic plan was successfully generated:\n",
        'pdf_title_main': "Cartographic Survey of the Cavity",
        'pdf_dim': "Bounding box dimensions",
        'pdf_plan_xy': "X-Y Plane (Top view)",
        'pdf_plan_xz': "X-Z Plane (Front view)",
        'pdf_plan_yz': "Y-Z Plane (Side view)",
        'pdf_iso': "Isometric Projection",
        'lang': "EN"
    },
    'es': {
        'app_title': "Renderizado Topográfico VTopo (LABAC)",
        'viewer_title': "Intérprete Visual Topo (.tro)",
        'path_label': "Ruta del archivo topográfico (.tro):",
        'btn_browse': "Explorar",
        'btn_load': "Compilar Modelo 3D",
        'ctrl_title': "Controles del Modelo Topográfico",
        'lf_cam': "Orientación Axial y Exportación",
        'btn_iso': "Isométrico",
        'btn_xy': "Plano X-Y (Superior)",
        'btn_xz': "Plano X-Z (Frontal)",
        'btn_yz': "Plano Y-Z (Perfil)",
        'btn_pdf': "Generar PDF Topográfico",
        'lf_filters': "Filtros Geométricos",
        'btn_toggle_rad': "Ocultar/Mostrar Visuales Radiantes",
        'btn_toggle_pcd': "Ocultar/Mostrar Fronteras (PCD)",
        'lf_env': "Reconstrucción Superficial (Alpha-Shape)",
        'lbl_alpha': "Parámetro geométrico Alfa (Volumen):",
        'btn_gen_env': "Generar Envoltura VTopo",
        'btn_toggle_env': "Mostrar/Ocultar",
        'btn_close': "Cerrar Visor",
        'err_title': "Error",
        'err_not_found': "El archivo especificado no se encuentra.",
        'err_corrupt': "El archivo está corrupto o es ilegible:",
        'err_no_data': "No se detectaron datos topográficos válidos en el archivo.",
        'msg_pcd_found': "Archivo PCD detectado. Extrayendo fronteras...",
        'msg_pdf_ok': "El plano topográfico se generó con éxito:\n",
        'pdf_title_main': "Levantamiento Cartográfico de la Cavidad",
        'pdf_dim': "Dimensiones de la caja delimitadora",
        'pdf_plan_xy': "Plano X-Y (Vista superior)",
        'pdf_plan_xz': "Plano X-Z (Vista frontal)",
        'pdf_plan_yz': "Plano Y-Z (Vista lateral)",
        'pdf_iso': "Proyección Isométrica",
        'lang': "ES"
    }
}

def calculer_coordonnees_spheriques(origine, distance, azimut_deg, pente_deg):
    # Transformation des visées polaires locales en un repère global cartésien
    azimut_rad = math.radians(azimut_deg)
    pente_rad = math.radians(pente_deg)
    distance_horizontale = distance * math.cos(pente_rad)
    
    delta_x = distance_horizontale * math.sin(azimut_rad)
    delta_y = distance_horizontale * math.cos(azimut_rad)
    delta_z = distance * math.sin(pente_rad)
    
    return origine + np.array([delta_x, delta_y, delta_z])

def analyser_fichier_tro(chemin_fichier):
    # Parsing du fichier texte topographique formaté selon la norme Visual Topo
    stations = {}
    lignes_cheminement = []
    lignes_radiantes = []
    points_parois = []
    
    with open(chemin_fichier, 'r', encoding='utf-8', errors='replace') as fichier:
        lignes = fichier.readlines()
        
    for ligne in lignes:
        elements = ligne.strip().split()
        if len(elements) < 5 or elements[0].startswith(';') or elements[0] in ['Version', 'Club', 'Couleur', 'Param']:
            continue
            
        station_depart = elements[0]
        station_arrivee = elements[1]
        
        try:
            distance = float(elements[2])
            azimut = float(elements[3])
            pente = float(elements[4])
        except ValueError:
            continue
            
        if station_depart not in stations:
            stations[station_depart] = np.array([0.0, 0.0, 0.0])
            
        point_depart = stations[station_depart]
        
        if station_depart == station_arrivee:
            continue
            
        point_arrivee = calculer_coordonnees_spheriques(point_depart, distance, azimut, pente)
        
        if station_arrivee == '*':
            lignes_radiantes.append((point_depart, point_arrivee))
            points_parois.append(point_arrivee)
        else:
            stations[station_arrivee] = point_arrivee
            lignes_cheminement.append((point_depart, point_arrivee))
            
    return stations, lignes_cheminement, lignes_radiantes, points_parois

def construire_lignes_open3d(segments, couleur_rgb):
    # Génération des maillages filaires vectoriels pour le rendu matériel
    if not segments:
        return o3d.geometry.LineSet()
        
    sommets = []
    indices_lignes = []
    index_actuel = 0
    
    for pt_depart, pt_arrivee in segments:
        sommets.append(pt_depart)
        sommets.append(pt_arrivee)
        indices_lignes.append([index_actuel, index_actuel + 1])
        index_actuel += 2
        
    lineset = o3d.geometry.LineSet()
    lineset.points = o3d.utility.Vector3dVector(np.vstack(sommets))
    lineset.lines = o3d.utility.Vector2iVector(np.vstack(indices_lignes))
    lineset.colors = o3d.utility.Vector3dVector([couleur_rgb for _ in range(len(indices_lignes))])
    
    return lineset

class VisualiseurVTopo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = 'fr'
        self.geometry("650x280")
        self.configure(bg="#2d2d2d")
        self.protocol("WM_DELETE_WINDOW", self.fermer_application)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#2d2d2d", foreground="white", font=("Arial", 11))
        
        self.vis = None
        self.en_cours = False
        
        self.geometrie_cheminement = None
        self.geometrie_radiante = None
        self.geometrie_stations = None
        self.geometrie_enveloppe_vtopo = None
        self.geometrie_frontieres_pcd = None
        
        self.donnees_cheminement = []
        self.donnees_radiantes = []
        self.coordonnees_stations_array = np.empty((0, 3))
        self.points_parois_bruts = []
        self.points_pcd_bruts = np.empty((0, 3))
        
        self.afficher_radiantes = True
        self.afficher_enveloppe = False
        self.afficher_frontieres_pcd = True
        
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
        self.btn_browse = tk.Button(cadre_saisie, command=self.parcourir_fichier, bg="white", fg="black", highlightbackground="white")
        self.btn_browse.pack(side=tk.RIGHT)
        self.btn_load = tk.Button(self.cadre_selection, command=self.initialiser_moteur, bg="#00aaff", fg="black", highlightbackground="#00aaff", font=("Arial", 12, "bold"))
        self.btn_load.pack(fill=tk.X)

    def basculer_langue(self):
        langues = ['fr', 'en', 'es']
        idx = langues.index(self.lang)
        self.lang = langues[(idx + 1) % len(langues)]
        self.actualiser_textes_interface()

    def actualiser_textes_interface(self):
        # Synchronisation du référentiel textuel sur les éléments Tkinter
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
            self.title(t['ctrl_title'])
            self.lf_cam.config(text=t['lf_cam'])
            self.btn_iso.config(text=t['btn_iso'])
            self.btn_xy.config(text=t['btn_xy'])
            self.btn_xz.config(text=t['btn_xz'])
            self.btn_yz.config(text=t['btn_yz'])
            self.btn_pdf.config(text=t['btn_pdf'])
            
            self.lf_filters.config(text=t['lf_filters'])
            self.btn_toggle_rad.config(text=t['btn_toggle_rad'])
            if hasattr(self, 'btn_toggle_pcd') and self.btn_toggle_pcd.winfo_exists():
                self.btn_toggle_pcd.config(text=t['btn_toggle_pcd'])
            
            self.lf_env.config(text=t['lf_env'])
            self.lbl_alpha.config(text=t['lbl_alpha'])
            self.btn_gen_env.config(text=t['btn_gen_env'])
            self.btn_toggle_env.config(text=t['btn_toggle_env'])
            
            self.btn_close.config(text=t['btn_close'])

    def parcourir_fichier(self):
        chemin_initial = str(Path.home() / "Desktop")
        fichier = filedialog.askopenfilename(initialdir=chemin_initial, filetypes=[("Fichiers TRO", "*.tro"), ("Tous les fichiers", "*.*")])
        if fichier:
            self.variable_chemin.set(fichier)

    def initialiser_moteur(self):
        t = TR[self.lang]
        chemin_tro = self.variable_chemin.get()
        if not chemin_tro or not Path(chemin_tro).exists():
            messagebox.showerror(t['err_title'], t['err_not_found'])
            return
            
        try:
            stations, cheminement, radiantes, parois = analyser_fichier_tro(chemin_tro)
            self.donnees_cheminement = cheminement
            self.donnees_radiantes = radiantes
            self.points_parois_bruts = parois
            self.coordonnees_stations_array = np.vstack(list(stations.values())) if stations else np.empty((0, 3))
        except Exception as e:
            messagebox.showerror(t['err_title'], f"{t['err_corrupt']} {e}")
            return
            
        if not stations:
            messagebox.showerror(t['err_title'], t['err_no_data'])
            return

        self.geometrie_cheminement = construire_lignes_open3d(cheminement, [0.0, 0.7, 1.0])
        self.geometrie_radiante = construire_lignes_open3d(radiantes, [0.3, 0.3, 0.3])
        
        self.geometrie_stations = o3d.geometry.PointCloud()
        self.geometrie_stations.points = o3d.utility.Vector3dVector(self.coordonnees_stations_array)
        self.geometrie_stations.paint_uniform_color([1.0, 0.2, 0.2])
        
        # Inspection et extraction conditionnelle du nuage de points lourd (PCD)
        chemin_pcd = Path(chemin_tro).with_suffix('.pcd')
        if chemin_pcd.exists():
            print(t['msg_pcd_found'])
            try:
                nuage_brut = o3d.io.read_point_cloud(str(chemin_pcd))
                # Allègement du nuage pour prévenir la saturation de l'algorithme d'Alpha-Shape
                nuage_echantillon = nuage_brut.voxel_down_sample(voxel_size=0.5)
                self.points_pcd_bruts = np.asarray(nuage_echantillon.points)
                
                # Construction vectorielle des frontières géométriques
                maillage_pcd = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(nuage_echantillon, 2.0)
                self.geometrie_frontieres_pcd = o3d.geometry.LineSet.create_from_triangle_mesh(maillage_pcd)
                self.geometrie_frontieres_pcd.paint_uniform_color([0.2, 0.8, 0.2]) # Vert topo
            except Exception as e:
                print(f"Avertissement lors de l'extraction des frontières PCD : {e}")
                self.geometrie_frontieres_pcd = None
        else:
            self.geometrie_frontieres_pcd = None
            self.points_pcd_bruts = np.empty((0, 3))

        self.cadre_selection.pack_forget()
        self.construire_interface_controle()
        self.actualiser_textes_interface()
        
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(window_name=f"Topographie : {Path(chemin_tro).name}", width=1400, height=900, left=480, top=50)
        
        self.vis.add_geometry(self.geometrie_cheminement)
        self.vis.add_geometry(self.geometrie_radiante)
        self.vis.add_geometry(self.geometrie_stations)
        
        if self.geometrie_frontieres_pcd is not None:
            self.vis.add_geometry(self.geometrie_frontieres_pcd)
        
        options = self.vis.get_render_option()
        options.background_color = np.asarray([0.02, 0.02, 0.02])
        options.line_width = 2.0
        options.point_size = 5.0
        
        self.en_cours = True
        self.boucle_rendu()

    def construire_interface_controle(self):
        self.geometry("450x550")
        
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
        
        self.btn_pdf = tk.Button(self.lf_cam, command=self.exporter_pdf_topographique, bg="#8e44ad", fg="black", highlightbackground="#8e44ad", font=("Arial", 10, "bold"))
        self.btn_pdf.pack(fill=tk.X, padx=5, pady=(5, 0))

        self.lf_filters = tk.LabelFrame(cadre_principal, bg="#2d2d2d", fg="#00aaff", font=("Arial", 10, "bold"))
        self.lf_filters.pack(fill=tk.X, pady=(5, 10), ipady=5, ipadx=5)
        self.btn_toggle_rad = tk.Button(self.lf_filters, command=self.basculer_radiantes, bg="#00aaff", fg="black", highlightbackground="#00aaff", font=("Arial", 10, "bold"))
        self.btn_toggle_rad.pack(fill=tk.X, padx=5, pady=5)
        
        # Injection conditionnelle du bouton de contrôle des frontières selon l'existence du nuage de points PCD
        if self.geometrie_frontieres_pcd is not None:
            self.btn_toggle_pcd = tk.Button(self.lf_filters, command=self.basculer_frontieres_pcd, bg="#2ecc71", fg="black", highlightbackground="#2ecc71", font=("Arial", 10, "bold"))
            self.btn_toggle_pcd.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.lf_env = tk.LabelFrame(cadre_principal, bg="#2d2d2d", fg="#2ecc71", font=("Arial", 10, "bold"))
        self.lf_env.pack(fill=tk.X, pady=(5, 15), ipady=5, ipadx=5)
        
        self.lbl_alpha = ttk.Label(self.lf_env)
        self.lbl_alpha.pack(anchor=tk.W, padx=5)
        self.variable_alpha = tk.DoubleVar(value=2.5)
        ttk.Scale(self.lf_env, from_=0.1, to=20.0, orient=tk.HORIZONTAL, variable=self.variable_alpha).pack(fill=tk.X, padx=5, pady=(0, 5))
        
        cadre_btn_env = tk.Frame(self.lf_env, bg="#2d2d2d")
        cadre_btn_env.pack(fill=tk.X, padx=5, pady=5)
        self.btn_gen_env = tk.Button(cadre_btn_env, command=self.calculer_enveloppe_vtopo, bg="#27ae60", fg="black", highlightbackground="#27ae60", font=("Arial", 10, "bold"))
        self.btn_gen_env.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.btn_toggle_env = tk.Button(cadre_btn_env, command=self.basculer_enveloppe, bg="#f39c12", fg="black", highlightbackground="#f39c12", font=("Arial", 10, "bold"))
        self.btn_toggle_env.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        self.btn_close = tk.Button(cadre_principal, command=self.fermer_application, bg="#ff4444", fg="black", highlightbackground="#ff4444", font=("Arial", 12, "bold"))
        self.btn_close.pack(side=tk.BOTTOM, fill=tk.X)

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

    def basculer_radiantes(self):
        if not self.vis or self.geometrie_radiante is None:
            return
        self.afficher_radiantes = not self.afficher_radiantes
        if self.afficher_radiantes:
            self.vis.add_geometry(self.geometrie_radiante, reset_bounding_box=False)
        else:
            self.vis.remove_geometry(self.geometrie_radiante, reset_bounding_box=False)

    def basculer_frontieres_pcd(self):
        if not self.vis or self.geometrie_frontieres_pcd is None:
            return
        self.afficher_frontieres_pcd = not self.afficher_frontieres_pcd
        if self.afficher_frontieres_pcd:
            self.vis.add_geometry(self.geometrie_frontieres_pcd, reset_bounding_box=False)
        else:
            self.vis.remove_geometry(self.geometrie_frontieres_pcd, reset_bounding_box=False)

    def calculer_enveloppe_vtopo(self):
        if not self.vis or len(self.points_parois_bruts) < 4:
            return
            
        if self.geometrie_enveloppe_vtopo is not None:
            self.vis.remove_geometry(self.geometrie_enveloppe_vtopo, reset_bounding_box=False)
            
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.vstack(self.points_parois_bruts))
        alpha = self.variable_alpha.get()
        
        try:
            maillage = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)
            maillage.compute_vertex_normals()
            maillage.paint_uniform_color([0.6, 0.55, 0.5])
            
            self.geometrie_enveloppe_vtopo = maillage
            self.afficher_enveloppe = True
            self.vis.add_geometry(self.geometrie_enveloppe_vtopo, reset_bounding_box=False)
        except Exception as e:
            print(f"Erreur lors du maillage : {e}")

    def basculer_enveloppe(self):
        if not self.vis or self.geometrie_enveloppe_vtopo is None:
            return
        self.afficher_enveloppe = not self.afficher_enveloppe
        if self.afficher_enveloppe:
            self.vis.add_geometry(self.geometrie_enveloppe_vtopo, reset_bounding_box=False)
        else:
            self.vis.remove_geometry(self.geometrie_enveloppe_vtopo, reset_bounding_box=False)

    def exporter_pdf_topographique(self):
        t = TR[self.lang]
        if self.coordonnees_stations_array.size == 0:
            return
            
        dossier_cible = Path(self.variable_chemin.get())
        nom_grotte = dossier_cible.stem
        chemin_export = dossier_cible.parent / f"Rapport_VTopo_{nom_grotte}.pdf"

        # Établissement de la boîte englobante pour le titre cartographique
        tous_points = np.vstack([self.coordonnees_stations_array])
        if len(self.points_parois_bruts) > 0:
            tous_points = np.vstack([tous_points, np.vstack(self.points_parois_bruts)])
        if self.points_pcd_bruts.size > 0:
            tous_points = np.vstack([tous_points, self.points_pcd_bruts])

        xmin, ymin, zmin = np.min(tous_points, axis=0)
        xmax, ymax, zmax = np.max(tous_points, axis=0)
        dimensions = [xmax - xmin, ymax - ymin, zmax - zmin]

        try:
            with PdfPages(chemin_export) as pdf:
                def dessiner_page(axes_idx, titre, xlabel, ylabel, is_iso=False):
                    fig, ax = plt.subplots(figsize=(11.69, 8.27))
                    fig.suptitle(f"{t['pdf_title_main']} : {nom_grotte}\n{t['pdf_dim']} (X, Y, Z) : {dimensions[0]:.1f}m x {dimensions[1]:.1f}m x {dimensions[2]:.1f}m", fontsize=14, fontweight='bold')

                    rot_iso = R.from_euler('x', 35.264, degrees=True) * R.from_euler('y', 45, degrees=True) if is_iso else None

                    # Rendu conditionnel des contours extraits du PCD
                    if self.points_pcd_bruts.size > 0:
                        pts_pcd_proj = rot_iso.apply(self.points_pcd_bruts)[:, [0, 1]] if is_iso else self.points_pcd_bruts[:, axes_idx]
                        pmin_x, pmax_x = np.min(pts_pcd_proj[:, 0]), np.max(pts_pcd_proj[:, 0])
                        pmin_y, pmax_y = np.min(pts_pcd_proj[:, 1]), np.max(pts_pcd_proj[:, 1])
                        dx, dy = (pmax_x - pmin_x) * 0.05, (pmax_y - pmin_y) * 0.05
                        
                        bins = 1000
                        H, xedges, yedges = np.histogram2d(pts_pcd_proj[:, 0], pts_pcd_proj[:, 1], bins=bins, range=[[pmin_x - dx, pmax_x + dx], [pmin_y - dy, pmax_y + dy]])
                        Z_mask = (H.T > 0).astype(float)
                        Z_smooth = gaussian_filter(Z_mask, sigma=0.5)
                        X, Y = np.meshgrid((xedges[:-1] + xedges[1:]) / 2, (yedges[:-1] + yedges[1:]) / 2)
                        
                        ax.contour(X, Y, Z_smooth, levels=[0.1], colors='#2ecc71', linewidths=1.0, alpha=0.6)

                    # Superposition géométrique vectorisée : Radiantes
                    for pt1, pt2 in self.donnees_radiantes:
                        p1 = rot_iso.apply(pt1)[[0, 1]] if is_iso else pt1[axes_idx]
                        p2 = rot_iso.apply(pt2)[[0, 1]] if is_iso else pt2[axes_idx]
                        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#95a5a6', linewidth=0.5, alpha=0.7)

                    # Superposition géométrique vectorisée : Cheminement odométrique
                    for pt1, pt2 in self.donnees_cheminement:
                        p1 = rot_iso.apply(pt1)[[0, 1]] if is_iso else pt1[axes_idx]
                        p2 = rot_iso.apply(pt2)[[0, 1]] if is_iso else pt2[axes_idx]
                        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#2980b9', linewidth=2.0)

                    # Superposition géométrique vectorisée : Points de Station
                    pts_stat_proj = rot_iso.apply(self.coordonnees_stations_array)[:, [0, 1]] if is_iso else self.coordonnees_stations_array[:, axes_idx]
                    ax.scatter(pts_stat_proj[:, 0], pts_stat_proj[:, 1], color='#e74c3c', s=20, zorder=5)

                    ax.set_title(titre, fontsize=12, fontweight='bold')
                    ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
                    ax.axis('equal')
                    ax.grid(True, linestyle='--', alpha=0.5)

                    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
                    pdf.savefig(fig)
                    plt.close(fig)

                dessiner_page([0, 1], t['pdf_plan_xy'], "Axe X (m)", "Axe Y (m)")
                dessiner_page([0, 2], t['pdf_plan_xz'], "Axe X (m)", "Axe Z (m)")
                dessiner_page([1, 2], t['pdf_plan_yz'], "Axe Y (m)", "Axe Z (m)")
                dessiner_page(None, t['pdf_iso'], "Axe Projeté X' (m)", "Axe Projeté Y' (m)", is_iso=True)
                
            messagebox.showinfo("Exportation Réussie", f"{t['msg_pdf_ok']}{chemin_export}")
        except Exception as e:
            messagebox.showerror("Erreur d'exportation PDF", f"Impossible de compiler le registre cartographique :\n{e}")

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
    app = VisualiseurVTopo()
    app.mainloop()