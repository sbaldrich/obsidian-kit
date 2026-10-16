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

## Linting

- Linter driven by `schema.yaml`: one Python file run with `uv run`, read-only,
  output is rule id + relative path (no property values unless `--verbose`),
  reads vault paths from `vaults.conf`. Agent rules should run it after notes
  are created or edited.
- Self-test: check that the example frontmatter block in `schema.md` passes
  `schema.yaml`, so the two cannot drift.

## To verify in a scratch vault

- Do links inside properties (`project: "[[X]]"`) count for Bases
  `file.hasLink(this.file)`? The docs don't say, and the link-based design
  depends on it.
- Dataview task status (untested, docs say tasks expose `status`, `checked`,
  `completed` and `outlinks`). On a task note, its checkbox and status:
  `TASK WHERE contains(outlinks, this.file.link)`. All in-progress tasks:
  `TASK WHERE status = "/"`. Whether `this` works in TASK queries is not
  covered by the docs.

## Plugins

- Templater instead of core Templates: auto-prefix `YYYY-MM-DD` names, move
  notes to their folder, link pickers. Switch only if core Templates hurts.
- Dataview, when a query can't be expressed as a base.
- Obsidian CLI wrapper to create notes from templates (`scripts/obs` in the
  `legacy` tag).

## Note types and content

- Weekly, monthly and yearly notes.
- Birthdays and recurring tasks.
- CSS snippets (Bases icons, homepage styling).
- A "Today" home note (old version in the `legacy` tag, sanitized).
