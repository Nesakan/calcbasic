/**
 * CasioTapeTest - Comprehensive test suite for Casio Memory Areas (P0-P9)
 * and FA-6 Cassette Interface (SAVE, LOAD, VERIFY, and Compatibility Matrix).
 */
public class CasioTapeTest {

    private static int testsPassed = 0;
    private static int testsFailed = 0;

    public static void main(String[] args) {
        System.out.println("=================================================");
        System.out.println("   CASIO BASIC FA-6 TAPE & MEMORY TEST SUITE     ");
        System.out.println("=================================================\n");

        testProgramAreas();
        testDirectCommands();
        testCompatibilityMatrixRow1_SaveUnnamed();
        testCompatibilityMatrixRow2_SaveNamed();
        testCompatibilityMatrixRow3_SaveAllUnnamed();
        testCompatibilityMatrixRow4_SaveAllNamed();
        testVerifySuccess();
        testVerifyPrefixCas1();
        testVerifyContentMismatchError();
        testFilenameTruncation();

        System.out.println("\n-------------------------------------------------");
        System.out.println("Results: " + testsPassed + " passed, " + testsFailed + " failed.");
        System.out.println("-------------------------------------------------");

        if (testsFailed > 0) {
            System.exit(1);
        }
    }

    private static void assertTrue(String name, boolean condition) {
        if (condition) {
            System.out.println("  [PASS] " + name);
            testsPassed++;
        } else {
            System.out.println("  [FAIL] " + name);
            testsFailed++;
        }
    }

    private static void assertEquals(String name, Object expected, Object actual) {
        if ((expected == null && actual == null) || (expected != null && expected.equals(actual))) {
            System.out.println("  [PASS] " + name);
            testsPassed++;
        } else {
            System.out.println("  [FAIL] " + name + " (Expected: '" + expected + "', Got: '" + actual + "')");
            testsFailed++;
        }
    }

    private static void testProgramAreas() {
        System.out.println("Test Group 1: Program Areas P0 through P9");
        CasioMemoryManager mem = new CasioMemoryManager();

        assertEquals("Default active slot is P0", 0, mem.getActiveSlot());
        assertEquals("Initial prompt is Ready P0", "Ready P0", mem.getPrompt());

        mem.setActiveSlot(5);
        assertEquals("Switch to P5", 5, mem.getActiveSlot());
        assertEquals("Prompt updates to Ready P5", "Ready P5", mem.getPrompt());

        mem.setProgram(5, "10 PRINT \"IN P5\"");
        assertEquals("Get program in P5", "10 PRINT \"IN P5\"", mem.getProgram(5));
        assertEquals("P0 remains empty", "", mem.getProgram(0));

        mem.clearSlot(5);
        assertTrue("Clear slot 5 makes it empty", mem.isSlotEmpty(5));

        // Test bounds
        try {
            mem.setActiveSlot(10);
            assertTrue("Slot 10 should throw", false);
        } catch (IllegalArgumentException e) {
            assertTrue("Slot 10 out of bounds caught", true);
        }
        System.out.println();
    }

    private static void testDirectCommands() {
        System.out.println("Test Group 2: Direct Mode Commands");
        CasioParser parser = new CasioParser();

        assertEquals("Prompt initially", "Ready P0", parser.executeDirect(""));
        assertEquals("Switch slot via P3", "Ready P3", parser.executeDirect("P3"));
        assertEquals("Active slot is 3", 3, parser.getMemoryManager().getActiveSlot());

        // Arithmetic calculation
        String calc = parser.executeDirect("PRINT 10 + 20 * 3");
        assertEquals("Direct PRINT arithmetic", "70\n", calc);

        // Arrow storage
        parser.executeDirect("42 → A");
        assertEquals("Arrow storage 42 → A", 42.0, parser.getVariable('A'));

        // Switch back to P0
        parser.executeDirect("P0");
        assertEquals("Switch back to P0", 0, parser.getMemoryManager().getActiveSlot());
        System.out.println();
    }

