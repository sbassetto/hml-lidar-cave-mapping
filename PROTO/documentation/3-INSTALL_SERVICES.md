# HML-LiDAR RevA — Raspberry Pi field services

## English version

# Guide 3: Installation and automation of the field services

The HML-LiDAR RevA Raspberry Pi uses `systemd` services to manage the
physical acquisition switch, the Docker-based Livox acquisition environment,
and ROS 2 bag recording.

The configuration described in this document was verified directly on the
RevA field Raspberry Pi, named `chinook`.

The active field architecture is:

```text
Raspberry Pi boot
        ↓
switch2.service
        ↓
switch2.py
GPIO 4 / physical pin 7
pull-up enabled
500 ms debounce
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

The three RevA service files are stored in:

```text
PROTO/scripts/RPi/
```

as:

```text
switch2.service
backpack-driver.service
cave_bag_record.service
```

The physical-switch controller is:

```text
switch2.py
```

---

## 1. Physical-switch controller

### Program

`switch2.py`

The RevA field system uses a physical switch connected to GPIO 4
(physical pin 7).

The GPIO input is configured with an internal pull-up resistor and a
500 ms debounce interval:

```python
switch = Button(4, pull_up=True, bounce_time=0.5)
```

When the switch is moved to the ON position, `switch2.py` starts, in order:

```text
backpack-driver.service
cave_bag_record.service
```

When the switch is moved back to OFF, the program:

1. stops `cave_bag_record.service`;
2. waits 10 seconds to allow recording finalization;
3. stops `backpack-driver.service`.

The field version also contains a startup safeguard. If the Raspberry Pi
boots while the physical switch is already in the ON position, the program
waits until the switch is returned to OFF before arming the event handlers.

This avoids an unintended acquisition start immediately during boot.

---

## 2. Switch monitoring service

### Service

`switch2.service`

This is the system service that keeps `switch2.py` running continuously.

The service installed on the RevA field Raspberry Pi was:

```ini
[Unit]
Description=Service de monitoring du bouton Lidar
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/samuel/Cave_explorer/switch2.py
WorkingDirectory=/home/samuel/Cave_explorer
StandardOutput=inherit
StandardError=inherit
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

On the verified field system, `switch2.service` was enabled and running.

The process was observed as:

```text
/usr/bin/python3 /home/samuel/Cave_explorer/switch2.py
```

with `root` privileges and `systemd` as its parent process.

A second historical unit named `switch-manager.service` was also present on
the Raspberry Pi, but it was verified as:

```text
disabled
inactive
```

It is therefore not part of the RevA reference configuration.

No active `hml_button.service` was present on the verified field Raspberry Pi.

---

## 3. Docker/Livox acquisition service

### Service

`backpack-driver.service`

This service starts the Docker Compose environment used for the Livox
LiDAR/IMU acquisition stack.

The field service was:

```ini
[Unit]
Description=Backpack Docker Driver Service
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=simple
User=samuel
Group=samuel
WorkingDirectory=/home/samuel/Cave_explorer/

ExecStartPre=-/usr/bin/docker compose down
ExecStart=/usr/bin/docker compose up --remove-orphans

ExecStop=/usr/bin/docker compose down

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

The working directory contains the field Docker configuration, including the
`docker-compose.yml` used by RevA.

When started, the service brings up the Docker acquisition environment.

The ROS 2 bag recording service subsequently addresses the acquisition
container by its field name:

```text
cave_explorer-livox-1
```

When the physical switch is returned to OFF, `switch2.py` stops the recording
service first, waits 10 seconds, and then stops `backpack-driver.service`.

---

## 4. ROS 2 bag recording service

### Service

`cave_bag_record.service`

This service performs the actual ROS 2 recording.

The service installed on the RevA field Raspberry Pi was:

```ini
[Unit]
Description=ROS 2 Bag Recorder for Cave Data (in livox container)
After=network.target docker.service backpack-driver.service
Requires=docker.service backpack-driver.service

[Service]
Type=simple
User=root

ExecStartPre=/bin/mkdir -p /home/samuel/Cave_explorer/data/cave_data
ExecStartPre=/bin/sleep 15

ExecStart=/usr/bin/docker exec -t cave_explorer-livox-1 \
  bash -c 'source /opt/ros/humble/setup.bash && \
    source /dev_ws/install/setup.bash && \
    ros2 bag record \
      -o /data/cave_data/cave_bag_$(date +%%Y-%%m-%%d_%%H-%%M-%%S) \
      /livox/lidar \
      /livox/imu'

