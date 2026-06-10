# Guide 1 : Installation et Configuration Initiale du Raspberry Pi (Ubuntu 22.04 LTS 64-bit)

Ce guide détaille l'installation d'un système d'exploitation Linux 64-bit propre sur le Raspberry Pi de Chinook, optimisé pour l'utilisation de ROS 2 Humble.

## 1. Flash de la Carte SD
Pour garantir la compatibilité avec ROS 2 Humble, nous utilisons **Ubuntu Server 22.04 LTS (64-bit)**.

1. Télécharge et installe **Raspberry Pi Imager** sur ton Mac.
2. Insère la carte SD dans ton Mac.
3. Dans l'application :
   * **OS** : Choisis `Other general-purpose OS` > `Ubuntu` > **Ubuntu Server 22.04 LTS (64-bit)**.
   * **Storage** : Sélectionne ta carte SD.
4. Clique sur la roue crantée (Réglages avancés) pour pré-configurer le système :
   * Active SSH.
   * Définis l'utilisateur : (par ex) `samuel`.
   * Définis le mot de passe : (par ex) `chinook`.
   * Configure le Wi-Fi (si nécessaire pour le labo).
5. Clique sur **Write** pour flasher.

## 2. Premier démarrage et configuration réseau
Insère la carte SD dans le Raspberry Pi et démarre-le. Connecte-toi via le terminal de ton Mac :

ssh samuel@chinook.local

# (Le mot de passe configuré est : par ex chinook)

##3. Mise à jour du système
## Une fois connecté, mets à jour tous les paquets système avec la commande 

sudo apt update && sudo apt upgrade -y

## 4. Désactivation de la mise en veille réseau (Crucial)
Pour éviter que le Raspberry Pi ne coupe le Wi-Fi ou la carte réseau en pleine exploration, désactive la gestion de l'énergie Wi-Fi avec la commande suivante :

sudo iw dev wlan0 set power_save off

Le Raspberry Pi est maintenant prêt à recevoir ROS 2.