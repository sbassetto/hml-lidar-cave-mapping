import os
import numpy as np
from pathlib import Path
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore

# --- CONFIGURATION ---
BAG_PATH_STR = 'cave_bag_2026-04-19_21-28-59_result'
OUTPUT_PLY = 'grotte_complete.ply'

def get_points_from_pc2(msg):
    """ Décode le format binaire PointCloud2 en coordonnées XYZ """
    # On convertit les données brutes en buffer numpy
    data = np.frombuffer(msg.data, dtype=np.uint8)
    # On reshape en ignorant les champs d'intensité/couleur pour ne garder que XYZ (float32)
    # Le point_step est généralement de 32 octets pour le Mid360 (x,y,z,intensity,tag,line,timestamp)
    points = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)[:, :3]
    # On filtre les points invalides (NaN)
    return points[np.isfinite(points).all(axis=1)]

def write_ply(filename, points):
    """ Écrit un fichier PLY ASCII simple """
    header = f"""ply
format ascii 1.0
element vertex {len(points)}
property float x
property float y
property float z
end_header
"""
    with open(filename, 'w') as f:
        f.write(header)
        for p in points:
            f.write(f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n")

def main():
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    bag_path = Path(BAG_PATH_STR)
    all_points = []

    if not bag_path.exists():
        print(f"❌ Erreur : Le dossier {BAG_PATH_STR} est introuvable.")
        return

    print(f"--- 1. Extraction du nuage de points depuis le bag ---")
    
    with AnyReader([bag_path]) as reader:
        # On cible uniquement le nuage de points traité
        connections = [x for x in reader.connections if x.topic == '/kf_cloud']
        
        if not connections:
            print("⚠️ Topic /kf_cloud non trouvé. Vérifie le nom du topic.")
            return

        for connection, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, connection.msgtype, typestore=typestore)
            points = get_points_from_pc2(msg)
            all_points.append(points)

    if not all_points:
        print("❌ Aucune donnée trouvée.")
        return

    # Fusion de tous les segments
    full_cloud = np.vstack(all_points)
    
    print(f"--- 2. Écriture du fichier {OUTPUT_PLY} ({len(full_cloud)} points) ---")
    write_ply(OUTPUT_PLY, full_cloud)
    print("✅ Conversion terminée !")

if __name__ == "__main__":
    main()