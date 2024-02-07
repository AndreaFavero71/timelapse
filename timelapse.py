#!/usr/bin/python
# coding: utf-8

"""
#############################################################################################################
#  Andrea Favero 26 November 2023,
#  Timelapse module, based on Raspberry Pi 4b and PiCamera V3 (wide)
#############################################################################################################
"""


# __version__ variable
version = '0.2 (26 Nov 2023)'


################  setting argparser for parameter parsing  ######################################
import argparse

# argument parser object creation
parser = argparse.ArgumentParser(description='CLI arguments for timelapse.py')

# --version argument is added to the parser
parser.add_argument("-v", "--version", help='Shows the script version.', action='version',
                    version=f'%(prog)s ver:{version}')

# --debug argument is added to the parser
parser.add_argument("-d", "--debug", action='store_true',
                    help="Activates printout of settings, variables and info for debug purpose")

# --parent argument is added to the parser
parser.add_argument("--parent", type=str, 
                    help="Input the parent folder name (where to append pictures' folders)")

# --folder argument is added to the parser
parser.add_argument("--folder", type=str, 
                    help="Input the folder name where pictures are saved")

# --render argument is added to the parser
parser.add_argument("--render", action='store_true', 
                    help="Force the video rendering on Rpi Zero and Zero2")

# --skip_intro argument is added to the parser
parser.add_argument("--skip_intro", action='store_true', 
                    help="Does not show introction info on display")

# --fps argument is added to the parser
parser.add_argument("--fps", type=int, 
                    help="Input the video fps (video lenght adapts to this)")

# --time argument is added to the parser
parser.add_argument("--time", type=int, 
                    help="Input video length time in secs (fps adapt to this)")

# --text argument is added to the parser
parser.add_argument("--text", type=str, 
                    help="Input the text to overlay on video. If 'fps' the used value is overlaid")

args = parser.parse_args()   # argument parsed assignement
# ###############################################################################################


# livraries import
from picamera2 import Picamera2, Preview
from libcamera import controls
from os import system
from time import time, sleep, localtime, strftime
from datetime import datetime, timedelta
import os.path, pathlib, stat, sys, json
import RPi.GPIO as GPIO



def to_bool(value):
    """ Converts argument to boolean. Raises exception for invalid formats
        Possible True  values: 1, True, true, "1", "True", "yes", "y", "t"
        Possible False values: 0, False, false, None, [], {}, "", "0", "False", "no", "n", "f", 0.0, ...
    """

    if str(value).lower() in ("yes", "y", "true",  "t", "1"): # case lowercase value string is in the tuple elements
        return True                                   # True is returned
    elif str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): # case lowercase value string is in the tuple elements
        return False                                  # False is returned
    print("Issue with settings value:", value)      # case if and elif aren't sattisfied
    raise Exception                                   # exception is raised





def check_rpi_zero():
    """ Check if Rpi is ZeroW or Zero2W.
        Some program parts are non executed (i.e. ffmpeg commands) in this case.
    """
    
    import os                                         # os is imported to check the machine
    
    rpi_zero = False                                  # flag for a Zero or Zero2
    try:                                              # tentative approach
        processor = os.uname().machine                # processor is inquired
        print(f'Processor architecture: {processor}')  # print to terminal the processor architecture
        if 'armv6' in processor or 'armv7l' in processor:  # case the string armv6 or armv7l are contained in processor string
            rpi_zero = True                           # flag for program running on Rpi ZeroW
            print('Program adapted for armv6 and armv7l')  # feedback is printed to the terminal
    except:                                           # case an exception is raised
        print("Cannot detect the Raspberry Pi model")
        error = 1                                     # error is set to 1
        exit_func(error)                              # exit function is caleld
    return rpi_zero

    



def check_screen_presence():
    """ Checks if a display is connected, eventually via VNC; This is not the (SPI) display at Raspberry Pi."""
    
    import os                                         # os library is imported
    
    if 'DISPLAY' in os.environ:                       # case the environment variable DISPLAY is set to 1 (there is a display)
        if debug:                                     # case debug variable is set True (on __main__ or via argument)
            print('Display function is availbale')  # feedback is printed to the terminal
        return True                                   # function returns True, meaning there is a screen connected
    else:                                             # case the environment variable DISPLAY is set to 0 (there is NOT a display)
        if debug:                                     # case debug variable is set True (on __main__ or via argument)
            print('Display function is not availbale') # feedback is printed to the terminal
        return False                                  # function returns False, meaning there is NOT a screen connected



