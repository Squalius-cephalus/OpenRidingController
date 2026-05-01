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
        self.nunchuck_mode = {}

        self.nunchuck_c_released = False
        self.nunchuck_z_released = False
        
        self.last_x_nunchuck = 700
        self.last_nunchuck_flick = 0

        self.analog_x = 0
        self.analog_y = 0



    def update(self, current_time):
        self.states = {}
        try:
            self.states = self.handle_nunchuck() | self.detect_flick(current_time)
        except OSError:
            self.nunchuck_connected = False
            self.analog_x = 0
            self.analog_y = 0
            print("Nunchuck controller disconnected!")
        

    


    def handle_nunchuck(self):

        joystick_x, joystick_y = self.nc.joystick
        button_c = self.nc.buttons.C
        button_z = self.nc.buttons.Z
        
        deadzone = 5
        nunchuck_button_states = {
            "NunchuckCButton": False,
            "NunchuckZButton": False,
        }

        if button_c:
            nunchuck_button_states["NunchuckCButton"] = True
        if button_z:
            nunchuck_button_states["NunchuckZButton"] = True


        centered_x = joystick_x - 128
        centered_y = joystick_y - 128
        if self.nunchuck_mode.get("Mode") == "Mouse":
            if abs(centered_x) < deadzone:
                centered_x = 0
            if abs(centered_y) < deadzone:
                centered_y = 0


        sensitivity = self.nunchuck_mode.get("Sensitivity")
        if sensitivity == None:
            sensitivity = 1

        centered_x = int(centered_x * sensitivity)
        centered_y = int(centered_y * sensitivity)
        
        self.analog_x = centered_x
        self.analog_y = -centered_y

        return nunchuck_button_states

            
  
    
    def detect_flick(self, current_time):

        nunchuck_flick_states = {
            "NunchuckLeftFlick": False,
            "NunchuckRightFlick": False,
        }

        x, y, z = self.nc.acceleration


        # TODO: Move to settings.json
        flick_threshold = 450

        accel_x = x - self.last_x_nunchuck

        if (current_time - self.last_nunchuck_flick) > 0.2:
            if abs(accel_x) > flick_threshold:
                if accel_x >0:
                    nunchuck_flick_states["NunchuckRightFlick"] = True
                    print(accel_x)
                else:
                    nunchuck_flick_states["NunchuckLeftFlick"] = True
                self.last_nunchuck_flick = current_time

        self.last_x_nunchuck = x

        return nunchuck_flick_states
    

    def update_profile(self, profile):
        self.nunchuck_mode = profile["NunchuckMode"]

    def get_states(self):
        return self.states
    
    def is_connected(self):
        return self.nunchuck_connected
    
    def get_analog_states(self):
        return self.analog_x, self.analog_y


