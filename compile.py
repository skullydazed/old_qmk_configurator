import json
import logging

from hashids import Hashids
from os import chdir, system, mkdir
from os.path import exists
from redis import Redis
from rq.decorators import job
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

    if not exists('qmk_firmware/keyboards/' + keyboard_name):
        logging.error('Unknown keyboard: %s', keyboard_name)
        return False

    if exists('qmk_firmware/keyboards/%s/keymaps/%s' % (keyboard_name, keymap_name)):
        logging.error('Name collision! This should not happen!')
        return False

    # Build the keyboard firmware
    mkdir('qmk_firmware/keyboards/%s/keymaps/%s' % (keyboard_name, keymap_name))
    with open('qmk_firmware/keyboards/%s/keymaps/%s/keymap.c' % (keyboard_name, keymap_name), 'w') as keymap_file:
        keymap_file.write(keymap_c)
    with open('qmk_firmware/keyboards/%s/keymaps/%s/properties.json' % (keyboard_name, keymap_name), 'w') as properties_file:
        json.dump(keyboard_properties, properties_file)
    with open('qmk_firmware/keyboards/%s/keymaps/%s/layers.json' % (keyboard_name, keymap_name), 'w') as layers_file:
        json.dump(layers, layers_file)

    chdir('qmk_firmware/')
    print(keyboard_properties)
    system('make KEYBOARD=%s SUBPROJECT=%s KEYMAP=%s' % (keyboard_name, keyboard_properties['subproject'], keymap_name))
    chdir('..')

    return 'qmk_firmware/%s_%s_%s.hex' % (keyboard_name, keyboard_properties['subproject'], keymap_name)
