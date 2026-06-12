"""
Stirrup input handling for stirrup sensors.

This module initializes GPIO stirrup inputs, tracks how fast stirrups are moved,
and exposes helper classes for updating and retrieving stirrups current state.
"""

import time
from utils.utils import interpolate
import struct


class MPU6050:
    def __init__(self, i2c, addr):
        self.i2c = i2c
        self.addr = addr
        self.buf = bytearray(14)

        while not self.i2c.try_lock():
            pass

        try:
            self.i2c.writeto(addr, bytes([0x6B, 0x00]))
        finally:
            self.i2c.unlock()

    def read(self):
        if not self.i2c.try_lock():
            return None

        try:
            self.i2c.writeto_then_readfrom(
                self.addr,
                bytes([0x3B]),
                self.buf
            )
            return struct.unpack(">hhhhhhh", self.buf)

        finally:
            self.i2c.unlock()

class StirrupState:
    """
    Setup stirrup states and when it was activated last time.
    """
    last_time_foward: float = 0.0
    last_time_backward: float = 0.0
    timer: float = 0.0
    activated: bool = False
    peak: int = 0
    ready: bool = False
    last_direction: str = ""
    last_dir_change_time: float = 0.0
    values: dict = []

    forward_fast: bool = False
    forward_slow: bool = False
    backward_fast: bool = False
    backward_slow: bool = False
    forward_hold: bool = False
    backward_hold: bool = False

    def clear(self):
        """
        Reset stirrups states.
        """

        self.forward_fast = False
        self.forward_slow = False
        self.backward_fast = False
        self.backward_slow = False
        self.forward_hold = False
        self.backward_hold = False

    def get_dict(self, prefix):
        """
        Return stirrups states.
        """
        return {
            f"stirrup_{prefix}_forward_fast": self.forward_fast,
            f"stirrup_{prefix}_forward_slow": self.forward_slow,
            f"stirrup_{prefix}_backward_fast": self.backward_fast,
            f"stirrup_{prefix}_backward_slow": self.backward_slow,
            f"stirrup_{prefix}_forward_hold": self.forward_hold,
            f"stirrup_{prefix}_backward_hold": self.backward_hold,
        }


class StirrupsHandler:
    """
    Process stirrups inputs and exposes their current states.
    """
    def __init__(self,i2c):

        self.mpu1 = MPU6050(i2c, 0x68)
        self.mpu2 = MPU6050(i2c, 0x69)



        self.threshold_fast = 0.11
        self.threshold_slow = 0.3
        self.forward_threshold = 120
        self.backward_threshold = -100
        self.dead_zone = 20


        self.left_stirrup = StirrupState()
        self.right_stirrup = StirrupState()
        self.last_read = 0
        self.left = 0




    def set_new_profile(self, settings):
        """
        Updates stirrups thresholds and dead zone.
        """
        self.threshold_fast = settings["stirrup_speed_threshold_fast"]
        self.threshold_slow = settings["stirrup_speed_threshold_slow"]
        self.forward_threshold = settings["stirrup_forward_threshold"]
        self.backward_threshold = settings["stirrup_backward_threshold"]
        self.dead_zone = settings["stirrup_dead_zone"]
    def update(self):
        """
        Updates stirrups analog values and uses those to update the states.
        """

        current_time = time.monotonic()
        self.left_stirrup.clear()
        self.right_stirrup.clear()
        #self.update_imu()
        UPDATE_PERIOD = 1.0 / 60.0  # 16.67 ms
        try:
            if current_time - self.last_read >= UPDATE_PERIOD:
                self.last_read = current_time
                
                ax, ay, az, temp, gx1, gy, gz = self.mpu1.read()
                ax, ay, az, temp, gx2, gy, gz = self.mpu2.read()
                #print(ax, ay, az, gx, gy, gz)
                #print(az)
                self.right = gx2
                self.left = gx1

            self.handle_stirrups(self.right, current_time, self.left_stirrup)
            self.handle_stirrups(self.left, current_time, self.right_stirrup)
        except:
            # TODO: Better error handling
            print("STIRRUP NOT CONNECTED")


    def handle_stirrups(self, value, current_time, state):
        """
        Processes stirrup input to states
        """
        
        if value < -15000:
            state.values.append(value)
            if current_time - state.last_time_backward >= 0.3 and current_time - state.last_time_foward >= 1:
                if min(state.values)<-20000:
                    print("FAST, BACKWARD")
                    state.backward_fast = True
                else:
                    print("SLOW, BACKWARD")
                    state.backward_slow = True
                print(min(state.values))
                state.values = []
                

                state.last_time_backward = current_time
        if value > 15000:
            state.values.append(value)
            if current_time - state.last_time_foward >= 0.3 and current_time - state.last_time_backward >= 1:
                if max(state.values)>20000:
                    print("FAST, FORWARD")
                    state.forward_fast = True
                else:
                    print("SLOW, FORWARD")
                    state.forward_slow = True
                print(max(state.values))
                state.values = []

                state.last_time_foward = current_time



        


    def get_states(self):
        """
        Return stirrups states for horse logic.
        """
        states = self.left_stirrup.get_dict("left") | self.right_stirrup.get_dict("right")
        return states
