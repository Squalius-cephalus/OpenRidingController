import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.mouse import Mouse
import time
from hid_gamepad import Gamepad

class AnalogHandler:
    def __init__(self):
        self.states = {}
        self.rein_mode = [""]
        self.mouse_pressed = False
        self.joystick_moved = False
        self.kbd = Keyboard(usb_hid.devices)
        self.mouse = Mouse(usb_hid.devices)
        self.gamepad = Gamepad(usb_hid.devices)

        # Rein Mode: Mode, Key/axis, Key/axis
        # Mouse, LEFT_MOUSE, Hold
        # Joystick, LS, X

        # Pass to DigitalHandler
        # Keyboard, A, D

        self.mouse_map = {
            "LEFT_BUTTON": Mouse.LEFT_BUTTON,
            "RIGHT_BUTTON": Mouse.RIGHT_BUTTON,
            "MIDDLE_BUTTON": Mouse.MIDDLE_BUTTON,
            "BACK_BUTTON": Mouse.BACK_BUTTON,
            "FORWARD_BUTTON": Mouse.FORWARD_BUTTON,
        }

    def update(self, analog_inputs):

        left = analog_inputs[0]
        right = analog_inputs[1]
        analog = right-left

        mode = self.rein_mode[0]
        button = self.rein_mode[1]
        action = self.rein_mode[2]
        if analog != 0:
            if mode == "Mouse":
                self.mouse_movement(action, button, analog, False)
            if mode == "Joystick":
                self.joystick_movement(button, action, analog)

        else:
            if self.mouse_pressed:
                self.mouse_movement(action, button, analog, True)
            if self.joystick_moved:
                self.joystick_moved = False



    def mouse_movement(self, hold, button, analog_amount, release):
        if release:
            self.mouse.release(self._get_mouse_code(button))
            self.mouse_pressed = False
            return
        if hold == "Hold":
            self.mouse.press(self._get_mouse_code(button))
            self.mouse_pressed = True
        self.mouse.move(x=analog_amount)

    def joystick_movement(self, stick, axis, analog_amount):
        if stick == "Left":
            if axis.upper() == "Y":
                self.gamepad.move_joysticks(y=analog_amount)
            else:
                self.gamepad.move_joysticks(x=analog_amount)
        if stick == "Right":
            if axis.upper() == "Y":
                self.gamepad.move_joysticks(z=analog_amount)
            else:
                self.gamepad.move_joysticks(r_z=analog_amount)


    def set_new_profile(self, profile):
        self.rein_mode = profile["Rein Mode"]

    def _get_mouse_code(self, key_name):
        key = self.mouse_map.get(key_name.upper())
        if key is None:
            print("Unknown mouse key", key_name.upper())
            return Mouse.LEFT_BUTTON
        return key

