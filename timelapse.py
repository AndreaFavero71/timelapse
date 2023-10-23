#!/usr/bin/python
# coding: utf-8

"""
#############################################################################################################
#  Andrea Favero 17 July 2023,
#  Timelapse module, based on Raspberry Pi 4b and PiCamera V3 (wide)
#############################################################################################################
"""


#imports
from picamera2 import Picamera2, Preview
from libcamera import controls
from os import system
from time import time, sleep, localtime, strftime
from datetime import datetime, timedelta
import os.path, pathlib, sys, json
import RPi.GPIO as GPIO


def to_bool(value):
    """ Converts argument to boolean. Raises exception for invalid formats
        Possible True  values: 1, True, "1", "TRue", "yes", "y", "t"
        Possible False values: 0, False, None, [], {}, "", "0", "faLse", "no", "n", "f", 0.0, ...
    """
    if str(value).lower() in ("yes", "y", "true",  "t", "1"): return True
    elif str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))



def setup():
    """ Reads settings from the settings.txt file and load them as global variables.
        Makes the folder for the pictures
        Sets the camera, and the display
    """
    global erase_pics, preview, display, start_now, rendering, fix_movie_t, autofocus, hdr, overlay_fps   # boolean settings
    global folder, pic_name, start_hhmm, end_hhmm, pic_format         # string settings
    global camera_w, camera_h, interval_s, movie_time_s, fps, days    # integer settings
    global focus_dist_meters                             # float settings
    global GPIO, disp, picam2                            # modules
    global camera_started
    
    folder = pathlib.Path().resolve()                    # active folder   
    fname = os.path.join(folder,'settings.txt')          # folder and file name for the settings
    if os.path.exists(fname):                            # case the settings file exists
        with open(fname, "r") as f:                      # settings file is opened in reading mode
            settings = json.load(f)                      # json file is parsed to a local dict variable
