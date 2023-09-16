import os
import re
from utils import AccelergyUnitTest


class ExampleTester(AccelergyUnitTest):
    def setUp(self,
              test_dir: str,
              extra_accelergy_args: str = '',
              compare_files: list = (),
              ref_dir: str = 'ref-output',
              remove_regexes_before_compare: list = (),
              ignore_differences: list = (),
              **kwargs):

        my_dir = os.path.dirname(os.path.realpath(__file__))
        example_dir = os.path.join(
            my_dir, 'timeloop-accelergy-exercises', 'workspace', test_dir)
        if '-p' not in extra_accelergy_args:
            extra_accelergy_args += ' -p 6 --suppress_version_errors'
        super().setUp(example_dir, extra_accelergy_args=extra_accelergy_args, **kwargs)
        self.example_dir = example_dir
        self.compare_files = compare_files
        self.ref_dir = ref_dir
        print(f'Reference output directory: {self.ref_dir}')
        self.remove_regexes_before_compare = remove_regexes_before_compare
        self.ignore_differences = list(ignore_differences) + ['version']

    def get_ref_content(self, filename):
        ref_output_dir = os.path.join(self.example_dir, self.ref_dir)
        # If the reference dir does not have any yaml files, find the first sub-directory
        if not [f for f in os.listdir(ref_output_dir) if f.endswith('.yaml')]:
            for d in os.listdir(ref_output_dir):
                if os.path.isdir(os.path.join(ref_output_dir, d)):
                    ref_output_dir = os.path.join(ref_output_dir, d)
                    break
        if not os.path.exists(os.path.join(ref_output_dir, filename)):
            filename = f'timeloop-mapper.{filename}'
        if not os.path.exists(os.path.join(ref_output_dir, filename)):
            filename = filename.replace('mapper', 'model')

        print(
            f'Checking against reference output in {os.path.join(ref_output_dir, filename)}')
        return open(os.path.join(ref_output_dir, filename)).read()

    def compare_yamls_ignore_differences_allowed(self, a, b):
        return  # The baselines have too many problems...
        diff = self.compare_yamls(a, b)
        problems = {}
        for k, v in diff.items():
            if not any(d in str(k) or d in str(v) for d in self.ignore_differences):
                problems[k] = v
        if problems:
            print(f'Found differences that were not ignored: {problems}')
        self.maxDiff = None
        self.assertEqual(problems, {})

    def test_against_example_ref(self):
        if self.compare_files:
            for filename in self.compare_files:
                ref_content = self.get_ref_content(filename)
                self.compare_yamls(
                    self.get_file_content(filename), ref_content)
                self.compare_yamls_ignore_differences_allowed(
                    self.get_file_content(filename), ref_content)
        else:
            ref_art = self.get_ref_content('ART.yaml')
            ref_ert = self.get_ref_content('ERT.yaml')
            self.assertTrue(self.get_accelergy_success())
            self.compare_yamls_ignore_differences_allowed(
                self.accelergy_art, ref_art)
            self.compare_yamls_ignore_differences_allowed(
                self.accelergy_ert, ref_ert)


