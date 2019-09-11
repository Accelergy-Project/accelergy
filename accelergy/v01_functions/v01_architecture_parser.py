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

from copy import deepcopy
from accelergy.utils import ERROR_CLEAN_EXIT, INFO, WARN, register_function
from accelergy.v01_functions.v01_shared_functions import is_component_list
import functools

# list to store the functions that need to added to ERT generator class
functions = []
register_function = functools.partial(register_function, functions)

@register_function
def v01_parse_architecture_description(self, architecture_description_list):
    v01_validate_top_level_architecture_description(architecture_description_list)
    raw_architecture_description = architecture_description_list['nodes'][0]
    self.design_name = raw_architecture_description['name']
    global_attributes = None if 'attributes' not in raw_architecture_description \
        else raw_architecture_description['attributes']
    for node in raw_architecture_description['nodes']:
        self.flatten_architecture_description(self.design_name, node, global_attributes)

def v01_validate_top_level_architecture_description(architecture_description_list):
    INFO("architecture description file version: 0.1")
    if 'nodes' not in architecture_description_list:
        ERROR_CLEAN_EXIT('v0.1 error: architecture description...',
                         '"nodes" not found at top-level')
    if not len(architecture_description_list['nodes']) == 1:
        ERROR_CLEAN_EXIT('v0.1 error: architecture description...',
                         'The first level list of your architecture description should only have one node, '
                         'which is your design\'s root node')
    raw_architecture_description = architecture_description_list['nodes'][0]
    if 'nodes' not in raw_architecture_description:
        ERROR_CLEAN_EXIT('v0.1 error: architecture description...',
                         'second-level design tree must contain nodes')
    # design name syntax check
    if 'name' not in raw_architecture_description:
        ERROR_CLEAN_EXIT(
            "v0.1 error: architecture description..."
            "please specify the design name as top-level key-value pair =>  name: <design_name>")

@register_function
def flatten_architecture_description(self, prefix, node_description, shared_attributes_dict= None):
    """ Recursively parse the nodes in the architecture tree"""
    # syntax error checks
    if 'name' not in node_description:
        ERROR_CLEAN_EXIT('component format violation: "name" needs to be specified as a key in node description')
    if 'class' in node_description and 'nodes' in node_description:
        ERROR_CLEAN_EXIT('class and nodes keys cannot exist in the same node')
    # extract basic information
    node_name = node_description['name']

    # construct the shared attributes that can be applied to sub-nodes
    # useful only if current node is internal
    if shared_attributes_dict is None and 'attributes' not in node_description:
        node_attrs = None
    elif shared_attributes_dict is not None and 'attributes' not in node_description:
        node_attrs = deepcopy(shared_attributes_dict)
    elif shared_attributes_dict is None and 'attributes' in node_description:
        node_attrs = node_description['attributes']
    else: #shared_attributes_dict is not None and attributes in node_description
        node_attrs = deepcopy(shared_attributes_dict)
        node_attrs.update(node_description['attributes'])

    # determine if the component is in list format
    list_length, name_base = is_component_list(node_name, shared_attributes_dict)

    # if the component is in list format, flatten out and create the instances
    if not list_length == 0:
        for item_idx in range(list_length):
            item_prefix = prefix + '.' + name_base + '[' + str(item_idx) + ']'
            if 'nodes' in node_description:
                for sub_node_description in node_description['nodes']:
                    self.flatten_architecture_description(item_prefix, sub_node_description, node_attrs)
            else:
                self.construct_new_leaf_node_description(item_prefix, node_description, shared_attributes_dict)
    # if the component is a standalone component, parse the component description directly
    else:
        node_prefix = prefix + '.' + node_name
        if 'nodes' in node_description:
            for sub_node_description in node_description['nodes']:
                self.flatten_architecture_description(node_prefix, sub_node_description, node_attrs)
        else:
            self.construct_new_leaf_node_description(node_prefix, node_description, shared_attributes_dict)

