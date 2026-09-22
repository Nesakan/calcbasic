# CalcBASIC Lexer / Tokenizer - Phase 1

# Token types:
#   NUMBER      - Floating point or integer literals (e.g., 42, 3.14)
#   IDENTIFIER  - Variable names (e.g., A, B, X, MyVar)
#   STRING      - String literal (e.g., "Hello", "World")
#   PLUS        - Addition operator (+) or string concatenation
#   MINUS       - Subtraction operator (-) or unary negation
#   STAR        - Multiplication operator (*)
#   SLASH       - Division operator (/)
#   POWER       - Exponentiation operator (^)
#   LEFT_PAREN  - Left parenthesis (()
#   RIGHT_PAREN - Right parenthesis ())
#   EQUAL       - Assignment operator (=) or equality comparison (=, ==)
#   NOT_EQUAL   - Not equal comparison (<>, !=)
#   LESS        - Less than comparison (<)
#   GREATER     - Greater than comparison (>)
#   LESS_EQUAL  - Less than or equal comparison (<=)
#   GREATER_EQUAL - Greater than or equal comparison (>=)
#   AND         - Logical AND operator
#   OR          - Logical OR operator
#   NOT         - Logical NOT operator
#   COMMA       - Argument separator (,)
#   SEMICOLON   - Semicolon delimiter (;)
#   NEWLINE     - Line terminator (end of a line)
#   EOF         - End of file marker

import re
from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Token:
    """Represents a single token produced by the lexer."""
    type: str
    value: Optional[Union[str, float]]
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line}, col={self.column})"


# Keyword mapping: maps keyword strings to their token types.
# Currently empty; will be populated as language features are added.
KEYWORDS: dict = {
    "PRINT": "PRINT",
    "AND": "AND",
    "OR": "OR",
    "NOT": "NOT",
    "IF": "IF",
    "THEN": "THEN",
    "ELSE": "ELSE",
    "ENDIF": "ENDIF",
    "END": "END",
    "FOR": "FOR",
    "TO": "TO",
    "STEP": "STEP",
    "NEXT": "NEXT",
    "INPUT": "INPUT",
}



# ---------------------------------------------------------------------------
# Core lexer logic


