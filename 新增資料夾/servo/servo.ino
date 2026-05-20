#include <Servo.h>

Servo servoX;
Servo servoY;

const int servoXPin = A3;
const int servoYPin = A5;

const int joyXPin = A7;
const int joyYPin = A6;

const int center = 512;
const int deadZone = 100;

// 伺服馬達的基準角度
const int baseAngleX = 90;
const int baseAngleY = 90;

// 限制在基準點正負 20 度
const int swingAngle = 20;

const int minAngleX = baseAngleX - swingAngle;
const int maxAngleX = baseAngleX + swingAngle;

const int minAngleY = baseAngleY - swingAngle;
const int maxAngleY = baseAngleY + swingAngle;

// 目前伺服馬達角度
float angleX = baseAngleX;
float angleY = baseAngleY;

// 最大轉動速度
const float maxSpeed = 3;

// 更新間隔，越大越慢
const int moveDelay = 30;

void setup() {
  servoX.attach(servoXPin);
  servoY.attach(servoYPin);

  // 開機時先讓伺服馬達回到基準角
  servoX.write(baseAngleX);
  servoY.write(baseAngleY);

  delay(500);
}

void loop() {
  int joyX = analogRead(joyXPin);
  int joyY = analogRead(joyYPin);

  int offsetX = joyX - center;
  int offsetY = joyY - center;

  float speedX = 0;
  float speedY = 0;

  if (abs(offsetX) > deadZone) {
    speedX = map(offsetX, -512, 511, -maxSpeed * 100, maxSpeed * 100) / 100.0;
  }

  if (abs(offsetY) > deadZone) {
    speedY = map(offsetY, -512, 511, -maxSpeed * 100, maxSpeed * 100) / 100.0;
  }

  angleX += speedX;
  angleY += speedY;

  // 角度限制在「伺服馬達基準點 ± 20 度」
  angleX = constrain(angleX, minAngleX, maxAngleX);
  angleY = constrain(angleY, minAngleY, maxAngleY);

  servoX.write((int)angleX);
  servoY.write((int)angleY);

  delay(moveDelay);
}