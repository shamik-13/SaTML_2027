# Phase 4 Handoff — Reviewer-Gap Closure

**You are picking up an in-progress research project at the last experimental phase before the
paper is written.** Read §1–§6 before touching anything. §7 is the audit procedure and it is
mandatory. Your task list is **`02_WORKPLAN_PHASE4.md`**, not this file.

Written 26 Aug 2026. Target IEEE SaTML 2027: abstract **22 Sep**, paper **29 Sep**, internal
gate **experiments complete by 15 Sep**.

---

# 0. Read this first, and read nothing else until you have

`docs/` holds 20 markdown files — see `00_README.md` for the map — and **most of them are superseded**. Reading them in the
wrong order will make you act on a framing that has already been retired twice.

| Read | File | Why |
|---|---|---|
| **1st** | this file | environment, established results, mistakes, procedure |
| **2nd** | `02_WORKPLAN_PHASE4.md` | **your task list.** Twelve experiments, E1–E12 |
| **3rd** | `03_FROZEN_CLAIMS.md` | what may be claimed and at what strength. E1 and E12 have landed; H1 is open to E2 and H3(a) to E3 |
| **as needed** | `04_EXPERIMENTS_AND_FINDINGS.md` | the authoritative record, ~200 KB. §1 is findings F1–F24; the experiments run to §4.42. **Grep it, don't read it end to end** |
| for context | `05_PAPER_CONTRACT.md` | title, thesis, contributions, figures. Do not draft against it yet |
| for context | `06_PHASE3_REPORT.md` | what the previous phase closed, and its self-identified gaps |

**Do not act on these — they are inputs that have already been processed:**

| File | Status |
|---|---|
| `07_phase3_next_step_recommendation.md` | **Says "start writing the manuscript now". That was overruled** — the decision is experiments first. Its *claim-framing* decisions were adopted and are in §5 below |
| `08_satml_reviewer_gap_experiment_checklist.md` | The source of E1–E12. Already digested into `02_WORKPLAN_PHASE4.md`, with three corrections. Read the checklist only if you need an experiment's original motivation |
| `10_HANDOFF_PHASE2.md` | §5's task list is history. §1–§4 and §6–§7 are still accurate and are folded into this file |
| `11_next_actions_updated_experiments.md`, `09_WORKPLAN_phases1-3.md`, `12_review_experiments_and_next_actions.md`, `13_PLAN_v3.md`, `14_NOVEL_CONTRIBUTION.md`, `15_PROTOTYPE_FINDINGS.md`, `17_FEEDBACK_ON_ORIGINAL_PROPOSAL.md`, `16_detailed_feedback_revised_fdr_ids_project.md`, `18_`/`19_fdr_trustworthy_ids_research_idea*.md` | Historical. Read only to answer "why was this decided". `09_WORKPLAN_phases1-3.md` §14 explicitly points here |

---

# 1. What the project is

We test whether **online false-discovery-rate control** can make ML intrusion-detection alerting
trustworthy. The answer so far is largely no, for reasons that are now proved and measured.

Pipeline under test: a detector scores each network flow → the score becomes a **conformal
e-value** against a benign calibration set → flows are grouped into **episodes** → an online
procedure decides which episodes to alert on.

The paper has three contributions: a **feasibility theorem** with its boundary, the
**granularity–feasibility tradeoff**, and the **statistical trust layer as an attack surface**
(within-hypothesis padding, and across-hypothesis controller state).

**Do not re-litigate the framing.** It went through four rounds of external review and two
repositionings.

---

# 2. Environment

```
Project root : /Users/shamik/Work/others/SaTML
Code         : proto/*.py                (55 scripts, t1…t40; naming is chronological)
Outputs      : proto/out/*.json + *.log
Python       : proto/.venv/bin/python    numpy 2.5.2, pandas 3.0.5, sklearn 1.9.0,
                                         scipy 1.18.1, matplotlib 3.11.1, Python 3.14
Audit tool   : ~/.local/bin/codex        (codex-cli 0.142.3)
```

**Always run scripts from `proto/`** — several open `out/…json` by relative path.

## 2.1 Shared modules — use these, do not re-implement

