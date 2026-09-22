# CalcBASIC - A BASIC-like Programming Language Interpreter

CalcBASIC is a small BASIC-like programming language inspired by programmable calculator languages, built from scratch to teach interpreter implementation concepts.

## Features Implemented

### Current State
- **Lexer/Tokenizer**: Converts source code to tokens with line/column tracking
- **Recursive-Descent Parser**: Builds Abstract Syntax Trees (AST)
- **Tree-Walk Interpreter**: Evaluates AST nodes
- **Variables**: Assignment and lookup (`A = 10`, `NAME = "Alice"`)
- **Arithmetic Operations**: Addition (+), Subtraction (-), Multiplication (*), Division (/), Exponentiation (^)
- **String Literals & Concatenation**: Double/single quotes (`"Hello"`, `'World'`), escape sequences (`\n`, `\t`, `\"`, `\'`, `\\`), and concatenation via `+` (`"Hello " + "World"`)
- **Comparison Operators**: Equality (`=`, `==`), Inequality (`<>`, `!=`), Less than (`<`), Greater than (`>`), Less than or equal (`<=`), Greater than or equal (`>=`) evaluating to `1` (True) or `0` (False)
- **Boolean Operators**: Logical `AND`, `OR`, and `NOT` (case-insensitive) with proper operator precedence
- **Conditional Execution**: Single-line (`IF condition THEN stmt [ELSE stmt]`) and multi-line block IF (`IF condition THEN ... [ELSE ...] END IF` or `ENDIF`), supporting nested conditions
- **Loops**: `FOR var = start TO end [STEP step]` with `NEXT [var]`, supporting positive, negative, and fractional increments, variable validation, and nested loops
- **Mathematical Functions**: Comprehensive built-in math functions (`ABS`, `SQR`/`SQRT`, `SIN`, `COS`, `TAN`, `ASIN`, `ACOS`, `ATAN`, `ATAN2`, `LOG`/`LN`, `LOG10`, `EXP`, `INT`, `FIX`, `FLOOR`, `CEIL`, `ROUND`, `SGN`, `MIN`, `MAX`, `DEG`, `RAD`, `RND`) and constants `PI` and `E` (usable both as variables and functions)
- **Input**: `INPUT [prompt (,|;)] var1 [, var2, ...]` supporting default prompt `? `, custom prompts, multi-variable splitting, auto-type inference (`int`, `float`, `str`), explicit string variables (`NAME$`), and mockable input for testing
- **Output**: PRINT statement (`PRINT A`, `PRINT "Hello " + NAME`, `PRINT A > B AND B > 0`)
- **Operator Precedence**: Correct hierarchy (Power > Multiply/Divide > Add/Subtract > Comparison > NOT > AND > OR)
- **Right-Associative Power**: `2 ^ 3 ^ 2` = 2^(3^2) = 512
- **Parentheses**: For grouping expressions
- **Multi-line Programs**: Sequential statement execution
- **REPL**: Interactive read-eval-print loop with expression evaluation

