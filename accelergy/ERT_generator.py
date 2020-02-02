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

import math
from collections import OrderedDict
from accelergy.utils import *
from accelergy.parsing_utils import count_num_identical_comps
from accelergy.parsing_utils import comp_name_within_range

def ERT_dict_to_obj(ERT_info):
    ERT_dict = ERT_info['ERT_dict']
    parser_version = ERT_info['parser_version']
    precision = ERT_info['precision']
    ert_obj = ERT(parser_version, precision)
    for component_name, actions_dict in ERT_dict.items():
        for action_name, action_info_list in actions_dict.items():
            for action_info in action_info_list:
                arg_combo = action_info['arguments']
                energy = action_info['energy']
                action_dict = {'name': component_name,
                               'action_name': action_name,
                               'arguments': arg_combo,
                               'energy': energy,
                               'estimator': 'N/A'}
                ert_obj.add_action_entry(action_dict)
    return ert_obj


class EnergyReferenceTableGenerator:
    def __init__(self, info):
        pc_components = info['pcs']
        cc_components = info['ccs']
        self.parser_version = info['parser_version']
        self.precision = info['precision']
        self.estimation_plug_ins = info['plug_ins']
        self.ERT = ERT(self.parser_version, self.precision)

        for pc_name, pc in pc_components.items():
            self.generate_pc_ERT(pc)
        for cc_name, cc in cc_components.items():
            self.generat_cc_ERT(cc)

    def get_ERT(self):
        return self.ERT

    def generate_pc_ERT(self, pc):
        pc_name = pc.get_name()
        for pc_action_obj in pc.get_actions():
            action_name = pc_action_obj.get_name()
            arguments = pc_action_obj.get_arguments()
            estimation_plug_in_interface = {'class_name': pc.get_class_name(),
                                           'attributes': pc.get_attributes(),
                                           'action_name': action_name,
                                           'arguments': arguments}
            estimated_energy, estimator_name = self.eval_primitive_action_energy(estimation_plug_in_interface)
            self.ERT.add_action_entry({'name': pc_name,
                                'action_name': action_name,
                                'arguments': arguments,
                                'energy': estimated_energy,
                                'estimator': estimator_name})

    def generat_cc_ERT(self, cc):
        cc_name = cc.get_name()
        primitive_type = cc.get_primitive_type()
        sub_base_name_map = self.construct_sub_base_name_map(cc)

        for cc_action_obj in cc.get_actions():
            primitive_action_estimations = []
            cc_action_name = cc_action_obj.get_name()
            cc_arguments = cc_action_obj.get_arguments()
            if primitive_type is not None:
                try:
                    estimation_plug_in_interface = {'class_name': primitive_type,
                                                    'attributes': cc.get_attributes(),
                                                    'action_name': cc_action_name,
                                                    'arguments': cc_arguments}
                    estimated_energy, estimator_name = self.eval_primitive_action_energy(estimation_plug_in_interface)
                    energy = estimated_energy
                    primitive_action_estimations = estimator_name

                except:
                    WARN('Cannot find a "%s" estimator for %s'%(primitive_type, cc_name))
                    primitive_type = None

            if primitive_type is None:
                energy = 0
                primitive_action_tuples = cc_action_obj.get_primitive_list()
                for primitive_action_tuple in primitive_action_tuples:
                    subcomp_name = primitive_action_tuple[0]
                    subaction_obj = primitive_action_tuple[1]
                    subcomp_obj = sub_base_name_map[remove_brackets(subcomp_name)]
                    estimation_plug_in_interface = {'class_name': subcomp_obj.get_class_name(),
                                                    'attributes': subcomp_obj.get_attributes(),
                                                    'action_name': subaction_obj.get_name(),
                                                    'arguments': subaction_obj.get_arguments()}
                    estimated_energy, estimator_name = self.eval_primitive_action_energy(estimation_plug_in_interface)
                    # check if the subcomponent name is a list, if so, take it into account using list length
                    total_identical_comps = count_num_identical_comps(subcomp_name)
                    # accumulate energy (consider action_share and # of identical subactions)
                    energy += estimated_energy * subaction_obj.get_action_share() * total_identical_comps
                    primitive_action_estimations.append((subcomp_name, subaction_obj, estimator_name, estimated_energy))

            self.ERT.add_action_entry({'name': cc_name,
                                       'action_name': cc_action_name,
                                       'arguments': cc_arguments,
                                       'energy': round(energy, self.precision),
                                       'estimator': primitive_action_estimations})
        if primitive_type is not None:
            INFO('Component %s estimated with primitive type %s' % (cc_name, primitive_type))


    def construct_sub_base_name_map(self,cc):
        sub_base_name_map = {}
        for subcomp_name, subcomp_obj in cc.get_subcomponents().items():
            subcomp_base_name = remove_brackets(subcomp_name)
            sub_base_name_map[subcomp_base_name] = subcomp_obj
        return sub_base_name_map

    def eval_primitive_action_energy(self, estimator_plug_in_interface):
        """
        :param estimator_plug_in_interface: dictionary that adheres to
               Accelergy-external estimator interface format
        :return energy estimation of the action
        """
        best_accuracy = 0
        best_estimator = None
        for estimator in self.estimation_plug_ins:
            accuracy = estimator.primitive_action_supported(estimator_plug_in_interface)
            ASSERT_MSG(type(accuracy) is int or type(accuracy) is float,
                       'Wrong plug-in accuracy: %s ...  Returned accuracy must be integers or floats'%(estimator))
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_estimator = estimator
        if best_estimator is None:
            ERROR_CLEAN_EXIT('cannot find appropriate plug-in:', estimator_plug_in_interface,
                             'Available plug-ins:', self.estimation_plug_ins)
        energy = round(best_estimator.estimate_energy(estimator_plug_in_interface), self.precision)
        return energy, best_estimator.estimator_name