| Module | Provides | Tested by |
|---|---|---|
| `h_stream.py` | split indices, detector fitting, window scoring, conformal e-values, episode grouping, oracle frontier | `t22a_stream_selftest.py`, against §4.17/§4.19/§4.20 |
| `h6_procs.py` | LOND, LORD++, SAFFRON, ADDIS, online e-BH, e-GAI family, spending sequences | `t21b_h6_selftest.py`, against literal transcriptions of the published formulas |
| `h_meta.py` | the raw csv's annotation columns (IPs, ports, service, conn state, segment, per-endpoint labels) re-ordered into `h_stream`'s row order | `verify()` checks alignment on **all 16,353,511 rows** |
| `t33_selftest_A1A2B1.py` | 40 assertions over the A1/A2/B1 machinery | run it after any edit to those |
| `t34b_E1_selftest.py` | the E1 machinery: merges, conformal ranks, calibrator, e-BH entry times. Verified against 20 deliberate mutations | run it after any edit to `t34*` or `h6_procs` |

Re-implementing the stream construction is how tie-breaks and off-by-ones diverge. It has
happened. Use the modules.

## 2.2 Data

| What | Where | Size |
|---|---|---|
| LSPR23 raw flows | `proto/data/lspr23/ls23pr_v1.csv` | 10.6 GB, 16,353,511 rows, 101 cols |
| Red-team task record (external ground truth) | `proto/data/lspr23_attacknarratives.json` | 9.7 MB, 288 narratives |
| AIT NetFlows | `proto/data/nf_wilson/` | 313 MB |
| **Derived: features** | `/tmp/lspr_full.csv` | 4.4 GB |
| **Derived: 50%-benign features** | `/tmp/lspr_feat.csv` | 2.4 GB |
| **Derived: ports** | `/tmp/lspr_ports.csv` | 153 MB |
| **Derived: annotation columns** | `/tmp/lspr_meta.csv` | 1.1 GB |
| **Derived: npy caches** | `/tmp/lspr_cache/`, `/tmp/lspr_meta_cache/` | 2.6 GB + 812 MB |

All six derived artefacts were present and valid at handoff. **They will vanish if `/tmp` is
cleared.** Regeneration, from `proto/data/lspr23/`, ~4 min each:

```bash
# features -> /tmp/lspr_full.csv
awk -F',' 'NR>1 {
   printf "%s,%s,%s,%s,%s", $7,$2,$3,$95,$6
   for(i=9;i<=40;i++){ v=$i; if(v==""||v=="NaN"||v=="Infinity"||v=="-Infinity") v=0; printf ",%s", v }
   printf "\n" }' ls23pr_v1.csv > /tmp/lspr_full.csv

# ports -> /tmp/lspr_ports.csv
awk -F',' 'NR>1 {print $4","$5}' ls23pr_v1.csv > /tmp/lspr_ports.csv

# annotation columns -> /tmp/lspr_meta.csv
awk -F',' 'NR>1 {print $2","$3","$4","$5","$89","$91","$92","$93","$94","$96","$97","$98","$99}' \
    ls23pr_v1.csv > /tmp/lspr_meta.csv
```
`lspr_full.csv` columns: `ts, src, dst, label, proto, f0…f31`; `ts` is **microseconds**. Add
`if($95!=1 && rand()>0.5) next` after `NR>1` for the 50%-benign variant. The `.npy` caches rebuild
themselves from these on first use.

## 2.3 Dataset facts you need

- 16,353,511 flows; 1,644,599 malicious (10.06%); span 161.5 h.
- **7,381,261 rows are out of timestamp order.** Always sort by `ts` first — `h_stream` does.
- **90% of flows fall in the final 25.6 h.** Row-index splits give short *time* windows: the
  deployment window at position 0.85 spans only **2.4 h**. This is why §4.14 measures feedback
  latency in *alerts*, and why E7 needs a scoping decision.
- **There is no flow→campaign ground truth.** `Category`, `Severity`, `SigID`, `Expoid_dst` are
  empty for 1,630,732 of 1,644,599 malicious flows. Say **episode**, never *incident*.
- The 288 narratives **cannot** be joined to individual flows, so they cannot supply campaign
  labels — but 83 carry a machine-readable compromise report (hostname, IPs, timestamp) over 39
  IPv4 addresses, and 295 carry step-submission times. §4.32 joins them on **host IP and time**.
