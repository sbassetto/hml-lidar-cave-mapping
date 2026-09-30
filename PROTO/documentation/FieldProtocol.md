# HML-LiDAR RevA — Field Protocol

## English version

This document summarizes the field acquisition and immediate post-acquisition
procedure used with the HML-LiDAR RevA prototype.

## 1. Transportation and preparation

Protect the helmet-mounted LiDAR during transport using suitable foam or
equivalent mechanical protection.

The acquisition computer, battery and associated electronics should be carried
in a protected caving bag or enclosure appropriate for the field environment.

The physical recording control should remain accessible to the operator while
being positioned so that it cannot easily be activated accidentally.

Before entering the cave:

1. verify the mechanical attachment of the LiDAR;
2. verify cables and strain relief;
3. verify the battery state;
4. verify that sufficient acquisition storage is available;
5. inspect the electronics enclosure and connectors.

## 2. Starting a field recording

At the acquisition location:

1. connect the LiDAR and acquisition hardware;
2. power the acquisition system;
3. allow the Raspberry Pi and sensor system to start;
4. activate the configured physical recording control;
5. immediately keep the helmet and LiDAR system stationary for approximately
   **15 seconds**.

During this initial stationary period, avoid deliberate head rotation or
translation.

This stationary interval provides a stable initial sensor sequence for
subsequent DLIO processing.

## 3. Cave progression

After the initial stationary period, proceed through the cave normally.

For best reconstruction quality:

- avoid unnecessarily abrupt head rotations when practical;
- avoid impacts or movement of the LiDAR relative to the helmet;
- maintain secure cable routing;
- verify periodically that the acquisition hardware remains mechanically
  stable.

Normal caving movements do not have to be artificially eliminated. RevA
post-processing provides mechanisms for inspecting the reconstructed
trajectory and, when necessary, performing local a-posteriori reprocessing.

## 4. Ending the acquisition

At the end of the recording:

1. deactivate the physical recording control;
2. allow the recording system sufficient time to finalize the ROS 2 bag;
3. verify that recording activity has stopped before disconnecting power;
4. power down the acquisition system;
5. protect the sensor and electronics for transport.

Avoid removing power immediately while a ROS 2 bag is still being finalized.

## 5. Data transfer

Once back at the vehicle, laboratory, base camp or another secure location:

1. check the workstation battery and available storage;
2. connect the workstation to a power source if appropriate;
3. place the Mac and Raspberry Pi on a common network;
4. power the Raspberry Pi;
5. verify SSH connectivity.

For the RevA prototype, for example:

```bash
ssh samuel@chinook.local
```

The username and hostname must be adapted to the actual installation.

Run:

```text
0_mission_sync.sh
```

This script transfers the raw ROS 2 acquisitions from the Raspberry Pi to the
post-processing workstation.

After a successful transfer, the RevA transfer procedure removes the
transferred source data from the Raspberry Pi in order to free acquisition
storage.

Before starting another field acquisition, verify that the expected recordings
are present on the workstation.

## 6. DLIO post-processing

Raw acquisition transfer and DLIO computation are separate RevA stages.

DLIO post-processing is started using:

```text
1_traiter_bag.command
```

The operator may process an individual ROS 2 bag or use the available
batch-processing mode.

The script runs the DLIO processing environment, replays the raw acquisition
and records the processed ROS 2 output.

Processing may take substantially longer than the original field acquisition,
depending on the workstation and replay configuration.

## 7. Inspection and subsequent processing

After DLIO processing, inspect the resulting trajectory and point cloud before
assembling multiple sessions.

The subsequent RevA workflow is:

```text
raw acquisition
        ↓
0_mission_sync.sh
        ↓
1_traiter_bag.command
        ↓
DLIO processed bag
        ↓
[optional]
2_update_bag_EditeurTemporel_ZUPT.py
        ↓
3_LancerPegar.command / Pegar.py
        ↓
[optional]
4_LancerEditeur.command / EditeurReseau.py
        ↓
5-VisualisateurTopographiqueWithDensity.py
        ↓
6_ExtracteurTopographique.py
        ↓
VisualTopo-compatible .tro
```

`7-VisualisateurTRO.py` can optionally be used to inspect the generated
topographic representation.

For detailed post-processing instructions, see:

```text
5.PostAcquisitionTreatmentPipeline.md
```

---

# Version française

# HML-LiDAR RevA — Protocole de terrain

Ce document résume la procédure d'acquisition sur le terrain et les premières
étapes de post-traitement utilisées avec le prototype HML-LiDAR RevA.

## 1. Transport et préparation

Protéger le LiDAR monté sur le casque pendant le transport à l'aide d'une
mousse adaptée ou d'une protection mécanique équivalente.

L'ordinateur d'acquisition, la batterie et les composants électroniques
associés doivent être transportés dans un sac de spéléologie ou une enveloppe
de protection adaptée à l'environnement.

