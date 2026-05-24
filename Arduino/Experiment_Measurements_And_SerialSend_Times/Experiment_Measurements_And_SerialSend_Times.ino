
#include "EMGFilter.h"
#include "esp_wifi.h"

#define bicepsSensorPin 34
#define tricepsSensorPin 34

EMGFilters bicepsFilter;
EMGFilters tricepsFilter;

int sampleRate = SAMPLE_FREQ_1000HZ;
int humFreq = NOTCH_FREQ_50HZ;

const short nrOfMeasurments = 3000;

struct Measurement {
  short raw;
  short filtered;
};
Measurement bicepsMeasArr[nrOfMeasurments];
Measurement tricepsMeasArr[nrOfMeasurments];

unsigned int maxValMeas;
float avgValMeas;
unsigned int maxValMeasPlusSend;
float avgValMeasPlusSend;

unsigned int maxValTime;
float avgValTime;
unsigned int maxValSend;
unsigned long timeClusterSend;
float avgValSend;
unsigned int maxValSendConv;
float avgValSendConv;

unsigned int timeMeas[nrOfMeasurments];
unsigned int timeMeasDirectSend[nrOfMeasurments];
unsigned int timeTimeFunc[nrOfMeasurments];
unsigned int timeSerialSend[nrOfMeasurments];
unsigned int timeSerialSendConventional[nrOfMeasurments];

String msg = "";

void setup() {

  //initialize filter
  bicepsFilter.init(SAMPLE_FREQ_1000HZ, NOTCH_FREQ_50HZ, true, true, true);
  tricepsFilter.init(SAMPLE_FREQ_1000HZ, NOTCH_FREQ_50HZ, true, true, true);
  // open serial
  Serial.begin(2000000);
  // turn off the WiFi radio entirely
  esp_wifi_deinit();
  esp_wifi_stop();
  delay(250);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();  // remove \r \n and spaces

    if (cmd.equalsIgnoreCase("start")) {
      Serial.println("Starting:");

      for (int i = 0; i < nrOfMeasurments; i++) {
        //Sensor Measurement
        timeNeededMeasurement(i);

        //How long does it take to call micros()
        timeFunctionMeasurement(i);
      }

      timeSendMeasurementsSingleBuffer();
      timeSendMeasurementsSingleConventional();

      for (int i = 0; i < nrOfMeasurments; i++) {
        maxValMeas = max(timeMeas[i], maxValMeas);
        maxValTime = max(timeTimeFunc[i], maxValTime);
        maxValMeasPlusSend = max(timeMeasDirectSend[i], maxValMeasPlusSend);
        maxValSend = max(timeSerialSend[i], maxValSend);
        maxValSendConv = max(timeSerialSendConventional[i], maxValSendConv);
      }

      avgValMeas = getAverage(timeMeas);
      avgValTime = getAverage(timeTimeFunc);
      avgValSend = getAverage(timeSerialSend);
      avgValSendConv = getAverage(timeSerialSendConventional);
      avgValMeasPlusSend = getAverage(timeMeasDirectSend);

      timeSendMeasurementsClusterBuffer();

      Serial.print("Max time needed for a measurement + filtering was: ");
      Serial.print(maxValMeas);
      Serial.println(" micro seconds.");
      Serial.print("AVG time needed for a measurement + filtering was: ");
      Serial.print(avgValMeas);
      Serial.println(" micro seconds.\n");
      Serial.print("Max time needed for a measurement + filtering + direct Send via Serial.print() was: ");
      Serial.print(maxValMeasPlusSend);
      Serial.println(" micro seconds.");
      Serial.print("AVG time needed for a measurement + filtering + direct Send via Serial.print() was: ");
      Serial.print(avgValMeasPlusSend);
      Serial.println(" micro seconds.\n");

      Serial.print("Max time needed for calling micros() was: ");
      Serial.print(maxValTime);
      Serial.println(" micro seconds.");
      Serial.print("AVG time needed for calling micros() was: ");
      Serial.print(avgValTime);
      Serial.println(" micro seconds.\n");

      Serial.print("Max time needed for Sending 1 Pack via Serial with Buffer: ");
      Serial.print(maxValSend);
      Serial.println(" micro seconds.");
      Serial.print("AVG time needed for Sending 1 Pack via Serial with Buffer: ");
      Serial.print(avgValSend);
      Serial.println(" micro seconds.");
      Serial.print("Sum Time needed for Sending all Packs 1 by 1 via Serial with Buffer: ");
      Serial.print(sumUpArray(timeSerialSend));
      Serial.println(" micro seconds.\n");

      Serial.print("Time needed for Sending all Packs as Clusters via Serial: ");
      Serial.print(timeClusterSend);
      Serial.println(" micro seconds.\n");

      Serial.print("Max time needed for Sending 1 Pack via Serial.print(): ");
      Serial.print(maxValSendConv);
      Serial.println(" micro seconds.");
      Serial.print("AVG time needed for Sending 1 Pack via Serial.print(): ");
      Serial.print(avgValSendConv);
      Serial.println(" micro seconds.");
      Serial.print("Sum Time needed for Sending all Packs 1 by 1 via Serial.print(): ");
      Serial.print(sumUpArray(timeSerialSendConventional));
      Serial.println(" micro seconds.\n");
    }
  } else {
    delay(100);
  }
}

