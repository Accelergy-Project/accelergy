import unittest
import pkg_resources
import yaml
from accelergy.utils import *


from accelergy.raw_inputs_2_dicts import RawInputs2Dicts
from accelergy.arch_dict_2_obj import fully_define_arch_dict
from accelergy.system_state import SystemState
from accelergy.component_class import ComponentClass

class TestArchInterpretation(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.version = float(pkg_resources.require("accelergy")[0].version)
        with open('./data/hierarchical_primitive_arch_step01.yaml') as f:
            self.desired_arch_dict = yaml.load(f, accelergy_loader)
        with open('./data/hierarchical_primitive_arch_step02.yaml') as f:
            self.desired_fully_defined_arch_dict = yaml.load(f, accelergy_loader)

    def test_fromYAMLtoDict(self):
        """ step01: contruct dictionary representation of the architecture with YAML file
        define all the component names, project attributes
        """
        # accelergy's dict representation of the arch spec
        #  1. flattens all the component names
        #  2. projects all the shared attributes
        #  3. DO NOT perform mappings/arithmetic operations of the attributes,
        #      as default attributes from the classes are not available from just parsing the input arch yaml file
        raw_input_info = {'path_arglist':['./data/hierarchical_primitive_arch.yaml'], 'parser_version': self.version}
        raw_dicts = RawInputs2Dicts(raw_input_info)
        interpreted_arch_dict = raw_dicts.get_arch_spec_dict()
        self.assertEqual(interpreted_arch_dict, self.desired_arch_dict)

    def test_DictToObj(self):
        raw_input_info = {'path_arglist':['./data/hierarchical_primitive_arch.yaml'], 'parser_version': self.version}
        raw_dicts = RawInputs2Dicts(raw_input_info)
        interpreted_arch_dict = raw_dicts.get_arch_spec_dict()

        system_state = SystemState()
        for pc_name, pc_info in raw_dicts.get_pc_classses().items():
            system_state.add_pc_class(ComponentClass(pc_info))

        fully_defined_dict = fully_define_arch_dict(interpreted_arch_dict, {}, system_state.pc_classes)
        for component_name, component_info in self.desired_fully_defined_arch_dict['components'].items():
            self.assertEqual(fully_defined_dict['components'][component_name]['name'], component_info['name'])
            self.assertEqual(fully_defined_dict['components'][component_name]['class'], component_info['class'])
            for attr_name, attr_val in component_info['attributes'].items():
                self.assertEqual(fully_defined_dict['components'][component_name]['attributes'][attr_name], attr_val)

if __name__ == '__main__':
    unittest.main()