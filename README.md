# HML-LiDAR Cave Mapping

Open-source helmet-mounted LiDAR/IMU workflow for cave mapping using a Livox Mid-360, Raspberry Pi 4, ROS 2, DLIO, multi-session point-cloud registration, network revision, and VisualTopo-compatible topographic export.

**Project:** HML-LiDAR — Head/Helmet-Mounted LiDAR for cave mapping  
**Institution:** LABAC, Polytechnique Montréal  
**Authors:** Samuel Bassetto; Giovanni Beltrame  
**Revision:** RevA  
**Release:** RevA-v1.0.0  
**Status:** Field-tested research prototype — archived RevA release  
**Date:** 2026-10-01

## Overview

This repository provides an open-source workflow for affordable and reproducible 3D cave documentation using a helmet-mounted LiDAR/IMU system.

The workflow covers the complete chain from field acquisition to topographic export:

```text
Acquisition ROS2
    ↓
1. Transfer
    ↓
2. DLIO processing
    ↓
3. Optional ZUPT recovery
    ↓
4. Pegar
    ↓
5. Network editor
    ↓
6. Point-cloud annotation
    ↓
7. .tro topographic extraction
```

## Software workflow

RevA is organized as a modular processing suite. Each stage produces explicit intermediate artifacts so that processing decisions remain traceable and, when necessary, revisable.

1. **Transfer** — `0_mission_sync.sh` safely transfers raw ROS 2 acquisitions from the Raspberry Pi to the post-processing workstation. After a successful transfer, the source data are removed from the Raspberry Pi to free storage space. Deletion occurs only after the transfer completes successfully.

2. **DLIO processing** — `1_traiter_bag.command` runs the Docker/ROS 2/DLIO post-processing environment on a selected ROS 2 bag, or sequentially on the bags available in the local raw-data directory, using the active DLIO `params.yaml`. The processed ROS 2 topics are recorded into a new result bag for subsequent inspection and multi-session processing.

3. **Optional ZUPT-assisted restart** — `2_update_bag_EditeurTemporel_ZUPT.py` allows an operator to identify a temporal restart point and generate a new raw continuation with a synthetic stationary initialization interval for DLIO reprocessing.

4. **Pegar multi-session registration** — `Pegar.py` and `3_LancerPegar.command` provide operator-guided rigid registration of independently processed cave sessions using natural geometric overlap. Accepted transformations are stored explicitly and propagated through the connected sequence.

5. **Network revision** — `EditeurReseau.py` and `4_LancerEditeur.command` allow a previously accepted Pegar junction to be reopened and adjusted. The revised transformation is then propagated through downstream segments to generate a new network version.

6. **Point-cloud annotation** — `5-VisualisateurTopographiqueWithDensity.py` is used to identify uncertain, incomplete, or low-density regions of the reconstructed point cloud without modifying the original LiDAR measurements.

7. **Topographic extraction** — `6_ExtracteurTopographique.py` converts the connected trajectory and point cloud into a VisualTopo-compatible `.tro` file by generating stations, LRUD measurements, and radial splay observations.


## Online point-cloud visualization

HML-LiDAR `.pcd` outputs can also be inspected in a browser using
the project web viewer hosted on the Arbutus infrastructure of
Calcul Québec:

**http://134.87.12.16/index.html**

The viewer is an optional visualization service and is not required
for acquisition, DLIO processing, ZUPT-assisted reprocessing,
manual Pegar registration, or scientific reproducibility.

