#!/usr/bin/python
# coding: utf-8

"""
#############################################################################################################
#  Andrea Favero 01 July 2023, Timelaps application
#############################################################################################################
"""


from PIL import Image, ImageDraw, ImageFont  # classes from PIL for image manipulation
import ST7789                                # library for the TFT display with ST7789 driver 
import os.path, pathlib, json                # library for the json parameter parsing for the display


class Display:
    def __init__(self):
        """ Imports and set the display.
            (mini pi tft 240x240 colortft add on forr Rspberry Pi, ca 5€ from Aliexpress)."""
                
        folder = pathlib.Path().resolve()                             # active folder   
        fname = os.path.join(folder,'settings.txt')                   # folder and file name for the settings
#         print(fname)
        if os.path.exists(fname):                                     # case the settings file exists
            with open(fname, "r") as f:                               # settings file is opened in reading mode
                settings = json.load(f)                               # json file is parsed to a local dict variable
            try:
                disp_rotation = int(settings['disp_rotation'])        # display rotation (allowed 0, 90 180 and 270)
                disp_width = int(settings['disp_width'])              # display width, in pixels
                disp_height = int(settings['disp_height'])            # display height, in pixels
                disp_offsetL = int(settings['disp_offsetL'])          # Display offset on width, in pixels, Left if negative
                disp_offsetT = int(settings['disp_offsetT'])          # Display offset on height, in pixels, Top if negative
            except:
                print('error on converting imported parameters to int') # feedback is printed to the terminal
        else:                                                         # case the settings file does not exists, or name differs
            print('could not find the file: ', fname)                 # feedback is printed to the terminal 

        
        self.disp = ST7789.ST7789(port=0, cs=0,                       # SPI and Chip Selection                  
                            dc=25, backlight=22,                      # GPIO pins used for the SPI and backlight control
                            width=disp_width,            #(AF 240)    # see note above for width and height !!!
                            height=disp_height,          #(AF 240)    # see note above for width and height !!!                         
                            offset_left=disp_offsetL,    #(AF 0)      # see note above for offset  !!!
                            offset_top= disp_offsetT,    #(AF 0)      # see note above for offset  !!!
                            rotation=disp_rotation,                   # image orientation
                            invert=True, spi_speed_hz=10000000)       # image invertion, and SPI     
        
        self.disp.set_backlight(0)                                    # display backlight is set off
        self.disp_w = self.disp.width                                 # display width, retrieved by display setting
        self.disp_h = self.disp.height                                # display height, retrieved by display setting
        disp_img = Image.new('RGB', (self.disp_w, self.disp_h),color=(0, 0, 0))   # display image generation, full black
        self.disp.display(disp_img)                                   # image is displayed




    def set_backlight(self, value):
        """Set the backlight on/off."""
        self.disp.set_backlight(value)




    def clean_display(self):
        """ Cleans the display by settings all pixels to black."""

        disp_img = Image.new('RGB', (self.disp_w, self.disp_h), color=(0, 0, 0))  # full black screen as new image
        self.disp.display(disp_img)                                          # display is shown to display




    def show_on_disp2r(self, r1,r2,r3='',x1=20,y1=15,x2=20,y2=70,x3=20,y3=70,fs1=26,fs2=26,fs3=26):
        """Shows text on two rows, with parameters to generalize this function; Parameters are
            r1, r2, r3: text for row1, row2 and row3
            x1, x2, x3: x coordinate for text at row1, row2 and row3
            y1, y2: y coordinate for text at row1, row2 and row3
            fs1, fs2, fs3: font size for text at row1, row2 and row3
            """
        
        font1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs1)  # font and size for first text row
        font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs2)  # font and size for second text row
        font3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs2)  # font and size for second text row
        disp_img = Image.new('RGB', (self.disp_w, self.disp_h), color=(0, 0, 0)) 
        disp_draw = ImageDraw.Draw(disp_img)
        disp_draw.text((x1, y1), r1, font=font1, fill=(255, 255, 255))    # first text row start coordinate, text, font, white color
        disp_draw.text((x2, y2), r2, font=font2, fill=(255, 255, 255))    # second text row start coordinate, text, font, white color
        disp_draw.text((x3, y3), r3, font=font3, fill=(255, 255, 255))    # third text row start coordinate, text, font, white color
        
        self.disp.display(disp_img)                                       # image is plot to the display




    def display_progress_bar(self, percent, scrambling=False):
        """ Function to print a progress bar on the display."""
        
        w = self.disp_w                                            # display width, retrieved by display setting
        
        # percent value printed as text 
        fs = 48                 # font size
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs)     # font and its size
        text_x = int(self.disp_w/2 - (fs*len(str(percent))+1)/2)                   # x coordinate for the text starting location         
        text_y = 6                                                           # y coordinate for the text starting location
        disp_img = Image.new('RGB', (self.disp_w, self.disp_h), color=(0, 0, 0)) 
        disp_draw = ImageDraw.Draw(disp_img)
        disp_draw.text((text_x, text_y), str(percent)+'%', font=font, fill=(255, 255, 255))    # text with percent value
        
        # percent value printed as progress bar filling 
        x = 10                  # x coordinate for the bar starting location
        y = 65                  # y coordinate for the bar starting location
        gap = 5                 # gap in pixels between the outer border and inner filling (even value is preferable) 
        barWidth = 48           # width of the bar, in pixels
        barLength = w-2*x-4     # lenght of the bar, in pixels
        filledPixels = int( x+gap +(barLength-2*gap)*percent/100)  # bar filling length, as function of the percent
        disp_draw.rectangle((x, y, x+barLength, y+barWidth), outline="white", fill=(0,0,0))      # outer bar border
        disp_draw.rectangle((x+gap, y+gap, filledPixels-1 , y+barWidth-gap), fill=(255,255,255)) # bar filling
        
        self.disp.display(disp_img) # image is plotted to the display




    def test_display(self):
        """ Test showing some text into some rectangles."""
        
        print("\nDisplay test for 20 seconds")
        print("Display shows rectangles and text")
        
        import time
        import RPi.GPIO as GPIO                                    # import RPi GPIO library
        GPIO.setwarnings(False)                                    # GPIO warning set to False to reduce effort on handling them
        GPIO.setmode(GPIO.BCM)                                     # GPIO modulesetting
        u_btn = 23                                                 # GPIO pin used by the uppert button
        b_btn = 24                                                 # GPIO pin used by the bottom button
        GPIO.setup(u_btn, GPIO.IN)                                 # set the upper button_pin as an input
        GPIO.setup(b_btn, GPIO.IN)                                 # set the bottom button_pin as an input
        
        w = self.disp_w                                            # display width, retrieved by display setting
        h = self.disp_h                                            # display height, retrieved by display setting
        
        font1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)  # font1
        font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)  # font2
        disp_img = Image.new('RGB', (w, h), color=(0, 0, 0))       # full black image
        
        self.disp.set_backlight(1)                                 # display backlight is set on
        start = time.time()                                        # time refrence for countdown
        timeout = 20.5                                             # timeout
        while time.time() < start + timeout:                       # while loop until timeout
            
            if not GPIO.input(23) or not GPIO.input(24):           # case one of the buttons is pressed
                break                                              # while loop is interrupted
            
            t_left = int(round(timeout + start - time.time(),0))   # time left
            t_left_str = str(t_left)                               # string of time left
            pos = 184 if t_left>9 else 199                         # position x for timeout text
            disp_img = Image.new('RGB', (w, h), color=(0, 0, 0))   # full black image
            disp_draw = ImageDraw.Draw(disp_img)                   # image is plotted to display

            disp_draw.rectangle((2, 2, w-4, h-4), outline="white", fill=(0,0,0))    # border 1
            disp_draw.rectangle((5, 5, w-7, h-7), outline="white", fill=(0,0,0))    # border 2
            disp_draw.rectangle((8, 8, w-10, h-10), outline="white", fill=(0,0,0))  # border 3
            disp_draw.rectangle((w-67, h-55, w-15, h-15), outline="red", fill=(0,0,0))  # border for timeout
            
            disp_draw.text((pos, h-45), t_left_str , font=font2, fill=(255, 0, 0))  # timeout text
            disp_draw.text((30, 25), 'DISPLAY', font=font1, fill=(255, 255, 255))   # first row text test
            disp_draw.text((33, 75), 'TEST', font=font1, fill=(255, 255, 255))      # second row text test
            self.disp.display(disp_img)                            # image is plotted to the display
            time.sleep(0.1)                                        # little sleeping time   
 
        
        if time.time() >= start + timeout:                         # case the while loop hasn't been interrupted
            time.sleep(1)                                          # little sleeping time
        self.clean_display()                                       # display is set to full black
        self.disp.set_backlight(0)                                 # display backlight is set off
        time.sleep(1)                                              # little sleeping time
        print("Display test finished\n")                           # feedback is printed to the terminal




    def test_btns(self):
        """ Buttons test: Text changes color when buttons are pressedTest showing some text into some rectangles."""
        
        print("\nButtons test for 30 seconds")
        print("Text color changes when buttons are pressed")
    
        import time
        import RPi.GPIO as GPIO                                    # import RPi GPIO library
        GPIO.setwarnings(False)                                    # GPIO warning set to False to reduce effort on handling them
        GPIO.setmode(GPIO.BCM)                                     # GPIO modulesetting
        u_btn = 23                                                 # GPIO pin used by the uppert button
        b_btn = 24                                                 # GPIO pin used by the bottom button
        GPIO.setup(u_btn, GPIO.IN)                                 # set the upper button_pin as an input
        GPIO.setup(b_btn, GPIO.IN)                                 # set the bottom button_pin as an input
        
        w = self.disp_w                                            # display width, retrieved by display setting
        h = self.disp_h                                            # display height, retrieved by display setting
        
        font1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)  # font1
        font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)  # font2
        disp_img = Image.new('RGB', (w, h), color=(0, 0, 0))       # full black image
        
        self.disp.set_backlight(1)                                        # display backlight is set on
        start = time.time()                                               # time refrence for countdown
        timeout = 30                                                      # timeout
        while time.time() < start + timeout:                              # while loop until timeout
            t_left = str(int(round(timeout + start - time.time(),0)))     # time left
            pos = 195 if len(t_left)>1 else 210                           # position x for timeout text
            col1 = (0, 255, 0) if not GPIO.input(23) else (255, 255, 255) # case upper button is pressed                        
            col2 = (0, 255, 0) if not GPIO.input(24) else (255, 255, 255) # case bottom button is pressed
            if not GPIO.input(23) and not GPIO.input(24):                 # case both buttons are pressed
                col1 = col2 = (255, 0, 0)                                 # red color is assigned
            
            disp_draw = ImageDraw.Draw(disp_img)                          # image is plotted to display
            disp_draw.rectangle((w-57, h-42, w-4, h-4), outline="red", fill=(0,0,0))  # border for timeout
            disp_draw.text((pos, h-35), t_left , font=font2, fill=(255, 0, 0))       # timeout text
            disp_draw.text((20, 25), 'BUTTONS', font=font1, fill=col1)    # first row text test
            disp_draw.text((20, 75), 'TEST', font=font1, fill=col2)       # second row text test
            
            self.disp.display(disp_img)                                   # image is plotted to the display
        
        self.clean_display()                                              # display is set to full black
        self.disp.set_backlight(0)                                        # display backlight is set off
        print("Buttons test finished\n")                                  # feedback is printed to the terminal




display = Display()

if __name__ == "__main__":
    """the main function can be used to test the display. """

    display.test_display()
    display.test_btns()
    display.set_backlight(0)

    