- Attack prevalence by decile: 0.0097, 0.0085, 0.0033, 0.0033, 0.0033, 0.0652, 0.2558, 0.4688,
  0.5532, 0.4564. Detector quality is very sensitive to how much ramp-up lands in training.
- `Label == (Label_src == 1 or Label_dst == 1)` holds exactly, so the per-endpoint labels are a
  **decomposition** of the audited label, not an independent source.

## 2.4 Runtimes, for planning

`t33` self-test ~2 s · `t31` (one detector fit) ~30 s · `t30` (10 fits + forensics) ~190 s ·
`t32` (~3,700 ADDIS runs) ~235 s · `t22`-class (5 positions × 2 seeds) ~470 s. A single
`HistGradientBoosting` fit plus window scoring is ~25 s. Budget accordingly: sweeps over
positions × seeds × parameters get expensive fast, and the detector fit is almost always the
bottleneck, not the procedure.

---

# 3. Established results — do not contradict without evidence

Full detail in `04_EXPERIMENTS_AND_FINDINGS.md` §1 (F1–F24) and §4.1–§4.42. The load-bearing ones:

- **F1/F2 (§4.13, §4.20)** — procedures whose spending index advances on **every** hypothesis
  have a finite feasibility horizon and an absorbing rejection-free state: LOND, LORD++, e-LOND,
  e-GAI. Retaining feasibility over horizon `T` needs `|C| ≥ kT/w₀ − 1`. **Two families escape**:
  ADDIS (its index counts *tested* hypotheses, and threshold conformal evidence never produces
  one) and online e-BH (its threshold is a fixed point over the whole history). Each escape has a
  measured price.
- **F5 (§4.15, §4.22)** — feasibility is necessary, not sufficient. The margin is
  `CEIL·w₀/T − 1` and depends only on `|C|`, `k`, `T` — **never on the scores**. A second,
  unsupervised detector gives an identical margin to every digit and **zero** detections.
- **F7 (§4.16)** — for any τ > 1, no symmetric e-merging family that *attains* τ is
  τ-padding-robust. The attainment condition is required. **The escape is asymmetry, already
  proved and priced** — see §4.12 policy D before touching E3.
- **F9 (§4.31)** — drift is mild (median 1.94×). Position 0.85's 50.9× anti-conservatism is a
  **localised** anomaly: three host pairs of 25,864 carry 44 of 46 firings. Best explained by
  post-compromise label error; **not proved**, and E5 cannot upgrade it to proof.
- **F10/F11 (§4.3, §4.26)** — conditional validity fails with probability exactly 1/e at k = 1,
  independent of `|C|`. The Bates fix works and costs 38–78% of the ceiling at k = 1.
- **F14 (§4.23)** — **k = 1 is the only feasible rank and the least reliable one.** Margin
  +0.436 → −0.999 as k goes 1 → 1000, zero rejections at every k ≥ 10.
- **F15 (§4.28)** — boosting is *exactly* vacuous: `b* = 1` for any two-point e-value. The
  evidence is already extremal. **This mechanism is why E1 is likely to come out the way it
  does** — read §4.28 before writing E1.
- **F17 (§4.33)** — ADDIS's escape is itself an attack surface. `B* = 203` precursors silence it
  permanently; for 101 of its 147 detections the cheapest suppressing pad *also* advances the
  index.
- **Refuted, do not revive:** calibration drift catastrophically invalidating the evidence;
  inflation and fragmentation as attacks; boosting as power recovery; mem-e-LORD helping before
  the first rejection; raising k to trade power for reliability; Mondrian conformal repairing the
  0.85 anomaly.

## 3.1 Verification tags — keep using them

`[EXACT]` analytic · `[SIM]` synthetic · `[REAL]` measured on real data · `[PRIOR]` published
elsewhere, cite don't claim · `[ORACLE]` uses information a deployment would not have ·
`[OPEN]` not done.

---

# 4. Mistakes already made — do not repeat these

**Nine independent blind audits have found roughly sixty-one defects. Three had inverted or
rescaled a headline number.** Every one of the following was found in review, not in writing.

