# SaTML 2027 Research Paper Review — Consolidated Feedback

**Paper:** *When Guarantees Go Silent: Feasibility and Attackability of Online Error Control for ML Intrusion Detection*  
**Target:** SaTML 2027, Main Track — Research Paper  
**Review basis:** the current 19-page draft, including the appendices, proofs, figures, attack-cost tables, robustness analyses, and the revisions that already addressed several earlier concerns.

---

## 1. Overall assessment

This is a **credible SaTML main-track submission**, not a speculative long shot. The paper has a clear venue fit: it studies the security and operational failure modes of a statistical trust layer around an ML intrusion detector, rather than proposing yet another detector. Its strongest idea is that a statistically valid detection-and-decision pipeline can still become operationally infeasible, and that the mechanisms introduced to make it usable create new attacker-facing surfaces.

The revised draft is significantly stronger than the earlier version. In particular, it now:

- correctly frames FDR as a property of the alert queue rather than a per-alert probability;
- states the exchangeability condition behind conformal validity;
- distinguishes **primary / guarantee windows** from the invalid 0.85 stress-test window;
- adds a fixed-denominator granularity metric (“alert blur”);
- gives a “known vs. established here” paragraph for the feasibility result;
- narrows the feasibility theorem to the specific structural procedure families it actually covers;
- fixes the wording of Proposition 1’s eventual-feasibility claim;
- clarifies that Route B for the padding theorem is a special-case argument rather than a second proof of the full quantitative result;
- separates the low-footprint padding attack from the high-volume ADDIS state attack;
- adds a controlled padding-dilution experiment on the shipped detector;
- explicitly admits that the Isolation Forest arm does not independently validate the attacks;
- presents the state attack as a structural controllability result rather than a stealthy practical attack.

These are meaningful improvements.

### Current subjective acceptance estimate

I would currently place the paper at approximately:

- **~35–45% acceptance probability if submitted essentially as it is now**
- **~45–55% if the remaining technical/framing issues are fixed carefully**
- **~55–65% if the paper also gets one strong additional validation experiment and a substantially improved related-work positioning**

My central estimate for the current draft is **around 40%**.

That estimate reflects a paper I would expect to receive a mixture of **Weak Accept and Weak Reject** reviews, rather than unanimous rejection or clear acceptance.

---

## 2. Reviewer-style scorecard

| Dimension | Assessment |
|---|---|
| Fit to SaTML | **Excellent** |
| Problem significance | **Strong** |
| Originality | **Moderate-to-strong, but needs better differentiation from recent related work** |
| Technical depth | **Strong** |
| Theoretical contribution | **Promising, but assumptions/scope need extremely precise presentation** |
| Empirical depth | **Strong within one dataset, limited in breadth** |
| Security realism | **Good for padding; structural rather than practical for ADDIS state attack** |
| Reproducibility | **Very strong** |
| Clarity | **Improved, still dense** |
| Main-track readiness | **Borderline / Weak Accept territory** |

---

# 3. Strongest aspects of the paper

## 3.1 The central thesis is genuinely appropriate for SaTML

The paper does not ask whether the underlying classifier is accurate. It asks whether the **composed statistical trust layer**

> detector → conformal evidence → aggregation → online controller → alert

is actually usable and robust once deployed in an adversarial environment.

That is a good SaTML question.

The paper’s best conceptual statement is essentially:

> **Validity of the statistical procedure is not enough; feasibility, semantic granularity, and adversarial manipulability are properties of the composed system.**

This gives the work a stronger identity than “online FDR applied to NIDS.”

---

## 3.2 The feasibility result is more interesting after the revised framing

The earlier risk was that reviewers would dismiss C1 as “bounded evidence eventually loses to a shrinking threshold.”

The new “Known vs. established here” framing improves this substantially. The contribution is not merely the elementary inequality; it is the structural classification:

- which families of online FDR procedures have the finite-feasibility behaviour;
- when the silent state is absorbing;
- the cold-start / first-rejection deadline;
- the calibration-size scaling required to maintain feasibility over a deployment horizon;
- why the usual “α-investing fixes α-death” intuition does not automatically save this particular setting;
- which procedures escape and how.

That is a much more defensible contribution.

---

## 3.3 The granularity section is substantially better now

