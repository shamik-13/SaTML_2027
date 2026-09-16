# Trustworthy Alerting, Not Trustworthy Scores
## Incident-Level Online Error Control for ML Intrusion Detection — and How to Attack It

### Revised research plan for IEEE SaTML 2027 (main track, research paper)

**Revision note.** This supersedes `19_fdr_trustworthy_ids_research_idea.md`. The original plan was scientifically sound but positioned as a benchmark study whose premise, method, and three headline findings are all already published. Section 0 records exactly what changed and why. Everything else is the plan as it should now be executed.

**Hard deadlines.** SaTML 2027: mandatory abstract registration **Tue 22 Sep 2026**, paper **Tue 29 Sep 2026**, 11:59pm AoE. 12 pages of body text, `\documentclass[conference]{IEEEtran}` at 10pt, unlimited references and appendices. (SaTML 2026 closed 24 Sep 2025.) Today is 25 Aug 2026 — this is a **five-week** plan, and the scope below is cut to fit it.

---

# 0. What changed from v1, and why

| v1 position | Problem | v2 position |
|---|---|---|
| "SOCs consume alerts, not AUROC — FDP is the right objective" as the novel framing | This is Axelsson's base-rate fallacy argument (CCS'99 / TISSEC'00). 27 years old. | Cited as the motivating classic in the first paragraph. Novelty moved elsewhere. |
| "Can online FDR handle rare alternatives and serial dependence?" as RQ2/RQ3 | Answered by Rebjock et al. (AISTATS 2022) for time-series anomaly detection — they had to *propose new rules* because established ones fail. | Treated as **known background**. We inherit their result and build on it rather than rediscovering it. |
| "conformal p-values → online FDR → alerts" as the novel pipeline | Exists: C-PP-COAD (2025) does conformal + LORD + decaying-memory FDR. Conformal calibration in security ML: Transcend (USENIX'17), Transcendent (USENIX'22), FIRCE / FADES (2026). | Pipeline is the **substrate**, not the contribution. |
| §16.1 prevalence-regime stress test as a key differentiator | CALIBURN (2026) is streaming NIDS with operator-specified alert budgets under conformal risk control, and *its central claimed finding is regime-dependence on attack prevalence*. | Retained but demoted; positioned explicitly as the FDR analogue of CALIBURN's FPR result, with CALIBURN as the primary baseline to differentiate from. |
| §14 event- vs incident-level as an optional add-on | This is actually a **measurement-validity argument that invalidates the naive formulation**. Incidents span 1 to 10^5 events, so event-level FDP is dominated by whichever attack is most voluminous, and an attacker controls the denominator. | **Promoted to C1.** Incident-level online error control via conformal e-value averaging is the paper's methodological spine. |
| §3.7 adaptive attackers, one paragraph | Best SaTML fit in the whole document, and genuinely unclaimed: existing adversarial-FDR work covers batch BH (Chen et al. 2025) and *offline* conformal novelty detection under test-time perturbation (2025) — nobody has attacked online α-wealth dynamics or a rolling calibration buffer. | **Promoted to C3**, with two concrete attacks and defenses. |
| §18 "evaluate established adaptation strategies" | An undirected fishing expedition across six mechanisms. | Replaced by a principled choice: e-value procedures valid under arbitrary dependence, plus SupLORD for tail control. The mitigation set is derived, not swept. |
| Baselines = 5 threshold rules | Missing the baseline that probably wins: a feedback controller on delayed analyst dispositions, which needs no multiple-testing theory at all. | Added as **B6**, and the label-latency crossover becomes a headline result. |
| Comparison of "LORD at q=0.05" vs "threshold at 0.5" | Not a comparison. Given a fixed score function every alerting rule is a threshold sequence; these are two arbitrary points on one ROC. | **Protocol invariant P1**: no unmatched comparisons. Everything is reported at matched analyst budget, at matched realized FDP, or as a full Pareto frontier. |
| CIC-IDS2018 as primary dataset, labels described as "cleaner than the real world" | Measured label corruption is 7.53% on CSE-CIC-IDS2018 (>75% for some attack classes) and 6.67% on CIC-IDS2017. You cannot measure whether realized FDP is 0.04 or 0.09 against a q=0.05 target when ground truth is 7.5% wrong. Labels are not cleaner — they are partly *wrong*, which is worse for this specific metric. | Corrected/regenerated releases; FDP reported as an **identified interval** under label-error rate; primary claims shifted to *temporal stability* of FDP, which survives a roughly constant label bias; plus a manual label audit. |
| §3.4 asserts P(attack) << 1% and §16.1 sweeps prevalence by subsampling | Actual benchmark prevalences: CIC-IDS2017 ~22%, UNSW-NB15 ~64%, LSPR23 ~10%. Reaching 0.01% requires subsampling, which destroys the temporal dependence that is the other central claim. **You cannot get realistic base rates and realistic dependence from the same benchmark.** | Confronted directly in §7.3 with two orthogonal, non-conflated axes: incident-preserving attack subsampling (prevalence) and order permutation at fixed p-value multiset (dependence). |
| Not present | The conformal p-value floor `1/(|C|+1)` interacts with α-wealth decay to make the detector **permanently unable to alert** while reporting perfect FDR control. | **New: Proposition 1 + C2**, with the randomization/derandomization tension it forces. |
| 4 detectors × 6 procedures × 6 baselines × 6 datasets × 5 prevalences × 6 stress axes | A three-paper program in a 12-page limit. | Cut ~60%: 2 detectors, 5 procedures, 6 baselines, 3 datasets, 2 stress axes done properly. §12 records exactly what was cut. |

