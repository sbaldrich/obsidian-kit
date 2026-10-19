#!/usr/bin/env bash
# Tests for install.sh. Everything happens in a temporary directory with fake
# vaults; HOME is redirected there too. No real vault or config is touched.
#
#   bash tests/test-install.sh
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
INSTALL="$REPO/install.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/kit-install-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

export HOME="$TMP/home"
mkdir -p "$HOME"
unset KIT_TEST_INTERACTIVE

PASS=0
FAIL=0
ok()   { PASS=$((PASS + 1)); echo "  ok   $1"; }
bad()  { FAIL=$((FAIL + 1)); echo "  FAIL $1"; }
check() { # description command...
    local d="$1"; shift
    if "$@" >/dev/null 2>&1; then ok "$d"; else bad "$d"; fi
}
check_not() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then bad "$d"; else ok "$d"; fi; }

SUM="shasum -a 256"; command -v sha256sum >/dev/null 2>&1 && SUM="sha256sum"

# Fingerprint of everything in a vault except _kit/ (names and contents).
outside() { ( cd "$1" && find . -path ./_kit -prune -o -type f -print0 | LC_ALL=C sort -z | xargs -0 $SUM; find . -path ./_kit -prune -o -type l -print ); }
# Fingerprint of _kit/ without the install-time stamp.
inside()  { ( cd "$1/_kit" && find . -type f ! -name .kit-version -print0 | LC_ALL=C sort -z | xargs -0 $SUM ); }

new_vault() { # name -> path
    local v="$TMP/$1"
    mkdir -p "$v/.obsidian" "$v/notes" "$v/daily"
    echo '{"decoy": true}' > "$v/.obsidian/app.json"
    echo "decoy note" > "$v/notes/Decoy.md"
    echo "today" > "$v/daily/2026-01-01.md"
    echo "$v"
}

run() { # args... ; sets OUT and RC
    OUT="$("$INSTALL" "$@" 2>&1 < /dev/null)"; RC=$?
}
run_in() { # stdin-text args... (simulate a terminal)
    local input="$1"; shift
    OUT="$(printf '%s\n' "$input" | KIT_TEST_INTERACTIVE=1 "$INSTALL" "$@" 2>&1)"; RC=$?
}

REPO_STATE_BEFORE="$(git -C "$REPO" status --porcelain)"

echo "dry run on a fresh vault"
V="$(new_vault v1)"
B="$(outside "$V")"
run "$V" --dry-run
check "exit 0" test "$RC" = 0
check_not "no _kit created" test -e "$V/_kit"
check "outside unchanged" test "$(outside "$V")" = "$B"
check "lists what would be created" grep -q "Meeting template.md" <<< "$OUT"

echo "first install"
run "$V"
check "exit 0" test "$RC" = 0
check "outside unchanged" test "$(outside "$V")" = "$B"
check "templates deployed" test -f "$V/_kit/templates/Meeting template.md"
check "schema deployed" test -f "$V/_kit/schema.yaml" -a -f "$V/_kit/types.json"
check "bases deployed" test -f "$V/_kit/bases/Linked notes.base"
check "checklists deployed (as templates)" test -f "$V/_kit/templates/Weekly review checklist.md"
check_not "readme not deployed" test -e "$V/_kit/README.md"
check_not "tests not deployed" test -e "$V/_kit/tests"
check_not "sample vault not deployed" test -e "$V/_kit/sample-vault"
check_not "no tools deployed (lint runs from the repo)" test -e "$V/_kit/tools"
check_not "playground not deployed" test -e "$V/_kit/playground"
check_not "install.sh not deployed" test -e "$V/_kit/install.sh"
check_not "future-improvements not deployed" test -e "$V/_kit/FUTURE-IMPROVEMENTS.md"
check "version has the repo commit" grep -q "^commit: $(git -C "$REPO" rev-parse HEAD)" "$V/_kit/.kit-version"
check "version has a date" grep -q "^commit-date: " "$V/_kit/.kit-version"
check "manifest written" test -s "$V/_kit/.kit-manifest"
check "manifest excludes itself" bash -c "! grep -q 'kit-' '$V/_kit/.kit-manifest'"
I1="$(inside "$V")"

echo "second install changes nothing"
run "$V"
check "exit 0, no warning" bash -c "test $RC = 0 && ! grep -q differs <<< \"\$1\"" _ "$OUT"
check "content identical" test "$(inside "$V")" = "$I1"
check "outside unchanged" test "$(outside "$V")" = "$B"

