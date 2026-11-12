import cv2
import supervision as sv
from ultralytics import YOLO
from helpers import is_port_open
from collections import deque
from time import sleep
import base64
import websocket
import os
import threading
import uuid
import json


class Camera:
    def __init__(self):
        # Define the path to the weights file
        # Load the model
        self.model = YOLO("fairvision-ai.pt")
        self.stop_flag = False
        self.latest_frame = None
        self.error = None
        self.isAutomaticMode = False
        self.displayDeg = None
        self.displayList = None
        self.cameraDeg = 90
        self.idealDeg = -1
        self.ws = None
        self.wait = False
        self.cap = None
        self.buffer = None
        self.fps = None
        self.isRecordingEnabled = False

    def process_webcam(self, output_file="output.mp4", is_local = False):
        # camera_ip = get_local_ipv4()
        url = 0
        if not is_local:
            try:
                camera_ip = "192.168.1.1"
                if not camera_ip:
                    print("Unable to retrieve ipv4")
                    return

                print(camera_ip)

                if not is_port_open(camera_ip, 82):
                    raise "Switch cams"
                    self.error = f"This camera is currently unreachable"
                
                ws = websocket.WebSocket()
                ws.connect(f"ws://{camera_ip}:82")
                self.ws = ws
        
                self.ws.send("pos")
                self.cameraDeg = self.ws.recv()
                self.displayDeg(self.cameraDeg)
                url = f"http://{camera_ip}:81/stream"
            except:
                print("switching to local camera")
                url = 0
        
        cap = cv2.VideoCapture(url)
        self.cap = cap
        # cap = cv2.VideoCapture(1)

        if not cap.isOpened():
            self.error = f"Cannot open stream using this camera"
            return


        # Get the width, height, and fps of the input video
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        if fps <= 1:
            fps = 25

        self.fps = fps
        buffer_size = int(fps * 20)
        self.buffer = deque(maxlen=buffer_size)

        if self.isAutomaticMode:
            self.find_optimal_deg()

        # Define the codec and create VideoWriter object
        # fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'XVID' for .avi
        # out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

        # color palette
        color_palette = sv.ColorPalette.from_hex(['#FF0000', "#009C00"])

        bounding_box_annotator = sv.BoxAnnotator(color=color_palette)
        label_annotator = sv.LabelAnnotator(color=color_palette)

        # stabilize detections
        # if a result appers for consecutive times >= CHEATING_THRESHOLD display as cheating
        # otherwise display as Normal
        tracker = sv.ByteTrack(lost_track_buffer=60)

        cheat_counter = {}
        # CHEATING_THRESHOLD = int(fps * 0.25)
        CHEATING_THRESHOLD = 3
        reudction_acceleration_coef = {}
        acceleration_rate = 1.25
        while not self.stop_flag:
 
            ret, frame = cap.read()
            if not ret or frame is None:
                cap.release()
                self.error = f"Unable to read frame using this camera"
                return
            frame = cv2.resize(frame, (640, 360))
            
            if not self.wait:
                results = self.model(frame, conf=0.5, iou=0.5, verbose=False)[0]
                detections = sv.Detections.from_ultralytics(results)
                detections = tracker.update_with_detections(detections)

                # stabilization code
                print(cheat_counter)
                labels = []

                for i in range(len(detections)):
                    track_id = detections.tracker_id[i]

                    if track_id not in cheat_counter:
                        cheat_counter[track_id] = 0
                        reudction_acceleration_coef[track_id] = 1

                    if detections.class_id[i] == 0: # cheating
                        cheat_counter[track_id] = min(int(fps), cheat_counter[track_id] + 1)
                        reudction_acceleration_coef[track_id] = 1
                    elif  detections.class_id[i] == 1: # not cheating
                        cheat_counter[track_id] = max(0, cheat_counter[track_id] - reudction_acceleration_coef[track_id])
                        reudction_acceleration_coef[track_id] *= acceleration_rate
                    
                    if cheat_counter[track_id] < CHEATING_THRESHOLD:
                        labels.append("normal")
                        detections.class_id[i] = 1
                    else:
                        labels.append("Cheating")
                        detections.class_id[i] = 0
                        if self.isRecordingEnabled:
                            self.sync_save_clip()

                # display detections
                annotated_frame = bounding_box_annotator.annotate(scene=frame, detections=detections)
                annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
                # annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections)
            else:
                annotated_frame = bounding_box_annotator.annotate(scene=frame, detections=sv.Detections.empty())
                reudction_acceleration_coef = {}
                cheat_counter = {}
                tracker.reset()


            if self.latest_frame is not None:
                del self.latest_frame

            self.latest_frame = annotated_frame
            self.buffer.append(annotated_frame)


        cap.release()
        # out.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.stop_flag = True
        if self.ws:
            self.ws.close()

    def set_mode(self, new_mode):
        if new_mode == "automatic":
            self.isAutomaticMode = True
            self.find_optimal_deg()
        else:
            self.isAutomaticMode = False

    def setDisplayFunction(self, func):
        self.displayDeg = func
    
    def setClipListFunction(self, func):
        self.displayList = func

    def get_frame_base64(self):
        if self.latest_frame is None:
            print("None")
            return None
        _, buffer = cv2.imencode('.jpg', self.latest_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        return base64.b64encode(buffer).decode('utf-8')

    def set_deg(self, deg):
        if self.ws: 
            self.wait = True
            self.ws.send(f"mov {deg}")
            data = self.ws.recv()
            self.wait = False
            if data == "200":
                self.cameraDeg = deg
            return data
        
    def find_optimal_deg(self):
        possible_degs = [30, 60, 90, 120, 150]
        best_deg = -1
        highest_student_num = -1
        last_frame = None
        for deg in possible_degs:
            self.set_deg(deg)
            num_students = -1
            for _ in range(25):
                frame = self.latest_frame
                results = self.model(frame, conf=0.5, iou=0.5, verbose=False)[0]
                detections = sv.Detections.from_ultralytics(results)
                if len(detections.xyxy) > num_students:
                    num_students = len(detections.xyxy)
                sleep(1/25)
            print(num_students)
            if num_students >= highest_student_num:
                highest_student_num = num_students
                best_deg = deg
        self.sync_set_deg(best_deg)
        self.displayDeg(best_deg)

    def save_clip(self):
        if len(self.buffer) == 0:
            return
        self.isRecordingEnabled = False
        sleep(15)
        height, width, _ = self.buffer[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        vid = uuid.uuid4()

        out = cv2.VideoWriter(f'web/clips/clip-{vid}.mp4', fourcc, self.fps, (width, height))

        frames = list(self.buffer)
        for frame in frames:
            out.write(frame)
        out.release()

        os.makedirs("web/videos", exist_ok=True)
        try:
            with open("web/videos/data.json", "r") as f:
                data = json.load(f)
        except:
            data = []

        path = os.path.join(os.getcwd()).replace("\\", "/")
        # append new item
        data.append({"path": f'{path}/web/videos/clip-{vid}.mp4'})

        with open("web/videos/data.json", "w") as f:
             json.dump(data, f, indent=4)
        self.displayList(f"{path}/web/videos/clip-{vid}.mp4")
        sleep(10)
        self.isRecordingEnabled = True
    
    def setIsRecordingEnabled(self, state):
        self.isRecordingEnabled = state
    
    def sync_save_clip(self):
        print("Start saving")
        threading.Thread(target=self.save_clip, daemon=True).start()

    def sync_set_deg(self, deg):
        threading.Thread(target=self.set_deg, args=(deg,), daemon=True).start()