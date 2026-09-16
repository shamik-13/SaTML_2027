# Work Plan — Phase 4: Reviewer-Gap Closure

**Created 26 Aug 2026. This is the active task tracker.** It supersedes `09_WORKPLAN_phases1-3.md` §14
(which froze the experiment matrix after Phase 3) and the "start writing now" recommendation in
`07_phase3_next_step_recommendation.md` §7.

**Decision that produced it.** With a month to the deadline, all remaining experiments are to be
finished before manuscript writing begins. The freeze declared at the end of Phase 3 is
**lifted for this queue only** — nothing outside the twelve items below is in scope.

Sources reconciled here: `08_satml_reviewer_gap_experiment_checklist.md` (the queue),
`07_phase3_next_step_recommendation.md` (the claim-framing decisions, which stand),
`06_PHASE3_REPORT.md` (what is already closed).

---

# 1. Deadlines and budget

| Date | Days from 26 Aug | Milestone |
|---|---|---|
| **15 Sep** | 20 | **experiments complete** — hard internal gate |
| **22 Sep** | 27 | abstract registration — mandatory regardless of state |
| **29 Sep** | 34 | paper submission |

Queue below is **~9 working days** of implementation, audit and runtime, excluding the
second-dataset extension (gated, +3–5 days if it passes triage). That leaves ~10 days of slack
before the 15 Sep gate and ~14 days for drafting. **The slack is the plan's only protection
against an experiment that inverts a claim**, which has happened twice in this project.

## 1.1 Standing rules, carried forward

1. No claim enters the record without a verification tag and its scope stated inline.
2. No comparison at unmatched operating points.
3. Every FDR number printed beside a power number in the same table.
4. Oracle-derived results labelled as such in every figure caption.
5. Single-split, single-seed numbers are not results — report intervals.
6. Any aggregation rule must be checked for validity on **every** group it is applied to.
7. **Every experiment gets a blind adversarial codex audit before its numbers are believed**
   (procedure in `01_HANDOFF_PHASE4.md` §7). Sixteen rounds so far have found ~112 defects, six of
   which had inverted or rescaled a headline number. This is not optional overhead. E1's four
   rounds are worth reading as a model: round 3 defeated E1's own unit tests by **mutation**,
   which is why the helpers are now module-level and the self-test is verified against 20
   deliberate mutations.
8. Results are recorded as `## 4.N` sections in `04_EXPERIMENTS_AND_FINDINGS.md`, written as
   current state, not as a change log. Section and finding numbers are pre-assigned below.

## 1.2 What is already closed and must not be re-run

T1–T11, H1–H8, A1, A2, B1. See `06_PHASE3_REPORT.md` §0 for the disposition table. In particular:

- the pre-committed slot **escape from the padding theorem is already proved and priced**
  (§4.16 corollary; §4.12 policy D: 109.4/284 episodes, power decaying as 1/m under padding,
  padding-invariance verified at r = 0, 10, 10³, 10⁵). E3 below extends it; it does not redo it.
- **five padding pools** including a black-box pool chosen with no detector access are done
  (§4.30), with identical cost. E8/E10 extend the *reporting*, not the pools.
- **horizon misspecification** is swept (§4.20). E2 is a different intervention — resetting
  state, not mis-stating T.

---

# 2. Claims currently provisional

`03_FROZEN_CLAIMS.md` stands. **E1 and E12 have landed**; one and a half entries remain open:

| Claim | Held open by | Status |
|---|---|---|
| **H1 / C1** — finite feasibility horizon | ~~E1~~ · **E2** | **E1 done.** Smoothing removes the floor and the absorbing state, so H1 now states its **finite-resolution** premise explicitly — but it does not narrow further, because smoothing buys no reliably-detected episode and the continuous route is strictly dominated (§4.34, F18). Still open to E2: restart could narrow it to *…under an uninterrupted controller* |
| **H2 / C2** — granularity–feasibility tradeoff | ~~E12~~ **closed** | **E12 done, FAIL.** No public dataset carries genuine flow→campaign labels (`proto/out/E12_triage.md`), so C2 **stays narrow** — deployable episode heuristics on LSPR23 — and the triage record is the answer to the objection |
| **H3(a) / C3** — padding theorem boundary | **E3** | If a deterministic precommitted weighting resists padding *and* survives attacker-controlled ordering at usable power, it becomes a mitigation the paper must present |

No prose may be written against H1 or H3(a) until E2 and E3 land.

---

# 3. Framing decisions that are already settled

Carried from `07_phase3_next_step_recommendation.md`; **not reopened by this queue.**

1. A1's resting place is *"localised anomaly, best explained by post-compromise label error, not
   proved."* E5 can tighten it; it cannot upgrade it to proof.
2. **Position 0.55 is the guarantee window** — ratio 1.07× (one benign flow fires of 2.29 M),
   margin +0.067, 104 alerts, FDP 0.000, recall 0.378. **Position 0.85 is the instrumented
   stress window**, used for attack and controller traces, never alone for "provably controls
   FDR". Every experiment below that evaluates guarantees does so at 0.55 and reports 0.85
   separately, or it inherits the label anomaly.
3. The alert audit leads with the E1-tier statement (*3 of 5 label-false alerts on
   confirmed-compromise hosts*); 96.1% agreement is a consistency check.
4. The ADDIS result is **structural**, not a cheap operational attack. The headline is the
   coincidence of the two attack surfaces (101 of 147 detections), not the 9.2×10⁷ flow budget.