echo "edited file"
echo "edit" >> "$V/_kit/templates/Meeting template.md"
E="$(inside "$V")"
run "$V"
check "refused (exit 1)" test "$RC" = 1
check "names the file and says modified" bash -c "grep -q modified <<< \"\$1\" && grep -q 'Meeting template.md' <<< \"\$1\"" _ "$OUT"
check "left untouched" test "$(inside "$V")" = "$E"
run "$V" --dry-run
check "dry run exit 0" test "$RC" = 0
check "dry run warns" grep -q "differs from the last install" <<< "$OUT"
check "dry run left untouched" test "$(inside "$V")" = "$E"
run_in "n" "$V"
check "answering n refuses" test "$RC" = 1
check "answering n leaves untouched" test "$(inside "$V")" = "$E"
run_in "y" "$V"
check "answering y overwrites" test "$RC" = 0 -a "$(inside "$V")" = "$I1"

echo "edited file with --force"
echo "edit" >> "$V/_kit/templates/Meeting template.md"
run "$V" --force
check "force overwrites" test "$RC" = 0 -a "$(inside "$V")" = "$I1"

echo "deleted file"
rm "$V/_kit/templates/Task template.md"
run "$V"
check "refused, says deleted" bash -c "test $RC = 1 && grep -q deleted <<< \"\$1\"" _ "$OUT"
run_in "y" "$V"
check "y restores it" test -f "$V/_kit/templates/Task template.md" -a "$(inside "$V")" = "$I1"

echo "added file (would be removed by --delete)"
echo "mine" > "$V/_kit/My note.md"
run "$V"
check "refused, says added" bash -c "test $RC = 1 && grep -q 'My note.md' <<< \"\$1\"" _ "$OUT"
check "file still there" test -f "$V/_kit/My note.md"
run "$V" --force
check "force removes it" test ! -e "$V/_kit/My note.md" -a "$(inside "$V")" = "$I1"
check "outside unchanged" test "$(outside "$V")" = "$B"

echo "_kit without an install record"
V2="$(new_vault v2)"; B2="$(outside "$V2")"
mkdir "$V2/_kit"; echo "old" > "$V2/_kit/Old.md"
run "$V2"
check "refused" test "$RC" = 1
check "file kept" test -f "$V2/_kit/Old.md"
run "$V2" --force
check "force installs and removes the old file" test "$RC" = 0 -a ! -e "$V2/_kit/Old.md" -a -f "$V2/_kit/schema.yaml"
check "outside unchanged" test "$(outside "$V2")" = "$B2"

echo "refused targets"
run "$TMP/does-not-exist"
check "missing path" test "$RC" = 1
NV="$TMP/not-a-vault"; mkdir -p "$NV/notes"; echo keep > "$NV/notes/a.md"
run "$NV"
check "no .obsidian" test "$RC" = 1
check "nothing written" test ! -e "$NV/_kit"
V3="$(new_vault v3)"; B3="$(outside "$V3")"
DECOY="$TMP/elsewhere"; mkdir -p "$DECOY"; echo precious > "$DECOY/keep.md"
ln -s "$DECOY" "$V3/_kit"
run "$V3" --force
check "symlinked _kit refused even with --force" test "$RC" = 1
check "symlink target untouched" test "$(cat "$DECOY/keep.md")" = precious -a "$(ls "$DECOY")" = keep.md
rm "$V3/_kit"
run "$HOME"
check "refuses HOME" test "$RC" = 1
run /
check "refuses /" test "$RC" = 1

echo "usage errors"
run
check "no vault exits 2" test "$RC" = 2
run "$V" --bogus
check "unknown option exits 2" test "$RC" = 2

echo "several vaults, spaces, relative path"
V4="$(new_vault "with space")"; B4="$(outside "$V4")"
mkdir -p "$TMP/rel/vault/.obsidian"; B6="$(outside "$TMP/rel/vault")"
OUT="$(cd "$TMP/rel" && "$INSTALL" "$V4" ./vault 2>&1 < /dev/null)"; RC=$?
check "both installed" test "$RC" = 0 -a -f "$V4/_kit/schema.yaml" -a -f "$TMP/rel/vault/_kit/schema.yaml"
check "outside unchanged (spaces, relative)" test "$(outside "$V4")" = "$B4" -a "$(outside "$TMP/rel/vault")" = "$B6"

echo "one bad vault does not block a good one"
V7="$(new_vault v7)"; B7="$(outside "$V7")"
run "$TMP/missing" "$V7"
check "exit 1" test "$RC" = 1
check "good vault installed" test -f "$V7/_kit/schema.yaml"
check "outside unchanged" test "$(outside "$V7")" = "$B7"

echo "from another working directory"
V8="$(new_vault v8)"
OUT="$(cd / && "$INSTALL" "$V8" 2>&1 < /dev/null)"; RC=$?
check "works" test "$RC" = 0 -a -f "$V8/_kit/schema.yaml"

echo "repo untouched"
check "git status unchanged" test "$(git -C "$REPO" status --porcelain)" = "$REPO_STATE_BEFORE"

echo
echo "passed: $PASS, failed: $FAIL"
[ "$FAIL" = 0 ]
