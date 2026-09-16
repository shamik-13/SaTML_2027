# Review of 04_EXPERIMENTS_AND_FINDINGS.md
## Recommended Next Actions for the FDR / Trustworthy-IDS Project

### Overall assessment

The project is now at a **decision-gate stage**, not an "add more experiments" stage.

The experimental record is much stronger than the original proposal. The project now has:

- an exact feasibility mechanism;
- real-data confirmation;
- a large discrepancy between flow-level and episode-level evaluation;
- a real detector operating near the feasibility boundary;
- an adversarial dilution mechanism;
- and a concrete tradeoff between statistical robustness and detection power.

The headline story is no longer:

> "FDR is useful for intrusion detection."

It is now much closer to:

> **Finite-resolution statistical evidence and online error-control dynamics can make trustworthy ML alerting vacuous or attackable at cybersecurity scale.**

However, I would **not start writing the paper yet**.

There are three high-priority blockers that could materially change the main claim. The next step should be a short **kill-the-paper sprint**: deliberately test the strongest possible alternatives and see whether the headline phenomena survive.

---

# 1. Immediate Priority: Test Modern e-Value Procedures

This is the most important next action.

The current experimental record establishes strong behavior for LORD++ and LOND, but the broader claim is about online statistical error control.

That is not yet safe.

The project currently notes that:

- SAFFRON and ADDIS are still open;
- e-LOND / e-BH are not yet used as direct comparators;
- converting e-values back into p-values via `min(1,1/e)` is valid but lossy.

This creates an obvious reviewer objection:

> Are the reported structural-silence effects a fundamental cybersecurity-scale problem, or merely a weakness of the particular online p-value procedures tested?

Recent online multiple-testing work is directly relevant.

At minimum, I would implement and test:

1. **e-LOND**
2. **an e-GAI / e-LORD-style method**
3. **the strongest recent compound-e / e-closure method that is realistically implementable**
4. **LORD++** as the classical reference

The most important question is:

\[
\boxed{
\text{Does structural silence persist under the strongest modern online e-value procedures?}
}
\]

This experiment could either strengthen or narrow the paper.

### If the answer is yes

Then the feasibility result becomes much stronger:

> The problem is not just alpha-death in classical p-value procedures; finite evidence resolution creates a deeper feasibility boundary even for modern statistical control.

### If the answer is no

That is still useful.

The paper may become:

> Classical online FDR procedures become structurally infeasible at cybersecurity scale, while newer e-value procedures avoid some of the pathology.

That is a narrower claim, but still scientifically meaningful.

### Why this must happen before more experiments

If a modern comparator removes the headline failure, then expanding the current experiment matrix before testing it would waste time.

This is therefore **Priority 1**.

---

# 2. Re-run the Real Detector on the Full Unsampled Deployment Stream

This is the largest methodological issue in the current real-data experiment.

The LSPR23 dataset contains approximately 16.35 million flows.

But the real detector experiment retained:

- all malicious flows;
- only 50% of benign flows;

producing roughly 9 million rows before chronological splitting.

Benign subsampling is acceptable for training efficiency.

It is **not acceptable for the final deployment stream** when the paper's main phenomena depend directly on:

- number of hypotheses \(T\);
- attack prevalence;
- rejection drought length;
- group sizes;
- calibration-to-stream scale;
- feasibility margins;
- and attack dilution cost.

Subsampling the deployment stream changes exactly the quantities being studied.

## Recommended protocol

Use the original full, timestamp-sorted LSPR23 stream.

```text
Full LSPR23
    |
    +-- early chronological period
    |       +-- detector training
    |             +-- benign subsampling allowed if needed
    |
    +-- middle chronological period
    |       +-- calibration
    |
    +-- late chronological period
            +-- deployment evaluation
                  +-- retain EVERY flow
```

Important:

> Define the chronological split on the full original stream first.

Do **not** define the split after benign subsampling.

