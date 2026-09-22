"""Test script for Phase 1.5 - Simple Interpreter"""
from calcbasic.lexer import tokenize, Token
from calcbasic.interpreter import SimpleInterpreter


def test_basic_assignment():
    """Test simple variable assignment."""
    s = SimpleInterpreter()
    tokens = tokenize("A = 10")
    print(f"Tokens for 'A = 10': {tokens}")
    assert len(tokens) == 4
    assert tokens[0].type == "IDENTIFIER"
    assert tokens[0].value == "A"
    assert tokens[1].type == "EQUAL"
    assert tokens[2].type == "NUMBER"
    assert tokens[2].value == 10
    assert tokens[3].type == "EOF"

    # Now evaluate
    s.evaluate("A = 10")
    assert s.variables["A"] == 10
    print("[PASS] test_basic_assignment passed")


def test_simple_expression():
    """Test simple expression evaluation."""
    s = SimpleInterpreter()
    result = s.evaluate("10 + 20")
    assert result == 30
    print("[PASS] test_simple_expression passed")


def test_multiplication():
    """Test multiplication precedence."""
    s = SimpleInterpreter()
    result = s.evaluate("2 * 3 + 4")
    assert result == 10  # (2*3) + 4 = 10, multiplication first
    print("[PASS] test_multiplication passed")


def test_parentheses():
    """Test parentheses grouping."""
    s = SimpleInterpreter()
    result = s.evaluate("(10 + 5) * 2")
    assert result == 30  # (10+5) * 2 = 30
    print("[PASS] test_parentheses passed")


def test_power():
    """Test exponentiation."""
    s = SimpleInterpreter()
    result = s.evaluate("2 ^ 3")
    assert result == 8
    print("[PASS] test_power passed")


def test_variable_lookup():
    """Test variable lookup after assignment."""
    s = SimpleInterpreter()
    s.evaluate("A = 5")
    result = s.evaluate("A + 3")
    assert result == 8
    print("[PASS] test_variable_lookup passed")


def test_print_statement():
    """Test PRINT statement."""
    from calcbasic.interpreter import interpret
    import sys
    from io import StringIO

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    interpret("PRINT 10 + 5")

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert "15" in output or "15.0" in output
    print("[PASS] test_print_statement passed")


def test_assignment_then_eval():
    """Test assignment followed by expression evaluation."""
    s = SimpleInterpreter()
    s.evaluate("X = 42")
    result = s.evaluate("X * 2")
    assert result == 84
    print("[PASS] test_assignment_then_eval passed")


if __name__ == "__main__":
    test_basic_assignment()
    test_simple_expression()
    test_multiplication()
    test_parentheses()
    test_power()
    test_variable_lookup()
    test_print_statement()
    test_assignment_then_eval()
    print("\n[PASS] All Phase 1.5 tests passed!")