# `src/` submission-package audit — minimality, completeness, notebook (12 Sep 2026)

Asked for once the draft (`paper/satml_codex_edit.tex`) was essentially final: make sure everything in
`src/` is required by the paper, and that `src/paper.ipynb` runs end to end from the shipped cache.
Follows `docs/50_src_audit.md` (8 Sep); the paper has moved since (rounds 32–34 added `t77` and three
tables) and the earlier audit's keep-list was re-derived against the current draft rather than reused.

## Method

Runtime traces, not greps, for the consumers: `builtins.open`/`io.open` wrapped while running the table
generator, the figure builder and the gates `t61`, `t65`, `t71`, `t69`, `t72` (the paper gates with
`T61_TEX`/`T65_TEX` pointed at the codex draft), recording every read under `src/lib/out/`. The import
graph of `src/lib` was parsed with `ast`. Every generated table (48 files) and figure (6) was matched
against the draft's `\input{tables/...}` and `\includegraphics` lines: all consumed, none missing. For
stages whose artefact no automated consumer reads, the draft was searched for the claim the stage backs.

## Minimality: two stages, one duplicate artefact and one orphan removed

| moved to `.attic/` | why it is not required |
|---|---|
| `t28_P5_padding.py`, `t28_P5.json` | static-threshold (`T/w0`) padding costs. The draft's only static figure, "median 34 flows at 0.85 under the canonical order", is `t28b_reallevel.json`'s own `med_pad_static` column (t28 has no order arm). Its sole dependent was `t43`. |
| `t43_E10_xwindow_padding.py`, `t43_E10.json` | padding across all five windows. The claim it backed left the paper before the codex rewrite; only the notebook's negative-results list still carried it (removed). `proto/t45` still reads the `proto/out` copy. |
| `t26_H4.json` | two-position grouping sweep, a strict subset of `t26_H4_5pos.json` (same 5 families × 7 widths, positions 0.62/0.85 only). Nothing reads it; `runner.py` no longer runs the two-position arm. |
| `h8_audit_sample.csv` | written by `proto/t27` (already in the attic), read by nothing in `src/`. |

Everything else stays, and each keep was verified against the draft, not assumed from the earlier audit:
`t17` is read by the theory stage `t18` (check 2 evaluates the bound on the measured pads); `t21d` backs
the "Horizon misspecification (single cell)" paragraph (144/152, 151, 0) and is loaded by `t61`; `t22`
backs "An Isolation Forest has the same margin … not one attack flow above the calibration maximum";
`t29` backs App. I's "optimal e-to-e boosting factor … is $b^\star=1$ by construction". The four CSVs
`a1_extreme_tail_seed{0,1}.csv` and `a2_audit_adjudicated.csv` are outputs of `t30`/`t31`.

Result: **61 stage modules + `figures.py` + `tables.py`, 60 artefacts, 17 MB, no `__pycache__`.**
`runner.py` also gained the missing `t77_cor2_premise` stage (added in round 32 but never registered).

## Completeness: the table generator now ships

`paper/make_appendix_tables.py` (2,822 lines, every table the paper `\input`s) lived outside `src/`, so
the package the Open Science section describes ("renders every table and figure directly from the shipped
result objects") could not have rebuilt a single table. Same defect the figures had before `figures.py`
moved, same fix: the generator is now **`src/lib/tables.py`** (`RES = ./out`, `OUTDIR` settable,
`build_all()`), `paper/make_appendix_tables.py` is a thin wrapper that sets `OUTDIR = paper/tables`, and
`src/make_tables.py [OUTDIR]` mirrors `make_figures.py`. All 48 files regenerate **byte-identical**
through both wrappers. `t61` reads the generator source from its new home; `t70` lists it as a consumer.

## Notebook: runs from cache, and now covers every stage

Before: 43 code cells, clean, but seven table-backed stages were never touched (`t21c` behind the
detection and procedure tables, `t23`, `t25`, `t63`, `t64`, `t76`, `t77`) and four prose-backed ones
(`t21d`, `t22`, `t29`; `t17` only via `t18`). Added one markdown + one code cell for each, placed in the
section that discusses them, printing the quantities the paper quotes (first-flow arms labelled as such;
`t76` totals summed over raw medians and rounded once, as the tables do). Section 7 now also rebuilds all
48 table files from `lib/out` into a temporary directory. The negative-results list lost the cross-window
padding item.

After: **106 cells, 54 code cells, 0 errors, 34 s** under `nbclient` from `src/`; every code cell has an
execution count and output; written back in place with outputs. The eleven theory stages rewrite their
JSONs during the run and `runner.py --theory` rewrites them again: **no artefact changed a byte** either
time. Verified by reading the notebook JSON, not by exit code (`docs/04` §8 traps).

## Gates after the changes

t61 247/0 (codex draft), t65 140 ok / 57 pre-existing misses on the codex draft and 0 on `satml.tex`
(unchanged from before this work), t69 0 drift, t70 3/0 (55 of 57 artefacts textually referenced after
teaching it to read notebook cell sources as text; the two "unused" are `t17_T2`, read by `t18`, and
`t18_T4`, the theory stage's own output), t71 38/0, t72 10/0.

## Left as is

`paper/figures/` still holds four PDF/PNG pairs no draft includes (`fig1_system`, `fig3_granularity`,
`fig4_attacks`, `fig4_attacks_body`); they are outside `src/` and were not touched. The two-position
branch of `t26_H4_grouping.main(five=False)` remains in the module; only its runner entry and artefact
went. `proto/out` remains the stale store `t45` validates `docs/04` against (docs/50, open).
