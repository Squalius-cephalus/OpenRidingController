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
    (0, 0),
    (255, 255),
    (511, 511)
]
        



        self.stirrups_curve_left = [
    (0, 0),
    (255, 255),
    (511, 511)
]
                
        self.dead_zone = 10
        self.neutral_right = -11
        self.threshold_fast = 0.4
        self.threshold_slow = 0.8




        self.right_logic = self.reset_states()
        self.left_logic = self.reset_states()



    def update(self):
        current_time = time.monotonic()

        self.left_logic["forward_fast"] = False
        self.left_logic["forward_slow"] = False
        self.left_logic["backward_fast"] = False
        self.left_logic["backward_slow"] = False

        self.right_logic["forward_fast"] = False
        self.right_logic["forward_slow"] = False
        self.right_logic["backward_fast"] = False
        self.right_logic["backward_slow"] = False
        
        
        

        self.update_analog()
        self.handle_stirrup_speed(self.left_stirrup,self.left_logic,current_time)
        self.handle_stirrup_speed(self.right_stirrup,self.right_logic,current_time)



    def update_analog(self):
        self.left_stirrup = interpolate(left_stirrup_input.value, self.stirrups_curve_left)
        self.right_stirrup = interpolate(right_stirrup_input.value, self.stirrups_curve_right)
        

    def handle_stirrup_speed(self, value, logic, current_time):
        if (current_time-logic["last_time"] >= 0.01):
            logic["last_time"] = current_time
            speed = (value-logic["last_value"])/0.01 /100
            logic["last_value"] = value
            if abs(speed) > 30 and value < 100:
                if (current_time - logic["last_activated"]) > 0.3:
                    logic["forward_fast"] = True
                    logic["last_activated"] = current_time
            elif abs(speed) > 30 and value >350:
                if (current_time - logic["last_activated"]) > 0.3:
                    logic["backward_fast"] = True
                    logic["last_activated"] = current_time
            elif abs(speed) > 20 and value >350:
                if (current_time - logic["last_activated"]) > 0.3:
                    logic["backward_slow"] = True
                    logic["last_activated"] = current_time
            elif abs(speed) > 20 and value < 100:
                if (current_time - logic["last_activated"]) > 0.3:
                    logic["forward_slow"] = True
                    logic["last_activated"] = current_time


                


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

    def reset_states(self):
        states = {
            "last_time":0,
            "last_value":350,
            "last_activated":0,
            "forward_fast": False,
            "forward_slow": False,
            "backward_fast": False,
            "backward_slow": False,
        }
        return states


    def get_states(self):
        states = {
        "stirrup_left_forward_fast":self.left_logic["forward_fast"],
        "stirrup_left_forward_slow":self.left_logic["forward_slow"],
        "stirrup_left_backward_fast":self.left_logic["backward_fast"],
        "stirrup_left_backward_slow":self.left_logic["backward_slow"],

        "stirrup_right_forward_fast":self.right_logic["forward_fast"],
        "stirrup_right_forward_slow":self.right_logic["forward_slow"],
        "stirrup_right_backward_fast":self.right_logic["backward_fast"],
        "stirrup_right_backward_slow":self.right_logic["backward_slow"],
        }

        return states

        
        
        





            

        

        

