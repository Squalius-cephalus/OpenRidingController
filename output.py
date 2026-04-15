import board
import digitalio
import neopixel
import json
from analogio import AnalogIn
from analog_input import ReinsHandler
from digital_input import StirrupHandler, ButtonHandler
from reins_input import ReinsHandler
from stirrup_input import StirrupHandler


import time





with open("/profiles.json", "r") as f:
    data = json.load(f)

DEBUG = True

loaded_profiles = data["profiles"]

profile_button = digitalio.DigitalInOut(board.GP15)
profile_button.direction = digitalio.Direction.INPUT
profile_button.pull = digitalio.Pull.UP

pause_button = digitalio.DigitalInOut(board.GP14)
pause_button.direction = digitalio.Direction.INPUT
pause_button.pull = digitalio.Pull.UP

button1 = digitalio.DigitalInOut(board.GP2)
button1.direction = digitalio.Direction.INPUT
button1.pull = digitalio.Pull.UP

button2 = digitalio.DigitalInOut(board.GP3)
button2.direction = digitalio.Direction.INPUT
button2.pull = digitalio.Pull.UP

button3 = digitalio.DigitalInOut(board.GP4)
button3.direction = digitalio.Direction.INPUT
button3.pull = digitalio.Pull.UP

button4 = digitalio.DigitalInOut(board.GP5)
button4.direction = digitalio.Direction.INPUT
button4.pull = digitalio.Pull.UP


left_rein_in = AnalogIn(board.GP26)
right_rein_in = AnalogIn(board.GP27)
left_stirrup_in = AnalogIn(board.GP28)
right_stirrup_in = AnalogIn(board.GP29)

onboard_led = neopixel.NeoPixel(board.GP16, 1, brightness=0.3, auto_write=True)

setup_calibration = False

class ProfileManager:
    def __init__(self, profiles, pixel):
        self.profiles = profiles
        self.pixel = pixel
        self.current_index = 0
        self.current_profile = self.profiles[self.current_index]
        if DEBUG:
            print("Active profile:", self.current_profile["Name"])
        self.pixel[0] = self.current_profile["Color"]

    def change_profile(self):
        self.current_index = (self.current_index + 1) % len(self.profiles)
        self.current_profile = self.profiles[self.current_index]
        if DEBUG:
            print("Active profile:", self.current_profile["Name"])
        self.pixel[0] = self.current_profile["Color"]



        time.sleep(0.3)


profile_manager = ProfileManager(loaded_profiles, onboard_led)
reins_handler = ReinsHandler()
stirrup_handler = StirrupHandler()




def calibrate():
    stirrup_handler.calibrate()
    reins_handler.calibrate()


def pause_inputs():

    last_toggle = 0
    blink = False
    original_color = profile_manager.pixel[0]
    time.sleep(0.5)
    print("Pause ON")

    while True:
        current_time = time.monotonic()
        if now - last_toggle >= 0.5:
            last_toggle = current_time
            blink = not blink
            profile_manager.pixel[0] = [0, 0, 0] if blink else original_color

        if not pause_button.value:
            time.sleep(0.5)
            print("Pause OFF")
            profile_manager.pixel[0] = original_color
            time.sleep(0.5)
            break


while True:

    now = time.monotonic()

    if not setup_calibration:
        calibrate()
        setup_calibration = True

    if not profile_button.value:
        time.sleep(0.1)
        button_held = 0

        while not profile_button.value:
            button_held += 1
            time.sleep(0.01)

            if button_held >= 100:
                calibrate()

        if button_held < 100:
            profile_manager.change_profile()

    if not pause_button.value:
        pause_inputs()

    # Update states from inputs
    reins_handler.update()
    stirrup_handler.update()


    stirrup_states = stirrup_handler.get_states()
    reins_states = reins_handler.get_digital_states()