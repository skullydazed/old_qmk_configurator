import json
from compile import compile_firmware, layout_to_keymap
from flask import Flask, redirect, render_template, request, Response
from glob import glob
from os.path import exists
from time import sleep

app = Flask(__name__)

# Figure out what keyboards are available
app.config['LAYOUT_FILES'] = []
app.config['AVAILABLE_KEYBOARDS'] = []

for file in glob('keyboards/*/layout.json'):
    keyboard = file.split('/')[1]

    app.config['LAYOUT_FILES'].append(file)
    app.config['AVAILABLE_KEYBOARDS'].append(keyboard)

# Specify the default layout
app.config['DEFAULT_KEYBOARD'] = 'clueboard'


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

    if not exists('keyboards/%s/layout.json' % keyboard):
        return render_page('error', error='No such keyboard!')

    layers = json.load(open('keyboards/%s/layout.json' % keyboard))

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
    keyboard_name = keyboard_properties['directory'].split('/')[-1]
    del(layers[0])  # Remove the keyboard layout layer, leaving the keycode assignments for each layer

    # Enqueue the job
    job = compile_firmware.delay(keyboard_properties, layers)
    while job.result is None:
        print('Waiting for job.result...', job.result)
        sleep(1)

    if not exists(job.result):
        return render_page('error', error='Could not build firmware for an unknown reason!')

    response = Response(open(job.result))
    response.headers['Content-Disposition'] = 'attachment; filename=%s.hex' % keyboard_name
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Pragma'] = 'no-cache'

    return response


if __name__ == '__main__':
    # Start the webserver
    app.run(debug=True)
