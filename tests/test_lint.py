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

    def cli(self, *args):
        env = {**os.environ, "HOME": str(self.tmp)}   # nothing real under HOME is reachable
        r = subprocess.run([sys.executable, str(LINT), *args], capture_output=True, text=True, env=env)
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

    def test_aliases_allowed_on_every_type(self):
        f = self.findings({
            "projects/p/A.md": PROJECT.replace("---\n", "---\naliases: [Alpha, The A]\n", 1),
            "reference/H.md": "---\ntype: hub\naliases:\n---\n",
            "projects/p/B.md": PROJECT.replace("---\n", "---\naliases: Beta\n", 1),
            "projects/p/C.md": PROJECT.replace("---\n", "---\nalias: [Gamma]\n", 1),
        })
        self.assertEqual(f, {
            ("invalid-value:aliases", "projects/p/B.md"),      # must be a list
            ("unexpected-property:alias", "projects/p/C.md"),  # only the plural is Obsidian's
        })

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
        rc, out, err = self.cli(str(self.vault))
        self.assertEqual(rc, 1)
        self.assertNotIn("SECRET-VALUE-123", out + err)
        rc, out, err = self.cli("--verbose", str(self.vault))
        self.assertNotIn("SECRET-VALUE-123", out)
        self.assertIn("SECRET-VALUE-123", err)

    def test_control_characters_in_names_are_escaped(self):
        make(self.vault, {"bad\x1b[31mname.md": "no type"})
        rc, out, err = self.cli(str(self.vault))
        self.assertNotIn("\x1b", out + err)
        self.assertIn("\\x1b", out)

    def test_lint_never_writes(self):
        make(self.vault, {"a.md": "x", "projects/p/P.md": PROJECT, "projects/p/Job.md": TASK, ".obsidian/app.json": "{}"})
        before = fingerprint(self.vault)
        self.cli(str(self.vault))
        self.cli("--strict", "--verbose", str(self.vault))
        self.assertEqual(fingerprint(self.vault), before)


class Cli(Base):
    def test_exit_codes(self):
        make(self.vault, {"reference/Hub.md": "---\ntype: hub\n---\n"})
        self.assertEqual(self.cli(str(self.vault))[0], 0)
        make(self.vault, {"stray.md": "no type"})
        self.assertEqual(self.cli(str(self.vault))[0], 1)

    def test_warnings_pass_unless_strict(self):
        make(self.vault, {"notes/Hub.md": "---\ntype: hub\n---\n"})   # wrong-folder: warning only
        self.assertEqual(self.cli(str(self.vault))[0], 0)
        self.assertEqual(self.cli("--strict", str(self.vault))[0], 1)

    def test_needs_a_vault_path(self):
        self.assertEqual(self.cli()[0], 2)

    def test_several_vaults_one_summary_each(self):
        make(self.vault, {"reference/Hub.md": "---\ntype: hub\n---\n"})
        other = make(self.tmp / "other", {"stray.md": "no type"})
        rc, out, _ = self.cli(str(self.vault), str(other))
        self.assertEqual(rc, 1)
        self.assertIn(f"{self.vault}: 1 note, 0 errors, 0 warnings", out)
        self.assertIn(f"{other}: 1 note, 1 error, 0 warnings", out)

    def test_refuses_home(self):
        # HOME is redirected to self.tmp, so this also proves the redirect works.
        rc, _, err = self.cli(str(self.tmp))
        self.assertEqual(rc, 1)
        self.assertIn("not a usable vault directory", err)

    def test_not_a_directory(self):
        self.assertEqual(self.cli(str(self.tmp / "nope"))[0], 1)



