# Detailed Feedback on the FDR-for-IDS Research Proposal
## How I would reposition the project for a stronger SaTML main-track submission

### Status
This note is based on:

1. the original proposal: **“From Anomaly Scores to Trustworthy Alerts: Online False-Discovery Control for Machine-Learning Intrusion Detection”**;
2. the supplied review document **`17_FEEDBACK_ON_ORIGINAL_PROPOSAL.md`**;
3. the prototype findings reported inside that feedback document; and
4. my independent assessment of how the revised project should be positioned.

**Important caveat:** the quantitative prototype findings discussed below are taken from the supplied feedback document. I have not independently rerun the prototype or re-derived every numerical result from raw code/results.

---

# 1. Executive assessment

My view changed materially after reading the feedback and the reported prototype findings.

I would **not abandon the project**.

I would, however, abandon the original main framing:

> “Apply online false-discovery-rate control to machine-learning intrusion detection.”

That framing is too close to existing literature and is not strong enough by itself for a SaTML main-track paper.

The much more promising paper hiding inside the project is:

> **When are online statistical false-discovery guarantees actually feasible for cybersecurity alert streams, and can the guarantee mechanism itself create operational blind spots or exploitable periods of statistical silence?**

That is a much more interesting trustworthy-ML question.

The strongest ideas are no longer:

- generic FDR control for IDS;
- dependence breaks classical FDR;
- drift invalidates calibration.

The strongest ideas now appear to be:

1. **event-level versus incident-level statistical control**;
2. **finite-resolution evidence interacting with online alpha/e-value dynamics**;
3. **structural silence / loss of discovery capability**;
4. **the feasibility envelope of online guarantees at cybersecurity scale**;
5. **adaptive attackers exploiting the decision-layer dynamics**;
6. **the statistical unit of prediction being different from the security-semantic unit of action**.

That is a substantially stronger paper.

---

# 2. What the supplied feedback gets right

## 2.1 The original motivation is valid, but not novel

The original proposal argues that SOC analysts consume alerts rather than AUROC, and therefore the fraction of analyst-facing alerts that are false is more operationally meaningful than classifier-centric metrics alone.

That is correct.

But it should be presented as **motivation**, not as a novelty claim.

The base-rate problem in intrusion detection is old. Axelsson’s classic work already showed why, when attacks are rare, even a detector with apparently strong sensitivity/specificity can produce an unusable posterior probability of attack given an alarm.

In the language of the current project:

\[
P(\text{attack}\mid\text{alert})
\]

or equivalently

\[
1-\mathrm{FDP}
\]

is operationally crucial.

So I agree with the feedback that the paper should not claim:

> “We are the first to realize that false alerts matter more than AUROC.”

That would be vulnerable to an immediate reviewer objection.

### Correct use of this idea

Use it to motivate:

> Existing classifier metrics do not by themselves provide an operational guarantee on analyst-facing discoveries.

Then move quickly to the actual new question.

---

# 3. The original statistical pipeline is also not enough for novelty

The original pipeline was:

\[
s_t
\rightarrow
p_t
\rightarrow
\text{online FDR controller}
\rightarrow
\text{alert}.
\]

That is elegant, but the general ingredients are already established.

Relevant neighboring lines of work include:

- online FDR for anomaly detection;
- conformal p-values for security/anomaly streams;
- streaming conformal calibration;
- drift-triggered recalibration;
- online FDR on conformal evidence;
- operational threshold/risk control for NIDS.

Therefore, the contribution cannot simply be:

> “We use conformal p-values and LORD/SAFFRON/ADDIS for network intrusion alerts.”

At best, that would be an application paper; at worst, it would look like a straightforward domain transfer whose core conclusions are already known.

This is the biggest change I would make to the proposal.

---

# 4. The prototype appears to have found a much stronger phenomenon

The most important reported prototype result is not about drift or dependence.

It is the interaction between:

1. **finite-resolution statistical evidence**, and
2. **online testing thresholds that can become extremely small over time**.

For a simple conformal p-value based on a calibration set of size \(n\),

\[
p_{\min}
=
\frac{1}{n+1}.
\]

This means no observation—no matter how extreme—can produce a p-value below that floor.

