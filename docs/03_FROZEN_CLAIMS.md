# Frozen Claim List

**Frozen 26 Aug 2026, after A1, A2 and B1** (`09_WORKPLAN_phases1-3.md` §13). This is the set of things
the manuscript may assert, at the strength stated here and no higher. `04_EXPERIMENTS_AND_FINDINGS.md`
remains the authoritative record; this file is the contract between that record and the prose.

**Rule.** Nothing enters the paper that is not on this list. A claim may be *weakened* during
drafting without ceremony; strengthening one, or adding one, requires a new experiment and a
new audit.

> **No entries remain provisional as of 26 Aug 2026: E1, E2, E3 and E12 have all landed.** `02_WORKPLAN_PHASE4.md` reopens the
> matrix for a twelve-item reviewer-gap queue.
>
> **Queue status, 27 Aug 2026: ALL TWELVE DONE.** E4, E5, E6, E7, E8, E9, E10 and E11 have all
> landed since, adding **F21–F24** and **S17–S22** and nine entries to the refuted list in §E.
> The stop condition was met before the last four ran.
>
> **Four of the late experiments *changed* a claim rather than confirming one, and every one
> surfaced in the audit rather than the first run.** (i) §4.37 / F21(b): contamination costs
> power **and** a bounded amount of validity — the workplan's "power, not validity" is wrong
> for the thresholded e-value this record uses, whose p-value carries the ceiling in its
> denominator. (ii) §4.40 / F23: the ADDIS state attack is **not** out of reach on bandwidth;
> it is out of reach on volume. (iii) §4.38 / F22: the grouping optimum does **not** transfer
> across windows. (iv) §4.42 / F24: the padding attack is not uniformly cheaper outside the
> anomalous window, though it exists at every one.
>
> **H1 — E1 and E2 have both landed; H1 is now CLOSED and narrowed on two axes.** §4.34 /
> F18: randomised smoothing removes the resolution floor and with it the absorbing state, so
> H1 is stated for **finite-resolution (discrete) evidence** — though smoothing buys no
> additional reliably-detected episode, is negative-yield under an arbitrary-dependence-valid
> merge, and the continuous calibrated route is strictly dominated. §4.35 / F19: periodic
> restart *does* restore detection (LOND 18.0 → 95.0 rejections, episode recall 0.065 →
> 0.345), so H1 is also stated for **an uninterrupted controller** — and the price is exact
> and stateable, since per-epoch FDR control does not pool. Both scopes are written into the
> claim below. H1 is no longer provisional.
>
> **H2 — E12 has landed and does not upgrade it.** The triage found no public dataset with a
> genuine flow→campaign identifier, complete negatives and recoverable chronological order
> (`proto/out/E12_triage.md`). H2 therefore **stays narrow**: deployable episode heuristics on
> LSPR23. The triage record is itself the answer to the objection and is quotable as such.
>
> **Round-2 review fixes — 31 Aug 2026 (`22_review2_worklist.md`, cheap-fix pass).** Incorporating
> the second-round review. New/changed claims: (R1) a stated **group-evidence validity assumption**
> (Assumption 1) that every $\FDR$ claim is now conditional on — framing, no number. (R3) exact
> **Poisson intervals** on the benign-firing diagnostic (`t50_calib_ci.json`): the guarantee windows'
> ratios have 95% CIs that **include 1** (0.55: [0.03, 5.96]) — the diagnostic cannot prove validity,
> only fail to reject it — while 0.85 **excludes 1** ([37.26, 67.89]); the "valid window" language is
> replaced by assumption-conditional wording. **Audit:** the CIs are new numbers → checked in `t45`
> (§4.46 block, +7 assertions). (R2) the grouping table's infeasible-vs-non-zero rows are reconciled
> (caption: the margin is level-$w_0$, the metrics are e-LOND at $\alpha=2w_0$). (R6) the "any adaptive
> procedure" claim is narrowed to a security principle, and the silence-monotonicity claim is dropped
> (both weakenings). R9/R10/R11 are wording/framing (abstract trim, terminology box, feasibility
> definitions). No headline number was strengthened.
>
> **W2 reframe — 31 Aug 2026 (reviewer worklist).** The primary/headline results are moved off
> the invalid-e-value window 0.85 onto the valid **guarantee window 0.55** (with 0.62 as a second
> valid window); 0.85 is retained and labelled an *instrumented stress-test window* at every
> occurrence. This is a **reframe plus a recompute at a valid window**, not a new claim: (i) the
> padding headline now leads with 118/101 flows at 0.55 and 72/69 at 0.62 (from `t28b_reallevel`,
> already computed at all positions — no rerun); (ii) `t20_T8_matched` was **rerun at 0.55** for
> the matched-operating-points table, gaining a `per_pos` schema whose 0.85 block is byte-identical
> to the prior run (asserted in-stage and in `t45`); (iii) `tab:procedures` now dual-reports 0.55
> and 0.85 from `t21c` (re-tabulation, no rerun). **Audit:** the 0.55 frontier numbers are checked
> in `t45` (§4.19 block, +8 assertions); no headline number was *strengthened* — the padding cost
> at the valid window (≈100 flows) is smaller than the 0.85 stress figure, and the operator-cost
> gap is larger, so both moves are conservative or neutral for the paper's claims. Caveat 2 (0.85
> is not a valid-e-value window) is unchanged and now reinforced by the register.
>
> **H3(a) — E3 has landed and CLOSES it.** §4.36 / F20: the asymmetry escape is not a
> mitigation. For every precommitted weight sequence the front-load cost `L*` is finite, the
> scheme's reach is capped at `P ≤ α_t·M` — the same quantity as F1's horizon — and on real
> traffic every padding-invariant scheme that keeps the arithmetic mean's recall is defeated
> by 1 to 8 leading flows against 111 appended ones. The escape makes the attack **cheaper**.
> The robustness / power / ordering triangle is closed and C3 is complete.

---

## A. Headline claims — the three the paper is built on

| # | Claim | Evidence | Type |
|---|---|---|---|
| **H1** | **Under finite-resolution (discrete) conformal evidence and an uninterrupted controller**, for any online procedure that rejects when evidence exceeds `1/α_t`, with `α_t` of the multiplicative or lag-sum form and evidence bounded by `M = (\|C\|+1)/k`, the set of times at which any rejection is possible during a rejection-free run is **finite**, and the state is **absorbing**. Retaining feasibility over horizon `T` requires `\|C\| ≥ kT/w₀ − 1` under the max-min optimal spending sequence — 6.4×10⁸ at LSPR23 scale, 3.5×10¹⁰ for one day at 10k flows/s. | §4.13, F1, F2, §4.34, F18, §4.35, F19 | theorem + measurement |
| **H2** | **The granularity–feasibility tradeoff, for a single uninterrupted controller.** Coarsening the alerting unit reduces `T` and buys feasibility exactly — `required \|C\| = kT/w₀ − 1` in every grouping family — and it is paid for in episode-level resolution: across five families × seven bucket widths, malicious-**flow** coverage stays at 0.508–0.519 while **episode** recall falls 0.518 → 0.226. The gap is created by the choice of unit alone, not by the detector, the procedure or the budget. | §4.29, §4.9, F3, F4, §4.35 | measurement |
| **H3** | **The statistical trust layer is an attack surface, in two distinct ways.** (a) *Within-hypothesis:* for any τ > 1, no symmetric e-merging family that attains τ is τ-padding-robust; on real traffic the attack costs a median 1–134 flows and is insensitive to how realistic the padding is. The asymmetric escape is not a mitigation: every precommitted weight sequence has a finite front-load cost, and the schemes that keep the mean's recall fall to 1–8 leading flows. (b) *Across-hypothesis:* a procedure that escapes the H1 horizon by conditioning its spending index on a property of the observed evidence exposes that property — ADDIS is permanently silenced by `B* = 203` precursor episodes, exactly as its closed form predicts. | §4.16, §4.30, §4.33, §4.36, F6, F7, F17, F20 | theorem ×3 + measurement |