    private static void testCompatibilityMatrixRow1_SaveUnnamed() {
        System.out.println("Test Group 3: Matrix Row 1 - SAVE (unnamed)");
        CasioTapeManager tape = new CasioTapeManager();
        tape.save(null, 0, "10 PRINT \"UNNAMED\"");

        // 1. LOAD (unnamed) -> OK
        try {
            String loaded = tape.load(null, 0);
            assertEquals("LOAD unnamed can load SAVE unnamed", "10 PRINT \"UNNAMED\"", loaded);
        } catch (Exception e) {
            assertTrue("LOAD unnamed threw exception: " + e.getMessage(), false);
        }

        // 2. LOAD "TEST" -> X (must fail)
        try {
            tape.load("TEST", 0);
            assertTrue("LOAD 'TEST' on unnamed SAVE should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD 'TEST' on unnamed SAVE correctly rejected", true);
        }

        // 3. LOAD ALL -> X (must fail)
        try {
            tape.loadAll(null, 0);
            assertTrue("LOAD ALL on single SAVE should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD ALL on single SAVE correctly rejected", true);
        }

        // 4. LOAD ALL "TEST" -> X (must fail)
        try {
            tape.loadAll("TEST", 0);
            assertTrue("LOAD ALL 'TEST' on single SAVE should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD ALL 'TEST' on single SAVE correctly rejected", true);
        }
        System.out.println();
    }

    private static void testCompatibilityMatrixRow2_SaveNamed() {
        System.out.println("Test Group 4: Matrix Row 2 - SAVE \"BASIC\"");
        CasioTapeManager tape = new CasioTapeManager();
        tape.save("BASIC", 0, "10 PRINT \"HELLO WORLD\"");

        // 1. LOAD (unnamed) -> OK
        try {
            String loaded = tape.load(null, 0);
            assertEquals("LOAD unnamed can load SAVE 'BASIC'", "10 PRINT \"HELLO WORLD\"", loaded);
        } catch (Exception e) {
            assertTrue("LOAD unnamed failed: " + e.getMessage(), false);
        }

        // 2. LOAD "BASIC" -> OK
        try {
            String loaded = tape.load("BASIC", 0);
            assertEquals("LOAD 'BASIC' can load SAVE 'BASIC'", "10 PRINT \"HELLO WORLD\"", loaded);
        } catch (Exception e) {
            assertTrue("LOAD 'BASIC' failed: " + e.getMessage(), false);
        }

        // 3. LOAD ALL -> X (must fail)
        try {
            tape.loadAll(null, 0);
            assertTrue("LOAD ALL on SAVE 'BASIC' should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD ALL on SAVE 'BASIC' correctly rejected", true);
        }

        // 4. LOAD ALL "BASIC" -> X (must fail)
        try {
            tape.loadAll("BASIC", 0);
            assertTrue("LOAD ALL 'BASIC' on single SAVE should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD ALL 'BASIC' on single SAVE correctly rejected", true);
        }
        System.out.println();
    }

    private static void testCompatibilityMatrixRow3_SaveAllUnnamed() {
        System.out.println("Test Group 5: Matrix Row 3 - SAVE ALL (unnamed)");
        CasioTapeManager tape = new CasioTapeManager();
        String[] progs = new String[10];
        progs[0] = "10 REM P0";
        progs[1] = "20 REM P1";
        tape.saveAll(null, 0, progs);

        // 1. LOAD -> X (must fail)
        try {
            tape.load(null, 0);
            assertTrue("LOAD on SAVE ALL unnamed should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD on SAVE ALL unnamed correctly rejected", true);
        }

        // 2. LOAD "TEST" -> X (must fail)
        try {
            tape.load("TEST", 0);
            assertTrue("LOAD 'TEST' on SAVE ALL unnamed should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD 'TEST' on SAVE ALL unnamed correctly rejected", true);
        }

        // 3. LOAD ALL -> OK
        try {
            String[] loaded = tape.loadAll(null, 0);
            assertEquals("LOAD ALL loaded P0", "10 REM P0", loaded[0]);
            assertEquals("LOAD ALL loaded P1", "20 REM P1", loaded[1]);
        } catch (Exception e) {
            assertTrue("LOAD ALL unnamed failed: " + e.getMessage(), false);
        }

        // 4. LOAD ALL "TEST" -> X (must fail)
        try {
            tape.loadAll("TEST", 0);
            assertTrue("LOAD ALL 'TEST' on unnamed SAVE ALL should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD ALL 'TEST' on unnamed SAVE ALL correctly rejected", true);
        }
        System.out.println();
    }

