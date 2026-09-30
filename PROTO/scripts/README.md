# HML-LiDAR RevA — scripts

This directory contains the scripts used by the HML-LiDAR RevA system.

The scripts are divided according to their execution environment:

- `RPi/` — Raspberry Pi scripts used for field acquisition and hardware control;
- `Mac/` — macOS-side scripts used for data transfer, DLIO post-processing,
  multi-session registration, network revision, inspection, annotation and
  topographic export.

The principal RevA post-acquisition workflow is documented in:

`../documentation/5.PostAcquisitionTreatmentPipeline.md`

The detailed description of the macOS processing tools is available in:

`Mac/ReadMe.md`