Then rerun the current headline real-data results:

- feasibility margin;
- episode detection;
- structural silence;
- dilution cost;
- padding-robust detection floor.

Until this is done, I would not put the current F5, F6 or F8 numbers in an abstract.

This is **Priority 2**.

---

# 3. Finish the Formal Padding-Robustness Argument

The dilution result is potentially one of the strongest contributions, but the theoretical story is not finished.

The current record correctly notes that:

- the arithmetic mean is admissible and valid under arbitrary dependence when group size is fixed in advance;
- the pre-committed-denominator rule is padding-robust within its cap;
- Vovk-Wang's theorem fixes arity \(K\), while the padding attack changes arity;
- therefore the current "padding robustness requires giving up admissibility" statement still needs formalization.

This is worth resolving immediately.

The experimental record already proposes two routes:

1. an essential-domination argument;
2. a direct construction using negatively dependent e-values.

I would spend the half-day and determine whether the statement can be made rigorous.

## Why this matters

If the theorem succeeds, you may be able to claim something much stronger than:

> The arithmetic mean happens to be vulnerable to dilution.

You may be able to claim something closer to:

> Under a broad class of admissible symmetric e-merging rules, robustness to attacker-controlled padding fundamentally conflicts with statistical power/admissibility.

That would be a genuine technical contribution.

## Also fix the cap-validity issue

The current real robust-rule experiment chooses \(n_0\) from the 99th percentile group size.

But the rule is valid only when:

\[
m \le n_0.
\]

If approximately 1% of real groups exceed the cap, then the full-stream guarantee is not valid as currently stated.

You need a deterministic policy for oversized groups.

Possible options:

- set \(n_0\) to the maximum allowed group size;
- deterministically split groups larger than \(n_0\);
- use pre-committed slots;
- derive another valid bounded-arity construction.

Then rerun the robustness/power tradeoff.

This is **Priority 3**.

---

# 4. After the Three Blockers: Make the Dilution Attack a Real Security Attack

The current dilution result is highly interesting.

On real traffic, the current experiment reports extremely low suppression costs in some settings.

But the current attack samples benign test flows and inserts them into a group.

That proves the statistical mechanism.

It does not yet prove a realistic **problem-space attack**.

For SaTML, the stronger version would be:

> An attacker can generate ordinary-looking traffic that enters the same deployable episode and suppresses the alert without needing to evade the underlying ML detector.

For example:

```text
attacker-controlled host
       |
       +-- normal-looking request
       +-- normal-looking connection
       +-- harmless protocol interaction
       +-- harmless protocol interaction
       |
       +-- malicious activity
                 |
          same grouped episode
                 |
          diluted evidence
                 |
          alert suppressed
```

## Attack variants to test

1. random benign-looking padding;
2. protocol-matched padding;
3. service-matched padding;
4. black-box adaptive padding;
5. controlled generated network traffic.

Ideally, the attacker should **not need detector scores**.

That would turn the result from:

> "mean aggregation is statistically dilution-sensitive"

into:

> **"the statistical trust layer creates a practical evasion surface even when the underlying detector still scores the malicious flows highly."**

That is a much stronger security contribution.

---

# 5. Do Not Spend Several Days on AIT-ADS Yet

AIT-ADS is conceptually useful because it would put the statistical layer after an existing IDS/SIEM.

However, the current experimental record shows that reconstructing labels requires:

- a large auxiliary dataset;
- substantial preprocessing;
- several days of work.

I would defer this.

First answer:

1. Does the structural-silence result survive modern e-value procedures?
2. Does it survive on the full unsampled LSPR deployment stream?
3. Does the dilution result survive after the aggregation validity issue is fixed?

If yes, then a second dataset is worth the time.

---

# 6. The Second Dataset Should Solve the Incident-Ground-Truth Problem

LSPR23 is useful, but it has an important limitation:

> its 288 red-team narratives cannot be cleanly mapped from individual flows to campaigns.

Therefore, the current units created by:

\[
(\text{SrcIP}, \text{DstIP}, \text{time bucket})
\]

are **episodes**, not known incidents.

That distinction matters.

I would therefore avoid saying:

> "flow-level and incident-level evaluation disagree by 60 points."

The supported claim is:

> **flow-level and deployable episode-level evaluation disagree dramatically.**

For the second dataset, prioritize one with genuine:

\[
\text{flow} \rightarrow \text{campaign/incident}
\]

ground truth.

That dataset would let you answer whether the semantic-granularity result survives when the incident definition is not an approximation.

---

# 7. Add an Analyst-Feedback Baseline After the Core Validity Checks

The experimental record correctly identifies a potentially devastating baseline:

> If analyst dispositions eventually arrive, why not simply use those labels to adjust the operating threshold?

This baseline must eventually be included.

A simple controller might conceptually do:

```text
too many false alerts
       |
raise threshold

too few alerts / excessive misses
       |
lower threshold
```

You should evaluate label delay:

\[
L \in
\{0,\ 1\text{h},\ 1\text{d},\ 1\text{w},\ \infty\}.
\]

The purpose is not necessarily to beat the feedback controller everywhere.

The purpose is to identify the honest domain where online statistical guarantees are useful.

For example, the final conclusion may be:

> Formal no-feedback online error control is most valuable when disposition labels are unavailable or arrive too slowly for ordinary feedback adaptation.

That would be a useful deployment result.

---

# 8. Use Matched Operating Points

The original proposal risked comparing arbitrary configurations.

For example:

- FDR method at \(q=0.05\);
- fixed score threshold 0.5.

That does not establish superiority.

Every alerting method traces out a tradeoff between:

- alert volume;
- false discovery;
- episode/incident recall;
- latency.

The final paper should compare methods using:

## A. Matched analyst budget

\[
A_1 = A_2.
\]

Compare:

- FDP;
- episode/incident recall;
- detection latency.

## B. Matched realized FDP

\[
FDP_1 \approx FDP_2.
\]

Compare:

- recall;
- alert volume;
- time to detection.

## C. Pareto frontiers

For example:

\[
\text{FDP}
\quad \text{vs} \quad
\text{episode recall}
\]

and

\[
\text{alerts/day}
\quad \text{vs} \quad
\text{episode recall}.
\]

The Pareto-frontier presentation is likely the cleanest.

---

# 9. Tighten the Current Claims

Several current statements are stronger than the evidence presently supports.

## Current F1

> "Event-level online error control is infeasible at security scale."

I would temporarily rewrite this as:

> **Finite-resolution conformal evidence makes several standard online FDR procedures structurally infeasible at event-level cybersecurity horizons under realistic calibration budgets.**

Why?

Because modern e-value procedures have not yet been tested.

## Current F3

> "Deployable incident grouping does not restore feasibility."

I would rewrite this as:

> **The tested host-pair/time-bucket grouping does not robustly restore feasibility on LSPR23.**

Why?

Because only one family of deployable groupings has been evaluated.

## Current F4

> "Flow-level and episode-level evaluation of the same system disagree by 60 points."

This is a good claim.

Keep "episode," not "incident," unless genuine incident ground truth becomes available.

---

# 10. Recommended 2-3 Day Kill-the-Paper Sprint

The project should now be run like an adversarial review.

Try to destroy the headline result.

| Priority | Task | Purpose |
|---|---|---|
| **1** | Implement e-LOND and strongest modern e-value comparator(s) | Determine whether structural silence is fundamental or procedure-specific |
| **2** | Re-run real detector on the full unsampled LSPR test stream | Remove the largest deployment-evaluation confound |
| **3** | Complete padding/admissibility formalization and fix cap validity | Make the theoretical robustness tradeoff defensible |
| **4** | Re-run F5/F6/F8 after 1-3 | Produce authoritative headline numbers |
| **5** | Implement realistic/problem-space dilution traffic | Turn the mechanism into a security attack |
| **6** | Add matched-budget and delayed-feedback baselines | Establish practical relevance |
| **7** | Add a second dataset with true incident labels | Validate semantic-granularity conclusions |

