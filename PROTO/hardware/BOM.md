# Bill of Materials — HML-LiDAR Cave Mapping System

**Project:** HML-LiDAR Cave Mapping  
**System:** Head/Helmet-Mounted LiDAR for cave documentation  
**Version:** v0.1.0-alpha  
**Date:** 2026-06-10  
**Status:** Working prototype — field-tested configuration  

## 1. Purpose

This Bill of Materials documents the hardware components used to assemble the HML-LiDAR cave mapping prototype. It integrates the general system components, the power subsystem, the voltage converters and the connectors visible in the current prototype photographs.

The objective is to make the system reproducible while keeping a clear distinction between critical components, substitutable components and prototype-level elements that require additional field protection before routine cave use.

## 2. System overview

The HML-LiDAR system combines a helmet-mounted LiDAR/IMU unit, an embedded ROS2 acquisition computer, a battery-powered DC distribution system, voltage conversion modules, a physical recording interface and a post-processing workstation.

```text
Helmet-mounted LiDAR/IMU
        ↓
Raspberry Pi 4 acquisition computer
        ↓
ROS2 bag recording
        ↓
Transfer to workstation
        ↓
Docker / ROS2 / DLIO processing
        ↓
PCD point cloud and VisualTopo .tro export
```

## 3. Power architecture

The photographed prototype uses a DJI TB47D battery as the main energy source. The battery is connected through a DJI Matrice 100 battery interface. The resulting DC power is distributed toward two DC-DC conversion branches: one branch supplies the LiDAR-side rail, and one branch supplies the Raspberry Pi 5 V rail.

```text
DJI TB47D battery
      ↓
DJI Matrice 100 battery interface
      ↓
────────────────────────────────────
↓                                  ↓
DC-DC converter for LiDAR           DC-DC converter for Raspberry Pi
VGEPS 190 W module                  LANTIANRC 5 V module
↓                                  ↓
LiDAR power input                   Raspberry Pi 5 V input
                                   ↓
                                    I/O Recording Switch

```

All regulated outputs must be measured with a multimeter before connecting the LiDAR or Raspberry Pi. The prototype-level converter boards visible in the photographs require insulation, strain relief and preferably a protective enclosure before routine wet-cave use.

## 4. Complete BOM

| item_id | category | subsystem | component | manufacturer | model_or_specification | quantity | required | substitutable | criticality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEN-001 | Sensing | LiDAR / IMU | LiDAR/IMU sensor | Livox | Livox Mid-360 | 1 | yes | limited | critical |
| CPU-001 | Computing | Embedded acquisition | Single-board computer | Raspberry Pi | Raspberry Pi 4 | 1 | yes | possible | critical |
| STO-001 | Storage | Embedded acquisition | Storage medium |  | High-endurance microSD card or SSD, >=256 GB recommended | 1 | yes | yes | high |
| MNT-001 | Mounting | Helmet mount | Speleological helmet |  | Helmet compatible with stable LiDAR mount | 1 | yes | yes | critical |
| MNT-002 | Mounting | Helmet mount | Sensor mount |  | Custom 3D-printed or machined mount | 1 | yes | yes | critical |
| MNT-003 | Cable management | Field robustness | Cable ties / Velcro / strain relief |  | Field-grade fastening material | as needed | yes | yes | high |
| BAG-001 | Transport | Field transport | Protective transport bag | MTDE | Orange cylindrical transport bag | 1 | recommended | yes | medium |
| PWR-001 | Power | Battery | Intelligent flight battery | DJI | TB47D, 4500 mAh, 99.90 Wh, 22.2 V, LiPo | 1 | yes | limited | critical |
| PWR-002 | Power | Battery interface | Battery holder / battery box | DJI | Matrice 100 battery interface / battery box | 1 | yes | limited | critical |
| PWR-003 | Power | Charging | AC battery charger | DJI | A14-100P1A, input 100–240 V AC, output 26.3 V / 3.83 A, 100 W | 1 | yes | limited | high |
| PWR-004 | Power | Voltage conversion | DC-DC converter for LiDAR supply | VGEPS | 190 W DC-DC converter; label observed: IN 24 V, OUT 19 V / 10 A | 1 | yes | limited | critical |
| PWR-005 | Power | Voltage conversion | DC-DC converter for Raspberry Pi supply | LANTIANRC | DC-DC / BEC-type module; visible 5 V and GND pads | 1 | yes | limited | critical |
| PWR-006 | Recording | User interface | Inline rocker switch |  | Round waterproof-style rocker switch with I/O marking | 1 | recommended | yes | medium |
| CAB-001 | Cabling | Data | LiDAR data cable |  | Short, flexible, field-protected Ethernet/data cable | 1 | yes | yes | high |
| PRO-001 | Protection | Electronics protection | Electronics enclosure or protective pouch |  | Splash-resistant enclosure recommended | 1 | recommended | yes | high |
| WS-001 | Post-processing | Workstation | Post-processing computer |  | macOS or Linux workstation with Docker | 1 | yes | yes | high |

## 5. Functional details and validation requirements

