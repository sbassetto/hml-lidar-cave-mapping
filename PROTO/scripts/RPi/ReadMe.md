This folder is used for script intented for the RPi only


Tip (in French): 
L'attribution des droits d'exécution au script Python est impérative pour autoriser le gestionnaire de services système à l'invoquer en arrière-plan. Sans cette modification, le système d'exploitation bloque l'accès au fichier par mesure de sécurité.

Taper la commande dans votre terminal : 

sudo chmod +x /opt/hml/button_daemon.py

Cette instruction doit être exécutée immédiatement après la création du fichier button_daemon.py et avant le rechargement des démons. Cela se fait via la commande :
systemctl daemon-reload. 

Le chemin absolu /opt/hml/ doit correspondre à l'emplacement exact où le fichier a été sauvegardé sur le Raspberry Pi.
