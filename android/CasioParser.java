import java.util.Arrays;
import java.util.List;

/**
 * CASIO BASIC Parser & Command Executor for Android
 *
 * Implements recursive-descent parsing and statement evaluation for Casio BASIC,
 * with full support for:
 * - Program areas P0 through P9 (CasioMemoryManager)
 * - FA-6 cassette tape interface commands: SAVE, SAVE ALL, LOAD, LOAD ALL, VERIFY (CasioTapeManager)
 * - Direct command mode (Ready P0 prompt)
 * - Mathematical expressions with Casio operator precedence and functions (SIN, COS, TAN, SQR, etc.)
 * - Arrow storage (expression → variable) and assignment (=)
 */
public class CasioParser {

    private final CasioTokenizer tokenizer;
    private final CasioMemoryManager memoryManager;
    private final CasioTapeManager tapeManager;

    // Runtime state (variables A-Z, 0-25)
    private final double[] variables;
    private final String[] stringVars;

    // Token execution state
    private List<CasioTokenizer.Token> tokens;
    private int pos;

    // Output buffer for PRINT or status messages
    private final StringBuilder outputBuffer;
    private String lastStatus;

    public CasioParser() {
        this(new CasioMemoryManager(), new CasioTapeManager());
    }

    public CasioParser(CasioMemoryManager memoryManager, CasioTapeManager tapeManager) {
        this.tokenizer = new CasioTokenizer();
        this.memoryManager = memoryManager;
        this.tapeManager = tapeManager;
        this.variables = new double[26];
        this.stringVars = new String[26];
        this.outputBuffer = new StringBuilder();
        this.lastStatus = memoryManager.getPrompt();
    }

    public CasioMemoryManager getMemoryManager() {
        return memoryManager;
    }

    public CasioTapeManager getTapeManager() {
        return tapeManager;
    }

    public String getLastStatus() {
        return lastStatus;
    }

    public double getVariable(char name) {
        int idx = Character.toUpperCase(name) - 'A';
        if (idx >= 0 && idx < 26) {
            return variables[idx];
        }
        return 0.0;
    }

    public void setVariable(char name, double value) {
        int idx = Character.toUpperCase(name) - 'A';
        if (idx >= 0 && idx < 26) {
            variables[idx] = value;
        }
    }

    /**
     * Execute a direct command entered at the Ready prompt.
     * Examples:
     *   SAVE "BASIC"
     *   SAVE ALL
     *   LOAD "BASIC"
     *   VERIFY "BASIC"
     *   P1
     *   NEW
     *   NEW ALL
     *   PRINT 2 + 3 * 4
     */
    public String executeDirect(String commandLine) {
        if (commandLine == null || commandLine.trim().isEmpty()) {
            return memoryManager.getPrompt();
        }

        String trimmed = commandLine.trim();

        // Check for slot switch command: P0, P1, ..., P9
        if (trimmed.toUpperCase().matches("^P[0-9]$")) {
            int slot = trimmed.charAt(1) - '0';
            memoryManager.setActiveSlot(slot);
            lastStatus = memoryManager.getPrompt();
            return lastStatus;
        }

        this.tokens = tokenizer.tokenizeDetailed(trimmed);
        this.pos = 0;
        this.outputBuffer.setLength(0);

        try {
            executeStatement();
            if (outputBuffer.length() > 0) {
                return outputBuffer.toString();
            }
            return lastStatus != null ? lastStatus : memoryManager.getPrompt();
        } catch (CasioTapeManager.CasioTapeException e) {
            lastStatus = e.getDisplayError() + "\n" + memoryManager.getPrompt();
            return lastStatus;
        } catch (Exception e) {
            lastStatus = "P" + memoryManager.getActiveSlot() + " error 0\n" + memoryManager.getPrompt();
            return lastStatus;
        }
    }

