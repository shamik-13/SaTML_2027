# Reviewer-Gap Checklist Before Writing the SaTML Manuscript
## Experiments and analyses I would close before freezing the paper

**Project:** Online statistical error control for ML intrusion detection  
**Target:** IEEE SaTML main track  
**State reviewed:** Phase 3 (`06_PHASE3_REPORT.md`, 26 Aug 2026)

---

# 0. Executive recommendation

The project already has a credible main-track contribution. The remaining work should **not** be another open-ended experiment phase.

Instead, I would run a final **reviewer-gap closure phase** whose purpose is:

> **For every obvious “why didn't you just …?” objection a strong SaTML/statistics reviewer could raise, either run the decisive experiment or make the limitation explicit before manuscript writing begins.**

The most important remaining gaps are not “add another classifier” or “run another \(q\)-sweep.” Those have diminishing value.

The high-value gaps are:

1. **Does randomized/smoothed or continuous statistical evidence remove the finite-evidence feasibility problem?**
2. **Does periodic restart/batching remove the long-horizon problem in a realistic SOC deployment?**
3. **Does the granularity result survive on a dataset with genuine flow-to-campaign ground truth?**
4. **Can the padding attack be demonstrated as an actual problem-space traffic manipulation rather than only an offline evidence manipulation?**
5. **Can an asymmetric/precommitted aggregation rule escape the padding theorem without becoming operationally useless?**
6. **Are the position-0.85 anomalous flows attack-like in raw feature space / near-neighbour geometry?**
7. **Does the operational conclusion survive a second reasonable feedback controller and wall-clock disposition delays?**
8. **Are the main results robust when parameters are selected on earlier data rather than with knowledge of the test window?**

I would treat Items 1–5 as the main “reviewer-killer” tests.

---

# 1. Priority Legend

## P0 — Must close before manuscript

A reviewer could use this as a central reason to reject or substantially weaken the main claim.

## P1 — Strongly recommended

Not fatal individually, but worth closing while time remains.

## P2 — Useful robustness / appendix

Do only after P0/P1 are complete.

---

# 2. P0 — Randomized / Smoothed Conformal Evidence

## Reviewer objection

> “Your finite discovery horizon comes from discrete threshold-conformal evidence. Recent conformal work explicitly discusses resolution collapse and shows that randomized smoothing or continuous relaxations can remove the p-value floor. Why not use those?”

This is probably the **single most important technical experiment still missing**.

The current record explicitly cites the recent “resolution collapse” work, but does not appear to test the proposed escape.

That makes this an obvious reviewer question.

---

## Why it matters

The current feasibility mechanism uses bounded evidence:

\[
E_t \le M,
\]

combined with a rejection requirement:

\[
E_t \ge \frac{1}{\alpha_t}.
\]

For rank-\(k\) threshold conformal evidence:

\[
M = \frac{|C|+1}{k}.
\]

If a randomized or continuous evidence construction effectively removes the finite ceiling, then the universal-sounding form of the feasibility story must be narrowed.

That would **not kill the paper**, but we need to know before writing.

---

## Experiment 1A — Randomized smoothed conformal p-values

Construct standard smoothed/randomized conformal p-values.

For ties / rank discreteness, use auxiliary randomness so that p-values have continuous support rather than a floor at:

\[
\frac{1}{|C|+1}.
\]

Run at least:

- e-LOND;
- e-GAI / e-LORD;
- online e-BH if compatible.

Measure:

- empirical FDR/FDP;
- recall;
- episode recall;
- alert count;
- variance across random seeds;
- probability the same attack is detected across repeated randomizations;
- detection latency variance.

Use at least 100 randomization seeds for the main selected configurations.

---

## Experiment 1B — Stability / reproducibility cost

This is essential.

If smoothing restores discoveries but two runs on identical network traffic produce different alerts, quantify it.

Metrics:

### Alert-set Jaccard

\[
J(A_i,A_j)
=
\frac{|A_i\cap A_j|}{|A_i\cup A_j|}.
\]

### Attack detection probability

For attack episode \(a\):

\[
P_{\text{rand}}(a\text{ detected}).
\]

### Alert-count variance

