# From Anomaly Scores to Trustworthy Alerts
## Online False-Discovery Control for Machine-Learning Intrusion Detection

### Research Concept for IEEE SaTML Main Track

---

## 1. Core Idea

Modern machine-learning intrusion detection systems are usually evaluated as **classifiers**. They output a score or probability for each event and are assessed using metrics such as:

- AUROC
- AUPRC
- F1
- precision
- recall
- false-positive rate
- true-positive rate

However, this is not how a Security Operations Center (SOC) experiences an intrusion detector.

A SOC receives an **alert stream**. The operational question is therefore not only:

> How accurately does the detector classify events?

but also:

> Among the alerts sent to analysts, how many are false?

This motivates reframing ML intrusion detection as an **online multiple-hypothesis-testing problem**.

For event \(x_t\), an ML detector produces a score

\[
s_t = f_\theta(x_t).
\]

Instead of applying a fixed threshold directly to \(s_t\), we transform the score into valid statistical evidence, such as a p-value or e-value, and apply an **online false-discovery-rate (FDR) controller**.

The intended pipeline is:

```text
Network event
      ↓
ML detector
      ↓
Anomaly / attack score
      ↓
Statistical calibration
      ↓
p-value or e-value
      ↓
Online FDR controller
      ↓
SOC alert
```

The central goal is to determine whether established statistical error-control methods can convert ordinary ML detectors into **more trustworthy alerting systems**.

---

# 2. Main Premise

Current ML-based IDS evaluation has an important operational gap.

A detector may have excellent AUROC or a low validation-set false-positive rate while still producing a highly unreliable alert stream in deployment.

For a SOC analyst, a natural quantity is the **False Discovery Proportion (FDP)**:

\[
FDP_t =
\frac{V_t}{R_t \vee 1},
\]

where:

- \(R_t\) is the total number of alerts issued up to time \(t\),
- \(V_t\) is the number of those alerts that are actually benign.

The expected FDP is the **False Discovery Rate**:

\[
FDR_t = \mathbb{E}[FDP_t].
\]

A target such as

\[
q = 0.05
\]

has a directly interpretable operational meaning:

> The alerting mechanism is configured to target roughly 5% false discoveries among issued alerts, under the assumptions of the statistical procedure.

This is fundamentally different from saying:

> The classifier has AUROC 0.98.

The proposed work investigates whether this stronger and more operationally meaningful notion of trust can be achieved in cybersecurity.

---

# 3. The Paper Is Not Just “Apply FDR to IDS”

A simple application of Benjamini–Hochberg or LORD to an IDS would be too weak.

The real research question is:

> **Can established online false-discovery-control methods provide meaningful and reliable guarantees under the non-IID, bursty, drifting and highly imbalanced conditions of real cybersecurity streams?**

Cybersecurity creates several complications that are unusual or particularly severe compared with standard multiple-testing settings.

## 3.1 Temporal dependence

Network events are strongly correlated.

Examples:

- multiple packets from the same connection
- multiple flows from the same host
- repeated authentication attempts
- scan bursts
- correlated service behavior

## 3.2 Attack burstiness

One attack campaign can generate thousands of malicious events within a short period.

## 3.3 Benign burstiness

Normal operations may also produce unusual bursts:

- backups
- software updates
- vulnerability scans
- configuration changes
- batch jobs
- traffic spikes

## 3.4 Extreme class imbalance

In many realistic environments,

\[
P(Y=\text{attack}) \ll 1\%.
\]

## 3.5 Distribution shift

The benign network distribution changes over time.

Examples:

- new services
- new hosts
- new applications
- changing user behavior
- topology changes
- seasonal workloads

## 3.6 Multi-stage attacks

A security incident is not necessarily a collection of independent malicious observations.

One campaign may contain:

```text
reconnaissance
    ↓
credential access
    ↓
initial compromise
    ↓
lateral movement
    ↓
privilege escalation
    ↓
exfiltration
```

## 3.7 Adaptive attackers

An attacker may intentionally generate borderline traffic or manipulate the stream in order to affect the alerting procedure.

Therefore, the paper is fundamentally a study of the **trustworthiness of statistical guarantees under security-specific conditions**.

---

# 4. Central Research Hypothesis

The starting hypothesis is:

> Conventional fixed-threshold IDS alerting provides no explicit control over analyst-facing false discoveries, and its realized false-discovery rate can vary dramatically across traffic regimes, attack prevalence and distribution shifts.

