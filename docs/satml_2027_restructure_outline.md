# Reviewer-Centered Restructuring Plan for *When Online Guarantees Go Silent*

**Source draft:** `SatML_2027 (16).pdf`  
**Constraint:** no additional experiments; improve the paper by selecting, ordering, and explaining the existing results.  
**Editorial objective:** make the paper read as one inevitable argument rather than a catalogue of theorems, procedures, diagnostics, attacks, and sensitivity analyses.

---

## Executive editorial decision

The strongest version of this paper is **not** a paper about two equal attack surfaces, a survey of online-FDR procedures, or an exhaustive audit of every design alternative. It is a paper about one composition-level failure chain:

> **Finite-resolution evidence can make an online statistical alert layer structurally unable to fire. Grouping is the natural way to restore feasibility, but grouping changes the security object and makes it attacker-controllable. For symmetric e-merging, this creates an unavoidable padding vulnerability that is visible in an end-to-end intrusion-detection pipeline and transfers to a second dataset.**

Everything in the main paper should serve that sentence.

The **ADDIS controller-state attack should be demoted to an appendix extension**. It is interesting and worth preserving, but it currently introduces a second mechanism, a second threat model, a stress window with invalid evidence, a synthetic validation, and a conspicuously high real-stream cost. Giving it equal weight to the padding result makes the paper look broader but less convincing. The padding story alone already supports “evasion” in the title and is the cleaner, more general, and better empirically supported security contribution.

The revised paper should leave a reviewer with four durable ideas:

1. **Feasibility precedes power.** A detector cannot compensate for an evidence ceiling that lies below the controller threshold.
2. **The best-case calibration requirement is linear in the number of tested hypotheses.** At flow scale, the required calibration corpus is implausibly large.
3. **Grouping buys feasibility by changing alert semantics.** It reduces the horizon but blurs the security event.
4. **The resulting grouped hypothesis is attacker-controllable.** No alert-capable symmetric e-merger can ignore arbitrary zero-evidence padding, and ordinary traffic suppresses alerts in the evaluated pipelines.

The paper should sound confident because it has a strong theorem-to-system chain. It should be careful through **precise claim boundaries**, not through repeated self-qualification.

---

# 1. What the reviewer should believe after reading the paper

## 1.1 One-sentence thesis

A statistically valid online controller is not automatically an operationally viable or secure alert layer: bounded conformal evidence creates a finite alert horizon; aggregation restores feasibility but necessarily exposes attacker-controlled group composition.

## 1.2 Contribution hierarchy

### Primary contribution 1: a deployment-level feasibility boundary

The paper characterizes when bounded evidence can cross an online controller's threshold at all. The key result is not merely that online levels become small, but that, for the covered arrival-time controller families and spending sequences, the system eventually enters a state in which **no admissible future observation can produce an alert**. The max-min horizon-aware allocation yields the best-case calibration-to-horizon requirement.

### Primary contribution 2: the operational repair creates a security tradeoff

Reducing the number of tested hypotheses through grouping restores feasibility at a known exchange rate. This is not a generic “aggregation helps power” observation: it changes the unit on which the guarantee is made and measurably blurs fine-grained attack activity.

### Primary contribution 3: a class-wide padding impossibility with end-to-end evidence

For any symmetric e-merging family capable of reaching an alert threshold, enough zero-evidence additions drive the merged evidence below that threshold. The arithmetic mean attains the bound, yielding an exact attack cost. The paper then validates the mechanism through real-flow replay, a state-free over-provisioning strategy, a host-conditioned detector, and a benign-inclusive transfer dataset.

### Supporting extension: adaptive controller state can also become attacker-facing

The ADDIS result shows that selective, evidence-conditioned index advancement may expose a second manipulation surface. This is a useful extension, but it should not define the main narrative or receive equal visual and textual weight.

## 1.3 What should no longer appear to be a principal contribution

The following are supporting analyses, not separate headline contributions:

- the catalogue of LOND, LORD++, SAFFRON, ADDIS, e-LOND, e-LORD, e-GAI, online e-BH, donation, closure, deadline, restart, and smoothing variants;
- the complete five-window, two-seed, two-order matrices;
- all five padding-pool variants;
- the low-prevalence sweep;
- the external red-team task-record comparison;
- keyed-hash grinding and order sensitivity;
- calibration contamination;
- matched operating-point baselines;
- analyst-feedback threshold controllers;
- the detailed label audit;
- every negative result for every proposed repair.

These analyses demonstrate care, but presenting them as co-equal evidence makes the central contribution harder to identify.

---

# 2. Why the current draft is difficult to review

## 2.1 It gives too many results equal status

The current first-page framing presents a feasibility theorem, a calibration exchange rate, grouping, blur, a padding impossibility, multiple aggregation fixes, exact costs, replay, transfer, and an ADDIS state attack before the reviewer has formed a simple mental model. A reviewer cannot yet tell which result is the paper's decisive contribution and which results are completeness checks.

The revision should establish a clear hierarchy:

1. structural failure;
2. necessary operational repair;
3. security consequence of that repair;
4. secondary extensions.

## 2.2 The introduction weakens the novelty claim before explaining it

Phrases such as “Neither ingredient of this result is new” and “We claim none of these ingredients” are accurate but rhetorically costly. They invite a reviewer to reduce the contribution to a trivial combination before the paper explains why the composition changes the problem from low power to impossibility.

Prior work should be credited without making the authors argue against themselves. The confident version is:

> Prior work establishes finite conformal resolution and decaying online testing levels separately. We characterize their composition as a deployment-feasibility problem, derive the resulting horizon, and show that the operational repair creates an adversarially controllable hypothesis.

## 2.3 Validity qualifications arrive before the reviewer understands the main result

The current model section introduces a detailed sigma-field, Assumption 1, a lemma, the distinction among marginal and conditional validity, ordering dependencies, and a claim-dependency table before the main feasibility result. This makes the paper appear to rest on an unverified assumption even though the central feasibility and padding theorems do not depend on it.

The revised body should state the validity scope once and positively:

> Interpreting an empirical e-LOND run as FDR-controlled requires marginally valid group e-values under the precommitted grouping rule. The feasibility boundary uses only the evidence ceiling, and the padding impossibility uses only the e-merging class; neither relies on this premise.

The full conditional statement, sigma-field construction, proof, and diagnostics belong in the appendix.

## 2.4 The paper repeatedly stops to defend itself

Many paragraphs contain a result, an objection, a qualification, an exception, and a second exception in the same place. This is transparent but interrupts momentum. A reviewer begins to infer that the result is fragile even where it is formally strong.

Use the following rhythm instead:

1. state the result;
2. explain why it matters;
3. provide the evidence;
4. state the exact scope once;
5. move technical edge cases to the appendix.

## 2.5 Multiple definitions of “oracle” create avoidable confusion

The draft marks the horizon-uniform allocation as `[ORACLE]` because it knows the horizon, while also calling exact padding costs “oracle lower bounds” because they know the realized evidence and live level. These are different notions.

Recommended terminology:

- call \(\gamma_t=1/T\) the **horizon-aware uniform allocation** or **best-case preallocated horizon**;
- reserve **oracle attack cost** for exact per-alert sizing.

## 2.6 The main feasibility metric is harder to interpret than necessary

The current level-\(w_0\) margin permits e-LOND to remain feasible at a negative margin, which requires repeated explanation and daggered table notes. In the main paper, report a controller-aligned feasibility ratio or margin for the selected baseline, so the boundary is visually and verbally simple:

\[
\rho = \frac{M c_0}{T}, \qquad \rho \ge 1 \text{ means cold-start feasibility under the horizon-aware allocation.}
\]

The cross-controller level-\(w_0\) margin can remain in the appendix. This is a presentation change, not a new experiment.

## 2.7 The current final figure visually equates strong and weak evidence

The padding panel is the paper's empirical climax. The ADDIS panels use a known-invalid real window and a synthetic stream. Giving all three equal space suggests that they carry equal evidentiary weight. The revised main figure should show padding only. Move the ADDIS panels and associated tables to the appendix.

## 2.8 Table captions are carrying too much argument

Several captions contain experimental setup, caveats, ordering conventions, validity status, and interpretation. This makes pages visually dense and forces reviewers to decode conclusions from notes.

Main-body captions should answer only:

- what is shown;
- what the key notation means;
- what comparison is primary.

All other details should appear in the methods paragraph or appendix.

---

# 3. Recommended body structure at a glance

The following structure fits a 12-page body while leaving space for readable figures and prose.

| New section | Function in the story | Approximate budget | Main items retained |
|---|---|---:|---|
| Abstract | One problem, one structural result, one repair, one attack, one transfer result | 0.4 page | Best-case bound, grouping tradeoff, Theorem 3, primary and AIT evidence |
| I. Introduction | Motivate the alert-layer problem and state the single causal chain | 1.2-1.4 pages | SOC motivation, composition gap, three contributions |
| II. Statistical Trust Layer and Evaluation Model | Give only the notation and assumptions needed to read the results | 1.0-1.2 pages | Evidence ceiling, group mean, rejection rule, threat model, compact data summary |
| III. Bounded Evidence Creates a Finite Alert Horizon | Establish structural failure and its security-scale consequence | 1.8-2.1 pages | Unified theorem, best-case corollary, simplified Fig. 2, one power-vs-feasibility example |
| IV. Grouping Restores Feasibility by Changing the Security Unit | Provide the inevitable bridge from theory to attack | 1.0-1.2 pages | Linear exchange, alert blur, simplified Fig. 3 |
| V. Attacker-Controlled Grouping Enables Padding Evasion | Deliver the main security result and empirical validation | 2.8-3.2 pages | Impossibility theorem, exact mean cost, state-free strategy, replay, host-conditioned and AIT transfer |
| VI. Design Alternatives and System Implications | Show that obvious fixes pay elsewhere without becoming another survey | 0.8-1.0 page | Compact three-row defense table, three deployment lessons |
| VII. Scope and Limitations | Consolidate validity and empirical scope once | 0.6-0.8 page | Claim-dependency paragraph, four limitations, ADDIS extension pointer |
| VIII. Related Work | Position the composition-level contribution | 0.6-0.8 page | Three tightly organized literature clusters |
| IX. Conclusion | Restate the causal chain, not every result | 0.2-0.3 page | Feasibility -> grouping -> attacker-controlled composition |

This creates a paper with one dominant arc and one empirical climax. The ADDIS material, full controller taxonomy, exhaustive matrices, and validity audits remain available without interrupting that arc.

---

# 4. Detailed paragraph-by-paragraph blueprint

## Title

The current title is strong and memorable. A slightly more focused version would better match the proposed main story:

### Preferred

**When Online Guarantees Go Silent: The Feasibility-Robustness Tradeoff in ML Intrusion Detection**

### Conservative alternative

**When Online Guarantees Go Silent: Feasibility and Padding Evasion in ML Intrusion Detection**

### Keep the current title when

The authors want “evasion” to include both padding and the appendix ADDIS extension. The current title remains defensible, but the paper should not promise two equal main attacks in its abstract.

---

## Abstract

### Required six-sentence structure

1. **Operational problem:** online FDR is attractive because intrusion detectors produce more scores than analysts can inspect.
2. **Hidden composition failure:** bounded conformal evidence may fall below the levels offered by arrival-time online controllers.
3. **Structural result:** state the finite horizon and best-case calibration-to-horizon bound.
4. **Necessary repair and cost:** grouping reduces the horizon but changes and blurs the security unit.
5. **Security result and evidence:** state the symmetric padding impossibility and the strongest primary/transfer findings; pair exact oracle costs with the existence of a state-free strategy.
6. **Takeaway:** validity, feasibility, semantics, and adversarial robustness must be evaluated jointly at the composed-system level.

### Recommended abstract draft

> Online false-discovery-rate control offers a principled way to turn machine-learning intrusion scores into an alert queue with a statistical error guarantee. We show that this composition can fail before detector quality matters. Deterministic conformal evidence is bounded by the calibration set, while common arrival-time controllers allocate shrinking testing levels; for two families covering LOND, e-LOND, e-LORD, and LORD++, this creates a finite discovery horizon. Even the best horizon-aware allocation requires \(|C| \ge kT/c_0-1\), which at LSPR23 flow granularity is about \(3.3\times10^8\) calibration flows for LOND/e-LOND, versus \(1.8\)-\(2.4\times10^6\) available. Grouping flows into episodes restores feasibility by reducing \(T\), but it also blurs fine-grained attack activity and makes the tested hypothesis partly attacker-controlled. We prove that no symmetric e-merging family capable of producing an alert can remain robust to arbitrary zero-evidence padding. In the LSPR23 pipeline, ordinary traffic suppresses all three canonical primary-window alerts at exact costs of 23-33 added flows; a fixed episode multiplier requiring no live controller state also suppresses every primary alert at higher cost. On a benign-inclusive transfer dataset, 78 of 79 detected episodes are suppressible under the same canonical pipeline. These results expose a composition-level tradeoff among statistical validity, operational feasibility, alert semantics, and adversarial robustness.

### Remove from the abstract