ExecStop=/usr/bin/docker exec -t cave_explorer-livox-1 pkill -INT ros2

KillSignal=SIGINT
TimeoutStopSec=20
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Before recording begins, the service:

```text
creates /home/samuel/Cave_explorer/data/cave_data
waits 15 seconds
starts ros2 bag record inside cave_explorer-livox-1
```

The recorded topics are:

```text
/livox/lidar
/livox/imu
```

Each acquisition is written under:

```text
/data/cave_data/
```

using a timestamped name of the form:

```text
cave_bag_YYYY-MM-DD_HH-MM-SS
```

When the service is stopped, a `SIGINT` is sent to the ROS 2 process so that
the bag can be finalized before the Docker acquisition environment is shut
down.

---

## 5. Installing the RevA service files

The reference service files are supplied in:

```text
PROTO/scripts/RPi/
```

Copy them to the Raspberry Pi systemd directory:

```bash
sudo cp switch2.service /etc/systemd/system/
sudo cp backpack-driver.service /etc/systemd/system/
sudo cp cave_bag_record.service /etc/systemd/system/
```

The field paths contained in these units correspond to:

```text
/home/samuel/Cave_explorer/
```

For another Raspberry Pi installation, adapt the username and absolute paths
before installing the services.

Reload the `systemd` configuration:

```bash
sudo systemctl daemon-reload
```

The physical-switch monitoring service is the service intended to start
automatically during boot:

```bash
sudo systemctl enable switch2.service
sudo systemctl start switch2.service
```

`backpack-driver.service` and `cave_bag_record.service` are normally controlled
by `switch2.py` according to the position of the physical switch.

They do not need to be manually started during normal field operation.

---

## 6. Verification

Check that the physical-switch monitoring service is active:

```bash
systemctl status switch2.service
```

Check the acquisition-driver service:

```bash
systemctl status backpack-driver.service
```

Check the recording service:

```bash
systemctl status cave_bag_record.service
```

Follow the switch-monitoring log:

```bash
journalctl -u switch2.service -f
```

Follow the recording-service log:

```bash
journalctl -u cave_bag_record.service -f
```

The active Python process can also be verified with:

```bash
ps -ef | grep '[s]witch2.py'
```

---

## 7. Normal field operation

After boot, `switch2.service` starts the GPIO monitoring program.

The normal acquisition procedure is therefore:

```text
boot Raspberry Pi
        ↓
wait for switch2.service
        ↓
switch OFF = system armed
        ↓
move switch to ON
        ↓
Docker/Livox stack starts
        ↓
15 s initialization delay
        ↓
ROS 2 LiDAR + IMU recording
        ↓
perform cave acquisition
        ↓
move switch to OFF
        ↓
ROS 2 recording receives SIGINT
        ↓
10 s finalization delay
        ↓
Docker/Livox stack stops
```

If the Raspberry Pi starts while the physical switch is already ON,
`switch2.py` waits for the operator to move it back to OFF before arming the
system.

---

## 8. RevA reproducibility note

The service definitions reproduced in this document were recovered directly
from the RevA field Raspberry Pi and correspond to the operating configuration
used on `chinook`.

The field configuration specifically confirmed:

```text
switch2.service        enabled and active
switch-manager.service disabled and inactive
hml_button.service     not installed
```

The repository therefore uses `switch2.service` and `switch2.py` as the
reference physical-switch control mechanism for RevA.

Older or experimental button-control files should not be interpreted as part
of the verified RevA acquisition chain.

---

# Version française

# Guide 3 : Installation et automatisation des services de terrain

Le Raspberry Pi du HML-LiDAR RevA utilise des services `systemd` pour gérer
l'interrupteur physique d'acquisition, l'environnement Docker du LiDAR Livox
et l'enregistrement des données ROS 2.

La configuration décrite dans ce document a été vérifiée directement sur le
Raspberry Pi de terrain RevA nommé `chinook`.

L'architecture terrain active est la suivante :

