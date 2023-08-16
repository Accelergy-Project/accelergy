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

import math
from accelergy.utils import *
from numbers import Number

MATH_FUNCS = {
    'ceil': math.ceil, 'comb': math.comb, 'copysign': math.copysign, 'fabs': math.fabs,
    'factorial': math.factorial, 'floor': math.floor, 'fmod': math.fmod, 'frexp': math.frexp,
    'fsum': math.fsum, 'gcd': math.gcd, 'isclose': math.isclose, 'isfinite': math.isfinite,
    'isinf': math.isinf, 'isnan': math.isnan, 'isqrt': math.isqrt, 'ldexp': math.ldexp,
    'modf': math.modf, 'perm': math.perm, 'prod': math.prod, 'remainder': math.remainder,
    'trunc': math.trunc, 'exp': math.exp, 'expm1': math.expm1, 'log': math.log,
    'log1p': math.log1p, 'log2': math.log2, 'log10': math.log10, 'pow': math.pow, 'sqrt': math.sqrt,
    'acos': math.acos, 'asin': math.asin, 'atan': math.atan, 'atan2': math.atan2,
    'cos': math.cos, 'dist': math.dist, 'hypot': math.hypot, 'sin': math.sin,
    'tan': math.tan, 'degrees': math.degrees, 'radians': math.radians, 'acosh': math.acosh,
    'asinh': math.asinh, 'atanh': math.atanh, 'cosh': math.cosh, 'sinh': math.sinh,
    'tanh': math.tanh, 'erf': math.erf, 'erfc': math.erfc, 'gamma': math.gamma,
    'lgamma': math.lgamma, 'pi': math.pi, 'e': math.e, 'tau': math.tau,
    'inf': math.inf, 'nan': math.nan, 'abs': abs, 'round': round, 'pow': pow, 'sum': sum, 
    'range': range, 'len': len, 'min': min, 'max': max
}
EXPR_CACHE = {}
WARNINGS_LOGGED = []

def interpret_component_list(name, binding_dictionary = None):
    """
    determines if the component is a list according to its name
    (1) if not, return name as the base nae, None suffix, and None list length
    (2) if yes, return real base name, suffix, and list length
    it is possible that the index of the list involves direct binding or arithmetical operations
    (operands could be strings that are keys in binding dictionary)
    """
    ASSERT_MSG(isinstance(name, str), 'is_component_list: parsing non-string type value -- %s'%name)
    left_bracket_idx = name.find('[')
    range_flag = name.find('..')
    if left_bracket_idx == -1 or range_flag == -1:
        return name, None, None
    else:
        if ']' not in name:
            WARN(name, ': located [ and .. but not ], typo?')
        else:
            name_base = name[:left_bracket_idx]
            right_bracket_idx = name.find(']')
            list_start_idx = str_to_int(name[left_bracket_idx+1:range_flag], binding_dictionary)
            list_end_idx = str_to_int(name[range_flag+2:right_bracket_idx], binding_dictionary)
            list_suffix = '[' + str(list_start_idx) + '..' + str(list_end_idx) + ']'
            ASSERT_MSG(list_end_idx >= list_start_idx,
                       'end index < start index %s (interpreted as %s)' % (name, name_base + list_suffix))
            list_length = int(list_end_idx) - int(list_start_idx) + 1
            return name_base, list_suffix, list_length

def str_to_int(str_to_be_parsed, binding_dictionary):
    """parses the string indexes to integers"""
    v = parse_expression_for_arithmetic(str_to_be_parsed, binding_dictionary)
    if isinstance(v, Number):
        parsed_int = int(v)
    else:
        if binding_dictionary is None:
            parsed_int = int(str_to_be_parsed)
        else:
            parsed_int = binding_dictionary[str_to_be_parsed] if str_to_be_parsed in binding_dictionary \
                                                          else int(str_to_be_parsed)
    return parsed_int

