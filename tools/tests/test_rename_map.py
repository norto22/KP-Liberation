"""Integration tests for rename_map.py against the live mission tree.

Verifies:
  - 100% coverage of prefixed identifiers found in the tree
  - Collision-free map (internal + vs tree)
  - KPPLM fn names don't clash with the existing KPLIB_fnc_* namespace
  - All 32 STR_GREUH_* stringtable keys are mapped
  - GRLIB_endgame from mission.sqm files is in the map
  - No map target duplicates a different existing tree identifier

Uses the real Missionframework tree so this is an integration test that
catches any drift between the map builder and the actual source files.
"""

# pyright: basic, reportMissingImports=false
import re
from pathlib import Path

import pytest

import rename_map
import sweep

_ROOT = Path(__file__).resolve().parent.parent.parent / "Missionframework"
_MISSIONBASE = _ROOT.parent / "Missionbasefiles"

_SCANNED_EXTS = (".sqf", ".hpp", ".ext", ".xml", ".sqm")

pytestmark = pytest.mark.integration


def _scan_identifiers(root: Path, prefixes: tuple[str, ...]) -> set[str]:
    """Collect all identifiers with the given prefixes from root tree."""
    pat = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(p) for p in prefixes) + r")\w+")
    result: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _SCANNED_EXTS:
            continue
        for m in pat.finditer(path.read_text(errors="replace")):
            result.add(m.group())
    return result


class TestRenameMap:
    @pytest.fixture(scope="class")
    def live_map(self):
        return rename_map.build_identifier_map(_ROOT)

    def test_map_covers_all_source_prefix_identifiers(self, live_map):
        """Every non-excluded identifier with a SOURCE_PREFIX in the tree must be in the map."""
        tree_idents = _scan_identifiers(_ROOT, rename_map.SOURCE_PREFIXES)
        tree_idents -= rename_map.IDENTIFIER_EXCLUSIONS
        missing = tree_idents - set(live_map)
        assert not missing, f"Identifiers found in tree but missing from map: {sorted(missing)}"

    def test_grlib_endgame_renamed_in_sqm(self):
        """After Pass C, GRLIB_endgame must be renamed to KPLIB_endgame in all mission.sqm files."""
        for sqm in _MISSIONBASE.rglob("mission.sqm"):
            text = sqm.read_text(errors="replace")
            assert "GRLIB_endgame" not in text, (
                f"GRLIB_endgame not renamed in {sqm.relative_to(_MISSIONBASE.parent)}"
            )
            assert "KPLIB_endgame" in text, (
                f"KPLIB_endgame not found in {sqm.relative_to(_MISSIONBASE.parent)}"
            )

    def test_str_greuh_keys_renamed_in_stringtable(self):
        """After Pass C, all 32 STR_GREUH_* keys must be STR_KPLIB_GREUH_* in stringtable."""
        stringtable = _ROOT / "stringtable.xml"
        text = stringtable.read_text(errors="replace")
        assert "STR_GREUH_" not in text, "STR_GREUH_* keys not fully renamed in stringtable.xml"
        kplib_greuh_count = text.count("STR_KPLIB_GREUH_")
        assert kplib_greuh_count >= 32, (
            f"Expected ≥32 STR_KPLIB_GREUH_ occurrences, got {kplib_greuh_count}"
        )

    def test_greuh_version_renamed_in_tree(self):
        """After Pass C, GREUH_version (a global set in GREUH_version.sqf) must be KPLIB_greuh_version."""
        import re as _re

        pat = _re.compile(r"\bKPLIB_greuh_version\b")
        found = any(
            pat.search(p.read_text(errors="replace")) for p in _ROOT.rglob("*.sqf") if p.is_file()
        )
        assert found, (
            "KPLIB_greuh_version not found in tree — GREUH_version rename may not have applied"
        )

    def test_map_is_collision_free(self, live_map):
        issues = sweep.check_map_collision_free(live_map)
        assert not issues, "Map has collisions:\n" + "\n".join(issues)

    def test_no_tree_collisions(self, live_map):
        issues = sweep.check_tree_collisions(live_map, _ROOT)
        assert not issues, "Map targets conflict with tree:\n" + "\n".join(issues)

    def test_kpplm_fn_names_dont_clash_with_kplib_fnc(self):
        """The 10 KPPLM_fnc_ function names must not already exist under KPLIB_fnc_."""
        kpplm_pat = re.compile(r"\bKPPLM_fnc_(\w+)\b")
        kplib_pat = re.compile(r"\bKPLIB_fnc_(\w+)\b")
        kpplm_fns: set[str] = set()
        kplib_fns: set[str] = set()
        functions_root = _ROOT / "FUNCTIONS"
        assert functions_root.exists(), f"Expected FUNCTIONS/ dir at {functions_root}"
        for path in _ROOT.rglob("*"):
            if path.is_file() and path.suffix.lower() in (".sqf", ".hpp", ".ext"):
                text = path.read_text(errors="replace")
                for m in kpplm_pat.finditer(text):
                    kpplm_fns.add(m.group(1))
                # Only collect KPLIB_fnc_ from FUNCTIONS/ (the existing module)
                if path.is_relative_to(functions_root):
                    for m in kplib_pat.finditer(text):
                        kplib_fns.add(m.group(1))
        clash = kpplm_fns & kplib_fns
        assert not clash, f"KPPLM fn names already in KPLIB_fnc_ namespace: {sorted(clash)}"

    def test_loadout_manager_fns_merged_into_kplib(self):
        """After Pass B, LOADOUT_MANAGER/FNC has 10 fn_ files, all KPPLM_ tokens gone."""
        fnc_dir = _ROOT / "KP" / "LOADOUT_MANAGER" / "FNC"
        fn_files = list(fnc_dir.glob("fn_*.sqf")) if fnc_dir.exists() else []
        assert len(fn_files) == 10, (
            f"Expected 10 fn_ files in LOADOUT_MANAGER/FNC, got {len(fn_files)}: "
            f"{sorted(f.name for f in fn_files)}"
        )
        # No KPPLM_ tokens should remain in the tree.
        import re as _re

        kpplm_pat = _re.compile(r"\bKPPLM_")
        for path in _ROOT.rglob("*"):
            if path.is_file() and path.suffix.lower() in (".sqf", ".hpp", ".ext", ".xml"):
                text = path.read_text(errors="replace")
                assert not kpplm_pat.search(text), (
                    f"KPPLM_ token still present in {path.relative_to(_ROOT)}"
                )

    def test_mission_string_keys_covered(self, live_map):
        """Every mission-owned setVariable/getVariable key must be in the identifier map."""
        set_re = re.compile(r'(?<![A-Za-z])setVariable\s*\[\s*"([^"]+)"')
        get_re = re.compile(r'(?<![A-Za-z])getVariable\s*(?:\[\s*)?"([^"]+)"')
        mission_prefixes = rename_map.SOURCE_PREFIXES
        uncovered: set[str] = set()
        for path in _ROOT.rglob("*.sqf"):
            text = path.read_text(errors="replace")
            for m in (*set_re.finditer(text), *get_re.finditer(text)):
                key = m.group(1)
                if key.startswith(mission_prefixes) and key not in live_map:
                    uncovered.add(key)
        assert not uncovered, f"Mission string keys not in map: {sorted(uncovered)}"
