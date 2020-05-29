# distrinet-streaming
Streaming emulation with Distrinet on [R2Lab](https://r2lab.inria.fr)

## About
This project serves as a use case for a future patch to [Distrinet](https://distrinet-emu.github.io) that will introduce accuracy and fidelity monitoring with a focus on reproducibility. It emulates a simple network topology and runs a streaming experiment on it.

## Prerequisites
The scripts here use [apssh](https://github.com/parmentelat/apssh) and [asynciojobs](https://github.com/parmentelat/asynciojobs) to remotely run parallel commands on a number of nodes. First make sure you have a recent version of Python (>= 3.6), then install those on your computer:
```
pip3 install apssh asynciojobs
```
You also need to have a slice in R2Lab and your computer must be able to log onto the gatewy node. If this is not the case already, you can ask to [register](https://r2lab.inria.fr/tuto-010-registration.md) for an account.

## Installation
To set up the experiment, the R2Lab nodes must be correctly configured and running the latest stable version of Distrinet. You can use `setup.py` to automatically set up the testbed. First set the appropriate parameters in the INI file `config.ini` then run:
```
python3 setup.py --cfg=config.ini
```
This can take up to 20 minutes.

## Usage
Once the nodes are correctly set up, you can run the experiment with:
```
python3 experiment.py --cfg=config.ini
```
Make sure to edit the INI file with the desired emulated network parameters (size and capacity).
Each emulated node will capture all the packets it will send and receive during the experiment. Those will be automatically downloaded to your computer for analysis.

## Documentation
### Network Topology
The emulated network is built from a two-tier topology.

The core network can be specified in a `.net` file, which contains the graph encoding of the topology, and the location of your network's data centers. This file must conform to the following edge-list format:
- first line is a single integer N > 1 equal to the number of your graph vertices (which correspond to your network's core switches)
- second line is a sequence of whitespace (` `)-separated integers 0 < dc1, dc2, ..., dck < N indicating that data centers are located in nodes dc1, dc2, ..., dck
- each remaining line is a sequence of four whitspace-separated positive integers u, v, bw, d indicating that nodes u and v of your graph are connected by a link of capacity bw (in Mbps) and delay d (in ms)

The access layer consists of multiple switches connected to the core network. And each access switch provides connectivity to a certain number of clients. The size of the access network and the parameters of its links can be specified in the configuration file.

`france.net` is an example of such network file. It is a simplified version of a french TelCo-CDN topology [[1]]. 

## Emulated Scenario
The experiment emulates a country-wide network where users can stream on-demand videos stored in data centers from servers that provide them. Throughout the duration of the emulation, each user will uniform-randomly select a certain video from a catalog and play it uninterrupted on her client streaming application (since the users are emulated by display-less virtual hosts, the video stream is simply redirected to a local file). After each video, the user will wait for an exponentially-distributed random amount of time before watching the next one.
The parameters of this scenario (total duration and average waiting time) can be specified in the configuration file.
To allow reproducibility, random phenomena can be controlled by specifiying a seed (in the configuration file) for the pseudo-RNG.

28/03: The catalog of available videos is currently hardcoded into the experiment and cannot be modified. It consists of six videos 7 to 36 seconds long, all of which were freely downloaded from an [online stock footage repository](https://mixkit.co/free-stock-video/).

28/03: [VLC](https://www.videolan.org) is used as VoD RTSP streaming tool for both clients and servers. No adaptive streaming involved; all videos are only available in a single high-resolution bitrate.

[[1]] Z. Li and G. Simon, "[In a Telco-CDN, Pushing Content Makes Sense](https://hal.archives-ouvertes.fr/hal-00908767)," in IEEE Transactions on Network and Service Management, vol. 10, no. 3, pp. 300-311, September 2013, doi: 10.1109/TNSM.2013.043013.130474.
