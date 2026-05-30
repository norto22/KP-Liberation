# Phase 0 — Refactor Guardrails Implementation Plan

Created: 2026-05-30
Agent: Claude Code
Status: VERIFIED
Approved: Yes
Iterations: 1
Worktree: No
Type: Feature

## Summary

**Goal:** Add automated guardrails — baseline-gated SQF syntax linting, a Python reference-integrity checker, and a modernized CI workflow — so the upcoming codebase tidy-up (especially the full `KPLIB_` namespace sweep) can be verified mechanically, with CI turning red only on *newly introduced* breakage, not pre-existing legacy quirks.

## Out of Scope

- **Any gameplay/SQF logic change.** Phase 0 adds tooling and CI only. The one apparent latent bug found (the `GREUH\scripts` vs `GREUH/Scripts` case mismatch) is *reported* by the checker as a warning, **not fixed** here — fixing it belongs to a later cleanup phase.
- **The npm-audit advisories** (51) in the `_tools/` gulp toolchain — separate concern, risks breaking the build.
- **Renaming anything** — the namespace-key inventory only *records* keys for the later sweep; it changes no code.

## Approach

**Chosen:** A new repo-root `tools/` Python package (distinct from the existing Node `_tools/` build dir) holding three CLI checks — `sqf_lint.py`, `refcheck.py`, `namespace_keys.py` — wired into a modernized `.github/workflows/main.yml` as a separate `checks` job alongside the existing build.
**Why:** Python is already present (3.12) and the `sqflint` analyzer is a Python package, so the checks run in-environment with no Arma engine needed; a baseline snapshot for the linter means "warn on legacy, fail on new" falls out naturally without fragile error-message classification. Cost: a second tooling language in the repo, mitigated by a README disambiguating `tools/` (Python checks) from `_tools/` (Node build).

### Autonomous Decisions

- **Location/naming:** `tools/` at repo root for the Python checks, deliberately parallel to the existing `_tools/` (leading-underscore = Node build). A `tools/README.md` states the distinction so the similar names don't confuse maintainers.
- **sqflint gating via baseline diff** (not message classification): `sqflint`'s structural errors and its stale-command false-positives (`findIf` etc.) share message text ("can't interpret statement"), so they can't be cleanly separated by string. A committed baseline of current findings, with CI failing only on findings *absent from the baseline*, is robust and maps exactly to the chosen "warn on legacy / fail on real breakage" policy.
- **Checker root = `Missionframework/`** — that's where `description.ext` and all referenced `.sqf/.hpp` live; runtime mission paths (`"scripts\server\..."`) resolve relative to it.
- **Output:** every check prints a human report; `refcheck` and `namespace_keys` also emit `--json` for the later sweep to consume.

## Context for Implementer

The checker must implement real **BIS `CfgFunctions` resolution**, not naive file globbing. The verified structure — do **not** assume a flat include list:
- The authoritative root is `Missionframework/description.ext`. Its `class CfgFunctions { ... }` block has **two direct `#include`s, which are siblings**: `CfgFunctions.hpp` and `KP\KPPLM\KPPLM_functions.hpp`.
- `CfgFunctions.hpp` is itself a **tag-class definition**, not a flat list: `class KPLIB { class functions { file = "functions"; class addActionsFob {}; ... }; class functions_curator { file = "functions\curator"; ... }; class functions_ui { file = "functions\ui"; ... }; #include "scripts\client\CfgFunctions.hpp"; #include "scripts\server\CfgFunctions.hpp"; }`. The nested client/server includes define more group classes inside the same `KPLIB` tag.
- **Three-level resolution rule.** BIS nests exactly: **tag class** (`class KPLIB`) → **group class** (`class functions { file = "..."; }`) → **function class** (`class addActionsFob {}`). Only the *group* class's `file=` contributes the directory; the **tag-class name is ignored** for path resolution. Resolve as `group.file + "/fn_" + functionClass.name + (ext or ".sqf")`. Track nesting depth so `file=` is read only from group-level classes — never emit `KPLIB/functions/fn_addActionsFob.sqf` (correct is `functions/fn_addActionsFob.sqf`).
- Overrides on a function class: `ext = ".fsm"` → `fn_Name.fsm` (e.g. `class highcommand {ext=".fsm";}`, `class sectorMonitor {ext=".fsm";}`); or its own `file = "..."` for a full-path override.
- Paths use **backslashes** and the engine is **case-insensitive**; on a case-sensitive Linux checkout the literal case can mismatch the real file (confirmed: `GREUH\scripts\...` referenced, `GREUH/Scripts/` on disk). Resolution must be case-insensitive, with a **case mismatch reported as a warning**.

