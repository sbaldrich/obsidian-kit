---
register: true
---
<%*
tR = '';
const currentFile = tp.file.find_tfile(tp.file.path(true));
const frontmatter = app.metadataCache.getFileCache(currentFile)?.frontmatter;

if (!frontmatter?.tags?.includes('weekly')) {
    throw new Error("This template can only be used on weekly notes.");
}

const weekNum = frontmatter.week;
const year = frontmatter.year;
const planNoteName = `Week ${weekNum} - Plan`;
const planNotePath = `weekly/${planNoteName}.md`;

const existingPlan = tp.app.vault.getAbstractFileByPath(planNotePath);
if (!existingPlan) {
    const planContent = `---\ntags:\n  - weekly-plan\nweek: ${weekNum}\nyear: ${year}\nweekly_note: "[[Week ${weekNum}]]"\n---\n\n## To-Do\n\n- [ ] \n\n## Notes\n\n`;
    await tp.file.create_new(planContent, planNoteName, false, 'weekly');
}

const currentContent = await app.vault.read(currentFile);
if (currentContent.includes('## Plan')) {
    new Notice(`Week ${weekNum} already has a Plan section.`, 3000);
    return;
}

const updatedContent = currentContent.replace(
    '## On This Week',
    `## Plan\n![[${planNoteName}]]\n\n## On This Week`
);

await app.vault.modify(currentFile, updatedContent);
new Notice(`Migrated Week ${weekNum} — plan note ${existingPlan ? 'already existed' : 'created'}.`, 2000);
-%>
