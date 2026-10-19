#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Check the notes of a vault against schema.yaml. Read-only: never writes.

    uv run tools/lint.py <vault-path> [...]

Findings are grouped by rule, most frequent first, each with a hint on how to
fix it and up to 5 example paths. --rule lists every path for one rule
(`--rule missing-required` matches every property), --all prints one line per
finding. --ignore <folder> hides findings for the notes under a folder;
--under <folder> shows only those (both repeatable, relative to the vault,
`*` and `**` allowed). Hidden notes are still read, so a duplicate name or a
checkbox involving them still counts elsewhere.
Output is rule ids and relative paths, never note content; --verbose
adds the offending values on stderr. Exit code: 0 no errors, 1 errors (or
warnings with --strict), 2 usage problem.

Rules (severity):
  error   missing-type  unknown-type  bad-frontmatter  missing-required:<prop>
          one-of  unexpected-property:<prop>  invalid-value:<prop>
  warning wrong-folder  name-pattern  name-date-mismatch  folder-name
          duplicate-name  unknown-checkbox
  per schema.yaml (task_checkbox): task-multiple-checkboxes
          task-no-checkbox  task-checkbox-outside-home
"""
import argparse
import datetime
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml

sys.dont_write_bytecode = True   # leave no __pycache__ behind
from kitlib import check_value, matches  # noqa: E402

REPO = Path(__file__).resolve().parent.parent

SKIP_DIRS = {"_kit"}
FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
FENCE = re.compile(r"^\s*(```|~~~)")
CHECKBOX = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[(.)\](?:\s|$)")
WIKILINK = re.compile(r"(?<!!)\[\[([^\[\]]+)\]\]")
PROP_LINK = re.compile(r"^\[\[([^\]|#]+)")
EMPTY = (None, "", [])


@dataclass(frozen=True)
class Finding:
    severity: str          # "error" | "warning"
    rule: str              # rule id, may carry a property name: "missing-required:status"
    path: str              # path relative to the vault
    detail: str = ""       # shown only with --verbose


def safe(text: str) -> str:
    """Escape control and invisible characters before printing an untrusted string."""
    return "".join(c if c.isprintable() else f"\\x{ord(c):02x}" for c in text)


def link_stem(target: str) -> str:
    """'folder/Note#Heading|alias' -> 'Note'."""
    target = re.split(r"[|#^]", target, maxsplit=1)[0].strip()
    stem = PurePosixPath(target).name
    return stem[:-3] if stem.endswith(".md") else stem


def find_notes(vault: Path) -> list[str]:
    """Relative paths of *.md files, skipping dot-folders, _kit and symlinks."""
    found = []
    for dirpath, dirnames, filenames in os.walk(vault, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames
                             if not d.startswith(".") and d not in SKIP_DIRS
                             and not os.path.islink(os.path.join(dirpath, d)))
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if name.endswith(".md") and not name.startswith(".") and not os.path.islink(full):
                found.append(os.path.relpath(full, vault).replace(os.sep, "/"))
    return found


def parse_note(vault: Path, rel: str) -> tuple[str, dict | None, str | None]:
    """(text, frontmatter or None, parse error). No frontmatter gives ({} , None)."""
    text = (vault / rel).read_text(encoding="utf-8", errors="replace")
    m = FRONTMATTER.match(text)
    if not m:
        return text, {}, None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        return text, None, type(exc).__name__
    if data is None:
        return text, {}, None
    if not isinstance(data, dict):
        return text, None, "not a mapping"
    return text, data, None


def checkboxes(text: str) -> list[tuple[str, list[str]]]:
    """[(status char, [link stems])] for checkbox lines outside fenced code."""
    result, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = CHECKBOX.match(line)
        if m:
            result.append((m.group(1), [link_stem(t) for t in WIKILINK.findall(line)]))
    return result


def lint_vault(vault: Path, schema: dict) -> tuple[int, list[Finding]]:
    types = schema["types"]
    states = {k.lower() for k in schema.get("checkboxes", {})}
    repeatable = set(schema.get("task_checkbox", {}).get("repeatable", []))
    task_rules = {r["id"]: r["severity"] for r in schema.get("task_checkbox", {}).get("rules", [])}
    findings: list[Finding] = []
    add = lambda sev, rule, path, detail="": findings.append(Finding(sev, rule, path, detail))

    notes = find_notes(vault)
    parsed: dict[str, tuple[str, dict]] = {}
    seen_folders: set[str] = set()
    stems: dict[str, list[str]] = {}

    for rel in notes:
        pure = PurePosixPath(rel)
        folder, stem = pure.parent.as_posix(), pure.stem
        stems.setdefault(stem, []).append(rel)

        if folder != "." and folder not in seen_folders:
            seen_folders.add(folder)
            bad = [p for p in PurePosixPath(folder).parts if not re.match(schema["folder_name"], p)]
            if bad:
                add("warning", "folder-name", folder, ", ".join(bad))

        text, fm, err = parse_note(vault, rel)
        if err:
            add("error", "bad-frontmatter", rel, err)
            continue
        parsed[rel] = (text, fm)

        ntype = fm.get("type")
        probe = (folder + "/x") if folder != "." else "x"
        if ntype in EMPTY:
            if not matches(schema["untyped"], probe):
                add("error", "missing-type", rel)
            continue
        spec = types.get(ntype) if isinstance(ntype, str) else None
        if spec is None:
            add("error", "unknown-type", rel, repr(ntype))
            continue

        props = {**(schema.get("all_types") or {}), **(spec.get("props") or {})}
        for name in spec.get("required", []):
            if fm.get(name) in EMPTY:
                add("error", f"missing-required:{name}", rel)
        if spec.get("one_of"):
            present = [k for k in spec["one_of"] if fm.get(k) not in EMPTY]
            if len(present) != 1:
                add("error", "one-of", rel, f"{len(present)} of {spec['one_of']} set")
        for name, value in fm.items():
            if name == "type":
                continue
            if name not in props:
                if spec.get("extra") != "allow":
                    add("error", f"unexpected-property:{name}", rel)
            elif value not in EMPTY and not check_value(props[name]["type"], props[name], value):
                add("error", f"invalid-value:{name}", rel, f"{props[name]['type']}: {value!r}")

        if not matches(schema["folder_exempt"], probe) and not any(
                matches([f], folder) for f in spec["folder"]):
            add("warning", "wrong-folder", rel, f"{ntype} expected in {spec['folder']}")
        if spec.get("name") and not any(re.match(p, stem) for p in spec["name"]):
            add("warning", "name-pattern", rel, f"{ntype} names match {spec['name']}")
        prefix = re.match(r"^(\d{4}-\d{2}-\d{2})\b", stem)
        if (schema.get("name_date_matches_property") and prefix and "date" in props
                and isinstance(fm.get("date"), datetime.date) and str(fm["date"]) != prefix.group(1)):
            add("warning", "name-date-mismatch", rel, f"name {prefix.group(1)}, date {fm.get('date')}")

    for stem, paths in sorted(stems.items()):
        if len(paths) > 1:
            for rel in paths:
                add("warning", "duplicate-name", rel, f"{len(paths)} notes named '{stem}'")

    # ---- checkboxes ---------------------------------------------------------
    boxes: dict[str, list[str]] = {}     # task stem -> notes holding a non-repeatable checkbox
    for rel, (text, fm) in parsed.items():
        unknown = set()
        for char, targets in checkboxes(text):
            if char.lower() not in states:
                unknown.add(char)
            if char in repeatable:
                continue
            for stem in targets:
                boxes.setdefault(stem, []).append(rel)
        for char in sorted(unknown):
            add("warning", "unknown-checkbox", rel, f"[{char}]")

    for rel, (text, fm) in parsed.items():
        if fm.get("type") != "task":
            continue
        stem = PurePosixPath(rel).stem
        found = boxes.get(stem, [])
        home_raw = next((fm[k] for k in ("project", "area") if fm.get(k) not in EMPTY), "")
        m = PROP_LINK.match(str(home_raw))
        home = link_stem(m.group(1)) if m else ""
        if len(found) > 1:
            add(task_rules.get("task-multiple-checkboxes", "error"), "task-multiple-checkboxes", rel,
                f"{len(found)} checkboxes")
        elif not found:
            add(task_rules.get("task-no-checkbox", "warning"), "task-no-checkbox", rel)
        elif home and PurePosixPath(found[0]).stem != home:
            add(task_rules.get("task-checkbox-outside-home", "warning"), "task-checkbox-outside-home", rel,
                f"checkbox in {found[0]}, home is {home}")

    findings.sort(key=lambda f: (f.severity != "error", f.path, f.rule))
    return len(notes), findings


# ---- report -----------------------------------------------------------------

EXAMPLES = 5


def family(rule: str) -> str:
    """'missing-required:status' -> 'missing-required'."""
    return rule.split(":", 1)[0]


def hints(schema: dict) -> dict[str, str]:
    """One suggestion per rule family on how to fix it, filled in from the schema."""
    types = ", ".join(schema["types"])
    extra = [f"`{t}`" for t, spec in schema["types"].items() if spec.get("extra") == "allow"]
    boxes = " ".join(f"[{c}]" for c in schema.get("checkboxes", {}))
    return {
        "missing-type": f"Add `type:` ({types}), or move the note to inbox/.",
        "unknown-type": f"Use one of: {types}. To keep a type of your own, add it to schema.yaml.",
        "bad-frontmatter": "The YAML between the --- lines doesn't parse; quote values that "
                           "contain ': ', '#' or start with '[['.",
        "missing-required": "Fill in the property; the type's template in _kit/templates/ shows its shape.",
        "one-of": "Set exactly one of the alternatives (for tasks and decisions: `project` or `area`).",
        "unexpected-property": "Remove or rename it, or add it to its type (or to all_types) in schema.yaml"
                               + (f" (only {', '.join(extra)} notes allow extra properties)." if extra else "."),
        "invalid-value": "Use the schema's format: dates YYYY-MM-DD, links \"[[Note]]\", lists as YAML "
                         "lists, enums one of their values (see the type in schema.yaml).",
        "wrong-folder": "Move it to its type's folder, in Obsidian so links update "
                        "(--verbose shows the expected folder).",
        "name-pattern": "Rename it to the type's pattern, e.g. `YYYY-MM-DD Title` for dated notes.",
        "name-date-mismatch": "Make the date in the name equal the `date` property.",
        "folder-name": "Rename the folder to lowercase-with-hyphens, in Obsidian so links update.",
        "duplicate-name": "Rename so every note name is unique: links and embeds resolve by name.",
        "unknown-checkbox": f"Use one of {boxes}.",
        "task-multiple-checkboxes": "Keep one checkbox, in the home note; mark the others [>] (moved).",
        "task-no-checkbox": "Add a checkbox line linking to the task in its home note.",
        "task-checkbox-outside-home": "Move the checkbox to the home note (its project or area); "
                                      "leave [>] where it was.",
    }


def breakdown(fam: str, items: list[Finding]) -> str:
    """Short summary of what a group is made of, e.g. 'relation 45, birthday 44'."""
    if fam == "duplicate-name":
        names = len({PurePosixPath(f.path).stem for f in items})
        return f"{names} name" + ("" if names == 1 else "s")
    counts: dict[str, int] = {}
    for f in items:
        if ":" in f.rule:
            key = f.rule.split(":", 1)[1]
            counts[key] = counts.get(key, 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    text = ", ".join(f"{safe(k)} {n}" for k, n in top[:6])
    return text + (f", +{len(top) - 6} more" if len(top) > 6 else "")


def print_detail(f: Finding, verbose: bool) -> None:
    if verbose and f.detail:
        sys.stdout.flush()
        print(f"            {safe(f.detail)}", file=sys.stderr)


def print_grouped(findings: list[Finding], hint: dict[str, str], limit: int | None, verbose: bool) -> None:
    groups: dict[str, list[Finding]] = {}
    for f in findings:
        groups.setdefault(family(f.rule), []).append(f)
    order = sorted(groups.items(), key=lambda kv: (kv[1][0].severity != "error", -len(kv[1]), kv[0]))
    for fam, items in order:
        print(f"\n  {items[0].severity:<7} {fam:<26} {len(items):>5}  {breakdown(fam, items)}".rstrip())
        print(f"          {hint.get(fam, '')}")
        shown = items if limit is None else items[:limit]
        for f in shown:
            sub = f"  ({safe(f.rule.split(':', 1)[1])})" if ":" in f.rule else ""
            print(f"            {safe(f.path)}{sub}")
            print_detail(f, verbose)
        if len(items) > len(shown):
            print(f"            ... and {len(items) - len(shown)} more (--rule {fam})")


def folder_patterns(raw: list[str]) -> list[str]:
    """Normalise --ignore/--under folders to vault-relative patterns; ValueError if unusable."""
    result = []
    for item in raw:
        p = PurePosixPath(item)      # drops "./" and trailing slashes
        if p.is_absolute() or not p.parts or ".." in p.parts:
            raise ValueError(item)
        result.append(p.as_posix())
    return result


def within(patterns: list[str], path: str) -> bool:
    """Is `path` one of the folders in `patterns`, or under one?"""
    return any(matches([p, p + "/**"], path) for p in patterns)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check vault notes against schema.yaml (read-only).")
    ap.add_argument("vaults", nargs="+", type=Path, help="path of a vault")
    ap.add_argument("--schema", type=Path, default=REPO / "schema.yaml")
    ap.add_argument("--strict", action="store_true", help="warnings fail the run too")
    ap.add_argument("--verbose", action="store_true", help="also print offending values, on stderr")
    ap.add_argument("-q", "--quiet", action="store_true", help="only print the summaries")
    ap.add_argument("--rule", action="append", default=[],
                    help="list every finding of this rule or rule family (repeatable)")
    ap.add_argument("--all", action="store_true", help="one line per finding, ungrouped")
    ap.add_argument("--ignore", action="append", default=[], metavar="FOLDER",
                    help="hide findings under this vault folder (repeatable)")
    ap.add_argument("--under", action="append", default=[], metavar="FOLDER",
                    help="show only findings under this vault folder (repeatable)")
    args = ap.parse_args()
    try:
        skip = folder_patterns(args.ignore)
        only = folder_patterns(args.under)
    except ValueError as exc:
        print(f"lint.py: --ignore and --under need a folder inside the vault, got {safe(str(exc))!r}",
              file=sys.stderr)
        return 2
    shown_path = lambda path: (not only or within(only, path)) and not within(skip, path)

    try:
        schema = yaml.safe_load(args.schema.read_text())
    except (OSError, yaml.YAMLError) as exc:
        print(f"lint.py: cannot read schema ({type(exc).__name__})", file=sys.stderr)
        return 2
    hint = hints(schema)
    unknown = [r for r in args.rule if family(r) not in hint]
    if unknown:
        print(f"lint.py: unknown rule {safe(unknown[0])} (rules: {', '.join(hint)})", file=sys.stderr)
        return 2

    failed = False
    for path in args.vaults:
        name = str(path)
        resolved = path.resolve() if path.exists() else path
        if not resolved.is_dir() or resolved in (Path("/"), Path.home().resolve()):
            print(f"{safe(name)}: not a usable vault directory", file=sys.stderr)
            failed = True
            continue
        count, findings = lint_vault(resolved, schema)
        hidden = 0
        if skip or only:
            notes = find_notes(resolved)
            for flag, patterns in (("--ignore", skip), ("--under", only)):
                for p in patterns:
                    if not any(within([p], n) for n in notes):
                        print(f"lint.py: {flag} {safe(p)} matches no note in {safe(name)}", file=sys.stderr)
            hidden = sum(not shown_path(n) for n in notes)
            findings = [f for f in findings if shown_path(f.path)]
        errors = sum(f.severity == "error" for f in findings)
        warnings = len(findings) - errors
        plural = lambda n, word: f"{n} {word}" + ("" if n == 1 else "s")
        notes_text = plural(count - hidden, "note") + (f" ({hidden} hidden)" if skip or only else "")
        print(f"{safe(name)}: {notes_text}, {plural(errors, 'error')}, {plural(warnings, 'warning')}")
        shown = [f for f in findings if not args.rule or f.rule in args.rule or family(f.rule) in args.rule]
        if args.quiet:
            pass
        elif args.all:
            for f in shown:
                print(f"  {f.severity:<7} {safe(f.rule):<30} {safe(f.path)}")
                print_detail(f, args.verbose)
        else:
            print_grouped(shown, hint, None if args.rule else EXAMPLES, args.verbose)
        if errors or (args.strict and warnings):
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