#         print()
#         print(settings)
#         print()
        try:                                             # tentative
            erase_pics = to_bool(settings['erase_pics']) # flag to erase old pictures from folder
            preview = to_bool(settings['preview'])       # flag to show the camera preview to screen (anso VNC)
            display = to_bool(settings['display'])       # flag for display usage
            start_now = to_bool(settings['start_now'])   # flag to force shoting immediatly or at set datetime
            rendering = to_bool(settings['rendering'])   # flag for automatic video rendering in Raspberry Pi
            fix_movie_t = to_bool(settings['fix_movie_t'])  # flag for automatic video rendering in Raspberry Pi
            autofocus = to_bool(settings['autofocus'])   # flag to enable/disable autofocus
            hdr = to_bool(settings['hdr'])               # flag for hdr (High Dinamy Range) camera setting
            
            overlay_fps = to_bool(settings['overlay_fps'])  # flag for overlaying the used fps at movie rendering
            
            folder = str(settings['folder'])             # folder name to store the pictures
            pic_name = str(settings['pic_name'])         # picture prefix name
            pic_format = str(settings['pic_format'])     # picture format
            start_hhmm = str(settings['start_hhmm'])     # hh:mm of shooting start time
            end_hhmm = str(settings['end_hhmm'])         # hh:mm of shooting end time
            
            interval_s = int(settings['interval_s'])     # pictures cadence in seconds (smallest is ca 2 seconds for jpeg and 5 for png)
            movie_time_s = int(settings['movie_time_s']) # movie duration time
            camera_w = int(settings['camera_w'])         # camera width in pixels
            camera_h = int(settings['camera_h'])         # camera height in pixels
            fps = int(settings['fps'])                   # default fps at video generation (when not forced to a fix video time)
            days = int(settings['days'])                 # how many days the timelapse is made
            
            focus_dist_meters = float(settings['focus_dist_meters']) # distance in meters for manual focus
            
            
            
        except:                                          # case of exceptions
            print('error on converting imported parameters to bool or int') # feedback is printed to the terminal
    else:                                                # case the settings file does not exists, or name differs
        print('could not find the file: ', fname)        # feedback is printed to the terminal 
   

    # camera related settings
    picam2 = Picamera2()                    # camera object
    camera_conf = picam2.create_preview_configuration(main={"size": (camera_w, camera_h)},
                                                      lores={"size": (640, 360)}, display="lores") # camera settings
    
    if hdr:                                 # case hdr is set true
        ret = os.system(f"v4l2-ctl --set-ctrl wide_dynamic_range=1 -d /dev/v4l-subdev0") # hdr on
    else:                                   # case hdr is set false
        ret = os.system(f"v4l2-ctl --set-ctrl wide_dynamic_range=0 -d /dev/v4l-subdev0") # hdr off
    if ret != 0:                            # case setting the hdr does not return zero
        print("HDR setting returned an error")  # feedback is printed to the terminal
    sleep(0.5)                              # little sleep time
    
    if autofocus:                           # case autofococus is set true
        picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})    # continuous focus
    else:                                   # case autofococus is set false
        focus_dist = 1/focus_dist_meters if focus_dist_meters > 0 else 10  # preventing zero division; 0.1 meters is min focus distance (1/0.1=10)
        picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus_dist}) # manual focus;  0.0 is infinite (1/large), 2 is 50cm (1/0.5)
    
    picam2.configure(camera_conf)           # applying settings to the camera
    sleep(0.5)                              # little sleep time
    
    if preview:                             # case the previes is set true
        picam2.start_preview(Preview.QTGL)  # preview related function is activated
    else:                                   # case the previes is set false
        picam2.start_preview(Preview.NULL)  # preview related function is set Null
    
    sleep(0.5)                              # little sleep time
    picam2.start()                          # camera is finally acivated
    camera_started = True                   # flag to track the camera status

    # GPIO settings
    GPIO.setwarnings(False)                 # GPIO warning set to False to reduce effort on handling them
    GPIO.setmode(GPIO.BCM)                  # GPIO module setting  
    if display:                             # case display is set true: imports and setting for display 
        from timelapse_display import display as disp
        upper_btn_pin = 23                  # GPIO pin used by the upper button
        lower_btn_pin = 24                  # GPIO pin used by the lower button
        GPIO.setup(upper_btn_pin, GPIO.IN)  # set the upper_btn_pin as an input
        GPIO.setup(lower_btn_pin, GPIO.IN)  # set the lower_button_pin as an input
        disp.clean_display()                # cleans the display
    else:                                   # case display is set false
        GPIO.setup(22, GPIO.OUT)            # set the pin 22 as an output
        GPIO.output(22,0)                   # set low the GPIO22 (used as for Mini Pi TFT Backlight)


    # folder presence check / creation
    folder = os.path.join('/home/pi/shared', folder) # folder will be appended to the pi Video folder
    if not os.path.exists(folder):          # if case the folder does not exist
        os.makedirs(folder)                 # folder is made if it doesn't exist



def make_space(folder):
    """ Removes all the pictures files from the folder, and empties the Trash bin.
    """
    
    f_types = ['jpg', 'png']              # file types to delete from folder
    for f_type in f_types:                # iteration over f_types
        for file in os.listdir(folder):   # iteration over files in folder
            if file.endswith(f_type):     # case file ends as per f_type
                ret1 = system(f"rm {folder}/*.{f_type}") # delete f_type files from folder
                if ret1 != 0:             # case the file(s) removal returns 0
                    print(f"Issue at removing old {f_type} picture from folder") # negative feedback printed to terminal
                break                     # for loop iteration on files is interrupted
    
    f_types.append('mp4')                 # file type to delete from trash bin
    
    if os.path.exists("/home/pi/.local/share/Trash/files/"):     # if case the folder exists
        if os.path.exists("/home/pi/.local/share/Trash/info/"):  # if case the folder exists
            for f_type in f_types:        # iteration over f_types
                for file in os.listdir("/home/pi/.local/share/Trash/files/"):  # iteration over files in trash bin folder
                    if file.endswith(f_type): # case file ends as per f_type
                        ret2 = system(f"rm /home/pi/.local/share/Trash/files/*.{f_type}")  # delete f_type files from folder  
                        ret3 = system(f"rm /home/pi/.local/share/Trash/info/*.{f_type}.trashinfo") # delete f_type info from folder
                        if ret2 != 0:     # case the file(s) removal returns 0
                            print(f"Issue at emptying the trash from {f_type} files")  # negative feedback printed to terminal
                        if ret3 != 0:     # case the info removal returns 0
                            print(f"Issue at emptying the trash from {f_type} files info") # negative feedback printed to terminal
                        break             # for loop iteration on files is interrupted

