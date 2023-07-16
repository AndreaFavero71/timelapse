# Timelapse system
Relevant files to make a timelapse system based on Raspberry Pi 4b and PiCamera V3 wide.<br /><br />


https://github.com/AndreaFavero71/timelapse/assets/108091411/0fade063-e42c-44f9-be13-aab4a095e572


<br /><br />


## 3D print cover with the camera support
The timelapse system has connection for tripod:<br />
![title image](/pictures/title.jpg)
<br /><br />
Stl file are available at folder [/stl](/stl/).<br /><br />

## Installation
For the installation the needed steps are listed in the [installation file](/setup/installation_steps.txt).<br /><br />

## How it works
The system is based on a python script and a text file for the settings (the only file to edit).<br /><br />
The [settings.txt](settings.txt) file includes the shooting start, stop and interval time, further than other options.<br />
Other options are:
- Usage of the display at Raspberry Pi.
- VNC preview
- HDR (High Dinamic Range) function at camera.
- Erasing older pictures from the microSD card can be enable
- Auto video generation after the shooting; this can be based on:
  - the set fps.
  - predefind video time.
- Shooting the same period for N days


## Credits and references
[Carolin Dunn](https://github.com/carolinedunn/timelapse/tree/master) tutorial on timelapse.<br />
[Daniel Kendell](https://www.youtube.com/watch?v=ofozNWdIDow) tutorial on overlapping text with ffmpeg.<br />
Useful [ffmpeg documentation](https://ffmpeg.org/documentation.html).<br /><br />
