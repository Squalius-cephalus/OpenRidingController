"""
This module process reins and stirrups states and convert
those something that Output Manager can understand.
"""

from utils.debug import log
class HorseLogicHandler:
    """
        Handles reins and stirrups states and combines those
        to new states that Output Manager can understand.
    """
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
        """
        Updates internal states based on reins and stirrups states.
        """
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

        self.reset_states()

        # Start moving or add speed
        if input_states["stirrup_left_backward_slow"] and not self.in_reverse:
            self.states["start_moving"] = True
        elif input_states["stirrup_left_backward_fast"] and not self.in_reverse:
            self.states["add_speed"] = True

        # Reverse a.k.a Rein Back
        if input_states["reins_pulled_currently"]:
            if not self.ready_to_reverse:
                self.ready_to_reverse = True
        else:
            if self.in_reverse:
                self.in_reverse = False
                self.states["after_reverse"] = True
            self.ready_to_reverse = False

        if self.ready_to_reverse and ((input_states["stirrup_left_forward_slow"]
                                       or input_states["stirrup_left_forward_fast"] )):
            if not self.in_reverse:
                self.states["reverse"] = True
                self.in_reverse = True

        if input_states["reins_pulled"]:
            if self.ready_to_jump:
                self.states["jump"] = True
            else:
                self.states["slow_down"] = True

        if input_states["stirrup_left_forward_hold"] and input_states["stirrup_right_forward_hold"]:
            self.ready_to_jump = True
        else:
            self.ready_to_jump = False

        if input_states["stirrup_right_backward_fast"]:
            self.states["right_backward_fast"] = True
        if input_states["stirrup_right_backward_slow"]:
            self.states["right_backward_slow"] = True

        # Stop, overrides everything!
        if input_states["reins_pulled_back"]:
            self.reset_states()
            if not self.stopped:
                self.reins_left = 0
                self.reins_right = 0
                self.stopped = True
                self.states["stop"] = True
        else:
            self.stopped = False

    def get_states(self):
        """
        Retrieve current states.

        Returns:
            Dictionary horse logig state data
        """
        for i, value in self.states.items():
            if value != self.previous_states[i]:
                log("Horse Logic report",i, "Has changed", value)
                self.previous_states[i] = value
        return self.states

    def update_analog(self, analog_input):
        """
        Updates reins analog states to the class.

        Args:
            analog_input: Reins analog input data in tuple
        """
        self.reins_left = analog_input[0]
        self.reins_right = analog_input[1]

    def get_analog_states(self):
        """
        Returns modified reins analog states.
        """
        return self.reins_left, self.reins_right

    def reset_states(self):
        """
        Resets internal states.
        """
        for key in self.states:
            self.states[key] = False