\[
\mathrm{Var}(R_T).
\]

### FDP variance

\[
\mathrm{Var}(FDP_T).
\]

A security system with a formal guarantee but highly random attack detection is operationally questionable.

---

## Experiment 1C — Continuous/asymptotic evidence relaxation

If realistically implementable, test one continuous alternative such as:

- a continuous p-to-e calibrator;
- the continuous inference relaxation from the recent resolution-collapse work;
- another standard continuous e-value construction.

Do **not** build a new method.

The question is simply:

> Does removing finite resolution restore useful power at the cybersecurity horizon, and what statistical guarantee is sacrificed?

Record explicitly whether the alternative offers:

- finite-sample exact validity;
- asymptotic validity;
- marginal validity;
- conditional validity.

---

## Possible outcomes

### Outcome A — smoothing does not fix practical detection

Very strong for the paper.

### Outcome B — smoothing fixes feasibility but introduces high variance

Also strong.

The paper becomes:

> finite-resolution guarantees have a feasibility problem; randomized escape trades determinism/stability for resolution.

### Outcome C — continuous relaxation solves the problem cleanly

Then narrow C1 to:

> exact finite-resolution evidence creates the feasibility boundary.

The paper still has:

- granularity tradeoff;
- attackable aggregation;
- state manipulation.

But we must not oversell C1.

---

## Completion criterion

Do not write the final C1 claim until this experiment is complete.

**Priority: P0 / critical.**

---

# 3. P0 — Periodic Restart / Batching as the Obvious Operational Fix

## Reviewer objection

> “A SOC does not need to run one online controller forever. Why not reset the controller every hour/day/shift and avoid alpha-death?”

This is a very likely reviewer reaction.

The current work studies horizon misspecification, but a **restart policy** is a different intervention.

Existing multiple-testing work already treats batching as a power-recovery mechanism, so we should directly address it.

---

## Experiment 2A — Periodic controller reset

Run the main procedures with deterministic epochs:

- 1 hour;
- 6 hours;
- 12 hours;
- 24 hours;
- 48 hours;
- one exercise/day boundary if available.

At every epoch boundary:

- reset online wealth/controller state;
- retain the same detector/calibration unless separately testing recalibration.

Compare with the uninterrupted controller.

---

## Measure

- global empirical FDP over the entire deployment;
- per-epoch FDP;
- episode recall;
- malicious-flow coverage;
- alerts/day;
- time-to-detection;
- fraction of epochs with zero discoveries;
- structural-silence fraction.

---

## Statistical issue to make explicit

If each epoch independently targets:

\[
q=0.05,
\]

does that imply the **pooled deployment-level FDR** is controlled at 0.05?

Do not assume so.

The paper should distinguish:

### Per-epoch guarantee

from

### whole-deployment guarantee.

If a global guarantee requires allocating error budget across epochs, test that too.

---

## Experiment 2B — Alpha-budgeted restarts

If theory permits, assign:

\[
q_1,q_2,\dots
\]

across epochs under a precommitted schedule.

Compare:

- statistical validity;
- power;
- operator interpretability.

---

## Experiment 2C — Restart + grouping interaction

Test whether:

\[
\text{restart}
+
\text{fine-grained hypotheses}
\]

can preserve episode resolution without requiring coarse grouping.

This could materially affect C2.

---

## Possible outcomes

### Restart restores power but loses a meaningful global guarantee

Excellent discussion result.

### Restart restores both power and an acceptable guarantee

Then it is an important mitigation and must be acknowledged.

### Restart does little

Strengthens C1 substantially.

---

## Completion criterion

The manuscript should be able to answer in one sentence:

> “Why not just restart the controller daily?”

**Priority: P0.**

---

# 4. P0 — Second Dataset with Genuine Flow-to-Campaign Labels

## Reviewer objection

> “Your ‘episodes’ are heuristic host/time groups, not actual security incidents. How do we know the granularity tradeoff is not an artifact of your grouping heuristic or of LSPR23?”

This is currently the largest **empirical breadth** weakness.

The Phase 3 report itself identifies the second dataset as the only open item that could still change a headline result.

---

## Required property

The second dataset should have:

