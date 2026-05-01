import time

import board
from utils import interpolate, get_current_position
from analogio import AnalogIn

left_stirrup_input = AnalogIn(board.GP28)
right_stirrup_input = AnalogIn(board.GP29)

class StirrupsHandler:
    def __init__(self, settings=0):
        
        self.neutral_right = 255
        self.neutral_left = 255
        self.left_stirrup = 255
        self.right_stirrup = 255



        self.stirrups_curve_right = [
    (55, 255),
    (161, 127),
    (346, 0),  #50%, neutral
    (400, -127),
    (432, -255)
]
        



        self.stirrups_curve_left = [
    (55, 255),
    (161, 127),
    (346, 0),  #50%, neutral
    (400, -127),
    (432, -255)
]
                
        self.dead_zone = 10
        self.neutral_right = -11
        self.threshold_fast = 0.4
        self.threshold_slow = 0.8



        self.right_logic = {
            "neutral_threshold": 9,
            "forward_threshold": 220,
            "backward_threshold": -130,
            "timer_on": False,
            "timer":0,
            "forward_flag": False,
            "backward_flag": False,
            "forward_fast": False,
            "forward_slow": False,
            "backward_fast": False,
            "backward_slow": False,
        }

        self.left_logic = {
            "neutral_threshold": 9,
            "forward_threshold": 220,
            "backward_threshold": -130,
            "timer_on": False,
            "timer":0,
            "forward_flag": False,
            "backward_flag": False,
            "forward_fast": False,
            "forward_slow": False,
            "backward_fast": False,
            "backward_slow": False,
        }



    def update(self):
        current_time = time.monotonic()
        

        self.update_analog()
        self.handle_stirrup_speed(self.left_stirrup,self.left_logic,current_time)
        self.handle_stirrup_speed(self.right_stirrup,self.right_logic,current_time)

    def update_analog(self):
        self.left_stirrup = interpolate(left_stirrup_input.value, self.stirrups_curve_left)
        self.right_stirrup = interpolate(right_stirrup_input.value, self.stirrups_curve_right)
        

    def handle_stirrup_speed(self, value, logic, current_time):
        logic["forward_fast"] = False
        logic["forward_slow"] = False
        logic["backward_fast"] = False
        logic["backward_slow"] = False

        if -self.dead_zone <= value <= self.dead_zone:
            
            if logic["timer_on"]:
                time_taken = current_time-logic["timer"]
                if logic["forward_flag"]:
                    if time_taken<= self.threshold_fast:
                        logic["forward_fast"] = True
                    elif time_taken<= self.threshold_slow:
                        logic["forward_slow"] = True
                        print(time_taken)
                    logic["forward_flag"] = False
                if logic["backward_flag"]:
                    if time_taken<= self.threshold_fast:
                        logic["backward_fast"] = True
                    elif time_taken<= self.threshold_slow:
                        logic["backward_slow"] = True
                    logic["backward_flag"] = False

                logic["timer"] = 0
                logic["timer_on"] = False      
        else:# Not in neutral position
            if not logic["timer_on"]:
                logic["timer"] = current_time
                logic["timer_on"] = True
            if value >= logic["forward_threshold"]:
                logic["forward_flag"] = True
            elif value <=  logic["backward_threshold"]:
                logic["backward_flag"] = True



    def calibrate(self):

        print("calibration")
        time.sleep(1)


        positions = ["neutral", "backward", "forward"]
        for i in range(0,3):
            print(positions[i], " position wait 3 sec")
            time.sleep(3)
            self.update_analog()
            position = positions[i]+"_threshold"
            self.right_logic[position] = self.right_stirrup
            self.left_logic[position] = self.left_stirrup

        print(self.right_logic, self.left_logic)


    def get_states(self):
        states = {
        "stirrup_left_forward_fast":self.left_logic["forward_fast"],
        "stirrup_left_forward_slow":self.left_logic["forward_slow"],
        "stirrup_left_backward_fast":self.left_logic["backward_fast"],
        "stirrup_left_backward_slow":self.left_logic["backward_slow"],

        "stirrup_right_forward_fast":self.right_logic["forward_fast"],
        "stirrup_right_forwardd_slow":self.right_logic["forward_slow"],
        "stirrup_right_backward_fast":self.right_logic["backward_fast"],
        "stirrup_right_backward_slow":self.right_logic["backward_slow"],
        }

        for i,ii in states.items():
            if ii:
                print(i)

        return states

        
        
        





            

        

        