Reference-pattern volumes to scan (string literals in `*.sqf/*.hpp/*.ext`): `execVM` (89), `preprocessFile`/`preprocessFileLineNumbers` (~197), `#include`. `call compile`/`remoteExec` reference *function names*, not file paths — out of scope for path resolution.

## Assumptions

- The current shipping codebase has **zero hard-broken references** (every `execVM`/`preprocess`/`#include`/CfgFunctions target exists at least case-insensitively). Tasks 2–3 verify this when first run; if a genuine hard-break surfaces, it is recorded in the refcheck baseline/JSON and surfaced to the user rather than silently fixed — Tasks 2,3,5 depend on this so the `checks` job is green on day one.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Existing code contains a hard-broken reference, so the gating `refcheck` fails CI on first run | Low | Med | Task 3 runs `refcheck` against the live tree as its DoD; any hard error is reported to the user and added to a baseline allowlist (mirroring the sqflint baseline) so day-one CI is green and the issue is tracked, not buried |
| `upload-artifact@v4` behavioral change vs `@master` breaks the build job | Low | Low | Single upload of one path — within v4's supported usage; Task 5 validates the YAML and the build job locally via `npx gulp` |

## Goal Verification

### Truths

1. Running the full check suite (`sqf_lint.py` + `refcheck.py`) against the **current** `Missionframework/` exits 0, while the report still lists the known legacy issues (the `GREUH` case mismatch, the `findIf` sqflint false-positives) as **non-failing warnings** — proving "warn on legacy" works end to end.
2. Introducing a regression — a new unbalanced bracket in any `.sqf`, **or** a reference/CfgFunctions target that no longer resolves — makes the suite exit non-zero and name the offending file — proving the guardrail actually guards the upcoming sweep.

## Progress Tracking

- [x] Task 1: SQF lint runner with baseline gating (`tools/sqf_lint.py`)
- [x] Task 2: Reference-integrity checker — CfgFunctions resolution (`tools/refcheck.py`)
- [x] Task 3: refcheck — path-reference + orphan scanning, live-tree verification
- [x] Task 4: Namespace-key inventory (`tools/namespace_keys.py`)
- [x] Task 5: Modernize `main.yml` + wire the checks job

## Implementation Tasks

### Task 1: SQF lint runner with baseline gating

**Objective:** Create the `tools/` Python package and a `sqf_lint.py` CLI that runs `sqflint` across `Missionframework/**/*.sqf`, normalizes findings, and gates on a committed baseline — exiting non-zero only when a finding is not already in the baseline. This is the structural-syntax guardrail; it makes "warn on legacy, fail on new" concrete. Verified by Truth 1 and Truth 2.

**Files:**

- Create: `tools/sqf_lint.py`
- Create: `tools/requirements.txt` (pin `sqflint==0.3.2`)
- Create: `tools/sqf_lint_baseline.txt` (generated from the current tree)
- Create: `tools/README.md` (purpose; `tools/` Python checks vs `_tools/` Node build)
- Create: `tools/tests/test_sqf_lint.py`

**Key Decisions / Notes:**

