---
register: true
---
<%*
tR = '';

const status = await tp.system.suggester(
    t => t,
    ["backlog", "in_progress", "done"],
    false,
    "Status..."
);

const rating = await tp.system.prompt("Rating (1-5)", "");
const today = tp.date.now("YYYY-MM-DD");

await tp.file.move(`movies/${tp.file.title}`);

tR += `---
category: "[[Movies]]"
start: ${today}
last: ${today}
status: ${status ?? "backlog"}
rating: ${rating ?? ""}
---
`;
%>
