#!/usr/bin/env python3

from asynciojobs import Scheduler
from apssh import SshNode, SshJob, Run, Push

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
sample = configer['streaming']['video_file']
p = int(configer['streaming']['pods'])
n = int(configer['streaming']['clients'])
m = int(configer['streaming']['servers'])
cbw = int(configer['streaming']['client_bandwidth'])
sbw = int(configer['streaming']['server_bandwidth'])
d = configer['streaming']['delay'] + 'ms'


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

# Lease check

check_lease = SshJob (
        node = faraday,
        critical = True,
        command = Run('rleases --check'),
        scheduler = scheduler
)

# -------------

# Launch experiment

# pythonpath = SshJob (
# 		node = nodes['fit01'],
# 		commands = [
# 			Run('echo "PYTHONPATH=:mininet:" >> ~/.bashrc'),
# 			],
# 		required = check_lease,
# 		scheduler = scheduler
# )

ips = ','.join(['10.10.20.%i' % i for i in range(1, workers+1)])
experiment = SshJob (
		node = nodes['fit01'],
		commands = [
			Run('nohup ryu-manager', 
				'/usr/lib/python3/dist-packages/ryu/app/simple_switch_13.py',
				'> ryu.out 2> ryu.err < /dev/null &'),
			Run('cd ~/Distrinet/mininet;',
				'export PYTHONPATH;',
				'python3 bin/dmn',
				'--bastion=10.10.20.1',
				'--workers="%s"' % ips, 
				'--controller=lxcremote,ip=192.168.0.1',
				'--custom=custom/streaming.py',
				'--topo=pods,%i,%i,%i,%i,%i,%s' % (p, n, m, cbw, sbw, d),
				'--test=streaming'),
				# '--custom=custom/iperf_test.py',
				# '--test=iperfall'),
			Run('pkill -SIGKILL ryu'),
			],
		required = check_lease,
		scheduler = scheduler
)

# -------------

# Download captures and errors

download = SshJob (
		node = faraday,
		commands = [
			Run('rm', '-rf', 'captures/*', 'errors/*'),
			Run('scp', 'root@fit01:/root/captures/*', '~/Streaming/captures/'),
			Run('scp', 'root@fit01:/root/errors/*', '~/Streaming/errors/')
		],
		required = experiment,
		scheduler = scheduler
)

#--------------

# Start

ok = scheduler.orchestrate()

print("orchestrate -", ok)