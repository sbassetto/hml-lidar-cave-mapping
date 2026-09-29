# HML-LiDAR RevA Prototype

This directory contains the hardware, software, configuration files, scripts, and technical documentation associated with the RevA field-tested prototype of the HML-LiDAR cave-mapping system.

RevA represents the configuration used to support the field evaluations reported in the associated scientific publication. It combines helmet-mounted LiDAR/IMU acquisition, ROS 2 data recording, reproducible DLIO post-processing, optional ZUPT-assisted restart, operator-guided multi-session registration with Pegar, revisable network assembly, point-cloud inspection and annotation, and topographic extraction to VisualTopo-compatible `.tro` files.

The directory is organized into four main components:

- `hardware/` — bill of materials, assembly information, and hardware documentation;
- `configuration/` — DLIO parameter files and field-tested processing profiles;
- `scripts/` — Raspberry Pi acquisition scripts and Mac-based post-processing tools;
- `software/` — software components and RevA-specific DLIO modifications required for reproducibility.

RevA should be considered a publication candidate and field-tested research prototype. The final archived RevA release will correspond to the version tagged and deposited with the associated scientific publication.