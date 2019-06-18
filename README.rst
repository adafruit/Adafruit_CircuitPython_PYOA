Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-pyoa/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/pyoa/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

.. image:: https://travis-ci.com/adafruit/Adafruit_CircuitPython_PYOA.svg?branch=master
    :target: https://travis-ci.com/adafruit/Adafruit_CircuitPython_PYOA
    :alt: Build Status

A CircuitPython 'Choose Your Own Adventure' framework for PyPortal.


Dependencies
=============
This driver depends on:

* Adafruit CircuitPython <https://github.com/adafruit/circuitpython>

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Usage Example
=============

.. todo:: Add a quick, simple example. It and other examples should live in the examples folder and be included in docs/examples.rst.

.. code-block:: python

    import sys
    sys.path.append('/Adafruit_CircuitPython_PYOA')

    import adafruit_sdcard
    import storage
    from adafruit_pyoa import PYOA_Graphics
    import board
    import digitalio

    try:
        sdcard = adafruit_sdcard.SDCard(board.SPI(), digitalio.DigitalInOut(board.SD_CS))
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd")
        print("SD card found") # no biggie
    except OSError:
        print("No SD card found") # no biggie

    gfx = PYOA_Graphics()

    gfx.load_game("/cyoa")
    current_card = 0   # start with first card

    while True:
        print("Current card:", current_card)
        current_card = gfx.display_card(current_card)


Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_PYOA/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Building locally
================

Zip release files
-----------------

To build this library locally you'll need to install the
`circuitpython-build-tools <https://github.com/adafruit/circuitpython-build-tools>`_ package.

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install circuitpython-build-tools

Once installed, make sure you are in the virtual environment:

.. code-block:: shell

    source .env/bin/activate

Then run the build:

.. code-block:: shell

    circuitpython-build-bundles --filename_prefix adafruit-circuitpython-pyoa --library_location .

Sphinx documentation
-----------------------

Sphinx is used to build the documentation based on rST files and comments in the code. First,
install dependencies (feel free to reuse the virtual environment from above):

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install Sphinx sphinx-rtd-theme

Now, once you have the virtual environment activated:

.. code-block:: shell

    cd docs
    sphinx-build -E -W -b html . _build/html

This will output the documentation to ``docs/_build/html``. Open the index.html in your browser to
view them. It will also (due to -W) error out on any warning like Travis will. This is a good way to
locally verify it will pass.
