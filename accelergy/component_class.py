from copy import deepcopy
from accelergy.utils.utils import *
from accelergy.action import Action
from accelergy.subcomponent import Subcomponent
from collections import OrderedDict
from accelergy.parsing_utils import *


class ComponentClass:
    def __init__(self, class_dict):
        self._name = class_dict["name"]
        # resolve_optional_required_attributes(class_dict)

        self._default_attributes = deepcopy(class_dict["attributes"])

        self._actions = {}
        self.set_actions(class_dict["actions"])

        self._subcomponents = None
        if "subcomponents" in class_dict:
            self._subcomponents = {}
            self.type = "compound"
            for scomp in class_dict["subcomponents"]:
                self._subcomponents[scomp["name"]] = Subcomponent(scomp)
        else:
            self.type = "primitive"
        self._primitive_type = (
            class_dict["primitive_type"] if "primitive_type" in class_dict else None
        )

    def add_action(self, action):
        ASSERT_MSG(
            "name" in action,
            '%s class actions must contain "name" keys' % (self.get_name()),
        )
        self._actions[action["name"]] = Action(action)

    def set_actions(self, action_list):
        ASSERT_MSG(
            isinstance(action_list, list),
            "%s class description must specify its actions in list format"
            % (self.get_name()),
        )
        for action in action_list:
            self.add_action(action)

    # -----------------------------------------------------
    # Getters
    # -----------------------------------------------------
    def get_name(self):
        return self._name

    def get_default_attr_to_apply(self, obj_attr_name_list):
        attr_to_be_applied = OrderedDict()
        for attr_name, attr_val in self._get_default_attrs().items():
            # print(f'Checking for {attr_name=} {attr_val=} in {obj_attr_name_list}')
            found_val = obj_attr_name_list.get(attr_name, None)
            if attr_val == "must_specify" and found_val is None:
                raise AttributeError(
                    f"Attribute {attr_name} for compound class "
                    f"{self.get_name()} must be specified. Available "
                    f"attributes are: {list(obj_attr_name_list.keys())}"
                )
            if found_val is not None:
                attr_to_be_applied[attr_name] = found_val
            else:
                attr_to_be_applied[attr_name] = attr_val
        return attr_to_be_applied

    def _get_default_attrs(self):
        return self._default_attributes

    def _get_attr_name_list(self):
        return list(self._default_attributes.keys())

    def _get_attr_default_val(self, attrName):
        ASSERT_MSG(
            attrName in self._default_attributes,
            "Attribute %s cannot be found in class %s" % (attrName, self.get_name()),
        )
        return self._default_attributes[attrName]

    def get_action_name_list(self):
        return list(self._actions.keys())

    def get_action(self, actionName):
        if actionName not in self._actions:
            self.add_action({"name": actionName, "subcomponents": []})
        return self._actions[actionName]

    def get_subcomponents_as_dict(self):
        ASSERT_MSG(
            self._subcomponents is not None,
            "component class %s does not have subcomponents" % self.get_name(),
        )
        return self._subcomponents

    def get_primitive_type(self):
        return self._primitive_type