5. Both attack surfaces stay under one contribution (C3).

---

# 4. The queue

Effort is implementation + audit + runtime. Script names follow the repo's chronological
convention. `[ ]` = not started.

---

## E1 — Smoothed and continuous evidence `[x]` P0 · 1 day · `t34_E1_smoothed.py` · §4.34

**DONE.** Recorded in `04_EXPERIMENTS_AND_FINDINGS.md` §4.34 as F18; H1 amended to state its
finite-resolution scope (`03_FROZEN_CLAIMS.md`). Outcome: the middle branch of the decision
logic below — detection is *not* restored in any usable sense, so C1 keeps its strength and
gains an explicit resolution premise plus a resolution ↔ stability tradeoff. Scripts:
`t34a_E1_derivation.py` (152 closed-form checks), `t34_E1_smoothed.py` (the measurement),
`t34b_E1_selftest.py` (unit tests). Four blind audit rounds; `out/codex_E1[a-e]_*.log`.

**Reviewer objection.** *"Your finite discovery horizon comes from discrete threshold-conformal
evidence. The resolution-collapse literature shows randomised smoothing removes the p-value
floor. Why not use it?"* The record cites Hennhöfer & Preisach (arXiv 2603.23205) and notes
smoothing "removes it at the cost of variance" — **and has never tested it.** This is the single
most exposed gap.

**Run two routes, which the source checklist merges and which behave differently.**

*Route A — smoothed p-values into p-value procedures* (LOND, SAFFRON, ADDIS). No calibrator.
`p = (#{c > s} + U·(1 + #{c = s}))/(|C|+1)`, `U ~ Unif(0,1)`, so a point above every calibration
score gets `p = U/(|C|+1)` and the floor `1/(|C|+1)` is genuinely gone.

*Route B — smoothed p → p-to-e calibrator → e-value procedures* (e-LOND, e-LORD, online e-BH).
Sweep the calibrator: Vovk `½p^{−1/2}`, and `λp^{λ−1}` for `λ ∈ {0.1, 0.25, 0.5, 0.75}`.

**Analytic prediction, to be confirmed or refuted, not assumed.**
Route A: `P(reject) = min(1, α_t·(|C|+1))`, so smoothing converts *structural silence* into
*detection with probability* `α_t·(|C|+1)` — the absorbing state disappears, determinism does
too. Route B: with the Vovk calibrator `e = ½√((|C|+1)/U) ≈ 673/√U` at `|C|+1 = 1.81×10⁶`, so
clearing `1/α_t ≈ 6.3×10⁵` needs `U ≤ 1.1×10⁻⁶` — F15's mechanism returning, because the
two-point e-value is extremal. **Derive both exactly before running, then check the simulation
against the derivation.** A mismatch is a bug, not a finding.

**Measure.** Over ≥100 randomisation seeds, at positions 0.55 and 0.85 × 2 detector seeds:
empirical FDP · episode recall · alert count · structural-silence fraction · alert-set Jaccard
`J(A_i,A_j)` between seed pairs · per-attack-episode detection probability
`P_rand(a detected)` · `Var(R_T)` · `Var(FDP_T)` · detection-latency variance.

**Record for the alternative:** whether it offers finite-sample exact, asymptotic, marginal or
conditional validity. Do not build a new method.

**Accept when.** For both routes, the feasibility boundary is located under smoothing and the
variance cost is quantified; and the C1 claim is either unchanged, or narrowed with the exact
scope written out.

**Decision logic.** No useful detection → C1 strengthens. Detection restored but unstable → C1
gains a *resolution ↔ stability* tradeoff, which is a better paper. Clean solution → C1 narrows
to exact discrete evidence and the paper leans on C2/C3.

---

## E2 — Periodic controller restart and batching `[x]` P0 · 0.75 day · `t35_E2_restart.py` · §4.35

**DONE.** Recorded in `04_EXPERIMENTS_AND_FINDINGS.md` §4.35 as F19. Outcome: restart DOES
restore detection (LOND 18.0 → 95.0 rejections, episode recall 0.065 → 0.345 at FDP 0.000),
nearly replacing oracle horizon knowledge — so H1 is now stated for an **uninterrupted
controller** and is closed. The price is exact: per-epoch FDR does not pool, and
`pooled FDR = 1 − (1 − q)^n` = 0.185 at the headline arm. E2c materially affects H2:
restart preserves episode resolution where coarsening does not (recall 0.406 vs 0.103), so
H2 is now scoped to a single uninterrupted controller. The prediction that most epochs
would go silent is **refuted** on this stream. 48 h epochs are unmeasurable on LSPR23.
Scripts: `t35a_E2_derivation.py` (201 checks), `t35_E2_restart.py` (908 derivation checks).

**Reviewer objection.** *"A SOC does not run one controller forever. Why not reset every
hour/shift/day?"* Batching is cited (Zrnic et al., *The Power of Batching*) with the note that
it frames batching as power recovery and does not address rejection feasibility. **Restart has
never been run.**

**Run.** Deterministic epochs of 1, 6, 12, 24, 48 h and the exercise-day boundary. At each
boundary reset wealth and controller state, keep the detector and calibration fixed. Compare
against the uninterrupted controller, at position 0.55 **and** the full stream where epoch
counts allow.

