#!/usr/bin/env python3

import sys

from dfa import DFA
from nfa import NFA
from regular import Regular


a = Regular(DFA.from_NFA(NFA.from_string("a")))
b = Regular(DFA.from_NFA(NFA.from_string("b")))
language = a + b  # TODO: fix symmetric difference a ^ b

print(language.dfa, file=sys.stderr)

while True:
    string = input()
    if string in language:
        print(string)
