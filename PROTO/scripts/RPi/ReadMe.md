# HML-LiDAR RevA — Raspberry Pi acquisition scripts

## English version

This directory contains the Raspberry Pi software used by the HML-LiDAR RevA
field acquisition system.

The RevA acquisition chain was verified directly on the field Raspberry Pi
named `chinook`.

The reference Raspberry Pi components are:

```text
switch2.py
switch2.service
backpack-driver.service
cave_bag_record.service
```

Their functions are:

- `switch2.py` — monitors the physical acquisition switch connected to GPIO 4;
- `switch2.service` — starts `switch2.py` automatically at Raspberry Pi boot;
- `backpack-driver.service` — starts and stops the Docker Compose environment
  containing the Livox acquisition stack;
- `cave_bag_record.service` — records the Livox LiDAR and IMU ROS 2 topics
  into timestamped ROS 2 bags.

The complete systemd installation and service definitions are documented in:

```text
../../documentation/3-INSTALL_SERVICES.md
```

---

## 1. RevA field architecture

The verified RevA acquisition sequence is:

```text
Raspberry Pi boot
        ↓
switch2.service
        ↓
switch2.py
GPIO 4 / physical pin 7
pull_up=True
debounce=0.5 s
        ↓
physical switch ON
        ├── start backpack-driver.service
        │       ↓
        │   docker compose up
        │       ↓
        │   cave_explorer-livox-1
        │
        └── start cave_bag_record.service
                ↓
             wait 15 s
                ↓
             ros2 bag record
             /livox/lidar
             /livox/imu

physical switch OFF
        ↓
stop cave_bag_record.service
        ↓
SIGINT sent to ros2
        ↓
wait 10 s
        ↓
stop backpack-driver.service
        ↓
docker compose down
```

---

## 2. Physical-switch controller

### `switch2.py`

The physical switch is connected to:

```text
GPIO 4
physical pin 7
```

The input uses the Raspberry Pi internal pull-up resistor and a 500 ms
software debounce:

```python
switch = Button(4, pull_up=True, bounce_time=0.5)
```

When the switch is moved to the ON position, the program starts:

```text
backpack-driver.service
cave_bag_record.service
```

When the switch is returned to OFF, the program:

1. stops `cave_bag_record.service`;
2. waits 10 seconds for recording finalization;
3. stops `backpack-driver.service`.

The field version also includes a startup safeguard:

```python
if switch.is_pressed:
    switch.wait_for_release()
```

If the Raspberry Pi boots while the switch is already in the ON position,
the system waits until the switch is returned to OFF before arming the
acquisition events.

This prevents an unintended recording sequence immediately after boot.

---

## 3. Switch monitoring service

### `switch2.service`

This service launches the physical-switch controller automatically.

The verified RevA field service runs:

```text
/usr/bin/python3 /home/samuel/Cave_explorer/switch2.py
```

with:

```text
User=root
WorkingDirectory=/home/samuel/Cave_explorer
Restart=always
```

The service was verified as enabled and active on `chinook`.

A historical unit named `switch-manager.service` was also present on the
field Raspberry Pi, but it was:

```text
disabled
inactive
```

and is therefore not part of the RevA reference configuration.

No active `hml_button.service` was installed on the verified field system.

---

## 4. Docker/Livox acquisition service

### `backpack-driver.service`

This service manages the Docker Compose acquisition environment located in:

```text
/home/samuel/Cave_explorer/
```

When started, it runs:

```bash
docker compose up --remove-orphans
```

Before startup, any previous Compose instance is shut down with:

```bash
docker compose down
```

When the service is stopped, the Docker acquisition environment is also
stopped with:

```bash
docker compose down
```

The field container used by the recording service is:

```text
cave_explorer-livox-1
```

---

## 5. ROS 2 recording service

### `cave_bag_record.service`

This service performs the actual LiDAR and IMU recording.

Before recording starts, it:

1. creates the acquisition directory if necessary;
2. waits 15 seconds for the Docker/Livox environment to become ready;
3. starts `ros2 bag record` inside the Livox container.

The recorded topics are:

```text
/livox/lidar
/livox/imu
```

The field recording directory is:

```text
/home/samuel/Cave_explorer/data/cave_data/
```

Inside the container, this directory is available as:

```text
/data/cave_data/
```

Acquisitions are named using the pattern:

```text
cave_bag_YYYY-MM-DD_HH-MM-SS
```

When the recording service is stopped, a `SIGINT` is sent to the ROS 2
recording process so that the bag can be finalized cleanly.

---

## 6. File installation

The RevA files in this directory are intended to reproduce the verified field
configuration.

The Python controller is deployed as:

```text
/home/samuel/Cave_explorer/switch2.py
```

Make it executable:

```bash
sudo chmod +x /home/samuel/Cave_explorer/switch2.py
```

The service files are installed in:

```text
/etc/systemd/system/
```

For example, from this repository directory:

```bash
sudo cp switch2.service /etc/systemd/system/
sudo cp backpack-driver.service /etc/systemd/system/
sudo cp cave_bag_record.service /etc/systemd/system/
```

Reload the systemd configuration:

```bash
sudo systemctl daemon-reload
```

Enable the switch-monitoring service at boot:

```bash
sudo systemctl enable switch2.service
```

Start it immediately:

```bash
sudo systemctl start switch2.service
```

During normal field operation, `backpack-driver.service` and
`cave_bag_record.service` are controlled automatically by `switch2.py`.

---

## 7. Verification

Check the physical-switch controller:

```bash
systemctl status switch2.service
```

Check the Docker/Livox acquisition service:

```bash
systemctl status backpack-driver.service
```

Check the ROS 2 recording service:

```bash
systemctl status cave_bag_record.service
```

Verify that `switch2.py` is running:

```bash
ps -ef | grep '[s]witch2.py'
```

Follow the switch service log:

```bash
journalctl -u switch2.service -f
```

Follow the recording service log:

```bash
journalctl -u cave_bag_record.service -f
```

---

## 8. Normal field operation

The normal RevA field sequence is:

```text
1. Boot the Raspberry Pi.
2. Wait for switch2.service to start.
3. Confirm that the physical switch is OFF.
4. Move the switch to ON.
5. The Docker/Livox environment starts.
6. The recording service waits 15 s.
7. ROS 2 records /livox/lidar and /livox/imu.
8. Perform the cave acquisition.
9. Move the switch back to OFF.
10. The ROS 2 recorder is stopped with SIGINT.
11. The system waits 10 s for finalization.
12. The Docker/Livox environment is stopped.
```

Raw acquisitions can then be transferred to the post-processing workstation
using:

```text
PROTO/scripts/Mac/0_mission_sync.sh
```

---

## 9. RevA reproducibility note

The RevA service architecture documented here was recovered and checked
directly on the field Raspberry Pi.

The verified reference configuration was:

```text
switch2.service        enabled and active
switch-manager.service disabled and inactive
hml_button.service     not installed
```

The RevA reference acquisition chain therefore uses:

```text
switch2.py
switch2.service
backpack-driver.service
cave_bag_record.service
```

Older or experimental button-control mechanisms are not part of the verified
RevA field configuration.

---

# Version française

Ce dossier contient les logiciels Raspberry Pi utilisés par le système
d'acquisition terrain HML-LiDAR RevA.

La chaîne d'acquisition RevA a été vérifiée directement sur le Raspberry Pi
terrain nommé `chinook`.

Les composants de référence sont :

```text
switch2.py
switch2.service
backpack-driver.service
cave_bag_record.service
```

Leur rôle est le suivant :

- `switch2.py` — surveille l'interrupteur physique connecté au GPIO 4 ;
- `switch2.service` — démarre automatiquement `switch2.py` au démarrage du
  Raspberry Pi ;
- `backpack-driver.service` — démarre et arrête l'environnement Docker Compose
  contenant la chaîne d'acquisition Livox ;
