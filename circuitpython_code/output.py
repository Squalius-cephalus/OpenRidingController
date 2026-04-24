from keyboard_output import KeyboardOutput
from mouse_output import MouseOutput
from gamepad_output import GamepadOutput
keyboard = KeyboardOutput()
mouse = MouseOutput()
gamepad = GamepadOutput()
import adafruit_nunchuk
import board
import busio




class OutputManager:
    def __init__(self, settings):
        self.buttons = {}
        self.previous_states = {}
        self.hold_keys = {}
        self.toggle_keys = {}
        self.reserved_keys = []
        self.last_nunchuck_flick = 0
        self.rein_mode = [""]
        self.nunchuck_mode = [""]
        self.keyboard_reins_threshold = settings["KeyboardReinsThreshold"]
        self.gamepad_reins_threshold = settings["GamepadReinsThreshold"]
        self.tap_time = settings["Tap Time"]

        # TODO: Move these to own class!!

        try:
            self.i2c = busio.I2C(board.GP1, board.GP0)
            self.nc = adafruit_nunchuk.Nunchuk(self.i2c)
            self.nunchuck_connected = True
            print("Nunchuck controller detected!")
        except Exception:
            self.i2c = None
            self.nc = None
            self.nunchuck_connected = False


        self.nunchuck_c_released = False
        self.nunchuck_z_released = False
        
        self.last_x_nunchuck = 700
        self.last_nunchuck_flick = 0


        

    def update(self, states, analog_amount, current_time):
        if self.nunchuck_connected:
            states = states | self.handle_nunchuck() | self.detect_flick(current_time)

        
        if self.reserved_keys:
            if not self.hold_keys:
                a = len(self.reserved_keys) - 1
                self.parse_input(self.reserved_keys[a], current_time)
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
        self.update_reins_output(current_time, analog_amount)
        
        

    def parse_input(self, button, current_time):
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
            self.add_hold_keys(key, value, mode, current_time, analog_value)
        elif action == "Tap":
            self.add_hold_keys(key, self.tap_time, mode, current_time, analog_value)
        elif action == "Toggle" or action == "ToggleOn" or action == "ToggleOff":
            self.handle_toggle_keys(key, mode, action, analog_value)
        elif action == "Multitap":
            self.handle_multitap_keys(key, value, mode, analog_value)
            print(button)

    def add_hold_keys(self, key, value, mode, current_time, analog_value):
        expiry = current_time + value
        self.hold_keys[key] = [mode, expiry]
        self.press_key(mode, key, analog_value)

    def handle_multitap_keys(self, key, value, mode, analog_value):
        print("Multitap detected")
        for i in range(value):
            button = [mode, key, "Tap", 0, analog_value]
            self.reserved_keys.append(button)

    def handle_toggle_keys(self, key, mode, action, analog_value):
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

    def release_key(self, mode, key):
        print(mode, key, "released")
        if mode == "Keyboard":
            keyboard.release(key)
        elif mode == "Gamepad":
            gamepad.release(key)
        elif mode == "MouseButtons":
            mouse.release(key)
        elif mode == "MouseMove":
            mouse.move(key,0)
        elif mode == "Joystick":
            gamepad.move(key,0)


    def press_key(self, mode, key, analog_value):
        print(mode, key, "pressed")
        if mode == "Keyboard":
            keyboard.press(key)
        elif mode == "Gamepad":
            gamepad.press(key)
        elif mode == "MouseButtons":
            mouse.press(key)
        elif mode == "MouseMove":
            mouse.move(key, analog_value)
        elif mode == "Joystick":
            gamepad.move(key, analog_value)



    def set_new_profile(self, profile):
        try:
            self.buttons = profile["Buttons"]
            self.rein_mode = profile["Rein Mode"]
            self.nunchuck_mode = profile["Nunchuck Mode"]
        except KeyError:
            while True:
                print("Profile has no buttons! Fix your profile.json!")



    def release_all(self):
        mouse.release_all()
        keyboard.release_all()
        gamepad.release_all()

    def update_reins_output(self, current_time, analog_value):

        if self.rein_mode[0] == "Mouse":
            mouse_button = self.rein_mode[1]
            hold = self.rein_mode[2]
            mouse.reins_output(mouse_button, hold, analog_value, False)
        elif self.rein_mode[0] == "MouseReturning":
            mouse_button = self.rein_mode[1]
            hold = self.rein_mode[2]
            mouse.reins_output(mouse_button, hold, analog_value, True)
        elif self.rein_mode[0] == "Gamepad":
            left_key = self.rein_mode[1]
            right_key = self.rein_mode[2]
            gamepad.reins_output(left_key, right_key, self.keyboard_reins_threshold, analog_value)
        elif self.rein_mode[0] == "Keyboard":
            left_key = self.rein_mode[1]
            right_key = self.rein_mode[2]
            keyboard.reins_output(left_key, right_key, self.keyboard_reins_threshold, analog_value)
        elif self.rein_mode[0] == "Joystick":
            analog_value = analog_value[1]-analog_value[0]
            gamepad.move("LSX", analog_value)


    def handle_nunchuck(self):
        # TODO: move i2c stuff to own function with proper error handling

        try:
            joystick_x, joystick_y = self.nc.joystick
            button_c = self.nc.buttons.C
            button_z = self.nc.buttons.Z
        except Exception:
            print("Nunchuck disconnected. Reconnecting requires reboot!")
            self.nunchuck_connected = False
            return {}

        
        #ax, ay, az = self.nc.acceleration
        deadzone = 5
        nunchuck_button_states = {
            "Nunchuck C Button": False,
            "Nunchuck Z Button": False,
        }

        if button_c:
            nunchuck_button_states["Nunchuck C Button"] = True
        if button_z:
            nunchuck_button_states["Nunchuck Z Button"] = True


        centered_x = joystick_x - 128
        centered_y = joystick_y - 128

        if abs(centered_x) < deadzone:
            centered_x = 0
        if abs(centered_y) < deadzone:
            centered_y = 0

        try:
            sensitivity = self.nunchuck_mode[1]
        except IndexError:
            sensitivity = 1

        centered_x = int(centered_x / sensitivity)
        centered_y = int(centered_y / sensitivity)


        if self.nunchuck_mode[0] == "Mouse":
            mouse.move_xy(centered_x, -centered_y)

        if self.nunchuck_mode[0] == "Analog":
     
            try:
                stick = self.nunchuck_mode[2]
            except IndexError:
                stick = "LS"

            x_axis = stick+"X"
            y_axis = stick+"Y"

            gamepad.move(x_axis, centered_x)
            gamepad.move(y_axis, -centered_y)

        return nunchuck_button_states

            
  
    
    def detect_flick(self, current_time):
        # TODO: merge duplicate code
        nunchuck_flick_states = {
            "Nunchuck Left Flick": False,
            "Nunchuck Right Flick": False,
        }
        try:
            x, y, z = self.nc.acceleration
        except Exception:
            print("Nunchuck disconnected. Reconnecting requires reboot!")
            self.nunchuck_connected = False
            return {}

        # TODO: Move to settings.json
        flick_threshold = 450

        accel_x = x - self.last_x_nunchuck

        if (current_time - self.last_nunchuck_flick) > 0.2:
            if abs(accel_x) > flick_threshold:
                if accel_x >0:
                    nunchuck_flick_states["Nunchuck Right Flick"] = True
                    print(accel_x)
                else:
                    nunchuck_flick_states["Nunchuck Left Flick"] = True
                self.last_nunchuck_flick = current_time

        self.last_x_nunchuck = x

        return nunchuck_flick_states


