# 1. Utiliser l'image officielle Ubuntu Jammy (compatible ROS 2 Humble)
FROM ubuntu:22.04

# Éviter les questions interactives lors de l'installation des paquets
ENV DEBIAN_FRONTEND=noninteractive

# 2. Configurer la langue (Locale) indispensable pour ROS 2
RUN apt-get update && apt-get install -y locales && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8

# 3. Installer les outils de base et configurer les dépôts ROS 2
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    software-properties-common \
    && add-apt-repository universe -y

# Ajout de la clé GPG officielle de ROS 2
RUN curl -sSL https://raw.githubusercontent.com/ros2/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# Ajout du dépôt ROS 2 dans les sources d'apt
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 4. Installer ROS 2 Humble (version ROS-Base, optimisée sans interface graphique)
RUN apt-get update && apt-get install -y \
    ros-humble-ros-base \
    ros-humble-rosbridge-server \
    python3-colcon-common-extensions \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# 5. Installer les dépendances Python nécessaires pour DLIO et lidar_to_vtopo.py
# On installe 'rosbags' pour la lecture directe et 'scipy'/'numpy' pour les calculs géométriques
RUN pip3 install --no-cache-dir \
    numpy \
    scipy \
    pandas \
    rosbags

# 6. Configurer l'environnement de travail dans le conteneur
WORKDIR /root/ros2_ws

# Ajouter le sourcing automatique de ROS 2 pour tous les terminaux interactifs
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

# Commande par défaut (garde le conteneur ouvert en attente d'ordres)
CMD ["bash"]