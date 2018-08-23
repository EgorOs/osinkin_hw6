#!/usr/bin/env python3
from calcs import Calculator, Token, tokenize, represent_as_tree, to_postfix
from string import ascii_lowercase
import copy


def merge_tokens(*args, integer_devision=False):
    new_token = Token('')
    new_token.pos = min([t.pos for t in args])
    new_token.end_pos = max([t.pos for t in args])
    new_token.priority = 0

    ch_queue = [t.ch for t in args if t.priority == 0]
    sign_queue = [t.ch for t in args if t.priority != 0]
    priority = max(args[0].priority, args[1].priority)
    merged_len = len(ch_queue)

    # Not power sign
    if priority < 3:
        new_val = int(ch_queue.pop(0))
        for i in range(len(ch_queue)):
            val = int(ch_queue.pop(0))
            sign = sign_queue.pop(0)
            if sign == '+':
                new_val += val
            elif sign == '-':
                new_val -= val
            elif sign == '*':
                new_val *= val
            elif sign == '/':
                new_val /= val
                if integer_devision:
                    new_val = round(new_val)
    else:
        new_val = ch_queue.pop(-1)
        for i in range(len(ch_queue)):
            new_val = ch_queue.pop(-1) ** new_val

    new_token.ch = str(new_val)
    new_token.merged_len = merged_len
    if new_val < 0:
        sign = copy.copy(new_token)
        sign.ch = '-'
        new_token.ch = new_token.ch[1::]
        return [sign, new_token]
    return [new_token]


def simplify_with_var(node):
    pos = node[0].pos
    end_pos = node[-1].pos
    if len(node) > 4:
        calculable = []
        incalculable = []
        tokens = node.copy()
        first_var = []
        prev_token = None
        if tokens[0].ch in set(ascii_lowercase):
            first_var.append(tokens.pop(0))
        for token in tokens:
            if token.ch in set(ascii_lowercase):
                incalculable.append(prev_token)
                incalculable.append(token)
            elif str(token.ch).isdigit():
                if prev_token:
                    calculable.append(prev_token)
                calculable.append(token)
            prev_token = token
        incalculable = first_var + incalculable
        calculable = merge_tokens(*calculable, integer_devision=True)
        if incalculable[0].ch in set(ascii_lowercase):
            result = incalculable + calculable
        else:
            result = calculable + incalculable
    else:
        result = node
    result[0].pos = pos
    result[0].end_pos = end_pos
    return result


def merge(s1, operator, s2):
    s1, s2 = int(s1), int(s2)
    if operator == '+':
        return str(s1 + s2)
    elif operator == '-':
        return str(s1 - s2)
    elif operator == '*':
        return str(s1 * s2)
    elif operator == '/':
        return str(int(s1 / s2))
    elif operator == '^':
        return str(s1 ** s2)


class AbstractOptimiser:
    def process(self, graph):
        g = self.pre_process(graph)

        result = self.process_internal(g)

        return self.post_process(result)

    def pre_process(self, graph):
        return tokenize(graph)

    def process_internal(self, graph):
        return graph

    def post_process(self, result):
        return result


class DoubleNegativeOptimiser(AbstractOptimiser):
    # -(-a) -> a

    def process_internal(self, graph):
        chars = [str(t.ch) for t in graph]
        n = len(chars)
        new_opcodes = []
        i = 0
        while True:
            if i >= n:
                break
            if i < n - 4:
                pattern = [*chars[i:i + 3], chars[i + 4]]
                if pattern == ['-', '(', '-', ')']:
                    new_opcodes += ['+', str(chars[i + 3])]
                    i += 5
                else:
                    new_opcodes.append(chars[i])
                    i += 1

            else:
                new_opcodes.append(chars[i])
                i += 1
        return new_opcodes


