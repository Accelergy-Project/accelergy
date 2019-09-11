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
from accelergy.utils import ERROR_CLEAN_EXIT, INFO, WARN, register_function, ASSERT_MSG
from accelergy.v02_functions.v02_shared_functions import v02_is_component_list
from copy import deepcopy
import functools

# list to store the functions that need to added to ERT generator class
functions = []
register_function = functools.partial(register_function, functions)

@register_function
def v02_parse_architecture_description(self, architecture_description):
    v02_validate_top_level_architecture_description(architecture_description)
    raw_architecture_description = architecture_description['subtree']
    self.design_name = raw_architecture_description['name']
    global_attributes = None if 'attributes' not in raw_architecture_description \
        else raw_architecture_description['attributes']
    if 'local' in raw_architecture_description:
        for c_id in range(len(raw_architecture_description['local'])):
            item_prefix = self.design_name + "." + raw_architecture_description['local'][c_id]['name']
            self.construct_new_leaf_node_description(item_prefix,
                                                     raw_architecture_description['local'][c_id],
                                                     global_attributes)
    if 'subtree' in raw_architecture_description:
        self.flatten_architecture_subtree(self.design_name,
                                          raw_architecture_description['subtree'],
                                          global_attributes)

def v02_validate_top_level_architecture_description(architecture_description):
    INFO("architecture description file version: 0.2, checking syntax...")
    if 'subtree' not in architecture_description:
        ERROR_CLEAN_EXIT('v0.2 error: architecture description...',
                         'Architecture tree nodes should be the value of top level key "subtree", '
                         '"subtree" not found at top-level')
    raw_architecture_description = architecture_description['subtree']
    if 'local' in architecture_description:
        ERROR_CLEAN_EXIT('v0.2 error: architecture description...',
                         'The first level list of your architecture description should only have a subtree, '
                         'which is your design\'s root node')

    # design name syntax check
    if 'name' not in raw_architecture_description:
        ERROR_CLEAN_EXIT(
            "v0.2 error: architecture description...\n"
            "please specify the design name as top-level key-value pair =>  name: <design_name>")
    design_name = raw_architecture_description['name']
    if 'local' in raw_architecture_description:
        ASSERT_MSG(isinstance(raw_architecture_description['local'], list),
                   "v0.2 error: %s.local has to be a list of components" % design_name)

    if 'subtree' in raw_architecture_description:
        ASSERT_MSG(isinstance(raw_architecture_description['subtree'], dict),
                   "v0.2 error: %s.subtree has to be a dictionary" % design_name)

@register_function
def flatten_architecture_subtree(self, prefix, node_description, shared_attributes_dict= None): # For version 0.2
    if 'name' not in node_description:
        ERROR_CLEAN_EXIT('v0.2 error: archtecture description...',
                         ' "name" needs to be specified as a key in node description', node_description)

    if shared_attributes_dict is None and 'attributes' not in node_description:
        node_attrs = None
    elif shared_attributes_dict is not None and 'attributes' not in node_description:
        node_attrs = deepcopy(shared_attributes_dict)
    elif shared_attributes_dict is None and 'attributes' in node_description:
        node_attrs = node_description['attributes']
    else: #shared_attributes_dict is not None and attributes in node_description
        node_attrs = deepcopy(shared_attributes_dict)
        node_attrs.update(node_description['attributes'])

    node_name = node_description['name']
    # determine if the component is in list format
    list_length, name_base = v02_is_component_list(node_name, shared_attributes_dict)

    # if the component is in list format, flatten out and create the instances
    if not list_length == 0:
        for item_idx in range(list_length):
            item_prefix = prefix + '.' + name_base + '[' + str(item_idx) + ']'
            self.v02_tree_node_classification(node_description, item_prefix, node_attrs)

    # if the component is a standalone component, parse the component description directly
    else:
        prefix = prefix + '.' + node_name
        self.v02_tree_node_classification(node_description, prefix, node_attrs)

@register_function
def v02_tree_node_classification(self, node_description, prefix, node_attrs):
    if 'subtree' in node_description:
        ASSERT_MSG(isinstance(node_description['subtree'], dict),
                   "v0.2 error: %s.subtree has to be a dictionary" % prefix)
        self.flatten_architecture_subtree(prefix, node_description['subtree'], node_attrs)

    elif 'local' in node_description:
        ASSERT_MSG(isinstance(node_description['local'], list),
                   "v0.2 error: %s.local has to be a list of components" % prefix)
        for c_id in range(len(node_description['local'])):
            local_node_list_length, local_node_name_base = v02_is_component_list(
                node_description['local'][c_id]['name'], node_attrs)
            if not local_node_list_length == 0:
                for local_node_list_item_idx in range(local_node_list_length):
                    local_node_name = prefix + '.' + local_node_name_base + '[' + str(local_node_list_item_idx) + ']'
                    self.construct_new_leaf_node_description(local_node_name,
                                                             node_description['local'][c_id],
                                                             node_attrs)
            else:
                local_node_name = prefix + '.' + node_description['local'][c_id]['name']
                self.construct_new_leaf_node_description(local_node_name,
                                                         node_description['local'][c_id],
                                                         node_attrs)
    else:
        ERROR_CLEAN_EXIT('v0.2 error: architecture description...',
                         'Unrecognized tree node type', node_description)
