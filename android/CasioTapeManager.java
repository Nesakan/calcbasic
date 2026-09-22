import java.util.ArrayList;
import java.util.List;
import java.util.zip.CRC32;

/**
 * CasioTapeManager - FA-6 Cassette Interface Simulation for Casio Pocket Computers.
 *
 * Implements the SAVE, SAVE ALL, LOAD, LOAD ALL, and VERIFY behaviors,
 * including 8-character filename enforcement, device prefixes ("CAS1:"),
 * error handling (P0 error 0), and the exact compatibility matrix from the manual:
 *
 * +----------------------+------+-----------------+----------+---------------------+
 * | Saved with           | LOAD | LOAD "filename" | LOAD ALL | LOAD ALL "filename" |
 * +----------------------+------+-----------------+----------+---------------------+
 * | SAVE                 |  O   |        X        |    X     |          X          |
 * | SAVE "filename"      |  O   |        O        |    X     |          X          |
 * | SAVE ALL             |  X   |        X        |    O     |          X          |
 * | SAVE ALL "filename"  |  X   |        X        |    O     |          O          |
 * +----------------------+------+-----------------+----------+---------------------+
 */
public class CasioTapeManager {

    /**
     * Represents a single program record or bundle stored on a cassette tape.
     */
    public static class TapeRecord {
        private final String filename;  // Up to 8 chars, uppercase, empty string if unnamed
        private final boolean isAll;    // true if saved via SAVE ALL
        private final int sourceSlot;   // Slot where saved from (e.g. 0 for P0)
        private final String content;   // Content of single program (if !isAll)
        private final String[] allSlots;// All slots P0-P9 (if isAll)
        private final long checksum;    // CRC32 checksum for verification
        private final long timestamp;

        public TapeRecord(String filename, boolean isAll, int sourceSlot, String content, String[] allSlots) {
            this.filename = filename != null ? filename : "";
            this.isAll = isAll;
            this.sourceSlot = sourceSlot;
            this.content = content != null ? content : "";
            if (allSlots != null) {
                this.allSlots = new String[allSlots.length];
                for (int i = 0; i < allSlots.length; i++) {
                    this.allSlots[i] = allSlots[i] != null ? allSlots[i] : "";
                }
            } else {
                this.allSlots = null;
            }

            // Calculate CRC32 checksum
            CRC32 crc = new CRC32();
            if (isAll && this.allSlots != null) {
                for (String s : this.allSlots) {
                    crc.update(s.getBytes());
                }
            } else {
                crc.update(this.content.getBytes());
            }
            this.checksum = crc.getValue();
            this.timestamp = System.currentTimeMillis();
        }

        public String getFilename() { return filename; }
        public boolean isAll() { return isAll; }
        public int getSourceSlot() { return sourceSlot; }
        public String getContent() { return content; }
        public String[] getAllSlots() { return allSlots; }
        public long getChecksum() { return checksum; }
        public long getTimestamp() { return timestamp; }
        public boolean isNamed() { return !filename.isEmpty(); }
    }

    /**
     * Result of a VERIFY operation.
     */
    public static class VerifyResult {
        public final boolean success;
        public final String filename;
        public final boolean isAll;
        public final String searchDisplay; // e.g. "BASIC    B"
        public final String statusDisplay; // e.g. "Ready P0" or "P0 error 0"
        public final String message;

        public VerifyResult(boolean success, String filename, boolean isAll, String searchDisplay, String statusDisplay, String message) {
            this.success = success;
            this.filename = filename;
            this.isAll = isAll;
            this.searchDisplay = searchDisplay;
            this.statusDisplay = statusDisplay;
            this.message = message;
        }

        @Override
        public String toString() {
            return searchDisplay + "\n" + statusDisplay;
        }
    }

    /**
     * Exception thrown when tape operations violate compatibility or cannot be completed.
     */
    public static class CasioTapeException extends Exception {
        private final int slot;
        private final int errorCode;

        public CasioTapeException(int slot, int errorCode, String message) {
            super(message);
            this.slot = slot;
            this.errorCode = errorCode;
        }

        public int getSlot() { return slot; }
        public int getErrorCode() { return errorCode; }

        public String getDisplayError() {
            return "P" + slot + " error " + errorCode;
        }
    }

