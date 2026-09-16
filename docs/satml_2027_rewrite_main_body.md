# Editorial diagnosis and proposed SaTML 2027 rewrite

This document has two parts:

1. an editorial diagnosis of the current 36-page draft; and
2. a near-complete rewrite of the 12-page main body, with explicit TODO markers for tables, figures, proofs, and appendix material.

The proposed prose preserves the current manuscript's terminology, numerical results, theorem scope, and citation numbering. Before pasting it into Overleaf, replace the numeric citations with your LaTeX citation commands, restore your equation/theorem labels, and verify every number against the result cache.

---

## Part I. Editorial diagnosis

### The paper's one-sentence thesis

**A statistical error-control layer can be formally valid yet operationally empty at security-scale horizons; the aggregation used to recover feasibility then becomes an adversarial attack surface.**

That sentence should govern the title, abstract, introduction, section order, figure selection, and conclusion. The current draft already contains this story, but it is obscured because nearly every experiment is promoted to the same narrative level.

### Strongest contributions, ranked

#### 1. The finite discovery horizon and exact feasibility boundary

This is the strongest and most general contribution. Finite-resolution conformal evidence has a hard ceiling, while many online FDR procedures spend a summable budget whose offered level eventually becomes too small. The paper does more than observe low power: it gives conditions under which the rejection-free state becomes **absorbing**, derives the exact calibration-horizon requirement, and classifies how studied procedures do or do not escape.

The portable statement is

\[
|\mathcal C| \ge \frac{kT}{c_0}-1,
\]

under horizon-uniform spending, where \(c_0=w_0\) for LORD++ and \(c_0=\alpha\) for LOND/e-LOND. At \(k=1\) and \(\alpha=0.05\), e-LOND needs twenty calibration units per tested hypothesis. This result is independent of detector quality, score distribution, and the group-validity assumption.

Why reviewers should care: prior work has observed resolution loss or alpha-death empirically. Your sharper addition is the transition from "underpowered" to "structurally unable to reject," together with the exact scaling law and the classification of escape mechanisms.

#### 2. Symmetric aggregation is inherently padding-vulnerable

Theorem 10 is the second anchor. It is a clean impossibility result: no symmetric e-merging family that can cross a rejection threshold above one can remain robust when an adversary appends zero-evidence members. The arithmetic mean is not just one vulnerable implementation; it is essentially the best possible symmetric rule for this purpose, and the quantitative padding bound is tight for the mean.

This theoretical result is unusually well supported empirically:

- the attack uses ordinary traffic to the host pair already under attack;
- constructing the pad is black-box, although exact minimal sizing is an oracle lower bound;
- controlled replay reaches the closed-form suppression threshold exactly;
- the result transfers to a host-conditioned detector; and
- the full chain suppresses 84 of 85 detected episodes on AIT-LDSv2.0, with all nine evaluated host-conditioned detections also suppressed.

This is the contribution most clearly aligned with SaTML's attack-and-system-security audience.

#### 3. Granularity is the bridge between feasibility and attackability

Do not sell this as an independent third theorem. Its narrative role is stronger as the causal bridge:

1. the feasibility boundary forces the defender to reduce the number of hypotheses;
2. grouping is the direct way to do so;
3. grouping buys feasibility exactly in proportion to the reduction in \(T\);
4. it pays in semantic resolution, measured by alert blur; and
5. the resulting group composition is what the padding attack manipulates.

The fixed-denominator result is the clean one: as the source-destination bucket grows from five minutes to one day, an alert goes from representing one atomic malicious episode to representing roughly 20--40. Moving episode recall and malicious-flow coverage should remain secondary because their denominators or traffic mass change with the grouping.

#### 4. Evidence-conditioned controller state as a second attack surface

The ADDIS state-manipulation result is intellectually interesting but should be a **supporting contribution**, not an equal-length second half of the paper. The real-stream demonstration occurs at the known-invalid window, and the attack is conspicuous rather than low cost. Its strongest form is therefore:

- a closed-form controllability result for an escape mechanism;
- a real-stream mechanism demonstration, explicitly not guarantee-bearing; and
- a synthetic experiment showing that the same manipulation silences ADDIS even when its FDR guarantee continues to hold on the attacked stream.

State clearly that this result does not cover online e-BH, which escapes through a history-wide fixed point rather than an attacker-advanced spending index.

#### 5. The group-validity premise and the cost of removing it

Assumption 1 and Lemma 1 are necessary for intellectual honesty, but they should support the paper rather than become a parallel storyline. State the group-local conditional premise early, prove the group e-value lemma in the appendix, and include one compact dependency statement:

- the feasibility theorem does not use Assumption 1;
- the symmetric-padding impossibility does not use Assumption 1;
- empirical FDR interpretations do use it;
- the 0.85 window violates even marginal e-validity and is used only as a stress/mechanism window; and
- direct group calibration removes Assumption 1 but makes the primary and replication configurations infeasible.

### What is currently weakening the paper

The current draft gives equal space to core results, robustness checks, negative experiments, implementation audits, alternative orderings, operating-point baselines, label investigations, and every attempted mitigation. This creates five apparent papers:

1. a conformal-resolution/online-FDR theory paper;
2. a granularity study;
3. an aggregation-evasion paper;
4. an adaptive-controller poisoning paper; and
5. an operational IDS benchmarking paper.

The rewrite should present only one paper: **a compositional security analysis of a statistical trust layer**. Everything else must answer one of three questions: why it goes silent, what the defender must do to recover, or how that recovery becomes attacker-facing.

### Main-body versus appendix triage

#### Keep in the 12-page body

- the pipeline figure and bounded-evidence equation;
- the finite-horizon theorem statements and short proof ideas;
- the calibration-horizon corollary and its security-scale interpretation;
- a compact procedure/escape taxonomy;
- the granularity-feasibility equation and alert-blur result;
- Theorem 10 and a short proof sketch;
- the black-box construction versus oracle-sizing distinction;
- primary and replication padding costs;
- controlled replay and transfer results;
- a short ADDIS state-manipulation subsection, including the guarantee-valid synthetic result;
- one paragraph on Assumption 1 and what depends on it;
- limitations and concrete design guidance.

#### Move to appendices

- full proofs;
- all five windows by two detector seeds;
- full procedure benchmark and both spending sequences;
- all grouping families and all bucket widths;
- the full order ensemble and keyed/public-hash insertion analysis;
- smoothing, restart, closure, donation, decision-deadline, and e-TOAD matrices;
- all padding pools and static-versus-running cost variants;
- cap and asymmetric-weight sweeps;
- group-MAX/direct-group-calibration details;
- calibration contamination;
- external red-team task matching;
- lower-prevalence sweep;
- operating-point frontier and analyst-feedback controllers;
- label audit, metadata-stratified diagnostics, and Bates adjustment;
- implementation/transcription unit tests and complete reproducibility details.

#### Remove from the paper body entirely, or keep only in an online supplement

- the long operational-feedback section as a standalone result;
- repeated descriptions of first-flow order as an optimistic upper bound;
- repeated explanations that 0.85 is invalid;
- repeated lists of what the paper does not claim;
- detailed discussion of every failed mitigation in the main text;
- table captions that function as multi-paragraph mini-sections.

Centralize each qualification once, then use a short notation such as "canonical order" or "stress window" thereafter.

### Recommended page budget

