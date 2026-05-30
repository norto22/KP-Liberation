# `tools/` — Python dev & CI checks

> **Not to be confused with [`_tools/`](../_tools)** — that (leading underscore)
> is the **Node/gulp mission build** that assembles and packs the PBOs.
> **This** `tools/` directory is the **Python** static-analysis tooling that
> guards code quality. They are independent toolchains.

These checks run entirely off the source files — **no Arma 3 engine required** —
so they work locally and in CI. They exist to make the upcoming codebase
tidy-up (especially the full `KPLIB_` namespace sweep) verifiable mechanically:
CI turns red only on *newly introduced* breakage, never on pre-existing legacy
quirks.

## Setup

```bash
pip install -r tools/requirements.txt
```

## The checks

| Script | What it does | Gates CI? |
|--------|--------------|-----------|
| `sqf_lint.py` | Runs the `sqflint` analyzer over every `Missionframework/**/*.sqf`; fails only on findings **not** in the committed baseline. | Yes — on *new* findings |
| `refcheck.py` | Resolves every `CfgFunctions` class→file mapping and every `execVM`/`preprocessFile`/`#include` path; flags broken references and orphan files. | Yes — on broken references |
| `namespace_keys.py` | Inventories all `setVariable`/`getVariable` string keys (mission-owned vs third-party) for the rename sweep to verify against. | No — informational |

Run from the repo root:

```bash
python tools/sqf_lint.py        # gate against the baseline
python tools/refcheck.py        # reference integrity
python tools/namespace_keys.py  # print the key inventory
```

### Updating the SQF lint baseline

The baseline (`sqf_lint_baseline.txt`) records the *expected* sqflint findings
on the current tree (legacy warnings + sqflint's false-positives on modern
commands like `findIf`). Regenerate it after an intentional, reviewed change:

```bash
python tools/sqf_lint.py --update-baseline
```

A finding **not** in the baseline (e.g. a new unbalanced bracket) fails the
check and names the offending file. Baseline format: one tab-separated
`relpath<TAB>severity<TAB>message` line per finding, sorted.

> sqflint is superlinear on the large equipment-*data* files (e.g.
> `arsenal_presets/unsung.sqf`, 167 KB), so files over ~40 KB and any that
> exceed the per-file timeout are skipped and listed in the output (never
> silently).

### Updating the reference-integrity baseline

`refcheck.py` resolves every `CfgFunctions` mapping and `execVM`/`preprocess`/
`#include` path. A **missing** target fails the check; a **case mismatch**
(harmless in a packed PBO, broken on case-sensitive Linux) is a warning;
orphan detection is limited to `fn_*` files not registered in `CfgFunctions`
(loose scripts load via dynamic paths and can't be traced statically).

Pre-existing broken references are recorded in `refcheck_baseline.json` so the
gate fails only on **newly introduced** breakage. The current baseline holds two
known-broken legacy references (`kp_fuel_consumption.sqf:17`,
`export_template.sqf:9`). Regenerate after an intentional change:

```bash
python tools/refcheck.py --update-baseline
```

## Tests

```bash
uv run --no-project --with pytest pytest tools/tests -q
```
