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

const int stepAngle = 7;    // 最終傾斜幅度
const int stepDelay = 1000;  // 傾斜停留時間

// ── 漸進移動：從 current 平滑移到 target ────────────────
// smoothDelay: 每個微步之間的延遲(ms)，越小越快但越可能抖
// increment  : 每個微步的角度，建議 1
void smoothWrite(Servo &servo, int current, int target, int smoothDelay = 20, int increment = 1) {
  if (current == target) return;
  int step = (target > current) ? increment : -increment;
  for (int angle = current; angle != target; angle += step) {
    servo.write(angle);
    delay(smoothDelay);
  }
  servo.write(target);  // 確保精確到位
}
int lastDirX = 2;
int lastDirY = 2;
// ── 移動一步 ────────────────────────────────────────────
void moveStep(int dirX,int dirY) {
  int targetX = baseAngleX;
  int targetY = baseAngleY;
  static int lastDirX = 2;
  static int lastDirY = 2;
  // if(!(dirX==2&&dirY==2)){
  //   if(dirX==lastDirX){
  //     smoothWrite(servoX, targetX, baseAngleX);
  //   }
  //   if(dirY==lastDirY){
  //     smoothWrite(servoY, targetY, baseAngleY);
  //   }
  //   delay(500); 
  // }

  switch (dirX) {
    case DIR_RIGHT:    targetX = baseAngleX + stepAngle; break;
    case DIR_LEFT:     targetX = baseAngleX - stepAngle; break;
    case DIR_STEADY:   targetX = baseAngleX;             break;
  }
  switch (dirY) {
    case DIR_UP:       targetY = baseAngleY + stepAngle; break;
    case DIR_DOWN:     targetY = baseAngleY - stepAngle; break;
    case DIR_STEADY:   targetY = baseAngleY;             break;
  }
      
  targetX = constrain(targetX, baseAngleX - swingAngle, baseAngleX + swingAngle);
  targetY = constrain(targetY, baseAngleY - swingAngle, baseAngleY + swingAngle);

  int smoothDelayLEFT = 20;
  int smoothDelayDOWN = 20;
  // 平滑傾斜到目標角度
  if(dirX==1){
    smoothWrite(servoX, baseAngleX, targetX,smoothDelayLEFT);
  }
  else {
    smoothWrite(servoX, baseAngleX, targetX);
  }
  if(dirY==1){
    smoothWrite(servoY, baseAngleY, targetY,smoothDelayDOWN);
  }
  else {
    smoothWrite(servoY, baseAngleY, targetY);
  }

  // 停留讓球滾動
  delay(stepDelay);
  
  // 平滑回正
  smoothWrite(servoX, targetX, baseAngleX);
  smoothWrite(servoY, targetY, baseAngleY);
  delay(500);
  
  lastDirX = dirX;
  lastDirY = dirY;
}

// void executeCommand(int dir, int steps) {
//   for (int i = 0; i < steps; i++) {
//     moveStep(dir);
//   }
// }

// ── 測試路徑 ─────────────────────────────────────────────
struct Command { int dirX;int dirY; int steps; };

const Command testPath[] = {
  { DIR_STEADY,   DIR_UP,      1 },
  { DIR_RIGHT,    DIR_STEADY,  1 },
  { DIR_STEADY,   DIR_DOWN,    1 },
  { DIR_LEFT,     DIR_STEADY,  1 },
  { DIR_STEADY,   DIR_STEADY,  1 }
  // { DIR_RIGHT,    DIR_UP,      1 },
  // { DIR_RIGHT,    DIR_DOWN,    1 },
  // { DIR_LEFT,     DIR_UP,      1 },
  // { DIR_LEFT,     DIR_DOWN,    1 }
};
const int pathLen = sizeof(testPath) / sizeof(testPath[0]);

void setup() {
  Serial.begin(9600);
  servoX.attach(servoXPin);
  servoY.attach(servoYPin);
  servoX.write(baseAngleX);
  servoY.write(baseAngleY);
  delay(500);
  Serial.println("READY");
}
// ,4,3,4,2,1
int path[]={2,3,2,1,2};
void loop() {
  if(Serial.available())
  if(Serial.read()=='s')
  {
    for (int i = 0; i <5; i++) {
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
