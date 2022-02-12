import threading
import logging
import UDPComms
from evdev import InputDevice, list_devices, ecodes
import time
import math

LOGGER = logging.getLogger('joystick')

THRESHOLD = 0.14
MESSAGE_RATE = 20
PUBLISHER_PORT = 8830
SUBSCRIBER_PORT = 8840

MAP = {
    # AXES
    0: "left_analog_x",
    1: "left_analog_y",
    3: "right_analog_x",
    4: "right_analog_y",
    2: "l2_analog",
    5: "r2_analog",
    16: "dpad_x",
    17: "dpad_y",
    # BUTTONS
    304: "button_cross",    # BTN_A
    305: "button_circle",   # BTN_B
    307: "button_square",   # BTN_X
    308: "button_triangle",  # BTN_Y
    310: "button_l1",       # BTN_LR
    311: "button_r1"        # BTN_TR
}
joystick_publisher = UDPComms.Publisher(PUBLISHER_PORT, 0)
joystick_subscriber = UDPComms.Subscriber(SUBSCRIBER_PORT, 0)

class JoyStick(threading.Thread):

    def __init__(self):
        super().__init__(daemon=True)
        self.values = None
        self.lock = threading.RLock()

    def get_input(self):
        with self.lock:
            return self.values

    def read_loop(self, dev):
        for event in dev.read_loop():
            if event.type in (ecodes.EV_ABS, ecodes.EV_KEY):
                key = MAP.get(event.code)
                if not key:
                    continue
                values = self.values
                if key in ("left_analog_x", "right_analog_x"):
                    value = event.value / 32768.
                elif key in ("left_analog_y", "right_analog_y"):
                    value = -event.value / 32768.
                elif key in ("l2_analog", "r2_analog"):
                    value = event.value / 256.
                else:
                    value = event.value
                with self.lock:
                    v = self.values
                    v[key] = value
                    if math.hypot(v['left_analog_x'], v['left_analog_y']) < THRESHOLD:
                        v['left_analog_x'] = 0.0
                        v['left_analog_y'] = 0.0
                    if math.hypot(v['right_analog_x'], v['right_analog_y']) < THRESHOLD:
                        v['right_analog_x'] = 0.0
                        v['right_analog_y'] = 0.0
                    # strvalues = [f"{v[k]:.2}" for k in v]
                    LOGGER.debug(' '.join([f"{v[k]}" for k in v]))

    def run(self):
        while True:
            found = False
            for dev_path in list_devices():
                dev = InputDevice(dev_path)
                if dev.name == 'Logitech Gamepad F710':
                    found = True
                    break
            if found:
                self.values = {MAP[k]: 0 for k in MAP}
                LOGGER.info(f"Joystick {dev.name} connected")
                try:
                    self.read_loop(dev)
                except OSError as ex:
                    LOGGER.error(f"Joystick disconnected: {ex}")
                    self.values = None
                else:
                    time.sleep(1)
            else:
                time.sleep(1)


logging.basicConfig(level=logging.INFO)
joystick = JoyStick()
joystick.start()

LOGGER.info(f"Publishing on UDP port {PUBLISHER_PORT}")
while True:
    values = joystick.get_input()
    if values is not None:
        msg = dict(
            lx=values['left_analog_x'],
            ly=values['left_analog_y'],
            rx=values['right_analog_x'],
            ry=values['right_analog_y'],
            R1=values['button_r1'],
            R2=values['r2_analog'],
            L1=values['button_l1'],
            L2=values['l2_analog'],
            dpadx=values['dpad_x'],
            dpady=values['dpad_y'],
            x=values['button_cross'],
            square=values['button_square'],
            circle=values['button_circle'],
            triangle=values['button_triangle'],
            message_rate=MESSAGE_RATE,
        )
        joystick_publisher.send(msg)
        try:
            msg = joystick_subscriber.get()
            print(f"got {msg}")
        except UDPComms.timeout:
            pass
    time.sleep(1 / MESSAGE_RATE)
