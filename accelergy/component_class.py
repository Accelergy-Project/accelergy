from copy import deepcopy
from accelergy.utils import *
from accelergy.action import Action
from accelergy.subcomponent import Subcomponent
from collections import OrderedDict

class ComponentClass:
    def __init__(self, class_dict):
        self._name = class_dict['name']
        self._default_attributes = deepcopy(class_dict['attributes'])

        self._actions = {}
        self.set_actions(class_dict['actions'])

        self._subcomponents = None
        if 'subcomponents' in class_dict:
            self._subcomponents = {}
            self.type = 'compound'
            for scomp in class_dict['subcomponents']: self._subcomponents[scomp['name']] = Subcomponent(scomp)
        else:
            self.type = 'primitive'
        self._primitive_type = class_dict['primitive_type'] if 'primitive_type' in class_dict else None

    def set_actions(self, action_list):
        ASSERT_MSG(type(action_list) is list,
                   '%s class description must specify its actions in list format'%(self.get_name()))
        for action in action_list:
            ASSERT_MSG('name' in action, '%s class actions must contain "name" keys'%(self.get_name()))
            self._actions[action['name']] = Action(action)

    #-----------------------------------------------------
    # Getters
    #-----------------------------------------------------
    def get_name(self):
        return self._name

    def get_default_attr_to_apply(self, obj_attr_name_list):
        attr_to_be_applied = OrderedDict()
        for attr_name, attr_val in self._get_default_attrs().items():
            if attr_val == "must_specify":
                ASSERT_MSG(attr_name in obj_attr_name_list,
                           "attributes %s for compound class %s must be specified in architecture description"
                           %(attr_name, self.get_name()))
            if attr_name not in obj_attr_name_list:
                attr_to_be_applied[attr_name] = attr_val
        return attr_to_be_applied

    def _get_default_attrs(self):
        return self._default_attributes

    def _get_attr_name_list(self):
        return list(self._default_attributes.keys())

    def _get_attr_default_val(self, attrName):
        ASSERT_MSG(attrName in self._default_attributes, 'Attribute %s cannot be found in class %s'%(attrName, self.get_name()))
        return self._default_attributes[attrName]

    def get_action_name_list(self):
        return list(self._actions.keys())

    def get_action(self, actionName):
        ASSERT_MSG(actionName in self._actions, '%s does not exist in class %s'%(actionName, self.get_name()))
        return self._actions[actionName]

    def get_subcomponents_as_dict(self):
        ASSERT_MSG(self._subcomponents is not None, 'component class %s does not have subcomponents' % self.get_name())
        return self._subcomponents

    def get_primitive_type(self):
        return self._primitive_type
