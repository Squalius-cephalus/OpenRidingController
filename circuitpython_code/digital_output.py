import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
import time


from hid_gamepad import Gamepad
class DigitalHandler:
    def __init__(self):
        self.keyboard = Keyboard(usb_hid.devices)

        self.gamepad = Gamepad(usb_hid.devices)
        self.buttons = {}
        self.previous_states = {}
        self.hold_keys = {}
        self.toggle_keys = {}
        self.reserved_keys = []
        self.last_time = 0
        self.analog_handler = None



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


    def update(self, states, analog_handler):
        current_time = time.monotonic()
        self.analog_handler = analog_handler

        if self.reserved_keys:
            if not self.hold_keys:

                a = len(self.reserved_keys) - 1

                self.parse_input(self.reserved_keys[a],current_time)

                self.reserved_keys.pop(0)





        for i, activated in states.items():
            if activated:
                button = self.buttons[i]

                if button[0] == "Macro":
                    print("Macro detected")
                    for ii in button:
                        self.parse_input(ii, current_time)

                elif button[0] == "None":
                    print("Button skipped")


                else:
                    self.parse_input(button, current_time)

        self.release_hold_keys(current_time)


    def parse_input(self,button, current_time):
        try:
            mode = button[0]
            key = button[1]
            action = button[2]
        except IndexError:
            print("ERROR: Check your profile!")
            mode = "Keyboard"
            key = "A"
            action = "Tap"
        try:
            value = button[3]
        except IndexError:
            value = 1
        try:

            analog_value = button[4]
        except IndexError:


            analog_value = 50
        if action == "Hold":
            self.add_hold_keys(key, value, mode, current_time,analog_value)
        elif action == "Tap":
            self.add_hold_keys(key, 0.3, mode, current_time, analog_value)
        elif action == "Toggle" or action == "ToggleOn" or action == "ToggleOff":
            self.handle_toggle_keys(key, mode, action,analog_value)
        elif action == "Multitap":
            self.handle_multitap_keys(key, value, mode,analog_value)
            print(button)

    def add_hold_keys(self, key, value, mode, current_time,analog_value):
        expiry = current_time + value
        self.hold_keys[key] = [mode, expiry]
        self.press_key(key, mode, analog_value)

    def handle_multitap_keys(self, key, value, mode,analog_value):
        print("Multitap detected")
        for i in range(value):
            button = [mode, key, "Tap", 0,analog_value]
            self.reserved_keys.append(button)


    def handle_toggle_keys(self, key, mode, action,analog_value):
        if self.toggle_keys.get(key) == mode:
            if action == "Toggle" or action == "ToggleOff":
                del self.toggle_keys[key]
                self.release_key(key, mode)
        else:
            if action != "ToggleOff":
                self.toggle_keys[key] = mode
                self.press_key(key, mode, analog_value)


    def release_hold_keys(self, current_time):
        to_remove = []

        for key, (mode, expiry) in self.hold_keys.items():
            if current_time >= expiry:
                to_remove.append([key, mode])

        for key in to_remove:
            self.release_key(key[0], key[1])
            self.hold_keys.pop(key[0])




    def release_key(self, key, mode):
        print(key, mode, "released")
        if mode == "Keyboard":
            keycode = self._get_keycode(key)
            self.keyboard.release(keycode)
        elif mode == "Gamepad":
            keycode = self._get_gamepad_code(key)
            self.gamepad.release_buttons(keycode)
        elif mode == "MouseButtons":
            self.analog_handler.mouse_button_release(key)
        elif mode == "MouseMove":
            self.analog_handler.mouse_button_release(key)
            self.analog_handler.mouse_move_xy(key, 0)
        elif mode == "Joystick":
            self.analog_handler.handle_analog(key, 0)


    def press_key(self, key, mode, analog_value):
        print(key, mode, "pressed")
        if mode == "Keyboard":
            keycode = self._get_keycode(key)
            self.keyboard.press(keycode)
        elif mode == "Gamepad":
            keycode = self._get_gamepad_code(key)
            self.gamepad.press_buttons(keycode)
        elif mode == "MouseButtons":
            self.analog_handler.mouse_button_press(key)
        elif mode == "MouseMove":
            self.analog_handler.mouse_move_xy(key, analog_value)
        elif mode == "Joystick":
            self.analog_handler.handle_analog(key, analog_value)

    def _get_gamepad_code(self, key_name):
        key = self.gamepad_map.get(key_name.upper())
        if key is None:
            print("Unknown gamepad key", key_name.upper())
            return 1
        return key





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

    def release_all(self):
        self.keyboard.release_all()



