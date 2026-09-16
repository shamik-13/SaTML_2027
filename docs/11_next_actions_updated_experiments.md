# Next Actions for the Online Error Control / Trustworthy-IDS Project
## Recommended Execution Plan After the Updated Experimental Record

### Current status

The project has moved beyond the exploratory phase.

The main questions from the earlier review have now largely been addressed:

- modern online procedures have been tested;
- full-stream evaluation has been run;
- a second detector has been added;
- the padding theorem has been formalized;
- realistic padding pools have been tested;
- matched operating points have been constructed;
- analyst-feedback baselines have been evaluated;
- grouping families, k, q, cap policies, horizon misspecification, calibration-conditional fixes and boosting have all been studied.

The project now has enough evidence for a coherent SaTML-style paper.

The goal should therefore change from:

> **“What else can we test?”**

to:

> **“What remaining issues could still undermine the paper, and what is the smallest coherent paper that captures the strongest result?”**

The next phase should be short, targeted and publication-oriented.

---

# 1. Immediate Priority: Diagnose the Position-0.85 Anti-Conservatism

This is the single most important remaining credibility issue.

The updated record shows that the procedure-comparison window at position 0.85 has a benign firing rate far above nominal:

\[
\text{observed benign firing rate}
\gg
\text{nominal firing rate}.
\]

The measured inflation is approximately:

\[
50.9\times
\]

for one detector seed and roughly:

\[
24.3\times
\]

for the other.

At this position, the constructed e-values therefore do not satisfy the nominal validity condition.

This does **not** invalidate the feasibility and structural-silence results.

In fact, anti-conservative evidence makes procedures fire more easily, so the inability-to-fire results are conservative.

However, it does affect any claim phrased as:

> “The method controls FDR.”

At this window, the observed FDP is an empirical measurement, not a theorem-backed guarantee.

## Next experiment

Extract all benign-labelled deployment flows satisfying the extreme-tail condition, approximately:

\[
s(x)
>
\max_{z\in C} s(z).
\]

Then compare them with ordinary benign flows.

Inspect:

- source IP;
- destination IP;
- source and destination port;
- protocol;
- service;
- timestamp;
- whether the source appears in malicious traffic;
- whether the destination appears in malicious traffic;
- proximity to attack periods;
- duplicated or near-duplicated records;
- network segment;
- feature distributions;
- whether a single service/class dominates the tail.

The goal is to distinguish between three explanations:

\[
\boxed{\text{distribution shift}}
\]

\[
\boxed{\text{systematic label error}}
\]

\[
\boxed{\text{new benign traffic mode}}
\]

## Decision rule

### If the cause is identifiable

Explain it explicitly and either:

- correct the labels/data;
- stratify the traffic;
- recalibrate appropriately;
- or treat the window as a deployment-shift case study.

### If the cause is not identifiable

Do **not** use position 0.85 as the sole headline example for guaranteed FDR claims.

Instead:

1. move the main guaranteed comparison to a cleaner window;
2. retain position 0.85 as an explicit failure case showing that evidence validity can collapse under deployment shift.

That could strengthen the paper rather than weaken it.

---

# 2. Manually Audit the Alert Sample

The experimental record already produces a sample of approximately 152 emitted alerts for manual inspection.

This should be completed before paper submission.

The paper's headline metrics include false discoveries, so the quality of the labels directly matters.

## Audit protocol

For each sampled alert, assign one of:

```text
clearly malicious
probably malicious
ambiguous
probably benign
clearly benign
```

Record:

- timestamp;
- source/destination;
- service/protocol;
- detector score;
- grouping identifier;
- dataset label;
- analyst judgement;
- evidence/reason for the judgement.

If possible, cross-reference the Locked Shields exercise documentation or associated logs.

## Output

Report:

- agreement rate;
- clearly incorrect labels;
- ambiguous fraction;
- qualitative causes of disagreements.

A simple table in the appendix would be sufficient.

## Why this matters

A second benchmark dataset cannot repair weak trust in the labels of the primary experiment.

The primary data should be audited first.

---

# 3. Highest-Value New Security Experiment: Attack ADDIS's State

This is the one genuinely new experiment I would prioritize.

The updated procedure comparison identifies two important escape mechanisms:

1. **online e-BH** escapes absorbing silence by using a historical fixed point;
2. **ADDIS** escapes because its spending index advances only on selected-but-noncandidate hypotheses.

For ADDIS, the relevant index behaves roughly as:

\[
S^t - C_{0+}.
\]

On the current threshold-conformal stream, this remains close to zero because episodes are mostly:

- discarded at p = 1, or
- immediately candidates.

Very few observations fall into:

\[
(\lambda,\tau].
\]

This prevents the spending sequence from advancing.

That creates a potential attack surface.

## Attack hypothesis

