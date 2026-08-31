# Fichier : serveur_edition.py
import flask
import threading
import webbrowser
import socket
import numpy as np
import open3d as o3d
from pathlib import Path
from werkzeug.serving import make_server
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore

def trouver_port_libre():
    """Trouve un port TCP local libre pour l'éditeur WebGL temporaire."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def extraire_nuage_pour_affichage(chemin_dossier_bag, taille_voxel=0.1):
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    points_liste = []
    nom_segment = Path(chemin_dossier_bag).name
    
    print(f"Chargement en mémoire du segment : {nom_segment}...")
    
    try:
        with AnyReader([Path(chemin_dossier_bag)], default_typestore=typestore) as reader:
            conns = [x for x in reader.connections if x.topic == '/kf_cloud']
            if not conns:
                print(f"Avertissement : Aucun topic /kf_cloud détecté dans {nom_segment}.")
                return None
            for connection, timestamp, rawdata in reader.messages(connections=conns):
                msg = reader.deserialize(rawdata, connection.msgtype)
                data = np.frombuffer(msg.data, dtype=np.uint8)
                points_bruts = data.view(dtype=np.float32).reshape(-1, msg.point_step // 4)
                points_valides = points_bruts[np.isfinite(points_bruts[:, :3]).all(axis=1)][:, :3]
                points_liste.append(points_valides)
    except Exception as e:
        print(f"Erreur critique lors de la lecture de l'archive {nom_segment} : {e}")
        return None
        
    if not points_liste: 
        print(f"Avertissement : Aucune donnée spatiale extraite pour {nom_segment}.")
        return None
    
    points_filtres = np.vstack(points_liste)
    nuage = o3d.geometry.PointCloud()
    nuage.points = o3d.utility.Vector3dVector(points_filtres)
    nuage_decime = nuage.voxel_down_sample(taille_voxel)
    print(f"Extraction réussie ({nom_segment}) : {len(nuage_decime.points)} voxels transmis au serveur WebGL.")
    
    return nuage_decime

class ServeurEditionGraphe(threading.Thread):
    def __init__(self, sequence, matrices_relatives, dossier_connected):
        threading.Thread.__init__(self)
        self.sequence = sequence
        self.matrices_relatives = matrices_relatives
        self.dossier_connected = dossier_connected
        self.nouvelles_matrices = None
        
        self.port = trouver_port_libre()
        self.app = flask.Flask(__name__)
        self.serveur = make_server('127.0.0.1', self.port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

        @self.app.route('/')
        def index():
            html_template = """
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Éditeur Manuel de Graphe Odométrique</title>
                <style>
                    body { margin: 0; overflow: hidden; background-color: #050505; color: white; font-family: sans-serif; }
                    #canvas-container { width: 100vw; height: 100vh; }
                    #ui-panel { position: absolute; top: 10px; left: 10px; background: rgba(15,15,15,0.95); padding: 15px; border: 1px solid #333; border-radius: 5px; z-index: 100; width: 440px; max-height: 95vh; overflow-y: auto; }
                    #chargement { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 20px; font-weight: bold; background: rgba(0,0,0,0.8); padding: 20px; border-radius: 8px; z-index: 200; }
                    .section { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #444; }
                    .section h4 { margin: 0 0 10px 0; color: #aaa; text-transform: uppercase; font-size: 12px; display: flex; justify-content: space-between; }
                    .checkbox-list { max-height: 100px; overflow-y: auto; font-size: 12px; font-family: monospace; background: #000; padding: 5px; border: 1px solid #333; }
                    .checkbox-item { display: flex; align-items: center; margin-bottom: 4px; }
                    .checkbox-item input { margin-right: 8px; }
                    select { width: 100%; padding: 8px; background: #222; color: white; border: 1px solid #555; margin-bottom: 10px; font-family: monospace; font-size: 12px; }
                    .slider-group { margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between; }
                    label { width: 140px; font-size: 11px; }
                    input[type=range] { flex-grow: 1; margin: 0 8px; width: 70px; }
                    input[type=number] { width: 60px; background: #222; color: white; border: 1px solid #555; padding: 3px; font-family: monospace; font-size: 12px; text-align: right; }
                    button { padding: 8px; width: 100%; background: #007BFF; color: white; border: none; border-radius: 3px; cursor: pointer; font-weight: bold; margin-bottom: 5px; font-size: 12px;}
                    button:hover { background: #0056b3; }
                    .btn-secondaire { background: #444; }
                    .btn-secondaire:hover { background: #555; }
                    .btn-valider { background: #28a745; font-size: 14px; margin-top: 10px; padding: 12px;}
                    .btn-valider:hover { background: #218838; }
                    .btn-reset { background: #dc3545; }
                    .btn-reset:hover { background: #a71d2a; }
                    .titre-sous-section { font-size: 11px; color: #888; margin: 8px 0 4px 0; border-bottom: 1px dashed #333; font-weight: bold;}
                </style>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            </head>
            <body>
                <div id="chargement">Analyse topologique et chargement des nuages en cours...</div>
                <div id="ui-panel" style="display:none;">
                    <div class="section">
                        <h4>Visibilité des segments <button class="btn-secondaire" style="width:auto; padding:2px 8px; margin:0;" onclick="toggleReperes()">Axes On/Off</button></h4>
                        <div class="checkbox-list" id="liste-visibilite"></div>
                        <div class="slider-group" style="margin-top:8px;">
                            <label>Taille des points:</label>
                            <input type="range" id="taille_points" min="0.01" max="0.3" step="0.01" value="0.05" oninput="majTaillePoints()">
                            <span id="val_taille_points" style="font-size:12px; width:30px; text-align:right;">0.05</span>
                        </div>
                    </div>

                    <div class="section">
                        <h4>Jonction Pegar à réviser manuellement</h4>
                        <select id="select-jonction" onchange="changerJonctionActive()"></select>
                    </div>

                    <div class="section">
                        <h4>Ajustement du Pivot et du Nuage</h4>
                        <button class="btn-secondaire" id="btn-etendre" onclick="etendreMarges()">Élargir l'amplitude spatiale (x2)</button>
                        
                        <div class="titre-sous-section">Configuration du Repère Local (Ne déplace pas le nuage)</div>
                        <div class="slider-group"><label>Pivot Px:</label><input type="range" id="px" step="0.01"><input type="number" id="num_px" step="0.01"></div>
                        <div class="slider-group"><label>Pivot Py:</label><input type="range" id="py" step="0.01"><input type="number" id="num_py" step="0.01"></div>
                        <div class="slider-group"><label>Pivot Pz:</label><input type="range" id="pz" step="0.01"><input type="number" id="num_pz" step="0.01"></div>
                        
                        <div class="slider-group"><label>Repère Roulis (X):</label><input type="range" id="fx" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_fx" step="0.001"></div>
                        <div class="slider-group"><label>Repère Tangage (Y):</label><input type="range" id="fy" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_fy" step="0.001"></div>
                        <div class="slider-group"><label>Repère Lacet (Z):</label><input type="range" id="fz" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_fz" step="0.001"></div>

                        <div class="titre-sous-section">Déplacement du Nuage (Relatif aux axes du repère)</div>
                        <div class="slider-group"><label>Trans. Tx:</label><input type="range" id="tx" step="0.01"><input type="number" id="num_tx" step="0.01"></div>
                        <div class="slider-group"><label>Trans. Ty:</label><input type="range" id="ty" step="0.01"><input type="number" id="num_ty" step="0.01"></div>
                        <div class="slider-group"><label>Trans. Tz:</label><input type="range" id="tz" step="0.01"><input type="number" id="num_tz" step="0.01"></div>

                        <div class="slider-group"><label>Rot. Roulis (X):</label><input type="range" id="rx" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_rx" step="0.001"></div>
                        <div class="slider-group"><label>Rot. Tangage (Y):</label><input type="range" id="ry" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_ry" step="0.001"></div>
                        <div class="slider-group"><label>Rot. Lacet (Z):</label><input type="range" id="rz" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_rz" step="0.001"></div>
                    </div>
                    
                    <button class="btn-reset" onclick="reinitialiserActif()">Réinitialiser les paramètres</button>
                    <button class="btn-valider" onclick="soumettreMatrices()">Compiler la nouvelle topologie</button>
                </div>
                <div id="canvas-container"></div>

                <script>
                    let scene, camera, renderer, controleurVue;
                    let repereGlobal, repereLocal;
                    let affichageReperes = true;
                    let sequence = [];
                    let matricesRelatives = [];
                    let noeudsGraphe = {};
                    let materiauxPoints = {};
                    let paramsNoeuds = {};
                    let paramsNoeudsInitiaux = {};
                    let indexJonctionActive = 0;
                    let margeTranslation = 30;
                    let multiplicateurMarge = 1;
                    
                    const couleurs = [0xffffff, 0x00aaff, 0xffaa00, 0x44ff44, 0xff44ff, 0xffff00, 0x00ffff, 0xff4444];

                    function creerEtiquetteAxe(texte, couleur, position) {
                        const canvas = document.createElement('canvas');
                        canvas.width = 256; canvas.height = 128;
                        const ctx = canvas.getContext('2d');
                        ctx.font = 'Bold 60px Arial';
                        ctx.fillStyle = couleur;
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(texte, 128, 64);
                        const texture = new THREE.CanvasTexture(canvas);
                        const materiel = new THREE.SpriteMaterial({ map: texture, depthTest: false });
                        const sprite = new THREE.Sprite(materiel);
                        sprite.position.copy(position);
                        sprite.scale.set(3, 1.5, 1);
                        return sprite;
                    }

                    function creerSystemeAxes(estGlobal) {
                        const groupe = new THREE.Group();
                        const taille = estGlobal ? 10 : 8;
                        const axes = new THREE.AxesHelper(taille);
                        groupe.add(axes);
                        
                        const prefixe = estGlobal ? 'Abs ' : 'Loc ';
                        const offset = taille + 1.5;
                        groupe.add(creerEtiquetteAxe(prefixe + 'X', '#ff4444', new THREE.Vector3(offset, 0, 0)));
                        groupe.add(creerEtiquetteAxe(prefixe + 'Y', '#44ff44', new THREE.Vector3(0, offset, 0)));
                        groupe.add(creerEtiquetteAxe(prefixe + 'Z', '#4444ff', new THREE.Vector3(0, 0, offset)));
                        return groupe;
                    }

                    function toggleReperes() {
                        affichageReperes = !affichageReperes;
                        if(repereGlobal) repereGlobal.visible = affichageReperes;
                        if(repereLocal) repereLocal.visible = affichageReperes;
                    }

                    async function initialiser() {
                        scene = new THREE.Scene();
                        camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
                        renderer = new THREE.WebGLRenderer({ antialias: true });
                        renderer.setSize(window.innerWidth, window.innerHeight);
                        document.getElementById('canvas-container').appendChild(renderer.domElement);
                        
                        repereGlobal = creerSystemeAxes(true);
                        scene.add(repereGlobal);
                        
                        repereLocal = creerSystemeAxes(false);
                        
                        controleurVue = new THREE.OrbitControls(camera, renderer.domElement);
                        
                        const repStruct = await fetch('/structure_graphe');
                        const struct = await repStruct.json();
                        sequence = struct.sequence;
                        matricesRelatives = struct.matrices;

                        const conteneurVisibilite = document.getElementById('liste-visibilite');
                        const selectJonction = document.getElementById('select-jonction');

                        for (let i = 0; i < sequence.length; i++) {
                            const nomSegment = sequence[i];
                            const repNuage = await fetch('/nuage/' + nomSegment);
                            const donneesNuage = await repNuage.json();
                            
                            const geometrie = new THREE.BufferGeometry();
                            geometrie.setAttribute('position', new THREE.Float32BufferAttribute(donneesNuage.points, 3));
                            
                            const couleur = couleurs[i % couleurs.length];
                            const materiel = new THREE.PointsMaterial({ color: couleur, size: 0.05 });
                            materiauxPoints[nomSegment] = materiel;
                            
                            const nuage = new THREE.Points(geometrie, materiel);
                            const noeud = new THREE.Group();
                            noeud.add(nuage);
                            noeudsGraphe[i] = noeud;
                            
                            if (i === 0) {
                                scene.add(noeud);
                            } else {
                                noeudsGraphe[i - 1].add(noeud);
                                const matriceInitiale = new THREE.Matrix4().fromArray(matricesRelatives[i - 1]).transpose();
                                const pos = new THREE.Vector3();
                                const quat = new THREE.Quaternion();
                                const scale = new THREE.Vector3();
                                matriceInitiale.decompose(pos, quat, scale);
                                
                                paramsNoeuds[i] = { 
                                    px: pos.x, py: pos.y, pz: pos.z, 
                                    fx: 0, fy: 0, fz: 0,
                                    tx: 0, ty: 0, tz: 0,
                                    rx: 0, ry: 0, rz: 0
                                };
                                paramsNoeudsInitiaux[i] = { 
                                    px: pos.x, py: pos.y, pz: pos.z, 
                                    quat: quat.clone()
                                };
                                
                                noeud.matrixAutoUpdate = false;
                                noeud.matrix.copy(matriceInitiale);
                                
                                const option = document.createElement('option');
                                option.value = i - 1;
                                option.text = `[${i-1}] ${sequence[i-1]}  --->  ${nomSegment}`;
                                selectJonction.appendChild(option);
                            }
                            
                            const div = document.createElement('div');
                            div.className = 'checkbox-item';
                            const cb = document.createElement('input');
                            cb.type = 'checkbox';
                            cb.checked = true;
                            cb.onchange = (e) => { nuage.visible = e.target.checked; };
                            const lbl = document.createElement('span');
                            lbl.innerText = `${i}: ${nomSegment}`;
                            lbl.style.color = '#' + couleur.toString(16).padStart(6, '0');
                            div.appendChild(cb);
                            div.appendChild(lbl);
                            conteneurVisibilite.appendChild(div);
                        }

                        document.getElementById('chargement').style.display = 'none';
                        document.getElementById('ui-panel').style.display = 'block';
                        
                        camera.position.set(20, 20, 30);
                        controleurVue.target.set(0, 0, 0);
                        
                        ['px', 'py', 'pz', 'fx', 'fy', 'fz', 'tx', 'ty', 'tz', 'rx', 'ry', 'rz'].forEach(id => {
                            const slider = document.getElementById(id);
                            const num = document.getElementById('num_' + id);
                            slider.addEventListener('input', (e) => { num.value = e.target.value; appliquerTransformationActive(); });
                            num.addEventListener('input', (e) => { slider.value = e.target.value; appliquerTransformationActive(); });
                        });

                        changerJonctionActive();
                        animer();
                    }

                    function majTaillePoints() {
                        const taille = parseFloat(document.getElementById('taille_points').value);
                        document.getElementById('val_taille_points').textContent = taille;
                        Object.values(materiauxPoints).forEach(mat => mat.size = taille);
                    }

                    function changerJonctionActive() {
                        indexJonctionActive = parseInt(document.getElementById('select-jonction').value);
                        const indexActuel = indexJonctionActive + 1;
                        const noeudParent = noeudsGraphe[indexJonctionActive];
                        
                        // Attachement du repère local visuel au nœud parent de la transformation en cours
                        if (repereLocal.parent) repereLocal.parent.remove(repereLocal);
                        noeudParent.add(repereLocal);

                        const p = paramsNoeuds[indexActuel];
                        const init = paramsNoeudsInitiaux[indexActuel];
                        
                        ['x', 'y', 'z'].forEach(axe => {
                            // Paramétrage des bornes du pivot (absolu par rapport au parent)
                            const valPivot = p['p' + axe];
                            const sliderPivot = document.getElementById('p' + axe);
                            sliderPivot.min = (init['p' + axe] - margeTranslation).toFixed(2);
                            sliderPivot.max = (init['p' + axe] + margeTranslation).toFixed(2);
                            sliderPivot.value = valPivot.toFixed(3);
                            document.getElementById('num_p' + axe).value = valPivot.toFixed(3);
                            
                            // Paramétrage des bornes de la translation locale du nuage (delta)
                            const valTrans = p['t' + axe];
                            const sliderTrans = document.getElementById('t' + axe);
                            sliderTrans.min = (-margeTranslation).toFixed(2);
                            sliderTrans.max = (margeTranslation).toFixed(2);
                            sliderTrans.value = valTrans.toFixed(3);
                            document.getElementById('num_t' + axe).value = valTrans.toFixed(3);

                            ['f', 'r'].forEach(prefixe => {
                                const val = p[prefixe + axe];
                                document.getElementById(prefixe + axe).value = val.toFixed(3);
                                document.getElementById('num_' + prefixe + axe).value = val.toFixed(3);
                            });
                        });
                        
                        appliquerTransformationActive();
                        
                        const noeudMobile = noeudsGraphe[indexActuel];
                        const coordonneesAbsolues = new THREE.Vector3();
                        noeudMobile.getWorldPosition(coordonneesAbsolues);
                        controleurVue.target.copy(coordonneesAbsolues);
                    }

                    function etendreMarges() {
                        margeTranslation *= 2;
                        multiplicateurMarge *= 2;
                        changerJonctionActive();
                        document.getElementById('btn-etendre').innerText = `Élargir l'amplitude spatiale (x${multiplicateurMarge * 2})`;
                    }

                    function reinitialiserActif() {
                        const index = indexJonctionActive + 1;
                        const p = paramsNoeuds[index];
                        const init = paramsNoeudsInitiaux[index];
                        
                        ['x', 'y', 'z'].forEach(axe => {
                            p['p' + axe] = init['p' + axe];
                            p['f' + axe] = 0;
                            p['t' + axe] = 0;
                            p['r' + axe] = 0;
                        });
                        
                        changerJonctionActive();
                    }

                    function appliquerTransformationActive() {
                        const index = indexJonctionActive + 1;
                        const p = paramsNoeuds[index];
                        const init = paramsNoeudsInitiaux[index];
                        
                        ['px', 'py', 'pz', 'fx', 'fy', 'fz', 'tx', 'ty', 'tz', 'rx', 'ry', 'rz'].forEach(cle => {
                            p[cle] = parseFloat(document.getElementById(cle).value);
                        });
                        
                        // Asservissement visuel du repère local sur la définition du pivot
                        repereLocal.position.set(p.px, p.py, p.pz);
                        repereLocal.rotation.set(p.fx, p.fy, p.fz, 'XYZ');

                        // Matrice extrinsèque de définition du repère local
                        const m_pivot = new THREE.Matrix4();
                        m_pivot.makeRotationFromEuler(new THREE.Euler(p.fx, p.fy, p.fz, 'XYZ'));
                        m_pivot.setPosition(p.px, p.py, p.pz);
                        const m_pivot_inv = m_pivot.clone().invert();

                        // Matrice intrinsèque du déplacement du nuage (opérée au sein du repère local défini ci-dessus)
                        const m_delta = new THREE.Matrix4();
                        m_delta.makeRotationFromEuler(new THREE.Euler(p.rx, p.ry, p.rz, 'XYZ'));
                        m_delta.setPosition(p.tx, p.ty, p.tz);

                        // Matrice structurelle initiale extraite des archives 
                        const m_init = new THREE.Matrix4();
                        m_init.makeRotationFromQuaternion(init.quat);
                        m_init.setPosition(init.px, init.py, init.pz);
                        
                        // Produit matriciel global : Définition de base -> Application relative -> Restitution dans l'espace parent -> Position brute
                        const mat = new THREE.Matrix4();
                        mat.multiplyMatrices(m_pivot, m_delta);
                        mat.multiply(m_pivot_inv);
                        mat.multiply(m_init);
                        
                        noeudsGraphe[index].matrix.copy(mat);
                    }

                    async function soumettreMatrices() {
                        document.body.style.cursor = 'wait';
                        let matricesFinales = [];
                        
                        for (let i = 0; i < sequence.length - 1; i++) {
                            const mWebGL = noeudsGraphe[i + 1].matrix.toArray();
                            const mNumPy = [
                                [mWebGL[0], mWebGL[4], mWebGL[8],  mWebGL[12]],
                                [mWebGL[1], mWebGL[5], mWebGL[9],  mWebGL[13]],
                                [mWebGL[2], mWebGL[6], mWebGL[10], mWebGL[14]],
                                [mWebGL[3], mWebGL[7], mWebGL[11], mWebGL[15]]
                            ];
                            matricesFinales.push(mNumPy);
                        }
                        
                        await fetch('/valider_graphe', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ matrices: matricesFinales })
                        });
                        
                        document.body.innerHTML = "<h2 style='text-align:center; margin-top:20%; color:#28a745;'>Modification topologique enregistrée.<br>Le serveur recalcule la chaîne cinématique. Vous pouvez fermer cette fenêtre.</h2>";
                    }

                    function animer() {
                        requestAnimationFrame(animer);
                        controleurVue.update();
                        renderer.render(scene, camera);
                    }

                    window.addEventListener('resize', () => {
                        camera.aspect = window.innerWidth / window.innerHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(window.innerWidth, window.innerHeight);
                    });

                    initialiser();
                </script>
            </body>
            </html>
            """
            return html_template

        @self.app.route('/structure_graphe')
        def structure_graphe():
            return flask.jsonify({
                'sequence': self.sequence,
                'matrices': [m.flatten().tolist() for m in self.matrices_relatives]
            })

        @self.app.route('/nuage/<nom_segment>')
        def nuage(nom_segment):
            chemin_dossier = Path(self.dossier_connected) / nom_segment
            nuage_o3d = extraire_nuage_pour_affichage(chemin_dossier, taille_voxel=0.05)
            if nuage_o3d:
                points_liste = np.asarray(nuage_o3d.points).flatten().tolist()
                return flask.jsonify({'points': points_liste})
            return flask.jsonify({'points': []})

        @self.app.route('/valider_graphe', methods=['POST'])
        def valider_graphe():
            payload = flask.request.get_json(silent=True) or {}
            donnees = payload.get('matrices')

            if not isinstance(donnees, list):
                return flask.jsonify({
                    "status": "erreur",
                    "message": "Liste de matrices absente ou invalide."
                }), 400

            if len(donnees) != len(self.matrices_relatives):
                return flask.jsonify({
                    "status": "erreur",
                    "message": "Le nombre de jonctions retournées ne correspond pas au réseau Pegar."
                }), 400

            matrices_validees = []
            for index, matrice_brute in enumerate(donnees):
                try:
                    matrice = np.asarray(matrice_brute, dtype=float)
                except Exception:
                    return flask.jsonify({
                        "status": "erreur",
                        "message": f"Jonction {index} : matrice illisible."
                    }), 400

                if matrice.shape != (4, 4) or not np.isfinite(matrice).all():
                    return flask.jsonify({
                        "status": "erreur",
                        "message": f"Jonction {index} : matrice 4x4 invalide."
                    }), 400

                if not np.allclose(
                    matrice[3, :],
                    [0.0, 0.0, 0.0, 1.0],
                    atol=1e-6
                ):
                    return flask.jsonify({
                        "status": "erreur",
                        "message": f"Jonction {index} : transformation homogène invalide."
                    }), 400

                matrices_validees.append(matrice)

            self.nouvelles_matrices = matrices_validees
            threading.Thread(target=self.serveur.shutdown).start()
            return flask.jsonify({"status": "succes"})

    def run(self):
        print(f"[Microservice WebGL] Éditeur manuel de graphe actif sur le port {self.port}.")
        self.serveur.serve_forever()

def lancer_edition_multicouche(sequence, matrices_relatives, dossier_connected):
    serveur = ServeurEditionGraphe(sequence, matrices_relatives, dossier_connected)
    serveur.start()
    webbrowser.open(f"http://127.0.0.1:{serveur.port}")
    serveur.join()
    return serveur.nouvelles_matrices