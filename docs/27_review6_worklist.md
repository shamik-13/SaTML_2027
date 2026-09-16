# Review 6 worklist — sixth round (prior-art collision + framing + two new measurements)

> **STATUS: R1, R1b, R2, R3, R4, R5, R6, R7, R8, R9 DONE and codex-verified; R10 in progress;
> R11 (page refit) deferred to the very end per the user.**
> Source: reviewer feedback pasted 2026-09-01 (round 6). Rule (unchanged, per
> `[[blind-codex-review-workflow]]`): for each item, (a) implement, (b) blind-codex review,
> (c) edit paper + notebook + `docs/04`. **Page size is deferred to the very end** (user instruction).
> Builds on `26_review5_worklist.md`.

The reviewer's headline: **C1 has a prior-art collision.** A NeurIPS 2024 paper states the conformal
resolution floor and its consequence for online multiple testing explicitly, and is not cited. The
fix is not to weaken C1 but to cite proactively and state the delta precisely.

---

## Validity triage — every point VERIFIED against the source before starting

| # | point | verdict | evidence |
|---|---|---|---|
| **R1** | Huo, Lu, Ren, Zou (NeurIPS 2024) state the `1/(\|D_cal\|+1)` floor and its online-testing consequence; not cited | **VALID — confirmed verbatim** | Downloaded the NeurIPS proceedings PDF. Appendix B.2, p.15: *"However, the conformal p-values are lower bounded by 1/(\|D_cal\| + 1), which leads to unsatisfactory performance for online multiple testing methods based on p-values. Since these methods require sufficiently small p-values to make rejections."* Related work, p.2: α-death defined per Ramdas et al. 2017 as *"a permanent end to decision-making when the decision threshold is too small"*. §4.1: *"methods relying on conformal p-values, such as LOND, SAFFRON, and ADDIS, encounter the alpha-death (stop early) issue … especially in small calibration sets."* App. D.3 sweeps `n_cal` 500→2500 and observes more selections as `n_cal` grows. Not in `refs.bib` (35 entries checked). |
| **R1b** | *(found by our own lit audit, not the reviewer)* Krönert, Célisse & Hattab, *FDR Control for Online Anomaly Detection* (arXiv 2312.01969) derive a calibration-cardinality condition `n = νm/α − 1` | **VALID and closer in FORM than Huo et al.** | Their Cor. 1: with `n = νm/α − 1` the empirical p-value grid `{j/(n+1)}` contains BH's critical values `{αk/m}` exactly, so windowed BH attains `FDR = m₀α/m` exactly. Structurally the same shape as our `\|C\| ≥ kT/c₀ − 1` but a **different question**: theirs is *exactness of the realised level* for a **batch BH over a sliding window of length `m`**; ours is *whether any rejection is possible at all* in a rejection-free run of an **α-spending online procedure over the whole horizon `T`**. They never claim infeasibility below it (Fig. 2 shows detection at non-aligned `n`), and their windowing *is* our §restart escape. Must be cited and distinguished. |
| **R2** | "our three results" contradicts C2 being "not a third independent result" | **VALID** | `main.tex:72` *"Our three results follow one spine"* vs `main.tex:151` *"This is not a third independent result"*. |
| **R3** | Intro pluralises the escape→attack link beyond what is proved | **VALID** | `main.tex:164` *"the procedures escaping C1 condition their spending index on observed evidence, exposing that index in closed form"* — plural. `sec:escapes` (`main.tex:462-476`) is careful: ADDIS escapes via a **selection-conditional spending index**; online e-BH escapes via a **history-wide fixed point**. No state-poisoning attack is demonstrated against online e-BH. Abstract (`:89`) and fig1 caption (`:178`) are already singular. |
| **R4** | Headline detections/padding use first-flow order, but the clean `M_j` argument needs the key-hash order | **VALID** | `tab:main` headline 18/72 and median pad 118/5,202 are first-flow. `apptab:ordering` gives key-hash 3/34. The `M_j` preservation argument (`main.tex:1010-1013`) is airtight only under a key-determined order (373 other episodes move under first-flow vs 0 under key-hash). No **attack** row exists for the recommended order — only a closed-form `median_rstar` inside `t53`. |
| **R5** | Empirical compatibility with the *unconditional* benign firing rate does not demonstrate `E[e_i \| M_j] ≤ 1` | **VALID (already admitted)** | `apptab:tail` 0.55 row: 1 firing benign flow, CI `[0.03, 5.96]`. Deeper-`k` columns exist but are **unconditional**. No metadata-**stratified** diagnostic anywhere. |
| **R6** | Feedback section lacks the dedicated feedback-online-FDR literature; P/PI/AQT never defined | **VALID** | `grep` for `AQT` in `main.tex`: only `tables/feedback.tex` and `apptab:frontier`. No definition of P, PI or AQT in body or appendix. Lu, Huo, Ren, Wang & Zou, *Feedback-Enhanced Online Multiple Testing with Applications to Conformal Selection* (arXiv 2509.03297, v3 2026-07-18) proposes **GAIF** + **OCTF** with finite-sample FDR/mFDR under instant/delayed/full/bandit feedback — exactly the regime our sentence dismisses. Not cited. |
| **R7** | "atomic ground truth" is stronger than the artefact supports | **VALID** | LSPR23 has no campaign identifier (the paper says so at `main.tex:213-215` and `sec:limitations`), so the 5-minute src-dst unit is a *chosen fixed denominator*, not externally validated incident truth. 6 occurrences. |
| **R8** | Host-conditioning claim must stay narrow | **VALID (mild)** | `main.tex:1069` *"a host-conditioned detector does not undo the transfer on either dataset once the pad's own context is replayed causally"* generalises past the covered setting (2 orgs, 9 episodes, distinct-peer counts pinned, no flood regime). `sec:transferattack` already states it narrowly; the Limitations line and the C3 lead-in do not. |

