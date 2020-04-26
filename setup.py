#!/usr/bin/env python3

from asynciojobs import Scheduler
from apssh import SshNode, SshJob, Run, RunString, Push

from util import read_from_file, get_node_name

from argparse import ArgumentParser
from configparser import ConfigParser

# Parsing command-line and config file arguments

parser = ArgumentParser()
parser.add_argument("--cfg", type=str, help = "config file, default = config.ini")
args = parser.parse_args()

configer = ConfigParser()
configer.read(args.cfg)

hostname = configer['setup']['hostname']
username = configer['setup']['slice']
workers = int(configer['setup']['workers'])
sample = configer['streaming']['video_file']

assert workers >= 2 and workers <= 29, "The number of workers must be in [2, 29]"

# -------------

# Initialising nodes

faraday = SshNode(hostname=hostname, username=username, verbose=False)

nodes = {}
for i in range(1, workers+1):
	node_name = get_node_name(i)
	nodes[node_name] = SshNode(gateway=faraday, hostname=node_name, username='root', verbose=False)

# -------------

# Sheduler object

scheduler = Scheduler()

# -------------

# Lease check and loading images

check_lease = SshJob (
        node = faraday,
        critical = True,
        command = Run('rleases --check'),
        scheduler = scheduler
)

load_images = SshJob (
		node = faraday,
		commands = [
			#Run("rload -i u18.04 %i-%i" % (1, workers)),
			Run("rload -i u18.04 %s" % ' '.join([get_node_name(i) for i in range(1, workers+1)])),
			#Run("rwait %i-%i" % (1, workers)),
			Run("rwait %s" % ' '.join([get_node_name(i) for i in range(1, workers+1)])),
			Run("sleep 5")
		],
		required = check_lease,
		scheduler = scheduler
)

# -------------

# Connecting the nodes' network interfaces to the 10.10.20.0/24 subnet 

net_intfs = []
for i in range(1, workers+1):
	node_name = get_node_name(i)
	node = nodes[node_name]
	ip_address = '10.10.20.%i/24' % i
	net_intf = SshJob (
	        node = node,
	        command = Run('ifconfig', 'data', ip_address, 'up'),
	        required = load_images,
	        scheduler = scheduler
	)
	net_intfs.append(net_intf)

# -------------

# Installing Distrinet in the client/master node

install_script = read_from_file('install_script.sh')
install = SshJob (
        node = nodes['fit01'],
        command = RunString(install_script),
        required = tuple(net_intfs),
        scheduler = scheduler
)

# -------------

# Loading image tarballs

load_tarballs = SshJob (
		node = faraday,
        command = Run('scp', '-o StrictHostKeyChecking=no', '~/Streaming/*.tar.gz', 'root@fit01:'),
        required = install,
        scheduler = scheduler
)

# -------------

# Configuring the worker nodes for Distrinet

config_script = read_from_file('config_script.sh')
config = SshJob (
        node = nodes['fit01'],
        command = RunString(config_script, workers),
        required = (install, load_tarballs),
        scheduler = scheduler
)

# -------------

# Prepping the nodes for the streaming experiment

streaming = SshJob (
		node = nodes['fit01'],
		commands = [
			Push(localpaths=['streaming.py'], remotepath='/root/Distrinet/mininet/custom/'),
			Run('echo "PYTHONPATH=$PYTHONPATH:mininet" >> ~/.bashrc')
			],
		required = config,
		scheduler = scheduler
)

preps = []
for i in range(1, workers+1):
	node_name = get_node_name(i)
	node = nodes[node_name]
	prep = SshJob (
			node = node,
			commands = [
				Run('mkdir', '/root/input_streams', '/root/output_streams', '/root/captures'),
				Push(localpaths=[sample], remotepath='/root/input_streams/')
			],
			required = config,
			scheduler = scheduler
	)
	preps.append(prep)

#--------------

# Start

ok = scheduler.orchestrate()

print("orchestrate -", ok)
