"""
Classes relating to deterministic finite automaton
"""

from collections import deque

from .nfa import NFA


class DFA(NFA):
    """
    Class representation of a deterministic finite automaton
    """

    def __init__(
        # pylint: disable=duplicate-code
        self,
        tuple_def: tuple[
            set[object],
            set[str],
            dict[tuple[object, str], object],
            object,
            set[object],
        ],
    ) -> None:
        """
        5-tuple definition of a DFA
        """
        Q, S, d, q0, F = tuple_def

        d = {(q_in, c): {q_out} for (q_in, c), q_out in d.items()} | {
            (q, ""): set() for q in Q
        }

        super().__init__((Q, S, d, q0, F))

    def __repr__(self) -> str:
        # pylint: disable=duplicate-code
        # associate states with human-readable numbers via enumeration
        state_map = {q: i for i, q in enumerate(self.Q, start=1)}

        return repr(
            (
                {state_map[q] for q in self.Q},
                self.S,
                {
                    (state_map[q_in], c): state_map[next(iter(q_out))]
                    for (q_in, c), q_out in self.d.items()
                    if c != ""
                },
                state_map[self.q0],
                {state_map[q] for q in self.F},
            )
        )

    @staticmethod
    def from_NFA(nfa: NFA) -> "DFA":
        """
        Construct an equivalent DFA from an NFA.
        """

        def E(R: set[object]) -> frozenset[object]:
            """
            The epsilon closure, which returns the set of states that are reachable from
            `R` through 0 or more epsilon transitions.
            """
            queue = deque(R)
            visited = set(R)

            while queue:
                q = queue.popleft()
                for r in nfa.d[q, ""]:
                    if r not in visited:
                        queue.append(r)
                        visited.add(r)

            return frozenset(visited)

        new_start = E({nfa.q0})
        queue = deque([new_start])
        subsets = {new_start}
        transitions = {}

        while queue:
            subset = queue.popleft()
            for c in nfa.S:
                neighbors = E(set().union(*(nfa.d[q, c] for q in subset)))
                transitions[subset, c] = neighbors

                if neighbors not in subsets:
                    queue.append(neighbors)
                    subsets.add(neighbors)

        # map subsets to plain states
        states = {subset: object() for subset in subsets}
        Q = set(states.values())
        S = nfa.S
        d = {
            (states[R_in], c): states[R_out] for (R_in, c), R_out in transitions.items()
        }
        q0 = states[new_start]
        F = {states[R] for R in subsets if R & nfa.F != set()}

        return DFA((Q, S, d, q0, F))

    def accept(self, string: str) -> bool:
        """
        Return true if the DFA accepts the input string, false otherwise.
        """
        q = self.q0
        for c in string:
            (q,) = self.d[q, c]

        return q in self.F

    def complement(self) -> "DFA":
        """
        Construct a DFA `M` from `M1` such that the language of `M`, denoted as `L(M)`,
        is the complement of `L(M1)`.
        """
        Q = self.Q
        S = self.S
        d = {
            (q_in, c): next(iter(q_out))
            for (q_in, c), q_out in self.d.items()
            if c != ""
        }
        q0 = self.q0
        F = self.Q - self.F

        return DFA((Q, S, d, q0, F))

    def intersection(self, other: "DFA") -> "DFA":
        """
        Construct a DFA `M` from `M1` and `M2` such that the language of M, denoted as
        `L(M)`, is the intersection of `L(M1)` and `L(M2).`
        """
        # pylint: disable=too-many-locals
        S = self.S | other.S

        pair_start = (self.q0, other.q0)
        queue = deque([pair_start])
        pairs = {pair_start}
        transitions = {}

        while queue:
            x, y = pair = queue.popleft()
            for s in S:
                (x_out,) = self.d[x, s] if s in self.S else {None}
                (y_out,) = other.d[y, s] if s in other.S else {None}
                pair_out = (x_out, y_out)
                transitions[pair, s] = pair_out

                if pair_out not in pairs:
                    queue.append(pair_out)
                    pairs.add(pair_out)

        states = {pair: object() for pair in pairs}
        Q = set(states.values())
        d = {
            (states[pair_in], s): states[pair_out]
            for (pair_in, s), pair_out in transitions.items()
        }
        q0 = states[pair_start]
        F = {states[x, y] for x, y in pairs if x in self.F and y in other.F}

        return DFA((Q, S, d, q0, F))

    def union(self, other: "DFA") -> "DFA":
        """
        Construct a DFA `M` from `M1` and `M2` such that the language of M, denoted as
        `L(M)`, is the union of `L(M1)` and `L(M2).`
        """
        return DFA.from_NFA(NFA.union(self, other))

    def is_empty(self) -> bool:
        """
        Returns true if the language of the DFA is the empty language, false otherwise.
        """
        return self.F == set()
