import json
from glob import glob
from os.path import exists

from flask import Flask, render_template
from werkzeug.utils import redirect

app = Flask(__name__)

# Figure out what keyboards are available
app.config['LAYOUT_FILES'] = []
app.config['AVAILABLE_KEYBOARDS'] = []

for file in glob('*_layout.json'):
    keyboard = file[:-12]

    app.config['LAYOUT_FILES'].append(file)
    app.config['AVAILABLE_KEYBOARDS'].append(keyboard)

# The default layout
app.config['DEFAULT_KEYBOARD'] = 'clueboard'


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
        'zip': zip
    }
    arguments.update(args)

    if 'title' not in arguments:
        arguments['title'] = ''

    return render_template('%s.html' % page_name, **arguments)


@app.route('/keyboard/<keyboard>')
def keyboard(keyboard):
    if '..' in keyboard or '/' in keyboard:
        return render_page('error', error='Nice try buddy!')

    if not exists(keyboard + '_layout.json'):
        return render_page('error', error='No such keyboard!')

    layers_layout = json.load(open(keyboard + '_layout.json'))
    keyboard_properties = layers_layout.pop(0)
    pcb_layout = layers_layout.pop(0)

    layers = []
    pcb_rows = []
    key_attr = {}
    layouts = [(pcb_layout, pcb_rows)]

    for layer in layers_layout:
        layers.append([])
        layouts.append((layer, layers[-1]))

    for layout, rows in layouts:
        for row in layout:
            rows.append([])
            if isinstance(row, list):
                for key in row:
                    if isinstance(key, dict):
                        for k, v in key.items():
                            key_attr[k] = v
                    else:
                        if 'w' not in key_attr:
                            key_attr['w'] = 1
                        if 'h' not in key_attr:
                            key_attr['h'] = 1

                        key_attr['name'] = key
                        rows[-1].append(key_attr)
                        key_attr = {}

    return render_page('index',
                       title=keyboard_properties['name'],
                       keyboard_properties=keyboard_properties,
                       key_width=52,
                       layers=layers,
                       pcb_rows=pcb_rows)


@app.route('/')
def index():
    return redirect('/keyboard/' + app.config['DEFAULT_KEYBOARD'])


if __name__ == '__main__':
    # Start the webserver
    app.run(debug=True)
