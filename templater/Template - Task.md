---
register: true
---
<%*
tR = '';

/* const period = await tp.system.prompt("Period", "1d");
const category = await tp.system.suggester(
    t => t,
    ["ktlo", "house", "health"],
    false,
    "Category..."
);*/

const today = tp.date.now("YYYY-MM-DD");

await tp.file.move(`tasks/${tp.file.title}`);

tR += `---
created: ${today}
last: ${today}
status: active
tags:
  - task
---
`;
%>
