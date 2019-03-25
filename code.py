import adafruit_sdcard
import storage
from pyoa_graphics import PYOA_Graphics
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

gfx.load_game("/sd/robots")
current_card = 0   # start with first card

while True:
    print("Current card:", current_card)
    current_card = gfx.display_card(current_card)
