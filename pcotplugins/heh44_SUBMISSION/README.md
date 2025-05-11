# Distance Estimation Project
## Loading PCOT and adding the plugins
To use this project within your own version of PCOT, follow the following steps:

1. Download and set up PCOT on your machine using the instructions included with the original.
2. Move the pcotdistances directory to inside the /pcotplugins directory
3. Edit the plugin variable path in the **.pcot.ini** file to contain the following:
```ini
[Locations]
pluginpath = ~/pcotplugins;~/PCOT/pcotplugins
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
Alternatively, a .pcot file called Multiple Points Selected for Submission.pcot can be loaded in. This displays multiple points being selected and their distances being output.

## Questions
If there are any further questions regarding set up, please do not hesitate to contact me at my email:
heh44@aber.ac.uk