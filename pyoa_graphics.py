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

class PYOA_Graphics():
    def __init__(self):
        self.root_group = displayio.Group(max_size=15)

        self._background_group = displayio.Group(max_size=1)
        self.root_group.append(self._background_group)
        self._text_group = displayio.Group(max_size=1)
        self.root_group.append(self._text_group)
        self._button_group = displayio.Group(max_size=2)
        #self.root_group.append(self._button_group)

        #self._text_font = bitmap_font.load_font("Arial-12.bdf")
        self._text_font = displayio.BuiltinFont
        try:
            glyphs = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-!,. "\'?!'
            print("Preloading font glyphs:", glyphs)
            self._text_font.load_glyphs(glyphs)
        except AttributeError:
            pass # normal for built in font

        self._left_button = Button(x=10, y=195,
                          width=120, height=40,
                          label="Left", label_font=self._text_font,
                          style=Button.SHADOWROUNDRECT)
        self._right_button = Button(x=190, y=195,
                          width=120, height=40,
                          label="Right", label_font=self._text_font,
                          style=Button.SHADOWROUNDRECT)
        self._button_group.append(self._left_button.group)
        self._button_group.append(self._right_button.group)


        self._speaker_enable = DigitalInOut(board.SPEAKER_ENABLE)
        self._speaker_enable.switch_to_output(False)
        self.audio = audioio.AudioOut(board.AUDIO_OUT)


        self._background_file = None
        self._wavfile = None

        board.DISPLAY.auto_brightness = False
        self.backlight_fade(0)
        board.DISPLAY.show(self.root_group)

    def load_game(self, game_directory):
        self._gamedirectory = game_directory
        self._gamefilename = game_directory+"/code.json"
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
        # if there's a background, display it
        self.set_background(card.get('background_image', None))
        # if there's a sound, start playing it
        #sound = card.get('sound', None)
        #if sound:
        #    self.play_sound(sound)

        # display main text
        text = card.get('text', None)
        text_color = card.get('text_color', 0x0)  # default to black
        if text:
            try:
                text_color = int(text_color)   # parse the JSON string to hex int
            except ValueError:
                text_color = 0x0
            self.set_text(text, text_color)

        # display buttons
        button01_text = card.get('button01_text', None)
        button02_text = card.get('button02_text', None)


        auto_adv = card.get('auto_advance', None)
        if auto_adv is not None:
            auto_adv = float(auto_adv)
            print("Auto advancing after %0.1f seconds" % auto_adv)
            time.sleep(auto_adv)
            return card_num+1

        while True:
            pass


    def play_sound(self, filename, *, wait_to_finish=True, loop=False):
        print("Playing sound", filename)
        board.DISPLAY.wait_for_frame()
        if self._wavfile:
            self._wavfile.close()
        self._wavfile = open(self._gamedirectory+"/"+filename, "rb")
        wavedata = audioio.WaveFile(self._wavfile)
        self._speaker_enable.value = True
        self.audio.play(wavedata)
        if not wait_to_finish:
            return
        while self.audio.playing:
            pass
        self._wavfile.close()
        self._speaker_enable.value = False

    def set_text(self, text, color):
        text = self.wrap_nicely(text, 40)
        text = '\n'.join(text)
        print("Set text to", text, "with color", hex(color))
        if self._text_group:
            self._text_group.pop()
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
                                                         position=(0,0))
            self._background_group.append(self._background_sprite)
        board.DISPLAY.refresh_soon()
        board.DISPLAY.wait_for_frame()
        if with_fade:
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
        string = string.replace('\n', '').replace('\r', '') # strip confusing newlines
        words = string.split(' ')
        the_lines = []
        the_line = ""
        for w in words:
            if len(the_line+' '+w) <= max_chars:
                the_line += ' '+w
            else:
                the_lines.append(the_line)
                the_line = ''+w
        if the_line:      # last line remaining
            the_lines.append(the_line)
        # remove first space from first line:
        the_lines[0] = the_lines[0][1:]
        return the_lines
