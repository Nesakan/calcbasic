"""Unit tests for CalcBASIC Boolean Operators (AND, OR, NOT) - Phase 3."""
import io
import sys
import unittest

from calcbasic.lexer import tokenize, Token
from calcbasic.parser import Parser, BinaryOpNode, UnaryOpNode, NumberNode, VariableNode, AssignmentNode
from calcbasic.interpreter import Interpreter


class TestBooleanLexer(unittest.TestCase):
    """Test tokenization of boolean operators."""

    def test_boolean_keywords(self):
        tokens = tokenize("AND OR NOT")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["AND", "OR", "NOT"])

    def test_case_insensitivity(self):
        tokens = tokenize("and Or nOt")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["AND", "OR", "NOT"])

    def test_boolean_in_expression_tokens(self):
        tokens = tokenize("A > 5 AND NOT B = 10 OR C")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, [
            "IDENTIFIER", "GREATER", "NUMBER",
            "AND",
            "NOT",
            "IDENTIFIER", "EQUAL", "NUMBER",
            "OR",
            "IDENTIFIER",
        ])


class TestBooleanParser(unittest.TestCase):
    """Test parsing and AST precedence for boolean operators."""

    def test_and_node(self):
        tokens = tokenize("1 AND 1")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "AND")

    def test_or_node(self):
        tokens = tokenize("1 OR 0")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "OR")

    def test_not_node(self):
        tokens = tokenize("NOT 0")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, UnaryOpNode)
        self.assertEqual(ast.operator.type, "NOT")
        self.assertIsInstance(ast.operand, NumberNode)
        self.assertEqual(ast.operand.value, 0)

    def test_precedence_and_over_or(self):
        # A OR B AND C should parse as A OR (B AND C)
        tokens = tokenize("A OR B AND C")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "OR")
        self.assertIsInstance(ast.left, VariableNode)
        self.assertIsInstance(ast.right, BinaryOpNode)
        self.assertEqual(ast.right.operator.type, "AND")

    def test_precedence_not_over_and(self):
        # NOT A AND B should parse as (NOT A) AND B
        tokens = tokenize("NOT A AND B")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "AND")
        self.assertIsInstance(ast.left, UnaryOpNode)
        self.assertEqual(ast.left.operator.type, "NOT")
        self.assertIsInstance(ast.right, VariableNode)

    def test_precedence_comparison_over_boolean(self):
        # A > 5 AND B < 10 should parse as (A > 5) AND (B < 10)
        tokens = tokenize("A > 5 AND B < 10")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "AND")
        self.assertIsInstance(ast.left, BinaryOpNode)
        self.assertEqual(ast.left.operator.type, "GREATER")
        self.assertIsInstance(ast.right, BinaryOpNode)
        self.assertEqual(ast.right.operator.type, "LESS")

    def test_not_comparison(self):
        # NOT A = 5 should parse as NOT (A = 5)
        tokens = tokenize("NOT A = 5")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, UnaryOpNode)
        self.assertEqual(ast.operator.type, "NOT")
        self.assertIsInstance(ast.operand, BinaryOpNode)
        self.assertEqual(ast.operand.operator.type, "EQUAL")

    def test_parenthesized_override(self):
        # (A OR B) AND C should parse as (A OR B) AND C
        tokens = tokenize("(A OR B) AND C")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "AND")
        self.assertIsInstance(ast.left, BinaryOpNode)
        self.assertEqual(ast.left.operator.type, "OR")


class TestBooleanInterpreter(unittest.TestCase):
    """Test evaluation of boolean expressions."""

    def setUp(self):
        self.interp = Interpreter()

    def test_and_truth_table(self):
        self.assertEqual(self.interp.interpret("1 AND 1"), 1)
        self.assertEqual(self.interp.interpret("1 AND 0"), 0)
        self.assertEqual(self.interp.interpret("0 AND 1"), 0)
        self.assertEqual(self.interp.interpret("0 AND 0"), 0)

    def test_or_truth_table(self):
        self.assertEqual(self.interp.interpret("1 OR 1"), 1)
        self.assertEqual(self.interp.interpret("1 OR 0"), 1)
        self.assertEqual(self.interp.interpret("0 OR 1"), 1)
        self.assertEqual(self.interp.interpret("0 OR 0"), 0)

    def test_not_truth_table(self):
        self.assertEqual(self.interp.interpret("NOT 0"), 1)
        self.assertEqual(self.interp.interpret("NOT 1"), 0)
        self.assertEqual(self.interp.interpret("NOT NOT 1"), 1)
        self.assertEqual(self.interp.interpret("NOT 42"), 0)

    def test_compound_logical_expressions(self):
        self.assertEqual(self.interp.interpret("10 > 5 AND 3 < 4"), 1)
        self.assertEqual(self.interp.interpret("10 > 5 AND 3 > 4"), 0)
        self.assertEqual(self.interp.interpret("10 < 5 OR 3 < 4"), 1)
        self.assertEqual(self.interp.interpret("10 < 5 OR 3 > 4"), 0)
        self.assertEqual(self.interp.interpret("NOT 10 > 5"), 0)
        self.assertEqual(self.interp.interpret("NOT 10 < 5"), 1)

    def test_arithmetic_comparison_boolean_precedence(self):
        # 2 + 3 > 4 AND 10 = 2 * 5  =>  5 > 4 AND 10 = 10  =>  1 AND 1 => 1
        self.assertEqual(self.interp.interpret("2 + 3 > 4 AND 10 = 2 * 5"), 1)
        # 0 OR 1 AND 0 => 0 OR (1 AND 0) => 0 OR 0 => 0
        self.assertEqual(self.interp.interpret("0 OR 1 AND 0"), 0)
        # (0 OR 1) AND 1 => 1 AND 1 => 1
        self.assertEqual(self.interp.interpret("(0 OR 1) AND 1"), 1)

    def test_variable_boolean_assignment(self):
        self.interp.interpret("AGE = 25")
        self.interp.interpret("HAS_TICKET = 1")
        self.interp.interpret("CAN_ENTER = AGE >= 18 AND HAS_TICKET = 1")
        self.assertEqual(self.interp.variables["CAN_ENTER"], 1)

        self.interp.interpret("HAS_TICKET = 0")
        self.interp.interpret("CAN_ENTER = AGE >= 18 AND HAS_TICKET = 1")
        self.assertEqual(self.interp.variables["CAN_ENTER"], 0)

    def test_string_comparison_in_boolean(self):
        self.interp.interpret('ROLE = "admin"')
        self.interp.interpret('LEVEL = 5')
        self.interp.interpret('IS_SUPER = ROLE = "admin" AND LEVEL >= 5')
        self.assertEqual(self.interp.variables["IS_SUPER"], 1)

    def test_type_error_string_in_boolean(self):
        with self.assertRaises(TypeError) as ctx:
            self.interp.interpret('"hello" AND 1')
        self.assertIn("Type mismatch", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:
            self.interp.interpret('1 OR "world"')
        self.assertIn("Type mismatch", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:
            self.interp.interpret('NOT "test"')
        self.assertIn("Type mismatch", str(ctx.exception))

    def test_print_boolean(self):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.interp.interpret("PRINT 1 AND 1")
            self.interp.interpret("PRINT 0 OR 1")
            self.interp.interpret("PRINT NOT 0")
            output = sys.stdout.getvalue().strip().splitlines()
            self.assertEqual(output, ["1", "1", "1"])
        finally:
            sys.stdout = old_stdout


if __name__ == "__main__":
    unittest.main()
