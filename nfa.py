from itertools import product


class NFA:
    """
    Class representation of a non-deterministic finite automaton
    """

    def __init__(
        self,
        N: tuple[
            set[object],
            set[str],
            dict[tuple[object, str], set[object]],
            object,
            set[object],
        ],
    ) -> None:
        """
        5-tuple definition of an NFA
        """
        self.N = N

    def __repr__(self) -> str:
        Q, S, d, q0, F = self.N

        # associate states with human-readable numbers via enumeration
        state_map = {q: i for i, q in enumerate(Q, start=1)}

        return repr(
            (
                {state_map[q] for q in Q},
                S,
                {
                    (state_map[q_in], c): {state_map[q] for q in q_out}
                    for (q_in, c), q_out in d.items()
                    if q_out != set()
                },
                state_map[q0],
                {state_map[q] for q in F},
            )
        )

    @staticmethod
    def from_string(string: str) -> "NFA":
        """
        Construct an NFA such that its language contains only the given string.
        """
        # object allocation guarantees unique states
        states = [object() for _ in range(len(string) + 1)]

        Q = set(states)
        S = set(string)
        d = {(q, c): set() for q, c in product(Q, S | {""})}
        for i, c in enumerate(string):
            d[states[i], c] |= {states[i + 1]}
        q0 = states[0]
        F = {states[-1]}

        return NFA((Q, S, d, q0, F))

    @staticmethod
    def from_alphabet(alphabet: set[str]) -> "NFA":
        """
        Construct an NFA such that its language is the given alphabet. The alphabet must
        contain only single-character strings.
        """
        q0 = object()
        states = {s: object() for s in alphabet}

        Q = set(states.values()) | {q0}
        S = set(alphabet)
        d = {
            (q, s): {states[s]} if q == q0 and s != "" else set()
            for q, s in product(Q, S | {""})
        }
        F = set(states.values())

        return NFA((Q, S, d, q0, F))

    def concat(self, other: "NFA") -> "NFA":
        """
        Construct an NFA `N` from `N1` and `N2` such that the language of `N`, denoted
        as `L(N)`, is the concatenation of `L(N1)` and `L(N2)`.
        """
        N1, N2 = self.N, other.N
        Q1, S1, d1, q1, F1 = N1
        Q2, S2, d2, q2, F2 = N2

        Q = Q1 | Q2
        S = S1 | S2
        d = {
            (q, c): set(d1[q, c])
            if (q, c) in d1
            else set(d2[q, c])
            if (q, c) in d2
            else set()
            for q, c in product(Q, S | {""})
        }
        for q in F1:
            d[q, ""] |= {q2}
        q0 = q1
        F = F2

        return NFA((Q, S, d, q0, F))

    def star(self) -> "NFA":
        """
        Construct an NFA `N` from `N1` such that the language of `N`, denoted as `L(N)`,
        is the Kleene star of `L(N1)`.
        """
        N1 = self.N
        Q1, S1, d1, q1, F1 = N1

        q0 = object()
        Q = Q1 | {q0}
        S = S1
        d = {
            (q, c): set(d1[q, c]) if (q, c) in d1 else set()
            for q, c in product(Q, S | {""})
        }
        for q in F1:
            d[q, ""] |= {q1}
        d[q0, ""] |= {q1}
        F = F1 | {q0}

        return NFA((Q, S, d, q0, F))

    def union(self, other: "NFA") -> "NFA":
        """
        Construct an NFA `N` from `N1` and `N2` such that the language of N, denoted as
        `L(N)`, is the union of `L(N1)` and `L(N2)`.
        """
        N1, N2 = self.N, other.N
        Q1, S1, d1, q1, F1 = N1
        Q2, S2, d2, q2, F2 = N2

        q0 = object()
        Q = Q1 | Q2 | {q0}
        S = S1 | S2
        d = {
            (q, c): set(d1[q, c])
            if (q, c) in d1
            else set(d2[q, c])
            if (q, c) in d2
            else set()
            for q, c in product(Q, S | {""})
        }
        d[q0, ""] |= {q1, q2}
        F = F1 | F2

        return NFA((Q, S, d, q0, F))
