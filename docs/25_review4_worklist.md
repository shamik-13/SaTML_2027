# Review 4 worklist — deep re-review of the round-3 fixes (12 items)

> **STATUS: ALL COMPLETE (2026-09-01), blind-codex-verified in 3 passes.** Paper + notebook + docs +
> t45 record-consistency (126/0) all updated; compile clean (0 undefined refs, 0 `??` in PDF).
> Codex caught, and we fixed, four substantive issues beyond the reviewer's list: (i) t52 B* is a
> DISTRIBUTION (median 140, tail to 255), not a seed-robust constant; (ii) t54 santos 212<319 was a
> survivorship artifact — closed-form now computed over the same suppressible set (closed ≤ emp);
> (iii) t54 host-shaw "unsuppressible" reworded to "0/600 draws within budget" + hedged (not a general
> defence, host features held fixed); (iv) replay is an empirical i.i.d. generator, pads pooled over
> the org's attacked victims. Ordering: hash canonical is now primary, first-flow = upper bound over
> the audited set, padding cost is survivorship-conditioned (~100 flows). New t54 finding: host
> conditioning DEFEATS the padding attack on Shaw (7% pad fire).


Source: reviewer feedback pasted 2026-09-01 (a second-pass audit of the round-3 changes).
Rule (unchanged): for each solution, (a) implement, (b) blind-codex review the code/theory/edit,
(c) edit paper + notebook. Page size deferred to the very end. May only weaken a claim without a
new experiment. Workflow per [[blind-codex-review-workflow]].

## Investigation notes (verified before starting)
- **`??` (item 12):** current source compiles CLEAN under tectonic (0 undefined refs). Root cause of
  the reviewer's 8 `??`: `cleveref` (main.tex:23) is loaded before `\newtheorem{assumption/lemma}`
  (25-30); under pdflatex the custom theorem envs have no registered cref name → `??`. Defensive fix:
  explicit `\crefname{assumption}{Assumption}{Assumptions}` + lemma/theorem/... after the newtheorem
  block. Only 3 `\cref` target assump/lem (lines 6, 452, 819).
- **t54 & t51 ARE chronological** (t54: benign-before-first-attack split; t51: first 35% by sorted ts).
  Item 11 = state it explicitly; no rerun of the split needed. BUT item 5a (empirical replay) and 5b
  (host end-to-end) DO need reruns.
- **Abstract formula (item 6):** only the ABSTRACT (main.tex:68) uses bare `kT/w_0-1`; the intro C1
  (line 132) already has the nuanced `k/α_T-1 (kT/w_0 for LORD++, kT/α for LOND/e-LOND)`. Fix abstract.
- **t52 (item 1):** `run_front` injects precursors as NULLS (`np.zeros(B,bool)`) with p∈(λ,τ] — the
  exact assumption violation. Fix = relabel as ALTERNATIVES; ADDIS sees only p-values so the run is
  identical, only the validity CLAIM becomes sound.

---

## TIER 1 — substantive (experiments/theory), codex-review each

- [ ] **V1 (item 1) — t52 precursors are ALTERNATIVES, not nulls.** BIGGEST. Relabel injected
  precursors non-null (p∈(λ,τ] allowed for alternatives); true nulls stay U(0,1) ⇒ ADDIS assumption &
  guarantee genuinely hold on the ATTACKED stream. Rerun (numbers unchanged: ADDIS sees only p). Rewrite
  Fig 4C + tables/addissynth.tex + §state to say "guarantee holds on the attacked stream."
- [ ] **V2 (item 3) — make a metadata-hash/random precommitted order PRIMARY.** first-flow is the max
  and is attacker-influenceable (timing lever). Rework t53: ~50 fixed hash/random seeds → median/IQR/
  range at 0.55 & 0.85; first-flow = optimistic upper bound. Decide downstream re-run scope with codex
  (headline padding/frontier conditioned on favourable order). Remove timing lever from canonical impl.
