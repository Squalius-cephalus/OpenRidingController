import adafruit_nunchuk
import board
import busio
from debug import log

class NunchukHandler:
    def __init__(self):
        try:
            i2c = busio.I2C(board.GP1, board.GP0)
            log("Nunchuk controller detected")
            self.nc = adafruit_nunchuk.Nunchuk(i2c)
            self.nunchuk_connected = True
        except Exception as e:
            log("Nunchuk not controller detected", e)
            self.nunchuk_connected = False

        self.states = {}
        self.nunchuk_settings = {}
        self.nunchuk_mode = ""
        self.nunchuk_sensitivity = 0
        self.nunchuk_joystick_axis = ""

        self.nunchuk_c_released = False
        self.nunchuk_z_released = False
        
        self.last_x_nunchuk = 700
        self.last_nunchuk_flick = 0

        self.analog_x = 0
        self.analog_y = 0



    def update(self, current_time):
        self.states = {}
        try:
            self.states = self.handle_nunchuk() | self.detect_flick(current_time)
        except OSError:
            self.nunchuk_connected = False
            self.analog_x = 0
            self.analog_y = 0
            log("Nunchuk controller disconnected!")
        

    


    def handle_nunchuk(self):

        joystick_x, joystick_y = self.nc.joystick
        button_c = self.nc.buttons.C
        button_z = self.nc.buttons.Z
        
        deadzone = 5
        nunchuk_button_states = {
            "nunchuk_c_button": False,
            "nunchuk_z_button": False,
        }

        if button_c:
            nunchuk_button_states["nunchuk_c_button"] = True
        if button_z:
            nunchuk_button_states["nunchuk_z_button"] = True


        centered_x = joystick_x - 128
        centered_y = joystick_y - 128
        if self.nunchuk_mode == "mouse":
            if abs(centered_x) < deadzone:
                centered_x = 0
            if abs(centered_y) < deadzone:
                centered_y = 0


        sensitivity = self.nunchuk_sensitivity
        if sensitivity == None:
            sensitivity = 1
        centered_x = int(centered_x * sensitivity)
        centered_y = int(centered_y * sensitivity)

        
        self.analog_x = centered_x
        self.analog_y = centered_y

        return nunchuk_button_states

            
  
    
    def detect_flick(self, current_time):

        nunchuk_flick_states = {
            "nunchuk_flick_left": False,
            "nunchuk_flick_right": False,
        }

        x, y, z = self.nc.acceleration


        # TODO: Move to settings.json
        flick_threshold = 450

        accel_x = x - self.last_x_nunchuk

        if (current_time - self.last_nunchuk_flick) > 0.2:
            if abs(accel_x) > flick_threshold:
                if accel_x >0:
                    nunchuk_flick_states["nunchuk_flick_right"] = True
                    log(accel_x)
                else:
                    nunchuk_flick_states["nunchuk_flick_left"] = True
                self.last_nunchuk_flick = current_time

        self.last_x_nunchuk = x

        return nunchuk_flick_states
    

    def set_new_profile(self, profile):
        self.nunchuk_settings = profile["nunchuk_mode"]
        self.nunchuk_mode = self.nunchuk_settings.get("mode")
        self.nunchuk_sensitivity = self.nunchuk_settings.get("sensitivity")
        self.nunchuk_joystick_axis = self.nunchuk_settings.get("axis")

    def get_states(self):
        return self.states
    
    def is_connected(self):
        return self.nunchuk_connected
    
    def get_analog_states(self):
        if not self.nunchuk_connected:
            return None
        return {"x":self.analog_x, 
                "y":self.analog_y, 
                "mode": self.nunchuk_mode, 
                "sensitivity": self.nunchuk_sensitivity, 
                "axis": self.nunchuk_joystick_axis}
    

