#include <Servo.h>

Servo servoX;
Servo servoY;

const int servoXPin = A5;
const int servoYPin = A3;

const int baseAngleX = 97;
const int baseAngleY = 90;
const int swingAngle = 10;

const int DIR_UP  = 0;
const int DIR_DOWN = 1;
const int DIR_LEFT     = 0;
const int DIR_RIGHT    = 1;
const int DIR_STEADY   = 2;
const int DIR_RESET    = 3;

const int stepAngle = 7;    // 最終傾斜幅度
const int stepDelay = 600;  // 傾斜停留時間

void smoothWrite(Servo &servo, int current, int target, int smoothDelay = 30, int increment = 1) {
  if (current == target) return;
  int step = (target > current) ? increment : -increment;
  for (int angle = current; angle != target; angle += step) {
    servo.write(angle);
    delay(smoothDelay);
  }
  servo.write(target);  // 確保精確到位
}

static int currentAngleX = baseAngleX;
static int currentAngleY = baseAngleY;

void moveStep(int dirX, int dirY) {
  int targetX = baseAngleX;
  int targetY = baseAngleY;
  static int lastAngleX = baseAngleX;
  static int lastAngleY = baseAngleY;

  if (dirX == DIR_RESET && dirY == DIR_RESET) {
    smoothWrite(servoX, currentAngleX, baseAngleX, 30);
    smoothWrite(servoY, currentAngleY, baseAngleY, 30);
    currentAngleX = baseAngleX;
    currentAngleY = baseAngleY;
    delay(500);
    return;
  }

  switch (dirX) {
    case DIR_RIGHT:  targetX = baseAngleX + stepAngle; break;
    case DIR_LEFT:   targetX = baseAngleX - stepAngle; break;
    case DIR_STEADY: targetX = lastAngleX;             break;
    case DIR_RESET:  targetX = baseAngleX;             break;
  }
  switch (dirY) {
    case DIR_UP:     targetY = baseAngleY + stepAngle; break;
    case DIR_DOWN:   targetY = baseAngleY - stepAngle; break;
    case DIR_STEADY: targetY = lastAngleY;             break;
    case DIR_RESET:  targetY = baseAngleY;             break;
  }
      
  targetX = constrain(targetX, baseAngleX - swingAngle, baseAngleX + swingAngle);
  targetY = constrain(targetY, baseAngleY - swingAngle, baseAngleY + swingAngle);

  int speedDelay = 30; 

  if (targetX != currentAngleX) {
    smoothWrite(servoX, currentAngleX, targetX, speedDelay);
    currentAngleX = targetX; // 更新真實位置
  }
  
  if (targetY != currentAngleY) {
    smoothWrite(servoY, currentAngleY, targetY, speedDelay);
    currentAngleY = targetY; // 更新真實位置
  }

  delay(stepDelay);
  
  lastAngleX = currentAngleX;
  lastAngleY = currentAngleY;
}


// ── 測試路徑 ─────────────────────────────────────────────
struct Command { int dirX;int dirY; int steps; };

const Command testPath[] = {
  { DIR_STEADY,   DIR_UP,      1 }, //up   =0
  { DIR_RIGHT,    DIR_STEADY,  1 }, //right=1
  { DIR_STEADY,   DIR_DOWN,    1 }, //down  =2
  { DIR_LEFT,     DIR_STEADY,  1 }, //left  =3
  { DIR_STEADY,   DIR_STEADY,  1 }, //steady=4
  { DIR_RESET,    DIR_RESET,   1 }  //reset=5

};

void setup() {
  Serial.begin(9600);
  servoX.attach(servoXPin);
  servoY.attach(servoYPin);
  servoX.write(baseAngleX);
  servoY.write(baseAngleY);
  delay(500);
  Serial.println("READY");
}
// //up=0, right=1,  down=2,  left=3,  steady=4,   reset=5
// origin maze template
int path[]={2,3,2,1,2,4,3,2,5}; //(0,4)->(8,0)
// int path[]={3,2,1,3,3,5}; //(0,8)->(8,0)
// int path[]={0,1,2,3,0,4,1,4,2,4,3,5};// test
// int path[]={0,3,0,1,3,0,1,5}; //(8,8)->(0,4)
// turn right down +90 degree
// int path[]={1,2,3,0,3,1,0,1,3,0,1,5}; //(8,8)->(0,4)

const int pathLen = sizeof(path)/sizeof(path[0]);

void loop() {
  if(Serial.available())
  if(Serial.read()=='r'){
    servoX.write(baseAngleX);
    servoY.write(baseAngleY);
    Serial.println("RESET");
    delay(500);  
  }
  if(Serial.read()=='s')
  {
    servoX.write(baseAngleX);
    servoY.write(baseAngleY);
    delay(100);
    Serial.println("START");
    Serial.print(pathLen);
    for (int i = 0; i < pathLen; i++) {
      // executeCommand(testPath[i].dir, testPath[i].steps);
      moveStep(testPath[path[i]].dirX,testPath[path[i]].dirY);
      Serial.print("ACK ");
      Serial.print(testPath[i].dirX);
      Serial.print(",");
      Serial.print(testPath[i].dirY);
    }
    Serial.println("DONE");
    
  }
}
