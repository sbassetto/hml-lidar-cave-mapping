# HML-LiDAR Cave Mapping

Open-source helmet-mounted LiDAR workflow for cave mapping using ROS2, DLIO, point-cloud processing, and VisualTopo export.

**Project:** HML-LiDAR — Head/Helmet-Mounted LiDAR for cave mapping  
**Institution:** LABAC, Polytechnique Montréal  
**Authors:** Samuel Bassetto; Giovanni Beltrame  
**Status:** Active development  
**Date:** 2026-06-28

## Overview

This repository provides an open-source workflow for affordable and reproducible 3D cave documentation using a helmet-mounted LiDAR/IMU system.

The workflow covers the complete chain from field acquisition to topographic export:

```text
Helmet-mounted Livox Mid-360 + IMU
        ↓
Raspberry Pi 4 / ROS2 acquisition
        ↓
ROS2 bag files
        ↓
Transfer to post-processing computer
        ↓
Docker / ROS2 Humble / DLIO
        ↓
Registered point cloud and trajectory
        ↓
PCD point cloud export
        ↓
VisualTopo-compatible .tro export
