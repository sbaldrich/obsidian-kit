---
register: false
---
<%* tR = ''; -%>
---
<%* let techs = await tp.user.util.suggestByCategory(tp, "Companies", "companies...", true) 
techs = techs.map(t => `  - "[[${t}]]"`).join("\n")-%>
companies: 
<%techs%>
---
