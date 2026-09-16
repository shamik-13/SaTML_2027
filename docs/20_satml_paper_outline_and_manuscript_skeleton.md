# SaTML Paper Outline / Manuscript Skeleton

## Working title

**When Guarantees Go Silent: Feasibility and Attackability of Online Error Control for ML Intrusion Detection**

Alternative title:

**Attacking the Trust Layer: Feasibility Limits of Online Error Control for ML Intrusion Detection**

---

# Abstract

Keep the abstract tightly structured.

## Sentence 1 — Problem

ML intrusion detectors emit enormous streams of predictions, while statistical error-control methods promise interpretable guarantees on the resulting alerts.

## Sentence 2 — Gap

Existing guarantees do not by themselves establish that useful discoveries remain statistically feasible at security-scale horizons, nor that the decision layer is robust to adversarial manipulation.

## Sentence 3 — Contribution 1

State the finite-resolution result:

> Under discrete finite-resolution conformal evidence and uninterrupted online controllers from the covered structural families, bounded evidence creates a finite discovery horizon.

## Sentence 4 — Contribution 2

State the granularity result:

> Coarser security units reduce the number of hypotheses and restore feasibility, but at measurable cost in episode-level resolution.

## Sentence 5 — Contribution 3

State the attack result:

> The aggregation and state mechanisms used by the trust layer expose two attack surfaces: within-hypothesis padding and across-hypothesis controller-state manipulation.

## Sentence 6 — Evaluation

Mention:

- LSPR23 live-fire stream;
- 16M+ flows;
- multiple deployment windows;
- two detectors;
- modern online procedures;
- smoothing;
- restarts;
- asymmetric aggregation;
- feedback baselines;
- attack analyses.

## Sentence 7 — Main implication

Suggested closing idea:

> Statistical trust layers for security ML must therefore be evaluated not only for nominal error guarantees, but also for feasibility, semantic granularity, and adversarial robustness.

Do **not** put every numerical result in the abstract.

---

# 1. Introduction

Target: approximately 1–1.25 pages.

> **Budget check, against the actual SaTML 2027 rules.** The limit is **12 pages of BODY
> TEXT**; references and appendices are unlimited and do not count, and the mandatory Open
> Science section (plus Ethical Considerations and any LLM-usage statement) sits before the
> references and is also excluded. §1–§10 as targeted sum to **9.5–10.25 pages**, so with §11
> at 0.75 and §12 at 0.25 the body lands at **10.5–11.25 — roughly a page of slack**, not the
> deficit a references-inclusive reading would suggest.
>
> Spend that page on §6, not on §4: §6 carries three theorems and two attack surfaces at 1.5
> pages and is the tightest section in the plan. Everything that does not fit belongs in an
> appendix rather than being cut, since appendix space is free — but **reviewers are not
> required to read appendices**, so no load-bearing claim may live only there.
>
> Formatting is `\documentclass[conference]{IEEEtran}` at the default 10pt and geometry.
> Changing font size, margins or spacing to fit more content is **grounds for desk
> rejection**, so the page budget is a real constraint and cannot be recovered by formatting.

## 1.1 ML security alerts need more than detector accuracy

Motivate the operational pipeline:

```text
network traffic
      ↓
ML detector
      ↓
millions of anomaly scores
      ↓
which ones become analyst alerts?
```

Traditional detector evaluation focuses on:

- AUROC;
- AUPRC;
- F1;
- threshold recall.

Operational question:

> An analyst cares about how many surfaced alerts are actually attacks.

Introduce false discoveries as the operational quantity.

## 1.2 Why online error control looks attractive

Briefly motivate online FDR.

\[
FDP_t=\frac{V_t}{R_t\vee1},
\qquad
FDR_t=\mathbb{E}[FDP_t].
\]

Security data arrive sequentially, so online testing appears attractive:

> continuously issue alerts while controlling false discoveries.

Do not derive LORD/LOND/etc. in depth here.

## 1.3 The missing systems question

Introduce the paper's central systems observation:

> A valid statistical guarantee is useful only if the evidence available from the ML detector can actually cross the statistical rejection threshold.

Show the composed system:

```text
ML detector
    ↓
calibrated evidence
    ↓
aggregation
    ↓
online controller
    ↓
SOC alert
```

Key framing:

> The statistical trust layer is part of the ML security system, not an innocent wrapper around it.

## 1.4 Three tensions we uncover

### Tension 1 — Evidence resolution vs horizon

Finite evidence ceiling versus shrinking online testing levels.

### Tension 2 — Granularity vs guarantee

Coarser grouping reduces the number of hypotheses but changes what constitutes a discovery.

### Tension 3 — Statistical validity vs adversarial robustness

Aggregation/state rules that make the controller usable can themselves be manipulated.

## 1.5 Contributions

Use exactly three numbered contributions.

