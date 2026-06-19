#include <Arduino.h>
#include <M5Stack.h>
#include <Wire.h>
#include <Protocentral_FDC1004.h>
#include <cmath>

#define UPPER_BOUND  0X4000
#define LOWER_BOUND  (-1 * UPPER_BOUND)
#define MEASURMENT 0

int capdac = 0;
FDC1004 FDC;


const float L = 30.0f;  

const float x_min  = 0.0f;    
const float x_max = L;      

float R_min  = 0.0f;  
float R_max = 0.0f;   

float cal_a = 0.0f;
float cal_b = 0.0f;
bool calibrated = false;

float Cp = 0.0f;  


float readCapacitance(uint8_t channel) {
  FDC.configureMeasurementSingle(MEASURMENT, channel, capdac);
  FDC.triggerSingleMeasurement(MEASURMENT, FDC1004_100HZ);
  delay(15);

  uint16_t value[2];
  if (!FDC.readMeasurement(MEASURMENT, value)) {
    int16_t msb = (int16_t)value[0];
    int32_t cap = ((int32_t)457) * ((int32_t)msb);
    cap /= 1000;
    cap += ((int32_t)3028) * ((int32_t)capdac);

    if (msb > UPPER_BOUND && capdac < FDC1004_CAPDAC_MAX) capdac++;
    else if (msb < LOWER_BOUND && capdac > 0)             capdac--;

    return (float)cap / 1000.0f;  // picofarads
  }
  return NAN;
}


float readAvg(uint8_t channel, int N = 10) {
  float sum = 0;
  for (int i = 0; i < N; i++) {
    float v = readCapacitance(channel);
    if (isnan(v)) return NAN;
    sum += v;
    delay(20);
  }
  return sum / N;
}

float calcul_ratio(float C1, float C2) {
  float c1c = C1 - Cp;
  float c2c = C2 - Cp;
  if ((c1c + c2c) == 0) return NAN;
  return c1c / (c1c + c2c);
}


float ratioToPosition(float R) {
  return cal_a * R + cal_b;
}

void setup() {
  M5.begin(true, false, true, true);
  Wire.begin();
  Serial.begin(115200);

  M5.Lcd.setTextSize(2);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("Calibration");
  M5.Lcd.println("Btn A -> pos basse");
  M5.Lcd.println("Btn B -> pos haute");


  Serial.println("Placer le curseur en position BASSE puis appuyer sur A");
  while (true) {
    M5.update();
    if (M5.BtnA.wasPressed()) {
      delay(200);
      float C1 = readAvg(0);
      float C2 = readAvg(1);
      if (isnan(C1) || isnan(C2)) {
        Serial.println("Erreur lecture — recommencer");
        continue;
      }

      R_min = C1 / (C1 + C2);
      Serial.print(">R_low: "); Serial.println(R_min, 6);
      Serial.print(">C1_low: "); Serial.println(C1, 4);
      Serial.print(">C2_low: "); Serial.println(C2, 4);
      break;
    }
    delay(50);
  }

  M5.Lcd.clear();
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("Pos basse OK");
  M5.Lcd.println("Btn B -> pos haute");
  Serial.println("Placer le curseur en position HAUTE puis appuyer sur B");

  while (true) {
    M5.update();
    if (M5.BtnB.wasPressed()) {
      delay(200);
      float C1 = readAvg(0);
      float C2 = readAvg(1);
      if (isnan(C1) || isnan(C2)) {
        Serial.println("Erreur lecture — recommencer");
        continue;
      }
      R_max = C1 / (C1 + C2);
      Serial.print(">R_high: "); Serial.println(R_max, 6);
      Serial.print(">C1_high: "); Serial.println(C1, 4);
      Serial.print(">C2_high: "); Serial.println(C2, 4);


      float ideal_R = 1.0f;        
      float reel_R  = R_max - R_min;
      float offset     = (ideal_R - reel_R) / 2.0f;

      Cp = 0.0f;  
      break;
    }
    delay(50);
  }

  if (fabs(R_max - R_min) < 1e-4f) {
    Serial.println("ERREUR: R_low == R_high, calibration impossible");
    while (true) delay(1000);
  }

  cal_a = (x_max - x_min) / (R_max - R_min);
  cal_b = x_min - cal_a * R_min;

  Serial.print(">cal_a: "); Serial.println(cal_a, 4);
  Serial.print(">cal_b: "); Serial.println(cal_b, 4);
  Serial.print(">Cp (pF): "); Serial.println(Cp, 4);

  M5.Lcd.clear();
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("Calibration OK");
  delay(1000);

  calibrated = true;
}

void loop() {
  if (!calibrated) return;

  float C1 = readCapacitance(0);
  float C2 = readCapacitance(1);
  if (isnan(C1) || isnan(C2)) return;

  float R = calcul_ratio(C1, C2);
  if (isnan(R)) return;

  float position = ratioToPosition(R);

  
  position = constrain(position, x_min, x_max);


  Serial.print(">C1 (pF):"); Serial.println(C1, 4);
  Serial.print(">C2 (pF):"); Serial.println(C2, 4);
  Serial.print(">Ratio R:"); Serial.println(R, 6);
  Serial.print(">Position (mm):"); Serial.println(position, 2);
  M5.Lcd.clear();
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.setTextSize(2);
  M5.Lcd.print("R = "); M5.Lcd.println(R, 4);
  M5.Lcd.print("x = "); M5.Lcd.print(position, 1); M5.Lcd.println(" mm");

  delay(50);
}