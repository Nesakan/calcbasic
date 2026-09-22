# CalcBASIC Interpreter - Phase 1.5 & 2
# Evaluates tokenized source code from the lexer, using AST from parser

import csv
import io
import math
import random
from calcbasic.lexer import tokenize, Token
from calcbasic.parser import (
    Parser,
    ASTNode,
    AssignmentNode,
    BinaryOpNode,
    NumberNode,
    VariableNode,
    PrintNode,
    StringNode,
    ProgramNode,
    UnaryOpNode,
    IfNode,
    ForNode,
    FunctionCallNode,
    InputNode,
)


class Interpreter:
    """
    Evaluates CalcBASIC AST nodes produced by the Phase 2 parser.

    Handles:
    - Variable assignment and lookup
    - Arithmetic expressions with proper precedence
    - String literals and string concatenation
    - Print statements
    - Multi-statement programs
    """

    def __init__(self, input_func=input):
        self.input_func = input_func
        self.variables = {
            "PI": math.pi,
            "E": math.e,
        }

    def _is_truthy(self, val) -> bool:
        """Determine truthiness of a value. Numbers are truthy if non-zero; strings raise TypeError."""
        if isinstance(val, (int, float)):
            return val != 0
        raise TypeError(f"Type mismatch: cannot use {type(val).__name__} in boolean operation")

    # ---- AST Evaluation Methods ----

    def _eval_number(self, node: NumberNode) -> float:
        """Evaluate a number node."""
        return node.value

    def _eval_variable(self, node: VariableNode) -> float | str:
        """Evaluate a variable node, raising if undefined."""
        name = node.name
        if name not in self.variables:
            raise ValueError(f"Undefined variable '{name}'")
        return self.variables[name]

    def _eval_binary(self, node: BinaryOpNode) -> float | str:
        """Evaluate a binary operation node with type checking."""
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        op = node.operator.type

        if op == "PLUS":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            else:
                raise TypeError(
                    f"Type mismatch: cannot add {type(left).__name__} and {type(right).__name__}"
                )
        elif op in ("MINUS", "STAR", "SLASH", "POWER"):
            if isinstance(left, str) or isinstance(right, str):
                raise TypeError(
                    f"Type mismatch: operator '{node.operator.value}' not supported for strings"
                )
            if op == "MINUS":
                return left - right
            elif op == "STAR":
                return left * right
            elif op == "SLASH":
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                return left / right
            elif op == "POWER":
                return left ** right
        elif op in ("EQUAL", "NOT_EQUAL", "LESS", "GREATER", "LESS_EQUAL", "GREATER_EQUAL"):
            # Comparison operators: supported for numbers with numbers, and strings with strings
            is_both_num = isinstance(left, (int, float)) and isinstance(right, (int, float))
            is_both_str = isinstance(left, str) and isinstance(right, str)
            if not (is_both_num or is_both_str):
                raise TypeError(
                    f"Type mismatch: cannot compare {type(left).__name__} and {type(right).__name__}"
                )
            if op == "EQUAL":
                return 1 if left == right else 0
            elif op == "NOT_EQUAL":
                return 1 if left != right else 0
            elif op == "LESS":
                return 1 if left < right else 0
            elif op == "GREATER":
                return 1 if left > right else 0
            elif op == "LESS_EQUAL":
                return 1 if left <= right else 0
            elif op == "GREATER_EQUAL":
                return 1 if left >= right else 0
            else:
                raise ValueError(f"Unknown operator: {op}")
        elif op == "AND":
            left_bool = self._is_truthy(left)
            right_bool = self._is_truthy(right)
            return 1 if (left_bool and right_bool) else 0
        elif op == "OR":
            left_bool = self._is_truthy(left)
            right_bool = self._is_truthy(right)
            return 1 if (left_bool or right_bool) else 0
        else:
            raise ValueError(f"Unknown operator: {op}")

    def _eval_assignment(self, node: AssignmentNode) -> None:
        """Evaluate an assignment node and store the variable."""
        value = self.evaluate(node.value)
        name = node.name.value
        self.variables[name] = value

    def _eval_string(self, node: StringNode) -> str:
        """Evaluate a string node."""
        return node.value

    def _eval_print(self, node: PrintNode) -> None:
        """Evaluate a print node and output the result."""
        value = self.evaluate(node.expression)
        print(value)

    def _eval_program(self, node: ProgramNode) -> float | str | None:
        """Evaluate each statement in a program sequentially."""
        last_result = None
        for stmt in node.statements:
            last_result = self.evaluate(stmt)
        return last_result

    def _eval_unary(self, node: UnaryOpNode) -> int | float:
        """Evaluate a unary operation node."""
        op = node.operator.type
        val = self.evaluate(node.operand)

        if op == "NOT":
            return 1 if not self._is_truthy(val) else 0
        elif op == "MINUS":
            if isinstance(val, (int, float)):
                return -val
            raise TypeError(f"Type mismatch: cannot negate {type(val).__name__}")
        elif op == "PLUS":
            if isinstance(val, (int, float)):
                return +val
            raise TypeError(f"Type mismatch: cannot apply '+' to {type(val).__name__}")
        else:
            raise ValueError(f"Unknown unary operator: {op}")

    def _eval_if(self, node: IfNode) -> float | str | None:
        """Evaluate an IF statement (single-line or block)."""
        cond_val = self.evaluate(node.condition)
        is_true = self._is_truthy(cond_val)

        last_result = None
        if is_true:
            for stmt in node.then_branch:
                last_result = self.evaluate(stmt)
        elif node.else_branch:
            for stmt in node.else_branch:
                last_result = self.evaluate(stmt)

        return last_result

    def _eval_for(self, node: ForNode) -> float | str | None:
        """Evaluate a FOR...TO...NEXT loop."""
        start_val = self.evaluate(node.start_expr)
        end_val = self.evaluate(node.end_expr)

        if node.step_expr is not None:
            step_val = self.evaluate(node.step_expr)
        else:
            step_val = 1

        if (
            not isinstance(start_val, (int, float))
            or not isinstance(end_val, (int, float))
            or not isinstance(step_val, (int, float))
        ):
            raise TypeError("Type mismatch: FOR loop bounds and step must be numbers")

        if step_val == 0:
            raise ValueError("FOR loop STEP cannot be zero")

        var_name = node.target.value
        current = start_val
        self.variables[var_name] = current
        last_result = None

        while (step_val > 0 and current <= end_val) or (step_val < 0 and current >= end_val):
            self.variables[var_name] = current
            for stmt in node.body:
                last_result = self.evaluate(stmt)
            # Advance variable by step
            current = self.variables[var_name] + step_val
            self.variables[var_name] = current

        return last_result

    def _eval_function_call(self, node: FunctionCallNode) -> float | int:
        """Evaluate a built-in mathematical function call."""
        func_name = node.name.value.upper()
        args = [self.evaluate(arg) for arg in node.args]

        # Verify all arguments are numbers
        for i, arg in enumerate(args):
            if not isinstance(arg, (int, float)):
                raise TypeError(
                    f"Type mismatch: function {func_name} argument {i + 1} must be a number, got {type(arg).__name__}"
                )

        num_args = len(args)

        # 0-argument functions
        if func_name == "PI":
            if num_args != 0:
                raise ValueError(f"Function PI expects 0 arguments, got {num_args}")
            return math.pi
        if func_name == "E":
            if num_args != 0:
                raise ValueError(f"Function E expects 0 arguments, got {num_args}")
            return math.e

        # Random: RND() or RND(n)
        if func_name == "RND":
            if num_args == 0:
                return random.random()
            elif num_args == 1:
                n = args[0]
                if n > 1:
                    return random.randint(1, int(n))
                return random.random()
            else:
                raise ValueError(f"Function RND expects 0 or 1 arguments, got {num_args}")

        # Variable-arity functions
        if func_name == "MIN":
            if num_args < 1:
                raise ValueError(f"Function MIN expects at least 1 argument, got 0")
            return min(args)
        if func_name == "MAX":
            if num_args < 1:
                raise ValueError(f"Function MAX expects at least 1 argument, got 0")
            return max(args)

        # 2-argument functions
        if func_name == "ATAN2":
            if num_args != 2:
                raise ValueError(f"Function ATAN2 expects 2 arguments, got {num_args}")
            return math.atan2(args[0], args[1])

        # 1- or 2-argument functions
        if func_name == "ROUND":
            if num_args == 1:
                return round(args[0])
            elif num_args == 2:
                return round(args[0], int(args[1]))
            else:
                raise ValueError(f"Function ROUND expects 1 or 2 arguments, got {num_args}")

        # 1-argument functions
        if num_args != 1:
            known_single_arg = (
                "ABS", "SQR", "SQRT", "SIN", "COS", "TAN",
                "ASIN", "ACOS", "ATAN", "LOG", "LN", "LOG10",
                "EXP", "INT", "FIX", "FLOOR", "CEIL", "SGN", "DEG", "RAD"
            )
            if func_name in known_single_arg:
                raise ValueError(f"Function {func_name} expects 1 argument, got {num_args}")
            raise ValueError(f"Undefined function '{node.name.value}'")

        x = args[0]

        if func_name == "ABS":
            return abs(x)
        elif func_name in ("SQR", "SQRT"):
            if x < 0:
                raise ValueError(f"Math domain error in {func_name}: argument must be non-negative (got {x})")
            return math.sqrt(x)
        elif func_name == "SIN":
            return math.sin(x)
        elif func_name == "COS":
            return math.cos(x)
        elif func_name == "TAN":
            return math.tan(x)
        elif func_name == "ASIN":
            if x < -1 or x > 1:
                raise ValueError(f"Math domain error in ASIN: argument must be between -1 and 1 (got {x})")
            return math.asin(x)
        elif func_name == "ACOS":
            if x < -1 or x > 1:
                raise ValueError(f"Math domain error in ACOS: argument must be between -1 and 1 (got {x})")
            return math.acos(x)
        elif func_name == "ATAN":
            return math.atan(x)
        elif func_name in ("LOG", "LN"):
            if x <= 0:
                raise ValueError(f"Math domain error in {func_name}: argument must be positive (got {x})")
            return math.log(x)
        elif func_name == "LOG10":
            if x <= 0:
                raise ValueError(f"Math domain error in LOG10: argument must be positive (got {x})")
            return math.log10(x)
        elif func_name == "EXP":
            return math.exp(x)
        elif func_name == "INT":
            return math.floor(x)
        elif func_name == "FIX":
            return int(x)
        elif func_name == "FLOOR":
            return math.floor(x)
        elif func_name == "CEIL":
            return math.ceil(x)
        elif func_name == "SGN":
            return 1 if x > 0 else (-1 if x < 0 else 0)
        elif func_name == "DEG":
            return math.degrees(x)
        elif func_name == "RAD":
            return math.radians(x)
        else:
            raise ValueError(f"Undefined function '{node.name.value}'")

    def _split_input_line(self, line: str) -> list[tuple[str, bool]]:
        """Split a comma-separated input line respecting quotes. Returns list of (val, was_quoted)."""
        line_str = line.strip()
        if not line_str:
            return []

        parts = []
        current = []
        in_quote = None
        was_quoted = False

        for ch in line_str:
            if in_quote:
                if ch == in_quote:
                    in_quote = None
                else:
                    current.append(ch)
            elif ch in ('"', "'"):
                in_quote = ch
                was_quoted = True
            elif ch == ",":
                parts.append(("".join(current).strip(), was_quoted))
                current = []
                was_quoted = False
            else:
                current.append(ch)

        parts.append(("".join(current).strip(), was_quoted))
        return parts

    def _parse_single_input_value(self, raw_val: str, var_name: str, was_quoted: bool = False) -> int | float | str:
        """Parse raw input into int, float, or string according to value and variable name."""
        raw_val = raw_val.strip()

        # If wrapped in quotes or marked as quoted, treat as string
        if was_quoted:
            return raw_val
        if len(raw_val) >= 2 and (
            (raw_val[0] == '"' and raw_val[-1] == '"') or (raw_val[0] == "'" and raw_val[-1] == "'")
        ):
            return raw_val[1:-1]

        # Explicit string variable convention (ends with $)
        if var_name.endswith("$"):
            return raw_val

        # Empty numeric input defaults to 0 in classic BASIC
        if raw_val == "":
            return 0

        # Attempt integer conversion
        try:
            return int(raw_val)
        except ValueError:
            pass

        # Attempt float conversion
        try:
            return float(raw_val)
        except ValueError:
            pass

        # Fallback to string
        return raw_val

    def _eval_input(self, node: InputNode) -> None:
        """Evaluate an INPUT statement."""
        if node.prompt is not None:
            prompt_str = str(node.prompt.value)
        else:
            prompt_str = "? "

        raw_line = self.input_func(prompt_str) or ""
        values = self._split_input_line(raw_line)

        target_idx = 0
        while target_idx < len(node.targets):
            if target_idx < len(values):
                val_str, was_quoted = values[target_idx]
                var_name = node.targets[target_idx].value
                self.variables[var_name] = self._parse_single_input_value(val_str, var_name, was_quoted)
                target_idx += 1
            else:
                # Prompt for remaining values
                more_line = self.input_func("?? ") or ""
                more_vals = self._split_input_line(more_line)
                if not more_vals:
                    more_vals = [("", False)]
                values.extend(more_vals)


    # ---- Top-level evaluation ----

    def evaluate(self, node: ASTNode | str) -> float | str | None:
        """
        Evaluate an AST node and return the result (if any).

        Args:
            node: The AST node (or source string) to evaluate
        """
        if isinstance(node, str):
            return self.interpret(node)

        node_type = type(node).__name__

        if node_type == "NumberNode":
            return self._eval_number(node)
        elif node_type == "VariableNode":
            return self._eval_variable(node)
        elif node_type == "BinaryOpNode":
            return self._eval_binary(node)
        elif node_type == "UnaryOpNode":
            return self._eval_unary(node)
        elif node_type == "StringNode":
            return self._eval_string(node)
        elif node_type == "AssignmentNode":
            self._eval_assignment(node)
            return None  # Assignment doesn't produce a value
        elif node_type == "PrintNode":
            self._eval_print(node)
            return None  # Print doesn't produce a value
        elif node_type == "ProgramNode":
            return self._eval_program(node)
        elif node_type == "IfNode":
            return self._eval_if(node)
        elif node_type == "ForNode":
            return self._eval_for(node)
        elif node_type == "FunctionCallNode":
            return self._eval_function_call(node)
        elif node_type == "InputNode":
            self._eval_input(node)
            return None  # Input doesn't produce an expression value
        else:
            raise ValueError(f"Unknown AST node type: {node_type}")

    # ---- Convenience functions ----

    def interpret(self, source: str) -> float | str | None:
        """
        Tokenize, parse, and evaluate a CalcBASIC source string.

        Args:
            source: The source code string to interpret
        """
        tokens = tokenize(source)
        parser = Parser(tokens)
        ast = parser.parse()
        return self.evaluate(ast)


# Backward compatibility aliases and functions
SimpleInterpreter = Interpreter


def interpret(source: str, input_func=input) -> None:
    """
    Interpret a CalcBASIC source string (backward-compatible function).

    Args:
        source: The source code string to interpret
        input_func: Optional callable for user input (default: built-in input)
    """
    interpreter = Interpreter(input_func=input_func)
    interpreter.interpret(source)