    private final List<TapeRecord> virtualTape;

    public CasioTapeManager() {
        this.virtualTape = new ArrayList<>();
    }

    /**
     * Clear all recorded contents on the virtual tape.
     */
    public void rewindAndEraseTape() {
        virtualTape.clear();
    }

    /**
     * Get the count of records on the virtual tape.
     */
    public int getRecordCount() {
        return virtualTape.size();
    }

    /**
     * Sanitize and format filename according to Casio rules:
     * - Strips "CAS1:" prefix if present.
     * - Trims whitespace and converts to uppercase.
     * - Caps length at 8 characters.
     */
    public static String sanitizeFilename(String filename) {
        if (filename == null) return "";
        String clean = filename.trim();
        if (clean.startsWith("\"") && clean.endsWith("\"") && clean.length() >= 2) {
            clean = clean.substring(1, clean.length() - 1);
        }
        if (clean.toUpperCase().startsWith("CAS1:")) {
            clean = clean.substring(5);
        }
        clean = clean.trim().toUpperCase();
        if (clean.length() > 8) {
            clean = clean.substring(0, 8);
        }
        return clean;
    }

    /**
     * Format the 16-character search indicator seen on Casio LCDs (e.g. "BASIC    B").
     */
    public static String formatSearchIndicator(String filename) {
        String name = sanitizeFilename(filename);
        if (name.isEmpty()) name = "PROGRAM";
        return String.format("%-8s B", name);
    }

    /**
     * SAVE: Saves the active program area onto the cassette tape.
     * @param filename Optional filename (up to 8 characters).
     * @param slot Active slot number (0-9).
     * @param code Program text.
     * @return Formatted message (e.g. "Ready P0").
     */
    public String save(String filename, int slot, String code) {
        String cleanName = sanitizeFilename(filename);
        TapeRecord record = new TapeRecord(cleanName, false, slot, code, null);
        virtualTape.add(record);
        return "Ready P" + slot;
    }

    /**
     * SAVE ALL: Saves the entire contents of all program areas (P0-P9) onto the cassette tape.
     * @param filename Optional filename (up to 8 characters).
     * @param slot Active slot number (0-9).
     * @param allSlots Array of 10 program texts.
     * @return Formatted message (e.g. "Ready P0").
     */
    public String saveAll(String filename, int slot, String[] allSlots) {
        String cleanName = sanitizeFilename(filename);
        TapeRecord record = new TapeRecord(cleanName, true, slot, null, allSlots);
        virtualTape.add(record);
        return "Ready P" + slot;
    }

    /**
     * LOAD: Loads a single program area from cassette tape into memory.
     *
     * Compatibility:
     * - LOAD (no name): Can load SAVE (unnamed) or SAVE "filename".
     * - LOAD "filename": Can load SAVE "filename" ONLY.
     * - Cannot load any program saved with SAVE ALL.
     */
    public String load(String filename, int targetSlot) throws CasioTapeException {
        String cleanName = sanitizeFilename(filename);
        boolean hasName = !cleanName.isEmpty();

        TapeRecord match = findRecord(cleanName, hasName, false);

        if (match == null) {
            throw new CasioTapeException(targetSlot, 0, "File not found: " + (hasName ? cleanName : "<unnamed>"));
        }

        // Check compatibility matrix
        if (match.isAll()) {
            // Cannot load an ALL save with single LOAD
            throw new CasioTapeException(targetSlot, 0, "Incompatible: Cannot load SAVE ALL program with LOAD");
        }

        if (hasName && !match.isNamed()) {
            // LOAD "filename" cannot load an unnamed SAVE
            throw new CasioTapeException(targetSlot, 0, "Incompatible: Cannot load unnamed SAVE with specified filename");
        }

        return match.getContent();
    }

