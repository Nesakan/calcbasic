# CalcBASIC Math Function Tests - Phase 6
import math
import unittest
from calcbasic.interpreter import Interpreter
from calcbasic.lexer import tokenize
from calcbasic.parser import Parser, FunctionCallNode


class TestMathFunctions(unittest.TestCase):
    """Test suite for CalcBASIC built-in mathematical functions."""

    def setUp(self):
        self.interp = Interpreter()

    def eval_expr(self, expr: str):
        return self.interp.interpret(expr)

    # ---------------------------------------------------------------------------
    # Lexer & Parser Tests for Functions
    # ---------------------------------------------------------------------------

    def test_lexer_comma_token(self):
        tokens = tokenize("ROUND(3.14159, 2)")
        token_types = [t.type for t in tokens]
        self.assertEqual(token_types, ["IDENTIFIER", "LEFT_PAREN", "NUMBER", "COMMA", "NUMBER", "RIGHT_PAREN", "EOF"])

    def test_parser_function_call_node(self):
        tokens = tokenize("SQRT(16)")
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast, FunctionCallNode)
        self.assertEqual(ast.name.value, "SQRT")
        self.assertEqual(len(ast.args), 1)

    def test_parser_nested_function_call(self):
        tokens = tokenize("SQRT(ABS(-16))")
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast, FunctionCallNode)
        self.assertEqual(ast.name.value, "SQRT")
        self.assertIsInstance(ast.args[0], FunctionCallNode)
        self.assertEqual(ast.args[0].name.value, "ABS")

    # ---------------------------------------------------------------------------
    # Basic Arithmetic & Numeric Functions
    # ---------------------------------------------------------------------------

    def test_abs(self):
        self.assertEqual(self.eval_expr("ABS(10)"), 10)
        self.assertEqual(self.eval_expr("ABS(-10)"), 10)
        self.assertEqual(self.eval_expr("ABS(0)"), 0)
        self.assertAlmostEqual(self.eval_expr("ABS(-3.14)"), 3.14)

    def test_sqrt_and_sqr(self):
        self.assertAlmostEqual(self.eval_expr("SQRT(16)"), 4.0)
        self.assertAlmostEqual(self.eval_expr("SQR(25)"), 5.0)
        self.assertAlmostEqual(self.eval_expr("SQRT(0)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("SQRT(2)"), math.sqrt(2))

    def test_sgn(self):
        self.assertEqual(self.eval_expr("SGN(42)"), 1)
        self.assertEqual(self.eval_expr("SGN(-99)"), -1)
        self.assertEqual(self.eval_expr("SGN(0)"), 0)

    def test_int_fix_floor_ceil(self):
        # INT: classic BASIC floor behavior (greatest integer <= x)
        self.assertEqual(self.eval_expr("INT(3.7)"), 3)
        self.assertEqual(self.eval_expr("INT(-3.7)"), -4)
        self.assertEqual(self.eval_expr("INT(5)"), 5)

        # FIX: truncates fractional part towards zero
        self.assertEqual(self.eval_expr("FIX(3.7)"), 3)
        self.assertEqual(self.eval_expr("FIX(-3.7)"), -3)

        # FLOOR & CEIL
        self.assertEqual(self.eval_expr("FLOOR(3.7)"), 3)
        self.assertEqual(self.eval_expr("FLOOR(-3.7)"), -4)
        self.assertEqual(self.eval_expr("CEIL(3.2)"), 4)
        self.assertEqual(self.eval_expr("CEIL(-3.7)"), -3)

    def test_round(self):
        self.assertEqual(self.eval_expr("ROUND(3.7)"), 4)
        self.assertEqual(self.eval_expr("ROUND(3.2)"), 3)
        self.assertAlmostEqual(self.eval_expr("ROUND(3.14159, 2)"), 3.14)
        self.assertAlmostEqual(self.eval_expr("ROUND(3.14159, 4)"), 3.1416)

    # ---------------------------------------------------------------------------
    # Exponential & Logarithmic Functions
    # ---------------------------------------------------------------------------

    def test_exp(self):
        self.assertAlmostEqual(self.eval_expr("EXP(0)"), 1.0)
        self.assertAlmostEqual(self.eval_expr("EXP(1)"), math.e)

    def test_log_and_ln(self):
        self.assertAlmostEqual(self.eval_expr("LOG(1)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("LN(1)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("LOG(E)"), 1.0)
        self.assertAlmostEqual(self.eval_expr("LN(E)"), 1.0)
        self.assertAlmostEqual(self.eval_expr("LOG10(1)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("LOG10(100)"), 2.0)
        self.assertAlmostEqual(self.eval_expr("LOG10(1000)"), 3.0)

    # ---------------------------------------------------------------------------
    # Trigonometric Functions & Angle Conversions
    # ---------------------------------------------------------------------------

    def test_trigonometry(self):
        self.assertAlmostEqual(self.eval_expr("SIN(0)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("COS(0)"), 1.0)
        self.assertAlmostEqual(self.eval_expr("TAN(0)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("SIN(PI / 2)"), 1.0)
        self.assertAlmostEqual(self.eval_expr("COS(PI)"), -1.0)

    def test_inverse_trig(self):
        self.assertAlmostEqual(self.eval_expr("ASIN(0)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("ASIN(1)"), math.pi / 2)
        self.assertAlmostEqual(self.eval_expr("ACOS(1)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("ACOS(0)"), math.pi / 2)
        self.assertAlmostEqual(self.eval_expr("ATAN(0)"), 0.0)
        self.assertAlmostEqual(self.eval_expr("ATAN(1)"), math.pi / 4)
        self.assertAlmostEqual(self.eval_expr("ATAN2(1, 1)"), math.pi / 4)
        self.assertAlmostEqual(self.eval_expr("ATAN2(0, -1)"), math.pi)

    def test_deg_and_rad(self):
        self.assertAlmostEqual(self.eval_expr("RAD(180)"), math.pi)
        self.assertAlmostEqual(self.eval_expr("DEG(PI)"), 180.0)
        self.assertAlmostEqual(self.eval_expr("SIN(RAD(90))"), 1.0)

    # ---------------------------------------------------------------------------
    # Min, Max, and Multi-arg Functions
    # ---------------------------------------------------------------------------

    def test_min_max(self):
        self.assertEqual(self.eval_expr("MIN(5, 2, 9, 1, 7)"), 1)
        self.assertEqual(self.eval_expr("MAX(5, 2, 9, 1, 7)"), 9)
        self.assertEqual(self.eval_expr("MIN(42)"), 42)
        self.assertEqual(self.eval_expr("MAX(-5, -10, -2)"), -2)

    # ---------------------------------------------------------------------------
    # Random & Constants
    # ---------------------------------------------------------------------------

    def test_rnd(self):
        # RND() returns [0, 1)
        val = self.eval_expr("RND()")
        self.assertTrue(0.0 <= val < 1.0)

        # RND(n) with n > 1 returns integer in 1..n
        int_val = self.eval_expr("RND(10)")
        self.assertTrue(isinstance(int_val, int))
        self.assertTrue(1 <= int_val <= 10)

    def test_constants_as_variables_and_functions(self):
        self.assertAlmostEqual(self.eval_expr("PI"), math.pi)
        self.assertAlmostEqual(self.eval_expr("PI()"), math.pi)
        self.assertAlmostEqual(self.eval_expr("E"), math.e)
        self.assertAlmostEqual(self.eval_expr("E()"), math.e)

    # ---------------------------------------------------------------------------
    # Case Insensitivity
    # ---------------------------------------------------------------------------

    def test_case_insensitivity(self):
        self.assertEqual(self.eval_expr("abs(-5)"), 5)
        self.assertEqual(self.eval_expr("Abs(-5)"), 5)
        self.assertAlmostEqual(self.eval_expr("sqrt(25)"), 5.0)
        self.assertAlmostEqual(self.eval_expr("Sqrt(25)"), 5.0)
        self.assertAlmostEqual(self.eval_expr("sin(0)"), 0.0)

    # ---------------------------------------------------------------------------
    # Precedence, Expressions & Complex Usage
    # ---------------------------------------------------------------------------

    def test_pythagorean_identity(self):
        result = self.eval_expr("SIN(1.23) ^ 2 + COS(1.23) ^ 2")
        self.assertAlmostEqual(result, 1.0)

    def test_nested_function_evaluation(self):
        self.assertAlmostEqual(self.eval_expr("SQRT(ABS(-16))"), 4.0)
        self.assertAlmostEqual(self.eval_expr("ROUND(SQRT(2), 3)"), 1.414)

    def test_function_in_program_with_variables(self):
        code = """
X = 9
Y = SQRT(X)
Z = Y * 2 + ABS(-4)
"""
        self.interp.interpret(code)
        self.assertEqual(self.interp.variables["X"], 9)
        self.assertEqual(self.interp.variables["Y"], 3.0)
        self.assertEqual(self.interp.variables["Z"], 10.0)

    def test_function_in_condition_and_loop(self):
        code = """
FOUND = 0
FOR I = 1 TO 5
    IF SQRT(I * I) = 3 THEN
        FOUND = I
    END IF
NEXT I
"""
        self.interp.interpret(code)
        self.assertEqual(self.interp.variables["FOUND"], 3)

    # ---------------------------------------------------------------------------
    # Error Handling & Edge Cases
    # ---------------------------------------------------------------------------

    def test_undefined_function(self):
        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("NONEXISTENT(10)")
        self.assertIn("Undefined function 'NONEXISTENT'", str(ctx.exception))

    def test_argument_count_errors(self):
        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("ABS(1, 2)")
        self.assertIn("Function ABS expects 1 argument, got 2", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("PI(1)")
        self.assertIn("Function PI expects 0 arguments, got 1", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("ATAN2(1)")
        self.assertIn("Function ATAN2 expects 2 arguments, got 1", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("ROUND(1, 2, 3)")
        self.assertIn("Function ROUND expects 1 or 2 arguments, got 3", str(ctx.exception))

    def test_type_mismatch_error(self):
        with self.assertRaises(TypeError) as ctx:
            self.eval_expr('SIN("hello")')
        self.assertIn("Type mismatch: function SIN argument 1 must be a number, got str", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:
            self.eval_expr('ROUND(3.14, "two")')
        self.assertIn("Type mismatch: function ROUND argument 2 must be a number, got str", str(ctx.exception))

    def test_domain_errors(self):
        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("SQRT(-1)")
        self.assertIn("Math domain error in SQRT", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("SQR(-4)")
        self.assertIn("Math domain error in SQR", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("LOG(0)")
        self.assertIn("Math domain error in LOG", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("LN(-10)")
        self.assertIn("Math domain error in LN", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("LOG10(0)")
        self.assertIn("Math domain error in LOG10", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("ASIN(2)")
        self.assertIn("Math domain error in ASIN", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.eval_expr("ACOS(-1.5)")
        self.assertIn("Math domain error in ACOS", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