I would **not** currently spend time on:

- a large detector zoo;
- many more datasets;
- SAFFRON/ADDIS unless they become specifically necessary;
- writing a full paper draft;
- reconstructing AIT-ADS labels.

---

# 11. Decision Gate After Tasks 1-3

Stop after the first three tasks and evaluate what survived.

## Green Light

If modern e-value procedures still exhibit a meaningful finite-evidence feasibility boundary **and** the dilution attack survives the full-stream evaluation:

Proceed aggressively.

The paper becomes:

> **Finite evidence resolution, security-scale sequential testing, and attacker-controlled aggregation create non-vacuity and attackability problems for statistical trust guarantees.**

That is compelling.

## Yellow Light A

If modern e-value methods eliminate structural silence but aggregation remains easily exploitable:

Pivot to:

> **Aggregation as an attack surface in statistically trustworthy ML alerting.**

This could still be strong.

## Yellow Light B

If modern methods remove catastrophic silence but require substantial calibration, alert-volume, or detection-power costs:

The paper becomes:

> **A feasibility and cost analysis of modern online statistical guarantees in cybersecurity.**

Potentially publishable, but less striking.

## Red Light

If current state-of-the-art methods:

- avoid structural silence;
- resist dilution;
- preserve useful detection;
- and beat simple feedback baselines;

then stop this direction before investing further.

That is why the kill test belongs **now**, not at the end of the project.

---

# 12. What I Think Is Strongest Right Now

The best part of the current experimental record is the combination of three things.

## 12.1 Exact mechanism

The project has an analytical explanation for why finite evidence resolution can collide with shrinking online testing thresholds.

That is stronger than a purely empirical anomaly.

## 12.2 Real-data knife edge

The real detector experiments reportedly operate near the theoretical feasibility boundary.

This suggests the mechanism is not merely asymptotic or pathological.

## 12.3 Low-cost adversarial suppression

The dilution attack reportedly suppresses real detected episodes with surprisingly little benign-looking padding in some configurations.

That creates an actual security interpretation:

> the trust mechanism itself may become an evasion target.

If all three survive the next validation sprint, then the project has a much stronger research identity than the original FDR-for-IDS proposal.

---

# 13. My Recommended Revised Thesis

The paper should no longer be about whether FDR is useful for IDS.

It should increasingly be organized around:

> **When do formal statistical trust guarantees remain non-vacuous at cybersecurity scale, how does the choice of security-semantic unit affect their feasibility, and can an attacker exploit the state or aggregation mechanism of the statistical decision layer?**

The conceptual flow becomes:

\[
\boxed{
\text{ML detector}
\rightarrow
\text{finite evidence}
\rightarrow
\text{online statistical controller}
\rightarrow
\text{feasibility boundary}
\rightarrow
\text{security-semantic grouping}
\rightarrow
\text{adversarial suppression}
}
\]

This preserves the original objective - using established statistical methods in cybersecurity - but shifts the novelty toward a much stronger domain-specific contribution.

---

# 14. Concrete Next Action

If only **one thing** is done next:

> **Implement the strongest current e-value-based online error-control comparator and rerun the structural-silence analysis.**

That experiment has the highest information value because it can immediately tell us whether the paper's central feasibility story is:

- fundamental;
- narrower than currently stated;
- or already solved by modern methods.

Immediately after that:

1. reproduce the real-data results on the full unsampled LSPR test stream;
2. finish the padding/admissibility theorem;
3. stop again and reassess.

Only after those survive would I start the full SaTML paper outline.
