# Plan v3 — Feasibility and Adversarial Exploitation of Online Error Control for ML Security Alerting

**Supersedes** `18_fdr_trustworthy_ids_research_idea_corrected.md` (v2).
**Deadline:** SaTML 2027 — abstract **22 Sep 2026** (27 days), paper **29 Sep 2026** (34 days), 12 pages body.

---

## 0. How to read this document

Every substantive claim carries a tag. This exists because v2 asserted novelty for two
findings that a 20-minute literature search would have shown were already named and
published. That will not happen again silently.

| Tag | Meaning |
|---|---|
| `[VERIFIED-SIM]` | Established by our prototype; exact (arithmetic property, not an empirical hypothesis) |
| `[VERIFIED-DATA]` | Measured on real data; scope and sample size stated |
| `[PRIOR]` | **Already published.** Cite and differentiate; do not claim |
| `[REFUTED]` | We predicted it; the prototype contradicted it |
| `[UNVERIFIED]` | Plausible, untested. No claim until tested |
| `[NOVELTY-CHECKED]` | A targeted literature search was run; the search terms are recorded |

---

## 1. Claims ledger

This is the most important section. Read it before anything else.

### 1.1 What survives

| Claim | Status | Detail |
|---|---|---|
| Conformal p-value floor `1/(\|C\|+1)` can make rejection impossible regardless of score | `[PRIOR]` | Named **"resolution collapse"** — Hennhöfer & Preisach, arXiv 2603.23205, *batch* weighted conformal, low-data regime. Also "conformal p-values cannot take very small values unless the sample size is extremely large" is stated as known. |
| Online test levels decay so procedures stop rejecting | `[PRIOR]` | Named **"alpha-death"** — documented in the onlineFDR package theory vignette and treated by Xu & Ramdas. Literature's position: afflicts alpha-*spending*, cured by alpha-*investing*. |
| **The two collide at security scale**: alpha-investing does **not** cure it, because earning wealth requires a rejection and no rejection is attainable once `α_t < p_min` | `[VERIFIED-SIM]` `[NOVELTY-CHECKED]` | LORD++ with \|C\|=10⁴ permanently unable to reject after **19 events**; recall 0.000 at π≤10⁻³ with a 5σ detector. Searched: "alpha-death", "discrete p-values online FDR granularity". **This interaction is what is left of the finding.** |
| Feasibility envelope `\|C\| ≥ 1/α_T`, superlinear in horizon | `[VERIFIED-SIM]` | Best-case (horizon-uniform) γ: LSPR23 event-level needs 6.4×10⁸ calibration flows; 1 hr @ 10k flows/s needs 1.4×10⁹; γ∝j^−1.6 needs 3×10¹³. Zrnic et al. frame batching as *power* recovery and (checked) do not address rejection feasibility or discrete evidence. |
| Grouping/aggregation restores discovery capability | `[PRIOR]` for the mechanism, `[VERIFIED-SIM]` for the magnitude | **Zrnic, Jiang, Ramdas & Jordan, "The Power of Batching in Multiple Hypothesis Testing" (AISTATS 2020)** — Batch-BH/Batch-St-BH interpolate online↔offline; BatchPRDS handles within-batch positive dependence. Our number: recall 0.000 → 1.000, silence 100% → 0% on the same stream. |
| Online **group-level** FDR with online-determined group membership | `[PRIOR]` | **"Online multi-layer FDR control", arXiv 2506.03406 / Mathematics 2025** — adapts alpha-investing, LOND and LORD to online multi-layer group FDR where group membership is *not predefined*. This is the procedure C1 needs, and it exists. Also p-filter (Barber & Ramdas) for the batch case. |
| Mean-of-e-values valid under arbitrary within-incident dependence | `[VERIFIED-SIM]` (trivially, by linearity of expectation) | Sound but not a contribution — it is one line of algebra. Its practical value is that dependence stops being an obstacle. |
| Attacking the **online state** of a sequential FDR procedure | `[UNVERIFIED]` `[NOVELTY-CHECKED]` | Searched: "adversarial online multiple testing", "alpha wealth starvation", "poisoning rejection history". **No prior work found.** Nearest: Chen et al. (batch BH, test-score perturbation), arXiv 2510.00463 (offline conformal novelty detection, test-time evasion), arXiv 2501.13242 (Byzantine *distributed* multiple testing). **This is the only unclaimed pillar.** |

### 1.2 What is dead

