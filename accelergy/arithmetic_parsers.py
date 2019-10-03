from accelergy.utils import ERROR_CLEAN_EXIT, WARN, INFO, ASSERT_MSG
import math
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
