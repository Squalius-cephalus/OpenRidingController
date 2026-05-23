"""
This module wraps Adafruit HID Mouse and process reins analog data for cursor movement.
"""

import usb_hid
from adafruit_hid.mouse import Mouse
from debug import log

class MouseOutput:
    def __init__(self):
        self.mouse = Mouse(usb_hid.devices)
        self.previous = 0
        self.dead_zone = 0
        self.current_position = 0
        self.mouse_moved = False
        self.hold_timer = 0
        self.hold_timer_started = False
        self.mouse_pressed = False
        self.mouse_map = {
            "LEFT_BUTTON": Mouse.LEFT_BUTTON,
            "RIGHT_BUTTON": Mouse.RIGHT_BUTTON,
            "MIDDLE_BUTTON": Mouse.MIDDLE_BUTTON,
            "BACK_BUTTON": Mouse.BACK_BUTTON,
            "FORWARD_BUTTON": Mouse.FORWARD_BUTTON,
        }

    def release(self, key):
        """
        Gets valid keycode based on key argument and releases mouse button.
        """
        keycode = self._get_mouse_code(key)
        self.mouse.release(keycode)

    def click(self, key):
        """
        Gets valid keycode based on key argument and clicks mouse button.
        """
        keycode = self._get_mouse_code(key)
        self.mouse.click(keycode)

    def press(self, key):
        """
        Gets valid keycode based on key argument and presses mouse button.
        """
        keycode = self._get_mouse_code(key)
        self.mouse.press(keycode)

    def move(self, axis, analog_amount, sensitivity, analog_amount_y=None):
        """
        Moves mouse cursor on one or two axis.
        Args:
            axis: If axis is a keycode, method passes it to press method.
            ...
            ...
            ...
            analog_amount_y: If not none, move cursor in two axis
        """
        if analog_amount_y is not None:
            self.mouse.move(
                x=int(analog_amount * sensitivity), y=int(analog_amount_y * sensitivity)
            )
            return
        directions = ["X", "Y", "WHEEL"]
        if axis in self.mouse_map:
            self.press(axis)
            return
        if axis not in directions:
            log("Unknown Mouse Direction:", axis)
            axis = "X"
        if axis == "X":
            self.mouse.move(x=int(analog_amount * sensitivity))
        elif axis == "Y":
            self.mouse.move(y=int(analog_amount * sensitivity))
        elif axis == "WHEEL":
            self.mouse.move(wheel=int(analog_amount * sensitivity))

    def reins_output(
        self,
        mouse_button,
        hold,
        analog_amount,
        returning,
        current_time,
        sensitivity,
        max_distance,
    ):
        """
        Move mouse cursor based on reins analog values, if Mouse Return is activated,
        cursor will return it's original position.
        """
        movement =  int((analog_amount[1] - analog_amount[0])*sensitivity)


        if self.mouse_pressed and abs(movement)==0:
            if not self.hold_timer_started:
                self.hold_timer = current_time
                self.hold_timer_started = True
            if current_time - self.hold_timer >= 0.15:
                self.release(mouse_button)
                self.mouse_pressed = False
                self.hold_timer_started = False

        if abs(movement)>0:
            if returning:
                movement = self.update_axis(movement, max_distance)
            self.mouse.move(movement)

            if hold and not self.mouse_pressed:
                self.mouse_pressed = True
                self.press(mouse_button)
        else:
            if self.current_position != 0:
                self.mouse.move(self.current_position*-1)
                self.current_position = 0



    def release_all(self):
        """
        Releases all mouse buttons.
        """
        self.mouse.release_all()
        self.mouse.move(x=0, y=0, wheel=0)

    def _get_mouse_code(self, key_name):
        if key_name is not None:
            key = self.mouse_map.get(key_name.upper())
            if key is None:
                log("Unknown mouse key", key_name.upper())
                return Mouse.LEFT_BUTTON
            return key
        else:
            return Mouse.LEFT_BUTTON

    def update_axis(self, analog_amount, max_distance):
        """
        Calculates new position for the cursor, this is used when "Mouse Return" is activated.
        """
        target = (analog_amount * (max_distance)) // 511
        movement = target - self.current_position
        self.current_position = target

        return movement
