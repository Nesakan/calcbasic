/**
 * CasioMemoryManager - JavaScript port of the P0-P9 memory subsystem
 */
class CasioMemoryManager {
    constructor() {
        this.TOTAL_SLOTS = 10;
        this.programSlots = new Array(this.TOTAL_SLOTS).fill("");
        this.activeSlot = 0; // P0
    }

    getActiveSlot() {
        return this.activeSlot;
    }

    setActiveSlot(slot) {
        if (slot < 0 || slot >= this.TOTAL_SLOTS) {
            throw new Error(`Invalid slot: P${slot}`);
        }
        this.activeSlot = slot;
    }

    getPrompt() {
        return `Ready P${this.activeSlot}`;
    }

    getProgram(slot) {
        if (slot < 0 || slot >= this.TOTAL_SLOTS) return "";
        return this.programSlots[slot] || "";
    }

    setProgram(slot, code) {
        if (slot < 0 || slot >= this.TOTAL_SLOTS) return;
        this.programSlots[slot] = code || "";
    }

    getActiveProgram() {
        return this.programSlots[this.activeSlot] || "";
    }

    setActiveProgram(code) {
        this.programSlots[this.activeSlot] = code || "";
    }

    isSlotEmpty(slot) {
        return !this.programSlots[slot] || this.programSlots[slot].trim() === "";
    }

    clearSlot(slot) {
        if (slot >= 0 && slot < this.TOTAL_SLOTS) {
            this.programSlots[slot] = "";
        }
    }

    clearActiveSlot() {
        this.clearSlot(this.activeSlot);
    }

    clearAll() {
        this.programSlots.fill("");
    }

    getAllPrograms() {
        return [...this.programSlots];
    }

    setAllPrograms(programs) {
        if (!Array.isArray(programs)) return;
        for (let i = 0; i < this.TOTAL_SLOTS && i < programs.length; i++) {
            this.programSlots[i] = programs[i] || "";
        }
    }
}
