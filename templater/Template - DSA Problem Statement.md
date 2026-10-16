---
register: true
---
<%* tR = ''; -%>
---
category: "[[Coding Tasks]]"
created: <%tp.date.now()%>
source: <% await tp.user.util.suggestByCategory(tp, "Online Judges", "Source...") %>
link: <%await tp.system.prompt('Problem link')%>
---
## Statement


## Constraints

