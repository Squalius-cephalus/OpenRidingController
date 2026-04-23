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
        #    "stirrup_left_forward"
        #    "stirrup_right_forward"
        #    "stirrup_left_backward"
        #    "stirrup_right_backward"
        #    "both_forward"
        #    "both_backward"
        #    "reins_pulled"
        #   "reins_pulled_currently"
        #   "reins_pulled_back"

        self.states = self.reset_states()
        current_time = time.monotonic()
        self.reins_pulled_currently = input_states["reins_pulled_currently"]

        # Stopping overrides everything, then reverse, jump etc
        if input_states['reins_pulled_back']:
            self.stopped = True
            self.states['Stop'] = True
        else:
            self.stopped = False
        if not self.stopped:
            self.handle_reverse(input_states)
            if not self.ready_to_reverse or not self.in_reverse:
                self.handle_jump(input_states, current_time)
                self.handle_speed(input_states)
                if not self.states["Jump"]:
                    self.handle_extra_outputs(input_states)
    def handle_jump(self, input_states, current_time):

        if input_states['stirrup_left_forward']:
            self.stirrup_left_last_time = current_time
            self.jump_toggle = True
        if input_states['stirrup_right_forward']:
            self.stirrup_right_last_time = current_time
            self.jump_toggle = True

        if self.jump_toggle:
            left_time = current_time - self.stirrup_left_last_time
            right_time = current_time - self.stirrup_right_last_time

            if abs(left_time-right_time) < 1:
                self.states["Jump"] = True
                self.jump_toggle = False


    def handle_extra_outputs(self, input_states):
        if input_states['stirrup_right_backward']:
            self.states['Right Backward'] = True



    def handle_speed(self, input_states):
        if input_states['stirrup_left_backward']:
            self.states['Add Speed'] = True
        if input_states['reins_pulled']:
            self.states['Slow Down'] = True

    def handle_reverse(self, input_states):
        if input_states["reins_pulled_currently"] and not self.ready_to_jump:
            self.ready_to_reverse = True
            if input_states["stirrup_left_forward"]:
                if not self.in_reverse:
                    self.in_reverse = True
                    self.states["Reverse"] = True
        else:
            self.ready_to_reverse = False
            if self.in_reverse:
                self.states["After Reverse"] = True
                self.in_reverse = False

    def get_states(self):
        for i, value in self.states.items():
            if value != self.previous_states[i]:
                print(i, "Has changed", value)
                self.previous_states[i] = value

        return self.states

    def update_analog(self, analog_input):
        self.reins_left = analog_input[0]
        self.reins_right = analog_input[1]
        if self.states['Stop']:
            print("stop stop stop")

            self.reins_left = 0
            self.reins_right = 0

    def get_analog_states(self):


        return self.reins_left, self.reins_right

    @staticmethod
    def reset_states():
        states = {
            "Add Speed": False,
        "Slow Down": False,
        "Stop": False,
        "Reverse": False,
        "After Reverse": False,
        "Jump": False,
        "Right Backward": False,
        }
        return states





