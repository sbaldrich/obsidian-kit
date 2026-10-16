---
type: project
status: active
started: 2026-10-01
---

## Linked notes

```base
views:
  - type: table
    name: Linked, kit excluded
    filters:
      and:
        - file.hasLink(this.file)
        - '!file.inFolder("_kit")'
    order:
      - file.name
      - type
  - type: table
    name: Linked, kit not excluded
    filters:
      and:
        - file.hasLink(this.file)
    order:
      - file.name
      - file.folder
      - type
```
