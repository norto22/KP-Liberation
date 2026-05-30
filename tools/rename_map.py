"""Rename table for the KP Liberation directory/naming cleanup sweep.

Provides the explicit identifier map, collision overrides, and module rename
tables consumed by sweep.py. The full identifier map is built lazily from the
live tree so it always reflects what's actually present.

Structure:
  COLLISION_OVERRIDES   — 2 GREUH_ vars that would otherwise merge incorrectly
  SOURCE_PREFIXES       — prefixes to unify → KPLIB_
  MODULE_DIR_RENAMES    — directory renames under KP/
  MODULE_PREFIX_RENAMES — namespace prefix substitutions (longest-first)
  MODULE_FILE_RENAMES   — file renames within the KPGUI/KPPLM modules
  STRINGTABLE_PREFIX_RENAMES — stringtable key prefix substitutions
  build_identifier_map(root) — scan tree → {old: new} flat map
"""

from __future__ import annotations

import re
from pathlib import Path

# ---- Collision overrides ----------------------------------------------------
# GREUH_version and KP_liberation_version are DIFFERENT variables sharing the
# suffix "version". Same for _config. Override their targets so they don't merge.
COLLISION_OVERRIDES: dict[str, str] = {
    "GREUH_version": "KPLIB_greuh_version",
    "GREUH_config": "KPLIB_greuh_config",
}

# ---- Source prefixes to unify → KPLIB_ -------------------------------------
# Order: longest first so case-insensitive prefix stripping always matches the
# longest applicable prefix (KP_liberation_ before GREUH_ etc.).
SOURCE_PREFIXES: tuple[str, ...] = (
    "KP_liberation_",
    "kp_liberation_",
    "GREUH_",
    "GRLIB_",
)

# ---- Module directory renames (under KP/) -----------------------------------
MODULE_DIR_RENAMES: dict[str, str] = {
    "KPGUI": "GUI",
    "KPPLM": "LOADOUT_MANAGER",
}

# ---- Module namespace prefix substitutions (longest-first) ------------------
# Applied by apply_prefix_renames in --modules mode.
MODULE_PREFIX_RENAMES: list[tuple[str, str]] = [
    ("KPPLM_fnc_", "KPLIB_fnc_"),  # longest first: function names keep _fnc_ connector
    ("STR_KPPLM_", "STR_KPLIB_"),  # stringtable keys for KPPLM module
    ("KPPLM_", "KPLIB_"),  # remaining KPPLM_ vars (CBA, KPR, dialog, etc.)
    ("KPGUI_", "KPLIB_GUI_"),
]

# ---- File renames within the KPGUI / KPPLM modules -------------------------
# Used as an identifier-style flat map for path literals (filenames in includes).
MODULE_FILE_RENAMES: dict[str, str] = {
    "KPGUI_defines.hpp": "defines.hpp",
    "KPGUI_classes.hpp": "classes.hpp",
    "KPPLM_functions.hpp": "functions.hpp",
    "KPPLM_dialog.hpp": "dialog.hpp",
    "fucking_set_fog.sqf": "set_fog.sqf",
}

# ---- Stringtable key prefix renames -----------------------------------------
# STR_GREUH_* localization keys → STR_KPLIB_GREUH_* (preserving GREUH grouping).
STRINGTABLE_PREFIX_RENAMES: list[tuple[str, str]] = [
    ("STR_GREUH_", "STR_KPLIB_GREUH_"),
]

# ---- Identifier exclusions --------------------------------------------------
# Identifiers that appear in the tree ONLY as filenames inside path literals,
# not as SQF variable/function names. Renaming them would require renaming the
# file on disk too, which is out of scope (GREUH/ module is kept as-is).
IDENTIFIER_EXCLUSIONS: frozenset[str] = frozenset(
    {
        # GREUH module script filenames — appear in path literals referencing
        # GREUH/SCRIPTS/*.sqf files that are intentionally kept as-is (GREUH/ module
        # is out of scope per the plan). These stems also appeared as variables in the
        # GREUH scripts; those were renamed by Pass C. Only the filename references remain.
        "GREUH_dialog",
        "GREUH_activate",
        "GREUH_actionmanager",
        "GREUH_playermarkers",
        "GREUH_platoonoverlay",
        "GREUH_cache_units",
        "GREUH_squadmanagement",
        "GREUH_view_distance_management",
        "GREUH_dynamic_view_distance",
        "GREUH_interface",
        "GREUH_version",
        "GREUH_config",
        # Mission config filename — hardcoded by the build pipeline; not renamed.
        "kp_liberation_config",
    }
)

# ---- Identifier map builder --------------------------------------------------

_SCANNED_EXTS = (".sqf", ".hpp", ".ext", ".xml", ".sqm", ".fsm")

_SOURCE_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(p) for p in SOURCE_PREFIXES) + r")\w+"
)


def _ident_target(old: str) -> str:
    """Compute the KPLIB_ target for a prefixed identifier."""
    if old in COLLISION_OVERRIDES:
        return COLLISION_OVERRIDES[old]
    for pfx in SOURCE_PREFIXES:
        if old.startswith(pfx):
            return "KPLIB_" + old[len(pfx) :]
    # Unreachable if called only on identifiers matched by _SOURCE_RE.
    return old


def build_identifier_map(root: Path) -> dict[str, str]:
    """Scan all mission files under root; return {old_ident: new_ident} map.

    Includes the stringtable prefix renames as explicit entries so the map is
    self-contained. SQF synonyms (same identifier, different case) correctly
    produce the same KPLIB_ target — sweep.check_map_collision_free treats
    those as legitimate merges, not collisions.
    """
    identifiers: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _SCANNED_EXTS:
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for m in _SOURCE_RE.finditer(text):
            identifiers.add(m.group())

    # Also scan Missionbasefiles sibling (mission.sqm contains GRLIB_endgame).
    missionbase = root.parent / "Missionbasefiles"
    if missionbase.exists():
        for path in missionbase.rglob("mission.sqm"):
            try:
                text = path.read_text(errors="replace")
            except OSError:
                continue
            for m in _SOURCE_RE.finditer(text):
                identifiers.add(m.group())

    flat: dict[str, str] = {
        ident: _ident_target(ident)
        for ident in sorted(identifiers)
        if ident not in IDENTIFIER_EXCLUSIONS
    }

    # Bake in stringtable prefix renames (STR_GREUH_* → STR_KPLIB_GREUH_*).
    # These are collected separately because STR_ is not in SOURCE_PREFIXES.
    str_re = re.compile(r"(?<![A-Za-z0-9_])STR_GREUH_\w+")
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _SCANNED_EXTS:
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for m in str_re.finditer(text):
            key = m.group()
            flat[key] = "STR_KPLIB_GREUH_" + key[len("STR_GREUH_") :]

    return flat
