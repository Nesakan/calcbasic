"""Tests for CalcBASIC String Literals and Concatenation (Task #1 / Phase 3)."""
import io
import sys
import unittest

from calcbasic.lexer import tokenize, Token
from calcbasic.parser import Parser, StringNode, AssignmentNode, BinaryOpNode, PrintNode, ProgramNode
from calcbasic.interpreter import Interpreter


class TestStringLexer(unittest.TestCase):
    """Lexer tests for string literals."""

    def test_double_quoted_string(self):
        tokens = tokenize('"Hello, World!"')
        self.assertEqual(len(tokens), 2)  # STRING + EOF
        self.assertEqual(tokens[0].type, "STRING")
        self.assertEqual(tokens[0].value, "Hello, World!")
        self.assertEqual(tokens[0].line, 1)
        self.assertEqual(tokens[0].column, 1)

    def test_single_quoted_string(self):
        tokens = tokenize("'CalcBASIC'")
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, "STRING")
        self.assertEqual(tokens[0].value, "CalcBASIC")

    def test_empty_string(self):
        tokens = tokenize('""')
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, "STRING")
        self.assertEqual(tokens[0].value, "")

    def test_escape_sequences(self):
        tokens = tokenize(r'"Line1\nLine2\tTabbed\\Backslash\"Quote\'Single"')
        self.assertEqual(len(tokens), 2)
        expected = "Line1\nLine2\tTabbed\\Backslash\"Quote'Single"
        self.assertEqual(tokens[0].value, expected)

    def test_unterminated_string_eof(self):
        with self.assertRaises(ValueError) as ctx:
            tokenize('"Unterminated string without closing quote')
        self.assertIn("Unterminated string literal", str(ctx.exception))

    def test_unterminated_string_newline(self):
        with self.assertRaises(ValueError) as ctx:
            tokenize('"Unclosed line 1\nA = 10')
        self.assertIn("Unterminated string literal", str(ctx.exception))

    def test_string_position_tracking(self):
        tokens = tokenize('A = "Hello" + "World"')
        # IDENTIFIER(A), EQUAL(=), STRING("Hello"), PLUS(+), STRING("World"), EOF
        self.assertEqual(len(tokens), 6)
        self.assertEqual(tokens[2].column, 5)
        self.assertEqual(tokens[3].column, 13)
        self.assertEqual(tokens[4].column, 15)


class TestStringParser(unittest.TestCase):
    """Parser tests for StringNode."""

    def test_parse_string_literal(self):
        tokens = tokenize('"Basic"')
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, StringNode)
        self.assertEqual(ast.value, "Basic")

    def test_parse_string_assignment(self):
        tokens = tokenize('NAME = "Alice"')
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, AssignmentNode)
        self.assertEqual(ast.name.value, "NAME")
        self.assertIsInstance(ast.value, StringNode)
        self.assertEqual(ast.value.value, "Alice")

    def test_parse_string_concatenation(self):
        tokens = tokenize('"Hello " + "World"')
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "PLUS")
        self.assertIsInstance(ast.left, StringNode)
        self.assertIsInstance(ast.right, StringNode)
        self.assertEqual(ast.left.value, "Hello ")
        self.assertEqual(ast.right.value, "World")


class TestStringInterpreter(unittest.TestCase):
    """Interpreter tests for string evaluation and concatenation."""

    def setUp(self):
        self.interp = Interpreter()

    def test_string_variable_assignment(self):
        self.interp.interpret('MSG = "Hello CalcBASIC"')
        self.assertEqual(self.interp.variables["MSG"], "Hello CalcBASIC")

    def test_string_concatenation(self):
        self.interp.interpret('GREETING = "Hello" + " " + "World"')
        self.assertEqual(self.interp.variables["GREETING"], "Hello World")

    def test_variable_and_string_concatenation(self):
        self.interp.interpret('NAME = "Alice"')
        self.interp.interpret('MSG = "Hello, " + NAME + "!"')
        self.assertEqual(self.interp.variables["MSG"], "Hello, Alice!")

    def test_print_string(self):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.interp.interpret('PRINT "Hello Output"')
            output = sys.stdout.getvalue()
            self.assertEqual(output.strip(), "Hello Output")
        finally:
            sys.stdout = old_stdout

    def test_print_string_expression(self):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.interp.interpret('A = "Hello"')
            self.interp.interpret('B = "World"')
            self.interp.interpret('PRINT A + " " + B')
            output = sys.stdout.getvalue()
            self.assertEqual(output.strip(), "Hello World")
        finally:
            sys.stdout = old_stdout

    def test_type_mismatch_string_and_number(self):
        with self.assertRaises(TypeError) as ctx:
            self.interp.interpret('"Score: " + 100')
        self.assertIn("Type mismatch", str(ctx.exception))

    def test_type_mismatch_number_and_string(self):
        with self.assertRaises(TypeError) as ctx:
            self.interp.interpret('100 + "Score"')
        self.assertIn("Type mismatch", str(ctx.exception))

    def test_invalid_string_operators(self):
        for expr in ['"a" - "b"', '"a" * 2', '"a" / 2', '"a" ^ 2']:
            with self.assertRaises(TypeError) as ctx:
                self.interp.interpret(expr)
            self.assertIn("Type mismatch", str(ctx.exception))

    def test_multi_line_program(self):
        program = (
            'NAME = "Bob"\n'
            'GREETING = "Welcome, " + NAME\n'
            'AGE = 25\n'
            'PRINT GREETING\n'
            'PRINT AGE * 2'
        )
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.interp.interpret(program)
            output = sys.stdout.getvalue().strip().splitlines()
            self.assertEqual(output[0], "Welcome, Bob")
            self.assertIn("50", output[1])
        finally:
            sys.stdout = old_stdout

        self.assertEqual(self.interp.variables["NAME"], "Bob")
        self.assertEqual(self.interp.variables["GREETING"], "Welcome, Bob")
        self.assertEqual(self.interp.variables["AGE"], 25)


if __name__ == "__main__":
    unittest.main()
