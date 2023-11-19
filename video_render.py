#!/usr/bin/python
# coding: utf-8

"""
#############################################################################################################
#  Andrea Favero 19 November 2023,
#  Timelapse movie assembler
#############################################################################################################
"""


################  libraries  ####################################################################
from os import walk, system
from time import time, sleep, localtime, strftime
from datetime import datetime, timedelta
from pathlib import Path
import os.path, sys, collections
from PIL import Image
# ###############################################################################################



################  initial settings, eventually overwritten by the args  #########################
parent_folder = '/home/pi/shared'  # parent folder where pictures folders are appended
folder = 'timelapse_pics'          # arbitrary folder, under parent_folder, where pictures are saved
fps = 24                           # initial fps value.
movie_time_s = 10                  # arbitrary time to force the video render to
movie_forced_to_fix_time = False   # boolean variable to force force the video render to a fix time lenght is set False
text = ''                          # empty string is assigned to text variable
# ###############################################################################################



################  setting argparser #############################################################
import argparse

# argument parser object creation
parser = argparse.ArgumentParser(description='CLI arguments for video_render.py')

# --parent argument is added to the parser
parser.add_argument("--parent", type=str, 
                    help="Input the parent folder name")

# --folder argument is added to the parser
parser.add_argument("--folder", type=str, 
                    help="Input the folder name where pictures are saved")

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



################  retrieve arguments  ###########################################################
if args.parent_folder != None:     # case the video_render.py has been launched with 'parent_folder' argument
    parent_folder = args.parent_folder   # the parent_folder string arg is assigned to the parent_folder variable
    
if args.folder != None:            # case the video_render.py has been launched with 'folder' argument
    folder = args.folder           # the folder string arg is assigned to the folder variable

if args.fps != None:               # case the video_render.py has been launched with 'fps' argument
    fps = int(args.fps)            # the fps integer is assigned to the fps variable

if args.time != None:              # case the video_render.py has been launched with 'time' argument
    movie_time_s = int(args.time)  # the time integer is assigned to the movie_time_s variable
    movie_forced_to_fix_time = True  # boolean variable to force force the video render to a fix time lenght is set True
    fps = 24                       # fps is set to 24, despite the value in arg (fix time movie has priority)

add_text = False                   # boolean variable to overlay text is set False
if args.text != None:              # case the video_render.py has been launched with 'text' argument
    text = args.text               # the arg text is assigned to the text variable
    text = text.strip()
    add_text = True                # boolean variable to overlay text is set True
# ###############################################################################################    



################  testing if the folder exists  #################################################
folder = os.path.join(parent_folder, folder)     # folder will be appended to the parent_folder
if not os.path.exists(folder):                   # case the folder does not exist
    print("\nFolder does not exist")
    print("Change the folder name at argument --folder")
    print("or change it at video_render.py\n")
    exit()                                       # script is terminated
# ###############################################################################################    



################  check the pictures format  ####################################################
f_types = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']   # list of picture formats the picamera2 can save to
dir_path = Path(folder)                        # complete path of the folder

# get a list of all extensions from the folder
file_exts = [''.join(file_path.suffixes) for file_path in dir_path.iterdir()
             if file_path.is_file() and file_path.suffix]

ext_counts = collections.Counter(file_exts)    # count the occurrence of each extension in list

pics_dict = {}                                 # empty dict to store extesnsion and image:quantity
for ext in f_types:                            # iteration through the image extensions
    if ext in file_exts:                       # case the extension found in folder exists in images extension list
        pics_dict.update({ext:ext_counts[ext]})  # key value are added to the image:quantity dict

if len(pics_dict) == 0:                        # case the dict is empty
    print("\nNo pictures in folder")
    print("Files in folder are: ", *list(ext_counts.keys()))
    print("Change the folder name at argument --folder, or change it at video_render.py\n")
    exit()                                     # script is terminated
else:
    pic_format = max(pics_dict, key=pics_dict.get)  # file extension with higher occurence
    for root, dirs, files in os.walk(folder):  # iteration in the folder
        for filename in files:                 # iteration through the files in folder
            if filename.endswith(pic_format[1:]):  # case the file has the more recurring image extension
                break                          # loop is interrupted
    im = Image.open(os.path.join(folder, filename))  # image file info are retrieved
    width = im.width                           # image width is assigned to width variable
    height = im.height                         # image width is assigned to height variable
# ###############################################################################################



################  calculates fps when forced video time  ########################################
if movie_forced_to_fix_time:                   # case this variable is True (via settings or argument)
    fps = int(round(int(ext_counts[pic_format])/movie_time_s))  # fps is calculated
# ###############################################################################################



################  print to terminal #############################################################
print()
print("Folder:", folder)
print("Picture format:", pic_format)
print(f"Pictures in folder:", pics_dict[pic_format])

if add_text:                         # case add_text is True (via settings or argument)
    if text == 'fps':                # case text equals to 'fps'
        text = f"{fps}X"             # string of the set (or calculated) fps is used 
    print("Text overlaid to video:", text)

if movie_forced_to_fix_time:         # case this variable is True (via settings or argument)
    print('Video render forced to:', movie_time_s, 'seconds')
else:
    print('Video rendering at:', fps, 'fps')

# ###############################################################################################




def video_render(folder, pic_format, width, height, fps, text, add_text):
    """ Renders all pictures in folder to a movie.
        Saves the video in folder with proper file datetime file name.
        When the setting constrains the video to a fix time, the fps are adapted.
    """
    render_start = time()
    print(f"\n  Video rendering started\n")
    
    render_warnings = False   # flag to printout the rendering ffmpeg error 
    render_progress = False   # flag to printout the rendering progress (statistics)
    loglevel = '' if render_warnings else '-loglevel error'
    if render_progress:
        stats = '-stats'
        stats_period = 20
    else:
        stats = '-nostats'
    
    pic_files = os.path.join(folder, '*' + pic_format)
    out_file = os.path.join(folder, strftime("%Y%m%d_%H%M%S", localtime())+'.mp4')
    size = str(width)+'x'+str(height)
    
    if add_text:
        font = '/usr/share/fonts/truetype/freefont/dejavu/DejaVuSans.ttf'
        fcol = 'white'                   # font color
        fsize = '48'                     # font size
        bcol = 'black@0.5'               # box color with % of transparency
        pad = str(round(int(fsize)/5))   # 20% of the font size
        pos_x = '70'                     # reference from the left
        pos_y = str(height - 70)       # reference from the bottom
        v_f = (f"drawtext=fontfile={font}:text={text}:fontcolor={fcol}:fontsize={fsize}:box=1:boxcolor={bcol}:boxborderw={pad}:x={pos_x}:y={pos_y}")
#         print(v_f)
        render_command = f"ffmpeg {stats} {loglevel} -f image2 -framerate {fps} -pattern_type glob -i '{pic_files}' -s '{size}'  -vf '{v_f}' '{out_file}' -y"
#         print(render_command)
    else:
        render_command = f"ffmpeg {stats} {loglevel} -f image2 -framerate {fps} -pattern_type glob -i '{pic_files}' -s '{size}' {out_file} -y"
    
    ret = system(render_command)

    if ret==0:
        render_time = timedelta(seconds=round(time() - render_start))
        print(f"Timelapse successfully rendered, in {render_time}")
        print(f"Timelase saved as {out_file} \n\n")
    else:
        print("Timelapse render error\n")


video_render(folder, pic_format, width, height, fps, text, add_text)