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

Validation of the parameter profiles

The parameter profiles distributed with HML-LiDAR RevA were empirically tested during additional real-world cave processing experiments, including data acquired in the Saint-Léonard cave in Montréal, Québec, Canada.

The Saint-Léonard dataset was used as a development and parameter-validation case but is not included in the RevA release and is not part of the datasets distributed with the repository.

The parameter values provided here are therefore retained as field-tested configurations. They should not be interpreted as universally optimal settings for a given cave morphology. Their suitability depends on acquisition conditions, cave geometry, sensor motion, and the characteristics of the recorded point clouds.
