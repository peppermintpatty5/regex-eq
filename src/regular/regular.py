"""
Classes relating to regular languages and regular expression parsing.

`Regular` is the only class from this module that you should be using.
"""

from dataclasses import dataclass
from enum import Enum
from string import printable

from .dfa import DFA
from .nfa import NFA


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
        nfa = Parser(regex).parse().eval()

        return Regular(DFA.from_NFA(nfa))

    @staticmethod
    def from_finite(language: set[str]) -> "Regular":
        """
        Construct a regular language from a finite language.
        """
        nfa = NFA.empty()
        nfa.update_union(*(NFA.from_string(string) for string in language))

        return Regular(DFA.from_NFA(nfa))

    def __contains__(self, w):
        if isinstance(w, str):
            return self.dfa.accept(w)
        return NotImplemented

    def __and__(self, other):
        if isinstance(other, Regular):
            return Regular(DFA.intersection(self.dfa, other.dfa))
        return NotImplemented

    def __or__(self, other):
        if isinstance(other, Regular):
            nfa = NFA.empty()

            if self.dfa is other.dfa:
                nfa.update_union(self.dfa, self.dfa.copy())
            else:
                nfa.update_union(self.dfa, other.dfa)
            return Regular(DFA.from_NFA(nfa))
        return NotImplemented

    def __invert__(self):
        dfa = DFA.from_NFA(self.dfa)
        dfa.update_complement()

        return Regular(dfa)

    def __add__(self, other):
        if isinstance(other, Regular):
            nfa = NFA.from_string("")

            if self.dfa is other.dfa:
                nfa.update_concat(self.dfa, self.dfa.copy())
            else:
                nfa.update_concat(self.dfa, other.dfa)
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
        val: Operator | Token,
        left: "Node | None" = None,
        right: "Node | None" = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right

    def eval(self) -> NFA:
        """
        Evaluate the syntax tree to produce an NFA
        """
        if isinstance(self.val, Node.Operator):
            operator = self.val
            a = self.left.eval() if self.left is not None else None
            b = self.right.eval() if self.right is not None else None

            if a is None:
                raise Exception("missing left operand")

            match operator:
                case Node.Operator.UNION:
                    a.update_union(b)
                case Node.Operator.CONCAT:
                    a.update_concat(b)
                case Node.Operator.STAR:
                    a.update_star()
                case Node.Operator.PLUS:
                    a_copy = a.copy()
                    a_copy.update_star()
                    a.update_concat(a_copy)
                case Node.Operator.QUESTION:
                    a.update_union(NFA.from_string(""))
                case _:
                    raise ValueError("invalid operator")
            nfa = a
        else:
            token = self.val
            match token.type:
                case Token.Type.SYMBOL:
                    nfa = NFA.from_string(token.lexeme)
                case Token.Type.DOT:
                    nfa = NFA.empty()
                    nfa.update_union(*(NFA.from_string(s) for s in printable))
                case _:
                    raise ValueError("invalid operand")
        return nfa


class Parser:
    """
    Regular expression parser
    """

    def __init__(self, regex: str) -> None:
        self._lexer = Lexer(regex)
        self._pushback: Token | None = None

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

    def _parse_term(self) -> Node | None:
        factor1 = self._parse_factor()

        if factor1 is None:
            return None

        while True:
            factor2 = self._parse_factor()
            if factor2 is None:
                break
            factor1 = Node(Node.Operator.CONCAT, factor1, factor2)

        return factor1

    def _parse_factor(self) -> Node | None:
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

    def _parse_exponent(self) -> Node | None:
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
