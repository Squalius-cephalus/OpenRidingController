import time

import board
from adafruit_simplemath import map_range
from analogio import AnalogIn

left_stirrup_input = AnalogIn(board.GP28)
right_stirrup_input = AnalogIn(board.GP29)

class StirrupsHandler:
    def __init__(self):
        self.debug = True
        self.left_input = 0
        self.right_input = 0
        # IR sensor aren't too accurate to we need to get their "zero" position
        self.left_neutral = 280
        self.right_neutral = 280


        self.min = 0
        self.max = 512

        # TODO: Move these to own settings.json
        # If sensor is on front, set inverted
        self.inverted = True
        self.dead_zone = 20
        self.forward_threshold = 100
        self.backward_threshold = 100
        self.timer_threshold = 1.0


        self.previous_states = states = {
            "stirrup_left_forward":False,
            "stirrup_right_forward":False,
            "stirrup_left_backward":False,
            "stirrup_right_backward": False,
            "stirrup_left_forward_hold": False,
            "stirrup_right_forward_hold": False,
            "stirrup_left_backward_hold": False,
            "stirrup_right_backward_hold": False,
            "both_forward":False,
            "both_backward": False,
            "stirrup_left_neutral":False,
            "stirrup_right_neutral": False,
        }
        self.states = states = {
            "stirrup_left_forward":False,
            "stirrup_right_forward":False,
            "stirrup_left_backward":False,
            "stirrup_right_backward": False,
            "stirrup_left_forward_hold": False,
            "stirrup_right_forward_hold": False,
            "stirrup_left_backward_hold": False,
            "stirrup_right_backward_hold": False,
            "both_forward":False,
            "both_backward": False,
            "stirrup_left_neutral":False,
            "stirrup_right_neutral": False,
        }

        self.left_internal_states = {
            "moving": False,
            "forward": False,
            "backward": False,
            "neutral": False,
            "timer_on": False,
            "time": 0.0,
        }

        self.right_internal_states = {
            "moving": False,
            "forward": False,
            "backward": False,
            "neutral": False,
            "timer_on": False,
            "time": 0.0,
        }

    def update(self):
        self.states = self.reset_states(self.states)
        current_time = time.monotonic()
        self.left_input = left_stirrup_input.value
        self.right_input = right_stirrup_input.value
        min_val, max_val = self.is_invert()
        self.left_input = int(map_range(self.left_input, 0, 65520, min_val, max_val))
        self.right_input = int(map_range(self.right_input, 0, 65520, min_val, max_val))


        self.stirrup_set_states(self.right_input, self.right_internal_states, self.right_neutral, current_time, "right")
        self.stirrup_set_states(self.left_input, self.left_internal_states, self.left_neutral, current_time, "left")

        if self.states["stirrup_left_forward_hold"] and self.states["stirrup_right_forward_hold"]:
            self.states["both_forward"] = True
        elif self.states["stirrup_left_backward_hold"] and self.states["stirrup_right_backward_hold"]:
            self.states["both_backward"] = True





    def stirrup_set_states(self, stirrup_input, internal_states, neutral, current_time, side):
        dead_zone_min = neutral-self.dead_zone
        dead_zone_max = neutral + self.dead_zone


        # print(dead_zone_min, dead_zone_max, stirrup_input)

        if dead_zone_min <= stirrup_input <= dead_zone_max:
            if self.states[f"stirrup_{side}_forward_hold"]:
                time_taken = current_time - internal_states["time"]
                if time_taken < self.timer_threshold:
                    self.states[f"stirrup_{side}_forward"] = True
                internal_states["timer_on"] = False
            elif self.states[f"stirrup_{side}_backward_hold"]:
                time_taken = current_time - internal_states["time"]
                if time_taken < self.timer_threshold:
                    self.states[f"stirrup_{side}_backward"] = True
                internal_states["timer_on"] = False
            self.states[f"stirrup_{side}_neutral"] = True
            self.states[f"stirrup_{side}_forward_hold"] = False
            self.states[f"stirrup_{side}_backward_hold"] = False
            internal_states["timer_on"] = False
        else:
            self.states[f"stirrup_{side}_neutral"] = False
            if internal_states["timer_on"] is False:
                internal_states["time"] = current_time
                internal_states["timer_on"] = True


        if stirrup_input > self.forward_threshold+neutral:
            self.states[f"stirrup_{side}_forward_hold"] = True
        elif stirrup_input < neutral-self.backward_threshold:
            self.states[f"stirrup_{side}_backward_hold"] = True






    def get_states(self):
        for i, value in self.states.items():
            if value != self.previous_states[i]:
                #print(i, "Has changed", value)
                self.previous_states[i] = value

        return self.states

    def get_analog_states(self):
        return self.left_input, self.right_input

    def calibrate(self):
        min_val, max_val = self.is_invert()

        left_input = int(map_range(left_stirrup_input.value, 0, 65520, min_val, max_val))
        right_input = int(map_range(right_stirrup_input.value, 0, 65520, min_val, max_val))

        self.left_neutral = left_input
        self.right_neutral = right_input

        print("Stirrups neutrals", self.left_neutral, self.right_neutral)


    def is_invert(self):
        if self.inverted:
            return [self.max, self.min]
        else:
            return [self.min, self.max]



    @staticmethod
    def reset_states(states):
        for key, value in states.items():
            if not any(word in key for word in ("neutral", "hold")):
                states[key] = False

        return states