La commande physique d'enregistrement doit rester accessible à l'opérateur
tout en étant positionnée de manière à limiter les activations accidentelles.

Avant l'entrée dans la cavité :

1. vérifier la fixation mécanique du LiDAR ;
2. vérifier les câbles et leurs dispositifs anti-traction ;
3. vérifier l'état de charge de la batterie ;
4. vérifier l'espace de stockage disponible ;
5. inspecter le boîtier électronique et les connecteurs.

## 2. Démarrage d'un enregistrement

Au point de départ de l'acquisition :

1. connecter le LiDAR et le matériel d'acquisition ;
2. mettre le système d'acquisition sous tension ;
3. laisser démarrer le Raspberry Pi et le capteur ;
4. activer la commande physique d'enregistrement configurée ;
5. maintenir immédiatement le casque et le système LiDAR immobiles pendant
   environ **15 secondes**.

Pendant cette période initiale, éviter les rotations et translations
volontaires du casque.

Cette période d'immobilité fournit une séquence initiale stable pour le
traitement DLIO ultérieur.

## 3. Progression dans la cavité

Après la période initiale d'immobilité, progresser normalement dans la cavité.

Pour favoriser la qualité de reconstruction :

- éviter lorsque cela est possible les rotations brusques inutiles de la tête ;
- éviter les chocs ou déplacements du LiDAR par rapport au casque ;
- maintenir les câbles correctement fixés ;
- vérifier périodiquement la stabilité mécanique du système.

Il n'est pas nécessaire de supprimer artificiellement les mouvements normaux
de progression en spéléologie. Le post-traitement RevA permet d'inspecter la
trajectoire reconstruite et, lorsque nécessaire, de réaliser un retraitement
local a posteriori.

## 4. Fin de l'acquisition

À la fin de l'enregistrement :

1. désactiver la commande physique d'enregistrement ;
2. laisser au système le temps de finaliser le ROS 2 bag ;
3. vérifier l'arrêt de l'enregistrement avant de couper l'alimentation ;
4. mettre le système d'acquisition hors tension ;
5. protéger le capteur et l'électronique pour le transport.

Éviter de couper immédiatement l'alimentation lorsqu'un ROS 2 bag est encore
en cours de finalisation.

## 5. Transfert des données

Une fois revenu au véhicule, au laboratoire, au camp de base ou dans un autre
environnement sécurisé :

1. vérifier la batterie et l'espace disque du poste de travail ;
2. brancher le Mac sur une alimentation si nécessaire ;
3. connecter le Mac et le Raspberry Pi au même réseau ;
4. mettre le Raspberry Pi sous tension ;
5. vérifier la connexion SSH.

Pour le prototype RevA, par exemple :

```bash
ssh samuel@chinook.local
```

Le nom d'utilisateur et le nom d'hôte doivent être adaptés à l'installation.

Exécuter :

```text
0_mission_sync.sh
```

Ce script transfère les acquisitions ROS 2 brutes du Raspberry Pi vers le
poste de post-traitement.

Après un transfert réussi, la procédure RevA supprime les données transférées
du Raspberry Pi afin de libérer l'espace de stockage nécessaire aux
acquisitions suivantes.

Avant une nouvelle acquisition sur le terrain, vérifier que les
enregistrements attendus sont bien présents sur le poste de travail.

## 6. Post-traitement DLIO

Le transfert des acquisitions brutes et leur traitement DLIO constituent deux
étapes distinctes de RevA.

Le traitement DLIO est lancé avec :

```text
1_traiter_bag.command
```

L'opérateur peut traiter un ROS 2 bag individuel ou utiliser le mode de
traitement par lot disponible.

Le script exécute l'environnement de traitement DLIO, rejoue l'acquisition
brute et enregistre les données ROS 2 traitées.

Le traitement peut être sensiblement plus long que l'acquisition terrain
originale selon le poste de calcul et la configuration de rejeu.

## 7. Inspection et traitements suivants

Après le traitement DLIO, inspecter la trajectoire et le nuage de points avant
l'assemblage de plusieurs sessions.

Le workflow RevA se poursuit ainsi :

```text
acquisition brute
        ↓
0_mission_sync.sh
        ↓
1_traiter_bag.command
        ↓
bag traité par DLIO
        ↓
[optionnel]
2_update_bag_EditeurTemporel_ZUPT.py
        ↓
3_LancerPegar.command / Pegar.py
        ↓
[optionnel]
4_LancerEditeur.command / EditeurReseau.py
        ↓
5-VisualisateurTopographiqueWithDensity.py
        ↓
6_ExtracteurTopographique.py
        ↓
fichier .tro compatible VisualTopo
```

`7-VisualisateurTRO.py` peut être utilisé en complément pour inspecter la
représentation topographique générée.

Pour la procédure détaillée de post-traitement, voir :

```text
5.PostAcquisitionTreatmentPipeline.md
```