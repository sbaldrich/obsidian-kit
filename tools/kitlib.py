"""Shared by build.py and lint.py: reading schema.yaml, checking property values,
matching folder patterns. Needs PyYAML (both tools declare it)."""
import datetime
import re
from pathlib import Path

import yaml

LINK = re.compile(r'^\[\[[^\[\]]+\]\]$')
KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


def load_schema(root: Path) -> dict:
    return yaml.safe_load((root / "schema.yaml").read_text())


def check_value(vtype: str, prop: dict, value) -> bool:
    """Is `value` acceptable for a property of schema value type `vtype`?"""
    if vtype == "date":
        return isinstance(value, datetime.date)
    if vtype == "year":
        return isinstance(value, int) and not isinstance(value, bool) and 1000 <= value <= 9999
    if vtype == "link":
        return isinstance(value, str) and bool(LINK.match(value))
    if vtype == "links":
        return isinstance(value, list) and all(isinstance(v, str) and LINK.match(v) for v in value)
    if vtype == "kebab":
        return isinstance(value, str) and bool(KEBAB.match(value))
    if vtype == "strings":
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    if vtype == "string":
        return isinstance(value, str)
    if vtype == "enum":
        return value in prop["values"]
    return False


def glob_re(pattern: str) -> re.Pattern:
    """Folder pattern -> regex. `*` is one path segment, `**` is anything."""
    out = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]+")
    return re.compile("^" + out + "$")


def matches(patterns: list[str], path: str) -> bool:
    return any(glob_re(p).match(path) for p in patterns)
