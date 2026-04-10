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

loaded_profiles = data["profiles"]

profile_button = digitalio.DigitalInOut(board.GP2) # Wrong pin! Needs to be in GP15
profile_button.direction = digitalio.Direction.INPUT
profile_button.pull = digitalio.Pull.UP

left_rein_in = AnalogIn(board.GP26)
right_rein_in = AnalogIn(board.GP27)
left_stirrup_in = AnalogIn(board.GP28)
right_stirrup_in = AnalogIn(board.GP29)

onboard_led = neopixel.NeoPixel(board.GP16, 1, brightness=0.3, auto_write=True)


class ProfileManager:
    def __init__(self, profiles, pixel):
        self.profiles = profiles
        self.pixel = pixel
        self.current_index = 0
        self.current_profile = self.profiles[self.current_index]

        print("Active profile:", self.current_profile["name"])
        self.pixel[0] = self.current_profile["color"]

    def change_profile(self):
        self.current_index = (self.current_index + 1) % len(self.profiles)
        self.current_profile = self.profiles[self.current_index]

        print("Active profile:", self.current_profile["name"])
        self.pixel[0] = self.current_profile["color"]
        keyboard_mouse_handler.release_all()
        keyboard_mouse_handler.mode = self.current_profile["mode"]

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


        self.map_range = [0, 127]
        self.highest_left_value = 0
        self.highest_right_value = 0
        self.rein_timer = self.now
        self.reins_pulled = False
        self.reins_lightly_pulled = False
        self.neutral_position = 0
        self.pulled_threshold = 127
        self.lighty_pulled_threshold = 80


        self.states = {
            "Combined": 0,
            "BothPulledLight": False,
            "BothPulledHard": False
        }

    def _read_scaled(self, pin):

        return int(map_range(pin.value, 0, 65520, self.map_range[0], self.map_range[1]))

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
                print("slow down you fucker")

                self.states["BothPulledLight"] = True
                self.reins_lightly_pulled = True

        # Pulling reins hard to stop the horse
        if left + right == self.pulled_threshold*2 and not self.reins_pulled:
            print("Reins pulled! Stop that horse")
            self.highest_left_value = 0
            self.highest_right_value = 0
            self.reins_pulled = True
            self.states["BothPulledHard"] = True
            print(now-self.rein_timer)

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
        self.left_timer = 0
        self.right_timer = 0
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
        self.left = int(map_range(self.left_stirrup_input.value, 0, 65520, -127, 127))
        self.right = int(map_range(self.right_stirrup_input.value, 0, 65520, -127, 127))
        self.now = current_time

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


        if self.left >= 127 and self.left_forward is False:
            self.left_forward = True
            if current_time-self.left_timer <= 0.2:
                self.states["LeftForwardFast"] = True
            elif current_time-self.left_timer <= 0.5:
                self.states["LeftForwardSlow"] = True



        if self.right >= 127 and self.right_forward is False:
            self.right_forward = True
            if current_time-self.right_timer <= 0.2:
                self.states["RightForwardFast"] = True
            elif current_time-self.right_timer <= 0.5:
                self.states["RightForwardSlow"] = True

        if self.left <= -120 and self.left_backward is False:
            self.left_backward = True
            if current_time-self.left_timer <= 0.2:
                self.states["LeftBackwardFast"] = True
            elif current_time-self.left_timer <= 0.5:
                self.states["LeftBackwardSlow"] = True

        if self.right <= -120 and self.right_backward is False:
            self.right_backward = True
            if current_time-self.right_timer <= 0.2:
                self.states["RightBackwardFast"] = True
            elif current_time-self.right_timer <= 0.5:
                self.states["RightBackwardSlow"] = True

        if self.left == 0:
            self.left_timer = now
            self.left_forward = False
            self.left_backward = False

        if self.right == 0:
            self.right_timer = now
            self.right_forward = False
            self.right_backward = False

    def get_states(self):
        return self.states

class KeyboardMouseInputManager:
    def __init__(self, profile_json):
        self.kbd = Keyboard(usb_hid.devices)
        self.mouse = Mouse(usb_hid.devices)
        self.buttons = profile_json["Buttons"]
        self.hold_time = 1
        self.hold_timer = 0
        # Track previous state to detect presses
        self.prev_states = {}
        self.toggle_states = {}
        self.active_holds = {}
        self.hold_mousekey = False

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
            "BothPulledHard": "BothReinPulledFast"
        }



    def _get_keycode(self, key_name):
        return getattr(Keycode, key_name.upper())

    def release_all(self):
        self.kbd.release_all()
        self.mouse.move(x=0)
        self.mouse.move(y=0)
        self.mouse.release(Mouse.LEFT_BUTTON)
        self.mouse.release(Mouse.RIGHT_BUTTON)

    def update(self, current_states):

        combined_rein_values = current_states["Combined"]
        print(current_states["Combined"])
        self.mouse.move(x=combined_rein_values)
        if combined_rein_values != 0 and self.buttons["ReinHoldMouse"]:
            self.mouse.press(Mouse.LEFT_BUTTON)
        else:
            self.mouse.release(Mouse.LEFT_BUTTON)

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
                keycode = self._get_keycode(key_name)

                if action == "Tap":
                    self.kbd.press(keycode)
                    self.kbd.release(keycode)
                if action == "DoubleTap":
                    self.kbd.press(keycode)
                    self.kbd.release(keycode)
                   # Delay could be a good idea! 
                    self.kbd.press(keycode)
                    self.kbd.release(keycode)


                if action == "Toggle":
                    if active and not prev:
                        toggled = self.toggle_states.get(state_name, False)

                        if not toggled:
                            self.kbd.press(keycode)
                            self.toggle_states[state_name] = True
                        else:
                            self.kbd.release(keycode)
                            self.toggle_states[state_name] = False

                if action == "Hold":
                    if button_name not in self.active_holds:
                        self.kbd.press(keycode)
                        self.active_holds[button_name] = (
                            now + self.hold_time,
                            keycode
                        )

            self.prev_states[state_name] = active

        for button_name in list(self.active_holds.keys()):
            release_time, keycode = self.active_holds[button_name]

            if now >= release_time:
                self.kbd.release(keycode)
                del self.active_holds[button_name]

profile_manager = ProfileManager(loaded_profiles, onboard_led)
reins_handler = ReinsHandler(left_rein_in, right_rein_in)
stirrup_handler = StirrupHandler(left_stirrup_in, right_stirrup_in)
keyboard_mouse_handler = KeyboardMouseInputManager(profile_manager.current_profile)


def calibrate():
    # THIS DOES NOTHING
    print("Calibrating...")
    time.sleep(1)
    print("Calibrating...")
    time.sleep(1)
    print("Calibrating...")
    time.sleep(1)
    print("Calibration complete.")




while True:
    now = time.monotonic()

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


    reins_handler.update(now)
    stirrup_handler.update(now)

    states = stirrup_handler.get_states()
    states2 = reins_handler.get_states()
    combined = states | states2
    keyboard_mouse_handler.update(combined)

    time.sleep(0.1)