**Also run E2b, alpha-budgeted restarts:** a precommitted `q_1, q_2, …` allocation across
epochs, versus per-epoch `q = 0.05`.

**Also run E2c, restart × grouping:** whether restart plus *fine* grouping preserves episode
resolution without the coarsening C2 requires. This one can materially affect C2.

**The statistical point that must be stated explicitly.** Per-epoch FDR control at `q` does
**not** imply pooled deployment FDR control at `q`. It does give pooled **mFDR** control
(`E[V]/E[R]` aggregates; `E[V/R]` does not). Write the distinction, with the counterexample if
one is cheap to construct.

**Analytic prediction.** At ~13,000 episodes/hour, 1-hour epochs need
`|C| ≥ kT_epoch/w₀ − 1 ≈ 5.2×10⁵` against `|C| = 1.8×10⁶` — comfortably feasible. So restart is
expected to *restore feasibility*. The counterweight is F2: the first-rejection deadline applies
afresh **every epoch** (18–334 hypotheses at `|C|` = 10⁴–10⁶), so most epochs should go silent
before their first rejection. Measure the fraction of epochs with zero discoveries — that is the
number that decides this experiment.

**Measure.** Global empirical FDP · per-epoch FDP · episode recall · malicious-flow coverage ·
alerts/day · time-to-detection · **fraction of epochs with zero discoveries** ·
structural-silence fraction.

**Accept when.** The manuscript can answer *"why not just restart daily?"* in one sentence with
a number behind it.

---

## E3 — Deterministic precommitted weights and the ordering attack `[x]` P0→P1 · §4.36

**DONE.** Recorded in `04_EXPERIMENTS_AND_FINDINGS.md` §4.36 as F20, extending F7. Outcome:
**the triangle is closed and C3 is complete.** No precommitted weight sequence escapes — the
front-load cost `L*` is finite for every summable `w`, the reach is capped at `P ≤ α_t·M`
(the same quantity as F1's horizon), and every padding-invariant scheme that keeps the mean
rule's recall falls to 1–8 leading flows against 111 appended ones. The asymmetric escape
makes the attack **cheaper**, not dearer. Scripts: `t36a_E3_derivation.py` (115 checks),
`t36_E3_asymmetric.py`, `t36b_E3_selftest.py` (verified against 7 mutations).

**Reviewer objection.** *"Your impossibility theorem is about symmetric e-merging. Why not use
an asymmetric rule?"*

**Already answered, and must not be redone:** §4.16's corollary proves `F(e) = e_slot` valid
under arbitrary dependence and padding-invariant; §4.12 policy D prices it. The record already
identifies the true condition — *the adversary must not be able to choose which slot its events
occupy.* **E3 tests exactly that condition.**

**Run E3a, deterministic weight schemes** (weights fixed before any score is observed):
first-event-only · last-event-only · exponential decay by position · uniform over the first `m₀`
slots · a security-prior scheme defined a priori. For each: validity check on **every** group,
padding resistance, episode recall, malicious-flow coverage, required group size.

**Run E3b, adversarial placement**, two attacker models:
(i) attacker cannot influence order → measure the genuine benefit;
(ii) attacker can influence timing/order → attacker places padding in high-weight positions and
attack evidence in low-weight positions. Report the attack cost.

**Analytic prediction.** First-event-only is padding-invariant but defeated by *one* leading
benign flow, which is the front-load attack already measured for truncation (median 345 leading
flows at a p99 cap, **1 flow** at a p50 cap, §4.12/§4.25). Expect the tradeoff
*padding robustness ↔ dependence on precommitted position ↔ attacker control of ordering* to
close, with no scheme escaping all three.

**Accept when.** Either a scheme resists padding at usable power under attacker-controlled
ordering — in which case it becomes a mitigation the paper must present — or the triangle is
shown closed, which completes C3.

---

## E4 — Calibration contamination `[x]` P1 · `t38a_E4_derivation.py` + `t38_E4_contamination.py` + `t38b_E4_selftest.py` · §4.37, F21

**DONE. THE QUEUE IS COMPLETE.** Recorded as §4.37, findings F21 and F21(b). The answer is
**one flow**: at `k = 1` the whole conformal rule is a single order statistic, so one
mislabelled high-scoring attack flow in calibration takes recall 0.065 → 0.000 (position 0.55)
and 0.282 → 0.000 (0.85). The tolerable number of adversarial mislabels is exactly `k − 1`, and
F14 fixes `k = 1`, so it is **zero** — `k` is the contamination budget as well as the power and
reliability parameter, and feasibility has already spent it.

**Two framings in this task needed correcting before measurement.** (a) *"Quantify the tolerable
ε."* The adversarial arm has no rate dependence at all — the top `εN` attack flows share one
maximum, so the curve is a step at one flow — and at `\|C\| ≈ 2×10⁶` even `ε = 10⁻⁷` rounds to
zero flows. The `ε` grid has no resolution where the effect lives; the per-flow sweep does.
(b) *"Contamination costs power, not validity."* Right for the full conformal p-value, wrong for
the thresholded e-value the pipeline actually uses, whose p-value carries the ceiling in its
**denominator**. A flow injected *below* the threshold inflates evidence by exactly `(1+ε)` and
is anti-conservative. That channel is **bounded** — `q = 0.05` → 0.0542 at the whole available
stealth budget, recall unchanged — while power is not bounded at all, and that asymmetry is the
finding.

Also settled: the random arm's scale is `1/(N·q₀)` where `q₀` is the **contamination pool's**
exceedance rate, not the deployment window's malicious firing rate (using the latter mispredicts
the transition by 15×); and **the feasibility margin is not a safety indicator** — constant to
six decimals across the whole sweep while detection goes to zero, because contamination
*increases* `\|C\|`.

