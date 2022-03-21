#!/usr/bin/env python3

from dfa import DFA
from nfa import NFA


a = NFA.from_string("a")
b = NFA.from_string("b")
n1 = a + a.star() | b
n2 = a | b + b.star()
m = DFA.from_NFA(n1) & DFA.from_NFA(n2)

print(m)

while True:
    print(m.accept(input()))