Now suppose the online testing rule at time \(t\) requires:

\[
p_t \leq \alpha_t.
\]

If eventually

\[
\alpha_t < p_{\min},
\]

then rejection becomes impossible:

\[
P(\text{reject at }t)=0.
\]

This is true **even if the detector score is maximally suspicious**.

That is far more interesting than ordinary “low power.”

It means the statistical trust mechanism can enter a state where it remains formally conservative yet is structurally incapable of discovering anything.

I would call this:

## Structural silence

A system is in **structural silence** at time \(t\) if, given the current evidence resolution and decision threshold,

\[
\sup_x \text{evidence strength}(x)
\]

is still insufficient to satisfy the rejection rule.

In the conformal-p-value case, one simple necessary condition for the possibility of rejection is

\[
\frac{1}{n+1}
\leq
\alpha_t.
\]

Equivalently,

\[
n
\geq
\frac{1}{\alpha_t}-1.
\]

This is a clean, interpretable feasibility condition.

---

# 5. Why this is much stronger than the original project

The original project asked:

> “Can FDR control improve IDS alert quality?”

The revised project can ask:

> **At cybersecurity-scale stream lengths, with finite calibration evidence, when is online statistical error control even capable of making a discovery?**

That is a deeper question.

It turns the paper from:

> applying a known method to a new domain

into:

> characterizing a previously underexamined feasibility boundary created by the interaction between a known statistical method and the scale/granularity of a cybersecurity system.

That is exactly the kind of “established technique + new domain implication” contribution that can be strong without inventing a new ML algorithm.

---

# 6. I would be careful with the word “impossible”

The feedback document uses very strong language around event-level online FDR becoming infeasible.

The underlying idea is promising, but the paper should avoid a universal claim such as:

> “Event-level online FDR is impossible for cybersecurity.”

That would be too broad.

The correct claim is conditional on:

- the evidence construction;
- the calibration set size;
- the target error level \(q\);
- the online procedure;
- its spending/threshold schedule;
- the stream horizon;
- the rejection history;
- the aggregation level.

A defensible formulation is:

> **We characterize the feasibility envelope of online false-discovery control for cybersecurity alert streams and show that common event-level formulations can enter structural silence at realistic stream lengths unless evidence resolution and testing granularity are designed jointly.**

That is both strong and accurate.

---

# 7. The event-level versus incident-level idea should become the centerpiece

This is, in my opinion, the single strongest conceptual idea in the whole project.

Network ML usually predicts at very fine granularity:

\[
\text{packet}
\rightarrow
\text{flow}
\rightarrow
\text{event}.
\]

But security operations reason at a different semantic granularity:

\[
\text{session}
\rightarrow
\text{alert cluster}
\rightarrow
\text{campaign}
\rightarrow
\text{incident}.
\]

One attack campaign can generate thousands or millions of flows.

If every flow becomes a sequential hypothesis, then the statistical testing horizon becomes enormous:

\[
T_{\text{flows}}
\gg
T_{\text{incidents}}.
\]

That matters because the feasibility of the testing rule depends on the horizon and on the sequence of prior discoveries.

The prototype reportedly finds an enormous difference between event-level and incident-level formulations on LSPR23.

Even if the exact reported numbers later change, the conceptual result is strong:

> The unit at which ML produces predictions is not necessarily the correct unit at which statistical trust guarantees should be imposed.

This is broader than FDR.

It is a general trustworthy-security-ML principle.

---

# 8. This can become a technical “granularity–feasibility” paper

I would explicitly study several aggregation levels.

For example:

\[
\text{flow}
\rightarrow
\text{host-time window}
\rightarrow
\text{session}
\rightarrow
\text{alert cluster}
\rightarrow
\text{incident}.
\]

For each level \(g\), measure:

- number of hypotheses \(T_g\);
- minimum required calibration size;
- attainable evidence resolution;
- realized FDR;
- detection power;
- incident recall;
- detection latency;
- analyst workload;
- structural-silence rate.

This creates a very nice tradeoff:

\[
\boxed{
\text{granularity}
\leftrightarrow
\text{statistical feasibility}
\leftrightarrow
\text{security utility}
}
\]

That is a much more interesting scientific object than simply comparing several online FDR algorithms.

