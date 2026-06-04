#include "EMGFilter.h"
#include <ESP32Servo.h>
#include "esp_wifi.h"

// --- Arduino Pins I/O ---
const int BICEPS_PIN = 34;
const int TRICEPS_PIN = 35;
const int SERVO_PIN = 13;

// --- Measuring and Controll Variables
// The Values where chossen by testing them
bool rollingWindow = false;
int currentWindowSize = 50;

float weightingFactor = 1.8;
int threshold = 28;
float speedMultiplier = 0.32;


//Servo Controll Variables, Change them according to your Servo
int servoFrequ = 50;       // Frequenzy of the controll pulses
int servoMinPulse = 500;   //500us pulse for 0 degree
int servoMaxPulse = 2500;  // 2500us pulse for max degree
int minAngleServo = 0;
int maxAngleServo = 180;  // most Servos go up to 180 degree
int exoMaxAngle = 120;    // the exoskelleton can work between 0-125 degree without hurting the user
int pulse = 0; // pulse time for the servo angele controll

// Scale the factors to int for cpu easier calculations
int scaleFactor = 1000;
int weightingFactorScaled = weightingFactor * scaleFactor;
int thresholdScaled = threshold * scaleFactor;
int speedMultiplierScaled = speedMultiplier * scaleFactor;
int minAngleServoScaled = minAngleServo * scaleFactor;
int maxAngleServoScaled = maxAngleServo * scaleFactor;
int exoMaxAngleScaled = exoMaxAngle * scaleFactor;
// Divider for the servoControll => maps degree to pulswidth
int angleToPulseDiv = (servoMaxPulse - servoMinPulse) / maxAngleServoScaled;


// --- Objects ---
EMGFilters bicFilter;
EMGFilters triFilter;
Servo servo;

// --- Communication Constants ---
const char HANDSHAKE = 'H';
const char HANDSHAKE_BACK = 'B';
const char MEASUREMENT = 'M';
const char STOP = 'S';
const char UPDATE_PARAMS = 'P';
const char MSG_END = '#';
const char ERROR = 'E';

bool isMeasuring = false;
String commandString = "";

// --- Timming Var ---
const unsigned long SAMPLE_INTERVAL_MICROS = 1000;  // 1000us = 1ms
unsigned long  previousSampleMicros = 0;

// --- Dynamic Buffer Size ---
const int MAX_WINDOW_SIZE = 500;

// --- Buffer and State Vars ---
int bicepsBuffer[MAX_WINDOW_SIZE];
int tricepsBuffer[MAX_WINDOW_SIZE];

int bufferIndex = 0;
long bicepsSum = 0;
long tricepsSum = 0;
int sampleCount = 0;

int currentBicepsMAV = 0;
int currentTricepsMAV = 0;

// Angles scaled by 1000 (e.g., 90.0 degrees = 90000)
long currentAngleScaled = 0 * scaleFactor;
long targetAngleScaled = currentAngleScaled;

// Safely flush the arrays when settings change
void resetBuffers() {
  for (int i = 0; i < MAX_WINDOW_SIZE; i++) {
    bicepsBuffer[i] = 0;
    tricepsBuffer[i] = 0;
  }
  bicepsSum = 0;
  tricepsSum = 0;
  bufferIndex = 0;
  sampleCount = 0;
  currentBicepsMAV = 0;
  currentTricepsMAV = 0;
}

void setup() {
  // Turn off WiFi to prevent background timer interruptions
  esp_wifi_deinit();
  esp_wifi_stop();

  // Start Serial for High-Speed PC Communication
  Serial.begin(2000000);

  // Initialize Filters
  bicFilter.init(SAMPLE_FREQ_1000HZ, NOTCH_FREQ_50HZ, true, true, true);
  triFilter.init(SAMPLE_FREQ_1000HZ, NOTCH_FREQ_50HZ, true, true, true);

  // Clean Buffers initially
  resetBuffers();

  // Setup Servo
  ESP32PWM::allocateTimer(0);
  servo.setPeriodHertz(servoFrequ);
  servo.attach(SERVO_PIN, servoMinPulse, servoMaxPulse);
  servo.write(currentAngleScaled / scaleFactor);  // Start at 0 degrees

  delay(250);
}

