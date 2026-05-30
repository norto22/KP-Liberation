#!/usr/bin/env python3
"""Reference-integrity checker for the KP Liberation mission.

Validates that every file the mission *refers to* actually exists:

* **CfgFunctions** — every registered `class` resolves to its `fn_<name>.sqf`
  (or `.fsm`) file, following BIS three-level tag→group→function semantics.
* **Script loads** (Task 3) — every `execVM`/`preprocessFile`/`#include`
  string-literal path resolves.

Any finding fails the check (exit 1) so CI goes red on every reference
problem: a missing target (ERROR), a case-only mismatch (WARNING — harmless in
a packed PBO but broken on a case-sensitive Linux server), or an unregistered
``fn_`` function (WARNING).

The mission engine is case-insensitive, so resolution is too; paths use
backslashes relative to the mission root (``Missionframework/``).
"""
# argparse Namespaces are dynamically typed and add_argument() returns an unused
# Action; these strict-only lints fire only on that CLI plumbing.
# pyright: reportAny=false, reportUnusedCallResult=false
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple, final

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ROOT = _REPO_ROOT / "Missionframework"


class Finding(NamedTuple):
    severity: str   # "error" | "warning"
    category: str   # "cfgfunctions" | "reference" | "orphan"
    ref: str        # the referenced path / expected file
    source: str     # where the reference lives
    message: str


class Resolution(NamedTuple):
    exists: bool        # found, at least case-insensitively
    exact: bool         # found with the exact case as written
    real: str | None    # actual on-disk relpath (posix), or None if missing


def resolve_mission_path(root: Path, raw: str) -> Resolution:
    """Resolve a backslash mission path under ``root``, case-insensitively."""
    rel = raw.replace("\\", "/").lstrip("/")
    if (root / rel).exists():
        return Resolution(True, True, rel)
    # Walk segment by segment, matching case-insensitively.
    cur = root
    real_parts: list[str] = []
    for part in rel.split("/"):
        match = None
        if cur.is_dir():
            for child in cur.iterdir():
                if child.name.lower() == part.lower():
                    match = child
                    break
        if match is None:
            return Resolution(False, False, None)
        real_parts.append(match.name)
        cur = match
    return Resolution(True, False, "/".join(real_parts))


# ---- CfgFunctions parsing ---------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
      \bclass\s+(?P<cname>\w+)
    | (?P<lbrace>\{)
    | (?P<rbrace>\})
    | \bfile\s*=\s*"(?P<fileval>[^"]*)"
    | \bext\s*=\s*"(?P<extval>[^"]*)"
    | \#include\s+"(?P<inc>[^"]*)"
    """,
    re.VERBOSE,
)


@final
class _Frame:
    __slots__ = ("name", "file", "ext", "has_child")

    def __init__(self, name: str):
        self.name = name
        self.file: str | None = None        # own file= (group dir or override)
        self.ext: str | None = None
        self.has_child = False


def _slice_cfgfunctions_block(text: str) -> str:
    """Return the body of the top-level ``class CfgFunctions { ... }`` block."""
    m = re.search(r"\bclass\s+CfgFunctions\b[^{]*\{", text)
    if not m:
        return ""
    depth = 0
    start = m.end()
    for i in range(m.end() - 1, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
    return text[start:]


def _walk(tokens: Iterator[re.Match[str]], stack: list[_Frame], root: Path,
          entries: list[tuple[str, str]]) -> None:
    pending_name: str | None = None
    for m in tokens:
        if m.group("cname"):
            pending_name = m.group("cname")
        elif m.group("lbrace"):
            parent = stack[-1] if stack else None
            if parent is not None:
                parent.has_child = True
            stack.append(_Frame(pending_name or "?"))
            pending_name = None
        elif m.group("rbrace"):
            if not stack:
                continue
            frame = stack.pop()
            parent = stack[-1] if stack else None
            _emit_if_function(frame, parent, entries)
        elif m.group("fileval") is not None:
            if stack:
                stack[-1].file = m.group("fileval").replace("\\", "/").strip("/")
        elif m.group("extval") is not None:
            if stack:
                stack[-1].ext = m.group("extval")
        elif m.group("inc") is not None:
            inc_path = resolve_mission_path(root, m.group("inc"))
            if inc_path.real is not None:
                inc_text = (root / inc_path.real).read_text(errors="replace")
                _walk(_TOKEN_RE.finditer(inc_text), stack, root, entries)


def _emit_if_function(frame: _Frame, parent: _Frame | None, entries: list[tuple[str, str]]) -> None:
    if frame.has_child:
        return  # a group or tag class, not a function
    ext = frame.ext or ".sqf"
    if frame.file is not None:
        # Function-level full-path override.
        rel = frame.file if frame.file.endswith((".sqf", ".fsm")) else f"{frame.file}/fn_{frame.name}{ext}"
        entries.append((frame.name, rel))
    elif parent is not None and parent.file:
        entries.append((frame.name, f"{parent.file}/fn_{frame.name}{ext}"))


def cfgfunctions_entries(root: Path) -> list[tuple[str, str]]:
    """Return (function_name, expected_relpath) for every registered function."""
    desc = root / "description.ext"
    if not desc.exists():
        return []
    body = _slice_cfgfunctions_block(desc.read_text(errors="replace"))
    entries: list[tuple[str, str]] = []
    _walk(_TOKEN_RE.finditer(body), [_Frame("CfgFunctions")], root, entries)
    return entries


def check_cfgfunctions(root: Path) -> list[Finding]:
    """Resolve every registered function file; ERROR if missing, WARNING on case mismatch."""
    findings: list[Finding] = []
    for name, rel in cfgfunctions_entries(root):
        res = resolve_mission_path(root, rel)
        if not res.exists:
            findings.append(Finding(
                "error", "cfgfunctions", rel, "CfgFunctions",
                f"registered function '{name}' has no file: {rel}",
            ))
        elif not res.exact:
            findings.append(Finding(
                "warning", "cfgfunctions", rel, "CfgFunctions",
                f"function '{name}' case mismatch: referenced {rel}, on disk {res.real}",
            ))
    return findings


# ---- Path-reference scanning ------------------------------------------------

_LOAD_RE = re.compile(r'\b(?:execVM|preprocessFileLineNumbers|preprocessFile)\s+"([^"]+)"')
_INCLUDE_RE = re.compile(r'#include\s+"([^"]+)"')
_SCANNED_EXTS = (".sqf", ".hpp", ".ext")


def _iter_references(root: Path) -> Iterator[tuple[str, str, str]]:
    """Yield (raw_path, source_relpath, category) for every load/include literal."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _SCANNED_EXTS:
            continue
        source = path.relative_to(root).as_posix()
        text = path.read_text(errors="replace")
        for m in _LOAD_RE.finditer(text):
            yield (m.group(1), source, "reference")
        for m in _INCLUDE_RE.finditer(text):
            yield (m.group(1), source, "include")


