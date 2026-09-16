# Next Step After Phase 3

## Executive recommendation

Phase 3 has closed the major experimental questions. The anti-conservatism investigation is complete, the alert audit is complete with a stated residual, the ADDIS state-manipulation attack works, the experiment matrix is frozen, and the paper contract is already written.

The project should now move into **manuscript construction**, not another broad experimental phase.

The recommended strategy is:

1. close two cheap credibility gaps from A1;
2. start writing the paper immediately;
3. run a narrowly scoped second-dataset search in parallel;
4. do not reopen the experiment matrix unless a concrete reviewer objection requires it.

---

# 1. Close Two Cheap A1 Gaps

The current interpretation of the position-0.85 anomaly is appropriately cautious:

> the excess extreme-tail events are highly localized and are best explained by post-compromise traffic being labelled benign, but this is not proved.

That wording should stay.

Before finalizing the paper, I would close two inexpensive gaps.

## 1.1 Near-duplicate analysis

For the 46 extreme-tail benign-labelled flows, compute nearest-neighbour distance in standardized feature space to:

- labelled malicious flows;
- ordinary benign deployment flows;
- benign calibration flows.

A useful diagnostic is:

\[
rho(x) =
d(x, nearest malicious) /
d(x, nearest benign)
\]

If the tail consistently lies closer to malicious traffic, that strengthens the label-error interpretation.

If not, retain the current narrower interpretation.

Do not turn this into a larger representation-learning study.

## 1.2 Per-feature comparison

Compare the 46 tail flows with benign and malicious populations feature-by-feature.

For continuous variables, use standardized differences or percentile locations.

For categorical variables, report enrichment.

The question is simply:

> Do these flows look attack-like in raw feature space, or only according to the detector score?

## 1.3 Do not reopen proximity-to-attack-period analysis

The Phase 3 report already shows that nearest-malicious-flow timing is degenerate because this window is saturated with attack activity.

Drop this unless a later dataset provides genuine campaign/phase annotations.

---

# 2. Keep Position 0.85, But Change Its Role

Position 0.85 should remain in the paper because it is the only window where detector tail reach is high enough to reveal meaningful procedure behavior.

However, it should not be presented as the cleanest example of theorem-backed FDR control.

Use it as:

> **the high-tail-reach stress window where procedures and attacks can be observed, but where the statistical evidence itself is affected by a localized label anomaly.**

It can strongly support:

- feasibility comparisons;
- structural-silence comparisons;
- operating-point comparisons;
- padding attacks;
- ADDIS state manipulation;
- empirical FDP against provided labels.

It should not alone support:

> “Procedure X provably controls FDR at 5% on LSPR23.”

For general claims, rely on the five-window evaluation. For detailed attack and controller traces, use position 0.85 as an instrumented case study.

---

# 3. How to Use the Alert Audit

Do not present the 96.1% audit agreement as independent ground-truth validation.

The E2 evidence partly derives from the same label process being audited.

Treat:

- **E2** as a consistency check;
- **E1** as the genuinely independent evidence.

The strongest independent statement is:

> **3 of the 5 alerts labelled false by the dataset occur on red-team-confirmed compromised hosts.**

That is more valuable than a large aggregate agreement percentage.

If a human analyst can complete the 152-row `human_verdict` / `human_notes` pass, do it before submission.

If not, state transparently that the audit combines an automated consistency analysis with a smaller independently corroborated subset.

---

# 4. The ADDIS Attack Is a Structural Contribution, Not a Cheap Operational Attack

The ADDIS state-manipulation attack is real and exact.

However, the minimum front-loaded attack budget in the main configuration is about:

\[
9.2 x 10^7
\]

flows, around 5.6 times the complete LSPR23 stream.

Therefore do not headline:

> “ADDIS can be cheaply silenced in practice.”

The better claim is:

> **A procedure that avoids alpha-death by conditioning its spending index on observed evidence exposes that state variable to adversarial manipulation.**

This is a structural security result.

---

# 5. The Better ADDIS Headline Is the Coincidence of the Two Attack Surfaces

The strongest Phase 3 result is that, for 101 of 147 ADDIS detections, the cheapest padding that suppresses the current alert also moves the resulting p-value into the selected-but-noncandidate interval.

