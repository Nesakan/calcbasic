/**
 * Casio BASIC Mini-Interpreter for Web/Mobile
 * Evaluates expressions, handles arrow storage, and executes stored programs.
 */
class CasioInterpreter {
    constructor(memoryManager, tapeManager) {
        this.memory = memoryManager;
        this.tape = tapeManager;
        this.variables = {};
        for (let i = 0; i < 26; i++) {
            this.variables[String.fromCharCode(65 + i)] = 0;
        }
        this.outputLines = [];
        this.onTapeOperation = null; // callback for UI tape animation
    }

    clearVariables() {
        for (let k in this.variables) {
            this.variables[k] = 0;
        }
    }

    /**
     * Executes a single direct command line.
     * Returns an object { type: 'ready'|'output'|'error', text: string, sub: string, delayMs: number }
     */
    async executeDirect(rawLine) {
        if (!rawLine || !rawLine.trim()) {
            return { type: 'ready', text: '', sub: this.memory.getPrompt() };
        }

        const line = rawLine.trim();

        // 1. Slot switch: P0, P1, ..., P9
        if (/^P[0-9]$/i.test(line)) {
            const slot = parseInt(line.charAt(1), 10);
            this.memory.setActiveSlot(slot);
            return { type: 'ready', text: '', sub: this.memory.getPrompt() };
        }

        // 2. NEW / NEW ALL
        if (/^NEW(\s+ALL)?$/i.test(line)) {
            if (/ALL/i.test(line)) {
                this.memory.clearAll();
            } else {
                this.memory.clearActiveSlot();
            }
            return { type: 'ready', text: '', sub: this.memory.getPrompt() };
        }

        // 3. CLEAR
        if (/^CLEAR$/i.test(line)) {
            this.clearVariables();
            return { type: 'ready', text: 'CLEARED', sub: this.memory.getPrompt() };
        }

        // 4. SAVE / SAVE ALL
        const saveMatch = line.match(/^SAVE(?:\s+ALL)?(?:\s+(?:"([^"]*)"|([A-Za-z0-9_]+)))?(?:\s+ALL)?$/i);
        if (saveMatch && /^SAVE/i.test(line)) {
            const isAll = /ALL/i.test(line);
            const filename = saveMatch[1] || saveMatch[2] || "";
            const activeSlot = this.memory.getActiveSlot();

            if (this.onTapeOperation) {
                this.onTapeOperation("SAVE", filename, isAll);
            }

            let result;
            if (isAll) {
                result = this.tape.saveAll(filename, activeSlot, this.memory.getAllPrograms());
            } else {
                result = this.tape.save(filename, activeSlot, this.memory.getActiveProgram());
            }

            return {
                type: 'ready',
                text: filename ? `SAVE "${CasioTapeManager.sanitizeFilename(filename)}"` : "SAVE",
                sub: result,
                delayMs: 800
            };
        }

        // 5. LOAD / LOAD ALL
        const loadMatch = line.match(/^LOAD(?:\s+ALL)?(?:\s+(?:"([^"]*)"|([A-Za-z0-9_]+)))?(?:\s+ALL)?$/i);
        if (loadMatch && /^LOAD/i.test(line)) {
            const isAll = /ALL/i.test(line);
            const filename = loadMatch[1] || loadMatch[2] || "";
            const activeSlot = this.memory.getActiveSlot();

            if (this.onTapeOperation) {
                this.onTapeOperation("LOAD", filename, isAll);
            }

            try {
                if (isAll) {
                    const loadedSlots = this.tape.loadAll(filename, activeSlot);
                    this.memory.setAllPrograms(loadedSlots);
                } else {
                    const loadedCode = this.tape.load(filename, activeSlot);
                    this.memory.setActiveProgram(loadedCode);
                }
                const displayName = filename ? CasioTapeManager.sanitizeFilename(filename) : "PROGRAM";
                return {
                    type: 'ready',
                    text: (displayName + "        ").slice(0, 8) + " B",
                    sub: this.memory.getPrompt(),
                    delayMs: 900
                };
            } catch (err) {
                return {
                    type: 'error',
                    text: err.message,
                    sub: this.memory.getPrompt(),
                    delayMs: 600
                };
            }
        }

        // 6. VERIFY
        const verifyMatch = line.match(/^VERIFY\s+(?:"([^"]*)"|([A-Za-z0-9_:]+))$/i);
        if (verifyMatch) {
            const filename = verifyMatch[1] || verifyMatch[2] || "";
            const activeSlot = this.memory.getActiveSlot();

            if (this.onTapeOperation) {
                this.onTapeOperation("VERIFY", filename, false);
            }

            const res = this.tape.verify(
                filename,
                activeSlot,
                this.memory.getActiveProgram(),
                this.memory.getAllPrograms()
            );

            return {
                type: res.success ? 'ready' : 'error',
                text: res.searchDisplay,
                sub: res.statusDisplay + (res.success ? "" : `\n${this.memory.getPrompt()}`),
                delayMs: 1000
            };
        }

        // 7. LIST
        if (/^LIST$/i.test(line)) {
            const prog = this.memory.getActiveProgram();
            return {
                type: 'output',
                text: prog ? prog.split('\n')[0] : "EMPTY",
                sub: this.memory.getPrompt(),
                fullListing: prog
            };
        }

        // 8. RUN
        if (/^RUN$/i.test(line)) {
            return this.runProgram();
        }

        // 9. Arrow Storage: <expr> → <var> or assignment <var> = <expr>
        if (line.includes("→") || line.includes("->")) {
            const parts = line.split(/→|->/);
            const val = this.evaluateExpression(parts[0].trim());
            const varName = parts[1].trim().toUpperCase().charAt(0);
            if (varName >= 'A' && varName <= 'Z') {
                this.variables[varName] = val;
                return { type: 'output', text: String(val), sub: this.memory.getPrompt() };
            }
        }

        // 10. PRINT statement
        if (/^PRINT(?:\s+(.*))?$/i.test(line)) {
            const m = line.match(/^PRINT(?:\s+(.*))?$/i);
            const exprStr = m && m[1] ? m[1].trim() : "";
            if (!exprStr) {
                return { type: 'output', text: '', sub: this.memory.getPrompt() };
            }
            const evaluated = this.evaluateExpression(exprStr);
            return { type: 'output', text: String(evaluated), sub: this.memory.getPrompt() };
        }

        // 11. Assignment: A = 10
        const assignMatch = line.match(/^([A-Za-z])\s*=\s*(.+)$/);
        if (assignMatch) {
            const varName = assignMatch[1].toUpperCase();
            const val = this.evaluateExpression(assignMatch[2].trim());
            this.variables[varName] = val;
            return { type: 'output', text: String(val), sub: this.memory.getPrompt() };
        }

        // 12. Direct Expression evaluation or quoted text (e.g. 5 + 3 * 2, "HELLO", SIN 45)
        try {
            const val = this.evaluateExpression(line);
            return { type: 'output', text: String(val), sub: this.memory.getPrompt() };
        } catch (e) {
            return { type: 'error', text: `P${this.memory.getActiveSlot()} error 0`, sub: this.memory.getPrompt() };
        }
    }

    /**
     * Executes the stored BASIC program in active slot with full FOR/NEXT loops.
     */
    runProgram() {
        const program = this.memory.getActiveProgram();
        if (!program || !program.trim()) {
            return { type: 'ready', text: "NO PROGRAM", sub: this.memory.getPrompt() };
        }

        const lines = program.split('\n').map(l => l.trim()).filter(l => l.length > 0);
        const output = [];

        // Parse lines into { lineNum, stmt }
        const parsed = [];
        for (let l of lines) {
            const m = l.match(/^([0-9]+)\s*(.*)$/);
            if (m) {
                parsed.push({ num: parseInt(m[1], 10), stmt: m[2].trim() });
            } else {
                parsed.push({ num: 0, stmt: l.trim() });
            }
        }

        parsed.sort((a, b) => a.num - b.num);

        let pc = 0;
        let iterations = 0;
        const MAX_STEPS = 2000;
        const loopStack = []; // { varName, endVal, step, loopPc }

        while (pc < parsed.length && iterations < MAX_STEPS) {
            iterations++;
            const { num, stmt } = parsed[pc];
            if (!stmt) { pc++; continue; }

            // PRINT statement
            const printMatch = stmt.match(/^PRINT(?:\s+(.*))?$/i);
            if (printMatch) {
                const expr = printMatch[1] ? printMatch[1].trim() : "";
                if (!expr) {
                    output.push("");
                } else if (expr.startsWith('"') && expr.endsWith('"') && expr.length >= 2) {
                    output.push(expr.slice(1, -1));
                } else {
                    output.push(String(this.evaluateExpression(expr)));
                }
                pc++;
                continue;
            }

            // FOR loop: FOR I = 1 TO 5 [STEP 1]
            const forMatch = stmt.match(/^FOR\s+([A-Za-z])\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+STEP\s+(.+))?$/i);
            if (forMatch) {
                const varName = forMatch[1].toUpperCase();
                const startVal = Number(this.evaluateExpression(forMatch[2].trim()));
                const endVal = Number(this.evaluateExpression(forMatch[3].trim()));
                const stepVal = forMatch[4] ? Number(this.evaluateExpression(forMatch[4].trim())) : 1;

                this.variables[varName] = startVal;
                loopStack.push({
                    varName,
                    endVal,
                    step: stepVal,
                    loopPc: pc + 1
                });
                pc++;
                continue;
            }

            // NEXT statement
            const nextMatch = stmt.match(/^NEXT(?:\s+([A-Za-z]))?$/i);
            if (nextMatch) {
                if (loopStack.length > 0) {
                    const top = loopStack[loopStack.length - 1];
                    this.variables[top.varName] = Number(this.variables[top.varName]) + top.step;
                    
                    const keepGoing = top.step >= 0 
                        ? this.variables[top.varName] <= top.endVal 
                        : this.variables[top.varName] >= top.endVal;

                    if (keepGoing) {
                        pc = top.loopPc;
                        continue;
                    } else {
                        loopStack.pop();
                    }
                }
                pc++;
                continue;
            }

            // GOTO
            const gotoMatch = stmt.match(/^GOTO\s+([0-9]+)$/i);
            if (gotoMatch) {
                const target = parseInt(gotoMatch[1], 10);
                const idx = parsed.findIndex(p => p.num === target);
                if (idx !== -1) {
                    pc = idx;
                    continue;
                } else {
                    break;
                }
            }

            // Arrow storage (expr → var)
            if (stmt.includes("→") || stmt.includes("->")) {
                const parts = stmt.split(/→|->/);
                const val = this.evaluateExpression(parts[0].trim());
                const varName = parts[1].trim().toUpperCase().charAt(0);
                if (varName >= 'A' && varName <= 'Z') {
                    this.variables[varName] = val;
                }
                pc++;
                continue;
            }

            // Standard assignment (A = expr)
            const assignMatch = stmt.match(/^([A-Za-z])\s*=\s*(.+)$/);
            if (assignMatch) {
                const varName = assignMatch[1].toUpperCase();
                const val = this.evaluateExpression(assignMatch[2].trim());
                this.variables[varName] = val;
                pc++;
                continue;
            }

            // Unrecognized or remark
            pc++;
        }

        // Format LCD display output
        let displayText = "DONE";
        if (output.length > 0) {
            // If output has multiple items, join neatly for LCD
            displayText = output.join(" ");
        }

        return {
            type: 'output',
            text: displayText,
            sub: this.memory.getPrompt(),
            fullOutput: output
        };
    }

    /**
     * Evaluates a mathematical expression with Casio precedence and math functions.
     */
    evaluateExpression(expr) {
        if (!expr) return 0;
        let clean = expr.trim();

        // String literal in double or single quotes
        if ((clean.startsWith('"') && clean.endsWith('"') && clean.length >= 2) ||
            (clean.startsWith("'") && clean.endsWith("'") && clean.length >= 2)) {
            return clean.slice(1, -1);
        }

        // If it's a raw unquoted string like HELLO or CASIO without operators/numbers
        if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(clean) && clean.length > 1) {
            // Check if it's a known constant like PI
            if (clean.toUpperCase() === "PI") return Math.PI;
            // Otherwise, treat as string constant
            return clean;
        }

        // Replace Casio functions with Math equivalents (Degree mode by default)
        clean = clean.replace(/\bSIN\s*\(([^)]+)\)/gi, 'Math.sin(($1) * Math.PI / 180)')
                     .replace(/\bSIN\s+([0-9.]+|[A-Za-z])/gi, 'Math.sin(($1) * Math.PI / 180)')
                     .replace(/\bCOS\s*\(([^)]+)\)/gi, 'Math.cos(($1) * Math.PI / 180)')
                     .replace(/\bCOS\s+([0-9.]+|[A-Za-z])/gi, 'Math.cos(($1) * Math.PI / 180)')
                     .replace(/\bTAN\s*\(([^)]+)\)/gi, 'Math.tan(($1) * Math.PI / 180)')
                     .replace(/\bTAN\s+([0-9.]+|[A-Za-z])/gi, 'Math.tan(($1) * Math.PI / 180)')
                     .replace(/\bSQR\s*\(([^)]+)\)/gi, 'Math.sqrt($1)')
                     .replace(/\bSQR\s+([0-9.]+|[A-Za-z])/gi, 'Math.sqrt($1)')
                     .replace(/√\s*([0-9.]+|[A-Za-z])/g, 'Math.sqrt($1)')
                     .replace(/\bABS\s*\(([^)]+)\)/gi, 'Math.abs($1)')
                     .replace(/\bLOG\s*\(([^)]+)\)/gi, 'Math.log10($1)')
                     .replace(/\bLN\s*\(([^)]+)\)/gi, 'Math.log($1)')
                     .replace(/\bEXP\s*\(([^)]+)\)/gi, 'Math.exp($1)')
                     .replace(/\bRND\b/gi, 'Math.random()')
                     .replace(/\bPI\b/gi, 'Math.PI');

        // Power operator ^ -> **
        clean = clean.replace(/\^/g, '**');

        // Replace single-letter variable identifiers A-Z with their numeric values
        clean = clean.replace(/\b([A-Z])\b/g, (match, varChar) => {
            if (this.variables.hasOwnProperty(varChar)) {
                return this.variables[varChar];
            }
            return match;
        });

        try {
            const res = Function(`"use strict"; return (${clean});`)();
            if (typeof res === "number") {
                return Number.isInteger(res) ? res : parseFloat(res.toFixed(6));
            }
            return res;
        } catch (e) {
            // If syntax error but looks like text, return as string
            return expr;
        }
    }
}
