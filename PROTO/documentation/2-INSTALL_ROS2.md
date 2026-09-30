# English version

# Guide 2: ROS 2 Humble Installation and SWAP Configuration

This guide explains how to install ROS 2 Humble on the Raspberry Pi and
describes the use of additional SWAP space to support the compilation of large
packages such as DLIO or Livox components without exhausting the available RAM.

## 1. Increase SWAP memory

By default, the Raspberry Pi may have 4 GB or 8 GB of RAM. During compilation
with `colcon build`, memory usage can become high enough to freeze the system.

The following procedure creates a 4 GB SWAP file on the storage device.

### 1. Disable the existing swap

```bash
sudo swapoff -a
```

### 2. Create a 4 GB swap file

```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
```

The size may be increased if necessary.

### 3. Set secure permissions

```bash
sudo chmod 600 /swapfile
```

### 4. Format the file as swap space

```bash
sudo mkswap /swapfile
```

### 5. Enable the new swap

```bash
sudo swapon /swapfile
```

To make the change persistent after reboot, edit:

```bash
sudo nano /etc/fstab
```

Add the following line at the end of the file:

```text
/swapfile none swap sw 0 0
```

Save with `Ctrl+O` and exit with `Ctrl+X`.

Verify that the SWAP space is active:

```bash
free -h
```

## 2. Install ROS 2 Humble

### A. Configure repositories and keys

```bash
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale lcl_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

Install the required repository-management tools:

```bash
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y
```

Install `curl` and retrieve the ROS 2 GPG key:

```bash
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros2/rosdn/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
```

Add the ROS 2 repository:

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### B. Install ROS 2 Base packages

On the Raspberry Pi, the lightweight ROS 2 Base installation is used instead
of the Desktop version in order to reduce disk-space and resource usage.

```bash
sudo apt update
sudo apt install ros-humble-ros-base python3-colcon-common-extensions -y
```

### C. Configure automatic ROS 2 sourcing

To make the `ros2` command available automatically in new terminal sessions:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

ROS 2 Humble is now installed.

The project workspaces can then be created under a user-specific directory,
for example:

```text
/home/${USER}/Cave_explorer/ros2_ws
```

The additional SWAP space is intended to reduce the risk of memory exhaustion
during compilation.

---

# Version française
# Guide 2 : Installation de ROS 2 Humble et Configuration du SWAP

Ce guide explique comment installer ROS 2 Humble sur le Raspberry Pi et détaille l'astuce indispensable du SWAP pour permettre la compilation de gros packages (comme DLIO ou Livox) sans faire planter le Pi par manque de RAM.

## 1. L'Astuce :  Augmentation de la mémoire SWAP

Par défaut, le Raspberry Pi possède 4 Go ou 8 Go de RAM. Lors de la compilation avec `colcon build`, le processeur utilise tellement de mémoire que le Pi fige (Crash/Freeze total). Nous allons forcer le système à utiliser la carte SD comme mémoire de secours (SWAP) à hauteur de **4 Go**.

# 1. Désactiver le swap existant
```bash
sudo swapoff -a
```

# 2. Redimensionner le fichier de swap 4Go (4096 Mo) (augmente au besoin)

```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
```
# 3. Sécuriser les permissions du fichier

```bash
sudo chmod 600 /swapfile
```

# 4. Préparer le fichier comme espace d'échange
```bash
sudo mkswap /swapfile
```

# 5. Activer le nouveau swap
```bash
sudo swapon /swapfile
```

# Pour rendre ce changement permanent après chaque redémarrage, modifie le fichier /etc/fstab :

```bash
sudo nano /etc/fstab
```

# Ajoute cette ligne tout à la fin du fichier :

```bash
/swapfile none swap sw 0 0
```

# Sauvegarde avec Ctrl+O puis quitte avec Ctrl+X.
# Vérifie que tes 4 Go de SWAP sont bien actifs avec la commande : 

```bash
free -h.
```

# 2. Installation de ROS 2 Humble

#A. Configuration des sources et clés

```bash
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale lcl_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

# Ajout du dépôt ROS 2
```bash
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y
```

# Ajout de la clé GPG
```bash
sudo apt update && sudo apt install curl -y
sudo curl -sSL [https://raw.githubusercontent.com/ros2/rosdn/master/ros.key](https://raw.githubusercontent.com/ros2/rosdn/master/ros.key) -o /usr/share/keyrings/ros-archive-keyring.gpg
```

# Ajout du dépôt officiel aux sources

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] [http://packages.ros.org/ros2/ubuntu](http://packages.ros.org/ros2/ubuntu) $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

# B. Installation des paquets ROS 2 Base (Optimisé pour systèmes)
# Sur le Raspberry Pi, nous n'installons pas la version Desktop (pas de Rviz ou de GUI) pour économiser l'espace et les ressources :

```bash
sudo apt update
sudo apt install ros-humble-ros-base python3-colcon-common-extensions -y
```

# C. Ajout du Sourcing Automatique
# Pour que la commande ros2 soit reconnue à chaque ouverture de terminal :

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

# ROS 2 est installé. Tu peux maintenant cloner tes workspaces dans /home/samuel/Cave_explorer/ros2_ws et compiler en toute sécurité grâce au SWAP. Tu prendras la peine de nommer d'autres liens que /samuel/ ... tu utiliseras ton ${USER} !
