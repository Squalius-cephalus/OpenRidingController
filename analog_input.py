import time

from adafruit_simplemath import map_range


DEBUG = True
# TODO: idk keksi parempi tapa tolle debugille lmao

class ReinsHandler:
    def __init__(self, left_rein_input, right_rein_input):
        self.left_offset = 0
        self.right_offset = 0
        self.left_rein_input = left_rein_input
        self.right_rein_input = right_rein_input
        self.now = time.monotonic()
        self.current_time = time.monotonic()
        self.left = 0
        self.right = 0
        self.map_range = [0, 512]
        self.rein_timer = self.now
        self.reins_pulled = False
        self.reins_pulled_far = False

        self.neutral_position = 0
        self.pulled_threshold = 400
        self.lighty_pulled_threshold = 155
        self.analog_value = 0
        self.timer_started = False
        self.elapsed_time = 0
        self.start_time = 0



        self.digital_states = {
            "BothPulled": False,
            "BothPulledFar": False
        }

    def _read_scaled(self, pin):

        return int(map_range(pin.value, 0, 65520, self.map_range[0], self.map_range[1]))

    def update(self, ):
        self.current_time = time.monotonic()

        left = int(map_range(self.left_rein_input.value-self.left_offset, 0, 65520, self.map_range[0], self.map_range[1]))
        right = int(map_range(self.right_rein_input.value - self.right_offset, 0, 65520, self.map_range[0], self.map_range[1]))
        self.digital_states = {
            "BothPulled": False,
            "BothPulledFar": False
        }

       



        if not self.reins_pulled or not self.reins_pulled_far:
            self.left = left
            self.right = right
            self.analog_value = 0

        if left >= self.pulled_threshold and right >= self.pulled_threshold and not self.reins_pulled_far:
            self.reins_pulled = True
            self.digital_states["BothPulledFar"] = True
            self.reins_pulled_far = True


        if left != 0 and right != 0 and not self.reins_pulled:
            if not self.timer_started:
                self.start_time = time.monotonic()
                self.timer_started = True

            self.elapsed_time = time.monotonic() - self.start_time
            # TODO: Add option for this!!
            if self.elapsed_time < 1:
                if left >= self.lighty_pulled_threshold and right >= self.lighty_pulled_threshold and not self.reins_pulled_far:
                    self.digital_states["BothPulled"] = True
                    if DEBUG: print("Reins pulled ", self.left, self.right, self.elapsed_time)

                    self.reins_pulled = True

        if left <= self.neutral_position and right <= self.neutral_position:
            self.reins_pulled = False
            self.reins_pulled_far = False
            self.rein_timer = self.current_time

        if self.reins_pulled is False and self.reins_pulled_far is False:
            self.analog_value = self.right - self.left


    def get_digital_states(self):
        return self.digital_states
    def get_analog_states(self):
        return [self.left, self.right]


    def get_new_profile(self, profile):
        return
    # TODO: THIS WHOLE THING


    def calibrate(self):
        left_samples = []
        right_samples = []

        for i in range(5):
            left_val = self.left_rein_input.value
            right_val = self.right_rein_input.value
            time.sleep(0.1)
            left_samples.append(left_val)
            right_samples.append(right_val)

        self.left_offset = int(sum(left_samples) / len(left_samples))
        self.right_offset = int(sum(right_samples) / len(right_samples))

        print("Calibration done, reins offsets:", self.left_offset, self.right_offset)

