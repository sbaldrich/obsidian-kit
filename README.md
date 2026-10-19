# Obsidian kit

What my Obsidian vaults share: a schema, templates, bases and checklists, plus
a linter that checks a vault against the schema. `install.sh` copies the kit
into a vault's `_kit/` folder.

Rule: **edit the kit here, never inside a vault's `_kit/`.** `_kit/` is
overwritten on every install.

The kit needs no community plugins, only core Obsidian (Templates, Daily
notes, Bases, Backlinks).

## What is in it

| Path | What | Deployed to `_kit/` |
|---|---|---|
| `schema.yaml` | Note types, folders, properties, conventions. The source of truth | yes |
| `templates/` | `<Type> template.md`, one per note type, **generated** from `schema.yaml`; plus four hand-written `<Name> checklist.md` | yes |
| `types.json` | Obsidian property types, **generated** from `schema.yaml` | yes |
| `bases/` | Reusable `.base` files | yes |
| `install.sh` | The installer | no |
| `tools/lint.py`, `tools/kitlib.py` | The linter and its helper | no |
| `tools/build.py` | Generates `templates/` and `types.json` | no |
| `tests/` | Tests for the installer and the linter | no |
| `playground/`, `sample-vault/` | Synthetic vaults for trying things | no |

## Install into a vault

Needs bash, rsync, git and uv. Tested on macOS only.

1. `./install.sh --dry-run ~/vaults/work` shows what would change, then
   `./install.sh ~/vaults/work` installs. Several vaults can be given at once.
   It writes only inside `<vault>/_kit/` and refuses a folder without
   `.obsidian/`. If `_kit/` was edited since the last install, it lists the
   differences and asks before overwriting (`--force` skips the question).
2. Once per vault, in Obsidian's settings:
   - Core plugins: turn on **Templates**, **Daily notes** and **Bases**.
   - Templates → template folder location: `_kit/templates`.
   - Daily notes → folder `daily`, date format `YYYY-MM-DD`, template
     `_kit/templates/Daily template`.
3. Optional, once per vault: merge the kit's property types into the vault's
   (existing entries win). Quit Obsidian first, then reopen it:

   ```bash
   VAULT=~/vaults/work
   python3 -I - "$VAULT/_kit/types.json" "$VAULT/.obsidian/types.json" <<'PY'
   import json, os, sys
   kit, dst = sys.argv[1], sys.argv[2]
   types = json.load(open(kit))["types"]
   if os.path.exists(dst):
       types.update(json.load(open(dst))["types"])
   with open(dst + ".tmp", "w") as f:
       json.dump({"types": types}, f, indent=2)
   os.replace(dst + ".tmp", dst)
   PY
   ```

4. Check the vault: `uv run tools/lint.py ~/vaults/work`.

## Use it

- **New note:** create it in its folder, then insert `<Type> template` (Templates:
  insert template). Dated notes are named `YYYY-MM-DD Title`.
- **Bases:** index bases (`Projects.base`, `Meetings.base`, ...) can be opened
  directly from `_kit/bases/`. `Linked notes.base` and `Daily.base` are
  embedded in notes and use `this`; the templates already embed them.
- **Checklists:** insert a `<Name> checklist` into a note (a daily note works)
  like any template, and tick it there.
- **Lint:** `uv run tools/lint.py <vault> [...]` checks every note against
  the schema. It only reads, and prints rule ids and paths, not note content.
  Findings are grouped by rule, most frequent first, each with a hint on how
  to fix it and 5 example paths. `--rule <id>` lists every path for one rule
  (`--rule missing-required` covers every property), `--all` prints one line
  per finding, `-q` only the summary. `--ignore legacy` hides findings for
  notes under a folder you don't want to fix now; `--under people` shows only
  that folder's (both repeatable; `*` and `**` allowed). Hidden notes still
  count for duplicate names and task checkboxes.
  `--verbose` adds the offending values on stderr; `--strict` makes warnings
  fail too.
- **Fix in an editor:** `--quickfix` prints `path:line: severity rule`, with
  the line of the offending property or checkbox, and the summary on stderr.
  In Neovim: `uv run tools/lint.py --quickfix --rule unknown-type ~/vaults/work | nvim -q -`,
  then `:cdo s/.../.../ | update` edits exactly those lines. (Not
  `nvim -q <(...)`: Neovim 0.11's UI can't read that file, E47.)
- **Tasks:** a task note has one checkbox, in its home note. See
  `task_checkbox` in `schema.yaml` for the full rule.

## Change the kit

- **Properties, types, headings, embeds in templates:** edit `schema.yaml`,
  then `uv run tools/build.py`. Commit the regenerated `templates/` and
  `types.json`. The build only writes `<Type> template.md`; the
  `* checklist.md` files are edited by hand.
- **Check:** `uv run tools/build.py --check` fails if the generated files are
  stale, if a property name has two value types, or if an embed names a
  missing base or view (in the schema or in a checklist).
- **Bases:** hand-written. Keep the line `!file.inFolder("_kit")` so templates
  don't show up in them, and keep base names unique (embeds resolve by name
  across the vault). Renaming a view means updating `schema.yaml`; the build
  tells you.
- **Tests:** `bash tests/test-install.sh` and `uv run tests/test_lint.py`
  (fake vaults in a temporary directory; they never touch a real vault).
- **Try things:** `playground/` and `sample-vault/` are synthetic vaults. For
  `sample-vault/`, `bash sample-vault/setup.sh` writes its local Obsidian
  config and installs the kit into it. Open either folder in Obsidian as a
  vault.

## House rules

- Nothing personal or vault-specific goes in this repo: no real names,
  companies, projects or paths. Examples are invented.
- The old category-and-tags kit, with its plugin dependencies, is under the
  git tag `legacy`.
