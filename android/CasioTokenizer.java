/**
 * CASIO BASIC Tokenizer for Android
 * Converts ASCII CASIO BASIC source into compact token stream
 *
 * Philosophy: Authentic CASIO calculators tokenize everything into 1-byte tokens.
 * This enables maximum performance and compact program storage.
 */

public class CasioTokenizer {

    // --- Token Types (matching CASIO's internal representation) ---

    public static final int TOK_EOF = 0;
    public static final int TOK_PLUS = 1;
    public static final int TOK_MINUS = 2;
    public static final int TOK_STAR = 3;
    public static final int TOK_SLASH = 4;
    public static final int TOK_POWER = 5;    // ^ (some CASIO use up-arrow)
    public static final int TOK_EQUAL = 6;    // = (assignment)
    public static final int TOK_ARROW = 7;    // → (storage, distinct from =)
    public static final int TOK_LPAREN = 8;   // (
    public static final int TOK_RPAREN = 9;   // )
    public static final int TOK_COMMA = 10;   // ,
    public static final int TOK_SIN = 11;
    public static final int TOK_COS = 12;
    public static final int TOK_TAN = 13;
    public static final int TOK_SQR = 14;     // √ or SQR
    public static final int TOK_ABS = 15;
    public static final int TOK_LOG = 16;     // LOG (base 10)
    public static final int TOK_LN = 17;      // LN (natural)
    public static final int TOK_EXP = 18;     // EXP
    public static final int TOK_RND = 19;
    public static final int TOK_SGN = 20;
    public static final int TOK_IDENT = 21;   // variable name (with type info)
    public static final int TOK_NUMBER = 22;  // numeric literal
    public static final int TOK_STRING = 23;  // string constant "text"
    public static final int TOK_ARROW_STO = 24; // → storage token (already TOK_ARROW)
    public static final int TOK_PRINT = 25;
    public static final int TOK_INPUT = 26;
    public static final int TOK_FOR = 27;
    public static final int TOK_NEXT = 28;
    public static final int TOK_GOTO = 29;
    public static final int TOK_GOSUB = 30;
    public static final int TOK_RETURN = 31;
    public static final int TOK_IF = 32;
    public static final int TOK_THEN = 33;
    public static final int TOK_TO = 34;
    public static final int TOK_STEP = 35;
    public static final int TOK_DIM = 36;
    public static final int TOK_CLEAR = 37;
    public static final int TOK_MODE = 38;
    public static final int TOK_COMPLEX = 39;
    public static final int TOK_BASEN = 40;

    // --- Keyword Mapping ---
    // Maps ASCII strings to token types
    // Sorted by length (longest first) to ensure correct matching

    private static final String[] KEYWORDS = {
        "SIN", "COS", "TAN", "ASN", "ACS", "ATN",  // trig
        "SINH", "COSH", "TANH",                       // hyperbolic
        "SQR", "ABS", "SGN", "LOG", "LN", "EXP", "RND",  // functions
        "PRINT", "INPUT", "FOR", "NEXT", "GOTO", "GOSUB", "RETURN",  // control
        "IF", "THEN", "TO", "STEP", "DIM", "CLEAR", "MODE",  // statements
        "COMPLEX", "BASEN", "RUN", "STOP"              // special
    };

    // Token type for each keyword (index-matched to KEYWORDS above)
    // These MUST match the TOK_* constants above
    private static final int[] TOK_TYPES = {
        TOK_SIN, TOK_COS, TOK_TAN, TOK_SIN, TOK_COS, TOK_TAN,  // ASN, ACS, ATN ignored or mapped
        TOK_SIN, TOK_COS, TOK_TAN,  // SINH, COSH, TANH - could map to SIN/COS/TAN with flag
        TOK_SQR, TOK_ABS, TOK_SGN, TOK_LOG, TOK_LN, TOK_EXP, TOK_RND,  // SQR, ABS, SGN, LOG, LN, EXP, RND
        TOK_PRINT, TOK_INPUT, TOK_FOR, TOK_NEXT, TOK_GOTO, TOK_GOSUB, TOK_RETURN,
        TOK_IF, TOK_THEN, TOK_TO, TOK_STEP, TOK_DIM, TOK_CLEAR, TOK_MODE, TOK_COMPLEX, TOK_BASEN,
        TOK_EOF, TOK_EOF  // RUN, STOP - handled elsewhere
    };

