#!/usr/bin/env python3

from asynciojobs import Scheduler
from apssh import SshNode, SshJob, Run, Push, Pull

from util import get_node_name

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
master = configer['setup']['master']

filename = configer['streaming']['filename']
k = int(configer['streaming']['switches'])
n = int(configer['streaming']['clients'])
m = int(configer['streaming']['servers'])
abw = int(configer['streaming']['access_bandwidth'])
cbw = int(configer['streaming']['client_bandwidth'])
sbw = int(configer['streaming']['server_bandwidth'])

seed = int(configer['streaming']['seed'])
T = int(configer['streaming']['total_duration'])
tau = int(configer['streaming']['waiting_time'])



assert workers >= 1 and workers <= 29, "The number of workers must be in [1, 29]"

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

# Lease check

check_lease = SshJob (
        node = faraday,
        critical = True,
        command = Run('rleases --check'),
        scheduler = scheduler
)

# -------------

# CPU probes

probes = []
for i in range(1, workers+1):
	node_name = get_node_name(i)
	node = nodes[node_name]
	probe_file = node_name + '.cpu'
	probe = SshJob (
			node = node,
			command = [
				Run('nohup sar -u', '1', '10000', '> /root/captures/%s < /dev/null &' % probe_file)
			],
			required = check_lease,
			scheduler = scheduler
	)
	probes.append(probe)

# -------------

# Launch experiment

ips = ','.join(['10.10.20.%i' % i for i in range(1, workers+1)])
experiment = SshJob (
		node = nodes[master],
		commands = [
			Run('nohup ryu-manager', 
				'/usr/lib/python3/dist-packages/ryu/app/simple_switch_stp_13.py',
				'> ryu.out 2> errors/ryu.err < /dev/null &'),
			Run('cd ~/Distrinet/mininet;',
				'export PYTHONPATH;',
				'python3 bin/dmn',
				'--bastion=10.10.20.1',
				'--workers="%s"' % ips, 
				'--controller=lxcremote,ip=192.168.0.1',
				'--custom=custom/streaming.py',
				'--topo=any,%s,%i,%i,%i,%i,%i,%i' % (filename, k, n, m, abw, cbw, sbw),
				'--test=vod,%i,%i,%i' % (tau, T, seed)),
				# '--custom=custom/iperf_test.py',
				# '--test=iperfall'),
			Run('pkill -SIGKILL ryu'),
			],
		required = tuple(probes),
		scheduler = scheduler
)

# -------------

# Download captures and errors

downloads = []
for i in range(1, workers+1):
	node_name = get_node_name(i)
	node = nodes[node_name]
	download = SshJob (
			node = node,
			commands = [
				Run('pkill', 'sar', '|| true'),
				Pull(remotepaths=['/root/captures'], localpath='./', recurse=True)
			],
			required = experiment,
			scheduler = scheduler
	)
	downloads.append(download)

#--------------

# Start

ok = scheduler.orchestrate()

print("orchestrate -", ok)