# -*- coding: utf-8 -*-
"""
Controls the power supply tester board.

The main component of the tester is the power transistor that will control
the current/power drawn from the power supply to be tested. This current
is controlled by the voltage at the gate of the transistor. And that voltage 
is set by the arduino pwm output

                                             ▲ Power supply to Test
                                             │    Max voltage 40V
                                     ┌───────┤
   Vset   ┌────────────────┐         │       │
    ▲     │            Vcc ├─────────┘   │ ┌─┘
    │     │  x10 Gain Amp  │             │ │    Power Transistor Gate
    └─────┤Input     Output├─────────────┤ │      
          │                │  0 to 40 V  │ └─┐
          └────────────────┘  Vgate      │   │   ▲  Vload
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
        │        │            │         │
PWM     ├>──────>┤   Low-Pass ├>────────┘
Voltage │        │    Filter  │
        │        │            │
        │        └────────────┘
        │
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
        amp_gain=10,
        resistance=10,
        vthresh=0.5,
    ):
        self.board = pymata4.Pymata4()

        self.pin_vset = pin_vset
        self.pin_vload = pin_vload
        self.amp_gain = amp_gain
        self.resistance = resistance
        self.vthresh = vthresh

        self.board.enable_analog_reporting(pin_vload)
        self.board.set_pin_mode_pwm_output(pin_vset)
        self.pin_voltage_value = 0  # this value is from 0 to 0x4000
        self.value_to_voltage = (5.2 / 1024) / 10.0

    def read_vload(self):
        """
        It reads the voltage on the load
        """
        time.sleep(0.1)
        value = self.board.analog_read(self.pin_vload)
        value = self.board.analog_read(self.pin_vload)
        value = self.value_to_voltage * value[0]  # throw timestap away
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


    def print(self):
        """
        print board
        """
        print("test")


if __name__ == "__main__":
    fire.Fire(Board)
