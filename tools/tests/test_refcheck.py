"""Unit tests for the reference-integrity checker (refcheck.py).

Single test class per the parsimony rule. Fixtures build a minimal mission
tree in tmp_path so resolution is exercised against real files, not mocks.
"""

# pytest fixtures (tmp_path) are untyped; relax this module.
# Sibling modules are importable via conftest's sys.path injection (not visible to static analysis).
# pyright: basic, reportMissingImports=false
import refcheck


def _mission(tmp_path, files):
    """Create a Missionframework-style tree; ``files`` maps relpath -> content."""
    root = tmp_path / "Missionframework"
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


class TestRefcheck:
    # ---- resolve_mission_path -----------------------------------------
    def test_resolve_backslash_exact(self, tmp_path):
        root = _mission(tmp_path, {"functions/fn_x.sqf": ""})
        res = refcheck.resolve_mission_path(root, "functions\\fn_x.sqf")
        assert res.exists and res.exact
        assert res.real == "functions/fn_x.sqf"

    def test_resolve_case_mismatch(self, tmp_path):
        # On-disk GREUH/Scripts; referenced GREUH\scripts (lowercase).
        root = _mission(tmp_path, {"GREUH/Scripts/a.sqf": ""})
        res = refcheck.resolve_mission_path(root, "GREUH\\scripts\\a.sqf")
        assert res.exists  # found case-insensitively
        assert not res.exact  # but the literal case is wrong
        assert res.real == "GREUH/Scripts/a.sqf"

    def test_resolve_missing(self, tmp_path):
        root = _mission(tmp_path, {"functions/fn_x.sqf": ""})
        res = refcheck.resolve_mission_path(root, "no\\such\\file.sqf")
        assert not res.exists
        assert res.real is None

    # ---- CfgFunctions three-level resolution --------------------------
    _DESC = 'class CfgFunctions {\n    #include "CfgFunctions.hpp"\n};\n'
    _CFG = (
        "class KPLIB {\n"
        "    class functions {\n"
        '        file = "functions";\n'
        "        class doThing {};\n"
        '        class viaFsm { ext = ".fsm"; };\n'
        "    };\n"
        "    class functions_curator {\n"
        '        file = "functions\\curator";\n'
        "        class initStuff {};\n"
        "    };\n"
        "};\n"
    )

    def _cfg_mission(self, tmp_path, extra=None):
        files = {
            "description.ext": self._DESC,
            "CfgFunctions.hpp": self._CFG,
            "functions/fn_doThing.sqf": "",
            "functions/fn_viaFsm.fsm": "",
            "functions/curator/fn_initStuff.sqf": "",
        }
        if extra is not None:
            files.update(extra)
        return _mission(tmp_path, files)

    def test_cfgfunctions_all_resolve_clean(self, tmp_path):
        root = self._cfg_mission(tmp_path)
        findings = refcheck.check_cfgfunctions(root)
        assert [f for f in findings if f.severity == "error"] == []

    def test_cfgfunctions_ignores_tag_class_in_path(self, tmp_path):
        # The expected path must be functions/fn_doThing.sqf — NOT
        # KPLIB/functions/fn_doThing.sqf (tag class is not a directory).
        root = self._cfg_mission(tmp_path)
        entries = dict(refcheck.cfgfunctions_entries(root))
        assert entries["doThing"] == "functions/fn_doThing.sqf"
        assert entries["initStuff"] == "functions/curator/fn_initStuff.sqf"

    def test_cfgfunctions_fsm_ext_resolves(self, tmp_path):
        root = self._cfg_mission(tmp_path)
        entries = dict(refcheck.cfgfunctions_entries(root))
        assert entries["viaFsm"] == "functions/fn_viaFsm.fsm"

    def test_cfgfunctions_function_level_file_override(self, tmp_path):
        # A function class can carry its own file=, in full-path form or dir form.
        desc = 'class CfgFunctions {\n    #include "CfgFunctions.hpp"\n};\n'
        cfg = (
            "class KPLIB {\n"
            "    class g {\n"
            '        file = "functions";\n'
            '        class fullPath { file = "scripts\\a\\my.sqf"; };\n'
            '        class dirForm { file = "scripts\\b"; };\n'
            "    };\n"
            "};\n"
        )
        root = _mission(
            tmp_path,
            {
                "description.ext": desc,
                "CfgFunctions.hpp": cfg,
                "scripts/a/my.sqf": "",
                "scripts/b/fn_dirForm.sqf": "",
            },
        )
        entries = dict(refcheck.cfgfunctions_entries(root))
        assert entries["fullPath"] == "scripts/a/my.sqf"  # full-path override
        assert entries["dirForm"] == "scripts/b/fn_dirForm.sqf"  # dir-style override

    def test_cfgfunctions_missing_file_is_error(self, tmp_path):
        # Drop the doThing implementation file -> one error referencing it.
        root = self._cfg_mission(tmp_path)
        (root / "functions/fn_doThing.sqf").unlink()
        errors = [f for f in refcheck.check_cfgfunctions(root) if f.severity == "error"]
        assert len(errors) == 1
        assert "fn_doThing.sqf" in errors[0].ref

    # ---- Task 3: path-reference scanning ------------------------------
    def test_scan_reference_missing_is_error(self, tmp_path):
        root = self._cfg_mission(
            tmp_path,
            extra={
                "init.sqf": r'execVM "scripts\nope\missing.sqf";',
            },
        )
        errors = [f for f in refcheck.scan_references(root) if f.severity == "error"]
        assert any("missing.sqf" in f.ref for f in errors)

    def test_scan_reference_case_mismatch_is_warning(self, tmp_path):
        # On-disk GREUH/Scripts/a.sqf; referenced lowercase via preprocessFile.
        root = self._cfg_mission(
            tmp_path,
            extra={
                "GREUH/Scripts/a.sqf": "",
                "init.sqf": r'_x = preprocessFileLineNumbers "GREUH\scripts\a.sqf";',
            },
        )
        scan = refcheck.scan_references(root)
        assert [f for f in scan if f.severity == "error"] == []
        assert any(f.severity == "warning" and "a.sqf" in f.ref for f in scan)

    def test_scan_reference_existing_include_is_clean(self, tmp_path):
        root = self._cfg_mission(
            tmp_path,
            extra={
                "ui/dialog.hpp": "",
                "description.ext": self._DESC + '#include "ui\\dialog.hpp"\n',
            },
        )
        scan = refcheck.scan_references(root)
        assert [f for f in scan if f.severity == "error"] == []

    def test_scan_ignores_references_inside_comments(self, tmp_path):
        # Commented / example execVM paths (e.g. in a usage docblock) are not refs.
        root = self._cfg_mission(
            tmp_path,
            extra={
                "a.sqf": '// execVM "scripts\\line_nope.sqf";\n'
                '/* preprocessFile "scripts\\block_nope.sqf"; */',
            },
        )
        assert [f for f in refcheck.scan_references(root) if f.severity == "error"] == []

    def test_scan_still_flags_real_ref_beside_a_comment(self, tmp_path):
        root = self._cfg_mission(
            tmp_path,
            extra={
                "a.sqf": '// a leading comment\nexecVM "scripts\\gone.sqf";',
            },
        )
        errs = [f.ref for f in refcheck.scan_references(root) if f.severity == "error"]
        assert any("gone.sqf" in r for r in errs)

    # ---- Task 3: orphan detection -------------------------------------
    def test_orphan_unregistered_fn_is_flagged(self, tmp_path):
        root = self._cfg_mission(tmp_path, extra={"functions/fn_ghost.sqf": ""})
        orphans = [f.ref for f in refcheck.find_orphans(root)]
        assert any("fn_ghost.sqf" in r for r in orphans)

    def test_orphan_registered_fn_not_flagged(self, tmp_path):
        root = self._cfg_mission(tmp_path)
        orphans = [f.ref for f in refcheck.find_orphans(root)]
        assert not any("fn_doThing.sqf" in r for r in orphans)

    def test_orphan_only_checks_fn_files(self, tmp_path):
        # Loose (non-fn_) scripts are out of scope — they load via dynamic paths,
        # so even an unreferenced one must not be flagged.
        root = self._cfg_mission(
            tmp_path,
            extra={
                "scripts/loose_unreferenced.sqf": "",
                "initPlayerLocal.sqf": "",
            },
        )
        assert refcheck.find_orphans(root) == []

    # ---- CI gating: red on ANY issue ----------------------------------
    def test_main_fails_on_broken_reference(self, tmp_path):
        root = self._cfg_mission(tmp_path, extra={"init.sqf": r'execVM "scripts\gone.sqf";'})
        assert refcheck.main(["--root", str(root)]) == 1

    def test_main_fails_on_case_mismatch_warning(self, tmp_path):
        # Even a warning makes CI red — "red on any issue".
        root = self._cfg_mission(
            tmp_path,
            extra={
                "GREUH/Scripts/a.sqf": "",
                "init.sqf": r'execVM "GREUH\scripts\a.sqf";',
            },
        )
        assert refcheck.main(["--root", str(root)]) == 1

    def test_main_passes_on_clean_tree(self, tmp_path):
        assert refcheck.main(["--root", str(self._cfg_mission(tmp_path))]) == 0
