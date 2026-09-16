# Review 5 worklist — fifth round (deep audit of the round-4 fixes)

> **STATUS: ALL 17 ITEMS COMPLETE (2026-09-01), blind-codex-verified in 4 passes.** Paper + notebook
> (60 cells, 0 errors) + `docs/04` §4.54 + `t45` (126/0) all updated; compile clean (0 undefined refs,
> 0 `??`, 0 overfull boxes); **body re-trimmed to a stable 12 pages** (Conclusion ends p12 across 3
> fresh compiles; 25 pp total).
>
> **Two measured results REVERSED, both because the review identified a measurement artefact:**
> (i) the LSPR23 stress-window "grafted pads fire 0.43 → inconclusive-OOD" came from a pad pool that
> was 88% the attacker's own flood; with a genuinely black-box pool the graft fires **0** and the
> transfer **holds at both windows**. (ii) AIT Shaw's "0/3 suppressible, host conditioning defeats
> the attack" was a static-context artefact; under a **causal** context replay it is **3/3** at
> median 269. Codex additionally caught: a cap bug that reported successes beyond the evaluated
> accumulation range (fixed, `causal_n_capped == 0` now asserted); a transductive feature-selection
> leak in `t54` (now per-fold from training orgs); that the `M_j` repair is airtight **only** under a
> key-determined order; and five overclaims in the written text (keyed-hash strength, the breadth of
> the host-conditioning reversal, `c_0` used before definition, the JM number being finite-horizon,
> and a stale 11–68× that is really 13–71×).

Source: reviewer feedback pasted 2026-09-01 (text + two screenshots). Rule (unchanged): for each
solution, (a) implement, (b) blind-codex review, (c) edit paper + notebook. Page size deferred to the
very end. Workflow per [[blind-codex-review-workflow]]. Builds on `25_review4_worklist.md`.

## Validity triage (all 17 points VERIFIED against the source before starting)

| # | point | verdict | evidence |
|---|---|---|---|
| W1 | Prop 2 discussion: `max_t tγ_t = 0.0764` wrong for horizon-uniform | **VALID** | `0.0764 @ t=55` is the **Javanmard–Montanari** sequence (`t15_T3_theorem.py:g_jm`), which the paper never runs. The paper's two sequences are `j^-1.6` (0.4375 @ t=1 ✓) and horizon-uniform `1/T`, whose `max_t tγ_t = 1` at `t=T`. Verified numerically. |
| W2 | Assumption 1 conditional-probability hole (global `M` vs `M'`) | **VALID** | `main.tex:231-236,264-271`, `appendix_proofs.tex:9-11`. `E[e_i∣M]≤1` does **not** imply `E[e_i∣M']≤1` for a richer `M'`. |
| W3 | §V presents `kT/w_0−1` as *the* exchange rate though e-LOND's coefficient is `α=2w_0` | **VALID** | `main.tex:518` vs `cor:budget` (line 405) and abstract (line 77, already generic). |
| W4 | Thm 10 "exact" but per-precursor size is `⌊λM⌋+1` not `λM` | **VALID** | `λM = 0.25×1,813,114 = 453,278.5`; the reported **453,279** already *is* `⌊λM⌋+1`. Formula text is off by the rounding. |
| W5 | "finite resolution of **any** conformal procedure" too broad | **VALID** | contradicts §IV-D smoothing (`main.tex:499-500`), which removes the floor. `main.tex:197`. |
| W6 | Table XXIII "re-running the whole chain" but host features held fixed | **VALID** | `t54_ait_suppression.py` samples pads from a *pre-computed* `pad_e` pool; `H` is never recomputed after an append. |
| W7 | black-box pool is partly oracle-selected | **VALID** | `t48`: most common service among **benign-labelled** flows (uses labels). `t49`/`r7host.tex`: most common among **detector-non-firing** flows (uses detector output). Body claims "no detector access" only. |
| W8 | "0 firings in 20,000 ⇒ premise confirmed" | **VALID** | `w3dilution.tex:8` "confirmed, not assumed". 0/20,000 gives a 95% CP upper bound of 1.5e-4, not 0. |
| W9 | Table XIX untraceable vs XV/XVII | **VALID** | `units.tex` 34/227 are `t28_P5`'s `r_90` p50/p90 priced against the **static** `τ=T/w_0`, pooled over 0.62+0.85 × 2 seeds (257 like-for-like episodes); `4,998 = 34 × 147` mixes that with **ADDIS's** detected-set count. Nothing in the caption says so. |
| W10 | metadata-hash order removes the timing lever but not metadata grinding | **VALID** | threat model (`main.tex:310-316`) gives the attacker SrcIP/DstIP choice; a *public* deterministic hash of those is grindable. |
| W11 | Fig 4C says "FDP ≤ q (VALID)" | **VALID** | ADDIS controls FDR, not per-realisation FDP; `make_figures.py:239`. Table reports mean FDP `0.047`. |
| W12 | XXII "weak, inconsistent defence" vs XXIII Shaw 0/3 | **VALID** | `r7ait.tex` vs `aitsupp.tex`; 8.92% b→v is *decisive* for Shaw. |
| W13 | "at all eight organisations" hides Santos 8/9 | **VALID** | suppressible 13+10+14+8+3+9+15+12 = **84** of **85** detections. |
| W14 | C2 "must aggregate" no longer literally true | **VALID** | online e-BH escapes the mechanism; preallocated restart escapes the horizon keeping deployment-wide FDR. `main.tex:152-153, 571`. |
| W15 | Conclusion "paying in the guarantee's composition" | **VALID** | contradicts the round-4 preallocation result. `main.tex:1097`. |
| W16 | malicious-flow coverage "not a granularity effect" | **VALID** | `apptab:w7coverage`: 0.55 flow-cov 0.001→0.021 (5 m→1 d), 0.85 0.301→0.995. Not flat within a window. |
| W17 | x-ref/terminology sweep (4 sub-items) | **VALID** | (a) `main.tex:639` cap loss → `sec:method` (§VII, methodology) should be `sec:transfer` (§IX-C); (b) `main.tex:1123` AIT mapping → `sec:limitations` (§X-A) is Limitations, not preprocessing; (c) `restart.tex` caption "LOND" vs body "e-LOND" (`t35` really runs `run_lond`, which is decision-identical since `p=min(1,1/Ev)`); (d) "anti-conservatism is 0.86–2.03×" — 0.86 is *conservative*. |

