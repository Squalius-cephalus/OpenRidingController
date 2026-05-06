import adafruit_nunchuk
import board
import busio
from debug import log

class NunchuckHandler:
    def __init__(self):
        try:
            i2c = busio.I2C(board.GP1, board.GP0)
            log("Nunchuck controller detected")
            self.nc = adafruit_nunchuk.Nunchuk(i2c)
            self.nunchuck_connected = True
        except Exception as e:
            log("Nunchuck not controller detected", e)
            self.nunchuck_connected = False

        self.states = {}
        self.nunchuck_settings = {}
        self.nunchuck_mode = ""
        self.nunchuck_sensitivity = 0
        self.nunchuck_joystick_axis = ""

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
            log("Nunchuck controller disconnected!")
        

    


    def handle_nunchuck(self):

        joystick_x, joystick_y = self.nc.joystick
        button_c = self.nc.buttons.C
        button_z = self.nc.buttons.Z
        
        deadzone = 5
        nunchuck_button_states = {
            "nunchuck_c_button": False,
            "nunchuck_z_button": False,
        }

        if button_c:
            nunchuck_button_states["nunchuck_c_button"] = True
        if button_z:
            nunchuck_button_states["nunchuck_z_button"] = True


        centered_x = joystick_x - 128
        centered_y = joystick_y - 128
        if self.nunchuck_mode == "mouse":
            if abs(centered_x) < deadzone:
                centered_x = 0
            if abs(centered_y) < deadzone:
                centered_y = 0


        sensitivity = self.nunchuck_sensitivity
        if sensitivity == None:
            sensitivity = 1
        centered_x = int(centered_x * sensitivity)
        centered_y = int(centered_y * sensitivity)

        
        self.analog_x = centered_x
        self.analog_y = -centered_y

        return nunchuck_button_states

            
  
    
    def detect_flick(self, current_time):

        nunchuck_flick_states = {
            "nunchuck_flick_left": False,
            "nunchuck_flick_right": False,
        }

        x, y, z = self.nc.acceleration


        # TODO: Move to settings.json
        flick_threshold = 450

        accel_x = x - self.last_x_nunchuck

        if (current_time - self.last_nunchuck_flick) > 0.2:
            if abs(accel_x) > flick_threshold:
                if accel_x >0:
                    nunchuck_flick_states["nunchuck_flick_right"] = True
                    log(accel_x)
                else:
                    nunchuck_flick_states["nunchuck_flick_left"] = True
                self.last_nunchuck_flick = current_time

        self.last_x_nunchuck = x

        return nunchuck_flick_states
    

    def set_new_profile(self, profile):
        self.nunchuck_settings = profile["nunchuck_mode"]
        self.nunchuck_mode = self.nunchuck_settings.get("mode")
        self.nunchuck_sensitivity = self.nunchuck_settings.get("sensitivity")
        self.nunchuck_joystick_axis = self.nunchuck_settings.get("axis")

    def get_states(self):
        return self.states
    
    def is_connected(self):
        return self.nunchuck_connected
    
    def get_analog_states(self):
        if not self.nunchuck_connected:
            return None
        return {"x":self.analog_x, 
                "y":self.analog_y, 
                "mode": self.nunchuck_mode, 
                "sensitivity": self.nunchuck_sensitivity, 
                "axis": self.nunchuck_joystick_axis}
    

