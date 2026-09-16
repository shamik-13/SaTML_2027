# Review 3 worklist — statistical/reviewer feedback (19 items)

> **STATUS: ALL 19 COMPLETE (2026-08-31), each blind-codex-verified.** Paper + notebook + docs
> updated; body re-trimmed to 12 pages (Conclusion ends p12, Open Science p13; 23 pp total; 0
> undefined refs, 0 ??; notebook 60 cells / 30 code all execute). New stages t52 (synthetic-valid
> ADDIS), t53 (ordering-sensitivity), t54 (AIT full suppression); t50→Clopper–Pearson. See
> docs/04 §4.49–4.52 and memory `review3-worklist-outcome`. Two findings changed conclusions:
> item 2 ordering is a MATERIAL sensitivity (0–18/0–72; first-flow is generous) not a robustness
> confirmation; item 4's first attempt was invalid (two-point nulls not uniformly conservative) and
> was rewritten with Uniform(0,1) nulls + state-poisoning framing.


Source: reviewer feedback pasted 2026-08-31 (paste-cache/e6b20eb000cfa4df.txt).
Rule: for each solution, (a) implement, (b) blind-codex review the code/theory/edit, (c) edit
paper + notebook. Page size deferred to the very end. Do NOT strengthen a claim without an
experiment; may only weaken.

Workflow per [[blind-codex-review-workflow]]:
`codex exec -s read-only --skip-git-repo-check -C <repo> - < prompt.md`

## Investigation notes (done before worklist)
- **Assumption 1** already exists (`main.tex:213-220`, `assump:groupval`). Uses conditional
  e-value property `E[e_i|F_{i-1}]<=1`. Reviewer: e-LOND needs only group-level MARGINAL
  e-validity; conditional is both wrong-for-e-LOND and not supplied by split conformal; random
  membership + random m unhandled.
- **Ordering** (`h_stream.build_episodes`, line 145-182): `order=lexsort((first_pos,first_ts))`.
  Bucket index ∈ group key ⇒ buckets partition time ⇒ this already orders bucket-by-bucket, then
  within-bucket by first-flow arrival (metadata, evidence-independent). `Ev` uses whole group
  (bucket-close). So NO cross-bucket look-ahead; within-bucket order is a valid pre-committed
  tie-break. Needs: explicit methodology + robustness rerun over ALTERNATIVE within-bucket orders.
- **Restart counterexample** (`appendix_proofs.tex:128-138`): wording "each epoch rejects exactly
  one hypothesis, false w.p. q → FDR=1-(1-q)^n" is WRONG (that gives pooled FDR=q). Correct
  construction: each epoch makes ONE false rejection w.p. q, else NONE. Body number 0.185 stays.
- **ADDIS state attack** mechanism in `t32_B1_addis_state.py` (uses `h6_procs.run_addis`, `Ctx`).
  Synthetic valid-null version is a new script (t52).
- **Poisson CI** `t50_calib_ci.py` uses Garwood Poisson. Swap → Clopper-Pearson binomial. Numbers
  ~unchanged (p tiny, n huge). Fix "exact Poisson" wording in body + tail.tex.
- **Table X** = `tables/w7coverage.tex` (apptab:w7coverage): caption "†infeasible bucket (no alerts
  issued)" but daggered 5m/30m/1h rows show non-zero cov/blur/recall. `tables/grouping.tex`
  (apptab:grouping) ALREADY has the corrected dagger text (Table VII style) — copy it.
- **Ref [26]** = `farzaneh2025coad` (refs.bib:67): title missing "Context-Aware". `gao2026boundary`
  (refs.bib:74) needs explicit contrast in Related Work.
- **LLM section** (main.tex:1119-1143) has a paraphrase, not the verbatim 2027 sentence; missing
  compute/responsibility paragraph. "pre-registered" appears at main.tex:906, 1122; change to
  "frozen before manuscript drafting" (no timestamped prereg predating analysis; docs/03 is a
  drafting-time freeze).

---

## TIER 1 — substantive technical (experiments/theory)

- [ ] **W1 (item 1) — Group-evidence validity.** MOST IMPORTANT. Reformulate `assump:groupval`:
  (a) state the validity requirement procedure-by-procedure; for e-LOND it is group-level MARGINAL
  e-validity `E[E(G_j)]<=1`, arbitrary between-group dependence; (b) a lemma giving sufficient
  conditions under which the metadata-defined random group (random membership, random m) yields
  such a group e-value; (c) separate this from calibration-conditional validity — recast Bates
  (Table XXVI) as testing a STRONGER conditional guarantee, not repairing e-LOND's requirement.
  If the marginal property can't be proved for the construction, present empirical FDR as
  conditional on an explicit group-validity assumption. Codex-review the lemma. Edit main.tex
  §II-B + §methodology + notebook.

- [ ] **W2 (item 2) — Causal grouped-hypothesis stream.** Add methodology: hypothesis emitted at
  bucket close; group evidence uses only decision-time observations; same-close-time groups in a
  pre-committed evidence-independent order (state it: first-flow arrival). Run robustness: headline
  detections under ≥2 alternative within-bucket orders (e.g. by gid, by hashed key). New stage
  (t53) reusing `build_episodes(tie_key=...)`. Codex-review the causality argument (subtle).

- [ ] **W3 (item 3) — Restart FDR counterexample.** Fix `appendix_proofs.tex` construction + any
  body wording (`main.tex:463`). Codex-review the corrected math.