---

## TIER 1 — theory / numerical correctness (codex-verify each)

- [x] **W1** Rewrite the `thm:family1` degree-condition paragraph (`main.tex:375-379`). Name the two
  sequences the numbers belong to; state the horizon-uniform case correctly (`max_t tγ_t = 1`, and
  `tγ_t` *increases*, so the `→0`/non-increasing hypotheses do not apply — the cold-start level
  `αγ_t(R+1)=α/T` is **constant** over the horizon, so feasibility is all-or-nothing and infeasibility
  is trivially absorbing).
- [x] **W2** Group-specific `M_j`. Replace the global `M` with a per-group σ-field (key, membership,
  arity `m_j`, position/index hence `γ_j`, horizon `T`); restate `assump:groupval` and `lem:groupval`;
  rewrite the padding-preservation paragraph so padding leaves **every true-null `M_j` literally
  unchanged**; sync `appendix_proofs.tex`. Fix "hence its offered level `α_j`" (`α_j` also depends on
  `R_{t-1}`, so it is *not* pre-committed) → "hence the spending weight `γ_j` it is offered".
- [x] **W3** Generic cold-start coefficient `c_0` in §V (`main.tex:518`) and anywhere else the rate is
  quoted as `kT/w_0−1` without qualification.
- [x] **W4** `thm:addis` / body: per-precursor group size `⌊λ(|C|+1)/k⌋+1` (=453,279 exactly).
- [x] **W5** `main.tex:197` "any conformal procedure" → "deterministic rank-based conformal evidence
  … (the unsmoothed construction considered here)".

## TIER 2 — experiments and measured claims

- [x] **W6** t54 **causal** host-context replay: recompute the six host features after each appended
  pad and re-score, so the Shaw host-conditioned result is a true causal replay. If infeasible,
  rename to "host-conditioned **static-context** replay diagnostic" and say so in the caption.
- [x] **W7** Make the black-box pool selection threat-model clean: choose the most common
  `(proto,dport)` over **all** window flows (no labels, no detector output) and verify it is the same
  service; harmonize the `r7host` description. Otherwise call it an *evaluation* pool.
- [x] **W8** `w3dilution.tex`: "0 observed firings in 20,000 (one-sided 95% upper bound 1.5×10⁻⁴)";
  drop "confirmed, not assumed".
- [x] **W9** `units.tex`: label every padding row with procedure, threshold type (running/static) and
  detected-set source; add the running-level e-LOND row so the table reconciles with `apptab:padpools`.
- [x] **W10** Reframe the hash canonical order: a **timing-independent canonicalization**, not a
  security solution (a public hash of attacker-chosen metadata is grindable); recommend a
  **pre-committed keyed hash / secret seed** as the adversary-resistant variant, with its extra
  threat-model assumption stated.
- [x] **W11** Fig 4C annotation → "all 120 silenced; mean FDP = 0.047 ≤ q".
- [x] **W12** Harmonize `r7ait.tex` ↔ `aitsupp.tex`: host conditioning is *usually* weak here but can
  be **decisive on an individual organisation**.
- [x] **W13** "84/85 detections suppressible across all eight organisations".

## TIER 3 — rhetoric

- [x] **W14** Drop "must aggregate" (intro `main.tex:152-153`, §VI opener `571`) for the abstract's own
  formulation: under uninterrupted deployment-wide control for the covered families, aggregation is a
  **direct route** to feasibility.
- [x] **W15** Conclusion: preallocated restart preserves deployment-wide FDR and pays in **power**;
  budget reset pays in the guarantee's composition.
- [x] **W16** Malicious-flow coverage: **not** "not a granularity effect" — it is not a clean
  denominator-invariant measure of resolution cost, being dominated by the traffic mass of whichever
  episodes fire and varying with both window and bucket. Fix `main.tex:154,542-546` + fig3 caption.

## TIER 4 — presentation

- [x] **W17** (a) `main.tex:639` cap detection loss → `\cref{sec:transfer,app:attacks}`;
  (b) Open Science AIT mapping → add an AIT paragraph to `app:data` and point there;
  (c) `restart.tex` caption → e-LOND (note LOND-identical); (d) "measured/nominal ratio 0.86–2.03×".

## Consistency gate
Rebuild notebook, regenerate appendix tables + figures, recompile clean, rerun `t45`, then page size.
