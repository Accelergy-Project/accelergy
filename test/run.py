import os
import unittest
import tests.action_area_scale.test
import tests.plugin_choices.test
import tests.plugin_choices_II.test
import tests.plugin_choices_III.test
import tests.exercises.test
from tests.basic.test_energy_calculation import TestEnergyCalculation
from tests.basic.test_helper_functions import TestHelperFunctions
from tests.basic.test_parsing_utils import TestParsingUtils
import argparse
import utils

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-p",
        "--preserve_output",
        action="store_true",
        help="Preserve output files from passed tests.",
    )
    args = arg_parser.parse_args()

    utils.PRESERVE_OUTPUT_FILES = args.preserve_output

    test_loader = unittest.TestLoader()

    suite = unittest.TestSuite()
    os.chdir("tests/basic")

    def addTests(test):
        suite.addTests(test_loader.loadTestsFromTestCase(test))

    addTests(TestEnergyCalculation)
    addTests(TestHelperFunctions)
    addTests(TestParsingUtils)
    addTests(tests.action_area_scale.test.Test)
    addTests(tests.plugin_choices.test.Test)
    addTests(tests.plugin_choices_II.test.Test)
    addTests(tests.plugin_choices_III.test.Test)
    addTests(tests.exercises.test.IspassTestAccelergy01)
    addTests(tests.exercises.test.IspassTestAccelergy02)
    addTests(tests.exercises.test.IspassTestAccelergy03)
    addTests(tests.exercises.test.IspassTestAccelergy04)
    addTests(tests.exercises.test.IspassTestTimeloop00)
    addTests(tests.exercises.test.IspassTestTimeloop01)
    addTests(tests.exercises.test.IspassTestTimeloop02)
    addTests(tests.exercises.test.IspassTestTimeloop03)
    addTests(tests.exercises.test.IspassTestTimeloop04)
    addTests(tests.exercises.test.IspassTestTimeloop05)
    addTests(tests.exercises.test.IspassTestTimeloop06)
    addTests(tests.exercises.test.IspassTestTimeloopAccelergy00)
    addTests(tests.exercises.test.IspassTestTimeloopAccelergy01)
    addTests(tests.exercises.test.IscaTest01)
    addTests(tests.exercises.test.IscaTest02)
    addTests(tests.exercises.test.IscaTest03)
    addTests(tests.exercises.test.IscaTest04)
    addTests(tests.exercises.test.IscaTest05)
    addTests(tests.exercises.test.IscaTest06)
    addTests(tests.exercises.test.IscaTest07)
    addTests(tests.exercises.test.IscaTest08)
    addTests(tests.exercises.test.IscaTest09)
    addTests(tests.exercises.test.IscaTest10)
    addTests(tests.exercises.test.IscaTest11)
    addTests(tests.exercises.test.BaselineTest01)
    addTests(tests.exercises.test.BaselineTest02)
    addTests(tests.exercises.test.BaselineTest03)
    addTests(tests.exercises.test.BaselineTest04)
    addTests(tests.exercises.test.BaselineTest05)
    # Don't want to make users install the tables to run the tests
    # addTests(tests.exercises.test.BaselineTest06)
    addTests(tests.exercises.test.BaselineTest07)
    addTests(tests.exercises.test.BaselineTest08)

    unittest.TextTestRunner(verbosity=2).run(suite)
