
import board
import digitalio
import neopixel
import json
import time
from analogio import AnalogIn
from adafruit_simplemath import map_range
import usb_hid
from adafruit_hid.mouse import Mouse
from hid_gamepad import Gamepad
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode



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
            print("Active profile:", self.current_profile["name"])
        self.pixel[0] = self.current_profile["color"]

    def change_profile(self):
        self.current_index = (self.current_index + 1) % len(self.profiles)
        self.current_profile = self.profiles[self.current_index]
        if DEBUG:
            print("Active profile:", self.current_profile["name"])
        self.pixel[0] = self.current_profile["color"]
        keyboard_mouse_handler.release_all()
        keyboard_mouse_handler.mode = self.current_profile["mode"]
        keyboard_mouse_handler.set_new_profile(self.current_profile)


        time.sleep(0.3)

    def current_mode(self):
        return self.current_profile["mode"]


class ReinsHandler:
    def __init__(self, left_rein_input, right_rein_input):
        self.left_rein_input = left_rein_input
        self.right_rein_input = right_rein_input
        self.now = time.monotonic()
        self.left = 0
        self.right = 0


        self.map_range = [0, 64]
        self.highest_left_value = 0
        self.highest_right_value = 0
        self.rein_timer = self.now
        self.reins_pulled = False
        self.reins_lightly_pulled = False
        self.neutral_position = 0
        self.pulled_threshold = 60
        self.lighty_pulled_threshold = 30


        self.states = {
            "Combined": 0,
            "BothPulledLight": False,
            "BothPulledHard": False
        }

    def _read_scaled(self, pin):

        return int(map_range(pin.value, 5000, 65520, self.map_range[0], self.map_range[1]))

    def update(self, current_time):
        left = self._read_scaled(self.left_rein_input)
        right = self._read_scaled(self.right_rein_input)
        self.now = current_time
        if not self.reins_pulled:
            self.left = left
            self.right = right

            self.states = {
                "Combined": 0,
                "BothPulledLight": False,
                "BothPulledHard": False
            }


        # Pulling reins to slow down the horse
        if left >= self.lighty_pulled_threshold and right >= self.lighty_pulled_threshold and not self.reins_pulled and not self.reins_lightly_pulled:
            time_taken = now - self.rein_timer
            if time_taken > 0.1:
                if DEBUG:
                    print("Both reins pulled SLOW")
                    print(now-self.rein_timer)

                self.states["BothPulledLight"] = True
                self.reins_lightly_pulled = True

        # Pulling reins hard to stop the horse
        if left + right == self.pulled_threshold*2 and not self.reins_pulled:
            if DEBUG: print("Reins pulled! Stop that horse")
            self.highest_left_value = 0
            self.highest_right_value = 0
            self.reins_pulled = True
            self.states["BothPulledHard"] = True

        if left <= self.neutral_position and right <= self.neutral_position:
            self.reins_pulled = False
            self.reins_lightly_pulled = False
            self.rein_timer = now

        if self.reins_pulled is False and self.reins_lightly_pulled is False:
            self.states["Combined"] = self.right - self.left
    def get_states(self):
        return self.states