A second hypothesis is:

> Established online FDR procedures can substantially stabilize alert quality under some cybersecurity conditions, but their guarantees and effectiveness may degrade under temporal dependence, drift and miscalibrated statistical evidence.

A third hypothesis is:

> The main source of FDR failure in realistic cyber streams may not be the online FDR algorithm itself, but invalid or stale score calibration caused by distribution shift and dependence.

This creates a useful trustworthy-ML question:

> When can a security practitioner actually trust a nominal statistical guarantee attached to an ML alert stream?

---

# 5. Research Questions

## RQ1 — How unreliable is conventional IDS thresholding?

**Question**

How much does the realized false-discovery proportion of standard ML-based IDS alerting vary over time and across operating regimes?

**Goal**

Establish that conventional thresholding does not provide stable analyst-facing alert quality.

**Methods**

Compare:

- fixed probability threshold
- F1-optimal threshold
- fixed false-positive-rate threshold
- quantile threshold
- top-\(k\) alerting
- fixed analyst-budget threshold

**Primary outcome**

\[
FDP_t
\]

through time and across datasets.

---

## RQ2 — Can online FDR methods control ML security alerts?

**Question**

Can established online multiple-testing methods maintain a desired false-discovery target on cybersecurity streams?

Evaluate target levels such as:

\[
q \in \{0.01, 0.05, 0.10, 0.20\}.
\]

Candidate methods include:

- LORD
- SAFFRON
- ADDIS
- alpha-investing variants
- e-value / dependence-robust online procedures
- batch Benjamini–Hochberg as a retrospective reference

**Primary question**

If we request:

\[
q = 0.05,
\]

does the realized FDR remain approximately at or below the target?

---

## RQ3 — Under which cybersecurity conditions does FDR control break?

Evaluate the impact of:

- temporal dependence
- attack burstiness
- benign burstiness
- attack prevalence
- dataset shift
- network-environment shift
- attack family
- calibration-set age
- calibration quality
- model type

This is potentially one of the most important parts of the paper.

The desired result is not necessarily:

> Every FDR method works perfectly.

A scientifically valuable result may instead be:

> Some procedures that behave correctly under near-IID conditions systematically lose control under realistic cyber dependencies.

---

## RQ4 — What security utility is lost when false discoveries are controlled?

Controlling false alerts is not useful if every attack is missed.

Therefore evaluate:

- attack recall
- malicious-flow recall
- incident recall
- time-to-first-detection
- completely missed incidents
- detection delay
- analyst alerts per day
- analyst investigations avoided
- alert precision
- FDR
- attack-family recall

The key tradeoff is:

\[
\text{false-discovery control}
\quad\text{vs.}\quad
\text{security detection utility}.
\]

---

## RQ5 — Do the conclusions generalize?

Evaluate across:

### Multiple detectors

Possible set:

1. Random Forest
2. XGBoost
3. MLP
4. Isolation Forest or another anomaly detector

The purpose is not to find the best detector.

The purpose is to determine whether conclusions about FDR control are **model-independent**.

### Multiple datasets

Primary candidates:

- NF-CSE-CIC-IDS2018-v3
- NF-ToN-IoT-v3
- AIT Alert Data Set
- LSPR23

Optional secondary validation:

- LANL multi-source cyber data
- WitFoo Precinct6 production SOC data

---

# 6. Statistical Formulation

At time \(t\), observe a network event:

\[
x_t.
\]

The detector produces:

\[
s_t = f_\theta(x_t).
\]

The null hypothesis is:

\[
H_t:
x_t \text{ is benign}.
\]

The score is transformed into statistical evidence.

One simple conformal-style construction using a benign calibration set \(C\) is:

\[
p_t =
\frac{
1+\sum_{i\in C}
\mathbf{1}[s_i \geq s_t]
}{
|C|+1
}.
\]

Interpretation:

> How extreme is the current anomaly score relative to known benign observations?

Thus:

\[
s_t \uparrow
\quad\Rightarrow\quad
p_t \downarrow.
\]

An online testing procedure receives:

\[
p_1,p_2,\ldots,p_t
\]

and chooses whether to reject:

\[
H_t.
\]

Rejecting \(H_t\) corresponds to:

> Issue a security alert.

---

# 7. Experimental Pipeline

