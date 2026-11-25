/**
 * Inpro Coder - Program Library & CalcBASIC Runner
 */

class ProgramLibrary {
    constructor() {
        this.STORAGE_KEY = "inpro_coder_programs_v2";
        this.programs = this.loadPrograms();
        this.activeId = this.programs.length > 0 ? this.programs[0].id : null;
    }

    loadPrograms() {
        try {
            const raw = localStorage.getItem(this.STORAGE_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    return parsed;
                }
            }
        } catch (e) { /* ignore */ }

        const now = Date.now();
        return [
            {
                id: "prog_welcome",
                name: "Welcome Demo",
                code: [
                    'PRINT "=== Welcome to Inpro Coder ==="',
                    'INPUT "What is your name? "; USER_NAME$',
                    'PRINT "Hello, " + USER_NAME$ + "!"',
                    'FOR I = 1 TO 3',
                    '    PRINT "Count: " + I',
                    'NEXT I'
                ].join('\n'),
                createdAt: now,
                updatedAt: now
            },
            {
                id: "prog_circle",
                name: "Circle Calculator",
                code: [
                    'PRINT "--- Circle Calculator ---"',
                    'INPUT "Enter radius: ", R',
                    'AREA = PI * R ^ 2',
                    'CIRC = 2 * PI * R',
                    'PRINT "Area: " + ROUND(AREA, 2)',
                    'PRINT "Circumference: " + ROUND(CIRC, 2)'
                ].join('\n'),
                createdAt: now,
                updatedAt: now
            },
            {
                id: "prog_guess",
                name: "Number Guessing",
                code: [
                    'PRINT "--- Number Guessing Game ---"',
                    'SECRET = RND(10)',
                    'WON = 0',
                    'FOR ATTEMPT = 1 TO 3',
                    '    IF WON = 0 THEN',
                    '        INPUT "Guess (1-10): ", G',
                    '        IF G = SECRET THEN',
                    '            PRINT "Correct! You win!"',
                    '            WON = 1',
                    '        ELSE',
                    '            IF G < SECRET THEN',
                    '                PRINT "Too low!"',
                    '            ELSE',
                    '                PRINT "Too high!"',
                    '            END IF',
                    '        END IF',
                    '    END IF',
                    'NEXT ATTEMPT',
                    'IF WON = 0 THEN',
                    '    PRINT "Secret was: " + SECRET',
                    'END IF'
                ].join('\n'),
                createdAt: now,
                updatedAt: now
            }
        ];
    }

    persist() {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.programs));
        } catch (e) { /* ignore */ }
    }

    getAll() {
        return [...this.programs];
    }

    getById(id) {
        return this.programs.find(p => p.id === id) || null;
    }

    getActive() {
        return this.getById(this.activeId) || this.programs[0] || null;
    }

    setActive(id) {
        if (this.getById(id)) {
            this.activeId = id;
        }
    }

    create(name = "Untitled Program", code = "") {
        const now = Date.now();
        const prog = {
            id: "prog_" + now + "_" + Math.random().toString(36).slice(2, 6),
            name: (name || "Untitled Program").trim(),
            code: code || "",
            createdAt: now,
            updatedAt: now
        };
        this.programs.unshift(prog);
        this.activeId = prog.id;
        this.persist();
        return prog;
    }

    update(id, name, code) {
        const prog = this.getById(id);
        if (!prog) return this.create(name, code);
        prog.name = (name || "Untitled Program").trim();
        prog.code = code || "";
        prog.updatedAt = Date.now();
        this.persist();
        return prog;
    }

    remove(id) {
        this.programs = this.programs.filter(p => p.id !== id);
        if (this.activeId === id) {
            this.activeId = this.programs.length > 0 ? this.programs[0].id : null;
        }
        this.persist();
    }

    importAll(list) {
        if (!Array.isArray(list)) return 0;
        let count = 0;
        for (const item of list) {
            if (item && typeof item.code === "string") {
                this.create(item.name || "Imported Program", item.code);
                count++;
            }
        }
        return count;
    }
}

class CalcBasicRunner {
    constructor() {
        this.variables = {};
        this.running = false;
        this.stopRequested = false;
        this.onPrint = () => {};
        this.onStatus = () => {};
        this.onInputRequest = async () => "";
        this.onVarsChange = () => {};
    }

    clearVariables() {
        this.variables = {};
        this.onVarsChange(this.variables);
    }

    stop() {
        this.stopRequested = true;
    }

