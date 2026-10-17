---
type: project
status: active
started: 2026-10-01
---

## Tasks

- [i] [[Sketch layout]]
- [/] [[Order seedlings]] ^order-seedlings
- [-] [[Hire tractor]]
- [x] [[Test soil]] ^test-soil
- [/] Something else

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