- the ADDIS stress-window result;
- the synthetic ADDIS result;
- the cap and asymmetric-rule details;
- the full list of online procedures;
- multiple windows and ordering qualifications;
- “each component may be valid under its stated assumptions,” unless the sentence is kept very short;
- any sentence that requires a parenthetical caveat longer than the claim itself.

---

## I. Introduction

### Paragraph 1: the operational object is the alert queue

Start with the SOC problem, not the statistical literature. The detector produces scores; the operator sees alerts and needs a meaningful error guarantee. Explain in plain language why AUROC/AUPRC do not answer the alert-queue question under low base rates.

**Keep:** the current opening insight that a SOC acts on an alert queue rather than scores.  
**Do not yet list:** LOND, LORD++, SAFFRON, ADDIS, e-GAI, and related procedures.

### Paragraph 2: the apparently modular solution

Introduce the four-module statistical trust layer:

\[
\text{detector} \rightarrow \text{conformal evidence} \rightarrow \text{security grouping} \rightarrow \text{online controller} \rightarrow \text{alert}.
\]

State the apparent promise: each module has a formal role, but module-level validity does not establish system-level viability.

### Paragraph 3: the hidden scale mismatch

Explain the core mechanism without theorem notation:

- deterministic rank-based evidence has a maximum fixed by the calibration set;
- an arrival-time online controller allocates a finite error budget across a long stream;
- eventually the largest possible evidence can be below the required threshold;
- this is structural silence, not merely weak detection power.

End with the paper's central question:

> Can the composed alert layer still issue an alert at the intended deployment horizon, and what security cost is incurred by the repair?

### Paragraph 4: the repair creates the attack surface

Explain that reducing the number of tests through episode grouping is the natural operational repair. Then make the bridge explicit:

> Grouping is not an unrelated preprocessing choice. It is the mechanism that makes the controller feasible, and it makes hypothesis membership partly controllable by the adversary.

This sentence should set up the rest of the paper.

### Paragraph 5: concise contribution list

Use three contributions, not “C1 / Bridge / C2” and not two equal attack surfaces.

#### Contribution 1 - Structural feasibility

> We characterize a finite discovery horizon for two families of arrival-time controllers operating on bounded evidence, and derive the max-min calibration-to-horizon requirement. The result converts a familiar loss-of-power phenomenon into a deployment test that can be evaluated before choosing a detector.

#### Contribution 2 - Feasibility-resolution tradeoff

> We show that episode grouping buys feasibility in direct proportion to the reduction in hypothesis count, while degrading a fixed fine-grained measure of alert resolution.

#### Contribution 3 - Padding impossibility and end-to-end transfer

> We prove that no alert-capable symmetric e-merging family is invariant to arbitrary zero-evidence padding, derive the exact cost for the mean, and validate the attack through real-flow replay, a state-free strategy, a host-conditioned detector, and a benign-inclusive transfer dataset.

Optionally add one final sentence:

> An appendix extends the analysis to evidence-conditioned controller state through an ADDIS manipulation result.

### Paragraph 6: novelty positioning without self-undermining

Use a positive distinction:

> Prior work separately studies conformal resolution, alpha-death, online FDR procedures, and e-value aggregation. Our contribution is to connect these ingredients into a deployment-level causal chain: the evidence ceiling determines whether an alert is possible; the operational repair changes alert semantics; and the repaired hypothesis becomes attacker-controllable.

Do not write “Neither ingredient is new” or “We claim none of these ingredients” in the contribution paragraph. The related-work section can provide exact attribution.

### Paragraph 7: empirical scope in one compact statement

State only what a reviewer needs:

- LSPR23 is the chronological main testbed;
- 0.55 is primary, 0.62 is a correlated secondary check;
- AIT-LDSv2.0 is the benign-inclusive transfer test;
- full windows, seeds, orders, and validity diagnostics are in the appendix.

Do not introduce the 0.85 stress window in the introduction. It belongs with the appendix ADDIS mechanism study.

### End-of-introduction roadmap

One sentence is enough:

> Sections II-III define the trust layer and derive its feasibility boundary; Section IV shows why grouping is the operational repair; Section V proves and evaluates the resulting padding vulnerability; Sections VI-VIII discuss defenses, scope, and related work.

### Move out of the introduction

- detailed sufficient conditions such as \(\gamma_t t^d\to0\);
- closure and donation constructions;
- selective index advancement and history-wide reconsideration;
- ADDIS validity failure and synthetic repair;
- window-specific caveats;
- exact order and seed conventions;
- the detailed statement that some findings use labels and others do not.

---

## II. Statistical Trust Layer and Evaluation Model

The purpose of this section is to make the rest of the paper readable, not to provide every implementation and validity detail.

### II-A. Bounded evidence and online decisions

Use only three equations in the main setup:

1. the two-point conformal e-value;
2. the evidence ceiling \(M=(|C|+1)/k\);
3. the rejection rule \(E(G_t)\ge 1/\alpha_t\).

Immediately give the plain-language interpretation:

> No detector score can create evidence above \(M\). Therefore a rejection is possible at time \(t\) only when \(\alpha_t\ge1/M\).

This one inequality is the spine of the paper.

### II-B. Grouped security hypotheses

Define the headline source-destination/two-hour episode and the arithmetic-mean e-merger. Explain why grouping is operationally natural and why the mean is the main symmetric arbitrary-dependence-valid merger evaluated.

Do not put the full variable-arity conditional-validity derivation here. Use a short scope box:

> **Guarantee scope.** The nominal FDR interpretation of e-LOND requires marginally valid group e-values under the precommitted grouping and ordering rule. The structural feasibility and padding-impossibility results do not depend on this premise. Appendix A states the exact condition and proves the group-level lemma; Appendix F reports diagnostics.

This turns the independence of the main claims from Assumption 1 into a strength rather than a defensive detour.

### II-C. Threat model

State the adversary's capabilities in a clean, affirmative list in prose:

- controls traffic from an attacker-operated or compromised host;
- can create ordinary traffic to the same destination within the same bucket;
- does not alter the detector, calibration code, stored scores, or original malicious flows;
- seeks to suppress the alert on its own grouped activity.

Then distinguish two attack-knowledge levels once:

- **exact sizing** uses realized evidence and the live testing level and is therefore a lower bound;
- **state-free over-provisioning** uses only the attacker's own episode size and a fixed multiplier.

Move calibration contamination and precursor episodes out of this main threat model.

### II-D. Evaluation overview

Keep this to roughly one-third of a page:

- LSPR23: 16.35M flows, chronological training/calibration/deployment;
- standard HistGradientBoosting detector used to isolate trust-layer behavior;
- primary 0.55 window and secondary 0.62 temporal check;
- metadata-derived canonical within-bucket order as the primary precommitted order;
- full five-window, two-seed, and order sensitivity in the appendix;
- AIT-LDSv2.0 introduced later for transfer.

Replace “detector novelty is not a contribution” with:

> We use a standard detector so that changes in alert behavior can be attributed to the statistical trust layer rather than to a novel classifier.

### Revised Figure 1

The main diagram should show a single causal chain:

1. detector scores become bounded evidence;
2. shrinking online levels create a finite alert horizon;
3. grouping lowers \(T\) and restores feasibility;
4. grouping makes membership attacker-controlled;
5. zero-evidence padding suppresses the alert.

Remove Surface B/ADDIS from the main diagram. A small dashed note may point to “adaptive controller-state extension, Appendix G,” but it should not compete visually with the main chain.

---

## III. Bounded Evidence Creates a Finite Alert Horizon

### Opening paragraph: define the phenomenon in plain language

Define **evidence-feasible at time \(t\)** and **finite discovery horizon**. Use one contrast:

> Detection power asks whether malicious activity produces strong evidence. Feasibility asks whether even the strongest admissible evidence could be accepted by the controller. The latter is fixed by the evidence ceiling and the controller level before a detector is evaluated.

Avoid introducing several near-synonymous terms at once. Use “finite discovery horizon” as the principal term; use “absorbing” only inside the theorem explanation.

### III-A. One headline theorem, two controller forms

The body should present one theorem with two cases or Theorems 1a and 1b under a single heading:

> **Theorem 1 (Finite discovery horizon).** With evidence bounded by \(M\), an arrival-time controller becomes permanently infeasible along a sufficiently long rejection-free run when its level is either (i) a spending-weight term whose history multiplier grows more slowly than the reciprocal weight decay, or (ii) a summable lag mixture over previous rejections. These cases cover the stated LOND/e-LOND/e-LORD and LORD++ configurations.

Then provide a three-sentence proof intuition:

- rejection requires \(\alpha_t\ge1/M\);
- under either form, the available level tends below that fixed floor during a long rejection-free run;
- after the final feasible step, no future evidence can restore an alert without changing the mechanism.

Put the exact hypotheses, non-monotone counterexample, precommitted e-LORD reparameterization, and full proofs in Appendix A. If combining the formal statements would risk mathematical imprecision, retain separate theorem statements but introduce them as two cases of one headline result and keep edge cases out of the body.

### III-B. Best-case calibration-to-horizon exchange rate

Keep Corollary 1 prominently. Rename the allocation:

> Among preallocated sequences over a known horizon, the horizon-aware uniform allocation maximizes the minimum cold-start level.

Then state:

\[
|C| \ge \frac{kT}{c_0}-1.
\]

Explain the count ratio in one memorable sentence:

> At \(k=1\), the best case requires 20 calibration units per hypothesis for LOND/e-LOND and 40 for LORD++.

The reviewer should be able to repeat this after reading the page.

### III-C. Security-scale consequence

Use a simplified version of current Figure 2:

- retain the LOND/e-LOND best-case line;
- optionally retain LORD++ as a second line;
- show the 1.8-2.4M available-calibration band;
- mark the LSPR23 flow horizon;
- move horizon-free \(T^{1.6}\), online e-BH, and extra annotations to the appendix unless they can be shown without clutter.

Main text should make one numerical point:

> At flow granularity, LOND/e-LOND would need approximately \(3.3\times10^8\) calibration flows under the best allocation, compared with \(1.8\)-\(2.4\times10^6\) available.

Do not also put every LORD++, one-hour-link, one-day-link, horizon-free, and short-prefix number in the same paragraph.

### III-D. Feasibility is not detector power

Use one clean empirical contrast, not four:

> The host-conditioned detector improves AUROC at the primary window but produces fewer e-LOND detections, while the feasibility boundary is unchanged because \(|C|\), \(k\), and \(T\) are unchanged.

This shows why the theorem matters. Move the Isolation Forest result, low-prevalence sweep, seed-specific 0-versus-30 contrast, and full detection matrix to Appendix C.

### III-E. Procedures outside the theorem

Use one paragraph:

> The theorem applies to arrival-time controllers whose spending state decays with elapsed hypotheses or rejection lags. Selective index advancement and history-wide reconsideration fall outside this class. Appendix C gives the complete procedure taxonomy and evaluates SAFFRON, ADDIS, online e-BH, closure, donation, deadlines, smoothing, and restart. These alternatives change the mechanism or temporal scope of the guarantee; they do not invalidate the need to check evidence scale against the intended horizon.

Remove current Table II from the body.

---

## IV. Grouping Restores Feasibility by Changing the Security Unit

This section is the bridge that makes the paper coherent. It should feel inevitable rather than like a new experiment section.

### Opening transition

> Corollary 1 makes the alerting unit a design variable. If the calibration corpus cannot grow, the direct way to restore feasibility is to reduce \(T\) by testing groups of flows rather than individual flows.

### IV-A. Grouping buys feasibility at a known rate

State the same exchange with \(T_{\text{group}}\). Focus the body on the source-destination family and the six bucket widths used in Figure 3. Say that five grouping families and all 35 configurations appear in Appendix D.

Use the controller-aligned feasibility ratio so that the crossing is intuitive.

### IV-B. Grouping spends resolution

Define the five-minute source-destination atom and **alert blur**. Explain why episode recall across changing bucket widths is not directly comparable. Keep the strongest progression:

- blur 1.0 at five minutes;
- 16.1 at two hours;
- 38.5 at one day in the primary window.

Do not include every intermediate value in prose; the figure can show the curve.

### Revised Figure 3

Use two aligned panels:

1. feasibility ratio versus bucket width;
2. alert blur versus bucket width.

Prefer the primary window as the emphasized line and the secondary as a lighter check. Move the other three windows to Appendix D. Mark the two-hour headline choice.

### Closing bridge to the attack

End with the paper's most important transition:

> The same operation that restores feasibility also determines which flows share one statistical hypothesis. Because endpoints, services, and timing are partly attacker-controlled, the repaired alert unit is now an input to the threat model.

The next section should begin immediately with the padding attack.

### Move to Appendix D

- all five grouping families;
- the 35-configuration table;
- full window and seed matrices;
- red-team task-record agreement and permutation/rotation nulls;
- detailed first-flow versus canonical ordering analysis;
- public versus keyed hash grinding;
- all alternative alert-resolution metrics.

The external task record is too weak to carry a main-body claim. It can remain as a directional sensitivity or be removed entirely.

---

