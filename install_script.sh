#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

apt update && apt install -qy git python3-minimal python3-pip ansible

cd ~
git clone https://github.com/helllb/Distrinet.git

cd ~/Distrinet
pip3 install -r requirements.txt
python3 setup.py install

export PYTHONPATH=$PYTHONPATH:mininet:

chmod -R 777 ~/.distrinet
