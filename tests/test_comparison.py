"""Unit tests for CalcBASIC Comparison Operators (Phase 2)."""
import io
import sys
import unittest

from calcbasic.lexer import tokenize, Token
from calcbasic.parser import Parser, BinaryOpNode, NumberNode, VariableNode, StringNode, AssignmentNode
from calcbasic.interpreter import Interpreter


class TestComparisonLexer(unittest.TestCase):
    """Test tokenization of comparison operators."""

    def test_single_char_comparisons(self):
        tokens = tokenize("< > =")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["LESS", "GREATER", "EQUAL"])
        self.assertEqual(tokens[0].value, "<")
        self.assertEqual(tokens[1].value, ">")
        self.assertEqual(tokens[2].value, "=")

    def test_two_char_comparisons(self):
        tokens = tokenize("<= >= <> == !=")
        types = [t.type for t in tokens if t.type != "EOF"]
        values = [t.value for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["LESS_EQUAL", "GREATER_EQUAL", "NOT_EQUAL", "EQUAL", "NOT_EQUAL"])
        self.assertEqual(values, ["<=", ">=", "<>", "==", "!="])

    def test_comparison_in_expression_tokens(self):
        tokens = tokenize("A + 1 <= B * 2")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, [
            "IDENTIFIER", "PLUS", "NUMBER",
            "LESS_EQUAL",
            "IDENTIFIER", "STAR", "NUMBER"
        ])


class TestComparisonParser(unittest.TestCase):
    """Test parsing and AST hierarchy of comparison expressions."""

    def test_basic_comparison_ast(self):
        tokens = tokenize("10 > 5")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "GREATER")
        self.assertIsInstance(ast.left, NumberNode)
        self.assertIsInstance(ast.right, NumberNode)
        self.assertEqual(ast.left.value, 10)
        self.assertEqual(ast.right.value, 5)

    def test_precedence_arithmetic_over_comparison(self):
        # A + 2 > B * 3 should parse as (A + 2) > (B * 3)
        tokens = tokenize("A + 2 > B * 3")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "GREATER")
        # Left operand must be BinaryOpNode(PLUS)
        self.assertIsInstance(ast.left, BinaryOpNode)
        self.assertEqual(ast.left.operator.type, "PLUS")
        # Right operand must be BinaryOpNode(STAR)
        self.assertIsInstance(ast.right, BinaryOpNode)
        self.assertEqual(ast.right.operator.type, "STAR")

    def test_parentheses_in_comparison(self):
        tokens = tokenize("(X + 1) <= (Y - 1)")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, BinaryOpNode)
        self.assertEqual(ast.operator.type, "LESS_EQUAL")

    def test_assignment_with_comparison(self):
        # RES = A = B should parse as Assignment(name="RES", value=BinaryOpNode(A, EQUAL, B))
        tokens = tokenize("RES = A = B")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, AssignmentNode)
        self.assertEqual(ast.name.value, "RES")
        self.assertIsInstance(ast.value, BinaryOpNode)
        self.assertEqual(ast.value.operator.type, "EQUAL")


class TestComparisonInterpreter(unittest.TestCase):
    """Test evaluation of comparison expressions."""

    def setUp(self):
        self.interp = Interpreter()

    def test_equality(self):
        self.assertEqual(self.interp.interpret("5 = 5"), 1)
        self.assertEqual(self.interp.interpret("5 = 6"), 0)
        self.assertEqual(self.interp.interpret("5 == 5"), 1)
        self.assertEqual(self.interp.interpret("5 == 6"), 0)

    def test_inequality(self):
        self.assertEqual(self.interp.interpret("5 <> 6"), 1)
        self.assertEqual(self.interp.interpret("5 <> 5"), 0)
        self.assertEqual(self.interp.interpret("5 != 6"), 1)
        self.assertEqual(self.interp.interpret("5 != 5"), 0)

    def test_less_than(self):
        self.assertEqual(self.interp.interpret("3 < 5"), 1)
        self.assertEqual(self.interp.interpret("5 < 3"), 0)
        self.assertEqual(self.interp.interpret("5 < 5"), 0)

    def test_greater_than(self):
        self.assertEqual(self.interp.interpret("5 > 3"), 1)
        self.assertEqual(self.interp.interpret("3 > 5"), 0)
        self.assertEqual(self.interp.interpret("5 > 5"), 0)

    def test_less_equal(self):
        self.assertEqual(self.interp.interpret("3 <= 5"), 1)
        self.assertEqual(self.interp.interpret("5 <= 5"), 1)
        self.assertEqual(self.interp.interpret("6 <= 5"), 0)

    def test_greater_equal(self):
        self.assertEqual(self.interp.interpret("6 >= 5"), 1)
        self.assertEqual(self.interp.interpret("5 >= 5"), 1)
        self.assertEqual(self.interp.interpret("3 >= 5"), 0)

    def test_string_comparisons(self):
        self.assertEqual(self.interp.interpret('"apple" = "apple"'), 1)
        self.assertEqual(self.interp.interpret('"apple" <> "banana"'), 1)
        self.assertEqual(self.interp.interpret('"apple" < "banana"'), 1)
        self.assertEqual(self.interp.interpret('"banana" > "apple"'), 1)
        self.assertEqual(self.interp.interpret('"cat" <= "dog"'), 1)
        self.assertEqual(self.interp.interpret('"dog" >= "dog"'), 1)

    def test_type_mismatch_comparison(self):
        with self.assertRaises(TypeError) as ctx:
            self.interp.interpret('"10" > 5')
        self.assertIn("Type mismatch", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:
            self.interp.interpret('5 = "5"')
        self.assertIn("Type mismatch", str(ctx.exception))

    def test_precedence_evaluation(self):
        # 2 + 3 > 4  =>  5 > 4 => 1
        self.assertEqual(self.interp.interpret("2 + 3 > 4"), 1)
        # 10 > 2 * 6 =>  10 > 12 => 0
        self.assertEqual(self.interp.interpret("10 > 2 * 6"), 0)
        # 5 + 5 = 2 * 5 => 10 = 10 => 1
        self.assertEqual(self.interp.interpret("5 + 5 = 2 * 5"), 1)

    def test_variable_comparison(self):
        self.interp.interpret("A = 10")
        self.interp.interpret("B = 20")
        self.interp.interpret("IS_LESS = A < B")
        self.assertEqual(self.interp.variables["IS_LESS"], 1)

        self.interp.interpret("IS_GREATER = A > B")
        self.assertEqual(self.interp.variables["IS_GREATER"], 0)

    def test_print_comparison(self):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.interp.interpret("PRINT 10 > 5")
            self.interp.interpret("PRINT 10 < 5")
            output = sys.stdout.getvalue().strip().splitlines()
            self.assertEqual(output, ["1", "0"])
        finally:
            sys.stdout = old_stdout


if __name__ == "__main__":
    unittest.main()