### C1 — Feasibility boundary

> We characterize when finite-resolution conformal evidence can support online rejection at security-scale horizons.

State the required scope explicitly:

- finite-resolution/discrete evidence;
- uninterrupted controller;
- covered structural procedure families.

Mention that randomized smoothing and periodic restart are tested as boundary cases rather than hidden exceptions.

### C2 — Granularity–guarantee tradeoff

> We show that coarsening the security decision unit restores feasibility exactly by reducing the number of hypotheses, while changing episode-level resolution.

Mention restart as another lever that preserves granularity but changes how the guarantee composes across epochs.

### C3 — Statistical trust layer as attack surface

> We identify and characterize within-hypothesis and across-hypothesis attacks against the statistical decision layer.

Include:

- symmetric padding impossibility;
- asymmetric/front-loading escape closure;
- ADDIS evidence-conditioned state manipulation.

---

# 2. Background and System Model

Target: approximately 1 page.

## 2.1 ML intrusion-detection pipeline

Define the sequential observations:

\[
x_1,x_2,\ldots
\]

ML detector:

\[
s_t=f(x_t).
\]

Calibration set:

\[
C=\{z_1,\ldots,z_n\}.
\]

Then introduce calibrated p/e evidence.

## 2.2 Conformal evidence

Explain the rank-\(k\) threshold evidence.

Key finite ceiling:

\[
M=\frac{|C|+1}{k}.
\]

This equation should be visually prominent.

Explain the intuition of \(k=1\), but save the empirical consequences for later.

**State the calibration premise here, where the construction is defined.** Every guarantee and
every detection number in the paper assumes the calibration set is attack-free. Say so at the
point the set is introduced rather than deferring it to limitations — §9.2 then quantifies what
the assumption is worth, and the answer is small enough that a reader should meet it early.

## 2.3 Security-semantic grouping

Explain why raw detector predictions are not necessarily analyst alerts.

Possible units:

```text
flow
 ↓
host-pair/time episode
 ↓
host episode
 ↓
campaign / incident
```

Define a group:

\[
G_j.
\]

Define aggregated evidence:

\[
E(G_j).
\]

Important terminology rule:

> LSPR23 does not provide usable flow→campaign ground truth, so deployable units in the paper are **episodes**, never incidents.

## 2.4 Online error-control procedures

Briefly define:

- LOND;
- LORD++;
- e-LOND / e-LORD / e-GAI;
- ADDIS;
- online e-BH.

Focus on the property that matters:

\[
\alpha_t
\]

and **what index advances the spending sequence**.

A compact procedure-comparison table would be useful.

Suggested columns:

- procedure;
- evidence type;
- spending index;
- horizon knowledge;
- dependence assumptions;
- covered by feasibility theorem?;
- escape mechanism;
- guarantee status on current evidence.

## 2.5 Security-system metrics

### Statistical metrics

\[
FDP,\quad FDR.
\]

### Detection metrics

- malicious-flow coverage;
- episode recall;
- time to first detection.

### Operational metrics

- alerts/day;
- analyst budget.

### Feasibility metric

Define the feasibility margin once and reuse it consistently.

---

# 3. Threat Model

Target: approximately 0.5 page.

## 3.1 Defender

The defender controls:

- ML detector;
- calibration set;
- grouping rule;
- evidence construction;
- online error controller.

## 3.2 Adversary

The attacker may control network behavior from compromised or attacker-controlled hosts.

Capabilities may include:

- adding benign-looking traffic to an episode;
- influencing timing/order;
- creating precursor episodes;
- knowing some controller parameters.

## 3.3 Knowledge levels

### White-box

Knows detector/statistical state.

### Grey-box

Knows procedure and parameters but not exact current state.

### Black-box

No score access; generates ordinary traffic.

## 3.4 Out of scope

Explicitly exclude:

- poisoning or retraining **the detector's training set**;
- compromising the SOC;
- arbitrary modification of stored scores;
- claiming attacks are already observed in the wild.

**Draw this line explicitly, or §9.2 will read as a contradiction.** Contaminating the
**calibration** set is *in* scope and is measured (§9.2): it requires only that a labeller
miss an attack flow, not that the adversary reach the training pipeline. Training-set
poisoning and calibration contamination are different capabilities with different
prerequisites, and the paper takes only the second.

---

# 4. When Can an Online Guarantee Produce Any Alert?

This is the theoretical core for C1.

Target: approximately 1.25–1.5 pages.

## 4.1 Evidence ceilings meet shrinking rejection levels

Start from:

\[
E_t\le M.
\]

A rejection requires:

\[
E_t\ge\frac{1}{\alpha_t}.
\]

Therefore:

\[
\alpha_t\ge\frac{1}{M}.
\]

Give this intuitive derivation before formal theorem notation.

## 4.2 Finite discovery horizon

