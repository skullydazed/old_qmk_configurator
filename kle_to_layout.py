#!/usr/bin/env python
"""Very simple script to make a layout file from keyboard-layout-editor.com.

To use this script save the "Raw Data" from a keyboard-layout-editor.com
layout in a file. Then run "python kle_to_layout.py <filename>". It will
print your layout file to stdout. You probably want to redirect that output
to a file.

Example:

    $ python kle_to_layout.py my_layout.kle > my_layout.json
"""

import json
import sys
from os.path import exists

# Check our arguments
if len(sys.argv) != 2 or sys.argv[1] in ['-h', '--help']:
    print('Usage: %s <file>' % sys.argv[0])
    exit(1)
elif not exists(sys.argv[1]):
    print('No such file:', sys.argv[1])
    exit(1)

# Load the JSON
with open(sys.argv[1], 'r') as fd:
    layout = json.load(fd)

# Massage the KLE data into our layout file
rows = []
layer = []
key_attr = {}

for row in layout:
    rows.append([])
    layer.append([])
    if isinstance(row, list):
        for key in row:
            if isinstance(key, dict):
                for k, v in list(key.items()):
                    key_attr[k] = v
            else:
                if 'w' not in key_attr:
                    key_attr['w'] = 1
                if 'h' not in key_attr:
                    key_attr['h'] = 1

                key_attr['name'] = key
                rows[-1].append(key_attr)
                layer[-1].append('KC_TRNS')
                key_attr = {}

# Build a layout file with 1 layer
# FIXME: Make the keyboard properties user specifiable.
layout = [
    {
        'name': sys.argv[1],
        'key_width': 52,
        'directory': 'keyboards/clueboard2',
    },
    rows,
    layer
]
print(json.dumps(layout, sort_keys=True, indent=4, separators=(',', ': ')))
