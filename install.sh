#!/usr/bin/env bash
# Deploy the kit into Obsidian vaults, under <vault>/_kit/ and nowhere else.
#
#   ./install.sh [--dry-run] [--force] <vault-path> [...]
#
#   -n, --dry-run   show what would change; write nothing
#   -f, --force     overwrite _kit/ even if it was edited in the vault
#   -h, --help
#
# Rule: edit the kit in this repo, never inside a vault's _kit/. If _kit/ was
# edited since the last install, the changes are listed and you are asked
# before they are overwritten (non-interactive runs refuse unless --force).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# Whitelist of repo paths that are deployed. Anything else stays in the repo.
DEPLOY="templates bases schema.yaml types.json"

DRY_RUN=0
FORCE=0
STAGE=""

die() { echo "install.sh: $*" >&2; exit 2; }
err() { echo "install.sh: $*" >&2; }
say() { echo "$*"; }

usage() { sed -n '2,11p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

if command -v sha256sum >/dev/null 2>&1; then
    SUM="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
    SUM="shasum -a 256"
else
    die "need sha256sum or shasum"
fi
command -v rsync >/dev/null 2>&1 || die "need rsync"

cleanup() { [ -z "$STAGE" ] || rm -rf "$STAGE"; }
trap cleanup EXIT

# ---- staging area (outside any vault) --------------------------------------

# Hash every regular file under $1 as "hash  relative/path". Symlinks are
# listed without being read. Meta files are left out.
list_hashes() {
    ( cd "$1" && find . \( -type f -o -type l \) ! -name .kit-version ! -name .kit-manifest -print \
        | LC_ALL=C sort \
        | while IFS= read -r f; do
            if [ -L "$f" ]; then
                printf 'symlink  %s\n' "${f#./}"
            else
                $SUM "${f#./}"
            fi
        done )
}

build_stage() {
    STAGE="$(mktemp -d "${TMPDIR:-/tmp}/obsidian-kit.XXXXXX")"
    mkdir "$STAGE/kit" "$STAGE/work"
    local p present=""
    for p in $DEPLOY; do
        if [ -e "$REPO/$p" ]; then
            ( cd "$REPO" && rsync -rltR --exclude .DS_Store "$p" "$STAGE/kit/" )
            present="$present $p"
        fi
    done
    [ -n "$present" ] || die "nothing to deploy"

    local commit="unknown" cdate="unknown" dirty="unknown"
    if git -C "$REPO" rev-parse HEAD >/dev/null 2>&1; then
        commit="$(git -C "$REPO" rev-parse HEAD)"
        cdate="$(git -C "$REPO" log -1 --format=%cI)"
        # shellcheck disable=SC2086
        if [ -n "$(git -C "$REPO" status --porcelain -- $present)" ]; then dirty="yes"; else dirty="no"; fi
    fi
    {
        echo "commit: $commit"
        echo "commit-date: $cdate"
        echo "uncommitted-changes: $dirty"
        echo "installed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$STAGE/kit/.kit-version"
    list_hashes "$STAGE/kit" > "$STAGE/kit/.kit-manifest"
    KIT_COMMIT="$commit"
    KIT_DIRTY="$dirty"
}

# ---- detect edits made inside a vault's _kit/ ---------------------------------

UNMANAGED=0

detect_changes() {
    local t="$1" w="$STAGE/work"
    : > "$w/modified"; : > "$w/deleted"; : > "$w/added"
    UNMANAGED=0
    [ -d "$t" ] || return 0
    list_hashes "$t" > "$w/cur"
    if [ -L "$t/.kit-manifest" ] || [ ! -f "$t/.kit-manifest" ]; then
        [ -s "$w/cur" ] && UNMANAGED=1
        return 0
    fi
    LC_ALL=C sort "$t/.kit-manifest" > "$w/old.s"
    LC_ALL=C sort "$w/cur" > "$w/cur.s"
    comm -23 "$w/old.s" "$w/cur.s" | sed 's/^[^ ]*  //' | LC_ALL=C sort > "$w/old.only"
    comm -13 "$w/old.s" "$w/cur.s" | sed 's/^[^ ]*  //' | LC_ALL=C sort > "$w/cur.only"
    comm -12 "$w/old.only" "$w/cur.only" > "$w/modified"
    comm -23 "$w/old.only" "$w/cur.only" > "$w/deleted"
    comm -13 "$w/old.only" "$w/cur.only" > "$w/added"
}

count_lines() { local n; n="$(wc -l < "$1")"; echo $((n + 0)); }

show_list() { # label file
    local n; n="$(count_lines "$2")"
    [ "$n" -gt 0 ] || return 0
    say "    $1 ($n):"
    head -n 10 "$2" | sed 's/^/      /'
    [ "$n" -le 10 ] || say "      ... and $((n - 10)) more"
}

interactive() { [ -t 0 ] || [ "${KIT_TEST_INTERACTIVE:-}" = 1 ]; }

confirm() {
    local ans
    printf '%s [y/N] ' "$1" >&2
    IFS= read -r ans || ans=""
    case "$ans" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

# ---- install one vault ------------------------------------------------------

install_one() { # path
    local dir="$1" vault target w="$STAGE/work" changed

    if [ ! -d "$dir" ]; then err "$dir: not a directory"; return 1; fi
    if ! vault="$(cd "$dir" && pwd -P)"; then err "$dir: cannot enter"; return 1; fi
    if [ "$vault" = "/" ] || [ "$vault" = "$HOME" ]; then err "refusing $vault"; return 1; fi
    if [ ! -d "$vault/.obsidian" ]; then err "$vault: no .obsidian/, not an Obsidian vault"; return 1; fi
    target="$vault/_kit"
    if [ -L "$target" ]; then err "$vault: _kit is a symlink, refusing"; return 1; fi
    if [ -e "$target" ] && [ ! -d "$target" ]; then err "$vault: _kit exists and is not a directory"; return 1; fi
    [ "$target" = "$vault/_kit" ] || { err "$vault: internal error, unexpected target"; return 1; }

    say "$vault/_kit"
    detect_changes "$target"
    changed=$(( $(count_lines "$w/modified") + $(count_lines "$w/deleted") + $(count_lines "$w/added") ))

    local needs_ok=0
    if [ "$UNMANAGED" = 1 ]; then
        say "  _kit/ has content but no valid install record; it would be replaced."
        needs_ok=1
    elif [ "$changed" -gt 0 ]; then
        say "  _kit/ differs from the last install (edit the repo, not _kit/):"
        show_list "modified" "$w/modified"
        show_list "deleted" "$w/deleted"
        show_list "added (would be removed)" "$w/added"
        needs_ok=1
    fi

    if [ "$DRY_RUN" = 1 ]; then
        [ "$needs_ok" = 0 ] || say "  a real run would ask first (or refuse without a terminal) unless --force"
        if [ -d "$target" ]; then
            rsync -rltn --delete -i "$STAGE/kit/" "$target/" | sed 's/^/  /'
        else
            say "  would create _kit/ with:"
            ( cd "$STAGE/kit" && find . -type f | LC_ALL=C sort | sed 's|^\./|    |' )
        fi
        return 0
    fi

    if [ "$needs_ok" = 1 ] && [ "$FORCE" = 0 ]; then
        if interactive; then
            confirm "  Overwrite these changes in $target?" || { err "$vault: left untouched"; return 1; }
        else
            err "$vault: _kit/ was edited; refusing (run interactively, or use --force)"
            return 1
        fi
    fi

    mkdir -p "$target" || { err "$vault: cannot create $target"; return 1; }
    if ! rsync -rlt --delete "$STAGE/kit/" "$target/"; then
        err "$vault: rsync failed"
        return 1
    fi
    say "  installed ${KIT_COMMIT:0:9} (uncommitted changes: $KIT_DIRTY)"
}

# ---- main -------------------------------------------------------------------

VAULTS=()
while [ $# -gt 0 ]; do
    case "$1" in
        -n|--dry-run) DRY_RUN=1 ;;
        -f|--force) FORCE=1 ;;
        -h|--help) usage; exit 0 ;;
        -*) die "unknown option: $1" ;;
        *) VAULTS+=("$1") ;;
    esac
    shift
done
[ "${#VAULTS[@]}" -gt 0 ] || { usage >&2; exit 2; }

build_stage

failed=0
for v in "${VAULTS[@]}"; do
    if ! install_one "$v"; then failed=1; fi
done
exit "$failed"
