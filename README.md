# Distance Estimation Project
## Loading PCOT and adding the plugins
This repository is intended to sit alongside a clean PCOT checkout:

```text
C:\Users\<your-username>\
  PCOT\
  DistEstimate\
```

To use this project with PCOT:

1. Download and set up PCOT from https://github.com/AU-ExoMars/PCOT.
2. Keep this repository outside PCOT as `DistEstimate`.
3. Edit the plugin path in the **.pcot.ini** file to contain the following:

```ini
[Locations]
pluginpath = C:\Users\<your-username>\DistEstimate\pcotdistanceestimate
```

For this repository layout, point `pluginpath` at `pcotdistanceestimate` rather than the repository root. PCOT loads plugin paths recursively, so pointing at the repository root would also load test files.

## Loading PCOT

The repository includes [Camera_calibration.py](pcotdistanceestimate/Camera_calibration.py), which can regenerate the camera calibration data used by the plugin. The script uses the calibration images stored in [data/calibration](data/calibration/) to create the camera data.

## Using the nodes

Once PCOT has started, look for the nodes within the processing tab on the right hand side.
Alternatively, sample workflows are available in `data/samples/workflows`.

## Questions
If there are any further questions regarding set up, please do not hesitate to contact me at my email:
https://github.com/henryh0we
