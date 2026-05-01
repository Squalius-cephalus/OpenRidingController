import time

class HorseLogicHandler:
    def __init__(self):
        self.states = self.reset_states()
        self.previous_states = self.reset_states()
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
        self.states = self.reset_states()

        if input_states["stirrup_left_backward_slow"] and not self.in_reverse:
            self.states["StartMoving"] = True
        elif input_states["stirrup_left_backward_fast"] and not self.in_reverse:
            self.states["AddSpeed"] = True





        if input_states["reins_pulled_currently"]:
            if not self.ready_to_reverse:
                self.ready_to_reverse = True
        else:
            if self.in_reverse:
                 self.in_reverse = False
                 self.states["AfterReverse"] = True

            self.ready_to_reverse = False
            self.states["Stop"] = False
            self.stopped = False

        if self.ready_to_reverse and (input_states["stirrup_left_forward_slow"] or input_states["stirrup_left_forward_fast"] ):
            if not self.in_reverse:
                self.states["Reverse"] = True
                self.in_reverse = True
        
        if input_states["reins_pulled"]:
            self.states["SlowDown"] = True
        if input_states["stirrup_right_backward_fast"]:
            self.states["RightBackwardFast"] = True
        if input_states["stirrup_right_backward_slow"]:
            self.states["RightBackwardSlow"] = True
            
        
        if input_states["reins_pulled_back"]:
            self.reset_states()
            if not self.stopped:
                self.reins_left = 0
                self.reins_right = 0
                self.stopped = True
                self.states["Stop"] = True



            



        


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

    @staticmethod
    def reset_states():
        states = {
        "StartMoving": False,
        "AddSpeed": False,
        "SlowDown": False,
        "Stop": False,
        "Reverse": False,
        "AfterReverse": False,
        "Jump": False,
        "RightBackwardSlow": False,
        "RightBackwardFast": False,
        }
        return states