| Section | Target pages | Purpose |
|---|---:|---|
| 1. Introduction | 1.25 | Problem, causal chain, two contributions and bridge |
| 2. Trust-layer model and evaluation protocol | 1.50 | Evidence ceiling, grouping, validity premise, threat model, datasets |
| 3. When valid controllers go silent | 2.25 | Theorems, exact boundary, scale, escape taxonomy |
| 4. Aggregation buys feasibility at a resolution cost | 1.00 | Granularity bridge |
| 5. Aggregation is a padding attack surface | 2.25 | Impossibility, concrete attack, replay, transfer, mitigations |
| 6. Adaptive state is a second surface | 0.70 | ADDIS mechanism and valid synthetic test |
| 7. Implications, validity, and limitations | 1.10 | Dependency map, design rules, limits |
| 8. Related work | 0.75 | Only nearest work and differentiation |
| 9. Conclusion | 0.20 | One paragraph |
| Figures/tables and layout reserve | 1.00 | Four compact figures/tables |

### Figure and table plan

1. `#TODO_FIGURE_PIPELINE` -- reuse current Fig. 1, but make the causal chain visually explicit: bounded evidence -> finite horizon -> grouping -> padding; place state manipulation as a secondary branch.
2. `#TODO_FIGURE_FEASIBILITY` -- reuse current Fig. 2. Keep the calibration-horizon lines and available-corpus band. Remove decorative detail that is restated in prose.
3. `#TODO_TABLE_PROCEDURE_TAXONOMY` -- compress current Table III and Table XIII to: procedure, spending index, absorbing under C1?, escape mechanism, operational price.
4. `#TODO_FIGURE_GRANULARITY` -- reuse only the feasibility and alert-blur panels of current Fig. 3. Move malicious-flow coverage to the appendix.
5. `#TODO_TABLE_CORE_EMPIRICS` -- a new compact table drawn from current Tables I, XIV, XXI, XXII, and XXIV. It should contain only primary/replication results plus transfer.
6. `#TODO_FIGURE_ATTACKS` -- reuse current Fig. 4, but make panel A the visual anchor. Keep the synthetic guarantee-valid state-attack panel; consider moving the invalid real-stream panel to the appendix or marking it unmistakably as mechanism-only.

---

# Part II. Proposed paper body

## Suggested title

**When Online Guarantees Go Silent: Feasibility and Evasion in ML Intrusion Detection**

Alternative, slightly broader title:

**Validity Is Not Viability: Feasibility and Attackability of Online Error Control for ML Intrusion Detection**

## Abstract

Machine-learning intrusion detectors produce far more scores than a security operations center can inspect. A natural response is to wrap the detector in a statistical trust layer: conformal evidence, aggregation into security-meaningful hypotheses, and an online false-discovery-rate controller. The components may be valid under their stated assumptions, yet their composition can still be operationally empty and adversarially fragile.

We first characterize when bounded conformal evidence can cross an online controller's threshold. For two families covering LOND, LORD++, e-LOND, and e-LORD, an uninterrupted rejection-free run has a finite discovery horizon; after the horizon, infeasibility is absorbing. Under the max-min-optimal horizon-uniform spending sequence, feasibility through \(T\) hypotheses requires \(|\mathcal C|\ge kT/c_0-1\). At flow granularity on our live-fire trace, this means approximately \(3.3\times10^8\) calibration flows for LOND/e-LOND and \(6.5\times10^8\) for LORD++, compared with 1.8--2.4 million available. Grouping reduces \(T\) and therefore buys feasibility exactly, but coarser alerts blur together tens of fine-grained attack units.

That repair creates an attack surface. We prove that no symmetric e-merging family that can fire is robust to appending zero-evidence members. In the deployed mean-aggregation pipeline, an attacker suppresses its own alert using ordinary same-pair traffic: the canonical primary-window detections require 23--33 added flows, and the replication-window median is six. Controlled replay matches the closed form, and the full attack suppresses 84 of 85 detected episodes on a second, benign-inclusive dataset. We further show that an evidence-conditioned escape mechanism exposes controller state: attacker-generated precursors permanently silence ADDIS, including on synthetic streams where its FDR guarantee remains valid.

Our results separate formal validity from feasibility, semantic resolution, and adversarial robustness, and show that guarantees for security ML must be evaluated as properties of the composed system.

## 1. Introduction

A network intrusion detector converts traffic into anomaly scores, but a security operations center (SOC) does not act on scores. It acts on an alert queue and needs to know how much of that queue is likely to be false. Ranking metrics such as AUROC, AUPRC, and recall at a selected threshold do not answer that question. This gap is especially consequential at the low base rates of operational intrusion detection, where even a strong classifier can produce an alert stream dominated by false positives [1, 2].

Online multiple-testing methods offer a principled interface. At time \(t\), a procedure tests one hypothesis, immediately decides whether to reject it, and updates its future testing levels. Procedures such as LOND, LORD++, SAFFRON, ADDIS, and their e-value counterparts control an online false-discovery criterion under different assumptions [3--8]. Conformal calibration can turn a detector score into distribution-free evidence when calibration and null test scores are exchangeable [9, 10], while e-values permit FDR control under arbitrary dependence [11, 12]. These ingredients suggest a modular statistical trust layer:

\[
\text{detector}\rightarrow\text{conformal evidence}\rightarrow
\text{security grouping}\rightarrow\text{online controller}\rightarrow\text{alert}.
\]

The validity of the individual modules does not establish the viability of their composition. In the construction studied here, deterministic conformal evidence is bounded by the finite calibration set, whereas an online procedure spends a finite error budget and generally offers smaller levels as the stream progresses. A formally valid controller may therefore reach a point at which even the largest evidence the detector can produce is insufficient for rejection. In security, where one deployment may contain millions of predictions and the first attack can arrive late, this is not a small-power effect: the alerting mechanism can become structurally silent.

The obvious repair is to test fewer hypotheses. A SOC already aggregates flows into host-, service-, or time-based episodes, so coarsening the alerting unit directly reduces the horizon the controller must survive. This repair is not free. It loses semantic resolution, and it makes the composition of each tested hypothesis partly controllable by the adversary. The same grouping that permits an alert can therefore permit the attacker to dilute it. Procedures that avoid the finite horizon by adapting their spending index to observed evidence expose a second surface: the attacker may control the state that preserves their testing level.

This paper studies that complete causal chain. We do not propose a new detector, conformal construction, or online FDR procedure. We ask when the existing composition can issue an alert, what the necessary repair costs in security semantics, and whether an adversary can exploit the repaired system.

Our contributions are two principal results connected by one operational bridge.

**C1: a feasibility boundary for bounded evidence.** We give sufficient structural conditions for a finite, absorbing discovery horizon. They cover two families containing LOND, e-LOND, e-LORD, and LORD++. For horizon-uniform spending, the resulting calibration requirement is exactly \(|\mathcal C|\ge kT/c_0-1\), where \(c_0\) is the procedure's cold-start coefficient. We identify the two distinct escape mechanisms present among the procedures we study--selective advancement of the spending index and deferred, history-wide reconsideration--and measure what each buys. The phenomenon that finite conformal resolution can hurt online testing is known [13, 14]; our contribution is to characterize when it becomes an impossibility, to derive the exact exchange rate, and to classify the escape routes.

**Bridge: granularity buys feasibility and spends resolution.** Coarsening a security hypothesis reduces \(T\), and hence the required calibration size, in exact lockstep. Against a fixed five-minute source-destination reference, however, a coarse alert represents tens of fine-grained attack units. This is the link between the two principal results: aggregation is the direct route around C1, and the resulting aggregate is what C2 attacks.