\[
\text{individual flow/event}
\rightarrow
\text{actual attack campaign / scenario / incident}
\]

mapping.

Not just:

- binary attack labels;
- host labels;
- alert categories.

---

## Minimum experiment only

Do **not** reproduce the whole paper.

Run:

### 3A — Event-level feasibility

Compute:

\[
T_{\text{flow}},
\quad
|C|,
\quad
M,
\quad
\text{feasibility margin}.
\]

### 3B — True campaign-level feasibility

Aggregate using the dataset's actual campaign identity.

Compute:

\[
T_{\text{campaign}}
\]

and the corresponding feasibility margin.

### 3C — Evaluation-unit disagreement

Compare:

- flow recall;
- campaign recall;
- number of analyst-facing discoveries.

### 3D — One padding experiment

Test whether the qualitative aggregation vulnerability transfers.

---

## Strict stop rule

Spend at most a short engineering budget on candidate inspection.

Reject a candidate if:

- campaign labels require manual reconstruction;
- negatives are incomplete;
- chronological ordering is unavailable;
- there are too few campaigns;
- the campaign identifiers are derived from the same heuristic we are trying to validate.

---

## Why this materially increases acceptance confidence

A successful result would change C2 from:

> “On LSPR23, our deployable episode heuristics exhibit this tradeoff.”

to:

> “The tradeoff appears under both deployable grouping and actual campaign ground truth.”

That is a significant upgrade.

**Priority: P0.**

---

# 5. P0 — Problem-Space Demonstration of the Padding Attack

## Reviewer objection

> “You show that adding benign e-values suppresses aggregated evidence. Can an attacker actually generate traffic that produces those e-values and lands in the same group?”

The current result is already strong mathematically and uses realistic benign pools, including black-box pools.

But a security reviewer may still ask for a **problem-space demonstration**.

---

## Experiment 4A — Controlled traffic generation

Use a controlled environment such as ConCap or another lightweight testbed.

Generate:

1. a malicious action that the detector scores strongly;
2. a small number of ordinary benign-looking connections controlled by the same host;
3. all traffic within the same grouping definition.

Demonstrate:

\[
\text{detected attack}
\rightarrow
\text{add benign traffic}
\rightarrow
\text{same underlying attack}
\rightarrow
\text{alert suppressed}.
\]

---

## The key requirement

Do **not** optimize raw features directly.

The attacker should manipulate only realistic network actions:

- HTTP/TLS requests;
- DNS lookups;
- benign service connections;
- short TCP sessions;
- normal protocol interactions.

This prevents a reviewer from calling the attack a feature-space artifact.

---

## Experiment 4B — Rate / volume realism

Convert attack cost from “number of flows” into:

- flows/sec;
- bytes/sec;
- packets/sec;
- total attack duration.

For the padding attack, this will likely make the realism argument much stronger.

For the ADDIS state attack, it will correctly show why the attack is structural rather than operationally cheap.

---

## Experiment 4C — Attacker control of group membership

Explicitly verify that the attacker can cause padding to share the same:

- source host;
- destination host if required;
- time bucket;
- service grouping if used.

If NAT or attribution complicates this, state the required deployment condition.

---

## Completion criterion

The paper should be able to claim:

> “We reproduced the suppression effect using attacker-generated network traffic, not merely offline insertion of benign feature vectors.”

**Priority: P0 for a security venue if feasible.**

---

# 6. P0/P1 — Asymmetric or Precommitted Aggregation Escape

## Reviewer objection

> “Your impossibility theorem is about symmetric e-merging. Why not use an asymmetric weighting rule?”

The record already recognizes that a fixed precommitted slot can be padding-invariant.

That gives the reviewer an immediate escape route.

We should quantify its cost more realistically.

---

## Experiment 5A — Fixed temporal weighting

Evaluate valid precommitted weight schemes such as:

- first event only;
- last event only;
- fixed exponential decay by position;
- fixed uniform weights over the first \(m_0\) slots;
- fixed security-prior weights defined before observing scores.

Do not choose weights using the observed anomaly scores.

---

## Experiment 5B — Adversarial event placement

Test two attacker models:

### Attacker cannot choose slot/order

Then asymmetric merging may genuinely help.

