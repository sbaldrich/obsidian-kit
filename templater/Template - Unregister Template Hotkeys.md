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

plugin.settings.enabled_templates_hotkeys = [];
await plugin.save_settings();

new Notice('Unregistered all template hotkeys. Reloading Templater...');

const createdFilePath = tp.file.path(true);

setTimeout(async () => {
    await tp.app.plugins.disablePlugin(pluginId);
    await tp.app.plugins.enablePlugin(pluginId);
    new Notice('Templater reloaded!');
    const createdFile = tp.app.vault.getAbstractFileByPath(createdFilePath);
    if (createdFile) await tp.app.vault.trash(createdFile, true);
}, 500);
-%>