**C2: the statistical trust layer is an attack surface.** Within a hypothesis, we prove that no symmetric e-merging family that can fire is invariant to adversarial zero-evidence padding. We instantiate the attack with ordinary traffic, derive its exact suppression threshold for the arithmetic mean, verify it by causal replay, and test transfer to a host-conditioned detector and a second dataset. Across hypotheses, we show that ADDIS's evidence-conditioned spending index can be advanced by attacker-generated precursors until every subsequent target is silent. This second mechanism is expensive on the real trace and does not apply to online e-BH; its significance is the controllability of a class of adaptive escape mechanisms.

We evaluate 16,353,511 flows from the LSPR23 live-fire exercise over five chronological deployment windows and two detector seeds. Position 0.55 is the primary analysis window and 0.62 is a pre-committed replication window. Position 0.85 has a benign tail that clearly violates marginal e-validity and is used only as a stress window for mechanism and attack-cost measurements. Every empirical FDR interpretation at the other windows remains conditional on the group-validity premise stated in Section 2. The feasibility results and the symmetric-padding impossibility do not depend on that premise.

#TODO_FIGURE_PIPELINE

Suggested source: current Fig. 1. Redraw it so the main horizontal story is: finite evidence ceiling -> online spending -> finite discovery horizon -> grouping/restart response. Draw Surface A from the grouping block and Surface B from the evidence-conditioned state. The caption should be no more than four lines.

## 2. Statistical trust layer and evaluation model

### 2.1 Flow-level conformal evidence

Flows \(x_1,x_2,\ldots\) arrive in timestamp order and a detector \(f\) produces scores \(s_i=f(x_i)\). A benign calibration set \(\mathcal C\), disjoint from training and preceding deployment, converts each score into threshold conformal evidence. Let \(K_i\) be the rank of \(s_i\) from the top of the calibration scores. For rank depth \(k\), the flow e-value is

\[
e_i = \frac{|\mathcal C|+1}{k}\,\mathbf 1\{K_i\le k\}.
\tag{1}
\]

Under the null and the relevant exchangeability premise, \(\mathbb E[e_i]\le1\). The construction is deliberately simple and two-point: a flow either reaches the calibration tail and receives \((|\mathcal C|+1)/k\), or receives zero. Its central operational property is the hard ceiling

\[
M=\frac{|\mathcal C|+1}{k}.
\tag{2}
\]

No detector score, however extreme, can generate evidence larger than \(M\). Randomized conformal smoothing removes the deterministic floor, but Section 3 and Appendix E show that this changes the nature rather than the existence of the operational tradeoff.

### 2.2 Security hypotheses and group evidence

A SOC rarely investigates one flow at a time. We therefore group flows into episodes \(G_j\) using pre-committed metadata and a time bucket. The headline configuration is a source-destination host pair in a two-hour bucket. The controller receives the arithmetic mean

\[
E_j = \frac{1}{m_j}\sum_{i\in G_j} e_i,
\tag{3}
\]

where \(m_j=|G_j|\). The mean is valid for every fixed arity under arbitrary dependence among its inputs and, unlike a maximum, does not systematically increase with group size. Its variable-arity use requires a group-level premise.

**Assumption 1 (group-local metadata-conditional validity).** For every benign flow \(i\) in a true-null group \(G_j\),

\[
\mathbb E[e_i\mid\mathcal M_j]\le1,
\tag{4}
\]

where \(\mathcal M_j\) contains only the pre-committed metadata that determines group \(j\): its key, membership and arity, its position under the pre-committed within-bucket order, and the horizon. It contains no information about other groups' composition.

**Lemma 1.** Under Assumption 1, every true-null group has a marginally valid group e-value, \(\mathbb E[E_j]\le1\), for random membership and arity and arbitrary within- and between-group dependence.

The proof is one application of conditional linearity and the tower property and appears in Appendix A. The premise is stronger than unconditional split-conformal validity and is not established by the dataset. We therefore separate all later claims by dependency: the feasibility boundary uses only the ceiling in (2), Theorem 2 is an aggregation result independent of how the evidence was generated, and only guarantee-bearing readings of empirical FDR require Assumption 1.

### 2.3 Online decisions

At hypothesis \(t\), an online procedure offers a level \(\alpha_t\) and rejects when

\[
E_t\ge \frac{1}{\alpha_t}.
\tag{5}
\]

Our guarantee-bearing empirical baseline is e-LOND, which controls FDR under arbitrary dependence when the group e-values are marginally valid. We also study LOND, LORD++, SAFFRON, ADDIS, online e-BH, and recent e-GAI, closure, donation, and decision-deadline variants. Their proofs rely on different assumptions; for the present analysis, the important distinction is what advances their spending sequence. Section 3 reduces the full list to a compact taxonomy.

We use \(q=\alpha=0.05\), \(w_0=0.025\), and \(k=1\). The main non-oracle spending sequence is \(\gamma_j\propto j^{-1.6}\). We also use \(\gamma_j=1/T\), which knows the horizon in advance and maximizes the smallest offered cold-start level over \(1,\ldots,T\). We label it horizon-uniform or oracle spending.

### 2.4 Threat model

The defender correctly implements the detector, calibration, grouping, aggregation, and controller. The adversary seeks to suppress or delay the alert on its own activity and, secondarily, to silence the controller for later hypotheses. It controls traffic from compromised or attacker-operated hosts. Because the episode key is \((\text{SrcIP},\text{DstIP},\text{bucket})\), ordinary connections to the host pair already involved in the attack enter the same hypothesis. The attack does not require modifying stored scores, compromising the SOC, poisoning detector training, or perturbing the original malicious flows.

Constructing a padding stream can be black-box: the attacker needs only a common service and a traffic volume. Computing the exact minimum padding size uses the realized evidence sum and controller state and is therefore an oracle lower bound. We keep these two capabilities distinct throughout. For the state attack, we additionally report white-box and grey-box sizing, because the attack acts on controller parameters rather than on detector features.

Groups closing in the same bucket require an order. Our main results use a deterministic hash of the group's own metadata key, with collisions broken by the key. This removes first-flow timing as a lever and ensures that appending flows to one existing group moves no other hypothesis. The originally shipped first-flow order is retained in the appendix as an optimistic detection upper bound on LSPR23; it should not be interpreted as a security mechanism or as a result that automatically transfers to other datasets.

### 2.5 Data and chronological protocol

LSPR23 contains 16,353,511 network flows from the Locked Shields live-fire cyber-defense exercise [24], including 1,644,599 flows labelled malicious. We sort the stream by timestamp and use chronological training, benign calibration, and deployment blocks, with no random mixing across time. Five deployment positions provide quasi-independent views of the same exercise, not five independent datasets. Two detector seeds change the scores while leaving the calibration size, number of hypotheses, and feasibility quantities fixed.

The detector is HistGradientBoosting over protocol and 32 flow timing and volume features. Detector novelty is not a contribution. A second, host-conditioned detector adds six strictly causal host-context features. AIT-LDSv2.0 [22] supplies an external benign-inclusive transfer test in which attacked hosts also receive real ordinary traffic. Complete features, preprocessing, procedure definitions, test matrices, and implementation checks are in Appendices B--D.

The primary window begins at position 0.55 and the replication window at 0.62; both were fixed before the validity diagnostic. At \(k=1\), only 0--3 benign deployment flows reach the calibration tail at each of four non-stress windows, so the diagnostic is too weak to establish validity. At position 0.85, 46 benign flows fire, approximately 50.9 times the nominal rate, clearly refuting marginal e-validity. We use 0.85 only where a result is algebraic or a mechanism/cost measurement that does not require valid evidence. Appendix H contains the complete marginal and metadata-stratified diagnostics.

#TODO_TABLE_EXPERIMENT_SCOPE

