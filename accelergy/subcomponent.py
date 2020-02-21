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
        self.dict_reprsentation['attributes'].update(attr_dict)

    def set_area_share(self, area_share):
        self.dict_reprsentation['area_share'] = area_share