/**
 * Casio Web Mobile Controller
 * Orchestrates UI, Web Audio, Virtual Tape Deck, and BASIC Interpreter
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Subsystems
    const audio = new CasioAudioSynthesizer();
    const memory = new CasioMemoryManager();
    const tape = new CasioTapeManager();
    const interpreter = new CasioInterpreter(memory, tape);

    // Pre-populate slots with retro sample programs
    memory.setProgram(0, '10 PRINT "HELLO CASIO"\n20 FOR I = 1 TO 5\n30 PRINT I\n40 NEXT I');
    memory.setProgram(1, '10 RADIUS = 7\n20 AREA = PI * RADIUS ^ 2\n30 PRINT AREA');
    memory.setProgram(2, '10 A = 1\n20 B = -5\n30 C = 6\n40 DISC = SQR(B^2 - 4*A*C)\n50 X1 = (-B + DISC) / (2*A)\n60 PRINT X1');

    // UI Elements
    const lcdText = document.getElementById("lcdText");
    const lcdStatus = document.getElementById("lcdStatus");
    const lcdSlotBadge = document.getElementById("lcdSlotBadge");
    const lcdCursor = document.getElementById("lcdCursor");
    const tapeCounter = document.getElementById("tapeCounter");
    const tapeModeStatus = document.getElementById("tapeModeStatus");
    const tapeActiveFileName = document.getElementById("tapeActiveFileName");
    const spoolLeft = document.getElementById("spoolLeft");
    const spoolRight = document.getElementById("spoolRight");
    const ledRec = document.getElementById("ledRec");
    const ledPlay = document.getElementById("ledPlay");
    const ledPower = document.getElementById("ledPower");

    // Modals
    const modalEditor = document.getElementById("modalEditor");
    const modalTapeLibrary = document.getElementById("modalTapeLibrary");
    const btnCodeEditor = document.getElementById("btnCodeEditor");
    const btnTapeLibrary = document.getElementById("btnTapeLibrary");
    const btnCloseEditor = document.getElementById("btnCloseEditor");
    const btnCloseTapeLibrary = document.getElementById("btnCloseTapeLibrary");
    const txtProgramEditor = document.getElementById("txtProgramEditor");
    const btnSaveSlotCode = document.getElementById("btnSaveSlotCode");
    const btnClearSlotCode = document.getElementById("btnClearSlotCode");
    const editorTitle = document.getElementById("editorTitle");
    const tapeRecordsList = document.getElementById("tapeRecordsList");
    const btnEraseTape = document.getElementById("btnEraseTape");
    const btnSoundToggle = document.getElementById("btnSoundToggle");

    // Command line buffer
    let currentInput = "";
    let counterVal = 0;
    let isExecuting = false;

    // Connect interpreter tape animation callback
    interpreter.onTapeOperation = (op, filename, isAll) => {
        triggerTapeAnimation(op, filename);
    };

    function updateLcdDisplay() {
        lcdText.textContent = currentInput;
        lcdSlotBadge.textContent = `SLOT [P${memory.getActiveSlot()}]`;
        updateSlotButtons();
    }

    function updateSlotButtons() {
        const active = memory.getActiveSlot();
        for (let i = 0; i < 10; i++) {
            const btn = document.getElementById(`slotBtn${i}`);
            if (btn) {
                btn.classList.toggle("active", i === active);
                btn.classList.toggle("has-code", !memory.isSlotEmpty(i));
            }
        }
    }

    function triggerTapeAnimation(operation, filename) {
        spoolLeft.classList.add("spinning");
        spoolRight.classList.add("spinning");

        counterVal = (counterVal + 1) % 1000;
        tapeCounter.textContent = String(counterVal).padStart(3, '0');

        if (operation === "SAVE") {
            ledRec.classList.add("on");
            tapeModeStatus.textContent = `TAPE: RECORDING "${CasioTapeManager.sanitizeFilename(filename)}"`;
            tapeActiveFileName.textContent = CasioTapeManager.sanitizeFilename(filename) || "UNTITLED";
            audio.playTapeChirp(800);
        } else if (operation === "LOAD") {
            ledPlay.classList.add("on");
            tapeModeStatus.textContent = `TAPE: READING "${CasioTapeManager.sanitizeFilename(filename)}"`;
            audio.playTapeChirp(700);
        } else if (operation === "VERIFY") {
            ledPlay.classList.add("on");
            tapeModeStatus.textContent = `TAPE: VERIFYING "${CasioTapeManager.sanitizeFilename(filename)}"`;
            audio.playTapeChirp(900);
        }

        setTimeout(() => {
            spoolLeft.classList.remove("spinning");
            spoolRight.classList.remove("spinning");
            ledRec.classList.remove("on");
            ledPlay.classList.remove("on");
            tapeModeStatus.textContent = "STATUS: STANDBY";
        }, 900);
    }

    async function handleExecute() {
        if (isExecuting) return;
        audio.playClick();

        const cmd = currentInput.trim();
        if (!cmd) {
            lcdStatus.textContent = memory.getPrompt();
            return;
        }

        isExecuting = true;
        lcdCursor.style.display = "none";

        try {
            const res = await interpreter.executeDirect(cmd);
            
            if (res.delayMs) {
                // Show intermediate state (e.g. search indicator "BASIC   B")
                if (res.text) {
                    lcdText.textContent = res.text;
                }
                await new Promise(r => setTimeout(r, res.delayMs));
            }

            if (res.type === 'error') {
                audio.playErrorBeep();
                lcdText.textContent = res.text;
                lcdStatus.textContent = res.sub || memory.getPrompt();
            } else {
                audio.playBeep(880, 0.05);
                lcdText.textContent = res.text;
                lcdStatus.textContent = res.sub || memory.getPrompt();
            }
        } catch (e) {
            audio.playErrorBeep();
            lcdText.textContent = `P${memory.getActiveSlot()} error 0`;
            lcdStatus.textContent = memory.getPrompt();
        } finally {
            currentInput = "";
            isExecuting = false;
            lcdCursor.style.display = "inline-block";
            updateLcdDisplay();
        }
    }

    // Keypad Click Event Handling
    const keypad = document.getElementById("keypad");
    keypad.addEventListener("click", (e) => {
        const btn = e.target.closest("button");
        if (!btn || isExecuting) return;

        const key = btn.dataset.key;
        if (!key) return;

        audio.playClick();

        if (key === "EXE") {
            handleExecute();
            return;
        }

        if (key === "AC") {
            currentInput = "";
            lcdText.textContent = "";
            lcdStatus.textContent = memory.getPrompt();
            return;
        }

        if (key === "DEL") {
            currentInput = currentInput.slice(0, -1);
            updateLcdDisplay();
            return;
        }

        if (key === "NEW") {
            currentInput = "NEW";
            updateLcdDisplay();
            return;
        }

        if (key === "ALL") {
            currentInput += (currentInput.length > 0 && !currentInput.endsWith(" ") ? " " : "") + "ALL";
            updateLcdDisplay();
            return;
        }

        // Functions with auto-space
        if (["SIN", "COS", "TAN", "SQR"].includes(key)) {
            currentInput += key + " ";
            updateLcdDisplay();
            return;
        }

        currentInput += key;
        updateLcdDisplay();
    });

    // Program Slot (P0 - P9) Tab Switching
    document.getElementById("slotTabBar").addEventListener("click", (e) => {
        const btn = e.target.closest(".slot-btn");
        if (!btn) return;
        audio.playClick();
        const slot = parseInt(btn.dataset.slot, 10);
        memory.setActiveSlot(slot);
        lcdStatus.textContent = memory.getPrompt();
        updateLcdDisplay();
    });

    // Quick Action Tape Buttons
    document.getElementById("btnQuickSave").addEventListener("click", () => {
        audio.playClick();
        currentInput = `SAVE "BASIC"`;
        updateLcdDisplay();
    });

    document.getElementById("btnQuickLoad").addEventListener("click", () => {
        audio.playClick();
        currentInput = `LOAD "BASIC"`;
        updateLcdDisplay();
    });

    document.getElementById("btnQuickVerify").addEventListener("click", () => {
        audio.playClick();
        currentInput = `VERIFY "BASIC"`;
        updateLcdDisplay();
    });

    document.getElementById("btnQuickRun").addEventListener("click", () => {
        audio.playClick();
        currentInput = "RUN";
        handleExecute();
    });

    // Physical Keyboard Listener
    window.addEventListener("keydown", (e) => {
        if (modalEditor.classList.contains("open") || modalTapeLibrary.classList.contains("open")) {
            return; // Allow normal typing in editor
        }

        if (e.key === "Enter") {
            e.preventDefault();
            handleExecute();
            return;
        }

        if (e.key === "Backspace") {
            e.preventDefault();
            currentInput = currentInput.slice(0, -1);
            updateLcdDisplay();
            return;
        }

        if (e.key === "Escape") {
            e.preventDefault();
            currentInput = "";
            lcdText.textContent = "";
            lcdStatus.textContent = memory.getPrompt();
            return;
        }

        // Printable characters
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
            audio.playClick();
            currentInput += e.key;
            updateLcdDisplay();
        }
    });

    // Sound Toggle
    btnSoundToggle.addEventListener("click", () => {
        const enabled = audio.toggleSound();
        btnSoundToggle.classList.toggle("active", enabled);
    });

    // Code Editor Modal Handlers
    btnCodeEditor.addEventListener("click", () => {
        audio.playClick();
        const active = memory.getActiveSlot();
        editorTitle.textContent = `PROGRAM AREA P${active}`;
        txtProgramEditor.value = memory.getActiveProgram();
        modalEditor.classList.add("open");
    });

    btnCloseEditor.addEventListener("click", () => {
        modalEditor.classList.remove("open");
    });

    btnSaveSlotCode.addEventListener("click", () => {
        audio.playClick();
        memory.setActiveProgram(txtProgramEditor.value);
        modalEditor.classList.remove("open");
        updateLcdDisplay();
        lcdStatus.textContent = `${memory.getPrompt()} (SAVED)`;
        setTimeout(() => { lcdStatus.textContent = memory.getPrompt(); }, 1500);
    });

    btnClearSlotCode.addEventListener("click", () => {
        audio.playClick();
        txtProgramEditor.value = "";
    });

    // Preset Samples
    document.querySelectorAll(".preset-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            audio.playClick();
            const sample = chip.dataset.sample;
            if (sample === "counter") {
                txtProgramEditor.value = '10 PRINT "COUNTER"\n20 FOR I = 1 TO 10\n30 PRINT I\n40 NEXT I';
            } else if (sample === "math") {
                txtProgramEditor.value = '10 RADIUS = 10\n20 AREA = PI * RADIUS ^ 2\n30 PRINT AREA';
            } else if (sample === "quadratic") {
                txtProgramEditor.value = '10 A = 1\n20 B = -4\n30 C = 4\n40 DISC = SQR(B^2 - 4*A*C)\n50 X1 = (-B + DISC) / (2*A)\n60 PRINT X1';
            }
        });
    });

    // Tape Library Modal Handlers
    btnTapeLibrary.addEventListener("click", () => {
        audio.playClick();
        renderTapeRecords();
        modalTapeLibrary.classList.add("open");
    });

    btnCloseTapeLibrary.addEventListener("click", () => {
        modalTapeLibrary.classList.remove("open");
    });

    btnEraseTape.addEventListener("click", () => {
        if (confirm("Are you sure you want to erase all virtual cassette tape records?")) {
            audio.playClick();
            tape.clearTape();
            renderTapeRecords();
        }
    });

    function renderTapeRecords() {
        const records = tape.getRecords();
        tapeRecordsList.innerHTML = "";

        if (records.length === 0) {
            tapeRecordsList.innerHTML = `<div style="font-size: 0.8rem; color: #64748b; text-align: center; padding: 20px;">Virtual tape is blank. Use SAVE or SAVE ALL to record programs.</div>`;
            return;
        }

        records.slice().reverse().forEach(rec => {
            const card = document.createElement("div");
            card.className = "tape-card";
            const name = rec.filename || "<UNNAMED>";
            const typeLabel = rec.isAll ? "SAVE ALL (P0-P9)" : `SAVE (P${rec.slot})`;
            const dateStr = new Date(rec.timestamp).toLocaleTimeString();

            card.innerHTML = `
                <div class="tape-card-info">
                    <span class="tape-card-name">${name}</span>
                    <span class="tape-card-meta">${typeLabel} • ${dateStr}</span>
                </div>
                <div style="display: flex; gap: 6px;">
                    <button class="action-btn secondary btn-load-tape" data-name="${rec.filename}" data-all="${rec.isAll}">LOAD</button>
                    <button class="action-btn secondary btn-verify-tape" data-name="${rec.filename}">VERIFY</button>
                </div>
            `;
            tapeRecordsList.appendChild(card);
        });

        // Attach buttons in library
        tapeRecordsList.querySelectorAll(".btn-load-tape").forEach(b => {
            b.addEventListener("click", () => {
                const name = b.dataset.name;
                const isAll = b.dataset.all === "true";
                modalTapeLibrary.classList.remove("open");
                currentInput = isAll ? (name ? `LOAD ALL "${name}"` : `LOAD ALL`) : (name ? `LOAD "${name}"` : `LOAD`);
                handleExecute();
            });
        });

        tapeRecordsList.querySelectorAll(".btn-verify-tape").forEach(b => {
            b.addEventListener("click", () => {
                const name = b.dataset.name;
                modalTapeLibrary.classList.remove("open");
                currentInput = name ? `VERIFY "${name}"` : `VERIFY`;
                handleExecute();
            });
        });
    }

    // Initial display update
    updateLcdDisplay();
});