An adversary deliberately generates precursor groups with:

\[
p \in (\lambda,\tau].
\]

These groups:

- consume advancement of the ADDIS testing index;
- do not produce useful discoveries;
- make future thresholds smaller;
- potentially restore the very alpha-death behavior ADDIS otherwise escapes.

This is fundamentally different from the existing dilution attack.

---

# 4. Define the ADDIS State-Manipulation Attack

Let:

\[
B
\]

be the number of attacker-generated precursor groups.

Define:

\[
B^*
=
\min B
\]

such that a later target attack is no longer detected.

Measure:

\[
P(\text{target detected}\mid B)
\]

for increasing B.

Possible attack objectives:

## A. Suppress detection

\[
P(\text{alert on target}) \le \epsilon.
\]

## B. Delay detection

\[
TTD_{\text{attack}} \ge \Delta.
\]

## C. Force structural silence

If possible:

\[
\alpha_t < \text{evidence floor}.
\]

## D. Reduce recall over an attack campaign

Measure campaign/episode recall as the attacker consumes the spending state.

---

# 5. Test the ADDIS Attack Under Different Attacker Knowledge

Do not rely only on a white-box attacker.

Test:

### White-box

Attacker knows:

- lambda;
- tau;
- the score/evidence transformation;
- current controller state.

### Grey-box

Attacker knows the procedure and parameters but not the exact current state.

### Black-box

Attacker sends ordinary-looking precursor traffic selected only from common services/protocols and observes whether the later attack is blocked/alerted.

If the attack survives under the grey-box or black-box setting, it becomes much stronger.

---

# 6. If the ADDIS Attack Works, Make It a Core Security Contribution

The paper would then contain two distinct attack surfaces.

## Attack Surface 1 — Within-Hypothesis Composition

The attacker pads a grouped episode with benign-looking events.

This reduces aggregated evidence.

Conceptually:

\[
\text{attack evidence}
+
\text{benign padding}
\rightarrow
\text{diluted group evidence}.
\]

You already have a theorem showing that symmetric e-merging families that can attain the rejection threshold cannot be padding-robust.

## Attack Surface 2 — Across-Hypothesis State

The attacker manipulates the sequential controller's internal spending state.

Conceptually:

\[
\text{precursor hypotheses}
\rightarrow
\text{spending-state advancement}
\rightarrow
\text{weaker future threshold}
\rightarrow
\text{target suppression}.
\]

Together these would give a powerful security framing:

> The attacker can manipulate both the composition of individual hypotheses and the state of the sequential decision process.

That is substantially stronger than a single evasion experiment.

---

# 7. After These Tasks, Freeze the Experiment Set

The project already has more findings than can comfortably fit in a 12-page main-track paper.

Do not keep adding:

- more classifiers;
- more online FDR procedures;
- more spending-sequence families;
- more cap variants;
- more arbitrary stress tests.

Once the anti-conservatism analysis, alert audit and ADDIS attack are done:

> **freeze the experiment matrix.**

Only add a new experiment afterward if it is required to answer a concrete reviewer-style objection.

---

# 8. Freeze the Paper Around Three Main Contributions

The current experimental record contains many findings, but the paper should revolve around three.

## Contribution 1 — Feasibility of Online Statistical Guarantees at Security Scale

Core result:

Finite-resolution conformal evidence has a maximum value:

\[
M = \frac{|C|+1}{k}.
\]

A rejection requires:

\[
E_t \ge \frac{1}{\alpha_t}.
\]

Therefore a necessary feasibility condition is:

\[
\alpha_t \ge \frac{1}{M}.
\]

For a broad class of online procedures whose spending index advances with elapsed hypotheses, the testing level eventually falls below this boundary.

Thus:

\[
\text{finite evidence resolution}
+
\text{long sequential horizon}
\rightarrow
\text{finite discovery horizon}.
\]

The paper now has explicit propositions describing the structural families for which this holds.

It also has important counterexamples that define the boundary:

- ADDIS can escape through selective advancement;
- online e-BH can avoid an absorbing rejection-free state by making simultaneous decisions;
- neither eliminates the calibration/power problem entirely.

This makes the theoretical claim more credible because its scope is explicit.

## Contribution 2 — Granularity–Feasibility Tradeoff

Security ML produces very fine-grained predictions.

Examples:

\[
\text{flow}
\]

or

\[
\text{event}.
\]

But security operations use larger units:

\[
\text{host}
\rightarrow
\text{session}
\rightarrow
\text{episode}
\rightarrow
\text{incident}.
\]

Coarsening the statistical unit reduces T and therefore restores feasibility.

However, the updated experiments show that this has a measurable cost.

The same underlying detections can maintain similar malicious-flow coverage while episode-level recall falls as groups become coarser.

This yields:

\[
\boxed{
\text{fine granularity}
\Rightarrow
\text{better security resolution but statistical difficulty}
}
\]

versus

\[
\boxed{
\text{coarse granularity}
\Rightarrow
\text{statistical feasibility but lower episode resolution}
}
\]

This should be called something like:

## The Granularity–Feasibility Tradeoff

It is a domain-specific trustworthy-ML result, not merely an implementation choice.

## Contribution 3 — The Statistical Trust Layer Is an Attack Surface

The paper now has a strong theorem:

For any threshold:

\[
\tau > 1,
\]

no symmetric e-merging family that can actually attain tau can remain robust to arbitrary padding.

The mechanism is straightforward.

If evidence is aggregated symmetrically, padding with uninformative events lowers the evidence density.

At sufficiently large padding r,

\[
F_{m+r}(x,0^r) < \tau.
\]

The real-data experiments then show that the attack is practical.

Across several realistic benign padding pools:

- generic benign;
- attacker-origin;
- protocol-matched;
- service-matched;
- black-box benign;

the suppression cost is essentially unchanged.

This provides a clean progression:

\[
\boxed{
\text{theorem}
\rightarrow
\text{real detector}
\rightarrow
\text{real network data}
\rightarrow
\text{black-box attack}
}
\]

If the ADDIS state attack also works, this contribution becomes even stronger.

---

# 9. Move the Remaining Findings into Supporting Roles

Several current findings are excellent but should not become standalone contributions.

## k = 1 is feasible but least reliable

Use this inside Contribution 1 to show:

\[
\text{evidence resolution}
\leftrightarrow
\text{conditional reliability}.
\]

## Bates conditional correction is costly

Use this to answer:

> “Why not simply apply the known calibration-conditional correction?”

The answer is:

> it works statistically, but consumes the evidence ceiling at precisely the rank where feasibility is already marginal.

## Boosting recovers no power

Use this to answer:

> “Why not apply modern e-value boosting?”

The answer is:

> the threshold-conformal e-value is already two-point and extremal, so there is no sub-threshold mass to redistribute.

## Spending sequence matters more than q

Use this as an operational implication.

The operator believes q is the meaningful control parameter.

But empirically gamma moves the operating point more than a large sweep of q.

This suggests that nominal FDR control gives the operator less direct control over:

- alert budget;
- recall;
- operational workload;

than expected.

This is an important practical result but does not need to become a fourth theoretical contribution.

---

# 10. Begin Writing the Paper Now

The project is now mature enough to start drafting.

The next writing artifact should be a **one-page paper contract**.

It should contain:

1. final working title;
2. one-sentence thesis;
3. problem statement;
4. three contributions;
5. four research questions;
6. threat model;
7. six or seven essential figures/tables;
8. explicit non-claims.

Do this before writing full prose.

---

# 11. Proposed Paper Thesis

A good current thesis is:

> **Online statistical error guarantees for ML intrusion detection face a three-way tension between finite evidence resolution, security alert granularity and adversarial robustness: fine-grained control becomes difficult or infeasible at long security horizons, coarsening restores feasibility at the cost of episode-level resolution, and the required aggregation creates a low-cost evasion surface.**

If the ADDIS state-manipulation attack works, extend it to:

> **...and even procedures that escape the feasibility boundary can expose their history-dependent decision state to adversarial manipulation.**

---

# 12. Proposed Research Questions

## RQ1 — Feasibility

> Under what combinations of evidence resolution, calibration size, stream horizon and online procedure can a security alert still be statistically rejected?

## RQ2 — Granularity

> How does changing the alerting unit from flows to deployable security episodes affect feasibility, recall and operational resolution?

## RQ3 — Attackability

> Can an adversary manipulate the composition or sequential state of statistically controlled alerts to suppress detection?

## RQ4 — Operational value

> What does formal online error control provide compared with matched-budget thresholds and feedback-based alert controllers?

---

# 13. Essential Figures / Tables

The paper should probably target approximately six or seven headline visual elements.

## Figure 1 — System Model

```text
network flow
    ↓
ML detector
    ↓
conformal evidence
    ↓
group aggregation
    ↓
online error controller
    ↓
SOC alert
```

Mark the two attack surfaces:

- within-group padding;
- across-time controller-state manipulation.

## Figure 2 — Feasibility Envelope

Plot minimum calibration size against deployment horizon.

Curves for:

- LOND;
- LORD++;
- e-LOND/e-GAI;
- online e-BH;
- relevant grouped configurations.

## Figure 3 — Granularity–Feasibility Tradeoff

X-axis: group granularity.

Y-axes or panels:

- feasibility margin;
- episode recall;
- malicious-flow coverage.

## Figure 4 — Padding Attack

Plot:

- number of padding flows
- versus probability of episode suppression.

Use several padding pools.

## Table 1 — Procedures and Assumptions

