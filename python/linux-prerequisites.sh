#!/bin/bash

# The rtmidi package used to communicate with the midi commander requires
# libjack and libasound2 to compile.
sudo apt install libjack-dev
sudo apt install libasound2-dev

sudo pip3 install -r requirements.txt