def setup():
    """ Reads settings from the settings.txt file and add them in a dictionary.
        Sets the camera, and the display
    """

    variables={}                                      # empty dictionary to store the local variable
    
    screen = check_screen_presence()                  # screen presence is checked (also VNC is accounted)
    rpi_zero = check_rpi_zero()                       # raspberry pi Zero and Zero2 processor check
    
    error = 0                                         # error cose is set to zero (no errors)
    folder = pathlib.Path().resolve()                 # active folder   
    fname = os.path.join(folder,'settings.txt')       # folder and file name for the settings
    if os.path.exists(fname):                         # case the settings file exists
        with open(fname, "r") as f:                   # settings file is opened in reading mode
            settings = json.load(f)                   # json file is parsed to a local dict variable
        
        if debug:                                     # case debug is set True
            print('\n\nSettings.txt content:')      # Introducing the next print to terminal
            print(settings)                           # print the settings
            print('\n\n')                             # print empty lines
        
        try:                                          # tentative approach
            preview = to_bool(settings['preview'])    # flag to show the camera preview to screen (anso VNC)
            erase_pics = to_bool(settings['erase_pics']) # flag to erase old pictures from folder
            erase_movies = to_bool(settings['erase_movies']) # flag to erase old movies from folder
            local_control = to_bool(settings['local_control']) # flag to enable setting changes via UI at Raspberry Pi
            start_now = to_bool(settings['start_now'])  # flag to force shoting immediatly or at set datetime
            period_hhmm = str(settings['period_hhmm'])  # shooting period in hhmm when start_now
            start_hhmm = str(settings['start_hhmm'])  # hh:mm of shooting start time
            end_hhmm = str(settings['end_hhmm'])      # hh:mm of shooting end time
            interval_s = int(settings['interval_s'])  # pictures cadence in seconds (smallest is ca 2 seconds for jpeg and 5 for png)
            days = int(settings['days'])              # how many days the timelapse is made
            rendering = to_bool(settings['rendering'])  # flag for automatic video rendering in Raspberry Pi
            fix_movie_t = to_bool(settings['fix_movie_t'])  # flag for automatic video rendering in Raspberry Pi
            movie_time_s = int(settings['movie_time_s']) # movie duration time
            fps = int(settings['fps'])                # default fps at video generation (when not forced to a fix video time)
            overlay_fps = to_bool(settings['overlay_fps'])  # flag for overlaying the used fps at movie rendering
            camera_w = int(settings['camera_w'])      # camera width in pixels
            camera_h = int(settings['camera_h'])      # camera height in pixels
            hdr = to_bool(settings['hdr'])            # flag for hdr (High Dinamy Range) camera setting
            autofocus = to_bool(settings['autofocus'])   # flag to enable/disable autofocus
            focus_dist_m = float(settings['focus_dist_m'])  # distance in meter for manual focus
            date_folder = to_bool(settings['date_folder'])  # flag to force folder name of current yyyymmdd instead folder name
            folder = str(settings['folder'])          # folder name to store the pictures
            pic_name = str(settings['pic_name'])      # picture prefix name
            pic_format = str(settings['pic_format'])  # picture format
            display = to_bool(settings['display'])    # flag for display usage
            
            
            ##############################################################################
            # additions made after project published at Instructables
            if settings.get('modified_disp') == None: # case modified_disp is not a key in settings.txt 
                instructions_info('modified_disp')    # instructions_info function is called
            else:                                     # case disp_preview is a key in settings.txt
                modified_disp = to_bool(settings['modified_disp'])  # flag to modified display for PWM
            
            if settings.get('disp_bright') == None:   # case disp_bright is not a key in settings.txt 
                instructions_info('disp_bright')      # instructions_info function is called
            else:                                     # case disp_bright is a key in settings.txt
                disp_bright = int(settings['disp_bright'])  # display brightness (allowed 0 to 100)
                disp_bright == 10 if disp_bright < 0 else disp_bright   # display brightness min value set to 10
                disp_bright == 100 if disp_bright > 100 else disp_bright # display brightness max value set to 100
            
            if settings.get('disp_preview') == None:  # case disp_preview is not a key in settings.txt 
                instructions_info('disp_preview')     # instructions_info function is called
            else:                                     # case disp_preview is a key in settings.txt
                disp_preview = to_bool(settings['disp_preview'])  # flag to display preview on the display
            
            if settings.get('disp_image') == None:    # case disp_image is not a key in settings.txt 
                instructions_info('disp_image')       # instructions_info function is called
            else:                                     # case disp_image is a key in settings.txt
                disp_image = to_bool(settings['disp_image'])  # flag to display image on the display
                
            if settings.get('rotate_180') == None:    # case rotate_180 is not a key in settings.txt 
                instructions_info('rotate_180')       # instructions_info function is called
            else:                                     # case rotate_180 is a key in settings.txt
                rotate_180 = to_bool(settings['rotate_180'])  # flag to rotate image of 180deg before saving it
            
            if settings.get('overlay_text') == None:  # case overlay_text is not a key in settings.txt 
                instructions_info('overlay_text')     # instructions_info function is called
            else:                                     # case overlay_text is a key in settings.txt
                overlay_text = str(settings['overlay_text'])  # overlay_text to overlay on video editing
                
            if settings.get('parent_folder') == None: # case parent_folder is not a key in settings.txt 
                instructions_info('parent_folder')    # instructions_info function is called
            else:                                     # case parent_folder is a key in settings.txt
                parent_folder = str(settings['parent_folder'])  # parent_folder name to append folders
            # ############################################################################

            
        except:                                       # case of exceptions
            print('Error: Missed parameter at imported parameters') # feedback is printed to the terminal
            print('or bad parameter format resulting in convertion error to bool or int') # feedback is printed to the terminal
            error = 1                                 # error variable is set to 1
            return error                              # error code is returned
   
    else:                                             # case the settings file does not exists, or name differs
        print('Could not find the file: ', fname)   # feedback is printed to the terminal
        error = 1                                     # error variable is set to 1
        return error                                  # error code is returned


    # evaluating and modifying settings due to HW reality
    if preview and not screen:                        # case the preview is set True and screen is not detected
        preview = False                               # preview is changed to False to prevent errors
        print("Preview setting changed to False as not detected any screen")  # feedback is printed to terminal

    # evaluating and modifying settings due to HW reality
    if rpi_zero:                                      # case the used board is Rpi Zero or Zero2
        rendering = False                             # rendering is changed to False
        print("Rendering setting changed to False as Rpi Zero or Zero2")  # feedback is printed to terminal

    # evaluating the settings priority
    if local_control:                                 # case the local_control is set Ture
        if not start_now:                             # case start_sow is set False
            start_now = True                          # start_now is changed to True
            print("Start_now changed to True as local_control is set True")  # feedback is printed to terminal
        if days > 1:                                  # case the set days are > 1
            days = 1                                  # days is set to one
    if start_now:                                     # case start_sow is set True
        days = 1                                      # only a single period (day) is considered
    
    GPIO, upper_btn, lower_btn, disp = set_gpio(display)  # calls the function to set gpio
    
    # calls to the function to set the camera
    picam2, camera_started, error = set_camera(camera_w, camera_h, rotate_180, hdr, autofocus, focus_dist_m, preview)  
    if error!=0:                                      # case camera setting raises errors
        return variables, error                       # error is returned
    
    # variables are added to the variables dictionary (key is the string of the variable name)
    variables['rpi_zero'] = rpi_zero
    variables['picam2'] = picam2
    variables['camera_started'] = camera_started
    variables['GPIO'] = GPIO
    
    variables['upper_btn'] = upper_btn
    variables['lower_btn'] = lower_btn
    variables['disp'] = disp
    
    variables['preview'] = preview
    variables['erase_pics'] = erase_pics
    variables['erase_movies'] = erase_movies
    
    variables['local_control'] =local_control
    variables['start_now'] = start_now
    variables['period_hhmm'] = period_hhmm
    variables['start_hhmm'] = start_hhmm
    variables['end_hhmm'] =end_hhmm
    variables['interval_s'] = interval_s
    variables['days'] = days
    
    variables['rendering'] = rendering
    variables['fix_movie_t'] = fix_movie_t
    variables['movie_time_s'] = movie_time_s
    variables['fps'] = fps
    variables['overlay_fps'] = overlay_fps
    variables['overlay_text'] = overlay_text
    
    variables['camera_w'] = camera_w
    variables['camera_h'] = camera_h
    variables['hdr'] = hdr
    variables['autofocus'] = autofocus
    variables['focus_dist_m'] = focus_dist_m
    variables['date_folder'] = date_folder
    variables['folder'] = folder
    variables['parent_folder'] = parent_folder
    variables['pic_name'] = pic_name
    variables['pic_format'] = pic_format
    variables['rotate_180'] = rotate_180
    
    variables['display'] = display
    variables['modified_disp'] = modified_disp
    variables['disp_preview'] = disp_preview
    variables['disp_image'] = disp_image
    variables['disp_bright'] = disp_bright
    
    return variables, error                           # error code is returned

   



def set_camera(camera_w, camera_h, rotate_180, hdr, autofocus, focus_dist_m, preview):
    
    print()                                           # an empry line is printed to terminal
    camera_started = False                            # camera_started variable is set False
    error = 0                                         # error variable is set to 0 (no errors)
    picam2 = Picamera2()                              # camera object
    
    
    if rotate_180:                                    # case rotate_180 variable is set True
        from libcamera import Transform               # library 
        camera_conf = picam2.create_preview_configuration(main={"size": (camera_w, camera_h)},
                                                          lores={"size": (640, 360)},
                                                          display="lores",
                                                          transform=Transform(180)) # camera settings
    
    else:                                             # case rotate_180 variable is set False
        camera_conf = picam2.create_preview_configuration(main={"size": (camera_w, camera_h)},
                                                      lores={"size": (640, 360)}, display="lores") # camera settings
        
    picam2.configure(camera_conf)                     # applying settings to the camera
    
    if hdr:                                           # case hdr is set True
        ret = os.system(f"v4l2-ctl --set-ctrl wide_dynamic_range=1 -d /dev/v4l-subdev0") # hdr on
    else:                                             # case hdr is set False
        ret = os.system(f"v4l2-ctl --set-ctrl wide_dynamic_range=0 -d /dev/v4l-subdev0") # hdr off
    if ret != 0:                                      # case setting the hdr does not return zero
        print("  HDR setting returned an error")      # feedback is printed to the terminal
        error = 0.5                                   # error variable is set to 1
        return error                                  # error code is returned
    else:                                             # case setting the hdr returns zero
        sleep(0.5)                                    # little sleep time    
    
    if autofocus:                                     # case autofocus is set True
        picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})  # Autofocus Auto requires a trigger to execute the focus
    else:                                             # case autofocus is set False
        focus_dist = 1/focus_dist_m if focus_dist_m > 0 else 10    #preventing zero division; 0.1 meter is the min focus dist (1/0.1=10)
        picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus_dist}) # manual focus; 0.0 is infinite (1/>>), 2 is 50cm (1/0.5)
    
    if preview:                                       # case the previes is set True
        picam2.start_preview(Preview.QTGL)            # preview related function is activated
    else:                                             # case the previes is set False
        picam2.start_preview(Preview.NULL)            # preview related function is set Null
    
    sleep(1)                                          # little sleep time
    picam2.start()                                    # camera is finally acivated
    camera_started = True                             # flag to track the camera status
    
    return picam2, camera_started, error              # camera object, camera_started and error code are returned





def set_gpio(display):
    """ Sets the GPIOs and eventually the display.
    """
    
    GPIO.setwarnings(False)                           # GPIO warning set to False to reduce effort on handling them
    GPIO.setmode(GPIO.BCM)                            # GPIO module setting  
    
    if display:                                       # case display (presence) is set True 
        from timelapse_display import display as disp   # display Class is imported
        upper_btn = 23                                # GPIO pin used by the upper button
        lower_btn = 24                                # GPIO pin used by the lower button
        GPIO.setup(upper_btn, GPIO.IN)                # set the upper_btn as an input
        GPIO.setup(lower_btn, GPIO.IN)                # set the lower_button_pin as an input
        disp.clean_display()                          # cleans the display from eventual older images
    else:                                             # case display (presence) is set False
        upper_btn = lower_btn = disp = None           # variables set to None
    
    return GPIO, upper_btn, lower_btn, disp           # fuction returns 




def instructions_info(parameter):
    """ Prints some info on the terminal.
    """
    print('\n\n')
    print("#######################################################################################")
    print("#######################################################################################")
    print(f"File settings.txt has been updated with a new parameter: ", parameter)
    print("Check the instructions for this parameter")
    print("https://www.instructables.com/Timelapse-With-Raspberry-Pi-4b-and-PiCamera-V3-wid/")
    print("Note: This meessage will appear for all the new parameters missed in your settings.txt ")
    print("#######################################################################################")
    print("#######################################################################################")
    print('\n\n')
    sys.exit(1)                                       # script is quitted with defined error value





