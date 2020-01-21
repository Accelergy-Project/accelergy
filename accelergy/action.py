from copy import deepcopy
from accelergy.utils import *
from accelergy.parsing_utils import *


class Action(object):
    """Action class"""
    def __init__(self, action_def_dict):

        self.action_def_dict = action_def_dict
        self.name = action_def_dict['name']

        self._arguments = None
        self.set_arguments(action_def_dict)

        # compound action contains action definitions in terms of subcomponents
        self._subcomponents = None
        self.set_subcomponents(action_def_dict)

        # repeat has the same meaning as action share
        if 'repeat' in action_def_dict:
            self._action_share = action_def_dict['repeat']
        elif 'action_share' in action_def_dict:
            self._action_share = action_def_dict['action_share']
        else:
            self._action_share = None
        # only compound actions will later set this property
        self._primitive_list = None

    def set_arguments(self, action_def_dict):
        if 'arguments' in action_def_dict:
            self._arguments = {}
            for arg_name, arg_range in action_def_dict['arguments'].items():
                self._arguments[arg_name] = arg_range

    def set_subcomponents(self, action_def_dict):
        if 'subcomponents' in action_def_dict:
            self._subcomponents = {}
            for subcomp in action_def_dict['subcomponents']:
                subcompActions = []
                for subcompAction in subcomp['actions']:
                    subcompActions.append(Action(subcompAction))
                self._subcomponents[subcomp['name']] = subcompActions

    def set_primitive_list(self, primitive_list):
        self._primitive_list = primitive_list

    def set_action_share(self, new_action_share):
        """update the parsed repeat/action_share value"""
        self._action_share = new_action_share

    def set_argument(self, new_arg_dict):
        """ update one or more argument name-val pairs"""
        self._arguments.update(new_arg_dict)

    def set_subcomps(self, defined_subcomps):
        self._subcomponents = defined_subcomps

    def get_name(self):
        return self.name

    def get_action_share(self):
        return self._action_share

    def get_arguments(self):
        return self._arguments

    def get_argument(self, arg_name):
        return self._arguments[arg_name]

    def get_subcomps(self):
        ASSERT_MSG(self._subcomponents is not None, 'action does not have defined subcomponents')
        return self._subcomponents

    def get_primitive_list(self):
        return self._primitive_list

    def get_action_info_as_dict(self):
        action_dict = {'name': self.name}
        if self._subcomponents is not None: action_dict['subcomponents'] = self._subcomponents
        if self._arguments is not None: action_dict['arguments'] = self._arguments
        return action_dict

    def get_subactions(self, subcompName):
        ASSERT_MSG(self._subcomponents is not None and subcompName in self._subcomponents,
                   'cannot find subactions associated with %s for action %s'%(subcompName, self.name))
        return self._subcomponents[subcompName]

    def get_arg_val(self, argName):
        ASSERT_MSG(argName in self._arguments, 'argument name %s is not associated with action %s'%(argName, self.name))
        return self._arguments[argName]

    def set_arg(self, arg_dict):
        self._arguments.update(arg_dict)

    def flatten_action_args_into_list(self, mappingDict):
        """ flatten an action into a list representing all possible argument value combinations"""

        args = self.get_arguments()
        if args is None:
            return [self]  # no arguments, no need to flatten

        # an action needs to be flattened into a list of actions with the same action name but different arg vals
        total_entries = 1
        argument_range_record = {}
        for arg_name, arg_range in args.items():
            ASSERT_MSG(type(arg_range) is str, '%s: argument value for action %s is not string, cannot parse range'%(arg_name,self.name))
            ASSERT_MSG('..' in arg_range, '%s: argument value for action %s is not range, cannot parse range'%(arg_name,self.name))
            new_arg_range = Action.map_arg_range_bounds(arg_range, mappingDict)[0]
            startIdx, endIdx = Action.parse_arg_range(new_arg_range)
            total_entries *= (endIdx - startIdx + 1)
            argument_range_record[arg_name] = (startIdx, endIdx)

        action_list = []
        for entry_idx in range(total_entries):
            offset = 1
            arg_def = {}
            for arg_name, range_record in argument_range_record.items():
                arg_range = range_record[1] - range_record[0] + 1
                arg_def[arg_name] = (entry_idx // offset) % arg_range + range_record[0]
                offset *= arg_range
            subcomp_list = []
            new_action = deepcopy(self); new_action._arguments = arg_def
            action_list.append(new_action)
        return action_list

    @staticmethod
    def parse_arg_range(arg_range):
        """ Parse the start index and end index for an argument range"""
        if type(arg_range) is not str or '..' not in arg_range:
            ERROR_CLEAN_EXIT('cannot parse the argument range specification: ', arg_range)
        split_sub_string = arg_range.split('..')
        start_idx = int(split_sub_string[0])
        end_idx = int(split_sub_string[1])
        return start_idx, end_idx

    @staticmethod
    def expand_action_to_list_with_arg_values(action_info):
        """flatten actions with arguments into list
           1) input action is fully defined with numerical ranges
           2) output list contains a list of actions each with a possible set of argument values
        """

        action_name = action_info['name']
        total_entries = 1
        argument_range_record = {}
        for argument_name, argument_range in action_info['arguments'].items():
            start_idx, end_idx = Action.parse_arg_range(argument_range)
            total_entries *= (end_idx - start_idx + 1)
            argument_range_record[argument_name] = (start_idx, end_idx)
        expanded_list = [{'name': action_name, 'arguments':{}} for i in range(total_entries)]
        # construct list of dictionaries that contain all the possible combination of argument values
        for entry_idx in range(total_entries):
            offset = 1
            for argument_name, range_record in argument_range_record.items():
                arg_range = range_record[1] - range_record[0] + 1
                expanded_list[entry_idx]['arguments'][argument_name] = \
                    (entry_idx // offset) % arg_range + range_record[0]
                offset *= arg_range
        return expanded_list

    @staticmethod
    def map_arg_range_bounds(arg_range_str, attributes_dict):
        """
        arguments for actions might have ranges that are specified in terms of it attributes
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

    @staticmethod
    def parse_arg_range(arg_range):
        if type(arg_range) is not str or '..' not in arg_range:
            ERROR_CLEAN_EXIT('cannot parse the argument range specification: ', arg_range)
        split_sub_string = arg_range.split('..')
        start_idx = int(split_sub_string[0])
        end_idx   = int(split_sub_string[1])
        return start_idx, end_idx