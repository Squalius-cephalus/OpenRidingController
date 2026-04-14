import pwmio
import time

class PiezoPlayer:
    def __init__(self, pin):
        self.piezo = pwmio.PWMOut(pin, duty_cycle=0, frequency=440, variable_frequency=True)

    def play_tone(self, frequency, duration):
        if frequency <= 0:
            self.piezo.duty_cycle = 0
            time.sleep(duration)
            return

        self.piezo.frequency = int(frequency)
        self.piezo.duty_cycle = 32768  # 50%
        time.sleep(duration)
        self.piezo.duty_cycle = 0

    def play_tune(self, notes):
        """
        notes = [(frequency, duration), ...]
        frequency = Hz (0 = pause)
        duration = seconds
        """
        for freq, dur in notes:
            self.play_tone(freq, dur)

    def beep(self):
        self.play_tone(1000, 0.1)

    def off(self):
        self.piezo.duty_cycle = 0

