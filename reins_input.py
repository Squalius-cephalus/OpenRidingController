import time

import board
from adafruit_simplemath import map_range
from analogio import AnalogIn

left_rein_input = AnalogIn(board.GP26)
right_rein_input = AnalogIn(board.GP27)

class ReinsHandler:
    def __init__(self):
        self.debug = True
        self.left_input = 0
        self.right_input = 0
        self.left_offset = 0
        self.right_offset = 0

        self.previous_states = self.reset_states()
        self.states = self.reset_states()


        # TODO: Move these to own settings.json
        self.pulled_threshold = 20
        self.pulled_back_threshold = 300
        self.lower_threshold = 10
        self.pulled_time_threshold = 0.35

        self.internal_states = {
        "reins_pulled_time": 0.0,
        "reins_timer_on":False,
        "reins_pulled": False,

        }

    def update(self):
        current_time = time.monotonic()
        self.states = self.reset_states()


        # Apply calibration offset
        self.left_input = left_rein_input.value-self.left_offset
        self.right_input = right_rein_input.value-self.right_offset
        # Map the inputs, 512 is good
        self.left_input = int(map_range(self.left_input, 0, 65520, 0, 512))
        self.right_input = int(map_range(self.right_input, 0, 65520, 0, 512))

        #if self.debug: print(f"Left input: {self.left_input:6d}, Right input: {self.right_input:6d}")

        # is reins pulled?
        if self.right_input + self.left_input > self.lower_threshold:
            self.states["reins_pulled_currently"] = True
            if self.internal_states["reins_timer_on"] is False:
                self.internal_states["reins_pulled_time"] = current_time
                self.internal_states["reins_timer_on"] = True


        if self.left_input >= self.pulled_threshold and self.right_input >= self.pulled_threshold:
            self.internal_states["reins_pulled"] = True

        # How fast reins have been pulled?
        if self.right_input + self.left_input <= self.lower_threshold and self.internal_states["reins_timer_on"]:
            if self.internal_states["reins_pulled"] == True:
                time_taken = current_time-self.internal_states["reins_pulled_time"]
                if self.pulled_time_threshold > time_taken:
                    #print("Success! Reins pulled! Horse, slow down")
                    self.states["reins_pulled"] = True
                self.internal_states["reins_pulled"] = False
            self.internal_states["reins_timer_on"] = False

        # Reins pulled back far, stop that horse!
        if self.left_input >= self.pulled_back_threshold and self.right_input >= self.pulled_back_threshold:
            self.internal_states["reins_pulled"] = False
            self.states["reins_pulled_back"] = True
            self.left_input = 0
            self.right_input = 0


    def get_states(self):
        for i, value in self.states.items():
            if value != self.previous_states[i]:
                #print(i, "Has changed", value)
                self.previous_states[i] = value

        return self.states

    def get_analog_states(self):
        return self.left_input, self.right_input

    def calibrate(self):
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
