# regex-eq

[![CI Status](https://github.com/peppermintpatty5/regex-eq/workflows/Continuous%20Integration/badge.svg)](https://github.com/peppermintpatty5/regex-eq/actions/workflows/ci.yml)

Determine if two regular expressions are equivalent.

## Background

In theory, the equivalence problem for regular expressions is Turing-decidable.

1. Convert both regular expressions into equivalent NFAs
2. Convert both of these NFAs into equivalent DFAs
3. Construct a new DFA such that its language is the symmetric difference of the languages of the two DFAs
4. Check if none of the reachable states in the newly constructed DFA are accepting states

The primary purpose of this program is to demonstrate computational theory as it applies to regular languages; any regard for efficiency is secondary.
