# HML-LiDAR RevA Prototype

This directory contains the hardware, software, configuration files, scripts, and technical documentation associated with the RevA field-tested prototype of the HML-LiDAR cave-mapping system.

RevA represents the configuration used to support the field evaluations reported in the associated scientific publication. It combines helmet-mounted LiDAR/IMU acquisition, ROS 2 data recording, reproducible DLIO post-processing, optional ZUPT-assisted restart, operator-guided multi-session registration with Pegar, revisable network assembly, point-cloud inspection and annotation, and topographic extraction to VisualTopo-compatible `.tro` files.

The directory is organized into four main components:

- `hardware/` — bill of materials, assembly information, and hardware documentation;
- `configuration/` — DLIO parameter files and field-tested processing profiles;
- `scripts/` — Raspberry Pi acquisition scripts and Mac-based post-processing tools;
- `software/` — software components and RevA-specific DLIO modifications required for reproducibility.

RevA is the field-tested research prototype archived for the associated scientific publication. The `RevA-v1.0.0` release freezes the hardware, software, configuration files, scripts and technical documentation corresponding to the RevA reference workflow. This release documents a reproducible research prototype and does not constitute a metrological certification of the system.