class Report(Base):
    """The grouped output: one block per rule family, a hint, up to 5 example paths."""

    def setUp(self):
        super().setUp()
        files = {f"stray{i}.md": "no type" for i in range(7)}
        files["people/P1.md"] = "---\ntype: person\ncontext: x\nbirthday: 1\nrelation: x\n---\n"
        files["people/P2.md"] = "---\ntype: person\ncontext: x\nbirthday: 1\n---\n"
        for i in range(3):   # 6 duplicate-name warnings: more than the 3 errors above
            files[f"reference/Same{i}.md"] = files[f"reference/x/Same{i}.md"] = "---\ntype: hub\n---\n"
        make(self.vault, files)

    def blocks(self, out: str) -> dict[str, list[str]]:
        """family -> the lines of its block (header first)."""
        result, current = {}, None
        for line in out.splitlines():
            if line.startswith("  ") and not line.startswith("   "):
                current = line.split()[1]
                result[current] = [line]
            elif current and line.strip():
                result[current].append(line)
        return result

    def test_groups_by_family_with_breakdown_hint_and_five_examples(self):
        rc, out, _ = self.cli(str(self.vault))
        self.assertEqual(rc, 1)
        b = self.blocks(out)
        missing = b["missing-type"]
        self.assertRegex(missing[0], r"error\s+missing-type\s+7$")
        self.assertIn("move the note to inbox/", missing[1])
        self.assertEqual(sum(l.strip().startswith("stray") for l in missing), 5)
        self.assertIn("... and 2 more (--rule missing-type)", missing[-1])
        unexpected = b["unexpected-property"]
        self.assertRegex(unexpected[0], r"unexpected-property\s+3  birthday 2, relation 1$")
        self.assertIn("people/P1.md  (birthday)", out)
        self.assertRegex(b["duplicate-name"][0], r"duplicate-name\s+6  3 names$")

    def test_errors_first_then_by_count(self):
        _, out, _ = self.cli(str(self.vault))
        self.assertEqual(list(self.blocks(out)), ["missing-type", "unexpected-property", "duplicate-name"])

    def test_rule_lists_every_path_of_a_family_or_a_rule(self):
        _, out, _ = self.cli("--rule", "missing-type", str(self.vault))
        self.assertEqual(list(self.blocks(out)), ["missing-type"])
        self.assertEqual(out.count("stray"), 7)
        self.assertNotIn("more", out)
        _, out, _ = self.cli("--rule", "unexpected-property:relation", str(self.vault))
        self.assertIn("people/P1.md  (relation)", out)
        self.assertNotIn("birthday", out)

    def test_unknown_rule_is_a_usage_error(self):
        self.assertEqual(self.cli("--rule", "nope", str(self.vault))[0], 2)

    def test_all_prints_one_line_per_finding(self):
        _, out, _ = self.cli("--all", str(self.vault))
        lines = out.splitlines()[1:]
        self.assertEqual(len(lines), 7 + 3 + 6)
        self.assertTrue(all(l.split()[0] in ("error", "warning") for l in lines))

    def test_quiet_prints_only_the_summary(self):
        _, out, _ = self.cli("-q", str(self.vault))
        self.assertEqual(len(out.splitlines()), 1)

    def test_every_rule_has_a_hint(self):
        rules = {"missing-type", "unknown-type", "bad-frontmatter", "missing-required", "one-of",
                 "unexpected-property", "invalid-value", "wrong-folder", "name-pattern",
                 "name-date-mismatch", "folder-name", "duplicate-name", "unknown-checkbox",
                 "task-multiple-checkboxes", "task-no-checkbox", "task-checkbox-outside-home"}
        hints = lint.hints(SCHEMA)
        self.assertEqual(set(hints), rules)
        self.assertTrue(all(hints.values()))
        self.assertIn("`option`", hints["unexpected-property"])
        self.assertIn("[>]", hints["unknown-checkbox"])



