from accelergy.ERT_generator import EnergyReferenceTableGenerator
from accelergy.energy_calculator import EnergyCalculator

import argparse, sys
from copy import deepcopy
from yaml import load
from accelergy.utils import accelergy_loader, ERROR_CLEAN_EXIT, WARN, INFO, ASSERT_MSG, accelergy_loader_ordered

def main():


    parser = argparse.ArgumentParser(
        description='Accelergy is an architecture-level energy estimator for accelerator designs. Accelergy allows '
                    ' users to describe the architecture of a design with user-defined compound components and generates energy '
                    'estimations according to the workload-generated action counts.')
    parser.add_argument('-o', '--outdir', type=str, default='./',
                        help = 'Path to output directory that stores '
                               'the ERT and/or flattened_architecture and/or energy estimation. '
                               'Default is current directory.')
    parser.add_argument('-p', '--precision', type=int, default='3',
                        help= 'Number of decimal points for generated energy values. '
                              'Default is 3.')
    parser.add_argument('-v', '--verbose', type=int, default = 0,
                        help= 'If set to 1, Accelergy outputs the interactions between the estimation plug-ins. '
                              'Default is 0')
    parser.add_argument('-s', '--ERT_summary', type=int, default = 1,
                        help= 'If set to 1, Accelergy outputs an easy-to-read '
                              'ERT summary that contains the average, min and max energy/action'
                              'for all the actions of all the components. '
                              'Default is 1')
    parser.add_argument('--enable_flattened_arch', type=int, default='0',
                        help= 'If set to 1, Accelergy outputs an architecture summary in the output directory and checks'
                              ' the validity of component names in the action counts file. '
                              'The flattened architecture includes all the interpreted attribute values and classes '
                              'for all the components in the design. '
                              'Default is 0.')

    parser.add_argument('files', nargs='*',
                        help= 'list of input files in arbitrary order.'
                              'Accelergy parses the top keys of the files to decide the type of input the file describes, '
                                                                    'e.g., architecture description, '
                                                                          'compound component class descriptions, etc. '
                        )

    args = parser.parse_args()
    path_arglist = args.files
    output_path = args.outdir
    precision = args.precision
    verbose = args.verbose
    flatten_arch_flag = args.enable_flattened_arch
    ERT_summary = args.ERT_summary

    print('\n#===================================================================================#')
    print('#=========================== Running Accelergy =====================================#')
    print('#===================================================================================#\n')

    raw_architecture_description, \
    raw_compound_class_description,\
    raw_action_counts,\
    raw_ERT,\
    raw_flattened_arch = interpret_input_path(path_arglist)
    INFO( 'Summary of collected inputs:'
    '\n   Architecture description found: %s '
    '\n   Compound component description found: %s '
    '\n   Action counts found: %s'
    '\n   ERT found: %s '
    '\n   Flattened architecture found: %s' % (raw_architecture_description is not None,
                                             raw_compound_class_description is not None,
                                             raw_action_counts is not None,
                                             raw_ERT is not None,
                                             raw_flattened_arch is not None))

    if raw_ERT is not None and raw_action_counts is not None:
        INFO('Accelergy found ERT and ACTION COUNTS '
             '\n----------> DIRECTLY PERFORM ENERGY ESTIMATION')
        if flatten_arch_flag == 0:
            raw_flattened_arch = None
        else:
            if raw_flattened_arch is None:
                ERROR_CLEAN_EXIT('enable_flattened_arch flag is set high, '
                                 'but no flattened architecture yaml file provided')
        estimator = EnergyCalculator()
        estimator.generate_estimations(raw_action_counts, raw_ERT, output_path, precision, raw_flattened_arch)

    elif raw_compound_class_description is not None and raw_architecture_description is not None:
        if raw_action_counts is None:
            INFO('Accelergy found ARCHITECTURE and COMPOUND COMPONENT but NO ERT or ACTION COUNTS  '
                 '\n---------->  PERFORM ERT GENERATION')
        else:
            INFO('Accelergy found ARCHITECTURE, COMPOUND COMPONENT, and ACTION COUNTS but NO ERT  '
                 '\n----------> PERFORM ERT GENERATION AND ENERGY ESTIMATION')

        generator = EnergyReferenceTableGenerator()
        generator.generate_ERTs(raw_architecture_description, raw_compound_class_description,
                                output_path, precision, flatten_arch_flag, verbose, ERT_summary)

        if raw_action_counts is not None:
            ert_path = output_path + '/' + 'ERT.yaml'
            raw_ERT = load(open(ert_path), accelergy_loader)
            if flatten_arch_flag == 0:
                raw_flattened_arch = None
            else:
                arch_path = output_path + '/' + 'flattened_architecture.yaml'
                raw_flattened_arch = load(open(arch_path), accelergy_loader)
            estimator = EnergyCalculator()
            estimator.generate_estimations(raw_action_counts, raw_ERT, output_path, precision, raw_flattened_arch)
    else:
        INFO('Not enough inputs to start computations. ')

