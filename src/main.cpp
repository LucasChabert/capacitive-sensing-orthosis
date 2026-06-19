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

const float x_min = 0.0f;   // gauche
const float x_max = L;      // droite

const unsigned long CALIB_MS = 5000;  // duree de moyennage par point (5 s)

float R_min = 0.0f;   // mesure BtnA (basse, droite)  -> x = L
float R_max = 0.0f;   // mesure BtnB (haute, gauche)  -> x = 0

bool calibrated = false;

float Cp = 0.0f;

// Droite : x = slope * R + intercept (passe exactement par les 2 extremites)
float slope = 0.0f;
float intercept = 0.0f;


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

float calcul_ratio(float C1, float C2) {
  float c1c = C1 - Cp;
  float c2c = C2 - Cp;
  if ((c1c + c2c) == 0) return NAN;
  return c1c / (c1c + c2c);
}

// Moyenne C1 et C2 sur CALIB_MS millisecondes, puis renvoie R moyen.
// Affiche un compte a rebours sur le LCD. Retourne NAN si echec.
float calibPoint(const char* nom) {
  double sumC1 = 0.0, sumC2 = 0.0;
  long   n = 0;
  unsigned long t0 = millis();

  while (millis() - t0 < CALIB_MS) {
    float C1 = readCapacitance(0);
    float C2 = readCapacitance(1);
    if (!isnan(C1) && !isnan(C2)) {
      sumC1 += C1;
      sumC2 += C2;
      n++;
    }
    float reste = (CALIB_MS - (millis() - t0)) / 1000.0f;
    M5.Lcd.setCursor(0, 80);
    M5.Lcd.printf("Mesure... %.1f s   ", reste);
    delay(20);
  }

  if (n == 0) {
    Serial.println("Erreur lecture — recommencer");
    return NAN;
  }

  float C1m = (float)(sumC1 / n);
  float C2m = (float)(sumC2 / n);
  float R   = C1m / (C1m + C2m);

  Serial.print(">"); Serial.print(nom); Serial.print("_R: ");  Serial.println(R, 6);
  Serial.print(">"); Serial.print(nom); Serial.print("_C1: "); Serial.println(C1m, 4);
  Serial.print(">"); Serial.print(nom); Serial.print("_C2: "); Serial.println(C2m, 4);
  Serial.print(">"); Serial.print(nom); Serial.print("_N: ");  Serial.println(n);
  return R;
}

// Droite passant par les 2 extremites (R_min,x_max) et (R_max,x_min).
bool fitLinear(float R1, float x1, float R2, float x2) {
  if (fabs(R2 - R1) < 1e-9f) {
    Serial.println("ERREUR: R identiques, regression impossible");
    return false;
  }
  slope = (x2 - x1) / (R2 - R1);
  intercept = x1 - slope * R1;
  return true;
}

float ratioToPosition(float R) {
  return slope * R + intercept;
}

// Attend l'appui du bouton voulu puis lance le moyennage 5 s.
float waitAndCalib(int btn, const char* nom) {
  while (true) {
    M5.update();
    bool pressed = (btn == 0) ? M5.BtnA.wasPressed() : M5.BtnB.wasPressed();
    if (pressed) {
      float R = calibPoint(nom);
      if (!isnan(R)) return R;
    }
    delay(30);
  }
}

void setup() {
  M5.begin(true, false, true, true);
  Wire.begin();
  Serial.begin(115200);

  M5.Lcd.setTextSize(2);

  // --- Point BASSE (droite) : BtnA -> x = L ---
  M5.Lcd.clear();
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("A -> basse (droite)");
  Serial.println("Curseur BASSE (droite) puis appuyer sur A");
  R_min = waitAndCalib(0, "low");

  // --- Point HAUTE (gauche) : BtnB -> x = 0 ---
  M5.Lcd.clear();
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("Basse OK");
  M5.Lcd.println("B -> haute (gauche)");
  Serial.println("Curseur HAUTE (gauche) puis appuyer sur B");
  R_max = waitAndCalib(1, "high");
  Cp = 0.0f;

  // --- Verifications ---
  if (fabs(R_max - R_min) < 1e-4f) {
    Serial.println("ERREUR: R_low == R_high, calibration impossible");
    while (true) delay(1000);
  }

  // Droite passant exactement par :
  //  R_min -> x = L (droite) ,  R_max -> x = 0 (gauche)
  if (!fitLinear(R_min, x_max, R_max, x_min)) {
    while (true) delay(1000);
  }

  Serial.print(">slope: ");     Serial.println(slope, 6);
  Serial.print(">intercept: "); Serial.println(intercept, 6);
  Serial.print(">Cp (pF): ");   Serial.println(Cp, 4);

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