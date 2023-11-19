#!/usr/bin/python
# coding: utf-8

"""
#############################################################################################################
#  Andrea Favero 19 November 2023, Timelaps application
#
# This specific script checks the pigpiod status, and reset it once at the start
# This is a workaround, solving pigpiod issues when automatically loaded at Raspberry Pi boot (Bullseye)
#############################################################################################################
"""

from subprocess import Popen, PIPE
import time


class Pigpiod:
    
    pigpiod_once = False
    
    def __init__(self):
        
        if not self.pigpiod_once:                      # case self.pigpiod_once is set False
            ret = self.stop_pigpio_daemon()            # piogpiod service is stopped 
            time.sleep(0.2)                            # arbitrary delay 
            ret = self.start_pigpio_daemon()           # piogpiod service is started
            if ret==0 or ret==1:                       # case the pigpio daemon started correctly or was already running
                print("Activated pigpiod")           # feedback is printed to the terminal
                self.pigpiod_once = True               # pigpiod_once is set True
            else:                                      # case the pigpio daemon returns an error
                print("Cannot activate pigpiod")     # feedback is printed to the terminal
        else:
            print("Already activated pigpiod")       # feedback is printed to the terminal
            pass


    def start_pigpio_daemon(self):
        """from https://forums.raspberrypi.com/viewtopic.php?t=175448."""
        p = Popen("sudo pigpiod", stdout=PIPE, stderr=PIPE, shell=True)
        s_out = p.stdout.readline().decode()
        s_err = p.stderr.readline().decode()
    #     print("out={}\nerr={}".format(s_out, s_err))
        if s_out == '' and s_err == '':
           return 0 # started OK
        elif "pigpio.pid" in s_err:
            return 1 # already started
        else:
            return 2 # error


    def stop_pigpio_daemon(self):
        """from https://forums.raspberrypi.com/viewtopic.php?t=175448."""
        p = Popen("sudo killall pigpiod", stdout=PIPE, stderr=PIPE, shell=True)
        s_out = p.stdout.readline().decode()
        s_err = p.stderr.readline().decode()
    #     print("out={}\nerr={}".format(s_out, s_err))
        if s_out == '' and s_err == '':
            return 0 # killed OK
        else:
            return 2 # error



pigpiod = Pigpiod()



    
