from accelergy.parsing_utils import *
from accelergy.component_class import ComponentClass


def arch_dict_2_obj(arch_dict, cc_classes, pc_classes):
    fully_defined_arch_dict = fully_define_arch_dict(arch_dict, cc_classes, pc_classes)
    return Architecture(fully_defined_arch_dict)


def fully_define_arch_dict(arch_dict, cc_classes, pc_classes):
    for cname, cinfo in arch_dict["components"].items():
        ASSERT_MSG(
            "class" in cinfo or "subclass" in cinfo,
            "Please specify class name for %s" % (cname),
        )
        class_name = cinfo["subclass"] if "subclass" in cinfo else cinfo["class"]

        if class_name in cc_classes:
            class_obj = cc_classes[class_name]
            for a in cinfo.get("required_actions", []):
                ASSERT_MSG(
                    a in class_obj._actions,
                    "Required action %s not found in compound component "
                    "class %s" % (a, class_name),
                )
        else:
            if class_name not in pc_classes:
                pc_classes[class_name] = ComponentClass(
                    {"name": class_name, "attributes": {}, "actions": []}
                )
            class_obj = pc_classes[class_name]
            for a in cinfo.get("required_actions", []):
                if a in class_obj._actions:
                    continue
                logging.info(
                    'Adding required action "%s" to class %s' % (a, class_name)
                )
                subcomp_action = {
                    "name": class_name,
                    "actions": [{"name": a, "arguments": {}}],
                }
                action = {"name": a, "subcomponents": [subcomp_action]}
                class_obj.add_action(action)

        attrs_to_be_applied = class_obj.get_default_attr_to_apply(cinfo["attributes"])
        for attr_name, attr_val in attrs_to_be_applied.items():
            cinfo["attributes"][attr_name] = attr_val
        cinfo["attributes"] = parse_expressions_sequentially_replacing_bindings(
            cinfo["attributes"],
            {},
            f"Architecture class {class_name} attributes",
        )
    return arch_dict


class Architecture(object):
    """Architecture class"""

    def __init__(self, arch_dict):
        self.version = arch_dict["version"]
        self.component_dict = {}
        for cname, cinfo in arch_dict["components"].items():
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
        ASSERT_MSG(
            compName in self.get_component_name_list(),
            "%s not found in architecture " % (compName),
        )
        return self.component_dict[compName]

    def generate_flattened_arch(self):
        from collections import OrderedDict

        flattened_arch = {
            "architecture": OrderedDict({"version": self.version, "local": []})
        }
        for cname in self.get_component_name_list():
            cobj = self.get_component(cname)
            dict_rep = OrderedDict(cobj.get_dict_representation())
            flattened_arch["architecture"]["local"].append(dict_rep)
        return flattened_arch

    @staticmethod
    def remove_brackets(name):
        """Removes the brackets from a component name in a list"""
        if "[" not in name and "]" not in name:
            return name
        if "[" in name and "]" in name:
            start_idx = name.find("[")
            end_idx = name.find("]")
            name = name[:start_idx] + name[end_idx + 1 :]
            name = Architecture.remove_brackets(name)
            return name


class ArchComp:
    def __init__(self, comp_dict):
        self.dict_representation = comp_dict
        if "attributes" not in self.dict_representation:
            self.dict_representation["attributes"] = {}

        self.dict_representation.setdefault("area_scale", 1.0)
        self.dict_representation.setdefault("energy_scale", 1.0)
        if "area_scale" in self.dict_representation["attributes"]:
            WARN(
                "Area scale in attributes is deprecated. Use it on the same level as the attributes, not a subkey."
            )
        if "energy_scale" in self.dict_representation["attributes"]:
            WARN(
                "Energy scale in attributes is deprecated. Use it on the same level as the attributes, not a subkey."
            )

    def get_attributes(self):
        return self.dict_representation["attributes"]

    def get_name(self):
        return self.dict_representation["name"]

    def get_class_name(self):
        if "subclass" in self.dict_representation:
            return self.dict_representation["subclass"]
        else:
            return self.dict_representation["class"]

    def get_dict_representation(self):
        return self.dict_representation

    def get_area_scale(self):
        if "area_scale" in self.dict_representation:
            return self.dict_representation["area_scale"]

        if "area_scale" in self.dict_representation["attributes"]:
            return self.dict_representation["attributes"]["area_scale"]

        return 1.0

    def get_energy_scale(self):
        if "energy_scale" in self.dict_representation:
            return self.dict_representation["energy_scale"]

        if "energy_scale" in self.dict_representation["attributes"]:
            return self.dict_representation["attributes"]["energy_scale"]

        return 1.0