Therefore the same manipulation does two things:

\[
current alert suppression
\]

and

\[
future spending-state degradation.
\]

This is much stronger than the 92-million-flow number.

Use this as the main ADDIS observation.

The front-loaded state attack should be presented as a structural confirmation and closed-form bound.

---

# 6. Freeze the Paper Around Three Contributions

## C1. Finite-evidence feasibility boundary

With bounded evidence

\[
M = (|C|+1)/k
\]

and rejection threshold

\[
E_t >= 1/alpha_t,
\]

a rejection is possible only while

\[
alpha_t >= 1/M.
\]

For broad procedure families whose spending index advances with the hypothesis stream, finite evidence resolution therefore induces a finite discovery horizon.

The paper should explicitly define the boundary:

Covered examples:

- LOND;
- LORD++;
- e-LOND;
- e-GAI-family procedures satisfying the derived structural form.

Important escapes:

- ADDIS;
- online e-BH.

Do not claim that every online FDR procedure has an absorbing horizon.

## C2. Granularity-feasibility tradeoff

Coarsening the alerting unit reduces the hypothesis count and can restore statistical feasibility.

But this costs episode-level resolution.

The core empirical observation is:

\[
malicious-flow coverage approximately stable
\]

while

\[
episode recall decreases
\]

as grouping becomes coarser.

This is the main domain-specific trustworthy-ML result.

## C3. The statistical trust layer is an attack surface

Symmetric e-value aggregation is fundamentally vulnerable to attacker-controlled padding.

The paper has:

- a theorem;
- real detector evidence;
- real network data;
- realistic and black-box padding pools.

ADDIS then shows that evidence-conditioned spending exposes a second, history-dependent state surface.

The clean framing is:

\[
within-hypothesis attack
+
across-hypothesis state attack.
\]

Keep both under one contribution.

---

# 7. Start the Manuscript Now

Do not wait for another major experiment.

Recommended writing order:

1. Problem Formulation
2. Threat Model
3. Feasibility Theory
4. Padding / Aggregation Theory
5. Experimental Setup
6. RQ1: Feasibility
7. RQ2: Granularity
8. RQ3: Attackability
9. RQ4: Operational Value
10. Discussion / Limitations
11. Introduction
12. Related Work
13. Abstract

Writing the introduction late is useful because the actual contribution is now much sharper than the original project idea.

---

# 8. Main-Figure Budget

Use about seven major visual items.

## Figure 1 — System and threat model

Show:

flow -> ML detector -> statistical evidence -> group aggregation -> online controller -> SOC alert

Mark both attack surfaces:

- within-group padding;
- controller-state manipulation.

## Figure 2 — Feasibility envelope

Plot minimum calibration size against deployment horizon.

Show which procedure families encounter the finite-evidence barrier and which escape it.

## Figure 3 — Granularity-feasibility tradeoff

Panels:

- feasibility margin;
- episode recall;
- malicious-flow coverage;

against grouping granularity.

## Figure 4 — Two attack surfaces

Two panels:

A. padding amount vs suppression;

B. ADDIS coupling showing that minimal current-alert suppression also advances the spending state.

## Table 1 — Procedure assumption/boundary map

Include:

- procedure;
- spending index;
- horizon knowledge;
- statistical assumptions;
- feasibility theorem applies?;
- escape mechanism;
- guarantee status on current evidence.

## Table 2 — Cross-window real-data results

Use multiple windows, not only position 0.85.

Include:

- calibration size;
- detector tail reach;
- feasibility margin;
- alerts;
- episode recall;
- empirical FDP;
- evidence-validity note.

## Figure 5 — Operational frontier

Compare:

- online error control;
- matched thresholds;
- feedback controller;
- achievable frontier.

This should stay in the main paper because it answers what the formal guarantee buys the operator.

---

# 9. Second Dataset: Run in Parallel, Not Before Writing

This is the only remaining empirical extension likely to affect a headline result.

The goal is not to repeat the entire paper.

The goal is to obtain genuine:

\[
flow -> campaign / incident
\]

ground truth and validate the granularity result.

Minimum second-dataset experiment:

1. event-level feasibility;
2. true campaign-level grouping;
3. flow recall vs campaign recall;
4. one padding experiment.