### Boundary conditions H1 must always be stated with

- **The resolution premise is load-bearing and must be stated.** Randomised smoothing makes
  the evidence unbounded (`inf p_u = 0`), so no state is absorbing and the hard horizon
  becomes a soft one: `P(reject) = min(1, α_t·(\|C\|+1))`, which decays to zero exactly as
  `α_t` does. §4.34 measures what lies past the boundary: structural silence 90.1% → 0.0% at
  the guarantee window, but the set of malicious episodes detected with probability ≥ 0.9 is
  **18 under both rules**, `Var(R_T) = 7.14`, and the alert set differs by 36% between
  randomisation seeds. Under Hommel — the merge valid under the arbitrary dependence the
  record's own aggregation satisfies for free — the yield is **negative** (12.0 against 18.0)
  and nothing is detected with probability ≥ 0.9. The continuous calibrated route is strictly
  dominated for every calibrator, Vovk's included, and boosting closes the gap only to a
  constant factor λ.

- **The uninterrupted premise is load-bearing too, and its price is exact.** Restarting the
  controller at wall-clock epochs restores detection — LOND 18.0 → 95.0 rejections and episode
  recall 0.065 → 0.345 at FDP 0.000, within 5% of what oracle horizon knowledge buys — because
  each epoch is a fresh horizon of `T/n` (§4.35, F19). What is given up is the deployment-level
  guarantee: per-epoch FDR control does not pool, and `pooled FDR = 1 − (1 − q)^n` is
  attainable (0.185 at four epochs). mFDR does pool; LOND, LORD++ and e-LOND control FDR.
  Half the gain is free — resetting the spending index costs no budget — and half is bought
  by spending `n·q`.

- **Two families escape** (§4.20): ADDIS, because its index counts *tested* hypotheses and
  threshold conformal evidence never produces one — and online e-BH, because its threshold is
  a fixed point over the whole history, so a rejection-free prefix is not absorbing.
- **Each escape has a measured price.** ADDIS's guarantee needs uniformly conservative null
  p-values, violated maximally here (measured `P(P/τ ≤ x | P ≤ τ) = 1.0` at every x), and it
  does not control FDR once k > 1 (FDP 0.033 → 0.707 at k = 1 → 1000). online e-BH escapes
  the absorbing state but not the calibration budget — `\|C\| ≥ T/(αR) − 1`, still linear in T
  — and buys **no** additional power here: 72 rejections against e-LOND's 72.
- **e-GAI does not escape**, by its own authors' equivalence e-LORD = e-LOND; and mem-e-LORD,
  the published α-death fix, is identical to e-LORD before the first rejection.

### Boundary condition H2 must always be stated with

- **The resolution cost is the fixed-ground-truth BLUR, not the moving-denominator recall**
  (§4.44 / W7, added 31 Aug 2026). Against a fixed atomic ground truth — the 5-minute src-dst
  malicious episodes (1,899 at window 0.55, 1,973 at 0.85) — each issued alert blurs together an
  increasing number of atomic units as the bucket coarsens, **1 → ~20–40** (monotone under every
  γ). That blur is the denominator- and γ-invariant resolution cost. Two cautions travel with it:
  (i) the **fixed-denominator coverage RISES** with coarsening (0.020 → 0.385 at 0.55), so
  "recall falls as the unit coarsens" is substantially a moving-denominator artifact; and (ii) that
  fall is **γ-dependent** — it holds under the **oracle uniform γ** that `fig3`/`t26_H4_5pos` plot
  but REVERSES under the paper's primary `γ ∝ j⁻¹·⁶` (recall *rises* 0.077 → 0.123 at 0.55). State
  the episode-recall decline as the oracle-sequence, moving-denominator view; rest the C2 cost on
  the blur. **`fig3`'s middle panel now plots the blur (all five windows), not the oracle-γ recall**
  (§4.44, resolved 31 Aug 2026), so the headline figure's resolution cost is γ-invariant. **Audit:**
  new numbers checked in `t45` (§4.44 block, +6 assertions); `recall(moving)` at 2 h matches `t21c`
  exactly, so the poly behaviour is genuine, not a bug. This weakens the original "recall falls
  monotonically" wording (permitted) and adds a measured hardening.

- **Coarsening is not the only lever.** Periodic restart divides the hypothesis count a single
  controller run must survive by the same factor and gives the identical margin formula
  `M·c/T_ep − 1`, but preserves episode resolution: hourly restart at 1 h grouping reaches
  episode recall **0.406** against **0.103** for 6 h coarsening uninterrupted (§4.35). The
  tradeoff is therefore between resolution and the *pooled guarantee*, not resolution and
  feasibility as such, and H2 is a statement about one uninterrupted controller.

### Boundary condition H3(a) must always be stated with

- **The asymmetry escape is closed, and closing it is part of the result.** A precommitted
  position-indexed weighting is valid under arbitrary dependence and padding-invariant, so it
  is the natural escape — but its reach is capped at `P ≤ α_t·M` positions and the number of
  leading zero-evidence flows that defeat it, `L* = min{L : Σ_{i>L} w_i < β}`, is finite for
  every summable weight sequence. Measured: 1–8 leading flows against 111 appended, at equal
  episode recall (§4.36). Quote the triangle — padding-invariance, usable power, resistance to
  attacker-controlled ordering, pick two — rather than the theorem alone.

### Boundary conditions H3(b) must always be stated with

- The attack is **exact and structural in VOLUME** — 9.2×10⁷ flows on this stream, 37.5× the
  deployment window's entire observed flow count and 5.6× the whole dataset. Its price is
  `λ\|C\|·[(τ−λ)w₀\|C\|]^{0.625}/k^{1.625}` — set by the calibration budget, not by any
  implementation weakness. **It is *not* structural in bandwidth, and no sentence may imply
  it is:** §4.40 / F23 prices those flows at 36.1 GB over the 2.4 h deployment span, i.e.
  33.4 Mbit/s from four hosts at 10 Mbit/s each. The barrier is that an attacker who
  multiplies a monitored network's flow count by 37.5 is not hiding — not that they cannot
  afford the traffic.
- It matters because (i) against ADDIS it is the **cheaper** attack, break-even at 2.7 episodes
  against a window of 255, and (ii) for **101 of ADDIS's 147 detections the minimal
  suppressing pad already advances the index**, so the two surfaces are one operation.