## V. Attacker-Controlled Grouping Enables Padding Evasion

This should be the longest and strongest section. It is where the reviewer receives the security payoff promised by the title.

## V-A. Attack in plain language

Before formal notation, give a concrete example:

> An attack episode is a source-destination pair within a two-hour bucket. The attacker can open additional ordinary connections to the same destination before the bucket closes. These connections join the same tested hypothesis. They do not alter the malicious flows or their detector scores, but low-evidence additions reduce the aggregate evidence presented to the controller.

This is easy for a security reviewer to understand and makes the theorem feel motivated rather than abstract.

## V-B. Symmetric padding impossibility

Retain the formal definition of threshold padding robustness, but shorten the surrounding discussion. State Theorem 3 prominently:

> No symmetric e-merging family that can attain an alert threshold \(\theta>1\) is invariant to arbitrary zero-evidence padding.

Give the quantitative bound and a concise proof intuition based on domination by the arithmetic mean. Emphasize two points:

1. the theorem is class-wide and does not depend on LSPR23, detector quality, or the group-validity assumption;
2. the mean attains the bound, so the quantitative attack cost is tight for the evaluated merger.

Move the scaled-rule edge case, negative-dependence special case, and extended attainment discussion to Appendix A.

## V-C. Exact cost and attacker knowledge

Keep the exact mean formula:

\[
r^\star=\lfloor S\alpha_t\rfloor-m+1.
\]

Immediately pair it with the knowledge caveat and the state-free result:

> The exact cost is a lower bound because it uses the realized evidence sum and live controller level. A fixed multiplier of the attacker's own episode size requires neither quantity. On the primary canonical stream, a multiplier of ten suppresses every alert, at a median cost 15.7 times the exact lower bound.

This prevents the reviewer from carrying an “oracle-only attack” objection through several pages.

Do not spend a full paragraph on the range of \(1/\alpha_t\), all multipliers, the tuned \(c=3\) floor, flat-padding variants, or the stress-arm exception. Put those in Appendix E.

## V-D. Primary end-to-end evidence

Organize the empirical part around questions rather than datasets.

### Question 1: does the closed form predict the implemented pipeline?

- primary canonical detections: exact costs 23, 24, 33;
- controlled real-flow replay suppresses 3/3 at exactly the predicted threshold;
- secondary canonical detections: median exact cost 6 across 11 alerts.

State the result directly. Avoid interrupting the paragraph with order, seed, stress-window, and pad-pool caveats.

### Question 2: can the pad be selected without detector access?

Explain the training-prefix frequency rule for choosing a common protocol-port pair. Say that the rule uses no attack labels, detector outputs, calibration scores, or deployment traffic. Report that sampled pool flows do not reach the conformal tail in the primary test and that real-flow replay succeeds.

The five pool variants and service-matched exception belong in Appendix E.

### Question 3: is the result an artifact of a flow-only detector or attack-only host pairs?

Present the two transfer checks in increasing strength:

1. adding six causal host-context features on LSPR23 does not prevent suppression in the evaluated replay;
2. on AIT-LDSv2.0, where attacked hosts also receive real benign traffic, 78/79 flow-only detections are suppressible under the canonical order, and all nine evaluated host-conditioned detections are suppressible under causal context recomputation.

Then state scope once:

> These experiments rule out the simple explanations that padding works only because the baseline detector lacks host context or because the main dataset contains no benign traffic to attacked hosts. They do not establish vulnerability of every possible host-aware detector.

This is precise without sounding apologetic.

## V-E. One compact main results table

Replace the current heavily captioned Table III with a simpler table:

| Setting | Detected episodes | Exact padding cost | State-free/replay evidence | Main conclusion |
|---|---:|---:|---|---|
| LSPR23 primary, canonical | 3 | 23, 24, 33 | 3/3 real-flow replay; fixed multiplier suppresses all | Exact mechanism matches implementation |
| LSPR23 secondary, canonical | 11 | median 6 | flat state-free sensitivity in appendix | Low costs persist in temporal check |
| AIT flow-only, canonical | 79 | per-organization medians 12-4,650 | 78/79 suppressible; per-draw success 0.93-1.00 | Transfers to benign-inclusive hosts |
| AIT host-conditioned | 9 | medians 269 and 364.5 | 9/9 suppressible with causal context recomputation | Tested host context does not stop attack |

Use a two-line caption. Put order, seed, cost-definition, and dataset-specific notes below the table or in Appendix E.

## Revised main attack figure

Use only the padding-suppression curve from current Figure 4A, emphasizing:

- primary exact costs;
- secondary distribution;
- state-free multiplier or real-flow replay marker;
- AIT transfer summary if it can be shown clearly.

Move current Figure 4B/C to the ADDIS appendix.

---

## VI. Design Alternatives and System Implications

This section should answer “What should a defender do?” without becoming another results catalogue.

## VI-A. Obvious aggregation defenses pay elsewhere

Use one compact three-row table:

| Defense idea | What it fixes | What it gives up | Evidence location |
|---|---|---|---|
| Capped normalization | Resists appended members below the cap | Leaves the symmetric e-merging validity class above the cap; power collapses at validity-preserving caps | Appendix E |
| Precommitted asymmetric weights | Can ignore appended tail flows | Becomes vulnerable to a small number of leading flows; larger reach costs recall | Appendix E / proof in A |
| Group maximum with group-level calibration | Invariant to low-evidence padding | Calibration units fall 40-49x, collapsing feasibility in the evaluated streams | Appendix F |

The prose should draw one conclusion:

> The fixes shift the tradeoff among validity, feasibility, power, resolution, and robustness; none optimizes one module independently of the others.

Move Theorems 5 and 6, full weight sweeps, cap sweeps, insertion attacks, and group-calibration tables to the appendices.

## VI-B. Three system-design implications

1. **Size evidence against the horizon before tuning the detector.** Compute the best-case calibration-to-hypothesis ratio first.
2. **Choose the grouping rule as part of the security specification.** Report both feasibility and a fixed-denominator alert-resolution measure.
3. **Threat-model the trust layer, not only the classifier.** Any field that determines group membership or controller state can become attacker-facing.

The restart and temporal-scope discussion can be one sentence with a pointer to Appendix C.

---

## VII. Scope and Limitations

Consolidate caveats here so that earlier sections can read confidently.

### VII-A. Claim dependency in four sentences

> The finite-horizon theorem and calibration exchange rate use only a finite evidence ceiling and the stated controller form. The symmetric padding impossibility uses only the e-merging class. The empirical suppression results measure attack behavior against observed traffic and labels but do not require the e-values to satisfy a nominal FDR guarantee. Interpreting e-LOND's empirical rejection set as FDR-controlled additionally requires valid group e-values under the precommitted grouping rule; Appendix F states and audits this premise.

