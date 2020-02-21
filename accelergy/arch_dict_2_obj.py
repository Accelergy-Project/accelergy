from accelergy.parsing_utils import *

def arch_dict_2_obj(arch_dict, cc_classes, pc_classes):
    fully_defined_arch_dict = fully_define_arch_dict(arch_dict, cc_classes, pc_classes)
    return Architecture(fully_defined_arch_dict)

def fully_define_arch_dict(arch_dict, cc_classes, pc_classes):
    for cname, cinfo in arch_dict['components'].items():
        ASSERT_MSG('class' in cinfo or 'subclass' in cinfo, 'Please specify class name for %s'%(cname))
        class_name = cinfo['subclass'] if 'subclass' in cinfo else cinfo['class']
        ASSERT_MSG(class_name in cc_classes or class_name in pc_classes, 'class "%s" is not defined'%class_name)
        class_obj = cc_classes[class_name] if class_name in cc_classes else pc_classes[class_name]
        attrs_to_be_applied = class_obj.get_default_attr_to_apply(cinfo['attributes'])
        for attr_name, attr_val in attrs_to_be_applied.items():
            cinfo['attributes'][attr_name] = attr_val
        for attr_name, attr_val in cinfo['attributes'].items():
            if type(attr_val) is str:
                if attr_val in cinfo['attributes']:
                    cinfo['attributes'][attr_name] = cinfo['attributes'][attr_val]
                op_type, op1, op2 = parse_expression_for_arithmetic(attr_val, cinfo['attributes'])
                if op_type is not None: cinfo['attributes'][attr_name] = process_arithmetic(op1, op2, op_type)
    return arch_dict

class Architecture(object):
    """Architecture class"""
    def __init__(self, arch_dict):
        self.version = arch_dict['version']
        self.component_dict = {}
        for cname, cinfo in arch_dict['components'].items():
            self.component_dict[cname] = ArchComp(cinfo)

    def __iter__(self):
        self.key_idx = 0
        return self

    def __next__(self):
        # stop iteration if all the components are iterated
        if self.key_idx == len(self.component_dict.keys()):
            raise StopIteration
        key = list(self.component_dict.keys())[self.key_idx]
        self.key_idx = self.key_idx + 1
        return self.component_dict[key]

    def get_component_name_list(self):
        return list(self.component_dict.keys())

    def get_component(self, compName):
        ASSERT_MSG(compName in self.get_component_name_list(), '%s not found in architecture '%(compName))
        return self.component_dict[compName]

    def generate_flattened_arch(self):
        from collections import OrderedDict
        flattened_arch = {'architecture': OrderedDict({'version': self.version, 'local': []})}
        for cname in self.get_component_name_list():
            cobj = self.get_component(cname)
            dict_rep = OrderedDict(cobj.get_dict_representation())
            flattened_arch['architecture']['local'].append(dict_rep)
        return flattened_arch


    @staticmethod
    def remove_brackets(name):
        """Removes the brackets from a component name in a list"""
        if '[' not in name and ']' not in name:
            return name
        if '[' in name and ']' in name:
            start_idx = name.find('[')
            end_idx = name.find(']')
            name = name[:start_idx] + name[end_idx + 1:]
            name = Architecture.remove_brackets(name)
            return name

class ArchComp():
    def __init__(self, comp_dict):
        self.dict_representation = comp_dict
        if 'attributes' not in self.dict_representation:
            self.dict_representation['attributes'] = {}

    def get_attributes(self):
        return self.dict_representation['attributes']

    def get_name(self):
        return self.dict_representation['name']

    def get_class_name(self):
        if 'subclass' in self.dict_representation:
            return  self.dict_representation['subclass']
        else:
            return self.dict_representation['class']

    def get_dict_representation(self):
        return self.dict_representation






