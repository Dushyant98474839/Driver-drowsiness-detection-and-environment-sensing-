//Include the library
#include <MQUnifiedsensor.h>

//Definitions
#define Board "Arduino UNO"
#define Voltage_Resolution 5
#define pin A0           //Analog input 0 of your arduino
#define MQType "MQ-135"  //MQ135
#define ADC_Bit_Resolution 10   // Changed to 10-bit resolution for Arduino UNO
#define RatioMQ135CleanAir 3.6  //RS / R0 = 3.6 ppm

//Declare Sensor
MQUnifiedsensor MQ135(Board, Voltage_Resolution, ADC_Bit_Resolution, pin, MQType);

float co = -1;
float alcohol = -1;
float co2 = -1;
float toluen = -1;
float nh4 = -1;
float acetone = -1;

void setup() {
  Serial.begin(115200);  //Init serial port
  // Removed analogReadResolution(14) as it’s not supported on UNO

  //Set math model to calculate the PPM concentration
  MQ135.setRegressionMethod(1);  //_PPM =  a*ratio^b

  /*****************************  MQ Init ********************************************/
  MQ135.init();
  MQ135.setRL(1);  // Set RL to 1 kΩ (adjust if your module differs)

  /*****************************  MQ Calibration ********************************************/
  // Serial.print("Calibrating please wait.");
  float calcR0 = 0;
  for (int i = 1; i <= 10; i++) {
    MQ135.update();  // Update data
    calcR0 += MQ135.calibrate(RatioMQ135CleanAir);
    Serial.print(".");
  }
  MQ135.setR0(calcR0 / 10);
  // Serial.println("  done!.");

  if (isinf(calcR0)) {
    Serial.println("Warning: Connection issue, R0 is infinite (Open circuit detected) please check your wiring and supply");
    while (1);
  }
  if (calcR0 == 0) {
    Serial.println("Warning: Connection issue found, R0 is zero (Analog pin shorts to ground) please check your wiring and supply");
    while (1);
  }
  /*****************************  MQ Calibration ********************************************/
  // Serial.println("** Values from MQ-135 ****");
  // Serial.println(F("|    CO    |  Alcohol  |    CO2    |  Toluen  |   NH4    |  Acetone |"));
}

void loop() {
  MQ135.update();  // Update data, the arduino will read the voltage from the analog pin

  MQ135.setA(605.18);
  MQ135.setB(-3.937);  // Configure the equation to calculate CO concentration value
  co = MQ135.readSensor();  // Sensor will read PPM concentration

  MQ135.setA(77.255);
  MQ135.setB(-3.18);  // Configure the equation to calculate Alcohol concentration value
  alcohol = MQ135.readSensor();

  MQ135.setA(110.47);
  MQ135.setB(-2.862);  // Configure the equation to calculate CO2 concentration value
  co2 = MQ135.readSensor();

  MQ135.setA(44.947);
  MQ135.setB(-3.445);  // Configure the equation to calculate Toluen concentration value
  toluen = MQ135.readSensor();

  MQ135.setA(102.2);
  MQ135.setB(-2.473);  // Configure the equation to calculate NH4 concentration value
  nh4 = MQ135.readSensor();

  MQ135.setA(34.668);
  MQ135.setB(-3.369);  // Configure the equation to calculate Acetone concentration value
  acetone = MQ135.readSensor();

  // Note: 400 Offset for CO2 source: https://github.com/miguel5612/MQSensorsLib/issues/29
  // Serial.print("|   ");
  // Serial.print(co);
  // Serial.print("   |   ");
  // Serial.print(alcohol);
  // Serial.print("   |   ");
  // Serial.print(co2 + 400);
  // Serial.print("   |   ");
  // Serial.print(toluen);
  // Serial.print("   |   ");
  // Serial.print(nh4);
  // Serial.print("   |   ");
  // Serial.print(acetone);
  // Serial.println("   |");
Serial.println(String(co) + "," + String(co2 + 400) + "," + String(alcohol) + "," + String(toluen) + "," + String(nh4) + "," + String(acetone));


  delay(50);  // Sampling frequency
}