---

# 1. One-sentence pitch

> Attaching an online false-discovery guarantee to an ML intrusion detector is not enough to make its alert stream trustworthy: the guarantee is stated over the wrong unit (events, not incidents), it can silently degrade into a detector that provably cannot alert at all, and the standard fix for distribution drift — rolling recalibration — hands an attacker a lever to suppress detection of their own campaign.

---

# 2. Core idea

Axelsson showed in 1999 that the operationally binding quantity for intrusion detection is `P(intrusion | alarm)` — equivalently `1 − FDP` — not the false-positive rate, and that the base rate makes this brutally hard. Twenty-seven years later, ML IDS papers still report AUROC, F1 and FPR.

The modern statistical toolkit for `1 − FDP` exists: conformal calibration turns a score into valid evidence, and online multiple-testing procedures turn a stream of evidence into a rejection sequence with a false-discovery guarantee. The pipeline is uncontroversial:

```text
network event / SIEM alert
      ↓
ML detector or existing IDS
      ↓
anomaly / attack score
      ↓
conformal calibration
      ↓
p-value or e-value
      ↓
online error-control procedure
      ↓
SOC alert
```

This paper does **not** ask whether that pipeline can be built (it can, and has been, in adjacent domains). It asks the three questions that decide whether the resulting guarantee means anything to a SOC:

1. **Is the guarantee stated over the right unit?** (No. §5)
2. **Can the guarantee be satisfied vacuously, or degenerate into structural silence?** (Yes. §6)
3. **Is the guarantee robust to an adversary who knows it is there?** (No. §9)

---

# 3. Positioning against the closest prior work

This table goes in the paper, roughly as-is. Reviewers will look for exactly this.

| Work | Setting | Evidence | Error notion | Unit | Online | Adversary | Delta to ours |
|---|---|---|---|---|---|---|---|
| Axelsson '99/'00 | IDS, analytical | — | `P(I\|A)` | event | — | — | Motivation; no procedure, no experiments |
| Bates et al. '23 (Ann. Stat.) | outlier testing | conformal p | FDR (BH) | item | ✗ | ✗ | Offline; establishes PRDS, which BH needs and LORD does not have |
| Marandon et al. (AdaDetect) | novelty detection | conformal p | FDR | item | ✗ | ✗ | Offline, batch |
| Bashari et al. '23 | novelty detection | conformal **e** | FDR | item | ✗ | ✗ | Offline; source of our e-value primitive |
| Rebjock et al. '22 (AISTATS) | time-series AD | p | online FDR | timestep | ✓ | ✗ | Not security; **already solves** rare-alternative + serial-dependence power loss |
| C-PP-COAD '25 | healthcare, O-RAN | conformal p | decaying-memory FDR | item | ✓ | ✗ | Same pipeline, non-security domain, event-level only |
| Transcend '17 / Transcendent '22 | malware, security | conformal p | rejection / drift | sample | ✓ | ✗ | Conformal *for drift detection*, no multiple-testing correction |
| FIRCE / FADES '26 | NIDS, security | conformal p | drift signal | flow | ✓ | ✗ | Rolling calibration + drift-triggered retraining; **no FDR control** |
| **CALIBURN '26** | **streaming NIDS** | conformal | **conformal risk control (FPR budget)** | flow | ✓ | ✗ | **Closest neighbour.** Explicitly applies *no multiple-testing correction*; marginal FPR bounds only; claims prevalence-regime dependence |
| Chen et al. '25 | multiple testing | p | FDR | test | ✗ | ✓ | Attacks **batch BH** via test-score perturbation |
| Adv. conformal novelty det. '25 | novelty detection | conformal p | FDR | item | ✗ | ✓ | Attacks **offline** AdaDetect/Bates via test-time evasion |
| **This paper** | **NIDS + SIEM alerts** | **conformal e** | **online FDR/FDX** | **incident** | **✓** | **✓ (α-wealth drain, calibration poisoning)** | — |

The narrow honest gap: online *multiple-testing* control on security alert streams is unclaimed, because CALIBURN did the FPR version. But "the FDR version of CALIBURN using Rebjock's rules" is a workshop paper. C1–C3 below are what make it a main-track paper.

---

# 4. Contributions

## C1 — Event-level false-discovery control is the wrong objective for security streams, and incident-level control is achievable

