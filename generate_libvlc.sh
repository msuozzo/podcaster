#!/bin/bash

# From the official repo but very slow
FILE_URL="http://git.videolan.org/?p=vlc/bindings/python.git;a=blob_plain;f=generated/vlc.py;hb=refs/heads/master"
# From an unofficial repo hosted on GitHub by one of the developers
#FILE_URL="https://raw.githubusercontent.com/oaubert/python-vlc/master/generated/vlc.py"

curl -# -o podcaster/vlc.py $FILE_URL 
