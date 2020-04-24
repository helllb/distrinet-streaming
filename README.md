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
