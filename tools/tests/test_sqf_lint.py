"""Unit tests for the baseline-gated SQF linter (sqf_lint.py).

Single test class per the parsimony rule. The real `sqflint` binary is never
invoked here — the subprocess hook is monkeypatched so the test is hermetic.
"""
# pytest fixtures (tmp_path, monkeypatch, capsys) are untyped; relax this module.
# Sibling modules are importable via conftest's sys.path injection (not visible to static analysis).
# pyright: basic, reportMissingImports=false
import sqf_lint
from sqf_lint import Finding


class TestSqfLint:
    # ---- parsing -------------------------------------------------------
    def test_parse_file_output_strips_position(self):
        out = '[2,15]:error:Parenthesis "[" not closed\n'
        findings = sqf_lint.parse_file_output(out, "functions/fn_x.sqf")
        assert findings == [
            Finding("functions/fn_x.sqf", "error", 'Parenthesis "[" not closed')
        ]

    def test_parse_file_output_ignores_blank_and_noise_lines(self):
        out = "\n[10,4]:warning:Variable \"_y\" not used\n   \nnot a finding line\n"
        findings = sqf_lint.parse_file_output(out, "a.sqf")
        assert findings == [Finding("a.sqf", "warning", 'Variable "_y" not used')]

    def test_parse_tolerates_leading_tab(self):
        out = '\t[1,1]:error:boom'
        assert sqf_lint.parse_file_output(out, "a.sqf") == [
            Finding("a.sqf", "error", "boom")
        ]

    # ---- baseline round-trip ------------------------------------------
    def test_baseline_roundtrip(self, tmp_path):
        findings = {
            Finding("b.sqf", "warning", "msg b"),
            Finding("a.sqf", "error", "msg a"),
        }
        path = tmp_path / "baseline.txt"
        path.write_text(sqf_lint.format_baseline(findings))
        assert sqf_lint.load_baseline(path) == findings

    def test_format_baseline_is_sorted_and_tab_separated(self):
        findings = {
            Finding("b.sqf", "error", "second"),
            Finding("a.sqf", "warning", "first"),
        }
        text = sqf_lint.format_baseline(findings)
        lines = text.splitlines()
        assert lines == [
            "a.sqf\twarning\tfirst",
            "b.sqf\terror\tsecond",
        ]

    # ---- diff ----------------------------------------------------------
    def test_diff_detects_new_and_resolved(self):
        a = Finding("a.sqf", "error", "a")
        b = Finding("b.sqf", "warning", "b")
        c = Finding("c.sqf", "error", "c")
        new, resolved = sqf_lint.diff({b, c}, {a, b})
        assert new == [c]
        assert resolved == [a]

    # ---- end-to-end main (subprocess hook mocked) ----------------------
    def _make_tree(self, tmp_path, files):
        root = tmp_path / "Missionframework"
        for name in files:
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("// sqf\n")
        return root

    def test_main_passes_when_all_findings_baselined(self, tmp_path, monkeypatch):
        root = self._make_tree(tmp_path, ["functions/fn_a.sqf"])
        baseline = tmp_path / "baseline.txt"
        baseline.write_text(
            sqf_lint.format_baseline({Finding("functions/fn_a.sqf", "warning", "legacy")})
        )
        monkeypatch.setattr(
            sqf_lint, "_run_sqflint", lambda path: "[3,1]:warning:legacy"
        )
        rc = sqf_lint.main(["--root", str(root), "--baseline", str(baseline)])
        assert rc == 0

    def test_main_fails_on_new_finding_and_names_file(self, tmp_path, monkeypatch, capsys):
        root = self._make_tree(tmp_path, ["functions/fn_a.sqf"])
        baseline = tmp_path / "baseline.txt"
        baseline.write_text("")  # empty baseline → finding is new
        monkeypatch.setattr(
            sqf_lint, "_run_sqflint", lambda path: '[2,15]:error:Parenthesis "[" not closed'
        )
        rc = sqf_lint.main(["--root", str(root), "--baseline", str(baseline)])
        assert rc == 1
        assert "functions/fn_a.sqf" in capsys.readouterr().out

    def test_main_per_file_isolation(self, tmp_path, monkeypatch, capsys):
        # Same message exists in a.sqf (baselined) and b.sqf (new). Only b fails.
        root = self._make_tree(tmp_path, ["a.sqf", "b.sqf"])
        baseline = tmp_path / "baseline.txt"
        baseline.write_text(sqf_lint.format_baseline({Finding("a.sqf", "error", "dup")}))

        def fake_run(_path):
            return "[1,1]:error:dup"  # both files emit the identical finding

        monkeypatch.setattr(sqf_lint, "_run_sqflint", fake_run)
        rc = sqf_lint.main(["--root", str(root), "--baseline", str(baseline)])
        out = capsys.readouterr().out
        assert rc == 1
        assert "b.sqf" in out
        assert "a.sqf" not in out  # the baselined occurrence is not reported

    def test_main_skips_oversized_file_and_reports_it(self, tmp_path, monkeypatch, capsys):
        # Oversized data files must be skipped (sqflint hangs on them) AND named
        # in the output — never silently dropped.
        root = self._make_tree(tmp_path, ["small.sqf"])
        (root / "big.sqf").write_text("x" * (sqf_lint.MAX_FILE_BYTES + 1))
        baseline = tmp_path / "baseline.txt"
        baseline.write_text("")
        seen = []

        def fake_run(path):
            seen.append(path.name)
            return "[1,1]:error:boom"

        monkeypatch.setattr(sqf_lint, "_run_sqflint", fake_run)
        rc = sqf_lint.main(["--root", str(root), "--baseline", str(baseline)])
        out = capsys.readouterr().out
        assert "big.sqf" not in seen   # never handed to sqflint
        assert "big.sqf" in out        # but reported as skipped
        assert rc == 1                 # small.sqf's finding is new

    def test_main_update_baseline_writes_current(self, tmp_path, monkeypatch):
        root = self._make_tree(tmp_path, ["a.sqf"])
        baseline = tmp_path / "baseline.txt"
        monkeypatch.setattr(sqf_lint, "_run_sqflint", lambda path: "[1,1]:warning:w")
        rc = sqf_lint.main(
            ["--root", str(root), "--baseline", str(baseline), "--update-baseline"]
        )
        assert rc == 0
        assert sqf_lint.load_baseline(baseline) == {Finding("a.sqf", "warning", "w")}