Use a strict stop rule.

Continue only if the dataset has:

- chronological traffic;
- sufficient benign calibration data;
- reliable attack labels;
- genuine flow-to-campaign mapping;
- enough campaigns for meaningful analysis.

Stop if campaign reconstruction is manual, negatives are incomplete, or the dataset is too small.

The paper is already viable without this extension.

---

# 10. Do Not Add a Second Feedback Controller Yet

The current controller already establishes the main practical point:

- prompt feedback can select a useful operating point;
- large delay weakens that advantage.

A second controller is only necessary if, during writing, the comparison looks vulnerable to the objection:

> “This result is specific to your proportional controller.”

Otherwise leave it for future work or an appendix.

---

# 11. Final Answers to the Phase 3 Questions

## Q1. Is “localized anomaly, best explained by label error, not proved” the right resting place?

**Yes.**

Keep exactly this level of certainty.

## Q2. Should position 0.85 remain the headline window?

**Keep it as the instrumented high-power case study, but not as the sole guarantee window.**

Use cross-window results for general claims.

## Q3. Is the ADDIS attack a contribution at 92M flows?

**Yes as a structural result; no as a cheap practical attack.**

Do not oversell operational feasibility.

## Q4. Is the coincidence of the two attack surfaces the better headline?

**Yes. Strongly.**

It is the more elegant and security-relevant finding.

## Q5. How much should E2 provenance discount the alert audit?

**Substantially.**

E2 is a consistency signal, not independent ground truth.

Emphasize the independently corroborated E1 cases.

## Q6. Which A1 gaps should be reopened?

Do:

1. near-duplicate analysis;
2. per-feature comparison if cheap.

Do not redo the proximity metric.

## Q7. Is the seven-item figure budget right?

**Yes, with both attack surfaces combined into one two-panel figure.**

Keep the operational frontier in the main paper.

---

# 12. Concrete Next 5 Days

## Day 1

- near-duplicate A1 analysis;
- per-feature A1 analysis;
- freeze A1/F9 wording.

## Day 2

Write:

- problem formulation;
- threat model;
- notation.

Build Figure 1.

## Day 3

Write:

- feasibility theorem section;
- procedure-boundary subsection.

Build Figure 2.

## Day 4

Write:

- granularity section;
- padding theorem;
- attack model.

Build Figures 3 and 4.

## Day 5

Write:

- experimental setup;
- cross-window results;
- operational comparison.

Build Table 2 and Figure 5.

At the end of Day 5, aim for a complete technical skeleton of the manuscript.

---

# 13. Parallel Track

During manuscript writing, inspect second-dataset candidates.

Time-box the initial inspection.

The only question is:

> Can we obtain genuine campaign-level ground truth at sufficient scale?

If yes, run the minimal validation.

If no, stop and continue writing.

---

# 14. Non-Claims to Preserve

The paper should explicitly avoid claiming:

1. every online FDR procedure necessarily becomes absorbing;
2. all LSPR23 labels are wrong;
3. position 0.85 proves label error;
4. the deployable groups are true incidents;
5. the ADDIS state attack is cheap operationally;
6. FDR control is always worse than feedback;
7. grouping solves the problem without cost;
8. the low FDP at position 0.85 is a theorem-backed guarantee;
9. the second detector proves universality;
10. the paper proposes a new FDR algorithm.

---

# 15. Recommended Thesis

> **Online statistical error control for ML intrusion detection faces a three-way tension between finite evidence resolution, alert granularity and adversarial robustness. Fine-grained streams can exceed the discovery horizon of broad classes of online procedures; coarser security-semantic grouping restores feasibility at the cost of episode-level resolution; and the aggregation required to obtain that feasibility introduces an attacker-controlled suppression surface. Procedures that escape the first failure mode by conditioning future spending on observed evidence expose a second, history-dependent state surface, which can coincide with the same padding operation.**

---

# 16. Immediate Next Step

If only one action is started now:

\[
oxed{
	extbf{Start writing the Problem Formulation and Feasibility Theory sections.}
}
\]

In parallel, close the two cheap A1 gaps.

Do not wait for another large experiment.

The project should now move from:

\[
experiment -> experiment -> experiment
\]

to:

\[
compress -> write -> validate generality in parallel.
\]