def test_camera(pic_test):
    """ Makes a first picture as test, and returns its size in Mb.
        This test picture is removed right after.
    """
    pic_size_bytes = 1                    # unit is assigned to pic_size_bytes variable
    pic_Mb = 1                            # unit is assigned to pic_Mb variable 
    try:                                  # tentative
        picam2.capture_file(pic_test)     # camera takes and save a picture
        pic_size_bytes = os.path.getsize(pic_test)  # picture size is measured in bytes
        pic_Mb = round(pic_size_bytes/1024/1024,2)  # picture size in Mb
        os.remove(pic_test)               # test picture is removed
        return 1, pic_size_bytes, pic_Mb  # return (when no exceptions)
    except:                               # exception
        print('\nCamera failure')         # feedback is printed to the terminal
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
#     print("datetime.now().hour:", datetime.now().hour, "datetime.now().minute:", datetime.now().minute)
#     print("now_s", now_s)
#     print("time_left_s", time_left_s)
    return now_s, time_left_s              # return



def printout(pic_Mb, disk_Mb, max_pics, frames, start_time_s, end_time_s, now_s, time_left_s, shoot_time_s, fps, overlay_fps):
    
    """ Prints the main information to the terminal.
    """
       
    line = "#"*80
    print('\n\n')
    print(line)
    print(line)
    print(f"  Picture resolution: {camera_w}x{camera_h}")
    print(f"  Picture HDR: {hdr}")
    print(f"  Picture format: {pic_format}")
    print(f"  Picture file size {str(pic_Mb)} Mb  (picture size varies on subject and light!)")
    print(f"  Free disk space: {disk_Mb} Mb")
    print(f"  Rough max number of pictures: {max_pics}")

    if max_pics < frames:
        print(f"  Number of pictures limited to: {frames}")
    else:
        print(f"  Camera will take {frames} pictures")

    if start_now:
        print("  Shooting starts now")
    else:
        if time_left_s > 0:
            print(f"  Shooting starts     {secs2hhmmss(start_time_s)}")
            print(f"  Shooting ends       {secs2hhmmss(end_time_s)}")
            print(f"  Shooting starts in  {secs2hhmmss(time_left_s)}")

    print(f"  Shooting period     {secs2hhmmss(shoot_time_s)}")
    print(f"  Shooting every {interval_s} seconds")
    
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
    print(line,"\n")




