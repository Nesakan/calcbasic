/**
 * Inpro Coder — UI Controller
 */
document.addEventListener("DOMContentLoaded", () => {
    const library = new ProgramLibrary();
    const runner = new CalcBasicRunner();

    // State
    let editorDirty = false;
    let isCreatingNew = false;
    let pendingInputResolver = null;

    // Elements
    const sidebarCount = document.getElementById("sidebarCount");
    const toastEl = document.getElementById("toast");

    // User Menu
    const userTrigger = document.getElementById("userTrigger");
    const userDropdown = document.getElementById("userDropdown");
    userTrigger.addEventListener("click", () => {
        const open = !userDropdown.hidden;
        userDropdown.hidden = open;
        userTrigger.setAttribute("aria-expanded", String(!open));
    });
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".user-menu-wrap")) {
            userDropdown.hidden = true;
            userTrigger.setAttribute("aria-expanded", "false");
        }
    });
    document.getElementById("btnLogout").addEventListener("click", () => {
        userDropdown.hidden = true;
        showToast("Authentication will be wired in the next phase.");
    });

    function showToast(msg) {
        toastEl.textContent = msg;
        toastEl.classList.add("show");
        clearTimeout(showToast._t);
        showToast._t = setTimeout(() => toastEl.classList.remove("show"), 2600);
    }

    function switchView(viewName) {
        document.querySelectorAll(".nav-btn").forEach(b => {
            b.classList.toggle("active", b.dataset.view === viewName);
        });
        document.querySelectorAll(".view").forEach(v => {
            v.classList.toggle("active", v.id === `view-${viewName}`);
        });

        if (viewName === "programs") renderPrograms();
        if (viewName === "create") syncEditor();
        if (viewName === "run") syncRunView();
    }

    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    function refreshGlobalContext() {
        sidebarCount.textContent = `${library.getAll().length} Saved`;
    }

    // ==================== VIEW 1: PROGRAMS ====================
    const programsGrid = document.getElementById("programsGrid");
    const programSearch = document.getElementById("programSearch");

    programSearch.addEventListener("input", renderPrograms);

    document.getElementById("btnNewProgram").addEventListener("click", () => {
        isCreatingNew = true;
        editorDirty = false;
        switchView("create");
    });

    function renderPrograms() {
        refreshGlobalContext();
        const query = programSearch.value.trim().toLowerCase();
        const list = library.getAll().filter(p =>
            !query || p.name.toLowerCase().includes(query) || p.code.toLowerCase().includes(query)
        );
        const active = library.getActive();

        programsGrid.innerHTML = "";
        if (list.length === 0) {
            programsGrid.innerHTML = `<div class="panel-card" style="grid-column: 1 / -1;"><p class="muted">No programs found. Click "+ New Program" to create one.</p></div>`;
            return;
        }

        list.forEach(prog => {
            const isEmpty = !prog.code.trim();
            const lineCount = isEmpty ? 0 : prog.code.split(/\r?\n/).length;
            const isActive = active && active.id === prog.id;

            const card = document.createElement("article");
            card.className = `prog-card ${isActive ? "active-slot" : ""}`;
            card.innerHTML = `
                <div class="prog-card-top">
                    <div class="prog-title">
                        <span>${escapeHtml(prog.name)}</span>
                    </div>
                    <span class="prog-meta">${lineCount} lines</span>
                </div>
                <div class="prog-preview ${isEmpty ? "empty" : ""}">${isEmpty ? "// Empty program" : escapeHtml(prog.code)}</div>
                <div class="prog-card-actions">
                    <button class="btn primary sm" data-act="run" data-id="${prog.id}" ${isEmpty ? "disabled" : ""}>Run ▶</button>
                    <button class="btn secondary sm" data-act="edit" data-id="${prog.id}">Edit</button>
                    <button class="btn secondary sm" data-act="download" data-id="${prog.id}">.bas</button>
                    <button class="btn danger sm" data-act="delete" data-id="${prog.id}">Delete</button>
                </div>
            `;
            programsGrid.appendChild(card);
        });
    }

    programsGrid.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-act]");
        if (!btn) return;
        const id = btn.dataset.id;
        const act = btn.dataset.act;
        const prog = library.getById(id);
        if (!prog) return;

        if (act === "run") {
            library.setActive(id);
            switchView("run");
            startProgramRun();
        } else if (act === "edit") {
            library.setActive(id);
            isCreatingNew = false;
            editorDirty = false;
            switchView("create");
        } else if (act === "download") {
            const fname = prog.name.toLowerCase().replace(/[^a-z0-9_-]+/g, "_") || "program";
            downloadBlob(`${fname}.bas`, prog.code, "text/plain");
            showToast(`Downloaded ${fname}.bas`);
        } else if (act === "delete") {
            library.remove(id);
            showToast(`Deleted "${prog.name}"`);
            renderPrograms();
        }
    });

    // ==================== VIEW 2: CREATE ====================
    const codeEditor = document.getElementById("codeEditor");
    const lineGutter = document.getElementById("lineGutter");
    const editorNameInput = document.getElementById("editorNameInput");

    function updateGutter() {
        const count = codeEditor.value.split(/\r?\n/).length;
        let out = "";
        for (let i = 1; i <= count; i++) out += i + "\n";
        lineGutter.textContent = out;
    }

    function syncEditor() {
        if (isCreatingNew) {
            editorNameInput.value = "";
            codeEditor.value = "";
        } else {
            const active = library.getActive();
            editorNameInput.value = active ? active.name : "";
            codeEditor.value = active ? active.code : "";
        }
        editorDirty = false;
        updateGutter();
        refreshGlobalContext();
    }

    codeEditor.addEventListener("input", () => {
        editorDirty = true;
        updateGutter();
        refreshGlobalContext();
    });

    editorNameInput.addEventListener("input", () => {
        editorDirty = true;
        refreshGlobalContext();
    });

    codeEditor.addEventListener("scroll", () => {
        lineGutter.scrollTop = codeEditor.scrollTop;
    });

    document.querySelectorAll(".chip[data-insert]").forEach(chip => {
        chip.addEventListener("click", () => {
            const text = chip.dataset.insert;
            const start = codeEditor.selectionStart;
            const end = codeEditor.selectionEnd;
            const val = codeEditor.value;
            codeEditor.value = val.slice(0, start) + text + val.slice(end);
            codeEditor.selectionStart = codeEditor.selectionEnd = start + text.length;
            codeEditor.focus();
            editorDirty = true;
            updateGutter();
            refreshGlobalContext();
        });
    });

    function saveEditorProgram() {
        const name = editorNameInput.value.trim() || "Untitled Program";
        const code = codeEditor.value;
        let saved;
        if (isCreatingNew || !library.getActive()) {
            saved = library.create(name, code);
            isCreatingNew = false;
        } else {
            saved = library.update(library.getActive().id, name, code);
        }
        editorDirty = false;
        refreshGlobalContext();
        return saved;
    }

    document.getElementById("btnEditorSave").addEventListener("click", () => {
        const saved = saveEditorProgram();
        showToast(`Saved "${saved.name}"`);
    });

    document.getElementById("btnEditorSaveRun").addEventListener("click", () => {
        saveEditorProgram();
        switchView("run");
        startProgramRun();
    });

    document.getElementById("btnEditorClear").addEventListener("click", () => {
        codeEditor.value = "";
        editorDirty = true;
        updateGutter();
        refreshGlobalContext();
    });

    // ==================== IMPORT / EXPORT (IN PROGRAMS) ====================
    document.getElementById("btnDownloadAll").addEventListener("click", () => {
        const payload = JSON.stringify({
            format: "INPRO_CODER_BACKUP",
            exportedAt: new Date().toISOString(),
            programs: library.getAll()
        }, null, 2);
        downloadBlob("inpro_coder_programs.json", payload, "application/json");
        showToast("Exported all programs");
    });

    document.getElementById("fileImportInput").addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
            const text = String(reader.result || "");
            if (file.name.endsWith(".json")) {
                try {
                    const parsed = JSON.parse(text);
                    if (parsed.programs && Array.isArray(parsed.programs)) {
                        const count = library.importAll(parsed.programs);
                        showToast(`Imported ${count} programs`);
                        renderPrograms();
                        return;
                    }
                } catch (err) { /* fallthrough */ }
            }
            const cleanName = file.name.replace(/\.[^.]+$/, "");
            library.create(cleanName, text);
            showToast(`Imported "${cleanName}"`);
            renderPrograms();
        };
        reader.readAsText(file);
        e.target.value = "";
    });

    // ==================== VIEW 4: RUN MODE ====================
    const runProgramSelect = document.getElementById("runProgramSelect");
    const consoleOutput = document.getElementById("consoleOutput");
    const consoleInputForm = document.getElementById("consoleInputForm");
    const consoleInput = document.getElementById("consoleInput");
    const inputPromptLabel = document.getElementById("inputPromptLabel");
    const runStatusText = document.getElementById("runStatusText");
    const runStateBadge = document.getElementById("runStateBadge");
    const btnRunStart = document.getElementById("btnRunStart");
    const btnRunStop = document.getElementById("btnRunStop");
    const varsPanel = document.getElementById("varsPanel");
    const varsList = document.getElementById("varsList");
    const btnToggleVars = document.getElementById("btnToggleVars");

    function syncRunView() {
        runProgramSelect.innerHTML = "";
        library.getAll().forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.id;
            opt.textContent = p.name;
            runProgramSelect.appendChild(opt);
        });
        const active = library.getActive();
        if (active) runProgramSelect.value = active.id;
        refreshGlobalContext();
    }

    runProgramSelect.addEventListener("change", () => {
        library.setActive(runProgramSelect.value);
        refreshGlobalContext();
    });

    function appendConsole(text, cls = "output") {
        const div = document.createElement("div");
        div.className = `log-line ${cls}`;
        div.textContent = text;
        consoleOutput.appendChild(div);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }

    runner.onPrint = (text, cls) => appendConsole(text, cls);
    runner.onStatus = (status, state) => {
        runStatusText.textContent = status;
        runStateBadge.textContent = status;
    };
    runner.onVarsChange = (vars) => {
        const keys = Object.keys(vars);
        btnToggleVars.textContent = `Variables (${keys.length})`;
        varsList.innerHTML = keys.length === 0
            ? `<div class="muted">No variables set yet.</div>`
            : keys.map(k => `<div class="var-row"><span class="var-k">${escapeHtml(k)}</span><span class="var-v">${escapeHtml(String(vars[k]))}</span></div>`).join("");
    };

    runner.onInputRequest = (promptText) => {
        return new Promise((resolve) => {
            appendConsole(promptText, "output");
            runStatusText.textContent = "WAITING FOR INPUT";
            runStateBadge.textContent = "INPUT";
            consoleInputForm.classList.add("awaiting-input");
            inputPromptLabel.textContent = "?";
            consoleInput.placeholder = "Enter input value and press EXE...";
            consoleInput.focus();
            pendingInputResolver = resolve;
        });
    };

    async function startProgramRun() {
        if (runner.running) return;
        const active = library.getActive();
        if (!active || !active.code.trim()) {
            appendConsole("Selected program is empty.", "system");
            return;
        }
        btnRunStart.disabled = true;
        btnRunStop.disabled = false;
        appendConsole(`--- RUN: ${active.name} ---`, "system");

        await runner.run(active.code);

        if (pendingInputResolver) {
            pendingInputResolver("");
            pendingInputResolver = null;
        }
        consoleInputForm.classList.remove("awaiting-input");
        inputPromptLabel.textContent = ">";
        consoleInput.placeholder = 'Type INPUT response or quick expression (e.g. PRINT 2+2, SQRT(16))...';
        btnRunStart.disabled = false;
        btnRunStop.disabled = true;
    }

    btnRunStart.addEventListener("click", startProgramRun);
    btnRunStop.addEventListener("click", () => {
        runner.stop();
        if (pendingInputResolver) {
            pendingInputResolver("");
            pendingInputResolver = null;
        }
    });
    document.getElementById("btnRunClear").addEventListener("click", () => {
        consoleOutput.innerHTML = "";
    });

    btnToggleVars.addEventListener("click", () => { varsPanel.hidden = !varsPanel.hidden; });
    document.getElementById("btnCloseVars").addEventListener("click", () => { varsPanel.hidden = true; });

    consoleInputForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const val = consoleInput.value;
        consoleInput.value = "";

        if (pendingInputResolver) {
            appendConsole(`? ${val}`, "input-echo");
            const res = pendingInputResolver;
            pendingInputResolver = null;
            consoleInputForm.classList.remove("awaiting-input");
            inputPromptLabel.textContent = ">";
            runStatusText.textContent = "RUNNING";
            runStateBadge.textContent = "RUNNING";
            res(val);
            return;
        }

        const cmd = val.trim();
        if (!cmd) return;
        appendConsole(`> ${cmd}`, "input-echo");

        if (/^RUN$/i.test(cmd)) { startProgramRun(); return; }

        try {
            const expr = /^PRINT\s+/i.test(cmd) ? cmd.slice(6) : cmd;
            appendConsole(String(runner.evalExpr(expr)), "output");
        } catch (err) {
            appendConsole(`Error: ${err.message}`, "error");
        }
    });

    function downloadBlob(filename, content, mime) {
        const blob = new Blob([content], { type: mime });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    renderPrograms();
});
