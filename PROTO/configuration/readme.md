# HML-LiDAR RevA — Configuration files

This directory contains the configuration files associated with the HML-LiDAR RevA post-processing environment.

Two complementary levels of DLIO configuration are preserved.

`dlio.yaml` documents the fixed baseline DLIO configuration associated with the RevA software build. It is retained as part of the reproducible RevA environment and is not intended to be exchanged between processing runs.

`params.yaml` contains the active DLIO processing parameters used by the RevA post-processing workflow. Alternative field-tested parameter profiles are provided in:

`dlio_profiles/`

These profiles allow the operator to select processing parameters adapted to different cave geometries during a-posteriori reprocessing. They do not modify `dlio.yaml` or the underlying RevA DLIO software build.

The configuration files are preserved to document the parameterization used during development and field testing of the HML-LiDAR RevA system. The supplied parameter profiles are empirical, field-tested configurations and are not claimed to constitute universally optimal DLIO settings.