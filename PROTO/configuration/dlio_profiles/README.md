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
a transition between morphological regimes using `EditeurTemporel_ZUPT.py`.

The tool generates a new raw ROS 2 bag beginning with a synthetic stationary
initialization interval. DLIO can then be restarted on this portion of the
acquisition using a different parameter profile.

This enables operator-guided, piecewise, a-posteriori adaptation of DLIO
parameters without modifying the original field acquisition.

The parameter adaptation is not performed automatically online during a
single DLIO execution.