The earlier version relied too heavily on episode recall while changing the episode definition as the grouping bucket changed.

The new fixed 5-minute atomic ground truth is a meaningful improvement.

The paper can now say:

- coarsening reduces the number of hypotheses and therefore buys feasibility;
- the denominator-independent cost is that an issued alert represents more atomic malicious units;
- “blur” increases from about 1 atomic unit to tens of units per alert.

That is much cleaner than claiming that moving-denominator episode recall alone proves a loss of resolution.

---

## 3.4 Surface A is a strong security result

The padding attack is probably the paper’s most convincing security result.

Important positives:

- it attacks the **decision layer**, not the detector;
- it does not require gradients or model access;
- it works by changing hypothesis composition;
- suppression costs are explicitly priced against the running controller level;
- the result exists in the primary valid windows, not only at the invalid stress window;
- four of five padding pools behave similarly;
- the black-box padding pool requires no detector access;
- the controlled experiment now confirms that 20,000 real benign-service flows produce zero detector fires and that the predicted dilution threshold is achieved exactly for all tested detections.

This substantially reduces the realism objection that existed in the first version.

---

## 3.5 The paper is unusually transparent about negative results and limitations

This is a genuine strength.

The draft openly reports that:

- one stress-test window does not carry valid e-values;
- the Isolation Forest does not detect anything;
- smoothing removes the hard floor but not reliable detections;
- restart changes the guarantee being offered;
- asymmetric weighting introduces a different attack surface;
- some groupings do not transfer across windows;
- the ADDIS state attack is enormous in traffic volume;
- there is only one live-fire dataset;
- five deployment windows are not five independent datasets.

This makes the manuscript more trustworthy.

---

## 3.6 Reproducibility is strong

The manuscript states that:

- procedure implementations are checked against literal implementations / identities;
- closed forms are numerically verified;
- measurement scripts carry tests;
- cached results and an executable notebook reproduce figures and tables;
- the raw third-party dataset can be regenerated through documented preprocessing.

This is above average for many conference submissions and should help in review.

---

# 4. Highest-priority remaining problems

These are the issues I would focus on before cosmetic editing.

---

## 4.1 The related-work positioning still needs a serious update

### Risk

The paper currently argues that prior work studies the detector or calibration while this paper targets the “decision layer after both.”

That distinction is useful, but it is currently too broad.

There is increasingly close work on **online conformal anomaly detection combined with online false-discovery control**, including recent work that directly combines conformal evidence, sequential anomaly decisions, and FDR-style control.

A reviewer familiar with this literature may react badly if the paper makes the field look emptier than it is.

### What to do

Add a short, explicit paragraph in Related Work with three categories:

1. **Online FDR for anomaly detection**
   - e.g. time-series anomaly-detection work using online FDR.

2. **Online / streaming conformal anomaly detection with FDR-style control**
   - explicitly include the closest recent conformal-FDR predecessor(s).

3. **This paper’s difference**
   - fixed finite calibration evidence interacting with long online horizons;
   - semantic aggregation into security alerting units;
   - adversarial control over group composition;
   - adversarial control over adaptive sequential state;
   - security-specific feasibility and attack-cost analysis.

### Recommended novelty wording

Avoid:

> “Prior work targets the detector or calibration; we are the first to target the decision layer.”

Prefer:

> “Prior work has combined online anomaly detection, conformal evidence, and false-discovery control. We study a different failure mode of the composed pipeline: how finite calibration resolution interacts with the sequential controller over security-scale horizons, how the aggregation required to make the controller feasible changes alert semantics, and how both aggregation and evidence-dependent controller state become adversarially manipulable.”

That is narrower and much harder to attack.

---

## 4.2 Group-level validity assumptions need to be stated much more carefully

This is one of the most technical risks in the paper.

You correctly state that the arithmetic mean of valid e-values is an e-value. However, a reviewer may ask:

> Are the individual flow-level e-values actually valid under the filtration / conditioning induced by grouping flows into episodes and then feeding those groups sequentially into an online procedure?

The paper currently moves relatively quickly from valid flow-level e-values to a valid group-level mean.

The issue is not the algebraic fact that means preserve the e-value expectation condition. The issue is whether the required validity is preserved **under the deployment filtration, adaptive grouping, temporal structure, and possible dependence between group formation and evidence**.

