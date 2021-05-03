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
from pymata4 import pymata4
from statistics import median
import fire
import time


class Board(object):
    """
    It controls the power-supply-tester board.
    """

    def __init__(
        self,
        port="COM4",
        pin_vset=3,
        pin_vload=0,
        pin_vin=1,
        amp_gain=10,
        resistance=10,
        vthresh=0.5,
    ):
        self.board = pymata4.Pymata4()

        self.pin_vset = pin_vset
        self.pin_vload = pin_vload
        self.pin_vin = pin_vin
        self.amp_gain = amp_gain
        self.resistance = resistance
        self.vthresh = vthresh

        self.board.enable_analog_reporting(pin_vload)
        self.board.set_pin_mode_pwm_output(pin_vset)
        self.pin_voltage_value = 0  # this value is from 0 to 0x4000
        self.value_to_voltage = (5.2 / 1024) / 10.0

    def read_pin_voltage(self, pin, times_to_read=3, wait_time_between_reads=0.01):
        """
        It reads the voltage on a pin multiple times because sometimes firmata returns 0 or none
        """
        if times_to_read <=0 or wait_time_between_reads <= 0:
            raise ValueError("Bad arguments")

        measurements = []
        for _ in times_to_read:
            time.sleep(wait_time_between_reads)
            value = self.board.analog_read(pin)
            if value is None:
                value = 0
            measurements.append(value)
        
        return median(measurements)


    def read_vload(self):
        """
        It reads the voltage on the load
        """
        value = self.read_pin_voltage(self.pin_vload)
        value = self.value_to_voltage * value[0]  # throw timestamp away
        return value

    def read_vin(self):
        """
        It reads the voltage on the Power Supply Tested
        """
        value = self.read_pin_voltage(self.pin_vin)
        value = self.value_to_voltage * value[0]  # throw timestamp away
        return value

    def set_vload(self, voltage, verbose=True):
        """
        It sets the voltage on the power resistor. It does that by raising the
        voltage on the gate of the transistor until it reaches the target
        voltage.

        :param voltage: voltage to set
        """
        if verbose:
            print("Setting voltage to %5.3f volts." % voltage)

        for n in range(0x4000):
            self.board.pwm_write(self.pin_vset, n)
            self.pin_voltage_value = n
            value = self.read_vload()
            if verbose:
                print("Voltage read: %5.3f" % value)
            if value > voltage:
                break
            if verbose:
                for _ in range(3):
                    print("Voltage read: %5.3f" % value)

    def test_current(self, current):
        """
        It sets a current to test a power supply

        :param current: current in amps
        """
        voltage_to_set = current * self.resistance
        self.set_vload(voltage_to_set)

    def test_resistance(self, resistance):
        """
        It sets a resistance to test a power supply

        :param current: current in amps
        """
        if resistance <= self.resistance:
            raise ValueError("The resistance is too low! It should be higher than Rload!")

        vin = self.read_vin()
        current_to_set = vin / resistance
        voltage_to_set = current_to_set * self.resistance
        self.set_vload(voltage_to_set)

    def print(self):
        """
        print board
        """
        print("test")


if __name__ == "__main__":
    fire.Fire(Board)
