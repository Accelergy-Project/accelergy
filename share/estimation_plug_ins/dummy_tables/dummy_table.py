# -*- coding: utf-8 -*-
import csv, os, sys
from accelergy.helper_functions import oneD_linear_interpolation

class DummyTable(object):
    """
    A dummy estimation plug-in
    Note that this plug-in is just a placeholder to illustrate the estimation plug-in interface
    It can be used as a template for creating user-defined plug-ins
    The energy values returned by this plug-in is not meaningful
    """
    # -------------------------------------------------------------------------------------
    # Interface functions, function name, input arguments, and output have to adhere
    # -------------------------------------------------------------------------------------
    def __init__(self):
        self.estimator_name =  "dummy_table"

    def primitive_action_supported(self, interface):
        """
        :param interface:
        - contains four keys:
        1. class_name : string
        2. attributes: dictionary of name: value
        3. action_name: string
        4. arguments: dictionary of name: value

        :type interface: dict

        :return return the accuracy if supported, return 0 if not
        :rtype: int

        """
        supported = 1 # dummy support everything
        return 0.1  if supported \
                    else 0  # if not supported, accuracy is 0

    def estimate_energy(self, interface):
        """
        :param interface:
        - contains four keys:
        1. class_name : string
        2. attributes: dictionary of name: value
        3. action_name: string
        4. arguments: dictionary of name: value

       :return the estimated energy
       :rtype float

        """
        if interface['action_name'] == 'idle':
            return 0 # dummy returns 0 for all idle actions
        if interface["class_name"] == "SRAM" and interface["attributes"]["depth"] == 0:
            return 0 # zero depth SRAM has zero energy

        return 1 # dummy returns 1 for all non-idle actions

    def primitive_area_supported(self, interface):
        """
        :param interface:
        - contains two keys:
        1. class_name : string
        2. attributes: dictionary of name: value

        :type interface: dict

        :return return the accuracy if supported, return 0 if not
        :rtype: int

        """
        supported = 1 # dummy support everything
        return 0.1  if supported \
                    else 0  # if not supported, accuracy is 0

    def estimate_area(self, interface):
        """
        :param interface:
        - contains two keys:
        1. class_name : string
        2. attributes: dictionary of name: value

        :type interface: dict

        :return the estimated area
        :rtype: float

        """
        if interface["class_name"] == "SRAM" and interface["attributes"]["depth"] == 0:
            return 0 # zero depth SRAM has zero area
        return 1 # dummy returns 1 for all areas