The two audit rounds found ten defects. Two were mine and would have changed the record: the
missing ceiling channel above, and a tautological "validity" check (`max(fdp) <= 1`) that could
not fail. Two more were operational — a without-replacement sampler that tried to allocate
102 GB, and a summary `print` that destroyed a completed twenty-minute run by meeting a `None`.

**Reviewer objection.** *"You assume a large clean benign calibration set. In security, how do
you know the calibration period is attack-free?"* Sharpened by A1, which found label problems in
this very dataset.

**Run.** Inject malicious flows into the calibration set at `ε ∈ {0, 10⁻⁵, 10⁻⁴, 10⁻³, 10⁻²}`,
under two models: uniformly random attack flows, and **highest-scoring** attack flows (the
adversarial case — a poisoner would contribute exactly these).

**Measure.** Evidence ceiling · benign firing rate · malicious firing rate · feasibility margin
· episode recall · FDP. At positions 0.55 and 0.85.

**Analytic prediction.** The ceiling `(|C|+1)/k` is unchanged by contamination; what moves is
the *threshold* `cal[-1]`. High-score contamination raises the maximum calibration score, so
malicious firing collapses long before benign firing does — expect recall to fall steeply and
FDP to stay flat, i.e. contamination costs power, not validity. Quantify the tolerable `ε`.

**Accept when.** The paper can state the contamination level at which the approach stops working.
Do not turn this into a poisoning paper.

---

## E5 — Finish the A1 forensics `[x]` P1 · `t37_E5_a1gaps.py` · extends §4.31

**DONE.** Recorded as the E5 subsection of §4.31; F9's wording is unchanged and **F9 and
§4.31 are now frozen**. Outcome: the tail is attack-like on both gaps and survives the
strictest control (host AND destination-port matched), so the label-error reading is
strengthened but still not proved — exactly the branch the pre-fixed interpretation rule
allows. The audit caught a catastrophic-cancellation bug that had turned the baseline
denominators into exact zeros, and a missing port-matched control.

**Reviewer objection.** *"You say the anti-conservative tail is probably post-compromise label
error. What does the feature geometry say?"* These are the two gaps `06_PHASE3_REPORT.md` §1.5
flags itself.

**Run E5a, near-neighbour geometry.** For each of the 46 (seed 0) and 22 (seed 1) extreme-tail
benign-labelled flows, in standardised model-feature space: distance to nearest labelled
malicious `d_M`, nearest ordinary benign deployment flow `d_B`, nearest calibration benign `d_C`.
Report distributions and `ρ = d_M/d_B`, **against a benign-baseline ρ computed the same way on a
matched sample of ordinary benign flows** — an absolute ρ means nothing without it.

**Run E5b, per-feature comparison.** Standardised differences and percentile locations of the
tail against benign and against malicious populations; enrichment for categoricals; top
distinguishing features.

**Interpretation rule, fixed in advance.** Tail attack-like → strengthens *"consistent with
post-compromise label error"*. Not attack-like → keep only the localisation claim. **Neither
outcome is proof**, and F9's wording caps at "best-supported explanation".

**Accept when.** F9 and §4.31 are frozen for the paper.

---

## E6 — Cross-window parameter transfer `[x]` P1 · `t26_H4_grouping.py --five` + `t39a_E6_derivation.py` + `t39_E6_transfer.py` + `t39b_E6_selftest.py` · §4.38, F22

**DONE.** Recorded as §4.38, finding F22. The prerequisite `t26` re-run is in place as a
`--five` mode writing a separate `out/t26_H4_5pos.json`, so the record's two-position H4
result reproduces unchanged. **Outcome, in two halves.** The objection is answered, but by
evidence of the *opposite* of tuning: the frozen grouping is the worst **feasible**
configuration of 35 at position 0.70 and within 10⁻⁴ of the worst at two more, and the frozen
cap is the worst of six at two of five windows. Nobody tunes on a test window to reach the
worst configuration. The **cap transfers** (worst previous-window regret 0.012, normalised
0.070) and its power-optimal value `n₀ = 2` is defeated by one front-load flow, which is
exactly why §4.12 chose on validity. The **grouping does not transfer** (worst regret 0.579,
normalised 0.991) and that is named as a limitation: coverage numbers are what the deployable
grouping achieves, not the best achievable. Three design rules had to be settled first
(`t39a`, 29 checks): normalised regret is undefined on a flat grid, selection on episode
recall selects coarseness because the family sets its denominator, and the feasibility gate
is not a tuned parameter. The two audit rounds found fifteen defects, two of which changed
reported numbers — folds whose *selection* window was flat were being counted as transfer
failures, and the oracle was allowed to pick configurations the feasibility theorem forbids.

**Reviewer objection.** *"Were the grouping width, cap, spending sequence or threshold chosen
after looking at the test window?"*

**Run E6a, previous-window selection.** For each window `j`: choose the configuration using only
window `j−1`, freeze it, evaluate on `j`. Parameters: bucket width, grouping family, cap `n₀`,
spending-sequence family, and `q` if treated as tunable.