    // Keyword -> token type lookup
    private static final java.util.HashMap<String, Integer> keywordMap;

    static {
        keywordMap = new java.util.HashMap<>();
        for (int i = 0; i < KEYWORDS.length; i++) {
            keywordMap.put(KEYWORDS[i], TOK_TYPES[i]);
        }
        // Also map lowercase
        for (String kw : KEYWORDS) {
            keywordMap.put(kw.toLowerCase(), TOK_TYPES[i]); // simplified
        }
    }

    // --- Arrow storage mapping ---
    // CASIO uses → (right arrow, U+2192) for variable storage
    // A → B stores into B, distinct from A = B

    private static final char ARROW_CHAR = '→'; // right arrow

    // --- Tokenizer State ---
    private String source;
    private int pos;
    private int line;
    private int column;

    public CasioTokenizer() {
        this.pos = 0;
        this.line = 1;
        this.column = 1;
    }

    /**
     * Tokenize a CASIO BASIC source string
     * @param source The BASIC source code
     * @return Array of token types
     */
    public int[] tokenize(String source) {
        this.source = source;
        this.pos = 0;
        this.line = 1;
        this.column = 1;

        java.util.ArrayList<Integer> tokens = new java.util.ArrayList<>();

        while (pos < source.length()) {
            char ch = source.charAt(pos);

            // Handle newline
            if (ch == '\n') {
                tokens.add(null); // placeholder for line tracking, or TOK_EOF handling
                line++;
                column = 1;
                pos++;
                continue;
            }

            // Handle whitespace (skip but track column)
            if (ch == ' ' || ch == '\t') {
                column++;
                pos++;
                continue;
            }

            // Handle right arrow (→) for storage
            if (ch == '→') {
                tokens.add(TOK_ARROW);
                column += 1; // arrow is 1 char visually
                pos++;
                continue;
            }

            // Handle numbers
            if (Character.isDigit(ch) || (ch == '.' && pos + 1 < source.length() && Character.isDigit(source.charAt(pos + 1)))) {
                int[] numTok = readNumber();
                // Add number token(s)
                for (int v : numTok) {
                    tokens.add(v);
                }
                continue;
            }

            // Handle strings "text"
            if (ch == '"') {
                String str = readString();
                tokens.add(TOK_STRING);
                // Could also store the string value separately
                column += str.length() + 2; // include quotes
                pos++;
                continue;
            }

            // Handle identifiers and keywords
            if (Character.isLetter(ch) || ch == '_') {
                String word = readIdentifier();
                Integer tokType = keywordMap.get(word.toUpperCase());
                if (tokType != null) {
                    tokens.add(tokType);
                } else {
                    // Unknown identifier - treat as variable
                    tokens.add(TOK_IDENT);
                    // Store name separately or handle in parser
                }
                column += word.length();
                pos++;
                continue;
            }

            // Single-character operators
            switch (ch) {
                case '+': tokens.add(TOK_PLUS); break;
                case '-': tokens.add(TOK_MINUS); break;
                case '*': tokens.add(TOK_STAR); break;
                case '/': tokens.add(TOK_SLASH); break;
                case '^': tokens.add(TOK_POWER); break;
                case '=': tokens.add(TOK_EQUAL); break;
                case '(': tokens.add(TOK_LPAREN); break;
                case ')': tokens.add(TOK_RPAREN); break;
                case ',': tokens.add(TOK_COMMA); break;
                case '\r': // carriage return, skip
                    pos++;
                    continue;
                default:
                    // Illegal character
                    throw new RuntimeException(
                        "Illegal character '" + ch + "' at line " + line + ", column " + column
                    );
            }
            column++;
            pos++;
        }

        // Add EOF
        tokens.add(TOK_EOF);

        // Convert to primitive array
        int[] result = new int[tokens.size()];
        for (int i = 0; i < result.length; i++) {
            result[i] = tokens.get(i);
        }
        return result;
    }

