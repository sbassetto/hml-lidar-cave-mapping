# Fichier : ExtracteurTopographique.py
import sys
import math
import numpy as np
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore
from scipy.spatial import cKDTree

# --- CONFIGURATION ---
SIMPLIFY_DIST = 1.5   # Distance entre chaque station de cheminement
NUM_SPLAYS = 10       # Nombre de secteurs pour les visées radiantes
EPAISSEUR_TRANCHE = 1.0 # Épaisseur de la coupe perpendiculaire en mètres
RAYON_MAX = 70.0      # Rayon de sécurité d'extraction locale de la galerie (scan max du Lidar)

def afficher_progression(actuel, total, prefixe='', longueur=50):
    if total == 0:
        return
    pourcentage = f"{100 * (actuel / float(total)):.1f}"
    rempli = int(longueur * actuel // total)
    barre = '█' * rempli + '-' * (longueur - rempli)
    sys.stdout.write(f'\r{prefixe} |{barre}| {pourcentage}% ({actuel}/{total})')
    sys.stdout.flush()
    if actuel == total:
        sys.stdout.write('\n')

def get_points_from_pc2(msg):
    data = np.frombuffer(msg.data, dtype=np.uint8)
    points = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)[:, :3]
    return points[np.isfinite(points).all(axis=1)]

