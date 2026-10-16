---
register: true
---
<%* tR = ''; -%>
---
tags:
  - monthly
prev:  <%`"[[${tp.date.now("YYYY-MM", "P-1M", tp.file.title)}]]"`%>
next:  <%`"[[${tp.date.now("YYYY-MM", "P}1M", tp.file.title)}]]"`%>
---

## On This Month
![[Daily.base#Monthly]]
