---
register: true
---
<%*
tR = '';

const name = await tp.system.prompt("Name");
if (!name) return;

const alias = await tp.system.prompt("Alias", name);
const relation = await tp.system.suggester(
    t => t,
    ["friends", "family", "business", "colleague", "acquaintance"],
    false,
    "Relation..."
);

await tp.file.rename(name);
await tp.file.move(`projects/people/${name}`);

tR += `---
category: "[[People]]"
start: ${tp.date.now("YYYY-MM-DD")}
last: ${tp.date.now("YYYY-MM-DD")}
name: ${name}
alias: ${alias}
relation: ${relation ?? ""}
---
`;
%>
