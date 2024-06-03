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

from inspect import signature
import copy
from importlib.machinery import SourceFileLoader
import math
import re
import traceback
from typing import Any, Callable, Union
from accelergy.utils.utils import *
from numbers import Number
from accelergy.utils.yaml import load_yaml, SCRIPTS_FROM
import accelergy.version as version
import ruamel.yaml
import os
import keyword

MATH_FUNCS = {
    "ceil": math.ceil,
    "comb": math.comb,
    "copysign": math.copysign,
    "fabs": math.fabs,
    "factorial": math.factorial,
    "floor": math.floor,
    "fmod": math.fmod,
    "frexp": math.frexp,
    "fsum": math.fsum,
    "gcd": math.gcd,
    "isclose": math.isclose,
    "isfinite": math.isfinite,
    "isinf": math.isinf,
    "isnan": math.isnan,
    "isqrt": math.isqrt,
    "ldexp": math.ldexp,
    "modf": math.modf,
    "perm": math.perm,
    "prod": math.prod,
    "remainder": math.remainder,
    "trunc": math.trunc,
    "exp": math.exp,
    "expm1": math.expm1,
    "log": math.log,
    "log1p": math.log1p,
    "log2": math.log2,
    "log10": math.log10,
    "pow": math.pow,
    "sqrt": math.sqrt,
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "atan2": math.atan2,
    "cos": math.cos,
    "dist": math.dist,
    "hypot": math.hypot,
    "sin": math.sin,
    "tan": math.tan,
    "degrees": math.degrees,
    "radians": math.radians,
    "acosh": math.acosh,
    "asinh": math.asinh,
    "atanh": math.atanh,
    "cosh": math.cosh,
    "sinh": math.sinh,
    "tanh": math.tanh,
    "erf": math.erf,
    "erfc": math.erfc,
    "gamma": math.gamma,
    "lgamma": math.lgamma,
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
    "nan": math.nan,
    "abs": abs,
    "round": round,
    "pow": pow,
    "sum": sum,
    "range": range,
    "len": len,
    "min": min,
    "max": max,
    "float": float,
    "int": int,
    "str": str,
    "bool": bool,
    "list": list,
    "tuple": tuple,
    "enumerate": enumerate,
    "getcwd": os.getcwd,
    "map": map,
}
SCRIPT_FUNCS = {}
LOADED_MATH_FUNCS_FROM = set()
# EXPR_CACHE = {}
# PARSED_EXPRESSIONS = set()


def propagate_required_keys(
    d1: dict, d2: dict, location: str, action_keys: bool = False
):
    """Propagate required keys from d1 to d2."""

    def propagate(key, setdefault: Any = None):
        if key in d2:
            return
        if key.upper() in d2:
            d2[key] = d2[key.upper()]
            return
        if key not in d1 and key.upper() not in d1:
            if setdefault is not None:
                d2[key] = setdefault
                return
            combined_keys = list(d1.keys()) + [k for k in d2.keys() if k not in d1]
            raise ValueError(
                f'Required key "{key}" not found in {location}. Found keys: '
                f'{", ".join(combined_keys)}'
            )
        d2[key] = d1.get(key, d1.get(key.upper()))

    if not version.input_version_greater_or_equal(0.4):
        # Legacy
        propagate("global_cycle_seconds", d2.get("latency", 1e-9))
        if isinstance(d2["global_cycle_seconds"], str):
            d2["global_cycle_seconds"] = (
                d2["global_cycle_seconds"].replace("ns", "e-9").replace(" ", "")
            )
        return

    propagate("global_cycle_seconds")
    propagate("action_latency_cycles", 1)
    if action_keys:
        return
    d2.setdefault("cycle_seconds", d2["global_cycle_seconds"])
    propagate("cycle_seconds")
    propagate("technology")
    propagate("n_instances", 1)


def assert_required_keys_numeric(d: dict, location: str, action_keys: bool = False):
    failmsg = f"Expected numeric value for key {{key}} in {location}."
    if not version.input_version_greater_or_equal(0.4):
        return

    if action_keys:
        for key in ["action_latency_cycles"]:
            if key in d and not isinstance(d[key], (int, float)):
                ERROR_CLEAN_EXIT(failmsg.format(key=key))
        return
    for key in ["global_cycle_seconds", "cycle_seconds", "n_instances"]:
        if key in d and not isinstance(d[key], (int, float)):
            ERROR_CLEAN_EXIT(failmsg.format(key=key))