### Language Examples
```basic
' Basic arithmetic and strings
A = 10 + 20
PRINT A                   ' Outputs: 30

NAME = "Alice"
GREETING = "Hello, " + NAME + "!"
PRINT GREETING            ' Outputs: Hello, Alice!

' Comparisons & Boolean logic (1 = True, 0 = False)
PRINT A > 15              ' Outputs: 1
PRINT NAME = "Bob"        ' Outputs: 0
IS_VALID = A > 15 AND NAME = "Alice"
PRINT IS_VALID            ' Outputs: 1
PRINT NOT (A = 30)        ' Outputs: 0
PRINT 10 < 5 OR 3 = 3     ' Outputs: 1

' Conditional execution (Single-line IF)
IF A > 15 THEN PRINT "A is large" ELSE PRINT "A is small"

' Conditional execution (Multi-line Block IF)
IF A >= 30 THEN
    STATUS = "HIGH"
    PRINT "Threshold reached"
ELSE
    STATUS = "NORMAL"
END IF

' Loops (FOR...TO...NEXT)
TOTAL = 0
FOR I = 1 TO 5
    TOTAL = TOTAL + I
NEXT I
PRINT TOTAL               ' Outputs: 15

' Loops with STEP
FOR K = 10 TO 0 STEP -2
    PRINT K               ' Outputs: 10, 8, 6, 4, 2, 0
NEXT K

' Operator precedence
B = 2 + 3 * 4             ' B = 14 (not 20)
PRINT B

' Power operations
C = 2 ^ 3 ^ 2             ' C = 512 (right-associative)
PRINT C

' Parentheses override
D = (2 + 3) * 4           ' D = 20
PRINT D

' Combined
X = 5
Y = X * 2 + 3             ' Y = 13
PRINT Y

' Mathematical functions & constants
RADIUS = 5
AREA = PI * RADIUS ^ 2
PRINT ROUND(AREA, 2)      ' Circle area: 78.54
HYPOT = SQRT(3^2 + 4^2)   ' Hypotenuse: 5.0
PRINT ROUND(SIN(PI/4)^2 + COS(PI/4)^2, 4)  ' Outputs: 1.0
PRINT ABS(-42)            ' Outputs: 42
PRINT INT(3.7)            ' Outputs: 3
PRINT INT(-3.7)           ' Outputs: -4 (classic BASIC floor)
PRINT MAX(10, 20, 5, 80)  ' Outputs: 80
PRINT RND()               ' Random float in [0, 1)

' Interactive User Input
INPUT "Enter your name: "; USER_NAME$
PRINT "Hello, " + USER_NAME$
INPUT "Enter age: ", AGE
INPUT "Enter 2 numbers (X, Y): ", X, Y
PRINT X + Y
```

## Project Structure
```
calcbasic/
├── __init__.py          # Package initialization
├── lexer.py             # Tokenizer
├── parser.py            # Recursive-descent parser
├── interpreter.py       # AST evaluator
├── repl.py              # Interactive REPL
└── tests/
    ├── test_lexer.py       # Lexer unit tests
    ├── test_strings.py     # String literals and concatenation tests
    ├── test_comparison.py  # Comparison operator tests
    ├── test_boolean.py     # Boolean operator tests (AND, OR, NOT)
    ├── test_if.py          # IF...THEN...ELSE tests (single-line & block)
    ├── test_for.py         # FOR...TO...NEXT loop tests
    ├── test_math.py        # Mathematical functions & constants tests
    ├── test_input.py       # INPUT statement tests
    ├── test_phase2.py      # Parser/interpreter tests
    └── test_precedence.py  # Precedence and PRINT verification
```

## How to Run

### Run Tests
```bash
# Run all unit tests
python -m unittest discover tests

# Or run individual test suites
python -m unittest tests.test_lexer
python -m unittest tests.test_strings
python -m unittest tests.test_comparison
python -m unittest tests.test_boolean
python -m unittest tests.test_if
python -m unittest tests.test_for
python -m unittest tests.test_math
python -m unittest tests.test_input
python test_phase2.py
python test_precedence.py
```

### Use the REPL
```bash
python repl.py
```
Then enter CalcBASIC statements:
```
CalcBASIC> A = 10 + 20
CalcBASIC> PRINT A
30
CalcBASIC> FOR I = 1 TO 3: PRINT I: NEXT I  (or on separate lines)
CalcBASIC> exit
```

### Interpret Files
Create a `.bas` file and run:
```bash
python -c "
from calcbasic.interpreter import Interpreter
interp = Interpreter()
with open('program.bas') as f:
    interp.interpret(f.read())
"
```

## Design Principles

1. **From Scratch**: No parser generators or existing interpreter frameworks
2. **Modular Architecture**: Clear separation of lexing, parsing, and interpretation
3. **Educational Focus**: Code is readable and beginner-friendly
4. **Extensible Design**: Easy to add new language features
5. **Correct Error Reporting**: Line/column information for debugging

## Next Planned Features
- String manipulation functions (`LEN`, `CHR$`, `ASC$`, `LEFT$`, `RIGHT$`, `MID$`)
- Arrays (`DIM` statement)
- Subroutines (`GOSUB`/`RETURN`)
- Loops (`WHILE...DO...LOOP`)

## Requirements
- Python 3.6+

## License
MIT - Feel free to learn from and extend this implementation!