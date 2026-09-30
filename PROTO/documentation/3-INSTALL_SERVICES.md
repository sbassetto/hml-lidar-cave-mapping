# English version

# Guide 3: Installation and Automation of Field Services (systemd)

For the HML-LiDAR Raspberry Pi to operate autonomously in the field, the
sensor drivers and the physical-switch control software must be available as
Linux system services.

The RevA field system uses **systemd** to manage these background services.

## 1. Deploy the service files

System services are installed in:

```text
/etc/systemd/system/
```

### Service A: Sensor drivers (`backpack-driver.service`)

This service starts the ROS 2 drivers associated with the Livox LiDAR and IMU.

Create or edit the service file:

```bash
sudo nano /etc/systemd/system/backpack-driver.service
```

Example configuration:

```ini
[Unit]
Description=Launcher for the Cave Explorer backpack LiDAR/IMU drivers
After=network.target

[Service]
Type=simple
User=samuel
Environment=ROS_DOMAIN_ID=0
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash -c "source /opt/ros/humble/setup.bash && source /home/samuel/Cave_explorer/ros2_ws/install/setup.bash && ros2 launch cave_explorer_bringup backpack_bringup.launch.py"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

The username and absolute paths must be adapted to the actual Raspberry Pi
installation.

### Service B: Recording control (`cave_bag_record.service`)

This service launches the Python software associated with the physical
recording switch.

Create or edit:

```bash
sudo nano /etc/systemd/system/cave_bag_record.service
```

Example configuration:

```ini
[Unit]
Description=ROS bag recording manager controlled by the hardware switch
After=backpack-driver.service

[Service]
Type=simple
User=samuel
WorkingDirectory=/home/samuel/Cave_explorer/data
Environment=ROS_DOMAIN_ID=0
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash -c "source /opt/ros/humble/setup.bash && python3 /home/samuel/Cave_explorer/scripts/switch2.py"
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Again, replace the username and paths according to the actual installation.

## 2. Enable and start the services

After creating or modifying systemd service files, reload the systemd
configuration:

```bash
sudo systemctl daemon-reload
```

Enable both services so that they are available after reboot:

```bash
sudo systemctl enable backpack-driver.service
sudo systemctl enable cave_bag_record.service
```

Start them immediately without rebooting:

```bash
sudo systemctl start backpack-driver.service
sudo systemctl start cave_bag_record.service
```

## 3. Diagnostic commands

Check the current status of the services:

```bash
sudo systemctl status backpack-driver.service
sudo systemctl status cave_bag_record.service
```

Follow the recording-control service log in real time:

```bash
sudo journalctl -u cave_bag_record.service -f
```

Restart the recording-control service if required:

```bash
sudo systemctl restart cave_bag_record.service
```

These commands are useful for diagnosing sensor-driver or hardware-switch
problems during field preparation.

---

# Version française


# Guide 3 : Installation et Automatisation des Services de Terrain (Systemd)

# Pour que Chinook soit totalement autonome en grotte, les drivers des capteurs et le script du switch matériel doivent #se lancer automatiquement dès l'allumage du Raspberry Pi. Nous utilisons pour cela les services de l'OS Linux (**Systemd**).

## 1. Déploiement des fichiers de Service

Les services doivent être créés dans le répertoire système `/etc/systemd/system/`.

### Service A : Les Capteurs (`backpack-driver.service`)

#Ce service démarre les drivers ROS 2 du LiDAR Livox et de l'IMU.
```bash
sudo nano /etc/systemd/system/backpack-driver.service
```
# Colle le contenu suivant :

```bash
Ini, TOML
[Unit]
Description=Launcher pour les drivers du Backpack Cave Explorer (LiDAR/IMU)
After=network.target

[Service]
Type=simple
User=samuel
Environment=ROS_DOMAIN_ID=0
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash -c "source /opt/ros/humble/setup.bash && source /home/samuel/Cave_explorer/ros2_ws/install/setup.bash && ros2 launch cave_explorer_bringup backpack_bringup.launch.py"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
# Service B : Le Bouton d'Enregistrement (cave_bag_record.service)
# Ce service exécute en boucle le script Python switch2.py qui écoute l'interrupteur physique.

```bash
sudo nano /etc/systemd/system/cave_bag_record.service
# Colle le contenu suivant :

```bash
Ini, TOML
[Unit]
Description=Gestionnaire d enregistrement Rosbag via Switch Matériel
After=backpack-driver.service

[Service]
Type=simple
User=samuel
WorkingDirectory=/home/samuel/Cave_explorer/data
Environment=ROS_DOMAIN_ID=0
Environment=PYTHONUNBUFFERED=1
ExecStart=/bin/bash -c "source /opt/ros/humble/setup.bash && python3 /home/samuel/Cave_explorer/scripts/switch2.py"
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
#Ces deux services sont également disponibles sur Git-HUB au téléchargement. Attention, change tes chemins avec TON $user.

# 2. Activation et Mise en Route des Services
# Une fois les deux fichiers enregistrés, exécute les commandes suivantes pour forcer Linux à les prendre en compte et les activer pour les prochains démarrages :

# 1. Recharger le gestionnaire de services de Linux
```bash
sudo systemctl daemon-reload
```
# 2. Activer le lancement automatique au boot
```bash
sudo systemctl enable backpack-driver.service
sudo systemctl enable cave_bag_record.service
```
# 3. Démarrer les services immédiatement (sans rebooter)
```bash
sudo systemctl start backpack-driver.service
sudo systemctl start cave_bag_record.service
```
# 3. Commandes de Diagnostic (Mémento de Secours)
# Si le switch ou le LiDAR ne répondent pas sur le terrain, connecte-toi au Pi et utilise ces commandes pour comprendre la panne :

# Vérifier le statut en temps réel :
```bash
sudo systemctl status backpack-driver.service
sudo systemctl status cave_bag_record.service
```
# Voir défiler les logs du bouton en direct :
```bash
sudo journalctl -u cave_bag_record.service -f
```
# Forcer le redémarrage d'un composant :
```bash
sudo systemctl restart cave_bag_record.service
```