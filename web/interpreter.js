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
            return { type: 'ready', text: '', sub: this.memory.getPrompt() };
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
                return { type: 'ready', text: String(val), sub: this.memory.getPrompt() };
            }
        }

        // 10. PRINT statement
        if (/^PRINT\s+/i.test(line)) {
            const exprStr = line.slice(5).trim();
            const evaluated = this.evaluateExpression(exprStr);
            return { type: 'output', text: String(evaluated), sub: this.memory.getPrompt() };
        }

        // 11. Assignment: A = 10
        const assignMatch = line.match(/^([A-Za-z])\s*=\s*(.+)$/);
        if (assignMatch) {
            const varName = assignMatch[1].toUpperCase();
            const val = this.evaluateExpression(assignMatch[2].trim());
            this.variables[varName] = val;
            return { type: 'ready', text: String(val), sub: this.memory.getPrompt() };
        }

        // 12. Direct Expression evaluation (e.g. 5 + 3 * 2, SIN 45)
        try {
            const val = this.evaluateExpression(line);
            return { type: 'output', text: String(val), sub: this.memory.getPrompt() };
        } catch (e) {
            return { type: 'error', text: `P${this.memory.getActiveSlot()} error 0`, sub: this.memory.getPrompt() };
        }
    }

    /**
     * Executes the stored BASIC program in active slot.
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
                parsed.push({ num: parseInt(m[1], 10), stmt: m[2] });
            } else {
                parsed.push({ num: 0, stmt: l });
            }
        }

        parsed.sort((a, b) => a.num - b.num);

        let pc = 0;
        let iterations = 0;
        const MAX_STEPS = 1000;

        while (pc < parsed.length && iterations < MAX_STEPS) {
            iterations++;
            const { num, stmt } = parsed[pc];
            if (!stmt) { pc++; continue; }

            // PRINT
            if (/^PRINT\s+/i.test(stmt)) {
                const expr = stmt.slice(5).trim();
                if (expr.startsWith('"') && expr.endsWith('"')) {
                    output.push(expr.slice(1, -1));
                } else {
                    output.push(String(this.evaluateExpression(expr)));
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

            // Arrow storage or assignment
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

            const assignMatch = stmt.match(/^([A-Za-z])\s*=\s*(.+)$/);
            if (assignMatch) {
                const varName = assignMatch[1].toUpperCase();
                const val = this.evaluateExpression(assignMatch[2].trim());
                this.variables[varName] = val;
                pc++;
                continue;
            }

            // Default
            pc++;
        }

        const lastOut = output.length > 0 ? output[output.length - 1] : "DONE";
        return {
            type: 'output',
            text: lastOut,
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

        // String literal
        if (clean.startsWith('"') && clean.endsWith('"')) {
            return clean.slice(1, -1);
        }

        // Replace Casio functions with Math equivalents
        // In Casio calculators, trigonometric functions use Degree mode by default
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

        // Replace variable identifiers A-Z with their numeric values
        clean = clean.replace(/\b([A-Z])\b/g, (match, varChar) => {
            if (this.variables.hasOwnProperty(varChar)) {
                return this.variables[varChar];
            }
            return match;
        });

        try {
            // Safe evaluation using Function
            const res = Function(`"use strict"; return (${clean});`)();
            if (typeof res === "number") {
                return Number.isInteger(res) ? res : parseFloat(res.toFixed(6));
            }
            return res;
        } catch (e) {
            throw new Error("Syntax Error");
        }
    }
}
