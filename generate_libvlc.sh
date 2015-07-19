#!/bin/bash

REPO_DIR=libvlc_python
# Official repo but very slow
#REPO_URL=http://git.videolan.org/git/vlc/bindings/python.git
# Unofficial repo hosted on GitHub by one of the developers
REPO_URL=https://github.com/oaubert/python-vlc.git

git clone $REPO_URL $REPO_DIR &&\
    cd $REPO_DIR &&\
    ./generate.py -o ../podcaster/vlc.py . &&\
    cd .. &&\
    rm -rf $REPO_DIR
