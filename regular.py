"""
Classes relating to regular languages and regular expression parsing.

`Regular` is the only class from this module that you should be using.
"""

from dataclasses import dataclass
from enum import Enum
from string import printable
from typing import Optional, Union

from dfa import DFA
from nfa import NFA


class Regular:
    """
    A regular language, which is associated with a DFA. Objects of this class behave
    like sets of strings in that you can:

    - Check if a string is `in` the language
    - Perform the following operations:
        - `|` Union
        - `&` Intersection
        - `~` Complement
        - `-` Relative complement
        - `^` Symmetric difference
    - Check for the following relations:
        - `<` Subset (proper)
        - `==` Equality
    - Check for emptiness by using `bool` (implicitly or explicitly)
    """

    def __init__(self, dfa: DFA) -> None:
        self.dfa = dfa

    @staticmethod
    def from_regex(regex: str) -> "Regular":
        """
        Construct a regular language from a regular expression.
        """
        return Parser(regex).parse().eval()

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
        return NotImplemented

    def __and__(self, other):
        if isinstance(other, Regular):
            return Regular(self.dfa.intersection(other.dfa))
        return NotImplemented

    def __or__(self, other):
        if isinstance(other, Regular):
            try:
                nfa = self.dfa.union(other.dfa)
            except ValueError:
                nfa = self.dfa.copy().union(other.dfa)
            return Regular(DFA.from_NFA(nfa))
        return NotImplemented

    def __invert__(self):
        return Regular(self.dfa.complement())

    def __add__(self, other):
        if isinstance(other, Regular):
            try:
                nfa = self.dfa.concat(other.dfa)
            except ValueError:
                nfa = self.dfa.copy().concat(other.dfa)
            return Regular(DFA.from_NFA(nfa))
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Regular):
            return self & ~other
        return NotImplemented

    def __xor__(self, other):
        if isinstance(other, Regular):
            return (self - other) | (other - self)
        return NotImplemented

    def __bool__(self):
        return not self.dfa.is_empty()

    def __eq__(self, other):
        if isinstance(other, Regular):
            return not self - other and not other - self
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Regular):
            return not self - other
        return NotImplemented


@dataclass
class Token:
    """
    A lexical unit consisting of a type and the corresponding lexeme.
    """

    class Type(Enum):
        """
        Enumeration of token types
        """

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

    type: Type
    lexeme: str


class Lexer:
    """
    Regular expression lexical analyzer
    """

    def __init__(self, regex: str) -> None:
        self._input = iter(regex)

    def next_token(self) -> Token:
        """
        Get the next token
        """

        class State(Enum):
            """
            States of the lexical analyzer
            """

            START = 0
            ESCAPE = 1

        CHAR_TOKENS = {
            ".": Token.Type.DOT,
            "*": Token.Type.STAR,
            "+": Token.Type.PLUS,
            "?": Token.Type.QUESTION,
            "|": Token.Type.UNION,
            "(": Token.Type.L_PAREN,
            ")": Token.Type.R_PAREN,
            "[": Token.Type.L_BRACKET,
            "]": Token.Type.R_BRACKET,
        }
        state = State.START

        while True:
            c = next(self._input, None)

            match state:
                case State.START:
                    match c:
                        case None:
                            return Token(Token.Type.END, "")
                        case _ if c in CHAR_TOKENS:
                            return Token(CHAR_TOKENS[c], c)
                        case "\\":
                            state = State.ESCAPE
                        case _:
                            return Token(Token.Type.SYMBOL, c)
                case State.ESCAPE:
                    match c:
                        case None:
                            return Token(Token.Type.ERROR, "")
                        case _:
                            return Token(Token.Type.SYMBOL, c)


class Node:
    """
    A node in a syntax tree
    """

    class Operator(Enum):
        """
        Enumeration of operators
        """

        UNION = 0
        CONCAT = 1
        STAR = 2
        PLUS = 3
        QUESTION = 4

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
        """
        Evaluate the syntax tree to produce a regular language
        """
        if isinstance(self.val, Node.Operator):
            operator = self.val
            a = self.left.eval() if self.left is not None else None
            b = self.right.eval() if self.right is not None else None

            if a is None:
                raise Exception("missing left operand")

            match operator:
                case Node.Operator.UNION:
                    lang = a | b
                case Node.Operator.CONCAT:
                    lang = a + b
                case Node.Operator.STAR:
                    lang = Regular(DFA.from_NFA(a.dfa.star()))
                case Node.Operator.PLUS:
                    lang = a + Regular(DFA.from_NFA(a.dfa.star()))
                case Node.Operator.QUESTION:
                    lang = a | Regular.from_finite({""})
                case _:
                    raise ValueError("invalid operator")
        else:
            token = self.val
            match token.type:
                case Token.Type.SYMBOL:
                    lang = Regular.from_finite({token.lexeme})
                case Token.Type.DOT:
                    lang = Regular.from_finite(set(printable))
                case _:
                    raise ValueError("invalid operand")
        return lang


class Parser:
    """
    Regular expression parser
    """

    def __init__(self, regex: str) -> None:
        self._lexer = Lexer(regex)
        self._pushback: Optional[Token] = None

    def _next_token(self) -> Token:
        if self._pushback is not None:
            x = self._pushback
            self._pushback = None
            return x
        return self._lexer.next_token()

    def _pushback_token(self, token: Token) -> None:
        if self._pushback is None:
            self._pushback = token
        else:
            raise Exception("pushback error")

    def _parse_expr(self) -> Node:
        term1 = self._parse_term()

        if term1 is None:
            raise Exception("missing term")

        while True:
            token = self._next_token()

            if token.type is not Token.Type.UNION:
                self._pushback_token(token)
                break

            term2 = self._parse_term()
            if term2 is None:
                raise Exception("missing expression after '|'")

            term1 = Node(Node.Operator.UNION, term1, term2)

        return term1

    def _parse_term(self) -> Optional[Node]:
        factor1 = self._parse_factor()

        if factor1 is None:
            return None

        while True:
            factor2 = self._parse_factor()
            if factor2 is None:
                break
            factor1 = Node(Node.Operator.CONCAT, factor1, factor2)

        return factor1

    def _parse_factor(self) -> Optional[Node]:
        token = self._next_token()

        if token.type in (Token.Type.SYMBOL, Token.Type.DOT):
            expr = Node(token)
        elif token.type is Token.Type.L_PAREN:
            expr = self._parse_expr()
            if expr is None:
                raise Exception("syntax error")
            if self._next_token().type is not Token.Type.R_PAREN:
                raise Exception("missing ')'")
        else:
            self._pushback_token(token)
            return None

        while True:
            exponent = self._parse_exponent()
            if exponent is None:
                break

            exponent.left = expr
            expr = exponent

        return expr

    def _parse_exponent(self) -> Optional[Node]:
        token = self._next_token()

        match token.type:
            case Token.Type.STAR:
                return Node(Node.Operator.STAR)
            case Token.Type.PLUS:
                return Node(Node.Operator.PLUS)
            case Token.Type.QUESTION:
                return Node(Node.Operator.QUESTION)
            case _:
                self._pushback_token(token)
                return None

    def parse(self) -> Node:
        """
        Parse the regular expression to produce a syntax tree
        """
        return self._parse_expr()
