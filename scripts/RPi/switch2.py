from gpiozero import Button
import subprocess
from signal import pause
import sys

# Pin GPIO 4 (Pin physique 7) antirebond mis à 500ms
switch = Button(4, pull_up=True, bounce_time=0.5)

SERVICES = [
    "backpack-driver.service",
    "cave_bag_record.service",
]

def on_switch_closed():
    print("Bouton activé : Lancement des services...")
    for service in SERVICES:
        subprocess.run(["sudo", "systemctl", "start", service])

def on_switch_open():
    print("--- ACTION : STOP ---")
    # 1. On arrête d'abord le recorder
    print("Arrêt du recorder (patientez...)")
    subprocess.run(["sudo", "systemctl", "stop", "cave_bag_record.service"])
    
    # 2. On laisse 10 secondes au système pour finaliser les fichiers sur la SD
    time.sleep(10)
    
    # 3. On arrête le driver
    subprocess.run(["sudo", "systemctl", "stop", "backpack-driver.service"])
    print("Services arrêtés proprement.")



# Assignation des fonctions aux événements
switch.when_pressed = on_switch_closed
switch.when_released = on_switch_open

print("Système de monitoring du bouton prêt (GPIO 4)...")

try:
    pause() # Attend les événements indéfiniment sans consommer de CPU
except KeyboardInterrupt:
    print("\nArrêt manuel du script")
    sys.exit(0)
