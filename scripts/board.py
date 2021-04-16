# -*- coding: utf-8 -*-
"""
Controls the tester board.

EXAMPLE: 
        python board.py --port=COM3 


REQUIREMENTS:
    python 3.7+
    pyfirmata  (to talk to the arduino)
    fire (to create command line tool)

@author: Eduardo Munoz
@email: edmugu@protonmail.com
"""
import pyfirmata
import fire
import time


class Board(object):
    """
    It controls the power supply tester board
    """

    def __init__(self):
        return

    def print(self):
        """
        print board
        """
        print("test")