1. **Gradient boosting with ~0.6% positives and `l2_regularization=0` explodes.** Leaf values
   reach ±10⁶ instead of ±17 and destroy tail ranking; median attack rank went 3rd → 104th and
   the k = 1 firing rate 48.9% → 0%. **Always use
   `HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, l2_regularization=1.0, min_samples_leaf=200, early_stopping=False)`** — `h_stream.fit_detector` does.
2. **Quantile grids are too coarse in the upper tail.** Use exact order statistics
   `cal[int(u*(NC-1))]`, not a grid over `u`.
3. **Randomised rules reported from a single draw.** Report the exact expectation with a
   Monte-Carlo interval. **This matters directly for E1**, which is a randomised procedure: ≥100
   seeds, and report variance, not just a mean.
4. **Parameters set from the evaluation split.** Derive from training/calibration, or label
   `[ORACLE]`. **E6 existed because of this, and is now done: §4.38 / F22.**
5. **Unstable sorts.** `np.argsort` breaks ties arbitrarily and moves the online rejection
   sequence. Use `np.lexsort`. **E9 quantified what this suppresses: nothing measurable
   (§4.41 / F24). `build_episodes` now takes an additive `tie_key` for that measurement;
   `tie_key=None` is the record's order.**
6. **Vacuity in a theorem statement.** Any "no X can do Y" claim needs a non-triviality
   condition — the padding theorem was initially false because `F ≡ 1` satisfied it vacuously.
7. **Seeds that don't enter the quantity being varied.** A planned six-config "distribution" of
   feasibility margins was three deterministic values duplicated. Check what your seed perturbs.
8. **Single-split, single-seed numbers reported as results.** Report intervals.
9. **Aggregation validity checked on the typical group, not every group.** `Σe/n₀` is valid only
   for `m ≤ n₀`; at a p99 cap 1% of groups violated it — and held 86.2% of all flows.
10. **A conditional rate divided by the wrong denominator.** `((e > 0) & benign).mean()` divides
    by *all* test flows. Write `e[benign] > 0`. This rescaled every number in an A1 table.
11. **Corroborating evidence computed from the thing being corroborated.** Subtracting an
    episode's own contribution removes self-corroboration; it does not make the indicator
    independent of the labelling process. Separate the tiers and let the weakest, genuinely
    external one carry the claim.
12. **An episode's own flows leaking in through a boundary bucket.** The grouping key is
    `(src, dst, time bucket)` and the split indices cut through buckets, so same-episode flows sit
    outside the window. Any "elsewhere in the stream" statistic must subtract the whole global
    group.
13. **A statistical test with no power reported as a pass.** A validity check on three
    calibration draws saw 6 events against an expected 3 and "failed" — pure Poisson noise. Size
    the check before believing either outcome.
14. **A `(service, dport)` key that aliased a missing port (−1) with port 0.** Shift, don't clip.
15. **A unit test that tests a copy of the code, not the code.** E1's first self-test checked
    copied algebra plus "does the source still contain this string"; an audit defeated it by
    moving the searched text into a comment and breaking the real function. Helpers that matter
    must be **module-level** and imported by the test, and the test must itself be verified by
    deliberately mutating the code and confirming it fails. E1's is checked against 20 mutations.
16. **A statistical gate that cannot fire, or fires on correct code.** E1's derivation check
    standardised a Pearson statistic by `sqrt(2·df)`, which is wrong when `n·p < 1` and would
    have blocked a *correct* result. Cells with `0 < p < 1` but tiny variance enter neither a
    z-test nor a deterministic check, so errors there are invisible and cancel in a signed pool.
17. **A tolerance so wide the check has no power.** A 5-sigma binomial tolerance with a `1/n`
    floor accepts a closed form wrong by a **factor of two** when the probability is small. Gate
    on *relative* tolerance and declare low-power cells inconclusive, never passing.

18. **A window borrowed from a different `|C|` regime.** E8 priced the 92,015,637-flow ADDIS
    state attack — computed at `|C|+1 = 1,813,114`, position 0.85 — over §4.35's 26.98 h
    long-span window, which is taken at split 0.05 where `|C| ≈ 406,870`. The required rate came
    out **elevenfold too low**. Every rate needs its window stated, and the window has to belong
    to the same split as the numerator.