- Invoke `sqflint <file>` per `.sqf` (or `sqflint -d <dir>`); parse output lines of form `[line,col]:severity:message`. Normalize each finding to a **position-insensitive key** `(<relpath>, <severity>, <message-without-[line,col]>)` so edits that shift line numbers don't churn the baseline.
- CLI: default mode = run, diff normalized findings against `tools/sqf_lint_baseline.txt`, print NEW findings, exit 1 if any new; also print resolved (baseline-but-now-absent) findings as info; `--update-baseline` rewrites the baseline file (sorted, stable order).
- **Baseline file format:** one entry per line, **tab-separated** `<relpath>\t<severity>\t<message>` (relpath relative to `Missionframework/`). `--update-baseline` writes lines sorted by that 3-tuple; the runner loads them into a `set` of 3-tuples. Keeping `relpath` in the key keeps the same message in two different files distinct — a new occurrence in file B is not masked by a baselined occurrence in file A.
- Resolve the analyzer via `shutil.which("sqflint")` (the pip console-script — empirically on PATH after `pip install sqflint`); if it returns `None`, fall back to `[sys.executable, "-m", "sqflint"]`. Mock the subprocess call in the unit test regardless of invocation form (per testing rule — no reliance on the real binary in unit runs).
- Generate the initial baseline by running the tool with `--update-baseline` against the live tree once, then commit the result.

**Definition of Done:**

- [ ] `python tools/sqf_lint.py` against the current tree exits 0 (all current findings are baselined).
- [ ] Writing a `.sqf` with a new unbalanced `[` and re-running exits 1 and prints that file's path.
- [ ] After `pip install -r tools/requirements.txt`, the runner resolves `sqflint` (via `shutil.which` or the `-m` fallback) — no crash from a missing entrypoint.
- [ ] The same error introduced in a *second* file while the first file's occurrence stays baselined → exit 1 naming only the second file (per-file key isolation).
- [ ] `python tools/sqf_lint.py --update-baseline` regenerates a stable, sorted baseline.
- [ ] Verify: `uv run --no-project --with pytest pytest tools/tests/test_sqf_lint.py -q`

### Task 2: Reference-integrity checker — CfgFunctions resolution

**Objective:** Create `tools/refcheck.py` that parses `Missionframework/description.ext`, follows its `class CfgFunctions` includes (including `KPPLM_functions.hpp` and the nested client/server `CfgFunctions.hpp`), and resolves every function `class` to its on-disk file using BIS semantics (`fn_<Name>.sqf` default, `ext=".fsm"` and class-level `file=` overrides, backslash paths, case-insensitive). A missing target is a gating ERROR; a case-only mismatch is a WARNING. Includes the shared `resolve_mission_path()` helper reused by Task 3.

**Files:**

- Create: `tools/refcheck.py`
- Create: `tools/tests/test_refcheck.py`

**Key Decisions / Notes:**

- `resolve_mission_path(root, raw)`: backslash→`/`, strip leading `/`, join under `root`; return (exists_exact, exists_caseinsensitive, real_path). Drives both ERROR (no case-insensitive match) and WARNING (case-only mismatch) classification. See `## Context for Implementer` for the exact CfgFunctions rules.
- Parse `#include "..."` recursively starting at `description.ext`'s `class CfgFunctions` block to gather all group files; a lightweight brace/`class`/`file=`/`ext=` scanner is sufficient — do **not** pull in a full C-preprocessor.
- **Track class-nesting depth:** tag (depth 1, e.g. `KPLIB`) → group (depth 2, carries `file=`) → function (depth 3). Read `file=` only from depth-2 group classes; ignore the depth-1 tag name for paths (see the three-level rule in `## Context for Implementer`). The sibling `KPPLM_functions.hpp` follows the same shape (`class KPPLM { class main { file = "KP\KPPLM\fnc"; class apply {}; ... } }`).
- CLI skeleton here: `--json <path>` and human report; exit 1 on any ERROR, warnings never fail. Task 3 adds the path-reference + orphan passes to the same CLI.

**Definition of Done:**

- [ ] Every `class` reachable from `description.ext`'s CfgFunctions resolves to an existing file; run prints a summary count and exits 0 on the current tree.
- [ ] A fixture CfgFunctions entry pointing at a non-existent `fn_X.sqf` produces an ERROR and exit 1; an `ext=".fsm"` entry resolves to the `.fsm` file.
- [ ] Verify: `uv run --no-project --with pytest pytest tools/tests/test_refcheck.py -q`

### Task 3: refcheck — path-reference + orphan scanning, live-tree verification

**Objective:** Extend `tools/refcheck.py` to (a) scan all `*.sqf/*.hpp/*.ext` for `execVM`/`preprocessFile`/`preprocessFileLineNumbers`/`#include` string-literal paths and resolve them (ERROR if unresolvable even case-insensitively, WARNING on case mismatch — this surfaces the `GREUH\scripts` issue), and (b) flag orphan files: `fn_*.sqf` not registered in any CfgFunctions, and `scripts/**/*.sqf` referenced by no path literal (WARNING). Then run it against the live tree to confirm the Assumption holds.