def tokenize(source: str, filename: Optional[str] = None) -> List[Token]:
    """
    Convert source code string into a list of Token objects.

    The lexer reads the source character-by-character and emits tokens
    for numbers, identifiers, operators, and delimiters.

    Args:
        source: The source code string to tokenize.
        filename: Optional filename for error reporting.

    Returns:
        A list of Token objects ending with an EOF token.

    Raises:
        ValueError: If an illegal character is encountered.
    """
    if filename is None:
        filename = "<calcbasic>"

    tokens: List[Token] = []
    line = 1
    column = 1
    pos = 0
    length = len(source)

    while pos < length:
        char = source[pos]
        start_col = column

        # ---- Newline handling ----
        if char == "\n":
            tokens.append(Token(type="NEWLINE", value=None, line=line, column=start_col))
            line += 1
            column = 1
            pos += 1
            continue

        # ---- Skip whitespace (but not newline above) ----
        if char in " \t\r":
            column += 1
            pos += 1
            continue

        # ---- String literals ----
        if char == '"' or char == "'":
            quote_char = char
            string_value, consumed, new_col = _read_string(
                source, pos, quote_char, column, length, line, filename
            )
            tokens.append(Token(type="STRING", value=string_value, line=line, column=start_col))
            column = new_col
            pos += consumed
            continue

        # ---- Numbers ----
        if char.isdigit() or (char == "." and pos < length and source[pos + 1].isdigit()):
            num_str, consumed, new_col = _read_number(source, pos, column, length)
            # Convert to float if it contains a decimal point, else int
            if "." in num_str:
                value: float = float(num_str)
            else:
                value: int = int(num_str)
                # Python int -> keep as int for simplicity; interpreter can cast
            tokens.append(Token(type="NUMBER", value=value, line=line, column=start_col))
            column = new_col
            pos += consumed
            continue

        # ---- Identifiers and keywords ----
        if char.isalpha() or char == "_":
            ident, consumed, new_col = _read_identifier(source, pos, column, length)
            # Check if it's a keyword (case-insensitive)
            token_type = KEYWORDS.get(ident.upper(), "IDENTIFIER")
            val = ident.upper() if token_type != "IDENTIFIER" else ident
            tokens.append(Token(type=token_type, value=val, line=line, column=start_col))
            column = new_col
            pos += consumed
            continue

        # ---- Operators and delimiters ----
        if char == "+":
            tokens.append(Token(type="PLUS", value="+", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == "-":
            tokens.append(Token(type="MINUS", value="-", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == "*":
            tokens.append(Token(type="STAR", value="*", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == "/":
            tokens.append(Token(type="SLASH", value="/", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == "^":
            tokens.append(Token(type="POWER", value="^", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == "(":
            tokens.append(Token(type="LEFT_PAREN", value="(", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == ")":
            tokens.append(Token(type="RIGHT_PAREN", value=")", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == ",":
            tokens.append(Token(type="COMMA", value=",", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == ";":
            tokens.append(Token(type="SEMICOLON", value=";", line=line, column=start_col))
            column += 1
            pos += 1
            continue
        if char == "<":
            if pos + 1 < length and source[pos + 1] == "=":
                tokens.append(Token(type="LESS_EQUAL", value="<=", line=line, column=start_col))
                column += 2
                pos += 2
            elif pos + 1 < length and source[pos + 1] == ">":
                tokens.append(Token(type="NOT_EQUAL", value="<>", line=line, column=start_col))
                column += 2
                pos += 2
            else:
                tokens.append(Token(type="LESS", value="<", line=line, column=start_col))
                column += 1
                pos += 1
            continue
        if char == ">":
            if pos + 1 < length and source[pos + 1] == "=":
                tokens.append(Token(type="GREATER_EQUAL", value=">=", line=line, column=start_col))
                column += 2
                pos += 2
            else:
                tokens.append(Token(type="GREATER", value=">", line=line, column=start_col))
                column += 1
                pos += 1
            continue
        if char == "=":
            if pos + 1 < length and source[pos + 1] == "=":
                tokens.append(Token(type="EQUAL", value="==", line=line, column=start_col))
                column += 2
                pos += 2
            else:
                tokens.append(Token(type="EQUAL", value="=", line=line, column=start_col))
                column += 1
                pos += 1
            continue
        if char == "!":
            if pos + 1 < length and source[pos + 1] == "=":
                tokens.append(Token(type="NOT_EQUAL", value="!=", line=line, column=start_col))
                column += 2
                pos += 2
                continue
            else:
                raise ValueError(
                    f"Illegal character '{char!r}' at line {line}, column {start_col} "
                    f"in {filename}"
                )

        # ---- Unknown character ----
        raise ValueError(
            f"Illegal character '{char!r}' at line {line}, column {start_col} "
            f"in {filename}"
        )

    # Append EOF token
    tokens.append(Token(type="EOF", value=None, line=line, column=column))
    return tokens


def _read_number(source: str, pos: int, column: int, length: int) -> tuple:
    """
    Read a numeric literal starting at ``pos``.

    Consumes digits and at most one decimal point followed by digits.
    Returns (number_string, characters_consumed, new_column).
    """
    start_pos = pos
    has_dot = False

    while pos < length:
        ch = source[pos]
        if ch.isdigit():
            pos += 1
        elif ch == "." and not has_dot:
            # Look ahead: only accept the dot if there are digits after it
            if pos + 1 < length and source[pos + 1].isdigit():
                has_dot = True
                pos += 1
            else:
                break
        else:
            break

    num_str = source[start_pos:pos]
    # New column is past the number
    new_column = column + (pos - start_pos)
    consumed = pos - start_pos
    return num_str, consumed, new_column


def _read_identifier(source: str, pos: int, column: int, length: int) -> tuple:
    """
    Read an identifier (letter or underscore followed by word characters).

    Returns (identifier_string, characters_consumed, new_column).
    """
    start_pos = pos

    while pos < length and (source[pos].isalnum() or source[pos] == "_"):
        pos += 1

    # Support optional trailing '$' for string variables / functions in BASIC
    if pos < length and source[pos] == "$":
        pos += 1

    ident = source[start_pos:pos]
    new_column = column + (pos - start_pos)
    consumed = pos - start_pos
    return ident, consumed, new_column


def _read_string(
    source: str,
    pos: int,
    quote_char: str,
    column: int,
    length: int,
    line: int = 1,
    filename: str = "<calcbasic>",
) -> tuple:
    """
    Read a string literal starting at ``pos`` (at the opening quote).

    Handles basic escape sequences: \\n, \\t, \\", \\', \\\\
    Returns (string_value, characters_consumed, new_column).

    Raises:
        ValueError: If the string literal is not closed before newline or EOF.
    """
    start_pos = pos
    start_col = column
    pos += 1  # Skip opening quote
    result = []
    escape_next = False
    closed = False

    while pos < length:
        ch = source[pos]
        pos += 1

        if escape_next:
            # Handle escape sequences
            if ch == "n":
                result.append("\n")
            elif ch == "t":
                result.append("\t")
            elif ch == '"' or ch == "'":
                result.append(ch)
            elif ch == "\\":
                result.append("\\")
            else:
                # Unknown escape: keep the backslash and the character
                result.append("\\" + ch)
            escape_next = False
        elif ch == "\\":
            escape_next = True
        elif ch == quote_char:
            # Closing quote found
            closed = True
            break
        elif ch == "\n":
            # Unterminated string literal before newline
            raise ValueError(
                f"Unterminated string literal at line {line}, column {start_col} in {filename}"
            )
        else:
            result.append(ch)

    if not closed:
        raise ValueError(
            f"Unterminated string literal at line {line}, column {start_col} in {filename}"
        )

    string_value = "".join(result)
    consumed = pos - start_pos
    new_column = column + consumed
    return string_value, consumed, new_column


# ---------------------------------------------------------------------------
# Example / test harness

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m calcbasic.lexer <source_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tokens = tokenize(source, filepath)

    print(f"Tokenizing `{filepath}`:")
    for tok in tokens:
        print(tok)