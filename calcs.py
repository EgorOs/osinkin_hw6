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
            BREAK_SIGN    = {'|': 4, '-': 1, '+': 1, '*': 1, '^':1, '/': 1, '(': 1, ')': 5}
            PLUS_SIGN     = {'|': 2, '-': 2, '+': 2, '*': 1, '^':1, '/': 1, '(': 1, ')': 2}
            MINUS_SIGN    = {'|': 2, '-': 2, '+': 2, '*': 1, '^':1, '/': 1, '(': 1, ')': 2}
            MUL_SIGN      = {'|': 2, '-': 2, '+': 2, '*': 2, '^':1, '/': 2, '(': 1, ')': 2}
            POWER_SIGN    = {'|': 2, '-': 2, '+': 2, '*': 2, '^':1, '/': 2, '(': 1, ')': 2}
            DIV_SIGN      = {'|': 2, '-': 2, '+': 2, '*': 2, '^':2, '/': 2, '(': 1, ')': 2}
            LEFT_BRACKET  = {'|': 5, '-': 1, '+': 1, '*': 1, '^':1, '/': 1, '(': 1, ')': 3}

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
        # Recursive descent parser
        # https://en.wikipedia.org/wiki/Recursive_descent_parser
        # https://habr.com/post/122397/
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

        def tokenize(expression):
            characters = list(expression)
            digits_token = None
            tokens = []
            while characters:
                ch = characters.pop(0)
                if ch.isdigit():
                    if digits_token != None:
                        digits_token = digits_token*10 + int(ch)
                    else:
                        digits_token = int(ch)
                #elif for floats? 1.337?
                else:
                    if digits_token != None:
                        tokens.append(Token(digits_token))
                    tokens.append(Token(ch))
                    digits_token = None
            if digits_token != None:
                tokens.append(Token(digits_token))
            return tokens


        class Node:
            def __init__(self, token):
                self.tokens = [tokens]
                self.priority = 0
                self.left_node = None
                self.right_node = None

            def update(self, token):
                self.tokens.append(token)

            # left valid, right valid depending on operator, but both sides of node should be valid
            # and dont forget nodes like this a+b+c+d, a*b*c*d
            # power sign shold push bias aswell and drop it as soon as power-streak ends a^b^c^d
            # if on ^ operator found with P priority, try to find others with P priority, if there are
            # some, break them down into groups and in each group check from right to left
            # check this case a(b+c)e, brackets are incorrect here, it should be something like
            # operator missing kind of error

        def represent_as_tree(tokens, queue=[]):
            # queue = tokens
            # sub_expression = []
            # in_brackets = []
            # for token in queue:
            #     if token == '(':
            #         if queue[-1] == ')' and sub_expression:
            #             open_br, close_br = token, queue.pop(-1)
            #             # print('--',open_br,close_br)
            #             in_brackets = represent_as_tree(queue)
            #             sub_expression += [in_brackets,close_br]
            #         # else:
            #             # raise Exception('no closing bracket')
            #     sub_expression.append(queue.pop(0))
            #     print(sub_expression)
            #     print(queue)
            priority_list = []
            bias = 0
            for pos, token in enumerate(tokens):
                if token.ch == '(':
                    bias += token.priority
                elif token.ch == ')':
                    bias -= token.priority
                elif token.priority > 0:
                    priority_list.append((pos, token.priority + bias)) # to find node with highest priority
            # print(priority_list)
            order = sorted(priority_list, key = lambda x: x[1], reverse = True)
            # print(order)
            if bias != 0:
                print('Brackets are not balanced')
                return False
            priority_tree = {}
            nodes_init_pos = {}
            prev_pos, prev_priority = None, None
            for pos, priority in order:
                # print(pos, priority)
                if prev_pos != None and prev_priority != None:
                    # print(prev_pos, pos)
                    if abs(prev_pos - pos) <= 2 and prev_priority == priority:
                        # expand node
                        if prev_pos < pos:
                            pos_l, pos_r = pos + 0, pos + 2
                        elif prev_pos > pos:
                            pos_l, pos_r = pos - 1,pos + 1
                        # print(priority_tree[priority][-1], '---')
                        # print('--', [t.ch for t in tokens[pos_l: pos_r]])
                        priority_tree[priority][-1] += [t.ch for t in tokens[pos_l: pos_r]]
                        # print('expand')
                    elif not priority_tree.get(priority):
                        # new key
                        # print('new key')
                        nodes_init_pos[priority] = [pos]
                        if prev_pos < pos:
                            pos_l, pos_r = pos -1 , pos + 2
                        elif prev_pos > pos:
                            pos_l, pos_r = pos - 1,pos + 2
                        pos_l = 0 if pos_l < 0 else pos_l
                        pos_r = len(tokens) if pos_l > len(tokens) else pos_r
                        p = [t.ch for t in tokens[pos_l: pos_r]]
                        # print(p)
                        priority_tree[priority] = [p]
                        # print(priority_tree[priority])
                    else:
                        # new node with same priority
                        nodes_init_pos[priority].append(pos)
                        pos_l = 0 if pos - 1 < 0 else pos - 1
                        pos_r = len(tokens) if pos + 2 > len(tokens) else pos + 2
                        priority_tree[priority].append([t.ch for t in tokens[pos_l: pos_r]])
                        # print('another node',pos_l,pos_r)
                    prev_pos = pos
                    prev_priority = priority
                else:
                    # create initial node
                    # print('init', prev_pos, prev_priority)
                    nodes_init_pos[priority] = [pos]
                    pos_l = 0 if pos - 1 < 0 else pos - 1
                    pos_r = len(tokens) if pos + 2 > len(tokens) else pos + 2
                    priority_tree[priority] = [[t.ch for t in tokens[pos_l: pos_r]]]
                    prev_pos = pos
                    prev_priority = priority

            pr = sorted(set([o[1] for o in order]))[::-1]
            print(pr)
            prev_key = None
            higher_node_pos = []
            for key in pr:
                # print(priority_tree[key])
                if prev_key != None:
                    new_node = []
                    higher_node_pos += nodes_init_pos[prev_key]
                    higher_node_pos = sorted(higher_node_pos)
                    node_pos = nodes_init_pos[key]
                    n_higher_nodes = len(higher_node_pos)
                    n_nodes = len(node_pos)
                    length = n_nodes if n_nodes < n_higher_nodes else n_higher_nodes
                    for i in range(length):
                        higher_node_name = 'N{}_{}'.format(prev_key, i)
                        print('ddd0', higher_node_pos,  node_pos)
                        if higher_node_pos[i] < node_pos[i]:
                            new_node = new_node[:len(new_node) - 1] + [str(higher_node_name)] + priority_tree[key][i][1::]
                        elif higher_node_pos[i] > node_pos[i]:
                            new_node = new_node[:len(new_node) - 1] + priority_tree[key][i][0:len(priority_tree[key][i])-1] + [str(higher_node_name)]
                    if n_higher_nodes > n_nodes:
                        i = length + 1
                        higher_node_name = 'N{}_{}'.format(prev_key, i)
                        new_node = new_node[:len(new_node) - 1] + [str(higher_node_name)]
                    if n_higher_nodes < n_nodes:
                        i = length + 1
                        new_node += priority_tree[key][-1][1:]

                    print(new_node,'----')
                    prev_key = key
                else:
                    prev_key = key
                    print(priority_tree[key])
            print(nodes_init_pos)
            return order

        tokens = tokenize(self.opcodes)
        print([i.ch for i in tokens])
        print(represent_as_tree(tokens))




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
        ('+a', True, ),
        ('^a', False ),
        ('a^', False),
        ('a^-b', False),
        ('a^+b', False),
        ('a^b', True),
        ('^-b', False),
        ]

    for case, exp in validate_check_list:
        tokens = list(case)

        calc = Calculator(tokens).validate()
        
        if calc != exp:
            print('Error in case for "{}". Actual "{}", expected {}'.format(case, calc, exp))

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
            print('Error in case for "{}". Actual "{}", expected {}'.format(case, calc, exp))

# validate_test()
# str_test()

calc = Calculator('-a+(2+(3+5*4+9))+1').validate()
# calc = Calculator('k*10-a+2*2+(0*2)+1').validate()