State the formal theorem/proposition.

For the covered procedure families during a rejection-free run, show that rejection-compatible times are finite.

Do **not** say:

> all online FDR methods eventually die.

Instead state the structural families exactly.

## 4.3 Horizon-uniform feasibility bound

Derive:

\[
|C|\ge \frac{kT}{w_0}-1.
\]

Give security-scale examples.

Example values from the frozen result may include:

\[
|C|_{\min}\approx 6.4\times10^8
\]

at LSPR23 scale, and a much larger requirement for a one-day high-rate stream.

Use only exact frozen numbers in the final manuscript.

## 4.4 Which procedures escape?

This subsection is essential.

### ADDIS

Explain its escape:

- its spending index counts selected/tested hypotheses rather than elapsed time.

### Online e-BH

Explain its escape:

- fixed-point decision over the whole history;
- rejection-free prefix is not necessarily absorbing.

### e-GAI / mem-e-LORD

Explain why they do not solve the pre-first-rejection problem in this setting.

This subsection demonstrates that theorem scope is deliberate.

## 4.5 Boundary test I: randomized smoothing

Present the reviewer-gap experiment here.

Main result:

- smoothing removes the hard floor;
- absorbing state disappears;
- reliable detections do not improve;
- alert-set instability increases;
- dependence-valid merging yields lower useful detection.

Interpretation:

> Hard impossibility becomes soft vanishing probability.

Useful quantities to report:

- number of episodes detected with probability \(\ge 0.9\);
- alert-set Jaccard or disagreement across seeds;
- variance in rejection count;
- dependence-valid merge performance.

## 4.6 Boundary test II: periodic restart

Show that restart genuinely restores detection.

Then state the price:

\[
FDR_{\text{per epoch}}
\not\Rightarrow
FDR_{\text{deployment}}.
\]

Use the exact pooled-FDR composition result if included in the frozen claim.

Important interpretation:

> Restart changes the statistical question rather than simply “fixing” the controller for free.

## 4.7 Section takeaway

Use a highlighted summary:

> **Finite-resolution evidence + uninterrupted sequential control creates a hard feasibility horizon. Removing either premise is possible, but introduces measurable costs in stability, power, or guarantee composition.**

---

# 5. The Granularity–Guarantee Tradeoff

This is C2.

Target: approximately 1 page.

## 5.1 Why granularity changes the statistical problem

At the flow level:

\[
T=T_{\text{flows}}.
\]

At an episode level:

\[
T=T_{\text{episodes}}\ll T_{\text{flows}}.
\]

Since:

\[
|C|_{\min}
=
\frac{kT}{w_0}-1,
\]

grouping buys feasibility directly by reducing \(T\).

## 5.2 Deployable grouping families

Describe the families briefly:

- source–destination;
- source host;
- time bucket;
- other frozen deployable definitions.

Do not enumerate all configurations in prose.

Full sweeps belong in the appendix.

## 5.3 Empirical granularity curve

This should be a main figure.

Across the grouping grid, report:

### Malicious-flow coverage

roughly stable.

### Episode recall

falls materially as groups become coarser.

Main interpretation:

> The detector sees essentially the same malicious flow mass, but the analyst-facing semantic unit changes.

**Claim the shape, not the level.** Window-to-window variation of the *best achievable* flow
coverage (0.676) is larger than the spread across configurations within any single window, and
the coverage-optimal grouping does not transfer between windows (§9.4). So the monotone
tradeoff is the result; the absolute numbers on any one curve are that window's, and a
reviewer who re-runs at a different position will not reproduce them. State this next to the
figure rather than in limitations — it is cheap to say and expensive to be caught on.

## 5.4 Coarsening is not the only solution

Compare restart with coarsening.

Show that restart can preserve fine episode granularity and restore detection, but changes how guarantees compose across time.

Sharpen the contribution:

> The tradeoff is not simply granularity vs feasibility. It is granularity vs the form of deployment-wide statistical guarantee under uninterrupted testing.

## 5.5 Generality limitation

State explicitly:

- one live-fire exercise;
- five quasi-independent windows, not five datasets;
- no genuine flow→campaign ground truth;
- deployable episodes, not incidents;
- the grouping optimum is window-specific (§9.4), so coverage numbers are what the
  *deployable* grouping achieves, never the best achievable.

Mention that a broad public-dataset triage failed to find a benchmark satisfying campaign identity + complete negatives + chronology.

Do not overstate external generality.

---

# 6. The Statistical Trust Layer as an Attack Surface

This is C3 and likely the most security-oriented section.

Target: approximately 1.5 pages.

## 6.1 Attack surface A: within-hypothesis padding

Suppose group evidence is:

\[
E(G)=F(e_1,\ldots,e_m).
\]

The attacker appends benign-looking evidence:

\[
F(e_1,\ldots,e_m,0,\ldots,0).
\]

Explain why the attack is aimed at the statistical trust layer rather than the detector.

## 6.2 Symmetric padding impossibility

State the theorem:

For any:

\[
\tau>1,
\]

no symmetric e-merging family that can attain \(	au\) can be universally \(	au\)-padding robust.

Give proof intuition in the main paper.

Move detailed proof to the appendix.

## 6.3 Real-network suppression cost

Report the main empirical range from the frozen results.

Show:

- median suppression cost;
- differences across deployment windows;
- insensitivity to padding-pool realism;
- black-box benign pool behavior;
- cross-window transfer of the attack.

Important point:

> The attack should not look like an artifact of the anomalous position-0.85 window.

Be precise about what the cross-window result does and does not say: the attack is measurable
at **every** window that produces detections, but it is **not uniformly cheaper** outside the
anomalous one — one window is roughly twice as expensive as 0.85. Claim "not confined to",
never "cheaper everywhere"; the pooled median is driven by two cheap windows.

### Can the attacker put the pad flows where they have to go?

**Answer this explicitly — it is the first thing a security reviewer asks, and the outline is
otherwise silent on it.** The grouping key is \((\mathrm{SrcIP},\mathrm{DstIP},\text{bucket})\),
so pads must land on the *target's own host pair*: the attacker sends ordinary traffic to the
host they are already attacking. None of the padding pools is matched that way, so the cost
model rests on the assumption that attacker-generated ordinary traffic to the victim scores
like ordinary traffic anywhere.

The argument has to be **structural, and the paper should say why**: it could not be measured,
because every detected episode across all windows and seeds sits on a host pair carrying only
attack traffic, so the dataset contains no ordinary traffic on an attack pair to build a
matched pool from. What settles it instead is the feature set — the detector scores a flow
from protocol plus per-flow timing and volume statistics, with **no endpoint identity among
them**, so a score cannot depend on which host pair a flow sits on and the black-box pool's
firing rate of exactly zero transfers to the attack pair by construction.

State the scope this buys and its limit in the same breath (see §10.4): this is a property of
**flow-level** feature sets. A detector using host reputation or per-host baselines would break
the argument, and for such a detector the transfer would have to be shown on a testbed.

## 6.4 Can asymmetric aggregation fix it?

Present the natural reviewer escape:

> use precommitted asymmetric weights.

Then state the result:

Every summable precommitted weight sequence has finite front-load cost:

\[
L^*
=
\min\left\{
L:
\sum_{i>L}w_i<\beta
\right\}.
\]

Empirically, equal-recall padding-invariant schemes can be defeated by a small number of leading flows.

Frame the triangle:

\[
\boxed{
\text{padding invariance}
\quad
\text{usable power}
\quad
\text{ordering robustness}
}
\]

**Pick two.**

This is a good graphical callout.

## 6.5 Attack surface B: controller-state manipulation

Introduce ADDIS.

Key observation:

> Its escape from the hard feasibility horizon comes from conditioning future spending on observed evidence.

That property becomes manipulable.

## 6.6 Closed-form ADDIS state attack

State:

\[
B^*=203
\]

for the studied configuration.

Explain:

- exact;
- structural;
- grey-box feasible;
- expensive in absolute volume.

Do **not** frame it as a cheap practical attack.

## 6.7 The two attack surfaces coincide

This should be one of the strongest subsections.

For the majority of detected ADDIS episodes in the studied configuration, the minimum padding required to suppress the current alert also advances the ADDIS spending state.

Conceptual statement:

\[
\boxed{
\text{suppress current alert}
\Longrightarrow
\text{degrade future controller state}
}
\]

Use the exact frozen numerator/denominator when drafting.

---

# 7. Experimental Methodology

Put this after the conceptual/theoretical core.

Target: approximately 1 page.

## 7.1 Dataset

Describe LSPR23.

Report:

- total flow count;
- malicious fraction;
- live-fire setting;
- chronology;
- sorting requirement.

## 7.2 Chronological protocol

Use a diagram:

```text
training
   ↓
calibration
   ↓
deployment
```

No leakage.

Mention the five deployment positions.

## 7.3 Detectors

### Primary

HistGradientBoosting.

### Robustness

Isolation Forest.

Explicit statement:

> Detector novelty is not a contribution.

## 7.4 Statistical procedures

List:

- LOND;
- LORD++;
- e-LOND / e-LORD / e-GAI;
- ADDIS;
- online e-BH;
- smoothing / continuous evidence variants where relevant.

## 7.5 Grouping and evidence aggregation

Describe the frozen grouping.

Important:

> The chosen grouping should be reported as a deployable configuration, not an oracle optimum.

