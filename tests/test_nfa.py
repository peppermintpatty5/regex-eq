"""
Unit tests for module `regular.nfa`
"""

import unittest

from regular.nfa import NFA


class TestNFA(unittest.TestCase):
    """
    Test cases for class `NFA`
    """

    def test_overlapping_states(self):
        """
        The operations for union and concatenation cannot be performed if the NFAs have
        any states in common.
        """
        q1, q2 = object(), object()

        a = NFA(({q1, q2}, {"a"}, {(q1, "a"): {q2}}, q1, {q2}))
        b = NFA(({q1, q2}, {"b"}, {(q1, "b"): {q2}}, q1, {q2}))

        self.assertRaises(ValueError, a.concat, b)
        self.assertRaises(ValueError, a.union, b)

    def test_emptiness(self):
        """
        The language of an NFA which has no reachable accepting states is the empty
        language.
        """
        q1, q2 = object(), object()

        n1 = NFA(({q1, q2}, {"a"}, {(q1, "a"): q2}, q1, set()))
        n2 = NFA(({q1, q2}, {"a"}, {(q1, "a"): q1}, q1, {q2}))
        n3 = NFA(({q1, q2}, {"a"}, {(q1, "a"): q2}, q1, {q2}))

        self.assertTrue(n1.is_empty())
        self.assertTrue(n2.is_empty())
        self.assertFalse(n3.is_empty())


if __name__ == "__main__":
    unittest.main()