19. **A default tolerance wider than the scale being resolved.** `np.isclose(x, 0.25)` has a
    tolerance of 2.5×10⁻⁶; the conformal floor it was being asked to resolve is 5.5×10⁻⁷ (E11).
    And `np.std(ddof=1)` over 50 bitwise-identical float64 values is ~10⁻¹⁷, not 0, so `sd > 0`
    reported four E9 statistics as varying when none did. For "are these the same", compare
    exactly or count distinct values; never inherit a library default.

20. **A null result with no power check.** E9's answer is "50 randomised orders change nothing".
    That is only a result if the randomisation moved something — verified by counting the
    episode positions each draw actually changes (324 of 651 movable). A seed that perturbs
    nothing produces the same table.

21. **A summary statistic standing in for a model.** E8's budgets are `n` flows *drawn from a
    pool*; "`n` × the mean" is a proxy, not a model, and the i.i.d.-expectation,
    typical-flow and cheapest-choosable models differ by up to 12% on the same budget. Name the
    model.

22. **An aggregate reported as if it were uniform.** E10's pooled median across four windows is
    6 flows, but the per-window medians are 3, 4.5, 62 and 35 — one window is *dearer* than the
    one the aggregate is being compared against. Report the breakdown before the aggregate.

23. **A degenerate selection window counted as a transfer result.** In E6, folds whose selection
    window is flat make the "selection" a tie-break; including their regret in a
    worst-transfer summary reported 0.195 where the real answer was 0.000. Flag them, keep them
    visible, and exclude them from the claim they cannot support.

24. **A cwd-relative artefact path.** Every script wrote to `out/...` relative to the *working
    directory*, so a run from the repo root created a second `out/` there and left the real
    artefact stale — which is how an auditor came to audit a stale `t38_E4.json` and report
    six fields as missing that the code writes correctly. Anchor to
    `Path(__file__).resolve().parent / "out"`. Two stale duplicates had already accumulated
    this way before it was noticed.

25. **Presentation code that can destroy measurement.** E4 completed a twenty-minute run and
    then died in its own summary `print`, because a format string met the `None` that the
    "FDP is undefined with no rejections" fix had just introduced. Nothing was written. **Dump
    the JSON before you print the summary**, always: measurement is expensive and formatting
    is not.

---

# 5. Framing decisions that are settled — do not reopen

These came out of Phase 3 review and are **not** in scope for your experiments.

1. **Position 0.55 is the guarantee window**: benign-firing ratio 1.07× (one benign flow of
   2.29 M), margin +0.067, **104 alerts, FDP 0.000, recall 0.378**. **Position 0.85 is the
   instrumented stress window** — highest tail reach (AUROC 0.999, 151 alerts, recall 0.576), used
   for attack and controller traces, but its evidence is **not a valid e-value** (50.9× / 24.3×).
   **Any experiment about guarantees evaluates at 0.55 and reports 0.85 separately**, or it
   inherits the label anomaly.
2. A1's resting place is *"localised anomaly, best explained by post-compromise label error, not
   proved."* E5 can tighten the wording; it cannot make it a proof.
3. The alert audit leads with the external-tier statement (*3 of 5 label-false alerts sit on
   red-team confirmed-compromise hosts*). The 96.1% agreement figure is a **consistency check**,
   because its structural indicator is computed from the audited label column.
4. The ADDIS result is **structural**, not a cheap operational attack. Headline is the coincidence
   of the two attack surfaces, not the 9.2×10⁷-flow budget.
5. Both attack surfaces stay under **one** contribution.
6. **Horizon knowledge is an oracle.** The rejection threshold `τ = T/w₀` and horizon-uniform
   `γ = 1/T` both use the evaluation-window episode count. Label it every time.

---

# 6. Your task list

**`02_WORKPLAN_PHASE4.md`.** Twelve experiments with tickable boxes, pre-assigned `§4.34`–`§4.43`
sections and `F18`–`F24` finding IDs, effort estimates, acceptance criteria, and decision logic
for what each outcome does to the contributions.

