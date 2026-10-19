#!/usr/bin/env bash
# (Re)create this sample vault's local Obsidian config and install the kit
# into its _kit/ with the real install.sh. Safe to re-run.
#
#   bash sample-vault/setup.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(dirname "$HERE")"
OBS="$HERE/.obsidian"

mkdir -p "$OBS"
[ -f "$OBS/app.json" ] || echo '{}' > "$OBS/app.json"
printf '{\n  "folder": "_kit/templates"\n}\n' > "$OBS/templates.json"
printf '{\n  "folder": "daily",\n  "format": "YYYY-MM-DD",\n  "template": "_kit/templates/Daily template"\n}\n' > "$OBS/daily-notes.json"

# Merge the kit's property types into the vault's (existing entries win).
python3 -I - "$REPO/types.json" "$OBS/types.json" <<'PY'
import json, os, sys
kit = json.load(open(sys.argv[1]))["types"]
mine = json.load(open(sys.argv[2]))["types"] if os.path.exists(sys.argv[2]) else {}
json.dump({"types": {**kit, **mine}}, open(sys.argv[2], "w"), indent=2)
PY

"$REPO/install.sh" "$HERE"