def display_info(pic_Mb, disk_Mb, max_pics, frames, start_time_s, end_time_s, now_s, time_left_s, shoot_time_s, fps):
    
    """ Prints the main information to the display.
    """
    disp.set_backlight(1)
    disp.show_on_disp2r('RESOLUTION', str(camera_w)+'x'+str(camera_h), fs1=27, y2=75, fs2=30)
    sleep(2)
    if hdr:
        disp.show_on_disp2r('HDR', 'ACTIVATED', fs1=27, y2=75, fs2=30)    
    else:
        disp.show_on_disp2r('HDR NOT', 'ACTIVATED', fs1=27, y2=75, fs2=30)
    sleep(2)
    disp.show_on_disp2r('PICTURE AS', str(pic_format), fs1=27, y2=75, fs2=30)
    sleep(2)
    disp.show_on_disp2r('SIZE (Mb)', str(pic_Mb), fs1=27, y2=75, fs2=30)
    sleep(2)
    disp.show_on_disp2r('DISK SPACE (Mb)', str(disk_Mb), fs1=21, y2=75, fs2=26)
    sleep(2)
    disp.show_on_disp2r('MAX PICS (#)', str(max_pics), fs1=25, y2=75, fs2=30)
    sleep(2)
    if max_pics < frames:
        disp.show_on_disp2r('LIMITED TO (#)', str(frames), fs1=21, y2=75, fs2=30)
        sleep(2)
    else:
        disp.show_on_disp2r('# OF SHOOTS', str(frames), fs1=24, y2=75, fs2=30)
        sleep(2)
    
    if start_now:
        disp.show_on_disp2r('SHOOTING', 'NOW', fs1=26, y2=75, fs2=30)
        sleep(2)
    else:
        if start_time_s > now_s :
            disp.show_on_disp2r('SHOOTING IN', secs2hhmmss(time_left_s), fs1=23, y2=75, fs2=22)
            sleep(2)
            disp.show_on_disp2r('STARTS ON', secs2hhmmss(start_time_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
            sleep(3)        
            disp.show_on_disp2r('ENDS ON', secs2hhmmss(end_time_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
            sleep(3)
    
    if rendering:
        disp.show_on_disp2r('RENDER', 'ACTIVE', fs1=25, y2=75, fs2=24)
    else:
        disp.show_on_disp2r('RENDER', 'NOT ACTIVE', fs1=25, y2=75, fs2=24)
    
    disp.set_backlight(0)




def secs2hhmmss(secs):
    return str(timedelta(seconds=secs))




def display_time_left(time_left_s):
    """ Shows the left time to shooting, and turns the display backlight off.
        The display backlight is set off longer for longer left time. 
    """
    # feedback is printed to display
    disp.show_on_disp2r('SHOOTING IN', secs2hhmmss(time_left_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
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




def shoot(folder, fname, frame, pic_format):
    """ Takes a picture, and saves it in folder with proper file name (prefix + incremental).
    """
    pic_name = '{}_{:05}.{}'.format(fname, frame, pic_format)  # file name construction for the picture
    picture = os.path.join(folder, pic_name)                   # path and file name for the picture
    sleep(0.5)                                                 # sleep time
    picam2.capture_file(picture)                               # camera takes and save a picture




def video_render(folder, fps, overlay_fps):
    """ Renders all pictures in folder to a movie.
        Saves the movie in folder with proper file datetime file name.
        When the setting constrains the movie to a fix time, the fps are adapted.
    """
    
    render_start = time()         # initial time as reference
    print(f"\nVideo rendering started\n") # feedback is printed to the terminal
    if display:                   # case display is set true
        disp.show_on_disp2r('RENDERING', '', y1= 50, fs1=26) # feedback is printed to display
    
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
        print(f"Timelapse successfully rendered, in {render_time}")          # positive feedback is printed to the terminal
        print(f"Timelase saved as {movie_fname}")                            # movie path/filename is printed to the terminal
        if display:                                                          # case display is set true
            disp.show_on_disp2r('RENDERING', 'DONE', fs1=26, y2=75, fs2=30)  # positive feedback is printed to display
    else:                                                                    # case the ffmpeg does not returns 0
        print("Timelapse edit error\n")                                      # negative feedback is printed to the terminal
        if display:                                                          # case display is set true
            disp.show_on_disp2r('RENDERING', 'ERROR', fs1=26, y2=75, fs2=28) # negative feedback is printed to display




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




def exit_func():
    """ Exit function, taking care to properly close things.
    """
    try:                            # tentative
        picam2.stop()               # camera is finally acivated
    except:                         # exception
        print("failing to close the Picamera") # feedback is printed to the terminal
    
    try:                            # tentative
        GPIO.output(22,0)           # set low the GPIO22 (used as for Mini Pi TFT Backlight)
    except:                         # exception
        print("failing to set low the GPIO pin 22") # feedback is printed to the terminal
    



def main():
    """ Main fuction, that essentially 
    """
    global picam2, camera_started
    
    setup()                                    # retrieves settings, and initializes things
    pic_test_fname = os.path.join(folder, 'picture_test.'+pic_format)   # name for the test picture
    ret, pic_size_bytes, pic_Mb = test_camera(pic_test_fname)           # test picture is made, measured, removed
    
    try:                                       # tentative
        start_time = datetime.strptime(str(start_hhmm),'%H:%M')  # start_hhmm string is parsed to datetime
        start_time_s = 3600*start_time.hour + 60*start_time.minute # start_time is converted to seconds (since 00:00)
        end_time = datetime.strptime(str(end_hhmm),'%H:%M')      # end_hhmm string is parsed to datetime
        end_time_s = 3600*end_time.hour + 60*end_time.minute       # end_time is converted to seconds (since 00:00)
    except:                                    # exception
        sys.exit(print("variable 'start_hhmm' or 'end_hhmm' do not reppresent a valid time")) # feedback is printed to terminal
            
    if end_time_s < start_time_s:   # case end_time is smaller (advance) than start_time, the end_time in on the next day
        shoot_time_s =  end_time_s + 86400 - start_time_s  # shooting time is calculated
    else:                           # case end_time is bigger (later) than start_time, the end_time in on the same day
        shoot_time_s = end_time_s - start_time_s   # shooting time is calculated
    
    frames = int(shoot_time_s/interval_s)      # frames (= pictures) quantity is calculated
    fps = round(frames/movie_time_s) if fix_movie_t else fps  # in case fix_movie_t is set true (forced movie time) the fps is calculated
    fps = 1 if fps < 1 else fps                # preventing fps == 0
    if erase_pics:                             # case erase_pics is set true (settings)
        make_space(folder)                     # emptying the folder from old pictures
    
    for day in range(days):                    # iteration over the days (settings)
        
        if rendering:                          # if rendering makes space every day 
            make_space(folder)                 # emptying the folder from old pictures
        disk_Mb = disk_space()                 # disk free space
        max_pics = int(disk_Mb/pic_Mb)         # rough amount of allowed pictures quantity in disk    
        now_s, time_left_s = time_update(start_time_s)   # current time, and time left to shooting start, is retrieved
        
        # startup feedback prints to the terminal
        printout(pic_Mb, disk_Mb, max_pics, frames, start_time_s, end_time_s, now_s, time_left_s, shoot_time_s, fps, overlay_fps)
        
        # startup feedback prints to the display
        if display:
            display_info(pic_Mb, disk_Mb, max_pics, frames, start_time_s, end_time_s, now_s, time_left_s, shoot_time_s, fps)

        frame = 0                                  # incremental index appended after pictures prefix
        now_s, time_left_s = time_update(start_time_s) # current time, and time left to shooting start, is retrieved again

        if not start_now:                          # case start_now is set false (delayed start)
            if time_left_s > 1:                    # case the time left for shooting is bigger than one second
                while time_left_s >= 1:            # while time left for shooting is bigger than one second
                    now_s, time_left_s = time_update(start_time_s)  # current time, and time left to shooting start, is retrieved again 
                    if display:                    # case display is set true
                        display_time_left(time_left_s) # prints left lime to display, and pause
                        
        
        # from here onward time is managed as per time module
        start_time = time()                        # start reference time
        ref_time = start_time                      # reference time for the next shoot

        while True:                                # infinite loop
            if time() >= ref_time:                 # case time has reached the shooting moment
                shoot(folder, pic_name, frame, pic_format)  # calls the shooting function
                
                if frame%100==0:                   # case the frame is mutiple of 100
                    ref = strftime("%d %b %Y %H:%M:%S", localtime())  # current local time passed as string
                    print('\n', ref, '\t', "frame:", '{:05d}'.format(frame), end = ' ', flush=True) # current time and frame feedback to terminal
                else:                              # case the frame is not mutiple of 100
                    print('*',end ='', flush=True) # a dot character is added to the terminal to show progress
            
                if display:                        # case display is set true
    #                 disp.set_backlight(0)        # display backlight is set off
                    disp.show_on_disp2r('SHOOT', '{:05}'.format(frame), fs1=32, y2=75, fs2=34)  # feedback is printed to display
                    disp.set_backlight(1)          # display backlight is set on
                
                frame+=1                           # frame variable is incremented by one
                ref_time = start_time + frame * interval_s  # reference time for the next shoot is assigned
                
                if frame >= frames:                # caase current frame equals the set frames quantity
                    print()                        # print empty line
                    
                    # last frame takes got its own print to terminal, to make visible the frames quantity
                    print('',strftime("%d %b %Y %H:%M:%S", localtime()), '\t', "frame:", '{:05}'.format(frame), " is the last frame")
                    print("\nShooting completed")  # feedback is printed to terminal
                    break                          # while loop is interrupted
            
            sleep(0.5)                 # sleep time in between time checks

        try:                           # attempt
            if not preview:
                picam2.close()         # picamera object is closed
                camera_started = False
        except:                        # exception
            pass                       # do nothing
        
    #     picam2.stop_preview(QTGL) #Preview.QTGL)
        
        if rendering:                  # case rendering is set true
            video_render(folder, fps, overlay_fps)  # video_render function is called
        
        print("CPU temp:", cpu_temp()) # cpu temperature is printed to terminal
        
        if days>0:
            print('\n\n\n')
    
    
    exit_func()                    # exit function is called






if __name__ == "__main__":
    main()



