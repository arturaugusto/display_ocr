#!/usr/bin/python3

import numpy as np
import cv2
from pyocr import pyocr
from pyocr import builders
from PIL import Image
from time import sleep

###############################################################
### Interactivity
###############################################################
drawing = False # true if mouse is pressed
ix,iy = -1,-1
rectangle = None

def define_rectangle(iy, ix, y, x):
  x_sorted = sorted([ix, x])
  y_sorted = sorted([iy, y])
  return (x_sorted[0], y_sorted[0]), (x_sorted[1], y_sorted[1])

def is_rectangle(rect):
  if rect != None\
    and 0 != rect[0][0]-rect[1][0]\
      and 0 != rect[0][1]-rect[1][1]:
        return True
  else:
    return False

# mouse callback function
def draw_shape(event,x,y,flags,param):
  global ix,iy,drawing,mode,rectangle
  if event == cv2.EVENT_LBUTTONDOWN:
    drawing = True
    ix,iy = x,y
  elif event == cv2.EVENT_MOUSEMOVE:
    if drawing == True:     
      rectangle = define_rectangle(iy, ix, y, x)    
  elif event == cv2.EVENT_LBUTTONUP:
    drawing = False        
    if not (ix == x and iy == y):            
      rectangle = define_rectangle(iy, ix, y, x)            

# GUI INPUTS
thresh, erosion_iters, most_common_filter = 0, 0, 0

def reg_threshold(x):
  global thresh
  thresh = x

def reg_erode(x):
  global erosion_iters
  erosion_iters = x
  
def reg_filter(x):
  global most_common_filter
  most_common_filter = x


###############################################################
### Imagery
###############################################################
def initialize_images():    
  p_img = '/path/to/image/file.jpg'
  img_temp = cv2.imread(p_img, 1) 
#    cv2.imshow('imagetemp',img_temp)
  img = img_temp.copy()
  return img, img_temp, None


###############################################################
### Processing
###############################################################
def processing():
  global rectangle,thresh,erosion_iters,most_common_filter    
  #
  r = cv2.getTrackbarPos('Threshold', 'Inputs')   #changed from frame to Inputs
  #
  cv2.namedWindow('image')
  cv2.setMouseCallback('image', draw_shape)
  #
  img_temp, img, roi = initialize_images()
  rectangle = None
  scale = 1
  factor = 0.75
  #
  while(1):
    sleep(0.2)
    img = img_temp.copy()
    #
    ### ROI ###########################################################
    if is_rectangle(rectangle):
      roi = img_temp[rectangle[0][1]:rectangle[1][1], rectangle[0][0]:rectangle[1][0]]
      cv2.rectangle(img,rectangle[0],rectangle[1],(0,255,0),0)
    else:
      roi = None
    ### FILTER ########################################################
    # retrieving parameters from GUI slidebars        
    ### DISPLAY #######################################################
    cv2.imshow('image',img)
    if roi is not None:      #changed from "if roi != None" which gave array related error
      kernel = np.ones((5, 5), np.uint8)
      roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
      roi = cv2.threshold(roi, thresh, 255, cv2.THRESH_BINARY)[1]
      roi = cv2.erode(roi, kernel, iterations=erosion_iters)
      cv2.imshow('ROI',roi) 

    if roi is not None and not drawing:    #changed from "if roi != None" which gave array related error
      ### OCR ###########################################################
      tool = pyocr.get_available_tools()[0] # 
      lang = 'letsgodigital'#'letsgodigital'#"eng"    #export TESSDATA_PREFIX=/path/to/tessdata/folder
      txt = tool.image_to_string(Image.fromarray(roi), lang=lang, builder=builders.TextBuilder())
      print(txt)
    ### ACTIONS #######################################################
    k = cv2.waitKey(1) & 0xFF
    if k == ord('c'):
      img_temp, img, roi = initialize_images()
      img = img_temp.copy()
      rectangle, roi = None, None
      pass
    elif k == ord('r'):
      # todo: ROI resizing
      scale *= factor
      print(scale)
      img = cv2.resize(img, (0,0), fx=factor, fy=factor)
      img_temp = img.copy()
    elif k == 27:   #esc key
      cv2.destroyAllWindows()
      break
  ### CLEANUP #######################################################
  #cv2.waitKey(0)                moved to inside esc key check
  #cv2.destroyAllWindows()

if __name__ == '__main__':
  print("Starting..")
  #
  cv2.namedWindow('Inputs')
  display = np.zeros((1, 200, 3), np.uint8)
  cv2.imshow('Inputs', display)

  cv2.createTrackbar('Threshold', 'Inputs', int(thresh), 255, reg_threshold)
  cv2.createTrackbar('Erode', 'Inputs', int(erosion_iters), 6, reg_erode)
  cv2.createTrackbar('Filter', 'Inputs', int(most_common_filter), 10, reg_filter)
  #
  processing()
  pass


