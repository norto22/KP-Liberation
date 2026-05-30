"""Unit tests for the namespace-key inventory (namespace_keys.py).

Single test class per the parsimony rule.
"""
# Sibling modules are importable via conftest's sys.path injection (not visible to static analysis).
# pyright: basic, reportMissingImports=false
import namespace_keys


def _tree(tmp_path, files):
    root = tmp_path / "Missionframework"
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


class TestNamespaceKeys:
    def test_classify_mission_vs_third_party(self):
        assert namespace_keys.classify("KPLIB_captured") == "mission"
        assert namespace_keys.classify("KP_liberation_storage_type") == "mission"
        assert namespace_keys.classify("GRLIB_all_fobs") == "mission"
        assert namespace_keys.classify("ace_medical_isMedicalVehicle") == "third_party"
        assert namespace_keys.classify("BIS_fnc_initModules") == "third_party"

    def test_writers_and_readers_recorded(self, tmp_path):
        root = _tree(tmp_path, {
            "a.sqf": 'x setVariable ["KPLIB_k", 1, true];',
            "b.sqf": '_v = x getVariable "KPLIB_k";',
        })
        inv = namespace_keys.build_inventory(root)
        assert inv["KPLIB_k"]["owner"] == "mission"
        assert inv["KPLIB_k"]["writers"] == ["a.sqf"]
        assert inv["KPLIB_k"]["readers"] == ["b.sqf"]

    def test_getvariable_both_forms(self, tmp_path):
        root = _tree(tmp_path, {
            "a.sqf": '_v = x getVariable "K1"; _w = x getVariable ["K2", 0];',
        })
        inv = namespace_keys.build_inventory(root)
        assert "K1" in inv and "K2" in inv

    def test_lookbehind_avoids_substring_match(self, tmp_path):
        root = _tree(tmp_path, {
            # 'mysetVariable' must NOT be read as setVariable.
            "a.sqf": 'mysetVariable ["GHOST", 1]; x setVariable ["REAL", 1];',
        })
        inv = namespace_keys.build_inventory(root)
        assert "REAL" in inv
        assert "GHOST" not in inv

    def test_reader_without_writer_is_visible(self, tmp_path):
        # The signal the sweep uses to catch a missed rename: a key read but
        # never written (or vice-versa).
        root = _tree(tmp_path, {"a.sqf": '_v = x getVariable "KPLIB_orphanKey";'})
        inv = namespace_keys.build_inventory(root)
        assert inv["KPLIB_orphanKey"]["writers"] == []
        assert inv["KPLIB_orphanKey"]["readers"] == ["a.sqf"]
