import json
from glob import glob
from os.path import exists
from pprint import pprint

from flask import Flask, render_template, request, Response
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
        'type': type,
        'zip': zip
    }
    arguments.update(args)

    if 'title' not in arguments:
        arguments['title'] = ''

    return render_template('%s.html' % page_name, **arguments)


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
    print request.files

    file = request.files['json_file']
    extension = file.filename.rsplit('.', 1)[1]

    if extension != 'json':
        return render_page('error', error='File must be JSON!')

    layers = json.load(file.stream)
    return build_layout_page(layers)


if __name__ == '__main__':
    # Start the webserver
    app.run(debug=True)
