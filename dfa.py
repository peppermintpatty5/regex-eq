from collections import deque

from nfa import NFA


class DFA(NFA):
    """
    Class representation of a deterministic finite automaton
    """

    def __init__(
        self,
        M: tuple[
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
        Q, S, d, q0, F = M

        d = {(q_in, c): {q_out} for (q_in, c), q_out in d.items()} | {
            (q, ""): set() for q in Q
        }

        super().__init__((Q, S, d, q0, F))

    def __repr__(self) -> str:
        Q, S, d, q0, F = self.N

        # associate states with human-readable numbers via enumeration
        state_map = {q: i + 1 for i, q in enumerate(Q)}

        return repr(
            (
                {state_map[q] for q in Q},
                S,
                {
                    (state_map[q_in], c): state_map[next(iter(q_out))]
                    for (q_in, c), q_out in d.items()
                    if c != ""
                },
                state_map[q0],
                {state_map[q] for q in F},
            )
        )

    def __and__(self, other):
        if isinstance(other, DFA):
            return self.intersection(other)
        else:
            return NotImplemented

    def __invert__(self):
        return self.complement()

    def __or__(self, other):
        if isinstance(other, DFA):
            return self.union(other)
        else:
            return NotImplemented

    @staticmethod
    def from_NFA(nfa: NFA) -> "DFA":
        """
        Construct an equivalent DFA from an NFA.
        """
        N1 = nfa.N
        Q1, S1, d1, q1, F1 = N1

        def E(R: set[object]) -> frozenset[object]:
            """
            The epsilon closure, which returns the set of states that are reachable from
            `R` through 0 or more epsilon transitions.
            """
            queue = deque(R)
            visited = set(R)

            while queue:
                q = queue.popleft()
                for r in d1[q, ""]:
                    if r not in visited:
                        queue.append(r)
                        visited.add(r)

            return frozenset(visited)

        new_start = E({q1})
        queue = deque([new_start])
        subsets = {new_start}
        transitions = {}

        while queue:
            subset = queue.popleft()
            for c in S1:
                neighbors = E(set().union(*(d1[q, c] for q in subset)))
                transitions[subset, c] = neighbors

                if neighbors not in subsets:
                    queue.append(neighbors)
                    subsets.add(neighbors)

        # map subsets to plain states
        states = {subset: object() for subset in subsets}
        Q = set(states.values())
        S = S1
        d = {
            (states[R_in], c): states[R_out] for (R_in, c), R_out in transitions.items()
        }
        q0 = states[new_start]
        F = {states[R] for R in subsets if R & F1 != set()}

        return DFA((Q, S, d, q0, F))

    def accept(self, string: str) -> bool:
        """
        Return true if the DFA accepts the input string, false otherwise.
        """
        Q, S, d, q0, F = self.N

        q = q0
        for c in string:
            (q,) = d[q, c]

        return q in F

    def complement(self) -> "DFA":
        """
        Construct a DFA `M` from `M1` such that the language of `M`, denoted as `L(M)`,
        is the complement of `L(M1)`.
        """
        N1 = self.N
        Q1, S1, d1, q1, F1 = N1

        Q = Q1
        S = S1
        d = {(q_in, c): next(iter(q_out)) for (q_in, c), q_out in d1.items() if c != ""}
        q0 = q1
        F = Q - F1

        return DFA((Q, S, d, q0, F))

    def intersection(self, other: "DFA") -> "DFA":
        """
        Construct a DFA `M` from `M1` and `M2` such that the language of M, denoted as
        `L(M)`, is the intersection of `L(M1)` and `L(M2).`
        """
        N1, N2 = self.N, other.N
        Q1, S1, d1, q1, F1 = N1
        Q2, S2, d2, q2, F2 = N2

        # alphabets for both machines must be the same
        if S1 == S2:
            S = S1
        else:
            raise ValueError("alphabet mismatch")

        pair_start = (q1, q2)
        queue = deque([pair_start])
        pairs = {pair_start}
        transitions = {}

        while queue:
            x, y = pair = queue.popleft()
            for s in S:
                (x_out,) = d1[x, s]
                (y_out,) = d2[y, s]
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
        F = {states[x, y] for x, y in pairs if x in F1 and y in F2}

        return DFA((Q, S, d, q0, F))

    def union(self, other: "DFA") -> "DFA":
        """
        Construct a DFA `M` from `M1` and `M2` such that the language of M, denoted as
        `L(M)`, is the union of `L(M1)` and `L(M2).`
        """
        N1, N2 = self.N, other.N
        Q1, S1, d1, q1, F1 = N1
        Q2, S2, d2, q2, F2 = N2

        # alphabets for both machines must be the same
        if S1 == S2:
            S = S1
        else:
            raise ValueError("alphabet mismatch")

        pair_start = (q1, q2)
        queue = deque([pair_start])
        pairs = {pair_start}
        transitions = {}

        while queue:
            x, y = pair = queue.popleft()
            for s in S:
                (x_out,) = d1[x, s]
                (y_out,) = d2[y, s]
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
        F = {states[x, y] for x, y in pairs if x in F1 or y in F2}

        return DFA((Q, S, d, q0, F))
