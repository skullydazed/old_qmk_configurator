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

What Doesn't Work
-----------------

Everything else.

* Save and download a keymap.c file for the user to use in their own checkout
* Save a JSON file describing this keyboard layout
* Build a .hex file that can be downloaded
* A way to add more layers
* A way to remove layers
* A way to reset a layer to its default
* Keycode validation
* Press tab to move to the next key
* Rotated keys (EG, ergodox)

What Can Be Made Better
-----------------------

* Colors
* UI
* The whole design in general

Demo Site
---------

If you'd like to view a demo site you can do so here:

    http://configurator.clueboard.co/
    
How Do I Run My Own Copy?
=========================

The Web UI is a simple flask application. To get started you will need
a local copy of Python (tested with 2.7, but should work on 2.6 as well)
and you will need to install flask. If you're not sure, you probably 
have python installed already, and can install flask with:

    $ sudo easy_install flask
    
If that fails you will need to install python.

Starting The Development Web Server
-----------------------------------

After installing the pre-requisites above run the "web.py" script.

    $ python web.py
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

(There may be other lines as well, as long as they are not errors
you can safely disregard them for now.)

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

The `layout.json` file uses the same format as 
<http://keyboard-layout-editor.com>, your first step is to generate a layout 
there. Save the text from the Raw Data tab, you'll use it later.

Next you need to create a dictionary describing the properties of your 
keyboard. Example:

    {
        "name": "Experimental Pad",
        "directory": "keyboards/experiment",
        "key_width": 100
    },
    
* name: The name of your keyboard
* directory: The directory inside `qmk_firmware` of your keyboard
* key_width: How many pixels wide a 1u key should be

Now that you have both of those, you can begin your `layout.json`. Make
a file with a single list containing your dictionary as one element and
your layout as another element, like so:

    [
        {
            "name": "Experimental Pad",
            "directory": "keyboards/experiment",
            "key_width": 100
        },
        [
            ["1","2","3","4"],
            ["Q","W","E","R"],
            ["A","S","D","F"],
        ]
    ]
    
This defines the physical layout of the board. Next you will need to create
one or more layers, these are roughly equivalent to the KEYMAP() macros in
your keyboard layout files. Append these layers to the list in your 
`layout.json` file. 

In this example we have two layers:

    [
        {
            "name": "Experimental Pad",
            "directory": "keyboards/experiment",
            "key_width": 100
        },
        [
            ["1","2","3","4"],
            ["Q","W","E","R"],
            ["A","S","D","F"],
        ],
        [
            ["KC_1","KC_2","KC_3","KC_4"],
            ["KC_Q","KC_W","KC_E","KC_R"],
            ["KC_A","KC_S","KC_D","MO(1)"],
        ],
        [
            ["KC_SPC","KC_LCTL","KC_LGUI","KC_LALT"],
            ["KC_TRNS","KC_TRNS","KC_TRNS","KC_TRNS"],
            ["KC_TRNS","KC_TRNS","KC_TRNS","MO(1)"],
        ]
    ]
    
 Save this file as `experiment_layout.json` next to the other layout files,
 and your keyboard will become available in the web interface.