Columns:

- procedure;
- evidence type;
- spending index;
- horizon knowledge;
- dependence assumption;
- finite-horizon theorem applies?;
- guarantee valid on current evidence?;
- observed power.

## Table 2 — Main Real-Data Results

For selected clean windows:

- detector;
- grouping;
- procedure;
- alerts;
- FDP;
- episode recall;
- flow coverage;
- feasibility margin;
- structural silence.

## Figure/Table 3 — Operational Frontier

Compare:

- online error control;
- fixed threshold;
- matched-budget threshold;
- feedback controller.

Use the same achievable score frontier.

---

# 14. Second Dataset: Run in Parallel, Not as a Blocker

A second dataset is still valuable, especially one with true flow-to-campaign ground truth.

Its purpose should be narrow:

> validate the granularity result using genuine campaign labels.

Do **not** rerun the entire paper on the second dataset.

Only reproduce:

1. feasibility versus granularity;
2. flow-level versus campaign-level recall;
3. perhaps one dilution-attack experiment.

If no suitable dataset is found quickly, proceed with LSPR23 and explicitly call the units **episodes**, not incidents.

---

# 15. Second Feedback Controller: Low Priority

The current proportional feedback controller is already enough to establish:

- prompt feedback can track the desired FDP region;
- long feedback delays substantially weaken control.

A second controller would help rule out controller-specific effects, but this is not a blocker.

If time permits, implement either:

- PI control;
- direct quantile targeting;
- exponential moving-average FDP control.

Treat it as a robustness check, not a central contribution.

---

# 16. What Not to Do Next

Do **not** spend the next week doing:

- five more classifiers;
- ten more datasets;
- every FDR procedure in the literature;
- additional arbitrary q sweeps;
- additional random spending sequences;
- more cap policies;
- broad hyperparameter searches.

The project already has enough experimental mass.

Additional experiments now have diminishing scientific value and increase the risk that the paper becomes unfocused.

---

# 17. Concrete Execution Order

## Phase A — Credibility closure

### A1. Diagnose position-0.85 anti-conservatism

Priority: **critical**

Output:

- explanation;
- corrected/stratified analysis or explicit failure-case framing.

### A2. Manually audit the alert sample

Priority: **critical**

Output:

- alert-label audit table;
- uncertainty statement.

## Phase B — Final high-value security experiment

### B1. ADDIS spending-state manipulation attack

Priority: **high**

Output:

\[
B^*
\]

minimum precursor budget required to suppress a later attack.

Test white-box, grey-box and black-box variants if feasible.

## Phase C — Freeze research

After A1, A2 and B1:

> **stop adding core experiments.**

Create a frozen list of:

- accepted headline claims;
- supporting claims;
- caveats;
- non-claims.

## Phase D — Paper contract

Write one page containing:

- title;
- thesis;
- contributions;
- RQs;
- figures;
- datasets;
- methods;
- threat model;
- exclusions.

## Phase E — Start manuscript

Recommended writing order:

1. Problem formulation;
2. feasibility theorem;
3. padding theorem;
4. experimental setup;
5. results;
6. discussion;
7. introduction;
8. related work;
9. abstract.

Writing the introduction last often helps because the real contribution is now much sharper than the project's original motivation.

---

# 18. Decision Gate

After the ADDIS experiment:

## If it works

Paper story:

\[
\boxed{
\text{feasibility}
+
\text{granularity tradeoff}
+
\text{two attack surfaces}
}
\]

This is the strongest version.

## If it does not work

Do not force it.

The paper remains strong with:

\[
\boxed{
\text{feasibility}
+
\text{granularity tradeoff}
+
\text{padding theorem/attack}
}
\]

The failed ADDIS attack can be mentioned as a negative robustness check.

---

# 19. Current Suggested Title

### Preferred

**When Guarantees Go Silent: Feasibility and Attackability of Online Error Control for ML Intrusion Detection**

Other options:

### More technical

**Finite Evidence, Long Streams: Feasibility Limits of Online Error Control in ML Intrusion Detection**

### More security-oriented

**Attacking the Trust Layer: Feasibility and Evasion in Statistically Controlled ML Intrusion Detection**

### Granularity-oriented

**Flows Are Not Alerts: Statistical Feasibility and Adversarial Aggregation in ML Intrusion Detection**

---

# 20. Immediate Next Action

If only one task is started next:

> **Perform the forensic analysis of the position-0.85 benign extreme-tail events.**

This is now the highest-value task because it determines whether the cleanest current procedure-comparison window can support guarantee-level claims.

Immediately afterward:

1. complete the manual alert audit;
2. test ADDIS state manipulation;
3. freeze the experiments;
4. start the one-page paper contract.

At this stage, the project is no longer searching for a result.

It is **validating and packaging a result that already exists**.