    async run(sourceCode) {
        this.running = true;
        this.stopRequested = false;
        this.clearVariables();

        const rawLines = (sourceCode || "").split(/\r?\n/);
        const statements = [];

        for (let i = 0; i < rawLines.length; i++) {
            const raw = rawLines[i];
            const trimmed = this.stripComment(raw).trim();
            if (!trimmed) continue;

            const lineNumMatch = trimmed.match(/^([0-9]+)\s+(.*)$/);
            if (lineNumMatch) {
                statements.push({ lineNo: i + 1, label: parseInt(lineNumMatch[1], 10), text: lineNumMatch[2].trim() });
            } else {
                statements.push({ lineNo: i + 1, label: null, text: trimmed });
            }
        }

        const blockMap = this.buildBlockMap(statements);
        const loopStack = [];
        let pc = 0;
        let steps = 0;
        const MAX_STEPS = 20000;

        try {
            this.onStatus("RUNNING", "running");
            while (pc < statements.length) {
                if (this.stopRequested) {
                    this.onPrint("Execution stopped.", "system");
                    break;
                }
                if (++steps > MAX_STEPS) {
                    throw new Error("Execution limit exceeded (possible infinite loop)");
                }

                const cur = statements[pc];
                const stmt = cur.text;

                if (/^(END|STOP)$/i.test(stmt)) break;
                if (/^REM\b/i.test(stmt)) { pc++; continue; }

                // PRINT
                if (/^PRINT\b/i.test(stmt)) {
                    const rest = stmt.slice(5).trim();
                    this.onPrint(rest ? String(this.evalExpr(rest)) : "", "output");
                    pc++;
                    continue;
                }

                // INPUT [prompt (; | ,)] var1 [, var2 ...]
                if (/^INPUT\b/i.test(stmt)) {
                    const rest = stmt.slice(5).trim();
                    let prompt = "? ";
                    let varsPart = rest;

                    const pMatch = rest.match(/^"([^"]*)"\s*([;,])\s*(.+)$/);
                    if (pMatch) {
                        prompt = pMatch[1];
                        varsPart = pMatch[3];
                    }

                    const varNames = varsPart.split(",").map(v => v.trim()).filter(Boolean);
                    const userRaw = await this.onInputRequest(prompt);
                    if (this.stopRequested) break;

                    const parts = varNames.length > 1
                        ? String(userRaw).split(",").map(s => s.trim())
                        : [String(userRaw).trim()];

                    varNames.forEach((vName, idx) => {
                        const valStr = parts[idx] !== undefined ? parts[idx] : "";
                        const upper = vName.toUpperCase();
                        if (upper.endsWith("$")) {
                            this.variables[upper] = valStr;
                        } else if (valStr !== "" && !isNaN(Number(valStr))) {
                            this.variables[upper] = Number(valStr);
                        } else {
                            this.variables[upper] = valStr;
                        }
                    });
                    this.onVarsChange(this.variables);
                    pc++;
                    continue;
                }

                // FOR var = start TO end [STEP step]
                const forMatch = stmt.match(/^FOR\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+STEP\s+(.+))?$/i);
                if (forMatch) {
                    const varName = forMatch[1].toUpperCase();
                    const startVal = Number(this.evalExpr(forMatch[2]));
                    const endVal = Number(this.evalExpr(forMatch[3]));
                    const stepVal = forMatch[4] ? Number(this.evalExpr(forMatch[4])) : 1;

                    this.variables[varName] = startVal;
                    this.onVarsChange(this.variables);

                    const shouldSkip = stepVal >= 0 ? startVal > endVal : startVal < endVal;
                    if (shouldSkip) {
                        const nextPc = this.findMatchingNext(statements, pc);
                        pc = nextPc !== -1 ? nextPc + 1 : pc + 1;
                    } else {
                        loopStack.push({ varName, endVal, stepVal, bodyPc: pc + 1 });
                        pc++;
                    }
                    continue;
                }

                // NEXT [var]
                const nextMatch = stmt.match(/^NEXT(?:\s+([A-Za-z_][A-Za-z0-9_]*))?$/i);
                if (nextMatch) {
                    if (loopStack.length > 0) {
                        const top = loopStack[loopStack.length - 1];
                        const newVal = Number(this.variables[top.varName]) + top.stepVal;
                        this.variables[top.varName] = newVal;
                        this.onVarsChange(this.variables);

                        const keep = top.stepVal >= 0 ? newVal <= top.endVal : newVal >= top.endVal;
                        if (keep) {
                            pc = top.bodyPc;
                            continue;
                        } else {
                            loopStack.pop();
                        }
                    }
                    pc++;
                    continue;
                }

                // Block IF
                const blockIfMatch = stmt.match(/^IF\s+(.+?)\s+THEN$/i);
                if (blockIfMatch) {
                    const cond = this.isTruthy(this.evalExpr(blockIfMatch[1]));
                    if (cond) {
                        pc++;
                    } else {
                        const info = blockMap.get(pc);
                        if (info && info.elsePc !== -1) pc = info.elsePc + 1;
                        else if (info && info.endPc !== -1) pc = info.endPc + 1;
                        else pc++;
                    }
                    continue;
                }

                if (/^ELSE$/i.test(stmt)) {
                    const info = blockMap.get(pc);
                    pc = (info && info.endPc !== -1) ? info.endPc + 1 : pc + 1;
                    continue;
                }

                if (/^END\s*IF$/i.test(stmt)) { pc++; continue; }

                // Single-line IF
                const singleIfMatch = stmt.match(/^IF\s+(.+?)\s+THEN\s+(.+)$/i);
                if (singleIfMatch) {
                    const cond = this.isTruthy(this.evalExpr(singleIfMatch[1]));
                    const splitElse = this.splitTopLevelElse(singleIfMatch[2].trim());
                    const branch = cond ? splitElse.thenPart : splitElse.elsePart;
                    if (branch) {
                        const jumped = await this.execInlineStatement(branch, statements);
                        if (jumped !== null) { pc = jumped; continue; }
                    }
                    pc++;
                    continue;
                }

                // GOTO
                const gotoMatch = stmt.match(/^GOTO\s+([0-9]+)$/i);
                if (gotoMatch) {
                    const target = parseInt(gotoMatch[1], 10);
                    const idx = statements.findIndex(s => s.label === target);
                    if (idx !== -1) { pc = idx; continue; }
                }

                // Arrow storage: expr → var
                if (stmt.includes("→") || stmt.includes("->")) {
                    const parts = stmt.split(/→|->/);
                    const val = this.evalExpr(parts[0].trim());
                    this.variables[parts[1].trim().toUpperCase()] = val;
                    this.onVarsChange(this.variables);
                    pc++;
                    continue;
                }

                // Assignment
                const assignMatch = stmt.match(/^(?:LET\s+)?([A-Za-z_][A-Za-z0-9_]*\$?)\s*=\s*(.+)$/i);
                if (assignMatch) {
                    this.variables[assignMatch[1].toUpperCase()] = this.evalExpr(assignMatch[2]);
                    this.onVarsChange(this.variables);
                    pc++;
                    continue;
                }

                pc++;
            }
            this.onStatus("READY", "idle");
        } catch (err) {
            this.onPrint(`Error (line ${statements[pc] ? statements[pc].lineNo : "?"}): ${err.message}`, "error");
            this.onStatus("ERROR", "error");
        } finally {
            this.running = false;
        }
    }

    async execInlineStatement(stmt, statements) {
        if (/^PRINT\b/i.test(stmt)) {
            const rest = stmt.slice(5).trim();
            this.onPrint(rest ? String(this.evalExpr(rest)) : "", "output");
            return null;
        }
        const gotoMatch = stmt.match(/^GOTO\s+([0-9]+)$/i);
        if (gotoMatch) {
            const target = parseInt(gotoMatch[1], 10);
            const idx = statements.findIndex(s => s.label === target);
            return idx !== -1 ? idx : null;
        }
        const assignMatch = stmt.match(/^(?:LET\s+)?([A-Za-z_][A-Za-z0-9_]*\$?)\s*=\s*(.+)$/i);
        if (assignMatch) {
            this.variables[assignMatch[1].toUpperCase()] = this.evalExpr(assignMatch[2]);
            this.onVarsChange(this.variables);
        }
        return null;
    }

    buildBlockMap(statements) {
        const map = new Map();
        const stack = [];
        for (let i = 0; i < statements.length; i++) {
            const t = statements[i].text;
            if (/^IF\s+.+\s+THEN$/i.test(t)) stack.push({ ifPc: i, elsePc: -1, endPc: -1 });
            else if (/^ELSE$/i.test(t) && stack.length > 0) stack[stack.length - 1].elsePc = i;
            else if (/^END\s*IF$/i.test(t) && stack.length > 0) {
                const top = stack.pop();
                top.endPc = i;
                map.set(top.ifPc, top);
                if (top.elsePc !== -1) map.set(top.elsePc, top);
            }
        }
        return map;
    }

    findMatchingNext(statements, forPc) {
        let depth = 1;
        for (let i = forPc + 1; i < statements.length; i++) {
            if (/^FOR\b/i.test(statements[i].text)) depth++;
            else if (/^NEXT\b/i.test(statements[i].text) && --depth === 0) return i;
        }
        return -1;
    }

    splitTopLevelElse(body) {
        let inQuotes = false;
        for (let i = 0; i < body.length; i++) {
            if (body[i] === '"') inQuotes = !inQuotes;
            if (!inQuotes && body.slice(i).match(/^ELSE\b/i) && (i === 0 || /\s/.test(body[i - 1]))) {
                return { thenPart: body.slice(0, i).trim(), elsePart: body.slice(i + 4).trim() };
            }
        }
        return { thenPart: body, elsePart: null };
    }

    stripComment(line) {
        let inQuotes = false, quoteChar = "";
        for (let i = 0; i < line.length; i++) {
            const ch = line[i];
            if ((ch === '"' || ch === "'") && !inQuotes) {
                if (ch === "'") return line.slice(0, i);
                inQuotes = true; quoteChar = ch;
            } else if (inQuotes && ch === quoteChar && line[i - 1] !== "\\") {
                inQuotes = false;
            }
        }
        return line;
    }

    isTruthy(val) {
        if (typeof val === "number") return val !== 0;
        if (typeof val === "boolean") return val;
        if (typeof val === "string") return val.length > 0;
        return Boolean(val);
    }

    evalExpr(exprStr) {
        const tokens = this.tokenizeExpr(exprStr);
        let pos = 0;
        const peek = () => tokens[pos] || { type: "EOF" };
        const consume = () => tokens[pos++];

        const parseOr = () => {
            let left = parseAnd();
            while (peek().type === "KW" && peek().val === "OR") {
                consume();
                const right = parseAnd();
                left = (this.isTruthy(left) || this.isTruthy(right)) ? 1 : 0;
            }
            return left;
        };

        const parseAnd = () => {
            let left = parseNot();
            while (peek().type === "KW" && peek().val === "AND") {
                consume();
                const right = parseNot();
                left = (this.isTruthy(left) && this.isTruthy(right)) ? 1 : 0;
            }
            return left;
        };

        const parseNot = () => {
            if (peek().type === "KW" && peek().val === "NOT") {
                consume();
                return this.isTruthy(parseNot()) ? 0 : 1;
            }
            return parseCmp();
        };

        const parseCmp = () => {
            let left = parseAdd();
            const ops = ["=", "==", "<>", "!=", "<", ">", "<=", ">="];
            while (peek().type === "OP" && ops.includes(peek().val)) {
                const op = consume().val;
                const right = parseAdd();
                let res = false;
                if (op === "=" || op === "==") res = left === right;
                else if (op === "<>" || op === "!=") res = left !== right;
                else if (op === "<") res = left < right;
                else if (op === ">") res = left > right;
                else if (op === "<=") res = left <= right;
                else if (op === ">=") res = left >= right;
                left = res ? 1 : 0;
            }
            return left;
        };

        const parseAdd = () => {
            let left = parseMul();
            while (peek().type === "OP" && (peek().val === "+" || peek().val === "-")) {
                const op = consume().val;
                const right = parseMul();
                if (op === "+") {
                    left = (typeof left === "string" || typeof right === "string")
                        ? String(left) + String(right)
                        : left + right;
                } else {
                    left = Number(left) - Number(right);
                }
            }
            return left;
        };

        const parseMul = () => {
            let left = parsePow();
            while (peek().type === "OP" && (peek().val === "*" || peek().val === "/")) {
                const op = consume().val;
                const right = parsePow();
                if (op === "*") left = Number(left) * Number(right);
                else {
                    if (Number(right) === 0) throw new Error("Division by zero");
                    left = Number(left) / Number(right);
                }
            }
            return left;
        };

        const parsePow = () => {
            const base = parseUnary();
            if (peek().type === "OP" && peek().val === "^") {
                consume();
                return Math.pow(Number(base), Number(parsePow()));
            }
            return base;
        };

        const parseUnary = () => {
            if (peek().type === "OP" && peek().val === "-") { consume(); return -Number(parseUnary()); }
            if (peek().type === "OP" && peek().val === "+") { consume(); return +Number(parseUnary()); }
            return parsePrimary();
        };

        const parsePrimary = () => {
            const tok = peek();
            if (tok.type === "NUM") { consume(); return tok.val; }
            if (tok.type === "STR") { consume(); return tok.val; }
            if (tok.type === "LP") {
                consume();
                const val = parseOr();
                if (peek().type === "RP") consume();
                return val;
            }
            if (tok.type === "ID") {
                consume();
                const name = tok.val.toUpperCase();
                if (peek().type === "LP") {
                    consume();
                    const args = [];
                    if (peek().type !== "RP") {
                        args.push(parseOr());
                        while (peek().type === "COMMA") { consume(); args.push(parseOr()); }
                    }
                    if (peek().type === "RP") consume();
                    return this.callBuiltin(name, args);
                }
                if (name === "PI") return Math.PI;
                if (name === "E") return Math.E;
                if (name === "RND") return Math.random();
                return this.variables.hasOwnProperty(name) ? this.variables[name] : 0;
            }
            throw new Error("Unexpected token in expression");
        };

        return parseOr();
    }

    callBuiltin(name, args) {
        const a = Number(args[0] ?? 0);
        const b = Number(args[1] ?? 0);
        switch (name) {
            case "ABS": return Math.abs(a);
            case "SQR":
            case "SQRT": return Math.sqrt(a);
            case "SIN": return Math.sin(a);
            case "COS": return Math.cos(a);
            case "TAN": return Math.tan(a);
            case "ASIN": return Math.asin(a);
            case "ACOS": return Math.acos(a);
            case "ATAN": return Math.atan(a);
            case "ATAN2": return Math.atan2(a, b);
            case "LOG":
            case "LN": return Math.log(a);
            case "LOG10": return Math.log10(a);
            case "EXP": return Math.exp(a);
            case "INT":
            case "FLOOR": return Math.floor(a);
            case "FIX": return Math.trunc(a);
            case "CEIL": return Math.ceil(a);
            case "ROUND": {
                const d = args.length > 1 ? Math.pow(10, b) : 1;
                return Math.round(a * d) / d;
            }
            case "SGN": return Math.sign(a);
            case "MIN": return Math.min(...args.map(Number));
            case "MAX": return Math.max(...args.map(Number));
            case "DEG": return (a * 180) / Math.PI;
            case "RAD": return (a * Math.PI) / 180;
            case "RND": return args.length > 0 ? Math.floor(Math.random() * a) + 1 : Math.random();
            case "PI": return Math.PI;
            case "E": return Math.E;
            default: throw new Error(`Unknown function ${name}`);
        }
    }

    tokenizeExpr(str) {
        const out = [];
        let i = 0;
        while (i < str.length) {
            const ch = str[i];
            if (/\s/.test(ch)) { i++; continue; }
            if (ch === '"') {
                let s = "";
                i++;
                while (i < str.length && str[i] !== '"') {
                    if (str[i] === "\\" && i + 1 < str.length) {
                        i++;
                        s += str[i] === "n" ? "\n" : str[i] === "t" ? "\t" : str[i];
                    } else s += str[i];
                    i++;
                }
                i++;
                out.push({ type: "STR", val: s });
                continue;
            }
            if (/[0-9]/.test(ch) || (ch === "." && /[0-9]/.test(str[i + 1]))) {
                let n = "";
                while (i < str.length && /[0-9.]/.test(str[i])) n += str[i++];
                out.push({ type: "NUM", val: parseFloat(n) });
                continue;
            }
            if (/[A-Za-z_]/.test(ch)) {
                let id = "";
                while (i < str.length && /[A-Za-z0-9_$]/.test(str[i])) id += str[i++];
                const up = id.toUpperCase();
                if (up === "AND" || up === "OR" || up === "NOT") out.push({ type: "KW", val: up });
                else out.push({ type: "ID", val: id });
                continue;
            }
            const two = str.slice(i, i + 2);
            if (["==", "<>", "!=", "<=", ">="].includes(two)) { out.push({ type: "OP", val: two }); i += 2; continue; }
            if ("+-*/^=<>".includes(ch)) { out.push({ type: "OP", val: ch }); i++; continue; }
            if (ch === "(") { out.push({ type: "LP" }); i++; continue; }
            if (ch === ")") { out.push({ type: "RP" }); i++; continue; }
            if (ch === ",") { out.push({ type: "COMMA" }); i++; continue; }
            i++;
        }
        return out;
    }
}