**Files:**

- Modify: `tools/refcheck.py`
- Modify: `tools/tests/test_refcheck.py`

**Key Decisions / Notes:**

- Reuse `resolve_mission_path()` from Task 2. Regex the load patterns: `(execVM|preprocessFileLineNumbers|preprocessFile)\s+"([^"]+)"` and `#include\s+"([^"]+)"`.
- **Orphan logic (deliberately conservative to keep the warning signal trustworthy):** the high-signal case is a **`fn_*`-prefixed file absent from the CfgFunctions registry** (a dead/unregistered function) — always flag these. For non-`fn_` loose `scripts/**/*.sqf`, flag only when referenced by *no* path literal AND *not* on the engine-conventional allowlist below.
- **Engine-conventional allowlist** (Arma auto-executes these, or they are `#include`d by `description.ext` outside the CfgFunctions block — never orphans): `init.sqf`, `initServer.sqf`, `initPlayerLocal.sqf`, `initPlayerServer.sqf`, `onPlayerRespawn.sqf`, `onPlayerKilled.sqf`, `briefing.sqf`, `XEH_preInit.sqf`, `XEH_postInit.sqf`, `init_*.sqf`, **plus every file reachable by `#include` from `description.ext` outside the CfgFunctions block** (the `ui\*.hpp`, `GREUH\UI\*.hpp`, `scripts\client\tutorial\*.hpp`, etc.). Build this set by parsing `description.ext`'s non-CfgFunctions `#include`s, don't hard-code only the filenames.
- After implementing, run `python tools/refcheck.py` on the real tree; confirm 0 ERRORs (Assumption). If a hard ERROR appears, add it to a `tools/refcheck_baseline.json` allowlist and report it to the user — do not edit gameplay code.

**Definition of Done:**

- [ ] On the current tree, `refcheck` reports the `GREUH\scripts` case mismatch as a WARNING and exits 0 (0 ERRORs).
- [ ] A fixture `.sqf` with `execVM "scripts\does\not_exist.sqf"` yields an ERROR and exit 1.
- [ ] `python tools/refcheck.py --json out.json` writes findings (errors+warnings+orphans) as JSON.
- [ ] Verify: `uv run --no-project --with pytest pytest tools/tests/test_refcheck.py -q`

### Task 4: Namespace-key inventory

**Objective:** Create `tools/namespace_keys.py` that scans every `setVariable`/`getVariable` string-literal key across `Missionframework/**/*.sqf`, classifies each as mission-owned (`GREUH_`/`GRLIB_`/`KP_liberation_`/`KPLIB_`/`kp_liberation_`) vs third-party/engine (`ace_`, `BIS_`, …), and emits a JSON inventory pairing writers (setVariable) with readers (getVariable). This is the artifact the later prefix sweep verifies against; it is informational and never gates CI.

**Files:**

- Create: `tools/namespace_keys.py`
- Create: `tools/tests/test_namespace_keys.py`

**Key Decisions / Notes:**

