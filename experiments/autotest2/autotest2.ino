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
      reset();
      Serial.println("RESET");
      delay(500);  
    }
    if(cmd=='s')
    {
      reset();
      delay(100);
      Serial.println("START");
      Serial.print(pathLen);
      for (int i = 0; i < pathLen; i++) {
        moveStep(testPath[path[i]].dirX,testPath[path[i]].dirY);
        Serial.print("STEP:");
        Serial.print(testPath[i].dirX);
        Serial.print(",");
        Serial.print(testPath[i].dirY);
      }
      Serial.println("DONE");
    }
    if(cmd=='t'){
      if(Serial.available()>0){
        String msg = Serial.readStringUntil('\n');
        msg.trim();
        int stepAngle = msg.toInt();
        Serial.println("stepangle:");
        Serial.print(stepAngle);
      }
    }
    if(cmd=='j'){
      Serial.println("JOY");
      reset();
      while(true){
        joyControl();
        if(cmd=='q'){
          Serial.println("QUIT JOY");
          reset();
          break;
        }
      }
    }
  }
}
