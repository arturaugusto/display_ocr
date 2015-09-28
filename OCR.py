#!/usr/bin/env python

import tesseract
import numpy as np
import cv2
import cv2.cv as cv
import time
import datetime
from time import strftime 
from collections import Counter
import ConfigParser

def ConfigSectionMap(section):
    global Config
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def SaveImage(event):
    global display
    params = list()
    params.append(cv.CV_IMWRITE_PNG_COMPRESSION)
    params.append(8)
    filename = datetime.datetime.now().strftime('%y%m%d%H%M%S_%f') + ".png"
    cv2.imwrite(filename, display, params)
def OnClose(event):
    global stopOpenCv
    stopOpenCv = True
def Recognize(iplimage):
    global meas_stack
    tesseract.SetCvImage(iplimage,api)
    full_text = ""
    full_text = api.GetUTF8Text()
    conf = api.MeanTextConf()
    # Ger the first line found by tesseract
    for index, text in enumerate(full_text.split('\n')):
        # Some char filter
        text = text.replace(" ", "")
        for char in ConfigSectionMap("POSPROCESS")['strip']:
            text = text.replace(char, "")
        try:
            text_val = float(text)
            # handle OCRed value if exists an expected value prvided by user
            if expected_value != "":
                up_limit = (float(expected_value))*(1+(float(expected_value_desv)/100))
                dn_limit = (float(expected_value))*(1-(float(expected_value_desv)/100))
                if (
                    len(text) > 0 and
                    text_val > dn_limit and 
                    text_val < up_limit
                   ):
                    pass
                else:
                    return 0
            # most common filter valur

            most_common_filter_pos = cv2.getTrackbarPos('Filter','frame')
            # add last text
            meas_stack.append(text)
            if len(meas_stack) > most_common_filter_pos:
                # remove old
                meas_stack = meas_stack[-(most_common_filter_pos+1):]
                # count most frequent value
                count = Counter(meas_stack)
                out = count.most_common()[0][0]
                ## show if the last is the most common
                #if out == meas_stack[-1]:
                print "Timestamp: " + datetime.datetime.now().strftime('%y%m%d%H%M%S_%f')
                print "Line " + str(index)
                print  out
        except:
            pass
def getthresholdedimg(hsv):
    yellow = cv2.inRange(hsv,np.array((20,100,100)),np.array((30,255,255)))
    blue = cv2.inRange(hsv,np.array((100,100,100)),np.array((120,255,255)))
    both = cv2.add(yellow,blue)
    return both

if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read("./config.ini")
    #####################################################################
    # Pre process params
    thresh = ConfigSectionMap("PREPROCESS")['threshold']
    erosion_iters = ConfigSectionMap("PREPROCESS")['erode']
    most_common_filter = ConfigSectionMap("POSPROCESS")['filter']
    drawing = False # true if mouse is pressed
    start_x,start_y = -1,-1
    end_x,end_y = 1,1
    # flag to stop opencv
    stopOpenCv = False
    # user assist vars
    expected_value = ""
    expected_value_desv = 20
    #####################################################################
    # Video capture
    cap = cv2.VideoCapture(0)
    # Tesseract config
    api = tesseract.TessBaseAPI()
    api.Init(".",ConfigSectionMap("OCR")['fonttype'],tesseract.OEM_DEFAULT)
    api.SetVariable("tessedit_char_whitelist", ConfigSectionMap("OCR")['whitelist'])
    api.SetPageSegMode(tesseract.PSM_AUTO)
    def nothing(x):
        pass

    # mouse callback function
    def draw_rectangle(event,x,y,flags,param):
        global start_x,start_y,end_x,end_y,drawing, expected_value
        if event == cv2.EVENT_LBUTTONDOWN:
            # menu position
            if y < 40:
                #menu map
                if x > 8 and x < 148:
                    SaveImage(event)
                if x > 153 and x < 190:
                    OnClose(event)
                if x > 195 and x < 252:
                	print "Author: Artur Augusto Martins (arturaugusto@gmail.com).\nOpenSource Development: https://github.com/arturaugusto/display_ocr.\nBased on examples availables at https://code.google.com/p/python-tesseract/.\nGPLv2 License"
            else:
                drawing = True
                start_x,start_y = x,y
                end_x,end_y = x,y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            #start_x,start_y = -1,-1
            #end_x,end_y = -1,-1
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if y < 40:
                end_x,end_y = x,41
            else:
                end_x,end_y = x,y

    cv2.namedWindow('frame')
    # Show black image as selected at first
    cv2.namedWindow('selection')
    display = np.zeros((200,200,3), np.uint8)
    cv2.imshow('frame', display)

    # GUI
    cv2.createTrackbar('Threshold','frame',int(thresh),255,nothing)
    cv2.createTrackbar('Erode','frame',int(erosion_iters),4,nothing)
    cv2.createTrackbar('Filter','frame',int(most_common_filter),10,nothing)
    # menu image
    menu = cv2.imread("menu.png")
    cv2.setMouseCallback('frame', draw_rectangle)

    # stack
    meas_stack = []
    phase_stack = []
    time_stack = []
    phase_stack_size = 4
    control_moving = False
    moviment_trigger = 40
    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()
        # add menu
        frame_h, frame_w = frame.shape[:2]
        frame[0:menu.shape[0], 0:menu.shape[1]] = menu
        ##############################################
        # ROI
        ##############################################

        cv2.rectangle(frame,(start_x,start_y),(end_x,end_y),(0,255,0),1)
        # selection region
        min_x = min(start_x, end_x)
        max_x = max(start_x, end_x)

        min_y = min(start_y, end_y)
        max_y = max(start_y, end_y)

        display = frame[min_y:max_y, min_x:max_x]
        height,width,channel = display.shape

        # Show frame
        cv2.imshow('frame', frame)
        ##############################################
        # OCR work
        ##############################################
        
        if (height > 10) and (width > 10):
            # Display selection on other window 
            channel = 1
            display = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
            thresh = cv2.getTrackbarPos('Threshold','frame')
            display = cv2.threshold(display, thresh, 255, cv2.THRESH_BINARY)[1]
            kernel = np.ones((5,5),np.uint8)
            erosion_iters = cv2.getTrackbarPos('Erode','frame')
            display = cv2.erode(display,kernel, iterations = erosion_iters)
            # Show selection
            cv2.imshow('selection', display)
            #image = wx.ImageFromStream(f)
            #bitmap = wx.BitmapFromImage(image)
            #static_bitmap.SetBitmap(bitmap)
            iplimage = cv.CreateImageHeader((width,height), cv.IPL_DEPTH_8U, channel)
            cv.SetData(iplimage, display.tostring(),display.dtype.itemsize * channel * (width))
            Recognize(iplimage)
        c = cv.WaitKey(20)
        if(c=="q"):
            break
        if stopOpenCv:
            break
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
