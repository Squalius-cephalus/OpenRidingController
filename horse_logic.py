import time

class HorseLogicHandler:
    def __init__(self):
        self.states = self.reset_states()
        self.previous_states = self.reset_states()
        self.reins_left = 0
        self.reins_right = 0

        self.ready_to_jump = False
        self.ready_to_reverse = False
        self.in_reverse = False
        self.stopped = False

        self.jump_timer = False
        self.jump_time = 0
        self.jump_toggle =False
        self.jump_time_threshold = 2




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


        if input_states['reins_pulled_back']:
            self.stopped = True
            self.states['Stop'] = True
        else:
            self.stopped = False
        if not self.stopped:
            self.handle_reverse(input_states)

            if not self.ready_to_reverse or not self.in_reverse:
                self.handle_jump(input_states, current_time)



                if not self.ready_to_jump:
                    self.handle_speed(input_states)
    def handle_jump(self, input_states, current_time):

        if input_states['stirrup_right_forward_hold'] and not self.ready_to_jump:
            self.ready_to_jump = True
            print("ready to jump")
        if not input_states['stirrup_right_forward_hold']:
            self.ready_to_jump = False

        if input_states['stirrup_left_forward'] and self.ready_to_jump:
            self.ready_to_jump = False
            self.states["Jump"] = True






    def handle_speed(self, input_states):
        if input_states['stirrup_left_backward']:
            self.states['Start Moving'] = True
        if input_states['stirrup_left_backward']:
            self.states['Add Speed'] = True
        if input_states['reins_pulled']:
            self.states['Slow Down'] = True

    def handle_reverse(self, input_states):
        if input_states["reins_pulled_currently"]:
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
                #print(i, "Has changed", value)
                self.previous_states[i] = value

        return self.states

    def update_analog(self, analog_input):
        self.reins_left = analog_input[0]
        self.reins_right = analog_input[1]

    @staticmethod
    def reset_states():
        states = {
            "Start Moving": False,
            "Add Speed": False,
        "Slow Down": False,
        "Stop": False,
        "Reverse": False,
        "After Reverse": False,
        "Jump": False,
        }
        return states