def arithmetic_failed_evaluate_warn(expr, setting, name, binding_dictionary, error=False):
    if (expr, setting) in WARNINGS_LOGGED:
        return

    warnstring = f'Failed to evaluate "{expr}". Setting {name}.{setting}="{expr}". Available bindings: {binding_dictionary}'
    warnstring = 'WARN: ' + warnstring if not error else 'ERROR: ' + warnstring

    print(warnstring)
    WARNINGS_LOGGED.append((expr, setting))

def parse_expression_for_arithmetic(expression, binding_dictionary, force_convert_numeric_on_fail=False):
    """
    Expression contains the operands and the op type,
    binding dictionary contains the numerical values of the operands (if they are strings)
    """
    try:
        try:
            if float(expression) == int(expression):
                return int(expression)
            return float(expression)
        except:
            pass
        MATH_FUNCS['__builtins__'] = None # Safety
        v = eval(expression, MATH_FUNCS, binding_dictionary)
        if float(v) == int(v):
            v = int(v)
        infostr = f'Calculated "{expression}" = {v}'
    except:
        v = expression
        if force_convert_numeric_on_fail:
            v = int(''.join(filter(str.isdigit, expression)))
            infostr = f'Calculated "{expression}" = {v}'
        else:
            infostr = f'Found non-numeric expression {expression}. Available bindings: {binding_dictionary}'

    if expression not in EXPR_CACHE or EXPR_CACHE[expression] != v:
        INFO(infostr)
    EXPR_CACHE[expression] = v
    return v

def count_num_identical_comps(name):
    total_num_identical_comps = 1
    start_idx = name.find('[')
    end_idx = name.find(']')
    potential_range = name[start_idx + 1 : end_idx]
    if '..' in potential_range:
        range_start = int(potential_range.split('..')[0])
        range_end = int(potential_range.split('..')[1])
        range = range_end - range_start + 1
        total_num_identical_comps = total_num_identical_comps * range
    if '[' and ']' in name[end_idx + 1: ]:
        total_num_identical_comps = total_num_identical_comps * count_num_identical_comps(name[end_idx + 1: ])
    return total_num_identical_comps


def comp_name_within_range(comp_name, comp_name_w_reference_range):
    """ Check if the component name is legal according to the specified component names"""

    if '[' not in comp_name:
        return True
    subname_vals_list = get_ranges_or_indices_in_name(comp_name)
    reference_ranges_list = get_ranges_or_indices_in_name(comp_name_w_reference_range)
    ASSERT_MSG(len(reference_ranges_list) == len(subname_vals_list),
               'subcomp name %s missing index specifications (should agree with the format %s'%(comp_name, comp_name_w_reference_range))
    for idx in range(len(reference_ranges_list)):
        ref_range_tupe = reference_ranges_list[idx]
        ref_min = ref_range_tupe[0]
        ref_max = ref_range_tupe[1]
        subname_val = subname_vals_list[idx]
        if type(subname_val) is int:
            if subname_val < ref_min or subname_val > ref_max:
                return False
        if type(subname_val) is tuple:
            start = subname_val[0]
            end = subname_val[1]
            if start < ref_min or end > ref_max:
                return False
    return True


def get_ranges_or_indices_in_name(name):
    """ recursive function that eventually collects all the list ranges/list indices in the specified component name"""

    exisiting_ranges = []
    start_idx = name.find('[')
    end_idx = name.find(']')
    range = name[start_idx + 1: end_idx]
    if '..' in range:
        range_start = int(range.split('..')[0])
        range_end = int(range.split('..')[1])
        val = (range_start, range_end)
    else:
        val = int(range)
    exisiting_ranges.append(val)
    subname = name[end_idx+1:]
    if '[' and ']' not in subname:
        return exisiting_ranges
    else:
        for val in get_ranges_or_indices_in_name(subname):
            exisiting_ranges.append(val)
    return exisiting_ranges
