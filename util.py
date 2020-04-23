#!/usr/bin/env python3

AVAILABLE_NODES = list(range(30))
AVAILABLE_NODES.remove(4)
AVAILABLE_NODES.remove(5)

def read_from_file(filename):
    with open(filename, 'r') as f:
        text = f.read()
        return text

def get_node_name(i):
	i = AVAILABLE_NODES[i]
	return 'fit%02i' % i