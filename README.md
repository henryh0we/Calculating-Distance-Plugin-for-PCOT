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
pluginpath = C:\Users\<your-username>\DistEstimate
```

The plugin path works recursively, so any directories within pluginpath should have their plugins added.

## Loading PCOT

Once the nodes have been added into pcot, on start up, you will be asked two questions:

1. To overwrite the camera data .json
2. To overwrite the focal length, baseline, height .json

Overwriting the camera data json will redo the calibration steps undertaken by camera_calibration.py on images within the Camera Calibration Directory. (This path may need to be changed, if files have been moved)

Overwriting the focal length, baseline, height .json uses the known data about AUPE, hard coded within the program to generate the focal length, baseline and height.

## Using the nodes

Once PCOT has started, look for the nodes within the processing tab on the right hand side.
Alternatively, sample workflows are available in `data/samples/workflows`.

## Questions
If there are any further questions regarding set up, please do not hesitate to contact me at my email:
https://github.com/henryrhowe02
