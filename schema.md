# Schema

Note types, folders and conventions shared by all vaults. Templates, bases,
checklists and agent rules follow this file.

The machine-readable rules (required properties, allowed values, folders, name
patterns) are in `schema.yaml`. If this file and `schema.yaml` disagree,
`schema.yaml` wins.

## Principles

- Folders describe what a note *is*. Links and properties describe what it is
  *about*.
- Queries are link-based (`file.hasLink(this.file)`), never folder-based.
  Exception: bases exclude the kit with `!file.inFolder("_kit")`, because
  templates carry real `type` values.
- Every note has a `type` property, except notes in `inbox/` (unprocessed
  captures) and `_kit/`.
- No `tags` property. Type and links do that job.
- The kit needs no community plugins: core Obsidian only (Templates, Bases,
  search, Backlinks). Whether to add plugins is each vault's decision.
- Base files are embedded by name (`![[Daily.base]]`), which resolves
  vault-wide. Kit base names must be unique in the vault.

## Folders

| Folder | Holds |
|---|---|
| `daily/` | daily notes |
| `inbox/` | unprocessed captures, no `type` yet |
| `projects/<name>/` | project home note, its task notes, options |
| `areas/<name>/` | area home note, task notes, incidents. History in `areas/<name>/archive/<year>/` |
| `meetings/` | meetings |
| `people/` | person hubs |
| `records/impact/`, `records/decisions/`, `records/1on1/`, `records/feedback/` | records |
| `reference/` | reference and hub notes, flat or one level of broad domains |
| `sources/` | notes on books, articles, papers, courses, talks |
| `archive/` | closed projects |
| `_kit/` | deployed kit. Never edit here; edit in the kit repo |

Not every folder exists in every vault.

## Conventions

- Folder names: lowercase, hyphens (`projects/invoicing-migration/`).
- Note titles keep normal casing (`Invoicing migration.md`).
- Dated notes: `YYYY-MM-DD Title`. A recurring meeting series is one note per
  year, named `YYYY Title`, with `date` set to its first meeting. People: full
  name. Reference notes: specific concept name.
- Dates: `YYYY-MM-DD`. Links: quoted wikilinks (`"[[Note]]"`). Lists: YAML lists.
- Where allowed values are given, no other values are valid. Optional
  properties may be omitted.
- Checkboxes: `[ ]` todo, `[/]` in progress, `[-]` cancelled, `[x]` done,
  `[>]` moved somewhere else.

## Note types

| type | What it is | Lives in | Typical vault |
|---|---|---|---|
| project | Home note of a project (a goal with an end) | `projects/<name>/` | both |
| task | A task big enough to need its own note | its project or area folder | both |
| area | Home note of an ongoing responsibility | `areas/<name>/` | both |
| meeting | One meeting, or one recurring series per year | `meetings/` | work |
| incident | An event within an area (e.g. on-call incident) | `areas/<name>/` | work |
| person | Hub note for a person | `people/` | both |
| impact | Something I did that mattered | `records/impact/` | work |
| decision | A decision worth remembering or justifying later | `records/decisions/` | both |
| 1on1 | One 1:1 conversation | `records/1on1/` | work |
| feedback | One piece of feedback, about someone or received | `records/feedback/` | work |
| cycle | Home note for one performance review cycle | `areas/career/` | work |
| story | A reusable career story (for interviews, reviews) | `areas/career/` | personal |
| reference | Durable knowledge, in my own words | `reference/` | both |
| hub | Entry point for a topic; reference notes link to it | `reference/` | both |
| source | My notes on a book, article, paper, course or talk | `sources/` | personal |
| option | A candidate being compared (house, hotel, employer) | its project folder | both |
| daily | Daily note: capture (work) or journal (personal) | `daily/` | both |

"Typical vault" is guidance only. The kit ships every template to every vault.

## Properties

Examples of each type's frontmatter. Comments give the allowed values.
`task` and `decision` take exactly one of `project` / `area`.

```yaml
# project
type: project
status: active            # active | paused | done | cancelled
area: "[[Payments]]"      # optional
started: 2026-09-01
target: 2026-12-15        # optional

# task (status lives in the checkbox linking to this note)
type: task
project: "[[Invoicing migration]]"   # or area: "[[Home]]"

# area
type: area
status: active            # active | closed

# meeting
type: meeting
date: 2026-10-02
project: ["[[Invoicing migration]]"]   # optional, list
area: "[[On-call]]"                    # optional
attendees: ["[[Priya Shah]]"]

# incident
type: incident
date: 2026-10-14
area: "[[On-call]]"

# person
type: person
aliases: []               # optional: nicknames, name variants
context: "Payments team, worked together on invoicing migration"

# impact
type: impact
date: 2026-10-08
project: "[[Invoicing migration]]"   # optional
competency: technical-leadership     # from the company's framework
cycle: 2026

# decision
type: decision
date: 2026-10-15
project: "[[Invoicing migration]]"   # or area

# 1on1
type: 1on1
date: 2026-10-10
person: "[[Priya Shah]]"

# feedback
type: feedback
date: 2026-10-08
person: "[[Priya Shah]]"
direction: about-them     # about-them | received
cycle: 2026
status: open              # open | delivered

# cycle
type: cycle
cycle: 2026

# story
type: story
competency: technical-leadership
role: "Senior engineer"   # role at the time

# reference
type: reference
topics: ["[[DDD]]"]       # links to hub notes

# hub
type: hub

# source
type: source
kind: book                # book | article | paper | course | talk
author: "Vlad Khononov"
url:                      # optional
status: reading           # to-read | reading | done | abandoned
started: 2026-09-20       # optional
finished:                 # optional

# option
type: option
status: considering       # considering | visited | rejected | chosen
# plus comparison-specific fields (price, location, ...) per project

# daily
type: daily
date: 2026-10-16
```

## Task status

A task's status is its checkbox: a checkbox line that links to the task note.
Task notes have no `status` property, so status is stored once.

**A task note has exactly one checkbox, in its home note** (the note its
`project` or `area` property links to). The only checkboxes allowed elsewhere
are `[>]` (moved): for example a daily note that carries the task forward, or
a former home note after the task moved to another project. A `[>]` line is
never the task's status.

To see a task's status, open its home note, or the Backlinks pane of the task
note, or embed the home note's line (`![[Home#^block-id]]`). Bases cannot read
checkboxes.

## Linting

`schema.yaml` is meant to drive a linter that checks vault notes (known `type`,
required properties, allowed values, formats, folder and name rules). Not built
yet.
