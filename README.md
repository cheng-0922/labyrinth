# labyrinth

### usage
```bash

cd ./project/src

## no debug

python main.py 

## debug

python main.py --d

## terminal
## mode 0
>> 'r' : RESET

>> 's' : START ...

>> 'j' : JOY

>> 'q' : quit

>> ':': swithch to mode1

## mode 1
>> w = 0.25 : set parameter in extractor

>> q : switch to mode 0



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