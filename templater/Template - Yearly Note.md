---
register: true
---
<%* tR = ''; await tp.file.move(`yearly/${tp.file.title}`); -%>
---
category: "[[Yearly Notes]]"
start: <% tp.date.now("YYYY-MM-DD") %>
last: <% tp.date.now("YYYY-MM-DD") %>
---
