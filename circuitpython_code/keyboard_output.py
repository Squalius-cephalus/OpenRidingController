import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

class KeyboardOutput:
    def __init__(self):
        self.keyboard = Keyboard(usb_hid.devices)
        self.is_analog = False

    @staticmethod
    def _get_keycode(key_name):
        try:
            return getattr(Keycode, key_name.upper())
        except AttributeError:
            print("Unknown key:", key_name)
            return getattr(Keycode, "A".upper())

    
    def release_all(self):
        self.keyboard.release_all()

    def press(self, key):
        self.keyboard.press(self._get_keycode(key))

    def release(self, key):
        self.keyboard.release(self._get_keycode(key))

    def reins_output(self, left_key, right_key, threshold, analog_value):
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


