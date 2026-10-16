---
register: true
---
<%*
tR = '';

const category = await tp.system.prompt("Category");
const today = tp.date.now("YYYY-MM-DD");

tR += `---
category: "[[${category ?? ""}]]"
tags:
  - review
  - srs
start: ${today}
last: ${today}
---

## Flashcards
`;
%>
