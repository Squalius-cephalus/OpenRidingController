"""
This module wraps Adafruit HID Gamepad and converts keycodes to HID friendly codes.
"""

import usb_hid
from hid_gamepad import Gamepad
from utils.debug import log

class GamepadOutput:
    def __init__(self):
        self.gamepad = Gamepad(usb_hid.devices)

        self.gamepad_map = {
            "A": 1,
            "B": 2,
            "X": 3,
            "Y": 4,
            "LB": 5,
            "RB": 6,
            "BACK": 7,
            "START": 8,
            "LSB": 9,
            "RSB": 10,
            "UP": 11,
            "DOWN": 12,
            "LEFT": 13,
            "RIGHT": 14,
            "HOME": 15,
            "SHARE": 16

        }


    def press(self, key):
        self.gamepad.press_buttons(self._get_gamepad_code(key))

    def release(self, key):
        self.gamepad.release_buttons(self._get_gamepad_code(key))

    def release_all(self):
        self.gamepad.release_all_buttons()
        self.gamepad.move_joysticks(x=0, y=0, z=0,r_z=0,r_y=0, r_x=0)


    def move(self, axis, analog_value, sensitivity):
        """
        Wraps gamepad buttons and analog axis movement to single method
        that output manager can call.
        
        Args:
            axis: Joystick axis or gamepad button.
            analog_value: -127 to 127 for joystick movement.
            sensitivity: Joystick sensitivity

        """
        analog_value = int(analog_value*sensitivity)

        if analog_value > 127:
            analog_value = 127
        elif analog_value < -127:
            analog_value = -127


        mapping = {
            None: ("x", analog_value),
            "LSX": ("x", analog_value),
            "LSY": ("y", -analog_value),
            "RSX": ("z", analog_value),
            "RSY": ("r_z", -analog_value),
            "LT":  ("r_x", analog_value),
            "RT":  ("r_y", analog_value),
        }


        if axis not in mapping.keys():
            if analog_value == 0:
                self.release(axis)
            else:
                self.press(axis)
            return

        send_axis, value = mapping[axis]

        self.gamepad.move_joysticks(**{send_axis: value})


    def _get_gamepad_code(self, key_name):
        key = self.gamepad_map.get(key_name.upper())
        if key is None:
            log("Unknown gamepad key", key_name.upper())
            return 1
        return key