```text
Chronological network stream
          │
          ▼
     ML detector
          │
          ▼
    attack score s_t
          │
          ▼
 statistical calibration
          │
          ▼
   p-value / e-value
          │
          ▼
 online FDR procedure
          │
       ┌──┴──┐
       │     │
      no    yes
       │     │
       │     ▼
       │   alert
       │
       ▼
   no alert
```

The detector and FDR layer should be separated cleanly.

This allows the paper to ask:

> Given the same underlying detector, how does changing the decision layer affect operational trustworthiness?

---

# 8. Chronological Evaluation Protocol

Random train/test splitting should be avoided.

The preferred setup is:

```text
earlier period
    ↓
training

middle period
    ↓
calibration

later period
    ↓
streaming deployment evaluation
```

For example:

\[
D =
D_{\text{train}}
\cup
D_{\text{cal}}
\cup
D_{\text{test}}
\]

subject to chronological ordering.

The test stream is processed sequentially:

\[
(x_1,y_1),
(x_2,y_2),
\ldots,
(x_T,y_T).
\]

No future information is available when deciding whether to alert at time \(t\).

---

# 9. ML Detectors

The ML models should intentionally be conventional.

The contribution is not a new detection architecture.

A reasonable model set is:

## Supervised

- Random Forest
- XGBoost
- MLP

## Unsupervised / anomaly detection

- Isolation Forest

Potential optional models:

- autoencoder
- one-class SVM
- simple logistic regression baseline

The goal is to demonstrate that the decision-layer conclusions are not specific to one model family.

---

# 10. Conventional IDS Baselines

FDR-controlled methods should be compared against realistic ways in which ML IDS thresholds are normally selected.

## Baseline 1 — Fixed threshold

For probability-based classifiers:

\[
s_t > 0.5.
\]

## Baseline 2 — Validation-F1-optimal threshold

\[
\tau^*
=
\arg\max_\tau F_1(\tau).
\]

## Baseline 3 — Fixed FPR

Choose \(\tau\) on calibration data so that:

\[
FPR \in
\{10^{-2},10^{-3},10^{-4}\}.
\]

## Baseline 4 — Quantile threshold

For example:

> Alert on the highest 1% of anomaly scores.

## Baseline 5 — Top-\(k\)

Issue exactly \(k\) alerts per time interval.

This represents an analyst-capacity constraint.

---

# 11. Candidate FDR Procedures

The exact method set should be finalized after implementation and literature verification.

Likely candidates include:

## LORD

Classical online FDR / alpha-investing family.

## SAFFRON

Adaptive online FDR procedure.

## ADDIS

Adaptive discarding-based online FDR.

## e-value-based online control

Particularly interesting for cybersecurity because some e-value approaches make weaker dependency assumptions.

## Benjamini–Hochberg

Use only as an offline retrospective reference because it is not a deployable online procedure in the same sense.

## Naive per-event p-value threshold

For example:

\[
p_t < 0.05.
\]

This demonstrates the effect of multiple testing.

---

# 12. Primary Metrics

## 12.1 False Discovery Proportion

\[
FDP_t =
\frac{V_t}{R_t\vee1}.
\]

This should be one of the paper's principal metrics.

## 12.2 Empirical False Discovery Rate

Across repeated runs / streams:

\[
\widehat{FDR}_t
=
\mathbb{E}[\widehat{FDP}_t].
\]

## 12.3 FDR violation frequency

For target \(q\):

\[
P(FDP_t > q)
\]

or a suitable repeated-experiment analogue.

## 12.4 Alert precision

\[
Precision =
\frac{TP}{TP+FP}.
\]

Note:

\[
FDP = 1-\text{precision}
\]

for the corresponding discovery set, but the sequential framing is important.

---

# 13. Security Utility Metrics

## Flow-level recall

\[
Recall =
\frac{TP}{TP+FN}.
\]

## Incident recall

Fraction of attack incidents that trigger at least one alert.

## Time to first detection

For incident \(j\):

\[
TTD_j =
t^{alert}_j - t^{start}_j.
\]

## Missed-incident rate

Fraction of attacks that generate no alerts.

## Analyst workload

Possible measures:

\[
\text{alerts per hour},
\]

\[
\text{alerts per day},
\]

\[
\text{false investigations per day}.
\]

## Alerts saved

Relative to a conventional threshold:

\[
\Delta A =
A_{\text{baseline}}
-
A_{\text{FDR}}.
\]

