#include "esp_camera.h"
#include <WiFi.h>
#include <ESP32Servo.h>
#include <WebSocketsServer.h>
#include <EEPROM.h>

#define EEPROM_SIZE 512

Servo myServo;
WebSocketsServer webSocket = WebSocketsServer(82);

// ===========================
// Select camera model in board_config.h
// ===========================
#include "board_config.h"

// ===========================
// Enter your WiFi credentials
// ===========================
const char *ssid = "FV-6202";
const char *password = "31032620m";
// bool tryingToReconnect = false;

IPAddress local_ip(192,168,1,1);
IPAddress gateway(192,168,1,1);
IPAddress subnet(255,255,255,0);

String successCode = "200";
String notFoundCode = "400";

int servoPin = 13;
int currServoPos = 90;
String currServoPosStr = "";

void startCameraServer();
void setupLedFlash();

void moveServo(int deg) {
  if (deg < 30) {
    deg = 30;
  } else if (deg > 150) {
    deg = 150;
  }

  int degsToMov = currServoPos - deg;
  int durOfMov = abs(degsToMov) * (50 / 3);

  currServoPos = deg; 
  EEPROM.write(0, deg);
  EEPROM.commit();

  if (degsToMov > 0) {
    myServo.write(82);
  } else {
    myServo.write(101);
  }
  delay(durOfMov);


  myServo.write(90);
}

void updateStrPos() {
  currServoPosStr = String(currServoPos);
}

String& processCommand(uint8_t * payload, size_t length) {
  String order = "";
  String val = "";
  String dur = "";
  bool sParam = false;
  for (int i = 0; i < length; i++) {
    if (i < 3) {
      order += (char) payload[i];
    } else if (i > 3 && (char) payload[i] == ' ') {
      sParam = true;
    } else if (i > 3 && !sParam) {
      val += (char) payload[i];
    } else if (i > 3) {
      dur += (char) payload[i];
    }
  }

  Serial.println(order);
  Serial.println(val);
  Serial.println(dur);
  if (order == "cmv") {
    myServo.write(val.toInt());
    delay(dur.toInt());
    myServo.write(90);
    return successCode;
  } else if (order == "mov") {
    moveServo(val.toInt());
    return successCode;
  } else if (order == "pos") {
    updateStrPos();
    return currServoPosStr;
  }
  else if (order == "rot") {
    // myServo.write(val.toInt());
    myServo.write(85);
    delay(1000);
    myServo.write(90);
    delay(2000);
    myServo.write(99);
    delay(1000);
    myServo.write(90);
    return successCode;
  } else if (order == "stp") {
    // myServo.write(0);
    // delay(750);
    myServo.write(90);
    return successCode;
  }
  return notFoundCode;
} 

void onWebSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      Serial.println("Client connected");
      break;

    case WStype_TEXT:
      webSocket.sendTXT(num, processCommand(payload, length));
      break;

    case WStype_DISCONNECTED:
      Serial.println("Client disconnected");
      break;
  }
}

void connectWifi(bool isFirstTime = false) {
  WiFi.softAP(ssid, password);
  WiFi.softAPConfig(local_ip, gateway, subnet);
  // WiFi.setSleep(false);

  // Serial.print("WiFi connecting");
  // while (WiFi.status() != WL_CONNECTED) {
  //   delay(500);
  //   Serial.print(".");
  // }

  // IPAddress localIp = WiFi.localIP();
  // localIp[3] = 184;
  // WiFi.config(localIp);

  // Serial.println("");
  // Serial.println("WiFi connected");

  // if (isFirstTime) {
  startCameraServer();
  // }

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(local_ip);
  Serial.println("' to connect");

  webSocket.begin();
  webSocket.onEvent(onWebSocketEvent);
  Serial.println("WebSocket server started");

  // tryingToReconnect = false;
}

void setup() {
  myServo.setPeriodHertz(50);
  myServo.attach(servoPin);
  Serial.begin(115200);
  EEPROM.begin(EEPROM_SIZE);
  Serial.setDebugOutput(true);
  Serial.println();

  int storedServoPos = EEPROM.read(0);
  if (storedServoPos != 255) {
    currServoPos = storedServoPos;
    moveServo(90);
  }

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 8000000;
  config.frame_size = FRAMESIZE_VGA;
  config.pixel_format = PIXFORMAT_JPEG;  // for streaming
  //config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;



  // if PSRAM IC present, init with UXGA resolution and higher JPEG quality
  //                      for larger pre-allocated frame buffer.
  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      // Limit the frame size when PSRAM is not available
      config.frame_size = FRAMESIZE_VGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    // Best option for face detection/recognition
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  // initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);        // flip it back
    s->set_brightness(s, 1);   // up the brightness just a bit
    s->set_saturation(s, -2);  // lower the saturation
  }
  // drop down frame size for higher initial frame rate
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_VGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

// Setup LED FLash if LED pin is defined in camera_pins.h
#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  connectWifi(true);
}

void loop() {
  // Do nothing. Everything is done in another task by the web server
  // if (WiFi.status() != WL_CONNECTED && !tryingToReconnect) {
  //   tryingToReconnect = true;
  //   connectWifi();
  // }
  webSocket.loop();
}
