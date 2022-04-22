#!/usr/bin/env python3
# pylint: skip-file

import sys

from regular import Regular


language = Regular.from_regex(sys.argv[1])

print(language.dfa, file=sys.stderr)

try:
    while True:
        string = input()
        if string in language:
            print(string)
except EOFError:
    pass
