#include <Servo.h>

Servo servoX;
Servo servoY;

const int servoXPin = A5;
const int servoYPin = A3;

const int joyXPin = A6;
const int joyYPin = A7;

const int center = 512;
const int deadZone = 50;

// 伺服馬達的基準角度
const int baseAngleX = 90;
const int baseAngleY = 95;

// 限制在基準點正負 10 度
const int swingAngle = 10;

const int minAngleX = baseAngleX - swingAngle;
const int maxAngleX = baseAngleX + swingAngle;

const int minAngleY = baseAngleY - swingAngle;
const int maxAngleY = baseAngleY + swingAngle;

// 目前伺服馬達角度
float angleX = baseAngleX;
float angleY = baseAngleY;

// 最大轉動速度
const float maxSpeed = 0.4;

// 更新間隔，越大越慢
const int moveDelay = 20;

void setup() {
  servoX.attach(servoXPin);
  servoY.attach(servoYPin);

  // 開機時先讓伺服馬達回到基準角
  servoX.write(baseAngleX);
  servoY.write(baseAngleY);

  delay(500);
}

void loop() {

  // 平均濾波使讀值較穩定
  int joyX = (analogRead(joyXPin) + analogRead(joyXPin) + analogRead(joyXPin)) / 3;
  int joyY = (analogRead(joyYPin) + analogRead(joyYPin) + analogRead(joyYPin)) / 3;
  
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
  angleY -= speedY;

  // 角度限制在「伺服馬達基準點 ± 10 度」
  angleX = constrain(angleX, minAngleX, maxAngleX);
  angleY = constrain(angleY, minAngleY, maxAngleY);

  servoX.write((int)angleX);
  servoY.write((int)angleY);

  delay(moveDelay);
}