- `cave_bag_record.service` — enregistre les topics ROS 2 LiDAR et IMU dans des
  bags horodatés.

La configuration détaillée des services `systemd` est décrite dans :

```text
../../documentation/3-INSTALL_SERVICES.md
```

---

## 1. Architecture terrain RevA

La séquence d'acquisition vérifiée est :

```text
Démarrage du Raspberry Pi
        ↓
switch2.service
        ↓
switch2.py
GPIO 4 / broche physique 7
pull_up=True
anti-rebond = 0,5 s
        ↓
interrupteur physique sur ON
        ├── démarrage de backpack-driver.service
        │       ↓
        │   docker compose up
        │       ↓
        │   cave_explorer-livox-1
        │
        └── démarrage de cave_bag_record.service
                ↓
             attente de 15 s
                ↓
             ros2 bag record
             /livox/lidar
             /livox/imu

interrupteur physique sur OFF
        ↓
arrêt de cave_bag_record.service
        ↓
SIGINT envoyé à ros2
        ↓
attente de 10 s
        ↓
arrêt de backpack-driver.service
        ↓
docker compose down
```

---

## 2. Contrôleur de l'interrupteur physique

### `switch2.py`

L'interrupteur physique est connecté au :

```text
GPIO 4
broche physique 7
```

L'entrée utilise la résistance de rappel interne du Raspberry Pi et un
anti-rebond logiciel de 500 ms :

```python
switch = Button(4, pull_up=True, bounce_time=0.5)
```

Lorsque l'interrupteur est placé sur ON, le programme démarre :

```text
backpack-driver.service
cave_bag_record.service
```

Lorsque l'interrupteur revient sur OFF, le programme :

1. arrête `cave_bag_record.service` ;
2. attend 10 secondes pour permettre la finalisation de l'enregistrement ;
3. arrête `backpack-driver.service`.

La version terrain comprend également une sécurité au démarrage :

```python
if switch.is_pressed:
    switch.wait_for_release()
```

Si le Raspberry Pi démarre alors que l'interrupteur est déjà sur ON, le
système attend son retour sur OFF avant d'armer les événements d'acquisition.

Cette sécurité évite le démarrage involontaire d'un enregistrement
immédiatement après le boot.

---

## 3. Service de surveillance de l'interrupteur

### `switch2.service`

Ce service lance automatiquement le contrôleur de l'interrupteur physique.

La configuration RevA vérifiée exécute :

```text
/usr/bin/python3 /home/samuel/Cave_explorer/switch2.py
```

avec :

```text
User=root
WorkingDirectory=/home/samuel/Cave_explorer
Restart=always
```

Le service a été vérifié comme activé et en cours d'exécution sur `chinook`.

Une unité historique nommée `switch-manager.service` était également présente,
mais elle était :

```text
disabled
inactive
```

Elle ne fait donc pas partie de la configuration RevA de référence.

Aucun service actif nommé `hml_button.service` n'était installé sur le système
terrain vérifié.

---

## 4. Service Docker/Livox

### `backpack-driver.service`

Ce service gère l'environnement d'acquisition Docker Compose situé dans :

```text
/home/samuel/Cave_explorer/
```

Lors de son démarrage, il exécute :

```bash
docker compose up --remove-orphans
```

Avant ce démarrage, toute instance précédente de l'environnement Compose est
arrêtée avec :

```bash
docker compose down
```

Lors de l'arrêt du service, l'environnement Docker est également arrêté avec :

```bash
docker compose down
```

Le conteneur terrain utilisé par le service d'enregistrement est :

```text
cave_explorer-livox-1
```

---

## 5. Service d'enregistrement ROS 2

### `cave_bag_record.service`

Ce service réalise l'enregistrement effectif des données LiDAR et IMU.

Avant le début de l'enregistrement, il :

1. crée le répertoire d'acquisition si nécessaire ;
2. attend 15 secondes pour permettre le démarrage de l'environnement
   Docker/Livox ;
