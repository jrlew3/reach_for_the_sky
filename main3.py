"""
Face Tracking version 
"""

import numpy as np
import cv2
import sys, os, io
import RPi.GPIO as GPIO
from init import *
from Cloud import *
from picamera.array import PiRGBArray
from picamera import PiCamera
import time, serial, argparse, struct

def detectFace(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(50,50),
    )
    
    if(verbose): 
        print("Detecting face")
    
    maxArea = 0
    xpos = 0
    ypos = 0 
    width = 0
    height = 0
    
    # Send largest face
    for (x, y, w, h) in faces:
        if w*h > maxArea:
            xpos = int(x)
            ypos = int(y)
            width = int(w)
            height = int(h)
            maxArea = w*h

    if 0 < maxArea:
        bbox = (xpos, ypos, width, height)
        return bbox
    
    return None


def updateStepper(currPos, delta):
    global stepperDirection
    stepperPos = ser.readline()
    ser.flushInput()
    print("Message from Arduino: ", stepperPos)
    
    try:
        stepperPos = int(stepperPos)
    except Exception as e:
        print(e)
        return
        
    if abs(stepperPos - currPos) < delta:
        currDirection = 1
    elif stepperPos <= currPos:
        currDirection = 2
    else: 
        currDirection = 4
   
    print("Current Direction: ", currDirection);
    if(currDirection != stepperDirection):
       stepperDirection = currDirection 
       ser.write(struct.pack('>B', currDirection))


# Parse verbose flag
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbosity", required=False, action="count", help="Verbose flag")
args = parser.parse_args()
verbose = False

if args.verbosity:
    verbose = True

# Open serial port to connect with Arduino
try: 
    ser = serial.Serial(
        port = '/dev/ttyACM0',
        baudrate = 9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )
    if not ser.isOpen():
        ser.open()
        time.sleep(1)
    if(verbose):
        print("Connected to Arduino succesfully")
except Exception as e:
    print(e)

 
# Initialize tracker 
trackingFace = 0 # Does not track face to begin with 
tracker_types = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT']
tracker_type = tracker_types[6]
if tracker_type == 'MOSSE':
    tracker = cv2.TrackerMOSSE_create()

# Initialize face detection 
faceCascade = cv2.CascadeClassifier("data/haarcascades/haarcascade_frontalface_alt.xml")

# Set up camera
displayWidth = 1280
displayHeight = 736
camera = PiCamera()
camera.framerate = 32
camera.resolution = (displayWidth, displayHeight)
rawCapture = PiRGBArray(camera, size=(displayWidth, displayHeight))
time.sleep(0.1)


stepperDirection = 0

# ------------------------ BEGINNING OF MAIN LOOP ----------------------- #

for image in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    frame = image.array

    # Get fps
    """
    timer = cv2.getTickCount()
    fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
    if(verbose)
        print("FPS:", fps)
    """

    # Initialize tracker 
    if not trackingFace:
        bbox = detectFace(frame)
        if bbox is not None: 
            print ("Bbox: ", bbox)
            tracker.init(frame, bbox)
            trackingFace = 1

    if trackingFace:
        ok, bbox = tracker.update(frame)
        if not ok: 
            trackingFace = 0
            print("ERROR: Not ok"); 
        else: 
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1, p2, (255,0,0),2,1)
            
            # image, center, radius, color, thickness, linetype, shift
            xpos = int(bbox[0] + bbox[2]/2)
            ypos = int(bbox[1])
            cv2.circle(frame, (xpos, ypos), 10, (0,0, 255), -1) 
            

            if(ser.inWaiting() > 0):
                delta = bbox[2]/4
                updateStepper(xpos, delta)

        if(time  
    cv2.imshow("Tracking", frame)
    rawCapture.truncate(0) #clear stream for next picture
    
       
    k = cv2.waitKey(1) & 0xff
    if k == 27:
        break

ser.close()
