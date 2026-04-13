import time

from adafruit_simplemath import map_range


DEBUG = True
now = time.monotonic()
class StirrupHandler:
    def __init__(self, left_stirrup_input, right_stirrup_input):
        self.left_stirrup_input = left_stirrup_input
        self.right_stirrup_input = right_stirrup_input
        self.left_offset = 0
        self.right_offset = 0
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
            "left_stirrup_forward": False,
                "right_stirrup_forward": False,
                "left_stirrup_backward": False,
                "right_stirrup_backward": False,
        }
        self.left_timer = 0
        self.right_timer = 0
        self.both_timer = 0
        self.dead_zone = 10

        self.trigger_forward = -60
        self.trigger_backward = 50
        self.last_run = 0
        self.states = {
            "LeftForward": False,
            "LeftBackward": False,
            "RightForward": False,
            "RightBackward": False,
            "BothForward": False,
            "BothBackward": False,
        }

    def reset(self):
        return


    def update(self):

        self.left = int(map_range(self.left_stirrup_input.value, 0, 65520, 0, 512))-self.right_offset
        self.right = int(map_range(self.right_stirrup_input.value, 0, 65520, 0, 512))-self.left_offset
        self.current_time = time.monotonic()

        #print(self.left, self.right)

        self.states = {
            "LeftForward": False,
            "LeftBackward": False,
            "RightForward": False,
            "RightBackward": False,
            "BothForward": False,
            "BothBackward": False,
        }



        for side in ["left", "right"]:
            value = getattr(self, side)
            forward_flag = f"{side}_forward"
            backward_flag = f"{side}_backward"
            timer_attr = f"{side}_timer"

            # Forward trigger
            if value <= self.trigger_forward and not getattr(self, forward_flag):
                setattr(self, timer_attr, self.current_time)
                setattr(self, forward_flag, True)
                self.internal_states[f"{side}_stirrup_forward"] = True

            # Backward trigger
            elif value >= self.trigger_backward and not getattr(self, backward_flag):
                setattr(self, timer_attr, self.current_time)
                setattr(self, backward_flag, True)
                self.internal_states[f"{side}_stirrup_backward"] = True

            # Dead zone reset
            if -self.dead_zone <= value <= self.dead_zone:
                setattr(self, timer_attr, self.current_time)
                setattr(self, forward_flag, False)
                setattr(self, backward_flag, False)

        if self.current_time - self.last_run >= 0.3:
            self.last_run = self.current_time


            lf = self.internal_states["left_stirrup_forward"]
            rf = self.internal_states["right_stirrup_forward"]
            lb = self.internal_states["left_stirrup_backward"]
            rb = self.internal_states["right_stirrup_backward"]

            if lf and rf:
                self.states["BothForward"] = True
            elif lb and rb:
                self.states["BothBackward"] = True
            elif lf:
                self.states["LeftForward"] = True
            elif rf:
                self.states["RightForward"] = True
            elif lb:
                self.states["LeftBackward"] = True
            elif rb:
                self.states["RightBackward"] = True

            # Reset states
            for key in self.internal_states:
                self.internal_states[key] = False








            self.internal_states = {
                "left_stirrup_forward": False,
                "right_stirrup_forward": False,
                "left_stirrup_backward": False,
                "right_stirrup_backward": False,
            }



    def get_states(self):
        return self.states

    def calibrate(self):
        left_samples = []
        right_samples = []

        for i in range(5):
            left_val = self.left
            right_val = self.right
            time.sleep(0.1)
            left_samples.append(left_val)
            right_samples.append(right_val)

        self.left_offset = int(sum(left_samples) / len(left_samples))
        self.right_offset = int(sum(right_samples) / len(right_samples))

        print("Calibration done, stirrup offsets:", self.left_offset, self.right_offset)


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