def start_camera(picam2, preview):
    """ Starts the camera and the preview stream.
    """    
    camera_started = True                             # camera_started is set True
    try:                                              # tentative approach
        if preview:                                   # case preview is set True             
            picam2.start_preview(Preview.QTGL)        # re-starting the camera preview
        picam2.start()                                # re-starting the camera
    except:                                           # case of exceptions
        camera_started = False                        # camera_started is set False
    return camera_started
                




def set_display_backlight(modified_disp, disp_bright):
    """ Sets the display backlight. When the display is modified (simple wire) PWM is applied.
    """
    if modified_disp:                                 # case modified_disp is set True (display modified)
        try:                                          # tentative approach
            disp.dimm_backlight(disp_bright)          # display backlight via PWM
        except:                                       # case of exceptions
            pass                                      # do nothing
    else:                                             # case modified_disp is set False (display not modified)
        if disp_bright == 100:                        # case brightness (disp_bright) is set to 100
            disp.set_backlight(1)                     # backlight is set ON on its intended GPIO pin
        elif disp_bright == 0:                        # case brightness (disp_bright) is set to 0
            disp.set_backlight(0)                     # backlight is set OFF (in reality a pullup keeps it ON)
        
            



def make_space(parent_folder):
    """ Removes all the pictures files from the parent_folder and sub-directories. 
        Empties the Trash bin from pictures and movies.
    """
    error = 0                                         # error is set to zero (no errors)
    folders = [x[0] for x in os.walk(parent_folder)]  # list folders in parent_folder
    f_types = ['jpg', 'png']                          # file types to delete from folder
    
    if erase_movies:                                  # case erase_movies is set True
        f_types.append('mp4')                         # the movie extension is added to the list of file types
    
    for directory in folders:                         # iteration over the folders
        for f_type in f_types:                        # iteration over f_types
            for file in os.listdir(directory): # iteration over files in directory
                if file.endswith(f_type):             # case file ends as per f_type
                    ret1 = system(f"sudo rm {parent_folder}/**/*.{f_type}") # delete f_type files from parent folder and sub folders
                    if ret1 != 0:                     # case the file(s) removal returns 0
                        print(f"Issue at removing old {f_type} picture from {directory}") # negative feedback printed to terminal
                        error = 1                     # error variable is set to 1
                    break                             # for loop iteration on files is interrupted
        
    if 'mp4' not in f_types:                          # case the movie type was not in the list of file types
        f_types.append('mp4')                         # file type to delete from trash bin
    
    if os.path.exists("/home/pi/.local/share/Trash/files/"):  # if case the folder does not exist
        for f_type in f_types:                        # iteration over f_types
            for file in os.listdir("/home/pi/.local/share/Trash/files/"):  # iteration over files in trash bin folder
                if file.endswith(f_type):             # case file ends as per f_type
                    ret2 = system(f"sudo rm /home/pi/.local/share/Trash/files/*.{f_type}")  # delete f_type files from folder  
                    ret3 = system(f"sudo rm /home/pi/.local/share/Trash/info/*.{f_type}.trashinfo") # delete f_type info from folder
                    if ret2 != 0:                     # case the file(s) removal returns 0
                        print(f"Issue at emptying the trash from {f_type} files")  # negative feedback printed to terminal
                        error = 1                     # error variable is set to 1
                    if ret3 != 0:                     # case the info removal returns 0
                        print(f"Issue at emptying the trash from {f_type} files info") # negative feedback printed to terminal
                        error = 1                     # error variable is set to 1
                    break                             # for loop iteration on files is interrupted
    return error




def test_camera(pic_test):
    """ Makes a first picture as test, and returns its size in Mb.
        This test picture is removed right after.
    """
    
    pic_size_bytes = 1                                # unit is assigned to pic_size_bytes variable
    pic_Mb = 1                                        # unit is assigned to pic_Mb variable 
    try:                                              # tentative approach
        if debug:
            print(f"Test camera by taking {pic_test} image")
        pic_test = pic_test.strip()
        picam2.capture_file(pic_test)                 # camera takes and save a picture
        pic_size_bytes = os.path.getsize(pic_test)    # picture size is measured in bytes
        pic_Mb = round(pic_size_bytes/1024/1024,2)    # picture size in Mb
        os.remove(pic_test)                           # test picture is removed
        error = 0                                     # error variable is set to 0
        return error, pic_size_bytes, pic_Mb          # return (when no exceptions)
    except:                                           # exception
        print('\nCamera failure')                     # feedback is printed to the terminal
        error = 1                                     # error variable is set to 1
        return error, pic_size_bytes, pic_Mb          # return (when expections)





