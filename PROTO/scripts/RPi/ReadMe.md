# HML-LiDAR RevA — Raspberry Pi scripts

## English version

This directory contains the scripts intended to run on the Raspberry Pi used
by the HML-LiDAR acquisition system.

These scripts support hardware control, recording management and interaction
with the physical acquisition switch.

### Executable permissions

When a Python script is launched by a system service, make sure that the file
has the appropriate execution permissions.

For example:

```bash
sudo chmod +x /home/samuel/Cave_explorer/switch2.py
```

This command should be executed after copying the script to the Raspberry Pi
and before starting the corresponding system service.

After creating or modifying a systemd service, reload the systemd
configuration:

```bash
sudo systemctl daemon-reload
```

The absolute path `/opt/hml/` must correspond to the actual location of the
script on the Raspberry Pi.

For the complete systemd configuration procedure, see:

```text
../../documentation/3-INSTALL_SERVICES.md
```

Raspberry Pi boot
    ↓
switch2.service  [enabled]
    ↓
switch2.py
    GPIO 4
    pull_up=True
    debounce=0.5 s
    ↓
switch ON
    ├─ start backpack-driver.service
    │      ↓
    │   docker compose up
    │      ↓
    │   cave_explorer-livox-1
    │
    └─ start cave_bag_record.service
           ↓
        wait 15 s
           ↓
        ros2 bag record
        /livox/lidar
        /livox/imu

switch OFF
    ↓
stop cave_bag_record.service
    ↓
SIGINT → finalisation du bag
    ↓
wait 10 s
    ↓
stop backpack-driver.service
    ↓
docker compose down

The same procedure is to do with 
switch2.py
switch2.service
backpack-driver.service
cave_bag_record.service

---

## Version française

Ce dossier contient les scripts destinés à être exécutés sur le Raspberry Pi
du système d'acquisition HML-LiDAR.

Ces scripts assurent notamment le contrôle matériel, la gestion des
enregistrements et l'interaction avec l'interrupteur physique d'acquisition.

### Droits d'exécution

L'attribution des droits d'exécution au script Python est impérative lorsqu'il
doit être invoqué en arrière-plan par un service système.

Par exemple :

```bash
sudo chmod +x /home/samuel/Cave_explorer/switch2.py
```

Cette instruction doit être exécutée après la copie du fichier
`button_daemon.py` sur le Raspberry Pi et avant le lancement du service
correspondant.

Après la création ou la modification d'un service systemd, rechargez la
configuration :

```bash
sudo systemctl daemon-reload
```

Le chemin absolu `/opt/hml/` doit correspondre à l'emplacement réel du script
sur le Raspberry Pi.

Pour la procédure complète de configuration des services systemd, voir :

```text
../../documentation/3-INSTALL_SERVICES.md
```

Raspberry Pi boot
    ↓
switch2.service  [enabled]
    ↓
switch2.py
    GPIO 4
    pull_up=True
    debounce=0.5 s
    ↓
switch ON
    ├─ start backpack-driver.service
    │      ↓
    │   docker compose up
    │      ↓
    │   cave_explorer-livox-1
    │
    └─ start cave_bag_record.service
           ↓
        wait 15 s
           ↓
        ros2 bag record
        /livox/lidar
        /livox/imu

switch OFF
    ↓
stop cave_bag_record.service
    ↓
SIGINT → finalisation du bag
    ↓
wait 10 s
    ↓
stop backpack-driver.service
    ↓
docker compose down

La même procédure est à appliquer pour les services :
switch2.py
switch2.service
backpack-driver.service
cave_bag_record.service