**This is now a measured result, not a caution — state it as one** and cross-reference §9.4.
The selection protocol is worth one sentence here: configurations are chosen on a *previous*
window and evaluated on the next, never on the window they are reported at, and the
feasibility gate is applied before selection because it is a function of \(|C|\), \(k\) and
\(T\) alone.

This prevents the manuscript from implying the selected grouping is universally best.

## 7.6 Evaluation metrics

Use the metrics already defined in Section 2.

Avoid redefining them.

## 7.7 Reproducibility / audit

Briefly mention:

- full-stream evaluation;
- implementation cross-checks;
- unit tests;
- adversarial code/result audits;
- claim-freezing procedure.

Keep this compact.

---

# 8. Operational Evaluation

This answers RQ4.

Target: approximately 0.75 page.

## 8.1 Matched operating points

Compare methods at:

- matched alert budget;
- matched empirical FDP;
- Pareto frontier.

Do not compare arbitrary \(q=0.05\) against arbitrary classifier thresholds.

## 8.2 How much control does \(q\) give the operator?

Show that:

- changing \(q\) changes recall less than changing the spending sequence;
- nominal FDR target does not map cleanly to an intuitive analyst operating point.

Operational conclusion:

> formal error control can reduce the operator's freedom to choose the desired workload/recall tradeoff.

## 8.3 Analyst feedback

Compare:

- proportional feedback;
- PI controller;
- Robbins–Monro / quantile targeting.

Use wall-clock delays, and **quote the number rather than the adjective**. "Deteriorates
rapidly" understates it: against a 0.05 target, FDP reaches **0.402 at fifteen minutes** of
disposition delay, because more than half the alerts in that window are issued before any
label returns. By a 24 h cycle the controller is indistinguishable from no feedback at all.

Key interpretation:

> Direct feedback is competitive when analyst disposition is effectively immediate, and the
> window in which that holds is measured in minutes, not in alerts.

**Include the result that is more surprising than the delay curve.** The controller sits at its
actuator limit for 95–100% of steps, so most of its measured advantage is the conservative
threshold it saturates against rather than the steering itself. A reader who assumes the
feedback loop is doing the work has the wrong model of why the baseline performs well.

Also state that the conclusion is not controller-specific: proportional, PI and Robbins–Monro
quantile targeting agree to three decimals from four hours of delay onward. That is what makes
the delay result a property of the *problem* rather than of one hand-tuned controller.

Do not claim formal no-feedback control always dominates.

---

# 9. Robustness and Failure Analyses

Target: approximately 0.75 page.

Move most detailed tables to appendix.

## 9.1 Calibration validity and label anomaly

Discuss position 0.85.

Explain:

- localized anomaly;
- a handful of host pairs carry most extreme-tail events;
- post-compromise label error is the best-supported explanation;
- not proven.

Mention near-neighbour and per-feature evidence.

Maintain the distinction:

> empirical FDP at this position is measured against labels, not theorem-backed FDR.

## 9.2 Calibration contamination

Present as a supporting result.

At \(k=1\), one adversarial high-scoring contaminating calibration example can eliminate detection power.

Main lesson:

> contamination tolerance is a count, not a rate.

**Give the second half too — contamination is not purely a power effect.** The threshold
conformal p-value carries the evidence ceiling \(M=|C|+1\) in its *denominator*, so a
contaminating flow that scores *below* the calibration maximum raises \(M\) without moving
the threshold and multiplies every firing flow's p-value by \(1/(1+\varepsilon)\). That is
anti-conservative — a validity effect, not a power one — and the FDR guarantee degrades from
\(q\) to at most \(q(1+\varepsilon)\) for the sum-of-offered-levels procedures.

The two channels are wildly asymmetric, and **that asymmetry is the point of the subsection**:

> Power dies at one flow and is unbounded. Validity degrades by a factor that would need a
> contaminating set the size of the whole calibration set to double.

Two qualifications travel with \(q(1+\varepsilon)\): it is *multiplicative on top of* the
position-0.85 anti-conservatism of §9.1, not a replacement for it; and it is stated for the
procedures whose bound is a sum of offered levels, not for online e-BH.

Do not make this a fourth contribution.

## 9.3 Timestamp/order robustness

One compact statement:

- randomized tie ordering does not affect reported statistics.

Detailed numbers can go appendix.

## 9.4 Were the parameters chosen on the window they are reported at?

**This is the reviewer question the paper cannot leave unanswered, and the answer is
affirmative and slightly awkward — which makes it more convincing, not less.** Keep it here
rather than in methodology: it is a robustness result about the whole paper.

Protocol: five deployment windows, two detector seeds. Select a configuration on window
\(j-1\), evaluate on \(j\) (four ordered pairs); and select on four windows, evaluate on the
held-out fifth (five folds). Objective is **malicious-flow coverage**, not episode recall —
the grouping family sets recall's denominator, so selecting on recall selects coarseness, and
the two objectives disagree at 5 of 5 windows.