- Regex `(?<![A-Za-z])setVariable\s*\[\s*"([^"]+)"` and `(?<![A-Za-z])getVariable\s*(?:\[\s*)?"([^"]+)"` — the negative lookbehind prevents matching `getVariable`/`setVariable` as a substring of a larger identifier (the inventory is the sweep's foundation, so phantom entries must be avoided). `getVariable` has both binary (`obj getVariable "k"`) and array (`obj getVariable ["k", default]`) forms; the optional `[` handles both. For each key record the set of writer files and reader files.
- Classification by prefix allow/deny lists; anything not matching a mission prefix is tagged `third_party` so the sweep never renames `ace_*`/`BIS_*`/`Addons` etc.
- Output JSON shape: `{ "<key>": {"owner": "mission|third_party", "writers": [...], "readers": [...]} }`. CLI `--json <path>` (default stdout).

**Definition of Done:**

- [ ] Run against the current tree lists the known keys (`KP_liberation_storage_type`, `KPLIB_captured`, …) as `mission` and `ace_medical_isMedicalVehicle`/`BIS_fnc_*` as `third_party`.
- [ ] A reader with no matching writer (and vice-versa) is observable in the JSON (empty writers/readers list) — the signal the sweep uses to catch a missed rename.
- [ ] Verify: `uv run --no-project --with pytest pytest tools/tests/test_namespace_keys.py -q`

### Task 5: Modernize `main.yml` + wire the checks job

**Objective:** Update `.github/workflows/main.yml` to bump the build to node 22 via `actions/setup-node@v4` (replacing `docker://node:10-alpine`), pin `actions/checkout@v4` and `actions/upload-artifact@v4`, and add a parallel `checks` job (Python 3.12) that installs `tools/requirements.txt` and runs the three checks — `sqf_lint.py` and `refcheck.py` gating, `namespace_keys.py` producing a non-gating JSON artifact.

**Files:**

- Modify: `.github/workflows/main.yml`

**Key Decisions / Notes:**

- Keep the existing `build` job's logic (working-directory `_tools`, `npm install`, `npx gulp`, artifact upload) — only swap the runner setup and pin the action versions.
- New `checks` job: `actions/checkout@v4` → `actions/setup-python@v5` (3.12) → `pip install -r tools/requirements.txt` → `python tools/sqf_lint.py` → `python tools/refcheck.py` → `python tools/namespace_keys.py --json tools/namespace_keys.json` (last one `continue-on-error` is unnecessary since it always exits 0).
- Cannot execute GitHub Actions locally; verify by (a) parsing the YAML and (b) running each job's commands locally.

**Definition of Done:**

- [ ] `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/main.yml'))"` succeeds (valid YAML).
- [ ] No `@master` action pins or `node:10-alpine` remain: `! rg -q '@master|node:10' .github/workflows/main.yml`.
- [ ] The build job's commands still work locally: `cd _tools && npm install && npx gulp` exits 0 — confirming the build is unaffected by the action/node-version changes.
- [ ] The checks job's commands run locally and exit as designed: `python tools/sqf_lint.py; python tools/refcheck.py; python tools/namespace_keys.py --json /tmp/nk.json` (first two exit 0 on current tree).

## Implementation Notes (deviations & findings)

- **Performance fix (Task 1):** `sqflint` is superlinear and times out (>120s) on the large equipment-data files. `sqf_lint.py` now skips files >40 KB or past a 30 s per-file timeout, **reporting** each skip (no silent caps), and parallelizes across cores. Full-tree baseline gen ≈ 44 s; 11 data files skipped; 338 findings baselined.
- **Orphan scope narrowed (Task 3):** loose-script orphan detection was **dropped** in favour of `fn_*`-not-registered only. Against the live tree the loose-script pass produced 36 mostly-false orphans (FOB templates and `do_*`/`open_*` action scripts load via constructed paths / UI handlers that can't be traced statically) — exactly the noise the spec-review flagged. This matches spec-review must_fix #3's recommended inversion.
- **Follow-up after the fail-on-any gating change — what the red CI surfaced and how it was resolved:**
  - The two flagged "broken refs" (`kp_fuel_consumption.sqf:17`, `export_template.sqf:9`) were **false positives** — `execVM` paths inside docblock *comments* (usage examples), not real code. `refcheck` now strips `//` and `/* */` comments before scanning, so they're no longer flagged. (Earlier notes calling them real bugs were wrong.)
  - The 9 `GREUH` case mismatches were **real** (case-sensitive Linux): the directory `GREUH/Scripts` was renamed to `GREUH/scripts` to match every reference (all already lowercase), also moving toward the lowercase-directory convention. The `sqf_lint` baseline relpaths were updated accordingly.
  - With both addressed, `refcheck` is **green** on the current tree.
- **refcheck gating (changed post-verification, per user request):** the initial baseline (gate on *new* errors only) was replaced with **fail on any finding** (error or warning) so CI goes red on every reference problem; `refcheck_baseline.json` was removed. `sqf_lint` keeps its baseline — its 338 findings include sqflint's own false positives on modern commands (`findIf` …), which can't all be "fixed", so it gates on *new* findings only.