- It survives **grey-box**; **black-box** is blocked *on this stream* by the anti-conservatism
  of §4.31, which is not a defence anyone would choose.

---

## B. Supporting claims — used inside the three, never as contributions

| # | Claim | Evidence |
|---|---|---|
| S1 | **Feasibility is not detection.** A second, unsupervised detector (Isolation Forest) has a feasibility margin identical to HistGradientBoosting's to every digit — the margin depends only on `\|C\|`, k and T, never on the scores — and tail reach **0.000** at all ten configurations: 152 detections against 0. | §4.22, F5 |
| S2 | **k = 1 is the only feasible rank and the least reliable one.** Margin +0.436 → −0.999 as k goes 1 → 1000, with zero rejections at every k ≥ 10; worst-case benign firing 50.9× nominal at k = 1 against 6.8× at k = 1000. | §4.23, F14 |
| S3 | **The known fix for conditional validity works and is priced by the quantity that creates the problem.** Bates calibration-conditional p-values hold δ in every cell and cost 38–78% of the ceiling at k = 1 against 4% at k = 1000; at k = 1, δ = 0.10 the median configuration goes feasible (+0.436) → infeasible (−0.376). | §4.26, F10, F11 |
| S4 | **Boosting returns exactly nothing — for the discrete evidence the record uses.** `b* = 1` for any two-point e-value, against `√(2τ)` for a genuine continuous one; on real scores `b* < 1` (median 0.368). The evidence is already extremal, for the same reason the feasibility boundary exists. §4.34 derives `b* = (τ/λ)^λ` for the calibrator family, recovers `√(2τ)` at λ = ½ as a cross-check, and shows that even boosted, the calibrated route is the direct p-value threshold shrunk by λ. | §4.28, F15, §4.34, F18 |
| S5 | **The spending sequence is a stronger lever than the error target.** A twenty-fold q sweep moves median episode recall by 0.088; switching γ at fixed q moves it by 0.188. Relaxing q buys feasibility strictly linearly and no faster (measured (margin+1) ratios 0.200/1.000/2.000/4.000 against predicted 0.2/1/2/4). | §4.24, F13 |
| S6 | **Every method sits on the achievable frontier at its own budget** (gaps ≤ 0.040 across both the primary 0.55 and stress-test 0.85 windows, and +0.000 for every H6 configuration); what online error control removes is the operator's *choice* of point. At the **primary guarantee window** e-LOND operates at 18 alerts / recall 0.065 / FDP 0.000 against a frontier of recall 0.378 on 104 alerts at the same zero error. | §4.19, §4.20, F13 |
| S7 | **No cap policy is both powerful and unattackable.** Four policies, all valid, all failing differently; truncation's two failure modes move in opposite directions with `n₀` (p50: 71/275 detected, 1 padding flow to suppress; p999: 6 detected, 3,560 flows). | §4.12, §4.25, F8 |
| S8 | **The dilution attack is insensitive to how realistic the padding is.** Five pools including a black-box one: identical median cost, because suppression depends on the pool only through `τ − μ` and τ exceeds the largest μ by four orders of magnitude. | §4.30, F6 |
| S9 | **The alert labels are not an under-estimate of truth.** 96.1% agreement under a rule whose structural indicator is label-derived (independent of each episode's own label, not of the labelling process); the label-independent part establishes that **3 of the 5** alerts the label calls false sit on a red-team confirmed-compromise host. FDP is narrowed in direction, not corrected to a value. | §4.32, F16 |
| S10 | **Calibration drift is mild** (1.3–2.0× on AIT, median 1.94× on LSPR23), and the one position where the evidence is not a valid e-value is a **localised** anomaly: three host pairs of 25,864 carry 44 of 46 firings, and removing them gives 2.22×, inside the other positions' range. Label error is the best-supported cause — the tail sits 3.8×/1.5× closer to malicious traffic than benign flows matched on the same host pair and destination port, and its mean is closer to the malicious population on 28 of 31 features — but a shift confined to the extreme tail is not separable from it here. | §4.31 (incl. E5), F9 |
| S11 | **Analyst feedback tracks the target while latency is short and fails as it grows**; the comparison is at matched budget throughout. In WALL-CLOCK terms "short" means minutes, not alerts: FDP 0.053 at zero delay, **0.402 at fifteen minutes**, 0.877 at a 24 h disposition cycle against 0.887 with no feedback. The conclusion is not controller-specific — proportional, PI and Robbins-Monro quantile targeting agree from 4 h onward — and the controller sits at its actuator limit for 95–100% of steps, so most of its measured advantage is the conservative threshold rather than the steering. | §4.14, §4.19, §4.39, F13 |
| S12 | **The discrete rank-1 rule queries the one point of the calibration tail that is well calibrated.** Benign ratio 1.07× at `a = 1/M` against 3–8× in the mid-tail at position 0.55 (1,817.7 benign flows against 228.8 nominal at `a = 10⁻⁴`). Smoothing, and any rank-based merge using `p_(k)` for `k > 1`, moves the operating point into that region — which is what puts the smoothed FDP above `q`, not the randomisation. | §4.34, F18 |
| S13 | **ADDIS's escape from the feasibility horizon is a property of the aggregation rule, not of the evidence resolution.** Under the record's mean-e rule the spending index advances on 0.19% of episodes; under any rank-based merge it advances on 85–96%, smoothed or discrete alike, and the escape disappears. Smoothing moves it by less than 10⁻⁴. | §4.34, F18 |
| S14 | **Per-epoch error control does not aggregate to the deployment.** mFDR pools by the mediant inequality; FDR does not, and `pooled FDR = 1 − (1 − q)^n` is attainable under per-epoch FDR control at `q`. | §4.35, F19 |
| S15 | **Restart's gain decomposes: the spending-index reset is free, the budget reset is not.** 46% of the gain survives a precommitted allocation summing to `q`; the rest requires spending `n·q`. | §4.35, F19 |
| S16 | **The front-load cost and the feasibility horizon are the same lemma on two axes.** `L*` is a tail sum of the weight sequence over within-episode position; §4.13's `Δ*` is a tail sum of the spending sequence over stream time. Both are finite by summability. | §4.36, §4.13, F20 |
| S17 | **The headline grouping and cap were not selected on the window they are evaluated on, and the evidence is that both are the *worst* configuration on their grid at some window.** The frozen grouping (`src-dst`, 2 h) is the worst **feasible** configuration of 35 at position 0.70 and within 10⁻⁴ of the worst at 0.62 and 0.77; the frozen cap `n₀ = p99` is the worst of six at two of five windows. The cap choice transfers (worst previous-window normalised regret 0.070) and its power-optimal value `n₀ = 2` is defeated by **one** front-load flow. The grouping choice does **not** transfer (0.991), so coverage numbers must be stated as *what the deployable grouping achieves*, never as the best achievable. | §4.38, F22 |
| S18 | **Bandwidth does not separate the two attack surfaces; volume against the monitored population does.** Suppressing one alert is 34 flows = 13.3 kB = 15 bit/s over the 2 h bucket from one host. The ADDIS state attack is 92,015,637 flows = 36.1 GB = 33.4 Mbit/s over position 0.85's own 2.4 h deployment span — four hosts at 10 Mbit/s, not out of reach. What is out of reach is 37.5× the deployment window's entire observed flow count, against 1.4×10⁻⁵ for suppressing an alert. | §4.40, F23 |
| S19 | **The deterministic tie-break is a reproducibility convention, not a load-bearing choice.** At most 1.3% of episodes share a first timestamp, the largest tie block is 3, and 50 randomised within-timestamp orders change none of 36 statistics at either window — with the randomisation verified to move ~50% of the movable positions per draw. | §4.41, F24 |
| S20 | **The padding attack is not an artefact of the position-0.85 anomaly.** Median suppression cost 3 / 4.5 / 62 / 35 flows at positions 0.55 / 0.62 / 0.70 / 0.77 against 35.25 at 0.85 — measurable everywhere, cheaper at two of the four, and dearer at one. The black-box pool has mean e exactly 0 and P(fire) exactly 0 at **all five** windows. | §4.42, F24 |
| S21 | **Calibration contamination is priced in flows, not in a rate, and at `k = 1` the adversarial tolerance is zero.** The rule is one order statistic, so one mislabelled high-scoring attack flow takes recall from 0.065 → 0.000 (position 0.55) and 0.282 → 0.000 (0.85). For random mislabels the scale is `ε* = 1/(N·q₀)` = **1.1–1.3 flows**, `q₀` being the contamination pool's exceedance rate (0.90, 0.76) — *not* the deployment window's malicious firing rate. `k` is the contamination budget as well as the power and reliability parameter, and F14's feasibility constraint has already spent it. | §4.37, F21 |
| S22 | **Contamination has a second, anti-conservative channel, and it is bounded.** The threshold conformal p-value carries the ceiling `M = \|C\|+1` in its denominator, so a contaminating flow that does *not* clear the threshold inflates evidence by exactly `(1+ε)` and `E[e] ≤ 1+ε`. Driven with the whole available stealth budget, `q = 0.05` becomes 0.0542 with recall unchanged — while **one** adversarial flow takes recall to zero. Power is unbounded, validity is not. Multiplicative on top of §4.31's own conservatism; stated for LOND and LORD++ only. | §4.37, F21(b) |

---

## C. Caveats that must appear wherever the relevant number does

1. **Horizon knowledge.** The rejection threshold `τ = T/w₀` and the horizon-uniform γ = 1/T
   both use `T`, the number of episodes in the evaluation window. That is an **oracle**. It is
   labelled in §4.20 and must be labelled in every table that uses it. §4.20's misspecification
   sweep prices it: LOND/LORD++ tolerate 2×/1×, e-GAI 5×, online e-BH 100×, ADDIS none needed.
2. **Position 0.85 is not a valid-e-value window.** Every FDP computed there is a measurement
   against labels, not a guarantee. The direction of the label error is known (§4.32) and it
   inflates the reported FDP, so the numbers are conservative — but the guarantee does not
   attach, and no sentence may imply it does.
3. **LSPR23 has no flow→campaign ground truth.** The units are **episodes**, never incidents.
   `Category`, `Severity`, `SigID` and `Expoid_dst` are empty for 1,630,732 of 1,644,599
   malicious flows.
4. **Padding costs are a lower bound.** μ and `P(fire)` are computed from the deployment
   window's realised e-values, so the attacker is credited with exact knowledge of the
   detector's output there (§4.30). **§4.42 inherits the same caveat** for the cross-window
   costs, and states it.
5. **The attacker's ability to place pad flows rests on a FLOW-LEVEL feature set, and that
   scope must be stated.** Pads must land on the target's own `(SrcIP, DstIP)` pair, and the
   claim that ordinary attacker traffic to the victim scores like ordinary traffic anywhere
   rests on the detector's 33 features carrying no endpoint identity, so a score cannot depend
   on the host pair. **For the flow-level detector this is now CONFIRMED by a controlled
   experiment (§4.45 / W3, 31 Aug 2026), not argued by construction:** 20,000 real
   black-box-service flows run through the shipped detector fire at rate **exactly 0**, and
   injecting them dilutes `E(G)=S/(m+r)` to suppression at exactly the closed-form `r*` on
   **18/18** guarantee-window and **72/72** stress-window detections (median `r*` reproduces
   §4.30 / Table I). A label-matched empirical pool still cannot be built (all 674 detected
   episodes sit on host pairs that are 100% malicious, F6), but the controlled dilution replaces
   the "by construction" framing. **The host-conditioned boundary is now measured (§4.47 / R7,
   31 Aug 2026):** a competent host-conditioned detector (six strictly-causal host features, AUROC
   0.95/1.00, no label leakage) is built, and at the **guarantee window the transfer still holds** —
   ordinary pads carrying the attacked pair's real causal context fire **0** over 4×10⁶ trials, and
   the detector fires on **0 of 2.29M** real benign flows. At the **stress window** grafted pads fire
   (0.43) but the detector fires on only **3 of 1.64M** real benign flows, so that firing is an
   **out-of-distribution** extrapolation — the 100%-malicious-pair structure means no real
   ordinary-to-victim traffic exists to settle the high-volume regime, which needs a benign-inclusive
   testbed. **Audit:** new numbers checked in `t45` (§4.45 and §4.47 blocks). Say this wherever a
   padding cost appears.
6. **The five window positions are quasi-independent deployments of one exercise**, not five
   datasets. They share a network, a red team and a labelling pipeline.
7. **Every number in this record assumes a clean benign calibration set, and that assumption
   is worth ONE FLOW.** At `k = 1` the whole conformal rule is the calibration maximum, so a
   single mislabelled high-scoring attack flow in the calibration window takes episode recall
   to zero at both windows measured (§4.37, F21). The tolerable quantity is a **count**, not a
   rate: zero adversarially, and 1.1–1.3 flows for random mislabelling. This caveat governs
   every detection number in the paper and must appear with the method, not in a limitations
   paragraph.
8. **Contamination also has a bounded anti-conservative channel.** A mislabelled flow that
   scores *below* the calibration maximum inflates `\|C\|` and therefore the ceiling, so every
   firing flow's p-value falls by exactly `(1+ε)` (§4.37, F21(b)). Wherever an FDR guarantee is
   stated, it is `q(1+ε)` under contamination at rate `ε` — for LOND and LORD++ only, and
   **multiplicatively on top of** caveat 2's window-0.85 anti-conservatism, not instead of it.
9. **The ADDIS state attack's absolute cost is dataset-specific**; the closed form and the
   mechanism are not. Its *operational* units (§4.40) are dataset-specific twice over: they
   depend on `\|C\|` for the flow count and on the deployment window's own span for the rate.
10. **Two of the A2 audit's four indicators are not discriminative** (§4.32), and the audit
   says so: temporal concurrency separates 100.0% of alerts from 86.0% of non-alerted benign
   episodes. Only the strict rule's two branches carry weight.

---

## D. Non-claims — must appear in the paper, explicitly

1. **We do not claim online FDR control is unusable.** We claim it has a finite feasibility
   horizon at security scale under finite-resolution conformal evidence, that coarsening the
   alerting unit buys feasibility at a measured cost in resolution, and that the aggregation
   the coarsening requires is attackable.
2. **We do not claim a better detector.** The detector is a vehicle; two of them give the same
   feasibility margin to every digit (S1).
3. **We do not claim dependence breaks online FDR.** It does not, once evidence is e-valued;
   that is prior work and is dissolved, not contributed.
4. **We do not claim calibration drift invalidates conformal evidence.** Measured and refuted
   (S10). The one anti-conservative window is a label error.
5. **We do not claim the ADDIS state attack is cheap in bytes**, deployable at scale, or
   observed in the wild — but we must not claim it is expensive in bytes either. It is exact,
   grey-box-feasible, priced by `\|C\|`, and **structural in volume rather than in bandwidth**:
   33.4 Mbit/s from four hosts, against 37.5× the deployment window's entire flow count
   (§4.40, F23). The honest sentence is "conspicuous", not "unaffordable".
6. **We do not claim to have corrected LSPR23's labels, nor to have proved they are wrong.**
   We identify a specific, reproducible set of host pairs that carry 96% of the anomaly, show
   that a new benign mode and duplicated records do not explain it, and state that label error
   is the best-supported remaining explanation — while a shift confined to the extreme tail
   would look the same and cannot be separated without the exercise's own logs.
7. **We do not claim incident-level or campaign-level results.** Episodes only.
8. **We do not claim the reported coverage is the best achievable.** The headline grouping is
   the worst *feasible* configuration of 35 on flow coverage at one of five windows and within
   10⁻⁴ of the worst at two more, and no selection rule recovers the optimum from a previous
   window (worst normalised regret 0.991). Coverage numbers are **what the deployable grouping
   achieves** (§4.38, F22). That the frozen choice is near-worst is our evidence *against*
   test-window tuning, and should be presented as such rather than hidden.
9. **We do not claim generality beyond one dataset.** One live-fire exercise, five window
   positions, two detectors, two seeds. A second dataset with genuine campaign labels would
   be the single item that could change a headline number, and **no such public dataset
   exists**: the E12 triage examined ~40 candidates against two catalogues covering 89 and 62
   datasets and found none with a genuine flow→campaign identifier, complete negatives and
   recoverable chronological order (`proto/out/E12_triage.md`). Where instance-like structure
   exists it is either an attack *class* label (MITRE technique strings) or is itself produced
   by a host-plus-time-window correlation heuristic — the very construct under test. Our own
   dataset family is closed too: LSPR24 (Zenodo 14900873) carries binary and detector-category
   labels but no campaign column, and its attack narratives carry no execution timestamps,
   IPs or segments at all.
10. **We do not claim the padding attack requires detector access.** It does not (S8) — but the
    *cost estimates* assume it (caveat 4).
11. **We do not claim the feasibility theorem covers every online procedure.** It covers two
    structural families; two procedures escape, and the escapes are part of the result.
12. **We do not claim the conformal-resolution/online-testing incompatibility was unknown.** Huo
    et al. (NeurIPS 2024) state the `1/(|C|+1)` floor and its consequence for p-value-based online
    testing, and observe α-death empirically for LOND/SAFFRON/ADDIS on conformal evidence (§6). C1
    claims the *characterisation*: a finite absorbing horizon for two families covering the e-value
    procedures too, the exact calibration–horizon rate, which procedures escape and by which
    mechanism, and what the escapes cost at security scale. Cite proactively; never imply priority
    over the phenomenon itself.
13. **We do not claim Surface B reaches online e-BH.** It is a property of an evidence-conditioned
    spending index, exemplified by ADDIS. Online e-BH escapes the horizon by a history-wide fixed
    point instead, and we do not attack it.
14. **We do not claim host-aware detection is no defence against padding in general.** We claim the
    particular strictly-causal host conditioning we build does not stop it on the two organisations
    and nine episodes replayed end-to-end, with distinct-peer counts pinned and the flood regime
    untested.
15. **We do not claim the UAI 2026 procedures are without value.** They are strict improvements over
    e-LOND and r-LOND under arbitrary dependence and we report them as such. We claim only that the
    improvement is *orthogonal to feasibility*: the donation construction's boost is capped at
    `1/(1-alpha)` before the first rejection because its wealth is `gamma`-weighted and `gamma` sums
    to one, and the closure's level is capped by the zero-evidence subset. Measured, they buy `+1`
    and `+0` true detections over ten window-seed configurations (S4.56).
16. **We do not claim the donation cold-start bound holds at all times.** It is a *cold-start*
    statement — the state `cor:budget` is about. Once `alpha(R+1) >= 1` (i.e. after `1/alpha = 20`
    rejections) the donated wealth can saturate the denominator and the level is unbounded. That
    regime never occurs in our runs (`n_unbounded_level = 0` in all 20 rows) but must never be
    quoted away.
17. **We do not claim the decision-deadline family escapes the horizon.** We claim deferring the
    decision leaves *at-arrival* feasibility essentially unchanged (identical at three of five
    windows) and buys power only by revisiting, so its price is alerting latency. Nor do we claim
    it never helps: it converts to power at 0.62 seed 0 (13 -> 32 detections).
18. **We do not claim to have resolved the inconsistency in the source's Eq. (102).** Its per-step
    top-`r` sets are not nested (so the procedure un-rejects, contradicting the ARC premise), yet
    their union is not certified by the balance its control proof rests on. We compute both, report
    the literal snapshot, flag the alternative as not source-certified, and pin both instances as
    regression tests. No claim in the paper depends on the choice.
19. **We do not claim `e-TOAD` as printed in its source.** Our implementation follows a corrected
    reading of two displayed statements in its Appendix D.2 — the active-set inequality and the
    step-up upper limit — because only that reading reproduces the source's own stated limiting
    cases (`d_t = t` is e-LOND, `d_t = infinity` is online e-BH), which the self-test verifies. The
    correction must be stated wherever the procedure is named.
20. **We do not claim group-level calibration removes `assump:groupval`.** It *relocates* the
    premise to exchangeability of grouped null units under attacker-influenceable metadata. Arity
    is the failure mode we measure (max statistic: rank correlation +0.41, worst arity bin 15.3x
    the nominal rate); the full premise also conditions on the trained detector, the chronological
    split, the grouping key and time effects, none of which S4.57 establishes.
21. **We do not claim the group construction is attack-robust — only padding-robust, and we have
    now priced the other attack.** Appending flows to a *fixed* group cannot lower its maximum
    (t57: 110/110 … 152/152 still firing after pads). But an adversary that **creates** groups pushes
    a target past a cold-start window only **65–86 groups** wide, and S4.61 measures the cost:
    **62–207 inserted hypotheses** suppress every group-MAX detection. *Group validity by design plus
    padding robustness does not buy attack resistance; it buys resistance to one attack while making
    the other far cheaper.* The trilemma R2d anticipated is therefore **dropped**: it is not
    "valid + robust + silent, pick two" but "valid + robust *against appending* + silent".
22. **We do not claim the group-vs-flow comparison isolates calibration granularity.** The baseline
    merges per-flow e-values while the group arm conformalises a raw group statistic. The
    *feasibility* conclusion is unaffected (it is arithmetic in `|C|`), and the first-fire positions
    show the statistic does not cause the zeros, but the detection counts differ in two respects.
23. **We do not claim 0.85's 42 group-calibrated detections are guarantee-bearing.** That window's
    benign firing rate is 51x nominal (S4.31), so its evidence is not a valid e-value under either
    calibration. It is reported for mechanism only, exactly as elsewhere.
24. **We do not claim the calendar figure is the law.** The scale-free statement is the *count*
    ratio `k/c_0`; the calendar requirement is that law times the two windows' group-rate ratio and
    is dataset-specific (8.5x-47.0x here).
25. **We do not claim the canonical key-hash order is a security mechanism.** It is a
    *timing-independent canonicalization*, and it removes the *timing* lever and the
    `M_j`-perturbation, nothing more. Three limits, all measured: (i) the sort key is own-key-only,
    so *appending* flows moves no other group, but a group's **absolute rank** still depends on which
    other keys are present, so an adversary that **creates** keys does move ranks (see non-claim 21);
    (ii) with a **public** seed the hash is grindable over the attacker-selectable `(SrcIP, DstIP)` —
    at a feasible prefix of 1.6–2.6%, 100 candidate keys land one inside it with probability
    0.80–0.93, and a single draw lands **outside** it with probability >= 0.974, so evading detection
    by grinding is nearly free; (iii) the **keyed** variant's seed `KEYED_SEED` is a **public
    constant** in the artifact, a reproducibility stand-in and not a secret. A deployment wanting
    grinding resistance must supply an external, private, rotated seed — a threat-model assumption we
    price but do not make.
26. **We do not claim the canonical order's detection counts are a better estimate of achievable
    power.** They are one draw from the ensemble of pre-committed evidence-independent orders
    (S4.58): the canonical draw sits at the ensemble maximum at 0.62 and below the median at
    0.70/0.77. What is claimed is that first-flow arrival is the *top* of that ensemble at every
    window and seed where anything detects, so it cannot be the headline. "Upper bound" means upper
    over the orders we **audit** (6 named + 50 random), not a proven maximum over all pre-committed
    evidence-independent orders; we have no such proof.
27. **We do not claim the canonical-order median padding costs are rates.** At 0.55 and 0.62 they are
    medians of n=3 and n=11 individually-priced episodes and are reported as such (23, 24, 33 at
    0.55). The order-robust figure is the per-order median across 50 orders.
28. **We do not claim every order-dependent number in the paper has been recomputed under the
    canonical order.** `tab:main`'s detections and padding costs, the suppression demonstration and
    the ordering ensemble have. Results that are a *contrast* between two procedures on one stream
    (smoothing, restart, weighting, controller comparisons) compute both legs under the same order
    and remain on first-flow; the conventions paragraph states this.
29. **We do not claim the red-team record gives label-independent confirmation that an alert is a
    true positive.** Every attributed alert sits on a labelled-malicious episode (S4.59,
    `frac_attributed_on_benign == 0.0`), and the LSPR23 labels were derived from this same exercise.
    What the record supplies non-circularly is the **count of distinct attacker-defined actions
    inside an alert's cell** — a decomposition of the attack the labels do not contain.
30. **We do not claim the red-team record CORROBORATES the blur curve — only that it agrees in
    direction.** A null that *rotates the red-team timeline* against the stream reproduces the
    observed counts at **18 of 19** cells (S4.59), so the rise in steps-per-alert is a wider bucket
    capturing more submissions rather than alert-level correspondence. The external unit agrees in
    direction and is too coarse to discriminate; the resolution cost survives the substitution but is
    not independently confirmed by it. The record is also usable at only **3 of 10** (window, order)
    cells: at 0.55/0.62 the issued alerts sit in the feasible prefix and predate the exercise's
    reporting period (under 10% overlap it in time), and at 0.85 only **2 of 17** tasks with a timed
    step declare a segment or file a compromise report. Elsewhere it is silent, not negative.
31. **We do not claim the 24-hour bucket carries any external evidence.** At that width both nulls
    tie the observation exactly, because every submission falls in **one** daily bucket so no
    permutation or rotation can move a step between alerts. The nulls are *degenerate* there; the
    spatial conjunct is **not** vacuous (at 0.70/first-flow it admits 12 of 30 temporally overlapping
    alerts). Only sub-daily widths inform, and the rank correlations are read on those.
32. **We do not claim the attribution uses two independent channels.** Across every row the
    compromise-IP conjunct adds **no** alert the segment conjunct did not already admit: the whole
    positive result rests on **six** coarse segment labels. Nor is the segment map independently
    *verified* — the 83-agree/0-disagree check applies the map and then checks it, which is a real
    smoke test and not proof.
33. **We do not claim the attribution rule is the only defensible one.** It uses the alert's
    **bucket span** (what the hypothesis formally covers), a task's declared segments and its
    compromise IPs. Re-pricing the same rule against each episode's actual first-to-last **flow span**
    lowers the magnitudes (0.70 key-hash 300 s: 4.29 → 3.13; 3600 s: 18.50 → 12.00) and preserves
    every zero-window conclusion; both are reported. We pre-committed to one rule and report two nulls
    rather than searching over rules.
34. **We do not claim the pure-null arm checks the body's simulated 4.5% early-false-rejection
    rate.** Zero rejections across the benign-only streams is *consistency*, not a test: the 10 rows
    are 5 overlapping windows counted under 2 orders, **P(zero | true rate 4.5%) = 0.79**, and the
    comparison is not like-for-like (the 4.5% is synthetic benign N(0,1) at a stated `|C|`; this is
    real benign episodes at `|C|` ≈ 1.8–2.4M, and the 2.2% figure is LORD++ rather than e-LOND). The
    body's 4.5% stands as a **scoped simulation claim** and is labelled as one.
35. **We do not claim episode-thinning is the full counterfactual for a low-prevalence SOC.** It is
    "the same detector, the same calibration set, fewer attack hypotheses". A real low-prevalence
    deployment would also have a different detector, a different calibration corpus and different
    benign traffic. What it *does* isolate — and this is the claim — is that base rate alone moves
    detection to zero while leaving feasibility untouched.
36. **We do not claim thinning cannot help the controller.** It provably can under *deletion*:
    removing a hypothesis shifts every later one into a higher `alpha_t`, and S4.60 carries the
    counterexample. That is why the primary mechanism is index-preserving (T, the margin and every
    survivor's level held exactly fixed); the two agree to within 0.02 in bootstrap probability, and
    under deletion the margin *rises* by up to +0.0129 while detection still collapses.
37. **We do not claim insertion beats padding for suppressing a single alert.** It does not, at
    **12 of 12** cells (S4.61): the targeted cost is 434–5,674 inserted hypotheses against padding's
    6–5,202 flows. The claim is the *other* one — insertion silences the **whole window** for 217–813
    hypotheses, and works where padding provably cannot.
38. **We do not claim the window-silencing ratio is exact.** `sum(pads_real)` is an **upper** bound
    on the cost of silencing a window by padding: suppressing an early rejection lowers `R` and can
    make later detections cheaper or vanish. The ratio (median 6x, max 1,058,220x) inherits that, and
    its maximum is heavy-tail driven — at 0.85 first-flow the top 10 of 72 pad costs carry ~100% of
    the sum. The verdicts are also stated at **1 flow per inserted group**; at 2 they fall from
    10/12 to 7/12.
39. **We do not claim the keyspace-trial counts are operational figures.** Three conditions:
    the seed must be **public** (the keyed arm has no trial count at all — it cannot be ranked
    offline); the adversary needs that many endpoint pairs it can actually send between; and
    **the artefact hashes pandas category codes, not raw IPs**, so introducing addresses would
    renumber them. The counts indicate the search's *size*.

40. **We do not claim a keyed hash is worthless, nor that it is a defence.** `[ADDED round 8;
    MEASURED by `t63_blindkey`]` The paper used to say "the keyed seed removes the search, not the
    attack" in `sec:attack` while `sec:transfer` said the keyed channel is "one we do not analyse" —
    both ours, and contradictory. Measured: **84/84 targets fall in every draw at 10⁶ blindly
    instantiated keys**, so the seed does not stop the attack; but at matched reliability (N₉₉
    against certain public suppression) it multiplies the *instantiated*-key cost by **2.1–89×,
    median 19×**, because every blind trial is real traffic between distinct endpoint pairs rather
    than a free offline hash. What we claim is a **partial mitigation for targeted insertion, and
    none at all for Surface A padding**. Two scope conditions travel with it: the cost model places
    insertions in the target's own bucket, which is optimal only because that bucket is the **first
    of its window at every cell measured** (where an earlier bucket exists the adversary inserts
    there and precedes the target with probability 1); and every budget is located on a
    six-per-decade grid, so each N is exact to within **1.48×** and no further.

41. **We do not claim the arity dependence of the group `max` statistic refutes group
    exchangeability.** `[ADDED round 8 — retracts §4.57's original reading]` It does not: a statistic
    may be strongly arity-dependent while calibration and null test groups stay perfectly
    exchangeable. Direct group calibration **does** discharge `assump:groupval`. What we claim is
    (i) group exchangeability is still a deployment assumption and adaptive group formation — this
    paper's threat model — breaks it by construction; (ii) the guarantee is **marginal, not
    arity-conditional**, which `t57`'s test-side read now measures — marginal coverage 0.55–2.32×
    nominal against per-stratum 0.13×–**24.2×** under `max` (0.00–5.6× under `mean`) — and arity is
    the stratum the adversary chooses; and (iii) the construction is infeasible regardless (`CEIL`
    falls 40–49×, detection → 0). The original arity bins were computed *inside* the calibration set,
    so their marginal is 1% to within 8.9×10⁻⁵ **by construction** and they measure no coverage
    property at all; they are retained only as a description of that set.


42. **We do not claim any window has been empirically validated.** `[ADDED round 8]` The benign-tail
    diagnostic rests on 1, 1, 3, 2 and 46 firings out of 1.6–2.3M; the 0.55 interval on the ratio is
    [0.027, 5.96]. It refutes 0.85 and cannot establish the other four. 0.55 and 0.62 are the
    **primary** and **replication** windows because they were pre-committed as the analysis pair, not
    because a diagnostic selected them. Every guarantee-bearing statement, at every window, is
    conditional on `assump:groupval`.

43. **We do not claim the operational evaluation is order-free.** `[ADDED round 8]` Only the
    *frontier* is, and that is measured (`t64`), not assumed — its tie-break is by stream position.
    Every controller row moves with the order: at 0.55 e-LOND goes 18 → **3** alerts and the gap to
    the zero-error frontier widens 5.8× → **34.7×**. The slot rule and the no-feedback threshold are
    order-free by construction and verified unchanged. Numbers quoted from smoothing, restart,
    asymmetric weighting and the q/γ sweeps remain **first-flow paired analyses** and are labelled as
    such.

---

## E. What was tested and did not survive — report as negative results

| Refuted | Where |
|---|---|
| Calibration drift catastrophically invalidates the evidence | §4.4, S10 |
| Inflation (padding a benign group into a false discovery) works as an attack | §4.6, F12 |
| Fragmentation (splitting a campaign across groups) works as an attack | §4.7, F12 |
| Boosting recovers power for threshold conformal e-values | §4.28, S4 |
| mem-e-LORD, the published α-death fix, helps before the first rejection | §4.20, F2 |
| Raising k trades power for conditional reliability | §4.23, S2 |
| Mondrian (stratified) conformal repairs the position-0.85 anti-conservatism | §4.31 |
| Black-box ADDIS state manipulation is practical on this stream | §4.33 |
| Asymmetric (precommitted-weight) aggregation is a usable mitigation for the padding attack | §4.36, F20 |
| Randomised smoothing of the conformal p-value restores useful detection | §4.34, F18 |
| Most restart epochs go silent before their first rejection | §4.35 — no epoch yields zero discoveries at the guarantee window, at any epoch length |
| A p-to-e calibrator (Vovk, or `λp^{λ−1}`) recovers power for threshold conformal evidence | §4.34, F18 |
| Contamination costs power but never validity | §4.37, F21(b) — the ceiling channel is anti-conservative; it is bounded by `(1+ε)`, which is why it does not matter, not because it is absent |
| The feasibility margin indicates whether the method is working | §4.37, F21(b) — constant to six decimals while recall goes to zero |
| Calibration contamination has a tolerable *rate* | §4.37, F21 — it has a tolerable *count*, and adversarially the count is zero |
| The grouping optimum transfers across deployment windows | §4.38, F22 — previous-window selection has worst normalised regret 0.991; the oracle itself varies more across windows than any configuration does within one |
| Episode recall is a usable objective for selecting a grouping family | §4.38, F22 — the family sets recall's denominator, so it selects coarseness; the two objectives disagree at 5 of 5 windows |
| The ADDIS spending-state attack is out of reach on bandwidth | §4.40, F23 — 33.4 Mbit/s over the deployment span, four hosts at 10 Mbit/s. It is out of reach on volume, not rate |
| Ordering at tied timestamps changes a reported quantity | §4.41, F24 — 50 randomised orders, 36 statistics, zero changes at either window |
| The padding attack is confined to the anomalous position-0.85 window | §4.42, F24 — measurable at all four other windows, and the black-box pool never fires at any of the five |
| Smallest-p-first maximises a tie block's rejection count | §4.41 — refuted by brute force over all `B!` orders: beaten on 127 of 600 blocks by up to 3 rejections |
| Compatibility of the *marginal* benign firing rate with nominal is evidence for Assumption 1 | §4.55 — the marginal is the weakest possible reading. Stratified on the observable components of `M_j` and read where the counts allow, 22 stratum-vs-own-window contrasts survive Benjamini–Yekutieli at **every** window, largest 9.3× [5.5, 15.5] in the arity bin the padding attack manipulates. At the shipped depth k=1 four fifths of the cells cannot be tested at all. Assumption 1 remains **assumed**, and the diagnostic is not offered as support for it |
| The padding attack is demonstrated only under the within-bucket order the paper recommends replacing | §4.55 — re-run under the canonical key-hash order: 3/3 suppressible at 0.55 (costs 23, 24, 33) and 34/34 at 0.85 (median 115.5) |
| The headline detection counts are order-robust | §4.58 — first-flow arrival strictly exceeds the maximum over 50 pre-committed orders at every window and seed where anything detects; the canonical order takes 18/13/30/31/72 to 3/11/0/0/34 |
| The zero canonical-order detections at 0.70 and 0.77 are a bug | §4.58 — under that order **no** episode clears its own step anywhere in the stream, and the exact biconditional (zero rejections iff nothing clears inside the feasible prefix) holds on all 60 arms |
| The 5-minute atom blur is an artefact of a denominator we chose | §4.59 — the red team's own task decomposition, an attacker-defined unit fixed before publication, rises with the alerting unit in rank agreement with the proxy wherever it can see the alerts (+1.000 at 0.70 over six bucket widths, +0.816 at 0.77) |
| The group-level MAX construction is attack-robust because padding cannot lower a maximum | §4.61 — it is robust to *appending* only. Its calibration set is groups, so its cold-start window collapses to **65–86** and every detection is suppressed by inserting **62–207** hypotheses |
| Suppressing an alert requires touching that alert's own evidence | §4.61 — it does not: creating hypotheses *ahead* of a target pushes it out of the feasible window, appending nothing. `thm:padding` and append-invariance are both irrelevant to it |
| Live-fire prevalence is a neutral or pessimistic evaluation regime | §4.60 — it is **optimistic**: thinning malicious episodes to a SOC base rate takes mean e-LOND detections from 3–72 to 0–8 at π=10⁻³ and to a 0–40% chance of *ever* rejecting at π=10⁻⁴, while feasibility is untouched (and *improves* under deletion) |
| The escapes survive realistic prevalence even if e-LOND does not | §4.60 — online e-BH and e-TOAD collapse alongside it, 0–40% bootstrap at π=10⁻⁴ |
| The red-team record independently confirms the blur count | §4.59 — it does not: a timeline-shift null reproduces the observed counts at 18 of 19 cells, so the rise is bucket width, not alert-level correspondence. Reported as agreement in direction, not corroboration |
| An external record can corroborate the alerts wherever it overlaps the deployment window | §4.59 — it cannot: issued alerts sit in the feasible prefix, the first minutes of a window, so at 0.55/0.62 under 10% of them overlap the exercise's reporting period at all. C1 places the alerts where the record is silent |
| Ordering sensitivity is a separate problem from feasibility | §4.58 — they are one finding: the feasible prefix is 1.6–2.6% of the stream, so detection requires a near-ceiling episode to land inside it, and first-flow arrival is favourable precisely because live-fire attack traffic arrives early |
| Padding the attacked group is evidence that group exchangeability fails | §4.67 — it is not. Split conformal on the grouped unit needs calibration and **true-null** test groups to be exchangeable, and padding changes the *attacked* group, which is a **false null**. Arity heterogeneity shows the assumption may be fragile under group-formation shift; the section is carried by infeasibility, which holds however the premise is resolved |
| A positive lower density of zero-evidence hypotheses rescales the closure's horizon by exactly ρ | §4.67 — it does not follow: `liminf Z_t/t ≥ ρ` gives eventual domination *below* ρ, for every ρ′ < ρ and never at ρ. The paper's operative form is instead exact and finite: `Z_t ≥ t−1−P_T` by counting, so the horizon offset is **additive in P_T** (≤ 152 here), with no density and no asymptotics |
| The horizon binds exactly when a procedure's spending index advances on every hypothesis | §4.67 — that is a classification of the procedures examined, not a characterisation of all procedures. `thm:family1` leaves a third route open: escape by history-dependent level growth fast enough to outrun γ_t, which none of these takes |
| Every detection count in the paper is under the canonical order | §4.67 — false as a blanket claim, and it was in the paper. Only **ten** artefacts carry an order arm; every other task takes `h_stream`'s `order="first-flow"` default. Headline absolute results are canonical; sixteen labelled ablations and sensitivity analyses are first-flow |
| A keyed canonicalization's measured cost applies to any adversary | §4.67 — it assumes one that can instantiate up to 3.15×10⁴ distinct `(SrcIP,DstIP)` pairs as real traffic. Against an adversary with a few hundred reachable pairs a secret seed is a hard stop, not the partial mitigation these figures price |
| Feasibility over a horizon T requires |C| ≥ kT/c₀ − 1 | §4.68 — only under **horizon-uniform γ**, which is max-min optimal and therefore the *cheapest* case. The general requirement is |C| ≥ k/α_T − 1; under horizon-free γ ∝ j^−1.6 the figure is 3.2×10¹³, not 6.5×10⁸ |
| Any procedure whose level is multiplicative in a spending sequence has a finite absorbing horizon | §4.68 — `thm:family1` also needs γ_t·t^d → 0 (and eventual monotonicity for absorbing). A level growing quadratically in the rejection count escapes the argument; the condition must be checked per procedure |
| The ADDIS state attack is demonstrated on a guarantee-bearing stream | §4.68 — the real-stream demonstration is at position 0.85, the known-invalid window, and **necessarily so**: ADDIS's horizon escape and its guarantee-invalidity are the same property on two-point conformal evidence. The guarantee-valid arm is synthetic (`apptab:addissynth`) |
| Online e-BH's horizon robustness (144 of 152 at 100×) is a measured rate | §4.68 — one window (0.85, invalid) and one seed, the only cell the horizon is swept on. LOND keeps all 151 at 2× and none at 100×; **LORD++** fails already at 2× |
| Suppressing an alert costs ≈10² flows | §4.68 — that is a median of eight per-window medians spanning **6 to 5,202**. The per-window median is the reported quantity; a single figure is a median-of-medians, not a rate |
| Online e-BH is covered by the feasibility propositions | §4.68 — it is one of the two **escapes**. `fig:envelope` plots it for comparison only; it still carries a calibration requirement linear in T per simultaneous discovery |
| Every reported attack cost is an oracle lower bound | §4.69 — false as a global convention. Only the per-alert padding cost r* is; L* and the whole-detected-set padding totals are **upper** bounds, G*/B* are exact closed forms, and N₅₀/₉₀/₉₉ are empirical reliability budgets over 400 draws. "Oracle" and "lower bound" are also two independent qualifiers |
| Abandoning symmetry only makes the padding attack cheaper | §4.69 — established only for the **pre-committed position-indexed weighted class** `thm:reach`/`thm:frontload` analyse, not for asymmetric e-merging in general |
| The AIT first-flow counts are an optimistic upper bound | §4.69 — "first-flow is the optimistic order" is an **empirical** property of LSPR23 (t53). Order sensitivity was never audited on AIT and t51/t54 carry no order arm, so the counts are neither canonical nor an upper bound there; every AIT rate is conditional on that one order's detected set |
| `apptab:audit` is the diagnostic that established the 0.85 invalidity | §4.69 — `apptab:tail` is (benign firing rate, interval excluding 1). `apptab:audit` is a later label-quality adjudication at the same window |
| 0.48% of episodes carrying evidence is a property of security prevalence | §4.69 — it is a measured property of **our streams**. Prevalence is a swept sensitivity parameter in this paper, never an asserted deployment regime |
| Dataset participants consented to instrumentation | §4.69 — we have no source for that. We rely on the publishers' ethical review and release terms, conducted no separate consent audit, and claim nothing beyond what those releases state |
