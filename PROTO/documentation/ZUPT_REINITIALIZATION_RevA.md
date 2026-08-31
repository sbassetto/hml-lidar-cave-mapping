# ZUPT-assisted temporal reinitialization and piecewise DLIO reprocessing

## Scope

HML-LiDAR RevA includes an operator-guided post-processing mechanism designed for two related situations:

1. recovery after a visually identified DLIO odometry divergence; and
2. deliberate transition between DLIO parameter sets when a continuous cave acquisition crosses markedly different geometric regimes.

The mechanism is implemented by `EditeurTemporel_ZUPT.py` and is intended for **a-posteriori reprocessing**. It does not change DLIO parameters online during a running odometry process.

## Terminology

The term **ZUPT-assisted** or **ZUPT-like reinitialization** is preferred here.

In a conventional zero-velocity update (ZUPT), a zero-velocity constraint is introduced into a state estimator during detected stationary phases. HML-LiDAR RevA instead creates a short **synthetic stationary sensor interval** at the beginning of a new raw ROS 2 bag and then restarts DLIO. The mechanism therefore uses the zero-motion principle to facilitate reinitialization, but it is not an in-filter conventional ZUPT update.

Recommended manuscript terminology:

> operator-guided ZUPT-assisted temporal reinitialization

or, when emphasizing the parameter adaptation capability:

> operator-guided ZUPT-assisted segmentation and piecewise a-posteriori DLIO reprocessing

## Inputs

The editor uses two synchronized representations of the same acquisition:

- a **DLIO-processed ROS 2 bag**, used only to inspect the reconstructed geometry and visually identify the temporal point at which a divergence or a morphological transition occurs;
- the corresponding **raw ROS 2 bag**, containing the original LiDAR and IMU sensor messages and used to generate the new reprocessable segment.

The processed `/kf_cloud` stream is indexed according to its message header timestamps and displayed through a WebGL temporal viewer. The operator may inspect a sliding window of the reconstructed point cloud and manually select a cut time.

## Temporal synchronization

Let

- \(t_0^{proc}\) be the hardware timestamp of the first `/kf_cloud` message in the processed bag;
- \(\Delta t_{op}\) be the relative time selected by the operator in the temporal viewer.

The target hardware time is

\[
t_{cut}^{hw} = t_0^{proc} + \Delta t_{op}.
\]

The raw bag is then scanned until the first IMU or LiDAR message whose sensor header timestamp reaches or exceeds \(t_{cut}^{hw}\). The corresponding ROS bag record timestamp becomes \(t_{cut}^{bag}\).

This hardware-time correspondence is used to map the visually selected location in the processed trajectory back to the original raw sensor stream.

## Construction of the stationary initialization interval

Immediately before the selected cut, the implementation retains the latest 200 IMU messages. Their mean measured linear acceleration is computed:

\[
\bar{\mathbf a} =
\frac{1}{N}\sum_{i=1}^{N}\mathbf a_i,
\qquad N \leq 200.
\]

This vector is used as the local stationary acceleration reference for the synthetic initialization interval.

A new ROS 2 bag is created. Its first 5 s are synthesized as a stationary sensor sequence:

- IMU messages are generated at 200 Hz;
- angular velocity is set to zero:
  \[
  \boldsymbol{\omega} = [0,0,0]^T;
  \]
- linear acceleration is set to the locally estimated mean vector
  \[
  \mathbf a = \bar{\mathbf a};
  \]
- a LiDAR point-cloud message sampled immediately before the cut is repeated at 10 Hz;
- ROS bag timestamps and sensor header timestamps are advanced coherently throughout the synthetic interval.

At \(t_{cut}^{bag}\), the original raw messages are copied unchanged from the source bag to the new bag.

The resulting archive therefore has the structure:

```text
5 s synthetic stationary initialization
                ↓
original raw sensor stream from selected cut onward
```

No reconstructed DLIO trajectory is copied into this archive: the dynamic part remains the original raw sensor data.

## DLIO reinitialization

The generated bag is subsequently processed as a new acquisition.

At every new DLIO process initialization, the ROS 2 parameter file is loaded. HML-LiDAR RevA therefore permits the user to select a different `params.yaml` profile for the new segment.

This enables a single continuous field acquisition to be reprocessed as several locally configured odometry regimes. For example:

```text
continuous raw cave acquisition
        │
        ├── large chamber
        │      DLIO profile A
        │
        ├── narrow passage
        │      ZUPT-assisted reinitialization
        │      DLIO profile B
        │
        └── second large chamber
               ZUPT-assisted reinitialization
               DLIO profile A or C
```

