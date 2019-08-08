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

import os,sys
from yaml import load
from accelergy.utils import accelergy_loader, ERROR_CLEAN_EXIT,create_folder, write_yaml_file, INFO

def config_file_checker():
    config_file_content = config_file_v02()
    return config_file_content

# ---------------------------------------------------------------------
# checker for config file version 0.2
# ---------------------------------------------------------------------
def config_file_v02():
    possible_config_dirs = ['.' + os.sep, os.path.expanduser('~') + '/.config/accelergy/']
    config_file_name = 'accelergy_config.yaml'
    for possible_dir in possible_config_dirs:
        if os.path.exists(possible_dir + config_file_name):
            original_config_file_path = possible_dir + config_file_name
            original_content = load(open(original_config_file_path), accelergy_loader)
            INFO('config file located:', original_config_file_path)
            if 'version' not in original_content:
                ERROR_CLEAN_EXIT('config file has no version number, cannot proceed')
            file_version = original_content['version']
            if file_version == 0.1 or file_version == 1.0: # probably exist 1.0 in the very initial version
                ERROR_CLEAN_EXIT('config file version outdated. Latest version is 0.2.'
                                 '\nPlease delete the original file, and run accelergy to create a new default config file.'
                                 '\nPlease ADD YOUR USER_DEFINED file paths BACK to the updated config file at '
                                 '~/.config/accelergy/accelergy_config.yaml')
            else:
                return original_content
    else:
        create_folder(possible_config_dirs[1])
        config_file_path = possible_config_dirs[1] + config_file_name
        default_estimator_path = os.path.abspath(str(sys.prefix) + '/share/accelergy/estimation_plug_ins/')
        default_pc_lib_path = os.path.abspath(
            os.path.join(str(sys.prefix) + '/share/accelergy/primitive_component_libs/'))
        config_file_content = {'version': 0.2,
                               'estimator_plug_ins': [default_estimator_path],
                               'primitive_components': [default_pc_lib_path]}
        INFO('Accelergy creating default config at:', possible_config_dirs[1] + config_file_name, 'with:\n',
             config_file_content)
        write_yaml_file(config_file_path, config_file_content)
        return config_file_content



