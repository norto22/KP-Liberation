#!/usr/bin/env python3
"""Baseline-gated SQF syntax linter.

Runs the ``sqflint`` static analyzer over every ``*.sqf`` file under the
mission framework and compares the findings against a committed baseline.
CI fails only on findings that are **not** already in the baseline, so the
many false-positives sqflint emits on modern SQF commands (``findIf`` etc.)
and other pre-existing legacy quirks never turn the build red — only newly
introduced problems do.

Usage:
    python tools/sqf_lint.py                  # gate against the baseline
    python tools/sqf_lint.py --update-baseline  # snapshot current findings

See tools/README.md for how this differs from the Node build in _tools/.
"""

# argparse Namespaces are dynamically typed and add_argument() returns an unused
# Action; these strict-only lints fire only on that CLI plumbing. ("standard"
# type-checking mode omits them too — see tools/pyproject.toml.)
# pyright: reportAny=false, reportUnusedCallResult=false
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    relpath: str
    severity: str
    message: str


# A sqflint result line, e.g.  [22,11]:warning:Local variable "_x" ...
_LINE_RE = re.compile(r"^\s*\[\d+,\d+\]:(\w+):(.*)$")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ROOT = _REPO_ROOT / "Missionframework"
_DEFAULT_BASELINE = Path(__file__).resolve().parent / "sqf_lint_baseline.txt"

# sqflint's parser is superlinear: it times out (>120s) on the big equipment
# *data* files (e.g. arsenal_presets/unsung.sqf, 167 KB). Those are classname
# arrays, not logic, so we skip files above this size and cap each invocation
# with a timeout. Skips are reported, never silent.
MAX_FILE_BYTES = 40_000
SQFLINT_TIMEOUT_S = 30


def parse_file_output(output: str, relpath: str) -> list[Finding]:
    """Parse sqflint stdout for a single file into position-insensitive findings."""
    findings: list[Finding] = []
    for raw in output.splitlines():
        m = _LINE_RE.match(raw.rstrip())
        if m:
            findings.append(Finding(relpath, m.group(1), m.group(2)))
    return findings


def _run_sqflint(path: Path) -> str | None:
    """Invoke sqflint on one file, returning its combined stdout/stderr.

    Prefers the pip console-script; falls back to ``python -m sqflint`` when the
    entrypoint isn't on PATH. Returns ``None`` if sqflint exceeds the timeout
    (a pathologically slow file) so the caller can skip it instead of hanging.
    """
    exe = shutil.which("sqflint")
    cmd = [exe, str(path)] if exe else [sys.executable, "-m", "sqflint", str(path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=SQFLINT_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None
    return proc.stdout + proc.stderr


def collect_findings(
    root: Path, run: Callable[[Path], str | None] | None = None
) -> tuple[set[Finding], list[str]]:
    """Run the analyzer over every *.sqf under ``root``.

    Returns ``(findings, skipped)`` where ``skipped`` lists files not linted
    because they exceed ``MAX_FILE_BYTES`` or timed out. Each file is a separate
    ``sqflint`` subprocess; the pool is sized to the core count (sqflint's parse
    is CPU-bound). Per-file (not ``-d``) is required because ``sqflint -d``
    reports bare basenames, which collide across directories.
    """
    if run is None:
        run = _run_sqflint
    paths = sorted(root.rglob("*.sqf"))

    def analyze(path: Path) -> tuple[str, bool, list[Finding]]:
        rel = path.relative_to(root).as_posix()
        if path.stat().st_size > MAX_FILE_BYTES:
            return (rel, True, [])
        out = run(path)
        if out is None:  # sqflint timed out on this file
            return (rel, True, [])
        return (rel, False, parse_file_output(out, rel))

    workers = max(1, os.cpu_count() or 4)
    findings: set[Finding] = set()
    skipped: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for rel, was_skipped, file_findings in pool.map(analyze, paths):
            if was_skipped:
                skipped.append(rel)
            findings.update(file_findings)
    return findings, sorted(skipped)


def format_baseline(findings: Iterable[Finding]) -> str:
    """Serialize findings as sorted, tab-separated ``relpath\\tseverity\\tmessage`` lines."""
    lines = sorted(f"{f.relpath}\t{f.severity}\t{f.message}" for f in findings)
    return "\n".join(lines) + ("\n" if lines else "")


def load_baseline(path: Path) -> set[Finding]:
    """Load a baseline file into a set of Findings (empty set if absent)."""
    path = Path(path)
    if not path.exists():
        return set()
    out: set[Finding] = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        relpath, severity, message = line.split("\t", 2)
        out.add(Finding(relpath, severity, message))
    return out


def diff(current: set[Finding], baseline: set[Finding]) -> tuple[list[Finding], list[Finding]]:
    """Return (new, resolved): findings added vs the baseline and findings gone from it."""
    new = sorted(current - baseline)
    resolved = sorted(baseline - current)
    return new, resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Baseline-gated SQF syntax linter.")
    parser.add_argument(
        "--root",
        type=Path,
        default=_DEFAULT_ROOT,
        help="Mission framework root to scan (default: Missionframework/).",
    )
    parser.add_argument(
        "--baseline", type=Path, default=_DEFAULT_BASELINE, help="Baseline file path."
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline from the current findings and exit 0.",
    )
    args = parser.parse_args(argv)

    current, skipped = collect_findings(args.root)
    if skipped:
        print(
            f"note: {len(skipped)} file(s) not linted (exceed {MAX_FILE_BYTES} bytes or timed out):"
        )
        for rel in skipped:
            print(f"  - {rel}")

    if args.update_baseline:
        Path(args.baseline).write_text(format_baseline(current))
        print(f"Baseline updated: {len(current)} finding(s) written to {args.baseline}")
        return 0

    baseline = load_baseline(args.baseline)
    new, resolved = diff(current, baseline)

    if resolved:
        print(
            f"info: {len(resolved)} baselined finding(s) no longer present (consider --update-baseline)."
        )

    if new:
        print(f"FAIL: {len(new)} new SQF finding(s) not in the baseline:")
        for f in new:
            print(f"  {f.relpath}: {f.severity}: {f.message}")
        return 1

    print(f"OK: {len(current)} finding(s), all baselined.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
