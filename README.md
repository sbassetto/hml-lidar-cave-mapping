# hml-lidar-cave-mapping
Open-source helmet-mounted LiDAR workflow for cave mapping using ROS2, DLIO, point-cloud processing, and VisualTopo export.

#By 
Samuel Bassetto, LABAC, Ecole Polytechnique de Montréal

Giovanni Beltrame, MIST Lab, Polytechnique Montréal

Date: 2026-06-28

# HML-LiDAR Cave Mapping

This repository provides an open-source workflow for helmet-mounted LiDAR cave mapping.

The project aims to support affordable and reproducible 3D cave documentation using:

- a helmet-mounted LiDAR/IMU system;
- ROS2 bag acquisition on a Raspberry Pi 4 Vers. B ;
- Docker-based processing;
- DLIO LiDAR-inertial odometry;
- point-cloud export to PCD;
- conversion from LiDAR-derived trajectory and point cloud to VisualTopo `.tro` files.

## Repository structure

config/          ROS2 and DLIO configuration files

scripts/Data/    transfer, processing, point-cloud export, and VisualTopo conversion scripts
    /MAC/       Scripts dedicated for the MAC 
    /RPi/       Scripts dedicated for the RPi

hardware/        Helmet-mounted hardware description, bill of materials, and mounting documentation
    /Photos/     Pictures of the LiDAR

docs/            Installation, field protocol, calibration, and troubleshooting documentation

data/            Small example datasets and processed outputs


