"""
This module wraps Adafruit HID Keyboard and converts keycodes to HID friendly codes.
"""
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from debug import log
class KeyboardOutput:
    """
    Handles keyboard output.
    """
    def __init__(self):
        self.keyboard = Keyboard(usb_hid.devices)

    @staticmethod
    def _get_keycode(key_name):
        try:
            return getattr(Keycode, key_name.upper())
        except AttributeError:
            log("Unknown key:", key_name)
            return getattr(Keycode, "A".upper())


    def release_all(self):
        """
        Release all the pressed keys.
        """
        self.keyboard.release_all()

    def press(self, key):
        """
        Get keycode and press keyboard key.
        Args:
            Keycode
        """
        self.keyboard.press(self._get_keycode(key))

    def release(self, key):
        """
        Get keycode and release keyboard key.
        Args:
            key: Keycode
        """
        self.keyboard.release(self._get_keycode(key))

    def reins_output(self, left_key, right_key, threshold, analog_value):
        """
        Convert reins analog value to keyboard output, key is activated
        if analog value if higher than threshold.
        Args:
            left_key: Left key keycode
            right_key: Right key keycode
            threshold: Threshold value to activate the key
            analog_value: Reins analog_value in tuple

        """
        left = analog_value[0]
        right = analog_value[1]

        if left >= threshold and left > right:
            self.press(left_key)
        else:
            self.release(left_key)

        if right >= threshold and right > left:
            self.press(right_key)
        else:
            self.release(right_key)
