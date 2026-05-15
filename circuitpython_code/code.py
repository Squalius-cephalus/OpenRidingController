import json
import board
import digitalio
import neopixel
import time
from digital_input import ButtonHandler
from horse_logic import HorseLogicHandler
from reins_input import ReinsHandler
from stirrups_input import StirrupsHandler
from nunchuk import NunchukHandler
from output import OutputManager
from debug import log

led = neopixel.NeoPixel(board.GP16, 1, brightness=0.3, auto_write=True)
with open("/profiles.json", "r") as f:
    data = json.load(f)

setup_done = False

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



class Controller:
    def __init__(self):
        
        self.output_manager = OutputManager()
        
        self.reins_handler = ReinsHandler()
        self.stirrups_handler = StirrupsHandler()
        self.nunchuk_handler = NunchukHandler()
        self.horse_logic_handler = HorseLogicHandler()
        self.button_handler = ButtonHandler(button1, button2, button3, button4)
        self.nunchuk_connected = self.nunchuk_handler.is_connected()


    def update_inputs(self, current_time):
        self.reins_handler.update()
        self.stirrups_handler.update()
        self.button_handler.update()
        if self.nunchuk_connected:
            self.nunchuk_handler.update(current_time)

    def get_states_from_inputs(self):
        stirrup_states = self.stirrups_handler.get_states()
        reins_states = self.reins_handler.get_states()
        return stirrup_states | reins_states
    
    def set_new_profile(self, new_profile):
        self.output_manager.set_new_profile(new_profile)
        self.nunchuk_handler.set_new_profile(new_profile)
        self.reins_handler.set_new_profile(profile_manager.current_profile["settings"])
        self.stirrups_handler.set_new_profile(profile_manager.current_profile["settings"])

        self.output_manager.release_all()
    def release_all(self):
        self.output_manager.release_all()
    
    def update(self, current_time):
        

        self.update_inputs(current_time)
        
        # Horse will process everything
        self.horse_logic_handler.update_analog(self.reins_handler.get_analog_states())
        self.horse_logic_handler.update(self.get_states_from_inputs())

        # These will be separated to Gamepad, Mouse and Keyboard handlers. But one main "handler" calls them.
        states = self.horse_logic_handler.get_states() | self.button_handler.get_states() | self.nunchuk_handler.get_states()
        self.output_manager.update(states, self.horse_logic_handler.get_analog_states(), self.nunchuk_handler.get_analog_states(), current_time)




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
    def __init__(self, profiles, passed_led):
        self.profiles = profiles
        self.led = passed_led
        self.current_index = -1
        self.current_profile = self.profiles[self.current_index]
   

    def change_profile(self):

        self.current_index = (self.current_index + 1) % len(self.profiles)
        self.current_profile = self.profiles[self.current_index]
        log("Active profile:", self.current_profile["name"])
        self.led.change_color(self.current_profile["settings"]["led_color"])
        time.sleep(0.3)
        return self.current_profile






onboard_led = OnboardLED(led)
profile_manager = ProfileManager(loaded_profiles, onboard_led)
controller = Controller()
while True:
    current_time = time.monotonic()
    if not profile_button.value or not setup_done:
        new_profile = profile_manager.change_profile()
        controller.set_new_profile(new_profile)
        setup_done = True 

    if not pause_button.value:
        time.sleep(0.5)
        log("Pause ON")
        controller.release_all()
        
        while True:
            onboard_led.blocking_blink(onboard_led.get_color(), 0.5, 1)
            if not pause_button.value:
                log("Pause OFF")
                time.sleep(1)
                break

    controller.update(current_time)

    
