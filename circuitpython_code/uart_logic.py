import time
import busio
import board


class UARTLogic:
    def __init__(self, pin, baudrate=115200, header=[0xAA, 0x55], update_freq=2):
        

        self.button_states = []
        self.analog_states = []

        self.reset_all()

        self.last_packet = 0
        self.last_send = 0
        if baudrate == 9600:
            print("Slow baudrate detected, update frequenzy slow down to 10Hz")
            self.update_freq = self.set_hz(10)
        else:
            self.update_freq = self.set_hz(update_freq)

        self.header = header

        self.uart = busio.UART(pin, baudrate=baudrate)
        

    def update(self):
        current_time = time.monotonic()

        if current_time-self.last_send>=self.update_freq:
            packet = self.build_packet()
            if packet != self.last_packet:
                out = []
                for b in packet:
                    out.append(f"{b:08b}")

                self.uart.write(packet)
                self.last_send = current_time
                self.last_packet = packet


    def set_hz(self,hz):
        return 1 / hz


    def press_buttons(self, *buttons):
        for button in buttons:
            self._validate_button_number(button)
            self.button_states[button] = True

    def release_buttons(self, *buttons):
        for button in buttons:
            self._validate_button_number(button)
            self.button_states[button] = False

    def release_all_buttons(self):
        for i in range(0,16):
            self.release_buttons(i)

    def click_buttons(self, *buttons):
        self.press_buttons(*buttons)
        self.release_buttons(*buttons)

    def move_joysticks(self, x=None, y=None, z=None, r_z=None, r_x=None, r_y=None):

        if x is not None:
            self._validate_joystick_value(x)
            self.analog_states[0] = x
        if y is not None:
            self._validate_joystick_value(y)
            self.analog_states[1] = y
        if z is not None:
            self._validate_joystick_value(z)
            self.analog_states[2] = z
        if r_z is not None:
            self._validate_joystick_value(r_z)
            self.analog_states[3] = r_z
        if r_x is not None:
            self._validate_joystick_value(r_x)
            self.analog_states[4] = r_x
        if r_y is not None:
            self._validate_joystick_value(r_y)
            self.analog_states[5] = r_y

    def reset_all(self):
        self.button_states = []
        for i in range(0,20):
            self.button_states.append(False)
        self.analog_states = [127,127,127,127,127,127]



    def pack_buttons(self):
        out = bytearray(3)

        for i, b in enumerate(self.button_states):
            if b:
                byte_index = i // 8
                bit_index = 7 - (i % 8)
                out[byte_index] |= (1 << bit_index)

        return out

    def pack_analog_values(self):
        packed = bytearray(6)

        for i, v in enumerate(self.analog_states):
            if not 0 <= v <= 255:
                raise ValueError("Value out of uint8 range")

            packed[i] = v  # direct assignment

        return packed
    

    def build_packet(self):
        packet = bytearray()

        packet.append(self.header[0])
        packet.append(self.header[1])

        packet.extend(self.pack_buttons())   # 2 bytes, 16 button values
        packet.extend(self.pack_analog_values())  # 6 bytes, 6 analog axis

        checksum = self.calc_xor_checksum(packet) # Simple XOR checksum
        packet.append(checksum)

        return packet
    

    def calc_xor_checksum(self, data):
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum

    @staticmethod
    def _validate_button_number(button):
        if not 0 <= button <= 19:
            raise ValueError("Button number must in range 0 to 19")
        return button

    @staticmethod
    def _validate_joystick_value(value):
        if not 0 <= value <= 255:
            raise ValueError("Joystick value must be in range 0 to 255")
        return value