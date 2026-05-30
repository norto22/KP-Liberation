#!/usr/bin/env python3
"""KP Liberation rename-sweep engine.

Applies directory/naming cleanup transformations in reproducible, bisectable
passes. Each mode transforms text in-place across the mission tree.

Usage:
  python tools/sweep.py --recase-paths   [--root DIR]
  python tools/sweep.py --modules        [--root DIR]
  python tools/sweep.py --identifiers    [--root DIR]
  python tools/sweep.py --check-map      [--root DIR]
  python tools/sweep.py --check-tree     [--root DIR]
"""

# pyright: reportAny=false, reportUnusedCallResult=false, reportMissingImports=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations

import argparse
import re
from collections.abc import Callable
from pathlib import Path

import rename_map as _rm

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ROOT = _REPO_ROOT / "Missionframework"

_SCANNED_EXTS = (".sqf", ".hpp", ".ext")
_ALL_SCANNED = (*_SCANNED_EXTS, ".sqm", ".xml", ".fsm")

# Path-literal patterns; group 1 is always the raw path value.
_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'(?:execVM|preprocessFileLineNumbers|preprocessFile)\s*"([^"]+)"'),
    re.compile(r'#include\s+"([^"]+)"'),
    re.compile(r'\bfile\s*=\s*"([^"]+)"'),
]


# ---- Core transformations ---------------------------------------------------


def recase_path(s: str) -> str:
    """Uppercase every directory segment; preserve the final filename segment's case.

    Splits on backslash (Arma convention). A segment is a "filename" when it
    contains a dot (file extension). All non-filename segments are directories
    and get UPPERCASE'd. Filenames are left exactly as written — their case is
    not forced, because mixed-case filenames (CfgFunctions.hpp, KPLIB_debriefs.hpp)
    must continue to resolve after the sweep.
    """
    parts = s.split("\\")
    if len(parts) == 1:
        # Single segment: dir if no extension → UPPERCASE; filename → preserve as-is.
        return s if "." in s else s.upper()
    dirs = [p.upper() for p in parts[:-1]]
    last = parts[-1] if "." in parts[-1] else parts[-1].upper()
    return "\\".join([*dirs, last])


def apply_identifiers(text: str, rename_map: dict[str, str]) -> str:
    """Word-boundary replace of every identifier in rename_map.

    Processes longest keys first to avoid prefix-shadowing (e.g. GRLIB_x_ext
    matched before GRLIB_x so the longer token wins).
    """
    for old in sorted(rename_map, key=len, reverse=True):
        new = rename_map[old]
        pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(old) + r"(?![A-Za-z0-9_])")
        text = pat.sub(new, text)
    return text


def apply_identifiers_code_only(text: str, rename_map: dict[str, str]) -> str:
    """Like apply_identifiers but preserves filename segments inside path literals.

    Replaces path literal filenames with unique tokens before applying renames,
    then restores them. This prevents renaming e.g. GREUH_config.sqf (a file
    that isn't being renamed) when GREUH_config is also a variable identifier.
    """
    placeholders: list[str] = []

    def _protect(m: re.Match[str]) -> str:
        path = m.group(1)
        parts = path.split("\\")
        if "." in parts[-1]:  # last segment is a filename → protect it
            tok = f"\x00FILE{len(placeholders)}\x00"
            placeholders.append(parts[-1])
            if len(parts) > 1:
                protected = "\\".join(parts[:-1]) + "\\" + tok
            else:
                protected = tok
            s = m.start(0)
            return m.group(0)[: m.start(1) - s] + protected + m.group(0)[m.end(1) - s :]
        return m.group(0)

    protected = text
    for pat in _PATH_PATTERNS:
        protected = pat.sub(_protect, protected)

    renamed = apply_identifiers(protected, rename_map)

    for i, original_filename in enumerate(placeholders):
        renamed = renamed.replace(f"\x00FILE{i}\x00", original_filename)
    return renamed


def apply_prefix_renames(text: str, prefix_pairs: list[tuple[str, str]]) -> str:
    """Prefix-substitution rename; caller must order longest-prefix-first."""
    for old_pfx, new_pfx in prefix_pairs:
        pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(old_pfx) + r"(\w+)")
        text = pat.sub(lambda m, p=new_pfx: p + m.group(1), text)
    return text


def recase_paths_in_text(text: str) -> str:
    """Recase all path literals (execVM/preprocessFile/#include/file=) in text."""

    def _repl(m: re.Match[str]) -> str:
        s = m.start(0)
        return m.group(0)[: m.start(1) - s] + recase_path(m.group(1)) + m.group(0)[m.end(1) - s :]

    for pat in _PATH_PATTERNS:
        text = pat.sub(_repl, text)
    return text


# ---- Validation checks ------------------------------------------------------


def check_map_collision_free(flat_map: dict[str, str]) -> list[str]:
    """Return descriptions of any pair of distinct sources sharing a target.

    SQF synonyms (same identifier, different case) sharing a target are NOT
    flagged — they represent the same variable being unified, which is correct.
    """
    seen: dict[str, str] = {}  # target → first source seen
    issues: list[str] = []
    for src, tgt in sorted(flat_map.items()):
        if tgt in seen and seen[tgt] != src:
            # SQF is case-insensitive; two spellings of the same identifier are synonyms.
            if seen[tgt].lower() != src.lower():
                issues.append(f"{src!r} and {seen[tgt]!r} both → {tgt!r}")
        else:
            seen.setdefault(tgt, src)
    return issues