void loop() {
  // =========================================================
  // NON-BLOCKING SERIAL LISTENER
  // =========================================================
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();

    if (inChar == MSG_END) {
      commandString.trim();
      processCommand(commandString);
      commandString = "";
    } else {
      commandString += inChar;
    }
  }

  // =========================================================
  // CONTINUOUS 1000Hz CONTROL LOOP
  // =========================================================
  unsigned long currentMicros = micros();

  if (currentMicros - previousSampleMicros >= SAMPLE_INTERVAL_MICROS) {
    previousSampleMicros = currentMicros;

    short rawBic = analogRead(BICEPS_PIN);
    short rawTri = analogRead(TRICEPS_PIN);

    short filtBic = bicFilter.update(rawBic);
    short filtTri = triFilter.update(rawTri);

    sampleCount++;

    if (rollingWindow) {

      bicepsSum -= bicepsBuffer[bufferIndex];
      tricepsSum -= tricepsBuffer[bufferIndex];

      bicepsBuffer[bufferIndex] = abs(filtBic);
      tricepsBuffer[bufferIndex] = abs(filtTri);

      bicepsSum += bicepsBuffer[bufferIndex];
      tricepsSum += tricepsBuffer[bufferIndex];

      currentBicepsMAV = bicepsSum / currentWindowSize;
      currentTricepsMAV = tricepsSum / currentWindowSize;

      bufferIndex = (bufferIndex + 1) % currentWindowSize;

      if (sampleCount >= currentWindowSize) {
        updateServo();
        sampleCount = 0;
      }

    } else {
      bicepsSum += abs(filtBic);
      tricepsSum += abs(filtTri);


      if (sampleCount >= currentWindowSize) {
        currentBicepsMAV = bicepsSum / currentWindowSize;
        currentTricepsMAV = tricepsSum / currentWindowSize;

        updateServo();

        bicepsSum = 0;
        tricepsSum = 0;
        sampleCount = 0;
      }
    }

    // =========================================================
    // Send Data to the PC
    // =========================================================
    if (isMeasuring) {
      Serial.print(rawBic);
      Serial.print(',');
      Serial.print(filtBic);
      Serial.print(',');
      Serial.print(rawTri);
      Serial.print(',');
      Serial.print(filtTri);
      Serial.print(',');

      // Manually format the scaled integer into a decimal string (e.g., 90500 -> "90.5")
      Serial.print(currentAngleScaled / 1000);
      Serial.print('.');
      Serial.print((abs(currentAngleScaled) % 1000) / 100);
      Serial.print(';');
    }
  }
}

// =========================================================
// 4. NON-BLOCKING SERVO UPDATE
// =========================================================
void updateServo() {
  // Calculate Net Force entirely scaled up by 1000.
  long netForceScaled = (currentBicepsMAV * scaleFactor) - (currentTricepsMAV * weightingFactorScaled);
  long angleChangeScaled = 0;

  if (abs(netForceScaled) >= thresholdScaled) {
    angleChangeScaled = netForceScaled * speedMultiplierScaled / scaleFactor;
  }

  if (angleChangeScaled != 0) {
    targetAngleScaled += angleChangeScaled;
    targetAngleScaled = constrain(targetAngleScaled, minAngleServoScaled, exoMaxAngleScaled);  // Limit between min and max degrees

    currentAngleScaled += (targetAngleScaled - currentAngleScaled);
    // Map angle change to controll pulse
    pulse = servoMinPulse + ((long long)currentAngleScaled * (servoMaxPulse - servoMinPulse)) / maxAngleServoScaled;
  }
  servo.writeMicroseconds(pulse);
}

// =========================================================
// COMMAND HANDLER
// =========================================================
void processCommand(String cmd) {
  if (cmd.length() == 0) return;
  char type = cmd[0];

  if (type == HANDSHAKE) {
    Serial.print(HANDSHAKE_BACK);
    Serial.print(MSG_END);
  } else if (type == MEASUREMENT) {
    isMeasuring = true;
  } else if (type == STOP) {
    isMeasuring = false;
    Serial.print(MSG_END);
  } else if (type == UPDATE_PARAMS) {
    String dataStr = cmd.substring(1);

    int p1 = dataStr.indexOf(',');
    int p2 = dataStr.indexOf(',', p1 + 1);
    int p3 = dataStr.indexOf(',', p2 + 1);
    int p4 = dataStr.indexOf(',', p3 + 1);

    if (p1 != -1 && p2 != -1 && p3 != -1 && p4 != -1) {
      weightingFactorScaled = dataStr.substring(0, p1).toInt();
      thresholdScaled = dataStr.substring(p1 + 1, p2).toInt();
      speedMultiplierScaled = dataStr.substring(p2 + 1, p3).toInt();

      int newWinSize = dataStr.substring(p3 + 1, p4).toInt();
      bool newIsRolling = dataStr.substring(p4 + 1).toInt() == 1;

      newWinSize = constrain(newWinSize, 1, MAX_WINDOW_SIZE);

      if (newWinSize != currentWindowSize || newIsRolling != rollingWindow) {
        currentWindowSize = newWinSize;
        rollingWindow = newIsRolling;
        resetBuffers();
      }
    }
  } else {
    Serial.print(ERROR);
  }
}