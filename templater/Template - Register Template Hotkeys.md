---
register: true
---
<%*
tR = '';
const pluginId = 'templater-obsidian';
const plugin = tp.app.plugins.plugins[pluginId];

if (!plugin) {
    new Notice('Templater plugin not found!', 5000);
    return;
}

// Use the template file path (not the newly created file) to exclude self
const thisTemplate = tp.config.template_file?.path;

const discovered = tp.app.vault.getMarkdownFiles()
    .filter(f => {
        if (!f.path.startsWith('meta/templater/')) return false;
        return tp.app.metadataCache.getFileCache(f)?.frontmatter?.register !== false;
    })
    .map(f => f.path);

const existing = plugin.settings.enabled_templates_hotkeys ?? [];
const templates = [...new Set([...existing, ...discovered])].sort();

plugin.settings.enabled_templates_hotkeys = templates;
await plugin.save_settings();

new Notice(`Registered ${templates.length} template hotkeys. Reloading Templater...`);

const createdFilePath = tp.file.path(true);

setTimeout(async () => {
    await tp.app.plugins.disablePlugin(pluginId);
    await tp.app.plugins.enablePlugin(pluginId);
    new Notice('Templater reloaded!');
    const createdFile = tp.app.vault.getAbstractFileByPath(createdFilePath);
    if (createdFile) await tp.app.vault.trash(createdFile, true);
}, 500);
-%>
``