---

# 14. Event-Level Versus Incident-Level Evaluation

A cybersecurity-specific complication is that thousands of network events may correspond to one attack.

Example:

```text
one brute-force campaign
        ↓
10,000 malicious flows
```

Detecting 9,000 flows may look impressive in event-level metrics, but an analyst may need only one useful incident alert.

Therefore evaluate both:

## Event-level discoveries

Each network event is a hypothesis.

## Incident-level outcomes

Group events by attack campaign / scenario.

Then evaluate quantities such as:

\[
IncidentRecall
=
\frac{
\#\text{attack incidents detected}
}{
\#\text{attack incidents}
}.
\]

A possible additional metric is an incident-level FDP:

\[
FDP_{\text{incident}}
=
\frac{
\#\text{false investigated incidents}
}{
\#\text{all investigated incidents}
}.
\]

Even if no new hierarchical FDR procedure is proposed, the distinction itself may expose important gaps between statistical validity and operational usefulness.

---

# 15. Dataset Plan

## 15.1 NF-CSE-CIC-IDS2018-v3

**Role:** primary development dataset.

Advantages:

- large scale
- chronological information
- multiple attack families
- standardized NetFlow representation
- reliable labels
- suitable for streaming evaluation

Use for:

- RQ1
- RQ2
- parameter selection
- major stress experiments

---

## 15.2 NF-ToN-IoT-v3

**Role:** cross-environment replication.

Use to test whether the findings depend on the traffic characteristics of one dataset.

---

## 15.3 AIT Alert Data Set

**Role:** alert-level evaluation.

This dataset is valuable because it contains alerts from existing IDS tools.

Instead of:

```text
network event
    ↓
ML detector
    ↓
alert
```

it allows:

```text
existing IDS alert
    ↓
statistical control
    ↓
analyst-facing alert
```

This broadens the applicability beyond purely ML-generated NIDS alerts.

---

## 15.4 LSPR23

**Role:** external realistic validation.

LSPR23 originates from the Locked Shields live-fire cybersecurity exercise.

Use it as the final reality check:

> Do conclusions derived from conventional benchmark datasets survive a substantially more realistic attack environment?

---

## 15.5 Optional datasets

### LANL

Useful because it contains long continuous enterprise activity.

Limitation:

Ground truth is not exhaustive enough to cleanly estimate all false positives.

Best used as an ecological robustness experiment.

### WitFoo Precinct6

Useful as a production-SOC case study.

Contains some analyst dispositions and incident information.

Limitation:

The primary labels are partly produced by the vendor's automated correlation pipeline and should not be treated as perfect independent ground truth.

---

# 16. Main Cybersecurity Stress Tests

These experiments are likely to distinguish the paper from a generic statistical-method application.

---

## 16.1 Attack prevalence

Construct or subsample test streams with different attack prevalence:

\[
\pi_{\text{attack}}
\in
\{0.01\%,0.1\%,1\%,5\%,10\%\}.
\]

Question:

> How sensitive are FDR procedures and conventional thresholds to base-rate changes?

This is particularly important because security base rates can vary enormously.

---

## 16.2 Attack burstiness

Keep the total number of malicious observations constant.

Compare:

### Uniform attack placement

```text
benign attack benign benign attack ...
```

versus

### Bursty attacks

```text
benign benign
ATTACK ATTACK ATTACK ATTACK ...
benign benign
```

Question:

> Does correlation among discoveries cause nominal FDR control to fail?

---

## 16.3 Benign anomaly bursts

Create/evaluate periods containing abnormal-but-benign behavior:

- backups
- scans
- update traffic
- sudden workload increases

Question:

> Does fixed thresholding generate alert floods?

And:

> Which FDR mechanisms remain controlled?

---

## 16.4 Distribution shift

Calibrate in environment \(E_1\).

Deploy in environment \(E_2\).

For example:

\[
\text{CIC calibration}
\rightarrow
\text{ToN deployment}.
\]

Question:

> Does stale calibration invalidate the statistical evidence?

---

## 16.5 Calibration age

Vary how long the benign calibration distribution is kept fixed.

For example:

- fixed once
- daily refresh
- weekly refresh
- rolling window
- adaptive refresh after detected shift

Measure:

\[
\text{calibration age}
\rightarrow
\text{p-value validity}
\rightarrow
\text{FDR}.
\]

