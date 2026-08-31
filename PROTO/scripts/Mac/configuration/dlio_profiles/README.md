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

A single raw acquisition may cross substantially different cave morphologies. HML-LiDAR RevA allows the operator to identify a transition or an odometric divergence during post-processing, use `EditeurTemporel_ZUPT.py` to generate a new raw continuation with a synthetic stationary initialization interval, and then relaunch DLIO with another YAML profile.

Therefore the parameter change is **not an online automatic adaptation inside one DLIO process**. It is an operator-guided, a-posteriori, piecewise reprocessing strategy in which DLIO is restarted and reads a new ROS 2 parameter file at initialization.

For traceability, `2_traiter_bag.command` stores the actual configuration used for each processed bag as `params_used.yaml` together with a small `processing_info.txt` provenance file.
