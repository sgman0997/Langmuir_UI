#include <Stepper.h>
#include <HX711_ADC.h>
#if defined(ESP8266)|| defined(ESP32) || defined(AVR)
#include <EEPROM.h>
#endif

// Number of steps per internal motor revolution
const float STEPS_PER_REV = 32;

//  Amount of Gear Reduction
const float GEAR_RED = 64;

// Number of steps per geared output rotation
const float STEPS_PER_OUT_REV = STEPS_PER_REV * GEAR_RED;
 
// Number of Steps Required
int StepsRequired;
 
// Create Instance of Stepper Class
// Specify Pins used for motor coils
// The pins used are 8,9,10,11
// Connected to ULN2003 Motor Driver In1, In2, In3, In4
// Pins entered in sequence 1-3-2-4 for proper step sequencing
 
Stepper steppermotor(STEPS_PER_REV, 8, 10, 9, 11);

//pins:
const int HX711_dout = 4; //mcu > HX711 dout pin
const int HX711_sck = 5; //mcu > HX711 sck pin

//HX711 constructor:
HX711_ADC LoadCell(HX711_dout, HX711_sck);

const int calVal_eepromAdress = 0;
const int tareOffsetVal_eepromAdress = 4;
unsigned long t = 0;

void setup() {
  Serial.begin(57600); delay(50);
  Serial.println();
  Serial.println("Starting...");

  LoadCell.begin();
  float calibrationValue; // calibration value (see example file "Calibration.ino")
  //calibrationValue = 696.0; // uncomment this if you want to set the calibration value in the sketch
#if defined(ESP8266)|| defined(ESP32)
  EEPROM.begin(512); // uncomment this if you use ESP8266/ESP32 and want to fetch the calibration value from eeprom
#endif
  EEPROM.get(calVal_eepromAdress, calibrationValue); // uncomment this if you want to fetch the calibration value from eeprom

  unsigned long stabilizingtime = 2000; // preciscion right after power-up can be improved by adding a few seconds of stabilizing time
  boolean _tare = true; //set this to false if you don't want tare to be performed in the next step
  LoadCell.start(stabilizingtime, _tare);
  if (LoadCell.getTareTimeoutFlag()) {
    Serial.println("Timeout, check MCU>HX711 wiring and pin designations");
    while (1);
  }
  else {
    LoadCell.setCalFactor(calibrationValue); // set calibration value (float)
    Serial.println("Startup is complete");
  }
  steppermotor.setSpeed(15); //25 = 12 min for 7800 steps, 100=2.5 min for 7800 steps
}


void loop() {
  static boolean newDataReady = 0;
  const int serialPrintInterval = 1; //increase value to slow down serial print activity
  delay(100);
  // check for new data/start next conversion:

  //LoadCell.update();
  for (int k = 0; k <= 100; k++) {
      LoadCell.update();
      LoadCell.getData();
  }
  float i = LoadCell.getData();
  Serial.print("\n");
  Serial.println(i);
  t = millis();

/*
  if (LoadCell.update()) newDataReady = true;

  // get smoothed value from the dataset:
  if (newDataReady) {
    if (millis() > t + serialPrintInterval) {
      float i = LoadCell.getData();
      Serial.print("");
      Serial.println(i);
      newDataReady = 0;
      t = millis();
    }
  }
  

*/



  StepsRequired  =  - STEPS_PER_OUT_REV / 2;

  // receive command from serial terminal, send 't' to initiate tare operation:
  if (Serial.available() > 0) {
    char inByte = Serial.read();
    if (inByte == 't') LoadCell.tareNoDelay();
    else if (inByte == 'o') {   //open and sample
        for (int j = 0; j <= 730; j++) { //20 iterations, 780 = fully closed
        steppermotor.step(-10);          //50 steps per iteration
        
        for (int k = 0; k <= 100; k++) {
          LoadCell.update();
          LoadCell.getData();
        }
        float i = LoadCell.getData();
        Serial.print("");
        Serial.println(i);}
    }
    else if (inByte == 'c') {   //close and sample
        for (int j = 0; j <= 730; j++) { //20 iterations
        steppermotor.step(10);          //50 steps per iteration
        for (int k = 0; k <= 100; k++) {
          LoadCell.update();
          LoadCell.getData();
        }
        float i = LoadCell.getData();
        Serial.print("");
        Serial.println(i);}
    }
        
  }

  // Check for user input of steps at Serial Monitor and rotate stepper motor
 if (Serial.available())
 {
    int steps = Serial.parseInt() ;
    steppermotor.step(steps) ;
 }
  // check if last tare operation is complete:
  if (LoadCell.getTareStatus() == true) {
    Serial.println("Tare complete");
  }

}