### Attacker can influence timing/order

Then test whether the attacker can place:

- padding in high-weight positions;
- attack evidence in low-weight positions.

---

## Measure

- validity;
- padding resistance;
- episode recall;
- malicious-flow coverage;
- required group size;
- attack cost.

---

## What we want to establish

Likely tradeoff:

\[
\text{padding robustness}
\leftrightarrow
\text{dependence on precommitted position}
\leftrightarrow
\text{power / attacker control of ordering}.
\]

If a simple asymmetric rule solves everything, we need to know before submission.

**Priority: P0/P1.**

---

# 7. P1 — Finish the Position-0.85 Forensics

## Reviewer objection

> “You say the anti-conservative tail is probably post-compromise label error. What does the feature geometry say?”

Phase 3 already did most of the hard work.

Only two cheap analyses remain worthwhile.

---

## Experiment 6A — Near-neighbour geometry

For each of the 46 extreme-tail benign-labelled flows:

- nearest malicious flow distance;
- nearest ordinary benign distance;
- nearest calibration benign distance.

Use standardized model features.

Report distributions of:

\[
d_M,\ d_B,\ d_C.
\]

Useful statistic:

\[
\rho = d_M / d_B.
\]

---

## Experiment 6B — Per-feature enrichment

Compare:

- extreme-tail labelled-benign;
- ordinary benign;
- labelled malicious.

Report standardized feature differences and the top distinguishing features.

---

## Interpretation rule

If tail flows are attack-like:

> strengthens “consistent with post-compromise label error.”

If not:

> keep only the localization claim.

Do not claim proof either way.

**Priority: P1, cheap and worth doing.**

---

# 8. P1 — Second Feedback Controller + Wall-Clock Delay

## Reviewer objection

> “Your operational comparison depends on one hand-chosen proportional controller, and your feedback latency is measured in alerts rather than real time.”

This is a fair criticism of RQ4.

---

## Experiment 7A — Second controller

Implement one simple alternative:

### Option A — PI controller

or

### Option B — direct adaptive quantile controller.

Avoid inventing a sophisticated new control algorithm.

---

## Experiment 7B — Wall-clock disposition delay

Use realistic delays such as:

- 15 min;
- 1 h;
- 4 h;
- 8 h;
- 24 h;
- 72 h.

Use chronological timestamps.

If the current deployment window is too short, use the longer available stream/window for this experiment.

---

## Compare

- realized FDP;
- episode recall;
- alerts/day;
- burn-in;
- time until the controller becomes responsive.

---

## Desired result

The paper does not need FDR control to beat feedback universally.

The useful conclusion may be:

> direct feedback is competitive when dispositions arrive quickly; formal no-feedback error control is most relevant under long or absent feedback delays.

That is a strong and honest operational conclusion.

**Priority: P1.**

---

# 9. P1 — Cross-Window Parameter Transfer / Anti-Cherry-Picking

## Reviewer objection

> “Were the grouping width, cap, spending sequence, or threshold configuration selected after looking at the test window?”

The project has broad sweeps, which helps, but reviewers may still question the headline configuration.

---

## Experiment 8A — Previous-window selection

For each deployment window \(j\):

1. choose the configuration using only window \(j-1\);
2. freeze it;
3. evaluate on window \(j\).

Possible parameters:

- bucket size;
- grouping family;
- cap \(n_0\);
- spending sequence family;
- \(q\), if operationally tuned.

---

## Experiment 8B — Leave-one-window-out selection

Use four positions to choose a single configuration.

Evaluate on the held-out fifth.

Repeat five times.

---

## Goal

Show that the main qualitative findings do not require test-window oracle tuning.

**Priority: P1.**

---

# 10. P1 — Calibration Contamination / Poisoning Sensitivity

## Reviewer objection

> “Your evidence assumes a large clean benign calibration set. In security, how do you know the calibration period is attack-free?”

This is especially relevant because the project itself finds evidence of label issues.

---

## Experiment 9

Contaminate calibration with malicious flows at:

\[
\epsilon
\in
\{0,\ 10^{-5},\ 10^{-4},\ 10^{-3},\ 10^{-2}\}.
\]

