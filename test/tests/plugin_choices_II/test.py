import os
from utils import AccelergyUnitTest

class Test(AccelergyUnitTest):
    def setUp(self):
        super().setUp(os.path.dirname(os.path.realpath(__file__)))

    def test_plug_in_choices(self):
        self.assertTrue(self.get_accelergy_success())

        # The low-accuracy plug-in is picked if specified
        self.assert_area('arch.pick_higher_accuracy', 1)
        self.assert_energy('arch.pick_higher_accuracy', 'action_a', 1)
        self.assertIn('Unused arguments (required_parameter', self.accelergy_out)
