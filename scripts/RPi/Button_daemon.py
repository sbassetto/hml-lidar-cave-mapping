import RPi.GPIO as GPIO
import time
import subprocess
import sys

# --- CONFIGURATION MATÉRIELLE ---
# Définition de la broche GPIO (numérotation BCM) reliée au bouton physique
PIN_BOUTON = 17 

def setup_gpio():
    # Initialisation de la bibliothèque spécifique au Raspberry Pi
    GPIO.setmode(GPIO.BCM)
    # Activation de la broche en entrée avec une résistance de tirage vers le haut (pull-up)
    # Le bouton doit être câblé entre cette broche et la masse (GND)
    GPIO.setup(PIN_BOUTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def action_bouton(canal):
    # Fonction de rappel (callback) déclenchée lors d'une interruption matérielle
    print(f"Interruption détectée sur la broche {canal}.")
    
    # Déclenchement d'une commande système en réponse à l'appui
    # Cette ligne est configurée pour interagir avec le conteneur du projet HML
    try:
        # Exemple d'appel sécurisé vers le conteneur Docker pour lancer ou arrêter un script
        subprocess.run(["docker", "exec", "hml_m4", "bash", "-c", "echo 'Bouton pressé'"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de l'action : {e}")
    
    # Délai d'anti-rebond logiciel pour éviter les déclenchements multiples
    time.sleep(0.5)

def main():
    setup_gpio()
    
    # Configuration de la détection d'événement sur un front descendant (FALLING)
    # L'argument bouncetime ajoute un second niveau d'anti-rebond matériel
    GPIO.add_event_detect(PIN_BOUTON, GPIO.FALLING, callback=action_bouton, bouncetime=500)
    
    print("Démon de lecture GPIO activé. En attente d'instructions matérielles...")
    
    try:
        # Maintien du processus principal en activité avec une charge processeur minimale
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interruption manuelle du processus.")
    finally:
        # Libération systématique des ressources matérielles avant la fermeture
        GPIO.cleanup()
        sys.exit(0)

if __name__ == '__main__':
    main()