Report three things, in this order:

1. **The frozen configurations are not tuned — they are near-worst.** The headline grouping is
   the worst *feasible* configuration of 35 on one window and within \(10^{-4}\) of the worst
   on two more; the frozen cap is the worst of six on two of five windows. Nobody tunes on a
   test window to reach the worst configuration. Say it that way: the evidence against tuning
   is the *direction* of the result, not a small regret.
2. **The cap choice transfers; the grouping choice does not.** Worst previous-window
   normalised regret 0.070 for the cap against 0.991 for the grouping. Do not average these
   into one number.
3. **Why the frozen cap is not the powerful one.** A power-only selection picks a much smaller
   cap whose median front-load defeat cost is **one flow** and under whose raw rule ~39% of
   groups are not valid e-values. The cap was chosen for validity and attack cost, and that is
   the correct reason.

Note that the feasibility gate is applied before selection: it depends on \(|C|\), \(k\) and
\(T\) only, so it is not a tunable parameter and an "oracle" allowed to pick an infeasible
configuration is an unattainable upper bound rather than an oracle.

Detailed folds belong in the appendix.

## 9.5 What did not work

A short negative-results paragraph is valuable.

Examples:

- catastrophic calibration drift was not observed;
- fragmentation attack failed;
- inflation attack failed;
- mem-e-LORD does not help before the first rejection;
- boosting does not recover power for two-point evidence;
- smoothing removes the hard floor but does not restore reliable detection;
- asymmetric weighting is not a free mitigation;
- the grouping optimum does not transfer across windows;
- episode recall is not a usable objective for selecting a grouping family;
- the controller-state attack is not out of reach on *bandwidth* — only on volume;
- randomised tie ordering changes nothing;
- the padding attack is not confined to the anomalous window.

**Some of these refute our own earlier expectations, and saying so is worth the space.** Four
of the late experiments changed a claim rather than confirming one. A reviewer reads that as
a group that tested its own framing rather than only its hypotheses.

Full list belongs in appendix.

---

# 10. Discussion

Target: approximately 0.75–1 page.

## 10.1 What should a security practitioner do?

Provide constructive guidance.

### If deployment-wide FDR matters

Respect evidence-resolution and horizon requirements.

### If fine alert resolution matters

Restarting may preserve resolution, but changes how guarantees compose.

### If grouping is used

Treat aggregation as adversarially exposed.

### If analyst labels arrive quickly

Feedback control may be operationally preferable.

## 10.2 Guarantee semantics matter

Distinguish:

- per-flow;
- per-episode;
- per-epoch;
- deployment-wide.

One of the paper's broader lessons:

> A guarantee is meaningful only relative to the unit and time horizon over which it is defined.

## 10.3 Threat-model implications

Statistical testing often assumes observations/hypotheses are passive.

Security observations may be attacker-generated.

Therefore:

> evidence aggregation and controller state must themselves be threat-modeled.

This is a strong SaTML message.

## 10.4 Limitations

Be explicit.

### Single live-fire dataset

Five windows are not five independent datasets.

### No campaign ground truth

Episodes only.

### Position 0.85

Empirical FDP there is not a theorem-backed guarantee.

### ADDIS attack

Structural and grey-box feasible; absolute volume is dataset-specific and large.

### Attack-cost estimates

Some are lower bounds because realized detector evidence is used.

### Padding transfers because the features are flow-level

The claim that an attacker can place pad flows on the target's own host pair rests on the
detector's features carrying no endpoint identity (§6.3). It is structural rather than
measured, and it is **scoped to flow-level feature sets**: a detector using host reputation,
per-host baselines, or any feature conditioned on endpoint identity would need this shown on a
testbed. This is the one place where the problem-space traffic-generation experiment would
still have something to add.

### Scope of H1

Finite-resolution evidence + uninterrupted controller + covered procedure families only.

---

# 11. Related Work

Target: approximately 0.75 page.

Put this late so reviewers understand the contribution before the literature comparison.

## 11.1 Online FDR and alpha investing

Cover:

- LORD;
- LOND;
- SAFFRON;
- ADDIS;
- e-LOND/e-GAI;
- online e-BH;
- alpha-death.

Difference:

> This paper studies whether bounded ML-derived evidence can reach the required online rejection levels at security-scale horizons.

## 11.2 Conformal anomaly detection and finite resolution

Cover:

- conformal anomaly detection;
- security conformal work;
- resolution collapse;
- randomized smoothing;
- calibration-conditional validity.

Difference:

> Prior work studies calibration/resolution; this paper studies its interaction with sequential security alerting, semantic grouping, and adversarial manipulation.

## 11.3 Trustworthy ML intrusion detection

Cover:

- TESSERACT;
- Transcend / Transcendent;
- CALIBURN;
- NIDS evaluation methodology.

