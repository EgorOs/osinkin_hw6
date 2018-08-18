#!/usr/bin/env python3
from enum import Enum
from string import ascii_lowercase


class Calculator:
    def __init__(self, opcodes: list, operators=None):
        self.opcodes = opcodes
        self.operators = operators if operators is not None else []

    def __str__(self) -> str:

        class Symbol(Enum):
            BREAK_SIGN = '|'
            MUL_SIGN = '*'
            DIV_SIGN = '/'
            PLUS_SIGN = '+'
            MINUS_SIGN = '-'
            LEFT_BRACKET = '('
            RIGHT_BRACKET = ')'
            POWER_SIGN = '^'

        class Action(Enum):
            BREAK_SIGN = {'|': 4, '-': 1, '+': 1, '*': 1, '^': 1, '/': 1,
                          '(': 1, ')': 5}
            PLUS_SIGN = {'|': 2, '-': 2, '+': 2, '*': 1, '^': 1, '/': 1,
                         '(': 1, ')': 2}
            MINUS_SIGN = {'|': 2, '-': 2, '+': 2, '*': 1, '^': 1, '/': 1,
                          '(': 1, ')': 2}
            MUL_SIGN = {'|': 2, '-': 2, '+': 2, '*': 2, '^': 1, '/': 2, '(': 1,
                        ')': 2}
            POWER_SIGN = {'|': 2, '-': 2, '+': 2, '*': 2, '^': 1, '/': 2,
                          '(': 1, ')': 2}
            DIV_SIGN = {'|': 2, '-': 2, '+': 2, '*': 2, '^': 2, '/': 2, '(': 1,
                        ')': 2}
            LEFT_BRACKET = {'|': 5, '-': 1, '+': 1, '*': 1, '^': 1, '/': 1,
                            '(': 1, ')': 3}

        opcodes = self.opcodes + ['|']
        lst_postfix = []
        stack = ['|']
        pos = 0
        while True:
            sym = opcodes[pos]
            if sym in set(ascii_lowercase):
                lst_postfix.append(sym)
                pos += 1
            else:
                LAST_SIGN = Symbol(stack[-1]).name
                action_choice = Action[LAST_SIGN].value[sym]
                if action_choice == 1:
                    stack.append(sym)
                    pos += 1
                elif action_choice == 2:
                    last = stack.pop(-1)
                    lst_postfix.append(last)
                elif action_choice == 3:
                    stack.pop(-1)
                    pos += 1
                elif action_choice == 4:
                    break
                else:
                    raise Exception('invalid input string')
        return ''.join(lst_postfix)

    def optimise(self):
        for operator in self.operators:
            self.opcodes = operator.process(self.opcodes)

    def validate(self) -> bool:
        class Token:
            def __init__(self, ch):
                self.ch = ch
                if ch == '+' or ch == '-':
                    self.priority = 1
                elif ch == '*' or ch == '/':
                    self.priority = 2
                elif ch == '^':
                    self.priority = 3
                elif ch == '(' or ch == ')':
                    self.priority = 4
                else:
                    self.priority = 0

        def tokenize(expression: list) -> list:
            characters = list(expression)
            digits_token = None
            tokens = []
            while characters:
                ch = characters.pop(0)
                if ch.isdigit():
                    if digits_token is not None:
                        digits_token = digits_token * 10 + int(ch)
                    else:
                        digits_token = int(ch)
                # elif for floats? 1.337?
                else:
                    if digits_token is not None:
                        tokens.append(Token(digits_token))
                    tokens.append(Token(ch))
                    digits_token = None
            if digits_token is not None:
                tokens.append(Token(digits_token))
            return tokens

        def represent_as_tree(tokens: list) -> dict:
            priority_list = []
            bias = 0
            for pos, token in enumerate(tokens):
                if token.ch == '(':
                    bias += token.priority
                elif token.ch == ')':
                    bias -= token.priority
                elif token.priority > 0:
                    # find node with highest priority
                    priority_list.append((pos, token.priority + bias))

            order = sorted(priority_list, key=lambda x: x[1], reverse=True)

            if bias != 0:
                # brackets are not balanced
                return {}

            priority_tree = {}
            nodes_init_pos = {}
            prev_pos, prev_priority = None, None
            for pos, priority in order:
                if prev_pos is not None and prev_priority is not None:
                    if abs(prev_pos - pos) <= 2 and prev_priority == priority:
                        # expand node
                        if prev_pos < pos:
                            pos_l, pos_r = pos + 0, pos + 2
                        else:
                            pos_l, pos_r = pos - 1, pos + 1
                        priority_tree[priority][-1] += [t for t in
                                                        tokens[pos_l: pos_r]]
                    elif not priority_tree.get(priority):
                        # new key
                        nodes_init_pos[priority] = [pos]
                        if prev_pos < pos:
                            pos_l, pos_r = pos - 1, pos + 2
                        else:
                            pos_l, pos_r = pos - 1, pos + 2
                        pos_l = 0 if pos_l < 0 else pos_l
                        pos_r = len(tokens) if pos_l > len(tokens) else pos_r
                        priority_tree[priority] = [
                            [t for t in tokens[pos_l: pos_r]]]
                    else:
                        # new node with same priority
                        nodes_init_pos[priority].append(pos)
                        pos_l = 0 if pos - 1 < 0 else pos - 1
                        pos_r = len(tokens) if pos + 2 > len(
                            tokens) else pos + 2
                        priority_tree[priority].append(
                            [t for t in tokens[pos_l: pos_r]])
                    prev_pos = pos
                    prev_priority = priority
                else:
                    # create initial node
                    nodes_init_pos[priority] = [pos]
                    pos_l = 0 if pos - 1 < 0 else pos - 1
                    pos_r = len(tokens) if pos + 2 > len(tokens) else pos + 2
                    priority_tree[priority] = [
                        [t for t in tokens[pos_l: pos_r]]]
                    prev_pos = pos
                    prev_priority = priority

            return priority_tree

        def check_unary_operators(tokens: list) -> bool:
            prev_priority = None
            if tokens[-1].priority == 1:
                # unary operation can not end with +/-
                return False
            for token in tokens:
                if prev_priority is not None:
                    if token.priority != prev_priority:
                        pass
                    else:
                        return False
                    prev_priority = token.priority
                else:
                    prev_priority = token.priority
            return True

        def check_binary_operators(tokens: list) -> bool:
            prev_priority = None
            prev_token = None
            if tokens[-1].priority not in (0, 4):
                return False
            if tokens[0].priority not in (0, 4):
                return False
            for token in tokens:
                if prev_priority is not None:
                    if prev_token.ch == '/' and token.ch == 0:
                        return False
                    if token.priority != prev_priority:
                        pass
                    else:
                        return False
                    prev_priority = token.priority
                    prev_token = token
                else:
                    prev_priority = token.priority
                    prev_token = token
            return True

        tokens = tokenize(self.opcodes)
        tree = represent_as_tree(tokens)
        if not tree:
            return False
        for key in tree.keys():
            nodes = tree[key]
            for node in nodes:
                operation_priority = max(node[0].priority, node[1].priority)
                if operation_priority == 1:
                    if not check_unary_operators(node):
                        return False
                else:
                    if not check_binary_operators(node):
                        return False
        return True


