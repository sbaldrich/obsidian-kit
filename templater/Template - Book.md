---
register: true
---
<%*
tR = '';

const type = await tp.system.suggester(
    t => t,
    ["book", "audiobook", "manga"],
    false,
    "Type..."
);

const status = await tp.system.suggester(
    t => t,
    ["backlog", "in_progress", "done"],
    false,
    "Status..."
);

const rating = await tp.system.prompt("Rating (1-5)", "");
const cover = await tp.system.prompt("Cover URL", "");
const today = tp.date.now("YYYY-MM-DD");

await tp.file.move(`books/${tp.file.title}`);

tR += `---
category: "[[Books]]"
type: ${type ?? "book"}
start: ${today}
last: ${today}
status: ${status ?? "backlog"}
rating: ${rating ?? ""}
cover: ${cover ?? ""}
---
`;
%>