Difference:

> The target is the statistical decision layer after the detector.

## 11.4 Adversarial hypothesis testing and aggregation

Cover:

- adversarial hypothesis testing;
- test-score perturbation;
- e-merging;
- robust multiple testing.

Difference:

> The adversary manipulates the composition and sequential state of a live ML alerting system.

---

# 12. Conclusion

Target: approximately 0.25 page.

Keep this short.

Suggested structure:

1. Finite evidence + uninterrupted control can create a finite discovery horizon.
2. Grouping and restarting change feasibility but trade different statistical/operational properties.
3. The statistical trust layer must itself be threat-modeled because both aggregation and controller state can be adversarial surfaces.

Suggested final sentence:

> Trust guarantees for security ML should therefore be evaluated as properties of the **composed detection-and-decision system**, not of the statistical procedure in isolation.

---

# Appendix Skeleton

## Appendix A. Proofs

### A.1 Feasibility theorem
### A.2 Horizon-uniform optimum
### A.3 Symmetric padding theorem
### A.4 Asymmetric/front-load theorem
### A.5 ADDIS closed form
### A.6 Restart FDR-composition result

## Appendix B. Procedure Definitions

### B.1 LOND
### B.2 LORD++
### B.3 e-LOND / e-GAI
### B.4 ADDIS
### B.5 online e-BH
### B.6 smoothing and continuous calibrators

## Appendix C. Dataset and Preprocessing

### C.1 LSPR23
### C.2 chronology
### C.3 feature list
### C.4 detector setup
### C.5 calibration construction

## Appendix D. Full Experiment Matrices

### D.1 five deployment positions
### D.2 both seeds
### D.3 all grouping families
### D.4 all bucket widths
### D.5 \(k\)-sweep
### D.6 \(q\)-sweep
### D.7 spending sequences
### D.8 cross-window configuration transfer (all four ordered pairs and five leave-one-out folds, both seeds)

## Appendix E. Boundary Experiments

### E.1 randomized smoothing
### E.2 continuous e-values
### E.3 boosting
### E.4 restart schedules
### E.5 horizon misspecification

## Appendix F. Attack Experiments

### F.1 padding pools
### F.2 attack costs across windows
### F.3 cap policies
### F.4 asymmetric weights
### F.5 front-loading
### F.6 ADDIS state attack
### F.7 white-/grey-/black-box comparison
### F.8 attack costs in operational units (packets, bytes, sustained rate, attacker hosts)
### F.9 host-pair availability: why a matched padding pool cannot be built from this dataset

## Appendix G. Operational Baselines

### G.1 matched-budget thresholds
### G.2 proportional controller
### G.3 PI controller
### G.4 Robbins–Monro controller
### G.5 wall-clock delays

## Appendix H. Data-Quality Analyses

### H.1 position-0.85 tail forensics
### H.2 near-neighbour analysis
### H.3 per-feature analysis
### H.4 alert audit
### H.5 calibration contamination (both channels: threshold and ceiling)
### H.6 tie-order test

## Appendix I. Negative Results

Include the complete frozen list of hypotheses that were tested and refuted.

This is useful evidence of experimental thoroughness.

---

# Main-Paper Figure / Table Plan

Aim for approximately seven major visual elements.

## Figure 1 — System and Threat Model

```text
network flow
    ↓
ML detector
    ↓
conformal/statistical evidence
    ↓
group aggregation
    ↓
online error controller
    ↓
SOC alert
```

Mark:

- within-group padding attack;
- controller-state manipulation attack.

## Figure 2 — Feasibility Envelope

Plot minimum calibration size against deployment horizon.

Show procedure families and escape boundaries.

## Figure 3 — Granularity–Guarantee Tradeoff

Panels:

- feasibility margin;
- episode recall;
- malicious-flow coverage;

against grouping granularity.

## Figure 4 — Two Attack Surfaces

Two panels.

### Panel A

Padding amount vs alert suppression.

### Panel B

ADDIS coupling:

- suppress current alert;
- advance future controller state.

## Table 1 — Procedure Assumption Map

Suggested columns:

- procedure;
- spending index;
- horizon knowledge;
- dependence assumption;
- covered by H1?;
- escape mechanism;
- guarantee valid on current evidence?;
- main operational cost.

## Table 2 — Main Cross-Window Real Results

Suggested columns:

- position;
- detector;
- grouping;
- procedure;
- calibration size;
- feasibility margin;
- alerts;
- empirical FDP;
- episode recall;
- malicious-flow coverage;
- evidence-validity note.

## Figure 5 — Operational Frontier

Compare:

- online error control;
- fixed/matched thresholds;
- feedback controller;
- achievable frontier.

This answers:

> What does the formal guarantee actually buy the operator?

---

# Recommended Research Questions

## RQ1 — Feasibility

