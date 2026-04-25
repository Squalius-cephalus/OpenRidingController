import adafruit_nunchuk
import board
import busio




class NunchuckHandler:
    def __init__(self):
        try:
            i2c = busio.I2C(board.GP1, board.GP0)
            print("Nunchuck controller detected")
            self.nc = adafruit_nunchuk.Nunchuk(i2c)
            self.nunchuck_connected = True
        except Exception:
            print("Nunchuck not controller detected")
            self.nunchuck_connected = False

        
        
        self.states = {}
        self.nunchuck_mode = []


        self.nunchuck_c_released = False
        self.nunchuck_z_released = False
        
        self.last_x_nunchuck = 700
        self.last_nunchuck_flick = 0



    def update(self, current_time, mouse, gamepad):
        self.states = {}
        try:
            self.states = self.handle_nunchuck(mouse, gamepad) | self.detect_flick(current_time)
        except OSError:
            self.nunchuck_connected = False
            print("Nunchuck controller disconnected!")
        

    


    def handle_nunchuck(self, mouse, gamepad):

        joystick_x, joystick_y = self.nc.joystick
        button_c = self.nc.buttons.C
        button_z = self.nc.buttons.Z
        
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

        centered_x = int(centered_x * sensitivity)
        centered_y = int(centered_y * sensitivity)
        
        if abs(centered_x)+abs(centered_y)>0:
            if self.nunchuck_mode[0] == "Mouse":
                mouse.move_xy(centered_x, -centered_y)
            if self.nunchuck_mode[0] == "Joystick":
        
                try:
                    stick = self.nunchuck_mode[2]
                except IndexError:
                    stick = "LS"

                x_axis = stick+"X"
                y_axis = stick+"Y"
                gamepad.move(x_axis, int(centered_x*sensitivity))
                gamepad.move(y_axis, int(-centered_y*sensitivity))

        return nunchuck_button_states

            
  
    
    def detect_flick(self, current_time):

        nunchuck_flick_states = {
            "Nunchuck Left Flick": False,
            "Nunchuck Right Flick": False,
        }

        x, y, z = self.nc.acceleration


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
    

    def update_profile(self, profile):
        self.nunchuck_mode = profile["Nunchuck Mode"]

    def get_states(self):
        return self.states
    
    def is_connected(self):
        return self.nunchuck_connected


