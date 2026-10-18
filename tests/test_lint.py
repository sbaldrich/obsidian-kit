#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Tests for tools/lint.py. Vaults are built in temporary directories; nothing
real is read or written.

    uv run tests/test_lint.py
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import lint  # noqa: E402
import yaml  # noqa: E402

SCHEMA = yaml.safe_load((REPO / "schema.yaml").read_text())
LINT = REPO / "tools" / "lint.py"


def make(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def fingerprint(root: Path) -> dict:
    out = {}
    for dirpath, _, names in os.walk(root):
        for n in names:
            p = Path(dirpath) / n
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest() if not p.is_symlink() else "link"
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kit-lint-test."))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.vault = self.tmp / "vault"
        self.vault.mkdir()

    def findings(self, files: dict[str, str]) -> set[tuple[str, str]]:
        make(self.vault, files)
        _, found = lint.lint_vault(self.vault, SCHEMA)
        return {(f.rule, f.path) for f in found}

    def severities(self, files):
        make(self.vault, files)
        _, found = lint.lint_vault(self.vault, SCHEMA)
        return {f.rule: f.severity for f in found}

    def cli(self, *args, env=None):
        e = {**os.environ, **(env or {})}
        r = subprocess.run([sys.executable, str(LINT), *args], capture_output=True, text=True, env=e)
        return r.returncode, r.stdout, r.stderr


PROJECT = "---\ntype: project\nstatus: active\nstart: 2026-09-01\n---\n"
TASK = '---\ntype: task\nproject: "[[Alpha]]"\n---\n'


class TypeAndProperties(Base):
    def test_sample_vault_has_only_its_deliberate_finding(self):
        sample = REPO / "sample-vault"
        if not sample.is_dir():
            self.skipTest("no sample vault")
        _, found = lint.lint_vault(sample, SCHEMA)
        self.assertEqual({(f.rule, f.path) for f in found}, {("missing-type", "Scratch.md")})

    def test_missing_type_outside_inbox_only(self):
        f = self.findings({"loose.md": "text", "inbox/capture.md": "text", "notes/x.md": "---\nfoo: 1\n---\n"})
        self.assertEqual(f, {("missing-type", "loose.md"), ("missing-type", "notes/x.md")})

    def test_kit_and_dot_folders_are_ignored(self):
        f = self.findings({"_kit/templates/T.md": "---\ntype: nonsense\n---\n", ".obsidian/x.md": "x", ".trash/y.md": "y"})
        self.assertEqual(f, set())

    def test_unknown_type_and_bad_frontmatter(self):
        f = self.findings({"a.md": "---\ntype: gadget\n---\n", "b.md": "---\ntype: [unclosed\n---\n"})
        self.assertEqual(f, {("unknown-type", "a.md"), ("bad-frontmatter", "b.md")})

    def test_required_missing_or_empty(self):
        f = self.findings({"projects/p/P.md": "---\ntype: project\nstatus:\n---\n"})
        self.assertEqual(f, {("missing-required:status", "projects/p/P.md"), ("missing-required:start", "projects/p/P.md")})

    def test_one_of(self):
        f = self.findings({
            "projects/p/Both.md": '---\ntype: task\nproject: "[[A]]"\narea: "[[B]]"\n---\n',
            "projects/p/Neither.md": "---\ntype: task\nproject:\narea:\n---\n",
            "projects/p/One.md": '---\ntype: task\nproject: "[[A]]"\narea:\n---\n',
        })
        rules = {(r, p) for r, p in f if r == "one-of"}
        self.assertEqual(rules, {("one-of", "projects/p/Both.md"), ("one-of", "projects/p/Neither.md")})

    def test_unexpected_property_but_option_allows_extras(self):
        f = self.findings({
            "projects/p/P.md": PROJECT + "",
            "projects/p/Tagged.md": PROJECT.replace("---\n", "---\ntags: [x]\n", 1),
            "projects/p/Opt.md": "---\ntype: option\nstatus: chosen\nprice: 5\n---\n",
        })
        self.assertEqual(f, {("unexpected-property:tags", "projects/p/Tagged.md")})

    def test_invalid_values(self):
        f = self.findings({
            "records/impact/2026-01-01 A.md": '---\ntype: impact\ndate: yesterday\ncompetency: Tech Lead\ncycle: 26\n---\n',
            "records/1on1/2026-01-02 B.md": "---\ntype: 1on1\ndate: 2026-01-02\nperson: [[Unquoted]]\n---\n",
            "projects/p/Q.md": "---\ntype: project\nstatus: stopped\nstart: 2026-01-01\n---\n",
        })
        self.assertEqual(f, {
            ("invalid-value:date", "records/impact/2026-01-01 A.md"),
            ("invalid-value:competency", "records/impact/2026-01-01 A.md"),
            ("invalid-value:cycle", "records/impact/2026-01-01 A.md"),
            ("invalid-value:person", "records/1on1/2026-01-02 B.md"),
            ("invalid-value:status", "projects/p/Q.md"),
        })


class FoldersAndNames(Base):
    def test_wrong_folder_and_exemptions(self):
        meeting = "---\ntype: meeting\ndate: 2026-01-01\nattendees: ['[[A]]']\n---\n"
        f = self.findings({
            "notes/2026-01-01 M.md": meeting,
            "meetings/2026-01-01 Ok.md": meeting,
            "archive/old/2026-01-01 Arch.md": meeting,
            "areas/home/archive/2025/2026-01-01 Hist.md": meeting,
        })
        self.assertEqual(f, {("wrong-folder", "notes/2026-01-01 M.md")})

    def test_name_rules(self):
        decision = '---\ntype: decision\ndate: 2026-10-15\nproject: "[[A]]"\n---\n'
        series = "---\ntype: meeting\ndate: 2026-01-08\nattendees: ['[[A]]']\n---\n"
        f = self.findings({
            "records/decisions/Backfill.md": decision,
            "records/decisions/2026-10-16 Wrong date.md": decision,
            "records/decisions/2026-10-15 Fine.md": decision,
            "meetings/2026 Team sync.md": series,
        })
        self.assertEqual(f, {("name-pattern", "records/decisions/Backfill.md"),
                             ("name-date-mismatch", "records/decisions/2026-10-16 Wrong date.md")})

    def test_folder_name_reported_once_per_folder(self):
        f = self.findings({"Projects/My Thing/A.md": PROJECT, "Projects/My Thing/B.md": PROJECT})
        names = [x for x in f if x[0] == "folder-name"]
        self.assertEqual(names, [("folder-name", "Projects/My Thing")])

    def test_duplicate_names(self):
        f = self.findings({"inbox/Same.md": "x", "reference/Same.md": "---\ntype: hub\n---\n"})
        self.assertEqual({(r, p) for r, p in f if r == "duplicate-name"},
                         {("duplicate-name", "inbox/Same.md"), ("duplicate-name", "reference/Same.md")})


class Checkboxes(Base):
    def base(self, extra: dict[str, str]) -> set:
        files = {"projects/a/Alpha.md": PROJECT, "projects/a/Job.md": TASK}
        files.update(extra)
        return {(r, p) for r, p in self.findings(files) if r.startswith(("task-", "unknown-checkbox"))}

    def test_exactly_one_checkbox_in_home_is_clean(self):
        f = self.base({"projects/a/Alpha.md": PROJECT + "- [/] [[Job]]\n- [>] [[Job]]\n"})
        self.assertEqual(f, set())

    def test_no_checkbox_is_a_warning(self):
        f = self.base({})
        self.assertEqual(f, {("task-no-checkbox", "projects/a/Job.md")})
        self.assertEqual(self.severities({})["task-no-checkbox"], "warning")

    def test_moved_alone_is_not_a_status(self):
        f = self.base({"projects/a/Alpha.md": PROJECT + "- [>] [[Job]]\n"})
        self.assertEqual(f, {("task-no-checkbox", "projects/a/Job.md")})

    def test_two_checkboxes_is_an_error_even_in_one_note(self):
        f = self.base({"projects/a/Alpha.md": PROJECT + "- [ ] [[Job]]\n- [x] [[Job]]\n"})
        self.assertEqual(f, {("task-multiple-checkboxes", "projects/a/Job.md")})
        self.assertEqual(self.severities({})["task-multiple-checkboxes"], "error")

    def test_second_checkbox_in_another_note(self):
        f = self.base({"projects/a/Alpha.md": PROJECT + "- [ ] [[Job]]\n", "daily/2026-01-01.md": "---\ntype: daily\ndate: 2026-01-01\n---\n- [x] [[Job]]\n"})
        self.assertEqual(f, {("task-multiple-checkboxes", "projects/a/Job.md")})

    def test_checkbox_outside_home_is_a_warning(self):
        f = self.base({"daily/2026-01-01.md": "---\ntype: daily\ndate: 2026-01-01\n---\n- [ ] [[Job]]\n"})
        self.assertEqual(f, {("task-checkbox-outside-home", "projects/a/Job.md")})
        self.assertEqual(self.severities({})["task-checkbox-outside-home"], "warning")

    def test_code_blocks_embeds_and_aliases(self):
        text = PROJECT + "```\n- [ ] [[Job]]\n```\n- [ ] ![[Job]]\n- [/] [[Job|the job]]\n- [X] other [[Elsewhere]]\n"
        self.assertEqual(self.base({"projects/a/Alpha.md": text}), set())

    def test_unknown_checkbox_state(self):
        f = self.base({"projects/a/Alpha.md": PROJECT + "- [/] [[Job]]\n- [i] a plain item\n"})
        self.assertEqual(f, {("unknown-checkbox", "projects/a/Alpha.md")})


class Safety(Base):
    def test_symlinks_are_not_followed(self):
        outside = self.tmp / "outside"
        make(outside, {"bad.md": "---\ntype: nonsense\n---\n"})
        make(self.vault, {"ok.md": "---\ntype: hub\n---\n"})
        os.symlink(outside, self.vault / "linked-dir")
        os.symlink(outside / "bad.md", self.vault / "linked-file.md")
        count, found = lint.lint_vault(self.vault, SCHEMA)
        self.assertEqual(count, 1)
        self.assertEqual({(f.rule, f.path) for f in found}, {("wrong-folder", "ok.md")})

    def test_values_stay_out_of_output_unless_verbose(self):
        make(self.vault, {"projects/p/P.md": "---\ntype: project\nstatus: SECRET-VALUE-123\nstart: 2026-01-01\n---\n"})
        rc, out, err = self.cli(str(self.vault) + "/")
        self.assertEqual(rc, 1)
        self.assertNotIn("SECRET-VALUE-123", out + err)
        rc, out, err = self.cli("--verbose", str(self.vault) + "/")
        self.assertNotIn("SECRET-VALUE-123", out)
        self.assertIn("SECRET-VALUE-123", err)

    def test_control_characters_in_names_are_escaped(self):
        make(self.vault, {"bad\x1b[31mname.md": "no type"})
        rc, out, err = self.cli(str(self.vault) + "/")
        self.assertNotIn("\x1b", out + err)
        self.assertIn("\\x1b", out)

    def test_lint_never_writes(self):
        make(self.vault, {"a.md": "x", "projects/p/P.md": PROJECT, "projects/p/Job.md": TASK, ".obsidian/app.json": "{}"})
        before = fingerprint(self.vault)
        self.cli(str(self.vault) + "/")
        self.cli("--strict", "--verbose", str(self.vault) + "/")
        self.assertEqual(fingerprint(self.vault), before)


class Cli(Base):
    def test_exit_codes(self):
        make(self.vault, {"reference/Hub.md": "---\ntype: hub\n---\n"})
        self.assertEqual(self.cli(str(self.vault) + "/")[0], 0)
        make(self.vault, {"stray.md": "no type"})
        self.assertEqual(self.cli(str(self.vault) + "/")[0], 1)

    def test_warnings_pass_unless_strict(self):
        make(self.vault, {"notes/Hub.md": "---\ntype: hub\n---\n"})   # wrong-folder: warning only
        self.assertEqual(self.cli(str(self.vault) + "/")[0], 0)
        self.assertEqual(self.cli("--strict", str(self.vault) + "/")[0], 1)

    def test_vault_names_come_from_the_config(self):
        make(self.vault, {"reference/Hub.md": "---\ntype: hub\n---\n"})
        conf = self.tmp / "vaults.conf"
        conf.write_text(f"# comment\n\nmine = {self.vault}\n")
        rc, out, _ = self.cli("mine", env={"KIT_CONF": str(conf)})
        self.assertEqual(rc, 0)
        self.assertIn("mine: 1 notes, 0 errors, 0 warnings", out)
        rc, _, err = self.cli("nope", env={"KIT_CONF": str(conf)})
        self.assertEqual(rc, 2)
        rc, _, err = self.cli("mine", env={"KIT_CONF": str(self.tmp / "missing.conf")})
        self.assertEqual(rc, 2)

    def test_not_a_directory(self):
        self.assertEqual(self.cli(str(self.tmp / "nope") + "/")[0], 1)

    def test_runs_from_a_vaults_kit_folder_without_arguments(self):
        make(self.vault, {"reference/Hub.md": "---\ntype: hub\n---\n"})
        kit = self.vault / "_kit"
        (kit / "tools").mkdir(parents=True)
        for name in ("lint.py", "kitlib.py"):
            shutil.copy(REPO / "tools" / name, kit / "tools" / name)
        shutil.copy(REPO / "schema.yaml", kit / "schema.yaml")
        r = subprocess.run([sys.executable, str(kit / "tools" / "lint.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("vault: 1 notes, 0 errors, 0 warnings", r.stdout)
        self.assertEqual(list(kit.rglob("__pycache__")), [], "linting must not write into _kit/")


if __name__ == "__main__":
    unittest.main(verbosity=1)