**Run E6b, leave-one-window-out.** Choose one configuration from four positions, evaluate on the
held-out fifth, five times.

**Known extra cost.** `t26_H4_grouping.py` covers positions **0.62 and 0.85 only** (verified:
140 rows over exactly those two positions × two seeds). Bucket width and grouping family
therefore need a re-run across all five positions before E6 can select over them. That re-run is
the extra half-day in the estimate and is a prerequisite, not part of E6 proper.

**Accept when.** The main qualitative findings are shown not to require test-window tuning, or
the ones that do are named.

---

## E7 — Second feedback controller and disposition delay `[x]` P1 · `t40_E7_controller.py` · §4.39

**DONE.** Recorded in §4.39, extending F13. Scoping decision taken and stated: neither option
(a) nor (b) was available as written, because no deployment window on LSPR23 spans more than
26.98 h (§4.35); 15 min/1 h/4 h/8 h are measured at the guarantee window, 24 h only on the
long-span `[WEAK-CAL]` window, and 72 h is unmeasurable. Outcome: RQ4 is **not**
controller-specific (P, PI and Robbins-Monro AQT agree from 4 h onward), and wall-clock delay
is far harsher than alert-counted latency — FDP 0.402 at fifteen minutes against a 0.05
target, because 51.4% of alerts are open-loop. The controller also sits at its actuator limit
95–100% of steps, so most of the measured advantage is the threshold, not the feedback.

**Reviewer objection.** *"RQ4 rests on one hand-chosen proportional controller, and latency is
measured in alerts rather than real time."*

**Run E7a.** One simple alternative — PI control **or** direct adaptive quantile targeting. Do
not invent a control algorithm.

**Run E7b, disposition delay.** Target 15 min, 1 h, 4 h, 8 h, 24 h, 72 h on chronological
timestamps.

**Scoping constraint that must be resolved first.** §4.14 measures latency in *alerts* precisely
because the deployment window spans **2.4 h** — 24 h and 72 h have no room in it. Two options,
pick one and state it: (a) run E7b on the full 161.5 h stream with a coarser alerting unit, or
(b) report 15 min / 1 h / 4 h only and say why the longer delays are unmeasurable here. Option
(a) is preferable and is why E7 is 0.75 day rather than 0.5.

**Measure.** Realised FDP · episode recall · alerts/day · burn-in · time until the controller
becomes responsive.

**Accept when.** RQ4's conclusion is shown not to be controller-specific. The target conclusion
is honest either way: *direct feedback is competitive when dispositions arrive quickly; formal
no-feedback error control matters under long or absent feedback.*

---

## E8 — Physical cost units for both attacks `[x]` P2 · `t41a_E8_derivation.py` + `t41_E8_units.py` · §4.40, F23

**DONE.** Recorded as §4.40, finding F23. **The expected sentence was wrong and is corrected.**
Suppressing one alert costs 34 flows = 13.3 kB = **15 bit/s** over the 2 h bucket from one
host; the ADDIS state attack costs 92,015,637 flows = 36.1 GB = **33.4 Mbit/s** over position
0.85's own 2.4 h deployment span, i.e. four hosts at 10 Mbit/s. Bandwidth does not separate the
two surfaces. What does is volume against the monitored population: 37.5× the deployment
window's entire flow count against 1.4×10⁻⁵ for suppressing an alert. Not "pure arithmetic":
the unit of `Flow Duration` is *recovered* from the file's own internal consistency
(microseconds, three decades clear, on 84% of flows) rather than assumed, and four explicit
attacker cost models replace "n × the mean". The audit caught the state attack being priced
over §4.35's 26.98 h window, which belongs to a different `|C|` regime — an elevenfold
understatement of the required rate.

Convert every attack budget from flows into packets, bytes, mean bandwidth, required rate over
the bucket duration, and number of attacker hosts if distributed. Use the real per-flow packet
and byte distributions of each padding pool, not an average.

**Why it earns its place.** It is the sentence that separates the two attack surfaces: padding
is plausibly operational; the ADDIS state attack at 9.2×10⁷ flows is structural. Pure arithmetic
over cached columns.

**Accept when.** Both attacks are reported in operational units in §4.30 and §4.33.

---

## E9 — Timestamp-tie sensitivity `[x]` P2 · `t42a_E9_derivation.py` + `t42_E9_ties.py` · §4.41, F24

**DONE. Negligible → one appendix sentence**, the branch the accept criterion allows. At most
1.3% of episodes share a first timestamp and the largest tie block is 3, so at most 1.3% can
move. Across 50 randomised within-timestamp orders at positions 0.55 and 0.85, **all 36
statistics take a single value equal to the deterministic one** — with the randomisation
verified to move ~50% of the movable positions per draw, so the null is powered rather than
vacuous. `build_episodes` gained an additive `tie_key` argument; `tie_key=None` reproduces the
record exactly. One conjecture was **refuted** along the way: smallest-p-first does not
maximise a tie block's rejection count (beaten on 127 of 600 blocks by up to 3), so there is
no cheap surrogate for the block optimum.

Online testing depends on order. `h_stream.build_episodes` already uses
`np.lexsort((first_pos, first_ts))` **specifically** to make ties deterministic (standing
mistake 5), so this quantifies the variance that choice suppresses rather than fixing a bug.

**Run.** For equal-timestamp hypotheses: deterministic source order (current), versus randomised
within timestamp, 50 seeds. Measure variance in discoveries, FDP, recall, first detection.

