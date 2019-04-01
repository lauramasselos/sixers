import sys
import threading
import cv2
import numpy as np
import time

from pyzbar.pyzbar import decode

import constants


camera = {"frame": None}

data = {"server-end": False}
SEEN_YELLOW = False
# cmds = ["FORWARD","LEFT", "RIGHT","END"]
cmds = None

EV3_SOCKET = None

corner_detected = False
corner_detected_once = False
old_type = None
check_if_stops_after_switch = False
w = 160
is_current_color_green = True
yellow_threshed = None
END = False
sleep = False

def crash():
    print("Crashing.")
    data["server-end"] = True
    if EV3_SOCKET:
        EV3_SOCKET.close()

    sys.exit(1)


def start_camera():
    global camera

    vc = cv2.VideoCapture(0)
    vc.set(3, 160)
    vc.set(4, 120)

    if vc is None or not vc.isOpened():
        vc.release()
        crash()

    camera_fail_counter = 0
    while not data['server-end']:
        frame = vc.read()[1]
        camera["frame"] = frame
        if frame is None:
            camera_fail_counter += 1

            if camera_fail_counter > 100000:
                vc.release()
                crash()

        time.sleep(0.05)

    vc.release()


def calculate_frame():
    global END
    global is_current_color_green
    global corner_detected, corner_detected_once
    global next_cmd, old_type
    global check_if_stops_after_switch, sleep, camera
    prev_time = time.time()
    frame = camera["frame"]

    if frame is None:
        return constants.MoveCommand.FRAME_EMPTY

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if is_current_color_green:
        THRESHOLD_MIN = np.array([38, 25, 25], np.uint8)
        THRESHOLD_MAX = np.array([80, 255, 255], np.uint8)
    else:
        THRESHOLD_MIN = np.array([95, 25, 25], np.uint8)
        THRESHOLD_MAX = np.array([105, 255, 255], np.uint8)

    frame_threshed = cv2.inRange(hsv, THRESHOLD_MIN, THRESHOLD_MAX)

    kernel = np.ones((5, 5), np.uint8)
    frame_threshed = cv2.erode(frame_threshed, kernel, iterations=1)
    frame_threshed = cv2.dilate(frame_threshed, kernel, iterations=1)

    top_left_index = np.argmax(frame_threshed[0] == 255)

    bottom_left_index = np.argmax(frame_threshed[-1] == 255)

    vert_list = frame_threshed.sum(axis=0)
    vert_idx = np.argmax(vert_list) + 1
    print(np.abs(w // 2 - vert_idx))

    seen_qr = False

    # print(1/(time.time()-prev_time))
    # print(top_left_index, bottom_left_index)

    if sleep:
        time.sleep(1)
        sleep = False

    if END:
        if top_left_index != 0 and bottom_left_index != 0 and np.abs(w // 2 - vert_idx) < 35:
            data["server-end"] = True
            return constants.MoveCommand.STOP
        return constants.MoveCommand.CORNER_LEFT

    if corner_detected and not corner_detected_once and top_left_index != 0 and bottom_left_index != 0:
        if np.abs(w // 2 - vert_idx) < 35:
            cmds.pop(0)
            corner_detected = False

    if corner_detected and corner_detected_once:
        time.sleep(2)
        print("whattt")
        corner_detected_once = False
        if cmds[0] == "LEFT":
            is_current_color_green = not is_current_color_green
            return constants.MoveCommand.CORNER_LEFT
        elif cmds[0] == "RIGHT":
            is_current_color_green = not is_current_color_green
            return constants.MoveCommand.CORNER_RIGHT
        elif cmds[0] == "FORWARD":
            sleep = True
            return constants.MoveCommand.FORWARD
        elif cmds[0] == "END":
            END = True
            return constants.MoveCommand.CORNER_LEFT
        return constants.MoveCommand.STOP

    if not corner_detected:
        decoded_frame = decode(frame)
        print(1 / (time.time() - prev_time))
        if len(decoded_frame) > 0:
            print("QR")
            corner_detected = True
            corner_detected_once = True
            check_if_stops_after_switch = True
            return constants.MoveCommand.FORWARD
        elif top_left_index == 0 and bottom_left_index == 0:
            return constants.MoveCommand.STOP
        if np.abs(w // 2 - vert_idx) > 20:
            if w // 2 - vert_idx > 0:
                return constants.MoveCommand.ALIGN_LEFT
            else:
                return constants.MoveCommand.ALIGN_RIGHT
        else:
            return constants.MoveCommand.FORWARD
    else:
        return old_type


def start_socket(directions, ev3_socket, ev3_conn, ev3_address, is_green):
    global old_type
    global cmds
    global data
    global is_current_color_green
    global END
    global EV3_SOCKET

    EV3_SOCKET = ev3_socket

    is_current_color_green = is_green

    cmds = directions
    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.bind(('0.0.0.0', EV3_PORT))
    # sock.listen(1)
    # conn, addr = sock.accept()
    print("Connected from ", ev3_address)
    print('Commands', directions)
    while not data['server-end']:
        new_type = calculate_frame()
        if old_type == new_type:
            continue
        print('New command is', new_type)
        if isinstance(new_type, int):
            print('received int type command from calculate_frame, use enum!')
            ev3_conn.sendall(str(new_type).encode())
        if new_type is not None:
            ev3_conn.sendall(str(new_type.value).encode())
        old_type = new_type
    data['server-end'] = False
    END = False
    return True


def start_threads():
    camera_thread = threading.Thread(target=start_camera)
    camera_thread.daemon = True
    camera_thread.start()

    # start_socket()

    # vc.release()


if __name__ == "__main__":
    try:
        start_threads()
    except Exception as e:
        data["server-end"] = True
        print(e)
