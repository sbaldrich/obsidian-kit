Cross-note queries for scenarios 2 and 3. Untested: syntax may need tweaks.

## All tasks in progress, across projects

Expected: Order seedlings (Orchard), Pot herbs (Greenhouse), and the checkbox
in the other places those notes appear.

```dataview
TASK
WHERE status = "/"
```

## Open or in progress, grouped by project note

Watch the group heading: does the task's `status` get confused with the
project's `status` property?

```dataview
TASK
FROM "projects"
WHERE !completed AND status != "-"
GROUP BY file.link
```

## Table: task note, checkbox, and the linked note's properties

Needs the join, so it uses dataviewjs.

```dataviewjs
const rows = dv.pages('"projects"')
  .where(p => p.type === "project")
  .file.tasks
  .where(t => t.outlinks.length > 0)
  .map(t => {
    const note = dv.page(t.outlinks[0].path);
    return [t.outlinks[0], t.status === " " ? "todo" : t.status, note?.type, note?.project];
  });
dv.table(["Task", "Checkbox", "Note type", "Project"], rows);
```

## Scenario 3: task notes with more than one checkbox

Expected: Order seedlings, with `/` in Orchard and `x` in the daily note.

```dataviewjs
const byNote = {};
for (const t of dv.pages().file.tasks.where(t => t.outlinks.length > 0)) {
  const target = t.outlinks[0].path;
  (byNote[target] ??= []).push(`${t.status === " " ? "todo" : t.status} in ${t.path}`);
}
dv.table(
  ["Task note", "Checkboxes"],
  Object.entries(byNote)
    .filter(([, v]) => v.length > 1)
    .map(([k, v]) => [dv.fileLink(k), v.join("; ")])
);
```
