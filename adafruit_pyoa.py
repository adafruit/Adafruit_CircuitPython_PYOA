# The MIT License (MIT)
#
# Copyright (c) 2019 Adafruit for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_pyoa`
================================================================================

A CircuitPython 'Choose Your Own Adventure' framework for PyPortal.


* Author(s): Adafruit

Implementation Notes
--------------------

**Hardware:**

* `PyPortal <https://www.adafruit.com/product/4116>`

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

#pylint: disable=too-many-instance-attributes

# imports
import time
import os
import json
import board
import displayio
from digitalio import DigitalInOut
import adafruit_touchscreen
import audioio
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PYOA.git"

class PYOA_Graphics():
    def __init__(self):
        self.root_group = displayio.Group(max_size=15)

        self._background_group = displayio.Group(max_size=1)
        self.root_group.append(self._background_group)
        self._text_group = displayio.Group(max_size=1)
        self.root_group.append(self._text_group)
        self._button_group = displayio.Group(max_size=2)
        self.root_group.append(self._button_group)

        self._text_font = bitmap_font.load_font("Arial-Bold-12.bdf")
        #self._text_font = fontio.BuiltinFont
        try:
            glyphs = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-!,. "\'?!'
            print("Preloading font glyphs:", glyphs)
            self._text_font.load_glyphs(glyphs)
        except AttributeError:
            pass # normal for built in font

        self._left_button = Button(x=10, y=195, width=120, height=40,
                                   label="Left", label_font=self._text_font,
                                   style=Button.SHADOWROUNDRECT)
        self._right_button = Button(x=190, y=195, width=120, height=40,
                                    label="Right", label_font=self._text_font,
                                    style=Button.SHADOWROUNDRECT)
        self._middle_button = Button(x=100, y=195, width=120, height=40,
                                     label="Middle", label_font=self._text_font,
                                     style=Button.SHADOWROUNDRECT)

        self._speaker_enable = DigitalInOut(board.SPEAKER_ENABLE)
        self._speaker_enable.switch_to_output(False)
        self.audio = audioio.AudioOut(board.AUDIO_OUT)

        self._background_file = None
        self._wavfile = None

        board.DISPLAY.auto_brightness = False
        self.backlight_fade(0)
        board.DISPLAY.show(self.root_group)

        self.touchscreen = adafruit_touchscreen.Touchscreen(board.TOUCH_XL, board.TOUCH_XR,
                                                            board.TOUCH_YD, board.TOUCH_YU,
                                                            calibration=((5200, 59000), (5800, 57000)),
                                                            size=(320, 240))

    def load_game(self, game_directory):
        self._gamedirectory = game_directory
        self._gamefilename = game_directory+"/cyoa.json"
        try:
            f = open(self._gamefilename, "r")
        except OSError:
            raise OSError("Could not open game file "+self._gamefilename)
        self._game = json.load(f)
        f.close()

    def display_card(self, card_num):
        card = self._game[card_num]
        print(card)
        print("*"*32)
        print('****{:^24s}****'.format(card['page_id']))
        print("*"*32)

        # turn down the lights
        self.backlight_fade(0)
        # turn off background so we can render the text
        self.set_background(None, with_fade=False)
        self.set_text(None, None)
        for i in range(len(self._button_group)):
            self._button_group.pop()

        # display buttons
        button01_text = card.get('button01_text', None)
        button02_text = card.get('button02_text', None)
        self._left_button.label = button01_text
        self._middle_button.label = button01_text
        self._right_button.label = button02_text
        if button01_text and not button02_text:
            # show only middle button
            self._button_group.append(self._middle_button.group)
        if button01_text and button02_text:
            self._button_group.append(self._right_button.group)
            self._button_group.append(self._left_button.group)

        # if there's a background, display it
        self.set_background(card.get('background_image', None), with_fade=False)

        self.backlight_fade(1.0)

        # display main text
        text = card.get('text', None)
        text_color = card.get('text_color', 0x0)  # default to black
        if text:
            try:
                text_color = int(text_color)   # parse the JSON string to hex int
            except ValueError:
                text_color = 0x0
            self.set_text(text, text_color)

        board.DISPLAY.refresh_soon()
        board.DISPLAY.wait_for_frame()

        # if there's a sound, start playing it
        sound = card.get('sound', None)
        loop = card.get('sound_repeat', False)
        if sound:
            loop = loop == "True"
            print("Loop:", loop)
            self.play_sound(sound, wait_to_finish=False, loop=loop)

        auto_adv = card.get('auto_advance', None)
        if auto_adv is not None:
            auto_adv = float(auto_adv)
            print("Auto advancing after %0.1f seconds" % auto_adv)
            time.sleep(auto_adv)
            return card_num+1

        goto_page = None
        while not goto_page:
            p = self.touchscreen.touch_point
            if p:
                print("touch: ", p)
                if button01_text and not button02_text:
                    # showing only middle button
                    if self._middle_button.contains(p):
                        print("Middle button")
                        goto_page = card.get('button01_goto_page_id', None)
                if button01_text and button02_text:
                    if self._left_button.contains(p):
                        print("Left button")
                        goto_page = card.get('button01_goto_page_id', None)
                    if self._right_button.contains(p):
                        print("Right button")
                        goto_page = card.get('button02_goto_page_id', None)
        self.play_sound(None)  # stop playing any sounds
        for i, c in enumerate(self._game):
            if c.get('page_id', None) == goto_page:
                return i    # found the matching card!
        # eep if we got here something went wrong
        raise RuntimeError("Could not find card with matching 'page_id': ", goto_page)

    def play_sound(self, filename, *, wait_to_finish=True, loop=False):
        self._speaker_enable.value = False
        self.audio.stop()
        if self._wavfile:
            self._wavfile.close()
            self._wavfile = None

        if not filename:
            return   # nothing more to do, just stopped
        filename = self._gamedirectory+"/"+filename
        print("Playing sound", filename)
        board.DISPLAY.wait_for_frame()
        try:
            self._wavfile = open(filename, "rb")
        except OSError:
            raise OSError("Could not locate sound file", filename)

        wavedata = audioio.WaveFile(self._wavfile)
        self._speaker_enable.value = True
        self.audio.play(wavedata, loop=loop)
        if loop or not wait_to_finish:
            return
        while self.audio.playing:
            pass
        self._wavfile.close()
        self._wavfile = None
        self._speaker_enable.value = False

    def set_text(self, text, color):
        if self._text_group:
            self._text_group.pop()
        if not text or not color:
            return    # nothing to do!
        text = self.wrap_nicely(text, 37)
        text = '\n'.join(text)
        print("Set text to", text, "with color", hex(color))
        if text:
            self._text = Label(self._text_font, text=str(text))
            self._text.x = 10
            self._text.y = 100
            self._text.color = color
            self._text_group.append(self._text)

    def set_background(self, filename, *, with_fade=True):
        """The background image to a bitmap file.

        :param filename: The filename of the chosen background

        """
        print("Set background to", filename)
        if with_fade:
            self.backlight_fade(0)
        if self._background_group:
            self._background_group.pop()

        if filename:
            if self._background_file:
                self._background_file.close()
            self._background_file = open(self._gamedirectory+"/"+filename, "rb")
            background = displayio.OnDiskBitmap(self._background_file)
            self._background_sprite = displayio.TileGrid(background,
                                                         pixel_shader=displayio.ColorConverter(),
                                                         x=0, y=0)
            self._background_group.append(self._background_sprite)
        if with_fade:
            board.DISPLAY.refresh_soon()
            board.DISPLAY.wait_for_frame()
            self.backlight_fade(1.0)

    def backlight_fade(self, to_light):
        """Adjust the TFT backlight. Fade from one value to another
        """
        from_light = board.DISPLAY.brightness
        from_light = int(from_light*100)
        to_light = max(0, min(1.0, to_light))
        to_light = int(to_light*100)
        delta = 1
        if from_light > to_light:
            delta = -1
        for val in range(from_light, to_light, delta):
            board.DISPLAY.brightness = val/100
            time.sleep(0.003)
        board.DISPLAY.brightness = to_light/100


    # return a list of lines with wordwrapping
    @staticmethod
    def wrap_nicely(string, max_chars):
        """A helper that will return a list of lines with word-break wrapping.

        :param str string: The text to be wrapped.
        :param int max_chars: The maximum number of characters on a line before wrapping.

        """
        #string = string.replace('\n', '').replace('\r', '') # strip confusing newlines
        words = string.split(' ')
        the_lines = []
        the_line = ""
        for w in words:
            if '\n' in w:
                w1, w2 = w.split('\n')
                the_line += ' '+w1
                the_lines.append(the_line)
                the_line = w2
            elif len(the_line+' '+w) > max_chars:
                the_lines.append(the_line)
                the_line = ''+w
            else:
                the_line += ' '+w
        if the_line:      # last line remaining
            the_lines.append(the_line)
        # remove first space from first line:
        the_lines[0] = the_lines[0][1:]
        return the_lines
