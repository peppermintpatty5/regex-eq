"""
Classes relating to non-deterministic finite automaton
"""

from collections import deque
from itertools import product


class NFA:
    """
    Class representation of a non-deterministic finite automaton
    """

    def __init__(
        self,
        tuple_def: tuple[
            set[object],
            set[str],
            dict[tuple[object, str], set[object]],
            object,
            set[object],
        ],
    ) -> None:
        """
        5-tuple definition of an NFA

        Empty transitions may be omitted. For example, the following transition
        dictionaries `d1` and `d2` are logically equivalent.
        ```
        d1 = {(q1, s): set()}
        d2 = {}
        ```
        """
        self.Q, self.S, self._d, self.q0, self.F = tuple_def

    def __repr__(self) -> str:
        # associate states with human-readable numbers via enumeration
        state_map = {q: i for i, q in enumerate(self.Q, start=1)}

        return repr(
            (
                {state_map[q] for q in self.Q},
                self.S,
                {
                    (state_map[q_in], s): {state_map[q] for q in q_out}
                    for (q_in, s), q_out in self._d.items()
                    if q_out != set()
                },
                state_map[self.q0],
                {state_map[q] for q in self.F},
            )
        )

    def __iter__(self):
        queue = deque([self.q0])
        visited = {self.q0}

        while queue:
            q = queue.popleft()
            for s in self.S | {""}:
                for q_out in self.d(q, s):
                    if q_out not in visited:
                        queue.append(q_out)
                        visited.add(q_out)
            yield q

    @staticmethod
    def from_string(string: str) -> "NFA":
        """
        Construct an NFA such that its language contains only the given string.
        """
        # object allocation guarantees unique states
        states = [object() for _ in range(len(string) + 1)]

        Q = set(states)
        S = set(string)
        d = {(states[i], s): {states[i + 1]} for i, s in enumerate(string)}
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
        d = {(q0, s): states[s] for s in alphabet}
        F = set(states.values())

        return NFA((Q, S, d, q0, F))

    def d(self, q: object, s: str) -> set[object]:
        """
        Get the set of output states for the given input state and symbol.
        """
        return self._d[q, s] if (q, s) in self._d else set()

    def copy(self) -> "NFA":
        """
        Return a copy of the given NFA. The states in the copy are guaranteed to be
        globally unique.
        """
        new_states = {q: object() for q in self.Q}

        Q = set(new_states.values())
        S = set(self.S)
        d = {
            (new_states[q_in], s): {new_states[q] for q in q_out}
            for (q_in, s), q_out in self._d.items()
        }
        q0 = new_states[self.q0]
        F = {new_states[q] for q in self.F}

        return NFA((Q, S, d, q0, F))

    def concat(self, other: "NFA") -> "NFA":
        """
        Construct an NFA `N` from `N1` and `N2` such that the language of `N`, denoted
        as `L(N)`, is the concatenation of `L(N1)` and `L(N2)`.
        """
        if self.Q & other.Q:
            raise ValueError("states overlap")

        Q = self.Q | other.Q
        S = self.S | other.S
        d = {(q, s): self.d(q, s) | other.d(q, s) for q, s in product(Q, S | {""})}
        for q in self.F:
            d[q, ""] |= {other.q0}
        q0 = self.q0
        F = other.F

        return NFA((Q, S, d, q0, F))

    def star(self) -> "NFA":
        """
        Construct an NFA `N` from `N1` such that the language of `N`, denoted as `L(N)`,
        is the Kleene star of `L(N1)`.
        """
        q0 = object()
        Q = self.Q | {q0}
        S = self.S
        d = {(q, s): set(self.d(q, s)) for q, s in product(Q, S | {""})}
        for q in self.F:
            d[q, ""] |= {self.q0}
        d[q0, ""] |= {self.q0}
        F = self.F | {q0}

        return NFA((Q, S, d, q0, F))

    def union(self, other: "NFA") -> "NFA":
        """
        Construct an NFA `N` from `N1` and `N2` such that the language of N, denoted as
        `L(N)`, is the union of `L(N1)` and `L(N2)`.
        """
        if self.Q & other.Q:
            raise ValueError("states overlap")

        q0 = object()
        Q = self.Q | other.Q | {q0}
        S = self.S | other.S
        d = {(q, s): self.d(q, s) | other.d(q, s) for q, s in product(Q, S | {""})}
        d[q0, ""] |= {self.q0, other.q0}
        F = self.F | other.F

        return NFA((Q, S, d, q0, F))

    def is_empty(self) -> bool:
        """
        Returns true if the language of the DFA is the empty language, false otherwise.
        """
        return not any(q in self.F for q in self)