class StirrupHandler:
    def __init__(self, left_stirrup_input, right_stirrup_input):
        self.left_stirrup_input = left_stirrup_input
        self.right_stirrup_input = right_stirrup_input
        self.now = time.monotonic()
        self.left = 0
        self.right = 0
        self.left_forward = False
        self.right_forward = False
        self.left_backward = False
        self.right_backward = False
        self.ready = False
        self.left_timer = 0
        self.right_timer = 0
        self.both_timer = 0
        self.dead_zone = 15
        self.left_offset = 0
        self.right_offset = 0
        self.trigger_forward = -50
        self.trigger_backward = 30
        self.inverted = True
        self.threshold_slow = profile_manager.current_profile["Buttons"]["StirrupSlowTime"]
        self.threshold_fast = profile_manager.current_profile["Buttons"]["StirrupFastTime"]
        self.states = {
    "LeftForwardSlow": False,
    "LeftForwardFast": False,
    "LeftBackwardSlow": False,
    "LeftBackwardFast": False,
    "RightForwardSlow": False,
    "RightForwardFast": False,
    "RightBackwardSlow": False,
    "RightBackwardFast": False,
    "BothForward": False,
    "BothBackward": False,
}



    def update(self, current_time):
        self.left = int(map_range(self.left_stirrup_input.value, 0, 65520, -255, 255))-self.left_offset
        self.right = int(map_range(self.right_stirrup_input.value, 0, 65520, -255, 255))-self.right_offset
        self.now = current_time


        if now-self.both_timer >= profile_manager.current_profile["Buttons"]["StirrupsBothTime"]:
            #print("reset")
            self.states = {
                "LeftForwardSlow": False,
                "LeftForwardFast": False,
                "LeftBackwardSlow": False,
                "LeftBackwardFast": False,
                "RightForwardSlow": False,
                "RightForwardFast": False,
                "RightBackwardSlow": False,
                "RightBackwardFast": False,
                "BothForward": False,
                "BothBackward": False,
            }
            self.both_timer = current_time
            self.ready = True
        else:
            self.ready = False





        if self.left <= self.trigger_forward and self.left_forward is False:
            self.left_forward = True
            if current_time-self.left_timer <= self.threshold_fast:
                self.states["LeftForwardFast"] = True
                if DEBUG: print("Left Forward Fast", current_time-self.left_timer)
            elif current_time-self.left_timer <= self.threshold_slow:
                self.states["LeftForwardSlow"] = True



        if self.right <= self.trigger_forward and self.right_forward is False:
            self.right_forward = True
            if current_time-self.right_timer <= self.threshold_fast:
                self.states["RightForwardFast"] = True
                if DEBUG: print("Right Forward Fast", current_time-self.right_timer)
            elif current_time-self.right_timer <= self.threshold_slow:
                self.states["RightForwardSlow"] = True
                if DEBUG: print("Right Forward Slow", current_time - self.right_timer)

        if self.left >= self.trigger_backward and self.left_backward is False:
            self.left_backward = True
            if current_time-self.left_timer <= self.threshold_fast:
                self.states["LeftBackwardFast"] = True
                if DEBUG: print("Left Backward Fast", current_time-self.left_timer)
            elif current_time-self.left_timer <= self.threshold_slow:
                self.states["LeftBackwardSlow"] = True
                if DEBUG: print("Left Backward Slow", current_time - self.right_timer)

        if self.right >= self.trigger_backward and self.right_backward is False:
            self.right_backward = True
            if current_time-self.right_timer <= self.threshold_fast:
                if DEBUG: print("Right Backward Fast", current_time-self.right_timer)
                self.states["RightBackwardFast"] = True
            elif current_time-self.right_timer <= self.threshold_slow:
                self.states["RightBackwardSlow"] = True
                if DEBUG: print("Right Backward Slow", current_time - self.right_timer)

        if -self.dead_zone <= self.left <= self.dead_zone:
            self.left_timer = now
            self.left_forward = False
            self.left_backward = False

        if -self.dead_zone <= self.right <= self.dead_zone:
            self.right_timer = now
            self.right_forward = False
            self.right_backward = False




        if self.states["LeftForwardFast"] and self.states["RightForwardFast"]:
            print("Both Forward")
            self.states["BothForward"] = True
            self.states["RightForwardFast"] = False
            self.states["LeftForwardFast"] = False

        if self.states["LeftBackwardFast"] and self.states["RightBackwardFast"]:
            print("Both Backward")
            self.states["BothBackward"] = True
            self.states["RightBackwardFast"] = False
            self.states["LeftBackwardFast"] = False



    def get_states(self):

        return self.states

    def calibrate(self, left_value, right_value):
        self.left_offset = left_value
        self.right_offset = right_value

class ButtonHandler:
    def __init__(self):
        self.states = {
            "Button1": False,
            "Button2": False,
            "Button3": False,
            "Button4": False,
        }

    def update(self):
        if not button1.value:
            self.states["Button1"] = True
        else:
            self.states["Button1"] = False

        if not button2.value:
            self.states["Button2"] = True
        else:
            self.states["Button2"] = False

        if not button3.value:
            self.states["Button3"] = True
        else:
            self.states["Button3"] = False

        if not button4.value:
            self.states["Button4"] = True
        else:
            self.states["Button4"] = False

    def get_states(self):

        return self.states



