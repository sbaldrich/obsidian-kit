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

- Linter driven by `schema.yaml`: one Python file run with `uv run`, read-only,
  output is rule id + relative path (no property values unless `--verbose`),
  reads vault paths from `vaults.conf`. Agent rules should run it after notes
  are created or edited.
- Checks include the `task_checkbox` rules in `schema.yaml`: more than one
  non-`[>]` checkbox for a task note (error), none (warning), or one outside
  the home note (error).
- Self-test: check that the example frontmatter block in `schema.md` passes
  `schema.yaml`, so the two cannot drift.

## Verified in the playgrounds

- Links inside properties (`project: "[[X]]"`) count for Bases
  `file.hasLink(this.file)`. `!file.inFolder("_kit")` hides the kit from bases.
- Dataview can read `[/]` and `[-]`, join a checkbox to the linked note's
  properties, and `this` works in TASK queries. Ruled out of the kit anyway.

Pending: results of `playground-core/` (backlinks pane, embeds, embedded
search with `task-todo` / `task-done` / regex, Bases).

## Plugins

Ruled out for the kit:

- **Dataview.** Works (see above), but the kit stays plugin-free. Reconsider
  only if a query can't be expressed with Bases, search or embeds.
- **obsidian-checklist-plugin.** Would give one sidebar of tasks, but it
  documents only `[ ]` and `[x]` (unknown behavior for `[/]`, `[-]`, `[>]`),
  the kit can't install or configure plugins, and its maintenance looked thin.
  A vault may install it on its own.

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
