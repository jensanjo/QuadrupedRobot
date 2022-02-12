import numpy as np
import time
from pupper.HardwareInterface import HardwareInterface


class ServoTester():
    def __init__(self):
        self.servos = HardwareInterface()

    def set_legs(self, legs, angles):
        for leg in legs:
            for axis in range(3):
                angle = np.deg2rad(angles[axis])
                self.servos.set_actuator_position(angle, axis, leg)

if __name__ == '__main__':
    st = ServoTester()
    legs = [0]
    while True:
        for angle in [75, 45,30,15,0, 15, 30,45, 60,75]:
            st.set_legs(legs, [0, 45, -angle])
            # st.servos.set_actuator_position(-angle, 2, 0)
            time.sleep(1)