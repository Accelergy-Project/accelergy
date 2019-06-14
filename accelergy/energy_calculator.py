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

import os
from yaml import load, dump
from accelergy.utils import accelergy_loader, accelergy_dumper, \
                            write_yaml_file, ERROR_CLEAN_EXIT, WARN, INFO


class EnergyCalculator(object):
    def __init__(self):
        self.energy_reference_table   = {}
        self.action_counts            = {}
        self.energy_estimation_table  = {}
        self.design_name              = None
        self.decimal_points           = None

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

    def construct_action_counts(self, action_counts_list):
        if 'version' not in action_counts_list:
            ERROR_CLEAN_EXIT('please specify the version of parser your input format adheres to using '
                             '"version" key at top level')
        if 'nodes' not in action_counts_list:
            ERROR_CLEAN_EXIT('action counts tree nodes should be the value of top level key "nodes", '
                             '"nodes" not found at top-level')
        raw_action_counts = action_counts_list['nodes']

        if not len(raw_action_counts) == 1:
            ERROR_CLEAN_EXIT('the first level list of your action counts should only have one node, '
                             'which is your design\'s root node' )

        self.design_name = raw_action_counts[0]['name']
        for node_description in raw_action_counts[0]['nodes']:
            self.flatten_action_count(self.design_name, node_description)


    def flatten_action_count(self, prefix, node_description):
        # syntax error checks
        if 'name' not in node_description:
            ERROR_CLEAN_EXIT('component format violation: "name" needs to be specified as a key in node description')
        if 'action_counts' in node_description and 'nodes' in node_description:
            ERROR_CLEAN_EXIT('action_counts and nodes keys cannot exist in the same node')
        # extract basic information
        node_name = node_description['name']
        # node_base_name = EnergyCalculator.belongs_to_list(node_name)
        if 'action_counts' in node_description:
            full_name = prefix + '.' + node_name
            self.action_counts[full_name] = node_description['action_counts']

        else:
            prefix = prefix + '.' + node_name
            for sub_node_description in node_description['nodes']:
                self.flatten_action_count(prefix, sub_node_description)


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
            return name
        else:
            new_name = ''
            hierarchical_name_list = name.split('.')
            for name_segment in hierarchical_name_list:
                base_name_segment = EnergyCalculator.belongs_to_list(name_segment)
                new_name += base_name_segment + '.'
            new_name = new_name[:-1]
            INFO('list component detected:', name, 'projected into', new_name)
            return new_name

    def generate_estimations(self, action_counts_path, ERT_path, output_path, precision):
        print('\n=========================================')
        print('Generating energy estimation')
        print('=========================================')
        # load and parse access counts
        self.energy_reference_table = load(open(ERT_path), accelergy_loader)
        self.construct_action_counts(load(open(action_counts_path), accelergy_loader))
        INFO('design under evaluation:', self.design_name)
        INFO('processing action counts file:', os.path.abspath(action_counts_path))

        self.decimal_points = precision

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
        write_yaml_file(file_path, self.energy_estimation_table)
        print('---> Finished: energy calculation finished, estimation saved to:\n', os.path.abspath(output_path))