| item_id | function | connector_or_interface | validation_required | notes | source_or_photo |
| --- | --- | --- | --- | --- | --- |
| SEN-001 | Primary LiDAR/IMU sensing unit for cave acquisition | Ethernet/data connector and dedicated DC power input, exact final connector to document | Verify ROS2 driver, topics, timestamps, IMU orientation, DLIO parameters and point-cloud quality after any substitution. | Main sensing unit for the HML-LiDAR workflow. Substitution changes the driver, topics, time synchronization and odometry parameterization. |  |
| CPU-001 | Field acquisition computer for ROS2 bag recording | 5 V power input; Ethernet/USB interfaces depending on final wiring | Verify CPU load, thermal stability, ROS2 bag recording duration and storage write speed. | RAM size and operating system version should be documented for the stable release. |  |
| STO-001 | Stores ROS2 bag files during field acquisition | microSD or USB/SSD depending on acquisition configuration | Run a full-duration recording test and verify no message loss or storage saturation. | SSD is preferable for long acquisitions or high-rate data logging. |  |
| MNT-001 | Mechanical support for the head/helmet-mounted LiDAR system | Mechanical mounting interface | Verify that the mount does not compromise helmet safety and remains stable during walking, crawling and head rotation. | The protective function of the helmet must not be reduced by the mount. |  |
| MNT-002 | Holds the LiDAR/IMU rigidly on the helmet | Screws, brackets or custom mount geometry | Check vibration, sensor orientation stability and absence of relative motion between helmet and sensor. | Any change in mount geometry or sensor orientation must be documented and retested. |  |
| MNT-003 | Secures cables and prevents snagging | Mechanical strain relief | Inspect cable movement during field-like motion and narrow-passage simulation. | Cave use requires cables to be short, secured and protected from abrasion. |  |
| BAG-001 | Transports and protects battery and power components during field handling | Drawstring closure and reinforced eyelets | Verify that sharp edges, exposed solder joints and battery terminals are separately protected inside the bag. | Useful for transport, but not a substitute for a waterproof electronics enclosure. | TransportBag.jpeg |
| PWR-001 | Main field power source | DJI Matrice 100 / TB47D proprietary battery interface | Verify battery state of health, runtime, voltage stability and safe mechanical retention. | Battery originally designed for DJI Matrice-series systems and used here as the main energy source for the HML-LiDAR prototype. | BatteryTD74D.jpeg |
| PWR-002 | Mechanical and electrical interface between TB47D battery and prototype wiring | DJI Matrice 100 / TB47D proprietary connector | Verify polarity, mechanical lock, output voltage and absence of intermittent connection under movement. | Marked Matrice 100 on the photographed component. | BatteryBoxVersion.jpeg |
| PWR-003 | Charges TB47D battery outside the cave | DJI charger-to-battery connector | Use only in dry, controlled conditions; verify compatibility with TB47D battery. | Charging component only; not part of the helmet-mounted system during acquisition. | batteryCharger.jpeg |
| PWR-004 | Regulates battery voltage to the LiDAR-side supply used in the prototype | Soldered input/output pads; red/black DC power leads; final LiDAR connector to document | Measure output voltage and polarity with no load and under load before connecting the LiDAR; check thermal behavior. | The final LiDAR supply voltage and connector polarity must be explicitly documented in the wiring diagram. | TensiontransformationForLidar.jpeg |
| PWR-005 | Regulates battery voltage to 5 V for the Raspberry Pi | Soldered 5 V and GND pads; final Raspberry Pi power connector to document | Measure 5 V output and polarity under realistic Raspberry Pi load; check voltage drop during recording. | Raspberry Pi requires a stable 5 V supply with adequate current margin. | TensionTransformationForRpi-2.jpeg; TEnsionTransformationForRpi-3.jpeg; TensionTransformatorForRpi.jpeg |
| PWR-006 | Manual recording control for the RPi subsystem |   | Verify current rating, contact stability and protection against accidental activation. | Should be placed where it can be reached but not accidentally toggled in narrow passages. | Button.jpeg |
| CON-003 | Detachable DC connection within the prototype power wiring | Cylindrical DC connector; diameter and polarity to measure | Measure connector diameter, center polarity and voltage before duplication. | Do not assume polarity from appearance; document with an annotated photo. | batteryCharger.jpeg |
| CAB-001 | Carries LiDAR data to acquisition computer or interface | Final connector type to document | Verify ROS2 topic stability and absence of intermittent connection during movement. | Cable routing must reduce snagging risk. |  |

| WS-001 | Runs ROS2 bag replay, DLIO processing, PCD export and VisualTopo conversion | Docker, filesystem mounts, optional Foxglove port | Verify Docker, ROS2 Humble, DLIO, Python dependencies and script paths. | Version details should be recorded in the technical manual and release notes. |  |

## 6. Connector inventory

The connector inventory identifies all known or visible connection points. Some connector types are described functionally because the exact commercial part number has not yet been confirmed.

