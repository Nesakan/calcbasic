import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

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

    // --- FA-6 Cassette Interface & Memory Management Tokens ---
    public static final int TOK_SAVE = 41;
    public static final int TOK_LOAD = 42;
    public static final int TOK_VERIFY = 43;
    public static final int TOK_ALL = 44;
    public static final int TOK_NEW = 45;

    // --- Detailed Token Representation ---
    public static class Token {
        public final int type;
        public final String text;
        public final int line;
        public final int column;

        public Token(int type, String text, int line, int column) {
            this.type = type;
            this.text = text != null ? text : "";
            this.line = line;
            this.column = column;
        }

        @Override
        public String toString() {
            return tokenToString(type) + (!text.isEmpty() ? "('" + text + "')" : "");
        }
    }

    // --- Keyword Mapping ---
    private static final String[] KEYWORDS = {
        "SIN", "COS", "TAN", "ASN", "ACS", "ATN",  // trig
        "SINH", "COSH", "TANH",                       // hyperbolic
        "SQR", "ABS", "SGN", "LOG", "LN", "EXP", "RND",  // functions
        "PRINT", "INPUT", "FOR", "NEXT", "GOTO", "GOSUB", "RETURN",  // control
        "IF", "THEN", "TO", "STEP", "DIM", "CLEAR", "MODE",  // statements
        "COMPLEX", "BASEN", "RUN", "STOP",             // special
        "SAVE", "LOAD", "VERIFY", "ALL", "NEW"         // FA-6 / Memory
    };

    private static final int[] TOK_TYPES = {
        TOK_SIN, TOK_COS, TOK_TAN, TOK_SIN, TOK_COS, TOK_TAN,
        TOK_SIN, TOK_COS, TOK_TAN,
        TOK_SQR, TOK_ABS, TOK_SGN, TOK_LOG, TOK_LN, TOK_EXP, TOK_RND,
        TOK_PRINT, TOK_INPUT, TOK_FOR, TOK_NEXT, TOK_GOTO, TOK_GOSUB, TOK_RETURN,
        TOK_IF, TOK_THEN, TOK_TO, TOK_STEP, TOK_DIM, TOK_CLEAR, TOK_MODE,
        TOK_COMPLEX, TOK_BASEN, TOK_EOF, TOK_EOF,
        TOK_SAVE, TOK_LOAD, TOK_VERIFY, TOK_ALL, TOK_NEW
    };

    private static final HashMap<String, Integer> keywordMap;

    static {
        keywordMap = new HashMap<>();
        for (int i = 0; i < KEYWORDS.length; i++) {
            keywordMap.put(KEYWORDS[i], TOK_TYPES[i]);
            keywordMap.put(KEYWORDS[i].toLowerCase(), TOK_TYPES[i]);
        }
    }

    private static final char ARROW_CHAR = '→';

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
     * Tokenize a CASIO BASIC source string into integer token types
     */
    public int[] tokenize(String source) {
        List<Token> detailed = tokenizeDetailed(source);
        int[] result = new int[detailed.size()];
        for (int i = 0; i < detailed.size(); i++) {
            result[i] = detailed.get(i).type;
        }
        return result;
    }

    /**
     * Tokenize a CASIO BASIC source string into detailed Tokens with text values
     */
    public List<Token> tokenizeDetailed(String source) {
        this.source = source != null ? source : "";
        this.pos = 0;
        this.line = 1;
        this.column = 1;

        List<Token> tokens = new ArrayList<>();

        while (pos < this.source.length()) {
            char ch = this.source.charAt(pos);

            // Handle newline
            if (ch == '\n') {
                line++;
                column = 1;
                pos++;
                continue;
            }

            // Handle whitespace
            if (ch == ' ' || ch == '\t') {
                column++;
                pos++;
                continue;
            }

            // Handle right arrow (→) for storage
            if (ch == ARROW_CHAR || ch == '→') {
                tokens.add(new Token(TOK_ARROW, "→", line, column));
                column += 1;
                pos++;
                continue;
            }

            // Handle numbers
            if (Character.isDigit(ch) || (ch == '.' && pos + 1 < this.source.length() && Character.isDigit(this.source.charAt(pos + 1)))) {
                int startCol = column;
                String numStr = readNumberString();
                tokens.add(new Token(TOK_NUMBER, numStr, line, startCol));
                continue;
            }

            // Handle strings "text"
            if (ch == '"') {
                int startCol = column;
                String str = readString();
                tokens.add(new Token(TOK_STRING, str, line, startCol));
                continue;
            }

            // Handle identifiers and keywords
            if (Character.isLetter(ch) || ch == '_') {
                int startCol = column;
                String word = readIdentifier();
                Integer tokType = keywordMap.get(word.toUpperCase());
                if (tokType != null) {
                    tokens.add(new Token(tokType, word, line, startCol));
                } else {
                    tokens.add(new Token(TOK_IDENT, word, line, startCol));
                }
                continue;
            }

            // Single-character operators
            int startCol = column;
            switch (ch) {
                case '+': tokens.add(new Token(TOK_PLUS, "+", line, startCol)); break;
                case '-': tokens.add(new Token(TOK_MINUS, "-", line, startCol)); break;
                case '*': tokens.add(new Token(TOK_STAR, "*", line, startCol)); break;
                case '/': tokens.add(new Token(TOK_SLASH, "/", line, startCol)); break;
                case '^': tokens.add(new Token(TOK_POWER, "^", line, startCol)); break;
                case '=': tokens.add(new Token(TOK_EQUAL, "=", line, startCol)); break;
                case '(': tokens.add(new Token(TOK_LPAREN, "(", line, startCol)); break;
                case ')': tokens.add(new Token(TOK_RPAREN, ")", line, startCol)); break;
                case ',': tokens.add(new Token(TOK_COMMA, ",", line, startCol)); break;
                case '\r':
                    pos++;
                    continue;
                default:
                    throw new RuntimeException(
                        "Illegal character '" + ch + "' at line " + line + ", column " + column
                    );
            }
            column++;
            pos++;
        }

        // Add EOF
        tokens.add(new Token(TOK_EOF, "", line, column));
        return tokens;
    }

    /** Read a numeric literal string */
    private String readNumberString() {
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
        return num.toString();
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

    /** Read an identifier or keyword starting at current pos */
    private String readIdentifier() {
        StringBuilder sb = new StringBuilder();

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
            case TOK_IDENT: return "IDENT";
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
            case TOK_SAVE: return "SAVE";
            case TOK_LOAD: return "LOAD";
            case TOK_VERIFY: return "VERIFY";
            case TOK_ALL: return "ALL";
            case TOK_NEW: return "NEW";
            default: return "UNKNOWN(" + token + ")";
        }
    }
}