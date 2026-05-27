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
// int lastDirX = 2;
// int lastDirY = 2;
// ── 移動一步 ────────────────────────────────────────────
void moveStep(int dirX,int dirY) {
  int targetX = baseAngleX;
  int targetY = baseAngleY;
  static int lastDirX = 2;
  static int lastDirY = 2;
  if(dirX==3&&dirY==3){     // reset
    servoX.write(baseAngleX);
    servoY.write(baseAngleY);
    delay(500);
  }
  if(!(dirX==2&&dirY==2)){
    if(dirX==lastDirX){
      smoothWrite(servoX, targetX, baseAngleX);
    }
    if(dirY==lastDirY){
      smoothWrite(servoY, targetY, baseAngleY);
    }
    delay(500); 
  }

  switch (dirX) {
    case DIR_RIGHT:    targetX = baseAngleX + stepAngle; break;
    case DIR_LEFT:     targetX = baseAngleX - stepAngle; break;
    case DIR_STEADY:   targetX = baseAngleX;             break;
    case DIR_RESET:    targetX = baseAngleX;             break;
  }
  switch (dirY) {
    case DIR_UP:       targetY = baseAngleY + stepAngle; break;
    case DIR_DOWN:     targetY = baseAngleY - stepAngle; break;
    case DIR_STEADY:   targetY = baseAngleY;             break;
    case DIR_RESET:    targetY = baseAngleY;             break;
  }
      
  targetX = constrain(targetX, baseAngleX - swingAngle, baseAngleX + swingAngle);
  targetY = constrain(targetY, baseAngleY - swingAngle, baseAngleY + swingAngle);

  int smoothDelayLEFT = 15;
  int smoothDelayDOWN = 15;
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
  // smoothWrite(servoX, targetX, baseAngleX);
  // smoothWrite(servoY, targetY, baseAngleY);
  // delay(500);
  
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
  { DIR_STEADY,   DIR_UP,      1 }, //up   =0
  { DIR_RIGHT,    DIR_STEADY,  1 }, //right=1
  { DIR_STEADY,   DIR_DOWN,    1 }, //down  =2
  { DIR_LEFT,     DIR_STEADY,  1 }, //left  =3
  { DIR_STEADY,   DIR_STEADY,  1 }, //steady=4
  { DIR_RESET,    DIR_RESET,   1 }  //reset=5
  // { DIR_RIGHT,    DIR_UP,      1 },
  // { DIR_RIGHT,    DIR_DOWN,    1 },
  // { DIR_LEFT,     DIR_UP,      1 },
  // { DIR_LEFT,     DIR_DOWN,    1 }
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

int path[]={2,3,2,1,2,4,3,2,5}; //(0,4)->(8,0)
// int path[]={3,2,1,3,3,5}; //(0,8)->(8,0)

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