---

## TIER 1 — prior art and framing (the highest-priority block)

- [x] **R1** Cite Huo et al. and state the delta.
  - `refs.bib`: add `huo2024realtime` (NeurIPS 2024, proceedings entry).
  - **Related Work**: new sentence in the conformal/online-FDR paragraph naming what they establish
    (the floor, its consequence for p-value-based online testing, α-death observed empirically for
    LOND/SAFFRON/ADDIS, mitigated by a larger `n_cal`) and the remedy they propose (II-COS, an
    lFDR-based selection rule, *not* a conformal-p-value online procedure).
  - **Intro C1**: adopt the reviewer's safer-and-stronger novelty statement — prior work *observed*
    that finite conformal resolution can make online testing underpowered; we characterise **when it
    becomes structural impossibility**: a finite absorbing discovery horizon for two families covering
    LOND/e-LOND/LORD++/e-LORD, the exact calibration–horizon scaling, the classification of escapes and
    why they escape, and the design tradeoffs at security-scale horizons. Two sentences, not a
    paragraph.
  - Also make explicit that Huo et al.'s statement is for **p-value** procedures, whereas our families
    cover the **e-value** counterparts (e-LOND, e-LORD) too.
- [x] **R1b** Cite Krönert et al. and distinguish the formula. One sentence in Related Work + one in
  §V (`sec:granularity` or `cor:budget` discussion): same algebraic shape, different question
  (exact-level grid alignment for windowed BH vs feasibility of any rejection for an uninterrupted
  α-spending run over the full horizon), and their windowing is our restart escape.
- [x] **R2** Two contributions, not three. Abstract (`:72`), Intro contributions block
  (`:139-165`), Conclusion. C1 = feasibility characterisation; C2 = adversarial attackability;
  the granularity–resolution tradeoff is the **bridge**, kept as a named subsection but not counted
  as a co-equal result. Renumber `C1/C2/C3` → `C1/C2` with the bridge unlabelled, and sweep every
  `C3`/`C2` reference in the body (≈20 sites).
- [x] **R3** Singularise the escape→attack link. `main.tex:164`: "one escape mechanism, exemplified by
  ADDIS, conditions its spending index on observed evidence and thereby exposes it; online e-BH
  escapes by a different route (a history-wide fixed point) against which we do **not** demonstrate
  this attack." Sweep `sec:attack` lead-in (`:596-601`) and `fig:system` caption for the same
  pluralisation.

## TIER 2 — new measurements (codex-verify each)

