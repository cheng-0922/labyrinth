#include <Servo.h>

Servo servoX;
Servo servoY;

const int servoXPin = A5;
const int servoYPin = A3;

const int joyXPin = A6;
const int joyYPin = A7;

const int center = 512;
const int deadZone = 50;

const int baseAngleX = 97;
const int baseAngleY = 90;

const int swingAngle = 10;

const int minAngleX = baseAngleX - swingAngle;
const int maxAngleX = baseAngleX + swingAngle;

const int minAngleY = baseAngleY - swingAngle;
const int maxAngleY = baseAngleY + swingAngle;

float angleX = baseAngleX;
float angleY = baseAngleY;

const float maxSpeed = 0.4;
const int moveDelay = 20;

float filteredJoyX = center;
float filteredJoyY = center;
float filteredSpeedX = 0;
float filteredSpeedY = 0;

const float filterAlpha = 0.3;
const float speedAlpha = 0.6;

float joystickToSpeed(int offset) {
  if (abs(offset) <= deadZone) {
    return 0;
  }

  int direction = offset > 0 ? 1 : -1;
  int effectiveOffset = abs(offset) - deadZone;
  int effectiveRange = 512 - deadZone;

  float ratio = effectiveOffset / float(effectiveRange);
  ratio = ratio * ratio;

  return direction * ratio * maxSpeed;
}

void setup() {
  servoX.attach(servoXPin);
  servoY.attach(servoYPin);

  servoX.write(baseAngleX);
  servoY.write(baseAngleY);

  delay(500);
}

void loop() {
  int rawJoyX = analogRead(joyXPin);
  int rawJoyY = analogRead(joyYPin);

  filteredJoyX = filteredJoyX + filterAlpha * (rawJoyX - filteredJoyX);
  filteredJoyY = filteredJoyY + filterAlpha * (rawJoyY - filteredJoyY);

  int joyX = filteredJoyX;
  int joyY = filteredJoyY;

  // int joyX = (analogRead(joyXPin) + analogRead(joyXPin) + analogRead(joyXPin)) / 3;
  // int joyY = (analogRead(joyYPin) + analogRead(joyYPin) + analogRead(joyYPin)) / 3;

  int offsetX = joyX - center;
  int offsetY = joyY - center;

  float speedX = joystickToSpeed(offsetX);
  float speedY = joystickToSpeed(offsetY);

  filteredSpeedX = filteredSpeedX + speedAlpha * (speedX - filteredSpeedX);
  filteredSpeedY = filteredSpeedY + speedAlpha * (speedY - filteredSpeedY);

  angleX += filteredSpeedX;
  angleY -= filteredSpeedY;

  angleX = constrain(angleX, minAngleX, maxAngleX);
  angleY = constrain(angleY, minAngleY, maxAngleY);

  servoX.write((int)angleX);
  servoY.write((int)angleY);

  delay(moveDelay);
}