### What to add

Add a dedicated assumption paragraph in the system-model section.

For example:

> **Group-evidence validity assumption.** The grouping rule is fixed before deployment and depends only on metadata available independently of the detector scores used to construct the e-values. Under the null, each constituent e-value satisfies the required conditional e-value property with respect to the pre-group filtration. Therefore the pre-specified arithmetic mean remains a valid group e-value under arbitrary within-group dependence. If this conditional validity fails, the downstream online-FDR guarantee does not attach; the empirical validity diagnostics in Section IX-A evaluate this premise.

The exact statement must match the theorem you are relying on. Have someone with strong e-value / sequential-testing expertise verify it.

### Why this matters

If a reviewer believes the group e-values do not satisfy the form of validity required by the online procedures, that threatens a large part of the paper, not just one experiment.

This is therefore a **top-priority technical audit item**.

---

## 4.3 “Valid window” is stronger language than the empirical evidence supports

The paper currently calls 0.55, 0.62, etc. “valid conformal evidence” because their empirical benign firing ratios are around 1.07–3.79× nominal, while 0.85 is 50.9×.

The problem is that the expected number of firing benign examples is extremely small. In some windows you observe only one, two, or three events.

With counts that small, a ratio near one is not strong empirical evidence that exchangeability / conditional e-value validity is actually satisfied.

### Better wording

Instead of:

> “Four of five positions carry valid conformal evidence.”

Use something like:

> “Four positions show no statistically compelling evidence of the severe anti-conservatism observed at 0.85 and are treated as the guarantee-analysis windows under the stated exchangeability assumption.”

or:

> “At four positions the empirical firing counts are compatible with the nominal calibration rate at the resolution available in this dataset; 0.85 exhibits a clear violation.”

This separates:

- **the theoretical guarantee**, which follows under the assumption; from
- **the empirical diagnostic**, which has limited statistical resolution.

### Add uncertainty

Report either:

- exact binomial confidence intervals; or
- Poisson intervals for the number of firing benign flows.

This will prevent a statistics reviewer from saying that “1 observed event with expectation ≈1” does not prove validity.

---

## 4.4 There is an apparent table-consistency problem around infeasible configurations

Table VI describes negative-margin configurations as ones where:

> “the controller cannot run and recall/coverage are therefore 0.”

But some infeasible configurations in the table still show non-zero recall / flow coverage values.

That is confusing and looks like either:

- a genuine bug;
- a table-caption mistake;
- or metrics being computed under a different procedure/sequence than the margin used to mark feasibility.

### Fix

Every row must have one unambiguous interpretation.

For each configuration specify:

- which procedure;
- which spending sequence;
- which feasibility condition;
- whether the row is actually executed or shown counterfactually;
- which metric is set to zero when the procedure is infeasible.

If the margin is the LORD++/level-\(w_0\) feasibility margin while the recall uses e-LOND, then do **not** label the row simply “infeasible.” Say something like:

> “negative level-\(w_0\) margin; e-LOND may still fire because its cold-start coefficient is \(\alpha=2w_0\).”

This is exactly the type of small-looking inconsistency that can cause a reviewer to distrust many tables.

---

## 4.5 Re-check every attack-cost table for consistent threshold definitions

The draft distinguishes:

- the running controller threshold;
- a static \(T/w_0\) threshold;
- e-LOND thresholds;
- ADDIS’s capped level;
- per-alert padding costs;
- global state-manipulation costs.

This is good, but the manuscript has many cost numbers and they are easy to mix.

### What to audit

Create an internal spreadsheet with columns:

- attack / experiment;
- procedure;
- window;
- controller level used;
- threshold \(1/\alpha_t\);
- whether the level is running or static;
- whether prior suppressed alerts change later \(\alpha_t\);
- lower bound / upper bound / exact;
- group size;
- pad-pool mean evidence;
- resulting flow count;
- byte estimate;
- time span;
- rate.

Then verify every number in the abstract, body, figures, and tables against that sheet.

### Critical presentation rule

Whenever a number is a lower bound, state **why** next to it.

For example:

> “118 flows, a lower bound obtained by reading the controller level from the unperturbed trajectory; suppressing earlier detections would further reduce later levels.”

