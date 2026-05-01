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
    "Keyboard": keyboard,
    "Gamepad": gamepad,
    "Joystick": gamepad,
    "MouseMove": mouse,
    "MouseButton": mouse,
}


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
                button = self.buttons[i]

                if button.get("Mode") == "Macro":
                    print("Macro detected")
                    for ii in button.get("Macro Inputs"):

                        self.parse_input(ii[0], current_time)
                elif button.get("Mode") == "None":
                    print("Button skipped")
                else:
                    self.parse_input(button, current_time)

        self.release_hold_keys(current_time)
        self.update_reins_output(current_time, reins_analog_amount)
        self.update_nunchuck_joystick_output()
        if not usb_connected:
            uart_logic.update()

    def parse_input(self, button, current_time):

        mode = self.get_valid(button, "Mode", "Keyboard", DEVICES.keys())
        key = self.get_with_default(button, "Keycode", "A")
        action = self.get_valid(button, "Action", "Tap", {
                                "Tap", "Hold", "Toggle", "ToggleOn", "ToggleOff", "Multitap"})
        value = self.get_with_default(button, "Value", 1)
        analog_value = self.get_with_default(button, "Analog", 127)

        possible_actions = {
            "Hold": self.add_hold_keys,
            "Tap": self.add_hold_keys,
            "Toggle": self.handle_toggle_keys,
            "ToggleOn": self.handle_toggle_keys,
            "ToggleOff": self.handle_toggle_keys,
            "Multitap": self.handle_multitap_keys
        }

        act = possible_actions.get(action)

        act(key, value, mode, action, current_time, analog_value)

    def add_hold_keys(self, key, value, mode, action, current_time, analog_value):
        if action == "Tap":
            value = self.tap_time
        expiry = current_time + value
        self.hold_keys[key] = [mode, expiry]
        self.press_key(mode, key, analog_value)

    def handle_multitap_keys(self, key, value, mode, _, __, analog_value):
        print("Multitap detected")
        for i in range(int(value)):
            fake_button =  {"Mode": mode,
                            "Keycode": key,
                            "Action": "Tap",
                            "Value": 0,
                            "Analog": analog_value}
            self.reserved_keys.append(fake_button)

    def handle_toggle_keys(self, key, _, mode, action, __, analog_value):
        if self.toggle_keys.get(key) == mode:
            if action == "Toggle" or action == "ToggleOff":
                del self.toggle_keys[key]
                self.release_key(mode, key)
        else:
            if action != "ToggleOff":
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

        print(mode, key, "pressed")

        if analog_value is not None and hasattr(device, "move"):
            device.move(key, analog_value)
        else:
            device.press(key)

    def release_key(self, mode, key):
        device = DEVICES.get(mode)

        print(mode, key, "released")

        if hasattr(device, "move"):
            device.move(key, 0)
        else:
            device.release(key)

    def release_all(self):
        mouse.release_all()
        keyboard.release_all()
        gamepad.release_all()

    def update_reins_output(self, current_time, analog_value):
        mode = self.get_with_default(self.rein_mode,"Mode", "Mouse")
        sensitivity = self.get_with_default(self.rein_mode, "Sensitivity", 1)

        if mode == "Joystick":
            centered_analog_value = int(map_range(analog_value[1] - analog_value[0], -512, 512, -127, 127))
            axis = self.rein_mode.get("Axis")
            gamepad.move(axis, centered_analog_value, sensitivity)

        elif mode == "Mouse":
            mouse_hold = self.get_with_default(self.rein_mode, "MouseHold", False)
            behaviour = self.get_with_default(self.rein_mode, "MouseBehaviour", "Normal")
            threshold = self.get_with_default(self.rein_mode,"Threshold", 300)
            mouse_button = self.get_with_default(self.rein_mode,"MouseButton", "LEFT_BUTTON")
            max_distance = self.get_with_default(self.rein_mode, "MouseMaxDistance", 1024)
            mouse.reins_output(
                mouse_button,
                mouse_hold,
                analog_value,
                behaviour,
                current_time,
                sensitivity,
                max_distance
            )

        elif mode == "Keyboard":
            left_key = self.rein_mode.get("LeftKey")
            right_key = self.rein_mode.get("RightKey")
            keyboard.reins_output(
                left_key,
                right_key,
                threshold,
                analog_value
            )

    def update_nunchuck_joystick_output(self):
        if not self.nunchuck_connected:
            return
        sensitivity = nunchuck_handler.nunchuck_mode.get("Sensitivity")
        centered_analog_value_x, centered_analog_value_y = nunchuck_handler.get_analog_states()

        mode = nunchuck_handler.nunchuck_mode.get("Mode")
        if mode == "Joystick":
            axis = nunchuck_handler.nunchuck_mode.get("Axis")
            gamepad.move(axis+"X", centered_analog_value_x ,sensitivity)
            gamepad.move(axis+"Y", centered_analog_value_y)
        elif mode == "Mouse":
            if abs(centered_analog_value_x)+abs(centered_analog_value_y) > 0:
                mouse.move("X", centered_analog_value_x, sensitivity)
                mouse.move("Y", centered_analog_value_y, sensitivity)

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
            self.buttons = profile["Buttons"]
            self.rein_mode = profile["ReinMode"]
            nunchuck_handler.update_profile(profile)
        except KeyError as e:
            while True:
                print("Profile is! Fix your profile.json! Missing:",  e)
