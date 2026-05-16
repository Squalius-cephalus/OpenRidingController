"""
Stirrup input handling for stirrup sensors.

This module initializes GPIO stirrup inputs, tracks how fast stirrups are moved,
and exposes helper classes for updating and retrieving stirrups current state.
"""

import time
import board
from utils import interpolate
from analogio import AnalogIn

left_stirrup_input = AnalogIn(board.GP28)
right_stirrup_input = AnalogIn(board.GP29)

class StirrupState:
    """
    Setup stirrup states and when it was activated last time.
    """
    last_time: float = 0.0
    activated: bool = False

    forward_fast: bool = False
    forward_slow: bool = False
    backward_fast: bool = False
    backward_slow: bool = False
    forward_hold: bool = False
    backward_hold: bool = False

    def clear(self):
        """
        Reset stirrups states.
        """

        self.forward_fast = False
        self.forward_slow = False
        self.backward_fast = False
        self.backward_slow = False
        self.forward_hold = False
        self.backward_hold = False

    def get_dict(self, prefix):
        """
        Return stirrups states.
        """
        return {
            f"stirrup_{prefix}_forward_fast": self.forward_fast,
            f"stirrup_{prefix}_forward_slow": self.forward_slow,
            f"stirrup_{prefix}_backward_fast": self.backward_fast,
            f"stirrup_{prefix}_backward_slow": self.backward_slow,
            f"stirrup_{prefix}_forward_hold": self.forward_hold,
            f"stirrup_{prefix}_backward_hold": self.backward_hold,
        }


class StirrupsHandler:
    """
    Process stirrups inputs and exposes their current states.
    """
    def __init__(self):

        self.stirrups_curve = [(45, 255),
                               (270, 127),
                               (390, 0),
                               (471, -127),
                               (480, -255)]

        self.threshold_fast = 0.11
        self.threshold_slow = 0.3
        self.forward_threshold = 120
        self.backward_threshold = -100
        self.dead_zone = 20
        self.left_stirrup = StirrupState()
        self.right_stirrup = StirrupState()


    def set_new_profile(self, settings):
        """
        Updates stirrups thresholds and dead zone.
        """
        self.threshold_fast = settings["stirrup_speed_threshold_fast"]
        self.threshold_slow = settings["stirrup_speed_threshold_slow"]
        self.forward_threshold = settings["stirrup_forward_threshold"]
        self.backward_threshold = settings["stirrup_backward_threshold"]
        self.dead_zone = settings["stirrup_dead_zone"]
    def update(self):
        """
        Updates stirrups analog values and uses those to update the states.
        """
        current_time = time.monotonic()
        self.left_stirrup.clear()
        self.right_stirrup.clear()
        self.update_analog()
        self.handle_stirrups(self.left_stirrup_value, current_time, self.left_stirrup)
        self.handle_stirrups(self.right_stirrup_value, current_time, self.right_stirrup)


    def handle_stirrups(self, value, current_time, state):
        """
        Processes stirrup input to states
        """
        if -self.dead_zone <= value <= self.dead_zone:
            state.activated = False
            state.last_time = current_time
        elif value < self.backward_threshold:
            state.backward_hold = True
            if not state.activated:
                state.activated = True
                if current_time-state.last_time < self.threshold_fast:
                    state.backward_fast = True
                elif current_time-state.last_time < self.threshold_slow:
                    state.backward_slow = True

        elif value > self.forward_threshold:
            state.forward_hold = True
            if not state.activated:
                state.activated = True
                if current_time-state.last_time < self.threshold_fast:
                    state.forward_fast = True
                elif current_time-state.last_time < self.threshold_slow:
                    state.forward_slow = True


    def update_analog(self):
        """
        Updates stirrups analog values.
        """
        self.left_stirrup_value = interpolate(left_stirrup_input.value, self.stirrups_curve)
        self.right_stirrup_value = interpolate(right_stirrup_input.value, self.stirrups_curve)


    def get_states(self):
        """
        Return stirrups states for horse logic.
        """
        states = self.left_stirrup.get_dict("left") | self.right_stirrup.get_dict("right")
        return states
