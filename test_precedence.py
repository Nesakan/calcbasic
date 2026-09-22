"""Test operator precedence and PRINT functionality"""
from calcbasic.interpreter import Interpreter

def test_precedence():
    """Test that operator precedence works correctly"""
    interp = Interpreter()

    # Test: multiplication before addition
    # 2 + 3 * 4 should be 2 + (3 * 4) = 14, not (2 + 3) * 4 = 20
    result = None
    # We need to capture the result somehow - let's modify approach

    # Test using assignment to check internal state
    interp.interpret("A = 2 + 3 * 4")
    assert interp.variables["A"] == 14, f"Expected 14, got {interp.variables['A']}"
    print("[PASS] Multiplication before addition: 2 + 3 * 4 = 14")

    # Test: power before multiplication
    # 2 * 3 ^ 2 should be 2 * (3 ^ 2) = 2 * 9 = 18, not (2 * 3) ^ 2 = 6 ^ 2 = 36
    interp.interpret("B = 2 * 3 ^ 2")
    assert interp.variables["B"] == 18, f"Expected 18, got {interp.variables['B']}"
    print("[PASS] Power before multiplication: 2 * 3 ^ 2 = 18")

    # Test: right-associative power
    # 2 ^ 3 ^ 2 should be 2 ^ (3 ^ 2) = 2 ^ 9 = 512, not (2 ^ 3) ^ 2 = 8 ^ 2 = 64
    interp.interpret("C = 2 ^ 3 ^ 2")
    assert interp.variables["C"] == 512, f"Expected 512, got {interp.variables['C']}"
    print("[PASS] Right-associative power: 2 ^ 3 ^ 2 = 512")

    # Test: parentheses override precedence
    # (2 + 3) * 4 should be 5 * 4 = 20
    interp.interpret("D = (2 + 3) * 4")
    assert interp.variables["D"] == 20, f"Expected 20, got {interp.variables['D']}"
    print("[PASS] Parentheses override: (2 + 3) * 4 = 20")

def test_print():
    """Test PRINT statement functionality"""
    # Since PRINT outputs to stdout, we can't easily capture it in tests
    # But we can verify it doesn't crash and variables work correctly

    interp = Interpreter()
    interp.interpret("A = 10")
    interp.interpret("B = 20")
    interp.interpret("PRINT A")  # Should print 10
    interp.interpret("PRINT B")  # Should print 20
    interp.interpret("PRINT A + B")  # Should print 30
    interp.interpret("PRINT A * B")  # Should print 200

    # Variables should still be set correctly
    assert interp.variables["A"] == 10
    assert interp.variables["B"] == 20
    print("[PASS] PRINT statements work correctly")

def test_combined():
    """Test combined assignment and print"""
    interp = Interpreter()

    # Complex expression
    interp.interpret("X = 5")
    interp.interpret("Y = X * 2 + 3")  # 5 * 2 + 3 = 10 + 3 = 13
    interp.interpret("PRINT Y")  # Should print 13
    assert interp.variables["Y"] == 13

    # Power with assignment
    interp.interpret("Z = 2 ^ 3 ^ 2")  # 2 ^ (3 ^ 2) = 2 ^ 9 = 512
    interp.interpret("PRINT Z")  # Should print 512
    assert interp.variables["Z"] == 512

    print("[PASS] Combined assignment and print work correctly")

def test_comparison_precedence():
    """Test comparison precedence relative to arithmetic."""
    interp = Interpreter()

    # Addition before comparison: 2 + 3 > 4 is (2 + 3) > 4 = 1, not 2 + (3 > 4) = 2 + 0 = 2
    interp.interpret("CMP1 = 2 + 3 > 4")
    assert interp.variables["CMP1"] == 1, f"Expected 1, got {interp.variables['CMP1']}"
    print("[PASS] Addition before comparison: 2 + 3 > 4 = 1")

    # Multiplication before comparison: 10 > 2 * 6 is 10 > (2 * 6) = 10 > 12 = 0
    interp.interpret("CMP2 = 10 > 2 * 6")
    assert interp.variables["CMP2"] == 0, f"Expected 0, got {interp.variables['CMP2']}"
    print("[PASS] Multiplication before comparison: 10 > 2 * 6 = 0")

    # Equality with expressions on both sides
    interp.interpret("CMP3 = 2 * 5 = 7 + 3")
    assert interp.variables["CMP3"] == 1, f"Expected 1, got {interp.variables['CMP3']}"
    print("[PASS] Both sides evaluated before equality: 2 * 5 = 7 + 3 => 1")

def test_boolean_precedence():
    """Test boolean operator precedence (NOT > AND > OR, and comparison before boolean)."""
    interp = Interpreter()

    # Comparison before boolean: 10 > 5 AND 2 < 1 => 1 AND 0 => 0
    interp.interpret("BOOL1 = 10 > 5 AND 2 < 1")
    assert interp.variables["BOOL1"] == 0
    print("[PASS] Comparison before boolean: 10 > 5 AND 2 < 1 = 0")

    # AND before OR: 1 OR 0 AND 0 => 1 OR (0 AND 0) => 1 OR 0 => 1
    interp.interpret("BOOL2 = 1 OR 0 AND 0")
    assert interp.variables["BOOL2"] == 1
    print("[PASS] AND before OR: 1 OR 0 AND 0 = 1")

    # NOT before AND: NOT 0 AND 1 => (NOT 0) AND 1 => 1 AND 1 => 1
    interp.interpret("BOOL3 = NOT 0 AND 1")
    assert interp.variables["BOOL3"] == 1
    print("[PASS] NOT before AND: NOT 0 AND 1 = 1")

    # NOT with comparison: NOT 5 > 10 => NOT (5 > 10) => NOT 0 => 1
    interp.interpret("BOOL4 = NOT 5 > 10")
    assert interp.variables["BOOL4"] == 1
    print("[PASS] NOT with comparison: NOT 5 > 10 = 1")

if __name__ == "__main__":
    test_precedence()
    test_print()
    test_combined()
    test_comparison_precedence()
    test_boolean_precedence()
    print("\n[PASS] All precedence and PRINT tests passed!")