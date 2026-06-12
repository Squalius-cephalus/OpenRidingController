import time
import board
import displayio
import rotaryio
import adafruit_ssd1306


class Menu:
    def __init__(self, display, profile_names, settings):

        self.display = display
        self.current_index = 0
        # UI state
        self.index = 0
        self.scroll_offset = 0
        self.visible_items = 4
        self.menu_stack = []

        # edit mode (settings)
        self.edit_mode = False
        self.edit_setting = None

        # external data
        self.profile_names = profile_names
        self.settings = settings

        self.title = "Main Menu"
        self.main_menu = [
            ("Resume", ("resume", None)),
            ("Profiles", ("submenu", "Profiles", self.build_profiles_menu())),
            ("Settings", ("submenu", "Settings", self.build_settings_menu()))
        ]

        self.current_menu = self.main_menu

    def build_profiles_menu(self):

        menu = []

        for i, name in enumerate(self.profile_names):
            menu.append((name, ("profile", i)))

        menu.append(("Back", self.back))

        return menu

    def build_settings_menu(self):

        menu = []
        for name in self.settings:
            menu.append((name, ("setting", name)))

        menu.append(("Back", self.back))

        return menu

    def resume(self):
        self.reset()
        return "resume"


    def back(self):
        if self.menu_stack:
            (
                self.current_menu,
                self.index,
                self.title,
                self.scroll_offset,
            ) = self.menu_stack.pop()

    def reset(self):
        self.current_menu = self.main_menu
        self.menu_stack = []
        self.index = 0
        self.scroll_offset = 0
        self.title = "Main Menu"
        self.edit_mode = False
        self.edit_setting = None


    def draw(self):
        self.display.fill(0)
        self.display.text(self.title, 0, 0, 1)

        if self.edit_mode:
            setting = self.settings[self.edit_setting]
            self.display.text(
                self.edit_setting,
                0,
                20,
                1
            )

            self.display.text(
                str(setting["value"]),
                0,
                35,
                1
            )

            self.display.show()
            return

        # scroll logic
        if self.index < self.scroll_offset:
            self.scroll_offset = self.index

        elif self.index >= self.scroll_offset + self.visible_items:
            self.scroll_offset = self.index - self.visible_items + 1

        visible = self.current_menu[
            self.scroll_offset:
            self.scroll_offset + self.visible_items
        ]

        y = 16

        for row, (name, action) in enumerate(visible):

            actual_index = self.scroll_offset + row

            text = name

            # setting value display
            if isinstance(action, tuple) and action[0] == "setting":
                text = f"{name}: {self.settings[name]['value']}"

            if actual_index == self.index:
                text = ">" + text

            self.display.text(text, 0, y, 1)
            y += 12

        self.display.show()

    def update(self, command):

        if self.edit_mode:
            s = self.settings[self.edit_setting]
            if command == "up":
                s["value"] = min(s["max"], s["value"] + s["step"])

            elif command == "down":
                s["value"] = max(s["min"], s["value"] - s["step"])
            elif command == "select":
                self.edit_mode = False
                self.edit_setting = None

            self.draw()
            return None

        length = len(self.current_menu)

        if command == "up":
            self.index = (self.index - 1) % length
        elif command == "down":
            self.index = (self.index + 1) % length
        elif command == "select":
            name, selected = self.current_menu[self.index]

            # Submenu
            if isinstance(selected, tuple) and selected[0] == "submenu":

                self.menu_stack.append(
                    (self.current_menu, self.index, self.title, self.scroll_offset)
                )

                self.title = selected[1]
                self.current_menu = selected[2]

                self.index = 0
                self.scroll_offset = 0

            # Profile select
            elif isinstance(selected, tuple) and selected[0] == "profile":

                profile_index = selected[1]
                self.reset()
                self.draw()
                return profile_index

            elif isinstance(selected, tuple) and selected[0] == "resume":
                profile_index = self.current_index
                self.reset()
                self.draw()
                return profile_index
            # SETTINGS EDIT
            elif isinstance(selected, tuple) and selected[0] == "setting":

                self.edit_mode = True
                self.edit_setting = selected[1]

            else:
                selected()

        self.draw()
        return None

class OLEDHandler:
    """
    Handles i2c for the OLED and the EC11 encoder
    """
    def __init__(self, i2c, profile_names, settings):

        displayio.release_displays()

        self.display = adafruit_ssd1306.SSD1306_I2C(
            128,
            64,
            i2c
        )

        self.encoder = rotaryio.IncrementalEncoder(
            board.GP7,
            board.GP6
        )

        self.menu = Menu(self.display, profile_names, settings)

    def update(self, button, current_index):
        """
        Shows menu and handles encoder inputs.
        """
        self.menu.current_index = current_index
        self.menu.draw()
        last_position = self.encoder.position
        while True:

            position = self.encoder.position
            if position != last_position:
                if position > last_position:
                    self.menu.update("down")
                else:
                    self.menu.update("up")
                last_position = position

            if not button.value:
                result = self.menu.update("select")
                while not button.value:
                    pass

                time.sleep(0.1)

                if result is not None:
                    return result

    def status(self, profile_name):
        """
        Displays current profile on the OLED
        """
        self.display.fill(0)
        self.display.text("Current Profile:", 0, 0, 1)
        self.display.text(profile_name, 0, 16, 1)
        self.display.show()
