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


from collections import OrderedDict
from accelergy.utils import *
from accelergy.parsing_utils import count_num_identical_comps


class AreaReferenceTableGenerator:
    def __init__(self, info):
        pc_components = info['pcs']
        cc_components = info['ccs']
        self.precision = info['precision']
        self.estimation_plug_ins = info['plug_ins']
        self.parser_version = info['parser_version']
        self.ART = ART(self.parser_version)

        for pc_name, pc in pc_components.items():
            self.generate_pc_ART(pc)
        for cc_name, cc in cc_components.items():
            self.generate_cc_ART(cc)

    def generate_pc_ART(self, pc):
        pc_name = pc.get_name()
        estimation_plug_in_interface = {'class_name': pc.get_class_name(),
                                        'attributes': pc.get_attributes()}
        estimated_area, estimator_name = self.eval_primitive_area(estimation_plug_in_interface)
        self.ART.add_entry({'comp_name': pc_name,
                            'area': round(estimated_area, self.precision),
                            'estimator': estimator_name})

    def generate_cc_ART(self, cc):
        cc_name = cc.get_name()
        cc_area = 0
        estimators = []
        for subcomp_name, subcomp_obj in cc.get_subcomponents().items():
            estimation_plug_in_interface = {'class_name': subcomp_obj.get_class_name(),
                                            'attributes': subcomp_obj.get_attributes()}
            estimated_area, estimator_name = self.eval_primitive_area(estimation_plug_in_interface)
            factored_estimated_area = estimated_area * subcomp_obj.get_area_share()
            pc_area = factored_estimated_area * count_num_identical_comps(subcomp_name)
            cc_area += pc_area
            estimators.append(OrderedDict({'name': subcomp_name,
                                           'estimator': estimator_name,
                                           'area': round(estimated_area, self.precision),
                                           'area_share': subcomp_obj.get_area_share(),
                                           'total_component_area': round(pc_area, self.precision)}))
        self.ART.add_entry({'comp_name': cc_name,
                            'area': round(cc_area, self.precision),
                            'estimator': estimators})

    def get_ART(self):
        return self.ART

    def eval_primitive_area(self, estimator_plug_in_interface):
        """
        :param estimator_plug_in_interface: dictionary that adheres to
               Accelergy-external estimator interface format
        :return energy estimation of the action
        """
        best_accuracy = 0
        best_estimator = None
        for estimator in self.estimation_plug_ins:
            accuracy = estimator.primitive_area_supported(estimator_plug_in_interface)
            ASSERT_MSG(type(accuracy) is int or type(accuracy) is float,
                       'Wrong plug-in accuracy: %s ...  Returned accuracy must be integers or floats'%(estimator))
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_estimator = estimator
        if best_estimator is None:
            ERROR_CLEAN_EXIT('cannot find appropriate plug-in:', estimator_plug_in_interface,
                             'Available plug-ins:', self.estimation_plug_ins)
        area = round(best_estimator.estimate_area(estimator_plug_in_interface), self.precision)
        return area, best_estimator.estimator_name

class ART:
    def __init__(self, parser_version):
        self.entries = {}
        self.parser_version = parser_version

    def add_entry(self, entry_dict):
        self.entries[entry_dict['comp_name']] = ComponentARTEntry(entry_dict)

    def get_ART(self):
        area_entries = []
        for component_name, area_entry_obj in self.entries.items():
            area_entries.append(OrderedDict({'name': component_name,
                                 'area': area_entry_obj.get_component_area()}))
        ART = {'ART':OrderedDict({'version': self.parser_version,
                                  'tables': area_entries})}
        return ART

    def get_ART_summary(self):
        area_entries = []
        for component_name, area_entry_obj in self.entries.items():
            area_entries.append(OrderedDict({'name': component_name,
                                             'area': area_entry_obj.get_component_area(),
                                             'primitive_estimations': area_entry_obj.get_component_estimators()}))
        ART_summary = {'ART_summary': OrderedDict({'version': self.parser_version,
                                                   'table_summary': area_entries})}
        return ART_summary

    def get_ART_summary_verbose(self):
        area_entries_verbose = []
        for component_name, area_entry_obj in self.entries.items():
            area_entries_verbose.append(OrderedDict({'name': component_name,
                                             'area': area_entry_obj.get_component_area(),
                                             'primitive_estimations': area_entry_obj.get_component_estimators_verbose()}))
        ART_summary_verbose = {'ART_summary': OrderedDict({'version': self.parser_version,
                                                           'table_summary': area_entries_verbose})}
        return ART_summary_verbose


class ComponentARTEntry:
    def __init__(self, area_dict):
        self.component_name = area_dict['comp_name']
        self.area  = area_dict['area']
        self.estimator = area_dict['estimator']

    def get_component_area(self):
        return self.area

    def get_component_estimators(self):
        if isinstance(self.estimator, str): return self.estimator
        new_estimator_list = []
        for estimator in self.estimator:
            new_entry = OrderedDict({'name': estimator['name'],
                         'estimator': estimator['estimator']})
            new_estimator_list.append(new_entry)
        return new_estimator_list

    def get_component_estimators_verbose(self):
        return self.estimator


