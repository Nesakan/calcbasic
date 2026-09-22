/**
 * CasioMemoryManager - Manages program areas P0 through P9 for Casio pocket computers.
 *
 * Casio pocket computers (such as FX-702P, FX-730P, PB-100 series with FA-6 interface)
 * partition user program memory into 10 discrete program areas labeled P0 through P9.
 */
public class CasioMemoryManager {

    public static final int TOTAL_SLOTS = 10; // P0 through P9

    private final String[] programSlots;
    private int activeSlot;

    public CasioMemoryManager() {
        this.programSlots = new String[TOTAL_SLOTS];
        for (int i = 0; i < TOTAL_SLOTS; i++) {
            this.programSlots[i] = "";
        }
        this.activeSlot = 0; // Default to P0
    }

    /**
     * Get the active program slot index (0 - 9).
     */
    public int getActiveSlot() {
        return activeSlot;
    }

    /**
     * Switch to a specific program area (P0 - P9).
     * @param slot Slot number 0 to 9.
     */
    public void setActiveSlot(int slot) {
        validateSlot(slot);
        this.activeSlot = slot;
    }

    /**
     * Get the prompt string for the active slot (e.g., "Ready P0").
     */
    public String getPrompt() {
        return "Ready P" + activeSlot;
    }

    /**
     * Get the program code in the specified slot.
     */
    public String getProgram(int slot) {
        validateSlot(slot);
        return programSlots[slot];
    }

    /**
     * Set the program code for the specified slot.
     */
    public void setProgram(int slot, String code) {
        validateSlot(slot);
        programSlots[slot] = code != null ? code : "";
    }

    /**
     * Get the program code currently in the active slot.
     */
    public String getActiveProgram() {
        return programSlots[activeSlot];
    }

    /**
     * Set the program code in the active slot.
     */
    public void setActiveProgram(String code) {
        programSlots[activeSlot] = code != null ? code : "";
    }

    /**
     * Check if a given slot is empty.
     */
    public boolean isSlotEmpty(int slot) {
        validateSlot(slot);
        return programSlots[slot].trim().isEmpty();
    }

    /**
     * Clear the specified program area (equivalent to Casio NEW command).
     */
    public void clearSlot(int slot) {
        validateSlot(slot);
        programSlots[slot] = "";
    }

    /**
     * Clear the active program area.
     */
    public void clearActiveSlot() {
        clearSlot(activeSlot);
    }

    /**
     * Clear all program areas P0 through P9 (equivalent to Casio NEW ALL command).
     */
    public void clearAll() {
        for (int i = 0; i < TOTAL_SLOTS; i++) {
            programSlots[i] = "";
        }
    }

    /**
     * Snapshot copy of all 10 program areas.
     */
    public String[] getAllPrograms() {
        String[] copy = new String[TOTAL_SLOTS];
        System.arraycopy(programSlots, 0, copy, 0, TOTAL_SLOTS);
        return copy;
    }

    /**
     * Load programs into all 10 program areas P0 through P9.
     */
    public void setAllPrograms(String[] programs) {
        if (programs == null) return;
        for (int i = 0; i < TOTAL_SLOTS && i < programs.length; i++) {
            programSlots[i] = programs[i] != null ? programs[i] : "";
        }
    }

    private void validateSlot(int slot) {
        if (slot < 0 || slot >= TOTAL_SLOTS) {
            throw new IllegalArgumentException("Invalid program area: P" + slot + " (must be P0 to P9)");
        }
    }
}
