---
register: true
---
<%*
tR = '';
/* --- Helper Functions --- */
	
// List file names (without extensions) in a given folder
async function listFileNames(folder) {
    const items = await app.vault.adapter.list(folder);
    let allFiles = items.files.map(f => f.split('/').pop().replace('.md', ''));

    // Check subfolders
    for (const subfolder of items.folders) {
        const subItems = await listFileNames(subfolder);
        allFiles = allFiles.concat(subItems);
    }

    return allFiles.map(f => f.split('/').pop().replace('.md', ''));
}

// Ensure a folder exists
async function ensureFolder(path) {
    if (!(await app.vault.adapter.exists(path))) {
        await app.vault.adapter.mkdir(path);
    }
}

// Multi-suggester using a manual loop
async function multiSelect(options) {
    let selections = [];
    while (true) {
        const choice = await tp.system.suggester(
            t => t,
            [...options, "✅ Done"],
            false,
            "Participants...",
            10
        );
        if (choice === "✅ Done" || choice === null) {
            break;
        }
        if (!selections.includes(choice)) {
            selections.push(choice);
        }
    }
    return selections;
}

// Check if title already starts with DDMM - 
function hasDatePrefix(title, day, month) {
    const prefix = `${day}${month} - `;
    return title.startsWith(prefix);
}

/* --- Main Script --- */

// Load people and project options
const peopleFolder = "people";
const projectFolder = "projects/projects";

const peopleNames = await listFileNames(peopleFolder);
const projectNames = await listFileNames(projectFolder);

// Select participants (allow multiple selections)
let participants = [];
if (peopleNames.length > 0) {
    participants = await multiSelect(peopleNames);
}

// Select a single project (optional)
let project = null;
if (projectNames.length > 0) {
    project = await tp.system.suggester(t => t, projectNames, false, "Project...");
}

// Select event type
const eventType = await tp.system.suggester(
    t => t,
    ["update", "milestone", "memory"],
    false,
    "Event type..."
);

// Ask user for the event date (default: today)
const today = moment();
const defaultDate = today.format('YYYY-MM-DD');
const rawDate = await tp.system.prompt("Event date", defaultDate);
const eventDate = moment(rawDate, 'YYYY-MM-DD');

const year = eventDate.format('YYYY');
const month = eventDate.format('MM');
const day = eventDate.format('DD');
const isoDate = eventDate.format('YYYY-MM-DD');

// Set folder paths
const baseFolder = "records/events";
const yearFolder = `${baseFolder}/${year}`;
const monthFolder = `${yearFolder}/${year}${month}`;

// Ensure folders exist
await ensureFolder(yearFolder);
await ensureFolder(monthFolder);

// Rename the file if needed
let currentTitle = tp.file.title;
const datePrefix = `${day}${month} - `;

if (!hasDatePrefix(currentTitle, day, month)) {
    currentTitle = `${datePrefix}${currentTitle}`;
    await tp.file.rename(currentTitle);
}

// Move the file
await tp.file.move(`${monthFolder}/${currentTitle}`);

// Build frontmatter
let frontmatter = `---
category: "[[Events]]"
start: ${isoDate}
last: "${isoDate}
type: ${eventType ?? ""}
`;

if (participants.length > 0) {
    frontmatter += `participants:\n`;
    participants.forEach(p => {
        frontmatter += `  - "[[${p}]]"\n`;
    });
}

if (project) {
    frontmatter += `project: "[[${project}]]"\n`;
}

frontmatter += `---\n`;

tR += frontmatter;
%>
