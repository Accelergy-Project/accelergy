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

import math, os, sys
from importlib.machinery import SourceFileLoader
from copy import deepcopy
from yaml import load, dump
from accelergy import syntax_validators
from accelergy.utils import accelergy_loader, accelergy_dumper, \
                            write_yaml_file, ERROR_CLEAN_EXIT, WARN, INFO,\
                            create_folder


class EnergyReferenceTableGenerator(object):
    """ Generate an energy reference table for each component in the design """

    PC_classes_set = None     # static variable to record all the PC classes
    estimator_list = None     # static variable to record all the estimators
    def __init__(self):

        # initializes all bookkeeping containers
        self.compound_class_description    = {}
        self.raw_architecture_description  = {}
        self.architecture_description      = {}
        self.primitive_class_description   = {}
        self.config                        = None
        self.energy_reference_table        = {}
        self.design_name                   = None
        self.output_path                   = None
        self.estimator_plug_ins            = []
        self.decimal_place                 = 3
        self.design                        = None

    @staticmethod
    def parse_arg_range(arg_range):

        if type(arg_range) is not str or '..' not in arg_range:
            ERROR_CLEAN_EXIT('cannot parse the argument range specification: ', arg_range)

        split_sub_string = arg_range.split('..')

        start_idx = int(split_sub_string[0])
        end_idx   = int(split_sub_string[1])

        return start_idx, end_idx

    @staticmethod
    def is_component_list(name, binding_dictionary = None):
        """
        determines if the component is a list according to its name
        component
        if not, return 0
        if yes, return list length

        it is possible that the last index of the list involves direct binding or arithmetical operations
        (operands could be strings that are keys in binding dictionary)
        """
        start_idx = name.find('[0')
        if start_idx == -1:
            return 0, None
        else:
            if ']' not in name:
                WARN(name, ': located [0: but not ], typo?')
            else:
                name_base = name[:start_idx]
                end_idx = name.find(']')
                tail = name[start_idx+3: end_idx]
                # check if the tail involves arithmetic operations
                optype, op1, op2 = EnergyReferenceTableGenerator.parse_expression_for_arithmetic(tail, binding_dictionary)
                if optype is None:
                    if tail in binding_dictionary:
                        # tail is a direct binding, directly retrieve the numerical value
                        tail = binding_dictionary[tail]
                    list_length = int(tail) + 1
                else:
                    list_length = int(EnergyReferenceTableGenerator.process_arithmetic(op1, op2, optype))+ 1
                return list_length, name_base


    @staticmethod
    def process_arithmetic(op1, op2, op_type):
        """ Turns string expression into arithmetic operation"""
        if op_type == '*':
            result = op1 * op2
        elif op_type == '/':
            result = int(math.ceil(op1/op2))
        elif op_type == '//':
            result = op1//op2
        elif op_type == '%':
            result = math.remainder(op1, op2)
        elif op_type == '-':
            result = int(op1 -op2)
        elif op_type == '+':
            result = int(op1 + op2)
        elif op_type == 'log2':
            result = int(math.ceil(math.log2(op1)))
        else:
            result = None
            ERROR_CLEAN_EXIT('wrong op_type')
        return result


    @staticmethod
    def parse_expression_for_arithmetic(expression, binding_dictionary):
        """
        Expression contains the operands and the op type,
        binding dictionary contains the numerical values of the operands (if they are strings)
        """
        # parse for the supported arithmetic operations
        if '*' in expression:
            op_type = '*'
        elif '/' in expression:
            op_type = '/'
        elif '//' in expression:
            op_type = '//'
        elif '%' in expression:
            op_type = '%'
        elif '+' in expression:
            op_type = '+'
        elif '-' in expression:
            op_type = '-'
        elif 'log2(' and ')' in expression:
            op_type = 'log2'
        else:
            op_type = None

        # if the expression is an arithmetic operation
        if op_type is not None:

            if not op_type == 'log2':
                op1 = expression[:expression.find(op_type)].strip()
                op2 = expression[expression.find(op_type) + 1:].strip()

            # log2 only needs one operand, and needs to be processed differently
            else:
                op1 = expression[expression.find('(') + 1: expression.find(')')].strip()
                op2 = None

            if op1 in binding_dictionary:
                op1 = binding_dictionary[op1]
            else:
                try:
                    op1 = int(op1)
                except ValueError:
                    print('arithmetic expression:', expression, '\n',
                          'available operand-value binding:', binding_dictionary)
                    ERROR_CLEAN_EXIT('arithmetic operation located, but cannot parse operand value')

            # if the operation needs 2 operands
            if op2 is not None:
                if op2 in binding_dictionary:
                    op2 = binding_dictionary[op2]
                else:
                    try:
                        op2 = int(op2)
                    except ValueError:
                        ERROR_CLEAN_EXIT('arithmetic operation located, but cannot parse operand value')
        # if the expression is not an arithmetic operation
        else:
            op1 = None
            op2 = None
        return op_type, op1, op2

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
                op_type, op1, op2 = EnergyReferenceTableGenerator.parse_expression_for_arithmetic\
                                                (attr_val, new_component_description['attributes'])
                if not op_type is None:
                    result = EnergyReferenceTableGenerator.process_arithmetic(op1, op2, op_type)
                    new_component_description['attributes'][attr_name] = result
                else:
                    if attr_val in new_component_description['attributes']:
                        new_component_description['attributes'][attr_name] = new_component_description['attributes'][attr_val]

        # save to data structure
        self.architecture_description[full_name] = deepcopy(new_component_description)


    # processes the hierarchical representation and save the processed results
    def construct_save_architecture_description(self, architecture_description_list):
        if 'version' not in architecture_description_list:
            ERROR_CLEAN_EXIT('please specify the version of parser your input format adheres to using '
                             '"version" key at top level')

        if 'nodes' not in architecture_description_list:
            ERROR_CLEAN_EXIT('architecture tree nodes should be the value of top level key "nodes", '
                             '"nodes" not found at top-level')

        raw_architecture_description = architecture_description_list['nodes']

        if not len(architecture_description_list['nodes']) == 1:
            ERROR_CLEAN_EXIT('the first level list of your architecture description should only have one node, '
                             'which is your design\'s root node' )

        global_attributes = None if 'attributes' not in raw_architecture_description[0] \
                                 else raw_architecture_description[0]['attributes']
        # design name syntax check
        if 'name' not in raw_architecture_description[0]:
            ERROR_CLEAN_EXIT (
                   "architecture description : " 
                   "please specify the design name as top-level key-value pair =>  name: <design_name>")

        self.design_name = raw_architecture_description[0]['name']

        # if design is itself just one leaf component
        if 'nodes' not in raw_architecture_description[0]:
            if 'class' in raw_architecture_description[0]:
                #TODO: single leaf node case can also have a name that is of list format
                self.construct_new_leaf_node_description(raw_architecture_description[0]['name'],
                                                         raw_architecture_description,
                                                         None)
                return
            # leaf class syntax violation
            else:
                ERROR_CLEAN_EXIT('architecture description syntax violation: leaf component without class')
        # if architecture tree has height > 1
        else:
            for node in raw_architecture_description[0]['nodes']:
                self.flatten_architecture_description(self.design_name, node, global_attributes)

    def flatten_architecture_description(self, prefix, node_description, shared_attributes_dict= None):

        """Recursively parse the nodes in the architecture tree"""

        # syntax error checks
        if 'name' not in node_description:
            ERROR_CLEAN_EXIT('component format violation: "name" needs to be specified as a key in node description')
        if 'class' in node_description and 'nodes' in node_description:
            ERROR_CLEAN_EXIT('class and nodes keys cannot exist in the same node')
        # extract basic information
        node_name = node_description['name']

        # construct the shared attributes that can be applied to sub-nodes
        # useful only if current node is internal
        if shared_attributes_dict is None and 'attributes' not in node_description:
            node_attrs = None
        elif shared_attributes_dict is not None and 'attributes' not in node_description:
            node_attrs = deepcopy(shared_attributes_dict)
        elif shared_attributes_dict is None and 'attributes' in node_description:
            node_attrs = node_description['attributes']
        else: #shared_attributes_dict is not None and attributes in node_description
            node_attrs = deepcopy(shared_attributes_dict)
            node_attrs.update(node_description['attributes'])

        # determine if the component is in list format
        list_length, name_base = EnergyReferenceTableGenerator.is_component_list(node_name, shared_attributes_dict)

        # if the component is in list format, flatten out and create the instances
        if not list_length == 0:
            for item_idx in range(list_length):
                item_prefix = prefix + '.' + name_base + '[' + str(item_idx) + ']'
                if 'nodes' in node_description:
                    for sub_node_description in node_description['nodes']:
                        self.flatten_architecture_description(item_prefix, sub_node_description, node_attrs)
                else:
                    self.construct_new_leaf_node_description(item_prefix, node_description, shared_attributes_dict)

        # if the component is a standalone component, parse the component description directly
        else:
            node_prefix = prefix + '.' + node_name
            if 'nodes' in node_description:
                for sub_node_description in node_description['nodes']:
                    self.flatten_architecture_description(node_prefix, sub_node_description, node_attrs)
            else:
                self.construct_new_leaf_node_description(node_prefix, node_description, shared_attributes_dict)


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
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_estimator = estimator
        if best_estimator is None:
            ERROR_CLEAN_EXIT('cannot find estimator plug-in:', estimator_plug_in_interface, self.estimator_plug_ins)
        energy = best_estimator.estimate_energy(estimator_plug_in_interface)
        return energy


    def generate_component_ERT(self, component_info, is_primitive_class):
        """
        According to component type, processes the received information differently

        primitive component:
            - base case of this function
            - apply default attributes, directly chooses the best estimator and generates ERT

        compound component: parse the subcomponet information and evaluate the ERT for the subcomponent actions first

            - top-level compound component with actions
                1. no argument, generate for the action by parsing its defintion and recursively call this function
                2. argument ranges: generate energy/action for one possible argument value(s) a time,
                                    and loops through all the possibilities

            - low-level compound components
              1. no argument, generate for the action by parsing its defintion and recursively call this function
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
            compound_class_description = self.compound_class_description[compound_class_name]

            if 'subcomponents' not in compound_class_description:
                ERROR_CLEAN_EXIT('compound class description missing subcomponents:', compound_class_name)

            defined_component = self.replace_placeholders_construct_compound_component_definition(component_info)

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
        subaction_ERT = self.generate_component_ERT(subcomponent_info, is_subcomponent_primitive_class)
        # the call is guaranteed to produce an ERT with 'energy' and 'argument' key
        subaction_energy = subaction_ERT[subaction_copy['name']]['energy']
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
                op_type, op1, op2 = EnergyReferenceTableGenerator.parse_expression_for_arithmetic(action['repeat'], upper_level_binding)
                if op_type is not None:
                    parsed_repeat = EnergyReferenceTableGenerator.process_arithmetic(op1, op2, op_type)

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
            op_type, op1, op2 = self.parse_expression_for_arithmetic(split_sub_string[0], attributes_dict)
            if op_type is not None:
                start_idx = self.process_arithmetic(op1, op2, op_type)
            else:
                if split_sub_string[0] not in attributes_dict:
                    ERROR_CLEAN_EXIT('cannot find mapping from', arg_range_str, 'to', attributes_dict)
                start_idx = attributes_dict[split_sub_string[0]]
            detect_arg_range_binding = True

        # process the end index
        try:
            end_idx = int(split_sub_string[1])
        except ValueError:
            op_type, op1, op2 = self.parse_expression_for_arithmetic(split_sub_string[1], attributes_dict)
            if op_type is not None:
                end_idx = self.process_arithmetic(op1, op2, op_type)
            else:
                if split_sub_string[1] not in attributes_dict:
                    ERROR_CLEAN_EXIT('cannot find mapping from', arg_range_str, 'to', attributes_dict)
                end_idx = attributes_dict[split_sub_string[1]]
            detect_arg_range_binding = True

        new_arg_range_str = str(start_idx) + '..' + str(end_idx)

        return new_arg_range_str, detect_arg_range_binding

    def replace_placeholders_construct_compound_component_definition(self, compound_component_info):
        """
        given the physical information of a compound component, the compound component object is constructed according
        to its compound classes, all compound properties are fully resolved and subcomponent definitions are included
        1. compound attributes are all assigned with values
        2. compound action argument ranges are all assigned values/ compound action arguments are static values
        3. subcomponent attributes values are assigned, as they only depend on compound attributes
            - subcomponent attributes can be:
                1. numbers
                2. string bindings to compound component attributes
                3. arithmetic operations that contain string bindings and numbers
        3. subcomponent definition of the compound actions are included

        :param compound_component_info: physical specification of a compound component
        :return: fully defined compound component
        """
        compound_component_name = compound_component_info['name']
        compound_class_info = self.compound_class_description[compound_component_info['class']]
        compound_component_definition = deepcopy(compound_class_info)  # a copy of default class definition
        compound_component_definition['class'] = compound_component_info['class']
        compound_component_definition['attributes'] = deepcopy(compound_component_info['attributes'])

        # apply the physical compound attribute values (parsing of the architecture should already fulfilled
        # the values of all attributes needed by the class, either default or redefined by the architecture)
        compound_attributes = compound_component_definition['attributes'] # fully defined attribute values



        # process subcomponent name format
        #     if subcomponent is a list, expand the list of subcomponents (list tail index can be arithmetic operantions)
        #     else keep the subcomponent name

        subcomponents = deepcopy(compound_component_definition['subcomponents'])

        list_of_new_components = []
        list_of_to_remove_components = []

        for subcomponent_idx in range(len(subcomponents)):
            subcomponent = subcomponents[subcomponent_idx]
            list_length, subcomponent_name_base = EnergyReferenceTableGenerator.is_component_list(subcomponent['name'], compound_attributes)
            if subcomponent_name_base is not None:
                list_of_to_remove_components.append(subcomponent)
                INFO('list component name: ', subcomponent['name'], 'detected in compound class: ', compound_component_info['class'])
                for i in range(list_length):
                    new_component = deepcopy(subcomponent)
                    new_component['name']  = subcomponent_name_base + '[' + str(i) + ']'
                    list_of_new_components.append(new_component)
        for comp in list_of_to_remove_components:
            subcomponents.remove(comp)
        for comp in list_of_new_components:
            subcomponents.append(comp)

        # process the subcomponent attribute values
        # subcomponent attributes can be:
        #     1. numbers
        #     2. string bindings to compound component attributes
        #     3. arithmetic operations that contain string bindings and numbers
        compound_component_definition['subcomponents'] = {}
        for subcomponent in subcomponents:
            subcomponent_name = subcomponent['name']
            sub_component_attributes = subcomponent['attributes']
            for sub_attr_name, sub_attr_val in sub_component_attributes.items():
                if type(sub_attr_val) is str:
                    # subcomponent attributes can be computed in terms of upper-level compound attributes
                    op_type, op1, op2 = EnergyReferenceTableGenerator.parse_expression_for_arithmetic(sub_attr_val, compound_attributes)
                    if op_type is not None:
                        sub_component_attributes[sub_attr_name] = EnergyReferenceTableGenerator.process_arithmetic(op1, op2, op_type)
                        # INFO(compound_component_name, 'sub-attribute', sub_attr_name, 'processed as arithmetic operation')
                    else:
                        try:
                            sub_component_attributes[sub_attr_name] = compound_attributes[sub_attr_val]
                            # INFO(compound_component_name, 'sub-attribute', sub_attr_name,'processed as binding')
                        except KeyError:
                            ERROR_CLEAN_EXIT('cannot find bindings from upper-level attribute names',
                                             '{',sub_attr_name, ':', sub_attr_val, '}')
            compound_component_definition['subcomponents'][subcomponent_name] = subcomponent

        # top-level compound component will not have 'actions' specified in the component info
        #      because accelergy needs to generate the energy values for all possible actions (and arguments)
        # the actions in the component class description is therefore processed
        #     action arguments can be:
        #             1. numbers
        #             2. string bindings to compound attributes (its own attributes)
        #     action arguments cannot be arithmetic operations
        if 'actions' not in compound_component_info:
            # if there is no actions specified in the compound component info
            compound_actions = compound_component_definition['actions']
            for c_action in compound_actions:
                c_action_name = c_action['name']
                if 'arguments' in c_action:
                    c_action_args = c_action['arguments']
                    for c_action_arg_name, c_action_arg_range in c_action_args.items():
                        c_action_args[c_action_arg_name], detect_arg_range_binding = \
                            self.map_arg_range_bounds(c_action_arg_range, compound_attributes)
                        if detect_arg_range_binding:
                            INFO(compound_component_name, 'action:', c_action_name, 'arg:', c_action_arg_name,
                                 'range interpreted as:', c_action_args[c_action_arg_name])

        # low-level compound components will have 'actions' assigned, since top-level action will be interpreted as
        # one or more defined low-level compound action
        #     no change should be added as the action arguments should be defined already, so the required action list
        #     from component info is copied, with the definition of the action retried from class description
        else:
            compound_component_definition['actions'] = deepcopy(compound_component_info['actions'])
            for action in compound_component_definition['actions']:
                action_name = action['name']
                for class_action_def in compound_class_info['actions']:
                    if class_action_def['name'] == action_name:
                        action['subcomponents'] = deepcopy(class_action_def['subcomponents'])


        return compound_component_definition


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

    def expand_primitive_component_lib_info(self, pc_path):
        """
         Processes the primitive component library files and add the primitive components to Accelergy
        :param pc_path: path that the primitive component lib is at
        :return: None
        """
        primitive_component_list = load(open(pc_path), accelergy_loader)
        syntax_validators.validate_primitive_classes(primitive_component_list)
        for idx in range(len(primitive_component_list['classes'])):
            pc_name = primitive_component_list['classes'][idx]['name']
            if pc_name in self.primitive_class_description:
                WARN(pc_name, 'redefined in', pc_path)
            self.primitive_class_description[pc_name] = primitive_component_list['classes'][idx]
        INFO('primitive component file parsed: ', pc_path)

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
                            self.expand_primitive_component_lib_info(root + os.sep + file_name)

    def construct_compound_class_description(self, compound_class_list):
        """
        checks if there are duplicated compound component class names
        expand the subcomponent list into multiple subcompounents (if there is any)
        :param compound_class_list: list of compound classes that need parsing
        :return: None (self.compound_class_description is updated)
        """
        if 'version' not in compound_class_list:
            ERROR_CLEAN_EXIT('please specify the version of parser your input format adheres to using '
                             '"version" key at top level')

        for idx in range(len(compound_class_list['classes'])):
            compound_class_name = compound_class_list['classes'][idx]['name']
            if compound_class_name in self.compound_class_description:
                ERROR_CLEAN_EXIT('duplicate compound class name in component class description,',
                                 'error class name', compound_class_name)
            self.compound_class_description[compound_class_name] = compound_class_list['classes'][idx]

            try:
                subcomponents = self.compound_class_description[compound_class_name]['subcomponents']
            except KeyError:
                subcomponents = None
                ERROR_CLEAN_EXIT('compound classes must have "subcomponents" key to specify the lower-level details',
                                  'error class name: ', compound_class_name)

            # list_of_new_components = []
            # list_of_to_remove_components = []
            #
            # for subcomponent_idx in range(len(subcomponents)):
            #     subcomponent = subcomponents[subcomponent_idx]
            #     list_length, subcomponent_name_base = EnergyReferenceTableGenerator.is_component_list(subcomponent['name'])
            #     if subcomponent_name_base is not None:
            #         list_of_to_remove_components.append(subcomponent)
            #         INFO('list component name: ', subcomponent['name'], 'detected in compound class: ', compound_class_name)
            #         for i in range(list_length):
            #             new_component = deepcopy(subcomponent)
            #             new_component['name']  = subcomponent_name_base + '[' + str(i) + ']'
            #             list_of_new_components.append(new_component)
            # for comp in list_of_to_remove_components:
            #     subcomponents.remove(comp)
            # for comp in list_of_new_components:
            #     subcomponents.append(comp)



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


    def locate_config(self):
        """
        Search for accelerg_config.yaml in ./ and $HOME/.config/accelergy
        if not found, create default at $HOME/.config/accelergy/accelergy_config.yaml
        Default config file contains the path to the default estimator and  primitive component library
        """
        possible_config_dirs = ['.' + os.sep, os.path.expanduser('~') + '/.config/accelergy/']
        config_file_name = 'accelergy_config.yaml'
        self.config = None
        for possible_dir in possible_config_dirs:
            if os.path.exists(possible_dir + config_file_name):
                self.config = load(open(possible_dir + config_file_name), accelergy_loader)
                INFO('config file located:', possible_dir + config_file_name)
                break

        if self.config is None:
            create_folder(possible_config_dirs[1])
            this_dir, this_filename = os.path.split(__file__)
            default_estimator_path = os.path.abspath(os.path.join(this_dir, '../../../../share/accelergy/estimation_plug_ins/'))
            default_pc_lib_path = os.path.abspath(os.path.join(this_dir, '../../../../share/accelergy/primitive_component_libs/'))
            config_file_content = {'version': 0.1,
                                   'estimator_plug_ins': [default_estimator_path],
                                   'primitive_components': [default_pc_lib_path]}

            config_file_path = possible_config_dirs[1] + config_file_name
            INFO('Accelergy creating default config at:', possible_config_dirs[1] + config_file_name, 'with:', config_file_content)
            write_yaml_file(config_file_path, config_file_content)
            self.config = config_file_content

    def generate_ERTs(self, design_path, output_path, precision):
        """
        main function to start the energy reference generator
        parses the input files
        produces the energy reference tables for components
        """
        print('\n=========================================')
        print('Generating energy reference tables')
        print('=========================================')

        # ------------------------------------------------------------------------------
        # Load accelergy config and design specification
        # ------------------------------------------------------------------------------
        self.locate_config()
        self.design = load(open(design_path), accelergy_loader)
        INFO('design loaded:', design_path)
        self.output_path    = output_path
        self.construct_compound_class_description(self.design['compound_components'])
        self.decimal_place  = precision

        # load in the primitive classes (static) in the library
        self.construct_primitive_class_description()

        # ------------------------------------------------------------------------------
        # Parse the architecture description and save the parsed version
        # ------------------------------------------------------------------------------
        self.construct_save_architecture_description(self.design['architecture'])

        # ------------------------------------------------------------------------------
        # Generate Energy Reference Tables for the components
        # ------------------------------------------------------------------------------
        self.instantiate_estimator_plug_ins()
        for component_name, component_info in self.architecture_description.items():
            component_info['name'] = component_name
            ERT_check_result = self.ERT_existed(component_name)
            if not ERT_check_result[0]:
                is_primitive_class = True if self.is_primitive_class(component_info['class']) else False
                ERT = self.generate_component_ERT(component_info, is_primitive_class)
                self.energy_reference_table[ERT_check_result[1]] = ERT

        ERT_file_path = self.output_path + '/' + 'ERT.yaml'
        write_yaml_file(ERT_file_path, self.energy_reference_table)
        print('---> Finished: ERT generation finished, ERT saved to:\n', os.path.abspath(output_path))