    /**
     * Parse and execute a single statement.
     */
    public void executeStatement() throws CasioTapeManager.CasioTapeException {
        if (pos >= tokens.size() || peekType() == CasioTokenizer.TOK_EOF) {
            return;
        }

        int tok = peekType();

        // --- SAVE / SAVE ALL ---
        if (tok == CasioTokenizer.TOK_SAVE) {
            advance(); // consume SAVE
            boolean isAll = false;
            String filename = "";

            if (peekType() == CasioTokenizer.TOK_ALL) {
                advance(); // consume ALL
                isAll = true;
                if (peekType() == CasioTokenizer.TOK_STRING || peekType() == CasioTokenizer.TOK_IDENT) {
                    filename = advance().text;
                }
            } else if (peekType() == CasioTokenizer.TOK_STRING || peekType() == CasioTokenizer.TOK_IDENT) {
                filename = advance().text;
                if (peekType() == CasioTokenizer.TOK_ALL) {
                    advance();
                    isAll = true;
                }
            }

            int slot = memoryManager.getActiveSlot();
            if (isAll) {
                lastStatus = tapeManager.saveAll(filename, slot, memoryManager.getAllPrograms());
            } else {
                lastStatus = tapeManager.save(filename, slot, memoryManager.getActiveProgram());
            }
            return;
        }

        // --- LOAD / LOAD ALL ---
        if (tok == CasioTokenizer.TOK_LOAD) {
            advance(); // consume LOAD
            boolean isAll = false;
            String filename = "";

            if (peekType() == CasioTokenizer.TOK_ALL) {
                advance(); // consume ALL
                isAll = true;
                if (peekType() == CasioTokenizer.TOK_STRING || peekType() == CasioTokenizer.TOK_IDENT) {
                    filename = advance().text;
                }
            } else if (peekType() == CasioTokenizer.TOK_STRING || peekType() == CasioTokenizer.TOK_IDENT) {
                filename = advance().text;
                if (peekType() == CasioTokenizer.TOK_ALL) {
                    advance();
                    isAll = true;
                }
            }

            int slot = memoryManager.getActiveSlot();
            if (isAll) {
                String[] allProgs = tapeManager.loadAll(filename, slot);
                memoryManager.setAllPrograms(allProgs);
            } else {
                String code = tapeManager.load(filename, slot);
                memoryManager.setActiveProgram(code);
            }
            lastStatus = memoryManager.getPrompt();
            return;
        }

        // --- VERIFY ---
        if (tok == CasioTokenizer.TOK_VERIFY) {
            advance(); // consume VERIFY
            String filename = "";
            if (peekType() == CasioTokenizer.TOK_STRING || peekType() == CasioTokenizer.TOK_IDENT) {
                filename = advance().text;
            }

            int slot = memoryManager.getActiveSlot();
            CasioTapeManager.VerifyResult res = tapeManager.verify(
                filename,
                slot,
                memoryManager.getActiveProgram(),
                memoryManager.getAllPrograms()
            );

            if (res.success) {
                lastStatus = res.statusDisplay;
            } else {
                lastStatus = res.statusDisplay + "\n" + memoryManager.getPrompt();
            }
            return;
        }

        // --- NEW / NEW ALL ---
        if (tok == CasioTokenizer.TOK_NEW) {
            advance(); // consume NEW
            if (peekType() == CasioTokenizer.TOK_ALL) {
                advance();
                memoryManager.clearAll();
            } else {
                memoryManager.clearActiveSlot();
            }
            lastStatus = memoryManager.getPrompt();
            return;
        }

        // --- CLEAR ---
        if (tok == CasioTokenizer.TOK_CLEAR) {
            advance();
            Arrays.fill(variables, 0.0);
            Arrays.fill(stringVars, null);
            lastStatus = memoryManager.getPrompt();
            return;
        }

        // --- PRINT ---
        if (tok == CasioTokenizer.TOK_PRINT) {
            advance(); // consume PRINT
            if (peekType() == CasioTokenizer.TOK_STRING) {
                String str = advance().text;
                outputBuffer.append(str).append("\n");
            } else {
                double val = parseExpression();
                outputBuffer.append(formatNumber(val)).append("\n");
            }
            lastStatus = memoryManager.getPrompt();
            return;
        }

        // --- Variable assignment / Arrow storage / Expression ---
        // Example: 10 → A, or A = 10, or calculation: 5 + 3
        double exprVal = parseExpression();

        if (peekType() == CasioTokenizer.TOK_ARROW) {
            advance(); // consume →
            if (peekType() == CasioTokenizer.TOK_IDENT) {
                String varName = advance().text;
                char v = varName.toUpperCase().charAt(0);
                setVariable(v, exprVal);
            }
        } else if (peekType() == CasioTokenizer.TOK_EQUAL) {
            // Already parsed left as identifier if was variable
            // For standard assignment handled in expression
        } else {
            // Direct expression evaluation (e.g. calculator display)
            outputBuffer.append(formatNumber(exprVal)).append("\n");
        }
        lastStatus = memoryManager.getPrompt();
    }

    // --- Expression Grammar (Double-precision) ---

    private double parseExpression() {
        double left = parseTerm();

        while (true) {
            int tok = peekType();
            if (tok == CasioTokenizer.TOK_PLUS) {
                advance();
                double right = parseTerm();
                left = left + right;
            } else if (tok == CasioTokenizer.TOK_MINUS) {
                advance();
                double right = parseTerm();
                left = left - right;
            } else {
                return left;
            }
        }
    }