A very small table is optional here. Columns: result; primary/replication; stress window; AIT; depends on Assumption 1? Rows: feasibility; observed FDR; symmetric impossibility; padding cost; transfer; state manipulation. This can replace several repeated caveats later.

## 3. When can an online guarantee produce any alert?

### 3.1 Evidence feasibility and an absorbing state

Equation (5) and the ceiling (2) give a necessary condition for a rejection at step \(t\):

\[
\alpha_t\ge\frac{1}{M}.
\tag{6}
\]

We call a step **evidence-feasible** when (6) holds. A procedure is **cold-start feasible through \(T\)** when a rejection remains possible at every step \(t\le T\) along a rejection-free prefix. A rejection-free state is **absorbing** when, once (6) fails, no future evidence sequence can restore feasibility without a restart or a prior rejection.

The distinction matters. Low observed recall can result from a weak detector, a rare attack, or an unfortunate order. Infeasibility is stronger: the procedure would reject nothing even if the current hypothesis received the maximum admissible evidence.

**Theorem 1 (finite discovery horizon).** Let the evidence be bounded above by \(M<\infty\), and let the controller run without restart.

1. **Multiplicative family.** Suppose
   \[
   \alpha_t=\alpha\gamma_t g(H_{t-1}),\qquad
   g(H_{t-1})\le c(R_{t-1}+1)^d,
   \]
   where \(R_{t-1}\) is the rejection count. If \(\gamma_t t^d\to0\), only finitely many steps can be feasible on a rejection-free run. If \(\gamma_t t^d\) is eventually non-increasing, there is a final feasible step and the subsequent infeasible state is absorbing.

2. **Lag-sum family.** Suppose
   \[
   \alpha_t=w_0\gamma_t+\sum_j a_j\gamma_{t-\tau_j},
   \qquad 0\le a_j\le\alpha,
   \]
   over prior rejection times \(\tau_j\), with \(\sum_t\gamma_t<\infty\). After a rejection-free gap of length \(\Delta\),
   \[
   \alpha_t\le(w_0+\alpha)\sum_{r\ge\Delta}\gamma_r.
   \]
   The tail sum tends to zero, so the procedure reaches a finite absorbing infeasible state.

The multiplicative case covers LOND, e-LOND, and the equivalent e-LORD parameterization for the spending sequences considered here. The lag-sum case covers LORD++. The proof uses only \(R_{t-1}\le t-1\) in the first case and the summability of distinct rejection lags in the second; complete proofs are in Appendix A. The theorem is deliberately scoped. It does not say that every online FDR procedure dies, and a controller whose history term grows sufficiently quickly can fall outside its conditions.

### 3.2 Exact calibration-horizon exchange rate

Before the first rejection, the procedures above offer only their cold-start budget. Write \(c_0\) for the coefficient multiplying the spending weight: \(c_0=w_0\) for LORD++ and \(c_0=\alpha\) for LOND/e-LOND. Feasibility at step \(t\) requires

\[
c_0\gamma_t\ge\frac{k}{|\mathcal C|+1}.
\tag{7}
\]

Among all nonnegative spending sequences with total mass at most one, \(\gamma_t=1/T\) maximizes \(\min_{t\le T}\gamma_t\). This gives the best possible cold-start horizon within this budget class.

**Corollary 1 (horizon-uniform feasibility).** Cold-start feasibility through \(T\) requires

\[
|\mathcal C|\ge \frac{kT}{c_0}-1.
\tag{8}
\]

At \(k=1\) and \(\alpha=0.05\), LOND/e-LOND require approximately 20 calibration units per tested hypothesis; LORD++ with \(w_0=0.025\) requires 40. This count ratio is independent of the dataset. Translating it into hours or days is dataset-specific because calibration and deployment generate units at different rates.

The consequence at security scale is immediate. If every flow is tested over the LSPR23-scale horizon, (8) requires approximately \(3.3\times10^8\) calibration flows for LOND/e-LOND and \(6.5\times10^8\) for LORD++, while the chronological windows supply 1.8--2.4 million. Horizon-uniform spending is already the cheapest way to preserve every cold-start step. With \(\gamma_j\propto j^{-1.6}\), keeping the full flow horizon feasible would require approximately \(3.2\times10^{13}\) calibration flows.

#TODO_FIGURE_FEASIBILITY

Reuse current Fig. 2. The caption should state only: (i) required calibration is linear in \(T\); (ii) horizon-uniform spending is the best cold-start allocation; (iii) the available corpus is orders of magnitude too small at flow granularity; and (iv) online e-BH escapes absorption but still needs evidence mass proportional to the desired number of simultaneous discoveries.

### 3.3 Feasibility is not detection power

The bound is necessary, not sufficient. Grouping the deployment into two-hour host-pair episodes reduces \(T\) to 31,568--57,368, making the horizon-uniform bound numerically feasible in our windows. Yet the horizon-free sequence still concentrates useful level in a short prefix: only the first 748--902 hypotheses can reject before any discovery, 1.6--2.6% of the stream. Whether a malicious high-evidence episode lands in that prefix becomes decisive.

The separation appears directly in the experiments. At position 0.70, both detector seeds have the same \(|\mathcal C|\), \(T\), and horizon-uniform feasibility margin \(+0.536\), but under first-flow order one seed yields 30 detections and the other yields none; under the canonical order both yield none. A host-conditioned detector raises AUROC from 0.916 to 0.954 at the primary window but reduces e-LOND detections under the paired first-flow analysis from 18 to two. An Isolation Forest has the same feasibility margin but no attack flow above the calibration maximum. Detector ranking quality can affect power, but it cannot change the structural margin in (8).

Low prevalence compounds the cold-start problem. The exercise contains far more malicious activity than a typical operational stream, yet thinning malicious episodes to \(10^{-4}\) while keeping \(T\) and every survivor's index fixed reduces the probability of any e-LOND rejection to 0--40% across the evaluated cells, mostly below 10%. The complete sensitivity analysis is in Appendix I; it is not needed for the theorem, but it shows why a short discovery prefix is especially problematic in the regime that motivates FDR control.

### 3.4 What escapes the horizon, and what it costs

The procedures we study exhibit two genuine escape mechanisms.

**Selective index advancement.** ADDIS advances its spending index only on hypotheses whose p-values are selected but not candidates. With the two-point evidence at \(k=1\), no observed episode lies in the relevant interval, so the index can stop advancing and the level can remain high. This is an escape from the absorbing horizon, but on the real stream it coincides with a violation of ADDIS's uniform-conservativeness premise. Section 6 shows that conditioning the index on observed evidence also makes the state attacker-controllable.

**History-wide reconsideration.** Online e-BH uses a step-up fixed point over the entire observed history. A rejection-free prefix is therefore not absorbing: a later observation can cause an earlier hypothesis to be reconsidered. Decision-deadline procedures interpolate between immediate e-LOND-style decisions and indefinite online-e-BH-style reconsideration [19, 20]. The price is latency, not improved evidence. In our canonical-order matrix, bucket-close deferral adds one detection in only the known-invalid stress window and none in the primary or replication windows.

Two other interventions remove a premise rather than escaping within it. Randomized conformal smoothing removes the deterministic floor but adds detections that are unstable across randomization and merging choices. Periodic restart renews the controller's cold-start budget and recovers substantial power: at the primary window, two-hour budget reset raises mean recall from 0.065 to 0.345, and one-hour reset to 0.406. Resetting \(q\) each epoch does not preserve deployment-wide FDR; pre-allocating epoch budgets with \(\sum_i q_i\le q\) does, but yields lower recall (0.195 for the two-hour configuration). Thus restart presents a transparent choice between per-epoch power and a deployment-wide guarantee.

