#include <Servo.h>

Servo servoX;
Servo servoY;

void joyControl();

const int bottomPinQ = 46;
const int bottomPinM = 48;
const int bottomPinP = 50;
const int bottomPinJ = 52;

const int servoXPin = A5;
const int servoYPin = A3;

const int joyXPin = A6;
const int joyYPin = A7;

const int baseAngleX = 97;
const int baseAngleY = 90;
const int swingAngle = 10;
const int swingAngle_Y = 15;

const int minAngleX = baseAngleX - swingAngle;
const int maxAngleX = baseAngleX + swingAngle;

const int minAngleY = baseAngleY - swingAngle;
const int maxAngleY = baseAngleY + swingAngle_Y;

//joymode
const int center = 512;
const int deadZone = 50;

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

void joyControl() {
  int rawJoyX = analogRead(joyXPin);
  int rawJoyY = analogRead(joyYPin);

  filteredJoyX = filteredJoyX + filterAlpha * (rawJoyX - filteredJoyX);
  filteredJoyY = filteredJoyY + filterAlpha * (rawJoyY - filteredJoyY);

  int joyX = filteredJoyX;
  int joyY = filteredJoyY;

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

//automode

const int DIR_UP  = 0;
const int DIR_DOWN = 1;
const int DIR_LEFT     = 0;
const int DIR_RIGHT    = 1;
const int DIR_STEADY   = 2;
const int DIR_RESET    = 3;

const int stepAngle = 7;    // 最終傾斜幅度
// const int stepDelay = 600;  // 傾斜停留時間

void reset(){
  servoX.write(baseAngleX);
  servoY.write(baseAngleY);
};

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

void moveStep(int dirX, int dirY,int stepDelay = 600) {
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

struct Command { int dirX;int dirY; int steps; };

const Command testPath[] = {
  { DIR_STEADY,   DIR_UP,      1 }, //up   =0
  { DIR_RIGHT,    DIR_STEADY,  1 }, //right=1
  { DIR_STEADY,   DIR_DOWN,    1 }, //down  =2
  { DIR_LEFT,     DIR_STEADY,  1 }, //left  =3
  { DIR_STEADY,   DIR_STEADY,  1 }, //steady=4
  { DIR_RESET,    DIR_RESET,   1 }  //reset=5
};

// up=0, right=1,  down=2,  left=3,  steady=4,   reset=5
// origin maze template
int path[]={2,3,2,1,2,4,3,2,5}; //(0,4)->(8,0)
// int path[]={3,2,1,3,3,5}; //(0,8)->(8,0)
// int path[]={0,1,2,3,0,4,1,4,2,4,3,5};// test
// int path[]={0,3,0,1,3,0,1,5}; //(8,8)->(0,4)
// turn right down +90 degree
// int path[]={1,2,3,0,3,1,0,1,3,0,1,5}; //(8,8)->(0,4)

const int pathLen = sizeof(path)/sizeof(path[0]);

void pControl(String msg){
  int xIndex = msg.indexOf('X');
  int yIndex = msg.indexOf('Y');
  
  if (xIndex != -1 && yIndex != -1) {
    // 切割出相對角度字串
    String xStr = msg.substring(xIndex + 1, yIndex);
    String yStr = msg.substring(yIndex + 1);
    
    // 自動轉換為帶正負號的整數 (例如 -3, 5)
    int offsetX = xStr.toInt(); 
    int offsetY = yStr.toInt(); 
    
    // 以 baseAngle 為基準加上修正量 
    int targetAngleX = baseAngleX + offsetX; 
    int targetAngleY = baseAngleY + offsetY; 
    
    // 安全邊界限制，防止超出 swingAngle 範圍 
    targetAngleX = constrain(targetAngleX, minAngleX, maxAngleX); 
    targetAngleY = constrain(targetAngleY, minAngleY, maxAngleY); 
    
    // 讓馬達即時到位 
    servoX.write(targetAngleX); 
    servoY.write(targetAngleY); 
  }
}

bool qMode = false;
bool mMode = false;
bool pMode = false;
bool jMode = false;

void readBottom(){
  int bottomState_Q = digitalRead(bottomPinQ);
  int bottomState_M = digitalRead(bottomPinM);
  int bottomState_P = digitalRead(bottomPinP);
  int bottomState_J = digitalRead(bottomPinJ);

  if (bottomState_Q == LOW) {
    qMode = true;
    if (qMode) {
      Serial.print("q");
      qMode = false;
    }
  }
  if (bottomState_M == LOW) {
    mMode = true;
    if (mMode) {
      Serial.print("m");
      mMode = false;
    }
  }
  if (bottomState_P == LOW) {
    pMode = true;
    if (pMode) {
      Serial.print("p");
      pMode = false;
    }
  }
  if (bottomState_J == LOW) {
    jMode = true;
    if (jMode) {
      Serial.print("j");
      jMode = false;
    }
  }
}