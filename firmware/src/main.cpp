


#include <Arduino.h>
#include <M5Stack.h>
#include <Wire.h>
#include <Protocentral_FDC1004.h>
#include <cmath>


#define UPPER_BOUND  0X4000
#define LOWER_BOUND  (-1 * UPPER_BOUND)
#define MEASURMENT 0

int capdac = 0;
int32_t capacitance = 0, capacitance2 = 0;
FDC1004 FDC;

// --- Constantes de calibration ---
const float deltad = 8.0f;   // écart fixe entre les deux capteurs (mm)
const float d0     = 6.0f;  // distance de référence mesurée mécaniquement (mm)
float eS = 0;


// --- Variables de calibration (mesurées à l'origine) ---
float C10 = 0.0f;
float C20 = 0.0f;
float alpha = 0.0f;  // epsilon1/epsilon2, constant
bool calibrated = false;
float f0 = 0;

// --- Lecture d'un canal FDC1004 ---
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

    return (float)cap / 1000.0f;  // en picofarads
  }
  return NAN;
}

void setup() {
  M5.begin(true, false, true, true);
  Wire.begin();
  Serial.begin(115200);

  // --- Calibration à l'origine ---
  // On attend 500ms pour que le capteur se stabilise
  delay(500);

  // Moyenne sur 10 lectures pour plus de robustesse
  float sum1 = 0, sum2 = 0;
  const int N = 10;
  for (int i = 0; i < N; i++) {
    sum1 += readCapacitance(0);
    sum2 += readCapacitance(1);
    delay(20);
  }
  C10 = sum1 / N;
  C20 = sum2 / N;
  f0 = C10/ C20;

  // rapport_eps = (epsilon1/epsilon2), admis constant
  alpha = ((C10 / C20) -1 )* (d0 / (deltad));

  Serial.print(">C10 (pF):"); Serial.println(C10, 4);
  Serial.print(">C20 (pF):"); Serial.println(C20, 4);
  Serial.print(">rapport_eps:"); Serial.println(alpha, 6);

  calibrated = true;
  eS = C20 * deltad;
}

void loop() {
  if (!calibrated) return;

  float C1 = readCapacitance(0);
  float C2 = readCapacitance(1);
  float f = C1/C2;
  if (isnan(C1) || isnan(C2)) return;

  Serial.print(">C1 (pF):"); Serial.println(C1, 4);
  Serial.print(">C2 (pF):"); Serial.println(C2, 4);
  Serial.print(">C1/C2 (pF):"); Serial.println(C1/ C2, 4);

 Serial.print(">ration des c :"); Serial.println(C1/C2, 6);
 Serial.print(">ration des  eps:"); Serial.println(alpha, 6);
 float d = eS / C2;
 Serial.print(">distance  :"); Serial.println((d), 6);

}

