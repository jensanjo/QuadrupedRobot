#!/usr/bin/env python3
import tkinter
from tkinter import HORIZONTAL, Tk, ttk
from tkinter.messagebox import askokcancel
from functools import partial
import numpy as np
from pupper.HardwareInterface import HardwareInterface
from pupper.Config import CALIBRATION_FILE, load_calibration_values, save_calibration_values


# default angles: Hip 0°, thigh 90°, calf -90°
SETPOINT_ANGLES = [0, 0, -90]  # originally [0, 45, -45]
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
        # Calibration image
        self.image = tkinter.PhotoImage(file=CALIBRATION_IMAGE)
        img = ttk.Label(content, image=self.image)
        img.grid(row=row, column=2, columnspan=4, rowspan=2)

        # Reset and Update buttons
        reset_button = tkinter.Button(
            content, text='Reset', command=self.on_reset_button_clicked, font=('bold', 20))
        reset_button.grid(row=1, column=7, padx=10, pady=10)
        save_button = tkinter.Button(
            content, text='Update', command=self.on_save_button_clicked, font=('bold', 20))
        save_button.grid(row=2, column=7, padx=10, pady=10)

        row += 2
        # Sliders
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
                self.scales[i, j] = scale
            row += 1
        row += 1
        for j, leg in enumerate(legs):
            label = ttk.Label(content, text=leg, font=('bold', 16))
            label.grid(row=row, column=2*j+1)

        # set initial slider values
        self.set_slider_values(np.zeros_like(self.values))

    def set_slider_values(self, values):
        rows, cols = values.shape
        # update sliders
        for i in range(rows):
            for j in range(cols):
                self.scales[i, j].set(values[i, j])

    def on_reset_button_clicked(self):
        print("Reset")
        self.set_slider_values(np.zeros_like(self.values))

    def on_save_button_clicked(self):
        title = "Save calibraton matrix"
        message = f"{self.values}\n"
        if askokcancel(title=title, message=message):
            self.on_save_callback()


class CalibrationTool:
    def __init__(self):
        self.servos = HardwareInterface()
        self.initial_values = load_calibration_values(CALIBRATION_FILE)
        self.corrections = np.zeros_like(self.initial_values)
        self.values = self.initial_values.copy()
        self.set_servo_positions(self.corrections)
        self.gui = CalibrationGui(self.values,
                                  self.value_changed, self.save_calibration_values)

    def value_changed(self, i, j, value):
        value = int(value)  # TODO
        self.corrections[i, j] = value
        self.values[i, j] = self.initial_values[i, j] + value
        self.set_servo_position(i, j, value)

    def set_servo_position(self, joint, leg, value):
        setpoints = SETPOINT_ANGLES
        setpoint = setpoints[joint] - value
        angle = np.deg2rad(setpoint)
        # set_actuator_position(joint_angle: radians, axis: 0..3 leg: 0..2)
        self.servos.set_actuator_position(angle, joint, leg)

    def set_servo_positions(self, values):
        rows, cols = values.shape
        # update servos
        for i in range(rows):
            for j in range(cols):
                self.set_servo_position(i, j, values[i, j])

    def save_calibration_values(self):
        save_calibration_values(CALIBRATION_FILE, self.values)


if __name__ == '__main__':
    import subprocess
    # check if robot service is running
    result = subprocess.run("systemctl is-active --quiet robot", shell=True)
    robot_is_running = result.returncode == 0
    if robot_is_running:
        print("Stop robot service")
        subprocess.run("sudo systemctl stop robot", shell=True)
    try:
        tool = CalibrationTool()
        tool.gui.mainloop()
    finally:
        if robot_is_running:
            print("Restart robot service")
            subprocess.run("sudo systemctl start robot", shell=True)
