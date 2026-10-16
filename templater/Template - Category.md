---
register: true
---
<%* tR = ''; -%>
---
tags:
  - categories
---

```base
filters:
  and:
  - category.contains(this.file.name)
```
