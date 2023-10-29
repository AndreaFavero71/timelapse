#!/usr/bin/python
# coding: utf-8

"""
#############################################################################################################
#  Andrea Favero 28 October 2023,
#  Timelapse module, based on Raspberry Pi 4b and PiCamera V3 (wide)
#############################################################################################################
"""


#imports
from picamera2 import Picamera2, Preview
from libcamera import controls
from os import system
from time import time, sleep, localtime, strftime
from datetime import datetime, timedelta
import os.path, pathlib, stat, sys, json
import RPi.GPIO as GPIO

parent_folder = '/home/pi/shared'        # parent folder from which pictures folders are appended
debug = False                            # variable for debug printout


def to_bool(value):
    """ Converts argument to boolean. Raises exception for invalid formats
        Possible True  values: 1, true, True, "1", "TRue", "yes", "y", "t"
        Possible False values: 0, false, False, None, [], {}, "", "0", "faLse", "no", "n", "f", 0.0, ...
    """
    global error
    if str(value).lower() in ("yes", "y", "true",  "t", "1"): return True
    elif str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): return False
    raise Exception('  Invalid value for boolean conversion: ' + str(value))
    error = 1                                            # error variable is set to 1 




def check_screen_presence():
    """ Checks if a display is connected, eventually via VNC; This is not the (SPI) display at Raspberry Pi."""
    
    import os
    
    if 'DISPLAY' in os.environ:                          # case the environment variable DISPLAY is set to 1 (there is a display)
        if debug:                                        # case debug variable is set true on __main__
            print('display function is availbale')       # feedback is printed to the terminal
        return True                                      # function returns true, meaning there is a screen connected
    else:                                                # case the environment variable DISPLAY is set to 0 (there is NOT a display)
        if debug:                                        # case debug variable is set true on __main__
            print('display function is not availbale')   # feedback is printed to the terminal
        return False                                     # function returns false, meaning there is NOT a screen connected



def setup():
    """ Reads settings from the settings.txt file and load them as global variables.
        Makes the folder for the pictures
        Sets the camera, and the display
    """
    global local_control, erase_pics, erase_movies, preview, display, start_now, rendering   # boolean settings
    global fix_movie_t, autofocus, hdr, overlay_fps, date_folder      # boolean settings
    global folder, pic_name, period_hhmm, period_hhmm, start_hhmm, end_hhmm, pic_format   # string settings
    global camera_w, camera_h, interval_s, movie_time_s, fps, days    # integer settings
    global focus_dist_m                                               # float setting
                    
    error = 0                                            # error cose is set to zero (no errors)
    folder = pathlib.Path().resolve()                    # active folder   
    fname = os.path.join(folder,'settings.txt')          # folder and file name for the settings
    if os.path.exists(fname):                            # case the settings file exists
        with open(fname, "r") as f:                      # settings file is opened in reading mode
            settings = json.load(f)                      # json file is parsed to a local dict variable
        
        if debug:                                        # case debug is set true
            print()                                      # print empty line
            print(settings)                              # print the settings
            print()                                      # print empty line
        
        try:                                             # tentative
            local_control = to_bool(settings['local_control']) # flag to enable setting changes via UI at Raspberry Pi
            erase_pics = to_bool(settings['erase_pics']) # flag to erase old pictures from folder
            erase_movies = to_bool(settings['erase_movies']) # flag to erase old movies from folder
            preview = to_bool(settings['preview'])       # flag to show the camera preview to screen (anso VNC)
            display = to_bool(settings['display'])       # flag for display usage
            start_now = to_bool(settings['start_now'])   # flag to force shoting immediatly or at set datetime
            rendering = to_bool(settings['rendering'])   # flag for automatic video rendering in Raspberry Pi
            fix_movie_t = to_bool(settings['fix_movie_t'])  # flag for automatic video rendering in Raspberry Pi
            autofocus = to_bool(settings['autofocus'])   # flag to enable/disable autofocus
            hdr = to_bool(settings['hdr'])               # flag for hdr (High Dinamy Range) camera setting
            overlay_fps = to_bool(settings['overlay_fps'])  # flag for overlaying the used fps at movie rendering
            date_folder = to_bool(settings['date_folder'])  # flag to force folder name of current yyyymmdd instead folder name
            
            folder = str(settings['folder'])             # folder name to store the pictures
            pic_name = str(settings['pic_name'])         # picture prefix name
            pic_format = str(settings['pic_format'])     # picture format
            period_hhmm = str(settings['period_hhmm'])   # shooting period in hhmm when start_now
            start_hhmm = str(settings['start_hhmm'])     # hh:mm of shooting start time
            end_hhmm = str(settings['end_hhmm'])         # hh:mm of shooting end time
            
            interval_s = int(settings['interval_s'])     # pictures cadence in seconds (smallest is ca 2 seconds for jpeg and 5 for png)
            movie_time_s = int(settings['movie_time_s']) # movie duration time
            camera_w = int(settings['camera_w'])         # camera width in pixels
            camera_h = int(settings['camera_h'])         # camera height in pixels
            fps = int(settings['fps'])                   # default fps at video generation (when not forced to a fix video time)
            days = int(settings['days'])                 # how many days the timelapse is made
            
            focus_dist_m = float(settings['focus_dist_m'])  # distance in meter for manual focus
            
        except:                                          # case of exceptions
            print('  error on converting imported parameters to bool or int') # feedback is printed to the terminal
            error = 1                                    # error variable is set to 1
            return error
   
    else:                                                # case the settings file does not exists, or name differs
        print('  could not find the file: ', fname)      # feedback is printed to the terminal
        error = 1                                        # error variable is set to 1
        return error                                     # error code is returned
    
    screen = check_screen_presence()                     # screen presence is checked
    if preview and not screen:                           # case the preview is set True and screen is not detected
        preview = False                                  # preview is changed to False to prevent errors
        print("  Preview setting changed to False as not detected any screen")  # feedback is printed to terminal
    
    # folder presence check / creation
    if date_folder:                                      # case date_folder is set True
        folder = str(datetime.today().strftime('%Y%m%d'))  # folder name is retrieved as yyyymmdd
    folder = os.path.join(parent_folder, folder)         # folder will be appended to the parent folder
    
    
    if not os.path.exists(folder):                       # case the folder does not exist
        os.makedirs(folder)                              # folder is made
        ret = system(f"sudo chmod 777 {folder}")         # change permissions to the folder: Read, write, and execute by all users
        if ret != 0:                                     # case the permission change return an error
            print(f"  Issue at changing the folder permissions") # negative feedback printed to terminal
    
    set_gpio()                              # gpio are set
    
    error = set_camera()                    # camera is set
    if error!=0:                            # case camera setting raises errors
        return error                        # error is returned

    return error                            # error code is returned

   