class ERT:
    def __init__(self, parser_version, precision):
        self.entries = {}
        self.base_name_map = {}
        self.parser_version = parser_version
        self.precision = precision

    def add_action_entry(self, entry_dict):
        comp_name = entry_dict['name']
        if comp_name not in self.entries:
            self.entries[comp_name] = ComponentERTEntry(comp_name, self.precision)
        self.entries[comp_name].add_action_energy(entry_dict)

    def get_ERT(self):
        from collections import OrderedDict
        ERT = {'ERT': OrderedDict({'version': self.parser_version, 'tables': []})}
        for comp_name, ERT_entry_obj in self.entries.items():
            ERT['ERT']['tables'].append(ERT_entry_obj.get_ERT_entry_dict_rep())
        return ERT

    def get_ERT_entry(self, component_name):
        component_base_name = remove_brackets(component_name)
        ERT_entry = self.get_ERT_entry_w_base_name(component_base_name)
        ASSERT_MSG(ERT_entry is not None, 'Cannot find corresponding entry for component %s' % component_name)
        ASSERT_MSG(comp_name_within_range(component_name, ERT_entry.get_component_name()),
                   'component name "%s" in action counts is not legal, legal range should be within "%s"'
                   %(component_name, ERT_entry.get_component_name()))
        return ERT_entry

    def get_ERT_entry_w_base_name(self, component_base_name):
        self.get_base_name_map()
        if component_base_name not in self.base_name_map: return None
        entry_name = self.base_name_map[component_base_name]
        ERT_entry = self.entries[entry_name]
        return ERT_entry

    def get_base_name_map(self):
        if self.base_name_map == {}:
            for complete_name in self.entries:
                base_name = remove_brackets(complete_name)
                self.base_name_map[base_name] = complete_name
        return self.base_name_map

    def get_ERT_summary(self):
        ERT_summary_list = []
        for comp_name, ERT_entry_obj in self.entries.items():
            ERT_entry_summary_dict = ERT_entry_obj.get_ERT_entry_summary_dict_rep()
            ERT_summary_list.append(ERT_entry_summary_dict)
        return {'ERT_summary': OrderedDict({'version': self.parser_version, 'table_summary': ERT_summary_list})}
    
    def get_ERT_summary_verbose(self):
        ERT_summary_list = []
        for comp_name, ERT_entry_obj in self.entries.items():
            ERT_entry_summary_dict = ERT_entry_obj.get_ERT_summary_verbose_dict_rep()
            ERT_summary_list.append(ERT_entry_summary_dict)
        return {'ERT_summary': OrderedDict({'version': self.parser_version, 'table_summary': ERT_summary_list})}

