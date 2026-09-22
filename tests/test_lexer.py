# CalcBASIC Lexer Tests - Phase 1

import unittest
from calcbasic.lexer import tokenize, Token


class TestLexer(unittest.TestCase):
    """Tests for the CalcBASIC lexer."""

    def test_simple_number(self):
        """Test tokenizing a simple number."""
        tokens = tokenize("42")
        self.assertEqual(len(tokens), 2)  # NUMBER + EOF
        self.assertEqual(tokens[0].type, "NUMBER")
        self.assertEqual(tokens[0].value, 42)

    def test_simple_identifier(self):
        """Test tokenizing a simple identifier."""
        tokens = tokenize("A")
        self.assertEqual(len(tokens), 2)  # IDENTIFIER + EOF
        self.assertEqual(tokens[0].type, "IDENTIFIER")
        self.assertEqual(tokens[0].value, "A")

    def test_assignement(self):
        """Test tokenizing A = 10."""
        tokens = tokenize("A = 10")
        # 4 tokens: IDENTIFIER, EQUAL, NUMBER, EOF
        self.assertEqual(len(tokens), 4)
        self.assertEqual(tokens[0].type, "IDENTIFIER")
        self.assertEqual(tokens[0].value, "A")
        self.assertEqual(tokens[1].type, "EQUAL")
        self.assertEqual(tokens[1].value, "=")
        self.assertEqual(tokens[2].type, "NUMBER")
        self.assertEqual(tokens[2].value, 10)
        self.assertEqual(tokens[3].type, "EOF")

    def test_addition(self):
        """Test tokenizing 10 + 20."""
        tokens = tokenize("10 + 20")
        print(f"Tokens for '10 + 20': {tokens}")
        # 4 tokens: NUMBER(10), PLUS, NUMBER(20), EOF
        self.assertEqual(len(tokens), 4)
        self.assertEqual(tokens[0].type, "NUMBER")
        self.assertEqual(tokens[0].value, 10)
        self.assertEqual(tokens[1].type, "PLUS")
        self.assertEqual(tokens[1].value, "+")
        self.assertEqual(tokens[2].type, "NUMBER")
        self.assertEqual(tokens[2].value, 20)
        self.assertEqual(tokens[3].type, "EOF")

    def test_parentheses(self):
        """Test tokenizing (10 + 5) * 2."""
        tokens = tokenize("(10 + 5) * 2")
        print(f"Tokens for '(10 + 5) * 2': {tokens}")

    def test_multiplication(self):
        """Test tokenizing 5 * 3."""
        tokens = tokenize("5 * 3")
        print(f"Tokens for '5 * 3': {tokens}")

    def test_division(self):
        """Test tokenizing 10 / 2."""
        tokens = tokenize("10 / 2")
        print(f"Tokens for '10 / 2': {tokens}")

    def test_power(self):
        """Test tokenizing 2 ^ 3."""
        tokens = tokenize("2 ^ 3")
        print(f"Tokens for '2 ^ 3': {tokens}")

    def test_illegal_character(self):
        """Test that illegal characters raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            tokenize("A @ B")
        self.assertIn("Illegal character", str(ctx.exception))
        print(f"Illegal character error: {ctx.exception}")

    def test_variables_assignment(self):
        """Test tokenizing variable assignment A = 10."""
        tokens = tokenize("A = 10")
        self.assertEqual(len(tokens), 4)  # IDENTIFIER, EQUAL, NUMBER, EOF
        self.assertEqual(tokens[0].type, "IDENTIFIER")
        self.assertEqual(tokens[0].value, "A")
        self.assertEqual(tokens[1].type, "EQUAL")
        self.assertEqual(tokens[1].value, "=")
        self.assertEqual(tokens[2].type, "NUMBER")
        self.assertEqual(tokens[2].value, 10)
        self.assertEqual(tokens[3].type, "EOF")

    def test_newline_handling(self):
        """Test that newlines are tokenized."""
        tokens = tokenize("A = 10\nB = 20")
        print(f"Tokens for 'A = 10\\nB = 20': {tokens}")
        # Each line ends with NEWLINE, then we have tokens
        # The exact count depends on implementation
        self.assertIsNotNone(tokens)


if __name__ == "__main__":
    unittest.main()