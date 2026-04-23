import usb_hid
from adafruit_hid.mouse import Mouse
class MouseOutput:
    def __init__(self):
        self.mouse = Mouse(usb_hid.devices)
        self.previous = 0
        self.dead_zone = 30
        self.current_position = 0
        self.mouse_moved = False


        self.mouse_map = {
            "LEFT_BUTTON": Mouse.LEFT_BUTTON,
            "RIGHT_BUTTON": Mouse.RIGHT_BUTTON,
            "MIDDLE_BUTTON": Mouse.MIDDLE_BUTTON,
            "BACK_BUTTON": Mouse.BACK_BUTTON,
            "FORWARD_BUTTON": Mouse.FORWARD_BUTTON,
        }


    def release(self, key):
        keycode = self._get_mouse_code(key)
        self.mouse.release(keycode)

    def press(self, key):
        keycode = self._get_mouse_code(key)
        self.mouse.press(keycode)

    def move(self, axis, analog_amount):
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

    def move_xy(self, analog_amount_x=0, analog_amount_y=0, wheel=0):

        self.mouse.move(x=analog_amount_x, y=analog_amount_y, wheel=wheel)



    def reins_output(self, mouse_button, hold, analog_amount, returning):
            combined = analog_amount[1]+analog_amount[0]
            movement = analog_amount[1]-analog_amount[0]
            if hold == "Hold" and combined>self.dead_zone:
                self.press(mouse_button)
            

            if returning:
                movement = self.update_axis(movement)
                if abs(movement)>0:
                    self.move("X", movement)
                    self.mouse_moved = True
                self.previous = movement
            else:
                if abs(movement)>(int(self.dead_zone/2)):
                    self.move("X",movement)
                    self.previous = movement

            if hold == "Hold" and abs(combined) < 6 and self.mouse_moved:
                self.release(mouse_button)
                self.mouse_moved = False


    def release_all(self):
        self.mouse.release_all()
        self.mouse.move(x=0, y=0, wheel=0)


    def _get_mouse_code(self, key_name):
        key = self.mouse_map.get(key_name.upper())
        if key is None:
            print("Unknown mouse key", key_name.upper())
            return Mouse.LEFT_BUTTON
        return key

        
    def update_axis(self, analog_amount):
        max_distance = 1024

        if abs(analog_amount) < self.dead_zone:
            target = 0
        else:
            target = (analog_amount * max_distance) // 512
        
        movement = target - self.current_position
        self.current_position = target

        return movement