- [x] **R4** Attack row for the canonical key-hash order. Extend `t48_W3_dilution.py` (or a small
  `t55`) with a **key-hash-ordered arm**: re-run e-LOND under `t53`'s canonical
  `hashed_order(key_hash(src,dst,bucket))`, take its detected malicious set (3 at 0.55, 34 at 0.85),
  and price suppression with the **same black-box pool** — measured `r*` vs closed form, per-episode.
  Report `3/3` and `34/34` suppressed with median cost. Add the row to `apptab:w3dilution` (or
  `apptab:ordering`) and one sentence in `sec:paddingcost`. This removes the "demonstrated only under
  an ordering you recommend replacing" objection.
  - Second, cheaper half of the reviewer's alternative (do **both** if it is free): assert that under
    the key-hash order a pad **cannot** move any hypothesis's slot — already measured in `t53`
    (`others_moved_hashed_key = 0`), so state it as the reason this row is the validity-clean one.
- [x] **R5** Metadata-stratified Assumption-1 diagnostic. New stage `t55_a1_strata.py`: for each
  window, measure the benign firing-rate ratio (measured / nominal `k/(|C|+1)`) at rank depths
  `k ∈ {1, 10, 100, 1000}` **within metadata strata** — (i) episode arity bins, (ii) protocol/service
  `(proto,dport)` classes, (iii) time-bucket strata, (iv) high-support host strata — with exact
  Clopper–Pearson intervals and a stratum-count summary (how many strata's CIs exclude 1, at each
  depth, vs the number expected by multiplicity). Deeper `k` is the point: it buys counts, so the
  intervals are informative where `k=1` gives one firing flow. New appendix table + 2–3 sentences in
  `sec:tail`. **The conclusion stays "under Assumption 1"** — this shows the assumption was
  interrogated, not that it is proved.

## TIER 3 — scope, terminology and the feedback section

- [x] **R6** Feedback section. Decision: **keep the experiment, cite the dedicated literature, and
  narrow the claim** (page budget is deferred, and deleting a measured result to make room is worse
  than fixing its framing).
  - `refs.bib`: `lu2026gaif` (arXiv 2509.03297), and for the online-conformal-selection neighbours
    `liu2025ocsarc` (arXiv 2508.13838) and `gollapudi2026limitedfeedback` (arXiv 2605.14953).
  - **Define P, PI and AQT** (currently undefined anywhere): appendix `app:procedures` — P and PI are
    proportional / proportional–integral controllers on a windowed `FDP` estimate; AQT is a
    stochastic-approximation quantile tracker with the `+(1−q) / −q` update. Source:
    `t40_E7_controller.py:26-60`.
  - **Weaken the claim** from *"analyst feedback is no substitute"* (a statement about feedback in
    general) to a statement about **these three threshold controllers under wall-clock disposition
    delay**, and add one sentence pointing at GAIF/OCTF as the principled route with finite-sample
    guarantees — noting our measurement is about *delay*, which is orthogonal to their construction
    and which our numbers price.
- [x] **R7** Terminology sweep: "atomic ground truth" → **"fixed atomic evaluation reference"** (first
  use spelled out, thereafter "atomic reference unit"). 6 sites: abstract `:83`, intro `:150`,
  `sec:granularity` `:549`, fig3 caption `:570`, `tab:terms` `:1243`, `app:matrices` `:1341`. Keep the
  denominator-invariance argument verbatim.
- [x] **R8** Narrow the host-conditioning claim wherever it is stated outside `sec:transferattack`:
  Limitations `:1069` and any C3 lead-in. Target phrasing: "the particular causal host-conditioning we
  test does not stop the attack in the attacker–victim settings covered (2 organisations, 9 episodes,
  distinct-peer counts pinned; no flood regime)". Check the abstract does not carry a broader version.

## TIER 4 — verification and hygiene

- [x] **R9** Literature-review audit for the SaTML 2027 LLM policy (which puts explicit responsibility
  on authors). Sweep the neighbourhoods surfaced by R1/R1b: online-FDR-for-anomaly-detection,
  conformal selection with feedback, adversarial/Byzantine multiple testing (Zhang et al.,
  arXiv 2501.13242 — adversary corrupts p-values directly, a clean contrast with ours perturbing
  none). Add what is genuinely near, distinguish each in one clause, do not pad the bibliography.
- [ ] **R10** Reproducibility chain: `t45_record_consistency.py` green, `runner.py` registration for
  any new stage, notebook cell + full execute, `docs/04` §4.55 record, tectonic compile with 0
  undefined refs / 0 `??`.