---

# 9. The biggest practical challenge: where do “incidents” come from?

A reviewer will immediately ask:

> “How do you know which flows belong to the same incident before you detect the incident?”

This must be handled explicitly.

There should be two separate evaluations.

## 9.1 Oracle incident grouping

Use ground-truth campaign/incident labels.

Purpose:

> Establish the fundamental feasibility result.

Question:

> If the correct semantic unit were available, how much does the feasibility boundary change?

This is scientifically valid, but not deployable.

## 9.2 Deployable incident approximation

Then group without using attack ground truth.

Possible mechanisms:

- same source/destination host within a time window;
- session/connection grouping;
- temporal clustering;
- host-level alert correlation;
- SIEM correlation rules;
- provenance/causal graph grouping;
- ATT&CK-stage correlation;
- existing alert-clustering algorithms.

Then measure how imperfect grouping changes:

\[
\text{FDR},
\quad
\text{power},
\quad
\text{incident recall},
\quad
\text{latency}.
\]

This experiment is essential.

Without it, the incident-level result risks looking like an oracle-only observation.

---

# 10. Structural silence is a trustworthy-ML failure, not just a statistics detail

A security system can satisfy an error guarantee in a vacuous way:

\[
\text{issue no alerts}.
\]

Then

\[
\mathrm{FDR}=0
\]

but security utility is also zero.

That is a classic distinction between:

- **validity**, and
- **usefulness/power**.

But in cybersecurity the consequence is particularly serious.

A detector that cannot alert during a real attack is not “trustworthy” merely because it does not issue false alerts.

Therefore every FDR result should be paired with a power/security-utility metric.

I would introduce an explicit metric such as:

## Structural Silence Rate (SSR)

Fraction of time steps for which the procedure is mathematically incapable of rejecting even at maximal available evidence.

For p-value evidence:

\[
SSR
=
\frac{1}{T}
\sum_{t=1}^{T}
\mathbf{1}
\left[
\alpha_t
<
p_{\min,t}
\right].
\]

A related metric is:

## Time to Structural Silence

\[
T_{\text{silence}}
=
\min
\{t:\alpha_t<p_{\min,t}\}.
\]

These are interpretable and directly connected to the mechanism.

---

# 11. The adaptive-attacker angle could make the paper especially strong for SaTML

This is the second strongest idea in the supplied feedback.

Once a statistical controller can lose discovery capability because of its history, an adversary can potentially target the **decision process**, not merely the classifier.

The attacker may not need to evade the ML detector directly.

Instead, the attacker may try to manipulate the sequence of hypotheses/rejections so that the controller enters a low-power state before the high-value attack.

Conceptually:

```text
low-signal attacker activity
        ↓
few/no rejections
        ↓
testing wealth / threshold decays
        ↓
structural silence or near-silence
        ↓
high-value attack
```

This creates a new threat model:

> **The attacker manipulates the online statistical state of the alerting system.**

That is much more directly “security” than simply evaluating statistical methods on a security dataset.

---

# 12. Possible attack formulation

Define an attacker budget:

\[
B
\]

as the number or cost of attacker-controlled precursor events.

Define:

\[
B^*
=
\min B
\]

such that the attacker can cause the controller to enter a desired low-power state before launching the target attack.

Possible objectives:

## Objective 1 — Induce structural silence

\[
\alpha_t < p_{\min}.
\]

## Objective 2 — Reduce target-attack detection probability

\[
P(\text{alert}\mid\text{target attack})
\leq \epsilon.
\]

## Objective 3 — Increase detection delay

\[
TTD_{\text{attack}}
\geq \Delta.
\]

Study \(B^*\) as a function of:

- \(q\);
- calibration size;
- procedure;
- evidence type;
- stream horizon;
- prior discovery history;
- aggregation granularity.

This could become one of the paper’s strongest sections.

---

# 13. Avoid overclaiming the adaptive attack

There is an important distinction:

### Natural rejection drought

The procedure becomes weak because few discoveries occur naturally.

### Adversarial rejection drought

The attacker deliberately chooses activity that manipulates or exploits that state.

The paper must show that the attacker has a realistic control channel.

For example:

- can the attacker inject many low-suspicion flows?
- can the attacker predict or estimate the defender’s statistical state?
- does the attack require impossible knowledge of \(lpha_t\)?
- can a black-box attacker infer the state from observable blocking/alert behavior?

The stronger the threat model, the more interesting the paper becomes.

---

# 14. Dependence should be demoted from “main problem” to “design consideration”

The original proposal treated temporal dependence as a central obstacle.

The feedback correctly notes that this becomes less compelling once we choose evidence/procedures designed to tolerate dependence.

That does not mean dependence is irrelevant.

It means:

> “Cyber data are dependent” is not itself the novelty.

Instead, dependence should influence:

- which procedures are theoretically appropriate;
- which guarantees are valid;
- how event aggregation is performed;
- how the assumption ledger is written.

The paper should include an explicit table:

| Procedure | Evidence type | Dependence assumption | Guarantee | Known limitation |
|---|---|---|---|---|

This would make the statistical story much cleaner.

---

# 15. Calibration drift should also be demoted

The original proposal emphasized:

\[
\text{drift}
\rightarrow
\text{miscalibration}
\rightarrow
\text{FDR failure}.
\]

According to the prototype summary, the observed miscalibration on the tested AIT stream was much smaller than expected.

That means calibration drift should not be precommitted as a headline result.

It should become:

> a robustness analysis.

The more interesting question is:

> At the extreme quantiles actually used by the online procedure, can we empirically validate the evidence at all?

This is subtler.

If the controller operates at:

\[
p \approx 10^{-6},
\]

but the validation stream contains only:

\[
10^5
\]

or

\[
10^6
\]

benign observations, then the relevant tail behavior is essentially unobservable.

That creates an **auditability problem**.

---

# 16. The tail-auditability issue is potentially a strong technical contribution

Suppose a guarantee relies on evidence at level:

\[
10^{-6}.
\]

To empirically estimate whether benign events satisfy that tail condition, we may need on the order of:

\[
10^7-10^8
\]

independent/effective observations.

Security benchmarks rarely provide that level of clean negative evidence.

Therefore:

> A formal statistical guarantee may operate at evidence levels that cannot be empirically audited using realistic cybersecurity datasets.

This is important.

It distinguishes:

## Theoretical validity

The mathematical assumptions imply a guarantee.

from:

## Empirical auditability

We have enough data to verify that those assumptions are even approximately true in the deployed domain.

That distinction fits SaTML very well.

---

# 17. The feedback-controller baseline is essential

A strong paper must include the simplest thing a SOC could do instead.

If analyst dispositions arrive over time, a system can use them as delayed labels and adjust its alert threshold directly.

Conceptually:

```text
too many false analyst dispositions
        ↓
raise threshold

too few detections / under-alerting
        ↓
lower threshold
```

This does not provide the same formal FDR guarantee, but it may work very well operationally.

The paper must therefore ask:

> When does sophisticated online error control provide value beyond a simple feedback controller?

This may identify the real deployment niche:

\[
\boxed{
\text{label-scarce or long-label-delay regime}
}
\]

rather than all SOC settings.

That would make the conclusion much more honest and useful.

---

# 18. Comparisons must be made on matched operating points

The original proposal risked comparing:

- FDR method at \(q=.05\)
- fixed detector threshold at \(0.5\)

which is not meaningful.

Every decision layer induces some tradeoff between:

- alert volume;
- false-discovery proportion;
- recall;
- latency.

Therefore comparisons should use one of the following.

## 18.1 Matched analyst budget

Force:

\[
A_1=A_2
\]

alerts per day/hour.

Compare:

- incident recall;
- FDP;
- latency.

## 18.2 Matched realized FDP

Choose configurations where:

\[
FDP_1\approx FDP_2.
\]

Compare:

- alert volume;
- power;
- incident recall;
- latency.

## 18.3 Full Pareto frontier

Plot:

\[
\text{FDP}
\quad \text{vs} \quad
\text{incident recall}
\]

or

\[
\text{alerts/day}
\quad \text{vs} \quad
\text{incident recall}.
\]

This is probably the cleanest evaluation.

---

# 19. The data critique in the feedback is serious

A paper whose headline metric is around:

\[
q=0.05
\]

cannot casually use datasets with several-percent label errors and then interpret small FDR differences literally.

If the ground-truth corruption rate is comparable to the target FDR, then there is an identification problem:

\[
\text{measurement error}
\approx
\text{quantity being measured}.
\]

This means dataset selection is not a minor implementation detail.

It is part of the methodology.

---

# 20. Dataset strategy I would use now

## Primary: LSPR23

This should move from “external validation” to a major dataset.

Reasons:

- long realistic stream;
- live-fire exercise;
- multi-stage campaigns;
- attack narratives/campaign structure;
- useful for event-to-incident comparison.

It is particularly valuable for the semantic-granularity question.

## Secondary: corrected CIC/CSE-CIC-derived data

Use only corrected or carefully validated labels.

Purpose:

- reproducible benchmark;
- scale;
- controlled detector experiments.

Do not treat inherited labels as unquestionable ground truth.

## AIT-ADS

Conceptually excellent because it moves the statistical layer after an existing IDS/SIEM rather than pretending to replace the entire detector.

But if labels require a large auxiliary reconstruction pipeline, defer it until the main paper is already working.

It should not become a schedule bottleneck.

## Drop as headline FDP datasets

### LANL

Excellent realism, but incomplete negative ground truth makes precise FDP measurement problematic.

### WitFoo

Potentially useful as a qualitative/secondary case study, but vendor-generated labels/dispositions are not clean enough for a headline statistical guarantee.

These can be discussed, but they should not anchor the main FDR claims.

---

# 21. A much stronger revised paper premise

I would frame the paper as follows:

> Statistical error guarantees are increasingly attractive for trustworthy ML security systems, but cybersecurity operates at extreme stream lengths, finite calibration sizes, and semantic units that differ from the per-event predictions produced by ML detectors. We study the feasibility of online false-discovery guarantees under these conditions and show that fine-grained event-level formulations can become structurally incapable of making discoveries. We then characterize how aggregation to security-semantic units changes the feasibility envelope and investigate whether an adaptive adversary can exploit the online controller’s state.

This is substantially stronger than:

> “We apply FDR to IDS.”

---

# 22. Revised research questions

I would reduce the project to four core RQs.

## RQ1 — Feasibility

> At what combinations of stream length, calibration size, error target, evidence type and online testing rule does event-level statistical control become structurally incapable of issuing alerts?

Outputs:

- analytical feasibility bounds;
- minimum calibration size;
- time to structural silence;
- empirical power.

## RQ2 — Security granularity

> How does changing the unit of testing from flows to sessions, alert clusters or incidents affect statistical feasibility and operational utility?

Outputs:

- number of hypotheses;
- required evidence resolution;
- structural-silence rate;
- incident recall;
- detection latency;
- FDP.

## RQ3 — Adaptive attacker

> Can an adversary manipulate or exploit the history-dependent statistical state of the alerting controller to suppress or delay detection of a later attack?

Outputs:

- minimum attack budget \(B^*\);
- success probability;
- detection-delay increase;
- procedure-specific vulnerability.

## RQ4 — Practical value

> When does formal online error control outperform simpler matched-budget or analyst-feedback thresholding?

Outputs:

- Pareto frontiers;
- label-delay sensitivity;
- analyst workload;
- incident recall;
- FDP.

---

# 23. Analytical section I would add

This is where the paper can become more technically involved without inventing a new algorithm.

Let:

\[
p_{\min}(n)
=
\frac{1}{n+1}.
\]

Let the online procedure produce a time-varying rejection threshold:

\[
\alpha_t
=
A(q,\gamma,\mathcal{H}_{t-1}),
\]

where:

- \(q\) is the target error level;
- \(\gamma\) is the spending sequence or tuning schedule;
- \(\mathcal{H}_{t-1}\) is the rejection/history state.

A necessary condition for a rejection at time \(t\) is:

\[
p_{\min}(n)
\leq
\alpha_t.
\]

Therefore:

\[
n
\geq
\frac{1}{\alpha_t}-1.
\]

This gives a minimum calibration requirement:

\[
n_{\min}(t)
=
\left\lceil
\frac{1}{\alpha_t}-1
\right\rceil.
\]

