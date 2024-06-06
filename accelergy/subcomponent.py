from accelergy.utils.utils import INFO


class Subcomponent:
    def __init__(self, comp_def):
        self.dict_representation = comp_def
        if "attributes" not in self.dict_representation:
            self.dict_representation["attributes"] = {}

        if "energy_scale" in self.dict_representation["attributes"]:
            self.set_energy_scale(
                self.dict_representation["attributes"]["energy_scale"]
            )
        self.set_energy_scale(self.dict_representation["energy_scale"])

    def set_name(self, name):
        self.dict_representation["name"] = name

    def get_name(self):
        return self.dict_representation["name"]

    def get_class_name(self):
        return self.dict_representation["class"]

    def get_attributes(self):
        return self.dict_representation["attributes"]

    def get_area_scale(self):
        return self.dict_representation["area_scale"]

    def get_energy_scale(self):
        return self.dict_representation["energy_scale"]

    def add_new_attr(self, attr_dict):
        # DO NOT CHANGE. Dictionary was not updating if we're going from dict["abc"] is a Ruamel
        # string -> dict["abc"] is a standard string.
        # To fix this, we delete the key before populating
        for k, v in attr_dict.items():
            if k in self.dict_representation["attributes"]:
                del self.dict_representation["attributes"][k]
            self.dict_representation["attributes"][k] = v

    def set_area_scale(self, area_scale):
        self.dict_representation["area_scale"] = area_scale

    def set_energy_scale(self, energy_scale):
        self.dict_representation["energy_scale"] = energy_scale
