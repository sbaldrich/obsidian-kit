#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Check the notes of a vault against schema.yaml. Read-only: never writes.

    uv run tools/lint.py                  every vault in vaults.conf
    uv run tools/lint.py work             one vault, by name (from vaults.conf)
    uv run tools/lint.py ./some/vault     one vault, by path (needs a / or ~)
    uv run _kit/tools/lint.py             from a vault: lint the vault holding _kit/

Output is a rule id and a relative path per finding, never note content.
--verbose adds the offending values on stderr. Exit code: 0 no errors,
1 errors (or warnings with --strict), 2 usage problem.

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

sys.dont_write_bytecode = True   # never leave a __pycache__ in a vault's _kit/
from kitlib import check_value, matches  # noqa: E402

KIT = Path(__file__).resolve().parent.parent


class UsageError(Exception):
    """Bad arguments or configuration (exit code 2)."""


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

        props = spec.get("props") or {}
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


# ---- vault selection ------------------------------------------------------------

def read_conf() -> dict[str, Path]:
    conf = Path(os.environ.get("KIT_CONF") or KIT / "vaults.conf")
    if not conf.is_file():
        raise UsageError(f"no vaults config at {conf}")
    vaults: dict[str, Path] = {}
    for n, line in enumerate(conf.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise UsageError(f"{conf}:{n}: expected name=path")
        name, path = (s.strip() for s in line.split("=", 1))
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or not path:
            raise UsageError(f"{conf}:{n}: invalid entry")
        p = Path(path).expanduser()
        vaults[name] = p if p.is_absolute() else conf.parent.resolve() / p
    return vaults


def select(targets: list[str]) -> list[tuple[str, Path]]:
    if not targets:
        if KIT.name == "_kit":          # running from a vault's _kit/tools
            return [(KIT.parent.name, KIT.parent)]
        return list(read_conf().items())
    chosen = []
    conf = None
    for t in targets:
        if "/" in t or t.startswith(("~", ".")):
            chosen.append((Path(t).name or t, Path(t).expanduser()))
        else:
            conf = conf if conf is not None else read_conf()
            if t not in conf:
                raise UsageError(f"unknown vault '{safe(t)}' (use ./{safe(t)} for a path)")
            chosen.append((t, conf[t]))
    return chosen


def main() -> int:
    ap = argparse.ArgumentParser(description="Check vault notes against schema.yaml (read-only).")
    ap.add_argument("targets", nargs="*", help="vault names from vaults.conf, or paths containing a /")
    ap.add_argument("--schema", type=Path, default=KIT / "schema.yaml")
    ap.add_argument("--strict", action="store_true", help="warnings fail the run too")
    ap.add_argument("--verbose", action="store_true", help="also print offending values, on stderr")
    ap.add_argument("-q", "--quiet", action="store_true", help="only print the summaries")
    args = ap.parse_args()

    try:
        schema = yaml.safe_load(args.schema.read_text())
        vaults = select(args.targets)
    except UsageError as exc:
        print(f"lint.py: {exc}", file=sys.stderr)
        return 2
    except (OSError, yaml.YAMLError) as exc:
        print(f"lint.py: cannot read schema or config ({type(exc).__name__})", file=sys.stderr)
        return 2

    failed = False
    for name, path in vaults:
        resolved = path.resolve() if path.exists() else path
        if not resolved.is_dir() or resolved in (Path("/"), Path.home()):
            print(f"{safe(name)}: not a usable vault directory", file=sys.stderr)
            failed = True
            continue
        count, findings = lint_vault(resolved, schema)
        errors = sum(f.severity == "error" for f in findings)
        warnings = len(findings) - errors
        plural = lambda n, word: f"{n} {word}" + ("" if n == 1 else "s")
        print(f"{safe(name)}: {count} notes, {plural(errors, 'error')}, {plural(warnings, 'warning')}")
        if not args.quiet:
            for f in findings:
                print(f"  {f.severity:<7} {f.rule:<30} {safe(f.path)}")
                if args.verbose and f.detail:
                    sys.stdout.flush()
                    print(f"          {safe(f.detail)}", file=sys.stderr)
        if errors or (args.strict and warnings):
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