Recent closure and compound-e improvements over e-LOND do not remove the initial barrier on these sparse-evidence streams. Before the first rejection, donation can increase the cold-start coefficient only by a constant factor, and the closure's zero-evidence subset advances almost as fast as elapsed time. Their exact bounds and the full procedure matrix are in Appendix A and Appendix E.

#TODO_TABLE_PROCEDURE_TAXONOMY

Compress current Table III and Table XIII. Suggested rows: e-LOND/LOND; LORD++; SAFFRON; ADDIS; online e-BH; decision-deadline/e-TOAD; donation e-LOND; closed e-LOND. Suggested columns: evidence type; spending/index mechanism; covered by Theorem 1; can a rejection-free prefix become absorbing?; what buys the escape; measured price. Do not include full rejection counts in this table.

## 4. Aggregation buys feasibility by spending resolution

Corollary 1 turns the alerting unit into a design variable. If the defender replaces flow-level hypotheses with grouped episodes, the deployment horizon falls from \(T_{\mathrm{flow}}\) to \(T_{\mathrm{group}}\). The required calibration size falls in the same proportion:

\[
|\mathcal C|_{\min}=\frac{kT_{\mathrm{group}}}{c_0}-1.
\tag{9}
\]

Grouping is therefore not merely a heuristic that happens to improve power. For the covered procedures under uninterrupted control, it buys cold-start feasibility on an exact exchange rate. We evaluate five operational grouping families--source-destination pair, source host, destination host, /24 subnet pair, and source-service--over bucket widths from five minutes to one day and over the whole deployment. Every family exhibits the predicted linear relationship between hypothesis count and required calibration.

The important cost is semantic resolution. Ordinary episode recall is not comparable across bucket widths because the definition and number of positives change. Malicious-flow coverage is also unstable because a few host pairs carry most of the malicious traffic. We therefore fix an atomic evaluation reference: each malicious source-destination episode in a five-minute bucket is one atom, regardless of the alerting bucket used by the controller. For each issued alert, **alert blur** is the number of distinct atomic malicious units represented by that alert.

At the primary window, a five-minute alert has blur 1.0. The mean blur rises to 3.6 at 30 minutes, 7.2 at one hour, 16.1 at two hours, 25.3 at six hours, and 38.5 at one day. The fixed atomic coverage can rise at the same time, because a coarse alert touches more of the attack, but it no longer localizes which fine-grained activity is responsible. The stress window shows the same direction, with blur increasing from 1.0 to 20.4. An external red-team task record also rises in the same direction, but permutation and timeline-rotation tests show that it is too coarse to independently validate alert-level correspondence; we therefore use it only as a robustness check in Appendix H.

This tradeoff explains why the next result is not an unrelated adversarial add-on. Aggregation is the direct response to the feasibility boundary, and the fields that determine membership--endpoints, services, and time--are partly chosen by the attacker. The defender buys a rejectable hypothesis by making its composition attacker-facing.

#TODO_FIGURE_GRANULARITY

Reuse the top two panels of current Fig. 3: feasibility margin and alert blur versus bucket width. Drop the malicious-flow-coverage panel from the main paper. Put the fixed atomic definition directly in the caption and show the zero-margin line. If space permits, annotate the two-hour headline configuration.

## 5. Aggregation is a padding attack surface

### 5.1 Appending ordinary flows dilutes group evidence

Consider a group with evidence inputs \(x=(e_1,\ldots,e_m)\) and group rule \(F_m(x)\). Under the two-point construction, an ordinary flow that does not reach the calibration tail contributes exactly zero. An attacker who adds \(r\) such flows to the same source-destination bucket changes the controller input to

\[
F_{m+r}(e_1,\ldots,e_m,\underbrace{0,\ldots,0}_{r}).
\tag{10}
\]

The original malicious flows and their detector scores are unchanged. The adversary attacks the statistical composition layer, not the classifier.

A natural hope is that a different symmetric aggregation rule could retain validity while ignoring this padding. The following result rules that out for the entire symmetric e-merging class.

**Definition 1 (padding robustness).** A family of e-merging functions \(\{F_N\}_{N\ge1}\) is \(\tau\)-padding-robust if, whenever a finite input \(x\) satisfies \(F_m(x)\ge\tau\), appending any number of zeros preserves \(F_{m+r}(x,0^r)\ge\tau\). The family **attains** \(\tau\) if some finite input reaches it. Attainment excludes vacuous rules that never fire.

**Theorem 2 (symmetric padding impossibility).** For any \(\tau>1\), no symmetric e-merging family that attains \(\tau\) is \(\tau\)-padding-robust. More precisely, for every symmetric e-merging family and finite nonnegative input \(x\),

\[
F_{m+r}(x,0^r)<\tau
\quad\text{whenever}\quad
r>\frac{\sum_i x_i}{\tau}-m.
\tag{11}
\]

The proof uses the essential domination of symmetric e-merging functions by the arithmetic mean [11]. On any finite input, a symmetric e-merging function is bounded by \(\max\{1,\operatorname{mean}(x)\}\). Appending zeros drives the mean below \(\tau\) at the threshold in (11). The arithmetic mean meets the bound exactly, so the quantitative result is tight. Appendix A gives the full proof and an independent negatively dependent construction.

Every online rejection threshold in our setting has \(\tau=1/\alpha_t>1\), so the theorem applies whenever the symmetric rule is capable of issuing an alert. It is not a peculiarity of the arithmetic mean or of LSPR23.

### 5.2 Exact cost for the mean

For the deployed mean rule, let \(S=\sum_{i\in G}e_i\) and \(m=|G|\). The padded evidence is \(S/(m+r)\). If the unpadded group is rejected at level \(\alpha_t\), the minimum number of zero-evidence additions that makes it fail is

\[
r^\star=\lfloor S\alpha_t\rfloor-m+1.
\tag{12}
\]

This expression exposes an important capability distinction. The **construction** of a plausible pad can be black-box: send ordinary traffic on a common service to the host already under attack, in the same bucket. The **minimum sizing** in (12) is not black-box because it uses \(S\), the live level \(\alpha_t\), and the unperturbed trajectory. Reported \(r^\star\) values are therefore oracle lower bounds on the attacker's required volume, not turnkey black-box budgets.

The canonical primary window yields only three e-LOND detections, and their individual costs are 23, 24, and 33 added flows. At the replication window, 11 canonical detections have a median cost of six flows. At the known-invalid stress window, the canonical median is 116 over 34 detections. The originally shipped first-flow order detects more episodes and detects them deeper in the spending sequence, so its costs are larger--118 at the primary window, 72 at replication, and 5,202 at the stress window--but every target remains suppressible. We keep that order-specific matrix in the appendix rather than forcing the reader to compare two narratives throughout the paper.

### 5.3 The pad can be ordinary, black-box traffic

We construct a weak-attacker pool using only network-observable frequency before deployment: the most common protocol-port pair in the training prefix. No attack labels, detector outputs, calibration scores, or deployment traffic are used to choose it. On the primary and stress windows, none of 20,000 sampled pool flows reaches the conformal tail; the one-sided 95% upper bound on the firing probability is \(1.5\times10^{-4}\). Injecting these real flows into each detected episode suppresses it at exactly the closed-form threshold in (12): 3/3 and 34/34 canonical-order detections, and 18/18 and 72/72 first-flow detections.

The result is insensitive to most choices of plausible ordinary traffic. Generic benign, attacker-origin, protocol-matched, and the black-box pool have nearly identical median costs because the controller threshold is much larger than their mean evidence. Service-matched padding is 1.4--2.0 times more expensive, but it does not change the conclusion. Choosing the modal service from the deployment window is not a valid black-box rule: at the stress window it selects the attacker's own flood, which scores highly and does not dilute. This distinction is retained in Appendix F so that the main claim rests on the pre-deployment black-box construction.

