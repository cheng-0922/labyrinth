# labyrinth

## usage
```bash

ssh lab@labyrinth

cd ./project/src

## no debug

python main.py 

## debug

python main.py --d

## image

python main.py --i <file_path>

## text mode

python main.py --t 

python main.py --d --t 
```
### terminal
- mode 0

```bash
>> 'r' : RESET
```
 -  - auto play mode 
```bash
>> 'm' extract maze then >> 'p' : START PID auto control

>> 'q' leave, print("QUIT P_CONTROL")
```

- - hand controll mode
```bash
>> 'm' extract maze then >> 'j' : JOY on joystick (print "JOY")

>> 'q' leave, print ("QUIT JOY")

>> 'o' : send a tilt message

>> 'f' : find the ball

>> '`' or esc on window : quit

>> ':': switch to mode 1 - modify maze_extract.py parameters

>> '/': switch to mode 2 - modify main.py parameters

>> '.': switch to mode 3 - modify ball_detector.py parameters
```
- mode 1,2,3

```bash
>> '1': go to mode 1

>> '2': go to mode 2

>> '3' got to mode 3

>> '?': show parameters 

>> 'q': leave mode 1 or 2 to mode 0

>> w = 0.25 : set parameter in extractor
```

### CV2 window
- auto play mode 
```bash
>> 'm' extract maze, shows fillrate on black mask and its connectivity

then >> 'p' : START PID auto control

>> 'q' leave, print("QUIT P_CONTROL")
```

- hand controll mode
```bash
>> 'm' extract maze, shows fillrate on black mask and its 

then >> 'j' : JOY on joystick (print "JOY") shows treasure points

>> 'q' leave, print ("QUIT JOY")


```
# Tree of files

```bash
.
├── README.md                          # 操作說明
├── experiments                        # 本專案中開發歷程之階段性檔案
│   ├── autotest2                      # 固定路徑之馬達操控測試
│   │   ├── autotest2.ino
│   │   └── setting.h
│   ├── ball_detect                    # 定位迷宮中的鋼珠
│   │   ├── Images
│   │   │   ├── Final27.05.2026.png
│   │   │   ├── green05.2026.png
│   │   │   └── test_maze.jpg
│   │   ├── ball.py
│   │   ├── bearing_ball.py
│   │   └── test.py
│   ├── maze_extract                   # 影像辨識迷宮構造（以照片測試程式）、控制雛形
│   │   ├── Debug30.05.2026.png
│   │   ├── Final27.05.png
│   │   ├── ball_detector.py
│   │   ├── bm01.jpg
│   │   ├── bm02.jpg
│   │   ├── bm03.jpg
│   │   ├── bm30.01.png
│   │   ├── generate_test_img.py
│   │   ├── green05.2026.png
│   │   ├── list.txt
│   │   ├── main.py
│   │   ├── maze.csv
│   │   ├── maze.png
│   │   ├── maze.py
│   │   ├── maze_dect.py
│   │   ├── maze_extract.py
│   │   ├── maze_tem.png
│   │   ├── node.py
│   │   ├── ref0.jpg
│   │   ├── ser.py
│   │   ├── test.py
│   │   ├── test_maze.jpg
│   │   └── test_maze_auto.jpg
│   └── servo                            # servo 馬達控制
│       └── servo.ino
│
└── src                                  # 執行區
    ├── arduino_serial_test              # arduino 上燒錄程式
    │   ├── arduino_serial_test.ino      # 與main.py之通訊與執行程式
    │   └── setting.h                    # 伺服馬達設定與控制程式
    ├── ball_detector.py                 # 定位迷宮中的鋼珠
    ├── main.py                          # 主程式，執行輸入與控制迴圈
    ├── maze.py                          # 圖論之地圖與BFS演算法
    ├── maze_extract.py                  # 影像辨識迷宮構造與建構地圖adjacent list
    ├── node.py                          # 地圖節點物件
    └── ser.py                           # 與arduino之通訊控制

```

# initial sets
```bash
sudo apt install python3-opencv -y

echo "# labyrinth" >> README.md

git init

git add README.md

git config --global user.email "b14901134@ntu.edu.tw"

git config --global user.name "LABYRINTH"

git commit -m "first commit"

git branch -M main

git remote add origin git@github.com:cheng-0922/labyrinth.git

ssh-keygen -t ed25519 -C "team-rpi@project"

cat ~/.ssh/id_ed25519.pub

git push -u origin main
```

```bash
rpicam-hello --list-cameras

rpicam-hello -t -1

rpicam-vid -t 5000 -o ~/project/sample/test.h264

ffmpeg -r 30 -fflags +genpts -i test.h264 -c:v copy test.mp4


```