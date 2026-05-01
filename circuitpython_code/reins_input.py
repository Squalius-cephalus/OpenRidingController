import time

import board
from utils import interpolate
from analogio import AnalogIn

left_rein_input = AnalogIn(board.GP26)
right_rein_input = AnalogIn(board.GP27)

class ReinsHandler:
    def __init__(self, settings):
        self.debug = True
        self.left_input = 0
        self.right_input = 0
        self.left_offset = 0
        self.right_offset = 0

        self.previous_states = self.reset_states()
        self.states = self.reset_states()

        self.reins_curve = [
    (60, 0),
    (256, 127),
    (340, 256),  #50%, neutral
    (390, 383),
    (432, 511)
]


        
        self.pulled_threshold_low = settings["ReinsThresholdSlowDown"]
        self.pulled_threshold_mid = settings["ReinsThresholdReinBack"]
        self.pulled_threshold_high = settings["ReinsThresholdStop"]
        self.reins_dead_zone = settings["ReinsDeadZone"]
        self.pulled_time_threshold = 0.35

        self.internal_states = {
        "reins_pulled_time": 0.0,
        "reins_timer_on":False,
        "reins_pulled": False,

        }

    def update(self):
        current_time = time.monotonic()
        self.states = self.reset_states()

        self.update_analog()

        # is reins pulled?
        if self.right_input > self.reins_dead_zone and self.left_input > self.reins_dead_zone:
            if self.internal_states["reins_timer_on"] is False:
                self.internal_states["reins_pulled_time"] = current_time
                self.internal_states["reins_timer_on"] = True

        if self.right_input > self.pulled_threshold_mid and self.left_input > self.pulled_threshold_mid:
            self.states["reins_pulled_currently"] = True


        if self.left_input >= self.pulled_threshold_low and self.right_input >= self.pulled_threshold_low:
            self.internal_states["reins_pulled"] = True

        # How fast reins have been pulled?
        if self.right_input + self.left_input < self.reins_dead_zone and self.internal_states["reins_timer_on"]:
            if self.internal_states["reins_pulled"] == True:
                time_taken = current_time-self.internal_states["reins_pulled_time"]
                if self.pulled_time_threshold > time_taken:
                    print("Success! Reins pulled! Horse, slow down")
                    self.states["reins_pulled"] = True
                self.internal_states["reins_pulled"] = False
            self.internal_states["reins_timer_on"] = False

        # Reins pulled back far, stop that horse!
        if self.left_input >= self.pulled_threshold_high and self.right_input >= self.pulled_threshold_high:
            self.internal_states["reins_pulled"] = False
            self.states["reins_pulled_back"] = True
            self.left_input = 0
            self.right_input = 0

    def update_analog(self):
        self.left_input = interpolate(left_rein_input.value, self.reins_curve)
        self.right_input = interpolate(right_rein_input.value, self.reins_curve)
        
    def get_states(self):
        for i, value in self.states.items():
            if value != self.previous_states[i]:
                print(i, "Has changed", value)
                self.previous_states[i] = value

        return self.states

    def get_analog_states(self):
        return self.left_input, self.right_input

    def calibrate(self):
        # TODO: REDO THIS
        self.left_offset = left_rein_input.value
        self.right_offset = right_rein_input.value
        print("Reins offsets ", self.left_offset, self.right_offset)
    @staticmethod
    def reset_states():
        states = {
            "reins_pulled":False,
            "reins_pulled_currently": False,
            "reins_pulled_back":False,
        }
        return states
