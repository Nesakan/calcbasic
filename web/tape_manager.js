/**
 * CasioTapeManager - JavaScript implementation of the FA-6 Cassette Interface
 * Enforces the Page 67 Compatibility Matrix and saves to localStorage.
 */
class CasioTapeManager {
    constructor() {
        this.STORAGE_KEY = "casio_virtual_tape_records";
        this.records = this.loadFromStorage();
    }

    loadFromStorage() {
        try {
            const data = localStorage.getItem(this.STORAGE_KEY);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            return [];
        }
    }

    saveToStorage() {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.records));
        } catch (e) {
            console.error("Failed to save to localStorage:", e);
        }
    }

    clearTape() {
        this.records = [];
        this.saveToStorage();
    }

    getRecords() {
        return [...this.records];
    }

    static sanitizeFilename(filename) {
        if (!filename) return "";
        let clean = String(filename).trim();
        if (clean.startsWith('"') && clean.endsWith('"') && clean.length >= 2) {
            clean = clean.slice(1, -1);
        }
        if (clean.toUpperCase().startsWith("CAS1:")) {
            clean = clean.slice(5);
        }
        clean = clean.trim().toUpperCase();
        if (clean.length > 8) {
            clean = clean.slice(0, 8);
        }
        return clean;
    }

    static formatSearchIndicator(filename) {
        let name = CasioTapeManager.sanitizeFilename(filename);
        if (!name) name = "PROGRAM";
        return (name + "        ").slice(0, 8) + " B";
    }

    save(filename, slot, code) {
        const cleanName = CasioTapeManager.sanitizeFilename(filename);
        const record = {
            id: "tape_" + Date.now() + "_" + Math.random().toString(36).substr(2, 4),
            filename: cleanName,
            isAll: false,
            slot: slot,
            content: code || "",
            allSlots: null,
            timestamp: Date.now()
        };
        this.records.push(record);
        this.saveToStorage();
        return `Ready P${slot}`;
    }

    saveAll(filename, slot, allSlots) {
        const cleanName = CasioTapeManager.sanitizeFilename(filename);
        const record = {
            id: "tape_" + Date.now() + "_" + Math.random().toString(36).substr(2, 4),
            filename: cleanName,
            isAll: true,
            slot: slot,
            content: "",
            allSlots: allSlots ? [...allSlots] : new Array(10).fill(""),
            timestamp: Date.now()
        };
        this.records.push(record);
        this.saveToStorage();
        return `Ready P${slot}`;
    }

    /**
     * LOAD single program:
     * - LOAD (unnamed): Loads latest unnamed or named SAVE record.
     * - LOAD "name": Loads latest matching named SAVE record.
     * - Throws if record was saved with SAVE ALL.
     */
    load(filename, targetSlot) {
        const cleanName = CasioTapeManager.sanitizeFilename(filename);
        const hasName = Boolean(cleanName);

        const match = this.findRecord(cleanName, hasName, false);
        if (!match) {
            throw new Error(`P${targetSlot} error 0`);
        }

        // Compatibility checks (Page 67)
        if (match.isAll) {
            throw new Error(`P${targetSlot} error 0`); // Cannot load SAVE ALL with single LOAD
        }

        if (hasName && !match.filename) {
            throw new Error(`P${targetSlot} error 0`); // Cannot load unnamed SAVE by filename
        }

        return match.content;
    }

    /**
     * LOAD ALL programs:
     * - LOAD ALL (unnamed): Loads latest unnamed or named SAVE ALL record.
     * - LOAD ALL "name": Loads latest matching named SAVE ALL record.
     * - Throws if record was saved with single SAVE.
     */
    loadAll(filename, targetSlot) {
        const cleanName = CasioTapeManager.sanitizeFilename(filename);
        const hasName = Boolean(cleanName);

        const match = this.findRecord(cleanName, hasName, true);
        if (!match) {
            throw new Error(`P${targetSlot} error 0`);
        }

        // Compatibility checks (Page 67)
        if (!match.isAll) {
            throw new Error(`P${targetSlot} error 0`); // Cannot load single SAVE with LOAD ALL
        }

        if (hasName && !match.filename) {
            throw new Error(`P${targetSlot} error 0`); // Cannot load unnamed SAVE ALL by filename
        }

        return match.allSlots;
    }

    /**
     * VERIFY program integrity against tape:
     */
    verify(filename, activeSlot, activeMemoryCode, allMemorySlots) {
        const cleanName = CasioTapeManager.sanitizeFilename(filename);
        const searchDisp = CasioTapeManager.formatSearchIndicator(cleanName);

        if (!cleanName) {
            return {
                success: false,
                filename: "",
                searchDisplay: searchDisp,
                statusDisplay: `P${activeSlot} error 0`
            };
        }

        // Find matching record by name
        let match = null;
        for (let i = this.records.length - 1; i >= 0; i--) {
            if (this.records[i].filename.toUpperCase() === cleanName) {
                match = this.records[i];
                break;
            }
        }

        if (!match) {
            return {
                success: false,
                filename: cleanName,
                searchDisplay: searchDisp,
                statusDisplay: `P${activeSlot} error 0`
            };
        }

        let matches = false;
        if (match.isAll) {
            matches = true;
            for (let i = 0; i < 10; i++) {
                const mem = (allMemorySlots && allMemorySlots[i] ? allMemorySlots[i] : "").trim();
                const tape = (match.allSlots && match.allSlots[i] ? match.allSlots[i] : "").trim();
                if (mem !== tape) {
                    matches = false;
                    break;
                }
            }
        } else {
            const mem = (activeMemoryCode || "").trim();
            const tape = (match.content || "").trim();
            matches = (mem === tape);
        }

        return {
            success: matches,
            filename: cleanName,
            isAll: match.isAll,
            searchDisplay: searchDisp,
            statusDisplay: matches ? `Ready P${activeSlot}` : `P${activeSlot} error 0`
        };
    }

    findRecord(cleanName, hasName, preferAll) {
        if (hasName) {
            for (let i = this.records.length - 1; i >= 0; i--) {
                if (this.records[i].filename.toUpperCase() === cleanName) {
                    return this.records[i];
                }
            }
            return null;
        } else {
            // Find latest matching preference
            for (let i = this.records.length - 1; i >= 0; i--) {
                if (this.records[i].isAll === preferAll) {
                    return this.records[i];
                }
            }
            if (this.records.length > 0) {
                return this.records[this.records.length - 1];
            }
            return null;
        }
    }
}
