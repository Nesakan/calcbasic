#!/usr/bin/env python3
"""
CASIO BASIC Tokenizer - Minimal Python Reference
Demonstrates keyword tokenization and arrow storage mapping.
"""

# --- CASIO Token Types (1-byte tokens like real calculators) ---
TOK_EOF = 0
TOK_PLUS = 1; TOK_MINUS = 2; TOK_STAR = 3; TOK_SLASH = 4
TOK_POWER = 5; TOK_EQUAL = 6; TOK_ARROW = 7  # → storage
TOK_LPAREN = 8; TOK_RPAREN = 9; TOK_COMMA = 10
TOK_SIN = 11; TOK_COS = 12; TOK_TAN = 13
TOK_SQR = 14; TOK_ABS = 15; TOK_LOG = 16; TOK_LN = 17
TOK_EXP = 18; TOK_RND = 19; TOK_SGN = 20
TOK_IDENT = 21; TOK_NUMBER = 22; TOK_STRING = 23
TOK_PRINT = 25; TOK_INPUT = 26; TOK_FOR = 27; TOK_NEXT = 28
TOK_GOTO = 29; TOK_GOSUB = 30; TOK_RETURN = 31
TOK_IF = 32; TOK_THEN = 33; TOK_TO = 34; TOK_STEP = 35
TOK_DIM = 36; TOK_CLEAR = 37; TOK_MODE = 38; TOK_COMPLEX = 39; TOK_BASEN = 40


# --- Keyword → Token mapping (CASIO-style) ---
KEYWORDS = {
    "PRINT": TOK_PRINT, "INPUT": TOK_INPUT, "FOR": TOK_FOR, "NEXT": TOK_NEXT,
    "GOTO": TOK_GOTO, "GOSUB": TOK_GOSUB, "RETURN": TOK_RETURN,
    "IF": TOK_IF, "THEN": TOK_THEN, "TO": TOK_TO, "STEP": TOK_STEP,
    "DIM": TOK_DIM, "CLEAR": TOK_CLEAR, "MODE": TOK_MODE,
    "SIN": TOK_SIN, "COS": TOK_COS, "TAN": TOK_TAN,
    "SQR": TOK_SQR, "ABS": TOK_ABS, "SGN": TOK_SGN,
    "LOG": TOK_LOG, "LN": TOK_LN, "EXP": TOK_EXP, "RND": TOK_RND,
    "COMPLEX": TOK_COMPLEX, "BASEN": TOK_BASEN,
}


def tokenize(source: str) -> list:
    """
    Tokenize CASIO BASIC source into list of token type integers.
    CASIO calculators use compact 1-byte tokens, not raw ASCII.
    """
    tokens = []
    pos = 0
    length = len(source)

    while pos < length:
        ch = source[pos]

        # Skip whitespace
        if ch in " \t":
            pos += 1; continue

        # Right arrow → (storage, distinct from =)
        if ch == "→":
            tokens.append(TOK_ARROW); pos += 1; continue

        # String literal "text"
        if ch == '"':
            end = source.find('"', pos + 1)
            if end == -1: end = length
            tokens.append(TOK_STRING); pos = end + 1; continue

        # Number
        if ch.isdigit() or (ch == "." and pos + 1 < length and source[pos+1].isdigit()):
            # consume full number
            start = pos
            while pos < length and (source[pos].isdigit() or source[pos] == "."):
                pos += 1
            tokens.append(TOK_NUMBER)
            # In full impl: also capture the numeric value
            # but for token-type-only: just append TOK_NUMBER
            continue

        # Identifier / Keyword
        if ch.isalpha() or ch == "_":
            # consume full word
            start = pos
            while pos < length and (source[pos].isalnum() or source[pos] == "_"):
                pos += 1
            word = source[start:pos].upper()
            # Look up keyword
            tok = KEYWORDS.get(word)
            if tok is not None:
                tokens.append(tok)
            else:
                # Not a keyword → identifier (variable)
                tokens.append(TOK_IDENT)
            continue

        # Single-char operators/delimiters
        op_map = {"+": TOK_PLUS, "-": TOK_MINUS, "*": TOK_STAR,
                  "/": TOK_SLASH, "^": TOK_POWER, "=": TOK_EQUAL,
                  "(": TOK_LPAREN, ")": TOK_RPAREN, ",": TOK_COMMA}
        if ch in op_map:
            tokens.append(op_map[ch]); pos += 1; continue

        # Unknown character
        raise RuntimeError(f"Illegal char '{ch}' at pos {pos}")

    tokens.append(TOK_EOF)
    return tokens


def token_to_str(t: int) -> str:
    """Human-readable token name."""
    names = {
        0: "EOF", 1: "PLUS", 2: "MINUS", 3: "STAR", 4: "SLASH",
        5: "POWER", 6: "EQUAL", 7: "ARROW (→)", 8: "LPAREN", 9: "RPAREN",
        10: "COMMA", 11: "SIN", 12: "COS", 13: "TAN",
        14: "SQR", 15: "ABS", 16: "LOG", 17: "LN", 18: "EXP", 19: "RND",
        21: "IDENT", 22: "NUMBER", 25: "PRINT", 26: "INPUT",
        27: "FOR", 28: "NEXT", 29: "GOTO", 30: "GOSUB", 31: "RETURN",
        32: "IF", 33: "THEN", 34: "TO", 35: "STEP", 36: "DIM",
        37: "CLEAR", 38: "MODE", 39: "COMPLEX", 40: "BASE-N",
    }
    return names.get(t, f"UNK({t})")


# --- Quick Demo ---
if __name__ == "__main__":
    programs = [
        '10 PRINT A',
        '10 A → 10',
        '10 SQR 16',
        '10 FOR I = 1 TO 10',
        '10 PRINT "HELLO"',
    ]

    print("=== CASIO BASIC Tokenizer Demo ===\n")
    for src in programs:
        try:
            toks = tokenize(src)
            print(f"Source: {src}")
            print(f"Tokens: {[token_to_str(t) for t in toks]}")
        except Exception as e:
            print(f"Source: {src}  ERROR: {e}")
        print()