class IntegerCostantsOptimiser(AbstractOptimiser):
    # a + 4*2 -> a + 8
    def process_internal(self, graph):
        if len(graph) < 3:
            return graph
        tree = represent_as_tree(graph)
        priority_lst = sorted(tree.keys(), reverse=True)
        new_token_lst = []
        prev_priority = None
        prev_key = None
        higher_nodes = {}
        for key in priority_lst:
            branch = tree[key]
            for node in branch:
                if not prev_key:
                    if [t.ch for t in node if t.ch in set(ascii_lowercase)]:
                        # put variables to the start or to the end of node,
                        # and calculate the rest
                        result = simplify_with_var(node)
                        result[0].calculable = False
                    else:
                        result = merge_tokens(*node, integer_devision=True)
                        result[0].calculable = True
                    pos, end_pos = result[0].pos, result[0].end_pos
                    higher_nodes[(pos, end_pos)] = result
                else:
                    tokens = node.copy()
                    node_pos = tokens[0].pos
                    node_end_pos = tokens[-1].pos
                    result = []
                    left_side = []
                    left_sign = []
                    right_side = []
                    right_sign = []
                    for limits in higher_nodes.keys():
                        pos, end_pos = limits
                        if node_end_pos == pos:
                            tokens.pop(-1)  # remove outdated tokens
                            right_sign = [tokens.pop(-1)]
                            right_side = higher_nodes[limits]

                        if node_pos == end_pos:
                            tokens.pop(0)  # remove outdated tokens
                            left_sign = [tokens.pop(0)]
                            left_side = higher_nodes[limits]

                    if not [t.ch for t in tokens]:
                        if left_side and left_side[0].calculable:
                            new_exp = left_side + left_sign + tokens
                            tokens = merge_tokens(*new_exp,
                                                  integer_devision=True)
                            left_side, left_sign = [], []
                        if right_side and right_side[0].calculable:
                            new_exp = tokens + right_sign + right_side
                            tokens = merge_tokens(*new_exp,
                                                  integer_devision=True)
                            right_side, right_sign = [], []

                    result += left_side + left_sign + tokens + right_sign + right_side

            prev_key = key

        return result

    def post_process(self, result):
        new_opcodes = [str(i.ch) for i in result]
        return new_opcodes


class UnnecessaryOperationsOptimiser(AbstractOptimiser):
    # a * 0 -> 0
    # a + 0 -> 0
    # *     a or True -> True
    # *     a and False -> False
    pass


def test_double_negetive():
    double_negate_tests = [
        ('-(-a)', 'a'),
        ('-(-5)', '5'),
        ('-(a+b)+c-(-d)', 'ab+-c+d+'),
    ]

    for case, exp in double_negate_tests:
        tokens = list(case)
        calc = Calculator(tokens, [DoubleNegativeOptimiser()])
        calc.optimise()

        if str(calc) != exp:
            print('Error in case for "{}". Actual "{}", expected {}'
                  .format(case, calc, exp))


def test_integer_constant_optimiser():
    # test cases помеченные (*) не обязательны к прохождению. 
    integer_constant_optimiser_tests = [
        (['1'], ['1']),
        (['1', '+', '2'], ['3']),
        (['1', '-', '2'], ['1-']),
        (['2', '*', '2'], ['4']),
        (['2', '/', '2'], ['1']),
        (['2', '^', '10'], ['1024']),
        (['a', '+', '2', '*', '4'], ['a8+', '8a+']),

        (['2', '+', 'a', '+', '3'], ['5a+', 'a5+']),  # (*)
    ]

    for case, exp in integer_constant_optimiser_tests:
        calc = Calculator(case, [DoubleNegativeOptimiser(),
                                 IntegerCostantsOptimiser()])

        calc.optimise()

        if str(calc) not in exp:
            print('Error in case for "{}". Actual "{}", expected {}'
                  .format(case, calc, exp))


def test_simplifier_optimiser():
    # test cases помеченные (*) не обязательны к прохождению. 
    simplifier_optimiser_test = [
        ('a+0', ['a']),
        ('a*1', ['a']),
        ('a*0', ['0']),
        ('b/b', ['1']),
        ('a-a', ['0']),
        ('a+(b-b)', ['a']),
        ('a+(7-6-1)', ['a']),
        ('a^0', ['1']),
        ('a-(-(-a))', ['0']),

        ('a+a+a', ['a3*', '3a*']),  # (*)
        ('(a-b)-(a-b)', ['0']),  # (*)
        ('(a-b)/(a-b)', ['1']),  # (*)
        ('(a+b)+(a+b)', ['ab+2*', '2ab+*']),  # (*)
        ('a*b+a*b', ['2ab**', '2ba**', 'a2b**', 'ab2**', 'b2a**', 'ba2**']),
        # (*)
    ]

    for case, exps in simplifier_optimiser_test:
        tokens = list(case)
        calc = Calculator(tokens, [DoubleNegativeOptimiser(),
                                   IntegerCostantsOptimiser(),
                                   SimplifierOptimiser()])

        calc.optimise()

        if str(calc) not in exps:
            print('Error in case for "{}". Actual "{}", expected {}'
                  .format(case, calc, exp))


test_double_negetive()
test_integer_constant_optimiser()
calc = Calculator('2^3^a', [IntegerCostantsOptimiser()])
# calc = Calculator('9*a/3+10+3*3', [IntegerCostantsOptimiser()])
# calc = Calculator('-9*a/4*3/e+d+2-2', [IntegerCostantsOptimiser()])
calc.optimise()
print(str(calc))