- [ ] **R11** *(deferred to the very end, per user)* Page refit to 12pp of body. **Current state:
  the Conclusion's last sentence lands on page 14**, so two pages must come out. Additions this
  round: the C1 prior-art paragraph (~14 lines), the Krönert distinction at `cor:budget` (~6), the
  R5 body block (~26), the P/PI/AQT definitions (~20, appendix — does not count), the R4 paragraph
  (~11), the online-e-BH non-claim (~5), the feedback narrowing (~6), the four-non-claims list (~7),
  and two new appendix tables (do not count). Per `[[review5-worklist-outcome]]`: incremental prose
  cuts in the float region get absorbed by float repacking; what moves the break is shrinking the
  figures and cutting **full-width** captions, plus cuts in the float-free region after the last
  figure (Operational §VII, Robustness §IX, Discussion, Related Work, Conclusion). Measure by which
  page the Conclusion's last sentence lands on, over three fresh compiles.

---

## Progress log

**R4 — DONE, codex pass 1 clean on the code.** `t48_W3_dilution.py` gained an `episodes_keyhash`
arm importing `key_hash`/`hashed_order` from `t53` so the two stages cannot drift. Result: **3/3
suppressible at 0.55** (costs 23, 24, 33; median 24) and **34/34 at 0.85** (median 115.5), measured
= closed form on every one. `t53`'s independent implementation reports the same 24.0 / 115.5 —
cross-validated, and `t45` now asserts the agreement. Codex verified the index algebra
(`inv[order]` un-permutation), the order's permutation/bucket-monotonicity, that the hash reads
nothing a pad can change, and that the pool/pricing reuse is legitimate; it verified independently
that no episode mixes src, dst or bucket. Its three actionable points were all taken: the result is
now in the table and the body, `per_episode.ep` is a stable gid (not a stream position), and the
n=3 set is reported as three individually priced attacks, never as a rate.

**R5 — DONE, and the codex pass CHANGED THE STATISTICS TWICE.**
- Pass 1 found a **CRITICAL**: the bootstrap resampled only the test side, while every rank in a
  window is computed against ONE realised calibration tail — so the intervals were too narrow and
  the p-values anti-conservative. Fixed by noting the rule fires iff `s_i > cal_desc[k]`, so a
  window's diagnostic depends on `C` through a single order statistic, and bootstrapping it
  (Poisson(1) multiplicities on `cal`'s order statistics), **shared across a window's strata**,
  crossed with the cluster bootstrap. Also fixed: the time strata were quantiled over unique bucket
  indices rather than flow counts (several windows had 2 populated strata of 8), and the
  "expected by chance" wording.
- Pass 1 also flagged that **BH is invalid** under this dependence. Switching to Benjamini–Yekutieli
  then exposed a second problem *we* found: a percentile-bootstrap p-value floors at `1/(B+1)`, and
  BY over ~500 tests needs thresholds an order of magnitude lower, so it returned **0 survivors for
  that reason alone** — a measurement of `B`, not of the evidence. Rebuilt: the bootstrap supplies
  the standard error, the tail is read from a log-scale normal approximation, and a cell firing
  **fewer than 10 times is not tested at all**.
- Final result, honest in both directions: **424 of 532 cells untestable**; of the 75 surviving BY,
  **none at k=1 lies at a guarantee window** (all five sit at 0.85, already a declared violation);
  but **22 stratum-vs-own-window contrasts survive at every window**, largest **9.32 [5.53, 15.51]
  in the arity bin `m=21–100`** — the exact component of `M_j` padding manipulates. Conclusion stays
  **under Assumption 1**; the diagnostic is explicitly not offered as support for it.

**R5 — codex pass 3** verified all four pass-2 fixes are real (family construction now
null-independent, weights genuinely global/paired, the calibration resample cluster-aware, the bucket
family what it claims) and confirmed the contrast rise 22 → 32 is the expected direction for fixing a
pairing bug. Two points remained, both taken: the k=1 "fails to reject" framing is now an explicit
**inconclusive non-rejection**, and the residual **time-block dependence** (a window's calibration
tail sits in 2–4 buckets, largest 46–74%) is stated next to the contrast claim with a sensitivity —
dropping the one family aligned with that confounder leaves **25 of 32**, still at all five windows.

**Reproducibility chain green:** `t45` **147 consistent, 0 inconsistent** (was 126; +21 assertions
for the key-hash arm, the t48/t53 agreement, and t55); notebook **64 cells, 0 errors**; `tectonic`
compile **0 undefined refs, 0 `??`, 0 overfull boxes**; 27 pp total, body ending on **p14**
(refit pending as R11).
