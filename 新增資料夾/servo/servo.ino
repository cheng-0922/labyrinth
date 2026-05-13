#include <Servo.h>

Servo servoX;
Servo servoY;

const int servoXPin = A3;
const int servoYPin = A5;

const int joyXPin = A7;
const int joyYPin = A6;

const int center = 512;
const int deadZone = 100;

const int homeAngle = 90;
const int swingAngle = 20;

const int minAngle = homeAngle - swingAngle;  // 70
const int maxAngle = homeAngle + swingAngle;  // 110

float angleX = homeAngle;
float angleY = homeAngle;

// 最大轉動速度，數字越大轉越快
const float maxSpeed = 1.5;

// 每次更新間隔，越大越慢
const int moveDelay = 20;

void setup() {
  servoX.attach(servoXPin);
  servoY.attach(servoYPin);

  servoX.write(angleX);
  servoY.write(angleY);
}

void loop() {
  int joyX = analogRead(joyXPin);
  int joyY = analogRead(joyYPin);

  int offsetX = joyX - center;
  int offsetY = joyY - center;

  float speedX = 0;
  float speedY = 0;

  // X 軸
  if (abs(offsetX) > deadZone) {
    speedX = map(offsetX, -512, 511, -maxSpeed * 100, maxSpeed * 100) / 100.0;
  }

  // Y 軸
  if (abs(offsetY) > deadZone) {
    speedY = map(offsetY, -512, 511, -maxSpeed * 100, maxSpeed * 100) / 100.0;
  }

  angleX += speedX;
  angleY += speedY;

  angleX = constrain(angleX, minAngle, maxAngle);
  angleY = constrain(angleY, minAngle, maxAngle);

  servoX.write((int)angleX);
  servoY.write((int)angleY);

  delay(moveDelay);
}