Can the adversary place these flows in the attacked group? Under the headline key, it sends ordinary traffic between the source and destination already involved in its activity before the two-hour bucket closes. The flow-only detector does not use endpoint identity, although response-dependent timing features mean transfer to an actual victim must still be measured. The controlled replay above performs that measurement rather than assuming it.

#TODO_TABLE_CORE_EMPIRICS

Build a compact claim-evidence table rather than reproducing current Table I. Suggested rows:

- Primary 0.55: \(T=57{,}368\), \(|\mathcal C|=2{,}448{,}993\), oracle margin +0.067, 3 canonical detections, padding costs 23/24/33, replay 3/3.
- Replication 0.62: \(T=49{,}267\), \(|\mathcal C|=2{,}449{,}031\), oracle margin +0.243, 11 canonical detections, median padding cost 6.
- Stress 0.85: mark "invalid evidence; cost/mechanism only", 34 canonical detections, median cost 116, replay 34/34.
- AIT flow-only transfer: 84/85 true detections suppressible across eight organizations.
- AIT host-conditioned end-to-end: 9/9 evaluated detections suppressible across shaw and wilson.

A footnote should say that the canonical order is own-key-only and that all per-alert costs are oracle lower bounds. Put the full five-window, two-seed, two-order matrix in the appendix.

### 5.4 Transfer beyond the flow-only detector

A detector could potentially defend by conditioning each flow on host history, making repetitive padding anomalous. We test that boundary in two stages.

First, on LSPR23 we add six strictly causal host-context features: prior connection counts, distinct-peer counts, and failed-connection fractions. The resulting detector has higher AUROC at both headline windows, yet fewer e-LOND detections, reinforcing the distinction between ranking quality and feasibility. We replay the append causally, updating the host context as each pad arrives. The black-box pads continue to contribute zero evidence, and every evaluated target remains suppressible at the flow-level closed-form scale. LSPR23 cannot settle the full benign-inclusive question, however, because host pairs containing attack traffic are almost entirely malicious and provide no realistic ordinary-to-victim pool.

Second, AIT-LDSv2.0 provides eight organizations in which attacked hosts also serve real benign traffic. For each held-out organization, we train on the other seven, calibrate on in-organization benign flows preceding the first attack, run the same two-hour host-pair/e-LOND pipeline, and replay real benign-to-victim traffic. Across the flow-only folds, 84 of 85 true detections are suppressible, with per-draw success from 0.80 to 1.00. We then recompute host context throughout accumulation for the two organizations with evaluated host-conditioned detections; all nine are suppressed. On shaw, ordinary victim traffic initially appears to fire frequently in its own context, but its firing rate falls below 0.5% when scored in the attacked pair's evolving context, and all three targets suppress.

This transfer result has a precise scope. It covers the six host features and the causal accumulation model we implement, including one already-active attacker-victim pair. It does not show that every host-aware detector is vulnerable, does not cover padding from many new peers, and does not evaluate a substantially higher-volume flood regime. Its role is to reject the simple explanation that the LSPR23 result exists only because the detector lacks host context.

### 5.5 Why the obvious aggregation fixes are not free

A pre-committed cap of the form \(\sum_i e_i/n_0\) is padding-invariant while \(m\le n_0\), but it is not a valid all-arity e-merging family beyond the cap and is strictly less powerful than the mean below it. In the measured cap sweep, conservative caps that preserve the intended validity domain eliminate the headline detections. The cap escapes Theorem 2 by leaving its class, not by providing a free symmetric repair.

Abandoning symmetry also moves rather than removes the vulnerability. Let a pre-committed position-weighted rule be \(F(e)=\sum_i w_i e_i\), with \(w_i\ge0\) and \(\sum_iw_i\le1\). It is invariant to appended flows because later positions receive pre-specified weights. However, a lone firing flow can occupy at most \(\alpha_tM\) positions whose weight is large enough to trigger an alert, and the summable weight tail implies a finite number of leading zero-evidence flows after which detection is impossible. In the primary-window sweep, weighting schemes that retain the mean's recall are defeated by one to eight leading flows, compared with 111 appended flows for the mean on the same detected episodes. Increasing the front-loading cost to 81--164 sacrifices about 58% of recall. Appendix A states the reach and front-load theorems; Appendix F gives the complete sweep.

A group maximum is invariant to appended low-evidence flows, but calibrating the group directly reduces the calibration set from millions of flows to 37,000--57,000 groups while leaving the deployment horizon essentially unchanged. The evidence ceiling falls by a factor of 40--49, the feasibility margin becomes approximately \(-0.97\), and the primary and replication windows issue no alert. Moreover, creating new hypotheses ahead of a target can still move it outside the shortened cold-start window. These alternatives reinforce the compositional point: robustness, validity, feasibility, and semantic resolution cannot be optimized one module at a time.

## 6. Evidence-conditioned state is a second attack surface

The preceding attack manipulates the composition of one hypothesis. A distinct surface appears when a controller escapes Theorem 1 by conditioning its spending index on observed evidence.

ADDIS advances its index on selected non-candidates, whose p-values lie in \((\lambda,\tau]\), and does not reject those hypotheses. With \(\gamma_j=(j+1)^{-1.6}/\zeta(1.6)\), an attacker can prepend groups in that interval, advance the spending index without spending discoveries, and force the future level below the conformal floor. Let \(W=w_0\) before the first rejection and \(W=\alpha R\) after \(R\) rejections. The required number of precursor hypotheses is the smallest \(D\) satisfying

\[
D+1>
\left[
\frac{(\tau-\lambda)W(|\mathcal C|+1)}{k\,\zeta(1.6)}
\right]^{1/1.6}.
\tag{13}
\]

Each precursor can be constructed as a group with one firing flow and enough zero-evidence flows to place its p-value in \((\lambda,\tau]\). The smallest group size is

\[
m^\star=\left\lfloor\frac{\lambda(|\mathcal C|+1)}{k}\right\rfloor+1.
\tag{14}
\]

At the 0.85 real-stream stress window, 202 precursors leave all 152 ADDIS rejections intact and 203 eliminate all of them, exactly matching (13). Because this window's evidence is not a valid e-value and the same two-point structure also violates the conservativeness condition ADDIS needs, this experiment demonstrates the controller mechanism and prices it; it is not an FDR-valid real-data result.

To isolate the mechanism, we generate streams with genuinely conservative independent null p-values and strong non-null targets. ADDIS's empirical all-null FDR is 0.010 and its mixed-stream mean FDP is 0.047 at recall 1.00, both below \(q=0.05\). We then prepend alternative--not null--precursors in \((\lambda,\tau]\), so the assumptions on true nulls remain unchanged on the attacked stream. The attack silences all 120 targets at a median of 140 precursors over 300 streams, with a range of 140--255. The guarantee can therefore remain valid while the security objective is defeated: controlling the fraction of false discoveries does not require the procedure to make any discovery.

The real-stream cost is conspicuous. At \(|\mathcal C|=1{,}813{,}113\), each precursor needs 453,279 flows, and 203 precursors require 92,015,637 flows--approximately 36.1 GB or 33.4 Mbit/s over the deployment span, 37.5 times the window's flow count. This is a structural controllability result, not a claim of low-footprint evasion. By contrast, suppressing one canonical e-LOND alert at the same window has median cost 116 flows.