    /** Read a numeric literal, return consumed values */
    private int[] readNumber() {
        int startCol = column;
        StringBuilder num = new StringBuilder();
        boolean hasDot = false;

        while (pos < source.length()) {
            char ch = source.charAt(pos);
            if (Character.isDigit(ch)) {
                num.append(ch);
                column++;
                pos++;
            } else if (ch == '.' && !hasDot && pos + 1 < source.length() && Character.isDigit(source.charAt(pos + 1))) {
                hasDot = true;
                num.append(ch);
                column++;
                pos++;
            } else {
                break;
            }
        }

        // Parse as int or float
        int[] result = new int[2]; // [tokenType, valueEncoded]
        String numStr = num.toString();

        if (numStr.contains(".")) {
            result[0] = TOK_NUMBER; // we'll use TOK_NUMBER for both, parser distinguishes
            try {
                result[1] = (int) Float.parseFloat(numStr);
            } catch (NumberFormatException e) {
                result[1] = 0;
            }
        } else {
            result[0] = TOK_NUMBER;
            try {
                result[1] = Integer.parseInt(numStr);
            } catch (NumberFormatException e) {
                result[1] = 0;
            }
        }

        return result;
    }

    /** Read a string literal "text" */
    private String readString() {
        StringBuilder sb = new StringBuilder();
        pos++; // skip opening quote
        column++;

        while (pos < source.length()) {
            char ch = source.charAt(pos);
            if (ch == '"') {
                pos++; // skip closing quote
                column++;
                break;
            }
            sb.append(ch);
            column++;
            pos++;
        }

        return sb.toString();
    }

    /** Read an identifier (variable name or keyword) */
    private String readIdentifier() {
        StringBuilder sb = new StringBuilder();
        column++;
        pos++;

        while (pos < source.length()) {
            char ch = source.charAt(pos);
            if (Character.isLetterOrDigit(ch) || ch == '_') {
                sb.append(ch);
                column++;
                pos++;
            } else {
                break;
            }
        }

        return sb.toString();
    }

    /**
     * Get human-readable token name
     * @param token token type integer
     * @return descriptive name
     */
    public static String tokenToString(int token) {
        switch (token) {
            case TOK_EOF: return "EOF";
            case TOK_PLUS: return "PLUS (+)";
            case TOK_MINUS: return "MINUS (-)";
            case TOK_STAR: return "STAR (*)";
            case TOK_SLASH: return "SLASH (/)";
            case TOK_POWER: return "POWER (^)";
            case TOK_EQUAL: return "EQUAL (=)";
            case TOK_ARROW: return "ARROW (→)";
            case TOK_LPAREN: return "LPAREN (()";
            case TOK_RPAREN: return "RPAREN ())";
            case TOK_COMMA: return "COMMA (,)";
            case TOK_SIN: return "SIN";
            case TOK_COS: return "COS";
            case TOK_TAN: return "TAN";
            case TOK_SQR: return "SQR";
            case TOK_ABS: return "ABS";
            case TOK_LOG: return "LOG";
            case TOK_LN: return "LN";
            case TOK_EXP: return "EXP";
            case TOK_RND: return "RND";
            case TOK_SGN: return "SGN";
            case TOK_IDENT: return "IDENT (variable)";
            case TOK_NUMBER: return "NUMBER";
            case TOK_STRING: return "STRING";
            case TOK_PRINT: return "PRINT";
            case TOK_INPUT: return "INPUT";
            case TOK_FOR: return "FOR";
            case TOK_NEXT: return "NEXT";
            case TOK_GOTO: return "GOTO";
            case TOK_GOSUB: return "GOSUB";
            case TOK_RETURN: return "RETURN";
            case TOK_IF: return "IF";
            case TOK_THEN: return "THEN";
            case TOK_TO: return "TO";
            case TOK_STEP: return "STEP";
            case TOK_DIM: return "DIM";
            case TOK_CLEAR: return "CLEAR";
            case TOK_MODE: return "MODE";
            case TOK_COMPLEX: return "COMPLEX";
            case TOK_BASEN: return "BASE-N";
            default: return "UNKNOWN(" + token + ")";
        }
    }
}