    private static void testCompatibilityMatrixRow4_SaveAllNamed() {
        System.out.println("Test Group 6: Matrix Row 4 - SAVE ALL \"BACKUP\"");
        CasioTapeManager tape = new CasioTapeManager();
        String[] progs = new String[10];
        progs[0] = "10 PRINT \"ALL P0\"";
        tape.saveAll("BACKUP", 0, progs);

        // 1. LOAD -> X (must fail)
        try {
            tape.load(null, 0);
            assertTrue("LOAD on SAVE ALL named should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD on SAVE ALL named correctly rejected", true);
        }

        // 2. LOAD "BACKUP" -> X (must fail)
        try {
            tape.load("BACKUP", 0);
            assertTrue("LOAD 'BACKUP' on SAVE ALL named should fail", false);
        } catch (CasioTapeManager.CasioTapeException e) {
            assertTrue("LOAD 'BACKUP' on SAVE ALL named correctly rejected", true);
        }

        // 3. LOAD ALL -> OK
        try {
            String[] loaded = tape.loadAll(null, 0);
            assertEquals("LOAD ALL loaded P0 from BACKUP", "10 PRINT \"ALL P0\"", loaded[0]);
        } catch (Exception e) {
            assertTrue("LOAD ALL failed: " + e.getMessage(), false);
        }

        // 4. LOAD ALL "BACKUP" -> OK
        try {
            String[] loaded = tape.loadAll("BACKUP", 0);
            assertEquals("LOAD ALL 'BACKUP' loaded P0", "10 PRINT \"ALL P0\"", loaded[0]);
        } catch (Exception e) {
            assertTrue("LOAD ALL 'BACKUP' failed: " + e.getMessage(), false);
        }
        System.out.println();
    }

    private static void testVerifySuccess() {
        System.out.println("Test Group 7: VERIFY Command - Successful Match");
        CasioParser parser = new CasioParser();
        parser.getMemoryManager().setActiveProgram("10 PRINT \"OK\"");

        // Save
        parser.executeDirect("SAVE \"BASIC\"");

        // Verify
        String status = parser.executeDirect("VERIFY \"BASIC\"");
        assertEquals("VERIFY matches and returns Ready P0", "Ready P0", status);
        System.out.println();
    }

    private static void testVerifyPrefixCas1() {
        System.out.println("Test Group 8: VERIFY with 'CAS1:' Device Prefix");
        CasioParser parser = new CasioParser();
        parser.getMemoryManager().setActiveProgram("10 PRINT \"CASIO\"");
        parser.executeDirect("SAVE \"MYPROG\"");

        // Verify with CAS1:MYPROG
        String status = parser.executeDirect("VERIFY \"CAS1:MYPROG\"");
        assertEquals("VERIFY with CAS1: prefix verifies successfully", "Ready P0", status);
        System.out.println();
    }

    private static void testVerifyContentMismatchError() {
        System.out.println("Test Group 9: VERIFY Command - Error Reporting");
        CasioParser parser = new CasioParser();
        parser.getMemoryManager().setActiveProgram("10 PRINT \"ORIGINAL\"");
        parser.executeDirect("SAVE \"BASIC\"");

        // Modify memory so it no longer matches the tape
        parser.getMemoryManager().setActiveProgram("10 PRINT \"TAMPERED\"");

        String status = parser.executeDirect("VERIFY \"BASIC\"");
        assertTrue("VERIFY content mismatch produces P0 error 0", status.contains("P0 error 0"));
        assertTrue("VERIFY content mismatch includes Ready P0", status.contains("Ready P0"));

        // Non-existent program
        String missing = parser.executeDirect("VERIFY \"NOTTHERE\"");
        assertTrue("VERIFY non-existent program produces P0 error 0", missing.contains("P0 error 0"));
        System.out.println();
    }

    private static void testFilenameTruncation() {
        System.out.println("Test Group 10: 8-Character Filename Rule");
        String sanitized = CasioTapeManager.sanitizeFilename("VERYLONGPROGRAMNAME");
        assertEquals("Filename capped at 8 characters", "VERYLONG", sanitized);

        String withCas1 = CasioTapeManager.sanitizeFilename("CAS1:CALCULATION");
        assertEquals("CAS1: stripped and capped at 8 characters", "CALCULAT", withCas1);
        System.out.println();
    }
}
