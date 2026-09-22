"""Unit tests for CalcBASIC FOR...TO...NEXT Loops (Phase 5)."""
import io
import sys
import unittest

from calcbasic.lexer import tokenize, Token
from calcbasic.parser import Parser, ForNode, AssignmentNode, PrintNode
from calcbasic.interpreter import Interpreter


class TestForLexer(unittest.TestCase):
    """Test tokenization of FOR, TO, STEP, NEXT."""

    def test_for_keywords(self):
        tokens = tokenize("FOR TO STEP NEXT")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["FOR", "TO", "STEP", "NEXT"])

    def test_case_insensitivity(self):
        tokens = tokenize("for to step next")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["FOR", "TO", "STEP", "NEXT"])


class TestForParser(unittest.TestCase):
    """Test parser AST construction for FOR loops."""

    def test_basic_for_ast(self):
        source = (
            "FOR I = 1 TO 5\n"
            "    PRINT I\n"
            "NEXT I"
        )
        tokens = tokenize(source)
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, ForNode)
        self.assertEqual(ast.target.value, "I")
        self.assertIsNone(ast.step_expr)
        self.assertEqual(len(ast.body), 1)
        self.assertIsInstance(ast.body[0], PrintNode)
        self.assertEqual(ast.next_target.value, "I")

    def test_anonymous_next_ast(self):
        source = (
            "FOR I = 1 TO 5\n"
            "    X = I * 2\n"
            "NEXT"
        )
        tokens = tokenize(source)
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, ForNode)
        self.assertIsNone(ast.next_target)

    def test_for_with_step_ast(self):
        source = (
            "FOR I = 10 TO 0 STEP -1\n"
            "    PRINT I\n"
            "NEXT I"
        )
        tokens = tokenize(source)
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, ForNode)
        self.assertIsNotNone(ast.step_expr)

    def test_mismatched_next_variable_error(self):
        source = (
            "FOR I = 1 TO 5\n"
            "    PRINT I\n"
            "NEXT J"
        )
        tokens = tokenize(source)
        with self.assertRaises(ValueError) as ctx:
            Parser(tokens).parse()
        self.assertIn("does not match FOR variable", str(ctx.exception))

    def test_missing_next_error(self):
        source = (
            "FOR I = 1 TO 5\n"
            "    PRINT I\n"
        )
        tokens = tokenize(source)
        with self.assertRaises(ValueError) as ctx:
            Parser(tokens).parse()
        self.assertIn("Expected NEXT", str(ctx.exception))


class TestForInterpreter(unittest.TestCase):
    """Test evaluation and execution of FOR loops."""

    def setUp(self):
        self.interp = Interpreter()

    def test_basic_sum_loop(self):
        source = (
            "SUM = 0\n"
            "FOR I = 1 TO 5\n"
            "    SUM = SUM + I\n"
            "NEXT I"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["SUM"], 15)
        # In classic BASIC, post-loop variable is incremented past end_val
        self.assertEqual(self.interp.variables["I"], 6)

    def test_anonymous_next(self):
        source = (
            "COUNT = 0\n"
            "FOR K = 1 TO 3\n"
            "    COUNT = COUNT + 1\n"
            "NEXT"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["COUNT"], 3)
        self.assertEqual(self.interp.variables["K"], 4)

    def test_positive_step(self):
        source = (
            "SUM = 0\n"
            "FOR I = 0 TO 10 STEP 2\n"
            "    SUM = SUM + I\n"
            "NEXT I"
        )
        self.interp.interpret(source)
        # 0 + 2 + 4 + 6 + 8 + 10 = 30
        self.assertEqual(self.interp.variables["SUM"], 30)
        self.assertEqual(self.interp.variables["I"], 12)

    def test_negative_step(self):
        source = (
            "SUM = 0\n"
            "FOR I = 10 TO 2 STEP -2\n"
            "    SUM = SUM + I\n"
            "NEXT I"
        )
        self.interp.interpret(source)
        # 10 + 8 + 6 + 4 + 2 = 30
        self.assertEqual(self.interp.variables["SUM"], 30)
        self.assertEqual(self.interp.variables["I"], 0)

    def test_fractional_step(self):
        source = (
            "COUNT = 0\n"
            "FOR X = 0 TO 1 STEP 0.25\n"
            "    COUNT = COUNT + 1\n"
            "NEXT X"
        )
        self.interp.interpret(source)
        # 0, 0.25, 0.5, 0.75, 1.0 => 5 iterations
        self.assertEqual(self.interp.variables["COUNT"], 5)
        self.assertAlmostEqual(self.interp.variables["X"], 1.25)

    def test_zero_iterations(self):
        source = (
            "RUN = 0\n"
            "FOR I = 10 TO 1\n"
            "    RUN = 1\n"
            "NEXT I"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["RUN"], 0)
        self.assertEqual(self.interp.variables["I"], 10)

    def test_nested_loops(self):
        source = (
            "PROD_SUM = 0\n"
            "FOR I = 1 TO 3\n"
            "    FOR J = 1 TO 2\n"
            "        PROD_SUM = PROD_SUM + I * J\n"
            "    NEXT J\n"
            "NEXT I"
        )
        self.interp.interpret(source)
        # I=1: 1*1 + 1*2 = 3
        # I=2: 2*1 + 2*2 = 6
        # I=3: 3*1 + 3*2 = 9
        # Total = 18
        self.assertEqual(self.interp.variables["PROD_SUM"], 18)
        self.assertEqual(self.interp.variables["I"], 4)
        self.assertEqual(self.interp.variables["J"], 3)

    def test_print_inside_loop(self):
        source = (
            "FOR I = 1 TO 3\n"
            "    PRINT I * 10\n"
            "NEXT I"
        )
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.interp.interpret(source)
            output = sys.stdout.getvalue().strip().splitlines()
            self.assertEqual(output, ["10", "20", "30"])
        finally:
            sys.stdout = old_stdout

    def test_step_zero_error(self):
        source = (
            "FOR I = 1 TO 5 STEP 0\n"
            "    PRINT I\n"
            "NEXT I"
        )
        with self.assertRaises(ValueError) as ctx:
            self.interp.interpret(source)
        self.assertIn("STEP cannot be zero", str(ctx.exception))

    def test_type_error_on_string_bounds(self):
        source = (
            "FOR I = \"start\" TO 10\n"
            "    PRINT I\n"
            "NEXT I"
        )
        with self.assertRaises(TypeError) as ctx:
            self.interp.interpret(source)
        self.assertIn("Type mismatch", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