def set_camera():    
    global picam2, camera_started
    
    global picam2, camera_started
    
    camera_started = False                  # camera_started variable is set False
    error = 0                               # error variable is set to 0 (no errors)
    picam2 = Picamera2()                    # camera object
    camera_conf = picam2.create_preview_configuration(main={"size": (camera_w, camera_h)},
                                                      lores={"size": (640, 360)}, display="lores") # camera settings
    picam2.configure(camera_conf)           # applying settings to the camera
    
    if hdr:                                 # case hdr is set true
        ret = os.system(f"v4l2-ctl --set-ctrl wide_dynamic_range=1 -d /dev/v4l-subdev0") # hdr on
    else:                                   # case hdr is set false
        ret = os.system(f"v4l2-ctl --set-ctrl wide_dynamic_range=0 -d /dev/v4l-subdev0") # hdr off
    if ret != 0:                            # case setting the hdr does not return zero
        print("  HDR setting returned an error")  # feedback is printed to the terminal
        error = 0.5                         # error variable is set to 1
        return error
    else:                                   # case setting the hdr returns zero
        sleep(0.5)                          # little sleep time    
    
    if autofocus:
        picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})  # Autofocus Auto requires a trigger to execute the focus
        
    else:
        focus_dist = 1/focus_dist_m if focus_dist_m > 0 else 10    #preventing zero division; 0.1 meter is the min focus dist (1/0.1=10)
        picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus_dist}) # manual focus; 0.0 is infinite (1/>>), 2 is 50cm (1/0.5)
    
    
    if preview:                             # case the previes is set true
        picam2.start_preview(Preview.QTGL)  # preview related function is activated
    else:                                   # case the previes is set false
        picam2.start_preview(Preview.NULL)  # preview related function is set Null
    sleep(1)                                # little sleep time
    picam2.start()                          # camera is finally acivated
    camera_started = True                   # flag to track the camera status
    return error                            # error code is returned





def set_gpio():
    # GPIO settings
    global  GPIO, disp                      # modules
    
    GPIO.setwarnings(False)                 # GPIO warning set to False to reduce effort on handling them
    GPIO.setmode(GPIO.BCM)                  # GPIO module setting  
    if display:                             # case display is set true: imports and setting for display 
        from timelapse_display import display as disp
        global upper_btn, lower_btn
        upper_btn = 23                      # GPIO pin used by the upper button
        lower_btn = 24                      # GPIO pin used by the lower button
        GPIO.setup(upper_btn, GPIO.IN)      # set the upper_btn as an input
        GPIO.setup(lower_btn, GPIO.IN)      # set the lower_button_pin as an input
        disp.clean_display()                # cleans the display
    else:                                   # case display is set false
        GPIO.setup(22, GPIO.OUT)            # set the pin 22 as an output
        GPIO.output(22,0)                   # set low the GPIO22 (used as for Mini Pi TFT Backlight)
   
    
        



