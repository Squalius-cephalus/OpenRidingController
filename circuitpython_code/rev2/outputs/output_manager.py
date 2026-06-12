"""
This module takes all the states from the Horse Logic and
uses that to send keycodes and analog values to various
HID devices. This also process the profile mapping. 
"""

from outputs.keyboard import KeyboardOutput
from outputs.mouse import MouseOutput
from outputs.gamepad import GamepadOutput
from adafruit_simplemath import map_range
import time
from utils.debug import log

keyboard = KeyboardOutput()
mouse = MouseOutput()
gamepad = GamepadOutput()

DEVICES = {
    "keyboard": keyboard,
    "gamepad": gamepad,
    "analog": gamepad,
    "mouse_move": mouse,
    "mouse_button": mouse,
}
ANALOG_MODES = {"mouse_move", "analog"}

class OutputManager:
    def __init__(self):
        self.buttons = {}
        self.previous_states = {}
        self.hold_keys = {}
        self.toggle_keys = {}
        self.reserved_keys = []
        self.macro_keys = []
        self.macro_timer = 0
        self.rein_mode = {}

        self.tap_time = 0.1

        self.possible_actions = {
            "hold": self.add_hold_keys,
            "tap": self.add_hold_keys,
            "toggle": self.handle_toggle_keys,
            "toggle_on": self.handle_toggle_keys,
            "toggle_off": self.handle_toggle_keys,
            "multitap": self.handle_multitap_keys,
        }

    def update(
        self, states, reins_analog_amount, nunchuk_analog=None, current_time=None
    ):
        """
        Update what keys/buttons need to be pressed or released.
        """
        if current_time is None:
            current_time = time.monotonic()

        # Multitap appeds to this dictionary, this fakes button presses.
        if self.reserved_keys:
            if not self.hold_keys:
                a = len(self.reserved_keys) - 1
                self.parse_input(self.reserved_keys[a], current_time)
                self.reserved_keys.pop(0)

        for i, activated in states.items():
            if activated:
                try:
                    button = self.buttons[i]
                except KeyError as e:
                    log("Profile is broken! Missing: ", e)
                    button = {"mode": None}

                mode = button.get("mode", "gamepad")
                if mode == "macro":
                    log("Macro detected")
                    for ii in button.get("macro"):
                        self.macro_keys.append(ii)
                elif mode is None:
                    log("Button skipped")
                else:
                    self.parse_input(button, current_time)

        self.release_hold_keys(current_time)
        self.update_reins_output(current_time, reins_analog_amount)
        if nunchuk_analog is not None:
            self.handle_nunchuk_analog(nunchuk_analog)

        if self.macro_keys:
            if current_time >= self.macro_timer:
                if self.macro_keys[0]["mode"] == "wait":
                    self.macro_timer = self.macro_keys[0]["value"] + current_time
                else:
                    self.parse_input(self.macro_keys[0], current_time)
                self.macro_keys.pop(0)

    def parse_input(self, button, current_time):
        """
        Gets data what button is pressed and parses what action it needs to do.
        """
        mode = self.get_valid(button, "mode", "keyboard", DEVICES.keys())
        key = self.get_with_default(button, "keycode", "A")
        action = self.get_valid(
            button,
            "action",
            "tap",
            {"tap", "hold", "toggle", "toggle_on", "toggle_off", "multitap"},
        )
        value = self.get_with_default(button, "value", 1)
        analog_value = self.get_with_default(button, "analog_value", 127)

        act = self.possible_actions[action]

        act(key, value, mode, action, current_time, analog_value)

    def add_hold_keys(self, key, value, mode, action, current_time, analog_value):
        """
        Adds keycode and current time to hold keys dict,
        after that presses the key.
        """
        if action == "tap":
            value = self.tap_time
        expiry = current_time + value
        self.hold_keys[key] = [mode, expiry]
        self.press_key(mode, key, analog_value)

    def handle_multitap_keys(self, key, value, mode, _, __, analog_value):
        """
        Fills a list to fake Tap actions.
        """
        log("Multitap detected")
        for i in range(int(value)):
            fake_button = {
                "mode": mode,
                "keycode": key,
                "action": "tap",
                "value": 0,
                "analog_value": analog_value,
            }
            self.reserved_keys.append(fake_button)

    def handle_toggle_keys(self, key, _, mode, action, __, analog_value):
        """
        Handles toggle action.
        """
        if self.toggle_keys.get(key) == mode:
            if action == "toggle" or action == "toggle_off":
                del self.toggle_keys[key]
                self.release_key(mode, key)
        else:
            if action != "toggle_off":
                self.toggle_keys[key] = mode
                self.press_key(mode, key, analog_value)

    def release_hold_keys(self, current_time):
        """
        Releases keys that are held down, if enough time has passed.
        """
        to_remove = []
        for key, (mode, expiry) in self.hold_keys.items():
            if current_time >= expiry:
                to_remove.append([mode, key])

        for key in to_remove:
            self.release_key(key[0], key[1])
            self.hold_keys.pop(key[1])

    def press_key(self, mode, key, analog_value=None):
        """
        Send keycode to press, or if device is analog it sends analog value to move cursor/joystick.
        """
        device = DEVICES.get(mode)

        if analog_value is not None and mode in ANALOG_MODES:
            device.move(key, analog_value, 1)
            log(mode, key, "moved to", analog_value)
        else:
            device.press(key)
            log(mode, key, "pressed")

    def release_key(self, mode, key):
        """
        Send keycode to release, or if device is analog it resets cursor/joystick to 0.
        """
        device = DEVICES.get(mode)
        if mode in ANALOG_MODES:
            device.move(key, 0, 1)
            log(mode, key, "moved to", 0)

        else:
            device.release(key)
            log(mode, key, "released")

    def release_all(self):
        """
        Resets toggles, held keys and forces devices to release all the keys/axis.
        """
        mouse.release_all()
        keyboard.release_all()
        gamepad.release_all()
        self.hold_keys = {}
        self.toggle_keys = {}
        self.reserved_keys = []

    def update_reins_output(self, current_time, analog_value):
        """
        Parses reins analog value and sends it to right device.
        """
        mode = self.get_with_default(self.rein_mode, "mode", "mouse")
        sensitivity = self.get_with_default(self.rein_mode, "sensitivity", 1)

        if mode == "analog":
            centered_analog_value = int(
                map_range(analog_value[1] - analog_value[0], -512, 512, -127, 127)
            )
            axis = self.get_with_default(self.rein_mode, "axis", "LS")
            gamepad.move(axis, centered_analog_value, sensitivity)

        elif mode == "mouse":
            mouse_hold = self.get_with_default(self.rein_mode, "mouse_hold", False)
            threshold = self.get_with_default(self.rein_mode, "keyboard_threshold", 300)
            mouse_button = self.get_with_default(
                self.rein_mode, "mouse_button", "LEFT_BUTTON"
            )
            max_distance = self.get_with_default(
                self.rein_mode, "mouse_max_distance", 1024
            )
            mouse_returning = self.get_with_default(
                self.rein_mode, "mouse_returning", False
            )
            mouse.reins_output(
                mouse_button,
                mouse_hold,
                analog_value,
                mouse_returning,
                current_time,
                sensitivity,
                max_distance,
            )

        elif mode == "keyboard":

            left_key = self.get_with_default(self.rein_mode, "left_key", "D")
            right_key = self.get_with_default(self.rein_mode, "right_key", "A")
            threshold = self.get_with_default(
                self.rein_mode, "keyboard_threshold", "150"
            )
            keyboard.reins_output(left_key, right_key, threshold, analog_value)

    def get_valid(self, d, key, default, valid_set):
        value = d.get(key)
        if value is None or value not in valid_set:
            return default
        return value

    def get_with_default(self, d, key, default):
        value = d.get(key, default)
        return default if value is None else value

    def set_new_profile(self, profile):
        """
        Sets rein mode settings and current profile button mapping.
        """
        try:
            self.buttons = profile["buttons"]
            self.rein_mode = profile["rein_mode"]

        except KeyError as e:
            raise ValueError(f"Missing profile key: {e}") from e

    def handle_nunchuk_analog(self, analog):
        """
        Gets Nunchuk controller joystick values and parses those to
        gamepad device or mouse device.
        """
        x = analog["x"]
        y = analog["y"]
        mode = analog["mode"]
        sensitivity = analog["sensitivity"]
        axis = analog["axis"]

        if abs(x) + abs(y) == 0:
            return

        if mode == "analog":
            gamepad.move(axis + "X", x, sensitivity)
            gamepad.move(axis + "Y", y, sensitivity)

        elif mode == "mouse":

            mouse.move("X", x, sensitivity, -y)