**E1, E2, E3 and E12 are done** — `02_WORKPLAN_PHASE4.md` §4 and
`04_EXPERIMENTS_AND_FINDINGS.md` §4.34/F18, §4.35/F19, §4.36/F20. **All three headline claims
are closed**: H1 is scoped to finite-resolution evidence under an uninterrupted controller,
H2 to a single uninterrupted controller, and H3(a)'s asymmetry escape is refuted as a
mitigation. Nothing in `03_FROZEN_CLAIMS.md` is provisional any more.

**§6's stop condition is MET.** E1, E2, E3 are resolved and their outcomes are written into
the claim boundaries; E5 is done and F9 is frozen; E7 is done and RQ4 is not
controller-specific; E12 is documented as unavailable; every refuted result is folded into
`03_FROZEN_CLAIMS.md`. Experiments may be frozen.

**ALL TWELVE ARE DONE.** E4 (§4.37/F21), E6 (§4.38/F22), E8 (§4.40/F23), E9 (§4.41/F24), E10
(§4.42/F24) and E11 (extends §4.33) have all landed; **Fig 4B is unblocked** — `t32_B1.json`'s
`coincidence` block carries all 147 per-episode rows, and every pre-existing number in that
file reproduces bit-identically. Findings now run **F1–F24**, experiment sections **§4.1–§4.43**,
and `03_FROZEN_CLAIMS.md` carries supporting claims **S1–S22** and nine new refuted entries.
Every one of the eighteen reviewer questions in `02_WORKPLAN_PHASE4.md` §9 is answered.

**Four of the six late experiments changed a claim rather than confirming one, and every one
of those surfaced in the audit rather than the first run:**

- **E4** — the workplan's "contamination costs power, not validity" is **wrong for the
  evidence this record uses**. The thresholded e-value carries the ceiling in its denominator,
  so a flow injected *below* the threshold is anti-conservative. Bounded by `(1+ε)`, which is
  why it does not matter — not because it is absent. And the tolerable quantity is a **count of
  flows**, not a rate: zero adversarially.
