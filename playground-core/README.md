# Playground (core only)

Synthetic vault for testing kit ideas with core Obsidian only: no community
plugins. Not part of the kit: never deployed. All names and data are invented.

Question: with task status stored only in the checkbox (task notes have no
`status` property), how far do core features get you in seeing it?

## Setup

Obsidian → Open folder as vault → this `playground-core/` folder. Nothing to
install. Open the Backlinks pane (right sidebar) and turn on "Show more
context" if it's off. Everything under `.obsidian/` is gitignored.

## The problem you wanted to see

`Order seedlings` is listed as `[/]` in [[Orchard]], and as `[x]` in
[[2026-10-16]]. Nothing links the two lines. Open [[Order seedlings]] and look
at the Backlinks pane: do you see both states, and can you tell which one is
the task's real status?

## A. Backlinks pane

Open any task note (try [[Order seedlings]], [[Hire tractor]], [[Pot herbs]]).
Look for: the Linked mentions entries show the line with its checkbox.

## B. Embedding the line

- Block embed: [[Order seedlings]] embeds the single checkbox line with a
  block id. [[2026-10-17]] does the same in a daily note. Look for: does the
  embedded checkbox render, and does ticking it change [[Orchard]]?
- Section embed: [[Sketch layout]] embeds the whole `Tasks` section of
  Orchard. Look for: all four states visible from one task note.

## C and D. Embedded search

[[Core queries]] has the queries. Look for:

- C: `task-todo` and `task-done` are documented only for `[ ]` and `[x]`. In
  which block does each task land, in particular `Order seedlings` `[/]` and
  `Hire tractor` `[-]`?
- D: the regex queries should list exactly the lines with `[/]` (and `[-]`
  for the last one), across projects or only in Orchard.

## E. Bases

[[Orchard]] has a base listing its task notes. Look for: it lists the notes
and their `project` link, with no status column possible.

## How tasks appear in daily notes

[[2026-10-16]] has a separate checkbox. [[2026-10-17]] has an embedded line and
a plain mention. Compare the three styles.
