import usb_hid
from hid_gamepad import Gamepad


class GamepadOutput:
    def __init__(self, uart_object=None):
        self.gamepad = Gamepad(usb_hid.devices)
        self.uart_enabled = False
        self.is_analog = True

        if uart_object != None:
            self.uart_object = uart_object
            self.uart_enabled = True

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

        self.uart_map = {
            "Y": 0,
            "B": 1,
            "A": 2,
            "X": 3,
            "LT": 4,
            "RT": 5,
            "LB": 6,
            "RB": 7,
            "L": 6,
            "R": 7,
            "MINUS": 8,
            "BACK": 8,
            "START": 9,
            "PLUS": 9,
            "LSB": 10,
            "RSB": 11,
            "LS": 10,
            "RS": 11,
            "HOME": 12,
            "CAPTURE": 13,
            "RESERVED1": 14,
            "RESERVED2": 15,
            "UP": 16,
            "DOWN": 17,
            "LEFT": 18,
            "RIGHT": 19
        }


    def update_uart(self):
        self.uart_thing.update()

    def press(self, key):
        self.gamepad.press_buttons(self._get_gamepad_code(key))

    def release(self, key):
        self.gamepad.release_buttons(self._get_gamepad_code(key))

    def release_all(self):
        self.gamepad.release_all_buttons()


    def move(self, axis, analog_value, sensitivity):

        analog_value = int(analog_value*sensitivity)

        if analog_value > 127: 
            analog_value = 127 
        elif analog_value < -127: 
            analog_value = -127


        mapping = {
            None: ("x", analog_value),
            "LSX": ("x", analog_value),
            "LSY": ("y", analog_value),
            "RSX": ("z", analog_value),
            "RSY": ("r_z", analog_value),
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
            print("Unknown gamepad key", key_name.upper())
            return 1
        return key
    
    def _get_uart_code(self, key_name):
        key = self.uart_map.get(key_name.upper())
        if key is None:
            print("Unknown uart key", key_name.upper())
            return 1
        return key
    
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