We show event-level FDP is a *degenerate* measurement on security telemetry, then give a construction that fixes it: per-event **conformal e-values**, averaged within incidents (valid under arbitrary dependence, by linearity of expectation), fed to an online e-value procedure. The within-incident dependence problem — the hardest obstacle in the v1 plan — dissolves, because averaging e-values requires no dependence assumption whatsoever.

## C2 — Online FDR control on long, sparse security streams can degenerate into provable structural silence

The conformal p-value floor interacts with α-wealth decay so that, after a sufficiently long rejection drought, **no input can be rejected regardless of how anomalous it is**, while the procedure continues to report perfect FDR control. We state the condition (Prop. 1), measure how often real streams enter it, and show the escape routes are both unpalatable: randomized alerting (a SOC will not accept coin-flip alerts) or derandomization via e-values (which reintroduces conservativeness).

## C3 — The standard drift fix is an attack surface

Two attacks on the alerting layer, not the detector: **α-wealth exhaustion** (drain the procedure's testing budget with borderline-benign traffic, then attack through the silence) and **rolling-calibration poisoning** (shift the benign score quantiles so the real campaign's evidence is no longer extreme). Rolling recalibration — the recommended mitigation for drift in Transcendent, FIRCE and our own §8 — is precisely what makes attack 2 possible. Defenses: arbitrary-dependence e-value procedures, trimmed-quantile calibration, wealth floors, calibration provenance restriction.

## C4 — A label-latency crossover that tells practitioners which mechanism to use

Against a feedback controller driven by delayed analyst dispositions, we locate the label latency `L*` below which multiple-testing machinery is unnecessary and above which it is the only option. This is the operational deliverable and it is what makes the negative results in C2–C3 actionable rather than merely discouraging.

---

# 5. C1: the unit-of-hypothesis problem

## 5.1 Why event-level FDP is degenerate

Let incident `j` comprise `n_j` malicious events. On real telemetry `n_j` ranges over four to five orders of magnitude: a single-packet exploit attempt has `n_j = 1`; a volumetric DDoS has `n_j ~ 10^5`.

Three consequences, each of which alone should disqualify event-level FDP as a headline metric:

1. **Domination.** `FDP_t` is controlled by whichever incident is most voluminous. Alert confidently on one DDoS and event-level FDP collapses toward zero while every low-volume incident is missed. The metric rewards exactly the detections a SOC needs least.
2. **Adversarial denominator.** `FDP_t = V_t / (R_t ∨ 1)`. An attacker who generates easily-detected high-volume noise inflates `R_t` with true discoveries, buying FDP headroom that the procedure will then spend on false ones.
3. **Redundancy.** Ten thousand rejections from one campaign are one unit of analyst value. Averaging error over them is averaging over a quantity that does not correspond to any decision anyone makes.

**Sanity check that must appear in the paper:** report `n_j` distribution per dataset, and report event-level FDP with and without the single largest incident. If those two numbers differ by an order of magnitude, C1 is established empirically in one figure.

## 5.2 Incident construction

Incidents must be defined *without* using labels at decision time. Three definitions, reported side by side, because the choice is a confound:

- **D1 — annotation-based.** Dataset-provided attack scenario / campaign IDs. Available in AIT-ADS (multi-step scenarios) and LSPR23. Ground truth, but not deployable.
- **D2 — provenance-based.** Group by `(src, dst-service, attack-technique)` within a session-gap timeout `Δ`. Deployable; sensitive to `Δ`, so sweep `Δ ∈ {60s, 300s, 1800s}`.
- **D3 — alert-signature-based.** For AIT-ADS: group by detector signature + host + window. This is what a real SIEM correlation rule does.

Evaluate under all three. If conclusions flip across D1–D3, that is itself a finding worth a paragraph.

## 5.3 The construction

**Primitive.** Per-event conformal e-value `e_t` from a benign calibration set `C` (Bashari et al. 2023 construction; verify the exact form against the paper before implementing). Requirement: `E[e_t] ≤ 1` under the null that `x_t` is benign and exchangeable with `C`.

**Incident aggregation.** For incident `j` with member events `S_j`:

$$E_j = \frac{1}{|S_j|}\sum_{t \in S_j} e_t$$

`E_j` is a valid e-value under **arbitrary dependence** among `{e_t}`, by linearity of expectation alone. No exchangeability, no PRDS, no independence, no mixing condition. This is the technical heart of the paper and the reason to use e-values rather than p-values.

**Online control.** Feed `E_1, E_2, ...` (in order of incident *first-alert opportunity*, not incident start, to preserve causality) to e-LOND / Ue-LOND for FDR control under arbitrary dependence, with e-BH as the offline retrospective reference.

