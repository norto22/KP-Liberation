# Directory & Naming Cleanup Implementation Plan

Created: 2026-05-30
Agent: Claude Code
Status: VERIFIED
Approved: Yes
Iterations: 1
Worktree: No
Type: Feature

## Summary

**Goal:** Complete structural tidy-up of the KP Liberation mission in one pass — recase all directories to UPPERCASE (files stay lowercase), rename the cryptic `KPGUI`/`KPPLM` modules, and unify every global-variable/save-key prefix (`GREUH_`/`GRLIB_`/`KP_liberation_`/`kp_liberation_`/`KPLIB_`) to a single `KPLIB_` namespace — updating every reference so nothing breaks, verified mechanically by the Phase 0 `refcheck` + `sqf_lint` + `namespace_keys` guardrails.

## Out of Scope

- **Gameplay logic.** Names and paths only — no behavioral change. Any diff that alters control flow or values is a bug.
- **Top-level `GREUH/` and `KP/` acronym dirs** — kept as-is per the user's decision (they're project acronyms; only their *sub*-directories recase).
- **Merging the 3 collision variables.** `GREUH_version`/`GREUH_config` stay distinct (→ `KPLIB_greuh_version`/`KPLIB_greuh_config`); they are NOT merged into the KP-side variables of the same suffix.

## Approach

**Chosen:** A tested Python transformation engine (`tools/sweep.py`) driven by an explicit rename map, applied in **four sequenced passes** (directory recasing → module renames → file renames → variable unification), each committed separately and verified by `refcheck` + `sqf_lint` + `namespace_keys` before the next. The engine is path-component-aware (uppercases directory segments, leaves filenames lowercase), identifier-aware (word-boundary replacement, no partial-token hits), and comment/string-aware where it must avoid false hits.
**Why:** A 400-file mechanical change is only safe if it's reproducible and bisectable — hand-editing is error-prone and unverifiable at this scale. Separate verified passes mean a failed in-game smoke test can be traced to exactly one transformation. Cost: building the engine up front, but it's reused across all four passes and the variable sweep cannot be done safely without it.

## Context for Implementer

- **Arma path semantics:** mission paths use backslashes and are case-insensitive *in a packed PBO*, but case-sensitive on a Linux dedicated server running an unpacked mission. After recasing, references must match the new UPPERCASE dirs exactly. `refcheck` (case-insensitive resolve + case-mismatch warning, which now FAILS CI) is the gate.
- **Path transform rule:** uppercase every directory segment, keep the final filename segment lowercase. `"scripts\server\game\set_fog.sqf"` → `"SCRIPTS\SERVER\GAME\set_fog.sqf"`. Applies to `execVM`/`preprocessFile*`/`#include` literals AND `CfgFunctions` `file=` attributes.
- **SQF identifiers are case-insensitive**, so `KP_liberation_arsenal` and `kp_liberation_arsenal` are the *same* variable — unify both to `KPLIB_arsenal`. But `GREUH_version` and `KP_liberation_version` are *different* variables that happen to share a suffix — see Out of Scope.
- **No in-progress saves** (confirmed by the user earlier), so persisted `setVariable`/`getVariable` string keys and the `GRLIB_save_key` value may be renamed too — no backward-compat constraint. `namespace_keys.py` verifies writer/reader pairing survives each string-key rename (a key left with writers-but-no-readers = a half-applied rename).
- **Guardrails are now fail-on-any** for `refcheck`; they must be green after every pass (regenerating the `sqf_lint` baseline as relpaths/messages change).

## Assumptions

