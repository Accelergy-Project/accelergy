import unittest

from accelergy import helper_functions as hf

class TestHelperFunctions(unittest.TestCase):

    def test_oneD_linear_interpolation(self):
        """ linear interpolation on one hardware attribute """

        # Rough estimation of simple ripple carry adder: E_adder = E_full_adder * bitwidth + E_misc

        E_full_adder = 4
        E_misc = 2
        bitwidth_0 = 32
        bitwidth_1 = 8
        energy_0 = E_full_adder * bitwidth_0 + E_misc
        energy_1 = E_full_adder * bitwidth_1 + E_misc
        bitwidth_desired = 16

        # expected output
        energy_desired = E_full_adder * bitwidth_desired + E_misc

        energy_interpolated = hf.oneD_linear_interpolation(bitwidth_desired,[{'x':bitwidth_0, 'y': energy_0},
                                                                             {'x':bitwidth_1, 'y':energy_1}])
        self.assertEqual(energy_interpolated, energy_desired)

    def test_oneD_quad_interpolation(self):
        """ quadratic interpolation on one hardware attribute """

        # Rough estimation of simple array multiplier: E_mult = E_full_adder * bitwidth^2 + E_misc

        E_full_adder = 4
        E_misc = 2
        bitwidth_0 = 32
        bitwidth_1 = 8
        energy_0 = E_full_adder * bitwidth_0**2 + E_misc
        energy_1 = E_full_adder * bitwidth_1**2 + E_misc
        bitwidth_desired = 16

        # expected output
        energy_desired = E_full_adder * bitwidth_desired**2 + E_misc

        energy_interpolated = hf.oneD_quadratic_interpolation(bitwidth_desired,[{'x':bitwidth_0, 'y': energy_0},
                                                                                {'x':bitwidth_1, 'y':energy_1}])
        self.assertEqual(energy_interpolated, energy_desired)


if __name__ == '__main__':
    unittest.main()