class ButtonState:
    def __init__(self, pin):
        self.pin = pin
        self.pressed = False
        self.triggered = False

    def update(self):

        self.triggered = False

        currently_pressed = not self.pin.value

        if currently_pressed and not self.pressed:
            self.triggered = True

        self.pressed = currently_pressed


class ButtonHandler:
    def __init__(self, *buttons):

        self.buttons = {}

        for index, pin in enumerate(buttons, start=1):
            name = f"button{index}"
            self.buttons[name] = ButtonState(pin)

    def update(self):

        for button in self.buttons.values():
            button.update()

    def get_states(self):

        states = {}

        for name, button in self.buttons.items():
            states[name] = button.triggered

        return states