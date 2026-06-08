# hml-lidar-cave-mapping
Open-source helmet-mounted LiDAR workflow for cave mapping using ROS2, DLIO, point-cloud processing, and VisualTopo export.

#By 
Samuel Bassetto, LABAC, Ecole Polytechnique de Montréal
Giovanni Beltrame, MIST Lab, Polytechnique Montréal

Date: 2026-06-28

# HML-LiDAR Cave Mapping

This repository provides an open-source workflow for helmet-mounted LiDAR cave mapping.

The project aims to support affordable and reproducible 3D cave documentation using:

- a helmet-mounted LiDAR/IMU system;
- ROS2 bag acquisition on a Raspberry Pi 4;
- Docker-based processing;
- DLIO LiDAR-inertial odometry;
- point-cloud export to PCD;
- conversion from LiDAR-derived trajectory and point cloud to VisualTopo `.tro` files.

## Repository structure

config/      ROS2 and DLIO configuration files
scripts/     Data transfer, processing, point-cloud export, and VisualTopo conversion scripts
hardware/    Helmet-mounted hardware description, bill of materials, and mounting documentation
docs/        Installation, field protocol, calibration, and troubleshooting documentation
data/        Small example datasets and processed outputs
paper/       Notes, figures, and supplementary material for the manuscript

Descriptif en Francais du projet HML :

Le projet Cave Explorer déploie un système de cartographie souterraine autonome basé sur la technologie LiDAR. L'objectif principal réside dans l'acquisition de nuages de points denses en milieu confiné et leur conversion automatisée vers des formats topographiques standards. L'infrastructure s'appuie sur un capteur Livox Mid360 interfacé avec un Raspberry Pi 4, opérant sous un environnement conteneurisé Docker. Le traitement algorithmique transforme les données brutes de télédétection en modèles tridimensionnels et en fiches de cheminement exploitables par les spéléologues.


=====================================================================
|| Architecture et Fonctionnalités du Système Cave Explorer - HML  ||
====================================================================
Le document suivant présente l'architecture matérielle et logicielle de ce projet. Il synthétise les fonctionnalités du code et la configuration du système pour l'acquisition et le traitement de données spéléologiques par LiDAR.

*Infrastructure Matérielle et Réseau
====================================
La base matérielle repose sur un lidar Livox MID360, monté sur un casque de spéléologie, d’un ordinateur Raspberry Pi 4 (RPi) fonctionnant sous un environnement conteneurisé Docker, d’une batterie DJI TS47 ou 48 d’un transformateur de courant et tension 20V-5V. 

* La communication avec le capteur s'effectue via une connexion Ethernet directe du RPi, tandis que le contrôle des entrées et sorties repose sur la bibliothèque logicielle RPi.GPIO. Le déploiement sur le terrain nécessite une configuration réseau ad-hoc. L'opérateur utilise le partage de connexion d'un appareil cellulaire mobile fonctionnant sur une bande de fréquence restreinte à 2,4 GHz. Cette interface locale permet de créer un pont entre le RPi d’acquisition et un ordinateur de traitement post-acquisition. Cela permet un accès sécurisé par protocole SSH au conteneur ROS 2 Humble embarqué et supprime la dépendance à un équipement de routage externe dans les réseaux souterrains.

Le dispositif est installé dans un conteneur de protection et dans une sacoche de portage 3L. 

Sur le terrain, le dispositif complet est allumé via le bouton d’allumage de la batterie. L’enregistrement est lancé par un commutateur (bouton) puis arrêté par un secon appui sur ce même bouton. Au démarrage du RPi, un deamon est lancé pour ausculter ce bouton placé sur des pins 4 et 7 du RPi.

Pour les tests, l’ordinateur s’est appelé Chinnok (en référence au Mont Chinnok en Alberta). Vous pourrez changer pour le nom qui vous convient.

