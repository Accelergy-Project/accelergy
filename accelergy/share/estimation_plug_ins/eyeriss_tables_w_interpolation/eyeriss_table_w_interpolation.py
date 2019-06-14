# -*- coding: utf-8 -*-
import csv, os, sys
from accelergy.helper_functions import oneD_linear_interpolation

class EyerissTableInterpolation(object):
    """
    a estimation plug-in
    """
    # -------------------------------------------------------------------------------------
    # Interface functions, function name, input arguments, and output have to adhere
    # -------------------------------------------------------------------------------------
    def __init__(self):
        self.estimator_name =  "eyeriss_table"

        # example primitive classes supported by this estimator
        self.supported_pc = ['SRAM', 'counter', 'mac', 'wire', 'crossbar']

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
        class_name = interface['class_name']
        attributes = interface['attributes']
        action_name = interface['action_name']
        arguments = interface['arguments']

        if class_name in self.supported_pc:
            attributes_supported_function = class_name + '_attr_supported'
            if getattr(self, attributes_supported_function)(attributes):
                action_supported_function = class_name + '_action_supported'
                accuracy = getattr(self, action_supported_function)(action_name, arguments)
                if accuracy is not None:
                    return accuracy

        return 0  # if not supported, accuracy is 0

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
        class_name = interface['class_name']
        query_function_name = class_name + '_estimate_energy'
        energy = getattr(self, query_function_name)(interface)
        return energy



    # ---------------------------------------------------------
    # User's functions, purely user-defined
    # ---------------------------------------------------------
    def SRAM_attr_supported(self, attributes):
        if 'technology' in attributes and\
            'width' in attributes and\
           'depth' in attributes and \
           'n_rdwr_ports' in attributes:

           if attributes['technology'] == '65nm':
               # SRAM tables are specifically generated for 65nm
               n_ports = attributes['n_rdwr_ports']
               width = attributes['width']
               depth = attributes['depth']

               # check if there is a table stored for a particular SRAM attributes
               if n_ports == 2 and width == 64 and depth == 1024:
                   return True
               elif n_ports == 2 and width == 1 and depth == 12:
                   return True
               # perform simple linear interpolation of depth at estimation
               elif n_ports == 2 and width ==16 and 1 <= depth <= 224:
                   return True
               else:
                   return False

               # if not using linear interpolation
               # elif n_ports == 2 and width == 16 and depth == 224:
               #     return True
               # elif n_ports == 2 and width == 16 and depth == 24:
               #      return True
               # elif n_ports == 2 and width == 16 and depth == 12:
               #     return True
               # elif n_ports == 2 and width == 1 and depth == 12:
               #     return True

        return False

    # ----------------- SRAM related ---------------------------
    def SRAM_action_supported(self, action_name, arguments):
        supported = False
        supported_action_names = ['read', 'write', 'idle']
        supported_arguments = {'data_delta': {'min': 0, 'max': 1}, 'address_delta': {'min': 0, 'max': 1}}
        if action_name in supported_action_names:
            if arguments is not None:
                for argument_name, argument_value in arguments.items():
                    if argument_name in supported_arguments:
                        if supported_arguments[argument_name]['min'] <= argument_value \
                                <= supported_arguments[argument_name]['max']:
                            supported = True
            else:
                supported = True
        if supported:
            return 95  # eyeriss accuracy is about 95%
        else:
            return None

    def SRAM_estimate_energy(self, interface):
        width = interface['attributes']['width']
        depth = interface['attributes']['depth']
        action_name = interface['action_name']
        arguments = interface['arguments']
        this_dir, this_filename = os.path.split(__file__)
        csv_file_path = os.path.join(this_dir,'data/SRAM.csv')
        energy = None
        with open(csv_file_path) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row['action_name'] == action_name and\
                   int(row['width']) == width and \
                   int(row['depth']) == depth:
                    if EyerissTable.matched_arguments(row, arguments):
                        energy = float(row['energy'])
                        break
        # no exact energy recorded in the table, do linear interpolation
        if energy is None:
            if 12 < depth < 24:
                known_list = [{'x':12, 'y': 0.0}, {'x':224, 'y': 0.0}]  # x is the depth, y is the energy
            elif 24 < depth < 224:
                known_list = [{'x':24, 'y': 0.0}, {'x':224, 'y': 0.0}]
            with open(csv_file_path) as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    if int(row['width']) == width and int(row['depth']) == known_list[0]['x'] and row['action_name'] == action_name:
                        if EyerissTableInterpolation.matched_arguments(row, arguments):
                            known_list[0]['y'] = float(row['energy'])
                    if int(row['width']) == width and int(row['depth']) == known_list[1]['x'] and row['action_name'] == action_name:
                        if EyerissTableInterpolation.matched_arguments(row, arguments):
                            known_list[1]['y'] = float(row['energy'])
            energy = oneD_linear_interpolation(depth, known_list)
        return energy

    @staticmethod
    def matched_arguments(row, arguments):
        if arguments is None:
            return True
        argument_matched = True
        for argument_name, argument_val in arguments.items():
            if not row[argument_name] == str(argument_val):
                argument_matched = False
                break
        if argument_matched:
            return True
        else:
            return False
    # ----------------- counter related ---------------------------

    def counter_attr_supported(self, attributes):

        supported_attributes = {'datawidth':[13, 10, 8, 4], 'technology': ['65nm']}
        supported_actions = ['count', 'idle']
        if 'datawidth' in attributes and 'technology' in attributes:
            if attributes['datawidth'] in supported_attributes['datawidth']\
                    and attributes['technology'] in supported_attributes['technology']:
                return True
        return False

    def counter_action_supported(self, action_name, arguments):
        supported_actions = ['count', 'idle']
        if action_name in supported_actions:
            return 95
        else:
            return None

    def counter_estimate_energy(self, interface):
        action_name = interface['action_name']
        datawidth = interface['attributes']['datawidth']

        this_dir, this_filename = os.path.split(__file__)
        csv_file_path = os.path.join(this_dir, 'data/counter.csv')
        energy = None
        with open(csv_file_path) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row['action_name'] == action_name and int(row['datawidth']) == datawidth:
                    energy = float(row['energy'])
                    break
        if energy is None:
            print('estimator plug-in error:, cannot estimate energy for supposedly supported input', interface)
            sys.exit(1)
        return energy

    # ----------------- mac related ---------------------------
    def mac_attr_supported(self, attributes):
        if 'technology' in attributes and 'datawidth' in attributes:
            if attributes['technology'] == '65nm' and attributes['datawidth'] == 16:
                return True
            else:
                return False
        else:
            return False
    def mac_action_supported(self, action_name, arguments):
        if action_name in ['idle', 'mac_random', 'mac_reused', 'mac_gated']:
            return 95
        else:
            return None

    def mac_estimate_energy(self, interface):
        action_name = interface['action_name']
        datawidth = interface['attributes']['datawidth']
        this_dir, this_filename = os.path.split(__file__)
        csv_file_path = os.path.join(this_dir, 'data/mac.csv')
        energy = None
        with open(csv_file_path) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row['action_name'] == action_name and int(row['datawidth']) == datawidth:
                    energy = float(row['energy'])
                    break
        if energy is None:
            print('estimator plug-in error:, cannot estimate energy for supposedly supported input', interface)
            sys.exit(1)
        return energy

    # ----------------- wire related ---------------------------
    def wire_attr_supported(self, attributes):
        if 'technology' in attributes and 'length' in attributes and 'datawidth' in attributes:
            if attributes['technology'] == '65nm':
                return True
            else:
                return False
        else:
            return False
    def wire_action_spported(self, action_name, arguments):
        if action_name in ['idle', 'transfer']:
            return 95
        else:
            return None
    def wire_estimate_energy(self, interface):
        action_name = interface['action_name']
        if action_name == 'transfer':
            length = interface['attributes']['length']
            datawidth = interface['attributes']['datawidth']
            C = 0.22
            VDD = 1.2
            alpha = 0.2
            E = 0.001 * datawidth * 0.5 * alpha * C * length * VDD ** 2
            return E
        else:
            return 0
    # ----------------- wire related ---------------------------
    def crossbar_attr_supported(self, attributes):
        if 'technology' in attributes and 'datawidth' in attributes \
            and 'n_inputs' in attributes and 'n_outputs' in attributes:
            if attributes['technology'] == '65nm':
                return True
            else:
                return False
        else:
            return False
    def crossbar_action_supported(self, action_name, arguments):
        if action_name in ['idle', 'transfer', 'transfer_repeated']:
            return 95
        else:
            return None
    def crossbar_estimate_energy(self, interface):
        # placeholder, eyeriss estimation did not use crossbar
        return 0