---

## 16.6 Attack-family analysis

Stratify results by:

- DDoS
- DoS
- brute force
- reconnaissance
- botnet
- web attacks
- infiltration
- multi-stage attacks

Question:

> Are some attack families systematically suppressed by FDR control because their detector scores are weaker?

---

# 17. Calibration as a Core Trustworthiness Question

The statistical guarantee depends on the validity of the evidence supplied to the FDR controller.

Suppose:

\[
P_{\text{cal}}(S)
\neq
P_{\text{deploy}}(S).
\]

Then the empirical p-values may cease to behave like valid null p-values.

This may produce:

\[
\text{distribution shift}
\rightarrow
\text{miscalibrated p-values}
\rightarrow
\text{FDR violation}.
\]

This is not merely a nuisance.

It can become one of the main scientific findings:

> **A nominal statistical guarantee attached to an ML security system is only trustworthy if the score-to-evidence calibration remains valid.**

The paper should explicitly measure this chain.

Possible diagnostics include:

- p-value histograms for known benign data
- calibration error
- null-uniformity diagnostics
- temporal change in benign score distributions
- FDR violation as calibration drifts

---

# 18. Established Adaptation Strategies to Evaluate

The paper does not initially need to propose a new method.

Instead, evaluate whether established approaches restore control.

## Rolling calibration

\[
C_t =
\{x_{t-W},...,x_{t-1}\}.
\]

## Weighted calibration

Give recent benign observations higher weight.

## Block-based calibration

Account for temporal dependence by calibrating over blocks rather than individual events.

## Periodic reset

Re-estimate calibration after fixed intervals.

## Drift-triggered reset

Use an established change detector and recalibrate after detected distribution shift.

## e-value-based testing

Investigate whether dependence-robust statistical evidence improves control under correlated cyber streams.

The key paper question remains empirical:

> Which established statistical mechanisms are actually reliable in cybersecurity?

---

# 19. Desired Headline Figure

One possible central figure is:

```text
False Discovery Proportion
70% ┤                        fixed threshold
    │               ╭──────────────╮
50% ┤        ╭──────╯              ╰────
    │
30% ┤
    │
10% ┤  ───── dependence-aware FDR ──────
 5% ┼──────────────────── target q=.05
    │
 0% └────────────────────────────────────
       normal    drift    attack    normal
                         time →
```

The purpose is to visually communicate:

1. conventional thresholding gives unstable analyst-facing alert quality;
2. some online procedures stabilize it;
3. particular shifts may break the nominal guarantee.

---

# 20. Desired Main Results

The ideal paper would establish several findings.

## Finding 1 — Conventional thresholds do not control alert quality

Even when classifier-level metrics appear good, realized FDP varies substantially across time and traffic regimes.

---

## Finding 2 — Online FDR can stabilize alert streams

Under stationary or moderately dependent conditions, appropriate online FDR procedures provide substantially more stable false-discovery behavior than ordinary IDS thresholds.

---

## Finding 3 — Cybersecurity dependence matters

Some procedures lose control under:

- strongly correlated flows
- large attack bursts
- benign anomaly bursts
- dataset shift

---

## Finding 4 — Calibration failure explains much of the breakdown

Changes in the benign score distribution produce invalid statistical evidence.

That results in:

\[
\text{bad calibration}
\rightarrow
\text{bad p/e-values}
\rightarrow
\text{FDR violation}.
\]

---

## Finding 5 — Established adaptive mechanisms restore some control

Rolling calibration, dependence-aware procedures or e-value approaches substantially improve robustness.

No fundamentally new algorithm is required.

---

## Finding 6 — FDR control reduces analyst workload without destroying incident recall

Ideally:

\[
\boxed{
\text{fewer false investigations}
+
\text{high incident recall}
+
\text{acceptable detection latency}
}
\]

This provides the application-level value.

---

# 21. What Would Count as a Successful Paper?

The project does **not** depend on showing that FDR methods dominate every baseline.

A publishable outcome could be:

> Existing IDS evaluation metrics hide large variation in analyst-facing false discoveries. Online statistical error-control methods provide useful guarantees under some security regimes, but common cybersecurity properties such as temporal dependence and distribution shift can invalidate those guarantees.

An even stronger result would be:

> We identify which combinations of calibration and online testing procedures remain reliable under realistic cyber conditions and quantify the corresponding analyst-workload versus attack-detection tradeoff.