**Accept when.** Negligible → one appendix sentence. Non-negligible → the deterministic
tie-break becomes a stated part of the method.

---

## E10 — Padding attack on windows other than 0.85 `[x]` P2 · `t43_E10_xwindow_padding.py` · §4.42, F24

**DONE.** Median suppression cost reported at **four** positions besides 0.85, against the ≥ 3
required: per-window medians 3 (0.55), 4.5 (0.62), 62 (0.70), 35 (0.77) against 35.25 at 0.85.
The attack is not confined to the anomalous window. It is *not* uniformly cheaper elsewhere —
the pooled figure of 6 flows is driven by the two cheap windows, and 0.70 is nearly twice as
expensive as 0.85. The black-box pool has mean e exactly 0 and P(fire) exactly 0 at **all
five** windows, so §4.30's deterministic-suppression result holds across the full span. Cost
rule AST-imported from `t28_P5_padding.py` so the two cannot diverge; §4.30's oracle caveat is
inherited and stated.

**Reviewer objection.** *"The attack only exists in your anomalous label window."*

**Run.** Reduced padding experiment at every position with target detections — 0.55 (104
alerts), 0.62 (108/110), 0.70 seed 0 (67), 0.77 (59). Two pools only: generic benign and the
black-box common-service pool. Report median suppression cost where measurable.

**Accept when.** Median cost reported at ≥3 positions besides 0.85.

---

## E11 — Per-episode coincidence export `[x]` — · `t32a_E11_derivation.py` + patch to `t32_B1_addis_state.py` + `t32b_E11_selftest.py` · extends §4.33

**DONE. Fig 4B is unblocked.** `t32_B1.json`'s `coincidence` block now carries all 147
per-episode rows (rank, `m_fire`, `nsz`, `α_t`, pre-pad `p`, `N*`, pad, `p⁺`, `saturated`,
`lands_in_window`) plus `M`, λ, τ, the floor width, the D5a threshold and both denominators.
Ten identities are asserted at write time and the three stored aggregates are recomputed from
the arrays, so the figure cannot disagree with the text. **Every pre-existing number
reproduces bit-identically** (0 keys removed, 0 values changed across 910 leaves).

The export turned out to need a derivation, not just plumbing: `t32a_E11_derivation.py` (40
checks) proves the reported equality **101 saturated = 101 landing is FORCED**, not a
property of this window — cap-saturation implies landing whenever `M·m ≥ 1/(τ−λ) = 4`, and
`min M·m = 1,813,114`. The converse holds only inside a window one conformal floor wide, and
zero episodes are in it. Without that, Figure 4B invites the reading that the equality is an
accident a second dataset could break.

The audit found nine defects, none of which moved a recorded number but three of which were
latent rescalings: `np.floor(α_t·M·m)+1` is not always the least integer in float64 (`N*` is
now computed with `Fraction`); `np.isclose`'s default tolerance at λ is 2.5×10⁻⁶ against a
5.5×10⁻⁷ floor, so the saturation test is now exact; and the D7a median identity was stated
as a theorem when it is conditional on there being no unsaturated lander, which is now
asserted rather than assumed. `t32b_E11_selftest.py` AST-imports the shipped `least_n_gt` and
catches nine mutations.

**Accept when.** ~~Fig 4B is plottable from JSON alone, and `t32`'s existing numbers reproduce
unchanged.~~ **Both met.**

---

## E12 — Second dataset with genuine flow→campaign labels `[x]` triage done, extension NOT taken · record: `proto/out/E12_triage.md`

**TRIAGE VERDICT: FAIL — do not spend the 3–5 days.** No public dataset carries a genuine
flow→campaign identifier with complete negatives and recoverable chronological order. Record:
`proto/out/E12_triage.md` (candidates table, rejected-on-sight list, search coverage, and a
citable paragraph for the paper). Nearest misses and the rule each trips: CasinoLimit (RAID
2025) labels MITRE *techniques*, i.e. attack classes not campaign instances; GAMBiT ships no
per-flow labels; GUIDE's `IncidentId` is produced by a proprietary entity+time-window
correlator — the very heuristic under test. LSPR24 exists (Zenodo 14900873, CC0) but has no
campaign column and its narratives are an empty shell. H2 therefore stays narrow; the triage
record is itself the answer to the reviewer objection. `t44_E12_dataset2.py` is not written.

**Reviewer objection.** *"Your 'episodes' are heuristic host/time groups, not incidents. How do
we know the granularity tradeoff isn't an artefact of your grouping heuristic or of LSPR23?"*
The largest remaining empirical-breadth weakness, and the only open item that can change a
headline number.

**Required property.** A real `flow/event → attack campaign / scenario / incident` mapping. Not
binary attack labels, not host labels, not alert categories.

**Triage first, time-boxed to half a day. Reject a candidate if** campaign labels need manual
reconstruction · negatives are incomplete · chronological ordering is unavailable · there are too
few campaigns · **the campaign identifiers derive from the same host/time heuristic we are trying
to validate.** Known non-starters from T11: ConCap (generator — replaces live-fire with
synthetic), AIT-LDSv2 (label reconstruction from a 137 GB download), ProvAttack1/2 (provenance
graphs, not flows).

