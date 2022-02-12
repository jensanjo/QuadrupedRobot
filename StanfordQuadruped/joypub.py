import threading
import UDPComms
from dataclasses import dataclass, asdict
import time

MESSAGE_RATE = 20
PUBLISHER_PORT = 8830
SUBSCRIBER_PORT = 8840

@dataclass
class JoystickMessage:
    """Represents a joystick message"""
    lx: float = 0.0
    ly: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    R1: int = 0 
    R2: float = 0.0
    L1: int = 0
    L2: float = 0.0
    dpadx: float = 0.0
    dpady: float = 0.0
    x: int = 0
    square: int = 0 
    circle: int = 0
    triangle: int = 0
    message_rate: int = MESSAGE_RATE

class JoystickPublisher(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.publisher = UDPComms.Publisher(PUBLISHER_PORT, 0)
        self.message = JoystickMessage()
        self.lock = threading.RLock()

    def toggle_active(self):
        with self.lock:
            self.message.L1 = 1

    def toggle_trot(self):
        with self.lock:
            self.message.R1 = 1
    
    def run(self):
        while True:
            with self.lock:
                msg = asdict(self.message)
                self.publisher.send(msg)
                # reset toggles
                self.message.L1 = 0
                self.message.R1 = 0
            time.sleep(1 / MESSAGE_RATE)
  
if __name__ == '__main__':
    pub = JoystickPublisher()
    m = pub.message
    pub.start()
