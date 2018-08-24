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

    if str(args[0].ch) in '+*':
        # remove unary plus or mul
        sign_queue.pop(0)

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
    digits = [i.ch for i in node if str(i.ch).isdigit()]
    if len(node) > 4 and len(digits) > 1:
        calculable = []
        incalculable = []
        tokens = node.copy()
        first_var = []
        prev_token = None
        if tokens[0].ch in set(ascii_lowercase):
            first_var.append(tokens.pop(0))
            prev_token = first_var[0]
        for token in tokens:
            if token.ch in set(ascii_lowercase):
                incalculable.append(prev_token)
                incalculable.append(token)
            # elif prev_token and prev_token.ch in set(ascii_lowercase):
            #     incalculable.append(token)
            elif str(token.ch).isdigit():
                if prev_token:
                    calculable.append(prev_token)
                calculable.append(token)
            prev_token = token
        incalculable = first_var + incalculable
        calculable = merge_tokens(*calculable, integer_devision=True)
        if incalculable[0].ch in set(ascii_lowercase):
            if int(calculable[0].ch) < 0:
                result = incalculable + tokenize('-') + calculable
            else:
                result = incalculable + tokenize('+') + calculable
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
        def remove_double_minuses(chars):
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
                    elif pattern == ['-', '(', '+', ')']:
                        new_opcodes += ['-', str(chars[i + 3])]
                        i += 5
                    else:
                        new_opcodes.append(chars[i])
                        i += 1

                else:
                    new_opcodes.append(chars[i])
                    i += 1
            return new_opcodes
        opt = remove_double_minuses(chars)
        new_opcodes = None
        while True:
            if opt == new_opcodes:
                break
            if new_opcodes:
                opt = new_opcodes
                new_opcodes = remove_double_minuses(opt)
            else:
                new_opcodes = remove_double_minuses(opt)
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
                # print([i.ch for i in node])
                if not prev_key:
                    # if there is no nodes with higher priority
                    # check if there is variable in this node
                    if [t.ch for t in node if t.ch in set(ascii_lowercase)]:
                        # put variables to the start or to the end of node,
                        # and calculate the rest
                        result = simplify_with_var(node)
                        result[0].calculable = False
                    else:
                        # if no variable calculate the node
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
                    used = []
                    for limits in higher_nodes.keys():
                        pos, end_pos = limits
                        if node_end_pos <= pos:
                            tokens.pop(-1)  # remove outdated tokens
                            right_sign = [tokens.pop(-1)]
                            right_side = higher_nodes[limits]
                            used.append(limits)

                        if node_pos >= end_pos:
                            tokens.pop(0)  # remove outdated tokens
                            left_sign = [tokens.pop(0)]
                            left_side = higher_nodes[limits]
                            used.append(limits)
                    for l in used:
                        del higher_nodes[l]

                    if not [t.ch for t in tokens if
                            t.ch in set(ascii_lowercase)]:
                        if left_side and not [t.ch for t in left_side if
                                              t.ch in set(ascii_lowercase)]:
                            # in left side doesn't contain variables
                            new_exp = left_side + left_sign + tokens
                            tokens = merge_tokens(*new_exp,
                                                  integer_devision=True)
                            left_side, left_sign = [], []
                        if right_side and not [t.ch for t in right_side if t.ch
                                               in set(ascii_lowercase)]:
                            new_exp = tokens + right_sign + right_side
                            tokens = merge_tokens(*new_exp,
                                                  integer_devision=True)
                            right_side, right_sign = [], []

                    result += left_side + left_sign + tokens + right_sign + right_side
                    pos = result[0].pos

                    # calculate result
                    priorities = len({i.priority for i in result})
                    if priorities < 3:
                        # if all signs have same priority P, for variables
                        # P = 0 by default
                        result = simplify_with_var(result)

                    # expanding new node limits
                    try:
                        end_pos = result[-1].end_pos
                    except AttributeError:
                        end_pos = result[-1].pos
                    higher_nodes[(pos, end_pos)] = result
            prev_key = key

        return result

    def post_process(self, result):
        new_opcodes = [str(i.ch) for i in result]
        return new_opcodes