def interpret_component_list(name, binding_dictionary=None):
    """
    determines if the component is a list according to its name
    (1) if not, return name as the base nae, None suffix, and None list length
    (2) if yes, return real base name, suffix, and list length
    it is possible that the index of the list involves direct binding or arithmetical operations
    (operands could be strings that are keys in binding dictionary)
    """
    ASSERT_MSG(
        isinstance(name, str),
        "is_component_list: parsing non-string type value -- %s" % name,
    )
    left_bracket_idx = name.find("[")
    range_flag = name.find("..")
    if left_bracket_idx == -1 or range_flag == -1:
        return name, None, None
    else:
        if "]" not in name:
            WARN(name, ": located [ and .. but not ], typo?")
        else:
            name_base = name[:left_bracket_idx]
            right_bracket_idx = name.find("]")
            list_start_idx = str_to_int(
                name[left_bracket_idx + 1 : range_flag], binding_dictionary
            )
            list_end_idx = str_to_int(
                name[range_flag + 2 : right_bracket_idx], binding_dictionary
            )
            list_suffix = "[" + str(list_start_idx) + ".." + str(list_end_idx) + "]"
            ASSERT_MSG(
                list_end_idx >= list_start_idx,
                "end index < start index %s (interpreted as %s)"
                % (name, name_base + list_suffix),
            )
            list_length = int(list_end_idx) - int(list_start_idx) + 1
            return name_base, list_suffix, list_length


def str_to_int(str_to_be_parsed, binding_dictionary):
    """parses the string indexes to integers"""
    v = parse_expression_for_arithmetic(
        str_to_be_parsed,
        binding_dictionary,
        "list index expression",
        strings_allowed=False,
    )
    if isinstance(v, Number):
        parsed_int = int(v)
    else:
        if binding_dictionary is None:
            parsed_int = int(str_to_be_parsed)
        else:
            parsed_int = (
                binding_dictionary[str_to_be_parsed]
                if str_to_be_parsed in binding_dictionary
                else int(str_to_be_parsed)
            )
    return parsed_int


def cast_to_numeric(x: Any) -> Union[int, float, bool]:
    if str(x).lower() == "true":
        return True
    if str(x).lower() == "false":
        return False
    if float(x) == int(x):
        return int(x)
    return float(x)


def is_quoted_string(expression):
    return isinstance(
        expression, ruamel.yaml.scalarstring.DoubleQuotedScalarString
    ) or isinstance(expression, ruamel.yaml.scalarstring.SingleQuotedScalarString)


def ruamel_str_to_normal_str(expression):
    return str(expression) if is_quoted_string(expression) else expression


def get_callable_lambda(func, expression):
    l = lambda *args, **kwargs: func(*args, **kwargs)
    l.__name__ = func.__name__
    l.__doc__ = func.__doc__
    l._original_accelergy_expression = expression
    l._func = func
    return l


def parse_expression_for_arithmetic(
    expression,
    binding_dictionary,
    location: str,
    strings_allowed: bool = True,
    use_bindings_after: str = None,
):
    refresh_math_funcs()

    if strings_allowed and is_quoted_string(expression):
        return expression

    # if id(expression) in PARSED_EXPRESSIONS:
    #     return expression

    try:
        return cast_to_numeric(expression)
    except:
        pass

    if not isinstance(expression, str):
        return expression

    if use_bindings_after is not None:
        keys = list(binding_dictionary.keys())
        index = keys.index(use_bindings_after)
        if index != -1:
            keys = keys[:index]
            binding_dictionary = {k: binding_dictionary[k] for k in keys}

    FUNCTION_BINDINGS = {}
    FUNCTION_BINDINGS["__builtins__"] = None  # Safety
    FUNCTION_BINDINGS.update(SCRIPT_FUNCS)
    FUNCTION_BINDINGS.update(MATH_FUNCS)

    try:
        v = eval(expression, FUNCTION_BINDINGS, binding_dictionary)
        infostr = f'Calculated {location} as "{expression}" = {v}.'
        if isinstance(v, str):
            v = ruamel.yaml.scalarstring.DoubleQuotedScalarString(v)
        if isinstance(v, Callable):
            v = get_callable_lambda(v, expression)
        success = True
    except Exception as e:
        errstr = f"Failed to evaluate: {expression}\n"
        errstr += f"Location: {location}\n"
        if (
            isinstance(expression, str)
            and expression.isidentifier()
            and expression not in binding_dictionary
            and expression not in FUNCTION_BINDINGS
        ):
            e = NameError(f"Name '{expression}' is not defined.")
        errstr += f"Problem encountered: {e.__class__.__name__}: {e}\n"
        err = errstr
        errstr += f"Available bindings: "
        bindings = {}
        bindings.update(binding_dictionary)
        bindings.update(SCRIPT_FUNCS)
        extras = []
        for k, v in bindings.items():
            if isinstance(v, Callable):
                bindings[k] = f"{k}{signature(getattr(v, '_func', v))}"
            else:
                extras.append(f"\n    {k} = {v}")
        errstr += "".join(f"\n\t{k} = {v}" for k, v in bindings.items())
        errstr += "\n\n" + err
        errstr += (
            f"Please ensure that the expression used is a valid Python expression.\n"
        )
        possibly_used = {
            k: bindings.get(k, FUNCTION_BINDINGS.get(k, "UNDEFINED"))
            for k in re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)", expression)
            if k not in keyword.kwlist
        }
        if possibly_used:
            errstr += f"The following may have been used in the expression:"
            errstr += "".join(f"\n\t{k} = {v}" for k, v in possibly_used.items())
            errstr += "\n"
        if strings_allowed:
            errstr += "Strings are allowed here. If you meant to enter a string, please wrap the\n"
            errstr += "expression in single or double quotes:\n"
            errstr += f"    Found expression: {expression}\n"
            errstr += f'    Expression as valid string: "{expression}"\n'
        success = False

    if not success:
        WARN(f'Evaluation of "{expression}" failed.')
        if strings_allowed and not version.input_version_greater_or_equal(0.4):
            errstr += (
                f"Expression will be treated as a string. This will be deprecated in version\n"
                f"0.4. Please wrap quotes around the expression to specify a string."
            )
            for l in errstr.splitlines():
                WARN(l)
            return expression
        raise ArithmeticError(f"{errstr}\n")

    # if expression not in EXPR_CACHE or EXPR_CACHE[expression] != v:
    INFO(infostr)

    # EXPR_CACHE[expression] = v
    # PARSED_EXPRESSIONS.add(id(v))
    return v


