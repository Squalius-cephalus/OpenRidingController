"""
This module handles reins analog inputs and returns
processed analog values and reins logic states for the
Horse Logic.
"""

import time
from debug import log
import board
from utils import interpolate
from analogio import AnalogIn

left_rein_input = AnalogIn(board.GP26)
right_rein_input = AnalogIn(board.GP27)


class ReinsHandler:
    """
    Handles all the reins logic and process analog inputs.
    """

    def __init__(self):
        self.left_input = 0
        self.right_input = 0
        self.left_offset = 0
        self.right_offset = 0

        self.states = {
            "reins_pulled": False,
            "reins_pulled_currently": False,
            "reins_pulled_back": False,
        }
        self.previous_states = self.states.copy()
        self.reins_curve = [
            (60, 0),
            (256, 127),
            (340, 256),  # 50%, neutral
            (390, 383),
            (432, 511),
        ]

        self.pulled_threshold_low = 0
        self.pulled_threshold_rein_back = 0
        self.pulled_threshold_high = 0
        self.pulled_time_threshold = 0.35

        self.internal_states = {
            "reins_pulled_time": 0.0,
            "reins_timer_on": False,
            "reins_pulled": False,
        }

        self.reins_timer_started = False
        self.reins_pulled = False
        self.reins_timer = 0.0

    def set_new_profile(self, settings):
        """
        Set new thresholds for reins logic using profile settings.
        Args:
            settings: Current profile settings
        """
        self.pulled_threshold_low = settings["reins_threshold_slow_down"]
        self.pulled_threshold_rein_back = settings["reins_threshold_rein_back"]
        self.pulled_threshold_high = settings["reins_threshold_stop"]

    def update(self):
        """
        Update reins analog values and based on those values,
        update reins logic states.
        """
        current_time = time.monotonic()
        self.reset_states()
        self.update_analog()
        combined_value = self.left_input+self.right_input

        if combined_value >= self.pulled_threshold_high*2:
            self.states["reins_pulled_back"] = True
            self.left_input = 0
            self.right_input = 0
            log("Stop! Reins pulled back! Horse, stop now!")
            return

        if self.left_input >0 and self.right_input > 0 and not self.reins_timer_started:
            self.reins_timer = current_time
            self.reins_timer_started = True

        if self.left_input >= self.pulled_threshold_low and self.right_input >= self.pulled_threshold_low:
            self.reins_pulled = True

        if combined_value == 0 and self.reins_timer_started:
            if self.reins_pulled:
                self.reins_timer_started = False
                self.reins_pulled = False
                if current_time-self.reins_timer <= 0.35:
                    log("Success! Reins pulled! Horse, slow down")
                    self.states["reins_pulled"] = True

        if (
            self.right_input > self.pulled_threshold_rein_back
            and self.left_input > self.pulled_threshold_rein_back
        ):
            self.states["reins_pulled_currently"] = True


    def update_analog(self):
        """
        Update reins analog values and interpolate them.
        """
        self.left_input = interpolate(left_rein_input.value, self.reins_curve)
        self.right_input = interpolate(right_rein_input.value, self.reins_curve)

    def get_states(self):
        """
        Returns reins logic states.
        """
        for i, value in self.states.items():
            if value != self.previous_states[i]:
                log("Reins input report", i, "Has changed", value)
                self.previous_states[i] = value
        return self.states

    def get_analog_states(self):
        """
        Returns reins analog states.
        """
        return self.left_input, self.right_input

    def reset_states(self):
        """
        Reset internal states.
        """
        for key in self.states:
            self.states[key] = False
