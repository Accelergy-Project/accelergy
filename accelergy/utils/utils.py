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

import logging
import os, sys

from copy import deepcopy
from typing import List

import logging


def create_folder(directory):
    """
    Checks the existence of a directory, if does not exist, create a new one
    :param directory: path to directory under concern
    :return: None
    """
    os.makedirs(directory, exist_ok=True)


def merge_dicts(dict1, dict2):
    merge_dict = deepcopy(dict1)
    merge_dict.update(dict2)
    return merge_dict


def ERROR_CLEAN_EXIT(*argv):
    ERROR("")
    ERROR(
        "================= An error has caused Accelergy to crash. Error below ================="
    )
    ERROR("")
    ERROR(*argv)
    sys.exit(1)


def ERROR(*argv):
    for v in argv:
        for l in str(v).splitlines():
            logging.getLogger("").error(l)


def WARN(*argv):
    for v in argv:
        for l in str(v).splitlines():
            logging.getLogger("").warn(l)


def INFO(*argv):
    for v in argv:
        for l in str(v).splitlines():
            logging.getLogger("").info(l)


def ASSERT_MSG(expression, msg):
    if not expression:
        raise AssertionError(msg)


def remove_brackets(name):
    """Removes the brackets from a component name in a list"""
    if "[" not in name and "]" not in name:
        return name
    if "[" in name and "]" in name:
        start_idx = name.find("[")
        end_idx = name.find("]")
        name = name[:start_idx] + name[end_idx + 1 :]
        name = remove_brackets(name)
        return name


def indent_list_text_block(prefix: str, list_to_print: List[str]):
    if not list_to_print:
        return ""
    return "\n| ".join(
        [f"{prefix}"] + [str(l).replace("\n", "\n|  ") for l in list_to_print]
    )


def get_config_file_path() -> str:
    possible_config_dirs = [
        "." + os.sep,
        os.path.expanduser("~") + "/.config/accelergy/",
    ]
    config_file_name = "accelergy_config.yaml"
    for possible_dir in possible_config_dirs:
        if os.path.exists(possible_dir + config_file_name):
            path = os.path.join(possible_dir, config_file_name)
            INFO(f"Located config file at {path}.")
            return path
    raise FileNotFoundError(
        f"Could not find Accelergy config file. Run 'accelergy' to "
        f"generate a default config file at {possible_config_dirs[1]}."
    )
