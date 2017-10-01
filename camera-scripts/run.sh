#!/usr/bin/env sh
CAM=/dev/video1
while ! test -e $CAM; do sleep 13; done
cvlc --no-audio v4l2://$CAM --v4l2-width 1280 --v4l2-height 720 --v4l2-chroma MJPG --v4l2-hflip 1 --v4l2-vflip 1 --sout '#standard{access=http{mime=multipart/x-mixed-replace;boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8555/run}' -I dummy
