# Timelapse system with Raspberry Pi 4b and PiCamera V3 (wide)

#### Relevant files to make a timelapse system based on Raspberry Pi 4b and PiCamera V3 wide

The Picamera V3 has interesting characteristics, like auto-focus and HDR;<br />
It comes with Horizontal field of view (102 degrees) or normal (66 degrees), eventually without IR filter (noIR version).<br />
My choice went for the wide version, to have a larger FoV.<br />
<br /><br />

## Purpose
My intention has been documenting the people approaching my CUBOTino booth, at Hannover Maker Faire 2023.<br />
Anyhow, by testing the system on sunrise and sunset, I was already rewarded by this project.<br />


https://github.com/AndreaFavero71/timelapse/assets/108091411/2fbdf898-6a90-448d-a211-95300df74fcc


Hannover Maker Faire 2023: [2 days in 2 minutes](https://youtu.be/wAfPYTDUh8o)<br />
Sunrise and sunset [examples](https://youtu.be/wO7wYDtcbZA)<br />

<br /><br /><br /><br />


## 3D print cover with the camera support
The timelapse system has connection for tripod:<br />
![title image](/pictures/title.jpg)   ![title image](/pictures/title5.jpg)<br />

and adjustable camera orientation with storage for the camera ribbon cable:<br />
![title image](/pictures/title2.jpg)   ![title image](/pictures/title3.jpg)  ![title image](/pictures/title4.jpg)
<br /><br />
The camera is supported via an arm to vary its orientation, when not used on a tripod with moving head.<br />
Two holes at the cover sides can be used for other fixing systems (i.e. for brackets withsuction caps, to suspend the system on a window).<br />
Stl file are available at folder [/stl](/stl/).<br /><br /><br />

## Installation
For the installation the needed steps are listed in the [installation file](/setup/installation_steps.txt).
<br /><br /><br /><br />


## How it works
The overall idea is to predefine the job, let it go, and collect the assembled movie once the job is done.<br />
The system is based on a python script and a text file for the settings (the only file to be edited).<br /><br />

The [settings.txt](settings.txt) file includes:
- shooting start (hh:mm).
- shotting stop (hh:mm).
- interval between shoots (seconds).
<br /><br />

Other options are:
- Start shooting immediately (true/false).
- VNC preview (true/false).
- Camera resolution.
- HDR (High Dinamic Range) function at camera (true/false).
- Erasing older pictures from the microSD card that includes emptying the Wastebasket (true/false); This is done at the starting of a new job.
- Auto video generation after the shooting (true/false); this can be based on:
  - predefined fps (frame per second value.
  - predefind video time (in seconds), and the fps will be consequently adapted; For this choice fix_movie_t (true/false) and movie_time_s (seconds).
- Number of shooting days (integer), for the period defined by start and stop time.
- Folder name where saving the pictures and generating the movie.
- Usage of the display at Raspberry Pi (true/false).
- Some parameters for the display, like width, height, horizontal and vertical shif, orientation.<br />

### Notes:
1. Boolean variables can be set as true/false or 1/0 or yes/no or.... .<br />
2. In case the movie is not sattisfactory: Via the script video_render.py the video can be (re)made by changing some parameters. For this reason, the pictures aren't automatically erased after a job completion; pictures are automatically erased at the start of a new job.<br />
3. I found convenient to share a Raspberry Pi folder via SMB protocol, allowing quick access via a pc. For this reason, the pictures_folder is generated in the shared folder. The [installation file](/setup/installation_steps.txt) gives instructions also for this function.
<br /><br /><br /><br />


## Automatic script starting at Boot
1. Edit the crontab: sudo crontab -e
2. Add at the end:
```
@reboot /bin/sleep 5; bash -l touch /home/pi/timelapse/timelapse_terminal.log && chmod 777 &_
```
```
@reboot /bin/sleep 5; bash -l /home/pi/timelapse/timelapse_bash.sh > /home/pi/timelapse/timelapse_terminal.log 2>&1
```
3. Save and exit: Ctrl + X, followed by Y, followed by Enter.<br />

After Raspberry Pi boots, the timepse.py script will be excuted according to parameters saved at [settings.txt](settings.txt) file.<br />
Note: To prevent the script from executing at boot, edit the crontab, comment out the two commands and save.
<br /><br /><br /><br />


## Parts
Total cost of the project is ca 130€ (plus shipments) <br />
- 1x [Raspberry Pi 4b](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) (ca 59€) <br />
- 1x [Picamera V3 Wide](https://www.raspberrypi.com/products/camera-module-3/) (ca 42€) <br />
- 1x [Power supply](https://www.raspberrypi.com/products/type-c-power-supply/) (ca 10€) <br />
- 1x [Display Mini PI TFT 1.3"](https://www.aliexpress.com/item/1005001746881831.html?spm=a2g0o.productlist.main.1.e4bc2106UJV1wR&algo_pvid=c521d890-1117-4153-aea3-4c44275d63c8&algo_exp_id=c521d890-1117-4153-aea3-4c44275d63c8-0&pdp_npi=3%40dis%21EUR%215.14%214.89%21%21%215.64%21%21%40212272e216895210456556006d077b%2112000017417119556%21sea%21NL%21768246036&curPageLogUid=E8Qr0bx7tC6v) (ca 5€ at Aliexpress.com) <br />
- 1x microSD V30 32Gb or higher (ca 10€) <br />
- Screws (see [screws list](/stl/screws_list.txt)) <br />
- Filament for the 3D printer <br />
<br /><br /><br />


## Possible improvements
1. Increase and improve feedback via the display (it's still quite under used).
2. I'm open for your suggestions.
<br /><br /><br />


## Credits and references
[Carolin Dunn](https://github.com/carolinedunn/timelapse/tree/master) tutorial on timelapse.<br />
[Daniel Kendell](https://www.youtube.com/watch?v=ofozNWdIDow) tutorial on overlapping text with ffmpeg.<br />
[TroubleChute](https://www.youtube.com/watch?v=8QxJWW0mjAs) tutorial for Raspberry Pi folder sharing via SMB protocol.<br />
[ffmpeg documentation](https://ffmpeg.org/documentation.html).<br /><br />

