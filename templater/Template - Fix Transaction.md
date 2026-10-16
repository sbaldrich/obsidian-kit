---
register: false
---
<%*
tR = '';
// 1. Validate current note is a transaction
const currentFile = tp.file.find_tfile(tp.file.path(true));
const frontmatter = app.metadataCache.getFileCache(currentFile)?.frontmatter;

if (!frontmatter || frontmatter.category !== "[[Financial Transactions]]") {
    throw new Error("This template can only be used on Financial Transaction notes.");
}

// 2. Read current file content to preserve body
const currentContent = await app.vault.read(currentFile);

// Extract body (everything after the closing --- of frontmatter)
let bodyContent = '';
const frontmatterEndMatch = currentContent.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
if (frontmatterEndMatch) {
    bodyContent = frontmatterEndMatch[1];
}

// 3. Parse folder path to extract year and month
const filePath = tp.file.path(true);
// Expected pattern: projects/transactions/YYYY/YYYYMM/filename.md
const pathMatch = filePath.match(/projects\/transactions\/(\d{4})\/(\d{6})\//);

if (!pathMatch) {
    throw new Error("Transaction note is not in expected folder structure: projects/transactions/YYYY/YYYYMM/");
}

const year = pathMatch[1];     // e.g., "2026"
const yearMonth = pathMatch[2]; // e.g., "202601"
const month = yearMonth.slice(4, 6); // Extract MM from YYYYMM

// 4. Construct date with day = 10
const day = "10";
const correctedDate = `${year}-${month}-${day}`; // e.g., "2026-01-10"
const mmdd = month + day; // e.g., "0110"

// 5. Get parent name from frontmatter
const parentsProperty = frontmatter.parents;
const firstParent = Array.isArray(parentsProperty) ? parentsProperty[0] : parentsProperty;
let parentName = '';

if (firstParent) {
    parentName = firstParent.replace(/[\[\]]/g, '');
} else {
    throw new Error("Transaction note is missing parents property.");
}

// 6. Generate new filename
const newFilename = `${mmdd} - ${parentName}`;

// 7. Build new content with corrected frontmatter + original body
const newContent = `---
category: "[[Financial Transactions]]"
created: ${frontmatter.created || tp.date.now()}
parents:
${(Array.isArray(frontmatter.parents) ? frontmatter.parents : [frontmatter.parents]).map(p => `  - "${p}"`).join('\n')}
date: ${correctedDate}
amount: ${frontmatter.amount || ''}
currency: ${frontmatter.currency || 'EUR'}
payee: ${frontmatter.payee ? `"${frontmatter.payee}"` : '""'}
method: ${frontmatter.method || ''}
type: ${frontmatter.type || ''}
status: ${frontmatter.status || 'pending'}
tags:
  - transaction
---
${bodyContent}`;

// 8. Write new content and rename file
await app.vault.modify(currentFile, newContent);
await tp.file.rename(newFilename);
-%>
