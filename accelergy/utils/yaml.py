# Copyright (c) 2019 Yannan Wu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import functools
import os
import glob
import re
import io
from typing import Callable, List, Dict, Any, Set, Union, OrderedDict
import ruamel.yaml
import accelergy.utils.utils as utils
import warnings
from ruamel.yaml.error import ReusedAnchorWarning

yaml = ruamel.yaml.YAML(typ="rt")
# yaml.default_flow_style = None
yaml.indent(mapping=4, sequence=4, offset=2)
yaml.preserve_quotes = True
warnings.simplefilter("ignore", ReusedAnchorWarning)


def recursive_mutator_stop(func):
    cache = set()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        assert not kwargs, (
            f"Recursive mutator stop only works with non-keyword arguments. "
            f"Args were {args} and kwargs were {kwargs}."
        )
        k = id(args[0])
        if k in cache:
            return args[0]
        cache.add(k)
        try:
            result = func(*args, **kwargs)
        finally:
            cache.remove(k)
        return result

    return wrapper


def load_file_and_includes(path: str, string: Union[str, None] = None) -> str:
    """
    Load a YAML file and recursively load any included YAML files
    :param path: string that specifies the path of the YAML file to be loaded
    :param string: string that contains the YAML content to be loaded
    :return: string that contains the loaded YAML content
    """
    assert (string is None) != (
        path is None
    ), "Must specify either path or string, but not both."
    if string is None:
        with open(path, "r") as f:
            string = f.read()
    if "!include" not in string:
        return string
    if "\n" not in string:
        return load_file_and_includes(
            os.path.join(os.path.dirname(path), string), None
        )
    else:
        lines = [s + "\n" for s in string.split("\n")]
    basename = os.path.dirname(path)

    for i, l in enumerate(lines):
        if not l.startswith("!include"):
            continue
        len_whitespace = len(l) - len(l.lstrip())
        s = re.sub(r"^\s*!include(dir)?", "", l).strip()
        s = re.sub(r"^\s*:\s*", "", s)
        replace = "\n" + load_file_and_includes(os.path.join(basename, s))
        replace = replace.replace("\n", "\n" + " " * len_whitespace) + "\n"
        lines[i] = replace
    return "".join(lines)


@recursive_mutator_stop
def merge_check(x: Union[Dict[str, Any], List[Any], Any]) -> None:
    if isinstance(x, list):
        for i, v in enumerate(x):
            x[i] = merge_check(v)
    elif isinstance(x, dict):
        found_merge = False
        for k, v in list(x.items()):
            x[k] = merge_check(v)
            if str(k) == "<<<" or str(k) == "<<":
                assert not found_merge, \
                    f'Cannot have multiple "<<<" or "<<" keys in a dict. ' \
                    f'Keys were {list(x.keys())}'
                found_merge = True
                x = merge(x, x.pop(k), str(k) == "<<<")
    return x


def load_yaml(
    path: str = None, string: str = None
) -> Union[Dict[str, Any], None]:
    """
    Load YAML content from a file or string
    :param path: string that specifies the path of the YAML file to be loaded
    :param string: string that contains the YAML content to be loaded
    :return: parsed YAML content
    """
    assert (string is None) != (
        path is None
    ), "Must specify either path or string, but not both."
    # Recursively parse through x, replacing any <<< with a recursive merge
    # print(f'Calling recursive merge check on {x}')
    return merge_check(yaml.load(load_file_and_includes(path, string)))


@recursive_mutator_stop
def merge(
    merge_into: dict, tomerge: Union[dict, list, tuple], recursive: bool = True
) -> dict:
    if isinstance(tomerge, (list, tuple)):
        assert not recursive, \
            f'Cannot recursively merge multiple dicts. Please only specify ' \
            f'one dict under the "<<<" key.'
        combined = dict()
        for m in tomerge:
            combined = merge(combined, m, recursive)
        tomerge = combined
    if not isinstance(tomerge, dict):
        raise ValueError(
            f'Expected a dict under the "<<<" or "<<" keys, but '
            f"got {tomerge}"
        )
    if not isinstance(merge_into, dict):
        raise ValueError(
            f'Expected to merge into a dict with the "<<<" key, '
            f"but got {merge_into}"
        )

    for k, v in tomerge.items():
        if k not in merge_into:
            merge_into[k] = v
        elif (
            isinstance(merge_into[k], dict)
            and isinstance(v, dict)
            and recursive
        ):
            merge_into[k] = merge(merge_into[k], v, recursive)
    if not recursive:
        print(f"Non-recursive merge of {tomerge} into {merge_into}")
    return merge_into