class KeyboardMouseInputManager:
    def __init__(self, profile_json):
        self.kbd = Keyboard(usb_hid.devices)
        self.mouse = Mouse(usb_hid.devices)
        self.gamepad = Gamepad(usb_hid.devices)
        self.buttons = profile_json["Buttons"]
        self.mode = profile_json["mode"]

        self.hold_timer = 0
        # Track previous state to detect presses
        self.prev_states = {}
        self.toggle_states = {}
        self.active_holds = {}
        self.hold_mousekey = False
        self.current_mode = profile_json["mode"]

        self.state_map = {
            "LeftForwardSlow": "LeftStirrupForwardSlow",
            "LeftForwardFast": "LeftStirrupForwardFast",
            "LeftBackwardSlow": "LeftStirrupBackwardSlow",
            "LeftBackwardFast": "LeftStirrupBackwardFast",
            "RightForwardSlow": "RightStirrupForwardSlow",
            "RightForwardFast": "RightStirrupForwardFast",
            "RightBackwardSlow": "RightStirrupBackwardSlow",
            "RightBackwardFast": "RightStirrupBackwardFast",
            "BothForward": "BothStirrupForward",
            "BothBackward": "BothStirrupBackward",
            "BothPulledLight": "BothReinPulledSlow",
            "BothPulledHard": "BothReinPulledFast",
            "Button1": "Button1",
            "Button2": "Button2",
            "Button3": "Button3",
            "Button4": "Button4"
        }

        self.gamepad_map = {
            "A": 1,
            "B": 2,
            "X": 3,
            "Y": 4,
            "LB": 5,
            "RB": 6,
            "BACK": 7,
            "START": 8,
            "LT": 9,
            "RT": 10,
            "UP": 11,
            "DOWN": 12,
            "LEFT": 13,
            "RIGHT": 14,
            "Z": 15,
            "D": 16,
            "LTF": 17,
            "LTB": 18,
            "RTF": 19,
            "RTB": 20,
            # add more mappings as needed
        }

    def _get_gamepad_code(self, key_name):
        print("Getting gamepad code", key_name)
        return self.gamepad_map.get(key_name, -1)

    @staticmethod
    def _get_keycode(key_name):
        return getattr(Keycode, key_name.upper())

    def set_new_profile(self, profile):
        self.buttons = profile["Buttons"]
        self.mode = profile["mode"]
        self.current_mode = profile["mode"]
        print(self.current_mode)

    def release_all(self):
        self.kbd.release_all()
        self.gamepad.release_all_buttons()
        self.gamepad.move_joysticks(x=0, y=0, z=0, r_z=0)
        self.mouse.move(x=0)
        self.mouse.move(y=0)
        self.mouse.release(Mouse.LEFT_BUTTON)
        self.mouse.release(Mouse.RIGHT_BUTTON)

    def press(self, keycode):
        if DEBUG: print("Press", keycode)




        if self.current_mode == "Keyboard":
            self.kbd.press(keycode)
        if self.current_mode == "Gamepad":
            if keycode == 17:  # helvettiin tämmöset magic numberit hyi
                self.gamepad.move_joysticks(y=-127)
                print(keycode)
            elif keycode == 18:  # helvettiin tämmöset magic numberit hyi
                self.gamepad.move_joysticks(y=127)
                print(keycode)
            else:
                self.gamepad.press_buttons(keycode)

    def release(self, keycode):
        if DEBUG: print("Release", keycode)

        if self.current_mode == "Keyboard":
            self.kbd.release(keycode)
        if self.current_mode == "Gamepad":
            if keycode == 17:  # helvettiin tämmöset magic numberit hyi
                self.gamepad.move_joysticks(y=0)
            elif keycode == 18:  # helvettiin tämmöset magic numberit hyi
                self.gamepad.move_joysticks(y=0)

            else:
                self.gamepad.release_buttons(keycode)
                print(keycode)



    def update(self, current_states):

        combined_rein_values = current_states["Combined"]

        self.current_mode = profile_manager.current_profile["mode"]


        if self.current_mode == "Keyboard":
            self.mouse.move(x=combined_rein_values)
            if combined_rein_values != 0 and profile_manager.current_profile["Buttons"]["ReinHoldMouse"]:
                self.mouse.press(Mouse.LEFT_BUTTON)
            else:
                self.mouse.release(Mouse.LEFT_BUTTON)

        if self.current_mode == "Gamepad":
            self.gamepad.move_joysticks(x=int(map_range(combined_rein_values, -64, 64, -127, 127)))

        for state_name, active in current_states.items():
            prev = self.prev_states.get(state_name, False)

            # Only trigger on press (edge)
            if active and not prev:
                if state_name not in self.state_map:
                    continue

                button_name = self.state_map[state_name]

                if button_name not in self.buttons:
                    continue

                mapping = self.buttons[button_name]

                key_name = mapping[0]
                action = mapping[1]
                try:
                    hold_time = mapping[2]
                except IndexError:
                    hold_time = 0.030




                if self.current_mode == "Gamepad":
                    keycode = self._get_gamepad_code(key_name)
                else:
                    keycode = self._get_keycode(key_name)


                if action == "DoubleTap":
                    self.press(keycode)


                if action == "Toggle":
                    if active and not prev:
                        toggled = self.toggle_states.get(keycode, False)

                        if not toggled:
                            self.press(keycode)
                            self.toggle_states[keycode] = True
                        else:
                            self.release(keycode)
                            self.toggle_states[keycode] = False

                if action == "ToggleOff":
                    if active and not prev:
                        self.release(keycode)
                        self.toggle_states[keycode] = False



                if action == "Tap":
                    if button_name not in self.active_holds:
                        self.press(keycode)
                        self.active_holds[button_name] = (
                            now + hold_time,
                            keycode
                        )

            self.prev_states[state_name] = active

        for button_name in list(self.active_holds.keys()):
            release_time, keycode = self.active_holds[button_name]

            if now >= release_time:

                self.release(keycode)
                del self.active_holds[button_name]

