---
register: false
---
<%* tR = ''; -%>
---
<%* let techs = await tp.user.util.suggestByCategory(tp, "Techniques", "Techs...", true) 
techs = techs.map(t => `  - "[[${t}]]"`).join("\n")-%>
techniques: 
<%techs%>
---
