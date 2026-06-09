# Guide 2 : Installation de ROS 2 Humble et Configuration du SWAP

Ce guide explique comment installer ROS 2 Humble sur le Raspberry Pi et détaille l'astuce indispensable du SWAP pour permettre la compilation de gros packages (comme DLIO ou Livox) sans faire planter le Pi par manque de RAM.

## 1. L'Astuce Secrète : Augmentation de la mémoire SWAP
#========================================================
Par défaut, le Raspberry Pi possède 4 Go ou 8 Go de RAM. Lors de la compilation avec `colcon build`, le processeur utilise tellement de mémoire que le Pi fige (Crash/Freeze total). Nous allons forcer le système à utiliser la carte SD comme mémoire de secours (SWAP) à hauteur de **4 Go**.

# 1. Désactiver le swap existant
sudo swapoff -a

# 2. Redimensionner le fichier de swap 4Go (4096 Mo) (augmente au besoin)
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096

# 3. Sécuriser les permissions du fichier
sudo chmod 600 /swapfile

# 4. Préparer le fichier comme espace d'échange
sudo mkswap /swapfile

# 5. Activer le nouveau swap
sudo swapon /swapfile

# Pour rendre ce changement permanent après chaque redémarrage, modifie le fichier /etc/fstab :

sudo nano /etc/fstab

# Ajoute cette ligne tout à la fin du fichier :

/swapfile none swap sw 0 0
# Sauvegarde avec Ctrl+O puis quitte avec Ctrl+X.
# Vérifie que tes 4 Go de SWAP sont bien actifs avec la commande : 
free -h.

# 2. Installation de ROS 2 Humble

#A. Configuration des sources et clés

sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale lcl_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# Ajout du dépôt ROS 2
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y

# Ajout de la clé GPG
sudo apt update && sudo apt install curl -y
sudo curl -sSL [https://raw.githubusercontent.com/ros2/rosdn/master/ros.key](https://raw.githubusercontent.com/ros2/rosdn/master/ros.key) -o /usr/share/keyrings/ros-archive-keyring.gpg

# Ajout du dépôt officiel aux sources
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] [http://packages.ros.org/ros2/ubuntu](http://packages.ros.org/ros2/ubuntu) $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# B. Installation des paquets ROS 2 Base (Optimisé pour systèmes)
# Sur le Raspberry Pi, nous n'installons pas la version Desktop (pas de Rviz ou de GUI) pour économiser l'espace et les ressources :

sudo apt update
sudo apt install ros-humble-ros-base python3-colcon-common-extensions -y

# C. Ajout du Sourcing Automatique
# Pour que la commande ros2 soit reconnue à chaque ouverture de terminal :

echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# ROS 2 est installé. Tu peux maintenant cloner tes workspaces dans /home/samuel/Cave_explorer/ros2_ws et compiler en toute sécurité grâce au SWAP. Tu prendras la peine de nommer d'autres liens que /samuel/ ... tu utiliseras ton ${USER} !
