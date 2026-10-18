# Agent rules (shared by all vaults)

For any AI agent working in a vault that has this kit in `_kit/`. A vault's own
agent file adds vault-specific rules on top of these and points here.

## Read first

- `_kit/schema.md`: note types, folders, conventions.
- `_kit/schema.yaml`: the exact rules (required properties, allowed values,
  folders, name patterns). When the two disagree, `schema.yaml` wins.

## The kit

- Never create, edit, move or delete anything in `_kit/`. It is overwritten on
  every install. Changes to the kit are made in the kit's own repo.
- Embed bases from `_kit/bases/` instead of writing lists by hand, for example
  `![[Linked notes.base#Meetings]]`.

## Creating and editing notes

- Every note has a `type`, except notes in `inbox/`. Use only types from the
  schema; do not invent types or properties. Only `option` notes may have extra
  properties.
- Start from the type's template in `_kit/templates/` (`<Type> template.md`):
  same properties in the same order, same headings. Replace the placeholders:
  `{{date:YYYY-MM-DD}}` is today's date, `{{date:YYYY}}` is the current year.
- Put the note in the folder the schema gives for its type. Folder names are
  lowercase with hyphens; note titles keep normal casing.
- Name notes as the schema says: dated notes `YYYY-MM-DD Title` (the date must
  equal the `date` property), people by full name, reference notes by a
  specific concept name.
- Values: dates `YYYY-MM-DD`; links are quoted wikilinks (`"[[Note]]"`); lists
  are YAML lists; use only the allowed values for enum properties. Leave a
  property empty rather than guessing.
- No `tags` property.
- Do not rename or move existing notes unless asked. Moves go through Obsidian
  so links update; never leave a note with a broken link.
- Do not delete notes. Closed projects go to `archive/`; area history goes to
  `areas/<name>/archive/<year>/`. Ask before archiving.
- Notes in `inbox/` are unprocessed. To process one, give it a `type`, apply
  the template's shape, and move it to its folder. Ask first.

## Links

- Link generously: the first mention of a person, project, area or concept
  gets a wikilink. Use the exact title of an existing note.
- Do not invent link targets. A link to a real person or concept that has no
  note yet is fine; say so when you add one.
- Queries are link-based: a note "belongs to" a project through a link or a
  link property, not through its folder.

## Tasks

- A task's status is its checkbox: `[ ]` todo, `[/]` in progress, `[-]`
  cancelled, `[x]` done, `[>]` moved somewhere else.
- A task note has exactly one checkbox that is not `[>]`, in its home note (the
  note its `project` or `area` property links to). Never add a second one
  elsewhere.
- To carry a task forward, or to show it elsewhere, use `[>]`, a plain link
  without a checkbox, or embed the home note's line.
- When a task moves to another project or area: change its `project` or `area`
  property, mark the old line `[>]`, and add the real checkbox to the new home
  note.
- Task notes have no `status` property.

## Privacy

- Vault content is personal. Do not copy it into other tools or repos, and do
  not send it over the network unless asked.
- Never put real names, companies, or data from a vault into the kit's repo.
  Use invented examples there.