def parse_expressions_sequentially_replacing_bindings(
    expression_dictionary: dict,
    binding_dictionary: dict,
    location: str,
    strings_allowed: bool = True,
    propagate_keys: bool = True,
):
    parsed = {}
    for k, v in expression_dictionary.items():
        attrs = {k: v for k, v in binding_dictionary.items()}
        attrs.update(parsed)
        parsed[k] = parse_expression_for_arithmetic(
            v, attrs, f'{location}"{k}"', strings_allowed
        )
    if propagate_keys:
        propagate_required_keys(binding_dictionary, parsed, location)
    return parsed


def count_num_identical_comps(name):
    total_num_identical_comps = 1
    start_idx = name.find("[")
    end_idx = name.find("]")
    potential_range = name[start_idx + 1 : end_idx]
    if ".." in potential_range:
        range_start = int(potential_range.split("..")[0])
        range_end = int(potential_range.split("..")[1])
        range = range_end - range_start + 1
        total_num_identical_comps = total_num_identical_comps * range
    if "[" and "]" in name[end_idx + 1 :]:
        total_num_identical_comps = (
            total_num_identical_comps * count_num_identical_comps(name[end_idx + 1 :])
        )
    return total_num_identical_comps


def comp_name_within_range(comp_name, comp_name_w_reference_range):
    """Check if the component name is legal according to the specified component names"""

    if "[" not in comp_name:
        return True
    subname_vals_list = get_ranges_or_indices_in_name(comp_name)
    reference_ranges_list = get_ranges_or_indices_in_name(comp_name_w_reference_range)
    ASSERT_MSG(
        len(reference_ranges_list) == len(subname_vals_list),
        "subcomp name %s missing index specifications (should agree with the format %s"
        % (comp_name, comp_name_w_reference_range),
    )
    for idx in range(len(reference_ranges_list)):
        ref_range_tupe = reference_ranges_list[idx]
        ref_min = ref_range_tupe[0]
        ref_max = ref_range_tupe[1]
        subname_val = subname_vals_list[idx]
        if isinstance(subname_val, int):
            if subname_val < ref_min or subname_val > ref_max:
                return False
        if isinstance(subname_val, tuple):
            start = subname_val[0]
            end = subname_val[1]
            if start < ref_min or end > ref_max:
                return False
    return True


def get_ranges_or_indices_in_name(name):
    """recursive function that eventually collects all the list ranges/list indices in the specified component name"""

    exisiting_ranges = []
    start_idx = name.find("[")
    end_idx = name.find("]")
    range = name[start_idx + 1 : end_idx]
    if ".." in range:
        range_start = int(range.split("..")[0])
        range_end = int(range.split("..")[1])
        val = (range_start, range_end)
    else:
        val = int(range)
    exisiting_ranges.append(val)
    subname = name[end_idx + 1 :]
    if "[" and "]" not in subname:
        return exisiting_ranges
    else:
        for val in get_ranges_or_indices_in_name(subname):
            exisiting_ranges.append(val)
    return exisiting_ranges


def load_functions_from_file(path: str):
    path = path.strip()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find math function file {path}.")
    python_module = SourceFileLoader("python_plug_in", path).load_module()
    funcs = {}
    defined_funcs = [
        f for f in dir(python_module) if isinstance(getattr(python_module, f), Callable)
    ]
    for func in defined_funcs:
        INFO(f"Adding function {func} from {path} to the script library.")
        funcs[func] = getattr(python_module, func)
    SCRIPT_FUNCS.update(funcs)
    LOADED_MATH_FUNCS_FROM.add(path)


def set_script_paths():
    try:
        config = load_yaml(get_config_file_path())
    except FileNotFoundError:
        config = None
    if config is None:
        config = {}
    funcs = {}
    paths = config.get("math_functions", [])
    for path in paths:
        load_functions_from_file(path)
    SCRIPT_FUNCS.update(funcs)


def refresh_math_funcs():
    scripts = os.environ.get("ACCELERGY_MATH_FUNCTIONS", "").split(":")
    scripts = [s.strip() for s in scripts if s.strip()]
    scripts += SCRIPTS_FROM
    for script in scripts:
        if script in LOADED_MATH_FUNCS_FROM:
            continue
        load_functions_from_file(script)


set_script_paths()