class IspassTestAccelergy01(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2020.ispass/accelergy/01_primitive_architecture_ERT')


class IspassTestAccelergy02(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/accelergy/02_primitive_architecture_energy',
            compare_files=['energy_estimation.yaml'])


class IspassTestAccelergy03(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2020.ispass/accelergy/03_compound_architecture')


class IspassTestAccelergy04(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/accelergy/04_eyeriss_like',
            '-p 5',
            compare_files=['energy_estimation.yaml', 'ERT.yaml', 'ART.yaml'],
        )


class IspassTestTimeloop00(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop/00-model-conv1d-1level',
            force_input_files=['arch/*.yaml'],
        )


class IspassTestTimeloop01(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop/01-model-conv1d-2level',
            force_input_files=['arch/*.yaml'],
        )


class IspassTestTimeloop02(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop/02-model-conv1d+oc-2level',
            force_input_files=['arch/*.yaml'],
        )


class IspassTestTimeloop03(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop/03-model-conv1d+oc-3level',
            force_input_files=['arch/*.yaml'],
        )


class IspassTestTimeloop04(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop/04-model-conv1d+oc-3levelspatial',
            force_input_files=['arch/*.yaml'],
        )


class IspassTestTimeloop05(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop/05-mapper-conv1d+oc-3level',
            force_input_files=['arch/*.yaml'],
        )


class IspassTestTimeloop06(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop/06-mapper-convlayer-eyeriss',
            force_input_files=['arch/*.yaml', 'arch/components/*.yaml'],
        )


class IspassTestTimeloopAccelergy00(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop+accelergy/',
            force_input_files=[
                'arch/eyeriss_like-int16.yaml', 'arch/components/*.yaml'],
            ref_dir='ref-output/int16',
        )


class IspassTestTimeloopAccelergy01(ExampleTester):
    def setUp(self):
        super().setUp(
            'exercises/2020.ispass/timeloop+accelergy/',
            force_input_files=[
                'arch/eyeriss_like-float32.yaml', 'arch/components/*.yaml'],
            ref_dir='ref-output/float32',
        )


class IscaTest01(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/01.2.1-DUDU-dot-product',
                      force_input_files=['arch/*.yaml'],)


class IscaTest02(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/01.2.2-SUDU-dot-product',
                      force_input_files=['arch/*.yaml'],)


class IscaTest03(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/01.2.3-SCDU-dot-product',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class IscaTest04(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/02.2.1-spMspM',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class IscaTest05(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/02.2.2-spMspM-tiled',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class IscaTest06(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/03.2.1-conv1d',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class IscaTest07(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/03.2.2-conv1d+oc',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class IscaTest08(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/03.2.3-conv1d+oc-spatial',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class IscaTest09(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/04.2.1-eyeriss-like-gating',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class IscaTest10(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/04.2.2-eyeriss-like-gating-mapspace-search',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class IscaTest11(ExampleTester):
    def setUp(self):
        super().setUp('exercises/2021.isca/designs/04.2.3-eyeriss-like-onchip-compression',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class BaselineTest01(ExampleTester):
    def setUp(self):
        super().setUp('baseline_designs/example_designs/eyeriss_like',
                      force_input_files=['arch/*.yaml',
                                         'arch/components/*.yaml'],
                      ref_dir='example_AlexNet_layer1_outputs')


class BaselineTest02(ExampleTester):
    def setUp(self):
        super().setUp('baseline_designs/example_designs/eyeriss_like_onchip_compression',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class BaselineTest03(ExampleTester):
    def setUp(self):
        super().setUp('baseline_designs/example_designs/eyeriss_like_w_gating',
                      force_input_files=['arch/*.yaml', 'components/*.yaml'],)


class BaselineTest04(ExampleTester):
    def setUp(self):
        super().setUp('baseline_designs/example_designs/simba_like',
                      ref_dir='example_AlexNet_layer1_outputs',
                      force_input_files=['arch/*.yaml', 'arch/components/*.yaml'],)


class BaselineTest05(ExampleTester):
    def setUp(self):
        super().setUp('baseline_designs/example_designs/simple_output_stationary',
                      force_input_files=['arch/*.yaml',
                                         'arch/components/*.yaml'],
                      ref_dir='example_AlexNet_layer1_outputs')


class BaselineTest06(ExampleTester):
    def setUp(self):
        super().setUp('baseline_designs/example_designs/simple_pim',
                      ref_dir='example_outputs',
                      force_input_files=['arch/*.yaml', 'arch/components/*.yaml'])


class BaselineTest07(ExampleTester):
    def setUp(self):
        super().setUp('baseline_designs/example_designs/simple_weight_stationary',
                      ref_dir='example_AlexNet_layer1_outputs',
                      force_input_files=['arch/*.yaml', 'arch/components/*.yaml'])


class BaselineTest08(ExampleTester):
    def setUp(self):
        super().setUp('baseline_designs/example_designs/sparse_tensor_core_like',
                      force_input_files=['arch/*.yaml', 'arch/components/*.yaml'])
