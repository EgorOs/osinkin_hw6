#!/usr/bin/env python3
from calcs import Calculator, Token, tokenize, represent_as_tree, to_postfix
from string import ascii_lowercase

def merge_tokens(*args):
    new_token = Token('')
    new_token.pos = min([t.pos for t in args])
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
    else:
        new_val = ch_queue.pop(-1)
        for i in range(len(ch_queue)):
            new_val = ch_queue.pop(-1)**new_val

    new_token.ch = str(new_val)
    new_token.merged_len = merged_len
    return new_token

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
                if i >= n :
                    break
                if i < n - 4:
                    pattern = [*chars[i:i+3], chars[i+4]]
                    if pattern == ['-', '(', '-', ')']:
                        new_opcodes += ['+', str(chars[i+3])]
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
            # tree = represent_as_tree(graph)
            # priority_lst = sorted(tree.keys(), reverse=True)
            # new_token_lst = []
            # prev_priority = None
            # for key in priority_lst:
            #     branch = tree[key]
            #     for node in branch:
            #         print([i.ch for i in node])
            #         new_token = merge_tokens(*node)
            #         pos = new_token.pos
            #         lenght = new_token.merged_len
            #         del graph[pos:pos+lenght]
            #     #     node_pos = node[0].pos
            #     #     if new_token_lst and prev_priority:
            #     #         print('new_token_lst', [i.ch for i in new_token_lst])
            #     #         if new_token_lst[0].pos < node_pos:
            #     #             node[0] = new_token_lst.pop(0)
            #     #             print('here', node[0])
            #     #         else:
            #     #             node[-1] = new_token_lst.pop(0)
            #     #     new_token = merge_tokens(*node)
            #     #     print('new_token', new_token.ch)
            #     #     new_token_lst.append(new_token)
            #     #     new_token_lst = sorted(new_token_lst, key=lambda x: x.pos)
            #     # prev_priority = key

            #         print(new_token.ch)
            opcodes = [str(t.ch) for t in graph]
            opcodes = to_postfix(opcodes)


            def calculate(opcodes):
                stack = []
                sign_priority = {'-':1, '+':1, '*':2, '/':2, '^':3}
                prev_sign_priority = 1
                for sym in opcodes:
                    if sym in set(ascii_lowercase) or sym.isdigit():
                        stack.append(sym)
                    else:
                        s1, s2 = stack.pop(-2), stack.pop(-1)
                        if prev_sign_priority < sign_priority[sym]:
                            # if len(s1) > 1 and '(' not in s1:
                            #     s1 = '(' + s1 + ')'
                            # if len(s2) > 1 and '(' not in s2:
                            #     s2 = '(' + s2 + ')'
                            if s1.isdigit() and s2.isdigit():
                                stack.append(merge(s1, sym, s2))
                            else:
                                pass
                        else:
                            stack.append(merge(s1, sym, s2))
                        prev_sign_priority = sign_priority[sym]
                return stack[0]

            # digits = [[]]
            # letters = []
            # first_char = None
            # for ch in opcodes:
            #     if not first_char:
            #         first_char = ch
            #     if ch in set(ascii_lowercase):
            #         letters.append(ch)
            #         if digits[-1]:
            #             digits.append([])
            #     else:
            #         digits[-1].append(ch)

            # new_digits = []
            # # Calculating what possible
            # for d in digits:
            #     try:
            #         new_digits.append(calculate(d))
            #     except Exception:
            #         new_digits += [d]


            # print(letters, 'letters')
            # print(new_digits, 'new_digits')
            # print(first_char)
            # if first_char in letters:
            #     new_opcodes = list(zip(letters,new_digits))
            #     if len(new_digits) < len(letters):
            #         new_opcodes += letters[-1]
            # else:
            #     new_opcodes = list(zip(new_digits, letters))
            #     if len(new_digits) > len(letters):
            #         new_opcodes.append(new_digits[-1])
            ctr = len(opcodes)
            pos = 0
            # in case it is cannot be optimised
            result = opcodes
            if ctr == 3:
                values = opcodes[pos:pos+3]
                if values[0].isdigit() and values[1].isdigit() and values[2] in '+-*/^':
                    result = calculate(values)
                else:
                    result = opcodes

            if ctr < 3:
                result = opcodes

            while True:
                try:
                    values = opcodes[pos:pos+4]
                    if values[0].isdigit() and values[1].isdigit() and values[2] in '+-*/^':
                        new_val = calculate(values[:3])
                        opcodes = opcodes[:pos] + [new_val] + opcodes[pos+3::]
                        result = opcodes
                    elif values[0].isdigit() and not values[1].isdigit() and values[2].isdigit() and values[3] in '+-*/^':
                        new_val = calculate((values[0], values[2], values[3]))
                        opcodes = opcodes[:pos+2] + [new_val] + opcodes[pos+4::]
                        del opcodes[pos]
                        pos -= 1
                        result = opcodes            
                    pos += 1
                except Exception as e:
                    # raise e
                    pos += 1
                ctr -= 1
                if ctr == 0: break
            return result

        def post_process(self, result):
            new_opcodes = []
            # new_opcodes = str(result).replace('[','').replace(']','').replace('(','').replace(')','').replace("'",'').split(', ')
            for expression in result:
                new_opcodes += expression
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
        
        # (['2', '+', 'a', '+', '3'], ['5a+', 'a5+']),        # (*)
    ]

    for case, exp in integer_constant_optimiser_tests:
        calc = Calculator(case, [DoubleNegativeOptimiser(), IntegerCostantsOptimiser()])

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

        ('a+a+a', ['a3*', '3a*']), # (*)
        ('(a-b)-(a-b)', ['0']), # (*)
        ('(a-b)/(a-b)', ['1']), # (*)
        ('(a+b)+(a+b)', ['ab+2*', '2ab+*']), # (*)
        ('a*b+a*b', ['2ab**', '2ba**', 'a2b**', 'ab2**', 'b2a**', 'ba2**']), # (*)
    ]

    for case, exps in simplifier_optimiser_test:
        tokens = list(case)
        calc = Calculator(tokens, [DoubleNegativeOptimiser(), IntegerCostantsOptimiser(), SimplifierOptimiser()])
        
        calc.optimise()

        if str(calc) not in exps:
            print('Error in case for "{}". Actual "{}", expected {}'
                  .format(case, calc, exp))


# test_double_negetive()
# test_integer_constant_optimiser()
calc = Calculator('a+2-2', [IntegerCostantsOptimiser()])
calc.optimise()
print(str(calc))
calc.optimise()
print(str(calc))