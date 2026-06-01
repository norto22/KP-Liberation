"""Unit tests for sweep.py — the KP Liberation rename-sweep engine.

Single test class per parsimony rule. Fixtures use tmp_path for tree checks.
"""

# Sibling modules importable via conftest sys.path injection.
# pyright: basic, reportMissingImports=false
import sweep


def _tree(tmp_path, files: dict[str, str]):
    """Create a minimal mission tree; files maps relpath -> content."""
    root = tmp_path / "Missionframework"
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


class TestRecase:
    def test_dir_segments_uppercased_filename_preserved(self):
        result = sweep.recase_path("scripts\\server\\game\\set_fog.sqf")
        assert result == "SCRIPTS\\SERVER\\GAME\\set_fog.sqf"

    def test_no_extension_all_segments_uppercased(self):
        assert sweep.recase_path("a\\b") == "A\\B"

    def test_single_segment_no_extension(self):
        assert sweep.recase_path("scripts") == "SCRIPTS"

    def test_single_filename_preserved(self):
        # A lone filename segment with extension stays unchanged.
        assert sweep.recase_path("init.sqf") == "init.sqf"

    def test_save_key_value_untouched(self):
        # No backslashes → treated as single dir-like segment → already uppercase
        val = "KP_LIBERATION_ALTIS_SAVEGAME"
        assert sweep.recase_path(val) == val

    def test_mixed_case_dirs_uppercased(self):
        assert sweep.recase_path("Scripts\\Server\\fn_x.sqf") == "SCRIPTS\\SERVER\\fn_x.sqf"

    def test_single_dir_with_child_file(self):
        assert sweep.recase_path("res\\image.paa") == "RES\\image.paa"


class TestApplyIdentifiers:
    def test_whole_token_renamed(self):
        result = sweep.apply_identifiers(
            "x = GRLIB_all_fobs;",
            {"GRLIB_all_fobs": "KPLIB_all_fobs"},
        )
        assert result == "x = KPLIB_all_fobs;"

    def test_no_partial_match_prefix(self):
        # Preceded by a letter — not a word boundary.
        result = sweep.apply_identifiers(
            "myGRLIB_all_fobsX = 1;",
            {"GRLIB_all_fobs": "KPLIB_all_fobs"},
        )
        assert result == "myGRLIB_all_fobsX = 1;"

    def test_no_partial_match_suffix(self):
        # Followed by a letter — not a word boundary.
        result = sweep.apply_identifiers(
            "GRLIB_all_fobsXYZ = 1;",
            {"GRLIB_all_fobs": "KPLIB_all_fobs"},
        )
        assert result == "GRLIB_all_fobsXYZ = 1;"

    def test_multiple_occurrences(self):
        result = sweep.apply_identifiers(
            "a = GRLIB_x; b = GRLIB_x;",
            {"GRLIB_x": "KPLIB_x"},
        )
        assert result == "a = KPLIB_x; b = KPLIB_x;"

    def test_longest_first_prevents_prefix_shadowing(self):
        # GRLIB_x_extended must match before GRLIB_x to avoid partial replacement.
        result = sweep.apply_identifiers(
            "a = GRLIB_x_extended; b = GRLIB_x;",
            {"GRLIB_x": "KPLIB_x", "GRLIB_x_extended": "KPLIB_x_extended"},
        )
        assert result == "a = KPLIB_x_extended; b = KPLIB_x;"

    def test_preceded_by_quote_is_boundary(self):
        # Inside a string literal: setVariable ["GRLIB_x", val] — quote precedes.
        result = sweep.apply_identifiers(
            'obj setVariable ["GRLIB_x", val];',
            {"GRLIB_x": "KPLIB_x"},
        )
        assert result == 'obj setVariable ["KPLIB_x", val];'


class TestRecasePaths:
    def test_execvm_literal_recased(self):
        text = 'execVM "scripts\\server\\game\\set_fog.sqf";'
        result = sweep.recase_paths_in_text(text)
        assert result == 'execVM "SCRIPTS\\SERVER\\GAME\\set_fog.sqf";'

    def test_preprocessfile_literal_recased(self):
        text = 'call (preprocessFile "scripts\\client\\init.sqf");'
        result = sweep.recase_paths_in_text(text)
        assert result == 'call (preprocessFile "SCRIPTS\\CLIENT\\init.sqf");'

    def test_include_literal_recased(self):
        text = '#include "scripts\\client\\ui.hpp"'
        result = sweep.recase_paths_in_text(text)
        assert result == '#include "SCRIPTS\\CLIENT\\ui.hpp"'

    def test_cfg_file_attr_recased(self):
        # CfgFunctions file= points to a directory (no extension) → all segments uppercase.
        text = 'file = "functions\\curator";'
        result = sweep.recase_paths_in_text(text)
        assert result == 'file = "FUNCTIONS\\CURATOR";'

    def test_non_path_text_unchanged(self):
        text = "GRLIB_save_key = 1;"
        assert sweep.recase_paths_in_text(text) == text


class TestCheckMap:
    def test_clean_map_exit_0(self):
        m = {"GRLIB_x": "KPLIB_x", "GREUH_y": "KPLIB_y"}
        assert sweep.check_map_collision_free(m) == []

    def test_collision_detected(self):
        # Two distinct sources both map to KPLIB_x → collision.
        m = {"GRLIB_x": "KPLIB_x", "GREUH_x": "KPLIB_x"}
        issues = sweep.check_map_collision_free(m)
        assert len(issues) == 1
        assert "KPLIB_x" in issues[0]

    def test_identical_src_tgt_not_collision(self):
        # Only a collision when TWO DISTINCT sources share a target.
        m = {"KPLIB_x": "KPLIB_x"}
        assert sweep.check_map_collision_free(m) == []

    def test_sqf_synonym_not_collision(self):
        # KP_liberation_x and kp_liberation_x are the same SQF variable → not a collision.
        m = {"KP_liberation_x": "KPLIB_x", "kp_liberation_x": "KPLIB_x"}
        assert sweep.check_map_collision_free(m) == []


class TestCheckTree:
    def test_no_collision_with_tree(self, tmp_path):
        root = _tree(tmp_path, {"scripts\\fn_x.sqf": "KPLIB_other = 1;"})
        m = {"GRLIB_x": "KPLIB_x"}
        assert sweep.check_tree_collisions(m, root) == []

    def test_collision_when_target_exists_independently(self, tmp_path):
        # KPLIB_fnc_save already in tree (not a source); renaming KPPLM_fnc_save → same target.
        root = _tree(
            tmp_path,
            {
                "scripts\\fn_x.sqf": "KPLIB_fnc_save = 1;",
            },
        )
        m = {"KPPLM_fnc_save": "KPLIB_fnc_save"}
        issues = sweep.check_tree_collisions(m, root)
        assert len(issues) == 1
        assert "KPLIB_fnc_save" in issues[0]

    def test_no_collision_when_source_maps_to_itself(self, tmp_path):
        # A KPLIB_ already in the tree but it's the source being renamed too — not a collision.
        root = _tree(tmp_path, {"scripts\\fn_x.sqf": "KPLIB_x = 1;"})
        m = {"KPLIB_x": "KPLIB_x_new"}
        assert sweep.check_tree_collisions(m, root) == []