The selection of the temporal transition and of the subsequent DLIO parameter profile is manual and operator-guided. RevA does not automatically classify cave morphology or optimize DLIO parameters online.

## Why this is useful in caves

A single cave traverse can change rapidly between geometric regimes. Large chambers may contain distant surfaces and relatively sparse geometric constraints, whereas narrow conduits may contain dense short-range geometry and rapid changes in orientation.

Using one fixed odometry configuration for an entire acquisition can therefore be unnecessarily restrictive. The ZUPT-assisted workflow allows the original acquisition to remain untouched while permitting local reprocessing choices after the field session.

The mechanism also provides a recovery route when the operator identifies an unacceptable odometric divergence in a first DLIO processing pass: the remaining raw trajectory can be restarted from a selected temporal location instead of discarding the entire acquisition.

## Relationship with the complete HML-LiDAR workflow

```text
RAW ROS 2 acquisition
        ↓
DLIO processing with profile A
        ↓
visual inspection
        ↓
acceptable? ─────────────── yes ──────────────┐
        │                                      │
        no / morphology transition             │
        ↓                                      │
EditeurTemporel_ZUPT                           │
        ↓                                      │
operator selects temporal cut                  │
        ↓                                      │
5 s synthetic stationary interval              │
        ↓                                      │
new raw continuation bag                       │
        ↓                                      │
DLIO restart with profile B                    │
        ↓                                      │
additional ZUPT-assisted restart if required   │
        ↓                                      │
processed segments ────────────────────────────┘
        ↓
Pegar: manual inter-segment registration
        ↓
Network editor: manual retrospective junction refinement
        ↓
connected cave survey
```

## Reproducibility

HML-LiDAR RevA stores the parameter file used for each completed DLIO treatment as `params_used.yaml`, together with processing provenance. This makes the piecewise parameterization auditable: each processed segment can be associated with the exact configuration that generated it.

The repository also includes the field-tested DLIO source overlay used to compile the RevA processing image, so that the parameter-loading behavior used during the reported field workflow can be reconstructed.

## Limitations and scientific interpretation

This mechanism should not be described as an automatic SLAM recovery algorithm.

The operator:

- identifies the temporal point of divergence or morphological transition;
- chooses whether a new processing segment is needed;
- chooses the DLIO parameter profile used after restart.

The 5 s stationary interval is synthetic. It is generated from the raw sensor state immediately preceding the selected cut and is intended to provide a repeatable initialization condition for DLIO. It should therefore be distinguished from an actual physical stop recorded in the cave.

The current RevA implementation uses fixed synthetic rates of 200 Hz for IMU messages and 10 Hz for repeated LiDAR messages, with a 5 s initialization duration. These values are implementation settings of the field-tested workflow and are not claimed to be theoretically optimal.

## Suggested Methods text for the manuscript

### ZUPT-assisted temporal reinitialization

When a DLIO trajectory exhibited an unacceptable divergence, or when the acquisition entered a cave section requiring a substantially different odometry configuration, the processed keyframe point cloud was inspected using a temporal WebGL viewer. The operator manually selected the corresponding position along the processed sequence. This relative time was mapped back to the original raw ROS 2 sensor archive using sensor-header timestamps.

A new raw archive was then generated beginning with a 5 s synthetic stationary interval. The mean three-axis linear acceleration measured over the latest 200 IMU samples preceding the selected cut was used as the stationary acceleration vector, while angular velocity was set to zero. Synthetic IMU messages were generated at 200 Hz and the latest LiDAR frame preceding the cut was repeated at 10 Hz with synchronized timestamps. After this initialization interval, all original raw sensor messages from the selected cut onward were copied unchanged.

The resulting archive was processed as a new DLIO sequence. Because the RevA DLIO build loads its ROS 2 configuration at process initialization, each restarted segment could be processed using a different parameter profile. This allowed a single continuous field acquisition to be reprocessed piecewise according to cave morphology, for example using different configurations for large chambers and narrow passages. Temporal cut selection and parameter-profile selection remained operator-guided; no automatic online morphology classification or parameter optimization was performed.

## Suggested figure caption

**ZUPT-assisted a-posteriori reprocessing workflow.** A first DLIO reconstruction is used to visually identify an odometric divergence or a transition between cave-morphology regimes. The selected processed timestamp is mapped to the original raw sensor stream. A new raw bag is generated with a 5 s synthetic stationary initialization interval followed by the unchanged raw acquisition from the selected cut onward. DLIO is then restarted and may load a different parameter profile. Repeated application produces multiple locally processed segments that are subsequently registered manually with Pegar.