- [ ] **V3 (item 4) — restart: two designs, not one loss.** Distinguish budget-reset (spends nq, more
  power, changes guarantee) from PREALLOCATED index-reset (Σqᵢ≤q ⇒ FDR_global ≤ ΣFDRᵢ ≤ q preserved,
  less power). Add FDP_global ≤ Σ FDP_i inequality (appendix + body). E2b is the preallocated escape.
  Reframe body + Discussion + Table XII. Strengthens C2.
- [ ] **V4 (item 5a) — t54 empirical pad replay.** Replace closed-form r* (`floor(S·lvl)-m+1`, assumes
  zero-evidence pads) with actual replay of real ordinary-to-victim flows carrying their real 0-or-M
  evidence, appended until Ev(G)<1/lvl; report empirical min/median cost + success rate over draws.
  Rewrite tables/aitsupp.tex caption (drop "valid zero-evidence pad").
- [ ] **V5 (item 5b) — t54 host-conditioned end-to-end (Shaw + one typical org).** t54 uses flow-only;
  run the full chain with host-conditioned detector (X_aug=[flow|host], t51 builds H) at least for
  Shaw (0.05%→8.92% b2v). Else narrow claim to "end-to-end for flow detector; host boundary separately
  measured."

## TIER 2 — theory/wording tied to results, codex-review the theory ones

- [ ] **V6 (item 2) — Assumption 1 / M + false-null padding argument.** Put the precommitted
  ordering/tie-break rule into M. Replace "padding changes only the arity m_j, not Assumption 1" (M
  DOES include arity) with the stronger argument: the attacked episode is a FALSE null, and e-LOND
  imposes e-validity only on TRUE-null groups, so manipulating a non-null group's composition doesn't
  invalidate the premise for the remaining true nulls. Replace "where the guarantee holds" → "at a
  guarantee-analysis window under Assumption 1" (main.tex:147, 549; addissynth.tex:15). Keep the
  benign-tail caveat (marginal implication only).
- [ ] **V7 (item 6) — abstract formula generic c.** |C| ≥ kT/c − 1 with cold-start coefficient c;
  6.5e8 for level-w0 procedures, 3.3e8 for LOND/e-LOND. (main.tex:68.)
- [ ] **V8 (item 7) — Table III last column.** Rename "valid" → "nominal guarantee / required
  assumptions", per-procedure (e-LOND → "FDR under group e-validity"; LORD++ → "conditional/indep.
  assumptions"; ADDIS → "uniformly conservative nulls, violated here"). (tables/detection.tex.)
- [ ] **V9 (item 8) — Prop 2 e-GAI/e-SAFFRON(λ=0.1) audit.** Appendix only proves e-SAFFRON(λ=0)=
  e-LORD; experiment uses λ=0.1. Either show the λ=0.1 level satisfies the multiplicative-family bound
  or narrow the theorem-coverage wording to proved members. Codex-review the proof.

## TIER 3 — writing/presentation

- [ ] **V10 (item 9) — "silent" definition (Table IV, 90.1%).** Not "fraction never rejects" (that's
  99.97%). Define exactly (fraction of steps structurally infeasible / after last feasible index).
  Fix tables/detection.tex caption + main.tex:478.
- [ ] **V11 (item 10) — victim-transfer claim.** Replace "scores identically wherever sent"
  (main.tex:651) with "endpoint identity itself cannot affect the score; response-dependent transfer
  is tested empirically (AIT)."
- [ ] **V12 (item 11) — AIT chronology sentence.** State that within each held-out org the calibration
  flows strictly precede the evaluated deployment flows (true in t51/t54). §sec:transfer / methodology.
- [ ] **V13 (item 12) — presentation.** (a) `\crefname` fix for pdflatex `??`. (b) stale "section E/F"
  → proper appendix refs. (c) §IX-A "external NetFlow corpus" 0.86–2.03×: identify/cite or remove
  (main.tex:899, r7ait.tex:24). (d) harmonize Surface-B cost: 36× precursor count (main.tex:740) vs
  ~54× emitted flows (main.tex:303) — distinguish explicitly.

## Consistency gate
Rebuild notebook, regenerate appendix tables, recompile clean (crefname → 0 ?? in pdflatex too), then
page size.
