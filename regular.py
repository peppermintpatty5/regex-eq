from enum import Enum
import sys
from typing import Optional

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


class TokenType(Enum):
    DOT = 0
    STAR = 1
    PLUS = 2
    QUESTION = 3
    UNION = 4
    L_PAREN = 5
    R_PAREN = 6
    L_BRACKET = 7
    R_BRACKET = 8
    SYMBOL = 9
    END = 10
    ERROR = 11


class Lexer:
    def __init__(self, input: str) -> None:
        self.index = 0
        self.input = input

    def next_token(self) -> tuple[TokenType, str]:
        class State(Enum):
            START = 0
            ESCAPE = 1

        state = State.START

        while True:
            c = self.input[self.index] if self.index < len(self.input) else ""
            self.index += 1

            if state is State.START:
                unit_tokens = {
                    ".": TokenType.DOT,
                    "*": TokenType.STAR,
                    "+": TokenType.PLUS,
                    "?": TokenType.QUESTION,
                    "|": TokenType.UNION,
                    "(": TokenType.L_PAREN,
                    ")": TokenType.R_PAREN,
                    "[": TokenType.L_BRACKET,
                    "]": TokenType.R_BRACKET,
                }
                if c in unit_tokens:
                    return (unit_tokens[c], c)
                elif c == "\\":
                    state = State.ESCAPE
                elif c == "":  # end of string
                    return (TokenType.END, c)
                else:
                    return (TokenType.SYMBOL, c)
            elif state is State.ESCAPE:
                if c == "":  # end of string
                    return (TokenType.ERROR, c)
                else:
                    return (TokenType.SYMBOL, c)


class Node:
    def __init__(
        self,
        val,
        left: Optional["Node"] = None,
        right: Optional["Node"] = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return repr({k: v for k, v in self.__dict__.items() if v is not None})


class Parser:
    def __init__(self, input: str) -> None:
        self._lexer = Lexer(input)
        self._pushback = None

    def next_token(self) -> tuple[TokenType, str]:
        if self._pushback is not None:
            x = self._pushback
            self._pushback = None
            return x
        else:
            return self._lexer.next_token()

    def pushback_token(self, x: tuple[TokenType, str]) -> None:
        if self._pushback is None:
            self._pushback = x
        else:
            raise Exception("pushback error")

    def parse_expr(self) -> Optional[Node]:
        term1 = self.parse_term()

        if term1 is None:
            return None

        while True:
            token, lexeme = self.next_token()

            if token is not TokenType.UNION:
                self.pushback_token((token, lexeme))
                break

            term2 = self.parse_term()
            if term2 is None:
                raise Exception("missing expression after '|'")

            term1 = Node("UNION", term1, term2)

        return term1

    def parse_term(self) -> Optional[Node]:
        factor1 = self.parse_factor()

        if factor1 is None:
            return None

        while True:
            factor2 = self.parse_factor()
            if factor2 is None:
                break
            else:
                factor1 = Node("CONCAT", factor1, factor2)

        return factor1

    def parse_factor(self) -> Optional[Node]:
        token, lexeme = self.next_token()

        if token in (TokenType.SYMBOL, TokenType.DOT):
            expr = Node((token, lexeme))
        elif token is TokenType.L_PAREN:
            expr = self.parse_expr()
            if expr is None:
                raise Exception("syntax error")
            elif self.next_token()[0] is not TokenType.R_PAREN:
                raise Exception("missing ')'")
            else:
                expr = expr
        else:
            self.pushback_token((token, lexeme))
            return None

        while True:
            exponent = self.parse_exponent()
            if exponent is None:
                break
            else:
                exponent.left = expr
                expr = exponent

        return expr

    def parse_exponent(self) -> Optional[Node]:
        token, lexeme = self.next_token()

        if token is TokenType.STAR:
            return Node("STAR")
        elif token is TokenType.PLUS:
            return Node("PLUS")
        elif token is TokenType.QUESTION:
            return Node("QUESTION")
        else:
            self.pushback_token((token, lexeme))
            return None


if __name__ == "__main__":
    parser = Parser(sys.argv[1])
    print(parser.parse_expr())