def show_image(image, show_time):
    """ Shows image to the display.
    """ 
    image = Image.open(image)                         # image is opened
    width, height = image.size                        # image size
    w = disp.disp_w                                   # display width
    h = disp.disp_h                                   # display height
    
    if width != w or height != h:                     # case image size do not math display size         
        ratio = width/w                               # ratio of image width/display width
        new_image_h = int(camera_h/ratio)             # image height to keep proportion
        resized_image = image.resize((w, new_image_h))  # image is resized
        image_with_bg = Image.new(image.mode, (w, h), (0,0,0))   # black blackground
        image_with_bg.paste(resized_image, (0, (h - new_image_h) // 2))  # image is pasted to the background
    
    set_display_backlight(modified_disp,100)          # display backlight is set to max
    disp.display_image(image_with_bg)                 # image is displayed
    sleep(show_time)                                  # sleep for shot_time
    set_display_backlight(modified_disp,0)            # display backlight is set to min





def preview_shoot_and_show(picam2, camera_started, preview_pic, preview_show_time):
    """ Activates the camera, takes a picture and show it to display.
    """
    if camera_started == False:                       # case camera_started is set False and almost time to shoot
        camera_started = start_camera(picam2, preview=False)  # starts the camera
    ret = picam2.capture_file(preview_pic)            # camera takes and save a picture
    show_image(preview_pic, preview_show_time)        # call to the function to show the picture




def disk_space():
    """ Checks the disk space (main disk), and returns it in Mb.
    """    
    st = os.statvfs('/')                              # status info from disk file system in root
    bytes_avail = (st.f_bavail * st.f_frsize)         # disk space (free blocks available * fragment size)
    return int(bytes_avail / 1024 / 1024)             # return disk space in Mb




def time_update(start_time_s):
    """ Check current datetime: Returns the total secs from 00:00, and the left time in secs to the shooting start time.
    """
    now_s = 3600*datetime.now().hour + 60*datetime.now().minute + datetime.now().second  # datetime convert to secs 
    time_left_s = start_time_s - now_s                # time difference in secs, between the current time and shooting start time
    return now_s, time_left_s                         # return




def printout(day, days, pic_Mb, disk_Mb, max_pics, frames, start_now, local_control,
             start_time_s, end_time_s, now_s, time_left_s, shoot_time_s, fps, overlay_fps):
    
    """ Prints the main information to the terminal.
    """
       
    line = "#"*78
    print('\n'*3)
    print(line)
    print(line)    
    
    if local_control:
        print(f"Local control is enabled")
    else:
        print(f"Local control is disabled")
    
    print(f"Picture resolution: {camera_w}x{camera_h}")
    
    if autofocus:
        print(f"Camera set to autofocus")
    else:
        print(f"Camera set to manual focus at {focus_dist_m} meters")
    
    print(f"Picture HDR: {hdr}")
    print(f"Picture format: {pic_format}")
    print(f"Picture file size {str(pic_Mb)} Mb  (picture size varies on subject and light!)")
    print(f"Free disk space: {disk_Mb} Mb")
    print(f"Rough max number of pictures: {max_pics}")
    
    if days>1:
        print(f"Day {day+1} of {days}")
    
    if start_now:
        print("Shooting starts:     now")
        if not local_control:
            print(f"Shooting period:     {secs2hhmmss(shoot_time_s)}")
    else:
        print(f"Shooting starts:     {secs2hhmmss(start_time_s)}")
        print(f"Shooting ends:       {secs2hhmmss(end_time_s)}")
        if time_left_s > 0:
            print(f"Shooting starts in:  {secs2hhmmss(time_left_s)}")

    print(f"Shooting every:      {interval_s} seconds")
    
    if max_pics < frames:
        if days>1 and not rendering:
            print(f"Number of pictures limited to: {frames} a day, due to storage space")
        else:
            print(f"Number of pictures limited to about: {frames}, due to staorage space")
    else:
        if days>1:
            print(f"Camera will take:    {frames} pictures a day")
        else:
            print(f"Camera will take:    {frames} pictures")
            
    if rendering:
        print(f"Timelapse video render activated")
        if overlay_fps:
            print(f"Fps value will be overlayed on the video")
        if fix_movie_t:
            print(f"Video rendered at {fps} fps, lasting {round(frames/fps)} secs")  
    else:
        print(f"Timelapse video render not activated")
    
    if display:                                       # case display is set True
        print(f"Display at Raspberry Pi activated")
    else:
        print(f"Display at Raspberry Pi not activated")
    
    print(line)
    print(line)




def display_info(variables, pic_Mb, disk_Mb, max_pics, frames, now_s, time_left_s):
    """ Prints the main information to the display.
    """
    
    disp_time_s = 4                                   # time to let visible each display page
    
    set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
    
    if variables['disp_bright']:                      # case autofocus is set True
        disp.show_on_disp4r('BRIGHTNESS', str(variables['disp_bright']) +'%', fs1=26, y2=75, fs2=36)
        sleep(disp_time_s)                            # sleep meant as reading time
    else:                                             # case autofocus is set False
        disp.show_on_disp4r('MANUAL FOCUS', 'FOSUS: ' + str(focus_dist_m) + ' m', fs1=22, y2=75, fs2=24)
        sleep(disp_time_s)                            # sleep meant as reading time
    
    if variables['autofocus']:                        # case autofocus is set True
        disp.show_on_disp4r('AUTOFOCUS', 'ACTIVATED', fs1=26, y2=75, fs2=28)
        sleep(disp_time_s)                            # sleep meant as reading time
    else:                                             # case autofocus is set False
        disp.show_on_disp4r('MANUAL FOCUS', 'FOSUS: ' + str(focus_dist_m) + ' m', fs1=22, y2=75, fs2=24)
        sleep(disp_time_s)                            # sleep meant as reading time
    
    if variables['hdr']:                              # case hdr is set True
        disp.show_on_disp4r('HDR', 'ACTIVATED', fs1=32, y2=75, fs2=30)
        sleep(disp_time_s)                            # sleep meant as reading time
    else:                                             # case hdr is set False
        disp.show_on_disp4r('HDR NOT', 'ACTIVATED', fs1=27, y2=75, fs2=30)
        sleep(disp_time_s)                            # sleep meant as reading time
    
    disp.show_on_disp4r('RESOLUTION', str(variables['camera_w'])+'x'+str(variables['camera_h']),
                        fs1=27, y2=75, fs2=30)
    sleep(disp_time_s)                                # sleep meant as reading time
    disp.show_on_disp4r('PICTURE AS', str(variables['pic_format']), fs1=27, y2=75, fs2=30)
    sleep(disp_time_s)                                # sleep meant as reading time
    disp.show_on_disp4r('SIZE (Mb)', str(pic_Mb), fs1=27, y2=75, fs2=30)
    sleep(disp_time_s)                                # sleep meant as reading time
    disp.show_on_disp4r('DISK SPACE (Mb)', str(disk_Mb), fs1=21, y2=75, fs2=26)
    sleep(disp_time_s)                                # sleep meant as reading time
    disp.show_on_disp4r('MAX PICS (#)', str(max_pics), fs1=25, y2=75, fs2=30)
    sleep(disp_time_s)                                # sleep meant as reading time
    
    if max_pics < frames:                             # case disk has not space for all the wanted pictures
        disp.show_on_disp4r('LIMITED TO (#)', str(frames), fs1=21, y2=75, fs2=30)
        sleep(disp_time_s)                            # sleep meant as reading time
    else:                                             # case disk has space for all the wanted pictures
        if not variables['local_control']:            # caselocal_control is set False
            disp.show_on_disp4r('# OF SHOOTS', str(frames), fs1=24, y2=75, fs2=30)
            sleep(disp_time_s)                        # sleep meant as reading time
    
    disp.show_on_disp4r('SHOOT EVERY', str(variables['interval_s'])+' s', fs1=25, y2=75, fs2=30)
    sleep(disp_time_s)

    if variables['disp_preview']:                     # case disp_preview is set True
        disp.show_on_disp4r('PREVIEW', 'ON DISPLAY', fs1=30, y2=75, fs2=26)
        sleep(disp_time_s)                            # sleep meant as reading time
    else:                                             # case disp_preview is set False
        disp.show_on_disp4r('PREVIEW NOT', 'DISPLAYED', fs1=24, y2=75, fs2=26)
        sleep(disp_time_s)                            # sleep meant as reading time
        
    if variables['disp_image']:                       # case disp_image is set True
        disp.show_on_disp4r('IMAGES ARE', 'DISPLAYED', fs1=26, y2=75, fs2=26)
        sleep(disp_time_s)                            # sleep meant as reading time
    else:                                             # case disp_image is set False
        disp.show_on_disp4r('IMAGES ARE', 'NOT DISPLAYED', fs1=26, y2=75, fs2=22)
        sleep(disp_time_s)                            # sleep meant as reading time
    
    if variables['local_control']:                    # case local_control are set True
        disp.show_on_disp4r('SHOOTING', 'CONTROLLED', 'VIA BUTTONS', fs1=30, fs2=24, fs3=24)
        sleep(disp_time_s)                            # sleep meant as reading time
    else:                                             # case local_control are set False
        if variables['start_now'] :                   # case start_now is set True
            disp.show_on_disp4r('SHOOTING', 'NOW', fs1=30, y2=75, fs2=30)
            sleep(disp_time_s)                        # sleep meant as reading time     
        else:                                         # case start_now is set False 
            if start_time_s > now_s :                 # case not yet time to start shooting
                disp.show_on_disp4r('SHOOTING IN', secs2hhmmss(time_left_s), fs1=23, y2=75, fs2=22)
                sleep(disp_time_s)                    # sleep meant as reading time
                disp.show_on_disp4r('STARTS ON', secs2hhmmss(start_time_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
                sleep(disp_time_s)                    # sleep meant as reading time
                disp.show_on_disp4r('ENDS ON', secs2hhmmss(end_time_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
                sleep(disp_time_s)                    # sleep meant as reading time
    
    if variables['rendering']:                        # case rendering is set True
        disp.show_on_disp4r('RENDER', 'ACTIVE', fs1=30, y2=75, fs2=30)
        sleep(disp_time_s)                            # sleep meant as reading time
    else:                                             # case rendering is set False
        disp.show_on_disp4r('RENDER', 'NOT ACTIVE', fs1=30, y2=75, fs2=24)
        sleep(disp_time_s)                            # sleep meant as reading time
    
    set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright




def secs2hhmmss(secs):
    """ Converts a period from seconds to hhmmss. 
    """
    return str(timedelta(seconds=secs))




def display_time_left(time_left_s):
    """ Shows the left time to shooting, and turns the display backlight off.
        The display backlight is set off longer for longer left time. 
    """
    # feedback is printed to display
    disp.show_on_disp4r('SHOOTING IN', secs2hhmmss(time_left_s), fs1=25, y2=55, fs2=22, y3=85, fs3=22)
    
    set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
    
    if time_left_s > 3600 and not quitting:           # case time_left_s is more than one hour
        set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
        sleep(3)                                      # sleep when waiting for the planned shooting start
        set_display_backlight(modified_disp,0)        # display backlight is set to disp_bright
        sleep(10)                                     # sleep when waiting for the planned shooting start
    
    elif time_left_s > 60 and not quitting:           # case time_left_s is more than one minute
        set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
        sleep(2)                                      # sleep when waiting for the planned shooting start
        set_display_backlight(modified_disp,0)        # display backlight is set to disp_bright
        sleep(5)                                      # sleep when waiting for the planned shooting start
    
    elif time_left_s > 12 and not quitting:           # case time_left_s is more than 12 seconds
        set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
        sleep(1)                                      # sleep when waiting for the planned shooting start
        set_display_backlight(modified_disp,0)        # display backlight is set to disp_bright
        sleep(1)                                      # sleep when waiting for the planned shooting start
    else:                                             # case time_left_s is less than 12 seconds
        sleep(0.1)                                    # sleep when waiting for the planned shooting start




def shoot(folder, fname, frame, pic_format, focus_ready, ref_time, display, disp_image, time_for_focus):
    """ Takes a picture, and saves it in folder with proper file name (prefix + incremental).
        When autofocus, the shoot is done once the camera confirms the focus achievement.
    """
    
    if autofocus:                                     # case autofocus is set True (settings)
        t_ref = time()                                # reference time for autofocus ready from camera
        while not picam2.wait(focus_ready):           # while the autofocus is not ready yet
            sleep(0.05)                               # short sleep
            if time()-t_ref >= time_for_focus:        # case the time for autofocus has elapsed
                break                                 # while loop is interrupted
    
    while time() < ref_time:                          # while it isn't time to shoot yet
        sleep(0.05)                                   # short sleep
    
    pic_name = '{}_{:05}.{}'.format(fname, frame, pic_format)  # file name construction for the picture
    picture = os.path.join(folder, pic_name)          # path and file name for the picture
    camera_info = picam2.capture_file(picture)        # camera takes and save a picture
#     print("  Camera_info at picture taking", camera_info)  # camera info are printed to the terminal
    last_shoot_time = time()                          # current time is assigned to last_shoot_time 
    
    if display and disp_image:                        # case display_image is set True
        show_image(picture, 5)                        # image s plot on display
    
    ret = system(f"sudo chmod 777 {picture}")         # change permissions to the picture file: Read, write, and execute by all users
    if ret != 0:                                      # case the permission change return an error
        print(f"Issue at permissions changing of picture file ")  # negative feedback printed to terminal
    
    return last_shoot_time                            # time reference of last shoot is returned




def video_render(folder, pic_format, width, height, fps, overlay_text):
    """ Renders all pictures in folder to a movie.
        Saves the video in folder with proper file datetime file name.
        When the setting constrains the video to a fix time, the fps are adapted.
    """

    print(f"\n\nVideo rendering started")             # feedback is printed to the terminal
    if display:                                       # case display is set True                              
        set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
        disp.show_on_disp4r('RENDERING', 'ONGOING', fs1=30, y2=75, fs2=32) # feedback is printed to the display
        sleep(4)                                      # sleep time in between time checks
    
    render_start = time()                             # time reference for the rendering process
        
    render_warnings = False                           # flag to printout the rendering ffmpeg error 
    render_progress = False                           # flag to printout the rendering progress (statistics)
    
    loglevel = '' if render_warnings else '-loglevel error'  # loglevel parameter setting
    
    # NOTE ffmpeg stats aren't updated when the comand is send through python
    if render_progress:                               # case render_progress is set True
        stats = '-stats'                              # stats parameter is set as active
        stats_period = 20                             # time interval (secs) for the stats update
    else:                                             # case render_progress is set False
        stats = '-nostats'                            # tats parameter is set as not active
    
    pic_files = os.path.join(parent_folder, folder, '*.' + pic_format)   # imput images files
    out_file = os.path.join(parent_folder, folder, strftime("%Y%m%d_%H%M%S", localtime())+'.mp4')  # output video file
    size = str(width)+'x'+str(height)                 # frame size
    
    
    if overlay_text != '':                            # case overlay_text is not an empty string
        text = overlay_text                           # overlay_text is assigned to text (shorter name)
        font = '/usr/share/fonts/truetype/freefont/dejavu/DejaVuSans.ttf'
        fcol = 'white'                                # font color
        fsize = '48'                                  # font size
        bcol = 'black@0.5'                            # box color with % of transparency
        pad = str(round(int(fsize)/5))                # 20% of the font size
        pos_x = '70'                                  # reference from the left
        pos_y = str(height - 70)                      # reference from the bottom
        v_f = (f"drawtext=fontfile={font}:text={text}:fontcolor={fcol}:fontsize={fsize}:box=1:boxcolor={bcol}:boxborderw={pad}:x={pos_x}:y={pos_y}")
#         print(v_f)
        render_command = f"ffmpeg {stats} {loglevel} -f image2 -framerate {fps} -pattern_type glob -i '{pic_files}' -s '{size}'  -vf '{v_f}' '{out_file}' -y"
#         print(render_command)
    else:                                             # case text is an empty string
        render_command = f"ffmpeg {stats} {loglevel} -f image2 -framerate {fps} -pattern_type glob -i '{pic_files}' -s '{size}' {out_file} -y"
    
    ret = system(render_command)                      # ffmpeg command is passed to system
    
    render_time = timedelta(seconds=round(time() - render_start))  # rendering time is calculated
    
    if ret==0:                                        # case no error is returned
        print(f"Timelapse successfully rendered, in {render_time} secs")  # feednback is printed to terminal
        print(f"Timelase saved as {out_file} \n")   # reference to the vieo location is printed to terminal
        if display:                                   # case display is set True                              
            set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
            disp.show_on_disp4r('RENDERING', 'DONE', fs1=30, y2=75, fs2=36) # feedback is printed to the display
            sleep(4)                                  # sleep time in between time checks
            set_display_backlight(modified_disp,0)    # display backlight is set to min

    else:                                             # case errors are returned
        print("Timelapse render error")             # feeedback is printed to terminal
        print(f"Timelapse rerror after {render_time} secs\n")  # feednback is printed to terminal
        if display:                                   # case display is set True                              
            set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
            disp.show_on_disp4r('RENDERING', 'ERROR', fs1=30, y2=75, fs2=34) # feedback is printed to the display
            sleep(4)                                  # sleep time in between time checks
            set_display_backlight(modified_disp,0)    # display backlight is set to min





def cpu_temp():
    """ Returns the cpu temperature.
    """
    cpu_t = 0                                         # zero is assigned to cpu_t variable
    try:                                              # tentative approach
        tFile = open('/sys/class/thermal/thermal_zone0/temp')  # file with the cpu temp, in mDegCelsius (text format)
        cpu_t = round(float(tFile.read()) /1000, 1)   # tempertaure is converted to (float) degCelsius
    except:                                           # exception
        tFile.close()                                 # file is closed
    return cpu_t                                      # cpu_t is returned




def stop_or_quit(button, button_press_time):
    """Distinguishes the request to just stop a cycle or to SHUT the Rpi OFF.
    The input is the upper or lower button and related pressing time.
    When the button is pressed longer than warning_time, a warning message is displayed.
    When the button is not released within the quit_time, the Rpi SHUT-OFF."""
    
    global  quitting, button_pressed, stop_shooting
    
    error = 0                                         # error is set to zero (no errors)
    warn_time = 5                                     # delay used as threshold to print a quit warning on display
    quit_time = 10                                    # delay used as threshold to quit the script
    warning = False                                   # warning is set False, to warn user to keep or release the button
    quitting = False                                  # quitting variable is set False
    
    while not GPIO.input(button):                     # while button is pressed 
        if not warning:                               # case warning is False
            if time() - button_press_time >= warn_time:  # case time elapsed is >= warn_time reference
                set_display_backlight(modified_disp,disp_bright)    # display backlight is set to disp_bright
                disp.show_on_disp4r('STOPPED', 'SHOOTING', fs1=37, y2=75, fs2=32) # feedback is printed to the display
                stop_shooting = True                  # stop shooting is set True
                warning = True                        # warning is set True
        
        while warning:                                # case warning is True                    
            if time() - button_press_time >= (warn_time + quit_time)/2:  # case time elapsed is >= warn_time reference
                if not start_now:                     # case start_now is set (or forced) False
                    set_display_backlight(modified_disp,disp_bright)    # display backlight is set to disp_bright
                    disp.show_on_disp4r('SURE TO', 'QUIT ?', fs1=36, y2=75, fs2=42) # feedback is printed to display
                if GPIO.input(button):                # case the button is released
                    warning = False                   # warning is set False
                    button_pressed = False            # button_pressed is set False
                    if not start_now:                 # case start_now is set (or forced) False
                        set_display_backlight(modified_disp,disp_bright)    # display backlight is set to disp_bright
                        disp.show_on_disp4r('NOT', 'QUITTING', fs1=42, y2=80, fs2=36) # feedback is printed to display
                    break                             # while loop is interrupted
                
                if time() - button_press_time >= quit_time:  # case time elapsed is >= quit time reference
                    quitting = True                   # quitting variable is set True
                    break                             # while loop is interrupted
                    
        while quitting:                               # case the keep_quitting variable is True
            print('\n\nQuitting request')             # feedback is printed to display
            for i in range(5):                        # iteration for  5 times
                set_display_backlight(modified_disp,disp_bright)    # display backlight is set to disp_bright
                disp.show_on_disp4r('SHUTTING', 'OFF', fs1=32, y2=75, fs2=42) # feedback is printed to display
                sleep(1)                              # wait time to let the message visible on the display

            countdown = 3                             # count-down variable
            for i in range(countdown,-1, -1):         # iteration down the countdown variable
                set_display_backlight(modified_disp,disp_bright)    # display backlight is set to disp_bright
                dots = ''                             # dot string variable is set empty
                for k in range(min(i,3)):             # iteration over the residual cont-down, with max of three
                    dots = dots + '.'                 # dot string variable adds a dot character          
                row2_text = str(i) + dots             # string variable to be printed on the second disply row
                disp.show_on_disp4r('SHUT OFF IN', row2_text, x1=20, x2=20, y2=50, fs1=25, fs2=70)# feedback is printed to the display
                if i > 0:                             # case the cont-down is above 0
                    sleep(1)                          # wait time to let the message visible on the display
            
            set_display_backlight(modified_disp,0)    # display backlight is set to min 

            if not GPIO.input(upper_btn) or not GPIO.input(lower_btn):   # case one of the buttons is pressed
                set_display_backlight(modified_disp,disp_bright)    # display backlight is set to disp_bright
                disp.show_on_disp4r('EXITING', 'SCRIPT', fs1=36, y2=75, fs2=42)  # feedback is printed to the display
                sleep(1)                              # some little delay
                process_to_kill = "timelapse_bash.sh | grep -v grep | grep -v timelapse_terminal.log"  # string to find the process PID to kill
                nikname = "timelapse_bash.sh"         # process name
                kill_process(process_to_kill, nikname)   # call to the killing function
                sleep(1)                              # some little delay
                set_display_backlight(modified_disp,disp_bright)    # display backlight is set to disp_bright
                disp.show_on_disp4r('SCRIPT', 'ENDED', fs1=36, y2=75, fs2=42)  # feedback is printed to the display
                sleep(2)                              # some little delay
                set_display_backlight(modified_disp,0)   # display backlight is set to min 
                error = 2                             # error coe is set to 2 (quittings the script, without RPI shut off) 
            
            exit_func(error)                          # qutting function is called
        
    




def button_action(button):
    """ Function called by an interrupt to the buttons.
        Dependint on the local_control variable, it start and pause the shooting, or it calls the stop_or_quit function.
    """
    
    global paused, button_pressed, paused_time
    

    if rendering_phase:                               # case rendering_phase is True
        return                                        # this function does nothing       
    
    button_pressed = True                             # button_pressed is set True
    debounce_time = 0.1                               # delay used as threshold to accept intentional request
    
    if local_control:                                 # case local_control is True
        button_press_time = time()                    # reference time used to measure how long the button has been kept pressed
        button = upper_btn if not GPIO.input(upper_btn) else lower_btn   # button used
        
        if not GPIO.input(button):                    # case button is still pressed once the button_action function is called           
            while not GPIO.input(button):
                if time() - button_press_time >= debounce_time:   # case time elapsed is >= debounce_time reference
                    if paused:                        # case decision is set False and paused is set True
                        paused = False                # paused is set False
                        paused_time = time() - last_shoot_time  # paused_time is a time shift (in secs) from last shoot
                        set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
                        disp.show_on_disp4r('STARTED', 'SHOOTING', fs1=37, y2=75, fs2=32)  # feedback is printed to the display
                    
                    elif not paused:                  # case decision is set False and paused is set False
                        paused = True                 # paused is set True
                        set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
                        disp.show_on_disp4r('PAUSED', 'SHOOTING', fs1=37, y2=75, fs2=32) # feedback is printed to the display
                        sleep(2.5)                    # wait time to let the message visible on the display
                    
                    stop_or_quit(button, button_press_time)  # calls (keep calling) the stop_or_quit function
        
        button_pressed = False                        # button_pressed variable is set False
    
    
    elif not local_control:                           # case local_control is set False
        button_press_time = time()                    # reference time used to measure how long the button has been kept pressed
        button = upper_btn if not GPIO.input(upper_btn) else lower_btn   # button used
        if not GPIO.input(button):                    # case button is still pressed once the button_action function is called           
            while not GPIO.input(button):             # while button is pressed 
                stop_or_quit(button, button_press_time)   # calls (keep calling) the stop_or_quit function
        button_pressed = False                        # button_pressed variable is set False






def wait_until(time_for_focus, disp_preview, preview_pic, preview_show_time):
    """Function looping until the shooting start time is reached."""
    
    now_s, time_left_s = time_update(start_time_s)    # current time, and time left to shooting start, is retrieved again
    
    if disp_preview:                                  # case the disp_preview is set True
        t = time_for_focus + preview_show_time        # sum of time for camera focus and display preview is assigned to variable t
    else:                                             # case the disp_preview is set false
        t = time_for_focus                            # time for camera focus is assigned to variable t
    
    if time_left_s > t:                               # case the time left for shooting is bigger than t
        while time_left_s > t:                        # while time left for shooting is bigger than time t
            now_s, time_left_s = time_update(start_time_s)  # current time, and time left to shooting start, is retrieved again
            if display and not quitting:              # case display is set True
                display_time_left(time_left_s)        # prints left lime to display, and pause
            if disp_preview:                          # case display_preview
                preview_shoot_and_show(picam2, camera_started, preview_pic, preview_show_time) # takes and show a picture to the display
        return now_s, time_left_s                         # last time check is returned
    
    if time_left_s >= time_for_focus:                 # case the time left for shooting is bigger than time_for_focus
        now_s, time_left_s = time_update(start_time_s)  # current time, and time left to shooting start, is retrieved again
        while time_left_s > time_for_focus:           # while time left for shooting is bigger than time time_for_focus
            if display and not quitting:              # case display is set True
                display_time_left(time_left_s)        # prints left lime to display, and pause
        return now_s, time_left_s                         # last time check is returned
    
    if time_left_s < 0:                              # case the time left for shooting is smaller than zero
        # this happens after the shootings of the day are done, and current time is still on that day (waiting for the next day to come)
        while time_left_s < 0:                       # while the time left for shooting is smaller than zero
            now_s, time_left_s = time_update(start_time_s)  # current time, and time left to shooting start of the next day
            if display and not quitting:              # case display is set True
                display_time_left(time_left_s + 86400) # prints left lime to display, and pause
            if disp_preview:                          # case display_preview
                preview_shoot_and_show(picam2, camera_started, preview_pic, preview_show_time) # takes and show a picture to the display
        return now_s, time_left_s                         # last time check is returned
            
                




def kill_process(process, nikname):
    """function to kill the process in argument."""
    
    import os
    import psutil
    import subprocess
    
    p_name = "ps ax | grep -i " + process             # process name to search the PID

    for line in os.popen(p_name):                     # iterating through each instance of the process
        print(f"\nKilling process {nikname}")
        fields = line.split()                         # output from px aux
        pid = fields[0]                               # extracting Process ID from the output
        cmd = "sudo kill -9 %s" % pid                 # command to terminate the process ( -9 to kill force fully)
        result = subprocess.run(cmd, shell=True)      # executing the command to terminate the process, and collecting the output
        if result.returncode == 0:                    # case the returncode equals to zero (command executed with success)
            print(f"Process {nikname} is terminated")  # feedback is printed to the terminal
                




def display_update(day, days, frame_d, frames, interval_s, plot_percentage):
    """ Displays the last shoot taken, and daily progress.
    """
    
    if plot_percentage:                               # case the shoot percentage makes sense (predefined shoots)
        percent = 100*(frame_d)/frames                # shooting percentage is calculated (each day)
        disp.display_progress_bar(percent, day+1, days, frame_d)  # call the function that displayes the progress and shoot number
    else:                                             # case of undefined number shoots
        disp.show_on_disp4r('SHOOT', '{:05}'.format(frame_d), fs1=32, y2=75, fs2=34)  # feedback is printed to display
    set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
    




def stop_pigpiod():
    ret=pigpiod.stop_pigpio_daemon()                  # call the class to stop the pigpiod server
    if ret == 0:                                      # case zero is returned
        print("\nPigpiod stopped successfully")       # feedback is printed to terminal
    else:                                             # case not-zero is returned
        print("\nPigpiod stopping issues")            # feedback is printed to terminal
    sleep(1)                                          # little delay




def exit_func(error):
    """ Exit function, taking care to properly close things.
    """
    
    try:                                              # tentative approach
        picam2.stop()                                 # camera is finally acivated
    except:                                           # exception
        print("\nFailing to close the Picamera")      # feedback is printed to the terminal
    
    if not rendering_phase:                           # case rendering_phase is set False
        try:                                          # tentative approach
            disp.clean_display()                      # cleans the display
        except:                                       # exception
            print("Failing to clean the display")   # feedback is printed to the terminal
        
        try:                                          # tentative approach
            GPIO.output(22,0)                         # set low the GPIO22 (used as for Mini Pi TFT Backlight)
        except:                                       # exception
            print("Failing to set low the GPIO pin 22") # feedback is printed to the terminal
        
        
        if display:
            try:                                      # tentative approach
                set_display_backlight(modified_disp, 0)   # lowers the display backlight to min
            except:                                   # exception
                pass                                  # do nothing
        
        
        try:                                          # tentative approach
            stop_pigpiod()                            # pigpiod server stop request
        except:                                       # exception
            print("Failing to stop pigpiod or not activated yet") # feedback is printed to the terminal
    
    
    print()                                           # empty line is printed to terminal
    sys.exit(error)                                   # script is quitted with defined error value






if __name__ == "__main__":
    
    global paused, button_pressed, paused_time, quitting, stop_shooting
    
    print()                                    # empty line is printed
    
    # parent folder where pictures folders are appended (overwritten via settings.txt and eventually via ars)
    parent_folder = '/home/pi/shared'          
    
    rendering_phase = False                    # flag covering the rendering period, is set False
    quitting = False                           # flag covering the quitting phase, is set False
    button_pressed = False                     # button_pressed is set False
    stop_shooting = False                      # flag to stop shooting on a day when multiple days
    paused = True                              # flag to start and pause shooting when local_control is set True
    paused_time = 0                            # paused_time variable to manage the time shift due to pause
    last_shoot_time = time()                   # last_shoot_time variable to manage the recover from a pause
    frame = 0                                  # incremental index appended after pictures prefix
    
    
    
    ################    setting up    ##############################################################
    debug = False                              # flag to enable/disable the debug related prints
    if args.debug != None:                     # case 'debug' argument exists
        if args.debug:                         # case the script has been launched with 'debug' argument
            debug = True                       # flag to enable/disable the debug related prints is set True
        
    error = 0                                  # error value for the script quitting (0 means no errors)
    try:
        variables, error = setup()             # retrieves settings, and initializes things
    except:
        exit_func(error)                       # exit function is caleld
    
    rpi_zero = variables['rpi_zero']
    picam2 = variables['picam2']
    camera_started = variables['camera_started']
    GPIO = variables['GPIO']
    upper_btn = variables['upper_btn']
    lower_btn = variables['lower_btn']
    disp = variables['disp']

    preview = variables['preview']
    erase_pics = variables['erase_pics']
    erase_movies = variables['erase_movies']
    
    local_control = variables['local_control']
    start_now = variables['start_now']
    period_hhmm = variables['period_hhmm']
    start_hhmm = variables['start_hhmm']
    end_hhmm = variables['end_hhmm']
    interval_s = variables['interval_s']
    days = variables['days']
    
    rendering = variables['rendering']
    fix_movie_t = variables['fix_movie_t']
    movie_time_s = variables['movie_time_s']
    fps = variables['fps']
    overlay_fps = variables['overlay_fps']
    overlay_text = variables['overlay_text']
    
    camera_w = variables['camera_w']
    camera_h = variables['camera_h']
    hdr = variables['hdr']
    autofocus = variables['autofocus']
    focus_dist_m = variables['focus_dist_m']
    date_folder = variables['date_folder']
    folder = variables['folder']
    parent_folder = variables['parent_folder']
    pic_name = variables['pic_name']
    pic_format = variables['pic_format']
    rotate_180 = variables['rotate_180']
    
    display = variables['display']
    modified_disp = variables['modified_disp']
    disp_preview = variables['disp_preview']
    disp_image = variables['disp_image']
    disp_bright = variables['disp_bright']
    # ##############################################################################################    

    
    
    ################  retrieve the arguments that can overwrite those from settings.txt ############
    skip_intro = False                         # flag to enable/disable introduction info on display
    if args.skip_intro != None:                # case 'skip_intro' argument exists
        if args.skip_intro:                    # case the script has been launched with 'skip_intro' argument
            skip_intro = True                  # flag to enable/disable introduction info on display is set True
    
    if args.parent != None:                    # case the script has been launched with 'parent' (folder) argument
        parent_folder = args.parent            # the parent string arg is assigned to the parent_folder variable
        parent_folder = parent_folder.strip()  # parent_folder text cleaned by pre/post characters
        variables['parent_folder'] = parent_folder  # variables dict is updated
        if debug:                              # case debug is set True
            print("Parent folder for pictures's folders (set via arguments):", parent_folder)  # feedback is printed to the terminal
    
    if args.folder != None:                    # case the script has been launched with 'folder' argument
        folder = args.folder                   # the folder string arg is assigned to the folder variable
        folder = folder.strip()                # folder text cleaned by pre/post characters
        date_folder = False                    # date_folder is set False
        variables['folder'] = folder           # variables dict is updated
        if debug:                              # case debug is set True
            print("Folder for pictures (set via arguments):", folder)  # feedback is printed to the terminal

    if args.render != None:                    # case the 'render' argument exists
        if args.render:                        # case the script has been launched with 'render' argument
            rendering = True                   # flag to enable/disable video rendering is set True
            variables['render'] = render       # variables dict is updated
            if debug:                          # case debug variable is set True (on __main__ or via argument)
                print("Rendering has been forced (via argument)") # feedback is printed to the terminal
    
    if args.fps != None:                       # case the video_render.py has been launched with 'fps' argument
        fps = int(args.fps)                    # the fps integer is assigned to the fps variable
        variables['fps'] = fps                 # variables dict is updated

    if args.time != None:                      # case the video_render.py has been launched with 'time' argument
        movie_time_s = int(args.time)          # the time integer is assigned to the movie_time_s variable
        variables['movie_time_s'] = movie_time_s   # variables dict is updated
        movie_forced_to_fix_time = True        # boolean variable to force force the video render to a fix time lenght is set True
        fps = 24                               # fps is set to 24, despite the value in arg (fix time movie has priority)
                   
    if args.text != None:                      # case the video_render.py has been launched with 'text' argument
        overlay_text = args.text               # the arg text is assigned to the overlay_text variable
        overlay_text = overlay_text.strip()    # text to be overlayed
        variables['overlay_text'] = overlay_text  # variables dict is updated
    
    if debug:                                  # case debug is set True
        print('\n\nVariables, and settings (eventually altered via args):')   # Introducing the next print to terminal
        print(variables)                        # print the settings
        print('\n\n')                          # print empty lines
        
    # ############################################################################################### 
    
    

    ################  import libraries depending from the settings #################################
    if display:                                # case display is set True
        from timelapse_pigpiod import pigpiod as pigpiod # start the pigpiod server

    if disp_preview:                           # case disp_preview is set True
        from PIL import Image                  # a library for image Trasformation is imported
    # ##############################################################################################
     
     
    
    ################  interrupt on buttons  ########################################################
    if display:                                # case there is the display, and related buttons
        try:                                   # tentative approach
            GPIO.add_event_detect(upper_btn, GPIO.FALLING, callback=button_action, bouncetime=20)  # interrupt 
            GPIO.add_event_detect(lower_btn, GPIO.FALLING, callback=button_action, bouncetime=20)  # interrupt 
        except:                                # exception
            pass                               # do nothing
    # ##############################################################################################
    
    
    
    ################  folder presence check / creation  ############################################
    if date_folder:                            # case date_folder is set True
        folder = str(datetime.today().strftime('%Y%m%d'))  # folder name is retrieved as yyyymmdd
    folder = os.path.join(parent_folder, folder) # folder will be appended to the parent folder
    
    if not os.path.exists(folder):             # case the folder does not exist
        os.makedirs(folder)                    # folder is made
        ret = system(f"sudo chmod 777 {folder}")   # change permissions to the folder: Read, write, and execute by all users
        if ret != 0:                           # case the permission change return an error
            print(f"Issue at changing the folder permissions") # negative feedback printed to terminal
    
    preview_pic = os.path.join(folder,"preview.jpg")  # path and filename for the preview picture
    preview_show_time = 5
    # ###############################################################################################
    
    
    
    ################  variables depending from previous settings  ###################################
    if local_control:                          # case local_control is set True
        plot_percentage = False                # plot_percentage variable is set False
    else:                                      # case local_control is set False
        plot_percentage = True                 # plot_percentage variable is set True
    
    if autofocus:                              # case the autofocus is set True (settings)
        time_for_focus = 8                     # time for the camera to focus
    else:                                      # case the autofocus is set False (settings)
        time_for_focus = 1                     # time for the camera to focus is set to one
    
    disp_sleep_time = min(interval_s/10, 2.5)  # display sleep time is calculated based on the shooting interval (max value 2.5 secs)
    # ###############################################################################################

    
    
    ################  camera test   ################################################################
    pic_test_fname = os.path.join(parent_folder, folder, 'picture_test.'+pic_format)   # name for the test picture
    error, pic_size_bytes, pic_Mb = test_camera(pic_test_fname)         # test picture is made, measured, removed
    if error>0:                                # case of an error
        exit_func(error)                       # exit function is called
    # ###############################################################################################
    
    

    ################  erasing pictures and movies   #################################################
    if erase_pics:                             # case erase_pics is set True (settings)
        error = make_space(parent_folder)      # emptying the folder from old pictures
    if error>0:                                # case of an error
        exit_func(error)                       # exit function is called
    # ###############################################################################################
    
    
    
    ################  timing for the shoot management   ############################################
    try:                                       # tentative approach
        start_time = datetime.strptime(str(start_hhmm),'%H:%M')  # start_hhmm string is parsed to datetime
        start_time_s = 3600*start_time.hour + 60*start_time.minute # start_time is converted to seconds (since 00:00)
        end_time = datetime.strptime(str(end_hhmm),'%H:%M')   # end_hhmm string is parsed to datetime
        end_time_s = 3600*end_time.hour + 60*end_time.minute  # end_time is converted to seconds (since 00:00)
    except:                                    # exception
        sys.exit(print("Variable 'start_hhmm' or 'end_hhmm' do not reppresent a valid time")) # feedback is printed to terminal
        error = 1                              # error variable is set to 1 (True)
        if error>0:                            # case of an error
            exit_func(error)                   # exit function is called
    
    if start_now:                              # case start_now is set True
        hh, mm = period_hhmm.split(':')        # period_hhmm is split in string 'hh' and string 'mm'
        shoot_time_s = int(hh) * 3600 + int(mm) * 60 # shooting time in seconds is calculated
                                   
    else:
        if end_time_s < start_time_s:          # case end_time is smaller (advance) than start_time, the end_time in on the next day
            shoot_time_s =  end_time_s + 86400 - start_time_s  # shooting time is calculated
        else:                                  # case end_time is bigger (later) than start_time, the end_time in on the same day
            shoot_time_s = end_time_s - start_time_s   # shooting time is calculated
    # ###############################################################################################
    
    
    
        
    # from here onward time is managed in seconds from EPOC time (as per time module)
    start_time = time()                        # start reference time
    ref_time = start_time                      # time reference time for shooting
    
    
    #################################################################################################
    ########################   iterative part of the main program   #################################
    #################################################################################################

    for day in range(days):                    # iteration over the days (settings)
        
        frame_d = 0                            # 'frame of the day'. Incremental frame index per each day used for shooting time
        
        if day > 0:                            # case day after the first one
            if rendering and make_space:       # if rendering and makes space are set True
                error = make_space(parent_folder)  # emptying the folder from old pictures
        
        disk_Mb = disk_space()                 # disk free space
        max_pics = int(disk_Mb/pic_Mb)         # rough amount of allowed pictures quantity in disk
        frames = int(shoot_time_s/interval_s)  # frames (= pictures) quantity is calculated
        fps = round(frames/movie_time_s) if fix_movie_t else fps  # in case fix_movie_t is set True (forced movie time) the fps is calculated
        fps = 1 if fps < 1 else fps            # avoiding fps = 0
     
        now_s, time_left_s = time_update(start_time_s)  # current time, and time left to shooting start, is retrieved
        
        # startup feedback prints to the terminal
        printout(day, days, pic_Mb, disk_Mb, max_pics, frames, start_now, local_control,
                 start_time_s, end_time_s, now_s, time_left_s, shoot_time_s, fps, overlay_fps)
        
        if display and not skip_intro:         # case display is set True and skip_intro is set False
            # startup feedback prints to the display
            display_info(variables, pic_Mb, disk_Mb, max_pics, frames, now_s, time_left_s)
        
        if not start_now:                      # case start_now is set False (delayed start)
            # function that updates the waiting time on the display
            now_s, time_left_s = wait_until(time_for_focus, disp_preview, preview_pic, preview_show_time)
            start_time = time()                # start reference time
            ref_time = start_time              # time reference time for shooting

            
#         now_s, time_left_s = time_update(start_time_s)  # current time, and time left to shooting start, is retrieved
        start_time = time()                        # start reference time
        ref_time = start_time                      # time reference time for shooting
        
        # this is the shooting loop
        # loop ends when frames quantity is reached, or stop request (buttons, Ctrl+C, etc)
        while not stop_shooting:
            
            if local_control and paused:           # case local conrol is set True and shooting is paused             
                while paused:                      # while the shooting is paused
                    if stop_shooting:              # case stop_shooting become True (global variable)
                        break                      # break the while loop
                    paused_time = time() - last_shoot_time  #  paused time (in secs) is calculated
                    if display and not quitting and not button_pressed:  # case of display, not quitting and not buttons action
                        set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
                        disp.show_on_disp4r('PRESS TO', 'START', fs1=37, y2=75, fs2=37) # feedback is printed to the display
                        sleep(0.5)                 # little time to let visible the plot on display
                        if disp_preview:           # case display_preview
                            preview_shoot_and_show(picam2, camera_started, preview_pic, preview_show_time) # takes and show a picture to the display
            
            if camera_started == False:            # case camera_started is set False and almost time to shoot
                camera_started = start_camera(picam2, preview)  # starts the camera
            
            if time() >= ref_time-time_for_focus:  # case time has reached the shooting moment    
                if autofocus:                      # case autofocus is set True (settings)
                    focus_ready = picam2.autofocus_cycle(wait=False)   #  autofocus is triggered, and it will return True once ready (not bloccant)
                else:                              # case autofocus is set False (settings)
                    focus_ready = True             # focus_ready is always True
                
                while time() < ref_time:           # while not yet time for shooting
                    sleep(0.1)                     # little sleep
                
                if not quitting:                   # case quittining is set False
                    # calls the shooting function
                    last_shoot_time = shoot(folder, pic_name, frame, pic_format, focus_ready, ref_time, display, disp_image, time_for_focus)
                    
                    if frame_d % 50 == 0:          # case the frame is mutiple of 100
                        t_ref = strftime("%d %b %Y %H:%M:%S", localtime())  # current local time passed as string
                        print('\n' + t_ref, '\t', "frame:", '{:05d}'.format(frame_d), end = ' ', flush=True) # current time and frame feedback to terminal
                    else:                          # case the frame is not mutiple of 100
                        print('*',end ='', flush=True) # a dot character is added to the terminal to show progress
                    
                    frame+=1                       # frame variable (used for picture name) is incremented by one each shoot
                    frame_d+=1                     # frame_d variable (used for shooting timing) is incremented by one each day
                    
                    if paused_time > 0:            # case the paused_time is > 0
                        start_time += paused_time  # start time is shifted onward by the paused_time
                        paused_time = 0            # paused_time variable is reset to zero
                    
                    ref_time = start_time + frame_d * interval_s  # reference time for the next shoot is assigned  
            
            # display update after each shoot
            if display and (local_control or frame_d < frames) and not button_pressed:   # case display is set True, and still shooting
                display_update(day, days, frame_d, frames, interval_s, plot_percentage)  # display is updated
                if  2 * disp_sleep_time < ref_time - time_for_focus - time():   # case there is time to apply a pause (sleep) before next focu
                    sleep(disp_sleep_time)         # sleep time in between time checks
                    set_display_backlight(modified_disp,0)  # display backlight is set to min
                    sleep(disp_sleep_time)         # sleep time in between time checks
                    
            
            if not local_control and frame_d >= frames:  # case local_control is set False and current frame_d equals the daily set frames quantity
                print()                            # print empty line
                
                # last frame gets its own print to terminal, to make visible the frames quantity
                print(strftime("%d %b %Y %H:%M:%S", localtime()), '\t', "frame:", '{:05}'.format(frame_d-1), " is the last frame")
                print("Shooting completed")        # feedback is printed to terminal
                break                              # while loop is interrupted
        
        
        # preventing the next program part to be executed until a decision is taken
        # based on how long a button is kept pressed
        if display and button_pressed:             # case a button is pressed
            while button_pressed:                  # while the button is pressed
                sleep(0.5)                         # short sleep time
        
        if not start_now:                          # case start_now is set False
            stop_shooting = False                  # stop_shooting variable is reset to False
        
        if not stop_shooting:                      # case stop_shooting is set False (all shots done)
            if display:                            # case display is set True                              
                set_display_backlight(modified_disp,disp_bright)  # display backlight is set to disp_bright
                disp.show_on_disp4r('FINISHED', 'SHOOTING', fs1=32, y2=75, fs2=32) # feedback is printed to the display
                sleep(4)                           # sleep time in between time checks
            if preview:                            # case preview is set True
                picam2.stop_preview()              # preview stream is stopped 
#             picam2.stop()                          # picamera object is closed
            camera_started = False                 # camera_started variable is set False
        
        if rendering and not quitting:             # case rendering is set True and button isn't pressed (as per quitting intention)
            if disp_preview and not start_now:     # case disp_preview is set True
                if  os.path.exists(disp_preview):  # case the folder does not exist
                    os.remove(preview_pic)         # preview picture is removed

            rendering_phase = True                 # rendering_phase variable is set True
            video_render(folder, pic_format, camera_w, camera_h, fps, overlay_text)   # calls to function for video rendering
            rendering_phase = False                # rendering_phase variable is reset tp False
        
        print("\nCPU temp:", cpu_temp())           # cpu temperature is printed to terminal
        
        start_time += 86400                        # start_time is shifted onward by one day
        ref_time = start_time                      # reference time to call the shoot function 
    
    
    if not quitting:                               # case quitting is set False (quitting not already called)
        exit_func(error)                           # exit function is called
