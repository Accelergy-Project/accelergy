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

import os, sys
import glob
import yaml
from copy import deepcopy
from yaml import dump
import yamlordereddictloader

class accelergy_loader(yaml.SafeLoader):
    """
    Accelergy yaml loader
    """
    def __init__(self, stream):
        
        self._root = os.path.split(stream.name)[0]
        super(accelergy_loader, self).__init__(stream)


def include_constructor(self, node):
    """
    constructor:
      parses the !include relative_file_path
      loads the file from relative_file_path and insert the values into the original file
    """
    filepath = self.construct_scalar(node)
    if filepath[-1] == ',':
        filepath = filepath[:-1]
    filename = os.path.join(self._root, filepath )
    with open(filename, 'r') as f:
        return yaml.load(f, accelergy_loader)

yaml.add_constructor('!include', include_constructor, accelergy_loader)

def includedir_constructor(self, node):
    """
    constructor:
      parses the !includedir relative_file_path
      loads the file from relative_file_path and insert the values into the original file
    """
    filepath = self.construct_scalar(node)
    if filepath[-1] == ',':
        filepath = filepath[:-1]
    dirname = os.path.join(self._root, filepath )
    yamllist = []
    for filename in glob.glob(dirname + "/*.yaml"):
        with open(filename, 'r') as f:
            yamllist.append(yaml.load(f, accelergy_loader))
    return yamllist

yaml.add_constructor('!includedir', includedir_constructor, accelergy_loader)


class accelergy_loader_ordered(yamlordereddictloader.SafeLoader):
    """
    Accelergy yaml loader
    """

    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(accelergy_loader_ordered, self).__init__(stream)

def include_constructor(self, node):
    """
    constructor:
      parses the !include relative_file_path
      loads the file from relative_file_path and insert the values into the original file
    """
    filepath = self.construct_scalar(node)
    if filepath[-1] == ',':
        filepath = filepath[:-1]
    filename = os.path.join(self._root, filepath)
    with open(filename, 'r') as f:
        return yaml.load(f, accelergy_loader_ordered)
yaml.add_constructor('!include', include_constructor, accelergy_loader_ordered)


def includedir_constructor(self, node):
    """
    constructor:
      parses the !includedir relative_file_path
      loads the file from relative_file_path and insert the values into the original file
    """
    filepath = self.construct_scalar(node)
    if filepath[-1] == ',':
        filepath = filepath[:-1]
    dirname = os.path.join(self._root, filepath)
    yamllist = []
    for filename in glob.glob(dirname + "/*.yaml"):
        with open(filename, 'r') as f:
            yamllist.append(yaml.load(f, accelergy_loader_ordered))
    return yamllist
yaml.add_constructor('!includedir', includedir_constructor, accelergy_loader_ordered)

class accelergy_dumper(yamlordereddictloader.SafeDumper):
    """ Accelergy yaml dumper """
    
    def ignore_aliases(self, _data):
        return True

def create_folder(directory):
    """
    Checks the existence of a directory, if does not exist, create a new one
    :param directory: path to directory under concern
    :return: None
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('ERROR: Creating directory. ' +  directory)
        sys.exit()
        
def merge_dicts(dict1, dict2):
    merge_dict = deepcopy(dict1)
    merge_dict.update(dict2)
    return merge_dict


def write_yaml_file(filepath, content):
    """
    if file exists at filepath, overwite the file, if not, create a new file
    :param filepath: string that specifies the destination file path
    :param content: yaml string that needs to be written to the destination file
    :return: None
    """
    if os.path.exists(filepath):
        os.remove(filepath)
    create_folder(os.path.dirname(filepath))
    out_file = open(filepath, 'a')
    out_file.write(dump( content, default_flow_style= False, Dumper= accelergy_dumper))

def get_yaml_format(content):
    return dump( content, default_flow_style= False, Dumper= accelergy_dumper)

def write_file(filepath, content):
    if os.path.exists(filepath):
        os.remove(filepath)
    create_folder(os.path.dirname(filepath))
    out_file = open(filepath, 'a')
    out_file.write(content)

def remove_quotes(filepath):
    """
    :param filepath: file that needs to processed
    :return: None
    removes the quotes inside yaml files
    """
    if os.path.exists(filepath):
        new_content = ''
        f = open(filepath, 'r')
        
        for line in f:
            if '\'' in line:
                line = line.replace('\'', '')
                new_content += line
        f.close()
        os.remove(filepath)
        newf = open(filepath, 'w')
        newf.write(new_content)
        newf.close()


def ERROR_CLEAN_EXIT(*argv):
    msg_str = 'ERROR: '
    for arg in argv:
        if type(arg) is not str:
            print(msg_str)
            print(arg)
            msg_str = ''
        else:
            msg_str += arg + ' '
    print(msg_str)
    sys.exit(1)

def WARN(*argv):
    msg_str = 'Warn: '
    for arg in argv:
        if type(arg) is not str:
            print(msg_str)
            print(arg)
            msg_str = ''
        else:
            msg_str += arg + ' '
    print(msg_str)

def INFO(*argv):
    msg_str = 'Info: '
    for arg in argv:
        if type(arg) is not str:
            print(msg_str)
            print(arg)
            msg_str = ''
        else:
            msg_str += arg + ' '
    print(msg_str)

def ASSERT_MSG(expression, msg):
    if not expression:
        ERROR_CLEAN_EXIT(msg)

def add_functions_as_methods(functions):
    def decorator(Class):
        for function in functions:
            setattr(Class, function.__name__, function)
        return Class
    return decorator

def register_function(sequence, function):
    sequence.append(function)
    return function

def remove_brackets(name):
    """Removes the brackets from a component name in a list"""
    if '[' not in name and ']' not in name:
        return name
    if '[' in name and ']' in name:
        start_idx = name.find('[')
        end_idx = name.find(']')
        name = name[:start_idx] + name[end_idx + 1:]
        name = remove_brackets(name)
        return name