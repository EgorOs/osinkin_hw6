#!/usr/bin/env python3
from calcs import Calculator, Token, tokenize, represent_as_tree

class AbstractOptimiser:
    def process(self, graph):
        g = self.pre_process(graph)

        result = self.process_internal(g)

        return self.post_process(result)

    def pre_process(self, graph):
        return graph
     
    def process_internal(self, graph):
        return graph
     
    def post_process(self, result):
        return result


class DoubleNegativeOptimiser(AbstractOptimiser):
        # -(-a) -> a
        def pre_process(self, opcodes):
            return tokenize(opcodes)

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
        pass


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
        (['2', '/', '2'], ['4']),
        (['2', '^', '10'], ['1024']),
        (['a', '+', '2', '*', '4'], ['a8+', '8a+']),
        
        (['2', '+', 'a', '+', '3'], ['5a+', 'a5+']),        # (*)
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


test_double_negetive()
# calc = Calculator('-(-90912)', [DoubleNegativeOptimiser()])
# calc.optimise()
# print(str(calc))