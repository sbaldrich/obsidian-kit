# Playground

Synthetic vault for testing kit ideas. Not part of the kit: never deployed.
All names and data are invented.

## Setup

1. Obsidian → Open folder as vault → this `playground/` folder.
2. Scenario 1 and 4 need only core Obsidian (Bases).
3. Scenarios 2 and 3 need Dataview: Settings → Community plugins → install and
   enable Dataview. For the `dataviewjs` blocks, also turn on Dataview's
   "Enable JavaScript Queries".

Everything under `.obsidian/` is gitignored.

## Scenario 1: links in properties and Bases

Open [[Alpha]]. Its base has two views, both filtered with
`file.hasLink(this.file)`.

| Note | How it links to Alpha | Expected if property links count |
|---|---|---|
| [[Beta]] | only `project: "[[Alpha]]"` in properties | listed |
| [[Gamma]] | `[[Alpha]]` in the body | listed (control) |
| [[Delta]] | no link | not listed (control) |

Report: is Beta listed? That decides whether the link-based design works with
property links.

## Scenario 2: Dataview and checkbox status

[[Orchard]] and [[Greenhouse]] list task notes as checkboxes in all four
states. Each task note embeds a Dataview query showing its own checkbox.
[[Dataview tests]] has the cross-note queries.

Report for each query: does it render, and are `[/]` and `[-]` reported
correctly (not only `[ ]` and `[x]`)? Note whether `this` works inside TASK
queries, and whether the task `status` is confused with the project's `status`
property.

## Scenario 3: the same task checked in two places

[[2026-10-16]] has `- [x] [[Order seedlings]]`, while [[Orchard]] has
`- [/] [[Order seedlings]]`. The last query in [[Dataview tests]] lists task
notes with more than one checkbox.

Report: does the query catch it? If this case is realistic, the schema needs a
rule such as "the checkbox in the home note is authoritative".

## Scenario 4: excluding `_kit/`

`_kit/templates/Template stub.md` has a real `type` and links to Alpha, like a
real template would. In [[Alpha]], the first view excludes `_kit/` and the
second doesn't.

Report: the stub appears only in the second view.

The stub is temporary. Installing the real kit into this vault runs
`--delete` inside `_kit/`, which removes it.