- [ ] **W4 (item 4) — Synthetic guarantee-valid ADDIS state attack (t52).** Stream with
  conservative-null p-values (ADDIS assumptions hold ⇒ genuine FDR validity), attacker precursors
  p∈(λ,τ], inject B*(Thm 9); show target detectable→permanently silent at B*. Establishes the
  state attack is not an artefact of the 0.85 null-consistency violation. Codex-review.

- [ ] **W5 (item 5) — Full Surface A pipeline on AIT (extend t51).** episode→group e-value→e-LOND
  level→padded group→suppression cost, on ≥1 of the 8 orgs. If runnable, report end-to-end
  suppression; else weaken claim to "pad-scoring premise transfers; full controller suppression not
  re-estimated on AIT." Codex-review.

- [ ] **W6 (item 15b) — Clopper-Pearson.** Replace Poisson with exact binomial (Clopper-Pearson)
  in `t50_calib_ci.py`; propagate to tail.tex + body wording. Codex-review the swap.

## TIER 2 — framing tied to technical results

- [ ] **W7 (item 6) — Higher-AUROC host detector.** Rename "more accurate/competent" →
  "higher-AUROC"; report AUROC + tail reach + #e-LOND detections + episode recall together; use the
  better-AUROC-worse-alerting fact to reinforce C1. If a valid config yields more host detections,
  repeat suppression there. (Depends on W1/W5 wording.)

- [ ] **W8 (item 7) — "Valid window" consistency.** Abstract "at a valid window", Table I (tab:main)
  "valid" labels, Table II (tab:frontier) "is a valid e-value", intro "measures exactly" → one
  consistent phrase ("primary guarantee-analysis window under Assumption 1; tail counts compatible
  with nominal calibration"); §IX-A "measures exactly" → "measures one marginal implication".

- [ ] **W9 (item 8) — Table X dagger.** `w7coverage.tex` caption → grouping.tex/Table VII dagger
  definition (negative level-w0 margin; e-LOND fires when margin > -1/2). Verify dagger assignment
  in make_appendix_tables.

- [ ] **W10 (item 9) — Oracle frontier.** Call it "ex-post oracle score frontier"; weaken to "the
  score ranking contains substantial headroom relative to the controller's operating point."
  (Optional: prospective fixed-threshold-on-previous-window baseline.)

- [ ] **W11 (item 10) — Black-box vs minimal r*.** Distinguish black-box pad CONSTRUCTION (no
  detector access) from ORACLE minimal r* (uses realised evidence/level ⇒ lower bound). Add a
  grey-box uncertainty statement for Surface A (fixed budget under ±X% t / unknown fired count).

- [ ] **W12 (item 11) — Cold-start prevalence.** Reframe: absorbing thm conditional on
  rejection-free prefix; a pre-deadline null rejection could bootstrap. New statement: at prevalence
  1e-4 a true discovery is unlikely to bootstrap before the deadline, so survival needs an early
  null rejection or external reset. Optional: quantify P(null rejection before t*).

## TIER 3 — writing/presentation

- [ ] **W13 (item 12) — Figure 4 rebuild.** Main Surface A panel at 0.55/0.62; 0.85 → inset/appendix;
  add synthetic valid-ADDIS beside Surface B. Depends on W4. (make_figures.py)
- [ ] **W14 (item 13) — Host/AIT into body** (§VI-C or VII), compact: boundary test → primary → AIT
  → flood boundary. Move Tables XX/XXI prominence.
- [ ] **W15 (item 14) — Related work.** Explicit Gao–Roquain–Xiang contrast (batch/global BH
  boundary + calibration/test imbalance vs our online wealth dynamics/cold-start/grouping/state).
  Fix `farzaneh2025coad` title → add "Context-Aware" (verify against arXiv).
- [ ] **W16 (item 16) — Scope language.** "calibration drift…measured and refuted" → nuanced
  4-windows/0.85 split; "better detector wouldn't help" → the actual theorem (detector quality can't
  change C1 margin (C,k,T-only); can change power).
- [ ] **W17 (item 17) — Abstract/intro softening.** "Making the layer operational forces
  aggregation" → "Under uninterrupted deployment-wide control, reducing the hypothesis count through
  aggregation is a direct route to feasibility"; "literature establishes this layer is valid" →
  constituent-procedures-valid / composition-raises-separate-questions.
- [ ] **W18 (item 18) — Open Science.** Now depends on AIT-LDSv2.0: both datasets, records/licenses,
  exact preprocessing for both; anonymised repo available shortly after submission, frozen through
  review.
- [ ] **W19 (item 19) — LLM section.** Add verbatim: "LLMs were used for editorial purposes in this
  manuscript, and all outputs were inspected by the authors to ensure accuracy and originality." +
  3-5 sentences compute/responsibility (why needed, model-size, query-volume minimisation,
  hardware/environmental). "pre-registered" → "frozen before manuscript drafting" (also main.tex:906).
- [ ] **W20 (item 15a) — Draft artifacts.** Kill any `??` refs to Assumption 1; "section E/F" →
  proper appendix refs; define or remove internal IDs (R7, E6a, E6b) in reader-facing text.

## Consistency gate
After all edits: rebuild notebook (build_notebook.py), regenerate appendix tables, run t45
consistency, recompile, then handle page size (Tier 4, separate).
