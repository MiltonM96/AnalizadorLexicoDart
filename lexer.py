"""
Analizador Léxico para Dart
Implementado mediante autómata finito determinista (AFD) manual.
Cada estado del autómata corresponde a un tipo de token siendo reconocido.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List


# ─── Tipos de tokens ────────────────────────────────────────────────────────

class TokenType(Enum):
    # Palabras reservadas
    KEYWORD         = "Palabra reservada"
    # Tipos primitivos
    TYPE            = "Tipo primitivo"
    # Literales
    LIT_INT         = "Constante entera"
    LIT_DOUBLE      = "Constante real"
    LIT_STRING_SQ   = "Cadena (comilla simple)"
    LIT_STRING_DQ   = "Cadena (comilla doble)"
    LIT_BOOL        = "Literal booleano"
    LIT_NULL        = "Literal null"
    # Identificadores
    IDENTIFIER      = "Identificador"
    # Operadores
    OP_ARITH        = "Op. aritmético"
    OP_ASSIGN       = "Op. asignación"
    OP_COMPARE      = "Op. comparación"
    OP_LOGIC        = "Op. lógico"
    OP_BITWISE      = "Op. bit a bit"
    OP_TERNARY      = "Op. ternario"
    OP_CASCADE      = "Op. cascada"
    OP_SPREAD       = "Op. spread"
    OP_NULL         = "Op. null-aware"
    OP_ARROW        = "Op. flecha"
    OP_TYPE         = "Op. tipo (is/as)"
    # Símbolos
    DELIMITER       = "Delimitador"
    # Comentarios
    COMMENT_LINE    = "Comentario línea"
    COMMENT_BLOCK   = "Comentario bloque"
    # Blancos
    WHITESPACE      = "Blanco"
    NEWLINE         = "Salto de línea"
    # Error
    ERROR           = "Error léxico"


# ─── Conjuntos de palabras ───────────────────────────────────────────────────

DART_KEYWORDS = {
    'abstract', 'assert', 'async', 'await', 'base', 'break', 'case',
    'catch', 'class', 'const', 'continue', 'covariant', 'default', 'deferred',
    'do', 'dynamic', 'else', 'enum', 'export', 'extends', 'extension',
    'external', 'factory', 'final', 'finally', 'for', 'Function', 'get',
    'hide', 'if', 'implements', 'import', 'in', 'interface', 'late',
    'library', 'mixin', 'new', 'of', 'on', 'operator', 'part', 'required',
    'rethrow', 'return', 'sealed', 'set', 'show', 'static', 'super', 'switch',
    'sync', 'this', 'throw', 'try', 'typedef', 'var', 'void', 'when',
    'while', 'with', 'yield',
}

DART_TYPES = {
    'int', 'double', 'num', 'String', 'bool', 'List', 'Map', 'Set',
    'Object', 'Iterable', 'Future', 'Stream', 'Never', 'Null',
}

DART_BOOLEANS = {'true', 'false'}
DART_NULL     = {'null'}
DART_TYPE_OPS = {'is', 'as'}  # operadores de tipo — usan OP_TYPE, no KEYWORD


# ─── Token ──────────────────────────────────────────────────────────────────

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    col: int
    error_msg: str = ""

    def to_dict(self):
        return {
            "type":      self.type.value,
            "type_key":  self.type.name,
            "lexeme":    self.lexeme,
            "line":      self.line,
            "col":       self.col,
            "error_msg": self.error_msg,
        }


# ─── Tablas de operadores (fuera del loop para no recrearlas por carácter) ───

_THREE_CHAR_OPS: dict[str, TokenType] = {
    '>>>': TokenType.OP_BITWISE,
    '<<=': TokenType.OP_ASSIGN,
    '>>=': TokenType.OP_ASSIGN,
    '~/=': TokenType.OP_ASSIGN,
}

_TWO_CHAR_OPS: dict[str, TokenType] = {
    '==': TokenType.OP_COMPARE,
    '!=': TokenType.OP_COMPARE,
    '<=': TokenType.OP_COMPARE,
    '>=': TokenType.OP_COMPARE,
    '&&': TokenType.OP_LOGIC,
    '||': TokenType.OP_LOGIC,
    '+=': TokenType.OP_ASSIGN,
    '-=': TokenType.OP_ASSIGN,
    '*=': TokenType.OP_ASSIGN,
    '/=': TokenType.OP_ASSIGN,
    '%=': TokenType.OP_ASSIGN,
    '~/': TokenType.OP_ARITH,   # división entera
    '++': TokenType.OP_ARITH,
    '--': TokenType.OP_ARITH,
    '<<': TokenType.OP_BITWISE,
    '>>': TokenType.OP_BITWISE,
    '&=': TokenType.OP_ASSIGN,
    '|=': TokenType.OP_ASSIGN,
    '^=': TokenType.OP_ASSIGN,
    '->': TokenType.OP_ARROW,
}

_SINGLE_OPS: dict[str, TokenType] = {
    '+': TokenType.OP_ARITH,
    '-': TokenType.OP_ARITH,
    '*': TokenType.OP_ARITH,
    '/': TokenType.OP_ARITH,
    '%': TokenType.OP_ARITH,
    '~': TokenType.OP_BITWISE,  # complemento a bits, no aritmético
    '=': TokenType.OP_ASSIGN,
    '<': TokenType.OP_COMPARE,
    '>': TokenType.OP_COMPARE,
    '!': TokenType.OP_LOGIC,
    '&': TokenType.OP_BITWISE,
    '|': TokenType.OP_BITWISE,
    '^': TokenType.OP_BITWISE,
    ':': TokenType.OP_TERNARY,
}

_DELIMITERS: set[str] = {'(', ')', '{', '}', '[', ']', ';', ',', '@'}


# ─── Autómata / Lexer ────────────────────────────────────────────────────────

class DartLexer:
    """
    Implementa un AFD manual que lee carácter a carácter y transiciona
    entre estados para reconocer los distintos lexemas de Dart.
    """

    def __init__(self, source: str):
        self.src   = source
        self.pos   = 0
        self.line  = 1
        self.col   = 1
        self.tokens: List[Token] = []

    # ── helpers ──

    def _peek(self, offset=0) -> str:
        idx = self.pos + offset
        return self.src[idx] if idx < len(self.src) else ''

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _add(self, ttype: TokenType, lexeme: str, line: int, col: int, err=""):
        self.tokens.append(Token(ttype, lexeme, line, col, err))

    # ── estados del AFD ──

    def _read_whitespace(self, start_line, start_col) -> str:
        """Estado: consumir espacios y tabs (no newlines)."""
        buf = ""
        while self._peek() in (' ', '\t', '\r'):
            buf += self._advance()
        return buf

    def _read_newlines(self, start_line, start_col) -> str:
        """Estado: consumir saltos de línea consecutivos."""
        buf = ""
        while self._peek() == '\n':
            buf += self._advance()
        return buf

    def _read_line_comment(self) -> str:
        """Estado: comentario de línea // ..."""
        buf = ""
        while self._peek() and self._peek() != '\n':
            buf += self._advance()
        return buf

    def _read_block_comment(self) -> tuple[str, bool]:
        """Estado: comentario de bloque /* ... */ (anidado Dart-style)."""
        buf = ""
        depth = 1
        while self.pos < len(self.src):
            ch = self._advance()
            buf += ch
            if ch == '/' and self._peek() == '*':
                buf += self._advance()
                depth += 1
            elif ch == '*' and self._peek() == '/':
                buf += self._advance()
                depth -= 1
                if depth == 0:
                    return buf, True
        return buf, False  # sin cerrar

    def _read_string(self, quote: str) -> tuple[str, bool]:
        """Estado: cadena delimitada por quote (simple o doble), con escapes."""
        buf = ""
        while self.pos < len(self.src):
            ch = self._peek()
            if ch == '\n' or ch == '':
                return buf, False  # sin cerrar
            ch = self._advance()
            buf += ch
            if ch == '\\':             # escape
                if self._peek():
                    buf += self._advance()
            elif ch == quote:
                return buf, True
        return buf, False

    def _read_number(self, first: str) -> tuple[str, TokenType, str]:
        """Estado: número entero o real (incluyendo hex 0x...)."""
        buf = first
        # hex
        if first == '0' and self._peek() in ('x', 'X'):
            buf += self._advance()
            while re.match(r'[0-9a-fA-F_]', self._peek() or ''):
                buf += self._advance()
            return buf, TokenType.LIT_INT, ""

        # dígitos enteros
        while re.match(r'[0-9_]', self._peek() or ''):
            buf += self._advance()

        # parte decimal
        is_double = False
        if self._peek() == '.' and re.match(r'[0-9]', self._peek(1) or ''):
            is_double = True
            buf += self._advance()  # '.'
            while re.match(r'[0-9_]', self._peek() or ''):
                buf += self._advance()

        # exponente
        if self._peek() in ('e', 'E'):
            is_double = True
            buf += self._advance()
            if self._peek() in ('+', '-'):
                buf += self._advance()
            if not re.match(r'[0-9]', self._peek() or ''):
                return buf, TokenType.ERROR, "Exponente sin dígitos"
            while re.match(r'[0-9]', self._peek() or ''):
                buf += self._advance()

        return buf, TokenType.LIT_DOUBLE if is_double else TokenType.LIT_INT, ""

    def _read_identifier(self, first: str) -> str:
        """Estado: identificador o palabra reservada."""
        buf = first
        while re.match(r'[a-zA-Z0-9_$]', self._peek() or ''):
            buf += self._advance()
        return buf

    def _read_raw_string(self, quote: str) -> tuple[str, bool]:
        """Estado: cadena raw r'...' o r\"...\" — sin procesamiento de escapes."""
        buf = ""
        while self.pos < len(self.src):
            ch = self._peek()
            if ch == '\n' or ch == '':
                return buf, False
            ch = self._advance()
            buf += ch
            if ch == quote:
                return buf, True
        return buf, False

    # ── tokenización principal ──

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.src):
            sl, sc = self.line, self.col
            ch = self._advance()

            # ── Blancos ──
            if ch in (' ', '\t', '\r'):
                rest = self._read_whitespace(sl, sc)
                self._add(TokenType.WHITESPACE, ch + rest, sl, sc)
                continue

            if ch == '\n':
                rest = self._read_newlines(sl, sc)
                self._add(TokenType.NEWLINE, ch + rest, sl, sc)
                continue

            # ── Comentarios ──
            if ch == '/' and self._peek() == '/':
                self._advance()  # segundo /
                body = self._read_line_comment()
                self._add(TokenType.COMMENT_LINE, '//' + body, sl, sc)
                continue

            if ch == '/' and self._peek() == '*':
                self._advance()  # *
                body, closed = self._read_block_comment()
                if closed:
                    self._add(TokenType.COMMENT_BLOCK, '/*' + body, sl, sc)
                else:
                    self._add(TokenType.ERROR, '/*' + body, sl, sc, "Comentario de bloque sin cerrar")
                continue

            # ── Cadenas ──
            if ch in ('"', "'"):
                # comprobar triple-quote
                if self._peek() == ch and self._peek(1) == ch:
                    self._advance(); self._advance()
                    triple = ch * 3
                    body = ""
                    closed = False
                    while self.pos < len(self.src):
                        c = self._advance()
                        body += c
                        if c == ch and self._peek() == ch and self._peek(1) == ch:
                            self._advance(); self._advance()
                            body += ch * 2
                            closed = True
                            break
                    ttype = TokenType.LIT_STRING_SQ if ch == "'" else TokenType.LIT_STRING_DQ
                    if closed:
                        self._add(ttype, triple + body, sl, sc)
                    else:
                        self._add(TokenType.ERROR, triple + body, sl, sc, "Cadena triple sin cerrar")
                else:
                    body, closed = self._read_string(ch)
                    ttype = TokenType.LIT_STRING_SQ if ch == "'" else TokenType.LIT_STRING_DQ
                    if closed:
                        self._add(ttype, ch + body, sl, sc)
                    else:
                        self._add(TokenType.ERROR, ch + body, sl, sc, "Cadena sin cerrar")
                continue

            # ── Números ──
            if ch.isdigit():
                lexeme, ttype, err = self._read_number(ch)
                self._add(ttype, lexeme, sl, sc, err)
                continue

            # ── Identificadores / palabras reservadas ──
            if ch.isalpha() or ch in ('_', '$'):
                lexeme = self._read_identifier(ch)
                # prefijo r para cadenas raw: r'...' r"..." r'''...''' r"""..."""
                if lexeme == 'r' and self._peek() in ('"', "'"):
                    raw_quote = self._advance()
                    ttype = TokenType.LIT_STRING_SQ if raw_quote == "'" else TokenType.LIT_STRING_DQ
                    if self._peek() == raw_quote and self._peek(1) == raw_quote:
                        # triple raw string
                        self._advance(); self._advance()
                        triple = raw_quote * 3
                        body = ""
                        closed = False
                        while self.pos < len(self.src):
                            c = self._advance()
                            body += c
                            if c == raw_quote and self._peek() == raw_quote and self._peek(1) == raw_quote:
                                self._advance(); self._advance()
                                body += raw_quote * 2
                                closed = True
                                break
                        if closed:
                            self._add(ttype, 'r' + triple + body, sl, sc)
                        else:
                            self._add(TokenType.ERROR, 'r' + triple + body, sl, sc, "Cadena raw triple sin cerrar")
                    else:
                        body, closed = self._read_raw_string(raw_quote)
                        if closed:
                            self._add(ttype, 'r' + raw_quote + body, sl, sc)
                        else:
                            self._add(TokenType.ERROR, 'r' + raw_quote + body, sl, sc, "Cadena raw sin cerrar")
                elif lexeme in DART_BOOLEANS:
                    self._add(TokenType.LIT_BOOL, lexeme, sl, sc)
                elif lexeme in DART_NULL:
                    self._add(TokenType.LIT_NULL, lexeme, sl, sc)
                elif lexeme in DART_TYPE_OPS:
                    self._add(TokenType.OP_TYPE, lexeme, sl, sc)
                elif lexeme in DART_KEYWORDS:
                    self._add(TokenType.KEYWORD, lexeme, sl, sc)
                elif lexeme in DART_TYPES:
                    self._add(TokenType.TYPE, lexeme, sl, sc)
                else:
                    self._add(TokenType.IDENTIFIER, lexeme, sl, sc)
                continue

            # ── Operadores y símbolos ──

            # null-aware: ??, ??=, ?., ?
            if ch == '?':
                if self._peek() == '?' and self._peek(1) == '=':
                    self._advance(); self._advance()
                    self._add(TokenType.OP_ASSIGN, '??=', sl, sc)
                elif self._peek() == '?':
                    self._advance()
                    self._add(TokenType.OP_NULL, '??', sl, sc)
                elif self._peek() == '.':
                    self._advance()
                    self._add(TokenType.OP_NULL, '?.', sl, sc)
                else:
                    self._add(TokenType.OP_TERNARY, '?', sl, sc)
                continue

            # spread: ...?  ...
            if ch == '.' and self._peek() == '.' and self._peek(1) == '.':
                self._advance(); self._advance()
                if self._peek() == '?':
                    self._advance()
                    self._add(TokenType.OP_SPREAD, '...?', sl, sc)
                else:
                    self._add(TokenType.OP_SPREAD, '...', sl, sc)
                continue

            # cascade: ..
            if ch == '.' and self._peek() == '.':
                self._advance()
                self._add(TokenType.OP_CASCADE, '..', sl, sc)
                continue

            # point (member access / decimal — ya capturado en número)
            if ch == '.':
                self._add(TokenType.DELIMITER, '.', sl, sc)
                continue

            # arrow =>
            if ch == '=' and self._peek() == '>':
                self._advance()
                self._add(TokenType.OP_ARROW, '=>', sl, sc)
                continue

            # >>>= (4 caracteres — antes que >>> y >>=)
            if ch + self._peek() + self._peek(1) + self._peek(2) == '>>>=':
                self._advance(); self._advance(); self._advance()
                self._add(TokenType.OP_ASSIGN, '>>>=', sl, sc)
                continue

            # operadores de 3 caracteres (>>>, <<=, >>=, ~/=)
            three = ch + self._peek() + self._peek(1)
            if three in _THREE_CHAR_OPS:
                self._advance(); self._advance()
                self._add(_THREE_CHAR_OPS[three], three, sl, sc)
                continue

            # operadores de 2 caracteres
            two = ch + self._peek()
            if two in _TWO_CHAR_OPS:
                self._advance()
                self._add(_TWO_CHAR_OPS[two], two, sl, sc)
                continue

            # operadores de 1 carácter
            if ch in _SINGLE_OPS:
                self._add(_SINGLE_OPS[ch], ch, sl, sc)
                continue

            # delimitadores
            if ch in _DELIMITERS:
                self._add(TokenType.DELIMITER, ch, sl, sc)
                continue

            # carácter desconocido → error léxico
            self._add(TokenType.ERROR, ch, sl, sc, f"Carácter no reconocido: '{ch}'")

        return self.tokens


# ─── API pública ─────────────────────────────────────────────────────────────

def analyze(source: str, include_whitespace: bool = False) -> dict:
    lexer = DartLexer(source)
    all_tokens = lexer.tokenize()

    visible = all_tokens if include_whitespace else [
        t for t in all_tokens if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)
    ]

    counts = {}
    error_count = 0
    for t in all_tokens:
        counts[t.type.value] = counts.get(t.type.value, 0) + 1
        if t.type == TokenType.ERROR:
            error_count += 1

    return {
        "tokens":      [t.to_dict() for t in visible],
        "total":       len(all_tokens),
        "visible":     len(visible),
        "errors":      error_count,
        "lines":       lexer.line,
        "counts":      counts,
    }
