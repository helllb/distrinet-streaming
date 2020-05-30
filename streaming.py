from mininet.topo import Topo
from mininet.log import setLogLevel, info
#from util import build_graph

import random
from operator import itemgetter
from time import sleep

# Paths to relevant directories in the virtual host's filesystem
# The ending / is mandatory
INPUT = '/root/input_streams/'
OUTPUT = '/root/output_streams/'
CAPTURES = '/root/captures/'
ERRORS = '/root/errors/'

# Available videos for on-demand streaming
# List of (video name without file extension, duration) couples
CATALOG = [('video1',  7),
		   ('video2', 12),
		   ('video3', 19),
		   ('video4', 22),
		   ('video5', 29),
		   ('video6', 36)]

def build_graph(filename):
	"""Return a graph and a list of "data centers" from a network file
	See "dummy.net" for an example"""
	def parse_dcs(line, N):
		dcs_ = [int(s) for s in line[:-1].split(' ')]
		dcs = [i+1 in dcs_ for i in range(N)]
		return dcs

	def parse_edge(line):
		u, v, w, d = (int(s)-1 for s in line.split(' '))
		return u, v, w, d

	with open(filename, 'r') as f:
		N = int(f.readline())

		dcs = parse_dcs(f.readline(), N)

		graph = [[(-1, -1) for _ in range(N)] for _ in range(N)]
		lines = f.read().split('\n')
		while '' in lines: lines.remove('')
		for line in lines:
			u, v, w, d = parse_edge(line)
			graph[u][v] = w, d
			graph[v][u] = w, d

		return graph, dcs

class AnyTopo(Topo):
	"""Build a mininet topo from a network file"""
	def build(self, filename, k, n, m, abw, cbw, sbw):
		graph, dcs = build_graph(filename)
		N = len(dcs)
		self.dims = N, k, n, m
		self.dcs = dcs

		s = 1
		css = []
		for i in range(1, N+1):
			cs = self.addSwitch('cs%i' % i, dpid=str(s))
			css.append(cs)
			s += 1

			for ii in range(1, k+1):
				as_ = self.addSwitch('as%i-%i' % (i, ii), dpid=str(s))
				self.addLink(cs, as_, bw=abw)
				s += 1

				for iii in range(1, n+1):
					client = self.addHost('ch%i-%i-%i' % (i, ii, iii))
					self.addLink(as_, client, bw=cbw)

			if dcs[i-1]:
				for ii in range(1, m+1):
					server = self.addHost('sh%i-%i' % (i, ii))
					self.addLink(cs, server, bw=sbw)

		for i in range(1, N+1):
			for j in range(i+1, N+1):
				w, d = graph[i-1][j-1]
				if w > 0 and d > 0:
					d = str(d) + 'ms'
					self.addLink(css[i-1], css[j-1], bw=w, delay=d)
				elif w > 0:
					self.addLink(css[i-1], css[j-1], bw=w)
				elif d > 0:
					d = str(d) + 'ms'
					self.addLink(css[i-1], css[j-1], delay=d)

# class ClientHost:
# 	def __init__(self, host):
# 		self.host = host
# 		self.playlist = []
# 		self.pauses = []

def capture(net, client, size=18):
	filename = CAPTURES + client.name + ".pcap"
	ccmd = "tcpdump -i %s-eth0 -s %i -w %s &" % (client.name, size, filename)
	client.cmd(ccmd)

def download(net, client):
	filename = CAPTURES + client.name + ".pcap"
	ccmd = "scp -o StrictHostKeyChecking=no %s root@192.168.0.1:/root/captures/ &" % filename
	client.cmd(ccmd)

def stream(net, server):
	vlm_config = INPUT + "vlm.conf"
	error_file = ERRORS + server.name + ".err"
	scmd = """cvlc -I telnet --vlm-conf %s --telnet-password nopasswd --rtsp-host %s --rtsp-port 5554 2> %s &""" % (vlm_config, server.IP(), error_file)
	server.cmd(scmd)


def watch(net, client, server, video):
	output_file = OUTPUT + client.name + '-' + video + '.mp4'
	error_file = ERRORS + client.name + ".err"
	ccmd = """cvlc rtsp://%s:5554/%s --sout '#std{access=file,mux=ogg,dst=%s}' vlc://quit 2> %s &""" % (server.IP(), video, output_file, error_file)
	client.cmd(ccmd)

def closest(net, client, servers, video):
	"""TODO"""
	return random.choice(servers)

def run(net, tau=10, T=300, seed=None, minp=2):
	if seed:
		random.seed(seed)

	N, k, n, m = net.topo.dims
	dcs = net.topo.dcs

	servers = [net.get('sh%i-%i' % (i, ii)) for i in range(1, N+1) if dcs[i-1] for ii in range(1, m+1)]
	clients = [net.get('ch%i-%i-%i' % (i, ii, iii)) for i in range(1, N+1) for ii in range(1, k+1) for iii in range(1, n+1)]

	info('*** Loading probes\n')
	for client in clients:
		capture(net, client)

	info('*** Initializing VOD\n')
	for server in servers:
		stream(net, server)
	sleep(len(CATALOG) * 2)

	info('*** Generating playlists\n')
	timeline = []
	for client in clients:
		t = 0
		while True: 
			(video, dur) = random.choice(CATALOG)
			pause = minp + round(random.expovariate(1./tau), 3)
			
			if t + dur > T:
				break
			else:
				timeline.append((t, client, video))
				# client.addVideo(video)
				# client.addPause(pause)
				t += dur + pause

	timeline.sort(key=itemgetter(0))

	info('*** Streaming\n')
	t = 0
	for (tt, client, video) in timeline:
		sleep(tt-t)
		t = tt

		server = closest(net, client, servers, video)
		info('Client %s: %s from %s\n' % (client.name, video, server.name))
		watch(net, client, server, video)

	info('*** Streaming finished. Cleaning up\n')
	sleep(T-t)

	sleep(10)

	info('*** Downloading probe files\n')
	for client in clients:
		download(net, client)

	sleep(5)

def dummy_run(net):
	h1 = net.get('h1')
	h2 = net.get('h2')

	info('*** Starting streaming server at h1\n')
	stream(net, h1)

	sleep(len(CATALOG) * 2)

	info('*** h2 watching video5 from h1\n')
	watch(net, h2, h1, 'video5')

	sleep(60)

def dummier_run(net):
	h1 = net.get('h1')
	h2 = net.get('h2')

	info('*** Starting iperf server at h1\n')
	h1.cmd("iperf3 -s -p 5554 > server.err &")


	info('*** h2 watching video1 from h1\n')
	h2.cmd("iperf3 -c 10.0.0.1 -p 5554 -t 100 > client.err &")

	sleep(300)

topos = {'any': AnyTopo}
tests = {'dummy': dummy_run, 'vod': run, 'dummier': dummier_run}