class ComponentERTEntry:
    def __init__(self, component_name, precision):
        self.component_name = component_name
        self.action_entries = {}
        self.estimator_s = {}
        self.precision = precision

    def add_action_energy(self, action_dict):
        action_name = action_dict['action_name']
        if action_name not in self.action_entries:
            self.action_entries[action_name] = []

        arguments = action_dict['arguments']
        energy = action_dict['energy']

        # if the entry is for a compound component, interpret the estimations for the primitive component actions
        subaction_estimations = []
        if isinstance(action_dict['estimator'], list):
            for primitive_estimation_info in action_dict['estimator']:
                subcomponent_name = primitive_estimation_info[0]
                subaction_obj = primitive_estimation_info[1]
                estimator_name = primitive_estimation_info[2]
                estimated_energy = primitive_estimation_info[3]
                if subcomponent_name not in self.estimator_s:
                    self.estimator_s[subcomponent_name] = {'estimator': estimator_name}
                interpreted_energy = estimated_energy * subaction_obj.get_action_share() * count_num_identical_comps(subcomponent_name)
                percentage = 0 if energy == 0 else round(100*interpreted_energy/energy,2)
                subaction_estimations.append(OrderedDict({'subcomponent_name': subcomponent_name,
                                                          'subaction_name': subaction_obj.get_name(),
                                                          'arguments': subaction_obj.get_arguments(),
                                                          'energy': estimated_energy,
                                                          'action_share': subaction_obj.get_action_share(),
                                                          'interpreted_energy': interpreted_energy,
                                                          'percentage': str(percentage) + "%",
                                                          'estimator': estimator_name}))
            self.action_entries[action_name].append(
                {'arguments': arguments, 'energy': energy, 'subaction_estimations': subaction_estimations})
        else:
            if self.estimator_s == {}:
                self.estimator_s = {self.component_name: {'estimator': action_dict['estimator']}}
            self.action_entries[action_name].append({'arguments': arguments, 'energy': energy})


    def get_component_name(self):
        return self.component_name

    def get_action_energy(self, action_entry_obj):
        action_name = action_entry_obj.get_action_name()
        action_arguments = action_entry_obj.get_action_arguments()
        action_list = self.action_entries[action_name]
        for arg_combo in action_list:
            if action_arguments is None:
                return arg_combo['energy']
            for arg_name, arg_val in action_arguments.items():
                matched = True
                if not arg_combo['arguments'][arg_name] == arg_val:
                    matched = False
                    break
            if matched:
                return arg_combo['energy']
        ASSERT_MSG(matched, 'cannot find corresponding action energy in ERT for component "%s" '
                         'action "%s", argument "%s"'%(self.component_name, action_name, action_arguments))

    def get_ERT_entry_dict_rep(self):
        ERT_entry_dict_rep = OrderedDict({'name': self.component_name, 'actions':{}})
        action_list = []
        for action_name, action_info_list in self.action_entries.items():
            for argument_combo in action_info_list:
                action_item = OrderedDict({'name': action_name})
                for key, val in argument_combo.items():
                    if not key == 'subaction_estimations':
                        action_item[key] = val
                action_list.append(action_item)
        ERT_entry_dict_rep['actions'] = action_list
        return ERT_entry_dict_rep

    def get_ERT_entry_summary_dict_rep(self):
        ERT_entry_summary = OrderedDict({'name': self.component_name, 'actions': None, 'primitive_estimation(s)': None})
        ERT_entry_summary['primitive_estimation(s)'] = []
        for key, val in self.estimator_s.items():
            ERT_entry_summary['primitive_estimation(s)'].append(OrderedDict({'name': key, 'estimator': val['estimator']}))
        ERT_entry_summary['actions'] = self.get_actions_energy_min_max_avg_as_list()
        return ERT_entry_summary

    def get_ERT_summary_verbose_dict_rep(self):
        ERT_entry_verbose_summary = OrderedDict({'name': self.component_name,
                                                 'actions': None,
                                                 'primitive_estimation(s)': None})

        ERT_entry_verbose_summary['actions'] = self.get_actions_energy_min_max_avg_as_list()
        ERT_entry_verbose_summary['primitive_estimation(s)'] = []
        for action_name, action_info in self.action_entries.items():
            for arg_combo in action_info:
                if 'subaction_estimations' in arg_combo:
                    dict = OrderedDict({'action_name': action_name, 'arguments': arg_combo['arguments'],'energy': arg_combo['energy'],
                                        'subaction_estimations': arg_combo['subaction_estimations']})
                    ERT_entry_verbose_summary['primitive_estimation(s)'].append(dict)
                else:
                    if ERT_entry_verbose_summary['primitive_estimation(s)'] == []:
                        ERT_entry_verbose_summary['primitive_estimation(s)'].append(self.estimator_s)
        return ERT_entry_verbose_summary

    def get_actions_energy_min_max_avg_as_list(self):
        actions = []
        for action_name, action_info in self.action_entries.items():
            if len(action_info) == 1:
                actions.append(OrderedDict({'name': action_name, 'energy': action_info[0]['energy']}))
            else:
                init_dict = OrderedDict({'name': action_name, 'average_energy': None, 'max_energy': -1, 'min_energy': math.inf})
                accumulator = 0
                for arg_combo in action_info:
                    accumulator = accumulator + arg_combo['energy']
                    if arg_combo['energy'] > init_dict['max_energy']:
                        init_dict['max_energy'] = arg_combo['energy']
                    if arg_combo['energy'] < init_dict['min_energy']:
                        init_dict['min_energy'] = arg_combo['energy']
                init_dict['average_energy'] = round(accumulator/len(action_info), self.precision)
                actions.append(init_dict)
        return actions

