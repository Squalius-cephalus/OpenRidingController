
class GamepadOutput:
    def __init__(self):
    

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
        pass

    def release(self, key):
        pass
    def release_all(self):
        pass

    def move(self, key, analog_value):
        pass


    def _get_gamepad_code(self, key_name):
        pass
    
    def reins_output(self, left_key, right_key, threshold, analog_value):
        pass