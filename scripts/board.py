# -*- coding: utf-8 -*-
"""
Controls the power supply tester board.

The main component of the tester is the power transistor that will control
the current/power drawn from the power supply to be tested. Its current
is controlled by the voltage difference between the gate and the load.
And that voltage is indirectly controlled by the arduino pwm output.

                                             ▲         Vin
                                             │  Power supply to Test
                                             │    Max voltage 40V
                                     ┌───────┤
   Vset   ┌────────────────┐         │       │
    ▲     │            Vcc ├─────────┘   │ ┌─┘
    │     │  x10 Gain Amp  │             │ │    Power Transistor Gate
    └─────┤Input     Output├─────────────┤ │
          │                │  0 to Vin   │ │
          └────────────────┘  Vgate      │ └─┐   ▲  Vload
                                             │   │
                                             │───┘
                                            ┌┴┐
                                            │ │ Power Resistor
                                            │ │ Resistance ~10 ohm
                                            └┬┘ Power up to 2 Watts
                                             │
                                             ▼

Arduino                               Vset
────────┐        ┌────────────┐         ▲
PWM     ├>──────>┤  Low-Pass  ├>────────┘
Voltage │        │   Filter   │
        │        └────────────┘
        │
        │        ┌────────────┐   ▲  Vin
Vin     │        │   x0.1     │   │
sense   │<──────<┤  Voltage   ├<──┘
        │        │  Divider   │
        │        └────────────┘
        │
        │        ┌────────────┐   ▲  Vload
Vload   │        │   x0.1     │   │
sense   │<──────<┤  Voltage   ├<──┘
        │        │  Divider   │
────────┘        └────────────┘

EXAMPLE: 
        python board.py --port=COM3 


REQUIREMENTS:
    python 3.7+
    pyfirmata  (to talk to the arduino)
    fire (to create command line tool)

@author: Eduardo Munoz
@email: edmugu@protonmail.com
"""
# from pymata4 import pymata4
from pyfirmata import Arduino, util
from statistics import median

# from my_pid import PID
from simple_pid import PID
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import fire
import time


