from enum import Enum
from string import printable
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
        return Parser(regex).parse_expr().eval()

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


class Token:
    class Type(Enum):
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

    def __init__(self, type: Type, lexeme: str) -> None:
        self.type = type
        self.lexeme = lexeme


class Lexer:
    """
    Regular expression lexical analyzer
    """

    def __init__(self, regex: str) -> None:
        self._input = iter(regex)

    def next_token(self) -> Token:
        class State(Enum):
            START = 0
            ESCAPE = 1

        state = State.START

        while True:
            c = next(self._input, None)

            match state:
                case State.START:
                    match c:
                        case None:
                            return Token(Token.Type.END, "")
                        case ".":
                            return Token(Token.Type.DOT, ".")
                        case ".":
                            return Token(Token.Type.DOT, ".")
                        case "*":
                            return Token(Token.Type.STAR, "*")
                        case "+":
                            return Token(Token.Type.PLUS, "+")
                        case "?":
                            return Token(Token.Type.QUESTION, "?")
                        case "|":
                            return Token(Token.Type.UNION, "|")
                        case "(":
                            return Token(Token.Type.L_PAREN, "(")
                        case ")":
                            return Token(Token.Type.R_PAREN, ")")
                        case "[":
                            return Token(Token.Type.L_BRACKET, "[")
                        case "]":
                            return Token(Token.Type.R_BRACKET, "]")
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

            match operator:
                case Operator.UNION:
                    return a | b
                case Operator.CONCAT:
                    return a + b
                case Operator.STAR:
                    return Regular(DFA.from_NFA(a.dfa.star()))
                case Operator.PLUS:
                    return a + Regular(DFA.from_NFA(a.dfa.star()))
                case Operator.QUESTION:
                    return a | Regular.from_finite({""})
                case _:
                    raise ValueError("invalid operator")

        elif type(self.val) is Token:
            token = self.val

            match token.type:
                case Token.Type.SYMBOL:
                    return Regular.from_finite({token.lexeme})
                case Token.Type.DOT:
                    return Regular.from_finite(set(printable))
                case _:
                    raise ValueError("invalid operand")

        else:
            raise Exception("how did this happen?")


class Parser:
    """
    Regular expression parser
    """

    def __init__(self, regex: str) -> None:
        self._lexer = Lexer(regex)
        self._pushback: Optional[Token] = None

    def next_token(self) -> Token:
        if self._pushback is not None:
            x = self._pushback
            self._pushback = None
            return x
        return self._lexer.next_token()

    def pushback_token(self, token: Token) -> None:
        if self._pushback is None:
            self._pushback = token
        else:
            raise Exception("pushback error")

    def parse_expr(self) -> Node:
        term1 = self.parse_term()

        if term1 is None:
            raise Exception("missing term")

        while True:
            token = self.next_token()

            if token.type is not Token.Type.UNION:
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
            factor1 = Node(Operator.CONCAT, factor1, factor2)

        return factor1

    def parse_factor(self) -> Optional[Node]:
        token = self.next_token()

        if token.type in (Token.Type.SYMBOL, Token.Type.DOT):
            expr = Node(token)
        elif token.type is Token.Type.L_PAREN:
            expr = self.parse_expr()
            if expr is None:
                raise Exception("syntax error")
            if self.next_token().type is not Token.Type.R_PAREN:
                raise Exception("missing ')'")
        else:
            self.pushback_token(token)
            return None

        while True:
            exponent = self.parse_exponent()
            if exponent is None:
                break

            exponent.left = expr
            expr = exponent

        return expr

    def parse_exponent(self) -> Optional[Node]:
        token = self.next_token()

        match token.type:
            case Token.Type.STAR:
                return Node(Operator.STAR)
            case Token.Type.PLUS:
                return Node(Operator.PLUS)
            case Token.Type.QUESTION:
                return Node(Operator.QUESTION)
            case _:
                self.pushback_token(token)
                return None
