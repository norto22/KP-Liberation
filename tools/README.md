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
| `refcheck.py` | Resolves every `CfgFunctions` class→file mapping and every `execVM`/`preprocessFile`/`#include` path; flags broken references and orphan files. | Yes — on **any** error or warning |
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

### Reference integrity (`refcheck.py`)

`refcheck.py` resolves every `CfgFunctions` mapping and `execVM`/`preprocess`/
`#include` path. It exits non-zero (**CI red**) on **any** finding — there is no
baseline; every reference problem must be fixed to get the check green:

- a **missing** target (ERROR),
- a **case mismatch** (WARNING — harmless in a packed PBO, broken on a
  case-sensitive Linux server),
- an unregistered `fn_*` function (WARNING).

Orphan detection is limited to `fn_*` files not in `CfgFunctions`; loose scripts
load via dynamic paths and can't be traced statically.

> `refcheck` is **green** on the current tree. It strips `//` and `/* */`
> comments before scanning, so commented-out / example `execVM` paths in
> docblocks are not treated as references. Unlike `refcheck`, the `sqf_lint`
> check keeps a baseline: its 338 findings include sqflint's own false positives
> on modern commands, which can't all be "fixed" — so it gates on *new* findings
> only.

## Tests

```bash
uv run --no-project --with pytest pytest tools/tests -q
```