Then define the deployment feasibility requirement:

\[
n
\geq
\max_{t\leq T} n_{\min}(t)
\]

for a desired horizon \(T\), under a specified history scenario.

The exact derivation will vary by procedure.

That is fine.

The paper can derive the **feasibility envelope** for several established procedures rather than proposing a new one.

---

# 24. The central figure should become a feasibility envelope

The original FDP-over-time figure is useful but no longer the main story.

A stronger headline figure would be:

```text
required calibration size
^
|                                  event-level
|                              /
|                           /
|                        /
|                     /
|                  /
|              session-level
|           /
|       incident-level
|    /
+--------------------------------------> stream horizon
```

Potential axes:

### X-axis

\[
T
\]

deployment horizon / number of hypotheses.

### Y-axis

\[
n_{\min}
\]

minimum calibration set needed to preserve nonzero rejection capability.

Different curves:

- flow-level;
- session-level;
- host-window;
- incident-level;
- different online procedures.

This would communicate the paper’s central point immediately.

---

# 25. Another key figure: validity versus power

A second important figure should show that:

\[
\mathrm{FDR}
\]

can look excellent even while:

\[
\mathrm{Recall}\rightarrow 0.
\]

For example:

```text
                  nominal FDR
                      good
                       │
                       │
            ┌──────────┴──────────┐
            │                     │
      useful control       structural silence
      high recall          near-zero recall
```

This reinforces:

> A trustworthy guarantee must be paired with a non-vacuity / power condition.

---

# 26. Proposed new metrics

I would add the following metrics to the original paper.

## Structural Silence Rate

\[
SSR
=
\frac{1}{T}
\sum_t
\mathbf 1[\text{rejection impossible at }t].
\]

## Time to Structural Silence

\[
T_{\mathrm{silence}}.
\]

## Feasible Horizon

For fixed \(n\):

\[
T_{\max}(n,q,\text{procedure}).
\]

## Minimum Calibration Requirement

\[
n_{\min}(T,q,\text{procedure}).
\]

## Incident Recall

