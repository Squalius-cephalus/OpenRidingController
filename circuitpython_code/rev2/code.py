"""
OpenRidingController Revision 2

This module initializes all hardware input devices, manages controller
profiles, processes horse control logic, and updates output devices
during the main loop.

License: MIT License
Copyright (c) 2026 Squalius-cephalus

"""
import json
import board
import digitalio
import neopixel
import time
from inputs.buttons import ButtonHandler
from horse_logic import HorseLogicHandler
from inputs.reins import ReinsHandler
from inputs.stirrups import StirrupsHandler
from inputs.nunchuk import NunchukHandler
from outputs.output_manager import OutputManager
from utils.debug import log
from outputs.oled import OLEDHandler
import busio
i2c = busio.I2C(
            board.GP5,  # SCL
            board.GP4,  # SDA
            frequency=100000
        )
# Initialize the onboard NeoPixel LED.
led = neopixel.NeoPixel(board.GP16, 1, brightness=0.3, auto_write=True)

# Load controller profiles from the RP2040 Zero.
with open("/profiles.json", "r") as f:
    data = json.load(f)

setup_done = False

loaded_profiles = data["profiles"]

# Configure profile selection button.
profile_button = digitalio.DigitalInOut(board.GP15)
profile_button.direction = digitalio.Direction.INPUT
profile_button.pull = digitalio.Pull.UP

# Configure pause button.
pause_button = digitalio.DigitalInOut(board.GP14)
pause_button.direction = digitalio.Direction.INPUT
pause_button.pull = digitalio.Pull.UP

# Configure encoder button.
encoder_button = digitalio.DigitalInOut(board.GP8)
encoder_button.direction = digitalio.Direction.INPUT
encoder_button.pull = digitalio.Pull.UP

class Controller:
    """
    Central coordinator for all controller input and output systems.

    This class is responsible for:
    - Updating hardware input handlers.
    - Sends rein and stirrup states to the horse control logic.
    - Gets processed states from horse logic.
    - Sending processed states to the output manager.
    """
    def __init__(self):
        """Initialize all hardware inputs and input handlers."""
        self.output_manager = OutputManager()
        self.reins_handler = ReinsHandler()
        self.stirrups_handler = StirrupsHandler(i2c)
        self.nunchuk_handler = NunchukHandler(i2c)
        self.horse_logic_handler = HorseLogicHandler()
        self.button_handler = ButtonHandler()
        self.nunchuk_connected = self.nunchuk_handler.is_connected()

    def update_inputs(self, current_time):
        """
        Update all input devices.

        Args:
            current_time: Current monotonic timestamp used for timed updates.
        """
        self.reins_handler.update()
        self.stirrups_handler.update()
        self.button_handler.update()
        if self.nunchuk_connected:
            self.nunchuk_handler.update(current_time)

    def get_states_from_inputs(self):
        """
        Merge all input states into a single dictionary.

        Returns:
            Combined input states from stirrups and reins handlers.
        """
        stirrup_states = self.stirrups_handler.get_states()
        reins_states = self.reins_handler.get_states()
        return stirrup_states | reins_states

    def set_new_profile(self, new_profile):
        """
        Apply a newly selected profile across all handlers.

        Args:
            new_profile: Profile configuration dictionary.
        """
        self.output_manager.set_new_profile(new_profile)
        self.nunchuk_handler.set_new_profile(new_profile)
        self.reins_handler.set_new_profile(profile_manager.current_profile["settings"])
        self.stirrups_handler.set_new_profile(
            profile_manager.current_profile["settings"]
        )

        self.output_manager.release_all()

    def release_all(self):
        """
        Release all inputs like toggle, hold etc.
        """
        self.output_manager.release_all()

    def update(self, current_time):
        """
        Execute a controller update cycle.

        This method:
        - Updates inputs.
        - Processes horse control logic.
        - Combines all controller states.
        - Pushes proceccess states to the output manager.

        Args:
            current_time: Current monotonic timestamp.
        """
        self.update_inputs(current_time)


        # Horse logic will process reins and stirrup states.
        self.horse_logic_handler.update_analog(self.reins_handler.get_analog_states())
        self.horse_logic_handler.update(self.get_states_from_inputs())

        # Merge states from all handlers.
        states = (
            self.horse_logic_handler.get_states()
            | self.button_handler.get_states()
            | self.nunchuk_handler.get_states()
        )
        self.output_manager.update(
            states,
            self.horse_logic_handler.get_analog_states(),
            self.nunchuk_handler.get_analog_states(),
            current_time,
        )


class OnboardLED:
    """
    Initialize the onboard LED controller.

    Args:
        neopixel_led: NeoPixel LED, onboard LED.
    """

    def __init__(self, neopixel_led):
        self.led = neopixel_led
        self.current_color = [255, 255, 255]

    def change_color(self, color):
        """
        Set the LED to a new color.

        Args:
            color: RGB color list.
        """
        self.led[0] = color
        self.current_color = color

    def get_color(self):
        """
        Returns:
            Current RGB color as list.
        """
        return self.current_color


class ProfileManager:
    """
    Handles profile selection.

    Profiles control configuration settings such as LED color,
    input sensitivity, and button mappings.
    """
    def __init__(self, profiles, passed_led):
        """
        Initialize the profile manager.

        Args:
            profiles: JSON list of profiles.
            passed_led: Onboard LED object used for visual feedback.
        """
        self.profiles = profiles
        self.led = passed_led
        self.current_index = -1
        self.current_profile = self.profiles[self.current_index]

    def get_profile_names(self):
        names = []
        for i in self.profiles:
            names.append(i["name"])
        return names

    def change_profile(self, index):
        """
        Cycle to the next available profile.

        Updates the LED color.

        Returns:
            The newly selected profile.
        """
        self.current_profile = self.profiles[index]
        self.current_index = index
        log("Active profile:", self.current_profile["name"])
        self.led.change_color(self.current_profile["settings"]["led_color"])
        time.sleep(0.3)
        return self.current_profile


onboard_led = OnboardLED(led)
profile_manager = ProfileManager(loaded_profiles, onboard_led)
controller = Controller()

settings = {
    "Mouse Sens.": {"value": 1, "min": 0.1, "max": 1, "step": 0.1},
    "Joystick Sens.": {"value": 1, "min": 0.1, "max": 1, "step": 0.1},
    "Stirrup Sens.": {"value": 1, "min": 0.1, "max": 1, "step": 0.1},
}

oled = OLEDHandler(i2c, profile_manager.get_profile_names(), settings)

def open_menu():
    time.sleep(0.5)
    controller.release_all()
    current_index = profile_manager.current_index
    profile = profile_manager.change_profile(oled.update(encoder_button, current_index))
    controller.set_new_profile(profile)
    oled.status(profile_manager.current_profile["name"])
    # settings does nothing
    #print(oled.get_settings())

# Main loop.
while True:
    current_time = time.monotonic()
    if not profile_button.value or not setup_done:
        new_profile = profile_manager.change_profile(0)
        controller.set_new_profile(new_profile)
        oled.status(new_profile["name"])
        setup_done = True

    if not encoder_button.value:
        open_menu()

    controller.update(current_time)