def interpret_input_path(path_arglist):
    raw_architecture_description = None
    raw_compound_class_description = None
    raw_action_counts = None
    raw_ERT = None
    raw_flattened_arch = None

    available_keys = ['architecture',
                      'compound_components',
                      'action_counts',
                      'ERT',
                      'flattened_architecture']

    for file_path in path_arglist:

        file = load(open(file_path), accelergy_loader)
        for key in file:

            if key == 'architecture':
                content = file[key]
                #-------------------------------------------------------------------------
                # check syntax of input file
                #-------------------------------------------------------------------------
                ASSERT_MSG('version' in content, 'File content not legal: %s, %s must contain '
                           '"version" key'%(file_path,key))
                tree_root_name = None
                if content['version'] == 0.1:
                    tree_root_name = 'nodes'
                if content['version'] == 0.2:
                    tree_root_name = 'subtree'
                ASSERT_MSG(tree_root_name is not None, 'File content not legal: %s, '
                                                       'version %s not supported'%(file_path, content['version']))
                ASSERT_MSG(tree_root_name in content,
                           'File content not legal: %s, architecture description must contain %s key'
                           %(file_path, tree_root_name))
                ASSERT_MSG(type(content[tree_root_name]) is list,
                           'File content not legal: %s, %s key must have value of type list'
                           %(file_path, tree_root_name))
                #-------------------------------------------------------------------------
                # merge input file
                #-------------------------------------------------------------------------
                if raw_architecture_description is None:
                    raw_architecture_description = {'architecture': file[key]}
                else:
                    ERROR_CLEAN_EXIT('File content not legal: %s. '
                                     '\n Second architecture description detected... '
                                     'Only one architecture is allowed...'%(file_path))
                    # ASSERT_MSG(raw_architecture_description['architecture']['version'] == content['version'],
                    #            'File content not legal: %s, versions of two %s'
                    #            'related file do not match'%(file_path, key))
                    # raw_architecture_description[key].update(file[key])
            if key == 'compound_components':
                content = file[key]
                file_reload = load(open(file_path), accelergy_loader_ordered)
                #-------------------------------------------------------------------------
                # check syntax of input file
                #-------------------------------------------------------------------------
                ASSERT_MSG('version' in content and 'classes' in content,
                           'File content not legal: %s, %s must contain '
                           '"version" and "classes" keys'%(file_path, key))
                ASSERT_MSG(type(content['classes']) is list,
                           'File content not legal: %s, "classes" key must have value of type list' % file_path)
                #-------------------------------------------------------------------------
                # merge input file
                #-------------------------------------------------------------------------
                if raw_compound_class_description is None:
                   raw_compound_class_description = {'compound_components': file_reload[key]}
                else:
                    ASSERT_MSG(raw_compound_class_description['compound_components']['version']
                               == content['version'],
                               'File content not legal: %s, versions of two %s '
                               'related file do not match'%(file_path, key))

                    raw_compound_class_description[key]['classes'].extend(file_reload[key]['classes'])

            if key == 'action_counts':
                content = file[key]
                #-------------------------------------------------------------------------
                # check syntax of input file
                #-------------------------------------------------------------------------
                ASSERT_MSG('version' in content, 'File content not legal: %s, %s must contain '
                            '"version" key '%(file_path, key))
                if content['version'] == 0.1:
                    ASSERT_MSG('nodes' in content, 'v0.1 error... File content not legal: %s, %s must contain '
                                                     '"nodes" key ' % (file_path, key))
                    if raw_action_counts is None:
                       raw_action_counts = {key: content}
                    else:
                        ASSERT_MSG(raw_action_counts[key]['version'] == content['version'],
                                   'File content not legal: %s, versions of two %s'
                                   'related files do not match'%(file_path, key))
                        if "nodes" in content:
                            if "nodes" in raw_action_counts[key]:
                                raw_action_counts[key]["nodes"].extend(content["nodes"])
                            else:
                                raw_action_counts[key]["nodes"] = content["nodes"]

                if content['version'] == 0.2:

                    ASSERT_MSG('local' in content or 'subtree' in content, 'File content not legal: %s, %s must contain '
                               '"local"/"subtree" key '%(file_path, key))

                    if "local" in content:
                        ASSERT_MSG(type(content["local"]) is list,
                                   'File content not legal: %s, "local" key must have value of type list'
                                   %(file_path))

                    if "subtree" in content:
                        ASSERT_MSG(type(content["subtree"]) is list,
                                   'File content not legal: %s, "subtree" key must have value of type list'
                                   %(file_path))

                    if raw_action_counts is None:
                       raw_action_counts = {key: content}
                    else:
                        ASSERT_MSG(raw_action_counts[key]['version'] == content['version'],
                                   'File content not legal: %s, versions of two %s'
                                   'related files do not match'%(file_path, key))
                        if "local" in content:
                            if "local" in raw_action_counts[key]:
                                raw_action_counts[key]["local"].extend(content["local"])
                            else:
                                raw_action_counts[key]["local"] = content["local"]
                        if "subtree" in content:
                            if "subtree" in raw_action_counts[key]:
                                raw_action_counts[key]["subtree"].extend(content["subtree"])
                            else:
                                raw_action_counts[key]["subtree"] = content["subtree"]

            if key == 'ERT':
                content = file[key]
                ASSERT_MSG('version' in content and 'tables' in content,
                           'File content not legal: %s, ERT must contain '
                            '"version" and "tables" keys'%file_path)
                ASSERT_MSG(type(content['tables'] is dict),
                           'File content not legal: %s, "tables" key must have value of type dict' % file_path)
                if raw_ERT is None:
                   raw_ERT = {key: file[key]}
                else:
                    ASSERT_MSG(raw_ERT[key]['version'] == content['version'],
                               'File content not legal: %s, versions of two %s '
                               'related files do not match'%(file_path, key))
                    raw_ERT[key]['tables'].update(file[key]['tables'])

            if key == 'flattened_architecture':
                content = file[key]
                ASSERT_MSG('version' in content and 'components' in content,
                           'File content not legal: %s, flattened_architecture description must contain '
                            '"version" and "tables" keys'%file_path)
                ASSERT_MSG(type(content['components'] is dict),
                           'File content not legal: %s, "components" key must have value of type dict' % file_path)
                if raw_flattened_arch is None:
                   raw_flattened_arch = {key: file[key]}
                else:
                    ASSERT_MSG(raw_ERT['version'] == content['version'],
                               'File content not legal: %s, versions of two %s '
                               'related files do not match'%(file_path,key))
                    raw_flattened_arch[key]['components'].update(file[key]['components'])
            if key not in available_keys:
                WARN('File contains unrecognized information:', file_path, key,
                     '\n Accelergy only recognizes the following keys', available_keys)
            else:
                INFO('%s related info found in %s'%(key, file_path))

    return raw_architecture_description, raw_compound_class_description, raw_action_counts, raw_ERT, raw_flattened_arch