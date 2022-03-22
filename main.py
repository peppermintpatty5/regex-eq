#!/usr/bin/env python3

from dfa import DFA
from nfa import NFA


a = NFA.from_string("a")
b = NFA.from_string("b")
m1 = DFA.from_NFA(a + a.star() | b) & DFA.from_NFA(a | b + b.star())
m2 = DFA.from_NFA(a | b)
m = (m1 & ~m2) | (~m1 & m2)

print(m1)
print(m2)
print(m)

while True:
    print(m.accept(input()))
