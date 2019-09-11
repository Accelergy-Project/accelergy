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
    start_idx = name.find('[')
    if start_idx == -1:
        return 0, None
    else:
        if ']' not in name:
            WARN(name, ': located [ but not ], typo?')
        else:
            name_base = name[:start_idx]
            end_idx = name.find(']')
            n = name[start_idx+1: end_idx]
            # check if the tail involves arithmetic operations
            optype, op1, op2 = parse_expression_for_arithmetic(n, binding_dictionary)
            if optype is None:
                if n in binding_dictionary:
                    # tail is a direct binding, directly retrieve the numerical value
                    n = binding_dictionary[n]
                list_length = int(n)
            else:
                list_length = int(process_arithmetic(op1, op2, optype))
            return list_length, name_base