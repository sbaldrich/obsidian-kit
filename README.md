# Obsidian kit

What several Obsidian vaults share: templates, bases, checklists, a schema and
agent rules. `install.sh` copies the kit into each vault's `_kit/` folder.

Rule: **edit the kit here, never inside a vault's `_kit/`.** `_kit/` is
overwritten on every install.

The kit needs no community plugins, only core Obsidian (Templates, Daily
notes, Bases, Backlinks). Whether a vault adds plugins is its own decision.

## What is in it

| Path | What | Deployed to `_kit/` |
|---|---|---|
| `schema.md` | Note types, folders, conventions | yes |
| `schema.yaml` | The same as rules a tool can read; the source of truth | yes |
| `templates/` | `<Type> template.md`, one per note type, **generated** from `schema.yaml`; plus four hand-written `<Name> checklist.md` (weekly review, project close, cycle end, yearly rollover) | yes |
| `types.json` | Obsidian property types. **Generated** from `schema.yaml` | yes |
| `bases/` | Reusable `.base` files | yes |
| `agents/common.md` | Rules for AI agents, shared by all vaults | yes |
| `install.sh`, `vaults.conf.example` | The installer | no |
| `tools/lint.py`, `tools/kitlib.py` | The linter and its helper | yes |
| `tools/build.py` | Generates `templates/` and `types.json` | no |
| `tests/` | Tests for the installer | no |
| `playground/`, `sample-vault/` | Synthetic vaults for trying things | no |
| `FUTURE-IMPROVEMENTS.md` | Ideas deferred on purpose | no |

Only the paths marked "yes" are deployed (a whitelist in `install.sh`).

## Install into your vaults

Needs bash, rsync and git. Tested on macOS (bash 3.2); not yet on Linux.

1. `cp vaults.conf.example vaults.conf` and edit it: one `name=path` per line.
   `vaults.conf` is gitignored. Paths may start with `~/` or be relative to the
   file.
2. `./install.sh --dry-run` shows what would change and writes nothing.
3. `./install.sh` installs into every vault; `./install.sh work` into one.

It writes only inside `<vault>/_kit/`, and refuses a folder without
`.obsidian/`. It records the kit's commit in `_kit/.kit-version` and a
checksum list in `_kit/.kit-manifest`. If `_kit/` was edited since the last
install, it lists the differences and asks before overwriting (`--force` skips
the question, and is needed when there is no terminal).

### One-time setup in each vault

Obsidian reads these from `.obsidian/`, which the installer never touches.

1. Settings → Core plugins: turn on **Templates**, **Daily notes** and
   **Bases**.
2. Templates → template folder location: `_kit/templates`.
3. Daily notes → folder `daily`, date format `YYYY-MM-DD`, template
   `_kit/templates/Daily template`.
4. Merge the kit's property types into the vault's. Existing entries win. Do
   it with Obsidian closed, then reopen it:

   ```bash
   python3 -I - "$VAULT/_kit/types.json" "$VAULT/.obsidian/types.json" <<'PY'
   import json, os, sys
   kit = json.load(open(sys.argv[1]))["types"]
   mine = json.load(open(sys.argv[2]))["types"] if os.path.exists(sys.argv[2]) else {}
   json.dump({"types": {**kit, **mine}}, open(sys.argv[2], "w"), indent=2)
   PY
   ```

5. In the vault's own agent file (for example `AGENTS.md`), add the vault's
   rules and point to `_kit/agents/common.md`.

## Use it

- **New note:** create it in its folder, then insert `<Type> template` (Templates:
  insert template). Dated notes are named `YYYY-MM-DD Title`.
- **Bases:** index bases (`Projects.base`, `Meetings.base`, ...) can be opened
  directly from `_kit/bases/`. `Linked notes.base` and `Daily.base` are
  embedded in notes and use `this`; the templates already embed them.
- **Checklists:** insert a `<Name> checklist` into a note (a daily note works)
  like any template, and tick it there.
- **Lint:** `uv run _kit/tools/lint.py` from the vault checks every note
  against the schema (needs `uv`). It only reads, and prints rule ids and
  paths, not note content; `--verbose` adds the offending values on stderr,
  `--strict` makes warnings fail too. From the kit repo:
  `uv run tools/lint.py work` (a name from `vaults.conf`) or
  `uv run tools/lint.py ./some/vault`.
- **Tasks:** a task note has one checkbox, in its home note. See
  `schema.md` for the full rule.

## Change the kit

- **Properties, types, headings, embeds in templates:** edit `schema.yaml`,
  then `uv run tools/build.py` (needs `uv`; it installs PyYAML on the fly).
  Commit the regenerated `templates/` and `types.json`. The build only writes
  `<Type> template.md`; the `* checklist.md` files are edited by hand.
- **Check:** `uv run tools/build.py --check` fails if the generated files are
  stale, if a property name has two value types, if an embed names a missing
  base or view (in the schema or in a checklist), or if the examples in
  `schema.md` break the schema.
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