**Causality constraint (easy to get wrong).** `E_j` cannot be computed at incident onset — it requires the incident's events. Two variants, both reported:
- **Anytime-valid variant:** running mean over events seen so far, tested at every step. Detection latency preserved; requires the running mean to remain a valid e-value at each stopping time (check: use a supermartingale construction, or apply a union-bound/anytime-valid wrapper — **this is the one piece of the design that needs a proof, do it in week 3**).
- **Fixed-window variant:** aggregate over a `W`-second window after first event above a trigger. Sacrifices latency for simplicity. Report time-to-first-detection so the cost is visible.

If the anytime-valid variant does not work out cleanly, the fixed-window variant is sufficient for the paper; say so rather than overclaiming.

---

# 6. C2: structural silence

## 6.1 The mechanism

Deterministic conformal p-values from calibration set `C`:

$$p_t = \frac{1 + \#\{i \in C : s_i \geq s_t\}}{|C| + 1}, \qquad p_t \geq \frac{1}{|C|+1} \ \ \text{always}.$$

Online FDR procedures in the LORD family reject when `p_t ≤ α_t`, where `α_t` is drawn from an α-wealth process. For any summable sequence `{γ_t}` (required for the guarantee; Javanmard & Montanari use `γ_t ∝ 1/(t log² t)`), during a rejection drought the assigned level decays as `α_t ≈ w_0 γ_t → 0`.

**Proposition 1 (claim — prove and verify in week 1).** With deterministic conformal p-values from a fixed calibration set `C`, any LORD-family procedure with summable `{γ_t}` enters a state after a finite rejection-free interval in which `α_t < 1/(|C|+1)`, and therefore **cannot reject any hypothesis regardless of the observed score**. Sustaining the ability to alert through a drought of length `T` requires

$$|C| \gtrsim \frac{1}{w_0\,\gamma_T} \sim T \log^2 T,$$

i.e. calibration-set size must grow superlinearly in stream length.

*Proof sketch:* immediate from `p_t ≥ 1/(|C|+1)`, `α_t ≤ w_0 γ_t` during a drought, and `γ_t → 0`. The content is the rate and the empirical frequency, not the existence.

*Status:* the existence argument is elementary and I am confident in it; the exact rate depends on the specific wealth recursion of each procedure (LORD++ vs SAFFRON vs ADDIS differ) and must be derived per-procedure. Verify numerically before claiming.

## 6.2 Why this matters and why it is not a footnote

Under prevalence `10^-4` on a stream of `10^6`–`10^7` flows — the regime the security motivation demands — droughts are the normal state, not the exception. So a system can hold `FDR ≤ 0.05` perfectly while being, for long stretches, **incapable of raising any alarm**. A detector that provably cannot detect is a trustworthiness failure of a kind classifier metrics cannot express, and it is caused by the guarantee itself.

## 6.3 New metric

**Structural silence rate:** the fraction of stream time during which `α_t < min_t p_t` is attainable — i.e. the procedure cannot reject *any* input. Cheap to compute, novel, and it will produce the paper's most quotable number.

## 6.4 The escape routes and why both cost something

- **Randomized (smoothed) conformal p-values.** Break ties with `U ~ Unif(0,1)`; the p-value becomes exactly uniform and has no floor. But alert/no-alert then depends on a coin flip. No SOC will accept "we did not alert on that because the RNG said so", and it is unauditable in an incident post-mortem. Worth stating plainly — it is an operational trust argument, which is on-topic for SaTML.
- **Growing calibration set.** Restores rejection capability but directly worsens the drift problem: an ever-growing window of benign traffic becomes ever staler. Prop. 1 and drift pull in opposite directions. Quantify the tension.
- **Conformal e-values / derandomization.** The principled route (Bashari et al.), and it composes with C1. Costs power. Measure it.

---

# 7. Evaluation protocol

## 7.1 Protocol invariant P1 — no unmatched comparisons

**Rule, enforced everywhere:** given a fixed score function, every alerting rule is a threshold sequence. Comparing "LORD at `q=0.05`" against "`s_t > 0.5`" is not a comparison; it is two arbitrary points on one ROC. Therefore every headline result is reported in one of three forms:

- **(M1) Matched analyst budget.** Fix `B` alerts/day. Report recall, incident recall, TTD, realized FDP for every method.
- **(M2) Matched realized FDP.** Tune every method to the same *achieved* FDP. Report recall.
- **(M3) Pareto frontier.** Sweep each method's own knob; plot recall (and incident recall) vs realized FDP. A method is better only if its frontier dominates.

Any claim not expressible in M1/M2/M3 does not go in the paper.

## 7.2 Chronological splits

Train → calibrate → stream, strictly ordered, no future information at decision time. Follow TESSERACT's temporal constraints and cite them. Report per-day and per-week breakdowns; a single aggregate FDP over the whole stream hides exactly the instability the paper is about.

## 7.3 The prevalence / dependence tension, handled honestly

Benchmark prevalences are nowhere near the motivating regime: CIC-IDS2017 ≈ 22%, UNSW-NB15 ≈ 64%, LSPR23 ≈ 10% (1.6M malicious of 16M flows). Reaching 0.01% requires subsampling, and naive subsampling destroys the dependence structure. Two **orthogonal, never-conflated** axes:

**Axis A — prevalence (incident-preserving).** Remove *whole incidents*, never individual flows, and never subsample benign traffic. Preserves benign temporal structure and all within-incident dependence exactly. Sweep `π ∈ {0.01%, 0.1%, 1%, native}`. State explicitly that low-`π` points are constructed, and that the benign process is untouched.

**Axis B — dependence (order permutation at fixed evidence multiset).** Keep `π` fixed and *relocate whole incidents* along the timeline: uniformly spread vs. clustered bursts. The multiset of per-event p/e-values is **identical** across conditions — only their arrival order changes. Therefore any change in realized FDP is attributable to dependence alone, with zero confound from the marginal score distribution. This is a clean, cheap, and (as far as I can tell) unused ablation design; it is the strongest single experiment in the plan.

Drop the following v1 stress axes for space: benign anomaly bursts (fold into Axis B as one condition), calibration age (fold into the drift experiment as 3 points, not 5), model type (2 detectors only).

## 7.4 Label noise — the identification problem

Measured corruption: **7.53%** on CSE-CIC-IDS2018, **6.67%** on CIC-IDS2017, with some attack classes above 75% (Liu et al., CNS 2022; Engelen et al., WTMC 2021). The NF-* NetFlow rebuilds inherit the upstream labeling. Against a `q = 0.05` target this is not a limitation, it is an **identification failure**: the quantity being measured is smaller than the noise in the measuring instrument.

Worse, label error is not uniform. It concentrates in ambiguous flows — precisely the ones a detector places near its threshold — so the error rate *among alerted events*, call it `ε_R`, satisfies `ε_R ≥ ε_overall`.

Four mandatory mitigations:

1. **Use corrected releases.** Prefer the regenerated/relabelled CICIDS distributions over the originals. State the version and the fix provenance in the paper.
2. **Report FDP as an interval,** not a point: `[max(0, F̂DP − ε_R), min(1, F̂DP + ε_R)]`. If the interval is wider than `q`, say so in the caption. This is the honest move and reviewers reward it.
3. **Manual label audit.** Hand-verify a random sample (target n ≈ 200–300) of alerts from one day of the primary dataset to estimate `ε_R` directly rather than importing the global figure. Cheap, high credibility.
4. **Shift the primary claim to temporal stability.** A roughly constant label bias shifts the FDP *level* but not its *variation over time*. "Fixed thresholding produces FDP that swings by 40 points across regimes while procedure X holds it within 8" survives label noise that "FDP is 0.048" does not. Make stability, not level, the headline.

## 7.5 Datasets — final

| Dataset | Role | Why | Prevalence |
|---|---|---|---|
| Corrected CIC-IDS2017 / NF-CSE-CIC-IDS2018-v3 | primary development | scale, chronology, attack families, corrected labels available | ~22% native → Axis A |
| **AIT-ADS** | **alert-level, incident-level** | 2.66M alerts from 3 detectors (AMiner, Wazuh, Suricata), 93 signatures, 8 testbeds, 3 weeks, **multi-step attack scenarios with campaign ground truth** | n/a (alerts) |
| LSPR23 | external realism | Locked Shields live-fire, ~16M flows / ~1.6M malicious | ~10% |

**AIT-ADS is promoted from v1's afterthought to a co-primary dataset.** It is the best fit in the whole plan: the deployment position is honest (a statistical control layer over an existing SIEM, not a new NIDS), the 93 signatures give a natural grouping structure for C1, and the multi-step scenarios give real incident ground truth for D1. It is also the setting where a practitioner could actually adopt this tomorrow.

**Dropped:** WitFoo Precinct6 (vendor-pipeline labels are unusable when FDP is the metric — v1 §15.5 concedes this), LANL (no exhaustive ground truth, so false positives are unidentifiable — same problem), NF-ToN-IoT-v3 (replication only if week 4 has slack), UNSW-NB15 (64% prevalence makes it useless for base-rate claims; mention only if a deliberate high-prevalence stress point is needed, citing CALIBURN's result there).

## 7.6 Detectors

**XGBoost** (supervised) and **Isolation Forest** (unsupervised). Two, not four. Purpose is only to show decision-layer conclusions are not detector-specific. Logistic regression as a sanity check in the appendix if it is free. Dropped: RF, MLP, autoencoder, one-class SVM.

## 7.7 Procedures

| Method | Role | Dependence assumption |
|---|---|---|
| Naive `p_t < 0.05` | shows the multiplicity effect | — |
| LORD++ | canonical online FDR reference | independence (**violated here** — see below) |
| SAFFRON *or* ADDIS (pick one) | adaptive reference | independence |
| **SupLORD** | **FDX / FDP tail control at stopping times** | conditional superuniformity |
| **e-LOND / Ue-LOND** | **arbitrary dependence** | none |
| e-BH | offline retrospective reference | arbitrary dependence |

**The dependence problem is doubly broken, and the paper must say so precisely.** (i) Conformal p-values sharing one calibration set are dependent — Bates et al. prove PRDS, which is enough for **BH** but is *not* the independence condition LORD/SAFFRON/ADDIS assume, so their guarantees do not transfer. (ii) Network telemetry adds serial dependence on top. Hence the e-value route in C1 is not a stylistic preference; it is the only branch where the stated guarantee actually holds.

**SupLORD matters because it controls the right thing.** LORD++/SAFFRON/ADDIS control mFDR at stopping times, not FDR, and none give tail control. A SOC does not care about a stream-average; it cares about not having a catastrophic Tuesday. `P(FDP_t > q)` — v1 §12.3 — is exactly the FDX quantity SupLORD provides. Use it.

## 7.8 Baselines

- **B1** fixed threshold `s_t > 0.5`
- **B2** validation-F1-optimal threshold
- **B3** fixed FPR `∈ {10^-2, 10^-3, 10^-4}`
- **B4** quantile threshold (top 1% of scores)
- **B5** top-`k` per interval (analyst capacity)
- **B6 — feedback controller on delayed dispositions (the baseline that may win).**

**B6 in detail, because it is the paper's real competition.** In any operating SOC, analyst dispositions arrive as delayed labels. Given them, estimate FDP directly over a trailing window and hold it at target with a simple controller:

$$\tau_{t+1} = \tau_t + \eta\left(\widehat{FDP}^{(\text{window})}_{t-L} - q\right)$$

No multiple-testing theory, no exchangeability, no dependence assumption, no α-wealth. Sweep label latency `L ∈ {0, 1h, 1d, 1w, ∞}`, where `∞` = no labels ever, which is the only regime where the FDR machinery is forced.

This is where C4 comes from: locate the crossover `L*`. My prior is that B6 wins comfortably for `L ≤ 1d`, which means the honest scope of the whole FDR programme is the label-scarce regime — which is *also* where drift most damages calibration validity. Confronting that tension is the difference between a paper reviewers trust and one they don't. Related: Feedback-Enhanced Online Multiple Testing (2025) — cite it.

## 7.9 Metrics

**Error control:** FDP interval (§7.4), realized FDR, **FDX** `P(FDP_t > q)`, **structural silence rate** (§6.3), incident-level FDP.

**Utility, all at matched budget per P1:** flow recall, **incident recall**, time-to-first-detection, missed-incident count, per-attack-family recall, alerts/day, false investigations/day.

**Vacuity guard.** `FDR ≤ q` is trivially satisfied by alerting on nothing. Every FDR number in the paper appears next to a power number, in the same table, always. Predict and check: for weak-signal attack families at low `π`, control at `q = 0.05` will yield *zero* alerts. Report that as the base-rate fallacy quantified with modern tooling — not as a surprise.

---

# 8. Calibration validity

Under `P_cal(S) ≠ P_deploy(S)` the conformal evidence stops being valid and the guarantee is void. This chain is not a nuisance, it is a result:

```text
drift → invalid conformal evidence → FDR violation
```

But note what v1 got backwards: this chain is **not an empirical discovery**, it is a consequence of the exchangeability assumption being violated by construction — the chronological protocol deliberately breaks exchangeability, so the failure is guaranteed a priori. v1's "Finding 4" is close to tautological. The publishable version is *quantitative*: how much drift, measured how, produces how much violation, and which mitigation buys back how much power.

**Diagnostics:** null-uniformity of p-values on held-out benign data (per day), KS / Wasserstein distance between calibration and deployment benign score distributions, e-value mean deviation from 1, and FDR violation regressed on drift magnitude.

**Mitigations — derived, not swept.** Rolling calibration (window `W`), drift-triggered recalibration, and e-value procedures whose validity does not rest on the dependence assumptions that drift also breaks. Three mechanisms, not six. And note the sting: rolling calibration is the mitigation, and §9's attack 2 targets exactly it.

---

# 9. C3: attacking the alerting layer

Threat model: attacker has (a) knowledge that an online error-control layer is deployed and its family, (b) ability to inject traffic that will be scored, (c) no access to model weights, calibration data, or the wealth state. Black-box, no evasion perturbations required. This is materially weaker than the assumptions in the existing adversarial-FDR literature — which is the point.

## A1 — α-wealth exhaustion

Inject `N` borderline flows whose scores sit just below the current rejection region: no rejections, so no wealth is earned, so `α_t` decays (Prop. 1), so the procedure slides toward structural silence. Then run the real campaign through the silence.

*Measure:* injection budget `N` vs. induced silence duration; success rate of a subsequent campaign vs. `N`; cost asymmetry (attacker packets per suppressed detection).

*Novelty:* Chen et al. (2025) attack **batch BH** by perturbing test scores. The 2025 conformal-novelty-detection attack uses **test-time evasion on offline** AdaDetect/Bates. Neither touches an **online wealth process**. A1 is an attack on the *temporal* mechanism, and it requires no perturbation of the attacker's own traffic.

## A2 — rolling-calibration poisoning

The recommended drift fix keeps `C_t = {x_{t−W}, ..., x_{t−1}}`. An attacker who contributes a controlled fraction `ρ` of that window with high-but-benign-looking traffic shifts the benign score quantiles upward. The real campaign's score is then no longer extreme relative to `C_t`, its p-value is not small, and it is never rejected.

*Measure:* `ρ` required for a target p-value inflation; interaction with `W` (shorter windows are more drift-robust and *more* poisonable — quantify the frontier); whether the drift diagnostics of §8 detect the poisoning or mistake it for legitimate drift (I expect the latter, which is the interesting result).

*Framing:* **the mitigation for drift is the attack surface for suppression.** This directly implicates Transcendent's and FIRCE's rolling-calibration designs, which makes it relevant beyond this paper.

## A3 — workload attack (brief)

Generate high-volume, easily-detected attack traffic to inflate `R_t` with true discoveries, freeing FDP headroom and consuming analyst capacity. At event level this *improves* the reported FDP while degrading the SOC — a direct demonstration of C1's domination problem under adversarial control. One paragraph, one figure; it ties C1 and C3 together neatly.

## Defenses

Arbitrary-dependence e-value procedures (A1 partially — check whether e-LOND's wealth dynamics are drainable, this is an open question worth stating), **wealth floors** (bound `α_t` below at the cost of a weakened guarantee — quantify the trade), **trimmed/robust quantile calibration** (A2), **calibration provenance restriction** (calibrate only on vetted or aged traffic), and incident-level control (A3).

---

# 10. Expected findings

Written as falsifiable predictions with pre-committed interpretations, so the paper is publishable whichever way each lands.

| # | Prediction | If it holds | If it fails |
|---|---|---|---|
| F1 | Event-level FDP changes by ≥1 order of magnitude when the single largest incident is removed | C1 established in one figure | C1 weakens to "incident-level is a better-aligned objective"; still fine |
| F2 | Fixed thresholding shows FDP swings of tens of points across regimes; e-value procedures hold within single digits — **at matched budget** | headline stability result | report it: the baselines are better than the literature assumes, which is a genuine service |
| F3 | Structural silence occurs on ≥1 real stream at realistic `π` | C2's quotable number | report the calibration size at which it stops occurring; still a design rule |
| F4 | LORD++/SAFFRON lose control under Axis B while e-LOND does not | validates the e-value route | strengthens the practical story: cheap procedures suffice |
| F5 | B6 dominates for `L ≤ 1 day`; FDR machinery only wins at `L → ∞` | C4's crossover; the paper's most useful practical output | even better for the FDR story — say so plainly |
| F6 | A2 succeeds at `ρ` well under 50% of the calibration window | strong SaTML result | report the required `ρ` as a robustness *guarantee* — also useful |
| F7 | At `q=0.05` and `π=10^-4`, some attack families get zero alerts | base-rate fallacy quantified | the tooling is stronger than expected; report the separation required |

---

# 11. Paper structure (12 pages)

| § | Content | Pages |
|---|---|---|
| 1 | Introduction — Axelsson's question, why modern tooling should answer it, why it doesn't yet | 1.25 |
| 2 | Background & related work — incl. the §3 delta table | 1.25 |
| 3 | Formulation — events, incidents, p/e-values, FDR/FDX, assumption ledger per procedure | 1.0 |
| 4 | **Event-level control is the wrong objective** (C1) + the e-value incident construction | 1.75 |
| 5 | **Structural silence** (C2) — Prop. 1, silence rate, the randomization tension | 1.25 |
| 6 | Experimental framework — datasets, splits, P1, label-noise identification, incident defs | 1.25 |
| 7 | Does anything control alert quality? — RQ1/RQ2 at matched budget, incl. B6 and the crossover (C4) | 1.5 |
| 8 | When do guarantees fail? — Axis A, Axis B, drift, calibration age | 1.5 |
| 9 | **Attacking the alerting layer** (C3) — A1, A2, A3, defenses | 1.5 |
| 10 | Discussion, threats to validity, limitations | 0.5 |
| 11 | Conclusion | 0.25 |

Overflow to appendix: full Pareto grids, per-family tables, D1/D2/D3 sensitivity, label audit protocol, proofs.

**Assumption ledger (§3) is non-optional.** One table: for each procedure, the exact condition required (independence / PRDS / conditional superuniformity / none), whether it holds on our streams, and what is claimed as a result. This single table is the difference between "we ran LORD on network data" and a trustworthy-ML paper.

---

# 12. Five-week plan (25 Aug → 29 Sep 2026)

**Week 1 (Aug 25–31) — substrate + C2.**
Corrected primary dataset ingested; chronological split; XGBoost + IsolationForest scored; conformal p-value and e-value layer; LORD++ and naive baselines; harness that logs `α_t` per step.
**Gate G1:** reproduce structural silence (Prop. 1) numerically, or establish the calibration size that prevents it. *This is the cheapest novel result in the plan — get it first so the paper has a spine by day 7.*

**Week 2 (Sep 1–7) — honest baselines + C4.**
B1–B5; **B6 controller with latency sweep**; P1 harness (M1/M2/M3) so no unmatched number can be produced by accident; RQ1 + RQ2 on the primary dataset.
**Gate G2:** the label-latency crossover `L*` is measured. If B6 dominates everywhere including `L=∞`, stop and rethink the framing before writing anything.

**Week 3 (Sep 8–14) — C1.**
Incident definitions D1/D2/D3; conformal e-values; incident-level averaging; e-LOND / Ue-LOND / SupLORD; the anytime-validity proof for the running-mean variant (fall back to fixed-window if it does not close); Axis B order-permutation ablation.
**Gate G3:** F1 (largest-incident sensitivity) resolved.

**Week 4 (Sep 15–21) — C3 + breadth.**
A1 and A2 implemented and swept; AIT-ADS alert-level pipeline; LSPR23 run; Axis A prevalence sweep; drift + calibration-age experiments.
**Abstract registration: Tue 22 Sep — mandatory. Register regardless of state.**

**Week 5 (Sep 22–29) — write and harden.**
Manual label audit (§7.4.3); all figures regenerated under P1; assumption ledger; threats to validity; appendices. Submit Tue 29 Sep.

**Descope order if behind** (drop from the bottom): NF-ToN-IoT replication → A3 → Axis A low-`π` points → SupLORD → D3 → LSPR23. **Never descope:** P1, the label-noise interval, B6, or the assumption ledger. Those four are what make it credible; the experiments are what make it interesting.

---

# 13. Threats to validity (write these before the results, not after)

1. **Label noise exceeds the target effect** on the primary dataset. Mitigated by corrected releases, FDP intervals, the manual audit, and shifting headline claims to temporal stability. Cannot be fully eliminated. State it in the abstract if the audit comes back badly.
2. **Constructed prevalence is not observed prevalence.** Axis A points below native prevalence are synthetic. Never present them as measurements of a real environment.
3. **Incident definitions are a confound.** Hence D1/D2/D3 side by side.
4. **Benchmark realism.** LSPR23 is live-fire but exercise traffic; AIT-ADS is testbed. No production SOC data — say so, and do not gesture at generality we do not have.
5. **Analyst workload is proxied by alert counts,** not measured on humans. A controlled study on false-alarm rate and analyst performance exists (arXiv 2307.07023); cite it and be explicit that we are not replicating it.
6. **Adversarial evaluation is against a fixed defense.** A1/A2 are not claims of worst-case security. Frame as existence proofs of a new attack surface, not as bounds.
7. **Prop. 1's rate is procedure-specific.** Derived per procedure or stated as a per-procedure empirical result. Do not state one rate as universal.

---

# 14. Abstract (draft)

> Machine-learning intrusion detectors are evaluated as classifiers, but security operations centres consume alert streams, and the quantity that binds their capacity is the fraction of alerts that are false. Online false-discovery-rate control is the natural statistical answer, and this paper asks whether the guarantee it provides means anything on real security telemetry. We show it largely does not, for three reasons that classifier metrics cannot express. First, the guarantee is stated over the wrong unit: security incidents span four orders of magnitude in event count, so event-level false-discovery proportion is dominated by whichever campaign is most voluminous and its denominator is under adversarial control. We give an incident-level construction — conformal e-values averaged within incidents, valid under arbitrary dependence — that restores alignment between the guarantee and the analyst's decision. Second, the discreteness of conformal p-values interacts with α-wealth decay so that, after a sufficiently long rejection drought, standard online procedures provably cannot alert on any input while continuing to report perfect error control; we characterise this structural-silence regime and measure how often real streams enter it. Third, the standard remedy for distribution drift is itself an attack surface: we present black-box attacks that drain a procedure's testing budget and that poison a rolling calibration window to suppress detection of the attacker's own campaign, neither of which requires perturbing attacker traffic. Across corrected NetFlow benchmarks, a live-fire exercise dataset and a multi-detector SIEM alert dataset, and measured strictly at matched analyst budget, we locate the label-latency threshold below which a simple feedback controller on analyst dispositions outperforms all multiple-testing machinery — bounding where these methods are worth deploying at all.

---

# 15. Research philosophy (unchanged in spirit, sharpened in target)

```text
established statistical method
+ a security formulation that shows the method's stated guarantee is misaligned
+ a failure mode the method's own mechanics create
+ an adversary who exploits the recommended mitigation
+ an honest baseline that bounds when any of it is worth deploying
```

Neither the detectors nor the error-control procedures are novel. The contribution is that a mature guarantee, transplanted into security telemetry, controls the wrong quantity, can silence itself, and can be turned off by an attacker who merely knows it is there — together with the constructions that fix the first problem and bound the third.
