from adafruit_simplemath import map_range
from debug import log
class UARTOutput:
    def __init__(self, uart_object=None):

        self.gamepad = uart_object

        self.uart_map = {
            "Y": 0,
            "B": 1,
            "A": 2,
            "X": 3,
            "LT": 4,
            "RT": 5,
            "LB": 6,
            "RB": 7,
            "BACK": 8,
            "START": 9,
            "LSB": 10,
            "RSB": 11,
            "HOME": 12,
            "SHARE": 13,
            "RESERVED1": 14,
            "RESERVED2": 15,
            "UP": 16,
            "DOWN": 17,
            "LEFT": 18,
            "RIGHT": 19
        }


    def update(self):
        self.uart_thing.update()

    def press(self, key):
        self.gamepad.press_buttons(self._get_gamepad_code(key))

    def release(self, key):
        self.gamepad.release_buttons(self._get_gamepad_code(key))

    def release_all(self):
        self.gamepad.release_all_buttons()


    def move(self, axis, analog_value):
        analog_value = int(map_range(analog_value, -127, 127, 0, 255))

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
        
        if analog_value > 127: 
            analog_value = 127 
        elif analog_value < -127: 
            analog_value = -127

        

        send_axis, value = mapping[axis]

        self.gamepad.move_joysticks(**{send_axis: value})


    def _get_gamepad_code(self, key_name):
        key = self.uart_map.get(key_name.upper())
        if key is None:
            log("Unknown UART key", key_name.upper())
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