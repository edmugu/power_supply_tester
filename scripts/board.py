# -*- coding: utf-8 -*-
"""
Controls the power supply tester board.

The main component of the tester is the power transistor that will control
the current/power drawn from the power supply to be tested. This current
is controlled by the voltage at the gate of the transistor. And that voltage 
is set by two voltage set by the arduino "coarse voltage" and "fine voltage."


           
                                             ▲  Power supply to Test
                                             │    Max voltage 40V
                                     ┌───────┤
   Vset   ┌────────────────┐         │       │
    ▲     │            Vcc ├─────────┘   │ ┌─┘
    │     │  x10 Gain Amp  │             │ │    Power Transistor Gate
    └─────┤Input     Output├─────────────┤ │      
          │  __            │  0 to 40 V  │ └─┐
          └────────────────┘  Vgate      │   │
                                             │
                                             │
                                            ┌┴┐
                                            │ │ Power Resistor
                                            │ │ Resistance ~10 ohm
                                            └┬┘ Power up to 2 Watts
                                             │
                                             ▼



Arduino
────────┐        ┌────────────┐      ┌────────────┐        Vset
        │        │            │      │   Op Amp   │          ▲
Coarse  ├────────┤   Low-Pass ├──────┤   Voltage  │          │
Voltage │        │    Filter  │      │    Adder   ├──────────┘
        │        │            │   ┌──┤            │      
        │        └────────────┘   │  └────────────┘      
        │                         │                      
        │                         └───────────────────┐  
        │                                             │  
        │        ┌────────────┐      ┌────────────┐   │  
        │        │            │      │   x0.1     │   │  
Fine    ├────────┤   Low-Pass ├──────┤  Voltage   ├───┘  
Voltage │        │    Filter  │      │  Divider   │      
        │        │            │      │            │      
────────┘        └────────────┘      └────────────┘      



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

    def __init__(self, pin_vcoarse, pin_vfine, amp_gain, resistance, vthresh):
        self.board = pymata4.Pymata4()

        self.pin_vcoarse = self.board.set_pin_mode_pwm_output(pin_vcoarse)
        self.pin_vfine = self.board.set_pin_mode_pwm_output(pin_vfine)
        self.amp_gain = amp_gain
        self.resistance = resistance
        self.vthresh = vthresh

    def print(self):
        """
        print board
        """
        print("test")