def bag_to_vtopo(chemin_absolu_bag):
    # Génération du fichier topographique de sortie dans le même répertoire que le script
    chemin_source = Path(chemin_absolu_bag)
    output_filename = f"{chemin_source.name}.tro"
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    raw_trajectory = []
    all_pc_points = []
    
    if not chemin_source.exists():
        print(f"Erreur : Dossier introuvable : {chemin_source}")
        return

    try:
        with AnyReader([chemin_source], default_typestore=typestore) as reader:
            conns = [x for x in reader.connections if x.topic in ['/path', '/kf_cloud']]
            
            total_messages = sum(conn.msgcount for conn in conns)
            if total_messages == 0:
                print("Erreur : Aucun message trouvé pour l'odométrie ou les nuages de points.")
                return

            print(f"Début de l'extraction de {total_messages} messages depuis le bag...")
            messages_traites = 0
            
            for connection, timestamp, rawdata in reader.messages(connections=conns):
                msg = reader.deserialize(rawdata, connection.msgtype)
                
                if connection.topic == '/path' and hasattr(msg, 'poses') and len(msg.poses) > 0:
                    p = msg.poses[-1].pose.position
                    raw_trajectory.append([p.x, p.y, p.z])
                
                if connection.topic == '/kf_cloud':
                    all_pc_points.append(get_points_from_pc2(msg))
                
                messages_traites += 1
                afficher_progression(messages_traites, total_messages, prefixe="Lecture  ")
                
    except Exception as e:
        print(f"\nErreur de lecture du bag : {e}")
        return

    if not raw_trajectory or not all_pc_points:
        return

    print("Fusion des nuages et construction de l'arbre spatial k-d (patienter)...")
    full_cloud = np.vstack(all_pc_points)
    tree = cKDTree(full_cloud)

    stations = [np.array(raw_trajectory[0])]
    for p_list in raw_trajectory:
        p = np.array(p_list)
        if np.linalg.norm(p - stations[-1]) >= SIMPLIFY_DIST:
            stations.append(p)

    total_stations = len(stations) - 1
    print(f"Génération géométrique de {total_stations} stations topographiques...")

    with open(output_filename, 'w') as f:
        f.write("Version 5.02\n\n; Généré pour le projet Cave Explorer\n")
        f.write("Club SB TJ\nCouleur 0,0,0\n")
        f.write("Param Deca Degd Clino Degd 0.0 Dir,Dir,Dir Arr Inc 0,0,0\n\n")
        f.write("SB_00 SB_00 0.00 0.00 0.00 1.00 1.00 1.00 1.00 N I *\n")

        for i in range(total_stations):
            s1 = stations[i]
            s2 = stations[i+1]
            diff = s2 - s1
            dist = np.linalg.norm(diff)
            direction = diff / dist
            
            azi = (450 - math.degrees(math.atan2(diff[1], diff[0]))) % 360
            pente = math.degrees(math.asin(diff[2] / dist))

            idx_nearby = tree.query_ball_point(s1, RAYON_MAX)
            
            if len(idx_nearby) > 0:
                local_pts_bruts = full_cloud[idx_nearby] - s1
                
                projections_axe = np.dot(local_pts_bruts, direction)
                tranche_mask = np.abs(projections_axe) < (EPAISSEUR_TRANCHE / 2.0)
                tranche_pts = local_pts_bruts[tranche_mask]
                
                if len(tranche_pts) > 0:
                    axe_z = np.array([0, 0, 1])
                    droite = np.cross(direction, axe_z)
                    if np.linalg.norm(droite) < 1e-6:
                        droite = np.array([1, 0, 0])
                    droite = droite / np.linalg.norm(droite)
                    haut = np.cross(droite, direction)
                    haut = haut / np.linalg.norm(haut)
                    
                    x_2d = np.dot(tranche_pts, droite)
                    y_2d = np.dot(tranche_pts, haut)
                    distances_rad = np.sqrt(x_2d**2 + y_2d**2)
                    angles_rad = np.arctan2(y_2d, x_2d)
                    
                    tol = math.radians(20)
                    m_right = np.abs(angles_rad) < tol
                    m_up    = np.abs(angles_rad - math.pi/2) < tol
                    m_left  = np.abs(np.abs(angles_rad) - math.pi) < tol
                    m_down  = np.abs(angles_rad + math.pi/2) < tol
                    
                    right = np.percentile(distances_rad[m_right], 5) if any(m_right) else 1.0
                    up    = np.percentile(distances_rad[m_up], 5) if any(m_up) else 1.0
                    left  = np.percentile(distances_rad[m_left], 5) if any(m_left) else 1.0
                    down  = np.percentile(distances_rad[m_down], 5) if any(m_down) else 1.0
                    
                    f.write(f"SB_{i:02d} SB_{i+1:02d} {dist:.2f} {azi:.1f} {pente:.1f} {up:.2f} {down:.2f} {left:.2f} {right:.2f} N I *\n")
                    
                    secteur_angle = (2 * math.pi) / NUM_SPLAYS
                    for k in range(NUM_SPLAYS):
                        angle_cible = -math.pi + k * secteur_angle
                        
                        diff_angle = np.abs(angles_rad - angle_cible)
                        diff_angle = np.minimum(diff_angle, 2 * math.pi - diff_angle)
                        m_sec = diff_angle < (secteur_angle / 2.0)
                        
                        if any(m_sec):
                            pts_sec = tranche_pts[m_sec]
                            dist_sec = distances_rad[m_sec]
                            idx_rep = np.argsort(dist_sec)[max(0, int(len(dist_sec)*0.05))]
                            pt_splay = pts_sec[idx_rep]
                            d_sp = np.linalg.norm(pt_splay)
                            
                            if d_sp >= 0.2:
                                azi_sp = (450 - math.degrees(math.atan2(pt_splay[1], pt_splay[0]))) % 360
                                pente_sp = math.degrees(math.asin(pt_splay[2] / d_sp))
                                f.write(f"SB_{i:02d} * {d_sp:.2f} {azi_sp:.1f} {pente_sp:.1f} * * * * N E M\n")
                else:
                    f.write(f"SB_{i:02d} SB_{i+1:02d} {dist:.2f} {azi:.1f} {pente:.1f} 1.00 1.00 1.00 1.00 N I *\n")
            else:
                f.write(f"SB_{i:02d} SB_{i+1:02d} {dist:.2f} {azi:.1f} {pente:.1f} 1.00 1.00 1.00 1.00 N I *\n")
            
            afficher_progression(i + 1, total_stations, prefixe="Calculs  ")

    print(f"Export VTopo finalisé : {output_filename}")

if __name__ == "__main__":
    # Déploiement silencieux d'une fenêtre de sélection Tkinter sans afficher le root
    root = tk.Tk()
    root.withdraw()
    
    # Pointage initial sur l'arborescence des résultats d'expédition
    chemin_initial = str(Path.home() / "Desktop" / "Expedition_Data" / "ros2_ws" / "results")
    dossier_selectionne = filedialog.askdirectory(initialdir=chemin_initial, title="Sélectionnez l'archive ROS 2 à extraire (.db3)")
    
    if not dossier_selectionne:
        print("Opération annulée. Aucun répertoire sélectionné.")
        sys.exit(0)
        
    print(f"Traitement par tranche perpendiculaire sur : {dossier_selectionne}")
    bag_to_vtopo(dossier_selectionne)