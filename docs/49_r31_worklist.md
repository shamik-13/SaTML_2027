# Round 31 worklist — reviewer feedback on the current `paper/satml.tex`

Nine points. Each was validated against the draft and the artefacts before anything was changed.

## Validation

| # | Point | Verdict | Evidence |
|---|---|---|---|
| 1 | Abstract too dense; keep three numbers | **valid** | abstract carried 20, 78/79, 24, 2,946, ~100x plus `max-min-optimal horizon-uniform allocation`, `canonical order`, `per-alert oracle lower bound`, `horizon-free`, `horizon-aware`, `greedy oracle joint cost` |
| 2 | Move the alpha-death distinction into the Introduction after Table I | **valid as placement** | the substance was correct but only in Related Work (Sec. VIII), 5 pages after the theorems |
| 3 | Sell Theorem 3's security abstraction; cite the precise Vovk–Wang result | **partly valid** | the contribution paragraph already existed; the precise result number did **not** — only `\cite{vovk2021evalues}` |
| 4 | Separate the nominal FDR guarantee from the security results in Secs III and V | **valid** | `tab:deps` and Sec. VII-A carried it; Secs III and V did not state it inline |
| 5 | Front-load that the padding is real traffic | **valid** | the evidence was in Sec. V-E only; the threat model said nothing |
| 6 | The host-conditioned AIT arm looks selective | **valid, and the worst of the nine** | `ORGS_HOST = ["shaw", "wilson"]` was hard-coded, comment `(Shaw + typical)`. The detector had **never** been run on the other six folds |
| 7 | Reduce body density rather than adding results | **valid** | body was full at p.12 |
| 8 | Final language pass; `Per-alert On LSPR23...` fragment | **valid** | dangling `Per-alert` at satml.tex:230; a mechanical sweep for doubled words, spacing, `??`, mixed hyphenation and hard-coded refs found nothing else |
| 9 | Keep limitations strong, do not lengthen | **valid, no action** | one limitation was *removed* (the host arm is no longer narrow) |

## Point 6: the experiment

`ORGS_HOST` now defaults to every organisation; the host-conditioned chain runs at all eight folds.

Two blind-audit findings changed the design and the wording:

1. **Fold-order dependence (CRITICAL).** One mutable RNG was threaded through the flow arm and then
   every host fold, so pool subsampling and replay draws depended on how many folds ran first —
   adding six organisations perturbs the two already reported. Fixed by keying the generator to
   `(organisation, arm, order)`, which also makes t67's first-flow arm reproduce t54's rows by
   construction rather than by coincidence of RNG position.
2. **"Suppressible" is a possibility count (CRITICAL).** It means at least one of 200 replay draws
   cleared the threshold inside the scored accumulation range. An episode outside it is a censored
   zero-success simulation, **not** a demonstrated attack failure. The table notes, the appendix
   prose and the body all now say so, and the per-draw success column carries the reliability the
   count does not.

Also fixed: `t76_joint_ait.py` read `tuple(t54.ORGS_HOST)`, which became `tuple(None)` under the new
default. The joint host arm stays at the two organisations the design note scoped it to.

## Gate changes, and why

`t65` encodes earlier reviewers' explicit demands, several of which this reviewer overrode. The rule
applied: **accuracy assertions stay, style pins move.**

- kept, reworded: the linear rate is the best case and other allocations cost more; the families are
  arrival-time; the impossibility needs unbounded membership and attainment; LSPR23 and AIT stay
  separate; the AIT number keeps its per-alert and canonical scope; Theorem 3 is stated on the
  attained alert, not on the family; <=240 words.
- relaxed: the abstract need no longer carry `$24$` and `$2{,}946$`. Both rows stay in the registry,
  pinned to the body, so neither can drift or return unregistered.
- tightened: `\cite[Prop.~3.1]{vovk2021evalues}` is now *required* at the theorem and the proof idea.
- host arm: the checks now derive the counts from the artefact and require the arm to cover every
  organisation the flow arm detects on, so a future narrowing fails the gate.

## Executed (8 Sep 2026)

All nine points applied.

- **1** abstract rewritten: 239 words, three numbers (20 calibration flows, 78 of 79, two orders of
  magnitude). `24`, `2,946`, "max-min-optimal horizon-uniform allocation", "per-alert oracle lower
  bound" and "greedy oracle joint cost" as an unglossed term are gone from it; every scope condition the
  earlier rounds won is still asserted, reworded.
- **2** a paragraph after Table I, leading with the contribution ("Bounded evidence and decaying levels
  are individually familiar; their composition is not a matter of degree"), not with a concession.
- **3** `\cite[Prop.~3.1]{vovk2021evalues}` at the theorem and the proof idea, now *required* by t65.
  Verified against the published paper: Prop. 3.1, AoS 49(3) §3, "the arithmetic mean M_K essentially
  dominates any symmetric e-merging function", with essential domination defined as G(e)>1 => F(e)>=G(e)
  — exactly the paper's rendering. (`appendix_proofs.tex` already had the number; the body did not.)
- **4** one sentence each in Secs III and V.
- **5** one sentence in the threat model, pointing at V-E and V-F.
- **6** the eight-fold host run — see `docs/04` §4.73.
- **7** body back to 12 pages. Cuts, not just compression: a verbatim-duplicated citation cluster removed
  from the Introduction (it is identical in Related Work); the auxiliary controller corroboration
  (e-LORD 101, restart 55) moved to App. C; the intro chain paragraph merged with the repair paragraph;
  the residual-risk restatement, Sec. VI-A's tradeoff list (it is tab:defenses' own column), a five-item
  appendix inventory and the Conclusion all tightened; figure* widths 0.78 -> 0.72.
