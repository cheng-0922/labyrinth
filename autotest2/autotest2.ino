#include "setting.h"

void setup() {
  Serial.begin(9600);
  servoX.attach(servoXPin);
  servoY.attach(servoYPin);
  servoX.write(baseAngleX);
  servoY.write(baseAngleY);
  delay(500);
  Serial.println("READY");
}

void loop() {
  if(Serial.available()){
    char cmd = Serial.read();
    if(cmd=='r'){
      servoX.write(baseAngleX);
      servoY.write(baseAngleY);
      Serial.println("RESET");
      delay(500);  
    }
    if(cmd=='s')
    {
      servoX.write(baseAngleX);
      servoY.write(baseAngleY);
      delay(100);
      Serial.println("START");
      Serial.print(pathLen);
      for (int i = 0; i < pathLen; i++) {
        moveStep(testPath[path[i]].dirX,testPath[path[i]].dirY);
        Serial.print("ACK ");
        Serial.print(testPath[i].dirX);
        Serial.print(",");
        Serial.print(testPath[i].dirY);
      }
      Serial.println("DONE");
    }
    if(cmd=='j'){
      Serial.println("JOY");
      joyControl();
      while(true){
        joyControl();
        if(cmd=='q'){
          servoX.write(baseAngleX);
          servoY.write(baseAngleY);
          break;
        }
      }
    }
  }
}
