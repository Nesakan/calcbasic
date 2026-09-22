# CalcBASIC Parser - Phase 2
# Recursive-descent parser that produces an Abstract Syntax Tree (AST)

from calcbasic.lexer import Token


# ---------------------------------------------------------------------------
# AST Node Types
# ---------------------------------------------------------------------------

class ASTNode:
    """Base class for all AST nodes."""
    pass


class NumberNode(ASTNode):
    """Represents a numeric literal."""
    def __init__(self, token: Token):
        self.token = token
        self.value = token.value


class VariableNode(ASTNode):
    """Represents a variable reference (e.g., X, MyVar)."""
    def __init__(self, token: Token):
        self.token = token
        self.name = token.value


class BinaryOpNode(ASTNode):
    """Represents a binary operation (e.g., A + B, 10 * 2)."""
    def __init__(self, left: ASTNode, operator: Token, right: ASTNode):
        self.left = left
        self.operator = operator
        self.right = right


class AssignmentNode(ASTNode):
    """Represents a variable assignment (e.g., A = 10)."""
    def __init__(self, name: Token, value: ASTNode):
        self.name = name
        self.value = value


class PrintNode(ASTNode):
    """Represents a print statement (e.g., PRINT A, PRINT 10 + 5)."""
    def __init__(self, expression: ASTNode):
        self.expression = expression


class StringNode(ASTNode):
    """Represents a string literal (e.g., "Hello", 'World')."""
    def __init__(self, token: Token):
        self.token = token
        self.value = token.value


class ProgramNode(ASTNode):
    """Represents a sequence of statements in a CalcBASIC program."""
    def __init__(self, statements: list):
        self.statements = statements


class UnaryOpNode(ASTNode):
    """Represents a unary operation (e.g., NOT X, -X)."""
    def __init__(self, operator: Token, operand: ASTNode):
        self.operator = operator
        self.operand = operand


class IfNode(ASTNode):
    """Represents an IF-THEN-ELSE statement."""
    def __init__(self, condition: ASTNode, then_branch: list, else_branch: list | None = None):
        self.condition = condition
        self.then_branch = then_branch if isinstance(then_branch, list) else [then_branch]
        self.else_branch = else_branch if (else_branch is None or isinstance(else_branch, list)) else [else_branch]


class ForNode(ASTNode):
    """Represents a FOR...TO...NEXT loop."""
    def __init__(
        self,
        target: Token,
        start_expr: ASTNode,
        end_expr: ASTNode,
        step_expr: ASTNode | None,
        body: list,
        next_target: Token | None = None,
    ):
        self.target = target
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.step_expr = step_expr
        self.body = body
        self.next_target = next_target


class FunctionCallNode(ASTNode):
    """Represents a function call (e.g., SIN(X), ABS(-5), ROUND(3.1415, 2))."""
    def __init__(self, name: Token, args: list):
        self.name = name
        self.args = args


class InputNode(ASTNode):
    """Represents an INPUT statement (e.g., INPUT X, INPUT "Prompt: ", NAME, INPUT A, B)."""
    def __init__(self, prompt: Token | None, targets: list[Token]):
        self.prompt = prompt
        self.targets = targets


# ---------------------------------------------------------------------------
# Recursive-Descent Parser
# ---------------------------------------------------------------------------

