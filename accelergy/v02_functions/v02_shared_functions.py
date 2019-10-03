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
from accelergy.arithmetic_parsers import  parse_expression_for_arithmetic, process_arithmetic
from accelergy.utils import WARN

def v02_is_component_list(name, binding_dictionary = None):
    """
    determines if the component is a list according to its name
    if not, return 0; if yes, return list length
    it is possible that the last index of the list involves direct binding or arithmetical operations
    (operands could be strings that are keys in binding dictionary)
    """
    left_bracket_idx = name.find('[')
    range_flag = name.find('..')
    if left_bracket_idx == -1 or range_flag == -1:
        return 0, None
    else:
        if ']' not in name:
            WARN(name, ': located [ and .. but not ], typo?')
        else:
            name_base = name[:left_bracket_idx]
            right_bracket_idx = name.find(']')
            list_start_idx = str_to_int(name[left_bracket_idx+1:range_flag], binding_dictionary)
            list_end_idx = str_to_int(name[range_flag+2:right_bracket_idx], binding_dictionary)
            list_length = list_end_idx - list_start_idx + 1
            if list_end_idx < list_start_idx:
                list_length = -1
            return list_length, name_base

# parses the string indexes to integers
def str_to_int(str_to_be_parsed, binding_dictionary):
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