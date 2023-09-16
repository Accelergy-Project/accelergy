import os
from utils import AccelergyUnitTest

class Test(AccelergyUnitTest):
    def setUp(self):
        super().setUp(os.path.dirname(os.path.realpath(__file__)))

    def test_plug_in_choices(self):
        self.assertTrue(self.get_accelergy_success())

        # Pick appropriate plug-in for higher accuracy
        self.assert_area('arch.pick_higher_accuracy', 2)
        self.assert_energy('arch.pick_higher_accuracy', 'action_a', 2)
        self.assertIn('Unused arguments (required_parameter', self.accelergy_out)
        
        # Fall back to lower accuracy plug-in if there is an error
        self.assert_energy('arch.pick_higher_accuracy', 'action_b', 1)
        self.assertIn('Broken action', self.accelergy_out)
        
        # Pick appropriate plug-in if the __init__ args do not match
        self.assert_area('arch.no_match_init', 2)
        self.assert_energy('arch.no_match_init', 'action_a', 2)
        self.assert_energy('arch.no_match_init', 'action_b', 1)
        self.assertIn('Broken action', self.accelergy_out)

        # Pick appropriate plug-in if the argument does not match
        self.assert_area('arch.match_args_init', 93)
        self.assert_energy('arch.match_args_init', 'action_a', 3)
        self.assert_energy('arch.match_args_init', 'action_b', 15)
        self.assert_energy('arch.match_args_init', 'action_c', 331)
        self.assert_energy('arch.match_args_init', 'action_c_optional_arg_override', 931)
        
        # Fall back to lower accuracy plug-in if there is an error in the init function of a plug-in
        self.assert_area('arch.error_in_area', 2)
        self.assert_energy('arch.error_in_area', 'action_a', 1000)
        self.assert_energy('arch.error_in_area', 'action_b', 3000)
        self.assertIn('Required parameter is too high!', self.accelergy_out)

        # Fall back to lower accuracy plug-in if there is an error in the init function of a plug-in
        self.assert_area('arch.error_in_init', 2)
        self.assert_energy('arch.error_in_init', 'action_a', 2)
        self.assert_energy('arch.error_in_init', 'action_b', 1)
        self.assertIn('Required parameter is too low!', self.accelergy_out)