\[
IR
=
\frac{\#\text{incidents detected}}
{\#\text{true incidents}}.
\]

## Time to First Incident Detection

\[
TTD_i.
\]

## Attacker Starvation Cost

\[
B^*.
\]

These metrics make the paper much more distinctive.

---

# 27. Proposed experimental design

I would keep the experiment set much tighter than the original proposal.

## Models

Use only two detectors.

For example:

1. XGBoost or Random Forest;
2. one anomaly detector / neural model.

The paper is not about classifier comparison.

## Statistical procedures

Use a small, principled set.

For example:

1. LORD-family baseline;
2. SAFFRON/ADDIS-type adaptive p-value rule;
3. e-LOND or another arbitrary-dependence e-value rule;
4. one stopping-time / stronger error-control variant if theoretically relevant;
5. offline BH as a retrospective reference only.

Each should be chosen because it represents a distinct assumption/behavior regime.

## Operational baselines

1. fixed threshold;
2. matched-alert-budget threshold;
3. matched-realized-FDP threshold;
4. analyst-feedback controller.

## Granularity levels

At minimum:

1. flow/event;
2. host/session/time-window;
3. oracle incident;
4. deployable incident approximation.

## Main datasets

1. LSPR23;
2. corrected CSE/CIC-derived stream.

Optional later:

3. AIT alert data if time permits.

---

# 28. Suggested paper structure

## 1. Introduction

- statistical guarantees are attractive for trustworthy security ML;
- existing work establishes online FDR/anomaly control;
- missing issue: feasibility at cybersecurity scale and granularity;
- headline observation: guarantees can become vacuous through structural silence;
- contributions.

## 2. Background

### 2.1 Security alerting and base-rate problem
### 2.2 Online multiple testing
### 2.3 Conformal p-values / e-values
### 2.4 Existing online anomaly/FDR work
### 2.5 Security ML temporal evaluation

## 3. Threat and Deployment Model

Define:

- detector;
- evidence;
- controller;
- stream;
- calibration;
- attacker knowledge;
- analyst feedback;
- incident semantics.

Include an assumption ledger.

## 4. Feasibility of Event-Level Error Control

Derive:

\[
p_{\min}
\]

and procedure-specific rejection feasibility.

Define:

- structural silence;
- feasible horizon;
- minimum calibration requirement.

## 5. From Flows to Security-Semantic Units

Evaluate:

- flows;
- sessions;
- clusters;
- incidents.

Use both:

- oracle grouping;
- deployable grouping.

## 6. Empirical Validation

Datasets:

- LSPR23;
- corrected CIC/CSE stream.

Show:

- theoretical envelope vs actual discoveries;
- FDR;
- power;
- structural silence.

## 7. Adaptive Statistical-State Attacks

Define attack strategy.

Evaluate:

- attack budget;
- state manipulation;
- detection probability;
- delay.

## 8. Comparison with Operational Baselines

Matched:

- alert budget;
- FDP;
- label delay.

Include analyst-feedback controller.

## 9. Discussion

- when guarantees are useful;
- when guarantees are vacuous;
- auditability of extreme tail evidence;
- incident semantics;
- deployment implications.

## 10. Limitations

- incident grouping;
- dataset labels;
- attacker visibility;
- SOC feedback assumptions;
- generality across controllers.

---

# 29. Revised contribution claims

I would aim for something like:

## C1 — Feasibility analysis

We characterize when finite-resolution evidence and online error-control schedules make security alerts statistically impossible, deriving procedure-specific feasibility bounds.

## C2 — Security-semantic granularity

We show that the feasibility of trustworthy alerting depends critically on the unit of testing, and quantify the difference between event-, session-, cluster- and incident-level control.

## C3 — Adaptive security threat

We introduce and evaluate attacks that exploit the history-dependent statistical state of the decision layer to suppress or delay later detections.

## C4 — Operational evaluation

We evaluate the guarantee–power–workload tradeoff against matched-budget and analyst-feedback baselines on realistic cybersecurity streams.

These are much stronger than:

> “We benchmark several FDR methods.”

---

# 30. Claims I would avoid

Do **not** claim:

> We are the first to notice that SOCs care about false alerts.

Do **not** claim:

> Online FDR has never been used for anomaly detection.

Do **not** claim:

> Dependence is a previously unknown problem for online FDR.

Do **not** claim:

> Conformal calibration for security streams is new.

Do **not** claim:

> Distribution shift necessarily catastrophically invalidates FDR.

Do **not** claim:

> Event-level online FDR is universally impossible.

Do **not** claim:

> Incident grouping is directly deployable if it uses oracle campaign labels.

All of those invite unnecessary reviewer attacks.

---

# 31. Claims that are potentially strong

Subject to a dedicated novelty review and reproduction of the prototype:

> Online statistical error control in cybersecurity has a previously undercharacterized **feasibility problem** caused by finite evidence resolution and long hypothesis streams.

> Security ML prediction granularity and security operational granularity are different, and this mismatch can determine whether a statistical guarantee is useful or vacuous.

> A system can satisfy a nominal FDR objective while being **structurally unable to detect attacks**.

> The state of an online statistical controller may itself constitute an **attack surface**.

> Formal guarantees that operate at extreme tail probabilities may be **empirically unauditable** with standard cybersecurity benchmark sizes.

Those are much more compelling.

---

# 32. My assessment of SaTML potential

Roughly:

| Version | Novelty | Technical depth | Security significance | SaTML main-track potential |
|---|---:|---:|---:|---:|
| Original “online FDR for NIDS” | 2/5 | 3.5/5 | 3.5/5 | 2–2.5/5 |
| + incident-level feasibility | 4/5 | 4/5 | 4.5/5 | ~4/5 |
| + analytical feasibility envelope | 4.5/5 | 4.5/5 | 4.5/5 | ~4.5/5 |
| + realistic adaptive statistical-state attack | potentially 5/5 | 4.5/5 | 5/5 | very promising |

This is not an acceptance prediction.

It is a relative assessment of the research framing.

The revised direction is substantially better.

---

# 33. What I would do next

I would **not** immediately expand the experiment matrix.

Before more implementation, do a focused novelty search on exactly three topics.

## Search A — finite-resolution / alpha-death / starvation in online FDR

Questions:

- Has anyone formally characterized p-value granularity versus online alpha-wealth?
- Is “alpha-death” already formalized?
- Are there existing horizon/calibration-size feasibility bounds?
- Does existing online-FDR work already discuss structural inability to reject?

## Search B — aggregation / hypothesis granularity

Questions:

- Has online FDR been studied at event vs incident/campaign granularity?
- Is hierarchical/grouped online FDR already used in security?
- Does incident aggregation restore statistical power in known applications?
- Are there analogous results in fraud, medicine, or monitoring?

## Search C — adversarial manipulation of online testing state

Questions:

- Can an adversary intentionally starve alpha wealth?
- Has adversarial online multiple testing been studied?
- Are there poisoning attacks against conformal p/e-values?
- Can an attacker manipulate rejection history or calibration state?

If the exact combination

\[
\text{finite evidence resolution}
+
\text{security granularity}
+
\text{adaptive statistical-state attack}
\]

is genuinely missing, then the project has a strong research identity.

---

# 34. Final recommendation

I would continue the project, but with a different thesis.

The project should no longer be:

> **“Can FDR improve intrusion detection alerts?”**

It should become:

> **“When do statistical trust guarantees remain non-vacuous at cybersecurity scale, what is the correct security-semantic unit for applying them, and can an attacker exploit their online state?”**

That is a much more technically interesting and security-relevant paper.

The core conceptual progression becomes:

\[
\boxed{
\text{ML score}
\rightarrow
\text{finite statistical evidence}
\rightarrow
\text{online error-control state}
\rightarrow
\text{feasibility / structural silence}
\rightarrow
\text{security-semantic aggregation}
\rightarrow
\text{adaptive attack surface}
}
\]

This direction preserves the best part of the original project—using established statistical machinery in a new cybersecurity setting—but moves the novelty away from “method transfer” and toward **a new domain-specific feasibility and security analysis**.

---

# 35. Candidate titles

### Conservative

**The Feasibility of Online False-Discovery Guarantees for Machine-Learning Security Alerts**

### Stronger

**Flows Are Not Incidents: Feasibility Limits of Online False-Discovery Control for ML Intrusion Detection**

### More provocative

**Silent by Guarantee: When Online False-Discovery Control Suppresses ML Intrusion Detection**

### Security-focused

**Attacking the Guarantee: Statistical-State Manipulation in Online ML Intrusion Detection**

### My preferred current working title

**Flows Are Not Incidents: When Statistical Error Guarantees Become Vacuous in ML Intrusion Detection**

---

# 36. One-paragraph revised pitch

Machine-learning intrusion detectors produce predictions at extremely fine granularity, while security operations reason over sessions, campaigns and incidents. This mismatch matters for statistical trust mechanisms. Online false-discovery-control procedures operate over sequences of hypotheses, yet conformal and related evidence has finite resolution determined by calibration data. At cybersecurity-scale stream lengths, the interaction between evidence resolution and history-dependent rejection thresholds can make event-level alerting structurally incapable of issuing discoveries while still satisfying its nominal error objective. We propose to characterize this feasibility envelope analytically and empirically, study how aggregation from flows to security-semantic units changes the guarantee–power tradeoff, and evaluate whether an adaptive adversary can manipulate the statistical state of the alerting controller to suppress or delay later detections. The work does not introduce a new detector or a new FDR algorithm; instead, it studies when established statistical guarantees are meaningful, vacuous, or exploitable in realistic security ML systems.

---

# References / neighboring work to verify in the final paper

The final manuscript should verify exact bibliographic details and versions before submission.

- Axelsson — base-rate fallacy / intrusion detection.
- TESSERACT — temporally and spatially realistic security-ML evaluation.
- Rebjock et al. — online FDR for anomaly detection under rare alternatives/dependence.
- C-PP-COAD — conformal p-values plus online FDR in streaming anomaly settings.
- CALIBURN — conformal/operational risk control for streaming NIDS.
- Transcend / Transcendent — conformal methods in security ML.
- e-LOND and related e-value online FDR methods.
- Work on “alpha-death” / power loss in online multiple testing.
- Corrected CIC-IDS2017 / CSE-CIC-IDS2018 labeling studies.
- LSPR23 — Locked Shields live-fire dataset.
