# Bill of Materials — HML-LiDAR Cave Mapping System

**Project:** HML-LiDAR Cave Mapping
**System:** Head/Helmet-Mounted LiDAR for cave documentation
**Version:** v0.1.0-alpha
**Date:** 2026-06-10
**Status:** Working prototype — field-tested configuration

## 1. Purpose

This Bill of Materials describes the hardware components used to assemble the HML-LiDAR cave mapping system. The objective is to support reproducible construction, maintenance, and adaptation of the system by researchers, speleologists, and open-source contributors.

The system combines a helmet-mounted LiDAR/IMU unit, an embedded acquisition computer, local power supply, field-mounted cabling, a physical recording interface, and a post-processing workstation.

## 2. System-level components

| ID      | Subsystem          | Component                           | Model / specification                                    |  Quantity | Required    | Substitutable | Notes                                                                                                                           |
| ------- | ------------------ | ----------------------------------- | -------------------------------------------------------- | --------: | ----------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| HML-001 | Sensing            | LiDAR/IMU sensor                    | Livox Mid-360                                            |         1 | Yes         | Limited       | Main LiDAR/IMU sensor used for ROS2 acquisition and DLIO processing. Substitution requires new driver and parameter validation. |
| HML-002 | Embedded computing | Single-board computer               | Raspberry Pi 4                                           |         1 | Yes         | Possible      | Used for field acquisition. RAM and storage capacity should be sufficient for ROS2 bag recording.                               |
| HML-003 | Storage            | microSD card or SSD                 | High-endurance storage, ≥256 GB recommended              |         1 | Yes         | Yes           | Must sustain ROS2 bag writing without dropouts. SSD is preferable for longer acquisitions.                                      |
| HML-004 | Power              | DJI TD47 or equivalent              | USB-C or regulated supply compatible with Raspberry Pi 4 |         1 | Yes         | Yes           | Must provide stable current during acquisition. Runtime must be field-tested.                                                   |
| HML-005 | Mounting           | Helmet                              | Speleological helmet compatible with rigid mount         |         1 | Yes         | Yes           | Must allow stable sensor fixation without compromising safety.                                                                  |
| HML-006 | Mounting           | Sensor mount                        | Custom 3D-printed or machined mount                      |         1 | Yes         | Yes           | Must minimize vibration and preserve known sensor orientation.                                                                  |
| HML-007 | Cabling            | Ethernet cable                      | Short, flexible, field-protected cable                   |         1 | Yes         | Yes           | Connects LiDAR to acquisition computer or interface, depending on configuration.                                                |
| HML-008 | Cabling            | Power cables                        | Short, strain-relieved cables                            | As needed | Yes         | Yes           | Cables must be secured to avoid snagging in cave environments.                                                                  |
| HML-009 | User interface     | Physical push button                | Momentary push button connected to GPIO17                |         1 | Recommended | Yes           | Used to trigger or signal recording without a graphical interface.                                                              |
| HML-010 | Protection         | Cable ties / Velcro / strain relief | Field-grade fastening material                           | As needed | Yes         | Yes           | Prevents cable movement and accidental disconnection.                                                                           |
| HML-011 | Protection         | Waterproof pouch or enclosure       | Splash-resistant enclosure for electronics               |         1 | Recommended | Yes           | Protects acquisition electronics from humidity, mud and dripping water.                                                         |
| HML-012 | Post-processing    | Workstation                         | macOS_M4/Linux workstation with Docker                   |         1 | Yes         | Yes           | Used for ROS2 bag replay, DLIO processing, point-cloud export and VisualTopo conversion.                                        |

## 3. Critical components

The following components are critical for reproducibility and should not be substituted without documenting the change and retesting the processing workflow.

| Component      | Why it is critical                                                                     | Validation required after substitution                                                                 |
| -------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Livox Mid-360  | Determines LiDAR geometry, IMU characteristics, point-cloud structure and ROS2 topics. | Verify driver, topics, timestamps, IMU orientation, DLIO parameters, and point-cloud quality.          |
| Raspberry Pi 4 | Determines acquisition stability, storage throughput and field reliability.            | Verify ROS2 bag recording duration, CPU load, storage writing speed and thermal stability.             |
| Sensor mount   | Determines vibration, orientation stability and motion artifacts.                      | Verify that the sensor does not move relative to the helmet during walking, crawling or head rotation. |
| Storage medium | Determines whether high-frequency ROS2 bag data can be recorded without loss.          | Verify recording without dropped messages during a full test acquisition.                              |
| Power supply   | Determines acquisition duration and stability.                                         | Verify voltage stability and runtime under field conditions.                                           |

## 5. Mounting and safety notes

The LiDAR mount must be mechanically stable and must not compromise the protective function of the helmet. The sensor and cables must be positioned so that they do not increase snagging risk in narrow passages. All cables must be strain-relieved.

The acquisition computer and power supply must be protected from dripping water, mud, impact and abrasion. The operator must be able to stop the acquisition and remove the system without tools in case of field difficulty.

The system is intended for documentation and research use. It must not replace standard cave safety equipment, established surveying procedures, or local access and conservation rules.

## 6. Versioning rule

Any modification to the sensing unit, sensor orientation, acquisition computer, mounting geometry, power system, or DLIO configuration must be documented as a new hardware configuration.

## 8. Change log

| Version      | Date       | Change                                         | Validation status                              |
| ------------ | ---------- | ---------------------------------------------- | ---------------------------------------------- |
| v0.1.0-alpha | 2026-06-10 | Initial BOM structure for HML-LiDAR prototype. | To be completed after full hardware inventory. |