def my_represent_none(self, data: None) -> str:
    """
    Represent None as 'null' in YAML
    :param self: YAML representer object
    :param data: None object to be represented
    :return: 'null' string
    """
    return self.represent_scalar("tag:yaml.org,2002:null", "null")


yaml.representer.add_representer(type(None), my_represent_none)


def my_change_ordereddict_to_dict(
    self, dictionary: OrderedDict
) -> Dict[str, Any]:
    """
    Change an OrderedDict to a dictionary in YAML
    :param self: YAML representer object
    :param dictionary: OrderedDict object to be represented
    :return: dictionary object
    """
    d = {}
    for key in dictionary.keys():
        d[key] = dictionary[key]
    return self.represent_dict(dictionary)


yaml.representer.add_representer(OrderedDict, my_change_ordereddict_to_dict)


def include_constructor(
    self, node: ruamel.yaml.nodes.ScalarNode
) -> Union[Dict[str, Any], None]:
    """
    Constructor that parses the !include relative_file_path and loads the file
    from relative_file_path
    :param self: YAML constructor object
    :param node: YAML node object
    :return: parsed YAML content
    """
    filepath = self.construct_scalar(node)
    if filepath[-1] == ",":
        filepath = filepath[:-1]
    return load_yaml(os.path.join(self._root, filepath))


yaml.constructor.add_constructor("!include", include_constructor)


def includedir_constructor(
    self, node: ruamel.yaml.nodes.ScalarNode
) -> List[Dict[str, Any]]:
    """
    Constructor that parses the !includedir relative_file_path and loads the
    file from relative_file_path
    :param self: YAML constructor object
    :param node: YAML node object
    :return: list of parsed YAML contents
    """
    filepath = self.construct_scalar(node)
    if filepath[-1] == ",":
        filepath = filepath[:-1]
    dirname = os.path.join(self._root, filepath)
    yamllist = []
    for filename in glob.glob(dirname + "/*.yaml"):
        yamllist.append(load_yaml(filename))
    return yamllist


yaml.constructor.add_constructor("!includedir", includedir_constructor)


@recursive_mutator_stop
def recursive_unorder_dict(to_unorder: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(to_unorder, dict):
        return {k: recursive_unorder_dict(v) for k, v in to_unorder.items()}
    elif isinstance(to_unorder, list):
        return [recursive_unorder_dict(v) for v in to_unorder]
    return to_unorder


@recursive_mutator_stop
def callables2strings(to_convert: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(to_convert, dict):
        to_convert = {k: callables2strings(v) for k, v in to_convert.items()}
    elif isinstance(to_convert, list):
        to_convert = [callables2strings(v) for v in to_convert]
    elif isinstance(to_convert, Callable):
        to_convert = str(to_convert)
    return to_convert


def write_yaml_file(filepath: str, content: Dict[str, Any]) -> None:
    """
    Write YAML content to a file
    :param filepath: string that specifies the destination file path
    :param content: YAML string that needs to be written to the destination file
    :return: None
    """
    if os.path.exists(filepath):
        os.remove(filepath)
    if os.path.dirname(filepath):
        utils.create_folder(os.path.dirname(filepath))
    out_file = open(filepath, "a")
    out_file.write(to_yaml_string(content))


def to_yaml_string(content: Dict[str, Any]) -> str:
    """
    Convert YAML content to a string
    :param content: YAML content to be converted to a string
    :return: string representation of the YAML content
    """
    dumpstream = io.StringIO()
    yaml.dump(callables2strings(
        recursive_unorder_dict(content)), stream=dumpstream)
    return dumpstream.getvalue()
