import time

from adafruit_simplemath import map_range


DEBUG = True
now = time.monotonic()
class StirrupHandler:
    def __init__(self, left_stirrup_input, right_stirrup_input):
        self.left_stirrup_input = left_stirrup_input
        self.right_stirrup_input = right_stirrup_input
        self.left_neutral = 255
        self.right_neutral = 255
        self.now = time.monotonic()
        self.current_time = time.monotonic()
        self.left = 412
        self.right = 412
        self.left_forward = False
        self.right_forward = False
        self.left_backward = False
        self.right_backward = False
        self.ready = False

        self.internal_states = {
                "left_stirrup_forward_fast": False,
                "right_stirrup_forward_fast": False,
                "left_stirrup_backward_fast": False,
                "right_stirrup_backward_fast": False,
            "left_stirrup_forward_slow": False,
            "right_stirrup_forward_slow": False,
            "left_stirrup_backward_slow": False,
            "right_stirrup_backward_slow": False,

        }
        self.left_timer = 0
        self.right_timer = 0
        self.left_timer_on = False
        self.right_timer_on = False
        self.both_timer = 0
        self.dead_zone = 20

        # TODO: Move these to own settings.json!
        self.time_threshold = 2.0
        self.slow = 0.2
        self.fast = 0.05
        self.trigger_forward = 120
        self.trigger_backward = 120


        self.last_run = 0
        self.states = {
            "LeftForwardSlow": False,
            "LeftBackwardSlow": False,
            "RightForwardSlow": False,
            "RightBackwardSlow": False,
            "LeftForwardFast": False,
            "LeftBackwardFast": False,
            "RightForwardFast": False,
            "RightBackwardFast": False,
            "BothForward": False,
            "BothBackward": False,
        }

    def reset(self):
        return


    def update(self):

        self.left = int(map_range(self.left_stirrup_input.value, 0, 65520, 0, 512))
        self.right = int(map_range(self.right_stirrup_input.value, 0, 65520, 0, 512))
        self.current_time = time.monotonic()


        # Reset states
        for key in self.states:
            self.states[key] = False

        for side in ["left", "right"]:
            value = getattr(self, side)
            forward_flag = f"{side}_forward"
            backward_flag = f"{side}_backward"
            timer_attr = f"{side}_timer"
            timer_state = f"{side}_timer_on"
            neutral = f"{side}_neutral"

            trigger_forward = getattr(self, neutral)-self.trigger_forward
            trigger_backward = getattr(self, neutral) + self.trigger_backward
            dead_zone_min = getattr(self, neutral)-self.dead_zone
            dead_zone_max = getattr(self, neutral)+self.dead_zone

            # Forward trigger
            if value <= trigger_forward and not getattr(self, forward_flag):
                if DEBUG: print(trigger_forward, "position",value, "dead_zone_min", dead_zone_min, "dead_zone_max", dead_zone_max)
                speed = self.current_time-getattr(self, timer_attr)
                if speed < self.time_threshold:
                    setattr(self, forward_flag, True)
                    if speed > self.slow:
                        self.internal_states[f"{side}_stirrup_forward_slow"] = True
                    elif speed < self.slow:
                        self.internal_states[f"{side}_stirrup_forward_fast"] = True



            # Backward trigger
            elif value >= trigger_backward and not getattr(self, backward_flag):
                if DEBUG: print(trigger_backward, "position",value, "dead_zone_min", dead_zone_min, "dead_zone_max", dead_zone_max)
                speed = self.current_time - getattr(self, timer_attr)
                if speed < self.time_threshold:
                    setattr(self, backward_flag, True)
                    if speed > self.slow:
                        self.internal_states[f"{side}_stirrup_backward_slow"] = True
                    elif speed < self.slow:
                        self.internal_states[f"{side}_stirrup_backward_fast"] = True



            # Dead zone reset
            if dead_zone_min <= value <= dead_zone_max:
                setattr(self, timer_attr, self.current_time)
                setattr(self, forward_flag, False)
                setattr(self, backward_flag, False)
                setattr(self, timer_state, False)
            else:
                if getattr(self, timer_state) is False:
                    setattr(self, timer_attr, self.current_time)
                    setattr(self, timer_state, True)




        if self.current_time - self.last_run >= 0.3:
            self.last_run = self.current_time


            lfs = self.internal_states["left_stirrup_forward_slow"]
            rfs = self.internal_states["right_stirrup_forward_slow"]
            lbs = self.internal_states["left_stirrup_backward_slow"]
            rbs = self.internal_states["right_stirrup_backward_slow"]
            lff = self.internal_states["left_stirrup_forward_fast"]
            rff = self.internal_states["right_stirrup_forward_fast"]
            lbf = self.internal_states["left_stirrup_backward_fast"]
            rbf = self.internal_states["right_stirrup_backward_fast"]

            if lff and rff:
                self.states["BothForward"] = True
            elif lbf and rbf:
                self.states["BothBackward"] = True
            elif lfs:
                self.states["LeftForwardSlow"] = True
            elif rfs:
                self.states["RightForwardSlow"] = True
            elif lbs:
                self.states["LeftBackwardSlow"] = True
            elif rbs:
                self.states["RightBackwardSlow"] = True
            elif lff:
                self.states["LeftForwardFast"] = True
            elif rff:
                self.states["RightForwardFast"] = True
            elif lbf:
                self.states["LeftBackwardFast"] = True
            elif rbf:
                self.states["RightBackwardFast"] = True

            # Reset internal states
            for key in self.internal_states:
                self.internal_states[key] = False





    def get_states(self):
        return self.states

    def calibrate(self):
        left_samples = []
        right_samples = []

        for i in range(5):
            left_val = int(map_range(self.left_stirrup_input.value, 0, 65520, 0, 512))
            right_val = int(map_range(self.right_stirrup_input.value, 0, 65520, 0, 512))
            time.sleep(0.1)
            left_samples.append(left_val)
            right_samples.append(right_val)

        self.left_neutral = int(sum(left_samples) / len(left_samples))
        self.right_neutral = int(sum(right_samples) / len(right_samples))

        print("Calibration done, stirrup neutral positions:", self.left_neutral, self.right_neutral)


# TODO: REWRITE THIS CLASS
class ButtonHandler:
    def __init__(self,button1, button2, button3, button4):
        self.states = {
            "Button1": False,
            "Button2": False,
            "Button3": False,
            "Button4": False,
        }
        self.button1_pressed = False
        self.button2_pressed = False
        self.button3_pressed = False
        self.button4_pressed = False

        self.button1 = button1
        self.button2 = button2
        self.button3 = button3
        self.button4 = button4

    def update(self):
        self.states = {
            "Button1": False,
            "Button2": False,
            "Button3": False,
            "Button4": False,
        }
        if not self.button1.value and self.button1_pressed == False:
            self.states["Button1"] = True
            self.button1_pressed = True

        if not self.button2.value and self.button2_pressed == False:
            self.states["Button2"] = True
            self.button2_pressed = True

        if not self.button3.value and self.button3_pressed == False:
            self.states["Button3"] = True
            self.button3_pressed = True

        if not self.button4.value and self.button4_pressed == False:
            self.states["Button4"] = True
            self.button4_pressed = True



        if self.button1.value:
            self.button1_pressed = False
        if self.button2.value:
            self.button2_pressed = False
        if self.button3.value:
            self.button3_pressed = False
        if self.button4.value:
            self.button4_pressed = False

    def get_states(self):
        return self.states