A strong negative result is also useful:

> Nominal FDR guarantees routinely fail on cybersecurity streams unless calibration and dependence are explicitly addressed.

That would itself be an important trustworthy-ML conclusion.

---

# 22. Expected Contributions

A possible introduction could claim four contributions.

## C1 — Problem formulation

We formulate analyst-facing ML intrusion alerting as an **online multiple-testing problem** and argue that false-discovery control is a more operationally meaningful trust objective than classifier-level false-positive rates alone.

## C2 — Systematic empirical evaluation

We conduct a large-scale evaluation of established online FDR procedures across:

- multiple ML detectors
- multiple cybersecurity datasets
- multiple attack families
- multiple target FDR levels
- multiple traffic regimes

## C3 — Security-specific stress testing

We characterize how:

- temporal dependence
- attack burstiness
- benign anomaly bursts
- changing attack prevalence
- distribution shift
- calibration aging

affect the validity of statistical alert guarantees.

## C4 — Operational security evaluation

We quantify the relationship between false-discovery control and:

- analyst workload
- incident recall
- attack recall
- missed incidents
- time-to-first-detection
- detection latency

---

# 23. Proposed Paper Structure

## 1. Introduction

- ML IDS systems are typically evaluated as classifiers.
- SOC analysts consume alerts, not AUROC.
- False discoveries are an operational trust problem.
- Online multiple testing offers an established statistical framework.
- Cybersecurity streams challenge its assumptions.
- State research questions and contributions.

---

## 2. Background and Related Work

### 2.1 Machine-learning intrusion detection

### 2.2 IDS evaluation and deployment gaps

### 2.3 SOC alert fatigue

### 2.4 Multiple hypothesis testing

### 2.5 False Discovery Rate

### 2.6 Online FDR control

### 2.7 Score calibration, conformal inference and e-values

### 2.8 Distribution shift and dependence in security telemetry

---

## 3. Problem Formulation

Define:

\[
x_t,\;
y_t,\;
s_t,\;
p_t,\;
H_t,\;
R_t,\;
V_t,\;
FDP_t,\;
FDR_t.
\]

Explain the mapping:

```text
security event
    ↔ hypothesis test

alert
    ↔ discovery

false alert
    ↔ false discovery
```

State the assumptions required by each statistical procedure.

---

## 4. Experimental Framework

### 4.1 Datasets

### 4.2 Chronological splits

### 4.3 ML detectors

### 4.4 Score-to-evidence calibration

### 4.5 FDR procedures

### 4.6 Conventional IDS threshold baselines

### 4.7 Metrics

### 4.8 Incident construction

---

## 5. Does Conventional IDS Thresholding Control Alert Quality?

Answer RQ1.

Demonstrate how FDP changes over time despite apparently strong classification performance.

---

## 6. Online FDR Control for Security Alerts

Answer RQ2.

Compare procedures across:

- target \(q\)
- detector
- dataset

Show the basic accuracy / FDR / recall tradeoff.

---

## 7. When Do the Guarantees Fail?

Answer RQ3.

Analyze:

- dependence
- burstiness
- prevalence
- benign anomalies
- shift
- calibration age

This may become the paper's most important empirical section.

---

## 8. Restoring Control

Evaluate established mechanisms:

- rolling calibration
- weighted calibration
- block calibration
- recalibration
- dependence-aware procedures
- e-value methods

No requirement to invent a new model.

---

## 9. Security Utility and Analyst Workload

Answer RQ4.

Evaluate:

- incident recall
- attack recall
- alerts/day
- false investigations/day
- time-to-detection
- missed incidents

---

## 10. Cross-Dataset and Live-Fire Validation

Answer RQ5.

Use:

- NF-ToN-IoT-v3
- AIT-ADS
- LSPR23

to determine whether conclusions extend beyond the development dataset.

---

## 11. Discussion

Topics:

- what does a 5% FDR target actually mean operationally?
- event-level vs incident-level discoveries
- delayed labels in real SOCs
- incomplete labels
- calibration poisoning
- adversarial manipulation
- changing threat prevalence
- guarantee assumptions
- when practitioners should not trust nominal FDR control

---

## 12. Limitations

Potential limitations:

- benchmark datasets do not perfectly represent production SOCs
- labels are much cleaner than real-world labels
- event grouping into incidents may rely on dataset annotations
- online FDR assumptions vary by method
- adaptive adversaries are only partially represented
- real analyst workload is approximated by alert counts rather than a full human study

