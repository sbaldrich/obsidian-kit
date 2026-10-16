---
register: true
---
<%*
tR = '';

async function ensureFolder(path) {
    if (!(await app.vault.adapter.exists(path))) {
        await app.vault.adapter.mkdir(path);
    }
}

const currentFile = tp.file.find_tfile(tp.file.path(true));
const fm = app.metadataCache.getFileCache(currentFile)?.frontmatter;

if (!fm || fm.category !== "[[Events]]" || fm.type !== "memory") {
    new Notice("This note is not an Event with type: memory", 5000);
    return;
}

const currentContent = await app.vault.read(currentFile);
const bodyMatch = currentContent.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
const body = bodyMatch ? bodyMatch[1] : '';

// preserve start (strip wikilink brackets for rebuilding)
const start = (fm.start ?? "").replace(/\[\[|\]\]/g, '').trim() || null;

// participants → people
const rawParticipants = fm.participants ?? [];
const participants = Array.isArray(rawParticipants) ? rawParticipants : [rawParticipants];

// Strip DDMM - prefix from filename
const suggestedTitle = tp.file.title.replace(/^\d{4} - /, '');
const newTitle = await tp.system.prompt("Memory title", suggestedTitle);
if (!newTitle) return;

const today = moment();
const created = today.format('YYYY-MM-DD');

// Use event's start date for folder/prefix if available, else today
const dateForPath = start ? moment(start, 'YYYY-MM-DD') : today;
const pathYear = dateForPath.format('YYYY');
const pathMonth = dateForPath.format('MM');
const pathDay = dateForPath.format('DD');

const baseFolder = "projects/memories";
const yearFolder = `${baseFolder}/${pathYear}`;
const monthFolder = `${yearFolder}/${pathYear}${pathMonth}`;

await ensureFolder(yearFolder);
await ensureFolder(monthFolder);

const datePrefix = `${pathDay}${pathMonth} - `;
const prefixedTitle = newTitle.startsWith(datePrefix) ? newTitle : `${datePrefix}${newTitle}`;

let frontmatter = `---
category: "[[Memories]]"
created: "[[${created}]]"
`;

if (start) {
    frontmatter += `start: "[[${start}]]"\n`;
}

if (participants.length > 0) {
    frontmatter += `people:\n`;
    participants.forEach(p => {
        frontmatter += `  - "${p}"\n`;
    });
}

frontmatter += `---\n`;

await app.vault.modify(currentFile, frontmatter + body);
await tp.file.rename(prefixedTitle);
await tp.file.move(`${monthFolder}/${prefixedTitle}`);
-%>
