/**
 * The MySensors Arduino library handles the wireless radio link and protocol
 * between your home built sensors/actuators and HA controller of choice.
 * The sensors forms a self healing radio network with optional repeaters. Each
 * repeater and gateway builds a routing tables in EEPROM which keeps track of the
 * network topology allowing messages to be routed to nodes.
 *
 * Created by Henrik Ekblad <henrik.ekblad@mysensors.org>
 * Copyright (C) 2013-2015 Sensnology AB
 * Full contributor list: https://github.com/mysensors/Arduino/graphs/contributors
 *
 * Documentation: http://www.mysensors.org
 * Support Forum: http://forum.mysensors.org
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * version 2 as published by the Free Software Foundation.
 *
 *******************************
 *
 * REVISION HISTORY
 * Version 1.0 - Henrik EKblad
 * 
 * DESCRIPTION
 * This sketch provides an example how to implement a humidity/temperature
 * sensor using DHT11/DHT-22 
 * http://www.mysensors.org/build/humidity
 */
 
// Enable debug prints
#define MY_DEBUG

// Enable and select radio type attached
#define MY_RADIO_NRF24
//#define MY_RADIO_RFM69

//#define MY_DEBUG_VERBOSE_RF24
//#define MY_RF24_PA_LEVEL     RF24_PA_LOW
//#define MY_RF24_DATARATE     RF24_1MBPS

#define MY_NODE_ID 1

#include <SPI.h>
#include <MySensors.h>  
#include <DHT.h>  

#define SN "Badkamer"
#define SV "1.0"
#define CHILD_ID_TEMP 1
#define CHILD_ID_HUM 2
#define CHILD_ID_MOT 3   // Id of the sensor child
#define HUMIDITY_SENSOR_DIGITAL_PIN 4

#define DIGITAL_INPUT_SENSOR 3   // The digital input you attached your motion sensor.  (Only 2 and 3 generates interrupt!)
#define INTERRUPT DIGITAL_INPUT_SENSOR-2 // Usually the interrupt = pin -2 (on uno/nano anyway)

unsigned long SLEEP_TIME = 60000; // Sleep time between reads (in milliseconds)

DHT dht;
float lastTemp;
float lastHum;
boolean metric = true; 
MyMessage msgHum(CHILD_ID_HUM, V_HUM);
MyMessage msgTemp(CHILD_ID_TEMP, V_TEMP);
MyMessage msgMot(CHILD_ID_MOT, V_TRIPPED);

void presentation()  
{ 
  // Send the Sketch Version Information to the Gateway
  sendSketchInfo(SN, SV);

  // Register all sensors to gw (they will be created as child devices)
  delay(200);
  present(CHILD_ID_TEMP, S_TEMP);
  delay(200);
  present(CHILD_ID_HUM, S_HUM);
  delay(200);
  present(CHILD_ID_MOT, S_MOTION);

  metric = getConfig().isMetric;
}

void setup()  
{ 
  dht.setup(HUMIDITY_SENSOR_DIGITAL_PIN); 
  if (SLEEP_TIME <= dht.getMinimumSamplingPeriod()) {
    Serial.println("Warning: UPDATE_INTERVAL is smaller than supported by the sensor!");
  }
  // Sleep for the time of the minimum sampling period to give the sensor time to power up
  // (otherwise, timeout errors might occure for the first reading)
  sleep(dht.getMinimumSamplingPeriod());

//  metric = getConfig().isMetric;

  pinMode(DIGITAL_INPUT_SENSOR, INPUT);      // sets the motion sensor digital pin as input

  delay(100);
  send(msgTemp.set("0"));
  delay(100);
  send(msgHum.set("0"));
  delay(100);
  send(msgMot.set("0"));
}

void loop()      
{  
  // Read digital motion value
  boolean tripped = digitalRead(DIGITAL_INPUT_SENSOR) == HIGH; 
        
  Serial.println(tripped);
  send(msgMot.set(tripped?"1":"0"));  // Send tripped value to gw 
  
  delay(dht.getMinimumSamplingPeriod());
 
  // Fetch temperatures from DHT sensor
  float temperature = dht.getTemperature();
  if (isnan(temperature)) {
      Serial.println("Failed reading temperature from DHT");
  } else if (temperature != lastTemp) {
    lastTemp = temperature;
    if (!metric) {
      temperature = dht.toFahrenheit(temperature);
    }
    send(msgTemp.set(temperature, 1));
    #ifdef MY_DEBUG
    Serial.print("T: ");
    Serial.println(temperature);
    #endif
  }
  
  // Fetch humidity from DHT sensor
  float humidity = dht.getHumidity();
  if (isnan(humidity)) {
      Serial.println("Failed reading humidity from DHT");
  } else if (humidity != lastHum) {
      lastHum = humidity;
      send(msgHum.set(humidity, 1));
      #ifdef MY_DEBUG
      Serial.print("H: ");
      Serial.println(humidity);
      #endif
  }
  
  sleep(INTERRUPT,CHANGE, SLEEP_TIME); //sleep a bit
}