    private double parseTerm() {
        double left = parsePower();

        while (true) {
            int tok = peekType();
            if (tok == CasioTokenizer.TOK_STAR) {
                advance();
                double right = parsePower();
                left = left * right;
            } else if (tok == CasioTokenizer.TOK_SLASH) {
                advance();
                double right = parsePower();
                if (right == 0.0) {
                    throw new RuntimeException("Division by zero");
                }
                left = left / right;
            } else {
                return left;
            }
        }
    }

    private double parsePower() {
        double base = parseUnary();
        if (peekType() == CasioTokenizer.TOK_POWER) {
            advance();
            double exp = parsePower(); // right-associative
            return Math.pow(base, exp);
        }
        return base;
    }

    private double parseUnary() {
        int tok = peekType();
        if (tok == CasioTokenizer.TOK_MINUS) {
            advance();
            return -parseUnary();
        } else if (tok == CasioTokenizer.TOK_PLUS) {
            advance();
            return parseUnary();
        }
        return parsePrimary();
    }

    private double parsePrimary() {
        int tok = peekType();

        // Number literal
        if (tok == CasioTokenizer.TOK_NUMBER) {
            CasioTokenizer.Token t = advance();
            try {
                return Double.parseDouble(t.text);
            } catch (NumberFormatException e) {
                return 0.0;
            }
        }

        // Functions: SQR, SIN, COS, TAN, ABS, LOG, LN, EXP, RND
        if (isMathFunction(tok)) {
            advance();
            double arg = parsePrimary();
            return applyMathFunction(tok, arg);
        }

        // Parentheses ( expr )
        if (tok == CasioTokenizer.TOK_LPAREN) {
            advance();
            double val = parseExpression();
            if (peekType() == CasioTokenizer.TOK_RPAREN) {
                advance();
            }
            return val;
        }

        // Identifier (Variable)
        if (tok == CasioTokenizer.TOK_IDENT) {
            CasioTokenizer.Token t = advance();
            char varChar = t.text.toUpperCase().charAt(0);

            // Check if followed by = (e.g. A = 5)
            if (peekType() == CasioTokenizer.TOK_EQUAL) {
                advance(); // consume =
                double val = parseExpression();
                setVariable(varChar, val);
                return val;
            }

            return getVariable(varChar);
        }

        return 0.0;
    }

    private boolean isMathFunction(int tok) {
        return tok == CasioTokenizer.TOK_SQR || tok == CasioTokenizer.TOK_SIN ||
               tok == CasioTokenizer.TOK_COS || tok == CasioTokenizer.TOK_TAN ||
               tok == CasioTokenizer.TOK_ABS || tok == CasioTokenizer.TOK_LOG ||
               tok == CasioTokenizer.TOK_LN  || tok == CasioTokenizer.TOK_EXP ||
               tok == CasioTokenizer.TOK_RND || tok == CasioTokenizer.TOK_SGN;
    }

    private double applyMathFunction(int tok, double arg) {
        switch (tok) {
            case CasioTokenizer.TOK_SQR: return Math.sqrt(arg);
            case CasioTokenizer.TOK_SIN: return Math.sin(Math.toRadians(arg)); // Degree mode default
            case CasioTokenizer.TOK_COS: return Math.cos(Math.toRadians(arg));
            case CasioTokenizer.TOK_TAN: return Math.tan(Math.toRadians(arg));
            case CasioTokenizer.TOK_ABS: return Math.abs(arg);
            case CasioTokenizer.TOK_LOG: return Math.log10(arg);
            case CasioTokenizer.TOK_LN:  return Math.log(arg);
            case CasioTokenizer.TOK_EXP: return Math.exp(arg);
            case CasioTokenizer.TOK_RND: return Math.random();
            case CasioTokenizer.TOK_SGN: return Math.signum(arg);
            default: return arg;
        }
    }

    private CasioTokenizer.Token advance() {
        if (pos < tokens.size()) {
            return tokens.get(pos++);
        }
        return new CasioTokenizer.Token(CasioTokenizer.TOK_EOF, "", 0, 0);
    }

    private int peekType() {
        if (tokens != null && pos < tokens.size()) {
            return tokens.get(pos).type;
        }
        return CasioTokenizer.TOK_EOF;
    }

    private String formatNumber(double val) {
        if (val == (long) val) {
            return String.format("%d", (long) val);
        }
        return String.valueOf(val);
    }
}