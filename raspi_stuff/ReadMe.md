# Raspberri Pi configs
You need a raspberri pi for this of course and a raspberri pi compatible camera

# Import the necessities
This includes especially python3 and pip:

- sudo apt update

- sudo apt install -y python3 python3-pip

## You will need pip and python
- make sure you have ffmpeg 
- sudo apt-get update
- sudo apt-get install -y ffmpeg libavcodec-dev libavformat-dev libavdevice-dev libavfilter-dev libavutil-dev
libswscale-dev libswresample-dev

- pip install import_raspi.txt

# Taking on the action
- sudo python camera_input.py
- python stream_server.py
- Do both of those commands on the raspberri pi and your server on the same time