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

        d = {(q_in, s): {q_out} for (q_in, s), q_out in d.items()}

        super().__init__((Q, S, d, q0, F))

    def __repr__(self) -> str:
        state_map = {q: i for i, q in enumerate(self.Q, start=1)}

        return repr(
            (
                {state_map[q] for q in self.Q},
                self.S,
                {
                    (state_map[q_in], s): state_map[next(iter(q_out))]
                    for (q_in, s), q_out in self.d_mat.items()
                    if s != ""
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
                for r in nfa.d(q, ""):
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
            for s in nfa.S:
                neighbors = E(set().union(*(nfa.d(q, s) for q in subset)))
                transitions[subset, s] = neighbors

                if neighbors not in subsets:
                    queue.append(neighbors)
                    subsets.add(neighbors)

        # map subsets to plain states
        states = {subset: object() for subset in subsets}
        Q = set(states.values())
        S = nfa.S
        d = {
            (states[R_in], s): states[R_out] for (R_in, s), R_out in transitions.items()
        }
        q0 = states[new_start]
        F = {states[R] for R in subsets if R & nfa.F != set()}

        return DFA((Q, S, d, q0, F))

    @staticmethod
    def intersection(*dfas: "DFA") -> "DFA":
        """
        Construct a DFA that is the intersection of multiple DFAs.
        """
        S = set().union(*(dfa.S for dfa in dfas))

        start = tuple(dfa.q0 for dfa in dfas)
        queue = deque([start])
        visited = {start}
        transitions = {}

        while queue:
            state = queue.popleft()
            for s in S:
                next_state = tuple(
                    next(iter(dfa.d(q, s)), None) for dfa, q in zip(dfas, state)
                )
                transitions[state, s] = next_state

                if next_state not in visited:
                    queue.append(next_state)
                    visited.add(next_state)

        state_map = {state: object() for state in visited}
        Q = set(visited)
        d = {
            (state_map[state], s): state_map[next_state]
            for (state, s), next_state in transitions.items()
        }
        q0 = state_map[start]
        F = {
            state_map[state]
            for state in visited
            if all(q in dfa.F for dfa, q in zip(dfas, state))
        }

        return DFA((Q, S, d, q0, F))

    def accept(self, string: str) -> bool:
        """
        Return true if the DFA accepts the input string, false otherwise.
        """
        q = self.q0
        for s in string:
            (q,) = self.d(q, s)

        return q in self.F

    def update_complement(self) -> None:
        """
        Update a DFA with the complement of itself.
        """
        self.F = self.Q - self.F