This prevents a reviewer from interpreting the number as a complete end-to-end adaptive attack simulation.

---

## 4.6 Do not claim that anti-conservative evidence automatically makes every silence result conservative

The manuscript says that because the 0.85 evidence is anti-conservative, silence / non-detection there is a lower bound.

That intuition is plausible, but it is safer to avoid a broad monotonicity claim unless it is actually proved for the grouped evidence and the procedure.

Higher null firing rates in aggregate do not necessarily imply **pointwise dominance** of all e-values or of the sequential path.

### Safer formulation

Say:

> “The severe anti-conservatism at 0.85 means the FDR guarantee does not attach. We therefore use this window only as a stress-test for mechanism and attack-cost measurements, not for guarantee-bearing conclusions.”

If you want the “conservative for detection” statement, prove the relevant monotonicity under the exact perturbation model.

---

# 5. Experimental weaknesses that still limit acceptance probability

---

## 5.1 Single-dataset scope remains the biggest empirical weakness

The paper uses a strong dataset: a very large live-fire exercise with chronological ordering.

But it is still one exercise.

Five windows are not independent datasets. They share:

- the same environment;
- the same red team;
- the same instrumentation;
- the same labelling process;
- many of the same distributional quirks.

The paper acknowledges this, which is good, but it is still the most obvious Weak Reject argument.

### Highest-value additional experiment

If you can add **one competent second detector that actually detects attacks**, it would help considerably.

Best option:

- a detector using endpoint / host-conditioned features or host reputation.

Why this is ideal:

1. it tests the boundary of the padding attack;
2. it addresses the paper’s own limitation;
3. it gives you a genuinely different detector rather than another generic flow classifier;
4. a partial failure would still be scientifically useful.

For example:

> “Against host-independent flow features, the attack transfers exactly. Against host-conditioned features, padding becomes X× more expensive / fails under condition Y.”

That is stronger than simply adding another random forest.

---

## 5.2 A second dataset would be valuable, but only if it supports the semantic question

A second NIDS dataset is not automatically useful.

If the dataset lacks:

- chronological order;
- complete negatives;
- meaningful episode/campaign identifiers;
- realistic attack grouping;

then it may add noise rather than evidence.

Your current explanation that you screened many public datasets is defensible.

If no second dataset satisfies the requirements, retain that limitation explicitly.

---

## 5.3 Isolation Forest currently adds little beyond one conceptual point

The Isolation Forest demonstrates:

> identical feasibility margin does not imply detection ability.

That is valid.

But it does not validate the attacks because it detects nothing.

Keep it only as a compact **necessity-vs-sufficiency sanity check**. Do not market “two detectors” as broad attack validation.

The revised draft already acknowledges this; keep that honesty.

---

# 6. Granularity result: strong improvement, but refine the interpretation

The fixed atomic ground truth solves the denominator problem, but the new metric should be described carefully.

“Alert blur” measures:

> how many fixed five-minute malicious atomic units are covered by one issued coarser alert.

That is intuitively useful as a localization metric.

However, coarser grouping also increases fixed atomic coverage. Therefore the result is not simply:

> “coarsening loses information.”

It is a tradeoff:

- broader coverage;
- fewer hypotheses;
- greater feasibility;
- worse localization / larger semantic scope per alert.

### Better claim

> “Coarsening buys feasibility and wider atomic coverage, but each alert localizes the attack less precisely: the number of fixed atomic units represented by one alert grows from 1 to tens.”

This is more balanced and more operationally meaningful.

---

# 7. Theoretical presentation improvements

---

## 7.1 Define “feasible over a horizon” precisely

The paper uses several related concepts:

- a step at which rejection is possible;
- a finite last feasible time;
- the absorbing silent state;
- cold-start feasibility;
- the ability to reject at every time \(t \le T\);
- deployment-wide feasibility.

These are not identical.

Add explicit definitions:

### Step feasibility

A hypothesis \(t\) is **evidence-feasible** if the maximum possible evidence \(M\) can cross the offered rejection threshold.

### Cold-start horizon feasibility

A procedure is **cold-start feasible through \(T\)** if a rejection would be possible at every step \(t \le T\) on a rejection-free prefix.

### Absorbing silence

