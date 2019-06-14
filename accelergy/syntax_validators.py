#----------------------------------------------------
# Validators for checking the syntax of input files
#----------------------------------------------------

# validator for estimator API syntax
from accelergy.utils import ERROR_CLEAN_EXIT

def validate_estimator_API(estimatorAPI):

    if not type(estimatorAPI) is dict:
        ERROR_CLEAN_EXIT('estimatorAPI is not a dictionary', estimatorAPI)

    if 'version' not in estimatorAPI:
        ERROR_CLEAN_EXIT('estimatorAPI no version found', estimatorAPI)

    estimator_info = None
    for key, val in estimatorAPI.items():
        if not key == 'version':
            estimator_info = val
    if estimator_info is None:
        ERROR_CLEAN_EXIT('estimatorAPI contains no estimator information', estimatorAPI)

    if 'module' not in estimator_info:
        ERROR_CLEAN_EXIT('no module specified in esitmatorAPI '
                         '(module value should be the same as esimtator python wrapper file name)', estimatorAPI)

    if 'class' not in estimator_info:
        ERROR_CLEAN_EXIT('no class specified in estimatorAPI', estimatorAPI)

def validate_primitive_classes(primitive_class_description):
    if type(primitive_class_description) is not dict:
        ERROR_CLEAN_EXIT('primitive class description should be a dictionary')

    if 'version' not in primitive_class_description:
        ERROR_CLEAN_EXIT('primitive class description no version found')

    if 'classes' not in primitive_class_description:
        ERROR_CLEAN_EXIT('primitive class description no list of classes found')

    primitive_classes = primitive_class_description['classes']
    if type(primitive_classes) is not list:
        ERROR_CLEAN_EXIT('primitive classes are not described in terms of a list')

    for primitive_class in primitive_classes:
        if type(primitive_class) is not dict:
            ERROR_CLEAN_EXIT('each primitive class should be described as a dictionary')
        if 'name' not in primitive_class:
            ERROR_CLEAN_EXIT('primitive class name not found', primitive_class)
        if 'actions' not in primitive_class:
            ERROR_CLEAN_EXIT('primitive class actions not found', primitive_class)
        if 'attributes' not in primitive_class:
            ERROR_CLEAN_EXIT('primitive class attributes not found', primitive_class)
