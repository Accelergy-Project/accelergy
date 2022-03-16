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
    optype, op1, op2 = parse_expression_for_arithmetic(str_to_be_parsed, binding_dictionary)
    if optype is None:
        if binding_dictionary is None:
            parsed_int = int(str_to_be_parsed)
        else:
            parsed_int = binding_dictionary[str_to_be_parsed] if str_to_be_parsed in binding_dictionary \
                                                          else int(str_to_be_parsed)
    else:
        parsed_int = int(process_arithmetic(op1, op2, optype))

    return parsed_int

def parse_expression_for_arithmetic(expression, binding_dictionary):
    """
    Expression contains the operands and the op type,
    binding dictionary contains the numerical values of the operands (if they are strings)
    """
    # parse for the supported arithmetic operations
    if '*' in expression:
        op_type = '*'
    elif 'round' in expression and '/' in expression:
        op_type = 'round'
    elif 'round_up' in expression and '/' in expression:
        op_type = 'round_up'
    elif '/' in expression:
        op_type = '/'
    elif '//' in expression:
        op_type = '//'
    elif '%' in expression:
        op_type = '%'
    elif '+' in expression:
        op_type = '+'
    elif '-' in expression:
        op_type = '-'
    elif 'log2(' and ')' in expression:
        op_type = 'log2'
    else:
        op_type = None

    # if the expression is an arithmetic operation
    if op_type is not None:

        if op_type == 'round':
            oprands = expression[5:]
            op1 = oprands.split('/')[0][1:]
            op2 = oprands.split('/')[1][:-1]
        elif op_type == 'round_up':
            oprands = expression[8:]
            op1 = oprands.split('/')[0][1:]
            op2 = oprands.split('/')[1][:-1]
        elif not op_type == 'log2':
            op1 = expression[:expression.find(op_type)].strip()
            op2 = expression[expression.find(op_type) + 1:].strip()

        # log2 only needs one operand, and needs to be processed differently
        else:
            op1 = expression[expression.find('(') + 1: expression.find(')')].strip()
            op2 = None

        if op1 in binding_dictionary:
            op1 = binding_dictionary[op1]
        else:
            try:
                op1 = int(op1)
            except ValueError:
                print('arithmetic expression:', expression, '\n',
                      'available operand-value binding:', binding_dictionary)
                ERROR_CLEAN_EXIT('arithmetic operation located, but cannot parse operand value')

        # if the operation needs 2 operands
        if op2 is not None:
            if op2 in binding_dictionary:
                op2 = binding_dictionary[op2]
            else:
                try:
                    op2 = int(op2)
                except ValueError:
                    print('arithmetic expression:', expression, '\n',
                          'available operand-value binding:', binding_dictionary)
                    ERROR_CLEAN_EXIT('arithmetic operation located, but cannot parse operand value')
    # if the expression is not an arithmetic operation
    else:
        op1 = None
        op2 = None
    return op_type, op1, op2

def process_arithmetic(op1, op2, op_type):
    """ Turns string expression into arithmetic operation"""
    ASSERT_MSG(type(op1) is not str and type(op2) is not str, 'operands have strings %s, %s'%(op1, op2))
    if op_type == '*':
        result = op1 * op2
    elif op_type == '/':
        result = op1/op2
    elif op_type == '//':
        result = op1//op2
    elif op_type == '%':
        result = math.remainder(op1, op2)
    elif op_type == '-':
        result = int(op1 -op2)
    elif op_type == '+':
        result = int(op1 + op2)
    elif op_type == 'log2':
        result = int(math.ceil(math.log2(op1)))
    elif op_type == 'round':
        result = int(round(op1/op2, 0)) # round according to the first decimal
    elif op_type == 'round_up':
        result = int(math.ceil(op1/op2))
    else:
        result = None
        ERROR_CLEAN_EXIT('wrong op_type')
    return result


def remove_brackets(name):
    """Removes the brackets from a component name in a list"""
    if '[' not in name and ']' not in name:
        return name
    if '[' in name and ']' in name:
        start_idx = name.find('[')
        end_idx = name.find(']')
        name = name[:start_idx] + name[end_idx + 1:]
        name = remove_brackets(name)
        return name

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
