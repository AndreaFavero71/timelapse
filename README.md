# Timelapse system
Relevant files to make a timelapse system based on Raspberry Pi 4b and PiCamera V3 wide.<br /><br />
(Note: still work in progress :smiley: )<br /><br />


https://github.com/AndreaFavero71/timelapse/assets/108091411/0fade063-e42c-44f9-be13-aab4a095e572


<br /><br />


## 3D print cover with the camera support
The timelapse system has connection for tripod:<br />
![title image](/pictures/title.jpg)
<br /><br />
The camera is supported via an arm to heavily influence its orientation, for instance when suspending the camera on a window via suction caps.<br />
Stl file are available at folder [/stl](/stl/).<br /><br />

## Installation
For the installation the needed steps are listed in the [installation file](/setup/installation_steps.txt).<br /><br />

## How it works
The system is based on a python script and a text file for the settings (the only file to edit).<br />
The overall idea is to predefine the job, and let it go.<br /><br /> 
The [settings.txt](settings.txt) file includes:
- shooting start (hh:mm).
- shotting stop (hh:mm).
- interval between shoots (seconds).<br /><br />
<a/>
Other options are:
- Start shooting immediately (true/false).
- Usage of the display at Raspberry Pi (true/false).
- VNC preview (true/false).
- Camera resolution.
- HDR (High Dinamic Range) function at camera (true/false).
- Erasing older pictures from the microSD card (this includes emptying the Wastebasket) (true/false).
- Auto video generation after the shooting (true/false); this can be based on:
  - predefined fps (frame per second value.
  - predefind video time (in seconds), and the fps will be consequently adapted; For this choice fix_movie_t (true/false) and movie_time_s (seconds).
- Number of shooting days (integer), for the period defined by start and stop time.
- Folder name where to save the pictures and to generate the movie.<br />
<a/>
Note: Boolean variables can be set as true/false or 1/0 or yes/no or.... .<br /><br />



## Credits and references
[Carolin Dunn](https://github.com/carolinedunn/timelapse/tree/master) tutorial on timelapse.<br />
[Daniel Kendell](https://www.youtube.com/watch?v=ofozNWdIDow) tutorial on overlapping text with ffmpeg.<br />
Useful [ffmpeg documentation](https://ffmpeg.org/documentation.html).<br /><br />
