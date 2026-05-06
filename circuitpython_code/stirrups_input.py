import time

import board
from utils import interpolate, get_current_position
from analogio import AnalogIn

left_stirrup_input = AnalogIn(board.GP28)
right_stirrup_input = AnalogIn(board.GP29)

class StirrupState:
    last_time: float = 0.0
    last_value: int = 350
    last_activated: float = 0.0

    forward_fast: bool = False
    forward_slow: bool = False
    backward_fast: bool = False
    backward_slow: bool = False

    def clear(self):
        self.forward_fast = False
        self.forward_slow = False
        self.backward_fast = False
        self.backward_slow = False

    def activate_forward_fast(self, current_time):
        self.forward_fast = True
        self.last_activated = current_time
    def activate_forward_slow(self, current_time):
        self.forward_slow = True
        self.last_activated = current_time
    def activate_backward_fast(self, current_time):
        self.backward_fast = True
        self.last_activated = current_time
    def activate_backward_slow(self, current_time):
        self.backward_slow = True
        self.last_activated = current_time

    def get_dict(self, prefix):
        return {
            f"stirrup_{prefix}_forward_fast": self.forward_fast,
            f"stirrup_{prefix}_forward_slow": self.forward_slow,
            f"stirrup_{prefix}_backward_fast": self.backward_fast,
            f"stirrup_{prefix}_backward_slow": self.backward_slow,
        }


class StirrupsHandler:
    def __init__(self):

        self.stirrups_curve = [(0, 0), (255, 255), (511, 511)]

        self.threshold_fast = 0.4
        self.threshold_slow = 0.8
        self.forward_threshold = 390
        self.backward_threshold = 100
        self.speed_threshold_fast = 30
        self.speed_threshold_slow = 20


        self.left_stirrup = StirrupState()
        self.right_stirrup = StirrupState()

    def set_new_profile(self, settings):
        self.speed_threshold_fast = settings["stirrup_speed_threshold_fast"]
        self.speed_threshold_slow = settings["stirrup_speed_threshold_slow"]
    def update(self):
        current_time = time.monotonic()
        
        self.left_stirrup.clear()
        self.right_stirrup.clear()

        self.update_analog()
        self.handle_stirrup_speed(self.left_stirrup_value, self.left_stirrup, current_time)
        self.handle_stirrup_speed(self.right_stirrup_value, self.right_stirrup, current_time)

    def update_analog(self):
        self.left_stirrup_value = interpolate(left_stirrup_input.value, self.stirrups_curve)
        self.right_stirrup_value = interpolate(right_stirrup_input.value, self.stirrups_curve)

    def handle_stirrup_speed(self, value, logic, current_time):
        cooldown = 0.3
        if current_time - logic.last_time >= 0.01:
            logic.last_time = current_time

            speed = (value - logic.last_value) / 0.01 / 100
            logic.last_value = value

            if current_time - logic.last_activated <= cooldown:
                 return
            
            if abs(speed) > self.speed_threshold_fast and value < self.backward_threshold:
                    logic.activate_forward_fast(current_time)
            elif abs(speed) > self.speed_threshold_fast and value > self.forward_threshold:
                    logic.activate_backward_fast(current_time)
                

            elif abs(speed) > self.speed_threshold_slow and value < self.backward_threshold:
                    logic.activate_forward_slow(current_time)
            elif abs(speed) > self.speed_threshold_slow and value > self.forward_threshold:
                    logic.activate_backward_slow(current_time)
              
            


    def get_states(self):
        states = self.left_stirrup.get_dict("left") | self.right_stirrup.get_dict("right")

        return states
