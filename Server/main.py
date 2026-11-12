from process import Camera
import eel
import threading
import sys
import os
import subprocess
import platform

camera = None
eel.init("web")

@eel.expose
def get_frame():
    global camera
    if not camera:
        return None
    if camera.error:
        eel.displayError(str(camera.error))
        camera = None
        return None
    frame_b64 = camera.get_frame_base64()
    return frame_b64

@eel.expose
def stop_camera(x=0,y=0):
    global camera
    if camera:
        camera.stop()
        camera = None
    eel.stopProgram()

def stop_camera_and_exit(x=0, y=0):
    stop_camera()
    sys.exit()

@eel.expose
def set_camera_mode(mode):
    if camera:
        camera.set_mode(mode)

@eel.expose
def start_camera():
    global camera
    if camera:
        return True
    camera = Camera()
    threading.Thread(target=camera.process_webcam, args=("output.mp4",), daemon=True).start()
    if camera.error:
        eel.displayError(str(camera.error))
        camera = None
        return None
    camera.setDisplayFunction(eel.displayNewDegree)
    camera.setClipListFunction(eel.displayClips)

@eel.expose
def set_camera_deg(deg):
    if camera:
        camera.sync_set_deg(deg)
        
@eel.expose
def set_recording_state(state):
    if camera:
        camera.setIsRecordingEnabled(state)

@eel.expose
def openFileExplorer(file_path):
    if os.path.exists(file_path):
        print(file_path)
        system = platform.system()

        if system == "Windows":
            os.startfile(file_path)
    else:
        print("File not found!")




eel.start("index.html", close_callback=stop_camera_and_exit)