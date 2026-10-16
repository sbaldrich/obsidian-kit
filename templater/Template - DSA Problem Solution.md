---
register: true
---
<%* tR = ''; -%>
---
category: "[[Coding Tasks]]"
created: <%tp.date.now()%>
parents:
  - <% await tp.user.util.suggestByCategory(tp, "Coding Tasks", "Problem...") %>
tags:
- solution
---

# Key invariant / idea:

## Optimal Complexity: 

## Gotchas:

## Sample Code

<%* await tp.user.util.moveTo(tp, 'reference') %>