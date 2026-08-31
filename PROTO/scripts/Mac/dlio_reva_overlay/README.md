# DLIO RevA source overlay

This directory contains the source files from the DLIO build actually used in the HML-LiDAR RevA field-processing workflow.

The Docker build first checks out upstream DLIO commit `c8acc37100e349d70a9d8432d656cbce7e5072cd`, then overlays these files before compiling. This preserves upstream attribution/license headers while making the field-tested build reproducible.

The relevant HML-LiDAR requirement is that processing parameters used for cave morphology changes are read from ROS 2 parameters at node initialization, enabling different `params.yaml` profiles to be used after ZUPT-assisted temporal reinitialization.

This snapshot should be replaced by a minimal patch once the exact upstream diff is audited; RevA keeps the field-tested sources to avoid reconstructing modifications from memory.