This should replace the main-body dependency table and repeated reminders throughout results.

### VII-B. Four limitations, each stated once

1. **Empirical breadth:** the main chronology comes from one live-fire exercise; AIT provides a second benign-inclusive transfer test, not broad cross-domain validation.
2. **Attack cost:** exact per-alert costs are lower bounds requiring live state; state-free over-provisioning is measured but can be more expensive.
3. **Detector and grouping scope:** transfer covers the six causal host features and grouping rules evaluated, not all host-aware architectures or multi-peer padding strategies.
4. **Theorem scope:** the finite horizon applies to bounded evidence and the stated arrival-time controller families under uninterrupted operation; alternative evidence constructions, restarts, selective advancement, and historical reconsideration change the mechanism or guarantee.

Avoid restating all order, seed, upper/lower-bound, and stress-window details here. Those belong in appendix table notes.

### VII-C. ADDIS extension pointer

Use at most two sentences:

> Appendix G studies a complementary surface in a controller that escapes elapsed-time decay through evidence-conditioned index advancement. It derives an ADDIS state-manipulation budget and separates a real-trace cost study from a guarantee-valid synthetic mechanism test; because this result is mechanism-specific and substantially more expensive, we treat it as an extension rather than the paper's main empirical claim.

Do not put ADDIS in the abstract, main figure, or contribution bullets.

---

## VIII. Related Work

Organize by the three gaps the paper fills, not by a list of procedure names.

### VIII-A. Online FDR and finite conformal resolution

Credit work on online FDR, alpha-death, conformal p/e-value resolution, smoothing, and existing observations of poor online-testing behavior. Then state the distinction:

> We turn the interaction into a deployment-feasibility criterion, derive a best-case calibration-to-horizon boundary, and connect the operational repair to a security vulnerability.

### VIII-B. Trustworthy intrusion detection and temporal evaluation

Connect chronological evaluation, concept drift, and conformal anomaly detection to the paper's protocol. State that prior work largely asks whether modules satisfy their assumptions or maintain predictive performance; this paper asks whether the composed alert mechanism can fire and remain secure.

### VIII-C. E-merging and adversarial testing

Credit symmetric and asymmetric e-merging theory and adversarial work on scores, p-values, and Byzantine reports. State the difference:

> The adversary neither changes detector scores nor corrupts reported evidence; it changes which legitimate observations belong to its own tested hypothesis.

### Remove from related work

- “We claim none of these ingredients.”
- lengthy discussion of every recent closure/donation method;
- feedback-aware procedures that are not needed to position the main result;
- repeated restatement of the paper's full contribution list.

---

## IX. Conclusion

Use one compact paragraph:

> Bounded evidence and shrinking online levels can make a statistically motivated alert layer structurally unable to fire. Grouping restores feasibility by reducing the number of hypotheses, but it coarsens alert semantics and makes group membership attacker-controllable. For symmetric e-merging, this produces an unavoidable padding vulnerability that ordinary traffic realizes in the evaluated pipelines and transfer dataset. Statistical validity is therefore only one property of a trustworthy security-ML alert layer; feasibility, semantics, and adversarial robustness must be designed and evaluated together.

Do not repeat the ADDIS result, validity diagnostics, stress-window caveat, or every theorem in the conclusion.

---

# 5. Main-body figure and table plan

## Figures

### Figure 1 - One causal chain

**Keep:** detector -> conformal evidence -> grouping -> online controller -> alert.  
**Show below:** bounded evidence + shrinking level -> finite horizon -> grouping lowers \(T\) but raises blur -> attacker pads group -> alert suppressed.  
**Remove:** equal-weight Surface B arrow.

### Figure 2 - Best-case calibration requirement

**Keep:** LOND/e-LOND best-case line, optional LORD++ line, available-calibration band, LSPR23 flow-scale marker.  
**Move:** horizon-free power-law line, online e-BH comparison, additional link-rate annotations.

### Figure 3 - Feasibility versus alert blur

**Keep:** source-destination grouping, bucket-width axis, primary emphasis, secondary check, two-hour marker.  
**Move:** all other windows and grouping families.

### Figure 4 - Padding cost and suppression

**Keep:** padding curve only, with primary/secondary and replay or state-free markers.  
**Move:** ADDIS real and synthetic panels to Appendix G.

## Tables

### Table 1 - Minimal system and evaluation configuration

A compact table can replace dispersed setup details:

- evidence construction and \(k\);
- baseline controller and \(q\);
- headline grouping;
- main order;
- primary/secondary windows;
- datasets.

### Table 2 - Core padding evidence

Use the simplified four-row table proposed in Section V-E.

### Table 3 - Defense tradeoffs

Use the three-row defense table proposed in Section VI-A.

## Remove from the main body

- current Table I dependency matrix;
- current Table II procedure taxonomy;
- stress-window rows in the headline attack table;
- any table whose caption is longer than the body paragraph interpreting it.

## Caption rule

A main-body caption should be no more than three lines in the two-column layout. Methodological qualifications belong in the text or appendix.

---

# 6. Proposed appendix architecture

The appendix should mirror the main paper rather than continue as a chronological record of every analysis performed.

## Appendix A. Formal Results and Proofs

- exact group-validity assumption and Lemma 1;
- full Theorem 1 cases and proofs;
- max-min proof for the horizon-aware allocation;
- full padding-impossibility proof and special cases;
- asymmetric-weight reach/front-load theorems;
- any closure/donation propositions needed for Appendix C;
- precise scope statements.

## Appendix B. Datasets, Models, and Reproducibility

- LSPR23 and AIT preprocessing;
- feature lists;
- detector configurations;
- chronological split construction;
- all procedure formulas and parameters;
- implementation consistency checks;
- artifact instructions.

## Appendix C. Full Feasibility Evidence and Controller Variants

- five windows and two seeds;
- full procedure matrix;
- SAFFRON, closure, donation, deadlines, smoothing, restart, online e-BH;
- low-prevalence sensitivity;
- Isolation Forest and additional detector contrasts;
- complete detection/feasibility matrices.

Begin the appendix with a two-sentence takeaway rather than forcing the reviewer to infer it from tables.

## Appendix D. Grouping and Ordering Sensitivities

- all five grouping families and six bucket widths;
- alert-blur variants;
- canonical versus first-flow order;
- random/precommitted orders;
- public and keyed hash analysis;
- external task-record directional check.

## Appendix E. Padding Attack Details

