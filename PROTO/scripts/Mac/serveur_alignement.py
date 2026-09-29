# Fichier : serveur_alignement.py
import flask
import threading
import webbrowser
import numpy as np
import socket
from werkzeug.serving import make_server

def trouver_port_libre():
    # Instanciation d'un socket temporaire pour l'attribution d'un port dynamique par le système
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class ServeurAlignement(threading.Thread):
    def __init__(self, points_source, points_cible, max_source, max_cible, fonction_rechargement, limite_affichage):
        threading.Thread.__init__(self)
        self.points_source = points_source
        self.points_cible = points_cible
        self.max_source = max_source
        self.max_cible = max_cible
        self.fonction_rechargement = fonction_rechargement
        self.matrice_finale = None
        self.ignorer_segment = False
        
        # Correction de l'exception Flask : assignation de la limite d'affichage au contexte de la classe
        self.limite_affichage = limite_affichage
        
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
                <title>Alignement Karstique Manuel - 12 DOF</title>
                <style>
                    body { margin: 0; overflow: hidden; background-color: #050505; color: white; font-family: sans-serif; }
                    #canvas-container { width: 100vw; height: 100vh; }
                    #ui-panel { position: absolute; top: 10px; left: 10px; background: rgba(15,15,15,0.95); padding: 15px; border: 1px solid #333; border-radius: 5px; z-index: 100; width: 440px; max-height: 95vh; overflow-y: auto; }
                    #chargement { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 20px; font-weight: bold; background: rgba(0,0,0,0.8); padding: 20px; border-radius: 8px; z-index: 200; }
                    .section { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #444; }
                    .section h4 { margin: 0 0 10px 0; color: #aaa; text-transform: uppercase; font-size: 12px; display: flex; justify-content: space-between; }
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
                    .btn-exclure { background: #b8860b; font-size: 14px; margin-top: 5px; padding: 12px; }
                    .btn-exclure:hover { background: #996500; }
                    .titre-sous-section { font-size: 11px; color: #888; margin: 8px 0 4px 0; border-bottom: 1px dashed #333; font-weight: bold;}
                </style>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            </head>
            <body>
                <div id="chargement">Initialisation de l'espace de travail...</div>
                <div id="ui-panel" style="display:none;">
                    <div class="section">
                        <h4>Paramètres d'Extraction <button class="btn-secondaire" style="width:auto; padding:2px 8px; margin:0;" onclick="toggleReperes()">Axes On/Off</button></h4>
                        <div class="slider-group">
                            <label title="Modèle fixe (Bleu)">Fenêtre Amont:</label>
                            <input type="range" id="duree_cible" min="5" max="__MAX_CIBLE__" step="1" value="10" onchange="redimensionnerNuages()" oninput="document.getElementById('val_duree_cible').textContent = this.value + 's'">
                            <span id="val_duree_cible" style="font-size:12px; width:30px; text-align:right;">10s</span>
                        </div>
                        <div class="slider-group">
                            <label title="Modèle mobile (Orange)">Fenêtre Aval:</label>
                            <input type="range" id="duree_source" min="5" max="__MAX_SOURCE__" step="1" value="10" onchange="redimensionnerNuages()" oninput="document.getElementById('val_duree_source').textContent = this.value + 's'">
                            <span id="val_duree_source" style="font-size:12px; width:30px; text-align:right;">10s</span>
                        </div>
                        <div class="slider-group">
                            <label title="Taille du voxel">Niveau de détail:</label>
                            <input type="range" id="taille_voxel" min="0.01" max="0.5" step="0.01" value="0.02" onchange="redimensionnerNuages()" oninput="document.getElementById('val_taille_voxel').textContent = this.value + 'm'">
                            <span id="val_taille_voxel" style="font-size:12px; width:30px; text-align:right;">0.02m</span>
                        </div>
                        <div class="slider-group">
                            <label>Taille des points:</label>
                            <input type="range" id="taille_points" min="0.005" max="0.2" step="0.005" value="0.05" oninput="majTaillePoints()">
                            <span id="val_taille_points" style="font-size:12px; width:30px; text-align:right;">0.05</span>
                        </div>
                    </div>

                    <div class="section">
                        <h4>Ajustement du Pivot et du Nuage</h4>
                        <button class="btn-secondaire" id="btn-etendre" onclick="etendreMarges()">Élargir l'amplitude spatiale (x2)</button>
                        
                        <div class="titre-sous-section">Configuration du Repère Local</div>
                        <div class="slider-group"><label>Pivot Px:</label><input type="range" id="px" step="0.01"><input type="number" id="num_px" step="0.01"></div>
                        <div class="slider-group"><label>Pivot Py:</label><input type="range" id="py" step="0.01"><input type="number" id="num_py" step="0.01"></div>
                        <div class="slider-group"><label>Pivot Pz:</label><input type="range" id="pz" step="0.01"><input type="number" id="num_pz" step="0.01"></div>
                        
                        <div class="slider-group"><label>Repère Roulis (X):</label><input type="range" id="fx" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_fx" step="0.001"></div>
                        <div class="slider-group"><label>Repère Tangage (Y):</label><input type="range" id="fy" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_fy" step="0.001"></div>
                        <div class="slider-group"><label>Repère Lacet (Z):</label><input type="range" id="fz" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_fz" step="0.001"></div>

                        <div class="titre-sous-section">Déplacement du Nuage</div>
                        <div class="slider-group"><label>Trans. Tx:</label><input type="range" id="tx" step="0.01"><input type="number" id="num_tx" step="0.01"></div>
                        <div class="slider-group"><label>Trans. Ty:</label><input type="range" id="ty" step="0.01"><input type="number" id="num_ty" step="0.01"></div>
                        <div class="slider-group"><label>Trans. Tz:</label><input type="range" id="tz" step="0.01"><input type="number" id="num_tz" step="0.01"></div>

                        <div class="slider-group"><label>Rot. Roulis (X):</label><input type="range" id="rx" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_rx" step="0.001"></div>
                        <div class="slider-group"><label>Rot. Tangage (Y):</label><input type="range" id="ry" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_ry" step="0.001"></div>
                        <div class="slider-group"><label>Rot. Lacet (Z):</label><input type="range" id="rz" min="-3.14159" max="3.14159" step="0.001"><input type="number" id="num_rz" step="0.001"></div>
                    </div>
                    
                    <button class="btn-reset" onclick="reinitialiserActif()">Réinitialiser les paramètres</button>
                    <button class="btn-valider" id="btn-valider" onclick="soumettreMatrice()">Valider l'alignement</button>
                    <!-- Commande d'exclusion dynamique du segment envoyée au serveur Flask -->
                    <button class="btn-exclure" id="btn-exclure" onclick="ignorerSegment()">🛑 Exclure et Finaliser l'Assemblage</button>
                </div>
                <div id="canvas-container"></div>

                <script>
                    let scene, camera, renderer, controleurVue;
                    let repereGlobal, repereLocal;
                    let affichageReperes = true;
                    let nuageSource, nuageCible;
                    
                    let p = { px: 0, py: 0, pz: 0, fx: 0, fy: 0, fz: 0, tx: 0, ty: 0, tz: 0, rx: 0, ry: 0, rz: 0 };
                    let init = { decalageX: 0, decalageY: 0, decalageZ: 0, centreCibleX: 0, centreCibleY: 0, centreCibleZ: 0 };
                    
                    let margeTranslation = 30;
                    let multiplicateurMarge = 1;

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

                    function majTaillePoints() {
                        const taille = parseFloat(document.getElementById('taille_points').value);
                        document.getElementById('val_taille_points').textContent = taille;
                        if(nuageSource && nuageCible) {
                            nuageSource.material.size = taille;
                            nuageCible.material.size = taille;
                        }
                    }

                    async function redimensionnerNuages() {
                        document.body.style.cursor = 'wait';
                        const btn = document.getElementById('btn-valider');
                        btn.textContent = "Extraction ROS 2 en cours...";
                        btn.disabled = true;

                        const val_cible = parseFloat(document.getElementById('duree_cible').value);
                        const val_source = parseFloat(document.getElementById('duree_source').value);
                        const val_voxel = parseFloat(document.getElementById('taille_voxel').value);

                        const reponse = await fetch('/redimensionner', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ duree_source: val_source, duree_cible: val_cible, taille_voxel: val_voxel })
                        });
                        const donnees = await reponse.json();

                        nuageSource.geometry.setAttribute('position', new THREE.Float32BufferAttribute(donnees.source, 3));
                        nuageCible.geometry.setAttribute('position', new THREE.Float32BufferAttribute(donnees.cible, 3));
                        nuageSource.geometry.computeBoundingBox();
                        nuageCible.geometry.computeBoundingBox();

                        document.body.style.cursor = 'default';
                        btn.textContent = "Valider l'alignement";
                        btn.disabled = false;
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
                        scene.add(repereLocal);

                        controleurVue = new THREE.OrbitControls(camera, renderer.domElement);
                        controleurVue.enableDamping = true;
                        controleurVue.dampingFactor = 0.05;

                        const reponseDonnees = await fetch('/donnees');
                        const donnees = await reponseDonnees.json();
                        
                        const tailleInitiale = parseFloat(document.getElementById('taille_points').value);

                        const geoCible = new THREE.BufferGeometry();
                        geoCible.setAttribute('position', new THREE.Float32BufferAttribute(donnees.cible, 3));
                        const matCible = new THREE.PointsMaterial({ color: 0x00aaff, size: tailleInitiale });
                        nuageCible = new THREE.Points(geoCible, matCible);
                        scene.add(nuageCible);

                        const geoSource = new THREE.BufferGeometry();
                        geoSource.setAttribute('position', new THREE.Float32BufferAttribute(donnees.source, 3));
                        const matSource = new THREE.PointsMaterial({ color: 0xffaa00, size: tailleInitiale });
                        nuageSource = new THREE.Points(geoSource, matSource);
                        
                        nuageSource.matrixAutoUpdate = false;
                        scene.add(nuageSource);

                        geoCible.computeBoundingBox();
                        const centreCible = new THREE.Vector3();
                        geoCible.boundingBox.getCenter(centreCible);

                        geoSource.computeBoundingBox();
                        const centreSource = new THREE.Vector3();
                        geoSource.boundingBox.getCenter(centreSource);

                        init.decalageX = centreCible.x - centreSource.x;
                        init.decalageY = centreCible.y - centreSource.y;
                        init.decalageZ = centreCible.z - centreSource.z;
                        
                        init.centreCibleX = centreCible.x;
                        init.centreCibleY = centreCible.y;
                        init.centreCibleZ = centreCible.z;

                        p.px = init.centreCibleX;
                        p.py = init.centreCibleY;
                        p.pz = init.centreCibleZ;

                        document.getElementById('chargement').style.display = 'none';
                        document.getElementById('ui-panel').style.display = 'block';

                        camera.position.set(centreCible.x + 15, centreCible.y + 15, centreCible.z + 25);
                        controleurVue.target.copy(centreCible);
                        controleurVue.update();
                        
                        ['px', 'py', 'pz', 'fx', 'fy', 'fz', 'tx', 'ty', 'tz', 'rx', 'ry', 'rz'].forEach(id => {
                            const slider = document.getElementById(id);
                            const num = document.getElementById('num_' + id);
                            slider.addEventListener('input', (e) => { num.value = e.target.value; appliquerTransformationActive(); });
                            num.addEventListener('input', (e) => { slider.value = e.target.value; appliquerTransformationActive(); });
                        });

                        rafraichirInterface();
                        animer();
                    }

                    function rafraichirInterface() {
                        ['x', 'y', 'z'].forEach(axe => {
                            const valPivot = p['p' + axe];
                            const sliderPivot = document.getElementById('p' + axe);
                            sliderPivot.min = (init['centreCible' + axe.toUpperCase()] - margeTranslation).toFixed(2);
                            sliderPivot.max = (init['centreCible' + axe.toUpperCase()] + margeTranslation).toFixed(2);
                            sliderPivot.value = valPivot.toFixed(3);
                            document.getElementById('num_p' + axe).value = valPivot.toFixed(3);
                            
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
                    }

                    function etendreMarges() {
                        margeTranslation *= 2;
                        multiplicateurMarge *= 2;
                        rafraichirInterface();
                        document.getElementById('btn-etendre').innerText = `Élargir l'amplitude spatiale (x${multiplicateurMarge * 2})`;
                    }

                    function reinitialiserActif() {
                        ['x', 'y', 'z'].forEach(axe => {
                            p['p' + axe] = init['centreCible' + axe.toUpperCase()];
                            p['f' + axe] = 0;
                            p['t' + axe] = 0;
                            p['r' + axe] = 0;
                        });
                        rafraichirInterface();
                    }

                    function appliquerTransformationActive() {
                        ['px', 'py', 'pz', 'fx', 'fy', 'fz', 'tx', 'ty', 'tz', 'rx', 'ry', 'rz'].forEach(cle => {
                            p[cle] = parseFloat(document.getElementById(cle).value);
                        });
                        
                        repereLocal.position.set(p.px, p.py, p.pz);
                        repereLocal.rotation.set(p.fx, p.fy, p.fz, 'XYZ');

                        const m_pivot = new THREE.Matrix4();
                        m_pivot.makeRotationFromEuler(new THREE.Euler(p.fx, p.fy, p.fz, 'XYZ'));
                        m_pivot.setPosition(p.px, p.py, p.pz);
                        const m_pivot_inv = m_pivot.clone().invert();

                        const m_delta = new THREE.Matrix4();
                        m_delta.makeRotationFromEuler(new THREE.Euler(p.rx, p.ry, p.rz, 'XYZ'));
                        m_delta.setPosition(p.tx, p.ty, p.tz);

                        const m_init = new THREE.Matrix4();
                        m_init.setPosition(init.decalageX, init.decalageY, init.decalageZ);
                        
                        const mat = new THREE.Matrix4();
                        mat.multiplyMatrices(m_pivot, m_delta);
                        mat.multiply(m_pivot_inv);
                        mat.multiply(m_init);
                        
                        nuageSource.matrix.copy(mat);
                    }

                    async function soumettreMatrice() {
                        document.body.style.cursor = 'wait';
                        const mWebGL = nuageSource.matrix.toArray();
                        const mNumPy = [
                            [mWebGL[0], mWebGL[4], mWebGL[8],  mWebGL[12]],
                            [mWebGL[1], mWebGL[5], mWebGL[9],  mWebGL[13]],
                            [mWebGL[2], mWebGL[6], mWebGL[10], mWebGL[14]],
                            [mWebGL[3], mWebGL[7], mWebGL[11], mWebGL[15]]
                        ];
                        
                        await fetch('/valider', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ matrice: mNumPy })
                        });
                        document.body.innerHTML = "<h2 style='text-align:center; margin-top:20%; color:#4caf50;'>Matrice d'orientation validée.<br>L'intégration topologique est en cours. Vous pouvez fermer cette fenêtre.</h2>";
                    }

                    // Déclenchement de la route de fermeture asynchrone sans validation mathématique
                    async function ignorerSegment() {
                        document.body.style.cursor = 'wait';
                        await fetch('/ignorer', { method: 'POST' });
                        document.body.innerHTML = "<h2 style='text-align:center; margin-top:20%; color:#ffaa00;'>Segment exclu par l'opérateur.<br>Finalisation du réseau global en cours. Vous pouvez fermer cette fenêtre.</h2>";
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
            html_content = html_template.replace('__MAX_SOURCE__', str(int(min(self.max_source, self.limite_affichage))))
            html_content = html_content.replace('__MAX_CIBLE__', str(int(min(self.max_cible, self.limite_affichage))))
            return html_content

        @self.app.route('/donnees')
        def donnees():
            return flask.jsonify({
                'source': self.points_source.flatten().tolist(),
                'cible': self.points_cible.flatten().tolist()
            })

        @self.app.route('/redimensionner', methods=['POST'])
        def redimensionner():
            duree_source_demandee = float(flask.request.json['duree_source'])
            duree_cible_demandee = float(flask.request.json['duree_cible'])
            taille_voxel_demandee = float(flask.request.json.get('taille_voxel', 0.02))
            
            nuage_source_brut, nuage_cible_brut = self.fonction_rechargement(duree_source_demandee, duree_cible_demandee)
            
            source_allege = nuage_source_brut.voxel_down_sample(taille_voxel_demandee)
            cible_allege = nuage_cible_brut.voxel_down_sample(taille_voxel_demandee)
            
            return flask.jsonify({
                'source': np.asarray(source_allege.points).flatten().tolist(),
                'cible': np.asarray(cible_allege.points).flatten().tolist()
            })

        @self.app.route('/valider', methods=['POST'])
        def valider():
            donnees_matrice = flask.request.json['matrice']
            self.matrice_finale = np.array(donnees_matrice)
            threading.Thread(target=self.serveur.shutdown).start()
            return flask.jsonify({"status": "succes"})

        @self.app.route('/ignorer', methods=['POST'])
        def ignorer():
            self.ignorer_segment = True
            threading.Thread(target=self.serveur.shutdown).start()
            return flask.jsonify({"status": "succes"})

    def run(self):
        print(f"[Microservice WebGL] Serveur d'alignement odométrique actif sur le port dynamique {self.port}.")
        self.serveur.serve_forever()

def obtenir_matrice_manuelle(nuage_source, nuage_cible, max_source, max_cible, fonction_rechargement, limite_affichage=240):
    taille_voxel_initiale = 0.02
    source_allege = nuage_source.voxel_down_sample(taille_voxel_initiale)
    cible_allege = nuage_cible.voxel_down_sample(taille_voxel_initiale)
    
    pts_source = np.asarray(source_allege.points)
    pts_cible = np.asarray(cible_allege.points)
    
    serveur = ServeurAlignement(pts_source, pts_cible, max_source, max_cible, fonction_rechargement, limite_affichage)
    serveur.start()
    webbrowser.open(f"http://127.0.0.1:{serveur.port}")
    serveur.join()
    
    if hasattr(serveur, 'ignorer_segment') and serveur.ignorer_segment:
        return "IGNORER"
        
    return serveur.matrice_finale