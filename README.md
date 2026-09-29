# HML-LiDAR Cave Mapping

Open-source helmet-mounted LiDAR for cave mapping using a LIVOX MID-360, RPi-4VB, ROS2, DLIO, point-cloud processing and VisualTopo export.

**Project:** HML-LiDAR — Head/Helmet-Mounted LiDAR for cave mapping  
**Institution:** LABAC, Polytechnique Montréal  
**Authors:** Samuel Bassetto; Giovanni Beltrame  
**Status:** Active development  /PROTO/
**Date:** 2026-06-28

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


## Online point-cloud visualization

HML-LiDAR `.pcd` outputs can also be inspected in a browser using
the project web viewer hosted on the Arbutus infrastructure of
Calcul Québec:

**http://134.87.12.16/index.html**

The viewer is an optional visualization service and is not required
for acquisition, DLIO processing, ZUPT-assisted reprocessing,
manual Pegar registration, or scientific reproducibility.

