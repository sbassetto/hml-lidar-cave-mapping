# Fichier : serveur_alignement.py
import flask
import threading
import webbrowser
import numpy as np
from werkzeug.serving import make_server

class ServeurAlignement(threading.Thread):
    """
    Démon asynchrone encapsulant un serveur Flask.
    Permet d'exposer une interface WebGL (Three.js) sans bloquer l'exécution du script principal.
    """
    def __init__(self, points_source, points_cible, max_source, max_cible, fonction_rechargement):
        threading.Thread.__init__(self)
        # Stockage local des coordonnées géométriques pour distribution via l'API REST
        self.points_source = points_source
        self.points_cible = points_cible
        # Limites temporelles absolues extraites des archives ROS 2
        self.max_source = max_source
        self.max_cible = max_cible
        # Clôture (closure) permettant d'invoquer l'extraction SQLite depuis le contexte principal
        self.fonction_rechargement = fonction_rechargement
        self.matrice_finale = None
        
        # Initialisation du micro-framework web
        self.app = flask.Flask(__name__)
        # Forçage sur l'adresse locale pour des raisons de sécurité de l'interface
        self.serveur = make_server('127.0.0.1', 5000, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

        @self.app.route('/')
        def index():
            # Injection du code client (HTML/CSS/JS) directement dans la route principale
            html_template = """
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Alignement Karstique Manuel</title>
                <style>
                    body { margin: 0; overflow: hidden; background-color: #111; color: white; font-family: sans-serif; }
                    #canvas-container { width: 100vw; height: 100vh; }
                    #ui-panel { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.85); padding: 20px; border: 1px solid #444; border-radius: 5px; z-index: 100; width: 380px; }
                    #instructions { position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px; font-size: 13px; pointer-events: none; z-index: 100; }
                    .slider-group { margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; }
                    label { width: 120px; font-size: 13px; }
                    input[type=range] { flex-grow: 1; margin: 0 10px; width: 100px; }
                    input[type=number] { width: 65px; background: #222; color: white; border: 1px solid #555; padding: 3px; font-family: monospace; font-size: 13px; text-align: right; }
                    .btn-groupe { display: flex; gap: 10px; margin-top: 20px; }
                    button { padding: 12px; flex-grow: 1; background: #007BFF; color: white; border: none; border-radius: 3px; cursor: pointer; font-weight: bold; }
                    button:hover { background: #0056b3; }
                    button:disabled { background: #555; cursor: wait; }
                    .btn-reset { background: #dc3545; }
                    .btn-reset:hover { background: #a71d2a; }
                    .separator { border-top: 1px solid #555; margin: 15px 0; }
                </style>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            </head>
            <body>
                <div id="ui-panel">
                    <h3 style="margin-top: 0; border-bottom: 1px solid #555; padding-bottom: 10px;">Ajustement Rigide (6-DOF)</h3>
                    
                    <div class="slider-group">
                        <label title="Modèle fixe (Bleu)">Fenêtre Amont:</label>
                        <input type="range" id="duree_cible" min="5" max="__MAX_CIBLE__" step="1" value="10" onchange="redimensionnerNuages()" oninput="document.getElementById('val_duree_cible').textContent = this.value + 's'">
                        <span class="valeur" id="val_duree_cible" style="width:40px; text-align:right;">10s</span>
                    </div>
                    <div class="slider-group">
                        <label title="Modèle mobile (Orange)">Fenêtre Aval:</label>
                        <input type="range" id="duree_source" min="5" max="__MAX_SOURCE__" step="1" value="10" onchange="redimensionnerNuages()" oninput="document.getElementById('val_duree_source').textContent = this.value + 's'">
                        <span class="valeur" id="val_duree_source" style="width:40px; text-align:right;">10s</span>
                    </div>
                    
                    <div class="separator"></div>

                    <div class="slider-group">
                        <label>Tx:</label>
                        <input type="range" id="tx" step="0.01" oninput="document.getElementById('num_tx').value = this.value">
                        <input type="number" id="num_tx" step="0.01" oninput="document.getElementById('tx').value = this.value">
                    </div>
                    <div class="slider-group">
                        <label>Ty:</label>
                        <input type="range" id="ty" step="0.01" oninput="document.getElementById('num_ty').value = this.value">
                        <input type="number" id="num_ty" step="0.01" oninput="document.getElementById('ty').value = this.value">
                    </div>
                    <div class="slider-group">
                        <label>Tz:</label>
                        <input type="range" id="tz" step="0.01" oninput="document.getElementById('num_tz').value = this.value">
                        <input type="number" id="num_tz" step="0.01" oninput="document.getElementById('tz').value = this.value">
                    </div>
                    
                    <div class="slider-group">
                        <label>Roulis (X):</label>
                        <input type="range" id="rx" min="-3.14159" max="3.14159" step="0.001" value="0" oninput="document.getElementById('num_rx').value = this.value">
                        <input type="number" id="num_rx" min="-3.14159" max="3.14159" step="0.001" value="0" oninput="document.getElementById('rx').value = this.value">
                    </div>
                    <div class="slider-group">
                        <label>Tangage (Y):</label>
                        <input type="range" id="ry" min="-3.14159" max="3.14159" step="0.001" value="0" oninput="document.getElementById('num_ry').value = this.value">
                        <input type="number" id="num_ry" min="-3.14159" max="3.14159" step="0.001" value="0" oninput="document.getElementById('ry').value = this.value">
                    </div>
                    <div class="slider-group">
                        <label>Lacet (Z):</label>
                        <input type="range" id="rz" min="-3.14159" max="3.14159" step="0.001" value="0" oninput="document.getElementById('num_rz').value = this.value">
                        <input type="number" id="num_rz" min="-3.14159" max="3.14159" step="0.001" value="0" oninput="document.getElementById('rz').value = this.value">
                    </div>
                    
                    <div class="btn-groupe">
                        <button class="btn-reset" onclick="reinitialiser()">Réinitialiser</button>
                        <button id="btn-valider" onclick="soumettreMatrice()">Valider</button>
                    </div>
                </div>
                <div id="instructions">
                    Navigation Caméra:<br>
                    Clic Gauche: Pivoter | Clic Droit: Translater | Molette: Zoomer<br>
                    Axes: <span style="color:red">X (Rouge)</span>, <span style="color:green">Y (Vert)</span>, <span style="color:blue">Z (Bleu)</span>
                </div>
                <div id="canvas-container"></div>
                <script>
                    let scene, camera, renderer, nuageSource, nuageCible, controleurVue;
                    let valeursInitiales = { tx: 0, ty: 0, tz: 0, rx: 0, ry: 0, rz: 0 };

                    function creerEtiquetteAxe(texte, couleur, position) {
                        const canvas = document.createElement('canvas');
                        canvas.width = 128; canvas.height = 128;
                        const ctx = canvas.getContext('2d');
                        ctx.font = 'Bold 80px Arial';
                        ctx.fillStyle = couleur;
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(texte, 64, 64);
                        const texture = new THREE.CanvasTexture(canvas);
                        const materiel = new THREE.SpriteMaterial({ map: texture, depthTest: false });
                        const sprite = new THREE.Sprite(materiel);
                        sprite.position.copy(position);
                        // Réduction de l'échelle des étiquettes pour une lecture moins invasive
                        sprite.scale.set(1.5, 1.5, 1.5);
                        scene.add(sprite);
                    }

                    // Fonction asynchrone invoquant l'API pour récupérer un nouveau volume de points
                    async function redimensionnerNuages() {
                        document.body.style.cursor = 'wait';
                        const btn = document.getElementById('btn-valider');
                        btn.textContent = "Extraction ROS 2 en cours...";
                        btn.disabled = true;

                        const val_cible = parseFloat(document.getElementById('duree_cible').value);
                        const val_source = parseFloat(document.getElementById('duree_source').value);

                        const reponse = await fetch('/redimensionner', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ duree_source: val_source, duree_cible: val_cible })
                        });
                        const donnees = await reponse.json();

                        // Remplacement direct des tampons mémoire de la carte graphique
                        nuageSource.geometry.setAttribute('position', new THREE.Float32BufferAttribute(donnees.source, 3));
                        nuageCible.geometry.setAttribute('position', new THREE.Float32BufferAttribute(donnees.cible, 3));
                        nuageSource.geometry.computeBoundingBox();
                        nuageCible.geometry.computeBoundingBox();

                        document.body.style.cursor = 'default';
                        btn.textContent = "Valider";
                        btn.disabled = false;
                    }

                    async function initialiser() {
                        scene = new THREE.Scene();
                        camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
                        renderer = new THREE.WebGLRenderer({ antialias: true });
                        renderer.setSize(window.innerWidth, window.innerHeight);
                        document.getElementById('canvas-container').appendChild(renderer.domElement);

                        const axesHelper = new THREE.AxesHelper(15);
                        scene.add(axesHelper);
                        
                        creerEtiquetteAxe('X', '#ff4444', new THREE.Vector3(16, 0, 0));
                        creerEtiquetteAxe('Y', '#44ff44', new THREE.Vector3(0, 16, 0));
                        creerEtiquetteAxe('Z', '#4444ff', new THREE.Vector3(0, 0, 16));

                        controleurVue = new THREE.OrbitControls(camera, renderer.domElement);
                        controleurVue.enableDamping = true;
                        controleurVue.dampingFactor = 0.05;

                        // Amorçage du flux de données initial
                        const reponseDonnees = await fetch('/donnees');
                        const donnees = await reponseDonnees.json();

                        const geoCible = new THREE.BufferGeometry();
                        geoCible.setAttribute('position', new THREE.Float32BufferAttribute(donnees.cible, 3));
                        const matCible = new THREE.PointsMaterial({ color: 0x00aaff, size: 0.08 });
                        nuageCible = new THREE.Points(geoCible, matCible);
                        scene.add(nuageCible);

                        const geoSource = new THREE.BufferGeometry();
                        geoSource.setAttribute('position', new THREE.Float32BufferAttribute(donnees.source, 3));
                        const matSource = new THREE.PointsMaterial({ color: 0xffaa00, size: 0.08 });
                        nuageSource = new THREE.Points(geoSource, matSource);
                        scene.add(nuageSource);

                        // Calcul d'encombrement pour le centrage automatique de la caméra et des repères
                        geoCible.computeBoundingBox();
                        const centreCible = new THREE.Vector3();
                        geoCible.boundingBox.getCenter(centreCible);

                        geoSource.computeBoundingBox();
                        const centreSource = new THREE.Vector3();
                        geoSource.boundingBox.getCenter(centreSource);

                        const axes = ['x', 'y', 'z'];
                        axes.forEach(axe => {
                            const decalage = centreCible[axe] - centreSource[axe];
                            valeursInitiales['t' + axe] = decalage;
                            
                            const slider = document.getElementById('t' + axe);
                            const numInput = document.getElementById('num_t' + axe);
                            
                            // Marge de translation fixée à 30 mètres de part et d'autre du centre de gravité
                            slider.min = (decalage - 30).toFixed(2);
                            slider.max = (decalage + 30).toFixed(2);
                            slider.value = decalage.toFixed(2);
                            numInput.value = decalage.toFixed(2);
                        });

                        camera.position.set(centreCible.x + 15, centreCible.y + 15, centreCible.z + 25);
                        controleurVue.target.copy(centreCible);
                        controleurVue.update();
                        
                        animer();
                    }
                    
                    function reinitialiser() {
                        const cles = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz'];
                        cles.forEach(cle => {
                            document.getElementById(cle).value = valeursInitiales[cle].toFixed(3);
                            document.getElementById('num_' + cle).value = valeursInitiales[cle].toFixed(3);
                        });
                    }

                    function animer() {
                        requestAnimationFrame(animer);
                        controleurVue.update();
                        
                        // Application synchrone des variables du panneau de contrôle vers la matrice locale
                        nuageSource.position.set(
                            parseFloat(document.getElementById('tx').value),
                            parseFloat(document.getElementById('ty').value),
                            parseFloat(document.getElementById('tz').value)
                        );
                        nuageSource.rotation.set(
                            parseFloat(document.getElementById('rx').value),
                            parseFloat(document.getElementById('ry').value),
                            parseFloat(document.getElementById('rz').value)
                        );
                        nuageSource.updateMatrix();
                        renderer.render(scene, camera);
                    }

                    async function soumettreMatrice() {
                        // Extraction de la transformation 4x4 calculée par le moteur WebGL
                        const matrice = nuageSource.matrix.toArray();
                        await fetch('/valider', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ matrice: matrice })
                        });
                        document.body.innerHTML = "<h2 style='text-align:center; margin-top:20%; color:#4caf50;'>Matrice d'orientation validée.<br>L'intégration topologique est en cours. Vous pouvez fermer cette fenêtre.</h2>";
                    }

                    window.addEventListener('resize', onWindowResize, false);
                    function onWindowResize() {
                        camera.aspect = window.innerWidth / window.innerHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(window.innerWidth, window.innerHeight);
                    }

                    initialiser();
                </script>
            </body>
            </html>
            """
            # Substitution dynamique du plafond d'extraction, configuré pour bloquer à 240 secondes
            html_content = html_template.replace('__MAX_SOURCE__', str(int(min(self.max_source, 240))))
            html_content = html_content.replace('__MAX_CIBLE__', str(int(min(self.max_cible, 240))))
            return html_content

        @self.app.route('/donnees')
        def donnees():
            # Conversion des matrices Numpy en listes compatibles JSON
            return flask.jsonify({
                'source': self.points_source.flatten().tolist(),
                'cible': self.points_cible.flatten().tolist()
            })

        @self.app.route('/redimensionner', methods=['POST'])
        def redimensionner():
            # Réception asynchrone des requêtes de redimensionnement temporel
            duree_source_demandee = float(flask.request.json['duree_source'])
            duree_cible_demandee = float(flask.request.json['duree_cible'])
            
            # Appel de la clôture (closure) définie dans Pegar.py pour relire la base de données
            nuage_source_brut, nuage_cible_brut = self.fonction_rechargement(duree_source_demandee, duree_cible_demandee)
            
            # Voxelisation stricte à 0.5m pour préserver la stabilité du transfert réseau local
            source_allege = nuage_source_brut.voxel_down_sample(0.5)
            cible_allege = nuage_cible_brut.voxel_down_sample(0.5)
            
            return flask.jsonify({
                'source': np.asarray(source_allege.points).flatten().tolist(),
                'cible': np.asarray(cible_allege.points).flatten().tolist()
            })

        @self.app.route('/valider', methods=['POST'])
        def valider():
            donnees_matrice = flask.request.json['matrice']
            # Reformatage de la matrice d'architecture WebGL vers l'architecture Open3D
            matrice_plate = np.array(donnees_matrice).reshape((4, 4)).transpose()
            self.matrice_finale = matrice_plate
            # Destruction sécurisée du processus serveur
            threading.Thread(target=self.serveur.shutdown).start()
            return flask.jsonify({"status": "succes"})

    def run(self):
        print("[Microservice WebGL] Serveur d'alignement odométrique actif sur le port 5000.")
        self.serveur.serve_forever()

def obtenir_matrice_manuelle(nuage_source, nuage_cible, max_source, max_cible, fonction_rechargement):
    # Compression géométrique initiale avant transmission
    source_allege = nuage_source.voxel_down_sample(0.5)
    cible_allege = nuage_cible.voxel_down_sample(0.5)
    
    pts_source = np.asarray(source_allege.points)
    pts_cible = np.asarray(cible_allege.points)
    
    # Lancement du processus démon et ouverture du navigateur par défaut
    serveur = ServeurAlignement(pts_source, pts_cible, max_source, max_cible, fonction_rechargement)
    serveur.start()
    webbrowser.open("http://127.0.0.1:5000")
    serveur.join()
    
    return serveur.matrice_finale