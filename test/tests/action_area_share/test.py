import os
from utils import AccelergyUnitTest


class Test(AccelergyUnitTest):
    def setUp(self):
        super().setUp(os.path.dirname(os.path.realpath(__file__)))

    def test_area_scale(self):
        self.assertTrue(self.get_accelergy_success())

        # Hierarchy area
        self.assert_area("arch.three_level_hierarchy", 4 * 3 * 2)
        self.assert_area("arch.two_level_hierarchy", 3 * 2)
        self.assert_area("arch.one_level_hierarchy", 2)
        self.assert_area("arch.primitive_direct_from_arch", 1)

        # Hierarchy area with area share in the arch spec
        self.assert_area("arch.three_level_hierarchy_with_area_scale", 2 * 4 * 3 * 2)
        self.assert_area("arch.two_level_hierarchy_with_area_scale", 3 * 3 * 2)
        self.assert_area("arch.one_level_hierarchy_with_area_scale", 4 * 2)
        self.assert_area("arch.primitive_direct_from_arch_with_area_scale", 5)

        # Hierarchy area with area share in the arch spec but not in attributes
        self.assert_area(
            "arch.three_level_hierarchy_with_area_scale_defined_not_in_attrs",
            6 * 4 * 3 * 2,
        )
        self.assert_area(
            "arch.two_level_hierarchy_with_area_scale_defined_not_in_attrs", 7 * 3 * 2
        )
        self.assert_area(
            "arch.one_level_hierarchy_with_area_scale_defined_not_in_attrs", 8 * 2
        )
        self.assert_area(
            "arch.primitive_direct_from_arch_with_area_scale_defined_not_in_attrs", 9
        )

        # Two subcomponents different area share
        self.assert_area("arch.two_subcomponents_different_shares", 2 + 3)

    def test_energy_scale(self):
        self.assertTrue(self.get_accelergy_success())

        # Hierarchy action
        self.assert_energy("arch.three_level_hierarchy", "read", 2 * 4 * 8)
        self.assert_energy("arch.three_level_hierarchy", "write", 0.5 * 0.5 * 0.5)
        self.assert_energy("arch.two_level_hierarchy", "read", 4 * 8)
        self.assert_energy("arch.two_level_hierarchy", "write", 0.5 * 0.5)
        self.assert_energy("arch.one_level_hierarchy", "read", 8)
        self.assert_energy("arch.one_level_hierarchy", "write", 0.5)

        self.assert_energy("arch.two_subcomponents_different_shares", "read", 8 + 4)
        self.assert_energy(
            "arch.two_subcomponents_different_shares", "write", 0.5 + 0.25
        )