- **E8** — "the state attack is structural" is **false in bandwidth** (33.4 Mbit/s) and true
  only in volume (37.5× the deployment window's entire flow count).
- **E6** — the grouping optimum does **not** transfer across windows. Named as a limitation.
- **E10** — the padding attack exists at every window but is **not uniformly cheaper** outside
  the anomalous one; position 0.70 is nearly twice as expensive as 0.85.

**`t45_record_consistency.py` is new and should be run after any edit to the record.** It
re-checks the load-bearing numbers *in* `04_EXPERIMENTS_AND_FINDINGS.md` against the JSON they
were transcribed from. No other check in this project covers that gap — the scripts, the
self-tests and the audits can all pass while the prose quotes a number no artefact contains,
and it caught exactly that in a §4.42 table row.

The original E1 instructions are kept below because the *method* they prescribe is the house
standard, and it has now caught three separate errors in my own derivations: derive first,
then check the simulation against the derivation, then audit, then mutation-test the tests.

Start with **E1** (smoothed and continuous evidence). It has the highest probability of narrowing
Contribution 1, and that should surface now. Two prerequisites before you write code:

- read `04_EXPERIMENTS_AND_FINDINGS.md` §4.28 — the boosting result explains the mechanism E1 is
  probing;
- derive both routes' rejection probabilities analytically first. `02_WORKPLAN_PHASE4.md` E1 states
  the predictions. **A simulation that disagrees with the derivation is a bug, not a finding** —
  resolve it before recording anything.

Run **E12's triage in parallel from day one**: a positive result adds 3–5 days and needs to be
known early.

## 6.1 What not to do

- **Do not start drafting the paper.** Three claims are provisional (`03_FROZEN_CLAIMS.md` header).
- **Do not add anything outside E1–E12.** No more classifiers, `q` values, spending sequences,
  cap policies, padding pools, or procedures — all swept, all in the declined list.
- **Do not build a traffic-generation testbed.** Explicitly declined in `02_WORKPLAN_PHASE4.md` §7,
  with the reasoning; E8 and E10 substitute for it.
- **Do not revive the calibration-drift hypothesis.** Measured and refuted.
- **Do not say "incident"** when you mean episode.
- **Do not report a single-seed or single-draw number as a result.**
- **Do not skip the audit** because a script "looks obviously right". All six inverted or
  rescaled conclusions came from scripts that looked obviously right — the most recent being
  E8's, where the ADDIS state attack was priced over a window belonging to a different `|C|`
  regime and came out elevenfold too cheap.
- **Do not treat "the mean is a summary of a pool" as harmless.** E8's budgets are `n` flows
  *drawn from a pool*; "`n` × the mean" is not a model, and four explicit attacker models
  disagree by up to 12% on the same budget (§4.40).
- **Do not use `np.isclose` or `sd > 0` as an equality test on quantities whose scale you
  have not checked.** `np.isclose`'s default tolerance at λ = 0.25 is 2.5×10⁻⁶, five times
  wider than the conformal floor it was being asked to resolve (E11); `np.std(ddof=1)` over
  50 bitwise-identical float64 values returns ~10⁻¹⁷, which reported four E9 statistics as
  varying when none did.

---

# 7. Mandatory: audit every result before it enters the record

Not optional overhead. It is why the numbers are trustworthy, and it has caught six inverted or
rescaled headline numbers.

**After writing a script and before believing its output:**

```bash
cd /Users/shamik/Work/others/SaTML
cat > /tmp/audit.txt <<'EOF'
You are auditing numerical/statistical code for LATENT BUGS. FIND ERRORS. Be adversarial and
specific. Do not summarise what the code does.

Working dir: /Users/shamik/Work/others/SaTML
Python: proto/.venv/bin/python
AUDIT: proto/<your_script>.py
Context you MUST read: proto/h_stream.py, proto/h6_procs.py
DO NOT read proto/data/lspr23/ls23pr_v1.csv or /tmp/lspr_*.csv or /tmp/lspr_*cache
(multi-GB; it will burn your context). Reason about the code and write small synthetic tests
in /tmp using proto/.venv/bin/python.

<state the setup: what an e-value is here, what the procedure does, what each quantity means,
 and what claim the numbers are going to support>

CHECK SPECIFICALLY:
1. <list the things you are least sure about, by name — be concrete>
...
N. Any use of test-split information to set a parameter evaluated on the same test split.

Report: file:line, what is wrong, why it changes a number, corrected code. One line for
things that are correct. Be explicit if a fix is correct but INCOMPLETE.
EOF
nohup codex exec --skip-git-repo-check --sandbox workspace-write "$(cat /tmp/audit.txt)" \
  < /dev/null > proto/out/codex_<task>.log 2>&1 &
```

**Notes.** Redirect stdin from `/dev/null` or it blocks. Always tell it not to read the multi-GB
files. Audits take 5–20 minutes; work on something else meanwhile. **Ask it to check the things
you are least sure about, by name** — the generic prompt finds much less. The most productive
questions have been: *is this parameter derived from the evaluation split? is this randomised
statistic reported from one draw? is this grid fine enough in the tail? does the seed actually
perturb the quantity being varied? is this conditional rate divided by the right denominator?*

**Re-audit after fixing.** The second round on the Phase 3 scripts confirmed twelve fixes and
found seven more issues, two of which softened a headline claim.

---

# 8. Recording results

1. Add a `## 4.N <title> (script.py) [TAG]` section to `04_EXPERIMENTS_AND_FINDINGS.md` with the full
   tables. That document is **current state only**, not a change log — state what is, not what was
   fixed. Section numbers are pre-assigned in `02_WORKPLAN_PHASE4.md` §8; the last existing section
   is §4.42 and the last finding is F24. §4.37 is the only pre-assigned section still unwritten.
2. Update the affected findings F1–F24, or add F25+ per the pre-assigned map.
3. Update the claim-strength table in §5 of that file. Use **Moderate** when the evidence is
   moderate — two Phase 3 rows are Moderate and the paper is better for it.
4. Add the script to the reproduction list in §8.
5. If the result changes a provisional claim, update `03_FROZEN_CLAIMS.md` — including its header,
   which currently holds H1, H2 and H3(a) open.
6. Tick the box in `02_WORKPLAN_PHASE4.md` §4 and the reviewer question in §9.
7. Write a unit test for anything with non-obvious index algebra or a closed form, following
   `t33_selftest_A1A2B1.py`. Closed forms get verified **against the implementation**, not against
   a re-derivation of it.
