#include "setting.h"

void setup() {

  Serial.begin(9600);

  servoX.attach(servoXPin);
  servoY.attach(servoYPin);

  servoX.write(baseAngleX);
  servoY.write(baseAngleY);

  pinMode(bottomPinQ, INPUT_PULLUP);
  pinMode(bottomPinM, INPUT_PULLUP);
  pinMode(bottomPinP, INPUT_PULLUP);
  pinMode(bottomPinJ, INPUT_PULLUP);

  delay(500);

  Serial.println("READY");
}
char cmd = 'r';
void loop() {
  readBottom();
  if(Serial.available()) {
    cmd = Serial.read();
  }
  // RESET
  if (cmd == 'r') {
    reset();
  }
  // TEST DEAD PATH
  if (cmd == 't') {
    readBottom();
    reset();
    delay(100);
    Serial.println("START DEAD PATH");
    for (int i = 0; i < pathLen; i++) {

      moveStep(
        testPath[i].dirX,
        testPath[i].dirY
      );

      Serial.print("STEP:");
      Serial.print(testPath[i].dirX);
      Serial.print(",");
      Serial.println(testPath[i].dirY);
    }

    Serial.println("DONE");
    cmd='r';
  }
  // SERIAL DIR TIME
  if (cmd == 's') {
    readBottom();
    if(Serial.available()){
      String msg_dir =Serial.readStringUntil('\n');
      msg_dir.trim();
      int dir = msg_dir.toInt();

      String msg_delay =Serial.readStringUntil('\n');
      msg_delay.trim();
      int stepDelay = msg_delay.toInt();

      moveStep(testPath[dir].dirX,testPath[dir].dirY,stepDelay);
      // Serial.println("MoveDir:");
      // Serial.print(dir);
    }
  }
  if(cmd == 'p'){
    reset();
    while (true) {
      readBottom();
      if (Serial.available() > 0) {
        String msg = Serial.readStringUntil('\n');
        msg.trim();
        
        // 檢查是否要退出 P 控制模式
        if (msg == "q" || msg == "r") {
          Serial.println("QUIT P_CONTROL");
          reset();
          cmd = 'r'; // 退回重置狀態
          break;
        }
        
        // 確實收到資料才餵給 pControl，不給它空轉的機會
        if (msg.indexOf('X') != -1 && msg.indexOf('Y') != -1) {
          pControl(msg);
        }
      }
    }
  }
  // JOYSTICK MODE
  if (cmd == 'j') {
    Serial.println("JOY");
    reset();
    while (true) {
      readBottom();
      joyControl();
      if (Serial.available()) {
        char c = Serial.read();
        if (c == 'q') {
          Serial.println("QUIT JOY");
          reset();
          cmd='r';
          break;
        }
      }
    }
  }
  
}