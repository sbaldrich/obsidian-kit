---
register: true
---
<%*
tR = '';

async function listFileNames(folder) {
    const items = await app.vault.adapter.list(folder);
    let allFiles = items.files.map(f => f.split('/').pop().replace('.md', ''));
    for (const subfolder of items.folders) {
        const subItems = await listFileNames(subfolder);
        allFiles = allFiles.concat(subItems);
    }
    return allFiles;
}

async function ensureFolder(path) {
    if (!(await app.vault.adapter.exists(path))) {
        await app.vault.adapter.mkdir(path);
    }
}

async function multiSelect(options, placeholder) {
    let selections = [];
    while (true) {
        const choice = await tp.system.suggester(
            t => t,
            [...options, "✅ Done"],
            false,
            placeholder,
            10
        );
        if (choice === "✅ Done" || choice === null) break;
        if (!selections.includes(choice)) selections.push(choice);
    }
    return selections;
}

const peopleFolder = "projects/people";
const peopleNames = await listFileNames(peopleFolder);

let people = [];
if (peopleNames.length > 0) {
    people = await multiSelect(peopleNames, "People...");
}

const today = moment();
const created = today.format('YYYY-MM-DD');

// Optional: approximate date when the memory occurred
const rawStart = await tp.system.prompt("When did this happen? (YYYY-MM-DD, leave blank if unknown)", "");
const start = rawStart?.trim();

// Use start date for folder/prefix if provided, else fall back to today
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
let currentTitle = tp.file.title;
if (!currentTitle.startsWith(datePrefix)) {
    currentTitle = `${datePrefix}${currentTitle}`;
    await tp.file.rename(currentTitle);
}

await tp.file.move(`${monthFolder}/${currentTitle}`);

let frontmatter = `---
category: "[[Memories]]"
created: "[[${created}]]"
`;

if (start) {
    frontmatter += `start: "[[${start}]]"\n`;
}

if (people.length > 0) {
    frontmatter += `people:\n`;
    people.forEach(p => {
        frontmatter += `  - "[[${p}]]"\n`;
    });
}

frontmatter += `---\n`;

tR += frontmatter;
%>