Test both:

- random attack contamination;
- high-score attack contamination.

Measure:

- evidence ceiling;
- benign firing rate;
- malicious firing rate;
- feasibility margin;
- recall;
- FDP.

---

## Why it helps

Even if this is ultimately a limitation, quantifying sensitivity lets the paper say what level of calibration contamination is tolerable.

Do not turn this into a full poisoning paper.

**Priority: P1.**

---

# 11. P2 — Ordering / Timestamp-Tie Sensitivity

## Reviewer objection

> “Online testing depends on order. What happens when many events or episodes share timestamps?”

Cheap robustness check.

---

## Experiment 10

For equal-time hypotheses:

- preserve deterministic source order;
- randomize within timestamp;
- repeat across 50 seeds.

Measure variance in:

- discoveries;
- FDP;
- recall;
- first detection.

If negligible, put one sentence in the appendix.

**Priority: P2.**

---

# 12. P2 — Physical Cost Reporting for Both Attacks

Even without new experiments, convert all attack budgets into operational units.

For each attack report:

- flows;
- packets;
- bytes;
- average bandwidth;
- required rate over the bucket duration;
- number of attacker hosts if distributed.

This will make the distinction very clear:

### Padding attack

Potentially operationally realistic.

### ADDIS state attack

Structurally real but very expensive.

**Priority: P2, easy.**

---

# 13. P2 — Attack Transfer Across More Than One Window

The padding attack should ideally not live entirely at position 0.85.

Run a reduced attack experiment on the other windows where any target detections exist.

No need for every pool.

Use:

- one generic benign pool;
- one black-box common-service pool.

Report median suppression cost where measurable.

This helps prevent:

> “The attack only exists in the anomalous label window.”

**Priority: P2/P1 if enough detections exist.**

---

# 14. What I Would NOT Spend Time On

Do not add:

- more generic classifiers;
- more \(q\) values;
- more random spending sequences;
- more symmetric cap policies;
- more benign padding pools;
- another full procedure zoo;
- another CIC-style dataset without campaign labels;
- exhaustive hyperparameter optimization.

Those do not address the strongest reviewer objections.

---

# 15. Recommended Final Experiment Queue

## Tier 0 — Do these before manuscript writing

| Order | Gap | Experiment | Why |
|---|---|---|---|
| **1** | Randomized/continuous evidence escape | smoothing + continuous evidence comparison | Could materially narrow C1 |
| **2** | Periodic restart/batching | hourly/daily/shift reset | Obvious operational fix to alpha-death |
| **3** | True incident/campaign validation | second dataset, minimal 3–4 experiments | Biggest empirical-generality weakness |
| **4** | Problem-space attack | controlled generated benign padding | Converts mathematical attack into security attack |
| **5** | Asymmetric merge escape | precommitted weights + adversarial ordering | Obvious counterexample to symmetric theorem |

---

## Tier 1 — Strongly recommended

| Order | Gap | Experiment |
|---|---|---|
| **6** | Position-0.85 residual | near-neighbour + per-feature analysis |
| **7** | Feedback baseline | second controller + wall-clock latency |
| **8** | Hyperparameter selection | previous-window / leave-one-window-out transfer |
| **9** | Calibration cleanliness | contamination sweep |

---

## Tier 2 — Appendix robustness

| Order | Gap | Experiment |
|---|---|---|
| **10** | same-time ordering | randomize timestamp ties |
| **11** | attack realism reporting | bytes/rate/bandwidth conversion |
| **12** | attack generality | reduced cross-window padding test |

---

# 16. Decision Logic for the Five P0 Tests

## P0-1 Randomized smoothing

### If it fails to restore useful detection

C1 becomes stronger.

### If it works but is unstable

Add a:

\[
\text{resolution}
\leftrightarrow
\text{randomness/stability}
\]

tradeoff.

### If it solves the issue cleanly

Narrow C1 to exact/discrete finite-resolution evidence.

---

## P0-2 Restarts

### If restarting solves power but loses whole-stream guarantees

This becomes an important mitigation/caveat.

### If a rigorous restart policy solves both

Present it as the practical remedy.

### If it does not solve the issue

C1 gets much stronger.