def validate_test():
    validate_check_list = [
        ('a+2', True),
        ('a-(-2)', True),
        ('a+2-', False),
        ('a+(2+(3+5)', False),
        ('a^2', True),
        ('a^(-2)', True),
        ('-a-2', True),
        ('6/0', False),
        ('a/(b-b)', True),
        ('+a', True,),
        ('^a', False),
        ('a^', False),
        ('a^-b', False),
        ('a^+b', False),
        ('a^b', True),
        ('^-b', False),
        ('+b/(0+0)', True),
        ('+b/(0)', True),  # or should this case be considered as False?
    ]

    for case, exp in validate_check_list:
        tokens = list(case)

        calc = Calculator(tokens).validate()

        if calc != exp:
            print('Error in case for "{}". Actual "{}", expected {}'
                  .format(case, calc, exp))


def str_test():
    str_check_list = [
        ("a", "a"),
        ("-a", "a-"),
        ("(a*(b/c)+((d-f)/k))", "abc/*df-k/+"),
        ("(a)", "a"),
        ("a*(b+c)", "abc+*"),
        ("(a*(b/c)+((d-f)/k))*(h*(g-r))", "abc/*df-k/+hgr-**"),
        ("(x*y)/(j*z)+g", "xy*jz*/g+"),
        ("a-(b+c)", "abc+-"),
        ("a/(b+c)", "abc+/"),
        ("a^(b+c)", "abc+^"),
        ("a^b^c", "abc^^"),
        ("a^(b^c)", "abc^^"),
        ("(a^b)^c", "ab^c^"),
        ("a*b^c", "abc^*"),
        ("(a*b)^c", "ab*c^"),
    ]

    for case, exp in str_check_list:
        tokens = list(case)
        calc = Calculator(tokens)

        if str(calc) != exp:
            print('Error in case for "{}". Actual "{}", expected {}'
                  .format(case, calc, exp))


validate_test()
str_test()

# calc = Calculator('-a+(2+(3+5*4+9))+1').validate()
# calc = Calculator('-a+((2+1)+(3+9))+1').validate()
# calc = Calculator('-(a+1)^1+(1+1)').validate()
# calc = Calculator('s^s').validate()
# calc = Calculator('k*10-a+2*2+(0*2)+1*2').validate()
