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

from copy import deepcopy
import functools
from accelergy.utils import ERROR_CLEAN_EXIT, INFO, WARN, register_function
from accelergy.v02_functions.v02_shared_functions import v02_is_component_list
from accelergy.arithmetic_parsers import  parse_expression_for_arithmetic, process_arithmetic

# list to store the functions that need to added to ERT generator class
functions = []
register_function = functools.partial(register_function, functions)

@register_function
def v02_compound_component_constructor(self, compound_component_info):
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

    # fully defined attribute values
    compound_attributes = compound_component_definition['attributes']

    # process subcomponent name format
    #     if subcomponent is a list, expand the list of subcomponents (list tail index can be arithmetic operantions)
    #     else keep the subcomponent name

    subcomponents = deepcopy(compound_component_definition['subcomponents'])
    # check if any sub-compound-component attribute is not specified in the top-level, apply defualt value specified
    # in the class definition


    list_of_new_components = []
    list_of_to_remove_components = []

    for subcomponent_idx in range(len(subcomponents)):
        subcomponent = subcomponents[subcomponent_idx]
        list_length, subcomponent_name_base = v02_is_component_list(subcomponent['name'], compound_attributes)
        if subcomponent_name_base is not None:
            list_of_to_remove_components.append(subcomponent)
            # INFO('list component name: ', subcomponent['name'], 'detected in compound class: ', compound_component_info['class'])
            for i in range(list_length):
                new_component = deepcopy(subcomponent)
                new_component['name'] = subcomponent_name_base + '[' + str(i) + ']'
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
                op_type, op1, op2 = parse_expression_for_arithmetic(sub_attr_val, compound_attributes)
                if op_type is not None:
                    sub_component_attributes[sub_attr_name] = process_arithmetic(op1, op2, op_type)
                    # INFO(compound_component_name, 'sub-attribute', sub_attr_name, 'processed as arithmetic operation')
                else:
                    try:
                        sub_component_attributes[sub_attr_name] = compound_attributes[sub_attr_val]
                        # INFO(compound_component_name, 'sub-attribute', sub_attr_name,'processed as binding')
                    except KeyError:
                        ERROR_CLEAN_EXIT('cannot find bindings from upper-level attribute names',
                                         '{', sub_attr_name, ':', sub_attr_val, '}')
        # process default sub-component-component attribute values that are not specified in the top-level
        # default values can be :
        #   (1) numerical values
        #   (2) arithmetic operations of other sub-compound-component attribute values
        sub_class = subcomponent['class']
        if sub_class in self.compound_class_description:
            sub_class_description = deepcopy(self.compound_class_description[sub_class])
            for attr_name, default_attr_val in sub_class_description['attributes'].items():
                if attr_name not in subcomponent['attributes']:
                    if type(default_attr_val) is str:
                        op_type, op1, op2 = parse_expression_for_arithmetic(default_attr_val,
                                                                            subcomponent['attributes'])
                        if op_type is not None:
                            default_attr_val = process_arithmetic(op1, op2, op_type)
                            # INFO(compound_component_name, 'sub-attribute', sub_attr_name, 'processed as arithmetic operation')
                        else:
                            try:
                                default_attr_val = subcomponent['attributes'][default_attr_val]
                                # INFO(compound_component_name, 'sub-attribute', sub_attr_name,'processed as binding')
                            except KeyError:
                                WARN('did not find bindings of the specified default attribute value for class: ',
                                    sub_class, '---> {', attr_name, ':', default_attr_val, '}, '
                                    '   Keep the original specifications')
                    subcomponent['attributes'][attr_name] = default_attr_val
        compound_component_definition['subcomponents'][subcomponent_name] = subcomponent
        # check if the subcomponent name is a list
        # list_length, name_base = v02_is_component_list(subcomponent_name, compound_attributes)
        # if subcomponent_name == 'Y_memory_controller[0..total_PEs-1]':
        #     print('----------------------', list_length, name_base)
        # if name_base is None:
        #     compound_component_definition['subcomponents'][subcomponent_name] = subcomponent
        # else:
        #     for item_idx in range(list_length):
        #         new_subcomponent_name = name_base + '[' + str(item_idx) + ']'
        #         compound_component_definition['subcomponents'][new_subcomponent_name] = deepcopy(subcomponent)

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
    #     from component info is copied, with the definition of the action retrieved from class description
    else:
        compound_component_definition['actions'] = deepcopy(compound_component_info['actions'])
        for action in compound_component_definition['actions']:
            action_name = action['name']
            for class_action_def in compound_class_info['actions']:
                if class_action_def['name'] == action_name:
                    action['subcomponents'] = deepcopy(class_action_def['subcomponents'])
    return compound_component_definition

@register_function
def v02_check_subcomponent_name_in_action_def(self, action_def, subcomponent_names, compound_attributes):
    returned_action_def = deepcopy(action_def)
    new_subcomponents = deepcopy(action_def['subcomponents'])
    for sub_component in returned_action_def['subcomponents']:
        sub_cname = sub_component['name']
        # check if the subcomponent name is a list
        list_length, name_base = v02_is_component_list(sub_cname, compound_attributes)
        if list_length == -1:
           new_subcomponents.remove(sub_component)
           # WARN(sub_cname, ' in "', returned_action_def['name'],
           #      '" interpreted as negative list length --> subcomponent ignored')
        elif name_base is not None:
            new_subcomponents.remove(sub_component)
            for item_idx in range(list_length):
                new_sub_cname = name_base + '[' + str(item_idx) + ']'
                new_sub_comp = deepcopy(sub_component)
                new_sub_comp['name'] = new_sub_cname
                new_subcomponents.append(new_sub_comp)
                if new_sub_cname not in subcomponent_names:
                    ERROR_CLEAN_EXIT('v0.2 error: compound class description...\n',
                                     'Cannot parse action "%s"\n'% returned_action_def['name'],
                                     'Cannot find "%s" in compound component definition'%new_sub_cname )
        else:
            if sub_cname not in subcomponent_names:
                ERROR_CLEAN_EXIT('v0.2 error: compound class description...\n',
                                 'Cannot parse action "%s"\n' % returned_action_def['name'],
                                 'Cannot find "%s" in compound component definition' % sub_cname)
    returned_action_def['subcomponents'] = new_subcomponents
    return returned_action_def