def make_space(parent_folder):
    """ Removes all the pictures files from the parent_folder and sub-directories. 
        Empties the Trash bin from pictures and movies.
    """
    
    global error
    
    folders = [x[0] for x in os.walk(parent_folder)] # list folders in parent_folder
    f_types = ['jpg', 'png']                   # file types to delete from folder
    
    if erase_movies:                           # case erase_movies is set True
        f_types.append('mp4')                  # the movie extension is added to the list of file types
    
    for directory in folders:                  # iteration over the folders
        for f_type in f_types:                 # iteration over f_types
            for file in os.listdir(directory): # iteration over files in directory
                if file.endswith(f_type):      # case file ends as per f_type
                    ret1 = system(f"sudo rm {parent_folder}/**/*.{f_type}") # delete f_type files from parent folder and sub folders
                    if ret1 != 0:              # case the file(s) removal returns 0
                        print(f"  Issue at removing old {f_type} picture from {directory}") # negative feedback printed to terminal
                        error = 1              # error variable is set to 1
                    break                      # for loop iteration on files is interrupted
        
    if 'mp4' not in f_types:                   # case the movie type was not in the list of file types
        f_types.append('mp4')                  # file type to delete from trash bin
    
    if os.path.exists("/home/pi/.local/share/Trash/files/"):  # if case the folder does not exist
        for f_type in f_types:            # iteration over f_types
            for file in os.listdir("/home/pi/.local/share/Trash/files/"):  # iteration over files in trash bin folder
                if file.endswith(f_type): # case file ends as per f_type
                    ret2 = system(f"sudo rm /home/pi/.local/share/Trash/files/*.{f_type}")  # delete f_type files from folder  
                    ret3 = system(f"sudo rm /home/pi/.local/share/Trash/info/*.{f_type}.trashinfo") # delete f_type info from folder
                    if ret2 != 0:         # case the file(s) removal returns 0
                        print(f"  Issue at emptying the trash from {f_type} files")  # negative feedback printed to terminal
                        error = 1         # error variable is set to 1
                    if ret3 != 0:         # case the info removal returns 0
                        print(f"  Issue at emptying the trash from {f_type} files info") # negative feedback printed to terminal
                        error = 1         # error variable is set to 1
                    break                 # for loop iteration on files is interrupted





def test_camera(pic_test):
    """ Makes a first picture as test, and returns its size in Mb.
        This test picture is removed right after.
    """
    
    global error
    
    pic_size_bytes = 1                    # unit is assigned to pic_size_bytes variable
    pic_Mb = 1                            # unit is assigned to pic_Mb variable 
    try:                                  # tentative
        picam2.capture_file(pic_test)     # camera takes and save a picture
        pic_size_bytes = os.path.getsize(pic_test)  # picture size is measured in bytes
        pic_Mb = round(pic_size_bytes/1024/1024,2)  # picture size in Mb
        os.remove(pic_test)               # test picture is removed
        return 1, pic_size_bytes, pic_Mb  # return (when no exceptions)
    except:                               # exception
        print('\n  Camera failure')         # feedback is printed to the terminal
        error = 1                         # error variable is set to 1
        return 0, pic_size_bytes, pic_Mb  # return (when expections)




def disk_space():
    """ Checks the disk space (main disk), and returns it in Mb.
    """    
    st = os.statvfs('/')                      # status info from disk file system in root
    bytes_avail = (st.f_bavail * st.f_frsize) # disk space (free blocks available * fragment size)
    return int(bytes_avail / 1024 / 1024)     # return disk space in Mb




def time_update(start_time_s):
    """ Check current datetime: Returns the total secs from 00:00, and the left time in secs to the shooting start time.
    """
    now_s = 3600*datetime.now().hour + 60*datetime.now().minute + datetime.now().second  # datetime convert to secs 
    if start_time_s < now_s:
        time_left_s = 86400 - now_s + start_time_s
    else:
        time_left_s = start_time_s - now_s  # time difference in secs, between the current time and shooting start time
    return now_s, time_left_s               # return




def printout(day, days, pic_Mb, disk_Mb, max_pics, frames, start_time_s, end_time_s,
             now_s, time_left_s, shoot_time_s, fps, overlay_fps):
    
    """ Prints the main information to the terminal.
    """
       
    line = "  "+"#"*78
    print('\n'*5)
    print(line)
    print(line)    
    if local_control:
        print(f"  Local control is enabled")
    else:
        print(f"  Local control is disabled")
    
    print(f"  Picture resolution: {camera_w}x{camera_h}")
    if autofocus:
        print(f"  Camera set to autofocus")
    else:
        print(f"  Camera set to manual focus at {focus_dist_m} meters")
    print(f"  Picture HDR: {hdr}")
    print(f"  Picture format: {pic_format}")
    print(f"  Picture file size {str(pic_Mb)} Mb  (picture size varies on subject and light!)")
    print(f"  Free disk space: {disk_Mb} Mb")
    print(f"  Rough max number of pictures: {max_pics}")
    
    print(f"  Day {day+1} of {days}")
    if start_now:
        print("  Shooting starts now")
    else:
        if time_left_s > 0:
            print(f"  Shooting starts     {secs2hhmmss(start_time_s)}")
            print(f"  Shooting ends       {secs2hhmmss(end_time_s)}")
            print(f"  Shooting starts in  {secs2hhmmss(time_left_s)}")

    print(f"  Shooting period     {secs2hhmmss(shoot_time_s)}")
    print(f"  Shooting every {interval_s} seconds")
    
    if max_pics < frames:
        if days>1 and not rendering:
            print(f"  Number of pictures limited to: {frames} a day, due to storage space")
        else:
            print(f"  Number of pictures limited to about: {frames}, due to staorage space")
    else:
        if days>1:
            print(f"  Camera will take {frames} pictures a day")
        else:
            print(f"  Camera will take {frames} pictures")
            
    if rendering:
        print(f"  Timelapse video render activated")
        if overlay_fps:
            print(f"  Fps value will be overlayed on the video")
        if fix_movie_t:
            print(f"  Video rendered at {fps} fps, lasting {round(frames/fps)} secs")
        
    else:
        print(f"  Timelapse video render not activated")
    
    if display:
        print(f"  Display at Raspberry Pi activated")
    else:
        print(f"  Display at Raspberry Pi not activated")
    print(line)
    print(line)




