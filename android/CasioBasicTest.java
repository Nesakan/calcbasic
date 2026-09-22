/**
 * Test harness for CASIO BASIC tokenizer and parser
 * Run via: java -cp . CasioBasicTest
 *
 * Demonstrates tokenization of CASIO BASIC programs
 */
public class CasioBasicTest {

    public static void main(String[] args) {
        System.out.println("=== CASIO BASIC Tokenizer Test ===\n");

        // Test 1: Tokenize simple program with PRINT
        System.out.println("Test 1: Tokenize '10 PRINT A'");
        String program1 = "10 PRINT A";
        int[] tokens1 = tokenizeProgram(program1);
        printTokens(program1, tokens1);
        System.out.println();

        // Test 2: Tokenize assignment with arrow storage
        System.out.println("Test 2: Tokenize '10 A → 10'");
        String program2 = "10 A → 10";
        int[] tokens2 = tokenizeProgram(program2);
        printTokens(program2, tokens2);
        System.out.println();

        // Test 3: Tokenize math expression with SQR
        System.out.println("Test 3: Tokenize '10 SQR 16'");
        String program3 = "10 SQR 16";
        int[] tokens3 = tokenizeProgram(program3);
        printTokens(program3, tokens3);
        System.out.println();

        // Test 4: Tokenize FOR/NEXT
        System.out.println("Test 4: Tokenize '10 FOR I = 1 TO 10'");
        String program4 = "10 FOR I = 1 TO 10";
        int[] tokens4 = tokenizeProgram(program4);
        printTokens(program4, tokens4);
        System.out.println();

        // Test 5: Full program with multiple statements
        System.out.println("Test 5: Full program");
        String fullProgram = "10 PRINT \"HELLO\"\n20 INPUT A\n30 LET B = SQR 16\n40 PRINT B\n50 END";
        int[] fullTokens = tokenizeProgram(fullProgram);
        printTokens(fullProgram, fullTokens);
        System.out.println("\n=== All Tokenizer Tests Complete ===");
    }

    /** Tokenize a CASIO BASIC program string */
    public static int[] tokenizeProgram(String source) {
        CasioTokenizer tok = new CasioTokenizer();
        return tok.tokenize(source);
    }

    /** Print program source and its tokens in human-readable format */
    public static void printTokens(String source, int[] tokens) {
        System.out.println("  Source: '" + escapeSource(source) + "'");
        System.out.println("  Tokens [" + tokens.length + "]:");
        for (int i = 0; i < tokens.length; i++) {
            String name = CasioTokenizer.tokenToString(tokens[i]);
            // For NUMBER tokens, show a brief indicator
            if (tokens[i] == CasioTokenizer.TOK_NUMBER) {
                name = "NUM";
            }
            System.out.println("    " + name);
        }
        System.out.println();
    }

    /** Escape special chars in source for display */
    private static String escapeSource(String s) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\n') {
                sb.append("\\n");
            } else if (c == '\"') {
                sb.append("\\\"");
            } else if (c == '→') {
                sb.append("\\arrow");
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }
}