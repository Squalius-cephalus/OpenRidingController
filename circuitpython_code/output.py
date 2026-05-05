from keyboard_output import KeyboardOutput
from mouse_output import MouseOutput
from gamepad_output import GamepadOutput
from nunchuck import NunchuckHandler
from adafruit_simplemath import map_range

from uart_logic import UARTLogic
from uart_output import UARTOutput
import supervisor
import board

nunchuck_handler = NunchuckHandler()
usb_connected = supervisor.runtime.usb_connected


class DummyOutput:
    def press(self, *args):
        pass

    def release(self, *args):
        pass

    def move(self, *args, **kwargs):
        pass

    def release_all(self, *args, **kwargs):
        pass

    def reins_output(self, *args, **kwargs):
        pass


if usb_connected:
    keyboard = KeyboardOutput()
    mouse = MouseOutput()
    gamepad = GamepadOutput()
else:
    keyboard = DummyOutput()
    mouse = DummyOutput()
    uart_logic = UARTLogic(board.GP8)
    gamepad = UARTOutput(uart_logic)


DEVICES = {
    "keyboard": keyboard,
    "gamepad": gamepad,
    "analog": gamepad,
    "mouse_move": mouse,
    "mouse_button": mouse,
}
ANALOG_MODES = {"mouse_move", "analog", "gamepad"}