def display_info(day, days, pic_Mb, disk_Mb, max_pics, frames, start_time_s, end_time_s,
                 now_s, interval_s, time_left_s, shoot_time_s, fps, autofocus, focus_dist_m):
    
    """ Prints the main information to the display.
    """
    
    disp_time_s = 3
    
    disp.set_backlight(1)
    
    if autofocus:
        disp.show_on_disp4r('AUTOFOCUS', 'ACTIVATED', fs1=26, y2=75, fs2=28)
        sleep(disp_time_s)
    else:
        disp.show_on_disp4r('MANUAL FOCUS', 'FOSUS: ' + str(focus_dist_m) + ' m', fs1=22, y2=75, fs2=24)
        sleep(disp_time_s)
    
    if hdr:
        disp.show_on_disp4r('HDR', 'ACTIVATED', fs1=32, y2=75, fs2=30)
        sleep(disp_time_s)
    else:
        disp.show_on_disp4r('HDR NOT', 'ACTIVATED', fs1=27, y2=75, fs2=30)
        sleep(disp_time_s)
    
    disp.show_on_disp4r('RESOLUTION', str(camera_w)+'x'+str(camera_h), fs1=27, y2=75, fs2=30)
    sleep(disp_time_s)
    disp.show_on_disp4r('PICTURE AS', str(pic_format), fs1=27, y2=75, fs2=30)
    sleep(disp_time_s)
    disp.show_on_disp4r('SIZE (Mb)', str(pic_Mb), fs1=27, y2=75, fs2=30)
    sleep(disp_time_s)
    disp.show_on_disp4r('DISK SPACE (Mb)', str(disk_Mb), fs1=21, y2=75, fs2=26)
    sleep(disp_time_s)
    disp.show_on_disp4r('MAX PICS (#)', str(max_pics), fs1=25, y2=75, fs2=30)
    sleep(disp_time_s)
    if max_pics < frames:
        disp.show_on_disp4r('LIMITED TO (#)', str(frames), fs1=21, y2=75, fs2=30)
        sleep(disp_time_s)
    else:
        disp.show_on_disp4r('# OF SHOOTS', str(frames), fs1=24, y2=75, fs2=30)
        sleep(disp_time_s)
    
    disp.show_on_disp4r('SHOOT EVERY', str(interval_s)+' s', fs1=25, y2=75, fs2=30)
    sleep(disp_time_s)
    
    if start_now:
        disp.show_on_disp4r('SHOOTING', 'NOW', fs1=26, y2=75, fs2=30)
        sleep(disp_time_s)
    else:
        if start_time_s > now_s :
            disp.show_on_disp4r('SHOOTING IN', secs2hhmmss(time_left_s), fs1=23, y2=75, fs2=22)
            sleep(disp_time_s)
            disp.show_on_disp4r('STARTS ON', secs2hhmmss(start_time_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
            sleep(disp_time_s)        
            disp.show_on_disp4r('ENDS ON', secs2hhmmss(end_time_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
            sleep(disp_time_s)
    
    if rendering:
        disp.show_on_disp4r('RENDER', 'ACTIVE', fs1=30, y2=75, fs2=30)
        sleep(disp_time_s)
    else:
        disp.show_on_disp4r('RENDER', 'NOT ACTIVE', fs1=30, y2=75, fs2=24)
        sleep(disp_time_s)
    
    disp.set_backlight(0)




def secs2hhmmss(secs):
    return str(timedelta(seconds=secs))




def display_time_left(time_left_s):
    """ Shows the left time to shooting, and turns the display backlight off.
        The display backlight is set off longer for longer left time. 
    """
    # feedback is printed to display
    disp.show_on_disp4r('SHOOTING IN', secs2hhmmss(time_left_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
    disp.set_backlight(1)        # backlight on
    
    if time_left_s > 3600:       # case time_left_s is more than one hour
        sleep(2)                 # sleep when waiting for the planned shooting start
        disp.set_backlight(0)    # backlight off
        sleep(10)                # sleep when waiting for the planned shooting start
    elif time_left_s > 60:       # case time_left_s is more than one minute
        sleep(2)                 # sleep when waiting for the planned shooting start
        disp.set_backlight(0)    # backlight off
        sleep(5)                 # sleep when waiting for the planned shooting start
    elif time_left_s > 12:       # case time_left_s is more than 12 seconds
        sleep(1)                 # sleep when waiting for the planned shooting start
        disp.set_backlight(0)    # backlight off
        sleep(1)                 # sleep when waiting for the planned shooting start
    else:                        # case time_left_s is less than 12 seconds
        sleep(0.1)               # sleep when waiting for the planned shooting start




def shoot(folder, fname, frame, pic_format, focus_ready, ref_time):
    """ Takes a picture, and saves it in folder with proper file name (prefix + incremental).
        When autofocus, the shoot is done once the camera confirms the focus achievement.
    """
    
    if autofocus:                                              # case autofocus is set True (settings)
        while not picam2.wait(focus_ready):                    # while the autofocus is not ready yet
            sleep(0.05)                                        # short sleep
    
    while time() < ref_time:                                   # while it isn't time to shoot yet
        sleep(0.05)                                            # short sleep
    
    pic_name = '{}_{:05}.{}'.format(fname, frame, pic_format)  # file name construction for the picture
    picture = os.path.join(folder, pic_name)                   # path and file name for the picture
    picam2.capture_file(picture)                               # camera takes and save a picture
    
    ret = system(f"sudo chmod 777 {picture}")   # change permissions to the picture file: Read, write, and execute by all users
    if ret != 0:                                               # case the permission change return an error
        print(f"  Issue at permissions changing of picture file ")  # negative feedback printed to terminal





def video_render(folder, fps, overlay_fps):
    """ Renders all pictures in folder to a movie.
        Saves the movie in folder with proper file datetime file name.
        When the setting constrains the movie to a fix time, the fps are adapted.
    """
    
    global error
    
    render_start = time()         # initial time as reference
    print(f"\n  Video rendering started...") # feedback is printed to the terminal
    if display:                   # case display is set true
        disp.show_on_disp4r('RENDERING', '', y1= 50, fs1=30) # feedback is printed to display
    
    render_warnings = False       # flag to printout the rendering ffmpeg error 
    render_progress = False       # flaf to printout the rendering progress (statistics)
    loglevel = '' if render_warnings else '-loglevel error'  # rendering log feedback commands for ffmpeg
    stats = '' if render_progress else '-nostats'            # statistic feedback commands for ffmpeg
    
    pic_files = os.path.join(folder, '*.' + pic_format)      # pictures files constructor 
    movie_fname = os.path.join(folder, strftime("%Y%m%d_%H%M%S", localtime())+'.mp4') # movie filename to output
    res = str(camera_w)+'x'+str(camera_h)                    # movie resolution
    
    if overlay_fps:                      # case overlay_fps is set true
        text = f"{fps}X"                 # text that will be overlayed  
        font = '/usr/share/fonts/truetype/freefont/dejavu/DejaVuSans.ttf'  # font path/filename
        fcol = 'white'                   # font color
        fsize = '48'                     # font size
        bcol = 'black@0.5'               # box color with % of transparency
        pad = str(round(int(fsize)/5))   # 20% of the font size
        pos_x = '80'                     # reference from the left
        pos_y = str(camera_h - 80)       # reference from the bottom
        # video filter (v_f) string holding the parameters
        v_f = (f"drawtext=fontfile={font}:text={text}:fontcolor={fcol}:fontsize={fsize}:box=1:boxcolor={bcol}:boxborderw={pad}:x={pos_x}:y={pos_y}")
        
        # ffmpeg command with text addition
        render = f"ffmpeg {stats} {loglevel} -f image2 -framerate {fps} -pattern_type glob -i '{pic_files}' -s '{res}'  -vf '{v_f}' '{movie_fname}' -y"
    
    else:                                # case overlay_fps is set false
        # ffmpeg command without text addition
        render = f"ffmpeg {stats} {loglevel} -f image2 -framerate {fps} -pattern_type glob -i '{pic_files}' -s '{res}' {movie_fname} -y"
    
    ret = system(render)                                                     # ffmpeg command is executed
    
    if ret==0:                                                               # case the ffmpeg returns 0
        render_time = timedelta(seconds=round(time() - render_start))        # rendering time
        print(f"  Timelapse successfully rendered, in {render_time}")          # positive feedback is printed to the terminal
        print(f"  Timelase saved as {movie_fname}")                            # movie path/filename is printed to the terminal
        if display:                                                          # case display is set true
            t_ref = datetime.now().strftime("%H:%M:%S")
            disp.show_on_disp4r('RENDERING', 'DONE AT:', t_ref, "(SCRIPT ENDED)",
                                fs1=30, fs2=30, fs3=30, fs4=22)       # positive feedback is printed to display
    else:                                                                    # case the ffmpeg does not returns 0
        print("  Timelapse edit error\n")                                      # negative feedback is printed to the terminal
        if display:                                                          # case display is set true
            disp.show_on_disp4r('RENDERING', 'ERROR', fs1=26, y2=75, fs2=28) # negative feedback is printed to display
        error = 1                                                            # error variable is set to 1




def cpu_temp():
    """ Returns the cpu temperature.
    """
    cpu_t = 0                                            # zero is assigned to cpu_t variable
    try:                                                 # tentative
        tFile = open('/sys/class/thermal/thermal_zone0/temp')  # file with the cpu temp, in mDegCelsius (text format)
        cpu_t = round(float(tFile.read()) /1000, 1)      # tempertaure is converted to (float) degCelsius
    except:                                              # exception
        tFile.close()                                    # file is closed
    return cpu_t                                         # cpu_t is returned




# def check_btns():
#     """both buttons are checked."""
#     if not GPIO.input(upper_btn) or not GPIO.input(lower_btn):  # case one button is pressed
#         stop_or_quit()                       # stop_or_quit function is called 




def stop_or_quit(button):
    """Distinguishes the request to just stop a cycle or to SHUT the Rpi OFF.
        The input is the upper or lower button and related pressing time.
        When the button is pressed longer than warning_time, a warning message is displayed.
        When the button is not released within the quit_time, the Rpi SHUT-OFF."""
    
    global error, stop_shooting, quitting_phase
    
    if rendering_phase:                      # case rendering_phase is True
        return                               # this function does nothing       
    
    warn_time = 2                            # delay used as threshold to print a quit warning on display
    quit_time = 6                            # delay used as threshold to quit the script
    warning = False                          # warning is set false, to warn user to keep or release the button
    quitting = False                         # quitting variable is set false
    ref_time = time()                        # reference time used to measure how long the button has been kept pressed
    
    button = upper_btn if not GPIO.input(upper_btn) else lower_btn   # button used

    if not GPIO.input(button):               # case button is still pressed once the stop_or_quit function is called           
        while not GPIO.input(button):                     # while button is pressed 
            if not warning:                               # case warning is false
                if time() - ref_time >= warn_time:        # case time elapsed is >= warn_time reference
#                     disp.clean_display()                  # display is cleaned
                    disp.set_backlight(1)                 # display backlight is turned on, in case it wasn't
                    disp.show_on_disp4r('STOPPED', 'SHOOTING', fs1=37, y2=75, fs2=34) # feedback is printed to the display
                    stop_shooting = True                  # stop shooting is set True
                    warning = True                        # warning is set true
                    sleep(1)                              # wait time to let the message visible on the display

            while warning:                                # case warning is true
                disp.set_backlight(1)                     # display backlight is turned on, in case it wasn't
                disp.show_on_disp4r('SURE TO', 'QUIT ?', fs1=36, y2=75, fs2=42) # feedback is printed to display
                if GPIO.input(button):                    # case the button is released
                    disp.set_backlight(1)                 # display backlight is turned on, in case it wasn't
                    disp.show_on_disp4r('NOT', 'QUITTING', fs1=42, y2=80, fs2=36) # feedback is printed to display
                    quitting_phase = False                # quitting_phase variable is set False
                    break                                 # while loop is interrupted
                if time() - ref_time >= quit_time:        # case time elapsed is >= quit time reference
                    quitting_phase = True                 # quitting_phase variable is set True
                    quitting = True                       # quitting variable is set true
                    
                if quitting:                              # case the keep_quitting variable is true
                    print('\n\n  quitting request')       # feedback is printed to display
                    for i in range(5):                    # iteration for  5 times
                         disp.set_backlight(1)            # display backlight is turned on, in case it wasn't
                         disp.show_on_disp4r('SHUTTING', 'OFF', fs1=36, y2=75, fs2=42) # feedback is printed to display
                         sleep(1)                         # wait time to let the message visible on the display
        
                    countdown = 3                         # count-down variable
                    for i in range(countdown,-1, -1):     # iteration down the countdown variable
                        disp.set_backlight(1)                     # display backlight is turned on, in case it wasn't
                        dots = ''                         # dot string variable is set empty
                        for k in range(min(i,3)):         # iteration over the residual cont-down, with max of three
                            dots = dots + '.'             # dot string variable adds a dot character          
                        row2_text = str(i) + dots         # string variable to be printed on the second disply row
                        disp.show_on_disp4r('SHUT OFF IN', row2_text, x1=20, x2=20, y2=50, fs1=25, fs2=70)# feedback is printed to the display
                        if i > 0:                         # case the cont-down is above 0
                            sleep(1)                      # wait time to let the message visible on the display
                    
                    disp.set_backlight(0)                 # display backlight is turned off

                    if not GPIO.input(upper_btn) or not GPIO.input(lower_btn):   # case one of the buttons is pressed
                        disp.set_backlight(1)             # display backlight is turned on
                        disp.show_on_disp4r('EXITING', 'SCRIPT', fs1=36, y2=75, fs2=42) # feedback is printed to the display
                        sleep(1)                          # some little delay
                        process_to_kill = "timelapse_bash.sh | grep -v grep | grep -v timelapse_terminal.log"  # string to find the process PID to kill
                        nikname = "timelapse_bash.sh"     # process name
                        kill_process(process_to_kill, nikname)  # call to the killing function
                        sleep(1)                          # some little delay
                        disp.set_backlight(1)             # display backlight is turned on, in case it wasn't
                        disp.show_on_disp4r('SCRIPT', 'ENDED', fs1=36, y2=75, fs2=42) # feedback is printed to the display
                        sleep(2)                          # some little delay
                        disp.set_backlight(0)             # display backlight is turned off
                        error = 2                         # error coe is set to 2 (quittings the script, without RPI shut off) 
    
                    exit_func(error)                      # qutting function is called
    
    
#     time.sleep(5)       # time to mask the button pressing time (interrupt), eventually used to quit the script
#     reset()             # call the robot reset function





def kill_process(process, nikname):
    """function to kill the process in argument."""
    
    import os
    import psutil
    import subprocess
    
    p_name = "ps ax | grep -i " + process        # process name to search the PID

    for line in os.popen(p_name):                # iterating through each instance of the process
        print(f"\nkilling process {nikname}")
        fields = line.split()                    # output from px aux
        pid = fields[0]                          # extracting Process ID from the output
        cmd = "sudo kill -9 %s" % pid            # command to terminate the process ( -9 to kill force fully)
        result = subprocess.run(cmd, shell=True) # executing the command to terminate the process, and collecting the output
        if result.returncode == 0:               # case the returncode equals to zero (command executed with success)
            print(f"  Process {nikname} is terminated")  # feedback is printed to the terminal
                




def exit_func(error):
    """ Exit function, taking care to properly close things.
    """
    try:                            # tentative
        picam2.stop()               # camera is finally acivated
    except:                         # exception
        print("  failing to close the Picamera") # feedback is printed to the terminal
    
    if not rendering_phase:         # case rendering_phase is set False
        try:                        # tentative
            disp.clean_display()    # cleans the display
        except:                     # exception
            print("  failing to clean the display") # feedback is printed to the terminal
        
        try:                        # tentative
            GPIO.output(22,0)       # set low the GPIO22 (used as for Mini Pi TFT Backlight)
        except:                     # exception
            print("  failing to set low the GPIO pin 22") # feedback is printed to the terminal
    
    sys.exit(error)                 # script is quitted with defined error value




def main():
    """ Main fuction.
    """
    
    global picam2, camera_started, error, stop_shooting, shooting_phase, rendering_phase, quitting_phase, focus_ready, days
    
    shooting_phase = False                     # flag covering the shooting period, is set False
    rendering_phase = False                    # flag covering the rendering period, is set False
    quitting_phase = False                     # flag covering the quitting_phase phase, is set False
    stop_shooting = False                      # flag to stop shooting on a day when multiple days
    error = 0                                  # error value for the script quitting (0 means no errors)
    error = setup()                            # retrieves settings, and initializes things
    
    if autofocus:                              # case the autofocus is set True (settings)
        time_for_focus = 8                     # time for the camera to focus
    else:                                      # case the autofocus is set False (settings)
        time_for_focus = 0                     # time for the camera to focus is set to zero

    
    frame = 0                                  # incremental index appended after pictures prefix
    pic_test_fname = os.path.join(folder, 'picture_test.'+pic_format)   # name for the test picture
    ret, pic_size_bytes, pic_Mb = test_camera(pic_test_fname)           # test picture is made, measured, removed
    
    try:                                       # tentative
        start_time = datetime.strptime(str(start_hhmm),'%H:%M')  # start_hhmm string is parsed to datetime
        start_time_s = 3600*start_time.hour + 60*start_time.minute # start_time is converted to seconds (since 00:00)
        end_time = datetime.strptime(str(end_hhmm),'%H:%M')      # end_hhmm string is parsed to datetime
        end_time_s = 3600*end_time.hour + 60*end_time.minute       # end_time is converted to seconds (since 00:00)
    except:                                    # exception
        sys.exit(print("  variable 'start_hhmm' or 'end_hhmm' do not reppresent a valid time")) # feedback is printed to terminal
        error = 1                              # error variable is set to 1 (True)
    
    if start_now:                              # case start_now is set True
        hh, mm = period_hhmm.split(':')        # period_hhmm is split in string 'hh' and string 'mm'
        shoot_time_s = int(hh) * 3600 + int(mm) * 60 # shooting time in seconds is calculated
        days = 1                               # when start_now only a single period (day) is considered
                                   
    else:
        if end_time_s < start_time_s:   # case end_time is smaller (advance) than start_time, the end_time in on the next day
            shoot_time_s =  end_time_s + 86400 - start_time_s  # shooting time is calculated
        else:                           # case end_time is bigger (later) than start_time, the end_time in on the same day
            shoot_time_s = end_time_s - start_time_s   # shooting time is calculated
            
    if erase_pics:                             # case erase_pics is set true (settings)
        make_space(parent_folder)              # emptying the folder from old pictures
    
    
    for day in range(days):                    # iteration over the days (settings)
        frame_d = 0                            # incremental index per each day used for shooting time
        
        if rendering and day>0:                # if rendering makes space every day after the first one
            make_space(parent_folder)          # emptying the folder from old pictures
        
        disk_Mb = disk_space()                 # disk free space
        max_pics = int(disk_Mb/pic_Mb)         # rough amount of allowed pictures quantity in disk
        frames = int(shoot_time_s/interval_s)  # frames (= pictures) quantity is calculated
        fps = round(frames/movie_time_s) if fix_movie_t else fps  # in case fix_movie_t is set true (forced movie time) the fps is calculated
        fps = 1 if fps < 1 else fps            # preventing fps == 0
     
        now_s, time_left_s = time_update(start_time_s)   # current time, and time left to shooting start, is retrieved
        
        # startup feedback prints to the terminal
        printout(day, days, pic_Mb, disk_Mb, max_pics, frames, start_time_s, end_time_s,
                 now_s, time_left_s, shoot_time_s, fps, overlay_fps)
        
        # startup feedback prints to the display
        if display:
            display_info(day, days, pic_Mb, disk_Mb, max_pics, frames, start_time_s, end_time_s,
                         now_s, interval_s, time_left_s, shoot_time_s, fps, autofocus, focus_dist_m)
            
            try:                                   # tentative
                GPIO.add_event_detect(upper_btn, GPIO.FALLING, callback=stop_or_quit, bouncetime=20) # interrupt usage (of the same input pin)
                GPIO.add_event_detect(lower_btn, GPIO.FALLING, callback=stop_or_quit, bouncetime=20) # interrupt usage (of the same input pin)
            except:                                # exception
                pass                               # do nothing
        
        if not start_now:                          # case start_now is set false (delayed start)   
            if time_left_s > time_for_focus:       # case the time left for shooting is bigger than time needed for camera focus
                while time_left_s >= time_for_focus:    # while time left for shooting is bigger than time needed for camera focus
                    now_s, time_left_s = time_update(start_time_s)  # current time, and time left to shooting start, is retrieved again 
                    if display and not quitting_phase:  # case display is set true
                        display_time_left(time_left_s)  # prints left lime to display, and pause
                        
        
        # from here onward time is managed as per time module
        start_time = time()                        # start reference time
        ref_time = start_time                      # reference time to call the shoot function

        while not stop_shooting:                   # looping until quitting_phase becomes True or breaking within the loop
            # while loop ends when frames quantity is reached, or stop request (buttons, Ctrl+C, etc)
            if camera_started == False:            # case camera_started is set False and almost time to shoot
                if preview:                        # case preview is set True             
                    picam2.start_preview(Preview.QTGL) # re-starting the camera preview
                picam2.start()                     # re-starting the camera
                camera_started = True              # camera_started is set True
            
            if time() >= ref_time:                 # case time has reached the shooting moment
                shooting_phase = True              # variable shooting_phase is set True
                
                if autofocus:                      # case autofocus is set True (settings)
                    focus_ready = picam2.autofocus_cycle(wait=False)   #  autofocus is triggered, and it will return True once ready (not bloccant)
                else:                              # case autofocus is set False (settings)
                    focus_ready = True             # focus_ready is always true
                    
                if not quitting_phase:             # case quittining_phase is set False
                    shoot(folder, pic_name, frame, pic_format, focus_ready, ref_time)  # calls the shooting function
                    if frame_d %50 == 0:            # case the frame is mutiple of 100
                        t_ref = strftime("%d %b %Y %H:%M:%S", localtime())  # current local time passed as string
                        print('\n ', t_ref, '\t', "frame:", '{:05d}'.format(frame_d), end = ' ', flush=True) # current time and frame feedback to terminal
                    else:                          # case the frame is not mutiple of 100
                        print('*',end ='', flush=True) # a dot character is added to the terminal to show progress
            
                    if display:                    # case display is set true
#                         disp.show_on_disp4r('SHOOT', '{:05}'.format(frame_d), fs1=32, y2=75, fs2=34)  # feedback is printed to display
                        percent = 100*(frame_d+1)/frames
                        disp.display_progress_bar(percent, day+1, days, frame_d+1)
                        disp.set_backlight(1)      # display backlight is set on
                    
                    frame+=1                       # frame variable (used for picture name) is incremented by one
                    frame_d+=1                     # frame_d variable (used for shooting timimng) is incremented by one
                    ref_time = start_time + frame_d * interval_s  # reference time for the next shoot is assigned
                
                    if frame_d >= frames:          # caase current frame equals the set frames quantity
                        print()                    # print empty line
                        
                        # last frame takes got its own print to terminal, to make visible the frames quantity
                        print(' ',strftime("%d %b %Y %H:%M:%S", localtime()), '\t', "frame:", '{:05}'.format(frame_d), " is the last frame")
                        print("  Shooting completed")  # feedback is printed to terminal
                        break                      # while loop is interrupted                    
            
            
            sleep_time = interval_s/20
            sleep(sleep_time)          # sleep time in between time checks
        
        shooting_phase = False         # variable shooting_phase is set True
        stop_shooting = False          # quitting_phase variable is reset to False
        quitting_phase = False         # quitting_phase variable is reset to False
        
        if preview:                    # case preview is set True
            picam2.stop_preview()      # preview stream is stopped
        picam2.stop()                  # picamera object is closed
        camera_started = False         # camera_started variable is set False
        
        if rendering:                  # case rendering is set true
            rendering_phase = True     # rendering_phase variable is set True
            video_render(folder, fps, overlay_fps)  # video_render function is called
            rendering_phase = False    # rendering_phase variable is reset tp False
        
        print("\n  CPU temp:", cpu_temp()) # cpu temperature is printed to terminal
    
    exit_func(error)                   # exit function is caleld







if __name__ == "__main__":
    main()