class SimplifierOptimiser(AbstractOptimiser):
    # a * 0 -> 0
    # a + 0 -> 0
    # *     a or True -> True
    # *     a and False -> False
    def process_internal(self, graph):


        def simplify_sum(node):
            sign = '+'
            variable_ctrs = {}
            order = []
            for t in node:
                if t.ch in set(ascii_lowercase) or str(t.ch).isdigit():
                    if t.ch not in variable_ctrs.keys():
                        order.append(str(t.ch))
                    variable_ctrs[str(t.ch)] = 0
            if node[0].ch != '-':
                node = tokenize('+') + node
            for i in range(0, len(node), 2):
                sign = node[i].ch
                var = str(node[i+1].ch)
                if sign == '-':
                    variable_ctrs[var] -= 1
                else:
                    variable_ctrs[var] += 1

            new_node = []
            for var in order:
                ctr = variable_ctrs[var]
                if ctr < 0:
                    ctr = [str(ctr)[1::]]
                    if ctr == ['1']:
                        ctr = []
                    else:
                        ctr += ['*']
                    new_node += ['-'] + ctr + [var]
                elif ctr > 0:
                    ctr = [str(ctr)]
                    if ctr == ['1']:
                        ctr = ['+']
                    else:
                        ctr = ['+'] + ctr + ['*']
                    new_node += ctr + [var]
                else:
                    pass
            if len(new_node) == 0:
                return tokenize('0')
            new_node = tokenize(new_node)
            return new_node

        def simplify_division(node):
            sign = '*'
            variable_ctrs = {}
            order = []
            for t in node:
                if t.ch in set(ascii_lowercase) or str(t.ch).isdigit():
                    if t.ch not in variable_ctrs.keys():
                        order.append(str(t.ch))
                    variable_ctrs[str(t.ch)] = 0
            if node[0].ch in set(ascii_lowercase):
                node = tokenize('*') + node
            for i in range(0, len(node), 2):
                sign = node[i].ch
                var = str(node[i+1].ch)
                if sign == '/':
                    variable_ctrs[var] -= 1
                else:
                    variable_ctrs[var] += 1
            new_node = []
            for var in order:
                if str(var) != '1':
                    ctr = variable_ctrs[var]
                    if ctr < 0:
                        new_node += ['/', var]*abs(ctr)
                    elif ctr > 0:
                        new_node += ['*', var]*ctr
                    else:
                        pass
            if len(new_node) == 0:
                return tokenize('1')
            if new_node[0] == '/':
                new_node = ['1'] + new_node
            elif new_node[0] == '*':
                new_node = new_node[1::]
            new_node = tokenize(new_node)
            return new_node

        def mul_by_zero(node):
            for i in range(len(node)-1):
                ch_1, ch_2 = node[i].ch, node[i+1].ch
                if str(ch_1) == '0' and str(ch_2) == '*':
                    new_node = ['0']
                elif str(ch_1) == '*' and str(ch_2) == '0':
                    new_node = ['0']
                else:
                    new_node = [str(t.ch) for t in node]
                new_node = tokenize(new_node)
            return new_node

        def add_zero(node):
            if len(node) < 2:
                return node
            else:
                if node[0].priority == 0:
                    node = tokenize('+') + node
                new_node = []
                for i in range(0, len(node) - 1, 2):
                    ch_1, ch_2 = node[i].ch, node[i+1].ch
                    if str(ch_2) != '0':
                        new_node.append(str(ch_1))
                        new_node.append(str(ch_2))
            new_node = tokenize(new_node)
            return new_node

        def to_zero_pwr(node):
            zero_pwr = 0
            new_node = []
            for token in node[::-1]:
                if str(token.ch) == '0':
                    zero_pwr = 2
                elif zero_pwr == 2:
                    zero_pwr -= 1
                elif zero_pwr ==1:
                    zero_pwr -= 1
                    new_node += tokenize('1')
                else:
                    new_node.append(token)
                    zero_pwr = False
            return new_node[::-1]

        def simplify(node):
            priority_set = {t.priority for t in node if t.priority != 0}
            priority = min(priority_set)
            if priority == 3:
                node = to_zero_pwr(node)
            elif priority == 2:
                node = mul_by_zero(node)
                if len(node) > 2:
                    node = simplify_division(node)
            elif priority == 1:
                if len(priority_set) == 1:
                    node = simplify_sum(node)
                node = add_zero(node)
            return node

        print([i.ch for i in graph])
        # change graph while prev != current
        # find unique vars in node and their number
        tree = represent_as_tree(graph)
        priority_lst = sorted(tree.keys(), reverse=True)
        new_token_lst = []
        prev_priority = None
        prev_key = None
        higher_nodes = {}
        result = graph
        for key in priority_lst:
            branch = tree[key]
            for node in branch:
                if not prev_key:
                    # if there is no nodes with higher priority
                    # check if there is variable in this node
                    pos, end_pos = node[0].pos, node[-1].pos
                    result = simplify(node)
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
                    used = []
                    for limits in higher_nodes.keys():
                        pos, end_pos = limits
                        if node_end_pos <= pos:
                            tokens.pop(-1)  # remove outdated tokens
                            right_sign = [tokens.pop(-1)]
                            right_side = higher_nodes[limits]
                            used.append(limits)

                        if node_pos >= end_pos:
                            tokens.pop(0)  # remove outdated tokens
                            left_sign = [tokens.pop(0)]
                            left_side = higher_nodes[limits]
                            used.append(limits)
                    for l in used:
                        del higher_nodes[l]


                    if left_side:
                        # in left side doesn't contain variables
                        new_exp = left_side + left_sign + tokens
                        try:
                            tokens = merge_tokens(*new_exp)
                        except Exception as e:
                            tokens = simplify(new_exp)
                        left_side, left_sign = [], []
                    if right_side:
                        new_exp = tokens + right_sign + right_side
                        try:
                            tokens = merge_tokens(*new_exp)
                        except Exception as e:
                            tokens = simplify(new_exp)
                        right_side, right_sign = [], []

                    result += left_side + left_sign + tokens + right_sign + right_side

                    pos = result[0].pos

                    # calculate result
                    # priorities = len({i.priority for i in result})
                    # if priorities < 3:
                    #     # if all signs have same priority P, for variables
                    #     # P = 0 by default
                    #     result = simplify_with_var(result)

                    # expanding new node limits
                    try:
                        end_pos = result[-1].end_pos
                    except AttributeError:
                        end_pos = result[-1].pos
                    higher_nodes[(pos, end_pos)] = result
            prev_key = key

        # return graph
        return result

    def post_process(self, result):
        new_opcodes = [str(i.ch) for i in result]
        return new_opcodes


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

        # ('a+a+a', ['a3*', '3a*']),  # (*)
        # ('(a-b)-(a-b)', ['0']),  # (*)
        # ('(a-b)/(a-b)', ['1']),  # (*)
        # ('(a+b)+(a+b)', ['ab+2*', '2ab+*']),  # (*)
        # ('a*b+a*b', ['2ab**', '2ba**', 'a2b**', 'ab2**', 'b2a**', 'ba2**']),
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
                  .format(case, calc, exps))


test_double_negetive()
test_integer_constant_optimiser()
test_simplifier_optimiser()
calc = Calculator('a-(-(-a))', [DoubleNegativeOptimiser()])
# calc = Calculator('-(-a)', [DoubleNegativeOptimiser()])
# calc = Calculator('2-a+3', [IntegerCostantsOptimiser()])
# calc = Calculator('1+(2+2)*a*3', [IntegerCostantsOptimiser()])
# calc = Calculator('9*a/3+10+3*3', [IntegerCostantsOptimiser()])
# calc = Calculator('-9*a/4*3/e+d+2-2', [IntegerCostantsOptimiser()])
# calc = Calculator('a^0', [DoubleNegativeOptimiser(),IntegerCostantsOptimiser(), SimplifierOptimiser()])
calc.optimise()
print(str(calc))