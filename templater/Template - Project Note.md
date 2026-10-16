---
register: true
---
<%*
tR = '';
const status = await tp.system.suggester(
    t => t,
    ["active", "waiting", "done"],
    false,
    "Status..."
);
const today = tp.date.now("YYYY-MM-DD");
await tp.file.move(`projects/projects/${tp.file.title}`);
-%>
---
category: "[[Projects]]"
start: <% today %>
last: <% today %>
status: <% status ?? "active" %>
controls:
  status: any
---

## Tasks with `INPUT[inlineSelect(option(active),option(done),option(waiting),option(to do),option(any),defaultValue(any)):controls.status]`Status

![[Tasks.base]]

## Reference Notes

![[Notes.base]]

## Latest Events

![[Events.base#By Project]]
