from copy import deepcopy
from accelergy.utils import  *
from accelergy.parsing_utils import *

class PrimitiveComponent():
    def __init__(self, def_info):
        """ An instance of the class represent a component in the architecture
            A component type instance can be a primitive component instance or component component instance
        """
        arch_component = def_info['component']
        component_class = def_info['pc_class']
        self._name = arch_component.get_name()
        self._class_name = arch_component.get_class_name()
        self._attributes = arch_component.get_attributes()
        self._actions = []
        for action in self.flatten_top_level_action_list(component_class):
            self._actions.append(action)

    def flatten_top_level_action_list(self, component_class):
        actionNameList = component_class.get_action_name_list()
        flattenedActionList = []
        for actionName in actionNameList:
            actionObj = deepcopy(component_class.get_action(actionName))
            flattened = actionObj.flatten_action_args_into_list(self.get_attributes())
            for action in flattened:
                flattenedActionList.append(action)
        return flattenedActionList

    def get_name(self):
        return self._name

    def get_attributes(self):
        return self._attributes

    def get_class_name(self):
        return self._class_name

    def get_actions(self):
        return self._actions

    def get_dict_representation(self):
        from collections import OrderedDict
        dict = OrderedDict({'name': self.get_name(),
                'class': self.get_class_name(),
                'actions': []})
        for action in self.get_actions():
            dict['actions'].append( OrderedDict({'name': action.get_name(),
                                                'arguments': action.get_arguments()}))
        return dict