| item_id | component | model_or_specification | function | connector_or_interface | validation_required | source_or_photo |
| --- | --- | --- | --- | --- | --- | --- |
| CON-001 | DJI battery connector | Matrice 100 / TB47D proprietary connector | Connects TB47D battery to power distribution | Proprietary DJI battery interface | Confirm polarity, mechanical retention and exact pin function before duplication. | BatteryBoxVersion.jpeg |
| CON-002 | DJI charger connector | A14-100P1A charger-to-battery connector | Connects DJI charger to TB47D battery | Proprietary DJI charging connector | Verify physical compatibility and correct charger/battery pairing. | batteryCharger.jpeg |
| CON-003 | Cylindrical DC connector | Round DC plug/socket visible on power lead | Detachable DC connection within the prototype power wiring | Cylindrical DC connector; diameter and polarity to measure | Measure connector diameter, center polarity and voltage before duplication. | batteryCharger.jpeg |
| CON-004 | VGEPS converter solder pads | Input/output solder pads on DC-DC converter | Input and output wiring for LiDAR-side DC-DC conversion | Solder pads with red/black power leads | Confirm pad labels, polarity and insulation; perform continuity and voltage tests. | TensiontransformationForLidar.jpeg |
| CON-005 | LANTIANRC converter solder pads | 5 V and GND solder pads on DC-DC / BEC-type module | Input and regulated 5 V output wiring for Raspberry Pi supply | Solder pads labelled 5V and GND; red/black wires | Confirm 5 V and GND polarity; test under Raspberry Pi load before field use. | TensionTransformationForRpi-2.jpeg; TEnsionTransformationForRpi-3.jpeg |
| CON-006 | Rocker switch terminals | Inline switch terminals, exact terminal type to confirm | Connects switch into the RPi GPIo |  | Verify current rating, insulation and mechanical strain relief. | Button.jpeg |

## 7. Critical components

The following components are critical for reproducibility and should not be substituted without documenting the change and retesting the acquisition and processing workflow.

| Component | Why it is critical | Validation required after substitution |
|---|---|---|
| Livox Mid-360 | Determines LiDAR geometry, IMU characteristics, point-cloud structure, timestamps and ROS2 topics. | Verify driver, topics, timestamps, IMU orientation, DLIO parameters and point-cloud quality. |
| Raspberry Pi 4 | Determines acquisition stability, storage throughput and field reliability. | Verify ROS2 bag recording duration, CPU load, storage write speed and thermal stability. |
| DJI TB47D battery and battery interface | Determines input voltage, available energy, connector type and field power stability. | Verify polarity, runtime, voltage stability, connector retention and converter input behavior. |
| DC-DC converters | Determine regulated voltages supplied to the LiDAR and Raspberry Pi. | Measure outputs with no load and under load; verify thermal behavior and polarity. |
| Sensor mount | Determines vibration, orientation stability and motion artifacts. | Verify that the sensor does not move relative to the helmet during walking, crawling and head rotation. |
| Storage medium | Determines whether high-frequency ROS2 bag data can be recorded without loss. | Verify recording without dropped messages during a full test acquisition. |

## 8. Safety and field notes

The battery and DC-DC conversion subsystem carries enough energy to damage electronics or create a field hazard if miswired. The complete assembly must therefore be tested outside the cave before field deployment.

The LiDAR mount must be mechanically stable and must not compromise the protective function of the helmet. Cables must be short, strain-relieved and routed to reduce snagging risk in narrow passages.

The DC-DC converter boards, solder joints and exposed pads visible in the current prototype should be treated as bench-prototype elements. For routine cave use, they should be enclosed, insulated and protected against dripping water, mud, abrasion and impact.

## 9. Internet links
Partial internet links to components supplier. Require a perticular attention as link can be broken, out of order...
Lidar: 
https://www.livoxtech.com/mid-360s

battery: 
https://store.dji.com/ca/product/matrice-100-tb47d-battery

Battery Compartment
https://www.aeromotus.com/product/matrice-100-battery-compartment-kit/?srsltid=AfmBOorGxWaJFC1UPpXSqTXe7X1TUYuZAqlG0yZztNBX7ymab9DVBCdw

Dc-DC converter (22V to 15V for the LiDAR)
https://www.amazon.ca/DROK-Waterproof-Converter-Adjustable-Transformer/dp/B00C0KL1OM

DC to DC converter (22V to 5V votre the RPi)
https://www.amazon.ca/MECCANIXITY-Converter-Voltage-Waterproof-Transformer/dp/B0DG5GCW2L/ref=asc_df_B0DG5GCW2L?mcid=2cadf647580a3f5980039dcc16aa6eb3&tag=googleshopc0c-20&linkCode=df0&hvadid=766556333461&hvpos=&hvnetw=g&hvrand=2053626137665046708&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9000439&hvtargid=pla-2448749223511&psc=1&hvocijid=2053626137665046708-B0DG5GCW2L-&hvexpln=0&gad_source=1

## 10. Change log

| Version | Date | Change | Validation status |
|---|---|---|---|
| v0.1.0-alpha | 2026-06-10 | Initial integrated BOM covering general system, power subsystem and connector inventory. | To be completed after full hardware verification and electrical validation. |