class Board(object):
    """
    It controls the power-supply-tester board.
    """

    def __init__(
        self,
        port="COM4",
        pin_vset=5,
        pin_vload=1,
        pin_vin=0,
        amp_gain=10,
        sense_voltage_divider=1,
        resistance=10,
        gate_thresh=0.48,  # the gate threshold of the MOSFET
        vcc=5,
    ):
        # self.board = pymata4.Pymata4()
        self.board = Arduino(port)
        self.board.digital[13].write(1)

        self.pin_vset = pin_vset
        self.pin_vload = pin_vload
        self.pin_vin = pin_vin
        self.vcc = vcc
        self.gate_thresh = 0.48
        self.amp_gain = amp_gain
        self.resistance = resistance
        self.sense_voltage_divider = sense_voltage_divider

        self.pin_voltage_value = 0  # this value is from 0 to 0x4000
        self.value_to_voltage = 5.2 * self.sense_voltage_divider
        self.voltages = {}
        self.voltages_history = {"time": [], "vload": [], "vin": []}
        self.time_created = time.time()

        self.it = util.Iterator(self.board)
        self.it.start()
        self.analog_pins = {"vload": self.pin_vload, "vin": self.pin_vin}
        self.board.analog[pin_vin].enable_reporting()
        self.board.analog[pin_vload].enable_reporting()
        self.vout = self.board.get_pin("d:5:p")

        self.pid = PID(0.0, 0.0, 0.0, 0)

    def read_voltages(self, times_to_read=5, wait_time_between_reads=0.001):
        """
        It reads the voltages on the board multiple times because sometimes firmata returns 0 or none
        """
        if times_to_read <= 0 or wait_time_between_reads <= 0:
            raise ValueError("Bad arguments")

        measurements = {"time": [], "vload": [], "vin": []}
        for _ in range(times_to_read):
            for pin_name, pin in self.analog_pins.items():
                value = self.board.analog[pin].read()
                if value is None:
                    value = 0
                value = value * self.value_to_voltage
                measurements[pin_name].append(value)
                self.voltages_history[pin_name].append(value)

            tmeas = self.time()
            measurements["time"].append(tmeas)
            self.voltages_history["time"].append(tmeas)
            time.sleep(wait_time_between_reads)

        med = {}
        for pin_name, pin in self.analog_pins.items():
            med[pin_name] = median(measurements[pin_name])

        self.voltages = med

        return med

    def time(self):
        """
        returns the time in respect with the time this was created
        """
        return time.time() - self.time_created

    def set_vload(self, voltage, max_tries=10, time_per_try=0.001, verbose=False):
        """
        It sets the voltage on the power resistor. It does that with the help of a PID

        :param voltage: voltage to set
        :param max_tries: how many times the PID can adjust the voltage before exiting
        :param time_per_try: how much to wait before re adjusting the voltage
        :param verbose: print as much info as possible
        """
        if verbose:
            print("Setting voltage to %5.3f volts." % voltage)

        # ziegler-Nichols tunning
        ku = 0.2
        tu = 0.33
        kp = 0.6 * ku
        ki = 1.2 * ku / tu
        kd = 3 * ku * tu / 40

        # self.pid = PID(kp, ki, kd, voltage)
        self.pid = PID(0.05, 0.3, 0.00, voltage)
        self.pid.output_limits = (0, 1 - self.gate_thresh)

        tries_count = 0
        time_history = []
        while tries_count < max_tries:
            tries_count += 1
            self.read_voltages()
            vload = self.voltages["vload"]
            time_history.append(self.time())
            output = self.pid(vload)
            output += self.gate_thresh
            self.vout.write(output)

            if verbose:
                print("\n")
                print("time: %5.3f" % self.time())
                print("pid output: %5.3f" % output)
                print(str(self.voltages))
        if verbose:
            self.save_data()

    def save_data(self, name=None):
        """
        It saves the voltages recorded through the whole process
        """
        if name is None:
            tmp = (str(int(time.time())), str(self.pid.tunings), str(self.pid.setpoint))
            name = "../data/%s_PID_%s_setpoint_%s.csv" % tmp
        df = pd.DataFrame(self.voltages_history)
        print(df)
        df.to_csv(name)

    def set_current(self, current, verbose=True):
        """
        It sets a current to test a power supply

        :param current:     current in amps
        :param test_time:   test_time in seconds
        """
        voltage_to_set = current * self.resistance
        print("setting the following voltage: " + str(voltage_to_set))
        self.set_vload(voltage_to_set)
        vload = self.voltages["vload"]
        tmp = (vload, vload / self.resistance)
        print("voltage set: %5.3f  current set: %5.3f" % tmp)

    def search_current_limit(self, iend, istart=0.001, isteps=100):
        """
        It tries different currents
        """
        print("doing a current limit search")
        points = np.linspace(istart, iend, num=isteps)

        data = []
        for i, s in enumerate(points):
            print("i: %d:  step: %5.3f" % (i, s))
            self.set_current(s, verbose=False)
            datav = {}
            datav["i"] = i
            datav["vin"] = self.voltages["vin"]
            datav["vload"] = self.voltages["vload"]
            datav["current"] = self.voltages["vload"] / self.resistance
            data.append(datav)

        df = pd.DataFrame(data)
        print(df)
        df.to_csv("../data/test3.csv")

    def test_resistance(self, resistance, test_time=9, verbose=True):
        """
        It sets a resistance to test a power supply

        :param current: current in amps
        :param test_time:   test_time in seconds
        """
        s = "The resistance is too low! It should be higher than Rload!"
        if resistance <= self.resistance:
            raise ValueError(s)

        tstart = time.time()
        while (time.time() - tstart) < test_time:
            current_to_set = self.voltages["vin"] / resistance
            voltage_to_set = current_to_set * self.resistance
            self.set_vload(voltage_to_set)
        self.save_data()

    def print(self):
        """
        print board
        """
        print("test")


if __name__ == "__main__":
    fire.Fire(Board)
