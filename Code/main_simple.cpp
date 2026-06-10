#include <Arduino.h>
#include <M5Stack.h>
#include <Wire.h>
#include <Protocentral_FDC1004.h>
#include <cmath>

#define UPPER_BOUND  0X4000                 // max readout capacitance
#define LOWER_BOUND  (-1 * UPPER_BOUND)
#define CHANNEL 0                          // channel to be read
#define MEASURMENT 0                       // measurment channel

int capdac = 0;
char result[100];
int32_t capacitance = 0, capacitance2 = 0;
FDC1004 FDC;
int deltad = 8;

int moyenne(int tableau[]) {
  int sum = 0;
  for (int i = 0; i < 100; i++) {
    sum += tableau[i];
  }
  return sum / 100;
}

void setup()
{
    M5.begin(true, false, true, true);
  Wire.begin();        //i2c begin
  Serial.begin(115200); // serial baud rate
 
}

void loop()
{
  

  FDC.configureMeasurementSingle(MEASURMENT, CHANNEL, capdac);
  FDC.triggerSingleMeasurement(MEASURMENT, FDC1004_100HZ);

  //wait for completion
  delay(15);
  uint16_t value[2];
  if (! FDC.readMeasurement(MEASURMENT, value))
  {
    int16_t msb = (int16_t) value[0];
    capacitance = ((int32_t)457) * ((int32_t)msb); //in attofarads
    capacitance /= 1000;   //in femtofarads
    capacitance += ((int32_t)3028) * ((int32_t)capdac);
    Serial.print(">C1 (pf):");
    Serial.println((((float)capacitance/1000)),4);


    if (msb > UPPER_BOUND)               // adjust capdac accordingly
	{
      if (capdac < FDC1004_CAPDAC_MAX)
	  capdac++;
    }
	else if (msb < LOWER_BOUND)
	{
      if (capdac > 0)
	  capdac--;
    }

  }

  FDC.configureMeasurementSingle(MEASURMENT, 1, capdac);
  FDC.triggerSingleMeasurement(MEASURMENT, FDC1004_100HZ);

  //wait for completion
  delay(15);
  uint16_t value2[2];
  if (! FDC.readMeasurement(MEASURMENT, value2))
  {
    int16_t msb = (int16_t) value2[0];
    capacitance2 = ((int32_t)457) * ((int32_t)msb); //in attofarads
    capacitance2 /= 1000;   //in femtofarads
    capacitance2 += ((int32_t)3028) * ((int32_t)capdac);
    Serial.print(">C2 (pf):");
    Serial.println((((float)capacitance2/1000)),4);


    if (msb > UPPER_BOUND)               // adjust capdac accordingly
	{
      if (capdac < FDC1004_CAPDAC_MAX)
	  capdac++;
    }
	else if (msb < LOWER_BOUND)
	{
      if (capdac > 0)
	  capdac--;
    }

  }

  Serial.print(">C1 - C2 (pf):");
  //Serial.println(((float)(capacitance1 - capacitance2)));
  float C1 = (float)capacitance;
  float C2 = (float)capacitance2;
  Serial.println(((float)(C1-C2)),4);
  Serial.print(">C1/C2 (pf):");
  //Serial.println(((float)(capacitance2/capacitance)));
  Serial.println(((float)(C1/C2)),4);
  if (C1-C2 !=0) {
    Serial.print(">d (pm):");
  Serial.println(((float)(((C2*deltad)/(C1-C2)))),4);
  }
  
}
