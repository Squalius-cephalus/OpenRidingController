"""
OpenRidingController Revision 1

This module handles extra inputs(button 1 to 4). 

"""

import board
import digitalio

# Configure extra buttons 1, 2, 3 and 4.
button1 = digitalio.DigitalInOut(board.GP9)
button1.direction = digitalio.Direction.INPUT
button1.pull = digitalio.Pull.UP

button2 = digitalio.DigitalInOut(board.GP10)
button2.direction = digitalio.Direction.INPUT
button2.pull = digitalio.Pull.UP

button3 = digitalio.DigitalInOut(board.GP11)
button3.direction = digitalio.Direction.INPUT
button3.pull = digitalio.Pull.UP

button4 = digitalio.DigitalInOut(board.GP12)
button4.direction = digitalio.Direction.INPUT
button4.pull = digitalio.Pull.UP

buttons = (button1, button2, button3, button4)

class ButtonState:
    """
    Tracks whether the button is currently pressed and whether
    it was newly pressed during the latest update cycle.
    """
    def __init__(self, pin):
        """
        Initialize a button state tracker.

        Args:
            pin: Configured DigitalInOut pin object.
        """
        self.pin = pin
        self.pressed = False
        self.triggered = False

    def update(self):
        """
        Extra buttons acts like the stirrup inputs.

        Detects rising-edge button presses and updates:
        - pressed: True while held down.
        - triggered: True only on the frame the button was pressed.
        
        
        """
        self.triggered = False

        currently_pressed = not self.pin.value

        if currently_pressed and not self.pressed:
            self.triggered = True

        self.pressed = currently_pressed


class ButtonHandler:

    """
    Manages multiple extra button inputs.

    Creates and updates ButtonState objects for each configured
    button and returns their trigger states.
    """
    def __init__(self):

        self.buttons = {}

        for index, pin in enumerate(buttons, start=1):
            name = f"button{index}"
            self.buttons[name] = ButtonState(pin)

    def update(self):
        """
        Update current states of the extra buttons.
        """
        for button in self.buttons.values():
            button.update()

    def get_states(self):
        """
        Returns states of the extra buttons.
        """

        states = {}

        for name, button in self.buttons.items():
            states[name] = button.triggered

        return states