profile_manager = ProfileManager(loaded_profiles, onboard_led)
reins_handler = ReinsHandler(left_rein_in, right_rein_in)
stirrup_handler = StirrupHandler(left_stirrup_in, right_stirrup_in)
keyboard_mouse_handler = KeyboardMouseInputManager(profile_manager.current_profile)
button_handler = ButtonHandler()

def calibrate():
    current_time = time.monotonic()
    stirrup_handler.left_offset = 0
    stirrup_handler.right_offset = 0
    left_offset = 0
    right_offset = 0
    original_color = profile_manager.pixel[0]

    print("Calibrating...")
    stirrup_handler.update(current_time)
    left_offset = left_offset+stirrup_handler.left
    right_offset = right_offset+stirrup_handler.right
    profile_manager.pixel[0] = [0,0,0]
    time.sleep(0.3)
    print("Calibrating...")
    stirrup_handler.update(current_time)
    left_offset = left_offset + stirrup_handler.left
    right_offset = right_offset + stirrup_handler.right
    profile_manager.pixel[0] = original_color
    time.sleep(0.3)
    print("Calibrating...")
    stirrup_handler.update(current_time)
    left_offset = left_offset + stirrup_handler.left
    right_offset = right_offset + stirrup_handler.right
    profile_manager.pixel[0] = [0, 0, 0]
    left_offset = int(left_offset /3)
    right_offset = int(right_offset /3)
    time.sleep(0.3)

    stirrup_handler.calibrate(left_offset, right_offset)
    print("Calibration complete.")
    profile_manager.pixel[0] = original_color



def pause_inputs():
    keyboard_mouse_handler.release_all()
    last_toggle = 0
    blink = False
    original_color = profile_manager.pixel[0]
    time.sleep(0.5)
    print("Pause ON")

    while True:
        now = time.monotonic()
        if now - last_toggle >= 0.5:
            last_toggle = now
            blink = not blink
            profile_manager.pixel[0] = [0, 0, 0] if blink else original_color

        if not pause_button.value:
            time.sleep(0.5)
            print("Pause OFF")
            profile_manager.pixel[0] = original_color
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
    reins_handler.update(now)
    stirrup_handler.update(now)
    button_handler.update()

    stirrup_states = stirrup_handler.get_states()
    reins_states = reins_handler.get_states()
    button_states = button_handler.get_states()
    combined = stirrup_states | reins_states | button_states
    keyboard_mouse_handler.update(combined)







