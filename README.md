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