*Acquisition et Odométrie (ROS 2)
==========================
Le système d'exploitation hôte délègue l'exécution des processus à Docker. Le conteneur exécute la distribution ROS 2 Humble, garantissant la communication entre les différents nœuds capteurs. Le système interagit directement avec le capteur Livox Mid360 pour récupérer les nuages de points bruts à haute densité et les données inertielles. Tout est enregistré directement sur carte SD puis transféré sur poste distant (et effacé localement). 

La carte utilisée était une carte de 256GB (pour environ 8h d’enregistrement).

*Traitement Topographique (Post-traitement)
==================================
Sur l’ordinateur post-acquisition, l’algorithme Direct LiDAR-Inertial Odometry, abrégé DLIO, fusionne les trames lasers et les mesures de la centrale à inertie pour corriger la dérive de trajectoire. Le post-traitement analytique requiert Python 3, enrichi des bibliothèques scientifiques Numpy et Scipy, spécifiquement pour le partitionnement spatial par arbre k-d. Le maillage final exige l'installation locale du logiciel open-source CloudCompare sur le poste de travail macOS.

Le traitement post-expédition repose sur des modules Python dédiés s'exécutant de manière autonome. 
* Un premier script copie les données du RPi sur un poste local via la passerelle SSH et efface les données d’enregistrement sur le RPi le préparant pour une autre acquisition.
* Un second script lancé en local procède à la lecture RosBag Play, le DLIO et l’enregistrement de tous les topics pour un traitement futur. Un paramétrage particulier a été réalisé dans Params.yaml et DLIO.yaml pour permettre un post-traitement tenant compte d’une progression spéléologique (et non d’une voiture ou d’une moto par exemple).
* Un troisième script lance la conversion des enregistrements ROS bag vers le format statique Point Cloud Data. Il parcourt la base de données SQLite3, extrait les coordonnées tridimensionnelles validées, et génère un fichier unique exploitable directement dans des logiciels d'analyse spatiale pour la texturation ou la mesure.
* Un quatrième script génère le fichier topographique textuel compatible avec la norme Visual Topo. L'algorithme simplifie d'abord la trajectoire continue pour définir des stations de cheminement espacées de manière régulière. Pour chaque station, il détermine un axe de progression géométrique et applique une coupe vectorielle perpendiculaire. La projection mathématique des points du nuage sur ce plan de coupe en deux dimensions permet d'extraire les dimensions exactes de la galerie à gauche, à droite, en haut et en bas. Le module génère ensuite une distribution radiale de visées secondaires pour assurer une modélisation précise des parois environnantes, tout en filtrant le bruit matériel situé à proximité immédiate du capteur.

L'ensemble de cette architecture garantit une chaîne de traitement continue et autonome, de l'acquisition souterraine brute jusqu'à la modélisation topographique normée, tout en respectant les limites de calcul imposées par le matériel embarqué.

Liste des scripts et codes :
=================================
La gestion des interruptions matérielles repose sur deux fichiers spécifiques au système d'exploitation de l'hôte Linux (RPi). Le script Python identifié comme button_daemon.py exploite la bibliothèque RPi.GPIO pour écouter la broche physique configurée en BCM 17, ou BCM 27 selon le schéma final, via une résistance de tirage vers le haut. Ce code est maintenu actif en arrière-plan grâce au fichier de configuration hml_button.service, placé dans le répertoire des démons système sous /etc/systemd/system/ (sur el RPi). L'activation de cette écoute passive s'effectue via les commandes de contrôle du gestionnaire de processus, spécifiquement le rechargement via systemctl daemon-reload, l'activation au démarrage par systemctl enable et le lancement immédiat via systemctl start.

Quelques références bibliographie
=================================
* Gallay, M., Šupinský, J., & Hochmuth, Z. (2022). LiDAR point clouds processing for large-scale cave mapping: a case study of the Majko dome in the Domica cave. Journal of Maps, 18(1), 1-12. https://doi.org/10.1080/17445647.2022.2035270

* Idrees, M. O., & Pradhan, B. (2017). Characterization of Macro- and Micro-Geomorphology of Cave Channel from High-Resolution 3D Laser Scanning Survey: Case Study of Gomantong Cave in Sabah, Malaysia. IntechOpen.
