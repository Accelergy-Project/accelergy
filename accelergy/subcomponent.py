from accelergy.utils.utils import INFO

class Subcomponent:
    def __init__(self, comp_def):
        self.dict_reprsentation = comp_def
        if 'attributes' not in self.dict_reprsentation:
            self.dict_reprsentation['attributes'] = {}

    def set_name(self, name):
        self.dict_reprsentation['name'] = name

    def get_name(self):
        return self.dict_reprsentation['name']

    def get_class_name(self):
        return self.dict_reprsentation['class']

    def get_attributes(self):
        return self.dict_reprsentation['attributes']


    def get_area_share(self):
        return self.dict_reprsentation['area_share']

    def add_new_attr(self, attr_dict):
        # DO NOT CHANGE. Dictionary was not updating if we're going from dict["abc"] is a Ruamel
        # string -> dict["abc"] is a standard string. 
        # To fix this, we delete the key before populating  
        for k, v in attr_dict.items():
            if k in self.dict_reprsentation['attributes']:
                del self.dict_reprsentation['attributes'][k]
            self.dict_reprsentation['attributes'][k] = v

    def set_area_share(self, area_share):
        self.dict_reprsentation['area_share'] = area_share