```text
Démarrage du Raspberry Pi
        ↓
switch2.service
        ↓
switch2.py
GPIO 4 / broche physique 7
pull-up activé
anti-rebond = 500 ms
        ↓
interrupteur sur ON
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

interrupteur sur OFF
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

Les trois fichiers de service RevA sont conservés dans :

```text
PROTO/scripts/RPi/
```

sous les noms :

```text
switch2.service
backpack-driver.service
cave_bag_record.service
```

Le programme de contrôle de l'interrupteur est :

```text
switch2.py
```

---

## 1. Contrôleur de l'interrupteur physique

### Programme

`switch2.py`

Le système terrain RevA utilise un interrupteur physique connecté au GPIO 4
(broche physique 7).

L'entrée GPIO utilise la résistance de rappel interne et un anti-rebond de
500 ms :

```python
switch = Button(4, pull_up=True, bounce_time=0.5)
```

Lorsque l'interrupteur est placé sur ON, `switch2.py` démarre successivement :

```text
backpack-driver.service
cave_bag_record.service
```

Lorsque l'interrupteur revient sur OFF, le programme :

1. arrête `cave_bag_record.service`;
2. attend 10 secondes pour permettre la finalisation de l'enregistrement;
3. arrête `backpack-driver.service`.

La version terrain comprend également une sécurité au démarrage. Si le
Raspberry Pi démarre alors que l'interrupteur est déjà placé sur ON, le
programme attend son retour sur OFF avant d'armer les gestionnaires
d'événements.

Cela évite le démarrage involontaire d'une acquisition immédiatement après le
démarrage du Raspberry Pi.

---

## 2. Service de surveillance de l'interrupteur

### Service

`switch2.service`

Ce service maintient `switch2.py` actif en permanence.

Le service installé sur le Raspberry Pi terrain RevA était :

```ini
[Unit]
Description=Service de monitoring du bouton Lidar
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/samuel/Cave_explorer/switch2.py
WorkingDirectory=/home/samuel/Cave_explorer
StandardOutput=inherit
StandardError=inherit
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

Sur le système terrain vérifié, `switch2.service` était activé et en cours
d'exécution.

Le processus observé était :

```text
/usr/bin/python3 /home/samuel/Cave_explorer/switch2.py
```

avec les privilèges `root` et `systemd` comme processus parent.

Une seconde unité historique nommée `switch-manager.service` était également
présente sur le Raspberry Pi, mais son état vérifié était :

```text
disabled
inactive
```

Elle ne fait donc pas partie de la configuration RevA de référence.

Aucun service actif nommé `hml_button.service` n'était installé sur le
Raspberry Pi terrain vérifié.

---

## 3. Service Docker/Livox

### Service

`backpack-driver.service`

Ce service démarre l'environnement Docker Compose utilisé pour l'acquisition
LiDAR/IMU Livox.

Le service terrain était :

```ini
[Unit]
Description=Backpack Docker Driver Service
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=simple
User=samuel
Group=samuel
WorkingDirectory=/home/samuel/Cave_explorer/

ExecStartPre=-/usr/bin/docker compose down
ExecStart=/usr/bin/docker compose up --remove-orphans

ExecStop=/usr/bin/docker compose down

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Le répertoire de travail contient la configuration Docker terrain et notamment
le fichier `docker-compose.yml` utilisé par RevA.

Lors du démarrage, ce service met en route l'environnement Docker
d'acquisition.

Le service d'enregistrement ROS 2 communique ensuite avec le conteneur terrain
nommé :

```text
cave_explorer-livox-1
```

Lorsque l'interrupteur physique est replacé sur OFF, `switch2.py` arrête
d'abord le service d'enregistrement, attend 10 secondes, puis arrête
`backpack-driver.service`.

---

## 4. Service d'enregistrement ROS 2

### Service

`cave_bag_record.service`

Ce service réalise l'enregistrement effectif des données ROS 2.

Le service installé sur le Raspberry Pi terrain RevA était :

```ini
[Unit]
Description=ROS 2 Bag Recorder for Cave Data (in livox container)
After=network.target docker.service backpack-driver.service
Requires=docker.service backpack-driver.service

[Service]
Type=simple
User=root

ExecStartPre=/bin/mkdir -p /home/samuel/Cave_explorer/data/cave_data
ExecStartPre=/bin/sleep 15

ExecStart=/usr/bin/docker exec -t cave_explorer-livox-1 \
  bash -c 'source /opt/ros/humble/setup.bash && \
    source /dev_ws/install/setup.bash && \
    ros2 bag record \
      -o /data/cave_data/cave_bag_$(date +%%Y-%%m-%%d_%%H-%%M-%%S) \
      /livox/lidar \
      /livox/imu'

