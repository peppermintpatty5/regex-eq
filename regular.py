from enum import Enum
from string import printable
import sys
from typing import Optional, Union

from dfa import DFA
from nfa import NFA


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

    @staticmethod
    def from_finite(language: set[str]) -> "Regular":
        """
        Construct a regular language from a finite language.
        """
        nfa = NFA.from_alphabet(set())

        for string in language:
            nfa = nfa.union(NFA.from_string(string))

        return Regular(DFA.from_NFA(nfa))

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


class Token:
    def __init__(self, type: TokenType, lexeme: str) -> None:
        self.type = type
        self.lexeme = lexeme


class Lexer:
    def __init__(self, input: str) -> None:
        self.index = 0
        self.input = input

    def next_token(self) -> Token:
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
                    return Token(unit_tokens[c], c)
                elif c == "\\":
                    state = State.ESCAPE
                elif c == "":  # end of string
                    return Token(TokenType.END, c)
                else:
                    return Token(TokenType.SYMBOL, c)
            elif state is State.ESCAPE:
                if c == "":  # end of string
                    return Token(TokenType.ERROR, c)
                else:
                    return Token(TokenType.SYMBOL, c)


class Operator(Enum):
    UNION = 0
    CONCAT = 1
    STAR = 2
    PLUS = 3
    QUESTION = 4


class Node:
    def __init__(
        self,
        val: Union[Operator, Token],
        left: Optional["Node"] = None,
        right: Optional["Node"] = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return repr({k: v for k, v in self.__dict__.items() if v is not None})

    def eval(self) -> Regular:

        if type(self.val) is Operator:
            operator = self.val

            a = self.left.eval() if self.left is not None else None
            b = self.right.eval() if self.right is not None else None

            if a is None:
                raise Exception("missing left operand")

            if operator is Operator.UNION:
                return a | b
            elif operator is Operator.CONCAT:
                return a + b
            elif operator is Operator.STAR:
                return Regular(DFA.from_NFA(a.dfa.star()))
            elif operator is Operator.PLUS:
                return a + Regular(DFA.from_NFA(a.dfa.star()))
            elif operator is Operator.QUESTION:
                return a | Regular.from_finite(set())
            else:
                raise Exception("invalid operator")

        elif type(self.val) is Token:
            token = self.val

            if token.type is TokenType.SYMBOL:
                return Regular.from_finite({token.lexeme})
            elif token.type is TokenType.DOT:
                return Regular.from_finite(set(printable))
            else:
                raise Exception("invalid operand")

        else:
            raise Exception("how did this happen?")


class Parser:
    def __init__(self, input: str) -> None:
        self._lexer = Lexer(input)
        self._pushback: Optional[Token] = None

    def next_token(self) -> Token:
        if self._pushback is not None:
            x = self._pushback
            self._pushback = None
            return x
        else:
            return self._lexer.next_token()

    def pushback_token(self, token: Token) -> None:
        if self._pushback is None:
            self._pushback = token
        else:
            raise Exception("pushback error")

    def parse_expr(self) -> Optional[Node]:
        term1 = self.parse_term()

        if term1 is None:
            return None

        while True:
            token = self.next_token()

            if token.type is not TokenType.UNION:
                self.pushback_token(token)
                break

            term2 = self.parse_term()
            if term2 is None:
                raise Exception("missing expression after '|'")

            term1 = Node(Operator.UNION, term1, term2)

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
                factor1 = Node(Operator.CONCAT, factor1, factor2)

        return factor1

    def parse_factor(self) -> Optional[Node]:
        token = self.next_token()

        if token.type in (TokenType.SYMBOL, TokenType.DOT):
            expr = Node(token)
        elif token.type is TokenType.L_PAREN:
            expr = self.parse_expr()
            if expr is None:
                raise Exception("syntax error")
            elif self.next_token().type is not TokenType.R_PAREN:
                raise Exception("missing ')'")
            else:
                expr = expr
        else:
            self.pushback_token(token)
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
        token = self.next_token()

        if token.type is TokenType.STAR:
            return Node(Operator.STAR)
        elif token.type is TokenType.PLUS:
            return Node(Operator.PLUS)
        elif token.type is TokenType.QUESTION:
            return Node(Operator.QUESTION)
        else:
            self.pushback_token(token)
            return None


if __name__ == "__main__":
    language = Parser(sys.argv[1]).parse_expr().eval()

    while True:
        string = input()
        if string in language:
            print(string)
