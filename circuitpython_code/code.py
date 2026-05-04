import json
import board
import digitalio
import neopixel
import time
from digital_input import ButtonHandler
from horse_logic import HorseLogicHandler
from reins_input import ReinsHandler
from stirrups_input import StirrupsHandler
from output import OutputManager


led = neopixel.NeoPixel(board.GP16, 1, brightness=0.3, auto_write=True)
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

setup_calibration = True




class OnboardLED:
    def __init__(self, neopixel_led):
        self.led = neopixel_led
        self.current_color = [255,255,255]

    def change_color(self, color):
        self.led[0] = color
        self.current_color = color

    def blocking_blink(self, color, speed=0.2, times=20):
        original_color = self.current_color

        for i in range(0,times):
            self.led[0] = color
            time.sleep(speed/2)
            self.led[0] = [0,0,0]
            time.sleep(speed/2)
        self.led[0] = original_color



    def get_color(self):
        return self.current_color

class ProfileManager:
    def __init__(self, profiles, passed_led, output_manager):
        self.profiles = profiles
        self.led = passed_led
        self.output_manager = output_manager
        self.current_index = 0
        self.current_profile = self.profiles[self.current_index]
        if DEBUG:
            print("Active profile:", self.current_profile["Name"])
        self.led.change_color(self.current_profile["Settings"]["LEDColor"])
        self.output_manager.set_new_profile(self.current_profile)

    def change_profile(self):
        self.current_index = (self.current_index + 1) % len(self.profiles)
        self.current_profile = self.profiles[self.current_index]
        if DEBUG:
            print("Active profile:", self.current_profile["Name"])
        self.led.change_color(self.current_profile["Settings"]["LEDColor"])
    
        self.output_manager.set_new_profile(self.current_profile)
        self.output_manager.release_all()
        time.sleep(0.3)

onboard_led = OnboardLED(led)
output_manager = OutputManager()
profile_manager = ProfileManager(loaded_profiles, onboard_led, output_manager)
reins_handler = ReinsHandler(profile_manager.current_profile["Settings"])
stirrups_handler = StirrupsHandler()
horse_logic_handler = HorseLogicHandler()


button_handler = ButtonHandler(button1, button2, button3, button4)




def calibrate():
    # TODO: Redo whole calibration routine, maybe calibrate reins sensor zero position or something
    return



def pause_inputs():

    last_toggle = 0
    blink = False
    original_color = onboard_led.get_color()
    time.sleep(0.5)
    output_manager.release_all()
    print("Pause ON")

    while True:
        current_time = time.monotonic()
        if current_time - last_toggle >= 0.5:
            last_toggle = current_time
            onboard_led.change_color(original_color)
            if not blink:
                onboard_led.change_color([0, 0, 0])
                blink = True
            else:
                blink = False
        button_held = 0
        while not profile_button.value:
            button_held += 1
            time.sleep(0.01)

            if button_held >= 200:
                onboard_led.blocking_blink([255, 0, 255])
                time.sleep(0.5)
                print("add some function here")
        if not pause_button.value:
            time.sleep(0.5)
            print("Pause OFF")
            onboard_led.change_color(original_color)
            time.sleep(0.5)
            break


while True:

    current_time = time.monotonic()

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
    stirrups_handler.update()
    button_handler.update()


    stirrup_states = stirrups_handler.get_states()
    reins_states = reins_handler.get_states()
    combined_states = reins_states | stirrup_states

    # Horse will process everything
    horse_logic_handler.update_analog(reins_handler.get_analog_states())
    horse_logic_handler.update(combined_states)

    # These will be separated to Gamepad, Mouse and Keyboard handlers. But one main "handler" calls them.
    output_manager.update(horse_logic_handler.get_states() | button_handler.get_states(), horse_logic_handler.get_analog_states(), current_time)
