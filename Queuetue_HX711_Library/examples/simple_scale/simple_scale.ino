#include <Q2HX711.h>


const byte data1 = 2;
const byte clock1 = 3;

const byte data2 = 4;
const byte clock2 = 5;

const byte data3 = 6;
const byte clock3 = 7;

float shift_val1;
float shift_val2;
float shift_val3;

Q2HX711 hx711_1(data1, clock1);
Q2HX711 hx711_2(data2, clock2);
Q2HX711 hx711_3(data3, clock3);

void setup() {


  Serial.begin(57600);
  Serial.println();
  Serial.println("Starting...");
  delay(1000);
  shift_val1 = hx711_1.read()/100.0;
  shift_val2 = hx711_2.read()/100.0;
  shift_val3 = hx711_3.read()/100.0;

}

void loop() {
  Serial.print("Load_cell 1 output val: ");
  Serial.println((hx711_1.read()/100.0) - shift_val1);
  Serial.print("Load_cell 2 output val: ");
  Serial.println((hx711_2.read()/100.0) - shift_val2);
  Serial.print("Load_cell 3 output val: ");
  Serial.println((hx711_3.read()/100.0) - shift_val3);

  //Serial.println(hx711_1.read()/100.0);
  //delay(10);
  //Serial.println(hx711_2.read()/100.0);
  delay(200);

  if (Serial.available() > 0) {
    char inByte = Serial.read();
    if (inByte == 't') {
        shift_val1 = hx711_1.read()/100.0;
        shift_val2 = hx711_2.read()/100.0;
        shift_val3 = hx711_3.read()/100.0;
    }
  }

}
