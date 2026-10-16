---
register: false
---
<%* tR = '';

const files = app.vault.getMarkdownFiles();
let selections = [];
while (true) {
    const remaining = files.filter(f => !selections.find(s => s.path === f.path));
    const choice = await tp.system.suggester(
        t => t.basename,
        [...remaining, null],
        false,
        selections.length === 0 ? "Select parent note..." : "Add another parent (cancel to finish)"
    );
    if (!choice) break;
    selections.push(choice);
}

if (selections.length === 0) return;
-%>
---
parents:
<%* selections.forEach(f => { tR += `  - "[[${f.basename}]]"\n`; }); -%>
---
