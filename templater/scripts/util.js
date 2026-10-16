// Ensure a folder exists
async function ensureFolder(path) {
    if (!(await app.vault.adapter.exists(path))) {
        await app.vault.adapter.mkdir(path);
    }
}

// Check if title already starts with DDMM - 
function hasDatePrefix(title, day, month) {
    const prefix = `${day}${month} - `;
    return title.startsWith(prefix);
}

async function moveToEventDirectory(tp, newTitle = tp.file.title, rename = true){
    // Get today's date parts
    const today = moment();
    const year = today.format('YYYY');
    const month = today.format('MM');
    const day = today.format('DD');

    // Set folder paths
    const baseFolder = "projects/events";
    const yearFolder = `${baseFolder}/${year}`;
    const monthFolder = `${yearFolder}/${year}${month}`;

    // Ensure folders exist
    await ensureFolder(yearFolder);
    await ensureFolder(monthFolder);

    // Rename the file if needed
    const datePrefix = `${day}${month} - `;

    if (rename && !hasDatePrefix(newTitle, day, month)) {
        newTitle = `${datePrefix}${newTitle}`;
    }
    await tp.file.rename(newTitle);
    // Move the file
    await tp.file.move(`${monthFolder}/${newTitle}`);
}

/**
 * Find note basenames that have `category: [[<category>]]` in YAML frontmatter.
 *
 * Searches the entire vault’s markdown files via `metadataCache`.
 *
 * @param {TP} tp - Templater API (auto-injected when called as `tp.user...`).
 * @param {string} category - The category page title (without brackets).
 * @returns {string[]} An array of basenames (no `.md`).
 * @example
 * const options = tp.user.my_script.findByCategory("Events");
 * const pick = await tp.system.suggester(options, options);
 */
function findByCategory(tp, category){

    const files = tp.app.vault.getMarkdownFiles();
    const metadataCache = tp.app.metadataCache;
    
    const matches = [];
    for (const f of files) {
        const cache = metadataCache.getFileCache(f);
        const fm = cache?.frontmatter;
        if (!fm) continue;
        if (fm["category"] && fm["category"] == `[[${category}]]` && !f.name.contains('Template')){
            matches.push(f.basename) // don't want the .md in the options
        }
    }
    return matches
}

async function moveTo(tp, location){
    await tp.file.move(`${location}/${tp.file.title}`);
}

async function suggestByCategory(tp, category, prompt = "Value...", multi = false){
    const matches = findByCategory(tp, category);
    const f = multi ? tp.system.multi_suggester : tp.system.suggester;
    return await f(
      t => t,
      matches,
      false,
      prompt,
      10)
}

async function suggestAllNotes(tp, prompt = "Value..."){
    const files = tp.app.vault.getMarkdownFiles();
    const fileNames = files.map(f => f.basename);

    const selected = await tp.system.suggester(
        name => name,
        fileNames,
        false,
        prompt,
        10);

    return `[[${selected}]]`;
}

module.exports = {
    findByCategory,
    suggestByCategory,
    moveToEventDirectory,
    suggestAllNotes,
    moveTo,
};

