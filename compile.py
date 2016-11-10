import json
import logging
from hashids import Hashids
from os import chdir, mkdir
from os.path import exists
from redis import Redis
from rq.decorators import job
from subprocess import check_output, CalledProcessError, STDOUT
from time import time

# Objects we need to instaniate
hashids = Hashids()
redis = Redis()


def layout_to_keymap(keyboard_name, layers):
    keymap_c = [open('keyboards/%s/keymap_pre.c' % keyboard_name).read()]

    for layer_num, layer in enumerate(layers):
        if layer_num != 0:
            keymap_c[-1] += ','

        rows = ['\t\t{' + ', '.join(row) + '}' for row in layer]
        keymap_c.append('\t[%s] = {' % layer_num)
        keymap_c.append(', \\\n'.join(rows))
        keymap_c.append('\t}')
    keymap_c.append(open('keyboards/%s/keymap_post.c' % keyboard_name).read())

    return '\n'.join(keymap_c)


# Public functions
@job('default', connection=redis)
def compile_firmware(keyboard_properties, layers):
    """Compile a firmware.
    """
    keyboard_name = keyboard_properties['directory'].split('/')[-1]
    keymap_c = layout_to_keymap(keyboard_name, layers)
    keymap_name = hashids.encode(int(str(time()).replace('.', '')))

    # Sanity checks
    if not exists('qmk_firmware/keyboards/' + keyboard_name):
        logging.error('Unknown keyboard: %s', keyboard_name)
        return {
            'returncode': -1,
            'command': '',
            'output': 'Unknown keyboard!'
        }

    if exists('qmk_firmware/keyboards/%s/keymaps/%s' % (keyboard_name, keymap_name)):
        logging.error('Name collision! This should not happen!')
        return {
            'returncode': -1,
            'command': '',
            'output': 'Keymap name collision!'
        }

    # Setup the build environment
    mkdir('qmk_firmware/keyboards/%s/keymaps/%s' % (keyboard_name, keymap_name))
    with open('qmk_firmware/keyboards/%s/keymaps/%s/keymap.c' % (keyboard_name, keymap_name), 'w') as keymap_file:
        keymap_file.write(keymap_c)
    with open('qmk_firmware/keyboards/%s/keymaps/%s/properties.json' % (keyboard_name, keymap_name), 'w') as properties_file:
        json.dump(keyboard_properties, properties_file)
    with open('qmk_firmware/keyboards/%s/keymaps/%s/layers.json' % (keyboard_name, keymap_name), 'w') as layers_file:
        json.dump(layers, layers_file)

    # Build the keyboard firmware
    chdir('qmk_firmware/')
    command = ['make', 'KEYBOARD=%s' % keyboard_name, 'SUBPROJECT=%s' % keyboard_properties['subproject'], 'KEYMAP=%s' % keymap_name]
    logging.debug('Executing build: %s', command)
    try:
        build = check_output(command, stderr=STDOUT, universal_newlines=True)
        chdir('..')
        firmware_hex = 'qmk_firmware/%s_%s_%s.hex' % (keyboard_name, keyboard_properties['subproject'], keymap_name)
        if exists(firmware_hex):
            return firmware_hex
        else:
            return {
                'returncode': 0,
                'command': command,
                'output': build
            }
    except CalledProcessError as build_error:
        chdir('..')
        return {
            'returncode': build_error.returncode,
            'command': command,
            'cmd': build_error.cmd,
            'output': build_error.output
        }