The result is also mechanism-specific. Online e-BH escapes the finite horizon by reconsidering a fixed point over the entire history rather than by advancing a spending index, so this attack has no analogous state variable to move. We do not claim that online e-BH is immune to every manipulation; only that Theorem 3 does not cover it.

#TODO_FIGURE_ATTACKS

Recommended main figure: current Fig. 4 panel A (padding cost curves) plus panel C (guarantee-valid synthetic state attack). Move panel B, the invalid real-stream ADDIS demonstration, to the appendix or give it a grey background labelled "stress window: mechanism only." The caption must distinguish black-box pad construction from oracle-minimal sizing.

## 7. Implications, validity, and limitations

### 7.1 Design implications

The results suggest a different order for designing statistical alerting systems.

**Size the evidence against the horizon before selecting a controller.** The first calculation should be (8), not an AUROC comparison. If the calibration corpus cannot support the intended number of hypotheses, tuning the detector or substituting another procedure in the same covered family cannot prevent structural silence.

**Choose the security unit before the testing rule.** Grouping determines both the hypothesis horizon and what an alert means. A deployment report should state the calibration-to-hypothesis ratio and a fixed-denominator resolution measure such as alert blur. Episode recall alone can make a coarser unit look better or worse simply because the denominator changed.

**State the temporal scope of the guarantee.** Restart is an effective engineering response, but budget reset provides a per-epoch guarantee, not automatically a deployment-wide one. Pre-allocation can preserve deployment-wide FDR at a power cost. A SOC should be told which promise it is receiving.

**Treat every data-conditioned module as attacker-facing.** If an adversary can choose fields that determine group membership, the aggregation rule is part of the threat model. If observed evidence advances a future spending index, that state is part of the threat model. Validity under stochastic assumptions does not imply resistance to deliberately chosen non-null inputs.

**Canonicalize order, but do not confuse canonicalization with defense.** Ordering groups by their own metadata rather than first-flow arrival prevents a pad from shifting unrelated hypotheses and makes the validity analysis local. A public hash over attacker-selectable keys can still be ground, and a secret keyed hash only changes the attacker's cost when sufficiently many endpoint pairs are available. Full order and insertion analyses are in Appendix F.

### 7.2 What depends on the group-validity premise

The paper makes three logically separate classes of claim.

1. **Feasibility.** Theorem 1 and Corollary 1 compare an upper bound on evidence with the controller's offered level. They hold whether the evidence is well calibrated, shifted, or invalid.
2. **Aggregation impossibility.** Theorem 2 is a statement about symmetric e-merging functions. It does not assume that LSPR23 produces valid e-values.
3. **FDR interpretation on data.** Lemma 1 and any statement that an empirical e-LOND run carries its nominal FDR guarantee require Assumption 1. The primary and replication diagnostics do not refute the premise, but the small number of benign tail events means they do not support it either. The 0.85 diagnostic clearly refutes marginal validity, so no guarantee is attached there.

A metadata-stratified diagnostic finds deeper-tail departures at every window, including arity strata, but a departure at rank 1000 does not imply failure at the rank-one threshold used by the pipeline. We therefore leave the guarantee conditional rather than treating non-rejection as validation. Directly calibrating grouped hypotheses would replace Assumption 1 with group exchangeability, but the resulting 40--49-fold reduction in calibration units makes the primary and replication streams infeasible. This is not a justification for assuming validity; it is the measured cost of the most direct construction that would make group validity easier to state.

### 7.3 Limitations

Our empirical analysis begins with one live-fire exercise. The five chronological windows are distinct deployments within that exercise, not independent datasets. LSPR23 lacks a reliable flow-to-campaign identifier, so our operational units are episodes rather than incidents or campaigns. The fixed five-minute atom is a stable evaluation denominator, not externally validated incident truth. The red-team task record agrees with the direction of the resolution result but is too sparse and coarse to establish alert-level correspondence.

The padding attack transfers to a second dataset and to the host-conditioned configurations we test, but its full scope is narrower than "host-aware detection cannot help." We model one active attacker-victim pair, do not vary features based on newly appearing peers, and do not test every possible stateful or graph-based detector. The transfer result establishes that simple causal host conditioning is not by itself a defense in these experiments.

Per-alert padding values are oracle lower bounds because exact sizing uses the realized group evidence and live controller level. The black-box contribution is the construction and measured low firing rate of ordinary service traffic, not knowledge of the minimal \(r^\star\). A practical attacker without state information would need to over-provision.

The state attack has a dataset-specific absolute volume even though its closed form is general for the stated ADDIS configuration. Its real-stream demonstration is at a known-invalid window and its operational cost is conspicuous. The guarantee-valid synthetic result establishes the mechanism, not the prevalence of such attacks in production. We do not attack online e-BH's history-wide fixed point.

Finally, C1 is scoped to finite-resolution evidence, uninterrupted operation, and the two controller families in Theorem 1, together with separately analyzed sparse-evidence closure variants. Smoothing, restarting, delayed decisions, different evidence constructions, and controllers with faster-growing history terms can change the conclusion, but each changes a premise or pays a distinct operational cost. We do not claim that online FDR control is generally unusable.

## 8. Related work

**Online FDR and finite conformal resolution.** LOND, LORD, SAFFRON, ADDIS, e-LOND, online e-BH, and e-GAI establish online error guarantees under different evidence and dependence assumptions [3--8, 16, 18]. Alpha-death and the loss of power from small testing levels are well known [5, 15]. Huo et al. [13] specifically observe poor online-testing behavior from the conformal p-value floor and respond with a local-FDR selection rule. Hennhofer and Preisach [14] study conformal resolution collapse and smoothing in a low-data batch setting. Our contribution is not the observation that a finite calibration set limits resolution. It is the structural characterization of a finite absorbing horizon for two online-controller families, the exact calibration-horizon exchange rate, and the classification and pricing of escape mechanisms. Kronert et al. [17] derive a related calibration expression for exactness of a windowed anomaly procedure; our bound marks the point below which an uninterrupted controller cannot reject at all.

**Trustworthy intrusion detection and composed statistical pipelines.** Temporal evaluation methodology in TESSERACT [29] and conformal drift systems such as Transcend(ent) [30, 31] motivate our chronological protocol. Prior anomaly-detection pipelines combine conformal evidence with online or sequential false-discovery control [32--36]. That literature establishes conditions under which the statistical modules are valid. We study a complementary systems question: whether bounded evidence can reach the controller's levels at the intended deployment horizon, what grouping does to alert semantics, and whether the resulting composition remains secure when traffic is adversarially generated.

**Aggregation and adversarial testing.** E-merging theory characterizes symmetric and asymmetric ways to combine e-values [11, 23]. Existing adversarial-testing work considers manipulated scores, perturbed p-values, or Byzantine reports [40--43]. Our adversary need not change a detector score or corrupt a reported statistic. It changes which legitimate observations belong to its own hypothesis or supplies non-null observations that advance a public adaptive state. Theorem 2 turns the first attack from an implementation example into a class-wide impossibility, while the ADDIS result identifies the second as a consequence of one horizon-escape mechanism.

**Feedback and batching.** Batching can recover power and stabilize online decisions [28], but batch procedures often need within-batch dependence assumptions that co-located network flows do not satisfy. Decision deadlines provide an arbitrary-dependence-compatible continuum between immediate and deferred decisions [19, 20], while feedback-aware online testing can incorporate revealed labels with finite-sample control [25, 39]. Our appendix prices simpler operational threshold controllers under analyst delay; those baselines are not a core contribution and should not be confused with feedback-aware FDR procedures.

## 9. Conclusion

