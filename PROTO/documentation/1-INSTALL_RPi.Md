# Guide 1: Initial Raspberry Pi Installation and Configuration
## Ubuntu 22.04 LTS 64-bit

This guide describes the installation of a clean 64-bit Linux operating
system on the Chinook Raspberry Pi, configured for use with ROS 2 Humble.

## 1. Flash the SD card

To ensure compatibility with ROS 2 Humble, the system uses
**Ubuntu Server 22.04 LTS (64-bit)**.

1. Download and install **Raspberry Pi Imager** on the Mac.
2. Insert the SD card into the Mac.
3. In Raspberry Pi Imager:
   - **OS:** select `Other general-purpose OS` > `Ubuntu` >
     **Ubuntu Server 22.04 LTS (64-bit)**.
   - **Storage:** select the target SD card.
4. Open the advanced settings and preconfigure the system:
   - enable SSH;
   - define the user, for example `samuel`;
   - define the password, for example `chinook`;
   - configure Wi-Fi if required.
5. Click **Write** to flash the SD card.

## 2. First boot and network configuration

Insert the SD card into the Raspberry Pi and start the system.

Connect to it from a terminal on the Mac:

```bash
ssh samuel@chinook.local
```
Use the password defined during system configuration, for example chinook.

# 3. System update
Once connected, update the system packages:
```bash
sudo apt update && sudo apt upgrade -y
```
# 4. Disable Wi-Fi power saving
To reduce the risk of the Raspberry Pi disabling or reducing its wireless
network connection during field use, disable Wi-Fi power saving:
```bash
sudo iw dev wlan0 set power_save off
```
The Raspberry Pi is now ready for the ROS 2 installation described in 2-INSTALL_ROS2.md.


# Translation in French
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