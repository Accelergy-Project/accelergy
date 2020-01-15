from accelergy.utils import *

def action_counts_dict_2_obj(actions_dict):
    action_counts = ActionCounts(actions_dict)
    return action_counts

class ActionCounts:
    def __init__(self, actions_dict):
        self.action_counts = {}
        for component_name, actions_list in actions_dict.items():
            self.action_counts[component_name] = []
            for action_info_dict in actions_list:
                self.action_counts[component_name].append(ActionCountEntry(action_info_dict))
    def get_action_counts(self):
        return self.action_counts

    def get_component_names_list(self):
        return list(self.action_counts.keys())

    def get_action_count_entries_for_compnoent(self, component_name):
        ASSERT_MSG(component_name in self.action_counts, '%s cannot be found in action counts specification'%component_name)
        return self.action_counts[component_name]

class ActionCountEntry:
    def __init__(self, action_info_dict):
        ASSERT_MSG('name' and 'counts' in action_info_dict, 'action count entry must be initialized with '
                   'dictionaries that contains "name" and "counts" keys: \n%s'%(action_info_dict))
        self.action_info_dict = action_info_dict

    def get_action_name(self):
        return self.action_info_dict['name']

    def get_action_arguments(self):
        if 'arguments' in self.action_info_dict:  return self.action_info_dict['arguments']
        else: return None


    def get_action_count(self):
        return self.action_info_dict['counts']

