from pyoa_graphics import PYOA_Graphics



gfx = PYOA_Graphics()

gfx.load_game("/Adafruit_CircuitPython_PYOA/robots")
current_card = 2   # start with first card

while True:
    print("Current card:", current_card)
    current_card = gfx.display_card(current_card)
