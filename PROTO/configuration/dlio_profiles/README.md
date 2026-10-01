# DLIO field-tested parameter profiles — HML-LiDAR RevA

These YAML files are field-tested processing profiles used with the HML-LiDAR post-processing workflow.
They are **not claimed to be globally optimal DLIO settings**. Their purpose is to make the empirical configurations used during cave reprocessing explicit and reproducible.

## Profiles

- `params_grande_salle.yaml` — large chambers / long-range geometry.
- `params_conduit_moyen.yaml` — intermediate-size passages.
- `params_etroiture.yaml` — narrow passages / close-range geometry.
- `params_foret.yaml` — outdoor forest field tests.
- `params_maison_alberta.yaml` — house/Alberta field tests; numerically identical to the forest profile in the supplied RevA test set.

## Piecewise a-posteriori processing

A single raw HML-LiDAR acquisition may cross substantially different cave
morphologies.

During post-processing, the operator may identify an odometric divergence or
a transition between morphological regimes using `2_update_bag_EditeurTemporel_ZUPT.py`.

The tool generates a new raw ROS 2 bag beginning with a synthetic stationary
initialization interval. DLIO can then be restarted on this portion of the
acquisition using a different parameter profile.

This enables operator-guided, piecewise, a-posteriori adaptation of DLIO
parameters without modifying the original field acquisition.

The parameter adaptation is not performed automatically online during a
single DLIO execution.

`1_traiter_bag.command` uses the active `cfg/params.yaml` file and does not
automatically select one of the profiles stored in this directory.

To use a specific field-tested profile, the operator must make that profile
the active `cfg/params.yaml` before launching DLIO processing and record which
profile was used for the processed segment.

The RevA processing environment distinguishes between the fixed DLIO configuration and the field-processing parameter profiles.

dlio.yaml documents the baseline DLIO configuration associated with the RevA software build. It is part of the fixed RevA processing environment and is not intended to be modified or exchanged between processing runs. Its purpose is to preserve the configuration associated with the DLIO implementation used for RevA and to make the software environment reproducible.

params.yaml, in contrast, contains the processing parameters used when running dlio_odom_node. This file may be replaced by one of the field-tested parameter profiles stored in dlio_profiles/ when reprocessing a segment of an acquisition.

The parameter profiles therefore represent operator-selected post-processing configurations, whereas dlio.yaml represents the fixed baseline configuration of the RevA DLIO implementation.

The profiles do not modify dlio.yaml and do not imply that the fixed DLIO configuration is changed during processing.