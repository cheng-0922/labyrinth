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

  while (Serial.available() > 0) {

    char cmd = Serial.read();

    // ======================
    // RESET
    // ======================

    if (cmd == 'r') {
      reset();
      Serial.println("RESET");
      continue;
    }

    // ======================
    // START PATH
    // ======================

    if (cmd == 's') {
      reset();
      delay(100);
      Serial.println("START");
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

      continue;
    }

    // ======================
    // TEST ANGLE
    // ======================

    if (cmd == 't') {
      String msg =
        Serial.readStringUntil('\n');
      msg.trim();

      int stepAngle = msg.toInt();

      Serial.print("STEPANGLE:");
      Serial.println(stepAngle);

      continue;
    }
    if (cmd == ''

    // ======================
    // JOYSTICK MODE
    // ======================

    if (cmd == 'j') {
      Serial.println("JOY");
      reset();

      while (true) {
        joyControl();

        if (Serial.available()) {
          char c = Serial.read();

          if (c == 'q') {
            Serial.println("QUIT JOY");
            reset();
            break;
          }
        }
      }

      continue;
    }
  }
}