A state is **absorbing with respect to future evidence** if, after entering it on a rejection-free trajectory, no later admissible observation can produce a rejection under the stated procedure.

This makes Corollary 3 easier to interpret.

---

## 7.2 Keep the “elementary core, nontrivial system consequence” framing

Do not oversell the inequality itself.

A good tone is:

> “The core inequality is elementary. The contribution is the structural classification, security-scale calibration consequence, and the interaction with the escape mechanisms.”

That makes the paper sound more mature, not less novel.

---

## 7.3 Theorem 6 is potentially one of the strongest results — make its assumptions impossible to misread

The theorem depends on:

- symmetric e-merging families;
- variable arity;
- attainment of a threshold \(\tau>1\);
- finite nonnegative inputs;
- padding by zero-evidence values.

Spell out that “padding” corresponds to attacker-added flows whose e-value is zero under the two-point construction.

Also explicitly distinguish:

- a **valid e-merging family at arbitrary arity**;
- a capped rule valid only under a pre-committed maximum group size;
- asymmetric position-weighted rules.

The theorem is compelling when the model class is crisp.

---

## 7.4 The generalization from ADDIS should be narrowed

The paper currently suggests something close to:

> any procedure escaping α-death by conditioning its spending index on observed evidence exposes that property to the adversary.

Conceptually good, but too universal unless formally proved.

Prefer:

> “The ADDIS example illustrates a broader security principle: when the state variable controlling future statistical decisions is a deterministic function of attacker-influenced evidence, that state variable must be included in the threat model.”

That generalizes the lesson without claiming a theorem for every adaptive procedure.

---

# 8. Operational baseline section: useful but secondary

The matched-operating-point analysis and analyst-feedback controllers are interesting, but they are not the core contribution.

Potential reviewer reaction:

> “The paper is already doing feasibility theory, granularity, merging impossibility, padding, asymmetric weights, controller-state manipulation, calibration contamination, matched thresholds, feedback controllers, smoothing, restart, and data-quality auditing.”

That is a lot.

### Recommendation

If space or narrative clarity becomes a problem:

**Keep in main body**
- matched operating point at the primary window, because it translates statistical behaviour into operator cost;
- one concise feedback result.

**Move / compress**
- full feedback-controller comparison;
- extensive q/γ sweep;
- secondary negative results.

The main narrative should remain:

1. feasibility;
2. aggregation needed to recover operability;
3. aggregation/adaptivity become attack surfaces.

---

# 9. Abstract improvements

The revised abstract is much better, but still very dense.

It currently contains:

- feasibility theorem;
- calibration scaling;
- 16.4M-flow scale;
- granularity;
- atomic ground truth;
- padding theorem;
- attack cost;
- valid window qualification;
- ADDIS state attack;
- 37.5× traffic;
- five windows;
- two detectors.

### Recommendation

Remove 20–25% of the numerical detail.

A stronger abstract structure:

1. **Problem:** valid statistical trust layers may be unusable/adversarially fragile at security scale.
2. **Feasibility result:** finite evidence + uninterrupted online spending gives a finite discovery horizon for important procedure classes.
3. **Systems consequence:** aggregation restores feasibility but coarsens alert semantics.
4. **Security consequence:** symmetric aggregation is padding-vulnerable; evidence-dependent controller state is attacker-influenced.
5. **Evidence:** large live-fire dataset, chronological evaluation, valid-window attack cost.
6. **Takeaway:** trustworthy guarantees must be evaluated at the composed-system level.

Use only 2–3 headline numbers.

---

# 10. Writing and terminology

The draft is technically strong but reads densely.

Common patterns to reduce:

- “the quantity that creates the problem is the quantity that prices the solution” repeated in different forms;
- long sentences with four or five independent claims;
- too many parenthetical qualifications inside theorem/result sentences;
- moving repeatedly between “validity,” “guarantee,” “feasibility,” “power,” “detection,” “resolution,” and “coverage” without reminding the reader they are different.

### Terminology table worth adding

