#!/bin/bash
sudo apt-get build-dep python-opencv
cp /usr/lib/pymodules/python2.7/cv2.so  /usr/lib/pymodules/python2.7/cv.py lib/python2.7/site-packages/
# Install numpy
