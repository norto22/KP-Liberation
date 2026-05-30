#!/usr/bin/env python3
"""Namespace-key inventory for the KP Liberation rename sweep.

Scans every ``setVariable``/``getVariable`` string-literal key, classifies it as
mission-owned vs third-party/engine, and pairs writers with readers.

The later `KPLIB_` unification sweep verifies its renames against this
inventory: string keys are matched by *value*, so renaming a `setVariable
"KPLIB_x"` writer without its `getVariable "KPLIB_x"` readers fails **silently**
at runtime (the read just returns nil). A mission key that ends up with writers
but no readers — or vice-versa — is the signal that a rename was half-applied.

Informational only — never gates CI.
"""
# argparse Namespaces are dynamically typed and add_argument() returns an unused Action.
# pyright: reportAny=false, reportUnusedCallResult=false
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ROOT = _REPO_ROOT / "Missionframework"

MISSION_PREFIXES = ("GREUH_", "GRLIB_", "KP_liberation_", "KPLIB_", "kp_liberation_")

# Negative lookbehind so 'setVariable'/'getVariable' inside a larger identifier
# (e.g. a hypothetical 'mysetVariable') is not captured. getVariable has both a
# binary form (obj getVariable "k") and an array form (obj getVariable ["k", d]).
_SET_RE = re.compile(r'(?<![A-Za-z])setVariable\s*\[\s*"([^"]+)"')
_GET_RE = re.compile(r'(?<![A-Za-z])getVariable\s*(?:\[\s*)?"([^"]+)"')


def classify(key: str) -> str:
    """'mission' if the key carries a mission prefix, else 'third_party'."""
    return "mission" if key.startswith(MISSION_PREFIXES) else "third_party"


def build_inventory(root: Path) -> dict[str, dict[str, str | list[str]]]:
    """Map every namespace key to its owner and the files that write/read it."""
    writers: dict[str, set[str]] = {}
    readers: dict[str, set[str]] = {}
    for path in sorted(root.rglob("*.sqf")):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(errors="replace")
        for m in _SET_RE.finditer(text):
            writers.setdefault(m.group(1), set()).add(rel)
        for m in _GET_RE.finditer(text):
            readers.setdefault(m.group(1), set()).add(rel)
    return {
        key: {
            "owner": classify(key),
            "writers": sorted(writers.get(key, set())),
            "readers": sorted(readers.get(key, set())),
        }
        for key in sorted(set(writers) | set(readers))
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KP Liberation namespace-key inventory.")
    parser.add_argument("--root", type=Path, default=_DEFAULT_ROOT,
                        help="Mission framework root (default: Missionframework/).")
    parser.add_argument("--json", type=Path, default=None,
                        help="Write the inventory JSON here (default: also print to stdout).")
    args = parser.parse_args(argv)

    inventory = build_inventory(args.root)
    text = json.dumps(inventory, indent=2)
    if args.json is not None:
        Path(args.json).write_text(text + "\n")
    mission = sum(1 for v in inventory.values() if v["owner"] == "mission")
    print(f"{len(inventory)} key(s): {mission} mission, {len(inventory) - mission} third-party.")
    if args.json is None:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