| Term | Meaning |
|---|---|
| Statistical validity | The assumptions required for the stated FDR/e-value guarantee |
| Feasibility | Whether any admissible evidence can cross the controller threshold |
| Detection power | Whether malicious episodes actually generate sufficient evidence |
| Episode recall | Recall under the current grouping definition |
| Atomic coverage | Coverage of a fixed fine-grained attack-unit denominator |
| Alert blur | Number of fixed atomic units represented by one alert |
| Padding cost | Flows needed to suppress a current alert |
| State-attack cost | Flows/precursors needed to manipulate sequential controller state |

This would help interdisciplinary SaTML reviewers.

---

# 11. LLM-usage disclosure and submission compliance

This needs to be treated as a submission-compliance item, not just an ethics paragraph.

The current disclosure is much better because it:

- states the use of an LLM;
- states implementation/analysis and drafting roles;
- says authors reviewed/edited the result;
- accepts responsibility;
- describes verification and testing.

Before submission, compare the section line-by-line with the **current SaTML 2027 mandatory wording/checklist**.

Where the venue asks for specific information, include it literally.

Possible items to verify:

- exact required editorial-use sentence;
- which model/system was used;
- why use was necessary;
- whether prompts contained sensitive/private information;
- how queries were minimized;
- computational/environmental disclosure if requested;
- confirmation that citations were manually verified.

Do not improvise here. Follow the current CFP/checklist exactly.

---

# 12. Citation audit

Because the paper explicitly discloses LLM assistance, reviewers may scrutinize the bibliography unusually closely.

Before submission, manually verify every reference:

- title;
- authors;
- venue;
- year;
- volume;
- pages;
- arXiv identifier;
- theorem/proposition numbers used in the text.

Pay special attention to:

- e-merging domination results;
- e-GAI equivalence used in Proposition 1;
- calibration-conditional results;
- recent 2025/2026 papers;
- any arXiv work not yet formally published.

A single incorrect theorem attribution can damage confidence disproportionately.

---

# 13. What different reviewers may say

## Theory / statistics reviewer

### Likely positives
- formal results;
- explicit structural procedure classes;
- exact scaling;
- proof appendix;
- e-merging impossibility result.

### Likely concerns
- conditional/group-level e-value validity;
- definition of horizon feasibility;
- empirical claims of “valid” windows based on tiny counts;
- novelty relative to α-death / online FDR literature.

### Target response
Make assumptions and theorem scope extremely precise and improve related-work positioning.

---

## Security reviewer

### Likely positives
- attacks target the trust layer rather than the classifier;
- black-box padding;
- operational flow/byte/rate cost;
- explicit threat model;
- controlled padding-dilution experiment.

### Likely concerns
- one detector actually validates the attack;
- one dataset;
- ADDIS global state attack is extremely conspicuous;
- victim-service traffic realism.

### Target response
Add a host-conditioned detector/testbed boundary experiment and keep Surface B framed as structural controllability.

---

## Applied ML reviewer

### Likely positives
- 16M+ flows;
- chronological protocol;
- no random split leakage;
- detailed negative results;
- reproducibility.

### Likely concerns
- only one exercise;
- moving group definitions;
- many metrics;
- no novel detector.

### Target response
Emphasize that detector novelty is intentionally not the contribution and retain the fixed atomic-unit metric.

---

# 14. Ranked revision plan

## Tier 1 — Must fix before submission

### 1. Audit the group-level e-value validity assumptions
This is the most important theoretical issue.

### 2. Fix all table/caption inconsistencies
Especially rows marked infeasible while reporting non-zero outcomes.

### 3. Rewrite “valid window” language
Separate theoretical assumptions from sparse empirical diagnostics.

### 4. Update the closest related work
Explicitly discuss recent online conformal anomaly detection + FDR work.

### 5. Audit every attack-cost number and label
Running vs. static threshold, lower bound vs. exact, and procedure-specific levels.

### 6. Narrow broad generalizations
Especially claims that extend the ADDIS phenomenon to arbitrary adaptive procedures.

---

## Tier 2 — Strongly recommended

### 7. Add one competent second detector that actually detects
Preferably host-conditioned or endpoint-aware.

### 8. Add uncertainty intervals to calibration-validity diagnostics
Exact binomial or Poisson confidence intervals.

### 9. Compress secondary baselines
Keep the main story focused.

### 10. Simplify the abstract
Fewer numbers, clearer three-step narrative.

---

## Tier 3 — Nice to have

