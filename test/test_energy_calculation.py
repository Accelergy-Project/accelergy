import unittest
import pkg_resources

from accelergy.raw_inputs_2_dicts import RawInputs2Dicts
from accelergy.ERT_generator import ERT_dict_to_obj
from accelergy.action_counts_dict_2_obj import action_counts_dict_2_obj
from accelergy.energy_calculator import EnergyCalculator

class TestEnergyCalculation(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.version = float(pkg_resources.require("accelergy")[0].version)
        self.desired_ERT_dict = {'design.mac': {'mac_random':[{'name': 'mac_random', 'arguments': None, 'energy': 3}],
                                                'mac_reused': [{'name': 'mac_reused', 'arguments': None, 'energy': 2}],
                                                'mac_gated': [{'name': 'mac_gated', 'arguments': None, 'energy': 1}],
                                                'idle': [{'name': 'idle','arguments': None, 'energy': 0}]
                                               },
                                  'design.scratchpad[0..2]': {'fill':[{'name': 'fill',
                                                                'arguments': {'address_delta': 0, 'data_delta': 0},
                                                                'energy': 3},
                                                               {'name': 'fill',
                                                                'arguments': {'address_delta': 0, 'data_delta': 1},
                                                                'energy': 6},
                                                               {'name': 'fill',
                                                                'arguments': {'address_delta': 1, 'data_delta': 0},
                                                                'energy': 5},
                                                               {'name': 'fill',
                                                                'arguments': {'address_delta': 1, 'data_delta': 1},
                                                                'energy': 7}],
                                                       'read':[{'name': 'read',
                                                                'arguments': {'address_delta': 0, 'data_delta': 0},
                                                                'energy': 4},
                                                               {'name': 'read',
                                                                'arguments': {'address_delta': 0, 'data_delta': 1},
                                                                'energy': 7},
                                                               {'name': 'read',
                                                                'arguments': {'address_delta': 1, 'data_delta': 0},
                                                                'energy': 6},
                                                               {'name': 'read',
                                                                'arguments': {'address_delta': 1, 'data_delta': 1},
                                                                'energy': 8}],
                                                       'idle': [{'name': 'idle','arguments': None, 'energy': 0}]
                                                      }
                                }
        self.desired_action_counts_dict = {'design.mac':[{'name': 'mac_random', 'counts': 50},
                                                         {'name': 'mac_gated', 'counts': 100}
                                                         ],
                                           'design.scratchpad[0]':[{'name': 'idle', 'counts': 100},
                                                                   {'name': 'fill',
                                                                    'arguments':{'address_delta': 0, 'data_delta':0},
                                                                    'counts': 1150},
                                                                   {'name': 'fill',
                                                                    'arguments': {'address_delta': 1, 'data_delta': 1},
                                                                    'counts': 24}
                                                                   ]
                                           }
    def test_fromYAMLfileToERTDict(self):
        """ generate desired ERT dictionary representation from YAML file input """

        raw_input_info = {'path_arglist':['./data/ERT.yaml'], 'parser_version': self.version}
        raw_dicts = RawInputs2Dicts(raw_input_info)
        self.assertEqual(raw_dicts.get_ERT_dict(), self.desired_ERT_dict)

    def test_constructERTobj(self):
        """ construct ERT obj with raw dictionary representation"""

        raw_input_info = {'path_arglist': ['./data/ERT.yaml'], 'parser_version': self.version}
        raw_dicts = RawInputs2Dicts(raw_input_info)
        ERT_info = {}
        ERT_info['ERT_dict'] = raw_dicts.get_ERT_dict()
        ERT_info['parser_version'] = self.version
        ERT_info['precision'] = 3
        ERT_obj = ERT_dict_to_obj(ERT_info)

    def test_fromYAMLfileToActionCountsDict(self):
        """generate desired action counts dictionary representation from YAML file input"""

        raw_input_info = {'path_arglist':['./data/action_counts.yaml'], 'parser_version': self.version}
        raw_dicts = RawInputs2Dicts(raw_input_info)
        self.assertEqual(raw_dicts.get_action_counts_dict(), self.desired_action_counts_dict)

    def test_constructActionCountsObj(self):
        """ construct action counts obj with raw dictionary representation"""

        raw_input_info = {'path_arglist':['./data/action_counts.yaml'], 'parser_version': self.version}
        raw_dicts = RawInputs2Dicts(raw_input_info)
        action_counts_obj = action_counts_dict_2_obj(raw_dicts.get_action_counts_dict())

    def test_energyComputation(self):
        """correct energy calculations of the components"""
        desired_ERT_obj = ERT_dict_to_obj(
            {'ERT_dict': self.desired_ERT_dict, 'parser_version': self.version, 'precision': 3})
        desired_action_counts_obj = action_counts_dict_2_obj(self.desired_action_counts_dict)
        energy_calculator = EnergyCalculator({'action_counts': desired_action_counts_obj,
                                              'ERT': desired_ERT_obj,
                                              'parser_version': self.version})

        mac_energy = energy_calculator.energy_estimates.get_energy_estimation('design.mac')
        scrachpad_energy = energy_calculator.energy_estimates.get_energy_estimation('design.scratchpad[0]')
        self.assertEqual(float(mac_energy), float(250))
        self.assertEqual(float(scrachpad_energy),float(1150*3 + 24*7))

    def test_wrongActionCounts(self):
        """ test if wrong component name in action count will result in error"""

        desired_ERT_obj = ERT_dict_to_obj(
            {'ERT_dict': self.desired_ERT_dict, 'parser_version': self.version, 'precision': 3})
        raw_input_info = {'path_arglist':['./data/action_counts_error.yaml'], 'parser_version': self.version}
        raw_dicts = RawInputs2Dicts(raw_input_info)
        action_counts_error_obj = action_counts_dict_2_obj(raw_dicts.get_action_counts_dict())
        init_info = {'action_counts': action_counts_error_obj,
                                              'ERT': desired_ERT_obj,
                                              'parser_version': self.version}
        with self.assertRaises(SystemExit) as cm:
           EnergyCalculator(init_info)
        self.assertEqual(cm.exception.code, 1)



if __name__ == '__main__':
    unittest.main()

