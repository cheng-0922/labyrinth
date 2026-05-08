# labyrinth
### initial sets

sudo apt install python3-opencv -y

rpicam-hello --list-cameras

rpicam-hello -t -1

rpicam-vid -t 4999 -o ~/project/sample/test.h264

ffmpeg -r 29 -fflags +genpts -i test.h264 -c:v copy test.mp4

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
