import usb_hid
from hid_gamepad import Gamepad
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

    def move(self, key, analog_value):
        if analog_value > 127:
            analog_value = 127
        elif analog_value < -127:
            analog_value = -127
            
        directions = ["LSX", "LSY", "RSY", "RSX", "LT", "RT"]
        if key not in directions:
            print("Unknown Analog key:", key)
            keycode = "LSX"
        if key == "LSX":
            self.gamepad.move_joysticks(x=analog_value)
        elif key == "LSY":
            self.gamepad.move_joysticks(y=analog_value)
        elif key == "RSX":
            self.gamepad.move_joysticks(z=analog_value)
        elif key == "RSY":
            self.gamepad.move_joysticks(r_z=analog_value)
        elif key == "LT":
            self.gamepad.move_joysticks(rx=analog_value)
        elif key == "RT":
            self.gamepad.move_joysticks(ry=analog_value)


    def _get_gamepad_code(self, key_name):
        key = self.gamepad_map.get(key_name.upper())
        if key is None:
            print("Unknown gamepad key", key_name.upper())
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