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
from accelergy.component_class import ComponentClass


class CompoundComponent:
    def __init__(self, def_info):
        arch_component = def_info["component"]
        pc_classes = def_info["pc_classes"]
        cc_classes = def_info["cc_classes"]

        self.name = arch_component.get_name()
        self.class_name = arch_component.get_class_name()
        self.attributes = arch_component.get_attributes()
        self.area_scale = arch_component.get_area_scale()
        self.energy_scale = arch_component.get_energy_scale()
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
        list_of_defined_primitive_components = self.process_subcomponents(
            self, cc_classes, pc_classes
        )
        for primitive_comp in list_of_defined_primitive_components:
            self._subcomponents[primitive_comp.get_name()] = primitive_comp
        self.construct_name_base_name_map()

    def process_subcomponents(self, component, cc_classes, pc_classes):
        """generate a list of primitive subcomponents of a compound component"""

        list_of_primitive_components = []
        component_class = cc_classes[component.get_class_name()]
        compound_attributes = component.get_attributes()
        subcomponents = deepcopy(component_class.get_subcomponents_as_dict())
        for default_sub_name, subcomponent in subcomponents.items():
            defined_sub_name = CompoundComponent.define_subcomponent_name(
                default_sub_name, compound_attributes
            )
            subcomponent.set_name(defined_sub_name)

        my_area_scale = self.process_area_scale(
            self.area_scale, compound_attributes, f"{self.name}.area_scale"
        )
        self.area_scale = my_area_scale
        my_energy_scale = self.process_area_scale(
            self.energy_scale, compound_attributes, f"{self.name}.energy_scale"
        )
        self.energy_scale = my_energy_scale
        # process the subcomponent attribute values, subcomponent attributes can be:
        #     1. numbers
        #     2. string bindings to/arithmetic operations of compound component attributes
        # default sub-component-component attribute values that are not specified in the top-level, default values can be :
        #     1. numbers
        #     2. bindings/arithmetic operations of other sub-compound-component attribute values
        for subname, subcomponent in subcomponents.items():
            # create nested name for subcomponents
            subname = (
                component.get_name() + "." + subcomponent.get_name()
                if component is not self
                else subcomponent.get_name()
            )
            subcomponent.set_name(subname)
            subclass_name = subcomponent.get_class_name()
            sub_class_type = "compound" if subclass_name in cc_classes else "primitive"
            if sub_class_type == "compound":
                subclass_def = cc_classes[subclass_name]
                defined_subcomponent = self.define_attrs_area_scale_for_subcomponent(
                    subcomponent, compound_attributes, subclass_def
                )
                list_of_new_defined_primitive_components = self.process_subcomponents(
                    defined_subcomponent, cc_classes, pc_classes
                )
                cc_area_scale = defined_subcomponent.get_area_scale()
                cc_energy_scale = defined_subcomponent.get_energy_scale()
                for new_defined_pc in list_of_new_defined_primitive_components:
                    new_defined_pc.set_area_scale(
                        new_defined_pc.get_area_scale() * cc_area_scale
                    )
                    new_defined_pc.set_energy_scale(
                        new_defined_pc.get_energy_scale() * cc_energy_scale
                    )
                    list_of_primitive_components.append(new_defined_pc)
            else:
                if subclass_name not in pc_classes:
                    pc_classes[subclass_name] = ComponentClass(
                        {
                            "name": subcomponent.get_class_name(),
                            "attributes": {},
                            "actions": [],
                        }
                    )
                subclass_def = pc_classes[subclass_name]
                defined_subcomponent = self.define_attrs_area_scale_for_subcomponent(
                    subcomponent, compound_attributes, subclass_def
                )
                defined_subcomponent.set_area_scale(
                    defined_subcomponent.get_area_scale() * my_area_scale
                )
                defined_subcomponent.set_energy_scale(
                    defined_subcomponent.get_energy_scale() * my_energy_scale
                )
                list_of_primitive_components.append(defined_subcomponent)
            self.all_possible_subcomponents[subname] = defined_subcomponent

        return list_of_primitive_components

    def flatten_action_list(self, cc_classes):
        top_level_action_list = self.flatten_top_level_action_list(
            cc_classes[self.get_class_name()]
        )
        for action_idx in range(len(top_level_action_list)):
            primitive_list = self.flatten_action_list_for_an_action(
                self.get_name(), top_level_action_list[action_idx], cc_classes
            )
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
        # subcomponent_name: list of action objects
        subcomponent_actions = action_copy.get_subcomps()
        compound_attributes = self.find_subcomponent_obj(
            component_name
        ).get_attributes()
        compound_arguments = action.get_arguments()
        aggregated_mappings = (
            deepcopy(compound_attributes)
            if compound_arguments is None
            else merge_dicts(compound_attributes, compound_arguments)
        )

        energy_scale = action.get_energy_scale()
        if energy_scale is None:
            energy_scale = 1.0

        for subcomp_name, action_obj_list in subcomponent_actions.items():
            # make sure the top-level component name is not added as prefix
            if not component_name == self.get_name():
                defined_subcomp_name = (
                    component_name
                    + "."
                    + CompoundComponent.define_subcomponent_name(
                        subcomp_name, aggregated_mappings
                    )
                )
            else:
                defined_subcomp_name = CompoundComponent.define_subcomponent_name(
                    subcomp_name, aggregated_mappings
                )

            subclass_name = self.find_subcomponent_obj(
                defined_subcomp_name
            ).get_class_name()
            subcomponent_class_type = (
                "compound" if subclass_name in cc_classes else "primitive"
            )
            defined_action_obj_list = self.define_subactions(
                action, action_obj_list, aggregated_mappings, energy_scale
            )
            for subaction in defined_action_obj_list:
                if subcomponent_class_type == "primitive":
                    list_of_primitive_actions.append((defined_subcomp_name, subaction))
                else:
                    default_subcomp_actions = deepcopy(
                        cc_classes[subclass_name]
                        .get_action(subaction.get_name())
                        .get_subcomps()
                    )
                    subaction.set_subcomps(default_subcomp_actions)
                    new_list_of_primitive_actions = (
                        self.flatten_action_list_for_an_action(
                            defined_subcomp_name, subaction, cc_classes
                        )
                    )
                    for new_primitive_action in new_list_of_primitive_actions:
                        list_of_primitive_actions.append(new_primitive_action)
        return list_of_primitive_actions

    def define_subactions(
        self, top_action, subactions, aggregated_dict, upper_level_energy_scale
    ):
        defined_subactions = []
        for subaction in subactions:
            parsed_energy_scale = CompoundComponent.parse_energy_scale(
                subaction, aggregated_dict
            )
            subaction.set_energy_scale(parsed_energy_scale * upper_level_energy_scale)
            subaction._arguments = parse_expressions_sequentially_replacing_bindings(
                subaction.get_arguments(),
                aggregated_dict,
                f"{self.get_name()}.{top_action.get_name()}"
                + f".{subaction.get_name()}.",
                strings_allowed=True,
            )
            defined_subactions.append(subaction)
        return defined_subactions

    @staticmethod
    def parse_energy_scale(action, upper_level_binding):
        """
        evaluates the values of energy_scale of a sub-component action
        - default value of energy_scale is 1
        - string bindings are allowed, and bindings can be from:
            1. compound attributes
            2. compound action arguments (its own upper-level action)
        - arithemtic operations are allowed in specifying energy_scale value

        """
        energy_scale = action.get_energy_scale()
        if energy_scale is not None:
            return parse_expression_for_arithmetic(
                energy_scale,
                upper_level_binding,
                f"action {action.get_name()} energy_scale",
                strings_allowed=False,
            )
        # default energy_scale value is 1
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

        name_base, list_suffix, list_length = interpret_component_list(
            subcomponent_name, mapping_dictionary
        )
        if list_suffix is not None:
            subcomponent_name = name_base + list_suffix
        return subcomponent_name

    def process_area_scale(self, area_scale, combined_attributes, name):
        if area_scale is None:
            return 1.0
        else:
            return parse_expression_for_arithmetic(
                area_scale, combined_attributes, name, strings_allowed=False
            )

    def define_attrs_area_scale_for_subcomponent(
        self, subcomponent, compound_attributes, subclass
    ):
        attrs = parse_expressions_sequentially_replacing_bindings(
            subcomponent.get_attributes(),
            compound_attributes,
            f"{subcomponent.get_name()}.",
            strings_allowed=True,
        )
        subcomponent.add_new_attr(attrs)
        attrs_to_be_applied = subclass.get_default_attr_to_apply(
            subcomponent.get_attributes()
        )
        subcomponent.add_new_attr(attrs_to_be_applied)
        CompoundComponent.apply_internal_bindings(subcomponent, compound_attributes)
        combined_attributes = merge_dicts(
            compound_attributes, subcomponent.get_attributes()
        )
        subcomponent.set_area_scale(
            self.process_area_scale(
                subcomponent.get_area_scale(),
                combined_attributes,
                f"{subcomponent.get_name()}.area_scale",
            )
        )
        subcomponent.set_energy_scale(
            self.process_area_scale(
                subcomponent.get_energy_scale(),
                combined_attributes,
                f"{subcomponent.get_name()}.energy_scale",
            )
        )
        return subcomponent

    @staticmethod
    def apply_internal_bindings(component, compound_attributes):
        """Locate and process any mappings or arithmetic operations between the component attributes"""
        attrs = parse_expressions_sequentially_replacing_bindings(
            component.get_attributes(),
            compound_attributes,
            f"{component.get_name()}.",
            strings_allowed=True,
        )
        component.add_new_attr(attrs)

    def construct_name_base_name_map(self):
        self.subcomponent_base_name_map = {}
        for subname in self.all_possible_subcomponents:
            sub_base_name = remove_brackets(subname)
            self.subcomponent_base_name_map[sub_base_name] = subname

    def find_subcomponent_obj(self, subcomponent_name):
        """find the corresponding subcomponent def to retrieve the action-related information"""

        subcomponent_base_name = remove_brackets(subcomponent_name)
        assert subcomponent_base_name in self.subcomponent_base_name_map, (
            f"Subcomponent {subcomponent_base_name} not found in "
            f"compound component {self.get_name()}. Subcomponents are: "
            f"{self.subcomponent_base_name_map.keys()}"
        )
        assert (
            self.subcomponent_base_name_map[subcomponent_base_name]
            in self.all_possible_subcomponents
        ), (
            f"Subcomponent {subcomponent_base_name} not found in "
            f"compound component {self.get_name()}. Subcomponents are: "
            f"{self.all_possible_subcomponents.keys()}"
        )
        return self.all_possible_subcomponents[
            self.subcomponent_base_name_map[subcomponent_base_name]
        ]
        return subcomp_obj

    # ------------ CONVERSION TO DICTS for BETTER OUTPUTS FUNCTIONS ------------#

    def get_subcomponents_as_dict(self):
        subcomp_dict = {}
        for sub_name, sub_obj in self._subcomponents.items():
            subcomp_dict[sub_name] = {
                "class": sub_obj.get_class_name(),
                "attributes": sub_obj.get_attributes(),
                "area_scale": sub_obj.get_area_scale(),
                "energy_scale": sub_obj.get_energy_scale(),
            }
        return subcomp_dict

    def get_dict_representation(self):
        """Generate the information of the component component in a dictionary format
        including: (1) attributes (2) class (2) flattened primitive list (2) flattened actions
        """

        from collections import OrderedDict

        cc_dict = OrderedDict()

        subcomponent_dict = self.get_subcomponents_as_dict()
        subcomponent_list = []
        for subcomp_name, subcomp_info_dict in subcomponent_dict.items():
            new_info_dict = OrderedDict({"name": subcomp_name})
            new_info_dict.update(subcomp_info_dict)
            subcomponent_list.append(new_info_dict)

        cc_dict.update(
            {
                "name": self.get_name(),
                "class": self.get_class_name(),
                "attributes": self.get_attributes(),
                "primitive_components": subcomponent_list,
                "actions": [],
            }
        )
        idx = 0
        for action in self._actions:
            cc_dict["actions"].append(
                OrderedDict(
                    {
                        "name": action.get_name(),
                        "arguments": action.get_arguments(),
                        "primitive_actions": [],
                    }
                )
            )
            for pc_action_tuple in action.get_primitive_list():
                cc_dict["actions"][idx]["primitive_actions"].append(
                    OrderedDict(
                        {
                            "name": pc_action_tuple[0],
                            "action": pc_action_tuple[1].get_name(),
                            "arguments": pc_action_tuple[1].get_arguments(),
                            "energy_scale": pc_action_tuple[1].get_energy_scale(),
                        }
                    )
                )
            idx = idx + 1
        return cc_dict
