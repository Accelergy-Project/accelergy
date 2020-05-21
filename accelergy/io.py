# Copyright (c) 2019 Yannan Wu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import argparse
from collections import OrderedDict
from accelergy.utils import *
import pyfiglet

def parse_commandline_args():
    ascii_banner = pyfiglet.figlet_format("Accelergy")
    print(ascii_banner)
    """parse command line inputs"""
    parser = argparse.ArgumentParser(
        description='Accelergy is an architecture-level energy estimator for accelerator designs. Accelergy allows '
                    ' users to describe the architecture of a design with user-defined compound components and generates energy '
                    'estimations according to the workload-generated action counts.')
    parser.add_argument('-o', '--outdir', type=str, default='./',
                        help = 'Path to output directory that stores '
                               'the ERT and/or flattened_architecture and/or energy estimation. '
                               'Default is current directory.')
    parser.add_argument('-p', '--precision', type=int, default='3',
                        help= 'Number of decimal points for generated energy values. '
                              'Default is 3.')
    parser.add_argument('-v', '--verbose', type=int, default = 0,
                        help= 'If set to 1, Accelergy outputs the verbose version of the output files '
                              'Default is 0')
    parser.add_argument('-f', '--output_files',  nargs="*", type =str, default = ['all'],
                         help= 'list that contains the desired output files.'
                               ' Options include: ERT, ERT_summary, ART, ART_summary, energy_estimation, flattened_arch,'
                               ' and all (which refers to all possible outputs)')
    parser.add_argument('--oprefix', type =str, default = '',
                         help= 'prefix that will be added to the output files names.')
    parser.add_argument('files', nargs='*',
                        help= 'list of input files in arbitrary order.'
                              'Accelergy parses the top keys of the files to decide the type of input the file describes, '
                                                                    'e.g., architecture description, '
                                                                          'compound component class descriptions, etc. '
                        )
    return parser.parse_args()


def generate_output_files(system_state):

    """Generate all the  necessary output files according to the input flags"""
    output_path = system_state.flags['output_path']
    verbose = system_state.flags['verbose']
    parser_version = system_state.parser_version
    output_prefix = system_state.flags['output_prefix']

    # Generate Flattened Architecture
    if system_state.flags['flattened_arch']:
        if not verbose:
            path = os.path.join(output_path, output_prefix + 'flattened_architecture.yaml')
            write_yaml_file(path, system_state.arch_spec.generate_flattened_arch())
            INFO('flattened architecture is saved to:', path)
        else:
            # Generate verbose architecture
            all_flattened_components = []
            for cc_name, cc_obj in system_state.ccs.items():
                all_flattened_components.append(cc_obj.get_dict_representation())

            for pc_name, pc_obj in system_state.pcs.items():
                all_flattened_components.append(pc_obj.get_dict_representation())

            all_flattened_components_w_headers = {'architecture':OrderedDict({'version': parser_version,
                                                                              'local': all_flattened_components})}

            path = os.path.join(output_path, output_prefix + 'flattened_architecture_verbose.yaml')
            write_yaml_file(path, all_flattened_components_w_headers)
            INFO('verbose flattened architecture is saved to:', path)

    if system_state.flags['ERT'] :
        # Generate ERT
        path = os.path.join(output_path, output_prefix + 'ERT.yaml')
        write_yaml_file(path, system_state.ERT.get_ERT())
        INFO('energy reference table is saved to:', path)

    if system_state.flags['ERT_summary']:
        if not verbose:
            path = os.path.join(output_path, output_prefix + 'ERT_summary.yaml')
            write_yaml_file(path, system_state.ERT.get_ERT_summary())
            INFO('energy reference table summary is saved to:', path)
        else:
            path = os.path.join(output_path, output_prefix + 'ERT_summary_verbose.yaml')
            write_yaml_file(path, system_state.ERT.get_ERT_summary_verbose())
            INFO('verbose energy reference table summary is saved to:', path)

    if system_state.flags['energy_estimation']:
        # Generate energy estimates
        path = os.path.join(output_path, output_prefix + 'energy_estimation.yaml')
        energy_estimation_dict = system_state.energy_estimations.get_energy_estimate_as_dict()
        if not energy_estimation_dict["energy_estimation"]["components"] == []:
            write_yaml_file(path, energy_estimation_dict)
            INFO('energy estimations are saved to:', path)
        else:
            WARN('no runtime energy estimations are generated... not generating energy_estimation.yaml')

    if system_state.flags['ART']:
        # Generate ART
        path = os.path.join(output_path, output_prefix + 'ART.yaml')
        write_yaml_file(path, system_state.ART.get_ART())
        INFO('area reference table is saved to:', path)

    if system_state.flags['ART_summary']:
        if not verbose:
            path = os.path.join(output_path, output_prefix + 'ART_summary.yaml')
            write_yaml_file(path, system_state.ART.get_ART_summary())
            INFO('area reference table summary is saved to:', path)
        else:
            path = os.path.join(output_path, output_prefix + 'ART_summary_verbose.yaml')
            write_yaml_file(path, system_state.ART.get_ART_summary_verbose())
            INFO('verbose area reference table summary is saved to:', path)