void timeNeededMeasurement(int index) {
  //Sensor Measurement and Time it needs
  unsigned long startTime = micros();
  // Raw data
  bicepsMeasArr[index].raw = analogRead(bicepsSensorPin);
  tricepsMeasArr[index].raw = analogRead(tricepsSensorPin);
  // filter processing
  bicepsMeasArr[index].filtered = bicepsFilter.update(bicepsMeasArr[index].raw);
  tricepsMeasArr[index].filtered = tricepsFilter.update(tricepsMeasArr[index].raw);

  timeMeas[index] = micros() - startTime;

  msg.clear();
  msg.concat(bicepsMeasArr[index].raw);
  msg.concat(',');
  msg.concat(bicepsMeasArr[index].filtered);
  msg.concat(',');
  msg.concat(tricepsMeasArr[index].raw);
  msg.concat(',');
  msg.concat(tricepsMeasArr[index].filtered);

  msg.concat(';');
  Serial.print(msg);
  timeMeasDirectSend[index] = micros() - startTime;
}

void timeFunctionMeasurement(int index) {
  //How long does it take to call micros()
  unsigned long startTime = micros();
  timeTimeFunc[index] = micros() - startTime;
}

void timeSendMeasurementsSingleBuffer() {
  char buffer[1024];
  size_t bufferIndex = 0;
  unsigned long startTime;

  for (int i = 0; i < nrOfMeasurments; i++) {
    startTime = micros();
     // Append biceps Values
    bufferIndex += strlen(itoa(bicepsMeasArr[i].raw, buffer + bufferIndex, 10));
    buffer[bufferIndex++] = ',';
    bufferIndex += strlen(itoa(bicepsMeasArr[i].filtered, buffer + bufferIndex, 10));
    buffer[bufferIndex++] = ',';

    // Append triceps Values
    bufferIndex += strlen(itoa(tricepsMeasArr[i].raw, buffer + bufferIndex, 10));
    buffer[bufferIndex++] = ',';
    bufferIndex += strlen(itoa(tricepsMeasArr[i].filtered, buffer + bufferIndex, 10));
    buffer[bufferIndex++] = ';';

    // Every 100 entries add newline
    if ((i + 1) % 100 == 0) {
      buffer[bufferIndex++] = '\n';
    }

    Serial.write(buffer, bufferIndex);
    timeSerialSend[i] = micros() - startTime;

    bufferIndex = 0;
  }
  Serial.println('#');
}

void timeSendMeasurementsSingleConventional() {
  unsigned long startTime;
  String msg = "";
  for (int i = 0; i < nrOfMeasurments; i++) {
    startTime = micros();
    msg.clear();
    msg.concat(bicepsMeasArr[i].raw);
    msg.concat(',');
    msg.concat(bicepsMeasArr[i].filtered);
    msg.concat(',');
    msg.concat(tricepsMeasArr[i].raw);
    msg.concat(',');
    msg.concat(tricepsMeasArr[i].filtered);
    msg.concat(';');

    // Every 100 entries add newline
    if ((i + 1) % 100 == 0) {
      msg.concat('\n');
    }
    Serial.print(msg);
    timeSerialSendConventional[i] = micros() - startTime;
  }
  Serial.println('#');
}

void timeSendMeasurementsClusterBuffer() {
  char buffer[1024];
  size_t bufferIndex = 0;
  unsigned long startTime;
  startTime = micros();
  for (int i = 0; i < nrOfMeasurments; i++) {
    // Append biceps Values
    bufferIndex += strlen(itoa(bicepsMeasArr[i].raw, buffer + bufferIndex, 10));
    buffer[bufferIndex++] = ',';
    bufferIndex += strlen(itoa(bicepsMeasArr[i].filtered, buffer + bufferIndex, 10));
    buffer[bufferIndex++] = ',';

    // Append triceps Values
    bufferIndex += strlen(itoa(tricepsMeasArr[i].raw, buffer + bufferIndex, 10));
    buffer[bufferIndex++] = ',';
    bufferIndex += strlen(itoa(tricepsMeasArr[i].filtered, buffer + bufferIndex, 10));
    buffer[bufferIndex++] = ';';

    // Every 100 entries add newline
    if ((i + 1) % 100 == 0) {
      buffer[bufferIndex++] = '\n';
    }

    // When buffer is close to full or last element → flush
    if (bufferIndex >= 1024 - 16 || i == nrOfMeasurments - 1) {
      Serial.write(buffer, bufferIndex);
      bufferIndex = 0;
    }
  }
  timeClusterSend = micros() - startTime;
  Serial.println('#');
}

float getAverage(unsigned int *array) {
  return (float)sumUpArray(array) / nrOfMeasurments;
}

unsigned long sumUpArray(unsigned int *array) {
  unsigned long sum = 0;  // must be long to avoid overflow

  for (int i = 0; i < nrOfMeasurments; i++) {
    sum += array[i];
  }

  return sum;
}