A nominal online error guarantee is useful only while the available evidence can cross the controller's threshold. With finite-resolution conformal evidence and uninterrupted budget spending, that window can be finite and absorbing, imposing a calibration requirement linear in the number of tested hypotheses. Aggregation buys feasibility at exactly that rate, but spends semantic resolution and exposes group composition to an attacker. Symmetric e-merging cannot be both capable of firing and invariant to zero-evidence padding, and ordinary traffic suppresses the resulting alerts at low measured cost in our primary and replication settings. An escape mechanism that conditions spending on observed evidence can expose controller state as well. Statistical trust layers for security ML must therefore be evaluated as composed systems: for validity, feasibility, alert semantics, and adversarial robustness together.

---

# Part III. Concrete restructuring map

## Proposed section mapping from the current draft

| New section | Draw from current material | Main editing action |
|---|---|---|
| 1. Introduction | Current Sec. I plus one paragraph from Sec. X | Retain only the causal chain and two contributions; remove result-by-result caveats |
| 2. Model and protocol | Current Secs. II, III, and VII | Merge into one compact section; move proofs, implementation, and full parameter definitions to appendix |
| 3. Finite horizon | Current Sec. IV | Preserve theorem statements and exact bound; compress procedure-specific branches and newest-procedure details |
| 4. Granularity bridge | Current Sec. V | Keep feasibility and blur; move flow coverage and red-team audit details to appendix |
| 5. Padding attack | Current Sec. VI-A--E and transfer subsection | Make Theorem 10 plus black-box replay the empirical/theoretical centerpiece |
| 6. State attack | Current Sec. VI-F--G | Reduce to one short theorem/mechanism section; foreground synthetic guarantee-valid result, not invalid real window |
| 7. Implications/limits | Current Secs. IX-A--D and X | Centralize premise dependencies and limitations; move experiment details out |
| 8. Related work | Current Sec. XI | Keep only nearest work and explicit differentiation |
| 9. Conclusion | Current Sec. XII | One paragraph |

## Current figure decisions

| Current asset | Decision | New marker |
|---|---|---|
| Fig. 1 pipeline | Keep and redraw | `#TODO_FIGURE_PIPELINE` |
| Fig. 2 calibration versus horizon | Keep | `#TODO_FIGURE_FEASIBILITY` |
| Fig. 3 granularity | Keep top and middle panels only | `#TODO_FIGURE_GRANULARITY` |
| Fig. 4 attacks | Keep padding and synthetic panels; demote/grey invalid-real panel | `#TODO_FIGURE_ATTACKS` |

## Current table decisions

| Current tables | Decision in the rewrite |
|---|---|
| I | Replace with a compact claim-evidence table using only primary, replication, stress label, and transfer |
| II | Convert to prose definitions or an appendix glossary |
| III | Compress with XIII into the main procedure taxonomy |
| IV--V | Appendix: full cross-window and cross-procedure matrices |
| VI--IX | Appendix, except alert blur visualized in the main granularity figure |
| X | Appendix: order sensitivity; main text gives only the canonical-order policy and one contrast |
| XI--XIII | Appendix; retain one paragraph on smoothing, restart, and escape taxonomy |
| XIV, XVI, XXI | Merge the essential primary/replication/replay facts into the new core empirical table |
| XV, XVII | Appendix: asymmetric weights and caps |
| XVIII--XX | Appendix details; main text keeps the state threshold, valid synthetic result, and operational scale |
| XXII--XXIV | Main text gets the transfer conclusion; complete detector/organization matrices stay in appendix |
| XXV--XXVII | Appendix or online supplement; not part of the central paper story |
| XXVIII--XXX | Appendix; main text states the validity conclusion and direct-group-calibration cost |
| XXXI--XXXVI | Appendix/online supplement; use only individual facts needed for limitations |

## Appendix organization that mirrors reviewer questions

Do not preserve the current appendix simply as a sequence of experiments. Reorganize it by the questions a reviewer will ask.

### Appendix A. Proofs and exact scope

- Lemma 1 group validity.
- Theorem 1 multiplicative and lag-sum proofs.
- Horizon-uniform optimality.
- Closure/donation bounds.
- Theorem 2 full proof and tightness.
- Position-weight reach/front-load theorems.
- ADDIS state-budget derivation.
- Restart FDR composition.

### Appendix B. Procedures and reproducibility

- exact procedure definitions and parameter values;
- unit-test identities and implementation checks;
- chronological split and feature definitions;
- artifact instructions.

### Appendix C. Full feasibility evidence

- five-window/two-seed matrices;
- all procedures and both spending sequences;
- low-prevalence sensitivity;
- smoothing, restart, closure/donation, and decision deadlines;
- feasibility-versus-detection examples.

### Appendix D. Granularity and ordering

- all grouping families and bucket widths;
- fixed atomic coverage and flow coverage;
- red-team external denominator;
- order ensemble, public hash, keyed hash, and configuration transfer.

### Appendix E. Attack measurements and mitigations

- all padding pools and per-window costs;
- controlled replay details;
- cap and position-weight sweeps;
- host-conditioned detector;
- AIT organization matrices;
- insertion and group-MAX alternatives;
- ADDIS real and synthetic experiments;
- operational-unit conversions.

### Appendix F. Validity and data quality

- marginal benign-tail diagnostic;
- metadata-stratified diagnostic;
- group-level calibration;
- contamination;
- alert audit;
- Bates conditional adjustment.

### Appendix G. Secondary operational baselines

- matched operating-point frontier;
- analyst-feedback delay experiments;
- other negative results that are useful for completeness but not for the central claim.

## Style rules for the Overleaf rewrite

1. Use **one name per concept**. Prefer "finite discovery horizon," "alert blur," "Surface A: padding," and "Surface B: state manipulation" throughout.
2. Put the canonical-order definition once in Section 2. Use a symbol or short footnote for first-flow appendix results instead of repeating a paragraph in every caption.
3. Put the stress-window warning once in the experiment-scope table and once when it is first used. Do not repeat it in every main-text sentence.
4. Every main-body result paragraph should follow the same pattern: claim -> why it follows -> one decisive number -> scope.
5. Do not report all five windows in prose. Use primary and replication for the main claim, stress only for algebraic/mechanism results, and the full matrix for robustness in the appendix.
6. Use one empirical baseline in the main story: e-LOND under the canonical order. Other procedures belong in the taxonomy or appendix unless they instantiate an escape mechanism.
7. Keep theorem statements in the body but move derivation detail to Appendix A. A reviewer should understand the condition, conclusion, and proof idea without opening the appendix.
8. Keep captions short. The current captions often contain the result, caveat, protocol, and discussion simultaneously; those belong in prose or a shared notation paragraph.
9. Avoid presenting negative experiments as independent contributions. Use them only to close an obvious alternative after a core claim.
10. End every section with the causal handoff to the next one: horizon -> grouping -> exposed aggregation -> exposed state -> system-level design rules.

## Final pre-submission compression checklist

- The abstract contains one theorem-scale result, one bridge, one attack result, and one scope sentence.
- The introduction names exactly two principal contributions and one bridge.
- No main table has more than six rows unless it replaces a figure.
- No main caption exceeds approximately 80 words.
- Primary and replication results are visually dominant; the invalid stress result is visually marked.
- The main body contains enough of each proof to make the theorem credible without the appendix.
- Every guarantee-bearing empirical sentence says, directly or through the scope table, that it is conditional on Assumption 1.
- The paper never equates "not refuted" with "validated."
- The state attack is described as structural and conspicuous, not practical and cheap.
- The padding construction is described as black-box, while exact minimal sizing is described as oracle.
- The transfer result is scoped to the tested host-context features and accumulation model.
- The paper closes on the composed-system lesson, not on the number of experiments completed.
