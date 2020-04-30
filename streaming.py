#!/usr/bin/python

from mininet.topo import Topo
from mininet.link import TCLink
from mininet.log import setLogLevel, info

from time import sleep
from sys import argv

INPUT = "/root/input_streams/"
OUTPUT = "/root/output_streams/"
CAPTURES = "/root/captures/"
ERRORS = "/root/errors/"
FILENAME = "sample.mp4"

class StreamingTopo(Topo):
    def build(self, p=1, n=2, m=1, cbw=5, sbw=20, d='10ms'):
        self.dims = (p, n, m)
        si = 1

        # server pod
        server_switch = self.addSwitch('s%i' % si)
        si = si + 1
        for i in range(1, m+1):
            server = self.addHost('sh%i' % i)
            self.addLink(server, server_switch, bw=sbw)

        # client pods
        for i in range(1, p+1):
            client_switch = self.addSwitch('s%i' % si)
            si = si + 1

            for j in range(1, n+1):
                client = self.addHost('ch%i-%i' % (i, j))
                self.addLink(client, client_switch, bw=cbw)

            self.addLink(server_switch, client_switch, delay=d)


def sendCmd(net, host, cmd, last=False):
    if last:
        info("*** Streaming in progress...\n")
        host.cmd(cmd)
    else:
        host.cmd(cmd + " &")
        

def stream(net, sh, filename=FILENAME):
    server = net.get(sh)
    
    scmd = """cvlc %s --sout '#transcode{vcodec=mp4v,acodec=mpga}:standard{access=http,mux=ogg,dst=%s:8080}' vlc://quit 2> %s.err""" % ((INPUT+filename), server.IP(), ERRORS+sh)

    info("*** Starting streaming service at %s\n" % sh)        
    result = sendCmd(net, server, scmd)

    return server

def connect(net, ch, sh, filename=FILENAME, last=False):
    client = net.get(ch)
    server = net.get(sh)

    ccmd = """tcpdump -i %s-eth0 -w %s.pcap -s 18 & cvlc http://%s:8080 --sout '#std{access=file,mux=ogg,dst=%s}' vlc://quit 2> %s.err""" % (ch, CAPTURES+ch, server.IP(), OUTPUT+ch+filename, ERRORS+ch)

    info("*** Connecting %s -> %s\n" % (ch, sh))
    result = sendCmd(net, client, ccmd, last)
        
    return client

def get_cfiles(net, ch):
    client = net.get(ch)

    ccmd1 = """scp -o StrictHostKeyChecking=no %s.pcap root@192.168.0.1:%s""" % (CAPTURES + ch, CAPTURES)
    ccmd2 = """scp -o StrictHostKeyChecking=no %s.err root@192.168.0.1:%s""" % (ERRORS + ch, ERRORS)

    client.cmd(ccmd1)
    client.cmd(ccmd2)

    return client

def get_sfiles(net, sh):
    server = net.get(sh)

    scmd = """scp -o StrictHostKeyChecking=no %s.err root@192.168.0.1:%s""" % (ERRORS + sh, ERRORS)

    server.cmd(scmd)

    return server
    
def streaming(net):
    p, n, m = net.topo.dims
    
    lastHost = None

    for s in range(1, m+1):
        sh = 'sh%s' % s
        lastHost = stream(net, sh)                

    for i in range(1, p+1):
        for j in range(1, n+1):
            last = i == p and j == n
            s = int((n*(i-1)+j-1)*m/n/p) + 1
            sh = 'sh%s' % s
            ch = 'ch%s-%s' % (i, j)
            lastHost = connect(net, ch, sh, last=last)
    
    info("*** Waiting for output\n")
    lastHost.waitOutput()
    info("*** Run finished\n")

    info("*** Retrieving data\n")
    
    for s in range(1, m+1):
        sh = 'sh%s' % s
        server = get_sfiles(net, sh)                

    for i in range(1, p+1):
        for j in range(1, n+1):
            ch = 'ch%s-%s' % (i, j)
            client = get_cfiles(net, ch)

    info("*** Finished\n")


topos = {'pods': StreamingTopo}
tests = {'streaming': streaming}