- **8** the `Per-alert On LSPR23` fragment fixed. A mechanical sweep (doubled words, spacing, `??`,
  mixed hyphenation, hard-coded refs, near-duplicate sentences) found one further defect: the citation
  cluster duplication above. `characterise` added to the no-split hyphenation list.
- **9** no disclaimer added; one limitation *removed* (the host arm is no longer narrow) and the
  budget caveat placed at the claim in V-F rather than in the limitations.

Gates after: t45 268/0, t61 242/0, t65 195/0, t68 2/0, t69 0 drift, t70 3/0, t71 38/0.

## Blind audit of the round-31 text against the artefacts

Second codex pass (`brief_B`), paper-vs-artefact. **No CRITICALs**, and every number checked matched the
artefact: 78/79 canonical with success 0.93–1.00 and medians 12–4,650; 84/85 first-flow with medians
212–13,142; Table III's host row 57/63 at 43–8,471.5; all eight `aitsupp` rows; the LSPR23 joint totals;
the Vovk–Wang use; and Secs III/V against the dependency table. It also confirmed that the appendix
prose describes the non-suppressed host episodes correctly as censored, not impossible.

All five findings were abstract **scope**, which is the standing tension with this round's request to
strip qualifiers. Four were real losses and are fixed; the word cap moved 240 -> 250 to pay for them,
recorded in t65 as scope-only:

- `20 calibration flows` -> `cold-start feasibility ... $20$ calibration units`. The ratio is unit-free
  (under grouping the unit is episodes), and Corollary 1 is a cold-start criterion. "flows" was
  inherited from the previous abstract, not introduced here.
- `78 of 79 true detections` -> `78 of 79 flow-only true detections`. Material *because of this round*:
  the paper now also reports a host-conditioned AIT arm at 57/63, so an unqualified 78/79 reads as the
  whole AIT result.
- `no symmetric e-merging rule` -> `family`. Theorem 3 is about a family indexed by arity, which is the
  cross-arity point.
- `two orders of magnitude` -> `about two orders`. 111x at 0.55 but 97.8x at 0.62.

Not taken: the auditor also wanted the LSPR23 joint result's full arm (canonical, seed 0, two windows,
horizon-aware, zero-evidence pads, greedy oracle) in the abstract. The abstract carries "On LSPR23" and
"greedy oracle"; the rest is in Sec. V-D and `tab:costcurve`. Putting six qualifiers on one abstract
sentence is the density the reviewer asked us to remove, and the claim is already marked as an oracle
strategy rather than a general joint-cost result.

## Two submission-blockers closed (8 Sep 2026)

**Bibliography (docs/45 item 23).** Verified against primary sources, not filled in from memory:

- `xu2024elond` — AISTATS 2024, PMLR 238, **pp. 3997–4005** (proceedings.mlr.press/v238/xu24a.html).
- `fisher2022deadlines` — AISTATS 2022, PMLR **151**, **pp. 8340–8359**
  (proceedings.mlr.press/v151/fisher22a.html); `volume` was missing too.
- `kronert2024fdr` — still an arXiv preprint (v2, Dec 2024), no journal, so
  `@article{journal={arXiv preprint}}` -> `@misc` with `eprint`/`archivePrefix`. Renders in the same
  house style as the other `@misc` entries.

Not changed, deliberately: the five NeurIPS entries (`ramdas2017lordpp`, `tian2019addis`,
`yasodharan2019nonzero`, `chen2024adversarialbh`, `huo2024realtime`) carry author/title/booktitle/volume/
year plus an arXiv note, which is the canonical NeurIPS citation form; NeurIPS proceedings are not
conventionally cited with page ranges. `egai2025` (ICML 2025, PMLR 267, confirmed via OpenReview and the
ICML programme) and `xu2026eclosure` (UAI 2026 — the arXiv Comments field reads "Camera-ready version for
UAI 2026") have no page range I could verify from a primary source. **Page numbers were not invented for
any entry**; where a range could not be verified it is omitted.

**Citation characterisations (docs/46 open item).** Both now verified against the arXiv abstracts and
both stand — see docs/46. [11] does use conformal p-values with an online FDR controller; [14] does use
BH-style batch FDR control.

Remaining before submission, all author-only: IEEE PDF eXpress; the anonymised repository freeze; the
docs/45 item 22 LLM footprint-proxy decision; and a look at Figs. 1 and 4 at print size, since the refit
took the two full-width figures from 0.78 to 0.72 textwidth.
