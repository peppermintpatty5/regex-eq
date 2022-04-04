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


class DAG:
    def __init__(
        self,
        val,
        left: Optional["DAG"] = None,
        right: Optional["DAG"] = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return repr({k: v for k, v in self.__dict__.items() if v is not None})


class Parser:
    def __init__(self, input: str) -> None:
        self.lexer = Lexer(input)
        self.pushback = None

    def next_token(self) -> tuple[TokenType, str]:
        if self.pushback is not None:
            x = self.pushback
            self.pushback = None
            return x
        else:
            return self.lexer.next_token()

    def pushback_token(self, x: tuple[TokenType, str]) -> None:
        if self.pushback is None:
            self.pushback = x
        else:
            raise Exception("pushback error")

    def parse_regex(self) -> Optional[DAG]:
        regex_branch = self.parse_term()

        while True:
            token, lexeme = self.next_token()

            if token is not TokenType.UNION:
                self.pushback_token((token, lexeme))
                break

            regex = self.parse_regex()
            if regex is None:
                raise Exception("missing expression after '|'")

            regex_branch = DAG("UNION", regex_branch, regex)

        return regex_branch

    def parse_term(self) -> Optional[DAG]:
        expr = self.parse_expr()

        if expr is None:
            return None

        while True:
            regex_branch = self.parse_term()
            if regex_branch is None:
                break
            else:
                expr = DAG("CONCAT", expr, regex_branch)

        return expr

    def parse_expr(self) -> Optional[DAG]:
        token, lexeme = self.next_token()

        if token in (TokenType.SYMBOL, TokenType.DOT):
            expr = DAG(lexeme)
        elif token is TokenType.L_PAREN:
            regex = self.parse_regex()
            if regex is None:
                raise Exception("syntax error")
            elif self.next_token()[0] is not TokenType.R_PAREN:
                raise Exception("missing ')'")
            else:
                expr = regex
        else:
            self.pushback_token((token, lexeme))
            return None

        while True:
            dup_symbol = self.parse_dup_symbol()
            if dup_symbol is None:
                break
            else:
                dup_symbol.left = expr
                expr = dup_symbol

        return expr

    def parse_dup_symbol(self) -> Optional[DAG]:
        token, lexeme = self.next_token()

        if token is TokenType.STAR:
            return DAG("STAR")
        elif token is TokenType.PLUS:
            return DAG("PLUS")
        elif token is TokenType.QUESTION:
            return DAG("QUESTION")
        else:
            self.pushback_token((token, lexeme))
            return None


if __name__ == "__main__":
    parser = Parser(sys.argv[1])
    print(parser.parse_regex())
