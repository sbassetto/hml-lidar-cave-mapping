# HML-LiDAR RevA
# Cet outil réalise une récupération opérateur-guidée après divergence DLIO.
# Il ne modifie pas les paramètres de DLIO "en cours de route".
# Il prépare un nouveau bag brut avec un court intervalle stationnaire synthétique
# afin de permettre une nouvelle initialisation lors du retraitement.

# Fichier : EditeurTemporel_ZUPT.py
import os
import shutil
import threading
import webbrowser
import socket
import numpy as np
import open3d as o3d
from pathlib import Path
import flask
from werkzeug.serving import make_server
from rosbags.highlevel import AnyReader
from rosbags.rosbag2 import Writer
from rosbags.typesys import Stores, get_typestore
from collections import deque
import traceback

TAILLE_VOXEL_PREVISUALISATION = 0.05


def trouver_port_libre():
    """Retourne un port TCP local libre pour le serveur WebGL temporaire."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]



class ServeurMontageZUPT(threading.Thread):
    def __init__(self, chemin_bag_traite, chemin_bag_raw):
        threading.Thread.__init__(self)
        self.chemin_bag_traite = Path(chemin_bag_traite)
        self.chemin_bag_raw = Path(chemin_bag_raw)
        
        self.temps_debut_hw_ns = None
        self.duree_totale_sec = 0
        self.geometrie_temporelle = {}
        
        self.app = flask.Flask(__name__)
        self.port = trouver_port_libre()
        self.serveur = make_server('127.0.0.1', self.port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        self._preparer_donnees_visuelles()
        self._configurer_routes()

    def _preparer_donnees_visuelles(self):
        print(f"Indexation matérielle de l'archive post-traitée : {self.chemin_bag_traite.name}...")
        typestore = get_typestore(Stores.ROS2_HUMBLE)
        chemin_db3 = list(self.chemin_bag_traite.glob("*.db3"))[0]
        blocs_bruts = {}
        
        with AnyReader([chemin_db3], default_typestore=typestore) as reader:
            conns = [x for x in reader.connections if x.topic == '/kf_cloud']
            
            for connection, timestamp, rawdata in reader.messages(connections=conns):
                msg = reader.deserialize(rawdata, connection.msgtype)
                
                hw_ns = msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec
                
                if self.temps_debut_hw_ns is None:
                    self.temps_debut_hw_ns = hw_ns
                    
                t_relatif = (hw_ns - self.temps_debut_hw_ns) / 1e9
                self.duree_totale_sec = max(self.duree_totale_sec, t_relatif)
                
                index_sec = int(t_relatif)
                data = np.frombuffer(msg.data, dtype=np.uint8)
                pts = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)
                pts_valides = pts[np.isfinite(pts[:, :3]).all(axis=1)][:, :3]
                
                if index_sec not in blocs_bruts:
                    blocs_bruts[index_sec] = []
                blocs_bruts[index_sec].append(pts_valides)
                
        print("Décimation géométrique pour le serveur WebGL...")
        for sec, listes_pts in blocs_bruts.items():
            nuage = o3d.geometry.PointCloud()
            nuage.points = o3d.utility.Vector3dVector(np.vstack(listes_pts))
            nuage_decime = nuage.voxel_down_sample(TAILLE_VOXEL_PREVISUALISATION)
            if len(nuage_decime.points) > 0:
                self.geometrie_temporelle[sec] = np.asarray(nuage_decime.points).flatten().tolist()

    def _configurer_routes(self):
        @self.app.route('/')
        def index():
            return """
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Outil de Calibration ZUPT Intégré</title>
                <style>
                    body { margin: 0; overflow: hidden; background-color: #050505; color: white; font-family: sans-serif; }
                    #canvas-container { width: 100vw; height: 100vh; }
                    #ui-panel { position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(20,20,20,0.95); padding: 20px; border: 1px solid #444; border-radius: 8px; z-index: 100; width: 600px; display: flex; flex-direction: column; gap: 15px; }
                    #info-panel { position: absolute; top: 20px; left: 20px; background: rgba(20,20,20,0.95); padding: 15px; border: 1px solid #444; border-radius: 8px; z-index: 100; width: 320px; box-shadow: 0 4px 6px rgba(0,0,0,0.5); }
                    .controle-ligne { display: flex; align-items: center; justify-content: space-between; gap: 15px; }
                    .slider-container { flex-grow: 1; display: flex; flex-direction: column; }
                    input[type=range] { width: 100%; margin: 10px 0; }
                    .btn { padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px; transition: background 0.2s; }
                    .btn-play { background: #007BFF; color: white; }
                    .btn-play:hover { background: #0056b3; }
                    .btn-couper { background: #dc3545; color: white; font-size: 14px; padding: 12px; width: 100%; box-sizing: border-box; }
                    .btn-couper:hover { background: #a71d2a; }
                    label { font-size: 12px; color: #ccc; }
                    .valeur-temps { font-family: monospace; font-size: 16px; font-weight: bold; color: #00aaff; }
                </style>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            </head>
            <body>
                <div id="info-panel">
                    <h4 style="margin:0 0 15px 0; color:#aaa; text-transform:uppercase; border-bottom: 1px solid #333; padding-bottom: 8px;">Fichiers Actifs</h4>
                    <div style="font-size:12px; color:#ddd; line-height:1.5; margin-bottom:20px;">
                        <strong style="color:#888;">Archive visuelle (Post-traitée) :</strong><br>
                        <span id="nom-traite" style="color:#00aaff; word-wrap:break-word; font-family:monospace;">Chargement...</span><br><br>
                        <strong style="color:#888;">Archive source (Brute) :</strong><br>
                        <span id="nom-raw" style="color:#ffaa00; word-wrap:break-word; font-family:monospace;">Chargement...</span>
                    </div>
                    <button class="btn btn-couper" onclick="exporterZUPT()">🛠️ SCINDER & INSÉRER ZUPT</button>
                </div>
                <div id="ui-panel">
                    <div class="controle-ligne">
                        <div style="display:flex; flex-direction:column;">
                            <label>Fenêtre (s)</label>
                            <input type="number" id="fenetre" value="30" min="1" max="120" style="width:60px; background:#222; color:white; border:1px solid #555; padding:5px;">
                        </div>
                        <button class="btn btn-play" id="btn-play" onclick="togglePlay()">Lecture</button>
                        <div class="slider-container">
                            <label>Progression de l'odométrie</label>
                            <input type="range" id="timeline" min="0" value="0" step="1" oninput="majTempsManuel()">
                        </div>
                        <div class="valeur-temps" id="affichage-temps">0.0 s</div>
                    </div>
                </div>
                <div id="canvas-container"></div>
                <script>
                    let scene, camera, renderer, controleurVue;
                    let dureeTotale = 0, tempsCourant = 0, enLecture = false, intervalleLecture;
                    let blocsGeometrie = {}, pointsMateriel;

                    async function initialiser() {
                        scene = new THREE.Scene();
                        camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
                        renderer = new THREE.WebGLRenderer({ antialias: true });
                        renderer.setSize(window.innerWidth, window.innerHeight);
                        document.getElementById('canvas-container').appendChild(renderer.domElement);
                        controleurVue = new THREE.OrbitControls(camera, renderer.domElement);
                        pointsMateriel = new THREE.PointsMaterial({ color: 0x00aaff, size: 0.15 });

                        // Récupération dynamique des métadonnées incluant les noms de fichiers
                        const repMeta = await fetch('/metadata');
                        const meta = await repMeta.json();
                        
                        dureeTotale = meta.duree;
                        document.getElementById('timeline').max = Math.floor(dureeTotale);
                        document.getElementById('nom-traite').innerText = meta.nom_traite;
                        document.getElementById('nom-raw').innerText = meta.nom_raw;

                        const repGeo = await fetch('/geometrie');
                        const donnees = await repGeo.json();
                        for (const [sec, coords] of Object.entries(donnees)) {
                            const geo = new THREE.BufferGeometry();
                            geo.setAttribute('position', new THREE.Float32BufferAttribute(coords, 3));
                            const nuage = new THREE.Points(geo, pointsMateriel);
                            nuage.visible = false;
                            scene.add(nuage);
                            blocsGeometrie[parseInt(sec)] = nuage;
                        }
                        camera.position.set(10, 10, 20);
                        
                        document.getElementById('fenetre').addEventListener('input', actualiserVisibilite);
                        actualiserVisibilite();
                        animer();
                    }

                    function actualiserVisibilite() {
                        const fenetre = parseInt(document.getElementById('fenetre').value) || 30;
                        const borneMin = Math.max(0, Math.floor(tempsCourant - fenetre));
                        const borneMax = Math.floor(tempsCourant);
                        let centreCalcul = new THREE.Vector3();
                        let pointsActifs = 0;

                        for (const [sec, nuage] of Object.entries(blocsGeometrie)) {
                            const s = parseInt(sec);
                            if (s >= borneMin && s <= borneMax) {
                                nuage.visible = true;
                                nuage.geometry.computeBoundingSphere();
                                if(nuage.geometry.boundingSphere) {
                                    centreCalcul.add(nuage.geometry.boundingSphere.center);
                                    pointsActifs++;
                                }
                            } else {
                                nuage.visible = false;
                            }
                        }
                        
                        if(pointsActifs > 0 && enLecture) {
                            centreCalcul.divideScalar(pointsActifs);
                            controleurVue.target.lerp(centreCalcul, 0.05);
                        }
                        document.getElementById('affichage-temps').innerText = tempsCourant.toFixed(1) + ' s';
                    }

                    function majTempsManuel() {
                        tempsCourant = parseFloat(document.getElementById('timeline').value);
                        actualiserVisibilite();
                    }

                    function togglePlay() {
                        enLecture = !enLecture;
                        const btn = document.getElementById('btn-play');
                        if (enLecture) {
                            btn.innerText = "Pause";
                            intervalleLecture = setInterval(() => {
                                tempsCourant += 0.5;
                                if (tempsCourant > dureeTotale) tempsCourant = dureeTotale;
                                document.getElementById('timeline').value = tempsCourant;
                                actualiserVisibilite();
                                if (tempsCourant >= dureeTotale) togglePlay();
                            }, 50);
                        } else {
                            btn.innerText = "Lecture";
                            clearInterval(intervalleLecture);
                        }
                    }

                    async function exporterZUPT() {
                        document.body.style.cursor = 'wait';
                        document.body.innerHTML = "<h2 style='text-align:center; margin-top:20%; color:#28a745;'>Création de l'archive corrigée en cours...<br>Le terminal Python confirmera la fin de l'opération.</h2>";
                        await fetch('/exporter', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ coupe: tempsCourant })
                        });
                    }

                    function animer() {
                        requestAnimationFrame(animer);
                        controleurVue.update();
                        renderer.render(scene, camera);
                    }
                    initialiser();
                </script>
            </body>
            </html>
            """

        @self.app.route('/metadata')
        def metadata():
            return flask.jsonify({
                'duree': self.duree_totale_sec,
                'nom_traite': self.chemin_bag_traite.name,
                'nom_raw': self.chemin_bag_raw.name
            })

        @self.app.route('/geometrie')
        def geometrie():
            return flask.jsonify(self.geometrie_temporelle)

        @self.app.route('/exporter', methods=['POST'])
        def exporter():
            coupe_sec = flask.request.json['coupe']
            threading.Thread(target=self._executer_scission_zupt, args=(coupe_sec,)).start()
            return flask.jsonify({"status": "succes"})

    def run(self):
        print("[Microservice WebGL] Prêt pour l'identification du point de rupture.")
        self.serveur.serve_forever()

    def _executer_scission_zupt(self, temps_relatif_sec):
        limite_hw_ns = self.temps_debut_hw_ns + int(temps_relatif_sec * 1e9)
        duree_calib_ns = int(5.0 * 1e9)
        
        dossier_parent = self.chemin_bag_raw.parent
        nom_base = self.chemin_bag_raw.name
        chemin_sortie = dossier_parent / f"{nom_base}_ZUPT_pret"
        
        if chemin_sortie.exists():
            shutil.rmtree(chemin_sortie)
            
        typestore = get_typestore(Stores.ROS2_HUMBLE)
        chemins_db3_raw = sorted(list(self.chemin_bag_raw.glob("*.db3")))
        
        print(f"\n1. Recherche du point de coupure absolu dans {len(chemins_db3_raw)} fragment(s) brut(s)...")
        record_time_cut = None
        tampon_imu = deque(maxlen=200)
        message_lidar_reference = None
        type_lidar_ref = None
        type_imu_ref = None
        
        ecrivain = None
        try:
            with AnyReader(chemins_db3_raw, default_typestore=typestore) as lecteur:
                for connexion, timestamp, rawdata in lecteur.messages():
                    if 'Imu' in connexion.msgtype or 'PointCloud2' in connexion.msgtype:
                        msg = lecteur.deserialize(rawdata, connexion.msgtype)
                        hw_ns = msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec
                        
                        if hw_ns >= limite_hw_ns:
                            record_time_cut = timestamp
                            break
                            
                        if 'Imu' in connexion.msgtype:
                            tampon_imu.append(msg)
                            type_imu_ref = connexion.msgtype
                        elif 'PointCloud2' in connexion.msgtype:
                            message_lidar_reference = msg
                            type_lidar_ref = connexion.msgtype
                            
            if record_time_cut is None or not tampon_imu:
                print("Erreur critique : Impossible d'atteindre la limite temporelle dans le fichier brut.")
                self.serveur.shutdown()
                
            msg_imu_gabarit = tampon_imu[-1]
            gravite_x = np.mean([m.linear_acceleration.x for m in tampon_imu])
            gravite_y = np.mean([m.linear_acceleration.y for m in tampon_imu])
            gravite_z = np.mean([m.linear_acceleration.z for m in tampon_imu])
            print(f"Alignement réussi. Gravité locale [X:{gravite_x:.2f}, Y:{gravite_y:.2f}, Z:{gravite_z:.2f}].")
            
            ecrivain = Writer(chemin_sortie, version=8)
            ecrivain.open()
            
            with AnyReader(chemins_db3_raw, default_typestore=typestore) as lecteur:
                connexions_ecriture = {}
                for connexion in lecteur.connections:
                    try:
                        connexions_ecriture[connexion.id] = ecrivain.add_connection(
                            connexion.topic, connexion.msgtype, 
                            typestore=typestore, msgdef=getattr(connexion, 'msgdef', '')
                        )
                    except Exception:
                        pass
                
                frequence_imu_ns = int(1e9 / 200)
                frequence_lidar_ns = int(1e9 / 10)
                
                hw_courant_ns = limite_hw_ns - duree_calib_ns
                temps_courant_record = record_time_cut - duree_calib_ns
                derniere_injection_lidar = temps_courant_record
                
                connexion_imu = next(c for c in lecteur.connections if 'Imu' in c.msgtype)
                connexion_lidar = next(c for c in lecteur.connections if 'PointCloud2' in c.msgtype)
                
                print("2. Synthèse d'un tunnel statique ZUPT de 5.0 secondes (Sync capteur)...")
                while temps_courant_record < record_time_cut:
                    msg_imu_gabarit.header.stamp.sec = int(hw_courant_ns // 1e9)
                    msg_imu_gabarit.header.stamp.nanosec = int(hw_courant_ns % 1e9)
                    msg_imu_gabarit.angular_velocity.x = 0.0
                    msg_imu_gabarit.angular_velocity.y = 0.0
                    msg_imu_gabarit.angular_velocity.z = 0.0
                    msg_imu_gabarit.linear_acceleration.x = gravite_x
                    msg_imu_gabarit.linear_acceleration.y = gravite_y
                    msg_imu_gabarit.linear_acceleration.z = gravite_z
                    
                    donnees_imu_mod = typestore.serialize_cdr(msg_imu_gabarit, type_imu_ref)
                    ecrivain.write(connexions_ecriture[connexion_imu.id], temps_courant_record, donnees_imu_mod)
                    
                    if temps_courant_record - derniere_injection_lidar >= frequence_lidar_ns:
                        message_lidar_reference.header.stamp.sec = int(hw_courant_ns // 1e9)
                        message_lidar_reference.header.stamp.nanosec = int(hw_courant_ns % 1e9)
                        donnees_lidar_mod = typestore.serialize_cdr(message_lidar_reference, type_lidar_ref)
                        ecrivain.write(connexions_ecriture[connexion_lidar.id], temps_courant_record, donnees_lidar_mod)
                        derniere_injection_lidar = temps_courant_record
                        
                    hw_courant_ns += frequence_imu_ns
                    temps_courant_record += frequence_imu_ns
                
                print("3. Concaténation de la topologie dynamique résiduelle...")
                compteurs = 0
                for connexion, timestamp, rawdata in lecteur.messages():
                    if timestamp >= record_time_cut:
                        if connexion.id in connexions_ecriture:
                            ecrivain.write(connexions_ecriture[connexion.id], timestamp, rawdata)
                            compteurs += 1
                            
                print(f"Opération terminale achevée. {compteurs} trames transférées avec l'horloge synchronisée.")
                
        except Exception as e:
            print(f"\nERREUR CRITIQUE PENDANT LA GÉNÉRATION : {str(e)}")
            traceback.print_exc()
        finally:
            if ecrivain is not None:
                ecrivain.close()
            print(f"L'archive est découpée et prête pour le relancement de DLIO : {chemin_sortie}")
            self.serveur.shutdown()

if __name__ == "__main__":
    print("--- ENVIRONNEMENT DE COUPE ZUPT ASSISTÉ ---")
    chemin_traite = input("Indiquez le chemin de l'archive post-traitée (pour visualisation WebGL) : ").strip()
    chemin_raw = input("Indiquez le chemin de l'archive brute initiale (source capteurs) : ").strip()
    
    if os.path.exists(chemin_traite) and os.path.exists(chemin_raw):
        serveur = ServeurMontageZUPT(chemin_traite, chemin_raw)
        serveur.start()
        webbrowser.open(f"http://127.0.0.1:{serveur.port}")
        serveur.join()
    else:
        print("Erreur : L'un des répertoires spécifiés est introuvable sur le volume de stockage.")