class Parser:
    """
    Recursive-descent parser for CalcBASIC.

    Grammar (precedence lowest to highest):
        expression  := or_expr
        or_expr     := and_expr (('OR') and_expr)*
        and_expr    := not_expr (('AND') not_expr)*
        not_expr    := 'NOT' not_expr | comparison
        comparison  := addition (('=' | '<>' | '<' | '>' | '<=' | '>=') addition)*
        addition    := term     (('+' | '-') term)*
        term        := factor   (('*' | '/') factor)
        factor      := power
        power       := unary    (('^') power)?         # right-associative
        unary       := '-' unary | '+' unary | primary
        primary     := NUMBER | IDENTIFIER | STRING | '(' expression ')'

    The parser consumes tokens from the lexer and builds an AST.
    """

    COMPARISON_OPS = (
        "EQUAL",
        "NOT_EQUAL",
        "LESS",
        "GREATER",
        "LESS_EQUAL",
        "GREATER_EQUAL",
    )

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        """Look at the current token without consuming it."""
        if self.pos >= len(self.tokens):
            return Token(type="EOF", value=None, line=0, column=0)
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        """Move to the next token and return the one we just passed."""
        tok = self._peek()
        self.pos += 1
        return tok

    def _expect(self, token_type: str) -> Token:
        """Expect and consume a specific token type, raising on mismatch."""
        tok = self._peek()
        if tok.type != token_type:
            raise ValueError(
                f"Expected {token_type}, got {tok.type} at line {tok.line}, "
                f"column {tok.column}"
            )
        return self._advance()

    # ---- Grammar methods (precedence order: lowest to highest) ----

    def _parse_expression(self) -> ASTNode:
        """
        expression := or_expr

        Top-level expression parser.
        """
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        """
        or_expr := and_expr (('OR') and_expr)*

        Handles logical OR with lowest precedence among booleans.
        """
        left = self._parse_and()

        while self._peek().type == "OR":
            op = self._advance()
            right = self._parse_and()
            left = BinaryOpNode(left=left, operator=op, right=right)

        return left

    def _parse_and(self) -> ASTNode:
        """
        and_expr := not_expr (('AND') not_expr)*

        Handles logical AND with higher precedence than OR.
        """
        left = self._parse_not()

        while self._peek().type == "AND":
            op = self._advance()
            right = self._parse_not()
            left = BinaryOpNode(left=left, operator=op, right=right)

        return left

    def _parse_not(self) -> ASTNode:
        """
        not_expr := 'NOT' not_expr | comparison

        Handles logical NOT with higher precedence than AND/OR.
        """
        if self._peek().type == "NOT":
            op = self._advance()
            operand = self._parse_not()
            return UnaryOpNode(operator=op, operand=operand)

        return self._parse_comparison()

    def _parse_comparison(self) -> ASTNode:
        """
        comparison := addition (('=' | '<>' | '<' | '>' | '<=' | '>=') addition)*

        Handles comparison operators with lower precedence than arithmetic
        but higher than boolean operators.
        """
        left = self._parse_addition()

        while self._peek().type in self.COMPARISON_OPS:
            op = self._advance()
            right = self._parse_addition()
            left = BinaryOpNode(left=left, operator=op, right=right)

        return left

    def _parse_addition(self) -> ASTNode:
        """
        addition := term (('+' | '-') term)*

        Handles addition and subtraction with higher precedence than comparison
        but lower than multiplication/division.
        """
        left = self._parse_term()

        while self._peek().type in ("PLUS", "MINUS"):
            op = self._advance()
            right = self._parse_term()
            left = BinaryOpNode(left=left, operator=op, right=right)

        return left

    def _parse_term(self) -> ASTNode:
        """
        term := factor (('*' | '/') factor)*

        Handles multiplication and division with higher precedence than +/-
        but lower than unary/exponentiation.
        """
        left = self._parse_factor()

        while self._peek().type in ("STAR", "SLASH"):
            op = self._advance()
            right = self._parse_factor()
            left = BinaryOpNode(left=left, operator=op, right=right)

        return left

    def _parse_factor(self) -> ASTNode:
        """
        factor := power

        Passes through to _parse_power for exponentiation handling.
        """
        return self._parse_power()

    def _parse_power(self) -> ASTNode:
        """
        power := unary (('^') power)?

        Handles exponentiation with right-associativity.

        Example: 2 ^ 3 ^ 2 parses as 2 ^ (3 ^ 2) because:
        - _parse_power parses base via _parse_unary()
        - sees '^', advances, calls _parse_power() recursively for exponent
        - the recursive call also checks for '^', so 3 ^ 2 is parsed first
        - result: BinaryOpNode(left=2, op='^', right=BinaryOpNode(left=3, op='^', right=2))
        """
        base = self._parse_unary()

        if self._peek().type == "POWER":
            self._advance()  # consume '^'
            exponent = self._parse_power()  # right-assoc: parse exponent first
            # We need the '^' token. Since _advance() consumed it, we need to
            # reconstruct or save it. The simplest approach: create the BinaryOpNode
            # using a new Token of type POWER, since we know the operator is '^'.
            # But we lose position info. Better: save the token before advancing.
            #
            # Actually, the cleanest: _parse_unary returns a node, and we check for ^.
            # When we see ^, we advance, parse the right side, and create BinaryOpNode.
            # The '^' token we consumed - we can create a new one since we know it's '^'.
            # For better position tracking, we should save the original token.
            #
            # For now, create a synthetic POWER token at position (0,0) - the interpreter
            # will use the operator type, not the token position, for evaluation.
            power_tok = Token(type="POWER", value="^", line=0, column=0)
            base = BinaryOpNode(left=base, operator=power_tok, right=exponent)

        return base

    def _parse_unary(self) -> ASTNode:
        """
        unary := '-' unary | '+' unary | primary

        Handles unary negation and unary plus.
        Also handles exponentiation: primary ^ unary (right-associative).

        After parsing primary, we check for '^' and build a power node if present.
        """
        tok = self._peek()

        if tok.type == "MINUS":
            self._advance()
            right = self._parse_unary()
            return UnaryOpNode(operator=tok, operand=right)

        elif tok.type == "PLUS":
            self._advance()
            return self._parse_unary()
        else:
            node = self._parse_primary()

            # After primary, check for exponentiation (right-associative)
            if self._peek().type == "POWER":
                self._advance()  # consume '^'
                exponent = self._parse_power()  # recursively parse exponent
                power_tok = Token(type="POWER", value="^", line=0, column=0)
                return BinaryOpNode(left=node, operator=power_tok, right=exponent)

            return node

    def _parse_primary(self) -> ASTNode:
        """
        primary := NUMBER | IDENTIFIER | STRING | '(' expression ')'

        Returns a leaf node for numbers, variables, strings, or parenthesized expressions.
        """
        tok = self._peek()

        if tok.type == "NUMBER":
            self._advance()
            return NumberNode(tok)
        elif tok.type == "IDENTIFIER":
            self._advance()
            if self._peek().type == "LEFT_PAREN":
                self._advance()  # consume '('
                args = []
                if self._peek().type != "RIGHT_PAREN":
                    args.append(self._parse_expression())
                    while self._peek().type == "COMMA":
                        self._advance()  # consume ','
                        args.append(self._parse_expression())
                self._expect("RIGHT_PAREN")
                return FunctionCallNode(name=tok, args=args)
            return VariableNode(tok)
        elif tok.type == "STRING":
            self._advance()
            return StringNode(tok)
        elif tok.type == "LEFT_PAREN":
            self._advance()  # consume '('
            node = self._parse_expression()
            self._expect("RIGHT_PAREN")  # consume ')'
            return node
        else:
            raise ValueError(
                f"Expected primary expression at line {tok.line}, "
                f"column {tok.column}"
            )

    def _parse_statement(self) -> ASTNode:
        """
        Parse a single statement: PRINT, assignment, or expression.
        """
        first = self._peek()

        # If it looks like a print statement: PRINT expression
        if first.type == "PRINT":
            return self._parse_print()

        if first.type == "IF":
            return self._parse_if()

        if first.type == "FOR":
            return self._parse_for()

        if first.type == "INPUT":
            return self._parse_input()

        # If it looks like an assignment: IDENTIFIER EQUAL expression
        if first.type == "IDENTIFIER":
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == "EQUAL":
                return self._parse_assignment()

        # Otherwise, parse as a standalone expression
        return self._parse_expression()

    def parse(self) -> ASTNode:
        """
        Parse the full token stream and return the root AST node.

        If multiple statements are present, returns a ProgramNode.
        If a single statement is present, returns that statement directly
        for backward compatibility with existing unit tests.
        """
        statements = []

        # Skip leading newlines
        while self._peek().type == "NEWLINE":
            self._advance()

        while self._peek().type != "EOF":
            stmt = self._parse_statement()
            statements.append(stmt)

            # Consume newlines between statements
            if self._peek().type == "NEWLINE":
                while self._peek().type == "NEWLINE":
                    self._advance()
            elif self._peek().type == "EOF":
                break
            else:
                tok = self._peek()
                raise ValueError(
                    f"Unexpected token {tok.type} ({tok.value!r}) at line {tok.line}, "
                    f"column {tok.column}"
                )

        if len(statements) == 1:
            return statements[0]
        return ProgramNode(statements)

    def _parse_assignment(self) -> AssignmentNode:
        """
        Parse an assignment statement: IDENTIFIER EQUAL expression

        Returns:
            AssignmentNode with the variable name and value AST.
        """
        name_tok = self._expect("IDENTIFIER")
        self._expect("EQUAL")  # consume '='
        value = self._parse_expression()
        return AssignmentNode(name=name_tok, value=value)

    def _parse_print(self) -> PrintNode:
        """
        Parse a print statement: PRINT expression

        Returns:
            PrintNode with the expression to print.
        """
        self._expect("PRINT")  # consume 'PRINT'
        expression = self._parse_expression()
        return PrintNode(expression)

    def _parse_if(self) -> IfNode:
        """
        Parse an IF statement (single-line or multi-line block).

        Single-line: IF condition THEN statement [ELSE statement]
        Block:
            IF condition THEN
                statements...
            [ELSE
                statements...]
            END IF | ENDIF
        """
        self._expect("IF")
        condition = self._parse_expression()
        self._expect("THEN")

        # Case 1: Single-line IF
        if self._peek().type != "NEWLINE" and self._peek().type != "EOF":
            then_stmt = self._parse_statement()
            then_branch = [then_stmt]
            else_branch = None

            if self._peek().type == "ELSE":
                self._advance()
                else_stmt = self._parse_statement()
                else_branch = [else_stmt]

            return IfNode(condition=condition, then_branch=then_branch, else_branch=else_branch)

        # Case 2: Multi-line Block IF
        while self._peek().type == "NEWLINE":
            self._advance()

        then_branch = []
        else_branch = None

        while True:
            tok = self._peek()
            if tok.type in ("EOF", "ELSE", "ENDIF"):
                break
            if tok.type == "END" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == "IF":
                break
            stmt = self._parse_statement()
            then_branch.append(stmt)
            while self._peek().type == "NEWLINE":
                self._advance()

        if self._peek().type == "ELSE":
            self._advance()  # consume 'ELSE'
            while self._peek().type == "NEWLINE":
                self._advance()
            else_branch = []
            while True:
                tok = self._peek()
                if tok.type in ("EOF", "ENDIF"):
                    break
                if tok.type == "END" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == "IF":
                    break
                stmt = self._parse_statement()
                else_branch.append(stmt)
                while self._peek().type == "NEWLINE":
                    self._advance()

        tok = self._peek()
        if tok.type == "ENDIF":
            self._advance()
        elif tok.type == "END":
            self._advance()
            self._expect("IF")
        else:
            raise ValueError(
                f"Expected END IF or ENDIF for block IF statement at line {tok.line}, column {tok.column}"
            )

        return IfNode(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def _parse_for(self) -> ForNode:
        """
        Parse a FOR...TO...NEXT loop.

        Syntax:
            FOR var = start TO end [STEP step]
                statements...
            NEXT [var]
        """
        self._expect("FOR")
        target_tok = self._expect("IDENTIFIER")
        self._expect("EQUAL")
        start_expr = self._parse_expression()
        self._expect("TO")
        end_expr = self._parse_expression()

        step_expr = None
        if self._peek().type == "STEP":
            self._advance()
            step_expr = self._parse_expression()

        while self._peek().type == "NEWLINE":
            self._advance()

        body = []
        while True:
            tok = self._peek()
            if tok.type in ("EOF", "NEXT"):
                break
            stmt = self._parse_statement()
            body.append(stmt)
            while self._peek().type == "NEWLINE":
                self._advance()

        self._expect("NEXT")

        next_target = None
        if self._peek().type == "IDENTIFIER":
            next_target = self._advance()
            if next_target.value != target_tok.value:
                raise ValueError(
                    f"NEXT variable '{next_target.value}' does not match FOR variable '{target_tok.value}' "
                    f"at line {next_target.line}, column {next_target.column}"
                )

        return ForNode(
            target=target_tok,
            start_expr=start_expr,
            end_expr=end_expr,
            step_expr=step_expr,
            body=body,
            next_target=next_target,
        )

    def _parse_input(self) -> InputNode:
        """
        Parse an INPUT statement.

        Syntax:
            INPUT [prompt (',' | ';')] target (',' target)*
        """
        self._expect("INPUT")

        prompt = None
        if self._peek().type == "STRING":
            prompt = self._advance()
            if self._peek().type in ("COMMA", "SEMICOLON"):
                self._advance()
            else:
                tok = self._peek()
                raise ValueError(
                    f"Expected ',' or ';' after INPUT prompt at line {tok.line}, column {tok.column}"
                )

        targets = []
        target = self._expect("IDENTIFIER")
        targets.append(target)

        while self._peek().type == "COMMA":
            self._advance()  # consume ','
            target = self._expect("IDENTIFIER")
            targets.append(target)

        return InputNode(prompt=prompt, targets=targets)