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


from accelergy.raw_inputs_2_dicts import RawInputs2Dicts
from accelergy.system_state import SystemState
from accelergy.io import parse_commandline_args, generate_output_files
from accelergy.utils import *

def main():
    accelergy_version = 0.3

    # ----- Interpret Commandline Arguments
    args = parse_commandline_args()
    output_prefix = args.oprefix
    path_arglist = args.files
    output_path = args.outdir

    # ----- Global Storage of System Info
    system_state = SystemState()
    system_state.set_accelergy_version(accelergy_version)

    # ----- Load Raw Inputs to Parse into Dicts
    raw_input_info = {'path_arglist': path_arglist, 'parser_version': accelergy_version}
    raw_dicts = RawInputs2Dicts(raw_input_info)

    # ----- Interpret the input architecture description using only the input information (w/o class definitions)
    system_state.set_hier_arch_spec(raw_dicts.get_hier_arch_spec_dict())

    # save file to correct output path location
    path = os.path.join(output_path, output_prefix + 'defined_input_architecture.yaml')
    write_yaml_file(path, system_state.hier_arch_spec)
    INFO('defined input architecture is saved to:', path)