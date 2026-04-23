import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
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
        self.last_tap = 0.0
        self.key_pressed = False
        self.key_send = False
        self.previous_mouse_position = 0
        self.cursor_offset = 0
        self.prev = 0
        self.mouse_release_timer = 0.0
        self.mouse_timer = False
        self.mouse_moved = False
        self.current_position = 0.0


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
        current_time = time.monotonic()

        left = analog_inputs[0]
        right = analog_inputs[1]
        analog = right-left





        mode = self.rein_mode[0]
        button = self.rein_mode[1]
        action = self.rein_mode[2]

        if mode == "Mouse":
            self.mouse_movement(action, button, analog, current_time)
        if mode == "Joystick":
            self.joystick_movement(button, action, analog)
        if mode == "Keyboard":
            try:
                threshold = self.rein_mode[3]
            except IndexError:
                threshold = 64
            self.keyboard_out(button, action, analog, threshold)



    def keyboard_out(self, right_button, left_button, analog, threshold):
        if analog > threshold:
            self.kbd.press(getattr(Keycode, right_button.upper()))
        elif analog < -threshold and not 0:
            self.kbd.press(getattr(Keycode, left_button.upper()))
        else:
            self.kbd.release(getattr(Keycode, left_button.upper()))
            self.kbd.release(getattr(Keycode, right_button.upper()))
    def mouse_movement(self, hold, button, analog_amount, current_time):


        if analog_amount > 512:
            analog_amount = 512
        elif analog_amount < -512:
            analog_amount = -512

        dx = self.update_axis(analog_amount)




        
        if self.current_position == 0:
            if not self.mouse_timer and self.mouse_moved:
                print("timer started")
                self.mouse_release_timer = current_time
                self.mouse_timer = True

            if current_time-self.mouse_release_timer > 0.2 and self.mouse_moved:
                self.mouse_timer = False
                print("mouse released")
                self.mouse_moved = False
                self.mouse.release(self._get_mouse_code(button))

        else:
            if self.current_position != 0:
                if hold == "Hold":

                    self.mouse.press(self._get_mouse_code(button))
                    self.mouse_release_timer = current_time
                    self.mouse_moved = True




        self.mouse.move(x=dx)

    def update_axis(self, value):
        MAX_OFFSET = 2048
        DEADZONE = 5

        # deadzone
        if abs(value) < DEADZONE:
            target = 0
        else:
            # map directly to position range
            target = (value * MAX_OFFSET) // 512

        # movement needed to reach target
        dx = target - self.current_position

        # update position
        self.current_position = target

        return dx


    def mouse_movement_generic(self, hold, button, analog_amount, release):

        if release:
            self.mouse.release(self._get_mouse_code(button))
            self.mouse_pressed = False
            return
        if hold == "Hold":
            self.mouse.press(self._get_mouse_code(button))
            self.mouse_pressed = True
        self.mouse.move(x=analog_amount)

    def mouse_move_xy(self, axis, analog_amount):
        directions = ["X", "Y", "Wheel"]
        if axis not in directions:
            print("Unknown Mouse Direction:", axis)
            axis = "X"
        if axis == "X":
            self.mouse.move(x=analog_amount)
        elif axis == "Y":
            self.mouse.move(y=analog_amount)
        elif axis == "Wheel":
            self.mouse.move(wheel=analog_amount)

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

    def handle_analog(self, keycode, analog_value):

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



    def mouse_button_release(self, key):
        keycode = self._get_mouse_code(key)
        self.mouse.release(keycode)

    def mouse_button_press(self, key):
        keycode = self._get_mouse_code(key)
        self.mouse.press(keycode)



    def set_new_profile(self, profile):
        self.rein_mode = profile["Rein Mode"]

    def _get_mouse_code(self, key_name):
        key = self.mouse_map.get(key_name.upper())
        if key is None:
            print("Unknown mouse key", key_name.upper())
            return Mouse.LEFT_BUTTON
        return key

    def release_all(self):
        directions = ["LSX", "LSY", "RSY", "RSX"]
        for i in directions:
            self.handle_analog(i, 0)

        self.gamepad.release_all_buttons()
        self.mouse.release_all()

