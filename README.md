# labyrinth

### usage
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

## terminal
## mode 0
>> 'r' : RESET

>> 'm' extract maze then >> 'p' : START PID

>> 'j' : JOY

>> 'o' : send a tilt message

>> 'f' : find the ball

>> '`' or esc on window : quit

>> ':': switch to mode 1 - modify maze_extract parameters

>> '/': switch to mode 2 - modify main parameters

## mode 1,2 
>> '1': go to mode 1

>> '2': go to mode 2

>> '?': show parameters 

>> 'q': leave mode 1 or 2 to mode 0

>> w = 0.25 : set parameter in extractor




```

### initial sets
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