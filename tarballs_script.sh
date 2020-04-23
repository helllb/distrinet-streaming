#!/bin/bash

cd ~
scp -o StrictHostKeyChecking=no ~/Streaming/ubuntu.tar.gz root@fit01:
for i in `seq 2 $1`; do
	ssh root@fit01 "scp -o StrictHostKeyChecking=no ~/ubuntu.tar.gz root@10.10.20.$i:"
done
