import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
import time
from hid_gamepad import Gamepad


DEBUG = True
from adafruit_simplemath import map_range
class OutputManager:
    def __init__(self, profile_json):
        self.kbd = Keyboard(usb_hid.devices)
        self.mouse = Mouse(usb_hid.devices)
        self.gamepad = Gamepad(usb_hid.devices)
        self.buttons = profile_json["Buttons"]
        self.hold_mousekey = profile_json["Buttons"]["ReinHoldMouse"]
        self.rein_mode = profile_json["Buttons"]["ReinMode"]
        self.pressed_keys = []
        self.current_time = time.monotonic()
        self.key_added = False
        self.toggled = False
        self.reins_moved = False

        self.modes = ["Keyboard", "MouseButton", "Gamepad", "Analog", "MouseMove", "Macro"]


        self.gamepad_map = {
            "A": 1,
            "B": 2,
            "X": 3,
            "Y": 4,
            "LB": 5,
            "RB": 6,
            "BACK": 7,
            "START": 8,
            "LSB": 9,
            "RSB": 10,
            "UP": 11,
            "DOWN": 12,
            "LEFT": 13,
            "RIGHT": 14,
            "LT": 15,
            "RT": 16,
            "LSX": 17,
            "LSY": 18,
            "RSX": 19,
            "RSY": 20,

        }

        self.mouse_map = {
            "LEFT_BUTTON": Mouse.LEFT_BUTTON,
            "RIGHT_BUTTON": Mouse.RIGHT_BUTTON,
            "MIDDLE_BUTTON": Mouse.MIDDLE_BUTTON,
            "BACK_BUTTON": Mouse.BACK_BUTTON,
            "FORWARD_BUTTON": Mouse.FORWARD_BUTTON,
        }

    def _get_gamepad_code(self, key_name):
        print("Getting gamepad code", key_name)
        try:
            return self.gamepad_map.get(key_name.upper())
        except ValueError:
            print("Unknown gamepad key", key_name.upper())
            return 1

    def _get_mouse_code(self, key_name):
        print("Getting gamepad code", key_name)
        try:
            return self.mouse_map.get(key_name.upper())
        except ValueError:
            print("Unknown mouse key", key_name.upper())
            return Mouse.LEFT_BUTTON


    @staticmethod
    def _get_keycode(key_name):
        try:
            return getattr(Keycode, key_name.upper())
        except AttributeError:
            print("Unknown key:", key_name)
            return getattr(Keycode, "A".upper())

    def set_new_profile(self, profile):
        try:
            self.buttons = profile["Buttons"]
        except KeyError:

            while True:
                print("Profile has no buttons! Fix your profile.json!")
                time.sleep(1)

        try:
            self.hold_mousekey = profile["Buttons"]["ReinHoldMouse"]
        except KeyError:
            print("ReinHoldMouse missing, setting to False")
            self.hold_mousekey = False
        try:
            self.rein_mode = profile["Buttons"]["ReinMode"]
        except KeyError:
            print("ReinMode missing, setting to Mouse")
            self.rein_mode = ["Mouse", "X", 1],



    def release_all(self):
        self.kbd.release_all()
        self.gamepad.release_all_buttons()
        self.gamepad.move_joysticks(x=0, y=0, z=0, r_z=0)
        self.mouse.move(x=0)
        self.mouse.move(y=0)
        self.mouse.release_all()

    def update(self,states):
        self.current_time = time.monotonic()
        for name, value in states.items():
            if value:

                # Let's add keys that needs to be pressed

                # [0] MODE
                # [1] KEYCODE
                # [2] ACTION
                # [3] TIME
                # [4] ANALOG VALUE

                try:
                    mapping = self.buttons[name]
                except KeyError:
                    print("WARNING: ", name, " does not exist!")
                    mapping = ["Keyboard", "A", "Tap", 0.5]

                if mapping[0] not in self.modes:
                    print("WARNING: ", mapping[0], " is not valid mode!")
                    return
                if mapping[0] == "Macro":
                    print("Macro detected!")
                    for i in mapping[1]:

                        key = self.read_input(i)
                        self.add_to_inputs(key)
                        self.handle_toggle_release(key)
                else:
                    key = self.read_input(mapping)
                    self.add_to_inputs(key)
                    self.handle_toggle_release(key)

        self.handle_tap_release()

    def press(self, key):
        keycode = key[1]
        analog_value = key[4]
        current_mode = key[0]
        if keycode == "ReleaseAll":
            self.release_all()
            return

        if current_mode == "Keyboard":
            if DEBUG: print("Press kb", keycode)
            self.kbd.press(self._get_keycode(keycode))
        elif current_mode == "MouseButton":
            if DEBUG: print("Press mouse", keycode)
            self.mouse.press(self._get_mouse_code(keycode))
        elif current_mode == "Gamepad":
            if DEBUG: print("Press Gamepad", keycode)
            self.gamepad.press_buttons(self._get_gamepad_code(keycode))
        elif current_mode == "Analog":
            if analog_value > 127:
                analog_value = 127
            if analog_value < -127:
                analog_value = 127
            self.handle_analog(keycode, analog_value)
        elif current_mode == "MouseMove":

            self.handle_mouse_movement(keycode, analog_value)

    def release(self, key):
        keycode = key[1]
        current_mode = key[0]
        if keycode == "ReleaseAll":
            return

        if current_mode == "Keyboard":
            if DEBUG: print("Release Keyboard", keycode)
            self.kbd.release(self._get_keycode(keycode))
        elif current_mode == "MouseButton":
            if DEBUG: print("Release Mouse", keycode)
            self.mouse.release(self._get_mouse_code(keycode))
        elif current_mode == "Gamepad":
            if DEBUG: print("Release Gamepad", keycode)
            self.gamepad.release_buttons(self._get_gamepad_code(keycode))
        elif current_mode == "Analog":
            self.handle_analog(keycode, 0)
        elif current_mode == "MouseMove":
            self.handle_mouse_movement(keycode, 0)

    def handle_analog(self, keycode, analog_value):

        if DEBUG: print("Analog moved", keycode, analog_value)
        directions = ["LSX", "LSY", "RSY", "RSX"]
        if keycode not in directions:
            print("Unknown Analog key:", keycode)
            keycode = "LSX"
        if keycode == "LSX":
            self.gamepad.move_joysticks(x=analog_value)
        elif keycode == "LSY":
            self.gamepad.move_joysticks(y=analog_value)
        elif keycode == "RSX":
            self.gamepad.move_joysticks(z=analog_value)
        elif keycode == "RSY":
            self.gamepad.move_joysticks(r_z=analog_value)

    def handle_mouse_movement(self, keycode, analog_value):

        if DEBUG: print("Mouse moved", keycode, analog_value)
        directions = ["X", "Y", "Wheel"]
        if keycode not in directions:
            print("Unknown Mouse Direction:", keycode)
            keycode = "X"
        if keycode == "X":
            self.mouse.move(x=analog_value)
        elif keycode == "Y":
            self.mouse.move(y=analog_value)
        elif keycode == "Wheel":
            self.mouse.move(wheel=analog_value)


    def read_input(self, mapping):
        mode = mapping[0]
        # Add error handling!
        keycode = mapping[1]
        action = mapping[2]
        # Default Tap time
        try:
            release_time = (mapping[3] + self.current_time)
        except IndexError:
            release_time = 0.1 + self.current_time
        try:
            analog_value = (mapping[4])
            if analog_value < -127:
                analog_value = -127
            elif analog_value > 127:
                analog_value = 127


        except IndexError:
            analog_value = 0
        key = [mode, keycode, action, release_time, analog_value]
        if key[2] == "ToggleOn":
            key[2] = "Toggle"
            key[3] = "ToggleOn"
        return key

    def handle_tap_release(self):
        for index, item in enumerate(self.pressed_keys):
            release_time = item[3]
            action = item[2]
            keycode = item[1]

            # For keys with Tap
            if release_time != "ToggleOn":
                if self.current_time >= release_time and action == "Tap":
                    print("Tap released", item[1])

                    self.release(item)
                    self.pressed_keys.pop(index)


    def handle_toggle_release(self, key):
        action = key[2]
        if key[3] == "ToggleOn":
            return
        if action == "ToggleOff":
            action = "Toggle"
        if action == "Toggle" and self.toggled is False:
            for index, item in enumerate(self.pressed_keys):

                action = item[2]
                keycode = item[1]

                # For keys with Toggle
                if self.toggled is False and action == "Toggle":
                    print("Toggle released", item[1])
                    self.release(item)
                    self.pressed_keys.pop(index)


    def add_to_inputs(self, key):
        action = key[2]
        keycode = key[1]
        self.toggled = False
        if not any(x[0] == key[0] and x[1] == key[1] and x[2] == key[2] for x in self.pressed_keys):
            if action == "Toggle" or action == "Tap":
                self.pressed_keys.append(key)
            if action == "Toggle" or action == "ToggleOn":
                self.toggled = True
                print("Toggle On", keycode)
                self.press(key)
            if action == "Tap":
                print("Tap pressed", keycode)
                self.press(key)


    def analog_input(self, analog_states):



        # Todo: siisti tää

        left = int(map_range(analog_states[0], 0, 400, 0, 127))
        right = int(map_range(analog_states[1], 0, 400, 0, 127))

        allowed_modes = ["Mouse","Analog","Gamepad","Keyboard"]

        try:
            left_key = self.rein_mode[1][0]
            right_key = self.rein_mode[1][1]
            threshold = self.rein_mode[1][2]
        except IndexError:
            left_key = "A"
            right_key = "D"
            threshold = 50
        if self.rein_mode[0] not in allowed_modes:

            return

        rein_value = right - left
        mode = self.rein_mode[0]
        axis = self.rein_mode[1][0]



        if rein_value != 0:
            if mode == "Mouse":
                if self.hold_mousekey:
                    time.sleep(0.02)
                    self.mouse.press(Mouse.LEFT_BUTTON)
                self.mouse.move(x=rein_value)
                self.reins_moved = True
                return
            elif mode == "Analog":
                self.handle_analog(axis, rein_value)
                self.reins_moved = True
                return
            elif mode == "Keyboard":

                if left >= threshold:
                    self.kbd.press(self._get_keycode(left_key))
                    self.reins_moved = True
                if right >= threshold:
                    self.kbd.press(self._get_keycode(right_key))
                    self.reins_moved = True
            elif mode == "Gamepad":

                if left >= threshold:
                    self.gamepad.press_buttons(self._get_gamepad_code(left_key))
                    self.reins_moved = True
                if right >= threshold:
                    self.gamepad.press_buttons(self._get_gamepad_code(right_key))
                    self.reins_moved = True
        else:

            if mode == "Mouse" and self.hold_mousekey:
                self.mouse.release(Mouse.LEFT_BUTTON)
                self.reins_moved = False
            elif mode == "Keyboard" and self.reins_moved:
                self.kbd.release(self._get_keycode(left_key))
                self.kbd.release(self._get_keycode(right_key))
                self.reins_moved = False
            elif mode == "Gamepad" and self.reins_moved:
                self.gamepad.release_buttons(self._get_gamepad_code(left_key))
                self.gamepad.release_buttons(self._get_gamepad_code(right_key))
                self.reins_moved = False

            elif mode == "Analog" and self.reins_moved:
                self.handle_analog(axis, 0)
                self.reins_moved = False




            #TODO: wasd juttu