class Ignore(Base):
    def setUp(self):
        super().setUp()
        make(self.vault, {
            "reference/Hub.md": "---\ntype: hub\n---\n",
            "legacy/Old.md": "no type",
            "legacy/Deep/Older.md": "no type",
            "legacy-2/Kept.md": "no type",
            "areas/a/old/Stale.md": "no type",
            "reference/Twin.md": "---\ntype: hub\n---\n",
            "legacy/Twin.md": "no type",
        })

    def test_findings_under_an_ignored_folder_are_hidden(self):
        rc, out, _ = self.cli("--all", "--ignore", "legacy", "--ignore", "areas/*/old", str(self.vault))
        self.assertIn(": 3 notes (4 hidden), 1 error, 1 warning", out)
        self.assertNotIn("legacy/", out)
        self.assertNotIn("Stale", out)
        self.assertIn("legacy-2/Kept.md", out)      # a folder boundary, not a prefix
        self.assertEqual(rc, 1)

    def test_ignored_notes_still_count_for_duplicates(self):
        _, out, _ = self.cli("--all", "--ignore", "legacy", str(self.vault))
        self.assertIn("duplicate-name", out)
        self.assertIn("reference/Twin.md", out)

    def test_exit_code_only_counts_what_is_shown(self):
        make(self.vault, {"reference/Twin.md": "---\ntype: hub\n---\n", "legacy-2/Kept.md": "---\ntype: hub\n---\n"})
        rc, out, _ = self.cli("--ignore", "legacy", "--ignore", "legacy-2", "--ignore", "areas", str(self.vault))
        self.assertEqual(rc, 0, out)

    def test_accepts_dot_slash_and_trailing_slash(self):
        _, out, err = self.cli("--ignore", "./legacy/", str(self.vault))
        self.assertIn("(3 hidden)", out)
        self.assertEqual(err, "")

    def test_rejects_paths_outside_the_vault(self):
        for bad in ("/legacy", "../x", "a/../../b", "/", "."):
            self.assertEqual(self.cli("--ignore", bad, str(self.vault))[0], 2, bad)

    def test_warns_when_a_pattern_matches_nothing(self):
        rc, _, err = self.cli("--ignore", "legacyy", str(self.vault))
        self.assertIn("--ignore legacyy matches no note", err)
        self.assertEqual(rc, 1)
        _, _, err = self.cli("--under", "nowhere", str(self.vault))
        self.assertIn("--under nowhere matches no note", err)

    def test_under_shows_only_that_folder(self):
        make(self.vault, {"Root.md": "no type"})
        rc, out, _ = self.cli("--all", "--under", "legacy", str(self.vault))
        self.assertIn(": 3 notes (5 hidden), 3 errors, 2 warnings", out)
        self.assertIn("legacy/Deep/Older.md", out)
        self.assertNotIn("legacy-2", out)
        self.assertNotIn("Root.md", out)
        self.assertNotIn("reference/", out)
        self.assertEqual(rc, 1)

    def test_under_several_folders_and_with_ignore(self):
        _, out, _ = self.cli("--all", "--under", "legacy", "--under", "areas", "--ignore", "legacy/Deep",
                             str(self.vault))
        self.assertIn("legacy/Old.md", out)
        self.assertIn("areas/a/old/Stale.md", out)
        self.assertNotIn("Older.md", out)

    def test_under_rejects_paths_outside_the_vault(self):
        self.assertEqual(self.cli("--under", "../x", str(self.vault))[0], 2)



class Quickfix(Base):
    def setUp(self):
        super().setUp()
        make(self.vault, {
            "people/P.md": "---\ntype: person\ncontext: x\nrelation: friend\naliases: Solo\n---\nbody\n",
            "people/Q.md": "---\ncontext: x\ntype: [[Areas]]\n---\n",
            "people/R.md": "---\ncontext: x\ntype:\n---\n",
            "people/S.md": "---\ntype: person\ncontext:\n---\n",
            "people/T.md": "---\ntype: person\ncontext: x\n---\n- [ ] fine\n- [?] odd\n- [?] again\n",
            "people/U.md": "no type",
        })

    def qf(self, *args):
        rc, out, err = self.cli("--quickfix", *args, str(self.vault))
        return rc, out.splitlines(), err

    def test_one_line_per_finding_with_the_offending_line(self):
        rc, lines, err = self.qf()
        v = str(self.vault)
        self.assertEqual(set(lines), {
            f"{v}/people/P.md:4: error unexpected-property:relation",
            f"{v}/people/P.md:5: error invalid-value:aliases",
            f"{v}/people/Q.md:3: error unknown-type",
            f"{v}/people/R.md:3: error missing-type",
            f"{v}/people/S.md:3: error missing-required:context",
            f"{v}/people/T.md:6: warning unknown-checkbox",
            f"{v}/people/U.md:1: error missing-type",
        })
        self.assertEqual(rc, 1)
        self.assertIn("6 errors, 1 warning", err)   # summary on stderr

    def test_respects_rule_and_folder_filters(self):
        _, lines, _ = self.qf("--rule", "missing-type")
        self.assertEqual(len(lines), 2)
        _, lines, _ = self.qf("--ignore", "people")
        self.assertEqual(lines, [])

    def test_paths_follow_the_vault_argument(self):
        r = subprocess.run([sys.executable, str(LINT), "--quickfix", "--rule", "unknown-type", "."],
                           capture_output=True, text=True, cwd=self.vault, env={**os.environ, "HOME": str(self.tmp)})
        self.assertEqual(r.stdout, "./people/Q.md:3: error unknown-type\n")

    def test_values_stay_out(self):
        _, lines, err = self.qf("--verbose")
        self.assertFalse(any("Solo" in l or "Areas" in l for l in lines))
        self.assertIn("Solo", err)            # --verbose details go to stderr only

    def test_excludes_other_output_modes(self):
        self.assertEqual(self.cli("--quickfix", "--all", str(self.vault))[0], 2)
        self.assertEqual(self.cli("--quickfix", "-q", str(self.vault))[0], 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
