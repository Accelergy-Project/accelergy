from yaml import load
from importlib.machinery import SourceFileLoader
from accelergy.utils import *

def plug_in_path_to_obj(path_list, output_prefix):
    """
    instantiate a list of estimator plug-in objects for later queries
    estimator plug-in paths are specified in config file
    """
    estimator_plug_ins = []
    for estimator_dir in path_list:
        for root, directories, file_names in os.walk(estimator_dir):
            for file_name in file_names:
                if '.estimator.yaml' in file_name:
                    INFO('estimator plug-in identified by: ', root + os.sep + file_name)
                    estimator_spec = load(open(root + os.sep + file_name), accelergy_loader)
                    for key, val in estimator_spec.items():
                        if not key == 'version':
                            estimator_info = val
                    module_name = estimator_info['module']
                    class_name = estimator_info['class']
                    file_path = root + '/' + module_name + '.py'
                    estimator_module = SourceFileLoader(class_name, file_path).load_module()

                    if 'parameters' not in estimator_info:
                        if not module_name == 'cacti_wrapper':
                            estimator_obj = getattr(estimator_module, class_name)()
                        else:
                            # for CACTI to use prefix to avoid contention
                            estimator_obj = getattr(estimator_module, class_name)(output_prefix)
                    else:
                        estimator_obj = getattr(estimator_module, class_name)( estimator_info['parameters'])
                    estimator_plug_ins.append(estimator_obj)
    return estimator_plug_ins