- `mission.sqm` files contain **no framework path literals** (verified across all 18 maps), so Pass A (dir recasing) does not touch them — but they **do** contain the identifier `GRLIB_endgame`, so Pass C's identifier sweep must include `Missionbasefiles/*/mission.sqm`. Tasks 2,5 depend on this.
- The build pipeline (`_tools/gulpfile.ts`) copies the whole `Missionframework/` tree and only hardcodes the root filenames `description.ext`, `kp_liberation_config.sqf`, `stringtable.xml` — none of which move — so directory recasing is transparent to the build. Task 5 verifies via `npx gulp`.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Variable unification merges two distinct vars (collision) | Med | High | Engine builds the rename map from an explicit table; the 3 known collisions are pre-resolved to distinct `KPLIB_greuh_*`/`KPLIB_*` names; Task 1 test asserts no two distinct source identifiers map to the same target |
| A reference is missed → broken path or dangling identifier | Med | High | `refcheck` (fail-on-any) catches broken paths; `namespace_keys` catches half-renamed string keys; `sqf_lint` catches resulting syntax errors; each pass gated on all three green |
| `.sqm` init-field `execVM`s reference recased paths (refcheck doesn't scan `.sqm`) | Low | High | Task 2 greps all 18 `mission.sqm` for path literals before the dir pass; any hits are included and re-checked |
| In-game behavior breaks despite green guardrails (semantic, not mechanical) | Med | High | Each pass is a separate commit → bisectable; user smoke-tests in-game per Goal Verification before merge |

## Goal Verification

### Truths

1. After all four passes, `python tools/refcheck.py`, `python tools/sqf_lint.py`, and `python tools/namespace_keys.py` all exit 0 on the recased tree, and a full `grep` for any `GREUH_`/`GRLIB_`/`KP_liberation_`/`kp_liberation_` identifier (outside the 2 preserved `KPLIB_greuh_*` names) returns nothing — proving the unification is complete, not partial.
2. `cd _tools && npm install && npx gulp` still assembles and packs all 18 map PBOs with zero errors after the recasing — proving the build pipeline survives the directory changes.

## Progress Tracking

- [x] Task 1: Build `tools/sweep.py` transformation engine + rename map + tests
- [x] Task 2: Audit reference surface (incl. all `mission.sqm`) + finalize the rename map
- [x] Task 3: Pass A — directory recasing (tree-wide UPPERCASE) + path-ref rewrite
- [x] Task 4: Pass B — module renames (GUI, LOADOUT_MANAGER) + file renames + their namespaces
- [x] Task 5: Pass C — variable prefix unification to `KPLIB_` (incl. save-key strings)
- [x] Task 6: Regenerate guardrail baselines, update tool prefix lists, final full verification

## Implementation Tasks

### Task 1: Build the transformation engine + rename map

**Objective:** Create `tools/sweep.py` — a reproducible, tested rename engine used by all later passes. It performs (a) path-component recasing in path literals (uppercase dir segments, lowercase filename) across `execVM`/`preprocessFile*`/`#include`/`CfgFunctions file=`, and (b) word-boundary identifier replacement from an explicit `{old: new}` map (no partial-token hits, applied to code, `setVariable`/`getVariable` string keys, and the `GRLIB_save_key` value). Includes a `--check-map` mode that asserts the map is collision-free (no two distinct sources → one target).

**Files:**

- Create: `tools/sweep.py`
- Create: `tools/rename_map.py` (the explicit identifier + module + collision table)
- Create: `tools/tests/test_sweep.py`

**Key Decisions / Notes:**

- Reuse `refcheck._strip_comments` semantics conceptually, but for identifier replacement do NOT strip comments — rename in comments too (so docblocks stay accurate), EXCEPT never rewrite inside a path literal's filename segment.
- Path recasing helper: split a backslash path, uppercase all but the last segment if the last has a file extension. Unit-test `"a\b\c.sqf" -> "A\B\c.sqf"` and `"a\b" -> "A\B"`.
- Identifier replace: `re.sub(r'(?<![A-Za-z0-9_])' + re.escape(old) + r'(?![A-Za-z0-9_])', new, text)` per map entry, longest-source-first to avoid prefix shadowing.
- `rename_map.py` seeds the 3 collisions: `GREUH_version→KPLIB_greuh_version`, `GREUH_config→KPLIB_greuh_config`, everything else `{GREUH_,GRLIB_,KP_liberation_,kp_liberation_}X → KPLIB_X` (case-folded suffix). Module entries: dir `KP/KPGUI→KP/GUI`, `KP/KPPLM→KP/LOADOUT_MANAGER`; namespace `KPGUI_→KPLIB_GUI_`, `KPPLM_fnc_→KPLIB_fnc_`, hpp files `KPGUI_*→*`, `KPPLM_*→*`; stringtable `STR_GREUH_*→STR_KPLIB_GREUH_*`.
- **`--check-tree` mode (collision vs the LIVE tree, not just the map):** diff every map *target* against identifiers already present in the tree, so an old→`KPLIB_X` rename can never duplicate an existing `KPLIB_X` (pre-plan check: 0 such cases, and 0 overlap between the 12 KPPLM fn names and `functions/` — the engine enforces both).
- The `GRLIB_save_key` VALUE (`"KP_LIBERATION_<WORLD>_SAVEGAME"`) is a save-discriminator string, NOT a path: the identifier map may rewrite its prefix, but `recase_path` must NEVER touch it.

**Definition of Done:**

- [ ] `recase_path("scripts\\server\\game\\set_fog.sqf")` returns `"SCRIPTS\\SERVER\\GAME\\set_fog.sqf"`; a path with no extension uppercases all segments; the save-key value string is left untouched by `recase_path`.
- [ ] `apply_identifiers("x = GRLIB_all_fobs;", map)` renames only whole tokens (no hit inside `myGRLIB_all_fobsX`).
- [ ] `python tools/sweep.py --check-map` AND `--check-tree` exit 0 on the real map/tree and exit 1 on deliberately-colliding fixtures.
- [ ] Verify: `uv run --no-project --with pytest pytest tools/tests/test_sweep.py -q`

### Task 2: Audit the full reference surface + finalize the map

**Objective:** Enumerate every reference the passes must update so nothing is missed: all directory path literals (incl. `CfgFunctions file=`), all 423 prefixed identifiers, all `setVariable`/`getVariable` string keys, and — critically — any path literals inside the 18 `Missionbasefiles/*/mission.sqm` files (which `refcheck` does not scan). Fold any `.sqm` hits and any newly-found identifiers into `rename_map.py`.

**Files:**

- Modify: `tools/rename_map.py`
- Create: `tools/tests/test_rename_map.py`

**Key Decisions / Notes:**

- `mission.sqm` audit (verified pre-plan): the 18 `Missionbasefiles/*/mission.sqm` have **no path literals** (Pass A skips them) but **do contain `GRLIB_endgame`** → Pass C's identifier sweep must include them. Re-grep for any other prefixed identifier in `.sqm`.
- **Existing-`KPLIB_` collision check:** enumerate every `KPLIB_*` suffix already in the tree; assert no map target equals a *different* existing identifier (verified: 0).
- **Module-name clash check:** assert the 12 `KPPLM` fn names don't already exist under `functions/` (the `KPLIB_fnc_*` group) before merging the namespace (verified: 0 overlap).
- **Config-file surface:** read `_tools/_presets.json` — every distinct `configFile` value must be covered by the sweep glob (verified: single `kp_liberation_config.sqf`).
- **stringtable surface:** the 32 `STR_GREUH_*` `<Key ID>`s + their `$STR_`/`localize` references are in the map (→ `STR_KPLIB_GREUH_*`).
- Cross-check the identifier list against `namespace_keys.py` output so every mission-owned string key is mapped.
- `test_rename_map.py`: map is total over the live identifier set AND collision-free (map-internal and vs the tree).

**Definition of Done:**

- [ ] The map covers 100% of prefixed identifiers in `Missionframework/` AND `GRLIB_endgame`/any other identifiers in `Missionbasefiles/*/mission.sqm` (test fails on any unmapped live identifier).
- [ ] No map target collides with a different existing tree identifier; KPPLM fn names don't clash with `functions/`; every `_presets.json` configFile is in the sweep glob; the 32 `STR_GREUH_*` keys are mapped.
- [ ] Verify: `uv run --no-project --with pytest pytest tools/tests/test_rename_map.py -q`

### Task 3: Pass A — directory recasing (tree-wide UPPERCASE)

**Objective:** `git mv` all 65 directories under `Missionframework/` (and `Missionbasefiles` mission folders if needed) to UPPERCASE names, then rewrite every path literal and `CfgFunctions file=` so dir segments are UPPERCASE and filenames stay lowercase. Filenames and file contents (other than path strings) are untouched in this pass.

**Files:**

- Modify: all `*.sqf`, `*.hpp`, `*.ext` with path literals (engine-driven; ~hundreds)
- Modify: directory structure (git mv)

**Key Decisions / Notes:**

- Do the `git mv`s bottom-up (deepest dirs first) to avoid path churn; on case-sensitive Linux these are real renames.
- Then run `python tools/sweep.py --recase-paths` to rewrite references.
- Regenerate the `sqf_lint` baseline relpaths (dir prefixes changed) — `python tools/sqf_lint.py --update-baseline`.

**Definition of Done:**

- [ ] `python tools/refcheck.py` exits 0 — the authority, resolving both `\` and `/` separators, reports zero case mismatches and zero broken refs. (A `rg` spot-pattern would miss forward-slash `#include`s, so refcheck is the gate, not grep.)
- [ ] `python tools/sqf_lint.py` exits 0 (baseline regenerated for new relpaths).
- [ ] Verify: `python tools/refcheck.py && python tools/sqf_lint.py`

### Task 4: Pass B — module + file renames

**Objective:** Rename the cryptic modules `KP/KPGUI → KP/GUI` and `KP/KPPLM → KP/LOADOUT_MANAGER` (dirs already UPPERCASE from Pass A — this is the *name* change), rename their hpp files (`KPGUI_defines.hpp→defines.hpp`, `KPPLM_functions.hpp→functions.hpp`, etc.), rename `fucking_set_fog.sqf → set_fog.sqf`, and update their coupled namespaces (`KPGUI_* → KPLIB_GUI_*`, `KPPLM_fnc_* → KPLIB_fnc_*`) — updating `description.ext` includes and `CfgFunctions` `file=`/class names accordingly.

**Files:**

- Modify: `Missionframework/description.ext`, `Missionframework/CfgFunctions.hpp` (+ the module `*_functions.hpp`)
- Modify: the ~16 module files + the 12 `KPPLM_fnc_` call sites + `set_fog` reference (`SCRIPTS/SERVER/init_server.sqf`)
- Modify: directory/file structure (git mv)

**Key Decisions / Notes:**

- `KPPLM_fnc_*` unifies into the main `KPLIB_fnc_*` namespace (the tag class becomes part of `KPLIB`), so the 12 call sites change `KPPLM_fnc_apply` → `KPLIB_fnc_apply` etc. Confirm no name clash with an existing `KPLIB_fnc_apply` (Task 1 `--check-map` covers this once these are in the map).
- `KPGUI_*` are UI macros (`#define`); rename in `KPGUI_defines.hpp`/`KPGUI_classes.hpp` and the `KPPLM_dialog.hpp` usages.
- Run `python tools/sweep.py --modules` after the `git mv`s.

**Definition of Done:**

- [ ] `python tools/refcheck.py` exits 0 (CfgFunctions still resolves; `KPLIB_fnc_*` count increased by the former KPPLM functions).
- [ ] No `KPGUI_`/`KPPLM_` token remains: `! rg -n 'KPGUI_|KPPLM_' Missionframework`.
- [ ] `python tools/sqf_lint.py` exits 0.
- [ ] Verify: `python tools/refcheck.py && python tools/sqf_lint.py`

### Task 5: Pass C — variable prefix unification to `KPLIB_`

**Objective:** Apply the identifier rename map to unify all remaining `GREUH_`/`GRLIB_`/`KP_liberation_`/`kp_liberation_` global variables and persisted string keys to `KPLIB_` (the 2 GREUH collisions → `KPLIB_greuh_*`), across all `*.sqf`/`*.hpp`/`*.ext` AND the `setVariable`/`getVariable` string literals AND the `GRLIB_save_key` value. This is the largest pass.

**Files:**

- Modify: ~400 files across `Missionframework/` (engine-driven)
- Modify: `Missionframework/stringtable.xml` (32 `STR_GREUH_*` keys) + their `$STR_GREUH_*`/`STR_GREUH_*` references
- Modify: `Missionbasefiles/*/mission.sqm` (18 files — each contains `GRLIB_endgame`)

**Key Decisions / Notes:**

- Run `python tools/sweep.py --identifiers` (uses the finalized `rename_map.py`).
- String keys: the same map applies to quoted `setVariable`/`getVariable` keys; `namespace_keys.py` verifies writer↔reader pairing is preserved (no key ends up with writers-but-no-readers or vice-versa beyond what existed pre-sweep).
- **stringtable.xml:** 32 `STR_GREUH_*` localization keys (referenced as `$STR_GREUH_*` in `GREUH/UI/GREUH_interface.hpp` and `STR_GREUH_*` in the GREUH scripts) → rename the `<Key ID=...>` AND every reference to `STR_KPLIB_GREUH_*` (preserving the GREUH grouping, matching the `KPLIB_greuh_*` collision convention).
- **mission.sqm:** all 18 `Missionbasefiles/*/mission.sqm` contain the identifier `GRLIB_endgame` (verified: no *path* literals, so Pass A doesn't touch them — but the identifier sweep MUST). `refcheck`/`namespace_keys` do NOT scan `.sqm`; this surface is verified by grep-completeness + the user's in-game smoke test.

**Definition of Done:**

- [ ] `! rg -n '\b(GREUH_|GRLIB_|KP_liberation_|kp_liberation_)' Missionframework` returns nothing except the intentional `KPLIB_greuh_*` names.
- [ ] `python tools/namespace_keys.py` shows all keys owned `mission` under `KPLIB_`, writer/reader pairing intact (no newly-orphaned keys vs the pre-sweep inventory).
- [ ] `python tools/sqf_lint.py` exits 0 (baseline regenerated — messages now reference `KPLIB_*`).
- [ ] Verify: `python tools/refcheck.py && python tools/sqf_lint.py && python tools/namespace_keys.py`

### Task 6: Regenerate baselines, update tools, final verification

**Objective:** Finalize: regenerate the `sqf_lint` baseline against the fully-swept tree, simplify the tools' prefix lists to the unified namespace (`namespace_keys.MISSION_PREFIXES = ("KPLIB_",)`), update `tools/README.md` + both plan docs, run the full build, and confirm all guardrails green — the mechanical proof the sweep is complete and non-breaking.

**Files:**

- Modify: `tools/sqf_lint_baseline.txt` (regenerated)
- Modify: `tools/namespace_keys.py` (prefix list), `tools/README.md`
- Modify: `docs/plans/2026-05-30-directory-naming-cleanup.md` (resolution notes)

**Key Decisions / Notes:**

- After this pass the only mission prefix is `KPLIB_`; update `namespace_keys.MISSION_PREFIXES` and its test accordingly.
- Build check is part of Goal Verification Truth 2.

**Definition of Done:**

- [ ] `python tools/refcheck.py && python tools/sqf_lint.py && python tools/namespace_keys.py` all exit 0.
- [ ] `cd _tools && npm install && npx gulp` exits 0 (all 18 PBOs pack).
- [ ] Full tool test suite green: `uv run --no-project --with pytest pytest tools/tests -q`.
- [ ] Verify: `python tools/refcheck.py && python tools/sqf_lint.py && (cd _tools && npx gulp >/dev/null 2>&1 && echo BUILD_OK)`