ExecStop=/usr/bin/docker exec -t cave_explorer-livox-1 pkill -INT ros2

KillSignal=SIGINT
TimeoutStopSec=20
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Avant le début de l'enregistrement, le service :

```text
crée /home/samuel/Cave_explorer/data/cave_data
attend 15 secondes
démarre ros2 bag record dans cave_explorer-livox-1
```

Les topics enregistrés sont :

```text
/livox/lidar
/livox/imu
```

Chaque acquisition est enregistrée sous :

```text
/data/cave_data/
```

avec un nom horodaté de la forme :

```text
cave_bag_YYYY-MM-DD_HH-MM-SS
```

Lorsque le service est arrêté, un signal `SIGINT` est envoyé au processus ROS 2
afin de permettre la finalisation du bag avant l'arrêt de l'environnement
Docker d'acquisition.

---

## 5. Installation des services RevA

Les fichiers de référence sont fournis dans :

```text
PROTO/scripts/RPi/
```

Copiez-les dans le répertoire `systemd` du Raspberry Pi :

```bash
sudo cp switch2.service /etc/systemd/system/
sudo cp backpack-driver.service /etc/systemd/system/
sudo cp cave_bag_record.service /etc/systemd/system/
```

Les chemins contenus dans les unités terrain correspondent à :

```text
/home/samuel/Cave_explorer/
```

Pour une autre installation, le nom d'utilisateur et les chemins absolus
doivent être adaptés avant l'installation des services.

Rechargez ensuite la configuration `systemd` :

```bash
sudo systemctl daemon-reload
```

Le service destiné à être lancé automatiquement au démarrage est le service de
surveillance de l'interrupteur :

```bash
sudo systemctl enable switch2.service
sudo systemctl start switch2.service
```

`backpack-driver.service` et `cave_bag_record.service` sont normalement pilotés
par `switch2.py` en fonction de la position de l'interrupteur physique.

Ils n'ont donc pas à être démarrés manuellement pendant l'utilisation normale
sur le terrain.

---

## 6. Vérifications

Vérifiez l'état du service de surveillance de l'interrupteur :

```bash
systemctl status switch2.service
```

Vérifiez l'état du service des pilotes d'acquisition :

```bash
systemctl status backpack-driver.service
```

Vérifiez l'état du service d'enregistrement :

```bash
systemctl status cave_bag_record.service
```

Suivez en direct le journal du contrôleur de l'interrupteur :

```bash
journalctl -u switch2.service -f
```

Suivez le journal du service d'enregistrement :

```bash
journalctl -u cave_bag_record.service -f
```

Le processus Python actif peut également être vérifié avec :

```bash
ps -ef | grep '[s]witch2.py'
```

---

## 7. Utilisation normale sur le terrain

Après le démarrage du Raspberry Pi, `switch2.service` lance le programme de
surveillance du GPIO.

La procédure normale d'acquisition est donc :

```text
démarrage du Raspberry Pi
        ↓
démarrage de switch2.service
        ↓
interrupteur OFF = système armé
        ↓
placer l'interrupteur sur ON
        ↓
démarrage de l'environnement Docker/Livox
        ↓
temporisation d'initialisation de 15 s
        ↓
enregistrement ROS 2 LiDAR + IMU
        ↓
réalisation de l'acquisition en grotte
        ↓
replacer l'interrupteur sur OFF
        ↓
envoi de SIGINT à l'enregistrement ROS 2
        ↓
temporisation de finalisation de 10 s
        ↓
arrêt de l'environnement Docker/Livox
```

Si le Raspberry Pi démarre alors que l'interrupteur physique est déjà placé
sur ON, `switch2.py` attend que l'opérateur le replace sur OFF avant d'armer le
système.

---

## 8. Note de reproductibilité RevA

Les définitions de services reproduites dans ce document ont été récupérées
directement sur le Raspberry Pi terrain RevA et correspondent à la
configuration opérationnelle de `chinook`.

La vérification du système terrain a notamment confirmé :

```text
switch2.service        activé et actif
switch-manager.service désactivé et inactif
hml_button.service     non installé
```

Le dépôt utilise donc `switch2.service` et `switch2.py` comme mécanisme de
référence pour le contrôle de l'interrupteur physique de RevA.

Les anciens fichiers ou mécanismes expérimentaux de gestion du bouton ne
doivent pas être interprétés comme faisant partie de la chaîne d'acquisition
RevA vérifiée.