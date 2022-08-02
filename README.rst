Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-pyoa/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/pyoa/en/latest/
    :alt: Documentation Status

.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_PYOA/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_PYOA/actions/
    :alt: Build Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code Style: Black

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

.. code-block:: python

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


Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/pyoa/en/latest/>`_.

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_PYOA/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
