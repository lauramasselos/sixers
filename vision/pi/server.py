import socket
import threading
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import time

camera={"frame": None}

PORT = 50000
data = {"server-end": False}
SEEN_YELLOW = False
cmds = ["LEFT","LEFT","END"]
corner_detected = False
corner_detected_once = False
old_type = None
check_if_stops_after_switch=False
w = 160
is_current_color_green = True
yellow_threshed = None

def start_camera(cam):
    global camera
    while not data['server-end']:
        camera["frame"] = cam.read()[1]

def calculate_frame():
    global is_current_color_green
    global corner_detected, corner_detected_once
    global next_cmd, old_type
    global check_if_stops_after_switch
    prev_time=time.time()
    frame = camera["frame"]
    if frame is None: return 2
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if is_current_color_green:
        THRESHOLD_MIN = np.array([38, 25, 25],np.uint8)
        THRESHOLD_MAX = np.array([80, 255, 255],np.uint8)
    else:
        THRESHOLD_MIN = np.array([95, 25, 25],np.uint8)
        THRESHOLD_MAX = np.array([105, 255, 255],np.uint8)

    frame_threshed = cv2.inRange(hsv, THRESHOLD_MIN, THRESHOLD_MAX)

    kernel = np.ones((5,5),np.uint8)
    frame_threshed = cv2.erode(frame_threshed,kernel,iterations=1)
    frame_threshed = cv2.dilate(frame_threshed,kernel,iterations=1)

    top_left_index = np.argmax(frame_threshed[0] == 255)

    bottom_left_index = np.argmax(frame_threshed[-1] == 255)

    vert_list =  frame_threshed.sum(axis=0)
    vert_idx = np.argmax(vert_list)+1
    print(np.abs(w//2-vert_idx))


    seen_qr = False

    #print(1/(time.time()-prev_time))
    #print(top_left_index, bottom_left_index)

    if corner_detected and not corner_detected_once and top_left_index!=0 and bottom_left_index!=0:
        if np.abs(w//2-vert_idx) < 35:
            cmds.pop(0)
            corner_detected = False

    if corner_detected and corner_detected_once:
        time.sleep(1)
        is_current_color_green = not is_current_color_green
        print("whattt")
        corner_detected_once = False
        if cmds[0] == "LEFT":
            return 6
        elif cmds[0] == "RIGHT":
            return 7

    if not corner_detected:
        decoded_frame = decode(frame)
        print(1/(time.time()-prev_time))
        if len(decoded_frame)>0:
            corner_detected = True
            corner_detected_once = True
            check_if_stops_after_switch=True
            return 5
        elif top_left_index == 0 and bottom_left_index == 0:
            return 2
        if (np.abs(w//2-vert_idx)>20):
            if w//2-vert_idx > 0:
                return 3
            else:
                return 4
        else:
            return 5
    else:
        return old_type


def start_socket():
     global old_type
     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     sock.bind(('0.0.0.0', PORT))
     sock.listen(1)
     conn, addr = sock.accept()
     print("Connected from ", addr)
     while not data['server-end']:
         new_type = calculate_frame()
         if old_type == new_type: continue
         conn.sendall(str(new_type).encode())
         old_type = new_type
     sock.close()

def start_threads():
    vc = cv2.VideoCapture(0)
    vc.set(3, 160)
    vc.set(4, 120)
    camera_thread = threading.Thread(target=start_camera, args=(vc,))
    camera_thread.daemon = True
    camera_thread.start()

    start_socket()

    vc.release()

if _name_ == "_main_":
    try:
        start_threads()
    except Exception as e:
        data["server-end"] = True
        print(e)