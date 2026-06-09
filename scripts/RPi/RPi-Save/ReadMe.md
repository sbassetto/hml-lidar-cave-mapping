# Docker setup for Livox Mid360 LiDAR on Raspberry Pi 5

This document guides you through setting up and running the Livox Mid360 LiDAR driver inside a Docker container on a Raspberry Pi 5.

---

## Prerequisites

* Docker and Docker Compose installed on the host. Be sure to be on the same subnet as the lidar (24). Lidar's ip is 192.168.1.3

---

## 1. Initial Setup

1. Clone this repository and navigate into it.

2. Make the setup script executable and run it:

   ```bash
   chmod +x initial_setup.sh
   ./initial_setup.sh
   ```

   This will install any required dependencies on the host.

3. Place your `msg_MID360_launch.py` configuration file into the `livox_ros_driver2` package (or adjust paths accordingly).

---

## 2. Running the Container

### Launch Docker

Start the container in detached mode:

```bash
docker compose up
```

### Stop Docker

Shut down and remove the container:

```bash
docker compose down
```

### Access the Container Shell

Open an interactive bash session inside the running container:

```bash
docker exec -it docker_driver-livox-1 bash
```

---

## 3. Inside the Container

### Full stack launch

```bash
source install/setup.bash
ros2 launch livox_ros_driver2 stack_launch.py

```bash
cd ../dev_ws
source install/setup.bash
ros2 launch bringup pc2_to_scan.launch.py
```

### Build & Source ROS 2 Workspace

### Launch odometry feed

```bash
cd ../dev_ws
source install/setup.bash
ros2 run py_avoid odom
```

```bash
source install/setup.bash
ros2 launch ego_planner single_run_real.launch.py
```


```bash
source install/setup.bash
ros2 launch ego_planner rviz.launch.py
```



### Launch the Livox Driver

```bash
source install/setup.bash
ros2 launch livox_ros_driver2 msg_MID360_launch.py
```

```bash
source install/setup.bash
ros2 launch mavros apm.launch fcu_url:=udp://127.0.0.1:14551@14551
```

```bash
cd ../dev_ws
source install/setup.bash
ros2 run py_avoid odom
```


```bash
sudo ip route del default dev end0
```

### Launch Odometry & Mapping

```bash
source install/setup.bash
ros2 launch super_odometry livox_mid360.launch.py
```

## 3. Recording data and tmux

### Creating a tmux session

```bash
tmux new -s rec
```

In this bash, once recording started : Ctrl-B and D, to close

### To reopen session later

```bash
tmux attach -t rec
```

### To kill tmux

```bash
tmux kill-session -t rec
```

## 4. Next Steps

* Integrate obstacle avoidance.
* Implement high-level pathfinding and planning.
* Tune parameters to your environment and use case.

---

*For more details or troubleshooting, refer to the official Livox ROS Driver documentation or open an issue in this repository.*

---
Rev du 21 Avril 2026. SB

* pour un dispositif autonome : créer 3 services : (1) docker (2) backpack-driver.service et (3) cave_bag_record.service


### service de docker (normalement fait automatiquement lorsque l'on a installé le docker...mais je le mets ici au cas où...
# /usr/lib/systemd/system/docker.service
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target nss-lookup.target docker.socket firewalld.service containerd.service time-set.target
Wants=network-online.target containerd.service
Requires=docker.socket
StartLimitBurst=3
StartLimitIntervalSec=60

[Service]
Type=notify
# the default is not to use systemd for cgroups because the delegate issues still
# exists and systemd currently does not support the cgroup feature set required
# for containers run by docker
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutStartSec=0
RestartSec=2
Restart=always

# Having non-zero Limit*s causes performance problems due to accounting overhead
# in the kernel. We recommend using cgroups to do container-local accounting.
LimitNPROC=infinity
LimitCORE=infinity

# Comment TasksMax if your systemd version does not support it.
# Only systemd 226 and above support this option.
TasksMax=infinity

# set delegate yes so that systemd does not reset the cgroups of docker containers
Delegate=yes

# kill only the docker process, not all processes in the cgroup
KillMode=process
OOMScoreAdjust=-500

[Install]
WantedBy=multi-user.target


### service pour lancer le driver du lidar.(on doit s'assurer d'avoir mis en place un service de docker.

# /etc/systemd/system/backpack-driver.service
[Unit]
Description=Backpack Docker Driver Service
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=simple
# Run as the user 'backpack' to avoid permission issues in the home directory
User=samuel
Group=samuel
WorkingDirectory=/home/samuel/Cave_explorer/

# Startup: Remove old containers (optional but safer) and bring up the new ones
ExecStartPre=-/usr/bin/docker compose down
ExecStart=/usr/bin/docker compose up --remove-orphans

# Shutdown: Gracefully stop and remove containers
ExecStop=/usr/bin/docker compose down

# Restart policy: If it crashes, wait 10s and restart
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target


#### service d'enregistrement 
# /etc/systemd/system/cave_bag_record.service
[Unit]
Description=ROS 2 Bag Recorder for Cave Data (in livox container)
# On attend que le réseau et le driver Docker soient prêts
After=network.target docker.service backpack-driver.service
Requires=docker.service backpack-driver.service

[Service]
Type=simple
User=root
# Création du dossier si inexistant (chemin absolu obligatoire)
ExecStartPre=/bin/mkdir -p /home/samuel/Cave_explorer/data/cave_data
# Délai indispensable pour laisser le conteneur 'livox' passer en état 'Up' au démarrage
ExecStartPre=/bin/sleep 15
# Utilisation de 'docker exec' avec le nom exact du conteneur pour plus de fiabilité
ExecStart=/usr/bin/docker exec -t cave_explorer-livox-1 \
  bash -c 'source /opt/ros/humble/setup.bash && \
    source /dev_ws/install/setup.bash && \
    ros2 bag record \
      -o /data/cave_data/cave_bag_$(date +%%Y-%%m-%%d_%%H-%%M-%%S) \
      /livox/lidar \
      /livox/imu'

# Arrêt propre avec le signal INT pour ne pas corrompre le fichier .db3
ExecStop=/usr/bin/docker exec -t cave_explorer-livox-1 pkill -INT ros2
KillSignal=SIGINT
TimeoutStopSec=20
# Relance automatique si le démarrage échoue (ex: docker encore trop lent)
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target


* Pour le bouton : Créer un service (fichier qui s'appelle switch2.service) avec le code suivant

# /etc/systemd/system/switch2.service
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

Vous pourrez modifier le fichier python switch2.py pour les différents timers (500ms pour le debouncing et 10s pour clôturer l'enregistrement proprement).

---