3. lance `ros2 bag record` à l'intérieur du conteneur Livox.

Les topics enregistrés sont :

```text
/livox/lidar
/livox/imu
```

Le répertoire terrain utilisé pour les acquisitions est :

```text
/home/samuel/Cave_explorer/data/cave_data/
```

Dans le conteneur, ce répertoire est accessible sous :

```text
/data/cave_data/
```

Les acquisitions utilisent un nom horodaté de la forme :

```text
cave_bag_YYYY-MM-DD_HH-MM-SS
```

Lors de l'arrêt du service, un signal `SIGINT` est envoyé au processus ROS 2
afin que le bag puisse être finalisé proprement.

---

## 6. Installation des fichiers

Les fichiers RevA de ce dossier permettent de reproduire la configuration
terrain vérifiée.

Le contrôleur Python est déployé sous :

```text
/home/samuel/Cave_explorer/switch2.py
```

Attribuez-lui les droits nécessaires :

```bash
sudo chmod +x /home/samuel/Cave_explorer/switch2.py
```

Les fichiers de service sont installés dans :

```text
/etc/systemd/system/
```

Par exemple, depuis ce dossier du dépôt :

```bash
sudo cp switch2.service /etc/systemd/system/
sudo cp backpack-driver.service /etc/systemd/system/
sudo cp cave_bag_record.service /etc/systemd/system/
```

Rechargez la configuration `systemd` :

```bash
sudo systemctl daemon-reload
```

Activez le contrôleur de l'interrupteur au démarrage :

```bash
sudo systemctl enable switch2.service
```

Démarrez-le immédiatement :

```bash
sudo systemctl start switch2.service
```

Pendant l'utilisation normale sur le terrain, `backpack-driver.service` et
`cave_bag_record.service` sont commandés automatiquement par `switch2.py`.

---

## 7. Vérification

Vérifiez le contrôleur de l'interrupteur :

```bash
systemctl status switch2.service
```

Vérifiez le service d'acquisition Docker/Livox :

```bash
systemctl status backpack-driver.service
```

Vérifiez le service d'enregistrement ROS 2 :

```bash
systemctl status cave_bag_record.service
```

Vérifiez que `switch2.py` est actif :

```bash
ps -ef | grep '[s]witch2.py'
```

Suivez le journal du contrôleur :

```bash
journalctl -u switch2.service -f
```

Suivez le journal du service d'enregistrement :

```bash
journalctl -u cave_bag_record.service -f
```

---

## 8. Utilisation normale sur le terrain

La séquence normale RevA est :

```text
1. Démarrer le Raspberry Pi.
2. Attendre le lancement de switch2.service.
3. Vérifier que l'interrupteur physique est sur OFF.
4. Placer l'interrupteur sur ON.
5. L'environnement Docker/Livox démarre.
6. Le service d'enregistrement attend 15 s.
7. ROS 2 enregistre /livox/lidar et /livox/imu.
8. Réaliser l'acquisition en grotte.
9. Replacer l'interrupteur sur OFF.
10. Le recorder ROS 2 reçoit SIGINT.
11. Le système attend 10 s pour finaliser les fichiers.
12. L'environnement Docker/Livox est arrêté.
```

Les acquisitions brutes peuvent ensuite être transférées vers le poste de
post-traitement avec :

```text
PROTO/scripts/Mac/0_mission_sync.sh
```

---

## 9. Note de reproductibilité RevA

L'architecture des services RevA décrite ici a été récupérée et vérifiée
directement sur le Raspberry Pi terrain.

La configuration de référence vérifiée était :

```text
switch2.service        activé et actif
switch-manager.service désactivé et inactif
hml_button.service     non installé
```

La chaîne d'acquisition de référence RevA repose donc sur :

```text
switch2.py
switch2.service
backpack-driver.service
cave_bag_record.service
```

Les anciens mécanismes expérimentaux de gestion du bouton ne font pas partie de
la configuration terrain RevA vérifiée.