---

## P0-3 Second dataset

### If campaign-level result replicates

Major confidence increase.

### If it does not

C2 needs narrowing to LSPR23/deployable episodes.

That is exactly why we should know before writing.

---

## P0-4 Problem-space padding

### If attack works

C3 becomes extremely compelling for SaTML.

### If offline evidence manipulation does not transfer to real traffic

Narrow C3 to a statistical vulnerability rather than practical evasion.

---

## P0-5 Asymmetric aggregation

### If it solves padding at reasonable power

It becomes a mitigation.

### If it loses power or is attackable through ordering

That completes the robustness/power/attackability triangle.

---

# 17. Reviewer Questions We Should Be Able to Answer Before Writing

Before manuscript drafting, we should have a clean answer to all of these:

1. **Why not randomize/smooth the conformal p-values?**
2. **Why not use continuous e-values?**
3. **Why not reset the FDR controller every day?**
4. **Why not batch hypotheses?**
5. **Why should we believe heuristic episodes reflect actual incidents?**
6. **Does the granularity result replicate with true campaign IDs?**
7. **Can an attacker actually generate the padding traffic?**
8. **Can an asymmetric aggregation rule stop the attack?**
9. **Does the padding attack require white-box detector access?**
10. **Are position-0.85 “false alerts” actually label errors?**
11. **Does the result depend on one feedback controller?**
12. **Does realistic analyst feedback delay change the conclusion?**
13. **Were headline parameters chosen using test data?**
14. **What if the benign calibration set is contaminated?**
15. **Does event ordering at tied timestamps matter?**
16. **How expensive are the attacks in bytes/second, not just flows?**
17. **Which claims are theorem-backed and which are empirical only?**
18. **Which guarantees still hold under the actual LSPR23 evidence?**

If those are answered before writing, the manuscript will be much easier to defend.

---

# 18. Suggested Stop Condition

The goal is not “zero possible reviewer questions.” That is impossible.

Stop experimenting once:

- all five P0 items are resolved;
- the two cheap A1 checks are done;
- the feedback robustness result is available;
- any failed experiment has been incorporated into the claim boundaries.

At that point:

\[
\boxed{
\text{freeze experiments permanently}
}
\]

and write.

---

# 19. My Current Priority Ranking

If time becomes tight, do them in exactly this order:

1. **Randomized/smoothed evidence**
2. **Restart/batching**
3. **Second dataset with true campaigns**
4. **Problem-space padding attack**
5. **Asymmetric aggregation**
6. **A1 near-neighbour/per-feature**
7. **Second feedback controller + wall-clock delays**
8. **Cross-window parameter transfer**
9. **Calibration contamination**
10. remaining appendix checks

The first two are particularly important because they are obvious **methodological escape hatches** a statistics reviewer may suggest immediately.

The third and fourth are particularly important for a **SaTML/security reviewer**.

---

# 20. Expected Paper Strength After Gap Closure

If the major results survive Items 1–5, the paper becomes substantially harder to reject on methodological grounds.

The final story would then be able to say:

> We did not merely observe a failure of one online FDR procedure with one discrete conformal construction. We tested the obvious statistical remedies (modern e-value procedures, smoothing/continuous evidence, restarting/batching), the obvious security abstraction remedy (coarser and true campaign-level grouping), and the obvious aggregation escape (asymmetric precommitted weighting). We then demonstrated that the remaining security tradeoffs and attack surfaces persist—or precisely characterized the conditions under which each remedy succeeds.

That would move the submission much closer to the strongest version of a SaTML main-track paper.

---

# 21. Immediate Next Action

The **next experiment I would start is randomized/smoothed conformal evidence**.

Reason:

The current record already acknowledges recent work showing that randomized smoothing can remove conformal resolution collapse. A reviewer will therefore ask about it immediately.

It has the highest probability of materially changing the scope of Contribution 1.

After that:

\[
\boxed{
\text{smoothing}
\rightarrow
\text{restart/batching}
\rightarrow
\text{second dataset}
\rightarrow
\text{problem-space attack}
\rightarrow
\text{asymmetric aggregation}
}
\]

Then close the lower-priority robustness items and start the manuscript.
