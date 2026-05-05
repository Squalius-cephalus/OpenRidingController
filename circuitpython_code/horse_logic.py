import time

class HorseLogicHandler:
    def __init__(self):
        self.states = {
        "start_moving": False,
        "add_speed": False,
        "slow_down": False,
        "stop": False,
        "reverse": False,
        "after_reverse": False,
        "jump": False,
        "right_backward_slow": False,
        "right_backward_fast": False,
        }
        self.previous_states = self.states.copy()
        self.reins_left = 0
        self.reins_right = 0
        self.stirrup_left_last_time = 4
        self.stirrup_right_last_time = 8

        self.ready_to_jump = False
        self.ready_to_reverse = False
        self.in_reverse = False
        self.stopped = False

        self.jump_timer = False
        self.jump_time = 0
        self.jump_toggle =False
        self.jump_time_threshold = 2
        self.reins_pulled_currently = False




    def update(self,input_states):
        # INPUT STATES
        #    "stirrup_left_forward_slow"
        #    "stirrup_right_forward_slow"
        #    "stirrup_left_backward_slow"
        #    "stirrup_right_backward_slow"
        #    "stirrup_left_forward_fast"
        #    "stirrup_right_forward_fast"
        #    "stirrup_left_backward_fast"
        #    "stirrup_right_backward_fast"
        #    "reins_pulled"
        #   "reins_pulled_currently"
        #   "reins_pulled_back"

        current_time = time.monotonic()
        self.reset_states()

        if input_states["stirrup_left_backward_slow"] and not self.in_reverse:
            self.states["start_moving"] = True
        elif input_states["stirrup_left_backward_fast"] and not self.in_reverse:
            self.states["add_speed"] = True

        if input_states["reins_pulled_currently"]:
            if not self.ready_to_reverse:
                self.ready_to_reverse = True
        else:
            if self.in_reverse:
                 self.in_reverse = False
                 self.states["after_reverse"] = True

            self.ready_to_reverse = False
            self.states["stop"] = False
            self.stopped = False

        if self.ready_to_reverse and (input_states["stirrup_left_forward_slow"] or input_states["stirrup_left_forward_fast"] ):
            if not self.in_reverse:
                self.states["reverse"] = True
                self.in_reverse = True
        
        if input_states["reins_pulled"]:
            self.states["slow_down"] = True
        if input_states["stirrup_right_backward_fast"]:
            self.states["right_backward_fast"] = True
        if input_states["stirrup_right_backward_slow"]:
            self.states["right_backward_slow"] = True
            
        
        if input_states["reins_pulled_back"]:
            self.reset_states()
            if not self.stopped:
                self.reins_left = 0
                self.reins_right = 0
                self.stopped = True
                self.states["stop"] = True

    def get_states(self):
        for i, value in self.states.items():
            if value != self.previous_states[i]:
                print("Horse Logic report",i, "Has changed", value)
                self.previous_states[i] = value
        return self.states


    def update_analog(self, analog_input):
        self.reins_left = analog_input[0]
        self.reins_right = analog_input[1]
        

    def get_analog_states(self):
        if self.in_reverse:
            return int(self.reins_left/2), int(self.reins_right/2)
        else:
            return self.reins_left, self.reins_right

    def reset_states(self):
        for key in self.states:
            self.states[key] = False