- all pad-pool constructions;
- full windows, seeds, and orders;
- exact versus state-free costs;
- multiplier and flat-padding sweeps;
- controlled replay details;
- host-conditioned LSPR23 analysis;
- AIT organization-level matrices;
- cap and asymmetric-weight defenses;
- insertion attacks.

## Appendix F. Validity Diagnostics and Alternative Calibration

- marginal and metadata-stratified diagnostics;
- label audit;
- direct group calibration;
- arity-stratified calibration;
- group maximum;
- calibration contamination, only if retained.

## Appendix G. Adaptive Controller-State Extension

Move the entire current Surface B section here:

- ADDIS mechanism and exact budget theorem;
- real stress-window cost study;
- guarantee-valid synthetic stream;
- grey-box estimation;
- operational traffic-volume conversion;
- current Figure 4B/C and Tables XXX-XXXII.

Frame it as an extension of the general design principle: mechanisms that escape elapsed-time decay by conditioning on observations may expose new state.

## Appendix H. Optional Secondary Baselines

The matched operating-point and analyst-feedback baselines should either:

- be moved here with a short explanation of why they answer a likely reviewer question; or
- be removed from the paper PDF and retained only in the artifact.

They are not needed for the main argument and should not be referenced from the body unless a claim depends on them.

## Appendix presentation rules

- Renumber appendix tables as **Table A1, A2, C1, E1**, etc., rather than continuing to Table XL. Local numbering makes the supplement feel structured rather than sprawling.
- Do not reproduce every raw matrix in the PDF. Put exhaustive order-by-seed-by-window outputs in the artifact and retain summary tables in the appendix.
- Start each appendix with “Question answered” and “Takeaway” sentences.
- Merge tables that differ only by seed or order when a panelled table or artifact pointer is clearer.

---

# 7. Current-to-new content map

| Current content | New location | Editorial action |
|---|---|---|
| Current abstract | Rewrite completely | Retain feasibility bound, grouping bridge, padding theorem, primary/AIT results; remove ADDIS and defense catalogue |
| Introduction paragraphs on modular trust layer | New Introduction P1-P4 | Keep and simplify |
| “Neither ingredient is new” paragraph | Intro novelty paragraph / Related Work | Recast positively; do not self-undermine |
| C1 / Bridge / C2 labels | Three contribution bullets | Replace; C2 currently bundles distinct attacks |
| Flow-level evidence equations | Section II-A | Keep only essential equations |
| Detailed Assumption 1 sigma-field and Lemma 1 | Appendix A; one scope box in II | Move technical statement/proof; retain dependency in plain language |
| Full controller list and parameters | Appendix B/C | Main body uses e-LOND baseline and names only theorem-covered families |
| Threat model | Section II-C | Keep padding threat only; move precursor/calibration-contamination threats |
| Five-window overlap percentages | Appendix B/D; one sentence in II | Compress |
| Stress-window validity discussion | Appendix F/G | Remove from main story |
| Table I claim dependencies | Section VII paragraph + Appendix F table | Remove main table |
| Theorems 1 and 2 | Section III-A + Appendix A | Present as one headline result/two cases; move edge cases |
| Corollary 1 | Section III-B | Keep prominently |
| Figure 2 | Section III-C | Simplify |
| Multiple detector/power contrasts | Section III-D + Appendix C | Keep one; move rest |
| Full Section III-D controller taxonomy | Appendix C | Replace with one paragraph |
| Table II | Appendix C | Remove from body |
| Grouping-family sweep | Appendix D | Body focuses on source-destination bucket widths |
| Alert blur | Section IV | Keep as main bridge |
| External red-team task record | Appendix D or remove | Too weak for main evidence |
| Theorem 3 | Section V-B | Make the main security theorem |
| Exact mean cost | Section V-C | Keep and pair immediately with state-free strategy |
| Five pad pools / 50 orders | Appendix E | Summarize in one sentence at most |
| Controlled replay | Section V-D | Keep prominently |
| Host-conditioned LSPR23 | Section V-D | Keep concise |
| AIT transfer | Section V-D | Keep prominently |
| Cap, asymmetric weights, maximum | Section VI-A | Keep one tradeoff table; details in E/F/A |
| Current Section VI ADDIS | Appendix G | Remove from abstract, contributions, main Fig. 1, and main results |
| Design implications | Section VI-B | Keep three concise lessons |
| Validity and limitations | Section VII | Consolidate; stop repeating earlier |
| Related work | Section VIII | Reorganize around three gaps |
| Current Figure 4 | Main padding panel + Appendix G state panels | Split by evidentiary role |
| Open science / ethics / LLM usage | Required back matter | Keep and complete; not part of narrative compression |

---

# 8. Tone guide: precise confidence without overclaiming

## 8.1 General rule

Confidence comes from saying exactly what was established, once. Repetition of non-claims does not make the paper more rigorous; it makes the result sound unstable.

Use:

- **prove** for formal theorems;
- **derive** for exact algebraic consequences;
- **show** for direct empirical observations;
- **validate** when replay matches a closed-form prediction;
- **transfer** when the same pipeline/mechanism is evaluated on AIT;
- **supports** for broader interpretation;
- **does not establish** only in the consolidated limitations section.

## 8.2 Before/after examples

### Novelty

**Current style**  
“Neither ingredient of this result is new...”

**Recommended**  
“Prior work establishes finite conformal resolution and decaying online levels separately. We characterize their composition as a finite-horizon deployment problem and derive the resulting calibration boundary.”

### Detector choice

**Current style**  
“Detector novelty is not a contribution.”

**Recommended**  
“We use a standard detector to isolate the behavior of the statistical trust layer.”

### Theorem scope

**Current style**  
“The theorems are deliberately scoped: they do not say every online FDR procedure dies...”

**Recommended**  
“The theorem covers arrival-time procedures satisfying the two stated spending forms. Procedures using selective advancement or history-wide reconsideration are analyzed separately in Appendix C.”

### Validity premise

**Current style**  
“The premise is stronger than... and is not established by the dataset. We therefore...”

**Recommended**  
“Nominal FDR control of the empirical e-LOND run requires group-level marginal validity. The feasibility and padding results are independent of this premise; Appendix F states and audits it.”

### Transfer scope

**Current style**  
“The transfer result has a precise scope. It does not show that every host-aware detector is vulnerable...”

**Recommended**  
“The transfer rules out the simplest defense represented by the six causal host-context features evaluated here; broader host-aware architectures remain open.”

### Canonical order

**Current style**  
“Canonicalisation is not a security mechanism...” followed by hash-grinding detail.

**Recommended**  
“A metadata-derived canonical order keeps unrelated hypotheses fixed under padding. Order manipulation and keyed alternatives are evaluated in Appendix D.”

