# Timelapse system with Raspberry Pi 4b and PiCamera V3 (wide)

#### timelapse system based on Raspberry Pi 4b and PiCamera V3 wide

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
Two holes at the cover sides can be used for other fixing systems (i.e. for brackets with suction caps to suspend the system on a window).<br />
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

A resume picture of the setting is available [here](https://github.com/AndreaFavero71/timelapse/blob/main/pictures/settings.png) <br />
More info at [instructable page of this project](https://www.instructables.com/Timelapse-With-Raspberry-Pi-4b-and-PiCamera-V3-wid/) <br />
<br /><br /><br /><br />


## Usage:
1. Switch on the Raspberry Pi.<br />
2. Connect to it; If you want a camera preview, a remote desktop connection is necessary like VNC Viewer.<br />
3. The relevant files are into the timelapse folder: ```cd timelapse```<br />
4. Edit the settings.txt file (quite self explanatory) and set the parameters according to your needs: ```nano settings.txt``` (save the file, with Ctrl + X, followed by Y, followed by Enter)<br />
5. Run the script: ```python timelapse.py``` (changes at the settings are only loaded at the scrip start). Arguments can be passed.<br />
6. The code defaults to V2 camera. If you use the V3 camera, add v3_camera argument: ```python timelapse.py --v3_camera```

Feedbacks on the display:<br />
- At the start it shows the main settings, including an estimation of pictures quantity the microSD can store<br />
- Time left for the first picture<br />
- After the first picture is taken, it indicates the picture progressive number<br />
- After the last picture is taken, if set, it indicates the video editing status<br />

In case the movie is not sattisfactory: Via the script video_render.py the video can be (re)made by changing some parameters. For this reason, when set, the pictures aren't automatically erased after a job completion; pictures are automatically erased at the start of a new job.<br />
By pressing one of the buttons for 5 seconds the cycle is stopped<br />
By pressing one of the buttons for more than 10 seconds the script is quitted; If the automating shut-off is set, this is the way to safely close stuff before unpowering the Raspberry Pi.<br />
<br /><br /><br /><br />


## Different methods defining the shooting approach:<br />
1) Shooting predefined between start_hhmm and stop_hhmm, for one or multiple days:<br />
- Set start_now as False and local_control as False.<br />
- Set start_hhmm and stop_hhmm to define the shooting period.<br />
- This method ends automatically, once the stop_hhmm of the last day is reached.<br /><br />


2) Shooting starting once the script is launced (eventually automated at the Raspberry Pi boot), and lasting for the period_hhmm:
- Set start_now as True and local_control as False.<br />
- Set period_hhmm to define how long the shooting period should last.<br />
- Also in this case the pictures quantity are predefined.<br />
To extend the shooting over days, weeks, etc, more than 2 digits can be set at the hours of period_hhmm (i.e. set '1000:30' to shoot for 1000 hours and 30 minutes).<br /><br />


3) By manually starting and pausing the shooting, eventually multiple times, via the buttons on the display:
- Set local_control as True.
- In this case the pictures quantity aren't predefined.
In all cases:
  - The interval between shots is defined by interval_s
  - A long press (>10 secs), of one of the buttons, will terminate the shooting and the script.

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


## Recovery from power outage
This is especially relevant when the system is used for long periods, and power outage might happens. <br />
1. Set the automatic scrip to start at Boot. <br />
2. Set "date_folder" : "False" <br />
3. Set "erase_pics" : "False" <br />

After the power outage, Raspberry Pi boots and the code checks for the latest picture suffix as reference for the next new picture.<br />
In case of multiple days shooting, the days already covered by shooting (partially or fully) are counted (full days without power are also counted). Counted days are detracted from the total days set in settings, to complete the shooting as per schedule.
<br /><br /><br /><br />


## Shooting when enough illuminance
The illuminance estimation by the camera can be used to avoid shooting if illuminance is below a threshold. <br />
1. Set "lux_check" : "True"   (Default is False). <br />
2. Set "lux_threshold" : "30" (30 is about the illuminance at sunset/sunshine. Check [Wikipdia](https://en.wikipedia.org/wiki/Illuminance) for values reference. <br />

When "lux_check" is set False the code doesn't check the illuminance estimation by the camera. <br />
When "lux_check" is set True, and illuminance drops below "lux_threshold", the pictures aren't taken. In this case less pictures are saved while the shooting schedule is safeguarded. <br />
As example of "lux_threshold": "30":<br />
![title image](/pictures/lux30.jpg)  <br />
Make your own check on which threshold fits your setup.
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


## More info:
A resume picture of the setting is available [here](https://github.com/AndreaFavero71/timelapse/blob/main/pictures/settings.png) <br />
More info at [instructable page of this project](https://www.instructables.com/Timelapse-With-Raspberry-Pi-4b-and-PiCamera-V3-wid/) <br />
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