def _collect_identifiers(root: Path, prefixes: tuple[str, ...]) -> set[str]:
    """Collect all identifiers beginning with any of the given prefixes."""
    if not prefixes:
        return set()
    pat = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(p) for p in prefixes) + r")\w+")
    result: set[str] = set()
    for path in root.rglob("*"):
        if path.suffix.lower() not in _ALL_SCANNED:
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for m in pat.finditer(text):
            result.add(m.group())
    return result


def check_tree_collisions(flat_map: dict[str, str], root: Path) -> list[str]:
    """Return entries where a map target already exists as a non-source tree identifier.

    A collision: src → tgt, tgt already in tree, and tgt is not itself a source
    being renamed away. After the sweep there would be two distinct identifiers
    merged under tgt — only safe for SQF variables, not for function names.
    """
    sources = set(flat_map.keys())
    # Collect all identifiers that share a prefix with any target.
    target_prefixes = tuple({t.split("_")[0] + "_" for t in flat_map.values() if "_" in t})
    tree_idents = _collect_identifiers(root, target_prefixes)
    issues: list[str] = []
    for src, tgt in sorted(flat_map.items()):
        if tgt in tree_idents and tgt not in sources:
            issues.append(
                f"{src!r} → {tgt!r}: target already exists as independent tree identifier"
            )
    return issues


# ---- CLI modes --------------------------------------------------------------


def _walk_files(root: Path, exts: tuple[str, ...]):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in exts:
            yield path


def _apply_to_tree(
    root: Path, transform: Callable[[str], str], exts: tuple[str, ...] = _SCANNED_EXTS
) -> int:
    count = 0
    for path in _walk_files(root, exts):
        old = path.read_text(errors="replace")
        new = transform(old)
        if new != old:
            path.write_text(new)
            count += 1
    return count


def _mode_recase_paths(root: Path) -> int:
    n = _apply_to_tree(root, recase_paths_in_text)
    print(f"Recased path literals in {n} file(s).")
    return 0


def _mode_modules(root: Path) -> int:
    # File renames FIRST so KPGUI_defines.hpp → defines.hpp before
    # prefix renames turn KPGUI_defines.hpp → KPLIB_GUI_defines.hpp.
    def transform(text: str) -> str:
        text = apply_identifiers(text, _rm.MODULE_FILE_RENAMES)
        text = apply_prefix_renames(text, _rm.MODULE_PREFIX_RENAMES)
        return text

    # Include .xml for stringtable.xml (STR_KPPLM_* keys).
    module_exts = (*_SCANNED_EXTS, ".xml")
    n = _apply_to_tree(root, transform, module_exts)
    print(f"Applied module renames to {n} file(s).")
    return 0


def _mode_identifiers(root: Path) -> int:
    ident_map = _rm.build_identifier_map(root)
    # Use code_only variant to avoid renaming filenames inside path literals.
    n = _apply_to_tree(root, lambda t: apply_identifiers_code_only(t, ident_map), _ALL_SCANNED)
    # Also sweep Missionbasefiles (contains GRLIB_endgame in mission.sqm files).
    missionbase = root.parent / "Missionbasefiles"
    if missionbase.exists():
        n += _apply_to_tree(
            missionbase, lambda t: apply_identifiers_code_only(t, ident_map), (".sqm",)
        )
    print(f"Applied identifier renames to {n} file(s).")
    return 0


def _mode_check_map(root: Path) -> int:
    ident_map = _rm.build_identifier_map(root)
    issues = check_map_collision_free(ident_map)
    if issues:
        for issue in issues:
            print(f"COLLISION: {issue}")
        print(f"\n{len(issues)} collision(s) found.")
        return 1
    print(f"Map is collision-free ({len(ident_map)} entries).")
    return 0


def _mode_check_tree(root: Path) -> int:
    ident_map = _rm.build_identifier_map(root)
    issues = check_tree_collisions(ident_map, root)
    if issues:
        for issue in issues:
            print(f"TREE-COLLISION: {issue}")
        print(f"\n{len(issues)} tree collision(s) found.")
        return 1
    print(f"No tree collisions ({len(ident_map)} map entries checked).")
    return 0


# ---- CLI entry point --------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KP Liberation rename-sweep engine.")
    parser.add_argument(
        "--root",
        type=Path,
        default=_DEFAULT_ROOT,
        help="Mission framework root (default: Missionframework/).",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--recase-paths", action="store_true", help="Uppercase directory segments in path literals."
    )
    mode.add_argument("--modules", action="store_true", help="Apply module/file renames (Pass B).")
    mode.add_argument(
        "--identifiers", action="store_true", help="Apply the full identifier rename map (Pass C)."
    )
    mode.add_argument(
        "--check-map", action="store_true", help="Verify the rename map is collision-free."
    )
    mode.add_argument(
        "--check-tree",
        action="store_true",
        help="Verify no map target duplicates a different tree identifier.",
    )
    args = parser.parse_args(argv)

    if args.recase_paths:
        return _mode_recase_paths(args.root)
    if args.modules:
        return _mode_modules(args.root)
    if args.identifiers:
        return _mode_identifiers(args.root)
    if args.check_map:
        return _mode_check_map(args.root)
    return _mode_check_tree(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
