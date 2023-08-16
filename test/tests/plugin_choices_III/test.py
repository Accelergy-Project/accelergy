import os
from utils import AccelergyUnitTest

class Test(AccelergyUnitTest):
    def setUp(self):
        super().setUp(os.path.dirname(os.path.realpath(__file__)))

    def test_plug_in_choices(self):
        # min_accuracy is too high!
        self.assertFalse(self.get_accelergy_success())
