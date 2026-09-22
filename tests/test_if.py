"""Unit tests for CalcBASIC IF...THEN...ELSE Statements (Phase 4)."""
import io
import sys
import unittest

from calcbasic.lexer import tokenize, Token
from calcbasic.parser import Parser, IfNode, AssignmentNode, PrintNode
from calcbasic.interpreter import Interpreter


class TestIfLexer(unittest.TestCase):
    """Test tokenization of IF, THEN, ELSE, ENDIF, and END IF."""

    def test_if_keywords(self):
        tokens = tokenize("IF THEN ELSE ENDIF END")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["IF", "THEN", "ELSE", "ENDIF", "END"])

    def test_case_insensitivity(self):
        tokens = tokenize("if then else endif end")
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["IF", "THEN", "ELSE", "ENDIF", "END"])


class TestIfParser(unittest.TestCase):
    """Test parser AST construction for single-line and block IF statements."""

    def test_single_line_if_then(self):
        tokens = tokenize("IF X > 0 THEN Y = 10")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, IfNode)
        self.assertEqual(len(ast.then_branch), 1)
        self.assertIsInstance(ast.then_branch[0], AssignmentNode)
        self.assertIsNone(ast.else_branch)

    def test_single_line_if_then_else(self):
        tokens = tokenize("IF X > 0 THEN Y = 10 ELSE Y = 20")
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, IfNode)
        self.assertEqual(len(ast.then_branch), 1)
        self.assertIsNotNone(ast.else_branch)
        self.assertEqual(len(ast.else_branch), 1)
        self.assertIsInstance(ast.else_branch[0], AssignmentNode)

    def test_block_if_end_if(self):
        source = (
            "IF X > 0 THEN\n"
            "    Y = 1\n"
            "    Z = 2\n"
            "END IF"
        )
        tokens = tokenize(source)
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, IfNode)
        self.assertEqual(len(ast.then_branch), 2)
        self.assertIsNone(ast.else_branch)

    def test_block_if_else_endif(self):
        source = (
            "IF X > 0 THEN\n"
            "    Y = 1\n"
            "ELSE\n"
            "    Y = 2\n"
            "ENDIF"
        )
        tokens = tokenize(source)
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast, IfNode)
        self.assertEqual(len(ast.then_branch), 1)
        self.assertIsNotNone(ast.else_branch)
        self.assertEqual(len(ast.else_branch), 1)

    def test_missing_then_error(self):
        tokens = tokenize("IF X > 0 Y = 10")
        with self.assertRaises(ValueError) as ctx:
            Parser(tokens).parse()
        self.assertIn("Expected THEN", str(ctx.exception))

    def test_unclosed_block_if_error(self):
        source = (
            "IF X > 0 THEN\n"
            "    Y = 1\n"
        )
        tokens = tokenize(source)
        with self.assertRaises(ValueError) as ctx:
            Parser(tokens).parse()
        self.assertIn("Expected END IF or ENDIF", str(ctx.exception))


class TestIfInterpreter(unittest.TestCase):
    """Test execution of single-line and block IF statements."""

    def setUp(self):
        self.interp = Interpreter()

    def test_single_line_if_true(self):
        self.interp.interpret("X = 5")
        self.interp.interpret("IF X > 0 THEN Y = 100")
        self.assertEqual(self.interp.variables["Y"], 100)

    def test_single_line_if_false(self):
        self.interp.interpret("X = -5")
        self.interp.interpret("Y = 0")
        self.interp.interpret("IF X > 0 THEN Y = 100")
        self.assertEqual(self.interp.variables["Y"], 0)

    def test_single_line_if_else_branching(self):
        self.interp.interpret("A = 10")
        self.interp.interpret("IF A > 5 THEN RES1 = 1 ELSE RES1 = 0")
        self.assertEqual(self.interp.variables["RES1"], 1)

        self.interp.interpret("IF A < 5 THEN RES2 = 1 ELSE RES2 = 0")
        self.assertEqual(self.interp.variables["RES2"], 0)

    def test_single_line_if_print(self):
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.interp.interpret('IF 1 > 0 THEN PRINT "TrueBranch" ELSE PRINT "FalseBranch"')
            self.interp.interpret('IF 1 < 0 THEN PRINT "TrueBranch" ELSE PRINT "FalseBranch"')
            output = sys.stdout.getvalue().strip().splitlines()
            self.assertEqual(output, ["TrueBranch", "FalseBranch"])
        finally:
            sys.stdout = old_stdout

    def test_block_if_then_only(self):
        source = (
            "SCORE = 85\n"
            "PASSED = 0\n"
            "IF SCORE >= 50 THEN\n"
            "    PASSED = 1\n"
            "    STATUS = \"OK\"\n"
            "END IF"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["PASSED"], 1)
        self.assertEqual(self.interp.variables["STATUS"], "OK")

    def test_block_if_else_executed(self):
        source = (
            "SCORE = 40\n"
            "IF SCORE >= 50 THEN\n"
            "    STATUS = \"PASS\"\n"
            "ELSE\n"
            "    STATUS = \"FAIL\"\n"
            "END IF"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["STATUS"], "FAIL")

    def test_block_if_with_endif_spelling(self):
        source = (
            "X = 7\n"
            "IF X = 7 THEN\n"
            "    MSG = \"Lucky\"\n"
            "ENDIF"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["MSG"], "Lucky")

    def test_nested_block_if(self):
        source = (
            "A = 10\n"
            "B = 20\n"
            "IF A > 0 THEN\n"
            "    IF B > 0 THEN\n"
            "        RESULT = \"Both Positive\"\n"
            "    ELSE\n"
            "        RESULT = \"Only A Positive\"\n"
            "    END IF\n"
            "ELSE\n"
            "    RESULT = \"A Non-Positive\"\n"
            "END IF"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["RESULT"], "Both Positive")

    def test_complex_boolean_condition_in_if(self):
        source = (
            "AGE = 20\n"
            "HAS_ID = 1\n"
            "IF AGE >= 18 AND HAS_ID = 1 THEN\n"
            "    ENTRY = \"Allowed\"\n"
            "ELSE\n"
            "    ENTRY = \"Denied\"\n"
            "END IF"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["ENTRY"], "Allowed")

    def test_string_condition_in_if(self):
        source = (
            "USER = \"admin\"\n"
            "IF USER = \"admin\" THEN\n"
            "    ROLE = 1\n"
            "ELSE\n"
            "    ROLE = 0\n"
            "END IF"
        )
        self.interp.interpret(source)
        self.assertEqual(self.interp.variables["ROLE"], 1)


if __name__ == "__main__":
    unittest.main()
