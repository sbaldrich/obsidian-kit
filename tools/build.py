#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Generate templates/ and types.json from schema.yaml.

    uv run tools/build.py            validate, then write the outputs
    uv run tools/build.py --check    validate, then fail if outputs are stale

Validation covers schema.yaml itself (every property declared once, one value
type per property name), the base embeds in `sections` (the base and view must
exist in bases/), the base links in the hand-written templates/*checklist.md,
and the example frontmatter in schema.md. Generated templates are named
"<Type> template.md"; the checklists are left alone. Only files inside the
repo are read or written.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import yaml
from kitlib import check_value, load_schema

# Schema value type -> Obsidian property type (as stored in types.json).
OBSIDIAN_TYPES = {
    "date": "date",
    "year": "number",
    "link": "text",
    "string": "text",
    "kebab": "text",
    "enum": "text",
    "links": "multitext",
    "strings": "multitext",
}
# Obsidian reserves these property names for a dedicated type.
RESERVED_NAMES = {"aliases": "aliases"}

TEMPLATE_SUFFIX = " template.md"


def template_name(type_name: str) -> str:
    return type_name[0].upper() + type_name[1:] + TEMPLATE_SUFFIX


def prop_types(schema: dict) -> dict[str, str]:
    """Obsidian type per property name, across all note types."""
    result = {"type": "text"}
    for spec in schema["types"].values():
        for name, prop in (spec.get("props") or {}).items():
            result[name] = RESERVED_NAMES.get(name) or OBSIDIAN_TYPES[prop["type"]]
    return result


def validate_schema(schema: dict) -> list[str]:
    errors = []
    seen: dict[str, tuple[str, str]] = {}
    for tname, spec in schema["types"].items():
        props = spec.get("props") or {}
        declared = set(spec.get("required", [])) | set(spec.get("optional", [])) | set(spec.get("one_of", []))
        for name in declared - props.keys():
            errors.append(f"{tname}.{name}: listed as required/optional/one_of but has no props entry")
        for name in props.keys() - declared:
            errors.append(f"{tname}.{name}: props entry is not required, optional or one_of")
        if not isinstance(spec.get("sections"), list):
            errors.append(f"{tname}: sections must be a list (may be empty)")
        else:
            for item in spec["sections"]:
                ok = isinstance(item, str) or (
                    isinstance(item, dict) and len(item) == 1
                    and isinstance(next(iter(item.values())), list)
                    and all(isinstance(e, str) for e in next(iter(item.values())))
                )
                if not ok:
                    errors.append(f"{tname}: a sections item must be a heading or {{heading: [embeds]}}")
        for pattern in spec.get("name", []):
            try:
                re.compile(pattern)
            except re.error:
                errors.append(f"{tname}: invalid name pattern")
        for name, prop in props.items():
            vtype = prop.get("type")
            if vtype not in OBSIDIAN_TYPES:
                errors.append(f"{tname}.{name}: unknown value type")
                continue
            if vtype == "enum" and not prop.get("values"):
                errors.append(f"{tname}.{name}: enum without values")
            obs = RESERVED_NAMES.get(name) or OBSIDIAN_TYPES[vtype]
            if name in seen and seen[name][1] != obs:
                errors.append(f"{name}: Obsidian type conflict between {seen[name][0]} and {tname}")
            seen.setdefault(name, (tname, obs))
    return errors


def sections_of(spec: dict) -> list[tuple[str, list[str]]]:
    """Body sections as (heading, embeds). An item is a heading, or {heading: [embeds]}."""
    result = []
    for item in spec["sections"]:
        if isinstance(item, str):
            result.append((item, []))
        else:
            ((heading, embeds),) = item.items()
            result.append((heading, embeds))
    return result


EMBED = re.compile(r"^([^#\[\]|]+\.base)(?:#(.+))?$")
BASE_LINK = re.compile(r"\[\[([^\[\]#|]+\.base)(?:#([^\[\]|]+))?\]\]")
CHECKLIST_SUFFIX = " checklist.md"


def base_ref_error(root: Path, base: str, view: str | None, cache: dict[str, set[str]]) -> str | None:
    """None if bases/<base> exists and has the view (when given), else a message."""
    path = root / "bases" / base
    if not path.is_file():
        return f"no such base '{base}'"
    if base not in cache:
        data = yaml.safe_load(path.read_text()) or {}
        cache[base] = {v.get("name") for v in data.get("views", [])}
    if view and view not in cache[base]:
        return f"base '{base}' has no view '{view}'"
    return None


def validate_embeds(root: Path, schema: dict) -> list[str]:
    """Every embed must name an existing base in bases/ and, if given, an existing view."""
    errors = []
    cache: dict[str, set[str]] = {}
    for tname, spec in schema["types"].items():
        for heading, embeds in sections_of(spec):
            for embed in embeds:
                m = EMBED.match(embed)
                if not m:
                    errors.append(f"{tname}/{heading}: malformed embed '{embed}'")
                    continue
                problem = base_ref_error(root, m.group(1), m.group(2), cache)
                if problem:
                    errors.append(f"{tname}/{heading}: {problem}")
    return errors


def validate_checklists(root: Path) -> list[str]:
    """Hand-written templates/*checklist.md may link to bases; those links must resolve."""
    errors = []
    cache: dict[str, set[str]] = {}
    folder = root / "templates"
    for path in sorted(folder.glob("*" + CHECKLIST_SUFFIX)) if folder.is_dir() else []:
        for base, view in BASE_LINK.findall(path.read_text()):
            problem = base_ref_error(root, base, view or None, cache)
            if problem:
                errors.append(f"templates/{path.name}: {problem}")
    return errors


def default_value(name: str, prop: dict, required: bool) -> str:
    if not required:
        return ""
    if prop["type"] == "date" and name in ("date", "start"):
        return "{{date:YYYY-MM-DD}}"
    if prop["type"] == "year" and name == "cycle":
        return "{{date:YYYY}}"
    if prop["type"] == "enum":
        return prop["values"][0]
    return ""


def render_template(type_name: str, spec: dict) -> str:
    lines = ["---", f"type: {type_name}"]
    required = set(spec.get("required", []))
    for name, prop in (spec.get("props") or {}).items():
        value = default_value(name, prop, name in required)
        lines.append(f"{name}: {value}" if value else f"{name}:")
    lines.append("---")
    out = "\n".join(lines) + "\n"
    blocks = []
    for heading, embeds in sections_of(spec):
        blocks.append("\n\n".join([f"## {heading}"] + [f"![[{e}]]" for e in embeds]))
    if blocks:
        out += "\n" + "\n\n".join(blocks) + "\n"
    return out


def render_types_json(schema: dict) -> str:
    return json.dumps({"types": dict(sorted(prop_types(schema).items()))}, indent=2) + "\n"


def outputs(root: Path, schema: dict) -> dict[Path, str]:
    result = {root / "types.json": render_types_json(schema)}
    for tname, spec in schema["types"].items():
        result[root / "templates" / template_name(tname)] = render_template(tname, spec)
    return result


def validate_examples(root: Path, schema: dict) -> list[str]:
    """The example frontmatter blocks in schema.md must satisfy schema.yaml."""
    text = (root / "schema.md").read_text()
    match = re.search(r"## Properties.*?```yaml\n(.*?)```", text, re.S)
    if not match:
        return ["schema.md: no yaml example block under '## Properties'"]
    chunks = [c for c in re.split(r"^# [^\n]*\n(?=type:)", match.group(1), flags=re.M) if c.strip()]
    errors, seen = [], set()
    for chunk in chunks:
        fm = yaml.safe_load(chunk)
        tname = fm.get("type")
        seen.add(tname)
        spec = schema["types"].get(tname)
        if spec is None:
            errors.append(f"schema.md example: unknown type {tname}")
            continue
        props = spec.get("props") or {}
        for name in spec.get("required", []):
            if fm.get(name) in (None, [], ""):
                errors.append(f"schema.md example {tname}: required {name} missing or empty")
        if spec.get("one_of"):
            present = [k for k in spec["one_of"] if fm.get(k) is not None]
            if len(present) != 1:
                errors.append(f"schema.md example {tname}: expected exactly one of {spec['one_of']}")
        for name, value in fm.items():
            if name == "type":
                continue
            if name not in props:
                if spec.get("extra") != "allow":
                    errors.append(f"schema.md example {tname}: unexpected property {name}")
            elif value is not None and not check_value(props[name]["type"], props[name], value):
                errors.append(f"schema.md example {tname}.{name}: invalid value")
    for missing in sorted(set(schema["types"]) - seen):
        errors.append(f"schema.md: no example for type {missing}")
    return errors


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".build-")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def stale_templates(root: Path, wanted: dict[Path, str]) -> list[Path]:
    folder = root / "templates"
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.name.endswith(TEMPLATE_SUFFIX) and p not in wanted)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="verify instead of writing")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="repo root (default: parent of tools/)")
    args = parser.parse_args()
    root = args.root.resolve()

    schema = load_schema(root)
    errors = validate_schema(schema)
    if not errors:
        errors += validate_embeds(root, schema)
        errors += validate_checklists(root)
        errors += validate_examples(root, schema)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    wanted = outputs(root, schema)
    stale = stale_templates(root, wanted)

    if args.check:
        problems = []
        for path, text in wanted.items():
            rel = path.relative_to(root)
            if not path.exists():
                problems.append(f"missing: {rel}")
            elif path.read_text() != text:
                problems.append(f"out of date: {rel}")
        problems += [f"stale: {p.relative_to(root)}" for p in stale]
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(f"ok: {len(wanted)} generated files match schema.yaml")
        return 0

    for path, text in wanted.items():
        if not path.exists() or path.read_text() != text:
            write_atomic(path, text)
    for path in stale:
        path.unlink()
    print(f"wrote {len(wanted)} files, removed {len(stale)} stale")
    return 0


if __name__ == "__main__":
    sys.exit(main())
