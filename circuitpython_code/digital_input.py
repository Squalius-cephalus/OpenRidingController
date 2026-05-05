import time

from adafruit_simplemath import map_range

# TODO: REWRITE THIS CLASS
class ButtonHandler:
    def __init__(self,button1, button2, button3, button4):
        self.states = {
            "button1": False,
            "button2": False,
            "button3": False,
            "button4": False,
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
            "button1": False,
            "button2": False,
            "button3": False,
            "button4": False,
        }
        if not self.button1.value and self.button1_pressed == False:
            self.states["button1"] = True
            self.button1_pressed = True

        if not self.button2.value and self.button2_pressed == False:
            self.states["button2"] = True
            self.button2_pressed = True

        if not self.button3.value and self.button3_pressed == False:
            self.states["button3"] = True
            self.button3_pressed = True

        if not self.button4.value and self.button4_pressed == False:
            self.states["button4"] = True
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
