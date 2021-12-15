# SPDX-FileCopyrightText: 2019 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pyoa`
================================================================================

A CircuitPython 'Choose Your Own Adventure' framework for PyPortal.


* Author(s): Adafruit

Implementation Notes
--------------------

**Hardware:**

* PyPortal https://www.adafruit.com/product/4116
* PyPortal Pynt https://www.adafruit.com/product/4465
* PyPortal Titano https://www.adafruit.com/product/4444
* PyBadge https://www.adafruit.com/product/4200
* PyGamer https://www.adafruit.com/product/4242
* HalloWing M4 https://www.adafruit.com/product/4300

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

# imports
import time
import json
import board
from digitalio import DigitalInOut
import displayio
import adafruit_touchscreen

try:  # No need for Cursor Control on the PyPortal
    from adafruit_cursorcontrol.cursorcontrol import Cursor
    from adafruit_cursorcontrol.cursorcontrol_cursormanager import CursorManager
except ImportError:
    pass
import audiocore
import audioio
from adafruit_display_text.label import Label
from adafruit_button import Button
import terminalio

try:
    from typing import Dict, Optional, List
except ImportError:
    pass

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PYOA.git"


class PYOA_Graphics:
    # pylint: disable=too-many-instance-attributes
    """A choose your own adventure game framework."""

    def __init__(self) -> None:
        self.root_group = displayio.Group()
        self._display = board.DISPLAY
        self._background_group = displayio.Group()
        self.root_group.append(self._background_group)
        self._text_group = displayio.Group()
        self.root_group.append(self._text_group)
        self._button_group = displayio.Group()
        self.root_group.append(self._button_group)

        if self._display.height > 250:
            self._text_group.scale = 2
            self._button_group.scale = 2

        self._speaker_enable = DigitalInOut(board.SPEAKER_ENABLE)
        self._speaker_enable.switch_to_output(False)
        if hasattr(board, "AUDIO_OUT"):
            self.audio = audioio.AudioOut(board.AUDIO_OUT)
        elif hasattr(board, "SPEAKER"):
            self.audio = audioio.AudioOut(board.SPEAKER)
        else:
            raise AttributeError("Board does not have an audio output!")

        self._background_file = None
        self._wavfile = None

        self._display.auto_brightness = False
        self.backlight_fade(0)
        self._display.show(self.root_group)
        self.touchscreen = None
        self.mouse_cursor = None
        if hasattr(board, "TOUCH_XL"):
            self.touchscreen = adafruit_touchscreen.Touchscreen(
                board.TOUCH_XL,
                board.TOUCH_XR,
                board.TOUCH_YD,
                board.TOUCH_YU,
                calibration=((5200, 59000), (5800, 57000)),
                size=(self._display.width, self._display.height),
            )
        elif hasattr(board, "BUTTON_CLOCK"):
            self.mouse_cursor = Cursor(
                self._display, display_group=self.root_group, cursor_speed=8
            )
            self.cursor = CursorManager(self.mouse_cursor)
        else:
            raise AttributeError("PYOA requires a touchscreen or cursor.")
        self._gamedirectory = None
        self._gamefilename = None
        self._game = None
        self._text = None
        self._background_sprite = None
        self._text_font = None
        self._left_button = None
        self._right_button = None
        self._middle_button = None

    def load_game(self, game_directory: str) -> None:
        """Load a game.

        :param str game_directory: where the game files are stored
        """
        self._gamedirectory = game_directory
        self._text_font = terminalio.FONT
        # Possible Screen Sizes are:
        # 320x240 PyPortal and PyPortal Pynt
        # 160x128 PyBadge and PyGamer
        # 480x320 PyPortal Titano
        # 240x240 if we wanted to use HalloWing M4

        # Button Attributes
        btn_left = 10
        btn_right = btn_left + 180
        btn_mid = btn_left + 90
        button_y = 195
        button_width = 120
        button_height = 40
        if self._display.height < 200:
            button_y //= 2
            button_y += 10
            button_width //= 2
            button_height //= 2
            btn_right //= 2
            btn_mid //= 2
        elif self._display.height > 250:
            button_y = (button_y * 3) // 4
            button_y -= 20
            button_width = (button_width * 3) // 4
            button_height = (button_height * 3) // 4
            btn_right = (btn_right * 3) // 4
            btn_mid = (btn_right * 3) // 4
        self._left_button = Button(
            x=btn_left,
            y=button_y,
            width=button_width,
            height=button_height,
            label="Left",
            label_font=self._text_font,
            style=Button.SHADOWROUNDRECT,
        )
        self._right_button = Button(
            x=btn_right,
            y=button_y,
            width=button_width,
            height=button_height,
            label="Right",
            label_font=self._text_font,
            style=Button.SHADOWROUNDRECT,
        )
        self._middle_button = Button(
            x=btn_mid,
            y=button_y,
            width=button_width,
            height=button_height,
            label="Middle",
            label_font=self._text_font,
            style=Button.SHADOWROUNDRECT,
        )
        self._gamefilename = game_directory + "/cyoa.json"
        try:
            with open(  # pylint: disable=unspecified-encoding
                self._gamefilename, "r"
            ) as game_file:
                self._game = json.load(game_file)
        except OSError as err:
            raise OSError("Could not open game file " + self._gamefilename) from err

    def _fade_to_black(self) -> None:
        """Turn down the lights."""
        if self.mouse_cursor:
            self.mouse_cursor.is_hidden = True
        self.backlight_fade(0)
        # turn off background so we can render the text
        self.set_background(None, with_fade=False)
        self.set_text(None, None)
        for _ in range(len(self._button_group)):
            self._button_group.pop()
        if self.mouse_cursor:
            self.mouse_cursor.is_hidden = False

    def _display_buttons(self, card: Dict[str, str]) -> None:
        """Display the buttons of a card.

        :param card: The active card
        :type card: dict(str, str)
        """
        button01_text = card.get("button01_text", None)
        button02_text = card.get("button02_text", None)
        self._left_button.label = button01_text
        self._middle_button.label = button01_text
        self._right_button.label = button02_text
        if button01_text and not button02_text:
            # show only middle button
            self._button_group.append(self._middle_button)
        if button01_text and button02_text:
            self._button_group.append(self._right_button)
            self._button_group.append(self._left_button)

    def _display_background_for(self, card: Dict[str, str]) -> None:
        """If there's a background on card, display it.

        :param card: The active card
        :type card: dict(str, str)
        """
        self.set_background(card.get("background_image", None), with_fade=False)

    def _display_text_for(self, card: Dict[str, str]) -> None:
        """Display the main text of a card.

        :param card: The active card
        :type card: dict(str, str)
        """
        text = card.get("text", None)
        text_color = card.get("text_color", 0x0)  # default to black
        text_background_color = card.get("text_background_color", None)
        if text:
            try:
                text_color = int(text_color)  # parse the JSON string to hex int
            except ValueError:
                text_color = 0x0

            try:
                text_background_color = int(
                    text_background_color
                )  # parse the JSON string to hex int
            except ValueError:
                text_background_color = None
            except TypeError:
                text_background_color = None

            self.set_text(text, text_color, background_color=text_background_color)

    def _play_sound_for(self, card: Dict[str, str]) -> None:
        """If there's a sound, start playing it.

        :param card: The active card
        :type card: dict(str, str)
        """
        sound = card.get("sound", None)
        loop = card.get("sound_repeat", False)
        if sound:
            loop = loop == "True"
            print("Loop:", loop)
            self.play_sound(sound, wait_to_finish=False, loop=loop)

    def _wait_for_press(self, card: Dict[str, str]) -> str:
        """Wait for a button to be pressed.

        :param card: The active card
        :type card: dict(str, str)
        :return: The id of the destination card
        :rtype: str
        """
        button01_text = card.get("button01_text", None)
        button02_text = card.get("button02_text", None)
        point_touched = None
        while True:
            if self.touchscreen is not None:
                point_touched = self.touchscreen.touch_point
            else:
                self.cursor.update()
                if self.cursor.is_clicked is True:
                    point_touched = self.mouse_cursor.x, self.mouse_cursor.y
            if point_touched is not None:
                point_touched = (
                    point_touched[0] // self._button_group.scale,
                    point_touched[1] // self._button_group.scale,
                )
                print("touch: ", point_touched)
                if button01_text and not button02_text:
                    # showing only middle button
                    if self._middle_button.contains(point_touched):
                        print("Middle button")
                        return card.get("button01_goto_card_id", None)
                if button01_text and button02_text:
                    if self._left_button.contains(point_touched):
                        print("Left button")
                        return card.get("button01_goto_card_id", None)
                    if self._right_button.contains(point_touched):
                        print("Right button")
                        return card.get("button02_goto_card_id", None)
            time.sleep(0.1)

    def display_card(self, card_num: int) -> int:
        """Display and handle input on a card.

        :param int card_num: the index of the card to process
        :return: the card number of the selected card
        :rtype: int
        """
        card = self._game[card_num]
        print(card)
        print("*" * 32)
        print("****{:^24s}****".format(card["card_id"]))
        print("*" * 32)

        self._fade_to_black()
        self._display_buttons(card)
        self._display_background_for(card)
        self.backlight_fade(1.0)
        self._display_text_for(card)
        self._display.refresh(target_frames_per_second=60)

        self._play_sound_for(card)

        auto_adv = card.get("auto_advance", None)
        if auto_adv is not None:
            auto_adv = float(auto_adv)
            print("Auto advancing after %0.1f seconds" % auto_adv)
            time.sleep(auto_adv)
            return card_num + 1

        destination_card_id = self._wait_for_press(card)

        self.play_sound(None)  # stop playing any sounds
        for card_number, card_struct in enumerate(self._game):
            if card_struct.get("card_id", None) == destination_card_id:
                return card_number  # found the matching card!
        # eep if we got here something went wrong
        raise RuntimeError(
            "Could not find card with matching 'card_id': ", destination_card_id
        )

    def play_sound(
        self,
        filename: Optional[str],
        *,
        wait_to_finish: bool = True,
        loop: bool = False
    ) -> None:
        """Play a sound

        :param filename: The filename of the sound to play. Use `None` to stop
            playing anything.
        :type filename: str or None
        :param bool wait_to_finish: Whether playing the sound should block
        :param bool loop: Whether the sound should loop
        """
        self._speaker_enable.value = False
        self.audio.stop()
        if self._wavfile:
            self._wavfile.close()
            self._wavfile = None

        if not filename:
            return  # nothing more to do, just stopped
        filename = self._gamedirectory + "/" + filename
        print("Playing sound", filename)
        self._display.refresh(target_frames_per_second=60)
        try:
            self._wavfile = open(filename, "rb")  # pylint: disable=consider-using-with
        except OSError as err:
            raise OSError("Could not locate sound file", filename) from err

        wavedata = audiocore.WaveFile(self._wavfile)
        self._speaker_enable.value = True
        self.audio.play(wavedata, loop=loop)
        if loop or not wait_to_finish:
            return
        while self.audio.playing:
            pass
        self._wavfile.close()
        self._wavfile = None
        self._speaker_enable.value = False

    def set_text(
        self,
        text: Optional[str],
        color: Optional[str],
        background_color: Optional[int] = None,
    ) -> None:
        """Display the test for a card.

        :param text: the text to display
        :type text: str or None
        :param color: the text color
        :type color: str or None
        :param background_color: the background color of the text
        :type background_color: int or None
        """
        if self._text_group:
            self._text_group.pop()
        if not text or not color:
            return  # nothing to do!
        text_wrap = 37
        if self._display.height < 130:
            text_wrap = 25
        text = self.wrap_nicely(text, text_wrap)
        text = "\n".join(text)
        print("Set text to", text, "with color", hex(color))
        text_x = 8
        text_y = 95
        if self._display.height < 130:
            text_x = 3
            text_y = 38
        elif self._display.height > 250:
            text_y = 50
        if text:
            self._text = Label(self._text_font, text=str(text))
            self._text.x = text_x
            self._text.y = text_y
            self._text.color = color
            if background_color:
                self._text.background_color = background_color
            self._text_group.append(self._text)

    def set_background(
        self, filename: Optional[str], *, with_fade: bool = True
    ) -> None:
        """The background image to a bitmap file.

        :param filename: The filename of the chosen background
        :type filename: str or None
        :param bool with_fade: If `True` fade out the backlight while loading the new background
            and fade in the backlight once completed.
        """
        print("Set background to", filename)
        if with_fade:
            self.backlight_fade(0)
        if self._background_group:
            self._background_group.pop()

        if filename:
            background = displayio.OnDiskBitmap(self._gamedirectory + "/" + filename)
            self._background_sprite = displayio.TileGrid(
                background,
                pixel_shader=background.pixel_shader,
            )
            self._background_group.append(self._background_sprite)
        if with_fade:
            self._display.refresh(target_frames_per_second=60)
            self.backlight_fade(1.0)

    def backlight_fade(self, to_light: float) -> None:
        """
        Adjust the TFT backlight. Fade from the current value to the ``to_light`` value

        :param float to_light: the desired backlight brightness between :py:const:`0.0` and
            :py:const:`1.0`.
        """
        from_light = self._display.brightness
        from_light = int(from_light * 100)
        to_light = max(0, min(100, int(to_light * 100)))
        delta = 1
        if from_light > to_light:
            delta = -1
        for val in range(from_light, to_light, delta):
            self._display.brightness = val / 100
            time.sleep(0.003)
        self._display.brightness = to_light / 100

    # return a list of lines with wordwrapping
    @staticmethod
    def wrap_nicely(string: str, max_chars: int) -> List[str]:
        """A helper that will return a list of lines with word-break wrapping.

        :param str string: The text to be wrapped.
        :param int max_chars: The maximum number of characters on a line before wrapping.
        :return: The list of lines
        :rtype: list(str)
        """
        # string = string.replace('\n', '').replace('\r', '') # strip confusing newlines
        words = string.split(" ")
        the_lines = []
        the_line = ""
        for w in words:
            if "\n" in w:
                _w1, _w2 = w.split("\n")
                the_line += " " + _w1
                the_lines.append(the_line)
                the_line = _w2
            elif len(the_line + " " + w) > max_chars:
                the_lines.append(the_line)
                the_line = "" + w
            else:
                the_line += " " + w
        if the_line:  # last line remaining
            the_lines.append(the_line)
        # remove first space from first line:
        the_lines[0] = the_lines[0][1:]
        return the_lines
