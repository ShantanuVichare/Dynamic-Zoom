import cv2
import time
import numpy as np
import torch
from src.FrameBuffer import FrameBuffer, FixedFrameBuffer
from src.utils import get_time

WAIT_TIME = 0.01 # in seconds

def log(*s):
    print('[InputStream]', get_time(), *s)

def InputStream(filePath, outputBuffer: FixedFrameBuffer):
    # Initialize global variables for the cursor position. Pass these in from pipeline.py   
    cursor_x, cursor_y = 100, 100  # Starting position
    crop_width, crop_height = 200, 200  # Size of the cropped area

    path = filePath
    cap = cv2.VideoCapture(path)  # path to video file
    
    # Mouse callback function to update cursor position
    def update_cursor_position(event, x, y, flags, param):
        log("Mouse event triggered: ", x, y)
        global cursor_x, cursor_y
        if event == cv2.EVENT_MOUSEMOVE:
            # Clamp the cursor position within the window size
            max_x = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) - 1
            max_y = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) - 1
            cursor_x = min(max(x, 0), max_x)
            cursor_y = min(max(y, 0), max_y)

    # Check if the video capture has been initialized correctly
    if not cap.isOpened():
        log("Error: Could not open video.")
        exit()

    # Get the frame rate of the video
    fps = cap.get(cv2.CAP_PROP_FPS)
    # Calculate the delay between frames in milliseconds
    delay = int(1000 / fps)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cv2.namedWindow('Video Stream')
    cv2.setMouseCallback('Video Stream', update_cursor_position)

    # loop over all frames
    for i in range(total_frames):
    #while True:
        # Read a new frame
        ret, frame = cap.read()
        if not ret:
            log("Error: Could not read frame.")
            break

        # Ensure the cropped area does not exceed the frame boundaries
        x_start = max(0, cursor_x - crop_width // 2)
        y_start = max(0, cursor_y - crop_height // 2)
        x_end = min(frame.shape[1], cursor_x + crop_width // 2)
        y_end = min(frame.shape[0], cursor_y + crop_height // 2)

        # Crop the frame if valid dimensions exist
        if (x_end > x_start) and (y_end > y_start):
            cropped_frame = frame[y_start:y_end, x_start:x_end]
            # Optionally resize the cropped frame if needed here
            
            # Display the original frame with a rectangle showing the crop area
            frame_with_rect = frame.copy()
            cv2.rectangle(frame_with_rect, (x_start, y_start), (x_end, y_end), (0, 255, 0), 2)

            # Optionally concatenate and display frames
            cv2.imshow('Video Stream', frame_with_rect)
            cv2.imshow('Cropped Area', cropped_frame)

            # Convert cropped_frame to tensor
            cropped_frame = torch.tensor(cropped_frame, dtype=torch.float32)

            # Write cropped frame to frame buffer
            log("writing frame "+str(i))
            outputBuffer.addFrame(cropped_frame) 
            log("written frame "+str(i))

        # Exit loop when 'q' is pressed
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break
    
    outputBuffer.input_exhausted = True
    log("Input Stream complete")
    cap.release()
    cv2.destroyAllWindows()