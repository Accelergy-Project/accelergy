# Copyright (c) 2019 Yannan Wu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os, re, string
from importlib.machinery import SourceFileLoader
from copy import deepcopy
from yaml import load
from accelergy import syntax_validators
from accelergy.utils import accelergy_loader, write_yaml_file, ERROR_CLEAN_EXIT, WARN, INFO, ASSERT_MSG
from accelergy.config_file_checker import config_file_checker
from accelergy.arithmetic_parsers import  parse_expression_for_arithmetic, process_arithmetic
from accelergy.utils import add_functions_as_methods

#### version control
import accelergy.v01_functions.v01_architecture_parser as v01_arch
import accelergy.v01_functions.v01_compound_component_constructor as v01_cc
import accelergy.v02_functions.v02_architecture_parser as v02_arch
import accelergy.v02_functions.v02_compound_component_constructor as v02_cc
@add_functions_as_methods(v01_arch.functions + v01_cc.functions +
                          v02_arch.functions + v02_cc.functions)

class EnergyReferenceTableGenerator(object):
    """ Generate an energy reference table for each component in the design """
    PC_classes_set = None     # static variable to record all the PC classes
    estimator_list = None     # static variable to record all the estimators
    def __init__(self):
        # initializes all bookkeeping containers
        self.compound_class_description      = {}
        self.raw_architecture_description    = None
        self.raw_compound_class_description  = None
        self.architecture_description        = {}
        self.primitive_class_description     = {}
        self.config                          = None
        self.energy_reference_table          = {}
        self.design_name                     = None
        self.output_path                     = None
        self.estimator_plug_ins              = []
        self.decimal_place                   = 3
        self.design                          = None
        self.compound_component_constructor  = None
        self.compound_class_version          = None
        self.arch_version                    = None
        self.verbose                         = 0
    @staticmethod
    def parse_arg_range(arg_range):
        if type(arg_range) is not str or '..' not in arg_range:
            ERROR_CLEAN_EXIT('cannot parse the argument range specification: ', arg_range)
        split_sub_string = arg_range.split('..')
        start_idx = int(split_sub_string[0])
        end_idx   = int(split_sub_string[1])
        return start_idx, end_idx
    @staticmethod
    def parse_repeat(action, upper_level_binding):
        """
        evaluates the values of repeat of a sub-component action
        - default value of repeat is 1
        - string bindings are allowed, and bindings can be from:
            1. compound attributes
            2. compound action arguments (its own upper-level action)
        - arithemtic operations are allowed in specifying repeat value

        """
        if 'repeat' in action and action['repeat'] is not None:
            if type(action['repeat']) is not int:
                op_type, op1, op2 = parse_expression_for_arithmetic(action['repeat'], upper_level_binding)
                if op_type is not None:
                    parsed_repeat = process_arithmetic(op1, op2, op_type)

                else:
                    if action['repeat'] in upper_level_binding:
                       parsed_repeat = upper_level_binding[action['repeat']]
                    else:
                        parsed_repeat = None
                        ERROR_CLEAN_EXIT('repeat value for primitive action cannot be parsed, ',
                                      'no binding found in compound arguments/ attributes',action)

                return parsed_repeat
            # return the actual value if repeat is an integer
            return action['repeat']
        # default repeat value is 1
        return 1
    @staticmethod
    def remove_brackets(name):
        """Removes the brackets from a component name in a list"""
        if '[' not in name and ']' not in name:
            return name
        if '[' in name and ']' in name:
            start_idx = name.find('[')
            end_idx = name.find(']')
            name = name[:start_idx] + name[end_idx + 1:]
            name = EnergyReferenceTableGenerator.remove_brackets(name)
            return name
    def is_primitive_class(self, class_name):
        if class_name in self.primitive_class_description :
            return True
        else:
            return False
    def construct_new_leaf_node_description(self, full_name, leaf_description, shared_attr_dict):
        """
        Interprets the architecture component
           1. apply the default values specified in the compound and primitive classes
           2. apply shared attributes projected from upper hierarchy
           3. check if there is any arithmetic expressions in the attribute
                    bindings have to be amongst the attribute names
           4. updates the architecture description data structure
        """

        # ERROR: duplicate names in architecture
        if full_name in self.architecture_description:
            ERROR_CLEAN_EXIT('flattened name: ', full_name, ' is already in architecture, check duplicated names')

        class_name = leaf_description['class']
        new_component_description = {'class': class_name}

        # apply the default values specified in the compound and primitive classes
        if not self.is_primitive_class(class_name) and not class_name in self.compound_class_description:
            ERROR_CLEAN_EXIT('cannot find the class specified:', class_name)
        if not self.is_primitive_class(class_name):
            new_component_description['attributes'] = deepcopy(self.compound_class_description[class_name]['attributes'])
        else:
            new_component_description['attributes'] = deepcopy(self.primitive_class_description[class_name]['attributes'])

        if 'attributes' in leaf_description:
            new_component_description['attributes'].update(leaf_description['attributes'])

        # apply shared attributes projected from upper hierarchy
        # if redefined at the node, the attribute value will not be projected
        if shared_attr_dict is not None:
            for name, value in shared_attr_dict.items():
                if 'attributes' not in leaf_description or \
                    name not in leaf_description['attributes'] :
                    new_component_description['attributes'].update({name:value})

                # Info: projected shared attributes overridden
                if 'attributes'  in leaf_description and \
                    name in leaf_description['attributes'] :
                    INFO('Ignored shared attribute value projection: attribute ', name, ' redefined at component ', full_name,
                          ' => ignore projected value from upper hierarchy')

        # check if there is any binding or arithmetic expressions in the attribute dictionary
        for attr_name, attr_val in new_component_description['attributes'].items():
            if type(attr_val) is str :
                op_type, op1, op2 = parse_expression_for_arithmetic\
                                                (attr_val, new_component_description['attributes'])
                if not op_type is None:
                    result = process_arithmetic(op1, op2, op_type)
                    new_component_description['attributes'][attr_name] = result
                else:
                    if attr_val in new_component_description['attributes']:
                        new_component_description['attributes'][attr_name] = new_component_description['attributes'][attr_val]

        # save to data structure
        self.architecture_description[full_name] = deepcopy(new_component_description)
    def initialize_ERT_for_action_with_arg_ranges(self, action):
        """
        initializes an ERT with zero energy for all possible action argument value combinations

        :param action: a dictionary that contains the following keys:
                      1. name
                      2. arguments dictionary: contains argument names as keys and argument ranges as values
        :return: an ERT skeleton for the action, each entry in the list is a dictionary that contains:
                 1. argument name-value pairs
                 2. energy key with its values initialized to zeo
        :rtype: list

        """
        # calculate the total number of possible entries in the table
        total_entries = 1
        for argument_name, argument_range in action['arguments'].items():
            start_idx, end_idx = self.parse_arg_range(argument_range)
            total_entries *= (end_idx - start_idx + 1)

        # construct list of dictionaries that contain all the possible combination of argument values
        action_ERT_with_args = []
        for entry_idx in range(total_entries):
            offset = 1
            argument_key_list = list(action['arguments'].keys())
            action_ERT_with_args.append([])
            action_ERT_with_args[entry_idx] = {'arguments': {}, 'energy': 0}
            # fill out the ERT entry with corresponding argument name-value pairs
            for key_idx in range(len(argument_key_list)):
                argument_name = argument_key_list[key_idx]
                argument_range = action['arguments'][argument_name]
                start_idx, end_idx = self.parse_arg_range(argument_range)
                arg_range = end_idx - start_idx + 1
                action_ERT_with_args[entry_idx]['arguments'][argument_name] = (entry_idx // offset) % arg_range
                offset *= arg_range
        return action_ERT_with_args
    def construct_interface_and_estimate(self, action, component_info):
        """
           constructs the interface with estimator plug-ins
           evaluates the available plug-ins in terms of accuracy
           queries the plug-in with the best estimation accuracy
        """
        primitive_class_name = component_info['class']
        attributes = component_info['attributes']

        # --> if the action requires arguments (either ranges or static values are provided)
        if 'arguments' in action:
            # if arguments are required by the class, create the
            argument_name, argument_info = list(action['arguments'].items())[0]
            if type(argument_info) is int:
                argument_value_provided = True
            else:
                argument_value_provided = False

            # make sure the argument info list is homogeneous, either ranges or static values
            for argument_name, argument_info in action['arguments'].items():
                if type(argument_info) is int and not argument_value_provided:
                    ERROR_CLEAN_EXIT('argument values can either be a homogeneous ranges or homogeneous numbers ')
                if type(argument_info) is str and argument_value_provided:
                    ERROR_CLEAN_EXIT('argument values can either be a homogeneous ranges or homogeneous numbers ')

            # if only the ranges are provided
            if not argument_value_provided:
                action_ERT =  self.initialize_ERT_for_action_with_arg_ranges(action)
                for arg_combo in action_ERT:
                    estimator_plug_in_interface = {'class_name': primitive_class_name,
                                                   'attributes': attributes,
                                                   'action_name': action['name'],
                                                   'arguments': arg_combo['arguments']}
                    # print(arg_combo)
                    energy = self.eval_primitive_action_energy(estimator_plug_in_interface)
                    arg_combo['energy'] = energy
                return action_ERT

            # if the argument values are static numbers
            else:
                # print(/action)
                estimator_plug_in_interface = {'class_name': primitive_class_name,
                                               'attributes': attributes,
                                               'action_name': action['name'],
                                               'arguments': action['arguments']}
                energy = self.eval_primitive_action_energy(estimator_plug_in_interface)
                return {'energy': energy, 'arguments': action['arguments']}  # energy of a fixed set of argument values

        # --> if there is no argument required for the action
        else:
            estimator_plug_in_interface = {'class_name': primitive_class_name,
                                           'attributes': attributes,
                                           'action_name': action['name'],
                                           'arguments': None}
            energy = self.eval_primitive_action_energy(estimator_plug_in_interface)
            return {'energy': energy, 'arguments': None}

    def eval_primitive_action_energy(self, estimator_plug_in_interface):
        """
        :param estimator_plug_in_interface: dictionary that adheres to
               Accelergy-external estimator interface format
        :return energy estimation of the action
        """
        best_accuracy = 0
        best_estimator = None
        for estimator in self.estimator_plug_ins:
            accuracy = estimator.primitive_action_supported(estimator_plug_in_interface)
            ASSERT_MSG(type(accuracy) is int or type(accuracy) is float,
                       'Wrong plug-in accuracy: %s ...  Returned accuracy must be integers or floats'%(estimator))
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_estimator = estimator
        if best_estimator is None:
            ERROR_CLEAN_EXIT('cannot find estimator plug-in:', estimator_plug_in_interface,
                             'Available plug-ins:', self.estimator_plug_ins)
        energy = best_estimator.estimate_energy(estimator_plug_in_interface)
        if self.verbose:
         INFO('Received energy estimation for primitive class:\n', estimator_plug_in_interface,
              '\n estimated by:', best_estimator, ' ---> estimated energy:', energy)
        return energy

    def generate_component_ert(self, component_info, is_primitive_class):
        """
        According to component type, processes the received information differently

        primitive component:
            - base case of this function
            - apply default attributes, directly chooses the best estimator and generates ERT

        compound component: parse the subcomponet information and evaluate the ERT for the subcomponent actions first

            - top-level compound component with actions
                1. no argument, generate for the action by parsing its definition and recursively call this function
                2. argument ranges: generate energy/action for one possible argument value(s) a time,
                                    and loops through all the possibilities

            - low-level compound components
              1. no argument, generate for the action by parsing its definition and recursively call this function
              2. argument values: since it is low-level, its argument values should already be defined by the
                                  high-level compound component's action argument value

        :param component_info:  dictionary the physical information about a component
        :param is_primitive_class: boolean whether this component is primitive
        :return: ERT for the component
        """

        # case 1: if is_primitive_class: directly call energy estimators
        if is_primitive_class:
            primitive_class_name = component_info['class']
            ERT = {}  # energy reference table for this class
            class_description = self.primitive_class_description[primitive_class_name]
            if 'actions' not in component_info:
              action_list = class_description['actions']
            else:
              action_list = component_info['actions']

            # apply the default primitive attribute values
            if 'attributes' not in component_info:
                component_info['attributes'] = {}
            for attr_name, attr_default in class_description['attributes'].items():
                if attr_name not in component_info['attributes']:
                    component_info['attributes'].update({attr_name: attr_default})

            for action in action_list:
              ERT[action['name']] = self.construct_interface_and_estimate(action, component_info)
            return ERT

        # case 2: if not is_primitive_class: parse the compound class information
        else:
            compound_component_ERT = {}
            compound_class_name = component_info['class']
            compound_component_attributes = component_info['attributes']
            ASSERT_MSG(compound_class_name in self.compound_class_description, 'Cannot find class definition: %s'%compound_class_name)
            compound_class_description = self.compound_class_description[compound_class_name]
            if 'subcomponents' not in compound_class_description:
                ERROR_CLEAN_EXIT('compound class description missing subcomponents:', compound_class_name)
            defined_component = getattr(self, self.compound_component_constructor)(component_info)
            # generate ERTs for the compound actions
            compound_actions = deepcopy(defined_component['actions'])
            for action in compound_actions:
                compound_action_name = action['name']
                if 'arguments' in action and action['arguments'] is not None:
                    compound_arg_name, compound_arg_info = list(action['arguments'].items())[0]
                    if type(compound_arg_info) is int:
                        argument_value_provided = True
                    else:
                        argument_value_provided = False

                    # if arguments are ranges, then this is the top level compound component
                    if not argument_value_provided:
                        # action is a list of energy values
                        action_ERT = self.initialize_ERT_for_action_with_arg_ranges(action)
                        # for each arg values combo for the compound component
                        for arg_val_combo in action_ERT:
                            # for each subcomponent involved in action definition
                            for subcomponent_action in action['subcomponents']:
                                subcomponent_name = subcomponent_action['name']
                                # retrieve hardware info from the updated subcomponent list
                                subcomponent_info = defined_component['subcomponents'][subcomponent_name]
                                # for each action that is related to this subcomponent
                                for subaction in subcomponent_action['actions']:
                                    subaction_energy = self.eval_subcomponent_action_for_ERT(subaction,
                                                                                             subcomponent_info,
                                                                                             arg_val_combo['arguments'],
                                                                                             compound_component_attributes)
                                    arg_val_combo['energy'] = round(arg_val_combo['energy'] + subaction_energy, self.decimal_place)

                    # if arguments are static values, then this is a compound component that is subcomponent of another compound component
                    else:
                        action_ERT = {'energy' : 0, 'arguments': action['arguments']}
                        for subcomponent_action in action['subcomponents']:  # for each subcomponent involved in action definition
                            subcomponent_name = subcomponent_action['name']
                            subcomponent_info = defined_component['subcomponents'][subcomponent_name]  # retrieve hardware info from the updated subcomponent list
                            for subaction in subcomponent_action['actions']:  # for each action that is related to this subcomponent
                                    subaction_energy = self.eval_subcomponent_action_for_ERT(subaction,
                                                                                             subcomponent_info,
                                                                                             action['arguments'],
                                                                                             compound_component_attributes)
                                    action_ERT['energy'] = round(action_ERT['energy'] + subaction_energy, self.decimal_place)

                else:
                    # if the compound action has no arguments
                    action_ERT = {'energy': 0, 'arguments': None}
                    subaction_energy = 0
                    for subcomponent_action in action['subcomponents']:  # for each subcomponent involved in action definition
                        subcomponent_name = subcomponent_action['name']
                        subcomponent_info = defined_component['subcomponents'][subcomponent_name]  # retrieve hardware info from the updated subcomponent list
                        for subaction in subcomponent_action['actions']:  # for each action that is related to this subcomponent
                            subaction_energy = self.eval_subcomponent_action_for_ERT(subaction,
                                                                                     subcomponent_info,
                                                                                     None,
                                                                                     compound_component_attributes)
                            action_ERT['energy'] = round(action_ERT['energy']+subaction_energy, self.decimal_place)

                # record the generated ERT for the compound component
                compound_component_ERT[compound_action_name] = deepcopy(action_ERT)
            return compound_component_ERT

    def eval_subcomponent_action_for_ERT(self, subaction, subcomponent_info, upper_level_arguments, upper_level_attributes):
        subaction_copy = deepcopy(subaction) # do not want to modify the class definitions
        if 'arguments' in subaction and subaction_copy['arguments'] is not None:  # if there is arguments, evaluate the arguments in terms of the compound action arguments
            for subarg_name, subarg_info in subaction_copy['arguments'].items():
                if type(subarg_info) is str :
                    try:
                        subaction_copy['arguments'][subarg_name] = upper_level_arguments[subarg_info]
                    except KeyError:
                        print('available compound arguments: ', upper_level_arguments)
                        print('primitive argument to for binding:', subarg_info)
                        ERROR_CLEAN_EXIT('subcomponent argument name cannot be ',
                                          'mapped to upper class arguments', subarg_info)

        subcomponent_info['actions'] = [subaction_copy]
        is_subcomponent_primitive_class = self.is_primitive_class(subcomponent_info['class'])
        subaction_ERT = self.generate_component_ert(subcomponent_info, is_subcomponent_primitive_class)
        # the call is guaranteed to produce an ERT with 'energy' and 'argument' key
        subaction_energy = subaction_ERT[subaction_copy['name']]['energy']
        if type(subaction_energy) is not int and type(subaction_energy) is not float:
            ERROR_CLEAN_EXIT('Unusual estimated energy received for:',subcomponent_info, 'Energy received: %s'%subaction_energy)
        # parse the repeat information of the subaction (if any)
        #     repeat can be int
        #                   binding to compound component arguments
        #                   binding to compound component attributes
        upper_level_binding = deepcopy(upper_level_attributes)
        if upper_level_arguments is not None:
            upper_level_binding.update(upper_level_arguments)

        parsed_repeat_info = EnergyReferenceTableGenerator.parse_repeat(subaction, upper_level_binding)
        subaction_energy *= parsed_repeat_info
        # print(subaction_ERT, parsed_repeat_info, subaction_energy)
        return subaction_energy
    def map_arg_range_bounds(self, arg_range_str, attributes_dict):
        """
        arguments for compound actions might have ranges that are specified in terms of it attributes
        parses the argument ranges in the format int/str..int/str, where str can be arithmetic operation

        :param arg_range_str: string that decribes the range of a compound action
        :param attributes_dict: attribute name-value pairs of the compound component
        :return: parsed argument range, whether there was binding
        """
        split_sub_string = arg_range_str.split('..')
        detect_arg_range_binding = False
        # process the start index
        try:
            start_idx = int(split_sub_string[0])
        except ValueError:
            op_type, op1, op2 = parse_expression_for_arithmetic(split_sub_string[0], attributes_dict)
            if op_type is not None:
                start_idx = process_arithmetic(op1, op2, op_type)
            else:
                if split_sub_string[0] not in attributes_dict:
                    ERROR_CLEAN_EXIT('cannot find mapping from', arg_range_str, 'to', attributes_dict)
                start_idx = attributes_dict[split_sub_string[0]]
            detect_arg_range_binding = True

        # process the end index
        try:
            end_idx = int(split_sub_string[1])
        except ValueError:
            op_type, op1, op2 = parse_expression_for_arithmetic(split_sub_string[1], attributes_dict)
            if op_type is not None:
                end_idx = process_arithmetic(op1, op2, op_type)
            else:
                if split_sub_string[1] not in attributes_dict:
                    ERROR_CLEAN_EXIT('cannot find mapping from', arg_range_str, 'to', attributes_dict)
                end_idx = attributes_dict[split_sub_string[1]]
            detect_arg_range_binding = True

        new_arg_range_str = str(start_idx) + '..' + str(end_idx)

        return new_arg_range_str, detect_arg_range_binding
    def instantiate_estimator_plug_ins(self):
        """
        instantiate a list of estimator plug-in objects for later queries
        estimator plug-in paths are specified in config file

        """
        for estimator_dir in self.config['estimator_plug_ins']:
            for root, directories, file_names in os.walk(estimator_dir):
                for file_name in file_names:
                    if '.estimator.yaml' in file_name:
                        INFO('estimator plug-in identified by: ', root + os.sep + file_name)
                        estimator_spec = load(open(root + os.sep + file_name), accelergy_loader)
                        # validate the spec syntax
                        syntax_validators.validate_estimator_API(estimator_spec)
                        for key,val in estimator_spec.items():
                            if not key == 'version':
                                estimator_info = val
                        module_name = estimator_info['module']
                        class_name = estimator_info['class']
                        file_path = root+ '/' + module_name + '.py'
                        estimator_module = SourceFileLoader(class_name,file_path).load_module()

                        if 'parameters' not in estimator_info:
                            estimator_obj = getattr(estimator_module, class_name)()
                        else:
                            estimator_obj = getattr(estimator_module, class_name)(estimator_info['parameters'])

                        self.estimator_plug_ins.append(estimator_obj)
    def construct_primitive_class_description(self):
        """
        construct a dictionary for primitive classes Accelergy
        primitive class file paths are specified in config file
        """
        # load in the stored primitive classes
        primitive_class_paths = self.config['primitive_components']
        for pc_path in primitive_class_paths:
            # primitive component library file is directly specified
            if '.yaml' in pc_path:
                self.expand_primitive_component_lib_info(pc_path)
            else:
                # primitive component dir is specified, need recursive search
                for root, directories, file_names in os.walk(pc_path):
                    for file_name in file_names:
                        if '.lib.yaml' in file_name:
                            pc_path = root + os.sep + file_name
                            primitive_component_list = load(open(pc_path), accelergy_loader)
                            syntax_validators.validate_primitive_classes(primitive_component_list)
                            for idx in range(len(primitive_component_list['classes'])):
                                pc_name = primitive_component_list['classes'][idx]['name']
                                if pc_name in self.primitive_class_description:
                                    WARN(pc_name, 'redefined in', pc_path)
                                self.primitive_class_description[pc_name] = primitive_component_list['classes'][idx]
                            INFO('primitive component file parsed: ', pc_path)
    def ERT_existed(self, component_name):
        """
        Component that belongs to a list shares ERT with other identical components in the list
        This function parses the name of the components and checks if the ERT for the component exists

        :param component_name: component name string as appears in the architecture
        :return: boolean, parsed name (list component only uses base name)
        """
        ERT_existed = True
        if '[' in component_name and ']' in component_name:
            component_name_to_be_recorded = EnergyReferenceTableGenerator.remove_brackets(component_name)
        else:
            component_name_to_be_recorded = component_name
        if component_name_to_be_recorded not in self.energy_reference_table:
            ERT_existed = False
        return ERT_existed, component_name_to_be_recorded
    def generate_ERTs_for_architecture(self):
        """
        For each component in the architecture, generate an ERT if needed
        generated ERTs are saved to self.energy_reference_table
        """
        for component_name, component_info in self.architecture_description.items():
            component_info['name'] = component_name
            ERT_check_result = self.ERT_existed(component_name)
            if not ERT_check_result[0]:
                INFO(component_info['name'], ' ---> Generating new ERT')
                is_primitive_class = True if self.is_primitive_class(component_info['class']) else False
                ERT = self.generate_component_ert(component_info, is_primitive_class)
                self.energy_reference_table[ERT_check_result[1]] = ERT
                INFO(component_info['name'], ' ---> New ERT generated')
    def construct_compound_class_description(self):
        """
        checks if there are duplicated compound component class names
        :param compound_class_list: list of compound classes that need parsing
        :return: None (self.compound_class_description is updated)
        """
        if 'version' not in self.raw_compound_class_description:
            ERROR_CLEAN_EXIT('please specify the version of parser your input format adheres to using '
                             '"version" key at top level')
        for idx in range(len(self.raw_compound_class_description['classes'])):
            compound_class_name = self.raw_compound_class_description['classes'][idx]['name']
            if compound_class_name in self.compound_class_description:
                ERROR_CLEAN_EXIT('duplicate compound class name in component class description,',
                                 'error class name', compound_class_name)
            self.compound_class_description[compound_class_name] = self.raw_compound_class_description['classes'][idx]
            try:
                subcomponents = self.compound_class_description[compound_class_name]['subcomponents']
            except KeyError:
                subcomponents = None
                ERROR_CLEAN_EXIT('compound classes must have "subcomponents" key to specify the lower-level details',
                                  'error class name: ', compound_class_name)
        self.compound_class_version = self.raw_compound_class_description['version']
        self.compound_component_constructor = 'v' + str(self.compound_class_version).replace('.', '') + \
                                          '_compound_component_constructor'
    def construct_save_architecture_description(self):
        if 'version' not in self.raw_architecture_description:
            ERROR_CLEAN_EXIT('please specify the version of parser your input format adheres to using '
                             '"version" key at top level')
        self.arch_version  = self.raw_architecture_description['version']
        architecture_description_parser = 'v' + str(self.arch_version).replace('.', '') + \
                                 '_parse_architecture_description'
        getattr(self, architecture_description_parser)(self.raw_architecture_description)
    def generate_easy_to_read_flattened_architecture(self):
        self.easy_to_read_flattened_architecture = {}
        list_names = {}
        for component_name, component_info in self.architecture_description.items():

            if '[' not in component_name or ']' not in component_name:
                self.easy_to_read_flattened_architecture[component_name] = deepcopy(component_info)
            else:
                name_base = EnergyReferenceTableGenerator.remove_brackets(component_name)
                idx_list = []
                for match in re.finditer(r'\[\w+\]', component_name):
                    idx_list.append(int(component_name[match.start()+1:match.end()-1]))
                if name_base not in list_names:
                    list_names[name_base] = {}
                    list_names[name_base]['format'] = []
                    parts = component_name.split('.')
                    for part_idx in range(len(parts)):
                        if '[' and ']' in parts[part_idx]:
                            list_names[name_base]['format'].append(part_idx)
                    list_names[name_base]['idx_list'] = idx_list
                else:
                    i = 0
                    for existing_idx in list_names[name_base]['idx_list']:
                        if idx_list[i] > existing_idx:
                            list_names[name_base]['idx_list'][i] = idx_list[i]
                        i +=1

        for name_base, list_info in list_names.items():
            ranged_name_list = name_base.split('.')
            max_name_list = name_base.split('.')
            for idx in range(len(list_info['format'])):
                range_location = list_info['format'][idx]
                range_max = list_info['idx_list'][idx]
                ranged_name_list[range_location] += '[0..' + str(range_max) + ']'
                max_name_list[range_location] += '[' + str(range_max)  + ']'
            sep = '.'
            ranged_name_str = sep.join(ranged_name_list)
            max_name_str = sep.join(max_name_list)
            self.easy_to_read_flattened_architecture[ranged_name_str] = self.architecture_description[max_name_str]
    def interpret_input_path(self, file_path):
        file = load(open(file_path), accelergy_loader)
        for key in file:
            if key == 'architecture':
                content = file[key]
                ASSERT_MSG('version' in content and 'subtree' in content,
                           'File content not legal: %s, architecture description must contain '
                            '"version" and "subtree" keys'%file_path)
                ASSERT_MSG(type(content['subtree'] is dict),
                           'File content not legal: %s, "subtree" key must have value of type dict' % file_path)
                if self.raw_architecture_description is None:
                    self.raw_architecture_description = file[key]
                else:
                    ASSERT_MSG(self.raw_architecture_description['version'] == content['version'],
                               'File content not legal: %s, Versions of two architecture description '
                               'related file do not match'%file_path)
                    self.raw_architecture_description.update(file[key]['subtree'])

            if key == 'compound_components':
                content = file[key]
                ASSERT_MSG('version' in content and 'classes' in content,
                           'File content not legal: %s, component class description must contain '
                            '"version" and "classes" keys'%file_path)
                ASSERT_MSG(type(content['classes'] is list),
                           'File content not legal: %s, "classes" key must have value of type list' % file_path)
                if self.raw_compound_class_description is None:
                    self.raw_compound_class_description = file[key]
                else:
                    ASSERT_MSG(self.raw_compound_class_description['version'] == content['version'],
                               'File content not legal: %s, Versions of two compound class description '
                               'related file do not match'%file_path)
                    self.raw_compound_class_description['classes'].append(file[key]['classes'])
    def generate_ERTs(self, raw_architecture_description, raw_compound_class_description
                      ,output_path, precision, flatten_arch_flag, verbose):
        """
        main function to start the energy reference generator
        parses the input files
        produces the energy reference tables for components
        """
        print('\n=========================================')
        print('Generating energy reference tables')
        print('=========================================')

        # Interpret inputs
        self.verbose = verbose
        self.output_path = output_path
        self.decimal_place = precision

        # Load accelergy config
        self.config = config_file_checker()

        # interpret the list of files
        # for file_path in path_arglist:
        #     self.interpret_input_path(file_path)
        #     INFO('Input file parsed: ', file_path)
        self.raw_architecture_description = raw_architecture_description['architecture']
        self.raw_compound_class_description = raw_compound_class_description['compound_components']

        # self.design = load(open(self.design_path), accelergy_loader)
        # INFO('design loaded:', design_path)
        self.construct_compound_class_description()

        # Load the primitive classes library
        self.construct_primitive_class_description()
        ASSERT_MSG(not len(self.primitive_class_description) == 0, 'No primitive component class found, '
                   'please check if the paths in config file are correct')

        # Parse the architecture description and save the parsed version if flag high
        self.construct_save_architecture_description()
        if flatten_arch_flag:
            self.generate_easy_to_read_flattened_architecture()
            arch_file_path = self.output_path + '/' + 'flattened_architecture.yaml'
            flattened_architecture_yaml = {'flattened_architecture': {'version': self.arch_version,
                                                                      'components': self.easy_to_read_flattened_architecture}}
            write_yaml_file(arch_file_path, flattened_architecture_yaml)
            INFO('Architecture flattened ... saved to ', arch_file_path)

        # Instantiate the estimation plug-ins as intances of the corresponding plug-in classes
        self.instantiate_estimator_plug_ins()
        ASSERT_MSG(not len(self.estimator_plug_ins) == 0, 'No estimation plug-in found, '
                                                      'please check if the paths in config file are correct')

        # Generate Energy Reference Tables for the components
        self.generate_ERTs_for_architecture()

        # Save the ERTs to ERT.yaml in the output directory
        ERT_file_path = self.output_path + '/' + 'ERT.yaml'
        ERT_dict = {'ERT':{'version': self.arch_version, 'tables': self.energy_reference_table}}
        write_yaml_file(ERT_file_path, ERT_dict)
        print('---> Finished: ERT generation finished, ERT saved to:\n', os.path.abspath(output_path))