def _resolve_ref(root: Path, raw: str, source: str, category: str) -> Resolution:
    """Resolve a reference; #include also tries relative to the including file."""
    res = resolve_mission_path(root, raw)
    if res.exists or category != "include":
        return res
    src_dir = Path(source).parent.as_posix()
    if src_dir and src_dir != ".":
        alt = resolve_mission_path(root, f"{src_dir}/{raw}")
        if alt.exists:
            return alt
    return res


def scan_references(root: Path) -> list[Finding]:
    """Resolve every execVM/preprocessFile/#include literal path under ``root``."""
    findings: list[Finding] = []
    for raw, source, category in _iter_references(root):
        if raw.startswith("\\"):
            continue  # absolute engine path (e.g. \a3\...), not a mission file
        res = _resolve_ref(root, raw, source, category)
        if not res.exists:
            findings.append(Finding("error", category, raw, source, f"unresolved path: {raw}"))
        elif not res.exact:
            findings.append(Finding("warning", category, raw, source,
                                    f"case mismatch: {raw} -> {res.real}"))
    return findings


# ---- Orphan detection -------------------------------------------------------

def find_orphans(root: Path) -> list[Finding]:
    """Flag ``fn_*.sqf`` files that are not registered in CfgFunctions (dead functions).

    Only ``fn_``-prefixed files are checked. Loose ``scripts/`` files load through
    too many dynamic mechanisms — constructed paths, UI ``addAction`` handlers,
    FSMs — to flag reliably; doing so produces mostly false positives (verified
    against the live tree), which would erode trust in the warning signal.
    """
    registered = {
        (resolve_mission_path(root, rel).real or rel).lower()
        for _, rel in cfgfunctions_entries(root)
    }
    findings: list[Finding] = []
    for path in sorted(root.rglob("fn_*.sqf")):
        rel = path.relative_to(root).as_posix()
        if rel.lower() not in registered:
            findings.append(Finding("warning", "orphan", rel, rel,
                                    f"function file not registered in CfgFunctions: {rel}"))
    return findings


def run_all(root: Path) -> list[Finding]:
    """All three reference checks combined."""
    return check_cfgfunctions(root) + scan_references(root) + find_orphans(root)


# ---- CLI --------------------------------------------------------------------

def _report(findings: list[Finding]) -> int:
    """Print findings; exit non-zero (CI red) if there is ANY error or warning."""
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    for f in errors:
        print(f"ERROR   [{f.category}] {f.source}: {f.message}")
    for f in warnings:
        print(f"warning [{f.category}] {f.source}: {f.message}")

    by_cat = {c: sum(1 for f in warnings if f.category == c)
              for c in sorted({f.category for f in warnings})}
    wsummary = ", ".join(f"{n} {c}" for c, n in by_cat.items()) or "none"
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) ({wsummary}).")
    return 1 if (errors or warnings) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KP Liberation reference-integrity checker.")
    parser.add_argument("--root", type=Path, default=_DEFAULT_ROOT,
                        help="Mission framework root (default: Missionframework/).")
    parser.add_argument("--json", type=Path, default=None,
                        help="Also write all findings as JSON to this path.")
    args = parser.parse_args(argv)

    findings = run_all(args.root)
    if args.json is not None:
        Path(args.json).write_text(json.dumps([f._asdict() for f in findings], indent=2))
    return _report(findings)


if __name__ == "__main__":
    raise SystemExit(main())
