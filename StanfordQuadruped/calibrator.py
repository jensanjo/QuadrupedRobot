#!/usr/bin/env python3
import tkinter
from tkinter import HORIZONTAL, Tk, ttk
from tkinter.messagebox import askokcancel
from functools import partial
import numpy as np
from pupper.HardwareInterface import HardwareInterface

# Location of the calibration file
# It contains 3 rows of 4 values, separated by spaces
# Row 1: Hip
# Row 2: Thight
# Row 3: Calf
# The format is compatible with numpy.loadtxt.
CALIBRATION_FILE = "nvtest.dat"

# default angles: Hip 0°, thigh 45°, calf -45°
DEFAULT_CALIBRATION_VALUES = np.array([[0]*4, [45]*4, [-45]*4])

CALIBRATION_IMAGE = '../Doc/imgs/MiniPupper.Calibration.png'
WINDOW_TITLE = "MiniPupper"
HEADER = "MiniPupper Calibration Tool V2"

class CalibrationGui(Tk):

    def __init__(self, values: np.array, on_value_changed_callback, on_save_callback):
        super().__init__()
        self.values = values
        self.on_save_callback = on_save_callback

        # create the GUI
        self.title("MiniPupper")
        content = ttk.Frame(self)
        content.grid(row=0, column=0, pady=10)

        row = 0
        title = ttk.Label(content, text=HEADER, font=('bold', 30))
        title.grid(row=row, column=0, columnspan=8, pady=10)

        row += 1
        ## Calibration image
        self.image = tkinter.PhotoImage(file=CALIBRATION_IMAGE)
        img = ttk.Label(content, image=self.image)
        img.grid(row=row, column=2, columnspan=4, rowspan=2)

        ## Reset and Update buttons
        reset_button = tkinter.Button(content, text='Reset', command=self.on_reset_button_clicked, font=('bold', 20))
        reset_button.grid(row=1, column=7, padx=10, pady=10)
        save_button = tkinter.Button(content, text='Update', command=self.on_save_button_clicked, font=('bold',20))
        save_button.grid(row=2, column=7, padx=10, pady=10)

        row += 2
        ## Sliders
        joints = [('Hip', (-100, 100)), ('Thigh', (-100, 100)),
                  ('Calf', (-100, 100))]
        legs = [f'Leg {i+1}' for i in range(4)]
        self.scales = {}
        for i, (name, (min, max)) in enumerate(joints):
            for j, leg in enumerate(legs):
                label = ttk.Label(content, text=name)
                cb = partial(on_value_changed_callback, i, j)
                scale = tkinter.Scale(content, from_=min, to=max,
                                      length=120, orient=tkinter.HORIZONTAL, command=cb)
                label.grid(row=row, column=2*j, padx=10, pady=2)
                scale.grid(row=row, column=2*j+1, padx=10, pady=2)
                self.scales[i,j] = scale
            row += 1
        row += 1
        for j, leg in enumerate(legs):
            label = ttk.Label(content, text=leg, font=('bold', 16))
            label.grid(row=row, column=2*j+1)

        ## set initial slider values
        self.set_slider_values(np.zeros_like(self.values))
    
    def set_slider_values(self, values):
        rows, cols = values.shape
        # update sliders
        for i in range(rows):
            for j in range(cols):
                self.scales[i,j].set(values[i,j])

    def on_reset_button_clicked(self):
        print("Reset")
        self.set_slider_values(np.zeros_like(self.values))

    def on_save_button_clicked(self):
        title="Save calibraton matrix"
        message = f"{self.values}\n"
        if askokcancel(title=title, message=message):
            self.on_save_callback()


class CalibrationTool:
    def __init__(self):
        self.servos = HardwareInterface()
        self.initial_values = self.load_calibration_values()
        self.corrections = np.zeros_like(self.initial_values)
        self.values = self.initial_values.copy()
        self.set_servo_positions(self.corrections)
        self.gui = CalibrationGui(self.values, 
            self.value_changed, self.save_calibration_values)

    def value_changed(self, i, j, value):
        # print(i,j,value)
        value = int(value) # TODO
        self.corrections[i,j] = value
        self.values[i,j] = self.initial_values[i,j] + value
        self.set_servo_position(i, j, value)

    def set_servo_position(self, joint, leg, value):
        # setpoints = [0, 45, -45]
        setpoints = [0, 0, -90]
        setpoint = setpoints[joint] - value
        print(f"{joint},{leg} -> {setpoint}")
        angle = np.deg2rad(setpoint)
        self.servos.set_actuator_position(angle, joint, leg)

    def set_servo_positions(self, values):
        rows, cols = values.shape
        # update servos
        for i in range(rows):
            for j in range(cols):
                self.set_servo_position(i, j, values[i,j])   

    def load_calibration_values(self):
        try:
            values = np.loadtxt(CALIBRATION_FILE, dtype=int)
            print(f"Get calibration values:\n{values}")
        except Exception as ex:
            values = DEFAULT_CALIBRATION_VALUES
            print(f"Getcalibration values failed: {ex}")
        return values

    def save_calibration_values(self):
        values = self.values
        try:
            np.savetxt(CALIBRATION_FILE, values, fmt='%d')
        except Exception as ex:
            print(ex)

'''
Servo control
set_actuator_position(joint_angle: radians, axis: 0..3 leg: 0..2)

angle_to_pwm

Assume that the leg servos are mounted perfectly. Then the default calibration 
should result in the right servo position.
If the angle command is equal to the default calibration the angle_deviation = 0.

pulse_width_micros = 1500  + micros_per_rad * angle_deviation = 1500.

angle_to_duty_cycle = pulse_width_micros * 1000 = 1500_000

For the thigh to be at 45° the pwm should theoretically be 200_000




'''
if __name__ == '__main__':
    tool = CalibrationTool()
    tool.gui.mainloop()
