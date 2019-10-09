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

import os, re
from yaml import load, dump
from accelergy.utils import accelergy_loader, accelergy_dumper, \
                            write_yaml_file, ERROR_CLEAN_EXIT, WARN, INFO, ASSERT_MSG


class EnergyCalculator(object):
    def __init__(self):
        self.energy_reference_table   = {}
        self.action_counts            = {}
        self.energy_estimation_table  = {}
        self.design_name              = None
        self.decimal_points           = None
        self.flattened_list           = None
        self.action_counts_version    = None

    @staticmethod
    def belongs_to_list(name):
        if '[' and ']' in name:
            start_idx = name.find('[')
            end_idx = name.find(']')
            index = name[start_idx+1:end_idx]
            try:
                int(index)
            except TypeError:
                ERROR_CLEAN_EXIT('list node located, but cannot parse for index')
            name_base = name[:start_idx]
            return name_base
        else:
            return name
    @staticmethod
    def remove_brackets(name):
        """Removes the brackets from a component name in a list"""
        if '[' not in name and ']' not in name:
            return name
        if '[' in name and ']' in name:
            start_idx = name.find('[')
            end_idx = name.find(']')
            name = name[:start_idx] + name[end_idx + 1:]
            name = EnergyCalculator.remove_brackets(name)
            return name

    def construct_action_counts(self, action_counts_list):
        if 'action_counts' in action_counts_list:
            action_counts_content = action_counts_list['action_counts']
        else:
            action_counts_content =  action_counts_list
        self.process_action_count_content(action_counts_content)

    def process_action_count_content(self, action_counts_list):
        if 'version' not in action_counts_list:
            ERROR_CLEAN_EXIT('please specify the version of parser your input format adheres to using '
                             '"version" key at top level')
        self.action_counts_version = action_counts_list['version']
        if action_counts_list['version'] == 0.2:
            ASSERT_MSG('subtree' in action_counts_list or 'local' in action_counts_list, 'v0.2 error: action counts... \n'
                        'the action counts must contain the "subtree" key or "local" key at the top level')
            # raw_action_counts = action_counts_list['subtree']
            # ASSERT_MSG(len(raw_action_counts) == 1, 'v0.2 error: action counts... \n'
            #                     'the first level list of your action counts should only have one node, '
            #                      'which is your design\'s root node')
            self.v02_flatten_action_count(None, action_counts_list)

        if action_counts_list['version'] == 0.1:
            raw_action_counts = action_counts_list['nodes']
            if 'nodes' not in action_counts_list:
                ERROR_CLEAN_EXIT('v0.1 error: action counts...\n Tree nodes should be the value of top level key "nodes", '
                                 '"nodes" not found at top-level')
            if not len(raw_action_counts) == 1:
                ERROR_CLEAN_EXIT('the first level list of your action counts should only have one node, '
                                 'which is your design\'s root node')
            self.design_name = raw_action_counts[0]['name']
            for node_description in raw_action_counts[0]['nodes']:
                self.v01_flatten_action_count(self.design_name, node_description)

    def v02_flatten_action_count(self, prefix, node_description):
        if 'local' in node_description:
            local_nodes = node_description['local']
            for local_node in local_nodes:
                ASSERT_MSG("name" in local_node, 'action count error... '
                                                 'component format violation: "name" needs to be '
                                                 'specified as a key in node description')
                if prefix is None:
                    full_name = local_node['name']
                else:
                    full_name = prefix + '.' + local_node['name']
                self.action_counts[full_name] = local_node['action_counts']
        if 'subtree' in node_description:
            for subtree_node_description in node_description['subtree']:
                ASSERT_MSG("name" in subtree_node_description, 'action count error... '
                                                 'component format violation: "name" needs to be '
                                                 'specified as a key in node description')
                if prefix is None:
                    subtree_prefix = subtree_node_description['name']
                else:
                    subtree_prefix = prefix + '.' + subtree_node_description['name']
                self.v02_flatten_action_count(subtree_prefix, subtree_node_description)

    def v01_flatten_action_count(self, prefix, node_description):
        # syntax error checks
        if 'name' not in node_description:
            ERROR_CLEAN_EXIT('component format violation: "name" needs to be specified as a key in node description')
        if 'action_counts' in node_description and 'nodes' in node_description:
            ERROR_CLEAN_EXIT('action_counts and nodes keys cannot exist in the same node')
        # extract basic information
        node_name = node_description['name']
        if 'action_counts' in node_description:
            full_name = prefix + '.' + node_name
            self.action_counts[full_name] = node_description['action_counts']

        else:
            prefix = prefix + '.' + node_name
            for sub_node_description in node_description['nodes']:
                self.v01_flatten_action_count(prefix, sub_node_description)


    def process_component_action_counts(self, action_count_list, component_ERT):
        component_total_energy = 0
        for action_count in action_count_list:
            action_name = action_count['name']
            action_args = action_count['arguments'] if 'arguments' in action_count\
                                                    else None
            count = action_count['counts']

            energy = None
            for name, ERT_info in component_ERT.items():
                if action_name == name:
                    if action_args is not None:
                        for arg_combo in ERT_info:
                            args_matched = True
                            for action_arg, action_arg_val in action_args.items():
                                if not arg_combo['arguments'][action_arg] == action_arg_val:
                                    args_matched = False
                            if args_matched:
                                energy = arg_combo['energy']
                    else:
                        energy = ERT_info['energy']
            if energy is None:
                ERROR_CLEAN_EXIT(['cannot find the action in related ERT', action_count])
            component_total_energy += count * energy
        return component_total_energy

    def process_name(self, name):
        """
        list component: reformat the component names to their format stored in ERTs
        standalone component: no modifications
        """
        if '[' not in name and ']' not in name:
            ASSERT_MSG(name in self.energy_reference_table, "Cannot find %s's ERT"%name)
            return name
        else:
            new_name = ''
            hierarchical_name_list = name.split('.')
            for name_segment in hierarchical_name_list:
                base_name_segment = EnergyCalculator.belongs_to_list(name_segment)
                new_name += base_name_segment + '.'
            new_name = new_name[:-1]
            if self.flattened_list is not None:
                ASSERT_MSG(new_name in self.flattened_list,
                           "According to the flattened architecture, %s is not a legal name " % name)
                saved_entry = self.flattened_list[new_name]
                for idx in range(len(saved_entry['format'])):
                    range_location = saved_entry['format'][idx]
                    range_min = int(saved_entry['range'][idx][0])
                    range_max = int(saved_entry['range'][idx][1])
                    curr_idx = int(hierarchical_name_list[range_location][hierarchical_name_list[range_location].find('[')+1:\
                                                           hierarchical_name_list[range_location].find(']')])
                    ASSERT_MSG(range_max>= curr_idx >= range_min,
                               'Invalid list component name %s, index out of bound'%name)
            # INFO('list component detected:', name, 'projected into', new_name)
            return new_name

    def load_flattened_arch(self, raw_flattened_arch):
        for component_name, component_info in raw_flattened_arch.items():
            if  '['  in component_name and ']'  in component_name:
                component_name_base = EnergyCalculator.remove_brackets(component_name)

                # dissect hierarchy
                parts = []
                part_start_idx = 0
                for i in range(len(component_name)):
                    if component_name[i] is '.' and component_name[i+1] is not '.' \
                          and component_name[i-1] is not '.':
                        parts.append(component_name[part_start_idx:i])
                        part_start_idx = i+1

                # dissect location of the lists
                format = []  # where the indexes are
                for part_idx in range(len(parts)):
                    if '[' and ']' in parts[part_idx]:
                        format.append(part_idx)

                # dissect range
                idx_list = [] # what the range is, each range is in the format [min, max]
                for match in re.finditer(r'\[\w+..\w+\]', component_name):
                    list_range = component_name[match.start() + 1:match.end() - 1].split('..')
                    idx_list.append(list_range)
                self.flattened_list[component_name_base] = {'format': format, 'range': idx_list}

    def extract_ERT(self, raw_ERT):
         if 'version' not in raw_ERT:
             self.energy_reference_table = raw_ERT
         else:
             ASSERT_MSG('version' in raw_ERT, 'v>=0.2 error: ERT ... \n ERT must contain "version" key')
             ASSERT_MSG('tables' in raw_ERT, 'v>=0.2 error: ERT ... \n ERT must contain "tables" key')
             ERT_version = raw_ERT['version']
             if ERT_version <= 0.2:
                 self.energy_reference_table = raw_ERT['tables']
             else:
                 ERROR_CLEAN_EXIT('ERT version: ', ERT_version, 'no parser available...')


    def generate_estimations(self, araw_action_counts, raw_ERT, output_path, precision, raw_flattened_arch):
        print('\n=========================================')
        print('Generating energy estimation')
        print('=========================================')
        # load and parse access counts
        self.extract_ERT(raw_ERT['ERT'])
        self.construct_action_counts(araw_action_counts)
        self.decimal_points = precision
        if raw_flattened_arch is None:
            WARN('flattened architecture is not given or --enable_flattened_arch not set high, will not perform legal component name check')
        else:
            self.flattened_list = {}
            self.load_flattened_arch(raw_flattened_arch['flattened_architecture']['components'])

        for name, action_count_list in self.action_counts.items():
            INFO('processing for component:', name)
            # the components in the list are stored differently in ERT
            processed_name = self.process_name(name)
            component_ERT = self.energy_reference_table[processed_name]
            # generate the total energy for the component
            component_energy = self.process_component_action_counts(action_count_list, component_ERT)
            self.energy_estimation_table[name] = round(component_energy, self.decimal_points)

        # save results
        file_path = output_path + '/estimation.yaml'
        write_yaml_file(file_path, {'energy_estimation': {'components': self.energy_estimation_table,
                                                          'version': self.action_counts_version}})
        print('---> Finished: energy calculation finished, estimation saved to:\n', os.path.abspath(output_path))