### 11. Add a second dataset if an actually suitable one exists
Do not add an inappropriate benchmark merely to claim dataset count.

### 12. Add a terminology/assumptions box
Useful for reviewers coming from security rather than sequential statistics.

### 13. Improve figures for “reviewer scanability”
Each main figure should answer one question at a glance.

---

# 15. The single additional experiment I would choose

If only one new experimental contribution can be added:

## Host-conditioned detector / testbed boundary experiment

Build or train a competent detector that uses:

- host identity;
- host history;
- endpoint reputation;
- per-host baselines;
- or similar contextual features.

Then repeat the padding experiment.

Questions to answer:

1. Does ordinary victim-service traffic still score benign?
2. Does padding still dilute the group evidence?
3. If yes, how does the cost change?
4. If no, which specific feature breaks transfer?
5. Does a different aggregation unit recreate the attack?
6. Does feasibility still exhibit the same statistical horizon?

This experiment directly targets the limitation the paper already identifies and would make the security contribution substantially more convincing.

---

# 16. Suggested final contribution framing

I would frame the submission around the following three claims.

### C1 — Feasibility is a separate property from validity

For important classes of online error-control procedures, finite-resolution conformal evidence creates a finite cold-start feasibility horizon under uninterrupted control. The result gives an explicit calibration/horizon scaling and classifies mechanisms that escape it.

### C2 — Restoring feasibility changes the semantics of the security decision

Coarsening reduces the hypothesis count and therefore the calibration requirement, but alerts become less local: one alert represents increasingly many fixed fine-grained attack units. Restart is another escape but changes how the guarantee composes.

### C3 — The mechanisms that make the system operational are attacker-facing

The aggregation required by C2 is vulnerable to padding under symmetric e-merging; asymmetric pre-committed weighting trades padding for front-loading. Evidence-adaptive controller state is also attacker-influenced, demonstrated concretely for ADDIS.

### Final message

> **Trust guarantees should be evaluated as properties of the entire detection-and-decision system, including feasibility, semantic unit, aggregation, sequential state, and adversarial control—not only as validity properties of the statistical procedure.**

That is the paper SaTML is most likely to accept.

---

# 17. Updated acceptance judgement

### If submitted today

**Borderline / Weak Accept–Weak Reject**

Approximate subjective odds:

**35–45%**

The paper is clearly above “easy reject” level, but there are enough technical and generality questions that one skeptical reviewer could pull the discussion toward rejection.

### After Tier-1 fixes

**Competitive Weak Accept**

Approximate subjective odds:

**45–55%**

### After Tier-1 fixes + a good host-conditioned validation experiment + stronger related-work positioning

**Solidly competitive SaTML submission**

Approximate subjective odds:

**55–65%**

I would not spend the remaining effort inventing another major theorem. The paper already has enough technical content. The highest-value work now is to remove reasons reviewers can distrust or discount the existing contributions.

---

# 18. Submission checklist

Before final upload:

- [ ] Group-level e-value validity statement checked by a sequential-testing expert
- [ ] Every theorem assumption appears in the main text
- [ ] “Valid window” wording replaced with assumption-aware language
- [ ] Confidence intervals added to benign firing diagnostics
- [ ] Closest online conformal-FDR work explicitly cited and contrasted
- [ ] Table VI feasibility labels reconciled with non-zero metrics
- [ ] Every attack cost checked against a common calculation sheet
- [ ] Running vs. static thresholds labelled consistently
- [ ] All lower bounds explicitly labelled
- [ ] ADDIS generalization narrowed to a security principle unless formally proved
- [ ] Isolation Forest described only as a feasibility/sufficiency sanity check
- [ ] Host-conditioned detector/testbed experiment added if feasible
- [ ] Abstract reduced to 2–3 headline numbers
- [ ] Main body does not rely on appendices for central claims
- [ ] Every bibliography entry manually checked
- [ ] SaTML 2027 LLM disclosure wording checked against current checklist
- [ ] Anonymous artifact repository tested from a clean environment
- [ ] Reproduction notebook executed once end-to-end from raw data
- [ ] All table/figure numbers cross-checked with manuscript references
- [ ] Final paper read once by a statistics-oriented reviewer
- [ ] Final paper read once by a security-oriented reviewer
