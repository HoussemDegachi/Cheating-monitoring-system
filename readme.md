# Cheating Monitoring System

An exam monitoring system that detects cheating-related behavior in real time. An ESP32-CAM streams images over a local network to a Python server, which runs a fine-tuned YOLO-26 model, tracks each student, and displays annotated video in a live interface.

Built by Lycée El-Menchia robotics Club (2026).
Chosen to represent the Governorate of Kébili in Tounes-Tobde3.

## Highlights

- Fine-tuned **YOLO-26** model that detects cheating-related behaviors (**80% precision**)
- **ESP32-CAM client written in C++** that creates its own hotspot and streams images to the server
- **Python processing pipeline** that classifies student behavior as cheating or non-cheating
- **Score-based decision system** that aggregates detections over time to reduce false positives and sudden fluctuations
- **Eel-based GUI** that shows the processed video and detection results live
- **Servo-controlled camera rotation**, either automatic or manual
- **Webcam fallback** if no ESP32-CAM is available

## How It Works

```
ESP32-CAM (Client)  --images over local hotspot-->  Server (Python)
        ^                                               |
        |                                      YOLO-26 detection + ID tracking
        |                                               |
   servo rotation  <------- orders -------        score system + annotation
                                                        |
                                                  GUI (live video + results)
```

## Components

### Client (ESP32-CAM, C++)

Runs on the ESP32-CAM and has three jobs:

- Create a local hotspot for the server to connect to
- Send the sequence of images to the server
- Receive rotation orders from the server and move the servo motor

### Server (Python)

Runs on a more powerful computer, where the AI model runs. It connects to the client's hotspot using a password, then runs three threads at the same time:

| Thread | Location | Responsibility |
|---|---|---|
| Main | `Server/main.py` | Coordinates the connection between the AI thread and the interface |
| AI | `process.py` | Receives images from the client, runs detection, tracking and scoring, and sends annotated images back to the main thread |
| GUI | `web/` | Displays the annotated video, takes user input, and shows errors in a user-friendly format |

**AI thread in detail**

1. Handles the connection between the client and the server and receives the image sequence from the ESP32-CAM
2. Runs the fine-tuned YOLO-26 model to check whether each student in the image is cheating
3. Uses OpenCV to give each student a unique ID across frames
4. Runs the score system, where each ID has its own score, so results are balanced and one-frame false positives or quick variations don't trigger an alert
5. Annotates the images and sends them back to the main thread

**GUI in detail**

- Displays the annotated video (the sequence of images)
- Lets the user choose the camera mode (automatic or manual rotation) and, in manual mode, the rotation angle
- Shows errors in a clear, readable format

## Tech Stack

| Area | Tools |
|---|---|
| Computer vision | YOLO-26 (fine-tuned), OpenCV |
| Server | Python |
| Client firmware | C++, Arduino IDE, ESP32-CAM |
| GUI | Eel, JavaScript, HTML/CSS |

## Getting Started

### 1. Download the files

1. Open the latest release
2. Download all the files
3. Move `fairvision-ai.pt` into the `Server` folder

### 2. Set up the client (optional but recommended)

Upload the code in the `Client` folder to an ESP32-CAM using the Arduino IDE.

### 3. Run the server

```bash
python Server/main.py
```

> **No ESP32-CAM?** If you don't have one, or it isn't set up correctly, the server automatically uses your webcam instead.

## Project Structure

```
.
├── Client/     # ESP32-CAM code (C++)
└── Server/
    ├── main.py          # Main thread
    ├── process.py       # AI thread
    ├── fairvision-ai.pt # Fine-tuned model (from the release)
    └── web/             # GUI (Eel)
```