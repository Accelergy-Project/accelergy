import os
import unittest
import tests.action_area_share.test
import tests.plugin_choices.test
import tests.plugin_choices_II.test
import tests.plugin_choices_III.test
import tests.exercises.test
from   tests.basic.test_energy_calculation import TestEnergyCalculation
from   tests.basic.test_helper_functions import TestHelperFunctions
from   tests.basic.test_parsing_utils import TestParsingUtils
import argparse
import utils

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-p', '--preserve_output', 
                            action='store_true', help='Preserve output files from passed tests.')
    args = arg_parser.parse_args()
    
    utils.PRESERVE_OUTPUT_FILES = args.preserve_output
    
    test_loader = unittest.TestLoader()
    
    suite = unittest.TestSuite()
    os.chdir('tests/basic')
    suite.addTests(test_loader.loadTestsFromTestCase(TestEnergyCalculation))
    suite.addTests(test_loader.loadTestsFromTestCase(TestHelperFunctions))
    suite.addTests(test_loader.loadTestsFromTestCase(TestParsingUtils))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.action_area_share.test.Test))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.plugin_choices.test.Test))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.plugin_choices_II.test.Test))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.plugin_choices_III.test.Test))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestAccelergy01))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestAccelergy02))
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestAccelergy03)) PROBLEM: Different numbers from Aladdin plug-in.
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestAccelergy04)) PROBLEM: Different numbers from Aladdin plug-in. See commit e741e80f1ca385dfaea0a7d4c09ad7d09794239f of the Aladdin plug-in.
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloop00))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloop01))
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloop02)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloop03)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloop04)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloop05)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloop06)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloopAccelergy00)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IspassTestTimeloopAccelergy01)) PROBLEM: Example uses dummy table
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest01))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest02))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest03))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest04))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest05))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest06))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest07))
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest08))
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest09)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest10)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.IscaTest11)) PROBLEM: Different numbers for address generation. Aladdin plug-in change?
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.BaselineTest01)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.BaselineTest02)) PROBLEM: Different numbers for address generation. Aladdin plug-in change?
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.BaselineTest03))  PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.BaselineTest04)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.BaselineTest05)) PROBLEM: Example uses dummy table
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.BaselineTest06)) Don't want to make users install the tables to run the tests
    # suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.BaselineTest07)) PROBLEM: Example uses dummy table
    suite.addTests(test_loader.loadTestsFromTestCase(tests.exercises.test.BaselineTest08))
    
    
    
    unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'Tests skipped:')
    print('\ttests.exercises.test.IspassTestAccelergy03')
    print('\ttests.exercises.test.IspassTestAccelergy04')
    print('\ttests.exercises.test.IspassTestTimeloop02')
    print('\ttests.exercises.test.IspassTestTimeloop03')
    print('\ttests.exercises.test.IspassTestTimeloop04')
    print('\ttests.exercises.test.IspassTestTimeloop05')
    print('\ttests.exercises.test.IspassTestTimeloop06')
    print('\ttests.exercises.test.IspassTestTimeloopAccelergy00')
    print('\ttests.exercises.test.IspassTestTimeloopAccelergy01')
    print('\ttests.exercises.test.IscaTest09')
    print('\ttests.exercises.test.IscaTest10')
    print('\ttests.exercises.test.IscaTest11')
    print('\ttests.exercises.test.BaselineTest01')
    print('\ttests.exercises.test.BaselineTest02')
    print('\ttests.exercises.test.BaselineTest03')
    print('\ttests.exercises.test.BaselineTest04')
    print('\ttests.exercises.test.BaselineTest05')
    print('\ttests.exercises.test.BaselineTest07')
    
