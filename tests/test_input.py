# CalcBASIC Input Statement Tests - Phase 7
import unittest
from calcbasic.interpreter import Interpreter, interpret
from calcbasic.lexer import tokenize
from calcbasic.parser import Parser, InputNode


class TestInputStatement(unittest.TestCase):
    """Test suite for CalcBASIC INPUT statement."""

    # ---------------------------------------------------------------------------
    # Lexer & Parser Tests for INPUT
    # ---------------------------------------------------------------------------

    def test_lexer_input_and_semicolon(self):
        tokens = tokenize('INPUT "Name: "; NAME$')
        types = [t.type for t in tokens]
        self.assertEqual(types, ["INPUT", "STRING", "SEMICOLON", "IDENTIFIER", "EOF"])
        self.assertEqual(tokens[3].value, "NAME$")

    def test_lexer_input_with_comma(self):
        tokens = tokenize('INPUT "Age: ", AGE')
        types = [t.type for t in tokens]
        self.assertEqual(types, ["INPUT", "STRING", "COMMA", "IDENTIFIER", "EOF"])

    def test_parser_input_default_prompt(self):
        tokens = tokenize("INPUT X")
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast, InputNode)
        self.assertIsNone(ast.prompt)
        self.assertEqual(len(ast.targets), 1)
        self.assertEqual(ast.targets[0].value, "X")

    def test_parser_input_with_prompt_and_targets(self):
        tokens = tokenize('INPUT "Enter coordinates: ", X, Y')
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertIsInstance(ast, InputNode)
        self.assertIsNotNone(ast.prompt)
        self.assertEqual(ast.prompt.value, "Enter coordinates: ")
        self.assertEqual([t.value for t in ast.targets], ["X", "Y"])

    def test_parser_input_missing_delimiter_syntax_error(self):
        tokens = tokenize('INPUT "Enter" X')
        parser = Parser(tokens)
        with self.assertRaises(ValueError) as ctx:
            parser.parse()
        self.assertIn("Expected ',' or ';' after INPUT prompt", str(ctx.exception))

    # ---------------------------------------------------------------------------
    # Interpreter Tests for INPUT
    # ---------------------------------------------------------------------------

    def test_input_default_prompt_and_integer(self):
        prompts = []

        def mock_input(prompt):
            prompts.append(prompt)
            return "42"

        interp = Interpreter(input_func=mock_input)
        interp.interpret("INPUT X")
        self.assertEqual(prompts, ["? "])
        self.assertEqual(interp.variables["X"], 42)
        self.assertIsInstance(interp.variables["X"], int)

    def test_input_custom_prompt_comma_and_float(self):
        prompts = []

        def mock_input(prompt):
            prompts.append(prompt)
            return "3.14159"

        interp = Interpreter(input_func=mock_input)
        interp.interpret('INPUT "Enter PI: ", MY_PI')
        self.assertEqual(prompts, ["Enter PI: "])
        self.assertAlmostEqual(interp.variables["MY_PI"], 3.14159)
        self.assertIsInstance(interp.variables["MY_PI"], float)

    def test_input_custom_prompt_semicolon_and_string(self):
        prompts = []

        def mock_input(prompt):
            prompts.append(prompt)
            return "Alice"

        interp = Interpreter(input_func=mock_input)
        interp.interpret('INPUT "Enter name: "; NAME')
        self.assertEqual(prompts, ["Enter name: "])
        self.assertEqual(interp.variables["NAME"], "Alice")
        self.assertIsInstance(interp.variables["NAME"], str)

    def test_input_quoted_string_strips_quotes(self):
        def mock_input(prompt):
            return '"42"'  # Quoted number should remain string "42"

        interp = Interpreter(input_func=mock_input)
        interp.interpret("INPUT CODE")
        self.assertEqual(interp.variables["CODE"], "42")
        self.assertIsInstance(interp.variables["CODE"], str)

    def test_input_string_variable_with_dollar_suffix(self):
        def mock_input(prompt):
            return "100"  # Numeric input into a $ variable stays a string

        interp = Interpreter(input_func=mock_input)
        interp.interpret("INPUT ID$")
        self.assertEqual(interp.variables["ID$"], "100")
        self.assertIsInstance(interp.variables["ID$"], str)

    def test_input_empty_numeric_defaults_to_zero(self):
        def mock_input(prompt):
            return ""

        interp = Interpreter(input_func=mock_input)
        interp.interpret("INPUT N")
        self.assertEqual(interp.variables["N"], 0)

    def test_input_multiple_variables_single_line(self):
        def mock_input(prompt):
            return "10, 20.5, Hello"

        interp = Interpreter(input_func=mock_input)
        interp.interpret("INPUT A, B, C")
        self.assertEqual(interp.variables["A"], 10)
        self.assertAlmostEqual(interp.variables["B"], 20.5)
        self.assertEqual(interp.variables["C"], "Hello")

    def test_input_multiple_variables_with_embedded_commas_in_quotes(self):
        def mock_input(prompt):
            return '"Doe, John", 35'

        interp = Interpreter(input_func=mock_input)
        interp.interpret("INPUT FULLNAME$, AGE")
        self.assertEqual(interp.variables["FULLNAME$"], "Doe, John")
        self.assertEqual(interp.variables["AGE"], 35)

    def test_input_multiple_variables_multi_line_reprompt(self):
        responses = ["10", "20"]
        prompts = []

        def mock_input(prompt):
            prompts.append(prompt)
            return responses.pop(0)

        interp = Interpreter(input_func=mock_input)
        interp.interpret("INPUT A, B")
        self.assertEqual(prompts, ["? ", "?? "])
        self.assertEqual(interp.variables["A"], 10)
        self.assertEqual(interp.variables["B"], 20)

    def test_input_in_single_line_if(self):
        def mock_input(prompt):
            return "99"

        interp = Interpreter(input_func=mock_input)
        code = """
X = 10
IF X = 10 THEN INPUT "Enter secret: ", SECRET
"""
        interp.interpret(code)
        self.assertEqual(interp.variables["SECRET"], 99)

    def test_input_in_block_if(self):
        def mock_input(prompt):
            return "50"

        interp = Interpreter(input_func=mock_input)
        code = """
FLAG = 1
IF FLAG = 1 THEN
    INPUT "Enter bonus: ", BONUS
ELSE
    BONUS = 0
END IF
"""
        interp.interpret(code)
        self.assertEqual(interp.variables["BONUS"], 50)

    def test_input_in_for_loop(self):
        inputs = ["10", "20", "30"]

        def mock_input(prompt):
            return inputs.pop(0)

        interp = Interpreter(input_func=mock_input)
        code = """
TOTAL = 0
FOR I = 1 TO 3
    INPUT VAL
    TOTAL = TOTAL + VAL
NEXT I
"""
        interp.interpret(code)
        self.assertEqual(interp.variables["TOTAL"], 60)

    def test_module_interpret_with_input_func(self):
        def mock_input(prompt):
            return "7"

        # Test module-level function
        interpret("INPUT N", input_func=mock_input)


if __name__ == "__main__":
    unittest.main()
