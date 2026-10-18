# Future improvements

Deferred on purpose. Revisit when a concrete need appears.

## Deployment

- **Per-vault config in each vault's own repo.** Which optional modules a vault
  uses should be configured by the vault, not by this repo. Machine-specific
  vault paths stay local and gitignored (`vaults.conf`).
- **Optional modules** (`modules/<name>/`, mirroring the kit layout), copied
  into `_kit/` along with the core. Modules add files; they don't ship variants
  of an existing file. No cookiecutter (generate-once, doesn't fit re-running
  the install with `--delete`).
  - First candidate: spaced repetition (flashcard template for `reference`).
- **CSS snippets.** Obsidian reads snippets only from `.obsidian/snippets/`,
  and the installer writes only inside `_kit/`. A shipped snippet needs a
  one-time manual symlink from `.obsidian/snippets/` to `_kit/snippets/`.

## Linting

`tools/lint.py` exists. Possible later: a `--fix` for the safe cases (empty
optional properties, placeholder leftovers), JSON output, a check for
unresolved wikilinks, and tightening some warnings (wrong folder, checkbox
outside the home note) into errors once the vaults are clean.

## Verified in the playgrounds

- Links inside properties (`project: "[[X]]"`) count for Bases
  `file.hasLink(this.file)`. `!file.inFolder("_kit")` hides the kit from bases.
- Dataview (tested in a since-removed playground) can read `[/]` and `[-]`,
  join a checkbox to the linked note's properties, and `this` works in TASK
  queries.

Pending: results of the core-only scenarios in `playground/` (backlinks pane,
embeds, embedded search with `task-todo` / `task-done` / regex, Bases).

## Plugins

The kit neither requires nor prescribes community plugins. Each vault decides
for itself, for example Dataview (reads every checkbox status) or
obsidian-checklist-plugin (one sidebar of tasks; documents only `[ ]` and
`[x]`, so check how it treats `[/]`, `[-]` and `[>]`). The kit can't install or
configure plugins anyway: that lives in each vault's `.obsidian/`.

Possible later:

- Templater instead of core Templates: auto-prefix `YYYY-MM-DD` names, move
  notes to their folder, link pickers. Switch only if core Templates hurts.
- Obsidian CLI wrapper to create notes from templates (`scripts/obs` in the
  `legacy` tag).

## Note types and content

- A hand-written Tasks note with embedded search queries (in progress, to do,
  moved), plus a CSS snippet for `.internal-query`. Core search shows raw lines,
  not clickable checkboxes, so check that first. Needs a decision on its type
  (a `dashboard` type, or untyped).
- Weekly, monthly and yearly notes.
- Birthdays and recurring tasks.
- CSS snippets (Bases icons, homepage styling).
- A "Today" home note (old version in the `legacy` tag, sanitized).