### Exact attack cost

**Current style**  
“Reported \(r^\star\) values are therefore oracle lower bounds... not turnkey budgets...”

**Recommended**  
“Exact sizing provides a lower bound. A fixed episode multiplier removes the need for live state and suppresses every primary canonical alert at higher measured cost.”

### ADDIS stress window

**Current style**  
“This demonstrates the mechanism and prices it; it is not an FDR-valid real-data result.”

**Recommended appendix style**  
“We use the real stress window to measure implementation-level cost and a separate conservative-null simulation to establish the mechanism under valid nulls.”

## 8.3 Phrases to minimize

- “We do not claim...”
- “not a contribution”
- “only” when describing a result
- “merely”
- “deliberately scoped”
- “not a hypothesis and not a remark”
- “not a general claim”
- repeated “known-invalid” labels outside the appendix
- multiple caveats in parentheses

## 8.4 Sentence-level readability rules

- One principal result per sentence.
- No more than two numerical values in a prose sentence unless they form a direct comparison.
- Explain a symbol in words before using it in a theorem.
- Keep theorem intuition separate from theorem edge cases.
- Use paragraph-opening topic sentences that tell the reviewer why the paragraph exists.
- Avoid introducing more than one new procedure name per paragraph.
- Reserve footnotes and appendix references for implementation detail, not the central logic.

---

# 9. Likely reviewer objections and where the revised paper answers them

| Reviewer objection | Main-body answer | Appendix support |
|---|---|---|
| “This is just alpha-death plus conformal resolution.” | Introduction novelty paragraph; Theorem 1 as a deployment-feasibility criterion; max-min calibration bound | Full relation to prior work and exact theorem scope in A/C |
| “A strong detector could solve this.” | Section III-D: feasibility depends on \(|C|,k,T\), with one host-detector contrast | Full detector and seed comparisons in C |
| “Grouping is an arbitrary design choice.” | Section IV: grouping is the direct way to reduce \(T\) when calibration cannot grow | All grouping families in D |
| “The attack is specific to the arithmetic mean.” | Theorem 3: class-wide symmetric e-merging impossibility | Full proof and special cases in A |
| “The attack needs oracle access.” | Section V-C pairs exact lower bound with fixed multiplier requiring no live state | Full multiplier/flat-pad sweep in E |
| “Padding works only because LSPR23 attack pairs have no benign traffic.” | AIT benign-inclusive transfer result | Organization matrices in E |
| “Host context would detect repetitive padding.” | Causal host-conditioned replay and AIT host-conditioned result | Feature details and per-organization results in B/E |
| “The group e-values may not be valid.” | Section VII separates the FDR interpretation from theorem and attack claims | Exact assumption, diagnostics, and group calibration in A/F |
| “The canonical order is artificial.” | Section II explains why a precommitted order isolates padding; order is not a defense claim | Complete ordering sensitivity and hash analysis in D |
| “The theorem does not cover all online FDR methods.” | Section III-E states the covered arrival-time class and points to alternatives | Full taxonomy, restart, smoothing, e-BH, etc. in C |
| “The paper contains two unrelated attacks.” | Main body centers only the feasibility -> grouping -> padding chain | ADDIS is explicitly an appendix extension in G |

---

# 10. Hard cuts, appendix moves, and artifact-only material

## Keep in the body

- one evidence construction;
- one headline controller baseline;
- one finite-horizon theorem with two cases;
- the max-min corollary;
- one security-scale feasibility figure;
- one grouping family illustrating feasibility versus blur;
- Theorem 3;
- exact mean cost and one state-free strategy;
- primary, secondary, replay, host-conditioned, and AIT transfer results;
- one compact defense table;
- one consolidated scope section.

## Move to appendices

- full proofs and theorem edge cases;
- Assumption 1 details and diagnostics;
- all alternative controllers;
- all windows, seeds, and orders;
- all grouping families;
- all padding pools;
- all defense sweeps;
- ADDIS;
- label audit;
- calibration contamination if retained;
- negative baselines.

## Consider removing from the PDF entirely and retaining in the artifact

- raw 50-order matrices;
- every seed-by-window-by-order result when an appendix summary already exists;
- analyst-feedback controllers that are not FDR methods;
- matched threshold tables that do not support a main claim;
- weak external-task-record null analyses;
- duplicate operational-unit conversions;
- tables whose only purpose is to verify arithmetic already reproduced by code.

The artifact can demonstrate completeness without forcing every result into the paper.

---

# 11. Suggested rewrite sequence

1. **Lock the one-sentence thesis and contribution hierarchy.** Do this before rewriting any paragraph.
2. **Remove ADDIS from the abstract, main contribution list, Figure 1, and Figure 4.** Create the appendix extension first so no content is lost.
3. **Rewrite the abstract and introduction from a blank page.** Do not edit the current introduction sentence by sentence; its architecture is the problem.
4. **Reduce Section II to essential notation, padding threat model, and compact data overview.** Move the validity machinery before polishing prose.
5. **Rewrite the theory section around one headline theorem and one memorable corollary.** Select one power-versus-feasibility example.
6. **Rewrite grouping as a causal bridge, not a standalone empirical section.** End with attacker-controlled membership.
7. **Make padding the empirical climax.** Put state-free evidence before the reviewer can object to oracle sizing.
8. **Create the compact defense table and three design implications.** Remove the full alternative-procedure discussion from the body.
9. **Write one consolidated scope/limitations section.** Delete repeated caveats elsewhere.
10. **Rebuild figures and captions for one-message readability.** Split padding and ADDIS visual evidence.
11. **Reorganize appendices by question.** Use local appendix numbering and move exhaustive matrices to the artifact.
12. **Run a final “reviewer memory” pass.** Every page should reinforce at least one of the four durable ideas listed in the executive decision.

---

# 12. Final reviewer-memory test

After a single read, a reviewer should be able to say:

> The paper studies the composed alert layer around an intrusion detector. Because conformal evidence is bounded and online levels shrink, common arrival-time controllers have a finite horizon in which any alert is possible; even the best allocation needs calibration linear in the number of hypotheses. Grouping restores feasibility but blurs attacks and makes the hypothesis attacker-controlled. The authors prove a class-wide padding impossibility for symmetric e-merging and show that ordinary traffic suppresses alerts in the main pipeline and a benign-inclusive transfer dataset. The contribution is therefore a coherent feasibility-to-security tradeoff, not another detector or another online-FDR procedure.

If the final paper produces that summary without requiring the reviewer to reconstruct it from caveats, tables, and appendices, it will be substantially stronger without adding a single experiment.