**If triage passes, run only four things:** (3A) event-level feasibility — `T_flow`, `|C|`, `M`,
margin; (3B) true campaign-level feasibility — `T_campaign` and margin under the dataset's own
campaign identity; (3C) evaluation-unit disagreement — flow recall vs campaign recall vs
analyst-facing discovery count; (3D) one padding experiment, to check the aggregation
vulnerability transfers.

**Accept when.** Either C2 upgrades to "holds under deployable grouping *and* real campaign
ground truth", or the triage record documents why no suitable dataset exists — which is itself
the answer to the objection.

---

# 5. Sequence

| Day | Work | Parallel |
|---|---|---|
| 1–2 | ~~**E1** smoothed / continuous evidence~~ **DONE** | ~~E12 triage~~ **DONE, FAIL** · `figs.py` scaffold |
| 3 | ~~**E2** restart / batching~~ **DONE** | ~~second-dataset decision~~ **DONE, FAIL** |
| 4 | ~~**E3** asymmetric weights~~ **DONE** + ~~**E11** export~~ **DONE** | Fig 1, Fig 2 |
| 5 | ~~**E5** A1 gaps~~ **DONE** + ~~**E4** contamination~~ **DONE** | Fig 3 |
| 6–7 | ~~**E6** transfer (incl. `t26` five-position re-run)~~ **DONE** | Fig 4A/4B |
| 8 | ~~**E7** controller + delay~~ **DONE** | Table 1 |
| 9 | ~~**E8** units + **E9** ties + **E10** cross-window padding~~ **ALL DONE** | Table 2, Fig 5 |
| 10+ | ~~E12 minimal experiments if triage passed~~ — triage failed, nothing to run | — |
| **by 15 Sep** | **experiments frozen permanently** | figures complete |

E1 goes first because it has the highest probability of narrowing a contribution, and that
should surface now rather than in December. E12's triage runs from day 1 because a positive
result adds 3–5 days and needs to be known early.

## 5.1 Figure track, running in parallel

**Zero plotting code exists in the repo** — `grep matplotlib proto/*.py` returns nothing, though
matplotlib 3.11.1 is installed. Seven main items are planned (`05_PAPER_CONTRACT.md` §7). All their
data already exists in `proto/out/*.json`, Fig 4B included since E11. Build one shared `figs.py`
(palette, type, sizing, PDF export) plus one script per item, in a single pass, so the set is
visually coherent rather than restyled five times.

---

# 6. Stop condition

Freeze experiments permanently once **all of**:

- E1, E2, E3 resolved and their outcome written into the claim boundaries;
- E5 done and F9 frozen;
- E7 done, so RQ4 is not controller-specific;
- E12 either run or documented as unavailable;
- every failed or inverted result folded into `03_FROZEN_CLAIMS.md`.

E4, E6, E8, E9, E10 are strongly preferred but not blocking. **All of them are now done**, as
is E11 — §4.37/F21, §4.38/F22, §4.40/F23, §4.41/F24, §4.42/F24, and Fig 4B unblocked.
**The twelve-item queue is complete.** Findings run F1–F24; experiment sections run §4.1–§4.42.
E12's pre-assigned §4.43 was **not written**: its output is a candidates table and a search-
coverage record, which lives in `proto/out/E12_triage.md` and is summarised in
`03_FROZEN_CLAIMS.md` §D non-claim 9. Nothing else is missing.

The goal is not zero possible reviewer questions. It is that every *obvious* methodological
escape hatch has either been tested or explicitly declined in print.

---

# 7. Not doing, with reasons

| Declined | Reason |
|---|---|
| **Problem-space traffic generation for the padding attack** (checklist §5, Exp 4A) | **Still declined, and the reason is now stronger.** The cost question is settled by arithmetic: §4.40/F23 prices suppression of one alert at **34 flows = 13.3 kB = 15 bit/s** over the 2 h bucket from one host, so a testbed emitting 34 `curl` calls would confirm a number we compute exactly. The *placement* question — pads must land on the target's own `(SrcIP, DstIP)` pair — is settled structurally: the detector's 33 features carry **no endpoint identity**, so a score cannot depend on the host pair (§4.30, `t46_hostpair_padding.py`). It could not have been settled empirically: all **674** detected episodes across five windows × two seeds sit on 100%-malicious host pairs, so LSPR23 has no ordinary traffic on an attack pair. A testbed would also replace live-fire data with synthetic and would exercise *our* flow meter rather than LSPR23's, confounding the result. **The one thing it would still add** is coverage of detectors whose features are conditioned on endpoint identity — host reputation, per-host baselines — for which the structural argument fails. That limit is stated in print (§4.30 scope, `03_FROZEN_CLAIMS.md` §C caveat 5) rather than tested. |
| More classifiers | Two is the target; the second gives an identical feasibility margin and zero detections (§4.22) |
| More `q` values, spending sequences, cap policies, padding pools, procedures | Swept (§4.24, §4.25, §4.20, §4.30). Diminishing value, and named in the checklist's own "do not spend time on" list |
| Another CIC-style dataset without campaign labels | Fails E12's required property by construction |
| Re-running the pre-committed slot rule | Done: §4.16 corollary, §4.12 policy D. E3 extends it |
| Proximity-to-attack-period metric | Degenerate on this window — both the tail and ordinary benign flows have a nearest malicious flow at 0.0 s (`06_PHASE3_REPORT.md` §1.5) |
| Exhaustive hyperparameter search | E6 answers the selection objection without it |

---

# 8. Recording results

Pre-assigned so nothing collides:

