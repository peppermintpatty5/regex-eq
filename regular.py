from dfa import DFA


class Regular:
    """
    A regular language, which is associated with a DFA.
    """

    def __init__(self, dfa: DFA) -> None:
        self.dfa = dfa

    @staticmethod
    def from_regex(regex: str) -> "Regular":
        """
        Construct a regular language from a regular expression.
        """
        return NotImplemented

    def __contains__(self, w):
        if isinstance(w, str):
            return self.dfa.accept(w)
        else:
            return NotImplemented

    def __and__(self, other):
        if isinstance(other, Regular):
            return Regular(self.dfa.intersection(other.dfa))
        else:
            return NotImplemented

    def __or__(self, other):
        if isinstance(other, Regular):
            return Regular(self.dfa.union(other.dfa))
        else:
            return NotImplemented

    def __invert__(self):
        return Regular(self.dfa.complement())

    def __add__(self, other):
        if isinstance(other, Regular):
            return Regular(DFA.from_NFA(self.dfa.concat(other.dfa)))
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Regular):
            return self & ~other
        else:
            return NotImplemented

    def __xor__(self, other):
        if isinstance(other, Regular):
            return (self - other) | (other - self)
        else:
            return NotImplemented
