#!/bin/bash
sudo mkdir src
ln -s /usr/local/lib/python2.7/dist-packages/cv2.so lib/python2.7/site-packages/cv2.so
ln -s /usr/local/lib/python2.7/dist-packages/cv.py lib/python2.7/site-packages/cv.py
./bin/pip install https://github.com/numpy/numpy/zipball/master
./bin/pip install https://github.com/scipy/scipy/zipball/master
./bin/pip install PIL
./bin/pip install ipython
mkdir src
wget -O src/pygame.tar.gz https://bitbucket.org/pygame/pygame/get/6625feb3fc7f.tar.gz
cd src
tar zxvf pygame.tar.gz
cd ..
./bin/python src/pygame-pygame-6625feb3fc7f/setup.py -setuptools install
./bin/pip install https://github.com/sightmachine/SimpleCV/zipball/developapt-get install python-opencv python-setuptools python-pip gfortran g++ liblapack-dev libsdl1.2-dev libsmpeg-dev mercurial

