import unittest

from regular.nfa import NFA


class TestNFA(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
