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

class EnergyCalculator:
    def __init__(self, info):
        self.action_counts = info['action_counts']
        self.parser_version = info['parser_version']
        self.ERT = info['ERT']
        self.base_name_map = {} # map base names to ERT entries
        self.energy_estimates = None
        self.calculate_energy_estimates()


    def calculate_energy_estimates(self):
        energy_estimates = {}
        total_design_energy = 0
        for component_name, action_counts_obj_list in self.action_counts.get_action_counts().items():
            component_energy = 0
            ERT_entry_obj = self.ERT.get_ERT_entry(component_name)
            for action_count_obj in action_counts_obj_list:
                energy_per_action = ERT_entry_obj.get_action_energy(action_count_obj)
                component_energy = component_energy + energy_per_action * action_count_obj.get_action_count()
            energy_estimates[component_name] = component_energy
            total_design_energy += component_energy
        self.energy_estimates = EnergyEstimates(energy_estimates, total_design_energy, self.parser_version)

class EnergyEstimates:
    def __init__(self, estimates_dict, total_design_energy, parser_version):
        self.energy_estimates_dict = estimates_dict
        self.parser_version = parser_version
        self.total_design_energy = total_design_energy

    def get_energy_estimation(self, component_name):
        if component_name not in self.energy_estimates_dict:
            return None
        return self.energy_estimates_dict[component_name]

    def get_energy_estimate_as_dict(self):
        energy_estimate_list = []
        for component_name, component_energy in self.energy_estimates_dict.items():
            energy_estimate_list.append(OrderedDict({'name': component_name, 'energy': component_energy}))
        estimate_dict = {'energy_estimation':OrderedDict({'version': self.parser_version, 'components': energy_estimate_list, 'Total': self.total_design_energy})}
        return estimate_dict

