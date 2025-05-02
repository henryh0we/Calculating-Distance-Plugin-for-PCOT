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

## Using the nodes
Once the nodes have been added into pcot, on start up, you will be asked two questions:
1. To overwrite Camera_data.json
2. To overwrite 

they should appear in the 