---
type: project
status: active
started: 2026-10-01
---

## Tasks

- [ ] [[Sketch layout]]
- [/] [[Order seedlings]] ^order-seedlings
- [-] [[Hire tractor]]
- [x] [[Test soil]] ^test-soil

## Task notes (Bases)

```base
views:
  - type: table
    name: Task notes
    filters:
      and:
        - file.hasLink(this.file)
        - type == "task"
    order:
      - file.name
      - project
```
