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
from accelergy.parsing_utils import *
class CompoundComponent:
    def __init__(self, def_info):
        arch_component = def_info['component']
        pc_classes = def_info['pc_classes']
        cc_classes = def_info['cc_classes']

        self.name = arch_component.get_name()
        self.class_name = arch_component.get_class_name()
        self.attributes = arch_component.get_attributes()
        self._primitive_type = cc_classes[self.class_name].get_primitive_type()
        self._subcomponents = {}
        self.all_possible_subcomponents = {}
        self.subcomponent_base_name_map = {}
        self._actions = []
        self.set_subcomponents(cc_classes, pc_classes)
        self.flatten_action_list(cc_classes)

    def get_class_name(self):
        return self.class_name

    def get_name(self):
        return self.name

    def get_attributes(self):
        return self.attributes

    def get_actions(self):
        return self._actions

    def get_subcomponents(self):
        return self._subcomponents

    def get_primitive_type(self):
        return self._primitive_type

    def set_subcomponents(self, cc_classes, pc_classes):
        self.all_possible_subcomponents[self.name] = self
        list_of_defined_primitive_components = self.process_subcomponents(self, cc_classes, pc_classes)
        for primitive_comp in list_of_defined_primitive_components:
            self._subcomponents[primitive_comp.get_name()] = primitive_comp
        self.construct_name_base_name_map()

    def process_subcomponents(self, component, cc_classes, pc_classes):
        """ generate a list of primitive subcomponents of a compound component"""

        list_of_primitive_components = []
        component_class = cc_classes[component.get_class_name()]
        compound_attributes = component.get_attributes()
        subcomponents = deepcopy(component_class.get_subcomponents_as_dict())
        for default_sub_name, subcomponent in subcomponents.items():
            defined_sub_name = CompoundComponent.define_subcomponent_name(default_sub_name, compound_attributes)
            subcomponent.set_name(defined_sub_name)
        # process the subcomponent attribute values, subcomponent attributes can be:
        #     1. numbers
        #     2. string bindings to/arithmetic operations of compound component attributes
        # default sub-component-component attribute values that are not specified in the top-level, default values can be :
        #     1. numbers
        #     2. bindings/arithmetic operations of other sub-compound-component attribute values
        for subname, subcomponent in subcomponents.items():
            # create nested name for subcomponents
            subname = component.get_name() + '.' + subcomponent.get_name() if component is not self \
                                                                           else subcomponent.get_name()
            subcomponent.set_name(subname)
            subclass_name = subcomponent.get_class_name()
            sub_class_type = 'compound' if subclass_name in cc_classes else 'primitive'
            if sub_class_type == 'compound':
                subclass_def = cc_classes[subclass_name]
                defined_subcomponent = CompoundComponent.define_attrs_area_share_for_subcomponent(subcomponent, compound_attributes, subclass_def)
                list_of_new_defined_primitive_components = self.process_subcomponents(defined_subcomponent, cc_classes, pc_classes)
                for new_defined_pc in list_of_new_defined_primitive_components:
                    list_of_primitive_components.append(new_defined_pc)
            else:
                subclass_def = pc_classes[subclass_name]
                defined_subcomponent = CompoundComponent.define_attrs_area_share_for_subcomponent(subcomponent, compound_attributes, subclass_def)
                list_of_primitive_components.append(defined_subcomponent)
            self.all_possible_subcomponents[subname] = defined_subcomponent

        return list_of_primitive_components


    def flatten_action_list(self, cc_classes):
        top_level_action_list = self.flatten_top_level_action_list(cc_classes[self.get_class_name()])
        for action_idx in range(len(top_level_action_list)):
            primitive_list = self.flatten_action_list_for_an_action(self.get_name(),
                                                                    top_level_action_list[action_idx],
                                                                    cc_classes)
            top_level_action_list[action_idx].set_primitive_list(primitive_list)
        self._actions = top_level_action_list


    def flatten_action_list_for_an_action(self, component_name, action, cc_classes):
        list_of_primitive_actions = []
        # 1. expand the list of subcomponents in the action (subcomponent name can be in list format)
        # 2. rename each subcomponent with hierarchical name
        # 3. define the range of the arguments of each subcomponent action
        # 4. if the action is a compound action -> go to 1
        #    if the action is a primitive action -> throw it in the list
        action_copy = deepcopy(action)
        subcomponent_actions = action_copy.get_subcomps() # subcomponent_name: list of action objects
        compound_attributes = self.find_subcomponent_obj(component_name).get_attributes()
        compound_arguments = action.get_arguments()
        aggregated_mappings = deepcopy(compound_attributes) if compound_arguments is None \
                              else merge_dicts(compound_attributes, compound_arguments)

        for subcomp_name, action_obj_list in subcomponent_actions.items():
            # make sure the top-level component name is not added as prefix
            if not component_name == self.get_name():
                defined_subcomp_name = component_name + '.' + CompoundComponent.define_subcomponent_name(subcomp_name, aggregated_mappings)
            else:
                defined_subcomp_name = CompoundComponent.define_subcomponent_name(subcomp_name, aggregated_mappings)

            subclass_name = self.find_subcomponent_obj(defined_subcomp_name).get_class_name()
            subcomponent_class_type = 'compound' if subclass_name in cc_classes else 'primitive'
            defined_action_obj_list = CompoundComponent.define_subactions(action_obj_list, aggregated_mappings)
            for subaction in defined_action_obj_list:
                if subcomponent_class_type == 'primitive':
                    list_of_primitive_actions.append((defined_subcomp_name, subaction))
                else:
                    default_subcomp_actions = deepcopy(cc_classes[subclass_name].get_action(subaction.get_name()).get_subcomps())
                    subaction.set_subcomps(default_subcomp_actions)
                    new_list_of_primitive_actions = self.flatten_action_list_for_an_action(defined_subcomp_name, subaction, cc_classes)
                    for new_primitive_action in new_list_of_primitive_actions:
                        list_of_primitive_actions.append(new_primitive_action)
        return list_of_primitive_actions

    @staticmethod
    def define_subactions(subactions, aggregated_dict):
        defined_subactions = []
        for subaction in subactions:
            parsed_action_share = CompoundComponent.parse_action_share(subaction, aggregated_dict)
            subaction.set_action_share(parsed_action_share)
            if subaction.get_arguments() is not None:
                for subarg_name, subarg_val in subaction.get_arguments().items():
                    if type(subarg_val) is str:
                        try:
                            subaction.set_argument({subarg_name: aggregated_dict[subarg_val]})
                        except KeyError:
                            op_type, op1, op2 = parse_expression_for_arithmetic(subarg_val, aggregated_dict)
                            if op_type is not None:
                                subaction.set_argument({subarg_name: process_arithmetic(op1, op2, op_type)})
                            else:
                                print('available compound arguments and attributes: ', aggregated_dict)
                                print('primitive argument to for binding:', subarg_val)
                                ERROR_CLEAN_EXIT('subcomponent argument name cannot be ',
                                                 'mapped to upper class arguments', subarg_val)
            defined_subactions.append(subaction)
        return defined_subactions

    @staticmethod
    def parse_action_share(action, upper_level_binding):
        """
        evaluates the values of action_share of a sub-component action
        - default value of action_share is 1
        - string bindings are allowed, and bindings can be from:
            1. compound attributes
            2. compound action arguments (its own upper-level action)
        - arithemtic operations are allowed in specifying action_share value

        """
        action_share = action.get_action_share()
        if action_share is not None:
            if type(action_share) is not int:
                op_type, op1, op2 = parse_expression_for_arithmetic(action_share, upper_level_binding)
                if op_type is not None:
                    parsed_action_share = process_arithmetic(op1, op2, op_type)
                else:
                    if action_share in upper_level_binding:
                       parsed_action_share = upper_level_binding[action_share]
                    else:
                        parsed_action_share = None
                        ERROR_CLEAN_EXIT('action_share/repeat value for primitive action cannot be parsed, ',
                                      'no binding found in compound arguments/ attributes',action,
                                         'available binding:', upper_level_binding)
                return parsed_action_share
            # return the actual value if action_share is an integer
            return action_share
        # default action_share value is 1
        return 1

    def flatten_top_level_action_list(self, component_class):
        actionNameList = component_class.get_action_name_list()
        flattenedActionList = []
        for actionName in actionNameList:
            actionObj = deepcopy(component_class.get_action(actionName))
            flattened = actionObj.flatten_action_args_into_list(self.attributes)
            for action in flattened:
                flattenedActionList.append(action)
        return flattenedActionList

    @staticmethod
    def define_subcomponent_name(subcomponent_name, mapping_dictionary):
        # define the list index specified in the subcomponents (if any)
        # mapping dictionary contains key-value paris where the keys can be used as reference in the list definition

        name_base, list_suffix, list_length = interpret_component_list(subcomponent_name, mapping_dictionary)
        if list_suffix is not None: subcomponent_name = name_base + list_suffix
        return subcomponent_name


    @staticmethod
    def define_attrs_area_share_for_subcomponent(subcomponent, compound_attributes, subclass):
        for attr_name, attr_val in subcomponent.get_attributes().items():
            if type(attr_val) is str:
                if attr_val in compound_attributes:
                    subcomponent.add_new_attr({attr_name: compound_attributes[attr_val]})
                else:
                    op_type, op1, op2 = parse_expression_for_arithmetic(attr_val, compound_attributes)
                    if op_type is not None:
                        subcomponent.add_new_attr({attr_name: process_arithmetic(op1, op2, op_type)})
        attrs_to_be_applied = subclass.get_default_attr_to_apply(subcomponent.get_attributes())
        subcomponent.add_new_attr(attrs_to_be_applied)
        CompoundComponent.apply_internal_bindings(subcomponent)
        if type(subcomponent.get_area_share()) is str:
            combined_attributes = merge_dicts(compound_attributes, subcomponent.get_attributes())
            op_type, op1, op2 = parse_expression_for_arithmetic(subcomponent.get_area_share(), combined_attributes)
            if op_type is not None:
                subcomponent.set_area_share(process_arithmetic(op1,op2, op_type))
            else:
                ASSERT_MSG(subcomponent.get_area_share() in combined_attributes,
                           'Unable to interpret the area share for subcomponent: %s' %(subcomponent.get_name()))
                subcomponent.set_area_share(combined_attributes[subcomponent.get_area_share()])
        return subcomponent

    @staticmethod
    def apply_internal_bindings(component):
        """ Locate and process any mappings or arithmetic operations between the component attributes"""

        for attr_name, attr_val in component.get_attributes().items():
            if type(attr_val) is str:
                if attr_val in component.get_attributes():
                    component.add_new_attr({attr_name: component.get_attributes()[attr_val]})
                else:
                    op_type, op1, op2  = parse_expression_for_arithmetic(attr_val, component.get_attributes())
                    if op_type is not None: component.add_new_attr({attr_name:process_arithmetic(op1, op2, op_type)})

    def construct_name_base_name_map(self):
        self.subcomponent_base_name_map = {}
        for subname in self.all_possible_subcomponents:
            sub_base_name = remove_brackets(subname)
            self.subcomponent_base_name_map[sub_base_name] = subname

    def find_subcomponent_obj(self, subcomponent_name):
        """ find the corresponding subcomponent def to retrieve the action-related information"""

        subcomponent_base_name = remove_brackets(subcomponent_name)
        ASSERT_MSG(self.subcomponent_base_name_map[subcomponent_base_name] in self.all_possible_subcomponents,
                   'subcomponent: %s not found'%(self.subcomponent_base_name_map[subcomponent_base_name]))
        subcomp_obj = self.all_possible_subcomponents[self.subcomponent_base_name_map[subcomponent_base_name]]
        ASSERT_MSG(comp_name_within_range(subcomponent_name, subcomp_obj.get_name()),
                   'subcompnent name %s in action definition does not have a valid index (should be a subset of %s)'
                   %(subcomponent_name, subcomp_obj.get_name()))
        return subcomp_obj



    # ------------ CONVERSION TO DICTS for BETTER OUTPUTS FUNCTIONS ------------#
    def get_subcomponents_as_dict(self):
        subcomp_dict = {}
        for sub_name, sub_obj in self._subcomponents.items():
            subcomp_dict[sub_name] = {'class': sub_obj.get_class_name(),
                                      'attributes': sub_obj.get_attributes(),
                                      'area_share': sub_obj.get_area_share()}
        return subcomp_dict

    def get_dict_representation(self):
        """ Generate the information of the component component in a dictionary format
            including: (1) attributes (2) class (2) flattened primitive list (2) flattened actions
        """

        from collections import OrderedDict
        cc_dict = OrderedDict()

        subcomponent_dict = self.get_subcomponents_as_dict()
        subcomponent_list = []
        for subcomp_name, subcomp_info_dict in subcomponent_dict.items():
            new_info_dict = OrderedDict({'name': subcomp_name})
            new_info_dict.update(subcomp_info_dict)
            subcomponent_list.append(new_info_dict)

        cc_dict.update({'name': self.get_name(),
                        'class': self.get_class_name(),
                        'attributes': self.get_attributes(),
                        'primitive_components': subcomponent_list,
                        'actions': []})
        idx = 0
        for action in self._actions:
            cc_dict['actions'].append(OrderedDict({'name': action.get_name(),
                                                   'arguments': action.get_arguments(),
                                                   'primitive_actions': []}))
            for pc_action_tuple in action.get_primitive_list():
                cc_dict['actions'][idx]['primitive_actions'].append(
                    OrderedDict({'name': pc_action_tuple[0],
                                 'action': pc_action_tuple[1].get_name(),
                                 'arguments': pc_action_tuple[1].get_arguments(),
                                 'action_share': pc_action_tuple[1].get_action_share()}))
            idx = idx + 1
        return cc_dict
