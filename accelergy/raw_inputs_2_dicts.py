from yaml import load
from copy import deepcopy
from accelergy.parsing_utils import *
from collections import OrderedDict


class RawInputs2Dicts():
    def __init__(self, input_info):
        self.parser_version = input_info['parser_version']
        self.possible_top_keys = {'architecture', 'compound_components', 'action_counts', 'ERT',
                                  'flattened_architecture', 'variables'}
        self.path_arglist = input_info['path_arglist']
        self.flatten_arch_spec_dict = {}
        self.hier_arch_spec_dict = {}
        self.cc_classes_dict = {}
        self.pc_classes_dict = {}
        self.ERT_dict = {}
        self.action_counts_dict = {}
        self.config = None
        self.arch_variables = {}
        self.load_and_construct_dicts()


    def check_input_parser_version(self, input_parser_version, input_file_type, input_file_path):
        # Accelergy v0.3 can parser input files of version 0.2 and 0.3 (except ERT)
        if input_file_type is not 'ERT':
            if input_file_type == 'config':
                ASSERT_MSG(input_parser_version == 0.2 or input_parser_version == 0.3,
                           'config file version outdated. Latest version is v.%s \
                            \n Please delete the original file, and run accelergy to create a new default config file.\
                            \n Please ADD YOUR USER_DEFINED file paths BACK to the updated config file at \
                            ~/.config/accelergy/accelergy_config.yaml' % self.parser_version)
            else:
                ASSERT_MSG(input_parser_version == 0.2 or input_parser_version == 0.3,
                           'input parser version for %s is v%s, cannot be parsed by current accelergy v%s'
                           % (input_file_path, input_parser_version, self.parser_version))

            # if input_parser_version < self.parser_version:
            #     WARN('Your %s input file has an older version. The most up-to-date version is %s '
            #          '--> Only the value of the "version" key needs to be updated '
            #          '(the syntax of the content does not need to be updated) '
            #          '\n --- OK'
            #          %(input_file_path, self.parser_version))
        else:
            ASSERT_MSG(input_parser_version == 0.3,
                       'ERT input file is version v%s, cannot be parsed by Accelergy v%s. '
                       '\n---> Please use Accelergy v0.2/ update your ERT input file format/ '
                       'regenerate the ERT using your design description'
                       % (input_parser_version, self.parser_version))

    def load_and_construct_dicts(self):
        # load and classify input files
        input_file_info = {}
        for path in self.path_arglist:
            if os.path.isfile(path):
                loaded_content_list = self.load_file(path)
                for loaded_content in loaded_content_list:
                    if loaded_content['top_key'] not in input_file_info:
                        input_file_info[loaded_content['top_key']] = []
                    input_file_info[loaded_content['top_key']].append(loaded_content)
            elif os.path.isdir(path):
                for root, directories, file_names in os.walk(path):
                    for file_name in file_names:
                        file_path = os.path.join(root, file_name)
                        loaded_content_list = self.load_file(file_path)
                        for loaded_content in loaded_content_list:
                            if loaded_content['top_key'] not in input_file_info:
                                input_file_info[loaded_content['top_key']] = []
                            input_file_info[loaded_content['top_key']].append(loaded_content)
            else:
                ERROR_CLEAN_EXIT('Cannot recognize input path: ', path)

        if 'variables' in input_file_info:
            for variable_spec in input_file_info['variables']:
                for var_name, var_var in variable_spec['content']['variables'].items():
                    if type(var_var) is str:
                        if var_var in variable_spec['content']['variables']:
                            variable_spec['content']['variables'][var_name] = variable_spec['content']['variables'][var_var]
                        else:
                            op_type, op1, op2 = parse_expression_for_arithmetic(var_var, variable_spec['content']['variables'])
                            if op_type is not None:
                                variable_spec['content']['variables'][var_name] = process_arithmetic(op1, op2, op_type)
                self.arch_variables.update(variable_spec['content']['variables'])

        for top_key, top_key_file_list in input_file_info.items():
            if top_key != 'variables':
                for file_info in top_key_file_list:
                    YAML_parser_fname = top_key + '_input_parser'
                    file_path = file_info['path']
                    INFO('Parsing file %s for %s info' % (file_path, top_key))
                    getattr(self, YAML_parser_fname)(file_info)

        # construct new or parse existing config file
        self.construct_parse_config_file()

        # construct primitive classes dictionary
        self.primitive_classes_input_parser()

    def load_file(self, file_path):
        if '.yaml' in file_path:
            file_obj = open(file_path)
            file = load(file_obj, accelergy_loader)
            loaded_content_list =[]
            for top_key in file.keys():
                if top_key not in self.possible_top_keys:
                    WARN('Cannot recognize the top key "%s" in file %s' % (top_key, file_path))
                else:
                    # YAML_parser_fname = top_key + '_input_parser'
                    loaded_content_list.append({'top_key': top_key, 'content': file, 'path': file_path})
                    # getattr(self, YAML_parser_fname)(file_info)
            file_obj.close()
            return loaded_content_list

    def architecture_input_parser(self, file_info):
        """responsible for parsing the loaded architecture YAML file """

        top_key = 'architecture'
        content = file_info['content']
        file_path = file_info['path']

        # only one arch file is allowed
        ASSERT_MSG(self.hier_arch_spec_dict == {},
                   'Second architecture description detected at %s ... '
                   'Only one architecture is allowed...' % (file_path))

        # check top-level syntax of input file
        ASSERT_MSG('version' in content[top_key], '%s must contain "version" key' % (file_path))
        self.check_input_parser_version(content[top_key]['version'], 'architecture', file_path)

        if 'subtree' in content[top_key]:
            ASSERT_MSG(type(content[top_key]['subtree']) is list,
                       'File content not legal: %s, subtree key must have value of type list' % (file_path))
        elif 'local' in content[top_key]:
            ASSERT_MSG(type(content[top_key]['local']) is list,
                       'File content not legal: %s, local key must have value of type list' % (file_path))
        else:
            ERROR_CLEAN_EXIT('Architecture Description must contain subtree or local key at top-level')

        # create arch spec dict
        self.hier_arch_spec_dict = {'architecture': {}}
        self.flatten_arch_spec_dict = {'version': self.parser_version, 'components': {}}
        arch_comp_list = content[top_key]
        if 'subtree' in arch_comp_list:
            arch_name = arch_comp_list['subtree'][0]['name']
            global_attributes = {} if 'attributes' not in arch_comp_list['subtree'][0] \
                else arch_comp_list['subtree'][0]['attributes']
            if 'attributes' in arch_comp_list['subtree']:
                ASSERT_MSG(type(arch_comp_list['subtree'['attributes']]) is dict,
                           'attributes must be specified in dictionary format')
            arch_comp_list['subtree'][0] = self.tree_node_classification(OrderedDict(arch_comp_list['subtree'][0]), arch_name, global_attributes)
        else:
            arch_comp_list = self.tree_node_classification(arch_comp_list, None, {})
        self.hier_arch_spec_dict['architecture'] = OrderedDict(arch_comp_list)

    def tree_node_classification(self, node_description, prefix, node_attrs):
        """
        Classify the nodes in a level to recursively parse (subtree) or construct components (local) for the architecture
        :param node_description: a dictionary that describes the subtree and local nodes in this level
        :param prefix: the prefix that needs to be preappend to all of the node names in this level
        :param node_attrs: a dictionary that contains the explicitly specified attributes and the projected upper level shared attributes
        :return: None
        """
        # interpret the mapping and arithmetic operations in the raw description
        all_attrs = deepcopy(node_attrs)
        all_attrs.update(self.arch_variables)
        for attr_name, attr_val in node_attrs.items():
            if type(attr_val) is str:
                if attr_val in all_attrs:
                    node_attrs[attr_name] = all_attrs[attr_val]
                    all_attrs[attr_name] = all_attrs[attr_val]
                else:
                    op_type, op1, op2 = parse_expression_for_arithmetic(attr_val, all_attrs)
                    if op_type is not None:
                        node_attrs[attr_name] = process_arithmetic(op1, op2, op_type)
                        all_attrs[attr_name] = node_attrs[attr_name]

        if 'subtree' in node_description:
            ASSERT_MSG(isinstance(node_description['subtree'], list), " %s.subtree has to be a list"%(prefix))
            node_description['subtree'] = self.parse_architecture_subtree(node_description['subtree'], prefix, node_attrs)

        if 'local' in node_description:
            ASSERT_MSG(isinstance(node_description['local'], list),
                       "error: %s.local has to be a list of components"%prefix)
            for c_id in range(len(node_description['local'])):
                node_info = node_description['local'][c_id]
                ASSERT_MSG('name' in node_info, 'name must be specified for each node')
                if 'attributes' not in node_info:
                    node_info['attributes'] = {}
                else:
                    ASSERT_MSG(type(node_info['attributes']) is dict,
                    '%s: attributes must be specified in dictionary format'%(node_info['name']))
                for attr_name, attr_val in node_attrs.items():
                    if attr_name not in node_info['attributes']:
                        node_info['attributes'][attr_name] = attr_val

                all_attrs = deepcopy(node_info['attributes'])
                all_attrs.update(self.arch_variables)
                for attr_name, attr_val in node_info['attributes'].items():
                    if type(attr_val) is str:
                        if attr_val in all_attrs:
                            node_info['attributes'][attr_name] = all_attrs[attr_val]
                            all_attrs[attr_name] = all_attrs[attr_val]
                        else:
                            op_type, op1, op2 = parse_expression_for_arithmetic(attr_val, all_attrs)
                            if op_type is not None and type(op1) is not str and type(op2) is not str:
                                node_info['attributes'][attr_name] = process_arithmetic(op1, op2, op_type)
                                all_attrs[attr_name] = node_info['attributes'][attr_name]
                name_base, list_suffix, list_length = interpret_component_list(node_info['name'], all_attrs)
                if list_suffix is not None:
                    node_info['name'] = name_base + list_suffix

                node_description['local'][c_id] = OrderedDict(node_info)

                # generate the flattened version of the architecture
                local_node_name = prefix + '.' + node_info['name'] if prefix is not None else node_info['name']
                node_info['name'] = local_node_name
                self.flatten_arch_spec_dict['components'][local_node_name] = node_info

        if 'subtree' not in node_description and 'local' not in node_description:
            ERROR_CLEAN_EXIT('Unrecognized tree node type', node_description)

        return node_description

    def parse_architecture_subtree(self, subtree_description, prefix, shared_attributes_dict=None):
        ASSERT_MSG(isinstance(subtree_description, list), '%s.subtree needs to be a list'%prefix)

        for subtree_idx in range(len(subtree_description)):
            subtree_item_description = subtree_description[subtree_idx]
            if 'name' not in subtree_item_description:
                ERROR_CLEAN_EXIT('error: architecture description...',
                                 ' "name" needs to be specified as a key in node description', subtree_item_description)

            if shared_attributes_dict is None and 'attributes' not in subtree_item_description:
                node_attrs = None
            elif shared_attributes_dict is not None and 'attributes' not in subtree_item_description:
                node_attrs = deepcopy(shared_attributes_dict)
            elif shared_attributes_dict is None and 'attributes' in subtree_item_description:
                node_attrs = subtree_item_description['attributes']
            else:  # shared_attributes_dict is not None and attributes in node_description
                node_attrs = deepcopy(shared_attributes_dict)
                node_attrs.update(subtree_item_description['attributes'])

            all_attrs = deepcopy(node_attrs)
            all_attrs.update(self.arch_variables)
            node_name = subtree_item_description['name']
            name_base, list_suffix, list_length = interpret_component_list(node_name, all_attrs)
            if list_suffix is not None:
                node_name = name_base + list_suffix
            subtree_item_description['name'] = node_name
            item_prefix = prefix + '.' + node_name  # generated for the flattened arch
            subtree_description[subtree_idx] = OrderedDict(self.tree_node_classification(subtree_item_description, item_prefix, node_attrs))
        return subtree_description  # accumulated hierarchical info for the hierarchical arch

    def compound_components_input_parser(self, file_info):
        """responsible for parsing the loaded compound component description YAML files """

        top_key = 'compound_components'
        file_path = file_info['path']
        file_reload = load(open(file_path), accelergy_loader_ordered)
        content = file_reload

        # check top level syntax, check parser version
        ASSERT_MSG('version' and 'classes' in content[top_key],
                   'File content not legal: %s, %s must contain '
                   '"version" and "classes" keys' % (file_path, top_key))
        self.check_input_parser_version(content[top_key]['version'], 'compound_component', file_path)
        ASSERT_MSG(type(content[top_key]['classes']) is list,
                   'File content not legal: %s, "classes" key must have value of type list' % file_path)

        # check syntax of each specified cc class and add into the cc_class_dict
        cc_classes_list = content[top_key]['classes']
        for cc_class in cc_classes_list:
            ASSERT_MSG('name' in cc_class.keys() and 'attributes' in cc_class.keys()
                       and 'actions' in cc_class.keys() and 'subcomponents' in cc_class.keys(),
                       'missing required keys in compound component class description: \n %s' % cc_class)
            if cc_class['name'] in self.cc_classes_dict:
                WARN('Redefined compound component class %s in file %s' % (cc_class['name'], file_path))
            for subcomponent_info in cc_class['subcomponents']:
                ASSERT_MSG('name' in subcomponent_info.keys() and 'class' in subcomponent_info.keys(),
                           '"name" and "class" keys must be specified for the subcomponents of the '
                           'compound component class: %s' % (cc_class['name']))
                if 'area_share' not in subcomponent_info:
                    subcomponent_info['area_share'] = 1  # default area share is 1
            for action_info in cc_class['actions']:
                ASSERT_MSG('name' in action_info.keys() and 'subcomponents' in action_info.keys(),
                           '"name" and "subcomponents" keys must be specified for compound action %s' % (
                           action_info['name']))
                for subcomponent_actions in action_info['subcomponents']:
                    ASSERT_MSG('actions' in subcomponent_actions and 'name' in subcomponent_actions,
                               '"name" and "actions" keys of the subcomponent must be specified for compound action'
                               ' %s' % (action_info['name']))
                    for subcomponent_action in subcomponent_actions['actions']:
                        ASSERT_MSG('name' in subcomponent_action,
                                   '"name" key of the subcomponent action needs to be specified for '
                                   'compound action: %s, subcomponent: %s' % (
                                   action_info['name'], subcomponent_actions['name']))
                        if 'action_share' not in subcomponent_action:
                            if 'repeat' in subcomponent_action:
                                subcomponent_action['action_share'] = subcomponent_action['repeat']
                            else:
                                subcomponent_action['action_share'] = 1  # default action share is 1
            self.cc_classes_dict[cc_class['name']] = deepcopy(cc_class)

    def construct_parse_config_file(self):
        """load exisiting config file content (if any)/ create a default config file"""

        possible_config_dirs = ['.' + os.sep, os.path.expanduser('~') + '/.config/accelergy/']
        config_file_name = 'accelergy_config.yaml'
        for possible_dir in possible_config_dirs:
            if os.path.exists(possible_dir + config_file_name):
                original_config_file_path = possible_dir + config_file_name
                original_content_obj = open(original_config_file_path)
                original_content = load(original_content_obj, accelergy_loader)
                original_content_obj.close()
                INFO('config file located:', original_config_file_path)
                print('config file content: \n', original_content)
                if 'version' not in original_content:
                    ERROR_CLEAN_EXIT('config file has no version number, cannot proceed')
                file_version = original_content['version']
                self.check_input_parser_version(file_version, 'config', original_config_file_path)
                self.config = original_content
                return

        create_folder(possible_config_dirs[1])
        config_file_path = possible_config_dirs[1] + config_file_name
        curr_file_path = os.path.abspath(__file__)
        accelergy_share_folder_path = os.path.abspath(curr_file_path + '../../../../../../share/accelergy/')
        default_estimator_path = os.path.abspath(accelergy_share_folder_path + '/estimation_plug_ins/')
        default_pc_lib_path = os.path.abspath(accelergy_share_folder_path + '/primitive_component_libs/')
        config_file_content = {'version': self.parser_version,
                               'estimator_plug_ins': [default_estimator_path],
                               'primitive_components': [default_pc_lib_path]}
        INFO('Accelergy creating default config at:', possible_config_dirs[1] + config_file_name, 'with:\n',
             config_file_content)
        write_yaml_file(config_file_path, config_file_content)
        self.config = config_file_content

    def primitive_classes_input_parser(self):
        """construct a dictionary for primitive classes"""
        primitive_class_paths = self.config['primitive_components']
        for pc_path in primitive_class_paths:
            if '.yaml' in pc_path:
                self.expand_primitive_component_lib_info(pc_path)
            for root, directories, file_names in os.walk(pc_path):
                for file_name in file_names:
                    if '.lib.yaml' in file_name:
                        pc_path = root + os.sep + file_name
                        self.expand_primitive_component_lib_info(pc_path)

        ASSERT_MSG(not len(self.pc_classes_dict) == 0, 'No primitive component class found, '
                                                       'please check if the paths in config file are correct')

    def expand_primitive_component_lib_info(self, pc_path):
        primitive_component_list_obj = open(pc_path)
        primitive_component_list = load(primitive_component_list_obj, accelergy_loader)
        primitive_component_list_obj.close()
        for idx in range(len(primitive_component_list['classes'])):
            pc_description = primitive_component_list['classes'][idx]
            if pc_description['name'] in self.pc_classes_dict:
                WARN(pc_description['name'], 'redefined in', pc_path)
            self.pc_classes_dict[pc_description['name']] = deepcopy(pc_description)
        INFO('primitive component file parsed: ', pc_path)

    def ERT_input_parser(self, file_info):
        top_key = 'ERT'
        file_path = file_info['path']
        content = file_info['content'][top_key]
        ERT_component_entry_list = content['tables']

        ASSERT_MSG('version' and 'tables' in content, 'ERT input must contain the "version" and "tables" keys')
        ASSERT_MSG(isinstance(content['tables'], list), 'ERT tables must be in the form of list')
        self.check_input_parser_version(content['version'], 'ERT', file_path)

        for ERT_component_entry in ERT_component_entry_list:
            ASSERT_MSG('name' and 'actions' in ERT_component_entry,
                       '"name" and "actions" keys must be specified in each ERT component entry')
            component_name = ERT_component_entry['name']
            action_dict_summary = {}
            action_list = ERT_component_entry['actions']
            for action in action_list:
                if action['name'] not in action_dict_summary: action_dict_summary[action['name']] = []
                action_dict_summary[action['name']].append(action)
            self.ERT_dict[component_name] = action_dict_summary

    def action_counts_input_parser(self, file_info):
        top_key = 'action_counts'
        file_path = file_info['path']
        ASSERT_MSG('version' in file_info['content'][top_key],
                   'Please specify the version of the action counts file: %s' % (file_path))
        self.check_input_parser_version(file_info['content'][top_key]['version'], 'action counts', file_path)
        action_counts_dict = file_info['content'][top_key]
        ASSERT_MSG('subtree' in action_counts_dict or 'local' in action_counts_dict,
                   'the action counts must contain the "subtree" key or "local" key at the top level: %s' % file_path)
        self.flatten_action_counts(None, action_counts_dict)

    def flatten_action_counts(self, prefix, node_description):
        if 'local' in node_description:
            local_nodes = node_description['local']
            ASSERT_MSG(isinstance(local_nodes, list), 'local nodes are not specified in list format in action counts')
            for local_node in local_nodes:
                ASSERT_MSG("name" and 'action_counts' in local_node, '"name" and "action_counts" need to be '
                                                                     'specified as a keys in action count local node descriptions: %s' % local_node)
                if prefix is None:
                    full_name = local_node['name']
                else:
                    full_name = prefix + '.' + local_node['name']
                self.action_counts_dict[full_name] = local_node['action_counts']

        if 'subtree' in node_description:
            subtree_nodes = node_description['subtree']
            ASSERT_MSG(isinstance(subtree_nodes, list),
                       'subtree nodes are not specified in list format in action counts')
            for subtree_node_description in subtree_nodes:
                ASSERT_MSG("name" in subtree_node_description, ' "name" need to be specified in the subtree node: %s'
                           % subtree_node_description)
                if prefix is None:
                    subtree_prefix = subtree_node_description['name']
                else:
                    subtree_prefix = prefix + '.' + subtree_node_description['name']
                self.flatten_action_counts(subtree_prefix, subtree_node_description)

    def get_hier_arch_spec_dict(self):
        ASSERT_MSG(not self.hier_arch_spec_dict == {}, 'Cannot get hierarchical architecture spec from raw inputs')
        return self.hier_arch_spec_dict

    def get_flatten_arch_spec_dict(self):
        ASSERT_MSG(not self.flatten_arch_spec_dict == {}, 'Cannot get architecture spec from raw inputs')
        return self.flatten_arch_spec_dict

    def get_pc_classses(self):
        ASSERT_MSG(not self.pc_classes_dict == {}, 'Cannot get primitive component class from raw inputs')
        return self.pc_classes_dict

    def get_cc_classses(self):
        if self.cc_classes_dict == {}:
            WARN('No compound component classes specified, architecture can only contain primitive components')
        return self.cc_classes_dict

    def get_estimation_plug_in_paths(self):
        ASSERT_MSG(self.config is not None and 'estimator_plug_ins' in self.config,
                   'config is not properly defined \n %s' % self.config)
        path_list = self.config['estimator_plug_ins']
        return path_list

    def get_action_counts_dict(self):
        if self.action_counts_dict == {}:
            WARN('No action counts are specified as yaml input')
        return self.action_counts_dict

    def get_ERT_dict(self):
        if self.ERT_dict == {}:
            WARN('No ERT is specified as yaml input')
        return self.ERT_dict

    def get_available_inputs(self):
        available_inputs = []
        if not self.flatten_arch_spec_dict == {}:
            available_inputs.append('architecture_spec')
        if not self.cc_classes_dict == {}:
            available_inputs.append('compound_component_classes')
        if not self.action_counts_dict == {}:
            available_inputs.append('action_counts')
        if not self.ERT_dict == {}:
            available_inputs.append('ERT')
        return available_inputs