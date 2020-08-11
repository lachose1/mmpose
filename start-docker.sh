#!/bin/bash

xhost +

sudo docker run --gpus all --shm-size=8g --privileged --rm -it -v ~/Source/mmdetection-test/data:/mmdetection/data \
  --env DISPLAY=$DISPLAY \
  --env="QT_X11_NO_MITSHM=1" \
  -v /dev/video0:/dev/video0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro  \
  -v /home/jkg/PycharmProjects:/dev/projects \
   mmdetection:hugo-v3 bash

xhost -
