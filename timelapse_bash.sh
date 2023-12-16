#!/usr/bin/bash

##########   Andrea Favero,  26 July2023  ####################################################
#  This bash script starts the Timelapse.py script, after the Pi boots.
#  When the python script is terminated wiithout errors (long buttons press), the Pi shuts down
#  (check notes below before uncommenting the "halt -p" command)
################################################################################################

# enter the folder with the main scripts
cd /home/pi/timelapse

# runs the timelapse main script
python3 timelapse.py

# exit code from the python script
exit_status=$?

# based on the exit code there are three cases to be handled
if [ "${exit_status}" -ne 0 ];
then
    if [ "${exit_status}" -eq 2 ];
    then
        echo ""
        echo "  timelapse.py exited on request"
        echo ""
    else
        echo ""
        echo "  timelapse.py exited with error"
        echo ""
    fi
	
else
    echo ""
    echo "  Successfully executed timelapse.py"
    echo ""

    # ‘halt -p’ command shuts down the Raspberry pi
    # un-comment 'halt -p' command ONLY when the script works without errors
    # un-comment 'halt -p' command ONLY after making an image of the microSD
    #halt -p

fi
