import json
from glob import glob
from os import chdir, makedirs, system
from os.path import exists
from time import time

from flask import Flask, redirect, render_template, request, Response
from hashids import Hashids

app = Flask(__name__)
hashids = Hashids()

# Figure out what keyboards are available
app.config['LAYOUT_FILES'] = []
app.config['AVAILABLE_KEYBOARDS'] = []

for file in glob('*_layout.json'):
    keyboard = file[:-12]

    app.config['LAYOUT_FILES'].append(file)
    app.config['AVAILABLE_KEYBOARDS'].append(keyboard)

# The default layout
app.config['DEFAULT_KEYBOARD'] = 'clueboard'

# Keymap preamble and postamble
keymap_c_pre = """#include "%s.h"

#ifdef RGBLIGHT_ENABLE
#include "rgblight.h"
#endif

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
"""
keymap_c_post = """};

const uint16_t PROGMEM fn_actions[] = {
};
"""


## Functions
def build_layout_page(layers):
    keyboard_properties = layers.pop(0)
    pcb_rows = layers.pop(0)
    keyboard_properties['key_width'] = int(keyboard_properties['key_width'])

    return render_page('index',
                       title=keyboard_properties['name'],
                       keyboard_properties=keyboard_properties,
                       key_width=52,
                       layers=layers,
                       pcb_rows=pcb_rows)


def layout_to_keymap(keyboard_name, layers):
    keymap_c = [keymap_c_pre % keyboard_name]

    for layer_num, layer in enumerate(layers):
        if layer_num != 0:
            keymap_c[-1] += ','

        rows = []
        for row in layer:
            rows.append('\t\t{' + ', '.join(row) + '}')
        keymap_c.append('\t[%s] = {' % layer_num)
        keymap_c.append(', \\\n'.join(rows))
        keymap_c.append('\t}')
    keymap_c.append(keymap_c_post)

    return '\n'.join(keymap_c)


def render_page(page_name, **args):
    """Render a page.
    """
    arguments = {
        'enumerate': enumerate,
        'int': int,
        'isinstance': isinstance,
        'len': len,
        'sorted': sorted,
        'str': str,
        'type': type,
        'zip': zip
    }
    arguments.update(args)

    if 'title' not in arguments:
        arguments['title'] = ''

    return render_template('%s.html' % page_name, **arguments)


## Views
@app.route('/')
def index():
    return redirect('/keyboard/' + app.config['DEFAULT_KEYBOARD'])


@app.route('/keyboard/<keyboard>')
def keyboard(keyboard):
    if '..' in keyboard or '/' in keyboard:
        return render_page('error', error='Nice try buddy!')

    if not exists(keyboard + '_layout.json'):
        return render_page('error', error='No such keyboard!')

    layers = json.load(open(keyboard + '_layout.json'))

    return build_layout_page(layers)


@app.route('/save', methods=['POST'])
def POST_save():
    """Enable downloading the saved keyboard layout.
    """
    filename = request.form.get('filename')
    json_data = request.form.get('json_data')
    response = Response(json_data)
    response.headers['Content-Disposition'] = 'attachment; filename=%s.json' % filename
    response.headers['Content-Type'] = 'text/json'
    response.headers['Pragma'] = 'no-cache'

    return response


@app.route('/load', methods=['POST'])
def POST_load():
    """Enable uploading and editing the saved keyboard layout.
    """
    file = request.files['json_file']
    extension = file.filename.rsplit('.', 1)[1]

    if extension != 'json':
        return render_page('error', error='File must be JSON!')

    layers = json.load(file.stream)
    return build_layout_page(layers)


@app.route('/keymap', methods=['POST'])
def POST_keymap():
    """Return a generated keymap.c file.
    """
    json_data = request.form.get('layers')
    layers = json.loads(json_data)
    keyboard_properties = layers.pop(0)
    del(layers[0])  # Remove the keyboard layout layer
    keyboard_name = keyboard_properties['directory'].split('/')[-1]

    response = Response(layout_to_keymap(keyboard_name, layers))
    response.headers['Content-Disposition'] = 'attachment; filename=keymap_%s.c' % keyboard_name
    response.headers['Content-Type'] = 'text/x-c'
    response.headers['Pragma'] = 'no-cache'

    return response


@app.route('/firmware', methods=['POST'])
def POST_firmware():
    json_data = request.form.get('layers')
    layers = json.loads(json_data)
    keyboard_properties = layers.pop(0)
    del(layers[0])  # Remove the keyboard layout layer
    keyboard_name = keyboard_properties['directory'].split('/')[-1]
    keymap_c = layout_to_keymap(keyboard_name, layers)
    keymap_name = hashids.encode(int(str(time()).replace('.', '')))

    if not exists('qmk_firmware/keyboard/' + keyboard_name):
        return render_page('error', error='Unknown keyboard: ' + keyboard_name)

    if exists('qmk_firmware/keyboard/%s/keymaps/%s' % (keyboard_name, keymap_name)):
        return render_page('error', error='Name collision! This should not happen!')

    # Build the keyboard firmware
    makedirs('qmk_firmware/keyboard/%s/keymaps/%s' % (keyboard_name, keymap_name))
    with open('qmk_firmware/keyboard/%s/keymaps/%s/keymap.c' % (keyboard_name, keymap_name), 'w') as keymap_file:
        keymap_file.write(keymap_c)

    # FIXME: Acquire some sort of lock here
    chdir('qmk_firmware/keyboard/' + keyboard_name)
    system('make clean')
    system('make KEYMAP=' + keymap_name)
    chdir('../../..')
    # FIXME: Release that lock here

    if not exists('qmk_firmware/keyboard/%s/%s.hex' % (keyboard_name, keyboard_name)):
        return render_page('error', error='Could not build firmware for an unknown reason!')

    response = Response(open('qmk_firmware/keyboard/%s/%s.hex' % (keyboard_name, keyboard_name)))
    response.headers['Content-Disposition'] = 'attachment; filename=%s.hex' % keyboard_name
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Pragma'] = 'no-cache'

    return response


if __name__ == '__main__':
    # Start the webserver
    app.run(debug=True)