    /**
     * LOAD ALL: Loads all program areas (P0-P9) from cassette tape into memory.
     *
     * Compatibility:
     * - LOAD ALL (no name): Can load SAVE ALL (unnamed) or SAVE ALL "filename".
     * - LOAD ALL "filename": Can load SAVE ALL "filename" ONLY.
     * - Cannot load any program saved with single SAVE.
     */
    public String[] loadAll(String filename, int targetSlot) throws CasioTapeException {
        String cleanName = sanitizeFilename(filename);
        boolean hasName = !cleanName.isEmpty();

        TapeRecord match = findRecord(cleanName, hasName, true);

        if (match == null) {
            throw new CasioTapeException(targetSlot, 0, "File not found: " + (hasName ? cleanName : "<unnamed>"));
        }

        // Check compatibility matrix
        if (!match.isAll()) {
            // Cannot load a single save with LOAD ALL
            throw new CasioTapeException(targetSlot, 0, "Incompatible: Cannot load single SAVE with LOAD ALL");
        }

        if (hasName && !match.isNamed()) {
            // LOAD ALL "filename" cannot load an unnamed SAVE ALL
            throw new CasioTapeException(targetSlot, 0, "Incompatible: Cannot load unnamed SAVE ALL with specified filename");
        }

        return match.getAllSlots();
    }

    /**
     * VERIFY: Verifies whether the program saved using SAVE or SAVE ALL matches computer memory.
     * The command automatically determines whether the program being checked was saved using
     * SAVE or SAVE ALL.
     *
     * @param filename Filename to verify (can include "CAS1:" prefix).
     * @param activeSlot Current active slot (e.g. 0).
     * @param activeMemoryCode Current program code in active slot.
     * @param allMemorySlots Current program code in all 10 slots.
     */
    public VerifyResult verify(String filename, int activeSlot, String activeMemoryCode, String[] allMemorySlots) {
        String cleanName = sanitizeFilename(filename);
        String searchDisp = formatSearchIndicator(cleanName);

        if (cleanName.isEmpty()) {
            return new VerifyResult(false, cleanName, false, searchDisp,
                    "P" + activeSlot + " error 0", "Filename is required for VERIFY");
        }

        // Search tape for specified program
        TapeRecord match = null;
        for (int i = virtualTape.size() - 1; i >= 0; i--) {
            TapeRecord rec = virtualTape.get(i);
            if (rec.getFilename().equalsIgnoreCase(cleanName)) {
                match = rec;
                break;
            }
        }

        if (match == null) {
            // Program not found on tape
            return new VerifyResult(false, cleanName, false, searchDisp,
                    "P" + activeSlot + " error 0", "Program not found on tape");
        }

        // Compare contents based on whether it was SAVE or SAVE ALL
        boolean matches = false;
        if (match.isAll()) {
            // Check all slots
            if (allMemorySlots != null && match.getAllSlots() != null) {
                matches = true;
                for (int i = 0; i < 10 && i < allMemorySlots.length && i < match.getAllSlots().length; i++) {
                    String mem = allMemorySlots[i] != null ? allMemorySlots[i].trim() : "";
                    String tape = match.getAllSlots()[i] != null ? match.getAllSlots()[i].trim() : "";
                    if (!mem.equals(tape)) {
                        matches = false;
                        break;
                    }
                }
            }
        } else {
            // Check active slot content
            String mem = activeMemoryCode != null ? activeMemoryCode.trim() : "";
            String tape = match.getContent() != null ? match.getContent().trim() : "";
            matches = mem.equals(tape);
        }

        if (matches) {
            return new VerifyResult(true, cleanName, match.isAll(), searchDisp,
                    "Ready P" + activeSlot, "Verification complete");
        } else {
            return new VerifyResult(false, cleanName, match.isAll(), searchDisp,
                    "P" + activeSlot + " error 0", "Contents in memory do not match tape");
        }
    }

    /**
     * Search virtual tape from newest to oldest for a matching record.
     */
    private TapeRecord findRecord(String cleanName, boolean hasName, boolean preferAll) {
        if (hasName) {
            for (int i = virtualTape.size() - 1; i >= 0; i--) {
                TapeRecord rec = virtualTape.get(i);
                if (rec.getFilename().equalsIgnoreCase(cleanName)) {
                    return rec;
                }
            }
            return null;
        } else {
            // Find most recent record with matching isAll flag
            for (int i = virtualTape.size() - 1; i >= 0; i--) {
                TapeRecord rec = virtualTape.get(i);
                if (rec.isAll() == preferAll) {
                    return rec;
                }
            }
            // Fallback to any most recent record
            if (!virtualTape.isEmpty()) {
                return virtualTape.get(virtualTape.size() - 1);
            }
            return null;
        }
    }
}
