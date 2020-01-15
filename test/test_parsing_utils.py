import unittest
from accelergy.parsing_utils import *

class TestParsingUtils(unittest.TestCase):
    def test_InterpretCopmonentList_plain_name(self):
        """ If plain name can be correctly detected """
        name = 'design.mac'
        name_base, list_suffix, list_length = interpret_component_list(name)
        self.assertEqual(name_base, 'design.mac')
        self.assertEqual(list_suffix, None)
        self.assertEqual(list_length, None)

    def test_InterpretCopmonentList_defined_name_list(self):
        """ If fully defined list name can be correctly detected """
        name = 'design.scratchpad[0..1]'
        name_base, list_suffix, list_length = interpret_component_list(name)
        self.assertEqual(name_base, 'design.scratchpad')
        self.assertEqual(list_suffix, '[0..1]')
        self.assertEqual(list_length, 2)

    def test_InterpretCopmonentList_undefined_binded_name_list(self):
        """ If undefined list name with string mappings can be correctly detected """
        name = 'design.scratchpad[startIdx..endIdx]'
        binding_dict = {'startIdx': 0, 'endIdx':1}
        name_base, list_suffix, list_length = interpret_component_list(name, binding_dict)
        self.assertEqual(name_base, 'design.scratchpad')
        self.assertEqual(list_suffix, '[0..1]')
        self.assertEqual(list_length, 2)

    def test_InterpretComponentList_undefined_arith_name_list(self):
        """ If undefined list name with arithmetic operations can be correctly detected """
        name = 'design.scratchpad[startIdx..endIdx+endIdx]'
        binding_dict = {'startIdx': 0, 'endIdx':1}
        name_base, list_suffix, list_length = interpret_component_list(name, binding_dict)
        self.assertEqual(name_base, 'design.scratchpad')
        self.assertEqual(list_suffix, '[0..2]')
        self.assertEqual(list_length, 3)

    def test_RemoveBrackets_no_braket_name(self):
        """ Test remove bracket"""
        name = 'design.mac'
        self.assertEqual(remove_brackets(name), name)
        name = 'design.PE[0..2].buffer[0..3].mux'
        self.assertEqual(remove_brackets(name), 'design.PE.buffer.mux')

    def test_CountNumIdenticalComps(self):
        """ Test Count number of identical components"""
        name = 'design.PE[0..2].buffer[0..3].mux'
        self.assertEqual(count_num_identical_comps(name), 12)

    def test_GetRangeOrIndicesInName(self):
        """ Test get range or indices in name"""
        name = 'design.PE[0..2].buffer[0..3].mux'
        self.assertEqual(get_ranges_or_indices_in_name(name),[(0,2),(0,3)])
        name = 'design.PE[0].buffer[0].mux'
        self.assertEqual(get_ranges_or_indices_in_name(name),[0,0])


if __name__ == '__main__':
    unittest.main()