| Claim | Status | Why |
|---|---|---|
| Drift catastrophically invalidates calibration → FDR violation | `[REFUTED]` | Real AIT NetFlows, 5-day chronological split: anti-conservative by only **1.3–2.0×**, and *conservative* (0.86–0.93) at 10⁻²–10⁻³. Rolling calibration 1.10–1.31. Was slated as a headline. It is a robustness subsection. |
| Temporal dependence breaks online FDR (the original proposal's central obstacle) | `[PRIOR]` + dissolved | Rebjock et al. (AISTATS 2022) already addressed serial dependence and rare alternatives for online-FDR anomaly detection. And with e-values it stops being an obstacle at all. |
| "N1": deployed calibration sets make e-values anti-conservative ~37% of the time, and more data does not help | `[PRIOR]` — **retract as a contribution** | Bates, Candès, Lei, Romano & Sesia give **calibration-conditional conformal p-values**: valid with probability ≥1−δ over the calibration draw, via a Simes-type adjustment, with reference code (`msesia/conditional-conformal-pvalues`). The problem is known and *solved*. Our "more data doesn't help" framing was misleading — the fix was never more data. **Action: apply their adjustment; cite; do not claim.** |
| "N2": guarantees at p≈10⁻⁶ are empirically un-auditable | `[VERIFIED-DATA]`, but weak as a contribution | 137,832 held-out flows → 2 events below 10⁻⁵, none below 10⁻⁶; auditing 10⁻⁶ needs ~10⁷–10⁸ events. True, but it is a restatement of why the calibration-conditional literature exists. Keep as a discussion point, not a contribution. |
| "Event-level online FDR is impossible for cybersecurity" | **Overclaim — retract** | Conditional on γ, procedure, evidence construction, \|C\|, q, horizon, rejection history and aggregation level. Correct phrasing: *infeasible under every valid γ we tested, by 2–3 orders of magnitude, at realistic horizons.* |
| Our LSPR23 headline (288 campaigns → 11,520 calibration flows) is a deployment result | **Qualify** | It uses **oracle** campaign grouping from the narratives file. Not deployable. See §4 — this is now a gating experiment, not a footnote. |

### 1.3 Net assessment, stated plainly

Two of v2's three pillars are substantially pre-empted at the methodology level. The
resolution floor is named prior work; alpha-death is named prior work; batching-restores-power
is published with algorithms; online group-level FDR with online group membership is
published. What remains is (a) the *interaction* of two known phenomena and the resulting
feasibility envelope, which the grouping/batching literature frames as power rather than
feasibility, (b) an empirical security study with deployable grouping, and (c) an attack
with no located prior work.

**This is a thinner paper than v2 claimed.** It is plausibly still main-track, but only if
the attack works. §11 makes that an explicit decision point rather than an assumption.

---

## 2. Contributions, reordered by remaining novelty

Reordered deliberately: the attack now leads because it is the only pillar with no prior
work found, and the feasibility result leads the analysis because it is exact and cheap.

### C1 — Statistical-state attacks on online alerting (`[UNVERIFIED]`, highest novelty)

An adversary targets the **decision layer's state**, not the classifier. No evasion
perturbation of attacker traffic is required.

- **A1 — group inflation.** At incident level, manufacture spurious low-signal groups. Each
  group consumes a hypothesis slot, driving `T` up and `α_T` down, raising the required
  `|C|` and pushing the controller toward the infeasible region. *This is the corrected
  form of v2's "α-wealth exhaustion": at event level the defender enters silence unaided
  after ~19 events, so `B* ≈ 0` and there is nothing to attack. The attack only has content
  where the defender is viable.*
- **A2 — rolling-calibration poisoning.** Contribute a fraction ρ of the rolling calibration
  window with high-but-benign traffic, lifting the benign score quantiles so the real
  campaign's evidence is no longer extreme. The recommended mitigation for drift is the
  attack surface.
- **Threat model, stated tightly.** Attacker knows a controller of a given family is
  deployed; can inject traffic that will be scored; **cannot** read `α_t`, the calibration
  set, or model weights. Must demonstrate a realistic observation channel — whether
  black-box inference of the controller's state from observable alerting behaviour is
  possible is itself a research question, and if the answer is no, A1 must be reframed as a
  blind/open-loop attack with a stated success probability.
- **Deliverable:** minimum attacker budget `B*` vs (q, |C|, procedure, granularity), and
  suppression duration / detection-delay increase.

### C2 — Feasibility envelope for online error control at security scale (`[VERIFIED-SIM]`)

Characterise when established online procedures can issue *any* discovery. Differentiated
from Zrnic et al. (power) and from resolution collapse (batch, low-data) by being about
**rejection feasibility as a function of stream horizon**, with the two mechanisms coupled.

### C3 — Security-semantic granularity, with deployable grouping (`[VERIFIED-SIM]` oracle / `[UNVERIFIED]` deployable)

The unit at which ML predicts is not the unit at which security acts, and the choice
determines whether the guarantee is usable. Methodologically this rides on existing
procedures (online multi-layer FDR, Batch-BH); the contribution is the security mapping and
the oracle-vs-deployable gap.

### C4 — Operational bound (`[UNVERIFIED]`)

The label-latency crossover against an analyst-disposition feedback controller: when is any
of this machinery worth deploying?

---

## 3. Positioning table (for the paper)

| Work | Setting | Online? | Grouped? | Feasibility of rejection? | Adversary? |
|---|---|---|---|---|---|
| Axelsson '99 | IDS, analytical | – | – | – | – |
| Bates et al. '23 | outlier testing | ✗ | ✗ | ✗ (gives calibration-conditional fix) | ✗ |
| Rebjock et al. '22 | time-series AD | ✓ | ✗ | ✗ (power under rare alternatives) | ✗ |
| Zrnic et al. '20 (batching) | multiple testing | ✓ | ✓ (batches) | ✗ (**power**, not feasibility) | ✗ |
| p-filter; Online multi-layer FDR '25 | grouped testing | ✓ | ✓ (online membership) | ✗ | ✗ |
| Hennhöfer & Preisach '26 | conformal AD | ✗ | ✗ | ✓ (**resolution collapse**, batch/low-data) | ✗ |
| onlineFDR / Xu & Ramdas | online testing | ✓ | ✗ | ✓ (**alpha-death**, spending only) | ✗ |
| CALIBURN '26 | streaming NIDS | ✓ | ✗ | ✗ (FPR budget, no multiplicity) | ✗ |
| Chen et al. '25 | multiple testing | ✗ | ✗ | ✗ | ✓ (batch BH) |
| Adv. conformal novelty '25 | novelty detection | ✗ | ✗ | ✗ | ✓ (offline, evasion) |
| **This paper** | **NIDS streams** | **✓** | **✓** | **✓ (coupled, horizon-scaled)** | **✓ (online state)** |

---

## 4. Gating experiment: does deployable grouping preserve the escape?

**This is the highest-priority experiment and neither v2 nor the reviewer's plan had run it.**
Our headline number uses LSPR23's oracle campaign labels. If deployable grouping fragments
288 campaigns into tens of thousands of groups, the requirement moves from 1.2×10⁴ toward
10⁶–10⁷ and the escape narrows or closes.

Three grouping regimes, reported side by side:

- **G-oracle** — LSPR23 narrative campaign IDs. Establishes the bound. Not deployable; label it so in every figure.
- **G-deploy** — no attack ground truth: `(src, dst-service)` within session-gap Δ ∈ {60s, 300s, 1800s}; and a host-time-window variant.
- **G-noisy** — G-oracle perturbed by controlled split/merge rates to trace sensitivity between the two.

**Measured for each:** number of groups `T_g`, `α_T` attained, `n_min = 1/α_T − 1`, structural
silence rate, incident recall, FDP interval, detection latency.

**Pre-registered decision rule.** If G-deploy yields `T_g` such that `n_min` exceeds 10⁷ on
LSPR23, C3 collapses to an oracle-only result and the paper must lead on C1+C2 alone.

---

## 5. Analytical core — corrected

v2 and the reviewer's §23 both stated the condition for p-values only. That misses the
dimension where the actual tension lives.

**p-value evidence.** `p_min = 1/(n+1)`. Rejection at `t` requires `p_min ≤ α_t`, hence

    n ≥ 1/α_t − 1

**e-value evidence (the case we use).** A threshold conformal e-value at rank `k` has
ceiling `e_max = (n+1)/k` and rejects when `e ≥ 1/α_t`, hence

    n ≥ k/α_t − 1

**The tension `k` creates.** A high ceiling needs small `k`. But small `k` makes the evidence
depend on the extreme order statistics of the calibration set, where the calibration-conditional
guarantee is weakest — measured exactly: at `k=1`, `P(E[e|C] > 1) ≈ 0.37` with p99 ≈ 4.1–4.9×,
and **invariant in `|C|`** (the relative dispersion of the k-th order statistic depends on `k`,
not `n`). `[VERIFIED-SIM]`

**The resolution is not more data — it is Bates et al.'s calibration-conditional adjustment,**
applied at a stated δ. This costs power, and quantifying that cost as a function of `k` is a
legitimate, modest contribution. `[PRIOR]` for the method, `[UNVERIFIED]` for the cost curve.

**Feasibility envelope.** For horizon `T` and a specified rejection history,
`n_min(T) = max_{t≤T} ⌈k/α_t − 1⌉`, derived per procedure (LOND, LORD++, and at least one
adaptive rule). Constants differ per procedure; the `T`-scaling does not. Do **not** state one
rate as universal — v2 did, and the rate is γ-dependent (`T^1.6` for γ∝j^−1.6 vs `T/w₀` for
horizon-uniform γ).

---

## 6. Protocol invariants (non-negotiable)

- **P1 — matched operating points only.** Every comparison at matched analyst budget, matched
  realised FDP, or as a full Pareto frontier. No "LORD at q=0.05 vs threshold at 0.5".
- **P2 — every FDR number printed beside a power number,** in the same table. `FDR ≤ q` is
  satisfied by alerting on nothing.
- **P3 — FDP reported as an interval** under label-error rate `ε_R`, never a point estimate.
  CSE-CIC-IDS2018 corruption is 7.53% (>75% for some classes); NF-* rebuilds inherit it. Use
  corrected releases; hand-audit ~200–300 alerts from one day to estimate `ε_R` directly;
  make **temporal stability of FDP** the headline rather than its absolute level, since a
  roughly constant label bias shifts level but not variation.
- **P4 — oracle-derived results labelled as such in every figure caption.**
- **P5 — assumption ledger table** in §3 of the paper: per procedure, the exact condition
  required (independence / PRDS / conditional superuniformity / none), whether it holds on our
  streams, and what is therefore claimed.

---

## 7. Baselines

B1 fixed threshold · B2 validation-F1 · B3 fixed FPR · B4 quantile · B5 top-k ·
**B6 analyst-disposition feedback controller** with label latency `L ∈ {0, 1h, 1d, 1w, ∞}`:

    τ_{t+1} = τ_t + η ( FDP̂_window(t−L) − q )

No multiplicity theory, no exchangeability, no dependence assumption. Expected to win for
`L ≤ 1 day`. If it does, the honest scope of the whole programme is the label-scarce regime —
say so in the abstract.

## 8. Data

| Dataset | Role | Status |
|---|---|---|
| LSPR23 (16M flows, 1.6M malicious, 288 campaigns) | **primary** — the only source with real multi-step campaign ground truth | narratives ✅ parsed; flows ⏳ downloading (1.9 GB) |
| AIT NetFlows (8 testbeds, real, timestamped) | calibration-validity experiments | ✅ working |
| Corrected CIC-IDS2017 / NF-CSE-CIC-IDS2018-v3 | scale, reproducibility | ❌ manual browser download needed (~1 hr); UQ links are JS landing pages |
| AIT-ADS | **deferred** | downloaded but **unlabelled**; labels need reconstruction from AIT-LDSv2 (137 GB) — 3–5 days, unaffordable |
| LANL, WitFoo, UNSW-NB15 | **dropped** | incomplete negative ground truth / vendor labels / 64% prevalence |

## 9. Detectors and procedures

**Detectors:** XGBoost (or HistGradientBoosting) + Isolation Forest. Two. The paper is not
about classifier comparison.

**Procedures:** LOND, LORD++ (both implemented exactly already), one adaptive rule
(SAFFRON *or* ADDIS — **not yet implemented**, and their wealth bookkeeping differs, so
per-procedure constants must be re-derived), e-LOND (arbitrary dependence), Batch-BH /
online multi-layer FDR as the grouped comparator, e-BH offline reference.

## 10. Metrics

Structural silence rate · time to structural silence · `n_min(T, q, procedure, k)` ·
feasible horizon `T_max(n)` · FDP interval · FDX `P(FDP_t > q)` · incident recall ·
time-to-first-incident-detection · alerts/day · attacker budget `B*`.

---

## 11. Four-week plan, with gates and fallbacks

Today 26 Aug. Abstract 22 Sep (27 d). Paper 29 Sep (34 d).

**Week 1 (26 Aug – 1 Sep) — settle the two things that decide the paper.**
1. **Implement A1 and A2** against the incident-level controller. This is first because it is
   the only unclaimed pillar and everything else is a fallback.
2. **Run the G-deploy gating experiment** (§4) on LSPR23 flows as soon as the download lands.

> **GATE 1.** If A1/A2 show no meaningful `B*` advantage over blind attack **and** G-deploy
> closes the escape → the paper is a feasibility-envelope + empirical study only. Decide then
> whether to target SaTML main track or a workshop. Do not discover this in week 4.

**Week 2 (2–8 Sep) — analysis and honest baselines.**
Feasibility envelope derived per procedure incl. the `k` dimension; Bates calibration-conditional
adjustment applied and its power cost measured; B1–B6 under P1; label audit for `ε_R`.

> **GATE 2.** If B6 dominates at every latency including `L=∞`, reframe the paper around that
> result rather than burying it.

**Week 3 (9–15 Sep) — breadth.**
G-oracle / G-deploy / G-noisy across granularity levels; second dataset (corrected CIC);
attack sweeps; drift/calibration-age as a *robustness subsection*, not a section.

**Week 4 (16–22 Sep) — write; register abstract 22 Sep regardless of state.**

**Week 5 (23–29 Sep) — figures under P1–P5, assumption ledger, threats to validity, submit.**

**Descope order (from the bottom):** second dataset → G-noisy → adaptive procedure (SAFFRON/ADDIS)
→ A2 → drift subsection. **Never descope:** P1–P5, B6, the assumption ledger, or the
oracle/deployable distinction.

---

## 12. Claims we will not make

- Not "we are first to note SOCs care about false alerts" (Axelsson 1999).
- Not "online FDR has not been used for anomaly detection" (Rebjock et al. 2022).
- Not "dependence is an unknown problem for online FDR" (known; and dissolved by e-values).
- Not "conformal calibration for security streams is new" (Transcend/Transcendent/FIRCE/FADES).
- Not "drift catastrophically invalidates FDR" (`[REFUTED]` on our own data).
- Not "event-level online FDR is impossible" (conditional; state the conditions).
- Not "the resolution floor is a new failure mode" (**resolution collapse**, arXiv 2603.23205).
- Not "threshold decay to zero is a new failure mode" (**alpha-death**, onlineFDR / Xu & Ramdas).
- Not "grouping to restore power is new" (**Zrnic et al. 2020**; online multi-layer FDR 2025).
- Not "calibration-conditional invalidity is a new finding" (**Bates et al.**, with a fix).
- Not "incident grouping is deployable" while using oracle campaign labels.

## 13. Threats to validity

1. Two pillars ride on prior work; if reviewers judge the interaction insufficiently novel, the
   paper rests on C1 (attack) alone. Explicit, and Gate 1 tests it early.
2. The headline feasibility numbers are **simulation**. Appropriate for arithmetic properties of
   the procedures, but the μ (detector separation) values are **assumed** — real per-family
   separation on LSPR23 is unmeasured and drives every recall number.
3. Real-data calibration evidence is one testbed, 5 days, 418k flows, IsolationForest only. It
   cannot speak to 10⁻⁶, and says nothing about drift over months.
4. LSPR23 is live-fire but exercise traffic. No production SOC data.
5. Analyst workload is proxied by alert counts. Cite the controlled false-alarm/analyst-performance
   study (arXiv 2307.07023); do not claim a human study.
6. A1/A2 are existence proofs against a fixed defence, not worst-case bounds.
7. SAFFRON/ADDIS are not yet implemented; per-procedure constants are currently unknown.

## 14. Abstract (draft — every clause traceable to §1)

> Statistical error guarantees are increasingly proposed to make machine-learning security
> alerting trustworthy. We study when such guarantees remain non-vacuous, and whether they can
> be turned off by an adversary. Two failure modes are individually known — the discrete
> resolution floor of conformal evidence, and the decay of online test levels — and we show
> that at cybersecurity stream lengths they couple: because earning testing budget requires a
> rejection, and no rejection is attainable once the assigned level falls below the evidence
> floor, alpha-investing does not recover from the collapse that alpha-spending is known to
> suffer. We derive the resulting feasibility envelope for established online procedures,
> including its dependence on the evidence-ceiling parameter, and find that flow-level control
> at realistic horizons requires calibration sets two to three orders of magnitude beyond what
> security telemetry provides, under every admissible spending sequence we tested. Grouping
> hypotheses is known to recover power; we show it recovers *feasibility*, quantify the gap
> between oracle campaign grouping and deployable grouping on a live-fire exercise dataset, and
> then show that the same grouped controller admits a new attack surface: an adversary who
> merely injects low-signal traffic can inflate the hypothesis stream or shift a rolling
> calibration window to suppress detection of a later campaign, without perturbing the attack
> itself. We close by bounding the practical value of the whole approach against a feedback
> controller driven by delayed analyst dispositions.

**Every claim in the above is tagged in §1.** Before submission, re-verify the `[UNVERIFIED]`
ones or delete the corresponding clause.
