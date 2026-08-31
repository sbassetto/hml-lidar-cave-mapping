# HML-LiDAR web point-cloud viewer

A browser-based viewer is available for inspecting HML-LiDAR `.pcd` point-cloud outputs without requiring a local Open3D installation.

**Viewer:** http://134.87.12.16/index.html

The service is hosted on the Arbutus infrastructure of Calcul Québec.

## Intended use

The viewer is provided as a convenience for visual inspection and dissemination of HML-LiDAR point-cloud results. It is complementary to the local processing workflow:

1. acquire and post-process ROS 2 data with HML-LiDAR;
2. export the reconstructed survey as `.pcd`;
3. inspect the point cloud locally or with the external web viewer.

The viewer is not part of the SLAM computation and does not alter the generated point cloud. Scientific processing and reproducibility therefore do not depend on the availability of this external service.

## Availability note

Because the viewer is hosted as an external research service, its network address or availability may change independently of a tagged HML-LiDAR release. For long-term reproducibility, point-cloud files and the HML-LiDAR source repository remain the archival research objects.
