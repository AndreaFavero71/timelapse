#!/usr/bin/python
# coding: utf-8

"""
#############################################################################################################
#  Andrea Favero 02 July 2023,
#  Timelapse movie assembler
#############################################################################################################
"""


#imports
from os import system
from time import time, sleep, localtime, strftime
from datetime import datetime, timedelta
import os.path, sys

# settings
camera_w = 1920
camera_h = 1080
folder = 'timelapse_pics'
folder = os.path.join('/home/pi/shared', folder) # folder will be appended to the pi Video folder
pic_format = 'jpg'
fps = 24
movie_time_s = 10
movie_forced_to_fix_time = True
add_text = True


if movie_forced_to_fix_time:
    print('\nvideo render forced to:', movie_time_s, 'seconds')
    frames = 0
    for file in os.listdir(folder):
        if file.endswith('.jpg'):
            frames+=1
    fps = int(round(frames/movie_time_s))
    print('video rendering at:', fps)

else:
    print('\nvideo rendering at:', fps)


def video_render(folder, fps):
    """ Renders all pictures in folder to a movie.
        Saves the movie in folder with proper file datetime file name.
        When the setting constarins the movie to a fix time, the fps are adapted.
    """
    render_start = time()
    print(f"\nVideo rendering started\n")
    
    render_warnings = False   # flag to printout the rendering ffmpeg error 
    render_progress = False   # flag to printout the rendering progress (statistics)
    loglevel = '' if render_warnings else '-loglevel error'
    stats = '' if render_progress else '-nostats'
    
    pic_files = os.path.join(folder, '*.' + pic_format)
    out_file = os.path.join(folder, strftime("%Y%m%d_%H%M%S", localtime())+'.mp4')
    size = str(camera_w)+'x'+str(camera_h)
    
    text_addition = True
    if text_addition:
        text = 'EXPERIMENT WITH TEXT'
        text = f"{fps}X"
        font = '/usr/share/fonts/truetype/freefont/dejavu/DejaVuSans.ttf'
        fcol = 'white'                   # font color
        fsize = '48'                     # font size
        bcol = 'black@0.5'               # box color with % of transparency
        pad = str(round(int(fsize)/5))   # 20% of the font size
        pos_x = '70'                    # reference from the left
        pos_y = str(camera_h - 70)       # reference from the bottom
        v_f = (f"drawtext=fontfile={font}:text={text}:fontcolor={fcol}:fontsize={fsize}:box=1:boxcolor={bcol}:boxborderw={pad}:x={pos_x}:y={pos_y}")
#         print(v_f)
        render_command = f"ffmpeg {stats} {loglevel} -f image2 -framerate {fps} -pattern_type glob -i '{pic_files}' -s '{size}'  -vf '{v_f}' '{out_file}' -y"
    else:
        render_command = f"ffmpeg {stats} {loglevel} -f image2 -framerate {fps} -pattern_type glob -i '{pic_files}' -s '{size}' {out_file} -y"
    
    ret = system(render_command)

    if ret==0:
        render_time = timedelta(seconds=round(time() - render_start))
        print(f"Timelapse successfully rendered, in {render_time}")
        print(f"Timelase saved as {out_file} \n\n")
    else:
        print("Timelapse edit error\n")


video_render(folder, fps)