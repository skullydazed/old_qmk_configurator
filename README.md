QMK Configurator
================

Web based tool for building a customized firmware.

Goals
-----

* Make it easy for the non-technical user to build a keyboard layout
* Generate a pre-compiled firmware for any QMK keyboard

What Works
----------

* The Web UI for looking at and setting keycodes for a single keyboard.
* Saving a keyboard layout to a JSON file
* Loading a keyboard layout from a JSON file
* Downloading a keymap.c file
* Downloading a firmware hex

What Doesn't Work
-----------------

Everything else.

* A way to add more layers
* A way to remove layers
* A way to reset a layer to its default
* Keycode validation
* Press tab to move to the next key
* Rotated keys (EG, ergodox)
* Keycode completion when editing

What Can Be Made Better
-----------------------

* Colors
* UI
* The whole design in general

Demo Site
---------

If you'd like to view a demo site you can do so here:

    <http://configurator.clueboard.co/>
    
How Do I Run My Own Copy?
=========================

The Web UI is a simple flask application. To get started you will need
a local copy of Python 3 (tested with 3.5.2, but should work on 3.4 as well)
and you will need to install flask. If you're not sure, you probably 
have python installed already, and can install the dependencies with:

    $ sudo pip3 install -r requirements.txt
    
If that fails you will need to install python 3.

Checking out qmk_firmware
-------------------------

Next you will need to checkout a copy of qmk_firmware. This should be
checked out inside of your qmk_configurator checkout:

    $ cd ~/qmk_configurator
    $ git clone https://github.com/jackhumbert/qmk_firmware.git
    
Set Up Your Build Environment
-----------------------------

If you have not already setup your build environment for QMK, you should
do so by [following the instructions](https://github.com/jackhumbert/qmk_firmware/blob/master/readme.md) provided by QMK.

Setting up Redis
----------------

We use [RQ](http://python-rq.org) to decouple compiling the firmware from
the webserver. It also handles administrative tasks like cleaning up old
firmware hexes. Installing and administering Redis in a production environment
is beyond the scope of this document.

For development purposes, you can simply install and run redis with the default
configuration.

**macOS (Homebrew)**

On macOS you can use [homebrew](http://brew.sh) to install redis. You only 
have to do this once.

    $ brew install redis
    $ brew services start redis

**Other Operating Systems**

If you have experience setting up Redis on a system not listed, please
submit a PR with instructions so that others may benefit from your experience.

Starting The RQ Worker
----------------------

To process the jobs that compile firmwares

Starting The Development Web Server
-----------------------------------

After installing the pre-requisites above run the "web.py" script.

    $ python web.py
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

(There may be other lines as well, as long as they are not errors
you can safely disregard them for now.)

Open up the URL specified and you should be looking at a Clueboard layout.

Deploying To Production
-----------------------

The development web server is not suitable for exposure to the internet.
Deploying this in a configuration suitable for the public internet is beyond
the scope of this document. However, you can use any standard WSGI stack
to deploy this behind. If your frontend webserver can serve static content
directly, you should configure it for /static.

How Do I Add My Keyboard?
=========================

To add your keyboard you'll need to generate a `<keyboard>_layout.json` file.

Start by creating the layout you want to display at
<http://keyboard-layout-editor.com>. You will want to copy the data from
the "Raw Data" tab and save it to a file.

Next, run the `kle_to_layout.py` script to create a skeleton layout file.

    $ python kle_to_layout.py my_custom_keyboard.kle

Edit this file to customize your keyboard further. At the top you will
find a dictionary describing the properties of your keyboard. Example:

    {
        "name": "Experimental Pad",
        "directory": "keyboards/experiment",
        "key_width": 100,
        "subproject": "rev1"
    },
    
* name: The name of your keyboard
* directory: The directory inside `qmk_firmware` of your keyboard
* key_width: How many pixels wide a 1u key should be

Next you will find the keyboard layout description. This is a list of
list of dictionaries describing the physical layout of your keyboard.

The last row in the outer list is the first layer of the keyboard. This
will be KC_TRNS for every key position initially. You will need to set
these to appropriate values for your keyboard.

If you want more than one layer on your keyboard, you may simply append
them to the list. Keep in mind that you can't specify only a partial layer.
Every layer in your list must have the same number of rows, and each row
must have the same number of columns as the same row in the other layers.
