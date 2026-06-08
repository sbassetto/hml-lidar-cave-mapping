import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import sensor_msgs_py.point_cloud2 as pc2
import os

def main():
    # === CONFIGURATION DES CHEMINS ===
    # /!\ METS ICI LE CHEMIN DE TON DOSSIER BAG (PAS LE .db3 DIRECTEMENT)
    bag_path = '/root/ros2_ws/results/output_bag' 
    output_pcd = '/root/ros2_ws/results/output_bag/grotte_complete.pcd'
    topic_name = '/kf_cloud'
    
    serialization_format = 'cdr'
    storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id='sqlite3')
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format=serialization_format,
        output_serialization_format=serialization_format)

    reader = rosbag2_py.SequentialReader()
    reader.open(storage_options, converter_options)

    topic_types = reader.get_all_topics_and_types()
    type_map = {topic.name: topic.type for topic in topic_types}

    if topic_name not in type_map:
        print(f"Erreur : Le topic {topic_name} n'est pas dans le bag.")
        return

    msg_type = get_message(type_map[topic_name])
    all_points = []

    print("Extraction et fusion des points en cours (patienter)...")
    while reader.has_next():
        (topic, data, t) = reader.read_next()
        if topic == topic_name:
            msg = deserialize_message(data, msg_type)
            # Extraction des champs x, y, z et intensité
            for p in pc2.read_points(msg, field_names=("x", "y", "z", "intensity"), skip_nans=True):
                all_points.append(p)

    num_points = len(all_points)
    print(f"Nombre total de points récupérés : {num_points}")

    if num_points == 0:
        print("Aucun point trouvé.")
        return

    print(f"Écriture du fichier : {output_pcd}...")
    with open(output_pcd, 'w') as f:
        f.write("# .PCD v0.7 - Point Cloud Data file format\n")
        f.write("VERSION 0.7\n")
        f.write("FIELDS x y z intensity\n")
        f.write("SIZE 4 4 4 4\n")
        f.write("TYPE F F F F\n")
        f.write("COUNT 1 1 1 1\n")
        f.write(f"WIDTH {num_points}\n")
        f.write("HEIGHT 1\n")
        f.write("VIEWPOINT 0 0 0 1 0 0 0\n")
        f.write(f"POINTS {num_points}\n")
        f.write("DATA ascii\n")
        for p in all_points:
            f.write(f"{p[0]} {p[1]} {p[2]} {p[3]}\n")
            
    print("Extraction terminée avec succès !")

if __name__ == '__main__':
    main()