> Under what combinations of evidence resolution, calibration size, stream horizon, and online procedure can an ML security alert still be statistically rejected?

## RQ2 — Granularity

> How does changing the alerting unit from flows to deployable security episodes affect statistical feasibility, recall, and operational resolution?

## RQ3 — Attackability

> Can an adversary manipulate the composition or sequential state of statistically controlled alerts to suppress detection?

## RQ4 — Operational value

> What does formal online error control provide compared with matched-budget thresholds and feedback-based alert controllers?

---

# Paper Narrative in One Diagram

Use this as the writing guide:

```text
1. ML scores need an alerting guarantee
                 │
                 ▼
2. Finite evidence limits what an
   uninterrupted online controller can reject
                 │
                 ▼
3. Grouping reduces the hypothesis count
   and restores feasibility
                 │
                 ▼
4. But grouping changes security resolution
   and requires evidence aggregation
                 │
                 ▼
5. That aggregation is attacker-manipulable
                 │
                 ▼
6. Alternative controller designs can escape
   the hard horizon, but create other costs
   or manipulable state variables
                 │
                 ▼
7. Statistical trust layers must themselves
   be treated as security-critical ML system components
```

This is the paper's core narrative.

---

# Recommended Writing Order

Do **not** begin with the Introduction.

Write in this order:

1. Problem Formulation / System Model
2. Threat Model
3. Feasibility Theory
4. Padding / Aggregation Theory
5. Experimental Methodology
6. RQ1 Results — Feasibility
7. RQ2 Results — Granularity
8. RQ3 Results — Attackability
9. RQ4 Results — Operational Value
10. Robustness / Failure Analyses
11. Discussion / Limitations
12. Introduction
13. Related Work
14. Conclusion
15. Abstract

Reason:

> The technical core is already frozen and least likely to change. The introduction is easier to write once the exact story and figure flow are visible.

---

# Important Writing Rules

## 1. Do not organize the paper by experiment IDs

Avoid:

```text
T1
T2
T3
...
```

Instead organize by:

```text
RQ1 Feasibility
RQ2 Granularity
RQ3 Attackability
RQ4 Operational Value
```

Experiment IDs belong in internal notes / appendix only.

## 2. Keep exactly three headline contributions

Do not promote every interesting finding into a contribution.

Headline:

1. finite-evidence feasibility;
2. granularity–guarantee tradeoff;
3. attackable trust layer.

Supporting findings stay inside these.

## 3. Keep H1's boundary conditions every time it is stated

Never state the theorem without:

- finite-resolution/discrete evidence;
- uninterrupted controller;
- covered procedure family.

## 4. Keep H2's terminology precise

Say:

- episode;
- deployable grouping.

Do not say:

- incident;
- campaign;

unless genuine ground truth exists.

## 5. Do not oversell the ADDIS attack

Correct framing:

> structural, exact, grey-box feasible, and physically achievable in bandwidth but very large in volume.

Avoid:

> cheap practical attack.

## 6. Position 0.85 requires an explicit validity caveat

Every FDP number there is:

> empirical against labels.

It is not a theorem-backed FDR guarantee.

## 7. Treat negative results as a strength

Examples:

- smoothing removes the hard horizon;
- restart restores detection;
- asymmetric aggregation can be padding-invariant;
- several proposed attacks fail.

The contribution is stronger because the paper characterizes **when fixes work and what they cost**, rather than pretending every alternative fails.

---

# Explicit Non-Claims to Preserve

The final paper should explicitly avoid claiming:

1. all online FDR procedures necessarily become absorbing;
2. online FDR is unusable;
3. LSPR23 labels are globally wrong;
4. position 0.85 proves label error;
5. deployable episodes are true incidents;
6. the ADDIS state attack is cheap;
7. FDR control is always better than feedback;
8. grouping solves the problem for free;
9. a low empirical FDP at position 0.85 is a theorem-backed guarantee;
10. the second detector proves universality;
11. dependence itself breaks online FDR;
12. the paper proposes a new FDR algorithm.

---

# Final Suggested Thesis

> **Online statistical error control for ML intrusion detection faces a three-way tension between finite evidence resolution, alert granularity, and adversarial robustness. Fine-grained streams can exceed the discovery horizon of broad classes of online procedures under finite-resolution evidence and uninterrupted control; coarser security-semantic grouping restores feasibility at the cost of episode-level resolution; and the aggregation required to obtain that feasibility introduces an attacker-controlled suppression surface. Procedures that escape the first failure mode by conditioning future spending on observed evidence expose a second, history-dependent state surface, which can coincide with the same padding operation.**

---

# One-Sentence Paper Pitch

> **We show that the statistical layer added to make ML intrusion alerts trustworthy can itself become infeasible, change the security semantics of what is detected, and create new adversarial attack surfaces.**