| Experiment | Section | Findings |
|---|---|---|
| E1 | §4.34 | F18 (resolution ↔ stability tradeoff); narrows F1 if it fires |
| E2 | §4.35 | F19 (restart: per-epoch vs pooled guarantee); narrows F1/F2 if it fires |
| E3 | §4.36 | extends F7; possibly F20 (the robustness/power/ordering triangle) |
| E4 | §4.37 | F21 (calibration contamination tolerance) |
| E5 | extends §4.31 | tightens F9 wording only |
| E6 | §4.38 | F22 (parameter transfer) |
| E7 | §4.39 | extends F13 |
| E8 | §4.40 | extends F6, F17 with operational units |
| E9 | §4.41 | appendix note |
| E10 | §4.42 | extends F6 across windows |
| E12 | ~~§4.43~~ `proto/out/E12_triage.md` | upgrades or narrows F3/F4 — **neither**; the triage record is itself the answer |

For each: add the `## 4.N` section, update the affected findings, update the §5 claim-strength
table, add the script to the §8 reproduction list, and tick the box here.

---

# 9. Reviewer questions this queue must leave answerable

From `08_satml_reviewer_gap_experiment_checklist.md` §17. Tick as each is closed.

`[x]` 1 Why not randomise/smooth the conformal p-values? → §4.34, F18: it works, and buys no
      reliably-detected episode; negative yield under an arbitrary-dependence-valid merge
`[x]` 2 Why not use continuous e-values? → §4.34, F18: strictly dominated for every calibrator
      including Vovk's; 0 rejections at λ ≥ 0.25 at the guarantee window
`[x]` 3 Why not reset the FDR controller every day? → §4.35, F19: because a day is longer than
      any measurable deployment window here (26.98 h max), and because the deployment-level
      guarantee degrades to `1 − (1 − q)^n`. Resetting more often works well otherwise
`[x]` 4 Why not batch hypotheses? → §4.35, F19: an α-budgeted restart preserving a
      deployment-level `q` keeps 46% of the gain; spending `n·q` keeps all of it and the
      pooled guarantee is then only `1 − (1 − q)^n`
`[x]` 5 Why believe heuristic episodes reflect incidents? → answered as a limitation; §4.9, §4.29
`[x]` 6 Does the granularity result replicate with true campaign IDs? → unanswerable: no public
      dataset provides them (`proto/out/E12_triage.md`). Stated as a limitation in print
`[x]` 7 Can an attacker actually generate the padding traffic? → **yes, trivially.** §4.40, F23:
    34 flows = 13.3 kB = **15 bit/s** over the 2 h bucket from one host, using the black-box
    pool that needs no detector access. §4.42, F24: the attack is measurable at all five window
    positions, and the black-box pool never fires at any of them. Testbed 4A declined in print
`[x]` 8 Can asymmetric aggregation stop the attack? → §4.36, F20: **no.** Every precommitted
      weighting has a finite front-load cost; the schemes that keep recall fall to 1–8 leading
      flows against 111 appended. The escape makes the attack cheaper
`[x]` 9 Does the padding attack need white-box access? → no; §4.30
`[x]` 10 Are the position-0.85 "false alerts" label errors? → best-supported, not proved; §4.31, §4.32, E5 tightens
`[x]` 11 Does the result depend on one feedback controller? → §4.39: **no.** P, PI and
      Robbins-Monro quantile targeting agree to three decimals from 4 h of delay onward
`[x]` 12 Does realistic feedback delay change it? → §4.39: **yes, drastically.** FDP 0.053 at
      zero delay, 0.402 at fifteen minutes, 0.877 at a daily cycle vs 0.887 with no feedback
`[x]` 13 Were headline parameters chosen on test data? → §4.38, F22: **no**, and the evidence is
    that both frozen parameters are the *worst* configuration on their grid at some window. The
    cap choice transfers (worst normalised regret 0.070); the grouping choice does **not**
    (0.991), and that is named as a limitation rather than smoothed over
`[x]` 14 What if calibration is contaminated? → §4.37, F21: **it stops working at ONE mislabelled
    attack flow.** Not a rate — a flow. Random mislabels have scale 1.1–1.3 flows. Validity
    survives: the only anti-conservative channel is bounded by `(1+ε)` and costs the attacker
    the power attack entirely
`[x]` 15 Does ordering at tied timestamps matter? → §4.41, F24: **no.** ≤1.3% of episodes are
    tie-movable, and 50 randomised orders change none of 36 statistics at either window. One
    appendix sentence
`[x]` 16 How expensive are the attacks in bytes/second? → §4.40, F23: 15 bit/s to suppress one
    alert; 33.4 Mbit/s for the ADDIS state attack. **Bandwidth is not what separates them** —
    volume against the monitored population is: 37.5× the deployment window's own flow count
`[x]` 17 Which claims are theorem-backed vs empirical? → `03_FROZEN_CLAIMS.md`
`[x]` 18 Which guarantees hold under the actual LSPR23 evidence? → §4.20, §4.26, §4.31

---

# 10. After the freeze

Writing order (`07_phase3_next_step_recommendation.md` §7): problem formulation → threat model →
feasibility theory → padding/aggregation theory → experimental setup → RQ1 feasibility → RQ2
granularity → RQ3 attackability → RQ4 operational value → discussion/limitations →
introduction → related work → abstract.

The introduction goes late: the contribution is now much sharper than the project's original
motivation, and writing it early would import the old framing.
