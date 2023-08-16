from abc import ABC, abstractmethod
from logging import info
from numbers import Number
import os
from typing import Callable, List, Union
from accelergy.utils.logging import ListLoggable
from accelergy.plug_in_interface.interface import Estimation
from accelergy.utils.utils import get_config_file_path
from accelergy.utils.yaml import load_yaml, write_yaml_file

class Estimator(ListLoggable, ABC):
    """ 
    Estimator base class. Estimator class must have "name" attribute, "percent_accuracy_0_to_100"
    attribute, and "get_area" method. Estimators may have any number of methods that are
    decorated with @action2energy.
    """
    name: Union[str, List[str]] = None
    percent_accuracy_0_to_100: Number = None

    def __init__(self, name: str=None):
        super().__init__(name=name)

    @abstractmethod
    def get_area(self) -> Union[Number, Estimation]:
        """ Returns the area in m^2 or an Estimation object with the area and units."""
        pass


def action2energy(func: Callable) -> Callable:
    """ 
    Decorator that adds an action to an Accelergy estimator. Actions are expected to return an
    energy value in Juoles or an Estimation object with the energy and units.
    """
    func._is_accelergy_action = True
    return func


def add_estimator_path(path: str, add_full_dir: bool = False):
    """ Adds a path to the list of Python plug-in paths in the Accelergy config file. """
    cfg_yaml = get_config_file_path()
    path = os.path.abspath(path)
    if add_full_dir:
        path = os.path.dirname(path)
    
    with open(os.path.expanduser(cfg_yaml), 'r') as f:
        cfg = load_yaml(f)
        python_paths = cfg.get('python_plug_ins', [])
        
    # Update the list of paths
    if path in python_paths:
        info(f'Path {path} already in the list of python paths.')
    else:
        cfg.update({'python_plug_ins': python_paths + [path]})
        info(f'Added path {path} to the list of python paths.')
        write_yaml_file(cfg_yaml, cfg)


def remove_estimator_path(path: str, remove_full_dir: bool = False):
    """ Removes a path from the list of Python plug-in paths in the Accelergy config file. """
    cfg_yaml = get_config_file_path()
    path = os.path.abspath(path)
    if remove_full_dir:
        path = os.path.dirname(path)
    
    with open(os.path.expanduser(cfg_yaml), 'r') as f:
        cfg = load_yaml(f)
        python_paths = cfg.get('python_plug_ins', [])
        
    # Update the list of paths
    if path not in python_paths:
        info(f'Path {path} not in the list of python paths.')
    else:
        cfg.update({'python_plug_ins': [p for p in python_paths if p != path]})
        info(f'Removed path {path} from the list of python paths.')
        write_yaml_file(cfg_yaml, cfg)
