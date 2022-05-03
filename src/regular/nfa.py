"""
Classes relating to non-deterministic finite automaton
"""

from collections import deque


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
        self.Q, self.S, self.d_mat, self.q0, self.F = tuple_def

    def __repr__(self) -> str:
        state_map = {q: i for i, q in enumerate(self.Q, start=1)}

        return repr(
            (
                {state_map[q] for q in self.Q},
                self.S,
                {
                    (state_map[q_in], s): {state_map[q] for q in q_out}
                    for (q_in, s), q_out in self.d_mat.items()
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
    def empty() -> "NFA":
        """
        Construct an NFA such that its language is the empty language.
        """
        q1 = object()

        return NFA(({q1}, set(), {}, q1, set()))

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

    def _add_transition(self, q: object, s: str, q_out: object) -> None:
        if (q, s) in self.d_mat:
            self.d_mat[q, s].add(q_out)
        else:
            self.d_mat[q, s] = {q_out}

    def d(self, q: object, s: str) -> set[object]:
        """
        Get the set of output states for the given input state and symbol.
        """
        return self.d_mat[q, s] if (q, s) in self.d_mat else set()

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
            for (q_in, s), q_out in self.d_mat.items()
        }
        q0 = new_states[self.q0]
        F = {new_states[q] for q in self.F}

        return NFA((Q, S, d, q0, F))

    def update_concat(self, *others: "NFA") -> None:
        """
        Update an NFA with the concatenation of itself and others.
        """
        for other in others:
            if self.Q & other.Q:
                raise ValueError("states overlap")

            self.Q |= other.Q
            self.S |= other.S
            self.d_mat |= other.d_mat
            for q in self.F:
                self._add_transition(q, "", other.q0)
            self.F = set(other.F)

    def update_star(self) -> None:
        """
        Update an NFA with the Kleene star of itself.
        """
        q0 = object()

        self.Q.add(q0)
        for q in self.F:
            self._add_transition(q, "", self.q0)
        self._add_transition(q0, "", self.q0)
        self.F.add(q0)
        self.q0 = q0

    def update_union(self, *others: "NFA") -> None:
        """
        Update an NFA with the union of itself and others.
        """
        if others:
            q0 = object()
            self.Q.add(q0)
            self._add_transition(q0, "", self.q0)
            self.q0 = q0

            for other in others:
                if self.Q & other.Q:
                    raise ValueError("states overlap")

                self.Q |= other.Q
                self.S |= other.S
                self.d_mat |= other.d_mat
                self._add_transition(q0, "", other.q0)
                self.F |= other.F

    def is_empty(self) -> bool:
        """
        Returns true if the language of the DFA is the empty language, false otherwise.
        """
        return not any(q in self.F for q in self)
