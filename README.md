# regex-eq

Determine if two regular expressions are equivalent.

## Background

In theory, the equivalence problem for regular expressions is Turing-decidable.

1. Convert both regular expressions into equivalent NFAs
2. Convert both of these NFAs into equivalent DFAs
3. Construct a new DFA such that its language is the symmetric difference of the languages of the two DFAs
4. Check if any accept state in the newly constructed DFA is reachable from the start state