class OutputManager:
    def __init__(self):
        self.buttons = {}
        self.previous_states = {}
        self.hold_keys = {}
        self.toggle_keys = {}
        self.reserved_keys = []
        self.rein_mode = [""]

        self.tap_time = 0.1
        self.nunchuck_connected = nunchuck_handler.is_connected()

    def update(self, states, reins_analog_amount, current_time):

        self.nunchuck_connected = nunchuck_handler.is_connected()
        if self.nunchuck_connected:
            nunchuck_handler.update(current_time)
            states = states | nunchuck_handler.get_states()

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
                    print("Profile is broken! Missing: ", e)
                    button = {
                        "mode": "keyboard",
                        "action":"tap"
                    }

                mode = button.get("mode", "keyboard")
                if mode == "macro":
                    print("Macro detected")
                    for ii in button.get("Macro Inputs"):

                        self.parse_input(ii[0], current_time)
                elif mode == "None":
                    print("Button skipped")
                else:
                    self.parse_input(button, current_time)

        self.release_hold_keys(current_time)
        self.update_reins_output(current_time, reins_analog_amount)
        self.update_nunchuck_joystick_output()
        if not usb_connected:
            uart_logic.update()

    def parse_input(self, button, current_time):

        mode = self.get_valid(button, "mode", "keyboard", DEVICES.keys())
        key = self.get_with_default(button, "keycode", "A")
        action = self.get_valid(button, "action", "tap", {
                                "tap", "hold", "toggle", "toggle_on", "toggle_off", "multitap"})
        value = self.get_with_default(button, "value", 1)
        analog_value = self.get_with_default(button, "analog_value", 127)

        possible_actions = {
            "hold": self.add_hold_keys,
            "tap": self.add_hold_keys,
            "toggle": self.handle_toggle_keys,
            "toggle_on": self.handle_toggle_keys,
            "toggle_off": self.handle_toggle_keys,
            "multitap": self.handle_multitap_keys
        }

        act = possible_actions.get(action)

        act(key, value, mode, action, current_time, analog_value)

    def add_hold_keys(self, key, value, mode, action, current_time, analog_value):
        if action == "tap":
            value = self.tap_time
        expiry = current_time + value
        self.hold_keys[key] = [mode, expiry]
        self.press_key(mode, key, analog_value)

    def handle_multitap_keys(self, key, value, mode, _, __, analog_value):
        print("Multitap detected")
        for i in range(int(value)):
            fake_button = {"mode": mode,
                           "keycode": key,
                           "action": "tap",
                           "value": 0,
                           "analog_value": analog_value}
            self.reserved_keys.append(fake_button)

    def handle_toggle_keys(self, key, _, mode, action, __, analog_value):
        if self.toggle_keys.get(key) == mode:
            if action == "toggle" or action == "toggle_off":
                del self.toggle_keys[key]
                self.release_key(mode, key)
        else:
            if action != "toggle_off":
                self.toggle_keys[key] = mode
                self.press_key(mode, key, analog_value)

    def release_hold_keys(self, current_time):
        to_remove = []

        for key, (mode, expiry) in self.hold_keys.items():
            if current_time >= expiry:
                to_remove.append([mode, key])

        for key in to_remove:
            self.release_key(key[0], key[1])
            self.hold_keys.pop(key[1])

    def press_key(self, mode, key, analog_value=None):
        device = DEVICES.get(mode)
        
        if analog_value is not None and mode in ANALOG_MODES:
            device.move(key, analog_value, 1)
            print(mode, key, "moved to", analog_value)
        else:
            device.press(key)
            print(mode, key, "pressed")

        

    def release_key(self, mode, key):
        device = DEVICES.get(mode)
        if mode in ANALOG_MODES:
            device.move(key, 0, 1)
            print(mode, key, "moved to", 0)
        else:
            device.release(key)
            print(mode, key, "released")

    def release_all(self):
        mouse.release_all()
        keyboard.release_all()
        gamepad.release_all()

    def update_reins_output(self, current_time, analog_value):
        mode = self.get_with_default(self.rein_mode, "mode", "mouse")
        sensitivity = self.get_with_default(self.rein_mode, "sensitivity", 1)

        if mode == "analog":
            centered_analog_value = int(
                map_range(analog_value[1] - analog_value[0], -512, 512, -127, 127))
            axis = self.get_with_default(self.rein_mode, "axis", "LS")
            gamepad.move(axis, centered_analog_value, sensitivity)

        elif mode == "mouse":
            mouse_hold = self.get_with_default(
                self.rein_mode, "mouse_hold", False)
            threshold = self.get_with_default(self.rein_mode, "threshold", 300)
            mouse_button = self.get_with_default(
                self.rein_mode, "mouse_button", "LEFT_BUTTON")
            max_distance = self.get_with_default(
                self.rein_mode, "mouse_max_distance", 1024)
            mouse_returning = self.get_with_default(
                self.rein_mode, "mouse_returning", False)
            mouse.reins_output(
                mouse_button,
                mouse_hold,
                analog_value,
                mouse_returning,
                current_time,
                sensitivity,
                max_distance
            )

        elif mode == "keyboard":

            left_key = self.get_with_default(self.rein_mode, "LeftKey", "D")
            right_key = self.get_with_default(self.rein_mode, "RightKey", "A")
            threshold = self.get_with_default(self.rein_mode, "Threshold", "150")
            keyboard.reins_output(
                left_key,
                right_key,
                threshold,
                analog_value
            )

    def update_nunchuck_joystick_output(self):
        if not self.nunchuck_connected:
            return
        sensitivity = nunchuck_handler.nunchuck_mode.get("sensitivity")
        centered_analog_value_x, centered_analog_value_y = nunchuck_handler.get_analog_states()

        mode = nunchuck_handler.nunchuck_mode.get("mode")
        if mode == "analog":
            axis = nunchuck_handler.nunchuck_mode.get("axis")
            gamepad.move(axis+"X", centered_analog_value_x, sensitivity)
            gamepad.move(axis+"Y", centered_analog_value_y, sensitivity)
        elif mode == "mouse":
            if abs(centered_analog_value_x)+abs(centered_analog_value_y) > 0:
                mouse.move("X", centered_analog_value_x, sensitivity, centered_analog_value_y)

    def get_valid(self, d, key, default, valid_set):
        value = d.get(key)
        if value is None or value not in valid_set:
            return default
        return value

    def get_with_default(self, d, key, default):
        value = d.get(key, default)
        return default if value is None else value

    def set_new_profile(self, profile):
        try:
            self.buttons = profile["buttons"]
            self.rein_mode = profile["rein_mode"]
            nunchuck_handler.update_profile(profile)
        except KeyError as e:
            while True:
                print("Profile is! Fix your profile.json! Missing:",  e)