---

## 13. Conclusion

Main message:

> Trustworthy intrusion detection requires reasoning about the reliability of the alert stream, not only the predictive quality of the underlying classifier.

---

# 24. Minimal Experimental Version

A first implementation does not need the entire final paper.

Start with:

## Dataset

NF-CSE-CIC-IDS2018-v3

## Detector

XGBoost

## Split

Chronological:

```text
train
calibration
test stream
```

## Methods

1. fixed F1 threshold
2. fixed FPR threshold
3. naive \(p<0.05\)
4. LORD
5. SAFFRON
6. ADDIS

## Target

\[
q=0.05.
\]

## Metrics

- cumulative FDP
- final FDP
- attack recall
- incident recall
- alerts/day

## First question

> Does an established online FDR procedure materially stabilize false discoveries compared with conventional IDS thresholding?

If the answer is clearly yes or clearly no for interesting reasons, proceed to the full project.

---

# 25. Phase 2 Experiments

After establishing the basic phenomenon:

1. add multiple detectors;
2. add multiple target FDR levels;
3. add attack prevalence experiments;
4. add burstiness experiments;
5. add distribution shift;
6. add rolling calibration;
7. replicate on NF-ToN-IoT-v3;
8. test alert-level applicability on AIT-ADS;
9. conduct final live-fire validation on LSPR23.

---

# 26. Main Technical Risk

The largest technical risk is:

> Are the constructed p-values/e-values valid enough for the claimed FDR procedures?

This must be treated very carefully.

The paper should not imply unconditional FDR guarantees if assumptions do not hold.

Instead distinguish:

### Nominal guarantee

What the statistical method guarantees under its assumptions.

### Empirical control

What actually occurs in the cybersecurity stream.

The gap between them is itself part of the research question.

---

# 27. Main Novelty Risk

The paper must avoid being framed as:

> We applied LORD to intrusion detection.

The novelty is instead the combination of:

1. **analyst-facing false discoveries as the trust objective**;
2. **online rather than static error control**;
3. **security-specific dependence and drift stress testing**;
4. **careful score-to-statistical-evidence calibration**;
5. **event-level and incident-level security evaluation**;
6. **cross-dataset and live-fire validation**;
7. **analysis of when nominal statistical guarantees fail**.

The contribution is therefore an empirical and methodological cybersecurity study rather than a new FDR algorithm.

---

# 28. One-Sentence Paper Pitch

> **We ask whether mature online false-discovery-control methods can turn ML intrusion scores into trustworthy analyst-facing alerts, and systematically determine when their guarantees hold or fail under the dependence, burstiness, base-rate shifts and distribution drift of realistic cybersecurity streams.**

---

# 29. Short Abstract-Level Concept

Machine-learning intrusion detection systems are commonly evaluated using classifier-centric metrics such as AUROC, F1 and false-positive rate, yet security analysts interact with streams of alerts rather than individual predictions. This work reframes ML intrusion alerting as an online multiple-hypothesis-testing problem and evaluates whether established false-discovery-rate control methods can provide meaningful guarantees on the fraction of analyst-facing alerts that are benign. Using several conventional supervised and anomaly-based detectors across multiple chronological cybersecurity datasets, we compare standard IDS thresholding with established online FDR procedures under varying attack prevalence, temporal dependence, burstiness and distribution shift. We additionally study how score calibration affects the validity of statistical evidence and whether rolling or dependence-aware calibration restores control when the deployment distribution changes. Beyond event-level accuracy, we evaluate incident recall, detection latency and analyst workload, including validation on realistic alert and live-fire cybersecurity datasets. The objective is not to introduce a new detector or statistical algorithm, but to determine when existing statistical guarantees can—or cannot—make ML-based intrusion detection operationally trustworthy.

---

# 30. Research Philosophy

This project intentionally follows the structure:

\[
\boxed{
\text{established statistical method}
+
\text{underexplored security formulation}
+
\text{realistic empirical stress test}
+
\text{operational consequence}
}
\]

The ML models are not expected to be novel.

The FDR methods are not expected to be novel.

The contribution lies in showing that a mature statistical framework answers an important cybersecurity question that standard IDS evaluation does not address, and in establishing the conditions under which its guarantees remain meaningful in real security telemetry.
