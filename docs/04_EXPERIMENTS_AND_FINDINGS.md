# Online Error Control for ML Intrusion Detection — Experimental Record

**State as of 26 Aug 2026.** Code in `proto/`, raw outputs in `proto/out/*.json`.
Mathematics and code independently audited by two reviewers working blind.

| Tag | Meaning |
|---|---|
| `[EXACT]` | Analytic property of the procedures. A dataset cannot change it. |
| `[SIM]` | Simulation on synthetic scores. Assumptions stated inline. |
| `[REAL]` | Measured on real network data. Scope and sample size stated inline. |
| `[PRIOR]` | Established in published work. Cite; do not claim. |
| `[OPEN]` | Not done. |

---

# 1. Findings

**F1. An online procedure whose spending sequence is indexed by elapsed time has a finite
feasibility horizon, and at security scale it is exceeded. Two families escape that
template, and each escape has a measured cost.** `[EXACT]` + `[REAL]`
For any procedure rejecting when evidence exceeds `1/α_t`, with evidence bounded by
`M = (|C|+1)/k` and `α_t` of either the multiplicative form `α·γ_t·g(history)` or the
lag-sum form (§4.13), the set of times at which any rejection is possible during a
rejection-free run is finite. Retaining feasibility over horizon T with no prior rejections
requires `|C| ≥ kT/w₀ − 1` under horizon-uniform γ, the max-min optimal spending sequence:
**640 million** at LSPR23 scale, **1.44 billion** for one hour at 10k flows/s, 3.46×10¹⁰
for one day. Under γ ∝ j^−1.6 it is 3.1×10¹³.

The template covers **LOND, LORD++, e-LOND and the e-GAI family** — the last by the
equivalence its own authors prove, e-LORD = e-LOND under `γ_t = ω_t∏_{j<t}(1−ω_j)`
(arXiv 2506.01452 §3.2). It does **not** cover two families (§4.20):

- **SAFFRON and ADDIS** index γ by a count of *tested* hypotheses — `t − C_{0+}` and
  `S^t − C_{0+}` — not by elapsed time. The horizon is finite only while that index
  diverges. On LSPR23 the ADDIS index is **exactly 0 at every t**, because a threshold
  conformal episode p-value is either 1 (discarded, never selected) or a candidate, and
  never lands in `(λ, τ]`; its level never decays and it is silent for 0.0% of the stream
  at all ten configurations. The escape is real but not free: ADDIS's guarantee requires
  uniformly conservative null p-values, which this evidence violates maximally (measured
  `P(P/τ ≤ x | P ≤ τ) = 1.0` at every x), so its FDP is **empirical-only**; and under the
  max-min optimal γ its `(τ−λ)` wealth discount falls below the conformal floor at `t = 1`,
  leaving it silent for 100% of the stream.
- **online e-BH** sets its threshold from `k*_t`, a fixed point over the whole history
  rather than a count of rejections already made, so a rejection-free prefix is **not
  absorbing** at any horizon. What this buys must be stated carefully (§4.20, §4.21).
  It escapes the *feasibility* statement but not the *calibration budget*: making `R`
  simultaneous discoveries under horizon-uniform γ still requires `|C| ≥ T/(αR) − 1`,
  linear in `T`, merely divided by `R`. The improvement over the Family I/II cold start is
  a factor `αR/w₀ = 2R` — 304× at the `R` = 152 measured here, not a factor of `T`. And on
  this stream it converts to **no extra power at all**: 72 rejections against e-LOND's 72
  under γ ∝ j^−1.6, 152 against 151 under horizon-uniform γ. Its measurable advantages are
  that it is never permanently silent and that it is the most horizon-robust procedure
  tested, keeping 144 of 152 rejections when the horizon is over-estimated 100×.

The mechanism therefore has a precise boundary: it binds whenever the index driving the
spending sequence advances on **every** hypothesis, and is escaped by procedures that
either advance it only on *tested* hypotheses or defer the decision to a later step.

**F2. The first-rejection deadline.** `[EXACT]`
Before any rejection the level carries no history term, so LORD++ has `α_t = γ_t·w₀` and
LOND/e-LOND have `α_t = α·γ_t`. With γ ∝ j^−1.6 the procedure must make its **first**
rejection within **18** hypotheses at `|C|`=10⁴ (**334** at `|C|`=10⁶) for LORD++, and **29**
(**515**) for LOND/e-LOND, or it is permanently silent. At prevalence 10⁻⁴ the first attack
arrives around event 10,000, so the deadline passes before any attack appears. Bootstrapping
does not rescue this: rejections raise the level, but rejections require feasibility.
The published fix for α-death does not rescue it either — mem-e-LORD (arXiv 2506.01452 §4.1)
has `R^d_{t−1} = 0` throughout a rejection-free run, so its level is *identical* to e-LORD's
until the first rejection, and it is measurably worse afterwards (142 rejections against
150) because the decaying memory also discounts rejections once they arrive (§4.20).

**F3. Whether grouping restores feasibility depends on the deployment horizon.** `[REAL]`
Grouping by (SrcIP, DstIP, time-bucket) — the only deployable definition available, since
LSPR23 carries no flow→campaign labels — cuts the hypothesis count but does not settle
feasibility on its own. Over the **whole 16.35M-flow stream** the required calibration set
exceeds the entire benign corpus at 5- and 30-minute buckets and consumes 94% of it at one
hour (§4.9). Over a **2.45M-flow deployment window** the same grouping is comfortably feasible
at two-hour and six-hour buckets, with margins +0.067 to +0.918, and infeasible at one of five
positions at one hour (§4.15). This is F1 measured rather than derived: feasibility is a
statement about the horizon, not about the grouping.

**Across five grouping families the required calibration set is exactly `kT/w₀ − 1`, so it
falls in lockstep with the episode count, and every family becomes feasible once the bucket
is coarse enough (§4.29).** Host-only grouping on the source side, (SrcIP, bucket), is
feasible at *every* bucket tested — margins +2.232 to +55.891 — because it collapses the
window to 944–16,494 episodes, and its episode recall (0.327–0.518) is **higher** than the
host-pair family's at every comparable bucket. So the feasibility barrier *can* be bought off
by coarsening the alerting unit to one a SOC would recognise. What it costs is F4's gap, which
widens monotonically with the unit: the same alerts cover 0.508–0.519 of malicious flows
regardless of family, while episode recall falls from 0.518 to 0.226. The claim that survives
is therefore narrower and more useful: **the tested host-pair family does not restore
feasibility, coarser deployable units do, and they pay for it in episode-level resolution.**

**F4. Flow-level and episode-level evaluation of the same system disagree by 60 points.** `[REAL]`
At the only feasible full-stream operating point the procedure detects **39.1% of attack
episodes** while covering **99.1% of malicious flows**. Attack episodes are small: median 7
malicious flows at 5-minute grouping, with 77.6% at ten or fewer.
Measured across five grouping families and seven bucket widths (§4.29), malicious-flow
coverage is essentially constant at **0.508–0.519** while episode recall falls from **0.518
to 0.226**. The gap is therefore created entirely by the choice of unit — not by the
detector, the procedure, or the alert budget — and it widens monotonically as the unit
coarsens, from +0.001 (source-host, 5-minute) to +0.283 (destination-host, daily). The one
exception is service-based grouping at 5 minutes, where episode recall slightly *exceeds*
flow coverage (−0.009) because grouping on destination port isolates the attacked services.

**F5. With the full calibration corpus the procedure is feasible at coarse grouping, but
feasibility does not imply detection.** `[REAL]`
Over five fixed-size window positions on the full 16.35M-flow stream, the feasibility margin
`(|C|+1)·w₀/T − 1` ranges **−0.061 to +0.918**: infeasible at one of five positions at
one-hour grouping, feasible at all five for two-hour and six-hour. Retaining every benign
flow roughly doubles `|C|` (1.81M–2.45M against 1.06M under 50% subsampling), which raises
the ceiling faster than it raises `T`. **But feasibility is necessary, not sufficient.** At
two of the five positions the fraction of attack flows reaching the evidence ceiling collapses
to 0.000–0.030 despite AUROC 0.83–0.91, and detections fall to zero at some seeds even with a
margin of +0.536. Detection depends on the far tail of the score distribution, not on ranking
quality. **The sharpest form of this separation is the second detector (§4.22):** Isolation
Forest yields a feasibility margin identical to HistGradientBoosting's to every digit — the
margin is `CEIL·w₀/T − 1` and depends only on `|C|`, `k` and `T`, never on the scores — while
its tail reach is **0.000 at all ten configurations**. Not one attack flow, at any position
or seed, scores strictly above all 1.8–2.4 million benign calibration scores. Same margin,
152 detections against 0.

**F6. The dilution attack costs 1–134 padding flows on real traffic, and the realism of the
padding does not matter.** `[REAL]`
An adversary padding their own episode with benign-looking flows suppresses detection. Median
cost across five window positions, two seeds and three grouping widths: **1–22** flows at
one-hour grouping, **3–62** at two-hour, **4–134** at six-hour. Large volumetric episodes
resist: 6 of 55 survived 1,000 padding flows in the single-window run.
Across five padding pools — generic benign, attacker-origin, protocol-matched,
service-matched and a black-box pool chosen without any detector access — the cost is
**identical** (median 34 flows over the 257 episodes where every pool is defined), because
the suppression cost depends on the pool only through `τ − μ` and τ exceeds the largest μ by
four orders of magnitude (§4.30). Two of the pools never fire at all, making the suppression
deterministic. And the cost to suppress with probability ≥ 0.90 equals the expected-value
cost to within one flow, so the expectation-based numbers above are not optimistic.
**The attacker can put those flows where the grouping key requires**: pads must land on the
target's own `(SrcIP, DstIP)` pair, and the detector's 33 features are `Protocol` plus
per-flow timing and volume statistics with **no endpoint identity among them**, so a score
is invariant to the host pair and the black-box pool's `P(fire) = 0` transfers to the attack
pair by construction. This has to be argued structurally rather than measured: across five
windows × two seeds, all **674** detected episodes sit on host pairs that are **100%
malicious**, so LSPR23 contains no ordinary traffic on an attack pair to build a
host-pair-matched pool from (§4.30, `t46_hostpair_padding.py`). The argument is a property
of **flow-level** feature sets; a detector conditioned on endpoint identity would break it.

**F7. No symmetric aggregation of e-values that can fire at all resists adversarial
padding.** `[EXACT]`
For any τ > 1, no family of symmetric e-merging functions that attains τ is τ-padding-robust:
padding an episode with `r > (Σx)/τ − m` uninformative events drives every such rule below τ
(§4.16). The attainment condition is required — the constant rule `F ≡ 1` is symmetric, valid
and padding-invariant, and never fires. Since rejection requires evidence ≥ `1/α_t` with
`α_t < 1`, the threshold is always τ > 1, so **the attack applies to every rejection threshold
any valid online procedure can set**. The escape is to abandon symmetry — a pre-committed slot
rule is valid under arbitrary dependence and padding-invariant — which works only if the
adversary cannot choose which slot its events occupy. **That condition does not hold, and the
escape is worse than the disease** (F20, §4.36): for every precommitted weight sequence the
number of leading zero-evidence flows that defeat it is finite, and on real traffic every
scheme that keeps the arithmetic mean's recall falls to 1–8 leading flows against 111 appended
ones.

**F8. No cap policy restores validity without destroying power or opening a new attack
channel.** `[REAL]`
`Σe/n₀` is a valid e-value only when group occupancy `m ≤ n₀`. Real group sizes are heavy
tailed (mean 75.9, p99 415, max 149,032 at two-hour grouping), so any cap set near a typical
group size is violated by the largest groups — at a p99 cap, 1.00% of test groups violate it but
those groups hold **86.2% of all flows**, with `E[Σe/n₀] = m/n₀` reaching **358**. Four
policies restore validity, and each fails differently: `n₀` = max detects 0/284 episodes;
deterministic splitting detects 0/284 and raises T from 26,098 to 30,938; truncation to the
first `n₀` events detects 12/284 and is suppressed by a median of **345 leading benign flows**;
a pre-committed random slot detects 109.4/284 in expectation (95% MC CI [102, 116]) but is a
randomised rule whose alerts depend on a coin flip, and whose power decays as **1/m** under
padding (expected detections 109.4 → 54.7 →
21.9 → 10.9 → 1.1 as the group is padded ×1, ×2, ×5, ×10, ×100).
Sweeping the cap from mean to max rather than testing two points (§4.25) shows validity is
not the binding constraint — truncation is valid at every cap — but that its two failure
modes move in opposite directions with `n₀`: at `n₀` = p50 = 2 the truncated rule detects 71
of 275 episodes and costs the attacker **one** padding flow to suppress; at `n₀` = p999 =
7,258 the front-load cost rises to 3,560 flows and detections fall to 6; at `n₀` = max it
detects nothing at all.

**F9. Calibration drift is mild, and the one position where the evidence is not a valid
e-value is a localised label error rather than drift.** `[REAL]`
On AIT NetFlows measured anti-conservatism is 1.3–2.0×, and the evidence is *conservative*
(0.86–0.93) at the 10⁻²–10⁻³ levels. On the earlier 50%-subsampled LSPR23 split the benign
firing rate is 2.0×10⁻⁶ against a nominal 9.4×10⁻⁷, a factor of 2.1. Across the five
full-stream window positions the **median** ratio of measured to nominal benign firing rate
is **1.94** at k = 1 (§4.23), consistent with those.

**At window position 0.85 — the position used by §4.17, §4.19, §4.20 and every procedure
comparison — the measured benign firing rate is 2.81×10⁻⁵ against a nominal 5.52×10⁻⁷: a
factor of 50.9 at seed 0 and 24.3 at seed 1 (§4.28).** There `E[e] ≈ 51` rather than ≤ 1, so
the evidence is not a valid e-value at that position and no FDR guarantee attaches to
anything computed there. **§4.31 identifies the cause.** Exactly 46 benign-labelled flows of
1,638,722 fire, and **three host pairs of 25,864 carry 44 of them**; removing those three
pairs takes the ratio from 50.90× to **2.22×**, inside the 1.07–3.79× range of the other four
positions (still anti-conservative — localised, not removed). The flows are periodic outbound TLS from an internal host to one external address
and LDAP / Global Catalog enumeration from a red-team **confirmed-compromise** host against
internal domain controllers — post-compromise activity carrying a benign label, because the
exercise instrumentation attributes flows to the red team by *endpoint identity* and cannot
mark actions taken by a compromised blue-team host. Distribution shift, a new benign traffic
mode and duplicated records are ruled out directly; a shift confined to the extreme tail is
not separable from label error without the exercise's own logs, so label error is the
best-supported explanation and not a proved one (§4.31). §4.32 reaches the same host pairs
from a different direction.

Neither consequence overturns a conclusion, and both must be stated. Anti-conservative
evidence can only make a procedure fire *more*, so every infeasibility and silence result at
position 0.85 is conservative — the true feasibility picture is worse, not better. And every
FDP reported there is a measurement against labels rather than a guarantee — but the
**direction** of the label error is now known, and it inflates the reported FDP rather than
deflating it (§4.32: 0.0265 by label against [0.0000, 0.0265] by audit). **"Drift is mild"
holds everywhere; position 0.85 is a label-error case study, not a drift case study.**

**F10. Conditional validity fails with probability exactly 1/e.** `[EXACT]`, fix `[PRIOR]`
`E[e|C] ~ ((n+1)/k)·Beta(k, n+1−k)`. At k=1, `P(E[e|C] > 1) = (n/(n+1))^n → 1/e = 0.3679`,
**independent of `|C|`** — the relative dispersion of the k-th order statistic depends on k,
not on n. Marginal validity holds and FDR is controlled; what fails is conditional coverage.
The fix is Bates et al.'s calibration-conditional p-values.

**F11. The evidence ceiling the procedures require is where conditional validity is worst.** `[EXACT]`
Small k gives the high ceiling that online control needs, and small k is exactly where the
deployed calibration set is least reliable: p99 of `E[e|C]` is 4.1–4.9 at k=1 versus 1.07 at
k=1000. More calibration data does not change this.
Measured on real scores (§4.23): the worst-case benign fire ratio falls from **50.90** at
k = 1 to **6.80** at k = 1000 while the feasibility margin falls from +0.436 to −0.999, so
the two move in opposite directions and no k satisfies both. Applying the Bates
calibration-conditional fix (§4.26) does not resolve this, because the fix is priced by the
same quantity: it costs 38–78% of the ceiling at k = 1 and 4% at k = 1000 — cheapest exactly
where the ceiling is already useless.

**F13. Online error control does not let the operator choose the operating point, and the
lever it does expose is not an operational one.** `[REAL]`
Measured against the achievable frontier of the same detector score, every method sits
essentially **on** that frontier at its own alert budget — gaps ≤ 0.039 recall in §4.19, and
**+0.000 for every procedure and spending sequence in §4.20** — so none is inefficient. What
differs is which point they occupy, and online error control does not let that be chosen: the
spending sequence γ and the α-wealth process select it. The same procedure on the same stream
lands at **72 alerts / recall 0.282 / FDP 0.000** under γ ∝ j^−1.6 and at **151 alerts /
recall 0.576 / FDP 0.026** under horizon-uniform γ — a factor of **2.0 in recall** from a
parameter that is neither an error target nor an alert budget, and whose effect exceeds that
of the error target itself. The polynomial-γ point is dominated: the frontier at the same
zero error rate offers recall **0.459 on 117 alerts**. The horizon-uniform point is not
dominated, but reaching it requires committing to the stream length in advance. An
analyst-feedback controller reaches recall 0.588 at FDP 0.068 and holds its target to ~20
alerts of latency; without feedback the same threshold family runs to 875 alerts at FDP
0.763.
§4.24 measures the two levers head to head. Sweeping q over a twenty-fold range
(0.01 → 0.20) moves median episode recall from 0.049 to 0.137, a span of 0.088; switching the
spending sequence at fixed q moves it from 0.085 to 0.273, a shift of 0.188 — more than twice
what the entire q sweep achieves. **The operator's nominal control is the weaker lever.**

**F14. k = 1 is the only feasible rank, and it is the least reliable one.** `[REAL]`
The threshold conformal ceiling falls exactly as `1/k`, so the feasibility margin runs
+0.436 (k = 1), −0.856 (k = 10), −0.986 (k = 100), −0.999 (k = 1000), and e-LOND makes zero
rejections at every k ≥ 10 in every one of ten configurations (§4.23). Raising k to buy
conditional reliability does not trade power for validity — it removes the operating point
altogether. And k = 1 is where reliability is worst: worst-case benign firing is 50.9×
nominal at k = 1 against 6.8× at k = 1000. The one rank that works is the one whose evidence
is least trustworthy.

**F15. The standard power-recovery technique for e-value procedures returns exactly nothing
here — for the discrete evidence the record uses.** `[EXACT]` / `[REAL]`
Boosting — redistributing the mass of e-values that fall below the rejection threshold — has
optimal factor `b* = 1` for any two-point e-value, and the threshold conformal e-value is
two-point by construction (§4.28); a genuine continuous e-value admits `b* = √(2τ)` for
contrast — and §4.34 confirms that closed form from the other direction, deriving
`b* = (τ/λ)^λ` for the calibrator family and recovering `√(2τ)` at λ = ½. The claim is
therefore scoped to **finite-resolution** evidence: under randomised smoothing boosting is
not vacuous, and it still leaves the calibrated route strictly below a direct p-value
threshold (F18). On real scores the optimal factor is *below* 1 (median 0.368, minimum 0.020),
because the measured benign firing rate exceeds nominal (F9). The evidence is already
extremal: there is no wasted mass to recover, and the same discreteness that creates the
feasibility boundary is what makes the remedy vacuous.

**F16. The alert labels are not an under-estimate of truth: the alerts the dataset calls
false carry corroborating evidence of being real attacks.** `[REAL]`
Adjudicating all 152 emitted alerts against the Locked Shields red team's own task record —
83 machine-readable compromise reports covering 39 IPv4 addresses, and 295 timestamped step
submissions — plus a structural indicator whose own contribution is exactly subtracted, gives
**96.1% agreement with the LSPR23 label** with no alert left ambiguous, and 98.0% under the
stricter of the two rules (§4.32). All **five** alerts the label calls false carry
corroborating evidence of being genuine attack traffic, and **3 of the 5 involve a red-team
confirmed-compromise host** — a fact that owes the audited labels nothing. They are the same
host pairs §4.31 identifies from the score tail. Measured FDP is therefore **not an
under-estimate**: e-LOND's 0.0265 becomes [0.0000, 0.0265] and ADDIS's 0.0329 becomes
[0.0000, 0.0263] under the structural rule. The caveat is that the structural indicator is
itself computed from the `Label` column — independent of each episode's own label, but not of
the labelling process — so the audit narrows the plausible direction of the error rather than
fixing a corrected value. The audit is also self-critical about its own evidence: the
discriminative indicator separates 94.7% of alerts from 1.0% of non-alerted benign episodes,
while temporal concurrency separates 100.0% from 86.0% and is useless, because the whole
window sits inside the exercise.

**F17. The one procedure that escapes the feasibility horizon exposes its spending state to
the adversary instead, and against it the two attack surfaces coincide.** `[EXACT]` + `[REAL]`
ADDIS escapes §4.13 because its spending index counts hypotheses that are *selected but not
candidates*, and threshold conformal evidence never produces one. An adversary who
manufactures episodes with `p ∈ (λ, τ]` advances that index at will; such episodes are never
rejected, so they cost no discoveries. The budget has a closed form, verified against the
implementation: `B*` is the smallest `D` with `D+1 > [(τ−λ)W(|C|+1)/(k·ζ(1.6))]^{1/1.6}`,
`W = w₀` before the first rejection and `αR` after R of them. On the real stream **B = 202
leaves all 152 rejections intact and B = 203 leaves none**, permanently — an absorbing state
of exactly the kind ADDIS was supposed to avoid. The attack survives the grey-box setting
(the admissible group size is a `τ/λ`-wide interval, so a ±33% estimate of `|C|` suffices)
and needs only over-provisioning when the controller state is unknown (36×).

Its price is set by the calibration budget, not by any implementation weakness: one precursor
costs `λ(|C|+1)/k` = 453,279 flows, so silencing the controller costs **9.2×10⁷ flows, 5.6×
the entire LSPR23 stream**, scaling as `λ|C|·[(τ−λ)w₀|C|]^{0.625}/k^{1.625}`. The same
quantity that buys feasibility buys resistance to the state attack. Two things make it matter
anyway. First, **against ADDIS it is the cheaper attack**: because ADDIS's level is five
orders of magnitude larger than e-LOND's, padding a single episode past ADDIS's threshold
costs a median 3.4×10⁷ flows, so state manipulation wins from the **third** episode onward
(break-even 2.7) — this window holds 255. Second, **the two surfaces are the same operation**:
ADDIS caps its level at λ and the state window starts at λ, so for **101 of its 147
detections** the cheapest padding that suppresses the alert also advances the index. The
structural claim is the one to make: any procedure that escapes α-death by conditioning its
spending index on a property of the observed evidence exposes that property to the adversary,
and the price of the exposure is fixed by the calibration budget.

**F12. Inflation and fragmentation do not work as attacks.** `[SIM]`
Padding a purely benign group never forces a false discovery at k ∈ {1, 100, 10⁴}. Splitting
a campaign across groups is counterproductive: per-group evidence is flat in group size, and
more groups mean more rejection opportunities and more earned wealth. The attack surface is
suppression by within-group dilution only.

**F18. Randomised smoothing removes the feasibility floor and the absorbing state, and buys
a lottery rather than detections: the reliably-detected set does not move.** `[EXACT]` / `[REAL]`
Smoothed conformal p-values `p_u = (G + U(1+E))/M` are exactly Unif(0,1), so `inf p_u = 0`,
`P(reject) = min(1, α_t·(|C|+1))` at every step, and F1's absorbing state cannot exist — the
hard horizon becomes a **soft** one that decays to zero exactly as `α_t` does. At the
guarantee window this takes LOND from 90.1% structural silence to 0.0% and from 18.0 to
23.9 ± 2.7 rejections, but **the set of malicious episodes detected with probability ≥ 0.9 is
18, identical to the discrete rule's deterministic 18** (§4.34); the extra yield is spread
over 78 further episodes, none reliable, at the cost of `Var(R_T) = 7.14` and an alert set
that differs by 36% between randomisation seeds. Under the merge valid where the record's own
rule is valid — Hommel, arbitrary dependence — the yield is **negative** (12.0 against 18.0)
and **no** episode is detected with probability ≥ 0.9. The calibrated e-value route is
strictly dominated for every calibrator: `P(reject) = min(1, (α_tλ)^{1/(1−λ)}M)`, a power-law
gap, and boosting — which F15 shows is exactly vacuous for the two-point e-value but which
here gives `b* = (τ/λ)^λ`, reproducing §4.28's `√(2τ)` at λ = ½ — closes it only to the
constant λ. **The optimal p-to-e calibrator is the threshold conformal e-value construction
itself**, so the reviewer's route done optimally returns to the paper's own construction. Two
further consequences: the discrete rank-1 rule queries the single point of the calibration
tail that is well calibrated (1.07× at `1/M`) while smoothing moves the operating point into
a mid-tail that is 3–8× anti-conservative (1,817.7 benign flows against 228.8 nominal at
`a = 10⁻⁴`), so **the coarseness protects its own validity**; and ADDIS's escape from F1 is
destroyed by any rank-based merge (index advance 0.19% → 85%), not by the randomisation,
which moves it by less than 10⁻⁴.

---


**F19. Restarting the controller restores detection and nearly replaces horizon knowledge —
by spending n times the error budget, which is exactly the guarantee it gives up.**
`[EXACT]` / `[REAL]`
A two-hour restart takes LOND at the guarantee window from 18.0 to **95.0 ± 5.7** rejections
and episode recall from 0.065 to **0.345** at FDP 0.000, within 5% of what the horizon-uniform
`[ORACLE]` spending sequence achieves uninterrupted (100.0, 0.364) — so restart buys most of
what oracle horizon knowledge buys, without the oracle (§4.35). ADDIS, which already escapes
the §4.13 template, gains nothing (107.0 → 106.5), as F1 predicts. The gain **decomposes**:
resetting the spending index costs no budget and is worth 46% of it (18.0 → 53.5 under a
precommitted uniform allocation summing to `q`); resetting the *budget* is the other 54% and
spends `n·q`. What is given up is the deployment-level guarantee: per-epoch FDR control does
not pool, because pooled FDP is a weighted average of per-epoch FDPs with data-dependent
weights. If every epoch rejects one false hypothesis with probability `q`, each has
`FDR_i = q` exactly while `pooled FDR = 1 − (1 − q)^n` — **0.185 at the four epochs of the
headline arm**, 0.676 at twenty-two. mFDR does pool, by the mediant inequality, but LOND,
LORD++ and e-LOND control FDR, not mFDR. Restart and coarsening are the **same** feasibility
lever algebraically (`margin = M·c/T_ep − 1`) and differ only in the price: coarsening pays in
episode resolution, restart pays in the pooled guarantee. Restarting hourly at 1 h grouping
reaches episode recall **0.406** against **0.103** for 6 h coarsening uninterrupted, with every
arm sitting exactly on the achievable frontier at its own alert budget (S6). Finally, the
reviewer's own question is barely measurable here: LSPR23's longest deployment window that
leaves room for training and calibration spans **26.98 h**, so a 48 h epoch does not exist and
a 24 h epoch recovers only a third of what a 6 h reset does (48.0 against 87.0 rejections).

**F20. The asymmetric escape from the padding theorem does not stop the attack; it makes the
attack cheaper. The robustness / power / ordering triangle is closed.** `[EXACT]` / `[REAL]`
The escape route F7 leaves open is a precommitted, position-indexed weight sequence
`F(e) = Σ_i w_i e_i`, valid under arbitrary dependence iff `Σ_i w_i ≤ 1` and padding-invariant
by construction. Two exact bounds close it (§4.36). **Power:** the number of positions at
which a lone attack flow can fire the rule is `P ≤ α_t·M`, the *same* quantity that governs
F1's feasibility horizon. **Ordering:** the number of leading zero-evidence flows that make
detection impossible is `L*(w) = min{L : Σ_{i>L} w_i < β}`, `β = 1/(α_t·M)`, which is
**finite for every summable `w`** by the same summable-tail lemma as §4.13's Proposition 2,
applied on the within-episode position axis. No choice of weights escapes; the design only
sets the price, and the price is paid out of power. Measured at the guarantee window, every
padding-invariant scheme that retains the arithmetic mean's episode recall (0.062 against
0.065) is defeated by **1 to 8** leading flows, against **111** appended flows for the
symmetric mean on the same episodes — the ordering attack is **14× to 112× cheaper**. Buying
`L*` up to 164 costs 57% of the recall and is still 3× cheaper to defeat. Last-event-only is
excluded by definition rather than by cost (one appended zero destroys it), and a
security-prior weighting is out of class and fires on 0 of 275 malicious episodes. The quoted
`L*` are upper bounds, because an attacker that suppresses earlier episodes leaves LOND with
a smaller `α_t` and a weakly smaller `L*`.

**F21. Calibration contamination is priced in flows, not in a rate, and at the only feasible
rank the adversarial tolerance is zero.** `[EXACT]` / `[REAL]`
At `k = 1` the whole conformal rule is one order statistic — the calibration maximum — so
contamination acts only through it. Injecting `j` attack flows above that maximum hands the
threshold to the attacker once `j ≥ k`, making the tolerable number of adversarial mislabels
exactly `k − 1`; F14 fixes `k = 1` as the only feasible rank, so **one** mislabelled
high-scoring flow takes recall from 0.065 to 0.000 at position 0.55 and from 0.282 to 0.000 at
0.85. `k` is the contamination budget as well as the power and reliability parameter, and
feasibility has already spent it. The adversarial arm has no rate dependence at all — the top
`εN` attack flows share one maximum, so the curve is a step at one flow — and at `|C| ≈ 2×10⁶`
even `ε = 10⁻⁷` rounds to zero flows, so the rate axis has no resolution where the effect lives.
The **random** arm's scale is `ε* = 1/(N·q₀)` with `q₀` the exceedance rate of the
*contamination pool* (0.9043 and 0.7623, not the deployment window's malicious firing rate):
**1.11 and 1.31 flows.** Random contamination costs nothing until it injects one flow the clean
detector would itself have fired on. The tolerable `ε` is 4×10⁻⁷ — three orders of magnitude
below the smallest non-zero grid point anyone would think to try, and the wrong unit.

**F21(b). Contamination costs power *and* a bounded amount of validity — the second channel
runs the other way.** `[EXACT]` / `[REAL]`
The threshold conformal e-value's p-value `min(1, n/(M·m))` carries the ceiling `M = |C|+1` in
its denominator, so `Ev_ε/Ev₀ = (1+ε)·(m_ε/m₀)`: a *firing* channel that deflates evidence and
a *ceiling* channel that inflates it. A contaminating flow that does not clear the threshold
leaves `m` alone, and `p` falls by exactly `(1+ε)` — anti-conservative, with `E[e] ≤ 1+ε`.
Driven deliberately with the whole available stealth budget, the threshold does not move by one
ULP, recall is unchanged, and `q = 0.05` becomes 0.050008 (position 0.55, 386 usable flows) or
0.054195 (position 0.85, 152,135). **Power dies at one flow and is unbounded; validity degrades
by a factor needing `a = N` flows to double.** The bound holds for LOND and LORD++, whose
guarantee is a sum of offered levels, and is *multiplicative on top of* the clean rule's own
conservatism (§4.31: up to 50.9×). Under the size-matched replacement model the ceiling channel
closes exactly. Separately, **the feasibility margin is not a safety indicator**: it is constant
to six decimals (0.999984 / 0.999978) across the entire sweep while detection goes to zero,
because contamination *increases* `|C|`.

**F22. The headline grouping and cap were not chosen on the test window — and the evidence
is that they are the *worst* configurations on the grid, not that they are close to the
best.** `[REAL]`
Over five deployment windows × two seeds (§4.38), the record's grouping (`src-dst`, 2 h)
attains the worst *feasible* flow coverage on a 35-configuration grid at position 0.70 and
sits within 10⁻⁴ of the worst at 0.62 and 0.77; the record's cap (`n₀ = p99`) is the worst of
six at two of five windows. No one tunes on a test window to obtain the worst configuration.
The two axes then behave very differently. **The cap transfers**: previous-window selection
has worst regret 0.012 (normalised 0.070) and leave-one-out 0.010 — and its power-optimal
value, `n₀ = 2`, has a median front-load defeat cost of **one flow** and leaves 39% of groups
outside the raw rule's validity condition, so §4.12's choice is a validity choice, correctly
made. **The grouping does not transfer**: previous-window selection has worst regret 0.579
(normalised 0.991), and window-to-window variation of the oracle, 0.676, exceeds every
within-window spread. Flow coverage at a fixed grouping is therefore not predictable from the
previous window, and the record's coverage numbers are *what the deployable grouping
achieves*, never *the best achievable*. The configurations that win are consistently coarse,
which is the C2 trade seen from the other side: coarsening buys flow coverage and spends
episode resolution. Selecting on **episode recall** instead would pick a different
configuration at 5 of 5 windows, because the grouping family sets recall's denominator — F4's
gap, in a new place.

**F23. Bandwidth does not separate the two attack surfaces; volume against the monitored
population does.** `[REAL]`
Priced in operational units (§4.40), suppressing one alert costs 34 flows = 13.3 kB = **15
bit/s** sustained over the 2 h bucket from a single host, and the ADDIS spending-state attack
costs 92,015,637 flows = 36.1 GB = **33.4 Mbit/s** over position 0.85's own 2.4 h deployment
span — four hosts at 10 Mbit/s. The expectation that the state attack is "structural" is *not*
a bandwidth statement.
What makes it structural is that 92 million flows is **37.5× the deployment window's entire
observed flow count** and 5.6× the whole 161.5 h dataset, against 1.4×10⁻⁵ of the window for
suppressing an alert. The duration unit these figures rest on is *recovered* from the file's
own internal consistency (`Flow Bytes/s` against the byte totals), not assumed: microseconds,
three decades clear of every alternative.

**F24. The deterministic tie-break costs nothing measurable, and the padding attack is not an
artefact of the anomalous window.** `[REAL]`
At most 1.3% of episodes share a first timestamp with another and the largest tie block is 3,
so at most 1.3% can move at all. Across 50 randomised within-timestamp orders at positions
0.55 and 0.85, **all 36 statistics** — discoveries, true positives, FDP, recall and first
detection rank, for LOND, LORD++ and ADDIS — take a single value equal to the deterministic
one (§4.41), with the randomisation verified to move 324 of 651 and 205 of 412 movable
positions per draw. Separately (§4.42), the padding attack's median suppression cost is
**35.25 flows at position 0.85 against per-window medians of 3, 4.5, 62 and 35 at the other
four**, so it is not confined to §4.31's anomalous window. Three of those four are below 0.85
and one (0.70, at 62) is nearly twice as expensive; the pooled figure of 6 flows is driven by
the two cheap windows and is not a uniform claim. The black-box pool has mean e exactly 0 and P(fire) exactly 0 at **all five** windows,
so §4.30's deterministic-suppression result holds across the full span.

---

# 2. Method

## 2.1 Procedures

**LORD++**: `α_t = γ_t·w₀ + (α−w₀)·γ_{t−τ₁} + α·Σ_{j≥2} γ_{t−τⱼ}` over rejection times
τ₁<τ₂<…, truncated at 2×10⁵ (truncated mass ≲1.5×10⁻⁷ against a 10⁻⁶ floor, immaterial at
these settings). **LOND**: `α_t = α·γ_t·(1+D_{t−1})`. Throughout, α = 0.05 and w₀ = α/2.

γ families: `γ_j ∝ j^−1.6` and Javanmard–Montanari `γ_j ∝ log(max(j,2)) / (j·exp(√log j))`,
each normalised over a finite horizon. Simulation results therefore characterise these
families; the horizon-free statement uses the `S(Δ)` bound in §4.1.

SAFFRON, ADDIS, online e-BH and the e-GAI family (e-LORD, e-SAFFRON, mem-e-LORD) are
implemented in `h6_procs.py` and measured in §4.20. SAFFRON uses λ = 0.5; ADDIS* uses
λ = 0.25, τ = 0.5 and a 0-indexed `γ_j ∝ (j+1)^−1.6`, both the defaults of their papers.
Their wealth bookkeeping does not merely change constants: SAFFRON and ADDIS index γ by a
count of tested hypotheses rather than by elapsed time, which is why ADDIS escapes the
§4.13 template entirely on this stream.

## 2.2 Evidence

Conformal p-value `p = (1 + #{i∈C : sᵢ ≥ s}) / (|C|+1)`, with floor `1/(|C|+1)`.
Threshold conformal e-value at rank k: `e = ((|C|+1)/k)·1{K ≤ k}`, where
`K = 1 + #{i∈C : sᵢ ≥ s}`, with ceiling `(|C|+1)/k`.

Validity: `E[e] = 1` exactly under exchangeability with continuous scores and **fixed,
pre-chosen k**. With ties under the `≥` convention it is conservative (`E[e] ≤ 1`).
Non-integer k is valid but strictly conservative, `E[e] = ⌊k⌋/k`. Conditional on a fixed
calibration set, validity does not hold in general — see F10.

Where an e-value is tested inside a p-value procedure, `min(1, 1/e)` is used, super-uniform
by Markov. This is valid but lossy. The native e-value comparators e-LOND, online e-BH and
the e-GAI family are measured directly in §4.20; `min(1, 1/e)` is used only where a p-value
procedure (SAFFRON, ADDIS) requires it, and the resulting two-point p-value distribution is
itself the reason their validity conditions fail there.

## 2.3 Aggregation rules

| rule | form | valid under arbitrary dependence | admissible | padding-robust |
|---|---|---|---|---|
| arithmetic mean | `(1/m)Σeᵢ` | yes, by linearity, **provided m is fixed in advance** | yes | no |
| pre-committed denominator | `Σe/n₀` | only for `m ≤ n₀` | no — dominated by the mean | yes, within the cap |
| pre-committed slot | `F(e) = e₁` | yes | — | yes (asymmetric) |
| top-k mean | `Σ(top k)/k` | **no** — selection is data-dependent, so linearity does not apply; `E[·]` = 0.5, 1, 10, 1000 at N = 50, 100, 10³, 10⁵ | — | — |

Linearity is insensitive to the joint law, so no dependence assumption enters the mean's
validity. It requires only that each `eᵢ` satisfy `E[eᵢ] ≤ 1` under the same null and that
the count `m` be data-independent. When `m` is adversary-controlled, linearity gives nothing
— this is the opening the dilution attack uses.

---

# 3. Data

## 3.1 LSPR23 — primary

Locked Shields Partner Run 2023, Zenodo 8042347. `ls23pr_v1.csv`, 10.59 GB, 101 columns.

- **16,353,511 flows**; **1,644,599 malicious** (10.06%); 14,708,912 benign
- **7,381,261 of 16,353,511 rows are out of timestamp order.** Any streaming evaluation must
  sort first.
- **No flow→campaign ground truth.** `Category`, `Severity`, `SigID`, `Service` and
  `Expoid_dst` are empty for almost all malicious flows — 1,630,732 of 1,644,599 have no
  `Expoid_dst`. Only 3 distinct `Anomaly_event` values and 22 distinct SigIDs exist across
  the dataset. The 288 attack narratives distributed with LSPR23 are red-team **task
  descriptions** and cannot be joined to flows.
- Attack arrival is strongly non-stationary. Prevalence by decile:
  0.0097, 0.0085, 0.0033, 0.0033, 0.0033, 0.0652, 0.2558, 0.4688, 0.5532, 0.4564.
  A chronological split therefore trains on few attacks and tests on many, and detector
  quality is sensitive to how much of the ramp-up falls in the training window (AUROC 0.87
  at a 50% split, 0.9991 at 60%).

## 3.2 AIT NetFlow — calibration experiments

Zenodo 13168643, tstat format, 138 columns. The `wilson` testbed contributes 417,672 TCP
flows spanning 2022-02-03 to 2022-02-08. Used unlabelled, benign-against-benign across time.

## 3.3 Not in use

**AIT-ADS** (Zenodo 8263181, 96 MB compressed → 2.7 GB): 8 testbeds × {AMiner, Wazuh}.
Alerts carry no labels; labelling requires attack windows from AIT-LDSv2 (137 GB), an
estimated 3–5 days of work. Deferred. **LANL** — incomplete negative ground truth, so false
positives are unidentifiable. **WitFoo** — vendor-generated labels. **UNSW-NB15** — 64%
attack prevalence. **NF-\*-v3 (UQ)** — JS landing pages, not scriptable; manual browser
download required.

---

# 4. Experiments

## 4.1 Feasibility quantities (`t1_silence.py`) `[EXACT]`

Three distinct quantities govern whether a rejection is possible:

1. **First-rejection deadline** — `max{t : γ_t·w₀ ≥ floor}`. Before any rejection this is
   the entire test level, so the procedure must reject by then or never.
2. **Drought tolerance given D prior rejections** — longest rejection-free run survivable in
   the most favourable arrangement (all D immediately before the drought), where
   `α_t ≈ γ_Δ·((α−w₀) + α(D−1))`.
3. **Absorbing Δ\*** — the horizon-free bound, valid for any nonnegative summable γ whether
   monotone or not. With `S(Δ) = Σ_{d≥Δ} γ_d`, during a rejection-free run of length Δ every
   index `t−τⱼ` is distinct and `≥ Δ`, and `γ_t ≤ S(t) ≤ S(Δ)`, so `α_t ≤ (w₀+α)·S(Δ)`,
   non-increasing in Δ. Since `Σγ = 1 ⟹ S(Δ) → 0`, `Δ* = min{Δ : (w₀+α)S(Δ) < floor}` is
   finite, and the state is **absorbing** once reached because Δ only grows.

γ ∝ j^−1.6:

| `\|C\|` | floor | first-rejection deadline | drought (D=1) | drought (D=1000) | Δ\* |
|---|---|---|---|---|---|
| 10³ | 9.99e−4 | 4 | 4 | 515 | 786 |
| 10⁴ | 1.00e−4 | **18** | 18 | 2,174 | 34,569 |
| 10⁵ | 1.00e−5 | 79 | 79 | 9,169 | 1,035,775 |
| 10⁶ | 1.00e−6 | **334** | 334 | 38,666 | 6,543,273 |
| 10⁷ | 1.00e−7 | 1,410 | 1,410 | 163,056 | 9,535,022 |

γ ∝ JM gives deadlines 1 / 18 / 187 / 1,715 / 15,253 for the same `|C|`, with far larger Δ\*.

Simulation, T = 500,000 events, benign N(0,1), attack N(5,1), α = 0.05:

| proc | π | `\|C\|` | #attacks | R | recall | silent | first silent |
|---|---|---|---|---|---|---|---|
| LORD++ | 1e−4 | 10⁴ | 50 | 0 | 0.000 | 100.0% | 19 |
| LORD++ | 1e−4 | 10⁶ | 50 | 0 | 0.000 | 99.9% | 335 |
| LORD++ | 1e−3 | 10⁶ | 500 | 0 | 0.000 | 99.9% | 335 |
| LORD++ | 1e−2 | 10⁶ | 5,000 | 4,534 | 0.865 | 0.0% | — |
| LOND | 1e−4 | 10⁴ | 50 | 0 | 0.000 | 100.0% | 30 |

The single working configuration is π = 10⁻² with `|C|` = 10⁶ — two hundred times the
security-realistic base rate. There the method behaves correctly (FDP 0.047 ≤ 0.05), which
is the regime it was designed for.

## 4.2 Aggregation and dependence (`t2b.py`) `[EXACT]` / `[SIM]`

Validity of the mean under arbitrary dependence follows from linearity, so simulating it is
uninformative: at k=1 the Monte-Carlo standard error is 1.118 over 8,000 replicates, larger
than the quantity being estimated. Cells failing an MC-error check print `UNINFORMATIVE`.

Group aggregation (synthetic), T = 500,000 events, 1% of groups malicious, μ = 5, k = 1:

| group size | hypotheses | `\|C\|` | recall | silence |
|---|---|---|---|---|
| 1 (event-level) | 500,000 | 10⁶ | 0.001 | 99.7% |
| 100 | 5,000 | 10⁶ | **1.000** | 0.0% |
| 1,000 | 500 | 10⁶ | **1.000** | 0.0% |
| any | any | 10⁴ | 0.000 | ≥96% |

## 4.3 Calibration-conditional validity (`t3_calvalidity.py`) `[EXACT]`

Computed analytically from `E[e|C] = ((n+1)/k)·(1−F(c₍ₖ₎))` with `1−F(c₍ₖ₎) ~ Beta(k, n+1−k)`,
so there is no Monte-Carlo error:

| k | ceiling | median | `P(E[e\|C] > 1)` | p99 | varies with `\|C\|`? |
|---|---|---|---|---|---|
| 1 | `\|C\|`+1 | 0.66–0.72 | **0.3679 = 1/e** | 4.1–4.9 | **no** — 10⁴ and 10⁶ identical |
| 10 | `\|C\|`/10 | 0.97 | ~0.45 | 1.9 | no |
| 100 | `\|C\|`/100 | 0.99 | ~0.48 | 1.24 | no |
| 1000 | `\|C\|`/1000 | 0.999 | ~0.49 | 1.07 | no |

## 4.4 Calibration validity on real traffic (`t4_real_calibration.py`) `[REAL]`

AIT `wilson`, 417,672 flows over 5 days, IsolationForest (200 trees), chronological thirds
for train / calibrate / test, benign against benign. `|C|` = 137,832, floor 7.26×10⁻⁶.

| nominal x | observed P(p ≤ x) | ratio | count |
|---|---|---|---|
| 0.5 | 6.88e−1 | 1.38 | 94,844 |
| 0.1 | 1.60e−1 | 1.60 | 22,021 |
| 0.05 | 7.88e−2 | 1.58 | 10,867 |
| 1e−2 | 9.27e−3 | **0.93** | 1,277 |
| 1e−3 | 8.63e−4 | **0.86** | 119 |
| 1e−4 | 2.03e−4 | 2.03 | 28 |
| 1e−5 | 1.45e−5 | 1.45 | **2** |

Rolling calibration over window W gives ratios of 1.10–1.31 at the 10⁻³ and 10⁻⁴ levels for
W ∈ {10k, 50k, 137k}.

With 137,832 held-out flows there were 2 events below 10⁻⁵ and none below 10⁻⁶. Validating
the quantiles the procedures operate at requires on the order of 10⁷–10⁸ held-out benign
events, so that region of the distribution is not auditable at benchmark scale.

## 4.5 Spending sequences and scale (`t6_gamma.py`) `[EXACT]`

Uniform `γ_j = 1/T` maximises `min_{t≤T} α_t`, since `min γ_t ≤ (1/T)Σγ_t ≤ 1/T`. It is
optimal for the objective *"able to reject at every t ≤ T"*. It is not optimal for "ever
rejects anything" — under that reading `γ₁ = 1` gives `α₁ = 0.025` and needs only n ≥ 39.
The horizon T must be fixed in advance and the stream must not exceed it.

Minimum `|C| = T/w₀ − 1` under uniform γ:

| scenario | T | min `\|C\|` | feasible |
|---|---|---|---|
| 1 day @ 10k flows/s | 8.64e8 | 3.46e10 | no |
| 1 hour @ 10k flows/s | 3.60e7 | 1.44e9 | no |
| CSE-CIC-IDS2018 event-level | 1.80e7 | 7.20e8 | no |
| LSPR23 event-level | 1.635e7 | **6.40e8** | no |
| 50,000 grouped hypotheses | 5.0e4 | 2.0e6 | yes |
| 288 grouped hypotheses (illustrative) | 288 | 1.15e4 | yes |

γ ∝ j^−1.6 requires 3.07×10¹³ at LSPR23 event level, five orders worse than uniform.

## 4.6 Dilution attack, synthetic (`t7_dilution.py`) `[SIM]`

`|C|` = 10⁶, k = 1, ceiling 1,000,001, a 40-event attack, threshold `1/α_t` at t=50 = 46,665:

| pad | group size | mean-e | detected |
|---|---|---|---|
| 0 | 40 | 175,000 | **yes** |
| 40 | 80 | 87,500 | yes |
| 200 | 240 | 29,167 | no |
| 1,000 | 1,040 | 6,731 | no |
| 10,000 | 10,040 | 697 | no |
| 100,000 | 100,040 | 70 | no |

Median padding to suppress: **0 / 153 / 475 / 732** for μ = 3 / 4 / 5 / 6. At μ = 3 the
episode is undetectable without any padding. Both independent audits reproduced these as
154/473/727 and 132/453/711 under slightly different estimators.

The padded statistic tends to ≈1 rather than 0, since benign pad events have `E[e] = 1`
each. Suppression therefore holds for any threshold above 1, which covers every real
threshold `1/α_t`.

**Inflation does not work.** Padding a purely benign group never forced a false discovery at
k ∈ {1, 100, 10⁴}: mean-e ≤ 10 and `Σe/n₀` ≤ 550 against a threshold of 46,665.

## 4.7 Fragmentation (`t8_split.py`) `[SIM]`

Per-group evidence is flat in group size — median mean-e ≈ 212,500 for G = 1…100 — because
for a pure-attack group `mean-e ≈ P(hit)·(|C|+1)` regardless of size. Only the variance
grows as groups shrink (p10–p90 widens from 185k–240k at G=1 to 0–1,000,001 at G=400).

End-to-end, splitting 400 malicious events across G groups yields 1, 2, 5, 20, 67, 79 groups
rejected for G = 1, 2, 5, 20, 100, 400. The only adverse effect is a longer stream: at
G ≥ 400 the threshold at position `j=G` exceeds the evidence ceiling.

## 4.8 Feasibility, robustness and the floor (`t9_threeway.py`) `[SIM]`

At LSPR23 scale (N = 16M, `|C|` = 10⁶, k = 1, α = 0.05):

- Feasibility requires a cap `n₀ ≥ 640`; below that the group count drives `α_T` under the
  evidence ceiling.
- Under the padding-robust rule the minimum detectable campaign is
  `N·k/(w₀·(|C|+1))` when `T = N/n₀` and every attack flow fires — 640 events, identical at
  every cap from 640 to 500,000.

| campaign size | admissible rule (mean) | padding-robust rule |
|---|---|---|
| 40 events | detected; suppressed by ~150 pads | **invisible** |
| 200 events | detected; suppressible | **invisible** |
| 1,000+ events | detected; suppressible | detected |

Scaling: protecting 40-event campaigns requires `|C|` ≥ 1.6×10⁷; 10-event, 6.4×10⁷;
single-event, 6.4×10⁸.

## 4.9 LSPR23 deployable grouping `[REAL]`

Grouping by (SrcIP, DstIP, time-bucket) over all 16,353,511 flows, with `|C|` taken at best
case as the entire benign corpus (14,708,912):

| bucket | T (hypotheses) | required `\|C\|` | feasible | floor (mal/episode) | episodes ≥ floor | % episodes | % malicious flows |
|---|---|---|---|---|---|---|---|
| 300s | 974,397 | 38,975,879 | **no** — 2.6× short | 44 | 553 | 5.2% | 94.8% |
| 1800s | 435,056 | 17,402,239 | **no** | 44 | 868 | 39.6% | 98.9% |
| 3600s | 346,557 | 13,862,279 | yes — 94% of the corpus | 47 | 524 | 39.1% | 99.1% |

Attack-episode size, in malicious flows per episode:

| bucket | #episodes | p25 | p50 | p75 | p90 | p95 | p99 | mean | max |
|---|---|---|---|---|---|---|---|---|---|
| 300s | 10,706 | 2 | **7** | 10 | 31 | 62 | 6,698 | 153.6 | 8,961 |
| 1800s | 2,191 | 13 | 17 | 56 | 188 | 191 | 21,057 | 750.6 | 51,235 |
| 3600s | 1,340 | 10 | 29 | 110 | 266 | 379 | 41,870 | 1,227.3 | 102,312 |

At 5-minute grouping 77.6% of episodes contain ten or fewer malicious flows and 3.8%
contain exactly one.

Coarser buckets merge genuinely distinct intrusions into a single episode, so episode counts
are not comparable across bucket widths and 39.1% is measured on a more forgiving unit than
a true incident.

## 4.10 Real detector and real attack (`t12_track2.py`) `[REAL]`

Features: `Protocol` plus columns 9–40, i.e. 33 of the 76 available. All malicious flows
retained, benign sampled at 50%, giving 8,999,203 rows, sorted by timestamp.
HistGradientBoostingClassifier, 200 iterations, learning rate 0.1, `l2_regularization=1.0`,
`min_samples_leaf=200`. Chronological 60 / 18 / 22 split.

Regularisation is load-bearing: with 0.6% positives and `l2_regularization=0`, leaf values
diverge (score range ±10⁶ rather than ±17) and tail ranking is destroyed — median attack-flow
rank falls from 3rd to 104th among ~10⁶ benign, and the k=1 firing rate from 48.9% to 0%.

**Detector:** AUROC **0.9991**, AUPRC 0.9990. `|C|` = 1,064,539 benign. Score range
[−17.28, 14.58].

**Measured separation:**
- `P(attack flow fires at k=1)` = **0.4821**, within the 0.04–0.89 implied by the μ = 3–6
  range assumed in simulation.
- `P(benign flow fires)` = 2.0×10⁻⁶ against a nominal 9.4×10⁻⁷, a factor of **2.1**,
  consistent with the 1.3–2.0× measured independently on AIT.

**Feasibility:**

| grouping | T | threshold `T/w₀` | ceiling `\|C\|+1` | feasible | episodes detected |
|---|---|---|---|---|---|
| 1h | 32,174 | 1,286,960 | 1,064,540 | **no** — by 21% | 0 / 421 |
| 2h | 26,098 | 1,043,920 | 1,064,540 | **yes** — by 2% | 32 / 284 (11.3%) |
| 6h | 21,222 | 848,880 | 1,064,540 | yes | 55 / 189 (29.1%) |

**Dilution attack**, padding drawn from real benign test flows:

| grouping | median pad to suppress | 10 pads | 25 | 50 | 100 | 250 | 500 | 1000 |
|---|---|---|---|---|---|---|---|---|
| 2h | **1** | 84.4% | 87.5% | 93.8% | 93.8% | 100% | 100% | 100% |
| 6h | **44** | 18.2% | 40.0% | 52.7% | 70.9% | 87.3% | 89.1% | 89.1% |

Real detected episodes sit barely above threshold, which is why the cost is 4–150× below the
synthetic estimate. At six-hour grouping 6 of 55 episodes survive 1,000 padding flows.

## 4.11 Detection floor against real scores (`t13_floor_crosscheck.py`) `[REAL]`

Same detector as §4.10, test stream N = 1,979,825 flows, `P_fire` = 0.4821. The
pre-committed cap `n₀` is set to the 99th-percentile group size, so that almost all groups
fall under it; a cap at the mean would invalidate the rule for half of them.

| grouping | T | mean group size | T × mean | n₀ (p99) | threshold |
|---|---|---|---|---|---|
| 1h | 32,174 | 61.5 | 1,979,825 = N | 378 | 1,286,960 |
| 2h | 26,098 | 75.9 | 1,979,825 = N | 416 | 1,043,920 |
| 6h | 21,222 | 93.3 | 1,979,825 = N | 419 | 848,880 |

| grouping | idealised floor | `P_fire`-corrected | exact | smallest detected episode | detected |
|---|---|---|---|---|---|
| 1h | 74 | 154 (×2.07) | 948 | **757** | 30 / 421 |
| 2h | 74 | 154 (×2.07) | 846 | **418** | 23 / 284 |
| 6h | 74 | 154 (×2.07) | 693 | **468** | 22 / 189 |

The exact form `n₀·T/(w₀·P_fire·(|C|+1))` predicts per-episode detection with 99.3% / 98.2%
/ 95.8% agreement (at 1h: TP=27, FP=0, FN=3, TN=391). False positives are zero at 1h and 2h,
so the formula never predicts a detection that does not occur; the false negatives are
episodes whose flows fired at above-average rate.

The idealised form `N·k/(w₀·(|C|+1))` understates by 9–13×. Exactly 2.07× of that gap is
`1/P_fire` (1/0.4821 = 2.074); the remainder comes from the `T = N/n₀` assumption.

`T × mean group size = N` holds exactly at every bucket width, so the floor is invariant to
**bucket width**. It is not invariant to the **choice of cap**: a usable cap must exceed
typical group sizes, and at p99 that is ≈6× the mean, inflating the floor proportionally.

Episodes clearing the exact floor: **6.4% / 6.3% / 13.8%** at 1h / 2h / 6h.

## 4.12 Cap validity and the policy space (`t14_T1_capvalidity.py`) `[REAL]`

Same detector and stream as §4.10, two-hour grouping, T = 26,098, threshold 1,043,920,
ceiling 1,064,540.

**Group sizes are heavy tailed**, which is what makes the cap a real design problem:
mean 75.9, p99 415, max 149,032.

At `n₀` = p99 = 416: **260 of 26,098 groups (1.00%) have `m > n₀`**, `E[Σe/n₀]` reaches
**358**, and those groups contain **86.2% of all flows**. A cap chosen from a typical
quantile is therefore invalid precisely where the traffic is.

Four policies that each guarantee `m ≤ n₀`. **Caps are derived from calibration-window group
sizes** (p99 = 345, max = 78,437), not from the test groups being evaluated, so they are
deployable rather than hindsight. Policy C's detections are aggregated back to the original
episode so all four share the same denominator.

| policy | n₀ | T | threshold | episodes detected | smallest detected (malicious flows) |
|---|---|---|---|---|---|
| A. `n₀` = max group size | 78,437 | 26,098 | 1,043,920 | **0 / 284** | — |
| B. truncate to first `n₀` | 345 | 26,098 | 1,043,920 | 12 / 284 | 382 |
| C. split oversized into sub-groups | 345 | 30,938 | 1,237,520 | **0 / 284** | — |
| D. pre-committed slot `F(e) = e_slot` | 1 | 26,098 | 1,043,920 | **109.4 / 284** (95% CI [102, 116]) | 2 |

D is randomised, so its entry is the exact expectation `Σ 1{feasible}·(firing fraction)` with
a Monte-Carlo interval over 400 draws, not a single realisation.

**Attack channel opened by each surviving policy.**

- **B** — front-loading. An attacker emitting leading benign flows pushes the malicious ones
  past index `n₀`, where they are never counted. Measured over the 12 detected episodes:
  median **345** leading pads, range 344–345, i.e. exactly the cost of filling the counted
  window.
- **D** — power dilution. Validity survives padding, because the statistic is a single
  e-value regardless of group size. Detection probability is the firing fraction of the
  group, so it decays as `1/m`: expected detections fall 109.4 → 54.7 → 21.9 → 10.9 → 1.1
  as the group is padded ×1, ×2, ×5, ×10, ×100. D is also **randomised** — the alert depends
  on which slot is drawn, which a SOC cannot audit or reproduce in a post-mortem.

**`P_fire` is not stationary.** Estimated on the calibration split it is **0.7477**; on the
test split, **0.4821**. Only the calibration estimate is available at deployment, and it
understates the floor by a factor of 1.55 here. Any floor formula depending on `P_fire`
inherits this drift.

The floor figures in §4.11 were computed with `n₀` = p99, so they characterise the arithmetic
of the formula rather than a deployable rule. Under a valid policy the operative numbers are
the detection rates in the table above.

## 4.13 Feasibility theorem (`t15_T3_theorem.py`) `[EXACT]`

**Setup.** Evidence `E_t ∈ [0, M]` with `M = (|C|+1)/k` for a threshold conformal e-value,
equivalently `M = 1/p_min = |C|+1` for a conformal p-value. The procedure rejects `H_t` iff
`E_t ≥ 1/α_t`. A rejection at `t` is therefore *possible at all* only if

    α_t ≥ 1/M.

Two structural families cover every procedure of interest.

**Family I — multiplicative.** `α_t = α·γ_t·g(H_{t−1})` with γ nonnegative and `Σγ ≤ 1`, and
`g ≤ c·(R_{t−1}+1)^d` for the rejection count `R`. Since `R_{t−1} ≤ t−1`,

    α_t ≤ α·c·γ_t·t^d,

so a rejection is possible at `t` only if `γ_t·t^d ≥ 1/(α c M)`.

> **Proposition 1.** If `γ_t·t^d → 0`, the set of times at which a rejection is possible is
> **finite**. If `γ_t·t^d` is additionally eventually non-increasing, that set is an initial
> segment and the infeasible state is **absorbing**.

The degree condition is not automatic and must be checked per procedure. Verified for our
two γ families: `max_t t·γ_t` = 0.4375 (at t=1) for γ ∝ j^−1.6 and 0.0764 (at t=55) for JM,
with `t·γ_t → 0` in both — so `d = 1` holds. **`d = 2` would fail for γ ∝ j^−1.6**, so a
procedure whose level grows quadratically in the rejection count would escape this argument.

**Family II — lag-sum.** `α_t = w₀γ_t + Σ_j a_j γ_{t−τ_j}` over rejection times `τ_j < t`
with `0 ≤ a_j ≤ α` for every j (LORD++: a₁ = α−w₀, a_j = α for j≥2; note Σ_j a_j exceeds α once
R≥2, so the bound uses a_j ≤ α term by term, NOT Σ a_j ≤ α). During a rejection-free run of
length Δ every lag `t−τ_j` is distinct and at least Δ, and `γ_t ≤ S(t) ≤ S(Δ)` where
`S(Δ) = Σ_{d≥Δ} γ_d`, so

    α_t ≤ (w₀ + α)·S(Δ).

> **Proposition 2.** `S` is non-increasing and `Σγ < ∞ ⟹ S(Δ) → 0`, so
> `Δ* = min{Δ : (w₀+α)S(Δ) < 1/M}` is finite. Because Δ only grows during a rejection-free
> run, the infeasible state is **absorbing** — and this requires no monotonicity of γ itself.

> **Corollary.** Feasibility over a horizon T with no prior rejections requires
> `|C| ≥ k/α_T − 1`. Under horizon-uniform γ (max-min optimal, §4.5) this is `|C| ≥ kT/w₀ − 1`.

**Procedure assignments.**

| procedure | `α_t` | family | d |
|---|---|---|---|
| LOND | `α·γ_t·(1+D_{t−1})` | I | 1 |
| e-LOND | `α·γ_t·(\|R_{t−1}\|+1)` | I | 1 |
| LORD++ | `γ_t w₀ + (α−w₀)γ_{t−τ₁} + αΣ_{j≥2}γ_{t−τⱼ}` | II | — |
| e-LORD / e-SAFFRON / mem-e-LORD (e-GAI) | `ω_t(α−Σ…)(R_{t−1}+1)`, i.e. Family I with `γ_t = ω_t∏_{j<t}(1−ω_j)` | I | 1 |
| SAFFRON | `(1−λ)[w₀γ_{t−C_{0+}} + …]` | **outside** — γ indexed by non-candidate count, not by `t` | — |
| ADDIS | `(τ−λ)[w₀γ_{S^t−C_{0+}} + …]` | **outside** — γ indexed by selected-non-candidate count | — |
| online e-BH | `E_i ≥ 1/(k*_t·α·γ_i)` | **outside** — `k*_t` is a fixed point over the whole history, not a count of rejections made | — |

**Correction to the coverage claim.** Propositions 1 and 2 are unaffected, but SAFFRON and
ADDIS do not belong to Family II as originally assigned: their lag arguments are counts of
*tested* hypotheses, not elapsed time, so `Δ` need not grow and `S(Δ)` need not fall. The
finite-horizon conclusion holds for them only under the added hypothesis that the driving
index diverges. On LSPR23 the ADDIS index is identically zero and the conclusion fails
outright (§4.20). online e-BH is outside both families because `k*_t` is not a function of
rejections already made, so the infeasible state is not absorbing.

Feasibility horizons, family I (largest `t` at which rejection is possible):

| γ | `\|C\|` | R=0 | R=10 | R=1000 | R=t (every hypothesis rejected) |
|---|---|---|---|---|---|
| j^−1.6 | 10⁴ | 29 | 129 | 2,176 | 7,942 |
| j^−1.6 | 10⁶ | 515 | 2,308 | 38,701 | unbounded within 10⁷ |
| JM | 10⁴ | 38 | 402 | 29,399 | unbounded within 10⁷ |
| JM | 10⁶ | 3,317 | 32,135 | 2,254,900 | unbounded within 10⁷ |

Absorbing Δ\*, family II. The polynomial family uses the **exact infinite normaliser**
`ζ(1.6) = 2.2858` (tail beyond 10⁷ is 3.45×10⁻⁵, immaterial):

| γ | `\|C\|`=10⁴ | 10⁶ | 10⁸ |
|---|---|---|---|
| j^−1.6 | 34,567 | 6,543,160 | 9,951,885 |
| JM | **not reached within horizon** | **not reached** | **not reached** |

JM has no closed-form normaliser, and its Δ\* tracks the truncation horizon rather than
converging: 9,680,767 at H = 10⁷ but 96,007,478 at H = 10⁸ for `|C|` = 10⁴, i.e. ≈0.96·H in
both cases. The lag-sum bound therefore does not bite for JM at any horizon we can compute,
and JM figures elsewhere in this section are horizon-dependent. Only the polynomial family
gives horizon-independent numbers. The Family-I horizons for JM carry the same caveat.

**Empirical confirmation — e-LOND fed maximum evidence.** Every attack flow is given the
ceiling value `M`, the most favourable possible input, over a 500,000-hypothesis stream:

Benign flows fire at the rate measured on real data (2×10⁻⁶, §4.10), and `R` increments on
any rejection including false ones, as e-LOND specifies:

| `\|C\|` | π | attacks | rejected | silent | first infeasible t | false rejections |
|---|---|---|---|---|---|---|
| 10⁴ | 10⁻⁴ | 50 | **0** | 100.0% | 30 | 0 |
| 10⁴ | 10⁻² | 5,000 | **0** | 100.0% | 30 | 0 |
| 10⁶ | 10⁻⁴ | 50 | **0** | 99.9% | 516 | 0 |
| 10⁶ | 10⁻² | 5,000 | 112 | 98.0% | 9,901 | 0 |
| 10⁸ | 10⁻⁴ | 50 | 8 | 92.8% | 36,213 | 0 |
| 10⁸ | 10⁻² | 5,000 | 5,000 | 0.0% | — | 1 |

e-LOND exhibits the same infeasibility as the p-value procedures. In the security-realistic
cell (`|C|` = 10⁶, π = 10⁻⁴) it rejects nothing even when every attack produces maximal
evidence. Only at `|C|` = 10⁸ with π = 10⁻² does it operate normally. Since a real detector
gives `P_fire` ≈ 0.48 rather than 1 (§4.10), deployment is strictly worse than this table.

The "reject everything" column shows the bootstrapping limit: a procedure that rejects at
every step retains full level and stays feasible indefinitely. That is not the security
regime, and it cannot be reached from a cold start, because rejections require feasibility.

## 4.14 Analyst-feedback baseline (`t16_T7_feedback.py`) `[REAL]`

Same detector and stream as §4.10. Episodes at two-hour grouping: 26,098 total, **284
malicious (1.09%)**, spanning 2.8 h. Episode score is the maximum flow score in the episode.

The controller alerts when the episode score exceeds `cal[⌊u·(|C|−1)⌋]` — an exact
calibration order statistic — and updates `u ← u + η(F̂DP − q)` **only when a new disposition
actually arrives**. Thresholds must be exact order statistics here: a 20,000-point quantile
grid addresses ~25 calibration order statistics per step in the upper tail and quantises the
controller into a fixed operating point regardless of gain.

**Latency is measured in alerts, not wall-clock**, because 90% of this stream's flows fall in
its final 25.6 h of a 161 h span, so row-index splits give very short windows. Latency L means
the disposition of an alert becomes available only after L further alerts.

| feedback latency | alerts | realised FDP | episode recall | alerts/day | updates | burn-in alerts |
|---|---|---|---|---|---|---|
| 0 (instant) | 141 | **0.057** | 0.468 | 1,207 | 132 | 10 |
| 5 alerts | 147 | 0.075 | 0.479 | 1,259 | 133 | 15 |
| 20 alerts | 148 | 0.061 | 0.489 | 1,267 | 119 | 30 |
| 50 alerts | 158 | 0.108 | 0.496 | 1,353 | 99 | 60 |
| 200 alerts | 270 | **0.378** | 0.592 | 2,312 | 61 | 210 |
| ∞ (no feedback) | 602 | **0.656** | 0.729 | 5,155 | 0 | 602 |

The controller reaches its target at low latency and holds it to roughly 50 alerts. The
L = 200 row is not a controlled system: 210 of its 270 alerts are issued before the first
disposition returns, so only 60 alerts are steered. Burn-in is at least `10 + L` alerts by
construction, which is itself a constraint on deployability at high latency.

Tuning sweep at zero latency, η ∈ {0.005, 0.02, 0.05, 0.2} × window ∈ {50, 200, 1000}: FDP
ranges 0.054–0.083 and recall 0.468–0.493. The best cell (η = 0.005, window = 200) gives FDP
**0.054**, recall 0.493, 148 alerts. η was selected on the evaluation stream, so this is a
best-case configuration for the rule family rather than a pre-committed one.

Oracle frontier for the episode max-score rule, using a Pareto-correct tie-break (maximise
true positives, then minimise FDP among ties — `fdp` is not monotone in k, so taking the last
index below the target can select a dominated point):

| target FDP | best recall | alerts | achieved FDP |
|---|---|---|---|
| 0.01 | 0.458 | 130 | **0.000** |
| 0.05 | 0.542 | 161 | 0.043 |
| 0.10 | 0.588 | 182 | 0.082 |
| 0.20 | 0.595 | 203 | 0.167 |

**Matched-error comparison against online error control.** Policy D (§4.12), the only valid
online rule with meaningful power, yields E[alerts] = 109.4, E[FDP] = 0.000, recall 0.385. At
**identical realised FDP (0.000)** the threshold rule reaches recall **0.458 on 130 alerts** —
19% more recall for 19% more alerts and the same error rate. At a matched *budget* of 134
alerts the threshold rule gives FDP 0.015 and recall 0.465, but that configuration is tuned by
search on the evaluation stream and is an upper bound rather than a deployable setting.

**Why the feedback signal is weak.** At 1.09% episode prevalence a q = 0.05 target admits only
about 298 alerts in the entire stream. Disposition feedback is inherently sparse in exactly the
regime where error control is claimed to matter.


## 4.15 Full-stream repetition (`t17_T2_fullstream.py`) `[REAL]`

Splits are defined on the full timestamp-sorted 16,353,511-flow stream before any
subsampling. Benign subsampling is confined to the training window; calibration and
deployment windows retain every flow. Fixed-size blocks (calibration 15%, test 15% of N) are
slid to five positions, so `T` and `|C|` vary because the **traffic** differs rather than
because the window sizes differ. Two detector seeds per position vary the scores while
leaving `T` and `|C|` untouched — the feasibility margin is therefore seed-independent by
construction, and pooling seeds into a single "distribution" of margins would be misleading.

**Feasibility margin `(|C|+1)·w₀/T − 1` by position:**

| grouping | T range | margins across the five positions | feasible |
|---|---|---|---|
| 1h | 35,714–65,190 | **−0.061**, +0.058, +0.273, +0.407, +0.269 | 4 / 5 |
| 2h | 31,568–57,368 | +0.067, +0.243, +0.536, +0.671, +0.436 | 5 / 5 |
| 6h | 26,028–47,037 | +0.302, +0.392, +0.536, +0.918, +0.742 | 5 / 5 |

`|C|` = 1,813,113–2,449,031 across positions, against 1,064,539 in the 50%-subsampled run.

**Detector quality and tail reach vary sharply by position**, and the two are not the same
thing:

| position | AUROC | fraction of attack flows reaching the ceiling |
|---|---|---|
| 0.55 | 0.916–0.927 | 0.885–0.904 |
| 0.62 | 0.799–0.871 | 0.650–0.889 |
| 0.70 | 0.847–0.914 | **0.000–0.030** |
| 0.77 | 0.828–0.833 | **0.018–0.019** |
| 0.85 | 0.999–0.9995 | 0.760–0.762 |

**Detections and dilution cost, two-hour grouping:**

| position | seed | AUROC | T | margin | episodes | detected | median pad |
|---|---|---|---|---|---|---|---|
| 0.55 | 0 | 0.916 | 57,368 | +0.067 | 275 | 82 | 3 |
| 0.55 | 1 | 0.927 | 57,368 | +0.067 | 275 | 72 | 3 |
| 0.62 | 0 | 0.799 | 49,267 | +0.243 | 398 | 93 | 6 |
| 0.62 | 1 | 0.871 | 49,267 | +0.243 | 398 | 33 | 3 |
| 0.70 | 0 | 0.914 | 37,231 | +0.536 | 287 | 64 | 62 |
| 0.70 | 1 | 0.847 | 37,231 | +0.536 | 287 | **0** | — |
| 0.77 | 0 | 0.828 | 31,672 | +0.671 | 246 | 50 | 35 |
| 0.77 | 1 | 0.833 | 31,672 | +0.671 | 246 | 54 | 35 |
| 0.85 | 0 | 0.999 | 31,568 | +0.436 | 255 | 116 | 35 |
| 0.85 | 1 | 0.9995 | 31,568 | +0.436 | 255 | 110 | 35.5 |

Two consequences. First, **detection is brittle to detector quality in a way ranking metrics
do not capture**: at position 0.70 an AUROC change of 0.914 → 0.847 between seeds takes
detections from 64/287 to 0/287, at an unchanged margin of +0.536, because what matters is
whether attack scores exceed *every* benign calibration score rather than how well they rank.
Second, **the earlier single-window "+2% margin" was an artefact of benign subsampling**
halving the calibration corpus; with the full corpus, margins at two-hour grouping run +0.067
to +0.671.

## 4.16 Padding theorem (`t18_T4_padding.py`) `[EXACT]`

Throughout, inputs are **finite**: `x ∈ [0,∞)^m`, `m ≥ 1`. With an infinite entry padding
does not drive the mean to zero and the bound below is vacuous.

**Definition (τ-padding-robustness).** A family `{F_N}_{N≥1}` of e-merging functions is
**τ-padding-robust**, for τ > 1, if for every `m ≥ 1`, every finite `x ∈ [0,∞)^m` with
`F_m(x) ≥ τ`, and every `r ≥ 0`, we have `F_{m+r}(x, 0^r) ≥ τ`.

**Definition (attainment).** `{F_N}` **attains** τ if some finite input has `F_m(x) ≥ τ`.
This assumption is necessary and not cosmetic: without it the definition is satisfied
vacuously by any family that never reaches τ — including the constant rule `F ≡ 1`, which is
symmetric, valid and padding-invariant, and which can never fire, since rejection requires
evidence `≥ 1/α_t > 1`. Attainment excludes exactly the rules that are useless.

> **Theorem.** No family of symmetric e-merging functions that **attains** τ is
> τ-padding-robust, for any τ > 1. Quantitatively, for every symmetric e-merging family,
> every finite `x ∈ [0,∞)^m` and every τ > 1,
>
>     F_{m+r}(x, 0^r) < τ   whenever   r > (Σᵢ xᵢ)/τ − m.

**Proof.** Vovk & Wang Prop. 3.1: the arithmetic mean `M_K` *essentially* dominates any
symmetric e-merging function — i.e. `F(e) > 1 ⟹ M_K(e) ≥ F(e)` on finite inputs. Ordinary
domination is false (`λ + (1−λ)M_K` is a counterexample), so the statement must be used via a
case split: if `F_N(x) ≤ 1` the bound is immediate since τ > 1; otherwise `F_N(x) ≤ M_K(x)`.
Either way

    F_N(x) ≤ max(1, mean(x))   for finite x.

Padding gives `mean(x, 0^r) = (Σx)/(m+r)`, hence `F_{m+r}(x, 0^r) ≤ max(1, (Σx)/(m+r))`,
which is below τ once `r > (Σx)/τ − m`. Attainment supplies an `x` with `F_m(x) ≥ τ` to which
this applies, so the family is not τ-padding-robust. ∎

**Tightness and the boundary.** At exactly `r = (Σx)/τ − m` the bound gives only
`F_{m+r} ≤ τ`, not `< τ`, and the arithmetic mean attains that equality — so the strict
inequality in `r > …` is tight. For integer padding against a `≥ τ` detection rule the first
suppressing pad count is `max(0, ⌊Σx/τ − m⌋ + 1)`.

**A special case with an independent proof.** For a uniformly random size-`m` subset `S` of
`[N]` (`m ≥ 1`), set `eᵢ = (N/m)·1{i ∈ S}`. Each has `E[eᵢ] = 1`, so these are valid
e-variables — perfectly negatively dependent, which an e-merging function must tolerate. Every
realisation is a permutation of `((N/m)·1_m, 0^{N−m})`, so a symmetric `F_N` returns the same
deterministic constant for all of them, and a constant e-variable is at most 1. Hence

    F_N((N/m)·1_m, 0^{N−m}) ≤ 1   for all N ≥ m.

This is **not** an independent proof of the theorem: it covers only the all-equal vector and
says nothing about `F_m` reaching τ beforehand. It is included because it needs no domination
result. Monte-Carlo check of the construction, 200,000 draws: `E[e₁]` = 1.0026, 0.9926, 0.9961
for `(N,m)` = (10,3), (100,5), (1000,40). The first is 0.76 standard errors above 1
(`Var = (N−m)/m = 7/3`, SE = 0.0034) — consistent with `E[e₁] = 1`, which holds exactly by
construction.

**Corollary (the escape is asymmetry).** `F_N(e) = e_slot` for a slot fixed in advance is an
increasing Borel map with `E[e_slot] ≤ 1` under arbitrary dependence, hence a valid e-merging
function, and it is invariant to zero-padding appended without moving the chosen slot:
verified unchanged at 10⁶ for `r` = 0, 10, 10³, 10⁵. Its power decays as `1/m` under padding
(§4.12, policy D) and it is randomised. The requirement is not asymmetry as such but that the
**adversary cannot choose which slot its events occupy**.

**The theorem is the measurement, not a separate confirmation.** The pad counts in §4.15 are
computed as `⌊Σe/τ − m⌋ + 1` — the bound above evaluated on real episodes. The measured
medians (3–62 padding flows at two-hour grouping, thresholds 1.26×10⁶–2.29×10⁶) are instances
of the bound. The empirical contribution is the magnitude on real traffic; the theorem supplies
the mechanism.

**Why the committed-cap rule is not a counterexample.** `Σe/n₀` is symmetric, valid and
padding-robust within its cap, but it is not an e-merging family for arities above `n₀` — its
validity is exactly the condition `m ≤ n₀` — and for `m < n₀` it is strictly dominated by the
arithmetic mean (5,000 against 25,000 for `x = (10⁶, 0, …, 0)`, `m` = 40, `n₀` = 200; at
`n₀ = m` the two coincide). It escapes by being inadmissible, and the power it forfeits is the
detection loss measured in §4.12.


## 4.17 Procedure comparison and attacker-origin padding (`t19_T5_T6.py`) `[REAL]`

Window position 0.85, two-hour grouping, `|C|` = 1,813,113, ceiling 1,813,114, T = 31,568
episodes (255 malicious), detector AUROC 0.9992.

**T5 — feasibility boundary per procedure on the real episode stream:**

| procedure | rejections | true positives | FDP | recall | silent | first infeasible t |
|---|---|---|---|---|---|---|
| LOND | 72 | 72 | 0.000 | 0.282 | 65.4% | 10,929 |
| e-LOND | 72 | 72 | 0.000 | 0.282 | 65.4% | 10,929 |
| LORD++ | 72 | 72 | 0.000 | 0.282 | 60.8% | 12,383 |

LOND and e-LOND share the level `α·γ_t·(R+1)` and are therefore identical by construction;
LORD++ differs only in when it becomes infeasible. All three are infeasible for 61–65% of the
episode stream, and none escapes the Family-I/II template of §4.13. **These rows are specific
to γ ∝ j^−1.6**; under the horizon-uniform spending sequence the same three procedures are
feasible over the whole stream and reach recall 0.576 (§4.20). SAFFRON, ADDIS, online e-BH
and the e-GAI family are measured in §4.20. Still not implemented: compound-e / e-closure
`[OPEN]`.

**T6 — does traffic from an attacker-controlled host score like generic benign traffic?**
105 source IPs appear as attack sources in the test window.

| padding pool | flows | P(fire) | mean e |
|---|---|---|---|
| generic benign | 1,638,722 | 2.81×10⁻⁵ | 50.9 |
| benign from attack sources | 301,016 | **1.20×10⁻⁴** | **216.8** |

Attacker-origin traffic is **4.3× more likely to reach the evidence ceiling**. But against a
rejection threshold of 1,262,720 the effect is immaterial: suppression requires
`r > (S − τn)/(τ − μ)`, and μ = 217 versus μ = 51 changes `τ − μ` by 0.013%. Measured pad
costs are identical for both pools — median **35**, p10 5, p90 268 over 116 detected episodes.

So the attacker does not need to be careful about what traffic they emit. The realism concern
that motivated this test does not bite: the mechanism survives problem-space padding
unchanged.

## 4.18 Related work on adversarial hypothesis testing `[PRIOR]`

A dedicated pass on the adversarial hypothesis-testing literature. What exists:

- **Adversary selects a distribution.** Yasodharan & Loiseau, *Nonzero-sum Adversarial
  Hypothesis Testing Games* (NeurIPS 2019, arXiv 1909.13031) — the adversary picks a
  distribution and generates i.i.d. samples; mixed-strategy Nash equilibria and error
  exponents, Bayesian and Neyman–Pearson. Related: *Detection Games Under Fully Active
  Adversaries* (arXiv 1802.02850), *M-ary Sequential Adversarial Hypothesis Testing Game*
  (arXiv 2206.09620).
- **Adversary perturbs test statistics.** Chen et al. (arXiv 2501.03402) — batch BH under
  test-score perturbation.
- **Adversary corrupts reported values.** *Distributed Multiple Testing with FDR Control in
  the Presence of Byzantines* (arXiv 2501.13242) — captured nodes report modified p-values;
  *Game Theoretical Approach to Sequential Hypothesis Test with Byzantine Sensors*
  (arXiv 1909.02909).
- **Adversary perturbs test inputs at deployment.** Adversarial robustness of learning-based
  conformal novelty detection (arXiv 2510.00463) — offline, evasion-style.

What is absent from all of them: an adversary that controls the **arity and composition of an
aggregated hypothesis**, or the **length of the hypothesis stream**. Every cited threat model
takes the hypothesis structure as given and attacks the values within it. The padding attack
(§4.16) and the group-inflation channel attack the structure itself.

## 4.19 Matched operating points (`t20_T8_matched.py`) `[REAL]`

One detector, one grouping, **now run at two window positions**: the **primary / guarantee
window** 0.55 (evidence a valid e-value) and the **stress-test window** 0.85 (evidence not a
valid e-value, §4.31). Every method is measured against the achievable frontier of the same
episode score, so no comparison is made at an unmatched operating point. **The negative result
— no method leaves recall on the table — holds at both windows; the headline is reported at the
valid primary window.**

### Primary / guarantee window (0.55, seed 0): AUROC 0.9165, `|C|` = 2,448,993, T = 57,368 episodes, 275 malicious

| method | alerts | FDP | recall | frontier recall at that budget | gap |
|---|---|---|---|---|---|
| online FDR (e-LOND, mean rule) | 18 | 0.000 | 0.065 | 0.065 | +0.000 |
| online FDR (policy D, slot) | 91.0 | 0.000 | 0.331 | 0.331 | +0.000 |
| feedback controller, L=0 | 119 | 0.076 | 0.400 | 0.396 | −0.004 |
| feedback controller, L=20 alerts | 135 | 0.185 | 0.400 | 0.404 | +0.004 |
| feedback controller, L=50 alerts | 150 | 0.267 | 0.400 | 0.440 | +0.040 |
| fixed threshold, no feedback | 1,047 | 0.836 | 0.625 | 0.625 | +0.000 |

Achievable frontier by error level (0.55):

| target FDP | best recall | alerts | achieved FDP |
|---|---|---|---|
| 0.000 | **0.378** | 104 | 0.000 |
| 0.010 | 0.396 | 110 | 0.009 |
| 0.050 | 0.396 | 110 | 0.009 |
| 0.100 | 0.396 | 110 | 0.009 |
| 0.200 | 0.440 | 145 | 0.166 |

**The comparison that matters is choice of point.** At the guarantee window e-LOND operates at
18 alerts / recall 0.065 / FDP 0.000; the frontier at the *same* FDP of 0.000 offers recall
0.378 on 104 alerts — nearly 6× the recall at the same zero error. The procedure selects a more
conservative point than the operator would, and the operator cannot override it, because the
point is set by the α-wealth process rather than a budget or an error target.

### Stress-test window (0.85, seed 0): AUROC 0.9992, `|C|` = 1,813,113, T = 31,568 episodes, 255 malicious

| method | alerts | FDP | recall | frontier recall at that budget | gap |
|---|---|---|---|---|---|
| online FDR (e-LOND, mean rule) | 72 | 0.000 | 0.282 | 0.282 | +0.000 |
| online FDR (policy D, slot) | 126.6 | 0.001 | 0.496 | 0.494 | −0.003 |
| feedback controller, L=0 | 161 | 0.068 | 0.588 | 0.588 | +0.000 |
| feedback controller, L=20 alerts | 160 | 0.081 | 0.576 | 0.588 | +0.012 |
| feedback controller, L=50 alerts | 171 | 0.140 | 0.576 | 0.616 | +0.039 |
| fixed threshold, no feedback | 875 | 0.763 | 0.812 | 0.812 | +0.000 |

Achievable frontier by error level (0.85):

| target FDP | best recall | alerts | achieved FDP |
|---|---|---|---|
| 0.000 | **0.459** | 117 | 0.000 |
| 0.050 | 0.584 | 156 | 0.045 |

**No method is inefficient at either window.** Every one sits on or within 0.040 recall of the
best achievable point at its own budget (max gap +0.040 for feedback L=50 at 0.55). Policy D's
−0.003 is the sampling slack of a randomised expectation. The 0.85 block reproduces the original
single-window run exactly and is asserted against it in the stage (`regression vs original 0.85
artifact: OK`).

**Reframe note (W2, 31 Aug 2026).** This section previously reported only 0.85. It now leads with
the valid 0.55 window per the reviewer worklist; the artifact `t20_T8.json` gained a `per_pos`
schema (`0.55`, `0.85`), the 0.85 numbers are byte-identical to the prior run, and both blocks are
checked in `t45`.

## 4.20 Procedures outside the LOND/LORD++ template (`t21_H6_procedures.py`, `t21c_H6_positions.py`, `t21d_H6_horizon.py`, `t21e_H6_frontier.py`) `[REAL]`

SAFFRON, ADDIS, online e-BH and the e-GAI family (e-LORD, e-SAFFRON, mem-e-LORD) on the
same episode stream as §4.17 and §4.19 — window position 0.85, two-hour grouping,
`|C|` = 1,813,113, ceiling 1,813,114, T = 31,568 episodes of which 255 are malicious,
detector AUROC 0.9992 — and repeated over the five window positions and two detector seeds
of §4.15. Evidence is the arithmetic-mean rule of §2.3; p-values for the p-value
procedures are `p = min(1, 1/Ev)` (§2.2).

Implementations are transcribed from the primary sources and unit-tested
(`t21b_h6_selftest.py`) against literal O(T²) transcriptions of the published formulas and
against four identities the papers themselves state: online e-BH at `γ_i = 1/K` evaluated
at `t = K` reduces to offline e-BH; `R(e-LOND) ⊆ R(online e-BH)`; e-LORD with sequence
`{ω_t}` equals e-LOND with `γ_t = ω_t∏_{j<t}(1−ω_j)`; and e-SAFFRON at `λ = 0` equals
e-LORD. The LOND / e-LOND / LORD++ rows reproduce §4.17 exactly and are asserted in the
script as a regression test.

**Two spending sequences are run for every γ-parameterised procedure**, because the choice
turns out to matter more than the procedure does:

- **`γ_j ∝ j^−1.6`** — the §4.17 choice. Requires no horizon.
- **horizon-uniform `γ_j = 1/T`** — max-min optimal (§4.5) and the sequence F1's corollary
  is stated in, but it needs the stream length in advance. `T` here is the number of
  evaluation episodes, so this row is **oracle** and is labelled as such throughout.

### Position 0.85, seed 0

`γ_j ∝ j^−1.6` (no horizon knowledge):

| procedure | rejections | true pos | FDP | recall | silent | first infeasible |
|---|---|---|---|---|---|---|
| LOND | 72 | 72 | 0.000 | 0.282 | 65.4% | 10,929 |
| e-LOND | 72 | 72 | 0.000 | 0.282 | 65.4% | 10,929 |
| LORD++ | 72 | 72 | 0.000 | 0.282 | 60.8% | 12,383 |
| SAFFRON (λ=0.5) | 70 | 70 | 0.000 | 0.275 | 75.1% | 7,856 |
| **ADDIS** (λ=0.25, τ=0.5) | **152** | 147 | 0.033 | **0.576** | **0.0%** | — |
| **online e-BH** | 72 | 72 | 0.000 | 0.282 | **0.0%** | — |

horizon-uniform `γ_j = 1/T` (**oracle**):

| procedure | rejections | true pos | FDP | recall | silent | first infeasible |
|---|---|---|---|---|---|---|
| LOND / e-LOND | 151 | 147 | 0.026 | 0.576 | 0.0% | — |
| LORD++ | 151 | 147 | 0.026 | 0.576 | 0.0% | — |
| SAFFRON | **0** | 0 | — | 0.000 | **100.0%** | 1 |
| ADDIS | **0** | 0 | — | 0.000 | **100.0%** | 1 |
| online e-BH | 152 | 147 | 0.033 | 0.576 | 0.0% | — |

e-GAI family (arXiv 2506.01452), which generates its own spending sequence from `ω_1`;
`ω_1 = 1/T` is the paper's own recommendation and is likewise **oracle**:

| procedure | rejections | true pos | FDP | recall | silent |
|---|---|---|---|---|---|
| e-LORD (ω₁=1/T, φ=ψ=0.5) | 150 | 147 | 0.020 | 0.576 | 0.0% |
| e-SAFFRON (λ=0.1) | 150 | 147 | 0.020 | 0.576 | 0.0% |
| mem-e-LORD (d=0.99) | 142 | 142 | 0.000 | 0.557 | 0.0% |

**mem-e-LORD controls mem-FDR, a decaying-memory error metric, not FDR.**

### Over five window positions × two detector seeds (min / median / max)

| γ | procedure | rejections | FDP | recall | silent (med) | mean FDP | configs with FDP > q |
|---|---|---|---|---|---|---|---|
| j^−1.6 | LOND / e-LOND | 0 / 24 / 72 | 0.000 / 0.000 / 0.000 | 0.000 / 0.085 / 0.282 | 85.1% | 0.0000 | 0 / 9 |
| j^−1.6 | LORD++ | 0 / 25 / 72 | 0.000 / 0.000 / 0.000 | 0.000 / 0.089 / 0.282 | 80.7% | 0.0000 | 0 / 9 |
| j^−1.6 | SAFFRON | 0 / 21 / 70 | 0.000 / 0.000 / 0.000 | 0.000 / 0.069 / 0.275 | 88.6% | 0.0000 | 0 / 6 |
| j^−1.6 | **ADDIS** | 0 / 106 / 152 | 0.000 / 0.033 / 0.046 | 0.000 / 0.274 / 0.576 | **0.0%** | **0.0243** | 0 / 9 |
| j^−1.6 | **online e-BH** | 0 / 31 / 72 | 0.000 / 0.000 / 0.000 | 0.000 / 0.094 / 0.282 | **0.0%** | 0.0000 | 0 / 9 |
| 1/T | LOND / e-LOND | 0 / 100 / 151 | 0.000 / 0.026 / 0.045 | 0.000 / 0.273 / 0.576 | 0.0% | 0.0209 | 0 / 9 |
| 1/T | LORD++ | 0 / 100 / 151 | 0.000 / 0.026 / 0.045 | 0.000 / 0.268 / 0.576 | 0.0% | 0.0209 | 0 / 9 |
| 1/T | SAFFRON, ADDIS | 0 / 0 / 0 | — | 0.000 | 100.0% | — | — |
| 1/T | online e-BH | 0 / 105 / 152 | 0.000 / 0.033 / 0.045 | 0.000 / 0.273 / 0.576 | 0.0% | 0.0237 | 0 / 9 |
| e-GAI | e-LORD, e-SAFFRON | 0 / 98 / 150 | 0.000 / 0.020 / 0.045 | 0.000 / 0.273 / 0.576 | 0.0% | 0.0195 | 0 / 9 |
| e-GAI | mem-e-LORD | 0 / 77 / 142 | 0.000 / 0.000 / 0.000 | 0.000 / 0.237 / 0.557 | 4.2% | 0.0000 | 0 / 9 |

One of the ten configurations (position 0.70, seed 1, AUROC 0.847) yields zero rejections
for every procedure — the tail-reach collapse of F5, not a property of any procedure.
Counts of nine therefore refer to the nine configurations that made at least one rejection.
**No configuration of any procedure exceeded q = 0.05.**

### Two procedures escape the §4.13 template, by two different mechanisms

**1. ADDIS escapes, and it is the only procedure that escapes without oracle horizon
knowledge.** §4.13's Family II indexes γ by elapsed time. ADDIS does not: its index is
`S^t − C_{0+}`, the count of hypotheses that were *selected* (`p ≤ τ`) but were *not
candidates* (`p ≤ λ`). Under threshold conformal evidence at k = 1 an episode p-value is
either exactly 1 — no flow in the group reached the ceiling, so the episode is discarded
and never selected — or small enough to be a candidate. Measured on this stream: 152
episodes have `Ev > 0`, all 152 are selected at τ = 0.5, all 152 are candidates at
λ = 0.25, and **no p-value falls in (λ, τ]**. The index is therefore exactly 0 at every
`t`, the level is pinned at `(τ−λ)·[W₀γ₀ + …]`, and it never decays. Silence is 0.0% at
all ten configurations.

**2. online e-BH escapes because its threshold is a fixed point over the whole history,
not a count of rejections already made.** It rejects `H_i` when `E_i ≥ 1/(k*_t·α·γ_i)`,
with `k*_t = max{k ≤ t : Σ_{j≤t} 1{E_j ≥ 1/(kαγ_j)} ≥ k}`. A rejection-free prefix is
therefore **not absorbing**: a stream in which no single hypothesis clears the k = 1 bar can
still admit many simultaneous rejections at a larger k. This is the bootstrapping route
§4.13 says "cannot be reached from a cold start"; online e-BH reaches it by computing the
fixed point rather than by accumulating rejections. Measured silence is 0.0% under both
spending sequences and both feasibility notions, at all ten configurations.

**What the escape does and does not buy is quantified in §4.21.** It removes the absorbing
state at any horizon, but it does **not** remove the calibration budget: making `R`
simultaneous discoveries still requires `|C| ≥ T/(αR) − 1`, linear in `T` and merely divided
by `R`. On this stream it also converts to **no additional power**: 72 rejections against
e-LOND's 72 under γ ∝ j^−1.6, and 152 against 151 under horizon-uniform γ. This is the
feasibility-is-not-detection separation of F5 appearing again, now on the procedure side:
online e-BH is never permanently silent, and detects exactly what e-LOND detects.

Both escapes are structural, not numerical, and **F1's coverage claim must be narrowed
accordingly** (see F1 below). §4.13's Propositions 1 and 2 are unaffected — what was wrong
was assigning SAFFRON and ADDIS to Family II, since their γ index is not elapsed time.

### What the escapes cost

**ADDIS's FDR guarantee does not transfer to this evidence.** ADDIS Theorem 1 requires
uniformly conservative null p-values, `P(P/τ ≤ x | P ≤ τ, F_{t−1}) ≤ x`. Measured over the
31,313 null episodes, only **5** are selected at all, and every one of them has
`p ≤ 1.1×10⁻⁶`, so the conditional probability is **1.0000 at every x** in
{0.001, 0.01, 0.05, 0.1, 0.25, 0.5} — the maximal possible violation. The ADDIS row is
therefore **empirical-only**: its realised FDP is 0.0243 on average over nine
configurations with a maximum of 0.046, but nothing in the theorem implies that. This is
the same discreteness that drives the escape — the escape and the loss of the guarantee
have one cause.

SAFFRON's assumption fails too, in its own way: null p-values are not super-uniform at the
extreme tail (`P(p ≤ 10⁻⁵) = 6.4×10⁻⁵`, though this is 2 null episodes out of 31,313 and
is not separable from Poisson noise at that count), and SAFFRON additionally assumes
independence, which episode-level conformal e-values do not satisfy.

**SAFFRON and ADDIS pay a constant wealth discount that is decisive at horizon-uniform
spending.** SAFFRON's level carries a factor `(1−λ)` and ADDIS's a factor `(τ−λ)`. Against
a conformal floor of `1/(|C|+1)` = 5.515×10⁻⁷, the initial levels at `γ = 1/T` are:

| procedure | initial level at γ = 1/T | vs floor 5.515×10⁻⁷ |
|---|---|---|
| LOND / e-LOND | `α/T` = 1.584×10⁻⁶ | feasible |
| LORD++ | `w₀/T` = 7.919×10⁻⁷ | feasible |
| SAFFRON | `(1−λ)w₀/T` = 3.960×10⁻⁷ | **infeasible from t = 1** |
| ADDIS | `(τ−λ)w₀γ₀` = 1.980×10⁻⁷ | **infeasible from t = 1** |

Both are silent for 100% of the stream at all ten configurations. The adaptivity that lets
ADDIS escape under a polynomial γ is exactly what sinks it under the optimal one.

**e-GAI does not escape.** Its own §3.2 shows e-LORD is e-LOND with
`γ_t = ω_t∏_{j<t}(1−ω_j)`, so it sits inside Family I by construction and merely
reparameterises the spending sequence. The measured implied sequence is
`γ_1 = 3.168×10⁻⁵ = 1/T`, `γ_T = 8.575×10⁻⁶`, summing to 0.865 — essentially the
horizon-uniform sequence with a mild geometric decay.

**mem-e-LORD, the published fix for α-death, does not act before the first rejection.**
During a rejection-free run `R^d_{t−1} = 0`, so its level is identical to e-LORD's. It
helps only after a rejection has occurred, which is precisely the event F2's
first-rejection deadline makes unattainable. Measured, it is strictly worse than e-LORD
(142 rejections against 150) because the decaying memory also discounts rejections once
they arrive.

### Horizon misspecification (`t21d_H6_horizon.py`)

Both oracle configurations are re-run over a guessed horizon `T̂ = c·T`:

| c | LOND / e-LOND | LORD++ | online e-BH | e-LORD (ω₁ = 1/T̂) |
|---|---|---|---|---|
| 0.1 | 70 rej, 90.0% silent | 70 rej, 80.6% silent | 70 rej, 90.0% silent | 139 rej, 17.0% silent |
| 0.25 | 71 rej, 75.0% silent | 151 rej, 0.0% | 71 rej, 75.0% silent | 150 rej, 0.0% |
| 0.5 | 131 rej, 50.0% silent | 152 rej, 0.0% | 131 rej, 50.0% silent | 150 rej, 0.0% |
| **1 (oracle)** | **151 rej, 0.0%** | **151 rej, 0.0%** | **152 rej, 0.0%** | **150 rej, 0.0%** |
| 2 | 151 rej, 0.0% | **0 rej, 100% silent** | 151 rej, 0.0% | 149 rej, 0.0% |
| 5 | **0 rej, 100% silent** | 0 rej, 100% silent | 149 rej, 0.0% | 149 rej, 0.0% |
| 10 | 0 rej, 100% silent | 0 rej, 100% silent | 149 rej, 0.0% | **0 rej, 100% silent** |
| 100 | 0 rej, 100% silent | 0 rej, 100% silent | **144 rej, 0.1% silent** | 0 rej, 100% silent |

Tolerance to over-estimating the horizon, which is the direction an operator errs in:
**ADDIS needs no horizon at all**; **online e-BH tolerates 100×** (144 of 152 rejections at
c = 100) because its feasibility condition carries the extra factor `T`; e-GAI tolerates
5×; LOND and LORD++ tolerate 2× and 1× respectively. Under-estimating is uniformly fatal,
since the budget is exhausted before the stream ends.

### Consequence for §4.19 and F13 (`t21e_H6_frontier.py`)

Every H6 configuration placed on the §4.19 frontier of the same episode score:

| method | alerts | FDP | recall | frontier recall at that budget | gap |
|---|---|---|---|---|---|
| e-LOND, `γ ∝ j^−1.6` (the §4.19 row) | 72 | 0.000 | 0.282 | 0.282 | +0.000 |
| e-LOND, horizon-uniform γ (oracle) | 151 | 0.026 | 0.576 | 0.576 | +0.000 |
| ADDIS, `γ ∝ j^−1.6` | 152 | 0.033 | 0.576 | 0.576 | +0.000 |
| ADDIS, horizon-uniform γ | 0 | — | 0.000 | 0.000 | +0.000 |
| online e-BH, `γ ∝ j^−1.6` | 72 | 0.000 | 0.282 | 0.282 | +0.000 |
| online e-BH, horizon-uniform γ | 152 | 0.033 | 0.576 | 0.576 | +0.000 |

Every configuration sits **exactly on** the achievable frontier at its own budget, which
strengthens §4.19's efficiency result. But the operating point moves by a factor of **2.0
in recall** (0.282 → 0.576) purely with the spending sequence, at a comparable error rate.
The frontier at FDP 0.000 offers recall 0.459 on 117 alerts, so the `γ ∝ j^−1.6` point is
dominated — while the horizon-uniform point at 151 alerts / recall 0.576 / FDP 0.026 is
not. **F13's "the point it picks is dominated" is therefore specific to `γ ∝ j^−1.6`, and
is restated below.** What survives, and is strengthened, is that the operator does not
choose the point: it is set by γ and the α-wealth process, and γ is neither an error target
nor a budget.

## 4.21 What the online e-BH escape costs (`t21f_H6_scaling.py`) `[EXACT]`

§4.20 shows online e-BH's rejection-free state is not absorbing. Two distinct questions
follow, and conflating them overstates the escape.

**(a) Can a rejection ever happen?** `k*_t ≤ t ≤ T`, so the necessary condition for
hypothesis `i` to be rejectable at any later time is `|C| ≥ k/(Tαγ_i) − 1`, which under
horizon-uniform γ is `|C| ≥ k/α − 1` = **19, independent of the horizon**:

| horizon T | Family I/II cold start, `kT/w₀ − 1` | online e-BH at `k = T`, `k/α − 1` |
|---|---|---|
| 10³ | 39,999 | 19 |
| 31,568 | 1,262,719 | 19 |
| 10⁶ | 39,999,999 | 19 |
| 16,353,511 (LSPR23 event scale) | **654,140,439** | **19** |

The Family I/II state is absorbing at every horizon; online e-BH's is not. **But `k = T`
is attainable only if every hypothesis is rejected, so this is an upper bound and not a
calibration budget.**

**(b) What is attainable?** Making `R` simultaneous discoveries under horizon-uniform γ
requires `R` hypotheses each carrying `E ≥ T/(Rα)`, hence `|C| ≥ T/(αR) − 1`:

| horizon T | R = 1 | R = 10 | R = 152 | R = 10⁴ | Family I/II cold start |
|---|---|---|---|---|---|
| 31,568 | 631,359 | 63,135 | 4,153 | 62 | 1,262,719 |
| 10⁶ | 19,999,999 | 1,999,999 | 131,578 | 1,999 | 39,999,999 |
| 16,353,511 | 327,070,219 | 32,707,021 | **2,151,777** | 32,706 | **654,140,439** |

**The requirement is still linear in T, divided by R.** The improvement over the Family I/II
cold start is exactly `αR/w₀ = 2R` — a constant factor per simultaneous signal, not a factor
of the horizon. At the `R` = 152 measured in §4.20 that is 304×: 2.15 million rather than 654
million at LSPR23 event scale. Large, but the same order of difficulty.

Confirmed against the actual fixed point: online e-BH fires exactly when `|C|` clears
`T/(αR) − 1` and not below it, at `(T, R)` = (10⁴, 100), (10⁵, 10³), (10⁶, 10⁴) and
(10⁶, 100), with `|C|` set 5% above and 5% below the predicted boundary. e-LOND rejects
nothing in any of these cells.

**Consequence.** The honest statement of the escape is that online e-BH removes the
*absorbing state*, not the *calibration budget*, and on the LSPR23 episode stream it
converts to no additional detections at all (§4.20). This is F5's
feasibility-is-not-detection separation reappearing on the procedure side.

## 4.22 Second detector (`t22_H1_H2_matrix.py`) `[REAL]`

Every real-data result before this one uses HistGradientBoosting alone. This adds
**Isolation Forest**, unsupervised, over the same five window positions and two seeds as
§4.15, at two-hour grouping.

Being unsupervised changes the split design and it is worth stating exactly how. Isolation
Forest consumes **no labels at fit time**, so its training rows are drawn from the whole
training window rather than from the label-balanced subsample the supervised detector uses.
It is given `n_estimators` = 200 and `max_samples` = 8192 — fixed in advance, never tuned
against test performance, and deliberately more generous than scikit-learn's defaults of 100
and `min(256, n)`, so the comparison does not handicap it. **Conformal calibration still
needs a benign calibration window**, so labels are still required there: being unsupervised
removes the label requirement from training only, not from the method.

| detector | AUROC | feasibility margin | tail reach | benign fire ratio |
|---|---|---|---|---|
| HistGradientBoosting | 0.799 / 0.893 / 0.9995 | +0.067 / +0.436 / +0.671 | 0.000 / 0.017 / 0.610 | 0.00 / 1.94 / 50.90 |
| Isolation Forest | 0.750 / 0.773 / 0.811 | +0.067 / +0.436 / +0.671 | **0.000 / 0.000 / 0.000** | 0.00 / 0.00 / 9.26 |

min / median / max over the ten configurations. "Tail reach" is the fraction of **attack
flows** whose e-value reaches the evidence ceiling; "benign fire ratio" is the measured
benign firing rate over the nominal `k/(|C|+1)`.

**The feasibility margin is identical for the two detectors, to every digit.** That is not a
coincidence and not a bug: the margin is `CEIL·w₀/T − 1`, and `CEIL = (|C|+1)/k` depends only
on the size of the benign calibration set, while `T` depends only on the grouping. Neither
depends on the scores. The margin is a statement about the resolution of the evidence, not
about the quality of the detector.

**Tail reach is 0.000 at every one of the ten configurations.** Not one attack flow, at any
position or seed, scores strictly above all 1.8–2.4 million benign calibration scores. AUROC
0.75–0.81 is a real ranking signal, and it buys nothing at all here, because what the
procedures need is not ranking but the far tail.

| detector | procedure | rejections | true positives |
|---|---|---|---|
| Isolation Forest | e-LOND, γ ∝ j^−1.6 | 0 in all 10 | 0 |
| Isolation Forest | e-LOND, horizon-uniform γ | 0 in all 10 | 0 |
| Isolation Forest | online e-BH, horizon-uniform γ | 0 in all 10 | 0 |
| Isolation Forest | **ADDIS**, γ ∝ j^−1.6 | **1 alert in 4 of 10** | **0** |

The three procedures that respect the feasibility boundary are completely silent. The one
that escapes it (§4.20) is not: ADDIS issues one alert in four of the ten configurations, and
**every one of them is a false discovery** — FDP 1.000, recall 0.000. Escaping the
feasibility template does not produce detections; with a detector that cannot reach the
ceiling, it produces only false alerts.

**H1 therefore does not soften the conclusions; it hardens them.** The objection it retires
is "your conclusions are an artefact of one classifier". The answer is that with a second,
unsupervised detector the pipeline yields zero true detections at every configuration, while
the feasibility margin is unchanged — which is F5's feasibility-is-not-detection separation
in its sharpest form: identical margin, 152 detections against 0.

---

## 4.23 Rank k on real data (`t22_H1_H2_matrix.py`) `[REAL]`

Every real-data experiment before this one fixes `k = 1`. §4.3 sweeps k analytically; F11's
ceiling-versus-reliability trade-off has never been measured on real scores. Five positions
× two seeds, two-hour grouping, HistGradientBoosting.

| k | ceiling | feasibility margin | tail reach | benign fire ratio | e-LOND (uniform γ) rejections |
|---|---|---|---|---|---|
| 1 | 2,287,989 | +0.067 / **+0.436** / +0.671 | 0.000 / 0.017 / 0.610 | 0.00 / 1.94 / **50.90** | 0 / 100 / 151 |
| 10 | 228,799 | −0.893 / **−0.856** / −0.833 | 0.000 / 0.019 / 0.631 | 0.23 / 0.80 / 10.62 | 0 / 0 / 0 |
| 100 | 22,880 | −0.989 / **−0.986** / −0.983 | 0.006 / 0.021 / 0.686 | 0.09 / 0.95 / 12.47 | 0 / 0 / 0 |
| 1000 | 2,288 | −0.999 / **−0.999** / −0.998 | 0.007 / 0.050 / 0.995 | 0.10 / 3.62 / **6.80** | 0 / 0 / 0 |

(median ceiling shown; ceilings vary with `|C|` across positions.)

**k = 1 is the only feasible rank.** The ceiling falls exactly as `1/k`, so the margin goes
from +0.436 to −0.999 and e-LOND makes zero rejections at every `k ≥ 10` in every
configuration. Raising k to buy reliability does not trade power for validity — it removes
the operating point altogether.

**And k = 1 is the least reliable rank.** The worst-case benign fire ratio falls from 50.90
at k = 1 to 6.80 at k = 1000: more calibration mass behind the threshold makes the realised
null rate track its nominal value more closely, exactly as F11 predicts. So the two columns
move in opposite directions and there is no k at which both are acceptable. F11 was an exact
statement about `E[e|C]`; this is the same trade-off measured on real detector scores.

Tail reach rises with k (median 0.017 → 0.050, max 0.610 → 0.995), confirming that the bar
does get easier to clear — but the ceiling it buys is too low to reject against.

---

## 4.24 The error target q, swept jointly with the spending sequence (`t24_H3_q_gamma.py`) `[REAL]`

Everything else in the record runs at `q = 0.05`, `w₀ = q/2`. §4.20 showed γ moves the
realised operating point by a factor of 2.0 in recall, which is more than q does, so
sweeping q alone would credit q with an effect that belongs to γ. This is therefore a joint
sweep. Five positions × two seeds, k = 1, two-hour grouping.

**The corollary `|C| ≥ kT/w₀ − 1` holds exactly.** It predicts `(margin + 1)` is proportional
to q:

| q | w₀ | feasibility margin (min/med/max) | (margin+1) median | ratio to q = 0.05 | predicted |
|---|---|---|---|---|---|
| 0.01 | 0.005 | −0.787 / −0.713 / −0.666 | 0.287 | **0.200** | 0.2 |
| 0.05 | 0.025 | +0.067 / +0.436 / +0.671 | 1.436 | **1.000** | 1.0 |
| 0.10 | 0.050 | +1.134 / +1.872 / +2.341 | 2.872 | **2.000** | 2.0 |
| 0.20 | 0.100 | +3.269 / +4.744 / +5.682 | 5.744 | **4.000** | 4.0 |

The measured ratio equals the prediction to three decimals at every q. **Relaxing the error
target buys feasibility strictly linearly and no faster.** At `q = 0.01` the median
configuration is infeasible; to gain one order of magnitude in feasibility an operator would
have to run at `q ≈ 0.5`, which is not an error target in any useful sense. This retires "the
boundary is an artefact of a strict target": the boundary moves exactly as much as the
theory says and no more.

**What q buys in operating point, against what γ buys:**

| q | e-LOND recall, γ ∝ j^−1.6 | e-LOND recall, horizon-uniform γ | silence at poly γ |
|---|---|---|---|
| 0.01 | 0.049 | 0.000 (100% silent) | 96.0% |
| 0.05 | 0.085 | 0.273 | 85.1% |
| 0.10 | 0.100 | 0.274 | 70.6% |
| 0.20 | 0.137 | 0.274 | 44.8% |

Sweeping q over a **twenty-fold** range moves median recall from 0.049 to 0.137, a span of
0.088. Switching the spending sequence at fixed q moves it from 0.085 to 0.273 at
`q = 0.05` — a shift of 0.188, more than twice what the entire q sweep achieves. **The
operator's nominal control (q) is the weaker of the two levers, and the stronger one (γ) is
not an error target, an alert budget, or anything else with an operational meaning.** This is
F13 measured a second way.

Two asymmetries are worth recording. At `q = 0.01` under horizon-uniform γ both e-LOND and
ADDIS are 100% silent while online e-BH still reaches recall 0.273 — the ARC structure
tolerates a stricter target. And ADDIS is completely insensitive to q under γ ∝ j^−1.6
(recall 0.274 at every q), because its level is pinned at `γ₀` by the discarding rule rather
than being set by the wealth.

---

## 4.25 Cap-selection sweep (`t25_H5_caps.py`) `[REAL]`

§4.12 tested `n₀` = p99 and max only, and §4.11 shows the detection floor scales with `n₀`.
This sweeps `n₀` over mean, p50, p90, p99, p999 and max, all derived from
**calibration-window** group sizes. Five positions × two seeds, two-hour grouping,
threshold `τ = T/w₀`.

Two rules per cap: **raw** `Σe/n₀` over the whole group, which is a valid e-value only where
occupancy `m ≤ n₀`; and **truncated** to the first `n₀` events, which is valid at every cap
by construction (policy B of §4.12).

| cap | `n₀` | groups with m > n₀ | flows in those groups | max `m/n₀` | flows needed to fire |
|---|---|---|---|---|---|
| mean | 47 | 5.72% | 93.5% | 2,258 | 38 |
| p50 | 2 | 37.58% | 98.8% | 60,370 | 2 |
| p90 | 21 | 10.24% | 95.8% | 5,749 | 17 |
| p99 | 408 | 1.08% | 82.6% | 340 | 285 |
| p999 | 7,258 | 0.12% | 59.4% | 13 | 4,907 |
| max | 97,911 | 0.01% | 16.6% | 1 | 72,274 |

| cap | detections, raw | detections, truncated | detection floor | front-load cost |
|---|---|---|---|---|
| mean | 0 / 40 / 102 | 0 / 35 / 81 | 28 / 45 / 52 | 3 / 16 / 21 |
| p50 | 0 / 99 / 146 | 0 / 71 / 108 | 2 / 3 / 5 | **1 / 1 / 1** |
| p90 | 0 / 68 / 133 | 0 / 60 / 109 | 16 / 18 / 24 | 2 / 8 / 8 |
| p99 | 0 / 0 / 34 | 0 / 0 / 24 | 221 / 316 / 384 | 65 / 116 / 122 |
| p999 | 0 / 0 / 12 | 0 / 0 / 6 | 20,777 | 3,553 / 3,560 / 3,568 |
| max | 0 / 0 / 2 | 0 / 0 / 0 | 140,316 | — |

against 246 / 275 / 398 attack episodes per configuration.

**"Flows needed" is `⌈τn₀/CEIL⌉` and is exactly linear in `n₀`** — the §4.11 floor scaling,
now measured across three orders of magnitude of cap. The measured floors track it.

**The sweep closes F8 across the whole cap range rather than at two points.** Truncation is
valid at every cap, so validity is not the binding constraint; the binding constraint is
that its two failure modes move in opposite directions with `n₀`:

- at the most powerful cap (p50, `n₀` = 2) the truncated rule detects 71 of 275 episodes but
  costs the attacker **one** padding flow to suppress;
- at the cap where the attack is expensive (p999, 3,560 padding flows) it detects 6;
- at `n₀` = max the front-load attack is irrelevant because there is nothing to suppress.

There is no cap at which the rule is both powerful and expensive to attack. The raw rule is
more powerful at every cap but is invalid where it matters most: at p50 the 37.58% of groups
that violate `m ≤ n₀` hold **98.8% of all flows**, with `E[Σe/n₀] = m/n₀` reaching 60,370.

## 4.26 The Bates calibration-conditional adjustment, applied (`t23_H7_bates.py`) `[EXACT]` / `[REAL]`

F10 states that conditional validity fails with probability exactly 1/e at k = 1 and that
Bates, Candès, Lei, Romano & Sesia (Ann. Statist. 2023) supply the fix. The fix had never
been applied. This applies it and prices it.

**The adjustment, in e-value form.** Conditional on a calibration set `C` of size `n`, the
rank-k threshold rule fires on a null point with probability `U = 1 − F(c_(n+1−k))`, and
`U ~ Beta(k, n+1−k)` over the draw of `C` (§4.3). The nominal multiplier `M = (n+1)/k`
satisfies `E[e|C] = M·U ≤ 1` only when `U ≤ k/(n+1)`. To be valid conditionally on `C` with
probability at least `1 − δ`, the multiplier must instead be

    M_δ(k, n) = 1 / Q_{1−δ}(Beta(k, n+1−k)),

which gives `E[e|C] = U/Q_{1−δ} ≤ 1` with probability exactly `1 − δ`. This is the
exact-order-statistic form of the Bates calibration-conditional p-value written for
e-values; the reference implementation is `msesia/conditional-conformal-pvalues`. The DKW
form they also give, `h(t) = t + √(log(1/δ)/(2n))`, is reported alongside because it is the
bound most people reach for.

**Power cost at `|C|` = 1,813,113:**

| k | δ | nominal ceiling | beta-adjusted | ratio | DKW-adjusted | ratio |
|---|---|---|---|---|---|---|
| 1 | 0.01 | 1,813,114 | 393,713 | **0.217** | 887 | 0.00049 |
| 1 | 0.05 | 1,813,114 | 605,232 | **0.334** | 1,100 | 0.00061 |
| 1 | 0.10 | 1,813,114 | 787,425 | **0.434** | 1,254 | 0.00069 |
| 1 | 0.20 | 1,813,114 | 1,126,551 | 0.621 | 1,500 | 0.00083 |
| 10 | 0.10 | 181,311 | 127,630 | 0.704 | 1,246 | 0.00687 |
| 100 | 0.10 | 18,131 | 16,044 | 0.885 | 1,174 | 0.06473 |
| 1000 | 0.10 | 1,813 | 1,742 | **0.961** | 742 | 0.40903 |

**The correction is expensive exactly where it is needed and free where it is useless.** At
k = 1 — the only feasible rank (§4.23) — it costs 38% to 78% of the ceiling. At k = 1000 it
costs 4%, and k = 1000 has a ceiling of 1,813 against a required threshold in the millions.
The correction shrinks as `1 + O(1/√k)` because more calibration mass sits behind a larger
rank, and that is the same reason the ceiling itself shrinks. **F11's trade-off is therefore
not something the fix resolves; the fix is priced by the same quantity that creates it.**

**The DKW form is unusable in this tail**, costing a factor of 1,200–2,000 at k = 1: its
additive `√(log(1/δ)/(2n))` term is 8×10⁻⁴ against `k/(n+1)` = 5.5×10⁻⁷, so it swamps the
signal entirely. Anyone applying the standard uniform bound here would conclude the method
is hopeless for the wrong reason.

**The guarantee holds empirically.** Over 2,000 calibration draws taken without replacement
from a 3.45M benign score pool, with the conditional null rate `u` estimated on a disjoint
500,000-flow holdout:

| `n_cal` | k | analytic `P(Beta(k,n+1−k) > k/(n+1))` | measured, nominal | measured, beta-adjusted (target ≤ 0.10) |
|---|---|---|---|---|
| 1,000 | 1 | 0.3681 | **0.3705** | 0.0920 |
| 1,000 | 10 | 0.4586 | 0.4385 | 0.0835 |
| 1,000 | 100 | 0.4888 | 0.4830 | 0.0925 |
| 10,000 | 1 | 0.3679 | 0.2870 | 0.0805 |
| 100,000 | 1 | 0.3679 | 0.1090 | 0.0355 |
| 100,000 | 100 | 0.4867 | 0.4245 | 0.0550 |

At `n_cal` = 1,000 the measured nominal exceedance matches the analytic 1/e to three
decimals, reproducing F10 on real detector scores. It drifts **below** the analytic value as
`n_cal` grows because the check resolves `u` on a finite holdout: at `n_cal` = 10⁵ the
quantity is `u ≈ 10⁻⁵` and a 500,000-flow holdout resolves it only to ±2×10⁻⁶, with the
detector's scores tied in the far tail. That is a resolution limit of the measurement, not
evidence that the 1/e result depends on `n`. **The adjusted rule holds its stated δ = 0.10 in
every cell**, which is the claim H7 exists to test.

**Detection cost on the real stream, δ = 0.10, five positions × two seeds:**

| k | mode | feasibility margin (min/med/max) | e-LOND (uniform γ) rejections | ADDIS (poly γ) rejections |
|---|---|---|---|---|
| 1 | nominal | +0.067 / **+0.436** / +0.671 | 0 / 100 / 151 | 0 / 106 / 152 |
| 1 | beta-adjusted | −0.537 / **−0.376** / −0.274 | 0 / **62** / 150 | 0 / 106 / 152 |
| 10 | nominal | −0.893 / −0.856 / −0.833 | 0 / 0 / 0 | 2 / 113 / 161 |
| 10 | beta-adjusted | −0.925 / −0.899 / −0.882 | 0 / 0 / 0 | 2 / 113 / 161 |
| 100 | beta-adjusted | −0.991 / −0.987 / −0.985 | 0 / 0 / 0 | 71 / 126 / 350 |
| 1000 | beta-adjusted | −0.999 / −0.999 / −0.998 | 0 / 0 / 0 | 96 / 663 / 745 |

**Applying the known fix at the only feasible rank moves the median configuration from
feasible (+0.436) to infeasible (−0.376) and cuts e-LOND's rejections from 100 to 62.** So
the honest answer to "you identified a known problem and ignored its known solution" is that
the solution exists, works, and costs the feasibility margin the result depends on.

**ADDIS is unaffected by the adjustment** (106 → 106) because its level is pinned by the
discarding rule rather than by the evidence ceiling (§4.20) — but see below.

**ADDIS's FDP as k rises.** §4.20 found ADDIS escapes the §4.13 template while violating its
own uniform-conservativeness condition, and observed FDP 0.033 at k = 1. Sweeping k shows
that was luck, not control:

| k | rejections (min/med/max) | FDP (min/med/max) | configurations with FDP > q |
|---|---|---|---|
| 1 | 0 / 106 / 152 | 0.000 / **0.033** / 0.046 | **0 / 9** |
| 10 | 2 / 113 / 161 | 0.009 / **0.070** / 1.000 | **8 / 10** |
| 100 | 71 / 126 / 350 | 0.030 / **0.246** / 0.497 | **9 / 10** |
| 1000 | 96 / 663 / 746 | 0.155 / **0.707** / 0.756 | **10 / 10** |

At k = 1000 ADDIS issues a median 663 alerts of which 71% are false, against a target of
0.05. **The one procedure that escapes the feasibility boundary does not control the error
rate it was chosen for.** This is the empirical counterpart of the assumption violation
measured in §4.20, and it means F1's narrowing does not need to concede error control to
ADDIS at any rank other than the one where it happened to hold.

---

---

## 4.27 Label noise and the FDP interval (`t27_H8_labelnoise.py`) `[REAL]`

FDP is the headline metric and it is measured against LSPR23 labels that had never been
validated. Engelen et al. (WTMC'21) and Liu et al. (CNS'22) measured 6.67% and 7.53% label
corruption in CIC-IDS2017 and CSE-CIC-IDS2018.

**Measured label inconsistency.** Flows whose feature vectors are byte-identical but whose
labels disagree cannot both be correct, so the minority label within each such collision
group is a reproducible lower bound on label noise that requires no external ground truth.
Over a 4,000,000-flow sample:

| key definition | duplicate keys carrying both labels | rows involved | minimum mislabelled | lower bound |
|---|---|---|---|---|
| all 33 features | 101 | 643 | 168 | **0.0042%** |
| features + src + dst | 0 | 0 | 0 | **0.0000%** |

**LSPR23's labels are cleaner than CIC's by roughly three orders of magnitude** at this
measure, which supports the prior assumption that exercise instrumentation beats post-hoc
labelling. The bound is a lower bound: it catches only mislabels that collide exactly with a
correctly-labelled twin, and it cannot see a systematically mislabelled attack class.

**FDP as an interval.** With `R` alerts of which `V` are labelled false, and
`ε₀ = P(truly malicious | labelled benign)`, `ε₁ = P(truly benign | labelled malicious)`,

    FDP_true = FDP_obs·(1 − ε₀) + (1 − FDP_obs)·ε₁.

| method | alerts | labelled false | observed FDP | interval over ε ∈ [0, 0.0753]² |
|---|---|---|---|---|
| e-LOND, horizon-uniform γ | 151 | 4 | 0.0265 | **[0.0245, 0.0998]** |
| ADDIS, γ ∝ j^−1.6 | 152 | 5 | 0.0329 | **[0.0304, 0.1057]** |

`ε₁` dominates: with few labelled-false alerts, converting a small fraction of the many
labelled-true alerts into false ones moves FDP far more than the reverse. **At LSPR23's
measured inconsistency the correction is immaterial and the reported FDP stands. At
CIC-level noise the q = 0.05 target could not be certified at all** — which is a reason to
state the dataset's label provenance in any FDP claim, not a reason to distrust this one.

A 152-alert audit sample is emitted to `out/h8_audit_sample.csv` (seed 20260826) with the
fields an analyst needs. The manual pass is `[OPEN]`: it requires the exercise ground truth,
and no automated procedure substitutes for it.

---

## 4.28 Boosting and compound e-values (`t29_compound_e.py`) `[EXACT]` / `[REAL]`

The external review asked for "the strongest recent compound-e / e-closure method that is
realistically implementable" as a comparator. The strongest general power-recovery technique
for e-value procedures is **boosting** (Wang & Ramdas 2022 §4; the lag-dependent truncation
of arXiv 2407.20683 is a form of it): an e-value below the rejection threshold can never
cause a rejection, so its mass is wasted and can be redistributed upward. Take the largest
`b` with `E[T_b(E)] ≤ 1` where `T_b(x) = b·x·1{b·x ≥ τ}`.

**Boosting is exactly vacuous for threshold conformal e-values.** With `E ∈ {0, M}` and
`P(E = M) = 1/M`,

    T_b(0) = 0,  T_b(M) = bM,  E[T_b(E)] = bM·(1/M) = b,

so `E[T_b(E)] ≤ 1` forces `b ≤ 1`, and `b* = 1` exactly. Verified numerically at
`M ∈ {10³, 10⁵, 1,813,114}` × `τ/M ∈ {0.1, 0.5, 0.9}`: `b* = 1.000000` in every cell.

The contrast is a genuine continuous e-value, the Vovk calibrator `E = ½U^{−1/2}`, for which
the optimum is `b* = √(2τ)` in closed form:

| τ | 2 | 5 | 20 | 100 |
|---|---|---|---|---|
| numerical `b*` | 1.985 | 3.126 | 6.179 | 13.42 |
| closed form `√(2τ)` | 2.000 | 3.162 | 6.325 | 14.14 |

Boosting recovers power by lifting mass that sits **below** the threshold. A two-point
e-value has none: everything is already at the ceiling or at zero, and zero cannot be
lifted. **The evidence is already extremal, so the strongest available power-recovery
technique returns nothing — and it returns nothing for the same reason the feasibility
boundary exists.**

**On real scores the optimal boost is below 1.** Using the *measured* rather than nominal
benign firing rate, `b* = 1/(CEIL·P̂_fire)`:

| position | 0.55 | 0.62 | 0.70 | 0.77 | 0.85 |
|---|---|---|---|---|---|
| measured / nominal firing rate | 1.07 | 1.16 | 3.79 | 2.72 | **50.90** |
| `b*` | 0.934 | 0.864 | 0.264 | 0.368 | **0.020** |

median `b*` = 0.368 over the eight configurations with a positive firing rate. Where
`b* < 1` the nominal e-value is already anti-conservative, so the correct adjustment is a
shrinkage rather than a boost. Either way there is no free power available.

**e-closure / compound e-values** (Ignatiadis, Wang & Ramdas) address several e-values per
hypothesis. Here there is exactly one aggregated e-value per episode, and the aggregation
step *is* the compound operation — which §4.16's theorem already covers for every symmetric
merging function. There is therefore no separate e-closure comparator to run; the relevant
result is the padding theorem, not a power-recovery method. This closes the last open item
of the external review's Priority 1.
## 4.29 Grouping families (`t26_H4_grouping.py`) `[REAL]`

F3 rested on (SrcIP, DstIP, time-bucket) alone. This adds host-only grouping on both sides,
/24 subnet pairs and a service-based family, sweeps the bucket from 5 minutes to a day, and
finishes the two runs that timed out earlier. Positions 0.62 and 0.85 × two seeds, k = 1,
q = 0.05.

Note that **the 86,400 s bucket and the no-time-field ("host-pair only") run coincide
exactly** in every family, because the deployment window spans 7.4 h at position 0.62 and
2.8 h at 0.85 — less than one day, so a day-long bucket already contains the whole window.

| family | bucket | T | malicious ep. | required `\|C\|` | margin | feasible | e-LOND recall |
|---|---|---|---|---|---|---|---|
| src-dst | 300 s | 121,234 | 2,439 | 4,849,339 | −0.559 | 0/4 | 0.000 |
| src-dst | 1,800 s | 56,972 | 601 | 2,278,879 | −0.059 | 0/4 | 0.477 |
| src-dst | 3,600 s | 46,785 | 408 | 1,871,399 | +0.164 | 4/4 | 0.446 |
| src-dst | 7,200 s | 40,418 | 326 | 1,616,699 | +0.339 | 4/4 | 0.423 |
| src-dst | 86,400 s / none | 30,771 | 184 | 1,230,839 | +0.733 | 4/4 | 0.345 |
| **src** | 300 s | 16,494 | 1,597 | 659,759 | **+2.232** | 4/4 | **0.518** |
| **src** | 86,400 s / none | 944 | 112 | 37,779 | **+55.891** | 4/4 | 0.327 |
| dst | 300 s | 39,762 | 1,159 | 1,590,479 | +0.342 | 4/4 | 0.428 |
| dst | 86,400 s / none | 10,857 | 98 | 434,279 | +3.888 | 4/4 | 0.226 |
| subnet24 | 300 s | 80,156 | 1,423 | 3,206,259 | −0.334 | 0/4 | 0.401 |
| subnet24 | 1,800 s | 39,888 | 368 | 1,595,519 | +0.343 | 4/4 | 0.343 |
| src-dport | 300 s | 63,730 | 3,070 | 2,549,199 | −0.161 | 0/4 | 0.517 |
| src-dport | 1,800 s | 19,248 | 1,318 | 769,919 | +1.848 | 4/4 | 0.394 |

**Feasibility is a statement about the horizon, not about the grouping — and this is now
measured across five families rather than asserted from one.** `required |C|` is exactly
`kT/w₀ − 1`, so it falls in lockstep with `T`. Every family becomes feasible once the bucket
is coarse enough; the bucket at which it does so differs only because the families produce
different `T`. Host-only grouping on the source side is feasible at **every** bucket
(margins +2.2 to +55.9) because it collapses the stream to 944–16,494 episodes.

**This narrows F3 rather than confirming it.** F3 currently says the tested host-pair family
does not robustly restore feasibility, which remains true. But a coarser deployable unit
does: (SrcIP, bucket) is feasible everywhere tested, needs 37,779–659,759 calibration flows
against the 1.8–2.4 million available, and its episode recall (0.327–0.518) is **higher**
than the host-pair family's at every comparable bucket. An attacker-host-level alert is a
perfectly ordinary SOC unit. So the honest statement is that the feasibility barrier can be
bought off by coarsening the alerting unit, and what it costs is the flow-versus-episode gap
below.

**F4 across every family** — the same alert set, scored per episode and per malicious flow:

| family | bucket | episode recall | malicious-flow coverage | gap |
|---|---|---|---|---|
| src-dst | 1,800 s | 0.477 | 0.509 | +0.032 |
| src-dst | 7,200 s | 0.423 | 0.509 | +0.086 |
| src-dst | 86,400 s / none | 0.345 | 0.509 | +0.164 |
| src | 300 s | 0.518 | 0.519 | +0.001 |
| src | 86,400 s / none | 0.327 | 0.513 | +0.185 |
| dst | 21,600 s | 0.273 | 0.509 | +0.237 |
| dst | 86,400 s / none | 0.226 | 0.509 | **+0.283** |
| subnet24 | 86,400 s / none | 0.229 | 0.508 | +0.280 |
| src-dport | 300 s | 0.517 | 0.508 | **−0.009** |
| src-dport | 86,400 s / none | 0.265 | 0.509 | +0.244 |

**Malicious-flow coverage is essentially constant at 0.508–0.519 across every family and
bucket, while episode recall falls from 0.518 to 0.226.** The gap is therefore not a property
of the detector or of the alert budget — it is created entirely by the choice of unit, and it
widens monotonically as the unit coarsens. Coarse grouping buys feasibility (above) and pays
for it here: the same alerts cover half the malicious traffic either way, but the fraction of
distinct episodes caught halves. The one exception is service-based grouping at 5 minutes,
where episode recall slightly **exceeds** flow coverage (−0.009), because grouping by
destination port isolates the attacked services into episodes that are individually caught.

---
## 4.30 Problem-space padding pools (`t28_P5_padding.py`) `[REAL]`

The external review's Priority 5 asked whether the dilution attack survives realistic
constraints on the traffic an attacker can emit. §4.17 costed two pools, generic benign and
attacker-origin. This adds protocol-matched, service-matched and a black-box pool, and
restates the cost in a way that does not assume the attacker gets the average outcome.

§4.17 solves `(S + rμ)/(n + r) < τ` for `r > (S − τn)/(τ − μ)` using the pool's **mean**
e-value μ, which is the cost at which suppression works *in expectation*. A padding flow
actually contributes 0 or `CEIL`, so the realised evidence is random. `r_90` below is the
smallest `r` for which suppression succeeds with probability ≥ 0.90, from
`P(Binomial(r, p_fire) < (τ(n+r) − S)/CEIL)`. That probability is **not monotone in r** — the
integer cutoff can stay fixed while the trial count grows — so it is found by exhaustive scan
rather than by bisection.

Positions 0.62 and 0.85 × two seeds, two-hour grouping, 352 detected episodes costed. The
service-matched pool is undefined for episodes whose modal destination port carries no benign
traffic, so the like-for-like comparison is restricted to the **257 episodes where every pool
is defined**:

| padding pool | mean e | P(fire) | `r_mean` p10/med/p90 | `r_90` p10/med/p90 |
|---|---|---|---|---|
| generic benign | 24.3 | 1.34×10⁻⁵ | 4 / 34 / 227 | 4 / 34 / 227 |
| attacker-origin | 120.5 | 6.64×10⁻⁵ | 4 / 35 / 227 | 4 / 34 / 227 |
| protocol-matched | 70.4 | 3.88×10⁻⁵ | 4 / 35 / 227 | 4 / 34 / 227 |
| service-matched | **0.0** | **0** | 4 / 35 / 227 | 4 / 34 / 227 |
| black-box (most common benign service) | **0.0** | **0** | 4 / 34 / 227 | 4 / 34 / 227 |

**Every pool costs the same.** The suppression cost depends on μ only through `τ − μ`, and
τ = 1,262,720 while the largest μ is 120.5 — four orders of magnitude smaller. Matching the
victim's protocol or service, using the attacker's own hosts, or picking the single most
common benign service all give the same 34-flow median. **The realism of the padding traffic
is irrelevant to the attack.**

**`r_90` equals `r_mean` to within one flow.** The pools fire so rarely (P ≤ 6.6×10⁻⁵) that
with ~34 pads the chance any of them fires is under 0.3%. The expected-value cost is
therefore already the high-probability cost, and §4.17's numbers were not optimistic — a
conclusion that had to be measured rather than assumed, since it does not follow from the
expectation alone.

Two pools — service-matched and black-box — have **mean e exactly 0 and never fire at all**.
An attacker who pads with the most common benign service emits traffic that the detector
never scores above the conformal ceiling, so the suppression is deterministic rather than
probabilistic, at no extra cost in volume.

**Oracle caveat.** μ and `P(fire)` are computed from the deployment window's realised
e-values, so the attacker is credited with exact knowledge of the detector's output on that
window. The costs are therefore a **lower bound** on what a real attacker needs. The same
caveat applies to §4.17. Since the conclusion is that the cost is insensitive to the pool,
and the black-box pool requires no detector knowledge to *choose*, the caveat does not
threaten the result: an attacker who simply sends the most common benign service gets μ = 0
without measuring anything.

### Can the attacker put the pad flows where they have to go? (`t46_hostpair_padding.py`)

The episode key is `(SrcIP, DstIP, bucket)`, so a pad flow must land on **the target's own
host pair** — the attacker sending ordinary traffic *to the victim*. None of the five pools
above is matched that way: generic is window-wide, attacker-origin is matched on **source**
only, protocol- and service-matched on the episode's modal protocol and destination port,
black-box on the window's most common service. The cost model therefore rests on an
assumption that has to be stated and checked: **that attacker-generated ordinary traffic to
the victim scores like ordinary traffic generally.**

**The empirical route is closed, and that is itself a measurement.** If attack host pairs
carried ordinary benign traffic, a host-pair-matched pool could be built from it and priced
like the other five. They do not. Over five window positions × two detector seeds — nine
cells with detections, **674 detected episodes** — *every* episode's host pair is **100%
malicious**, and not one episode has even a single benign flow on its own pair, against the
34 the median attack needs:

| | detected episodes | host pairs 100% malicious | episodes with ≥ 35 benign flows on their pair |
|---|---|---|---|
| all five windows × two seeds | 674 | **674 of 674** | **0 of 674** |

LSPR23 contains no example of ordinary traffic on an attack pair, so **no measurement on this
dataset can settle the question.**

**The structural route settles it anyway.** The detector's input is `Protocol` plus 32
per-flow timing and volume statistics — durations, byte and packet counts, packet-length and
inter-arrival distributions, flags. It contains **no IP address, no port, and no endpoint
identity of any kind**; `src`, `dst` and the ports enter the pipeline only through
`build_episodes`' grouping key, never through `fit_detector`. A flow's score is therefore
**invariant to which host pair it sits on**, so an ordinary HTTPS or DNS flow scores
identically whether it is sent to the victim or anywhere else, and the black-box pool's
e-value distribution — `P(fire)` **exactly 0** at all five windows (§4.42) — transfers to the
attack pair *by construction* rather than by assumption. The attacker needs only to make
ordinary connections to the host they are already attacking.

**Scope, and its limit.** This is a property of **flow-level feature sets**, not a general
fact about the attack. A detector that used host reputation, per-host baselines, or any
feature conditioned on endpoint identity would break the argument — its scores could depend
on the host pair, and the transfer would have to be demonstrated on a testbed rather than
argued from the feature list. That is the honest boundary on the claim, and it is the one
place where the problem-space experiment declined in `02_WORKPLAN_PHASE4.md` §7 would still
have something to add.

## 4.31 The position-0.85 extreme tail, identified (`t30_A1_tailforensics.py`) `[REAL]`

F9 records a benign firing rate 50.9× nominal at seed 0 and 24.3× at seed 1, at the window
position every procedure comparison uses. There `E[e | benign] ≈ 51`, so the constructed
evidence is not a valid e-value and nothing computed at that position carries an FDR
guarantee. The firing event is exactly `s(x) > max_{z∈C} s(z)` at k = 1, so the flows
responsible are identifiable, and there are few enough of them to enumerate.

### The flows

**46 benign-labelled flows of 1,638,722 fire at seed 0; 22 at seed 1.** Both listings are
written in full to `out/a1_extreme_tail_seed{0,1}.csv`. At seed 0 they are four source
hosts and five host pairs:

| src → dst | flows | service / dport | direction | pattern |
|---|---|---|---|---|
| 10.5.1.3 → 100.101.1.32 | 34 | TLS / 443 | internal → **external** | 15:12–15:41 UTC, one flow every 20–60 s, source ports incrementing monotonically 54057 → 54423 |
| 100.96.5.5 → 10.5.1.2 | 7 | LDAP / 389, Global Catalog / 3268 | DMZ → internal | directory enumeration |
| 100.96.5.5 → 10.5.1.3 | 3 | Global Catalog / 3268 | DMZ → internal | directory enumeration |
| 10.5.1.2 → 100.101.1.24 | 1 | TLS / 443 | internal → **external** | — |
| one IPv6 pair | 1 | TLS / 443 | internal → external | — |

**100.96.5.5 and 10.5.1.2 both appear in the red team's own confirmed-compromise list**
(§4.32; the list is external to the flow labels). 10.5.1.3 is the LDAP / Global Catalog
target, i.e. a domain controller. The two patterns are periodic outbound TLS from an
internal host to a single external address, and directory enumeration from a compromised
DMZ host against internal domain controllers.

### Which of the three explanations fits

Figures are seed 0 / seed 1.

| candidate | test | result |
|---|---|---|
| **new benign traffic mode** | fraction of the tail whose src host / dst host / (service, dport) never appears in the benign calibration window | **0.00% / 0.00% / 0.00%** and **0.00% / 0.00% / 4.55%**, against 1.22% / 0.67% / 0.14% for ordinary benign window flows. Every tail host was present in calibration, and all but one seed-1 flow's service. **Not supported.** |
| **duplicated or near-duplicated records** | tail flows byte-identical to a malicious flow anywhere in the 16.35M stream; to a calibration benign flow; repeats within the tail | **0 of 46** and **0 of 22**; **0.00%** in both; every vector distinct, largest repeat 1. **Ruled out.** |
| **broad distribution shift** | ratio of measured to nominal `P(rank ≤ k)` as k grows | 50.90 (k=1) → 9.18 (10) → 4.49 (10²) → 6.80 (10³) → 2.05 (10⁴) → **1.44** (10⁵); seed 1, 24.34 → 1.51. A uniformly moved distribution would keep the ratio flat in k. **Not the primary explanation**, though a shift confined to the extreme tail is not distinguishable from the alternative below by this test alone. |
| **systematic label error** | concentration, endpoint identity, protocol semantics | see below. **The best-supported explanation, and not proved.** |

**The inflation is localised in three host pairs of 25,864.** Removing them, seed 0:

| pairs removed | tail flows covered | benign firing rate | ratio to nominal | `E[e \| benign]` |
|---|---|---|---|---|
| 0 | 0 / 46 | 2.807×10⁻⁵ | **50.90** | 50.90 |
| 1 | 34 / 46 (74%) | 7.325×10⁻⁶ | 13.28 | 13.28 |
| 2 | 41 / 46 (89%) | 3.054×10⁻⁶ | 5.54 | 5.54 |
| **3** | **44 / 46 (96%)** | **1.223×10⁻⁶** | **2.22** | **2.22** |
| 5 | 46 / 46 | 0 | 0.00 | 0.00 |

At seed 1 five pairs take 24.34× to 2.22×. **The other four window positions measure
1.07–3.79× at k = 1**, so removing three host pairs puts position 0.85 inside the range of
every other position — but note that 2.22× is still anti-conservative, so this localises the
excess rather than removing it. `[ORACLE]` — the pairs are chosen from the test-split score
tail, so this measures how localised the cause is; it is not a deployable correction.

**The external host-identity test does not, on its own, adjudicate these flows.** 11 of 46
tail flows at seed 0 (23.9%) and 4 of 22 at seed 1 (18.2%) touch a red-team
confirmed-compromise host, against an 18.5% base rate among benign window flows — an
enrichment of essentially 1×, because a compromised host also sends a great deal of ordinary
traffic. Excluding those flows moves the ratio only 50.90 → 47.51 and 24.34 → 24.44. **The
argument for label error rests on the protocol semantics and the concentration, not on host
identity alone.**

**Supporting evidence.** 78.3% of the tail flows have a source host that carries
labelled-attack traffic elsewhere in the stream, against a 29.7% benign baseline; 100.0%
have an endpoint that does, against 51.6% (unchanged when the attack-host sets are
restricted to flows *before* the deployment window). All 46 carry `Label_src = Label_dst = 0`,
so the instrumentation attributes none of them to a red-team machine — which is exactly what
would be expected if the labelling marks flows by *endpoint identity* and therefore cannot
mark actions taken by a **compromised blue-team host**. 39 of the 46 fall in the last two
deciles of the window, i.e. late in the exercise, when post-compromise activity is expected.

**Conclusion. The position-0.85 anti-conservatism is a localised extreme-tail anomaly whose
best-supported explanation is systematic label error, not broad drift and not a new benign
mode.** 44 of 46 firings come from three host pairs; the traffic is Global Catalog / LDAP
enumeration from a red-team-confirmed compromised host against internal domain controllers,
and periodic outbound TLS from internal hosts to single external addresses — patterns that
are post-compromise activity by description, carrying a benign label because the exercise
instrumentation attributes flows to the red team by *endpoint identity* and therefore cannot
mark actions taken by a compromised blue-team host. §4.32 reaches the same host pairs from a
different direction.

**What is not established.** A distribution shift confined to the extreme tail would produce
the same rank-depth profile and the same concentration, and nothing here separates the two
without the exercise's own logs. The claim the record makes is therefore the weaker and
defensible one: *the excess is localised, reproducible, identified down to named host pairs,
and consistent with mislabelled post-compromise traffic*. It is not a proof of mislabelling,
and the paper must not read as one.

### Two repairs, neither of which works

| repair | oracle? | fire rate | `E[e \| benign]` | feasibility margin | e-LOND alerts / FDP / recall |
|---|---|---|---|---|---|
| baseline | — | 2.807×10⁻⁵ | 50.90 | +0.436 | 151 / 0.026 / 0.576 |
| Mondrian (stratified) conformal by `Service` | no | 9.337×10⁻⁵ | 21.66 | **−1.000 … −0.842** | 144 / 0.035 / 0.545 |
| Mondrian by `Conn_state` | no | 9.825×10⁻⁵ | 20.11 | **−1.000 … −0.753** | 87 / 0.057 / 0.322 |
| drop dport 443 from calibration and deployment | `[ORACLE]` | 6.911×10⁻⁶ | 11.07 | +1.587 | 83 / 0.012 / 0.516 |

**Mondrian conformal makes it worse.** Stratifying shrinks each stratum's calibration set,
so each stratum's ceiling falls — from 1,813,114 to a range of 4 … 769,720 by `Service` —
and the per-episode feasibility margin goes from +0.436 to between −1.000 and −0.842. The
conditional-validity gain is real but is paid for exactly where §4.26 says it would be: in
the evidence ceiling. Excluding the dominant service stratum halves the inflation and does
not remove it, because the residual tail is the LDAP / Global Catalog traffic.

**Neither restores `E[e] ≤ 1`, and neither should be expected to: the cause is not the
calibration, it is that a specific set of attack flows carries a benign label.** The two
usable responses are to correct those labels, or to present position 0.85 as what it is — a
case study in evidence validity collapsing under label error rather than under drift.
The record takes the second: **every FDP reported at position 0.85 remains a measurement
against labels, and the direction of the error is now known** (§4.32 shows it inflates the
reported FDP rather than deflating it).

**Effect on the other conclusions: none, and in the conservative direction.** Anti-conservative
evidence can only make procedures fire *more*, so every infeasibility and silence result at
position 0.85 is conservative.

---


### E5 — the two gaps the forensics flagged itself (`t37_E5_a1gaps.py`) `[REAL]`

`06_PHASE3_REPORT.md` §1.5 flagged three uncovered items. Two are closed here; the third,
proximity to attack periods, stays declined because the metric is degenerate on this window
(seconds-to-nearest-malicious-flow is 0.0 at p10, median and p90 for the tail *and* for
ordinary benign flows).

**The interpretation rule was fixed before the numbers were seen**: tail attack-like →
strengthens *"consistent with post-compromise label error"*; not attack-like → keep only the
localisation claim. **Neither outcome is proof.**

**Near-neighbour geometry.** For each tail flow, distance in standardised model-feature space
to the nearest labelled malicious flow (`d_M`), the nearest ordinary benign deployment flow
(`d_B`) and the nearest calibration benign flow (`d_C`). Standardisation uses the calibration
window's benign mean and standard deviation only; two features with zero calibration variance
are dropped rather than entered in raw units. Distances are formed by subtracting first: the
`‖a‖²+‖b‖²−2ab` identity cancels catastrophically in exactly this regime, returning **0.000000
for true distances of 0.0055** at the norms involved, and `d_B` is a denominator.

| seed | arm | n | `d_M` p50 | `d_B` p50 | `ρ = d_M/d_B` p50 |
|---|---|---|---|---|---|
| 0 | **tail** | 46 | **0.493** | 0.232 | **2.41** |
| 0 | benign, random | 400 | 1.536 | 0.000 | 7,842 |
| 0 | benign, host-matched | 400 | 1.513 | 0.018 | 52.2 |
| 0 | **benign, host *and port* matched** | 400 | **1.853** | 0.053 | **24.7** |
| 1 | **tail** | 22 | **0.490** | 0.088 | **6.21** |
| 1 | benign, random | 400 | 1.537 | 0.000 | 7,420 |
| 1 | benign, host-matched | 400 | 0.688 | 0.001 | 948 |
| 1 | **benign, host *and port* matched** | 400 | **0.711** | 0.001 | **968** |

**Lead with `d_M`, not `ρ`.** Ordinary benign traffic is highly repetitive, so its nearest
benign neighbour is essentially on top of it and `ρ`'s denominator collapses; the ratio is
then dominated by that collapse rather than by anything about malice. The interpretable
number is the absolute distance to the nearest malicious flow.

The control that carries the claim is the **host *and port* matched** baseline: §4.31 shows
the tail is concentrated in three host pairs of 25,864 and 86% of it is destination port 443,
so a baseline matched on neither would confound "attack-like" with "belongs to those hosts,
on that port". Against that baseline the tail sits **3.8× closer** to malicious traffic at
seed 0 (0.493 against 1.853) and **1.5× closer** at seed 1 (0.490 against 0.711). The seed-1
separation is much weaker than seed 0's and is reported as such.

**Per-feature.** The tail's mean is closer to the malicious population than to the benign one
on **28 of 31** retained features at both seeds, compared on a common scale — dividing each
side by its own population's standard deviation would make "closer to malicious" easier
whenever the malicious population is the more dispersed one, and is reported separately. The
largest standardised gaps from the benign population are in the byte- and packet-count
features. Destination port 443 accounts for 86% of the seed-1 tail against 11.7% of benign
flows (7.4× enriched) and Global Catalog 3268 for 9.1% against 0.33% (27.8× enriched, and
absent from the malicious population). Percentile locations carry a standard error of about 7
points from `n_tail = 46`, so they are reported to whole percents and the top-8 listing is
descriptive rather than a multiple-testing result.

**What this does and does not settle.** The tail is attack-like on both the geometry and the
per-feature comparison, and it stays attack-like under the strictest available control. By the
rule fixed in advance this **strengthens** the reading that these are attack flows carrying a
benign label. It is not proof, and F9's wording does not move: a distribution shift confined
to the extreme tail would produce the same geometry, and separating the two needs the
exercise's own logs, which we do not have. **F9 and §4.31 are now frozen for the paper.**

## 4.32 Adjudicated audit of the alert sample (`t31_A2_alertaudit.py`) `[REAL]`

§4.27 emitted 152 alerts to `out/h8_audit_sample.csv` and left the audit `[OPEN]` for want
of exercise ground truth. Part of that ground truth is in the repository:
`data/lspr23_attacknarratives.json` is the Locked Shields Partner Run 2023 red team's own
task record — **288 narratives, 295 timestamped step submissions spanning 07:03–15:08 UTC on
9 March 2023, and 83 machine-readable compromise reports naming the host, its IP addresses
and the time it fell, covering 39 IPv4 addresses.** That is documentation produced by the
attackers, not by the flow-labelling pipeline, so it is independent of the `Label` column
every FDP in this project is measured against. 20 step submissions fall inside the
deployment window (13:17–15:41 UTC).

**Evidence is tiered by independence, and the rule is fixed before the numbers are seen.**

- **E1, external** — an endpoint is a red-team confirmed-compromise host; red-team step
  submissions within ±15 min of the episode's span.
- **E2, structural** — an endpoint, or the (service, dport) the episode targets, carries
  labelled-attack traffic in *other* episodes. **The episode's own contribution is subtracted
  exactly**, over the whole `(src, dst, bucket)` group across the entire stream rather than
  over its deployment-window fragment, so an episode cannot corroborate itself through the
  flows its own time bucket holds outside the window. **E2 is nevertheless computed from the
  `Label` column**: it is independent of *this episode's* label but not of the labelling
  process, so it cannot rule out a systematic bias in that process. It is reported as such.
- **E3** — the `Label` column, used only as the thing being audited.

The three tiers therefore support different strengths of claim, and §4.32 reports all three
rather than the most favourable one.

### The indicators are not equally informative, and the audit says so

| set | n | E1 host | E2 either | **E2 both** | concurrent | rule says malicious | strict rule |
|---|---|---|---|---|---|---|---|
| **alerted** | 152 | 32.2% | 99.3% | **94.7%** | 100.0% | 99.3% | 97.4% |
| not alerted, labelled malicious | 108 | 15.7% | 98.1% | 75.9% | 87.0% | 96.3% | 81.5% |
| not alerted, labelled benign | 300 | 16.3% | 52.0% | **1.0%** | 86.0% | **46.7%** | **15.7%** |

The external-only tier (E1 alone) fires on 32.2% of alerts against 16.3% of non-alerted
benign episodes — a factor of 2, which is real but far too weak to adjudicate an individual
alert.

**E2 on both endpoints separates 94.7% from 1.0% — a 95× enrichment. Temporal concurrency
separates 100.0% from 86.0% and is nearly useless, because the whole window sits inside the
exercise.** The pre-registered rule's weakest branch (one endpoint plus concurrency)
therefore carries little information, and the rule as a whole would call 46.7% of
non-alerted benign episodes malicious. A `[POST-HOC]` strict variant that keeps only the two
discriminative branches calls 15.7% of them malicious.

### Verdicts

| verdict | n | % | label = malicious | label = benign |
|---|---|---|---|---|
| clearly malicious | 49 | 32.2% | 46 | 3 |
| probably malicious | 102 | 67.1% | 100 | 2 |
| ambiguous | 0 | 0.0% | — | — |
| probably benign | 1 | 0.7% | 1 | 0 |
| clearly benign | 0 | 0.0% | — | — |

**Agreement 146 of 152 = 96.1%**, with no alert left ambiguous. Under the strict rule, 148
of 152 alerts are called malicious and 145 of those are also labelled malicious — **98.0%**,
against a 15.7% false-call rate on the benign controls.

### The six disagreements, in full

| rank | src → dst | flows | service | label | verdict |
|---|---|---|---|---|---|
| 14876 | 100.96.5.5 → 10.5.1.2 | 1,078 | LDAP / 389 | benign | **clearly malicious** |
| 15147 | 100.96.5.5 → 10.5.1.3 | 1,152 | krb5 / 88 | benign | **clearly malicious** |
| 28006 | 10.5.1.2 → 100.101.1.24 | 188 | TLS / 443 | benign | **clearly malicious** |
| 26766 | IPv6 pair | 13 | TLS / 443 | benign | probably malicious |
| 27820 | 10.5.1.3 → 100.101.1.32 | 563 | TLS / 443 | benign | probably malicious |
| 23253 | IPv6 pair | 357 | — | malicious | probably benign |

**All five alerts the label calls false carry independent evidence of being genuine attack
traffic**, and three of them involve a red-team confirmed-compromise host. They are the same
host pairs §4.31 identifies from the score tail, reached from a different direction: LDAP,
Kerberos and Global Catalog traffic from a compromised DMZ host to internal domain
controllers, and outbound TLS from internal hosts. The single disagreement in the other
direction (rank 23253) is an episode whose source sends attack traffic in no other episode,
so the rule refuses to corroborate it; it is not evidence that the label is wrong.

### FDP under the audit

| method | R | FDP by label | E1+E2 rule | strict E1+E2 rule | **external-only (E1)** |
|---|---|---|---|---|---|
| e-LOND, horizon-uniform γ | 151 | 0.0265 | [0.0066, 0.0066] | [0.0000, 0.0265] | [0.0132, 0.6821] |
| ADDIS, γ ∝ j^−1.6 | 152 | 0.0329 | [0.0066, 0.0066] | [0.0000, 0.0263] | [0.0132, 0.6776] |

**The three tiers owe the audited labels different amounts, and the record reports all three
rather than the most favourable one.** The E1+E2 rules are the informative ones and both put
FDP at or below the label-derived value — but E2 is computed from the `Label` column, so
neither can rule out a *systematic* bias in that column, which is exactly the failure mode
§4.31 suspects. The external-only tier owes the labels nothing but is far less specific
(E1 fires on 32.2% of alerts and 16.3% of non-alerted benign episodes), so its upper endpoint
is uninformative. What it does establish without circularity: **3 of the 5 alerts the label
calls false involve a red-team confirmed-compromise host**, which is the fact the reader can
check against the narrative file directly.

The defensible statement is therefore: *the label-derived FDP is not an under-estimate, and
the specific alerts it counts as false are individually documented above with their evidence*
— not that the corrected FDP is 0.0066. §4.27's label-noise interval was two-sided and
symmetric in `ε₀`, `ε₁`; this narrows the plausible direction rather than fixing a value.

The enriched per-alert table, with all evidence fields and a blank `human_verdict` column,
is `out/a2_audit_adjudicated.csv`. **What remains open is a human pass with the full
exercise scoring system**; what is closed is that the audit is now a review of a documented
adjudication rather than an open-ended investigation, and that the reported FDP is
conservative rather than optimistic.

---

## 4.33 The ADDIS spending-state manipulation attack (`t32_B1_addis_state.py`) `[EXACT]` / `[REAL]`

§4.20 found ADDIS to be the only procedure that escapes the §4.13 feasibility template
without oracle horizon knowledge, and identified the mechanism: its spending index is

    D_t = S^t − C_{0+}(t) = #{i < t : λ < P_i ≤ τ},

the count of hypotheses **selected but not candidates**. Under threshold conformal evidence
at k = 1 an episode p-value is either exactly 1 (discarded, never selected) or small enough
to be a candidate, so `D_t ≡ 0`, the level never decays, and silence is 0.0%. §7 item 1
asked whether that is a second attack surface. **It is, it is exact, and this section prices
it.** An adversary who manufactures episodes with `p ∈ (λ, τ]` advances D on demand; those
episodes are never rejected, so they cost the attacker no discoveries and only spend state.

### How far the index must be advanced

Before any rejection the level is `min(λ, (τ−λ)·w₀·γ₀[D])`; after R rejections all made at
`D = 0` the bracket weight becomes `w₀ + (α−w₀) + α(R−1) = αR`. Rejection needs the level at
or above the conformal floor `k/(|C|+1)`, giving a closed form verified against the
`h6_procs` implementation itself (`t33_selftest_A1A2B1.py` asserts that `run_addis` reports
its first infeasible step at exactly `R + B*(R) + 1`, at four calibration sizes × four R):

> `B*(R)` = the smallest integer `D` with `D + 1 > [ (τ−λ)·W·(|C|+1) / (k·ζ(1.6)) ]^{1/1.6}`,
> with `W = w₀` before the first rejection and `W = αR` after R of them.

| prior rejections R | 0 | 1 | 2 | 10 | 50 | 152 |
|---|---|---|---|---|---|---|
| `B*` numeric | **203** | 314 | 485 | 1,326 | 3,626 | 7,266 |
| `B*` closed form | **203** | 314 | 485 | 1,326 | 3,626 | 7,266 |

On the real stream the transition is exactly where the formula puts it: **B = 202 leaves all
152 rejections intact; B = 203 leaves none, and the state is absorbing — 99.4% silent, no
true detection ever.**

| B | flows spent | rejections | recall | P(target still detected) | silent |
|---|---|---|---|---|---|
| 0 | 0 | 152 | 0.576 | 1.000 | 0.0% |
| 200 | 90,655,800 | 152 | 0.576 | 1.000 | 0.0% |
| 202 | 91,562,358 | 152 | 0.576 | 1.000 | 0.0% |
| **203** | **92,015,637** | **0** | **0.000** | **0.000** | **99.4%** |
| 512 | 232,078,848 | 0 | 0.000 | 0.000 | 99.4% |

### What one precursor costs

An episode of `n` flows containing `m` ceiling-reaching flows has `Ev = CEIL·m/n`, so
`p ∈ (λ, τ]` ⟺ `n ∈ (λ·CEIL·m, τ·CEIL·m]`. The cheapest precursor takes `m = 1`:

    n ∈ (453,278, 906,557]   →   453,279 flows per precursor

so **B*·n = 203 × 453,279 = 92,015,637 flows, 5.6× the entire 16.35M-flow LSPR23 stream**,
to silence the controller permanently from a cold start. Total cost scales as
`λ|C| · [(τ−λ)w₀|C|]^{0.625} / k^{1.625}`:

| `\|C\|+1` | 10⁴ | 10⁵ | 10⁶ | 1,813,114 | 10⁷ |
|---|---|---|---|---|---|
| `B*` | 7 | 33 | 140 | 203 | 592 |
| flows per precursor | 2,501 | 25,001 | 250,001 | 453,279 | 2,500,001 |
| **total flows** | 17,507 | 825,033 | 35,000,140 | **92,015,637** | 1,480,000,592 |

The attack is therefore priced by the calibration size — **the same quantity that buys
feasibility also buys resistance to the state attack**, super-linearly. It falls fast in k,
but every `k > 1` is already infeasible (F14), so the attacker cannot reach the cheap regime.

`(λ, τ)` prices it too: at λ = 0.05 the cost falls to 26,652,864 flows, at λ = 0.4 to
83,403,290. The window is `τ/λ` wide, which is what makes a grey-box attack possible.

### Per-target attack, and attacker knowledge

Injecting immediately before one chosen target, over all 147 episodes ADDIS detects:
**minimum `B*` = 203, median 4,024, maximum 7,176** — 9.2×10⁷ to 3.3×10⁹ flows. The cost
rises with the target's position because ADDIS banks wealth as it rejects, so the
front-loaded attack (before the first rejection) is by far the cheapest and the only one a
realistic adversary would mount.

- **White-box** (λ, τ, k, `|C|`, state known): sets `n = 453,279`, `m = 1`; every precursor
  lands in the window. 92,015,637 flows.
- **Grey-box** (procedure and parameters known, `|C|` and state unknown): the admissible size
  is an interval `τ/λ = 2×` wide, so aiming at its midpoint succeeds whenever the estimate of
  `|C|` is within **[0.667, 1.333]** of the truth — a ±33% tolerance. Not knowing the state
  costs only over-provisioning: `B*(R=152)/B*(R=0) = 36×`. **The grey-box attack works.**
- **Black-box** (no detector access, ordinary traffic of a chosen volume): `m` is then random
  and the precursor works only if `CEIL·m/n` lands in `[1/τ, 1/λ)`. At the *nominal* firing
  rate the per-group success probability is 0.195–0.303, so a properly calibrated stream
  would cost ≈ 5× the white-box budget. On this stream it is **effectively impossible**: with
  the firing rate estimated on the first half of the window and the attack priced on the
  held-out second half, `CEIL·f = 94.2` against `1/λ = 4.0`, so an ordinary-looking group of
  the required size lands *past* the window rather than inside it. **The black-box attack is
  blocked by the very anti-conservatism §4.31 diagnoses** — a defence no operator would
  choose and none can rely on.

### The two attack surfaces coincide against ADDIS

ADDIS caps its level at λ, and the state-advancement window **starts** at λ. Wherever the cap
binds, the cheapest padding that suppresses an alert lands the episode in `(λ, τ]`:

- 101 of the 147 detected episodes have `α_t = λ` exactly;
- for all 101, the minimal suppressing pad puts the episode inside `(λ, τ]`.

**For 69% of ADDIS's detections, suppressing the alert also advances the spending index, so
the two attack surfaces are one operation and the state attack comes free with the padding
attack.** This does not hold for e-LOND, whose level is five orders of magnitude smaller.

**The equality 101 = 101 is forced, not a property of this window** (`t32a_E11_derivation.py`,
`[EXACT]`). Write `X = M·m` for an episode with `m` firing flows at ceiling `M`. The minimal
suppressing size is `N* = ⌊α_t·X⌋ + 1`, so the padded p-value is bracketed within a single
conformal floor above the level:

  `α_t < p⁺ = N*/X ≤ α_t + 1/X ≤ α_t + 1/M`.

When the cap binds, `α_t = λ` and the *lower* half of the landing condition `λ < p⁺ ≤ τ` is
automatic; the upper half holds whenever `X ≥ 1/(τ−λ) = 4`. Here `min X = M = 1,813,114`, a
margin of 4.5×10⁵. **Cap-saturation therefore implies landing as a theorem.** The converse is
not a theorem: an unsaturated episode can land, but only if `λ − α_t < 1/X`, a window one
conformal floor wide (5.5×10⁻⁷ out of λ = 0.25). Measured: **zero** unsaturated landers, and
the unsaturated levels top out at 0.2461 — four orders of magnitude clear of that window. So
`#lands ≥ #saturated` always, and the observed equality is the generic case rather than a
coincidence that a second dataset might break.

`t32_B1.json`'s `coincidence` block exports the per-episode arrays behind this (**Figure 4B**):
episode rank, `m_fire`, `nsz`, `α_t`, pre-pad `p`, `N*`, pad, `p⁺`, `saturated`,
`lands_in_window`, for all 147 rows, with ten identities asserted at write time and the three
stored aggregates recomputed from the arrays. The population is ADDIS's **true detections**
(147); it made 152 alerts, 5 of them false, and both counts are exported so the figure's
denominator cannot be misread. Median `p⁺ − λ = 1.90×10⁻⁹`, i.e. the cheapest suppression
lands the episode a *third* of the way to nowhere above the level — 290× finer than the
conformal floor, because the median-`p⁺` episode carries `m ≈ 290` firing flows.

Two numerical details the export forced out into the open, neither of which moves a recorded
number here but either of which could elsewhere. `N*` is computed in exact rational
arithmetic: `α_t·X` is a float product of magnitude ~10¹⁰ and can round *up* onto an integer,
which makes `⌊·⌋+1` one too large and destroys the minimality that the bracket rests on (a
worked case: `α_t = 0.24761283661298505`, `X = 35,646,736,295`). And saturation is tested
exactly, not with `np.isclose`, whose default tolerance at λ is 2.5×10⁻⁶ — five times wider
than the 5.5×10⁻⁷ floor that separates the two regimes.

### The two surfaces priced in the same units

Padding priced against the levels ADDIS *actually* offered — traced out of `run_addis`
itself, running 2.734×10⁻³ up to the λ cap:

| attack | flows |
|---|---|
| suppress one detected episode by padding (median) | 34,465,311 |
| suppress all 147 detected episodes | 127,485,670,015 |
| **silence the controller permanently by state manipulation** | **92,015,637** |

**Break-even is 2.7 episodes: from the third onward, state manipulation is the cheaper
attack. This window contains 255.** Against ADDIS specifically it is the dominant attack, and the reason
is the same property that makes ADDIS escape §4.13: a procedure that spends a large level per
hypothesis is hard to suppress by dilution — its rejection threshold is low — and cheap to
defeat through the state that keeps the level large.

**Verdict on §18's decision gate: the attack works.** It is exact, it survives the grey-box
setting, its cost has a closed form, and it identifies the mechanism precisely. What it is
not is cheap in absolute terms on this stream: 9.2×10⁷ flows is 5.6× the whole dataset, and
that number is set by `|C|`, not by any weakness of the implementation. **The honest claim is
structural, not operational: any procedure that escapes α-death by conditioning its spending
index on a property of the observed evidence exposes that property to the adversary, and the
price of the exposure is fixed by the calibration budget.**

---

---

# 5. Claim strength

| Claim | Evidence | Strength |
|---|---|---|
| Finite feasibility horizon for procedures whose spending index advances on every hypothesis (LOND, LORD++, e-LOND, e-GAI) | F1, F2, §4.13, §4.20 | **Strong** — proved for two structural families, verified numerically, and boundary located by counterexample. **Scope: finite-resolution (discrete) evidence.** §4.34 locates the boundary from outside it |
| Randomised smoothing removes the floor and the absorbing state | F18, §4.34 | **Strong** — `p_u` exactly Unif(0,1); silence 90.1% → 0.0% measured, and `P(reject) = min(1, α_t(\|C\|+1))` confirmed against 5,032,227 checked cells |
| ...but it does not move the reliably-detected set | F18, §4.34 | **Strong** — episodes detected with `P ≥ 0.9` are 18 under both rules at position 0.55; Jaccard 0.642, `Var(R_T)` 7.14 |
| ...and under an arbitrary-dependence-valid merge the yield is negative | F18, §4.34 | **Strong** — Hommel: 12.0 rejections against the discrete 18.0, and zero episodes at `P ≥ 0.9` |
| Continuous (calibrated) e-values recover the power | F18, §4.34 | **Refuted** — `min(1, (α_tλ)^{1/(1−λ)}M)` is a strict subset of the direct threshold for every λ; 0.0 rejections at λ ≥ 0.25 at the guarantee window, Vovk's λ = ½ included |
| The discrete construction's coarseness protects its own validity | F18, §4.34 | **Moderate** — the rank-1 rule queries `a = 1/M` (ratio 1.07×) while the mid-tail is 3–8× anti-conservative; measured on one dataset at two window positions |
| The asymmetry escape from the padding theorem is a usable mitigation | F20, §4.36 | **Refuted** — every padding-invariant precommitted weighting that keeps the mean's recall falls to 1–8 leading flows against 111 appended ones; `L*` is finite for every summable weight sequence |
| ...and the triangle robustness / power / ordering is closed | F20, §4.36 | **Strong (exact + measured)** — `P ≤ α_t·M` and `L*` finite, both proved; seven schemes measured at two window positions and two detector seeds |
| ADDIS's escape survives a change of evidence resolution | F18, §4.34 | **Refuted** — the escape is a property of the two-point p-value the *merge* creates; any rank-based merge advances the index on 85–96% of episodes, smoothed or not |
| RQ4's feedback conclusion is controller-specific | §4.39 | **Refuted** — proportional, PI and Robbins-Monro quantile targeting agree to three decimals from 4 h of delay onward, and all three sit within 0.007 of no-feedback FDP at 8 h |
| Analyst feedback holds its target under realistic delay | §4.39 | **Refuted** — FDP 0.053 at zero delay but **0.402 at fifteen minutes**, because 51.4% of alerts are issued before any disposition returns; 0.877 at a 24 h cycle against 0.887 with no feedback at all |
| The measured feedback advantage is feedback | §4.39 | **Not supported** — the controller sits at its actuator limit, the calibration maximum, for 95–100% of steps at zero delay; most of the advantage is the conservative threshold, not the steering |
| Periodic restart restores detection | F19, §4.35 | **Strong** — LOND 18.0 → 95.0 rejections, episode recall 0.065 → 0.345 at FDP 0.000, two detector seeds, and 908 derivation checks against the closed forms |
| ...and nearly replaces oracle horizon knowledge | F19, §4.35 | **Strong** — 95.0 / 0.345 under `γ ∝ j^−1.6` against 100.0 / 0.364 for horizon-uniform γ uninterrupted |
| ...at the cost of the deployment-level guarantee | F19, §4.35 | **Strong (exact)** — per-epoch FDR does not pool; `pooled FDR = 1 − (1 − q)^n` is attainable, 0.185 at the headline arm's four epochs |
| ...half of which is free: resetting the spending index costs no budget | F19, §4.35 | **Moderate** — 46% of the gain survives a precommitted allocation summing to `q`, measured at one window and one grouping |
| Restart is an alternative to coarsening that preserves episode resolution | F19, §4.35 | **Moderate–strong** — 1 h grouping + hourly restart reaches episode recall 0.406 against 0.103 for 6 h coarsening; both on the achievable frontier at their own budgets, which are not matched |
| A 24 h ("daily") restart is enough | F19, §4.35 | **Not supported** — 48.0 rejections against 87.0 at 6 h; and on LSPR23 the longest measurable deployment window is 26.98 h, so 48 h is unmeasurable |
| ADDIS escapes the horizon, but only where its own validity condition fails | F1, §4.20 | **Strong** — 10 configurations; assumption violation measured directly |
| online e-BH escapes the *absorbing state* by deferring the decision | F1, §4.20, §4.21 | **Strong** — 10 configurations; boundary verified against the fixed point |
| ...but not the calibration budget, and on this stream not the detections either | §4.21 | **Strong** — `\|C\| ≥ T/(αR) − 1`, still linear in T; 72 rejections vs e-LOND's 72 |
| The published α-death fix (mem-e-LORD) does not act before the first rejection | F2, §4.20 | **Strong** — identical level by construction; measured strictly worse than e-LORD |
| Deployable grouping does not restore feasibility | F3, §4.9 | **Strong** — real data; no oracle grouping exists |
| Flow- and episode-level evaluation disagree by 60 points | F4, §4.9 | **Strong** — real data |
| The alerting layer is an attack surface | F6, §4.6, §4.10 | **Strong** — 1–44 flows on real traffic; no prior work located |
| No cap policy is both powerful and unattackable | F8, §4.12 | **Strong** — four policies, all measured on real data |
| No symmetric e-merging rule resists padding | F7, §4.16 | **Strong** — theorem with two independent proofs; bound matches measurement |
| Drift invalidates calibration in general | F9 | **Not supported** at the median (1.94×). Belongs in a robustness subsection |
| ...but the evidence is not a valid e-value at window position 0.85 | F9, §4.28 | **Strong** — measured 50.9× / 24.3× anti-conservative; every FDP there is a measurement, not a guarantee |
| ...and the excess is localised in three named host pairs | F9, §4.31 | **Strong** — 3 pairs of 25,864 carry 44 of 46 firings; removing them gives 2.22×, inside the other positions' 1.07–3.79× |
| ...and the cause is label error rather than drift | F9, §4.31 (incl. E5) | **Moderate** — new-mode and duplicate-record explanations ruled out; the protocol semantics fit post-compromise activity; and the tail sits 3.8× (seed 0) / 1.5× (seed 1) closer to malicious traffic than benign flows matched on the same host pair AND destination port, with its mean closer to the malicious population on 28 of 31 features. Still **not proved**: a shift confined to the extreme tail would look the same without the exercise logs |
| Stratified (Mondrian) conformal repairs it | §4.31 | **Refuted** — the per-stratum ceiling collapses to 4–769,720 and the feasibility margin goes +0.436 → −1.000…−0.842, while `E[e\|benign]` stays at 20–22 |
| The reported FDP is not an under-estimate | F16, §4.32 | **Moderate–strong** — 96.1% agreement under a rule whose structural indicator is itself label-derived; the label-independent part establishes only that 3 of the 5 label-false alerts sit on a confirmed-compromise host |
| The ADDIS escape is itself an attack surface | F17, §4.33 | **Strong** — closed form verified against the implementation; B = 202 keeps 152 rejections, B = 203 keeps none, permanently; survives grey-box |
| ...and it is cheap in absolute terms | F17, §4.33 | **Not supported** — 9.2×10⁷ flows, 5.6× the whole dataset. The cost is `λ\|C\|·[(τ−λ)w₀\|C\|]^0.625/k^1.625`, set by the calibration budget |
| ...but it is the cheapest attack *against ADDIS*, and free alongside padding | F17, §4.33 | **Strong** — break-even at 2.7 episodes against a window of 255; for 101 of 147 detections the minimal suppressing pad also advances the index |
| Conclusions are not an artefact of one classifier | §4.22 | **Strong** — a second, unsupervised detector gives tail reach 0.000 and zero true detections at all 10 configurations, at an identical feasibility margin |
| k = 1 is the only feasible rank and the least reliable one | F14, §4.23 | **Strong** — 4 ranks × 10 configurations; ceiling falls exactly as 1/k |
| Relaxing the error target buys feasibility only linearly | §4.24 | **Strong** — measured ratio matches `kT/w₀` prediction to 3 decimals at every q |
| The spending sequence moves the operating point more than the error target does | F13, §4.24 | **Strong** — 0.188 against 0.088 in median recall |
| The known fix for conditional validity exists, works, and costs the margin | F10, F11, §4.26 | **Strong** — δ held in every cell; median configuration goes feasible → infeasible |
| ADDIS does not control FDR once k > 1 | §4.26 | **Strong** — FDP 0.033 → 0.246 → 0.707 at k = 1 / 100 / 1000 |
| LSPR23 labels are far cleaner than CIC's | §4.27 | **Moderate** — 0.0042% lower bound; cannot detect a systematically mislabelled class |
| No power is recoverable by boosting | F15, §4.28 | **Strong** — `b* = 1` exactly for two-point e-values; below 1 on real scores |
| Coarser deployable grouping does restore feasibility | F3, §4.29 | **Strong** — (SrcIP, bucket) feasible at every bucket, margins +2.2 to +55.9, with higher episode recall |
| The flow-vs-episode gap is created by the choice of unit | F4, §4.29 | **Strong** — flow coverage constant at 0.508–0.519 while episode recall falls 0.518 → 0.226 across 5 families × 7 buckets |
| The dilution attack is insensitive to how realistic the padding is | F6, §4.30 | **Strong** — 5 pools, identical median cost; two pools never fire at all |
| Online error control removes the operator's choice of operating point | F13, §4.14, §4.19, §4.20 | **Strong** — all methods measured against one frontier, gaps +0.000 in §4.20 |
| The point it picks is dominated | F13, §4.19 | **Holds for γ ∝ j^−1.6 only.** Under horizon-uniform γ the point is on the frontier; state the spending sequence with the claim |
| The approach tolerates a measurable rate of calibration contamination | F21, §4.37 | **Refuted as a rate.** The tolerable quantity is a COUNT: zero adversarial mislabels at `k = 1`, and `ε* = 1.1–1.3 flows` for random ones. Expressed as a rate that is 4×10⁻⁷, three orders of magnitude below the smallest grid point |
| One mislabelled attack flow in calibration destroys detection | F21, §4.37 | **Strong (exact + measured)** — the rule at `k = 1` is one order statistic; recall 0.065 → 0.000 and 0.282 → 0.000 at the two windows, with `j ≥ k` handing the threshold to the attacker by construction |
| Contamination costs power, not validity | F21(b), §4.37 | **Partly refuted.** The ceiling channel is anti-conservative: `p` falls by exactly `(1+ε)` for flows injected below the threshold, `E[e] ≤ 1+ε`. But it is **bounded** — `q = 0.05` → 0.0542 at the entire available stealth budget — while power is not bounded at all. Multiplicative on top of §4.31's conservatism; not claimed for online e-BH |
| The feasibility margin indicates whether the method is working | F21(b), §4.37 | **Refuted** — constant to six decimals (0.999984 / 0.999978) across the whole contamination sweep while recall goes to zero, because contamination *increases* `\|C\|` |
| Headline parameters were chosen on the test window | F22, §4.38 | **Refuted** — the frozen grouping is the worst *feasible* configuration of 35 at position 0.70 and within 10⁻⁴ of the worst at two more; the frozen cap is the worst of six at two of five windows |
| The grouping choice transfers across windows | F22, §4.38 | **Refuted** — previous-window selection has worst regret 0.579 (normalised 0.991); the oracle itself varies 0.676 across windows, more than any within-window spread. Coverage numbers are what the deployable grouping achieves, not the best achievable |
| The cap choice transfers across windows | F22, §4.38 | **Strong** — worst previous-window regret 0.012 (normalised 0.070), leave-one-out 0.010, over 5 windows × 2 seeds. The power-optimal cap `n₀ = 2` is defeated by one front-load flow and leaves 39% of groups outside the raw rule's validity condition |
| Selecting a grouping on episode recall is a valid alternative to flow coverage | F22, §4.38 | **Refuted** — the family sets recall's denominator, so the two objectives pick different configurations at 5 of 5 windows; the degenerate single-episode grouping scores recall 1 |
| The ADDIS state attack is out of reach on bandwidth | F23, §4.40 | **Refuted** — 36.1 GB over position 0.85's own 2.4 h deployment span is 33.4 Mbit/s, four hosts at 10 Mbit/s each. It is out of reach on **volume**: 37.5× the deployment window's entire flow count |
| Suppressing an alert is operationally cheap | F23, §4.40 | **Strong** — 34 flows = 13.3 kB = 15 bit/s over the 2 h bucket, from the black-box pool that needs no detector knowledge; 1.4×10⁻⁵ of the window's traffic |
| The deterministic tie-break is load-bearing | F24, §4.41 | **Refuted** — 50 randomised within-timestamp orders change none of 36 statistics at either window, with the randomisation verified to move ~50% of the movable positions per draw. One appendix sentence |
| The padding attack is an artefact of the anomalous window | F24, §4.42 | **Refuted** — measurable at all four other windows, per-window medians 3 / 4.5 / 62 / 35 against 35.25 at 0.85, and the black-box pool never fires at any of the five. Strictly cheaper at three of the four, dearer at one — not uniformly |
| Dependence breaks online FDR | §4.2 | Prior work, and dissolved by e-values. Not a contribution |

---

# 6. Prior work to cite and differentiate

- **Axelsson (CCS'99 / TISSEC'00)** — base-rate fallacy; `P(intrusion|alarm) = 1−FDP` is the
  operational quantity. Motivation, not a contribution.
- **"alpha-death"** — Ramdas, Yang, Wainwright & Jordan (NeurIPS 2017), "Online control of the FDR
  with decaying memory": *"a permanent end to decision-making when the decision threshold is too
  small"*. The literature's position is that it afflicts alpha-*spending* and is cured by
  alpha-*investing*. Our position: investing does not cure it either, because earning wealth
  requires a rejection and none is attainable below the evidence floor.
- **PRIOR-ART COLLISION FOR C1 — Huo, Lu, Ren & Zou (NeurIPS 2024)**, *Real-Time Selection Under
  General Constraints via Predictive Inference*. **Appendix B.2, p.15, verbatim:** *"However, the
  conformal p-values are lower bounded by 1/(|D_cal| + 1), which leads to unsatisfactory performance
  for online multiple testing methods based on p-values. Since these methods require sufficiently
  small p-values to make rejections."* **§4.1:** *"methods relying on conformal p-values, such as
  LOND, SAFFRON, and ADDIS, encounter the alpha-death (stop early) issue … especially in small
  calibration sets."* **App. D.3** sweeps n_cal 500→2500 and reports selections rising toward target.
  Their remedy is II-COS, an lFDR-based selection rule (after Gang et al.'s SAST) — a *different
  procedure*, not an analysis of the composition. **So the PHENOMENON is prior art and must be cited
  proactively.** The delta C1 may claim: (i) the *characterisation* of when the power loss becomes a
  structural impossibility — a finite, **absorbing** feasible set in a rejection-free run, for two
  structural families; (ii) coverage of the **e-value** procedures (e-LOND, e-LORD), where Huo et al.
  say "based on p-values"; (iii) the **exact** calibration–horizon exchange rate |C| ≥ kT/c₀ − 1;
  (iv) a **classification of the escapes** by mechanism (ADDIS's selection-conditional index; online
  e-BH's history-wide fixed point) with each priced; (v) the premises priced when removed (smoothing,
  restart); (vi) quantification at **security-scale** horizons. Do NOT claim the incompatibility
  itself was unknown.
- **CLOSEST IN FORM — Krönert, Célisse & Hattab (arXiv 2312.01969)**, *FDR Control for Online Anomaly
  Detection*. Cor. 1: with calibration cardinality `n = νm/α − 1` the empirical p-value grid
  `{j/(n+1)}` contains BH's critical values `{αk/m}` exactly, so a **windowed BH** over `m`
  hypotheses attains `FDR = m₀α/m` **exactly**. Algebraically our `|C| ≥ kT/c₀ − 1`, but a different
  question: theirs is *exactness of the realised level* (and they tune `n` **upward** for FNR;
  Fig. 2 shows detection at non-aligned `n`), ours is the threshold below which **no rejection is
  possible at all**, over an uninterrupted horizon `T` rather than a sliding window of length `m` —
  and their windowing is precisely our restart escape. Cite and distinguish; do not let a reviewer
  find this unaddressed.
- **FEEDBACK-ONLINE-FDR — Lu, Huo, Ren, Wang & Zou (arXiv 2509.03297, v3 2026-07-18)**,
  *Feedback-Enhanced Online Multiple Testing with Applications to Conformal Selection*. GAIF
  (generalized alpha-investing with feedback) + **OCTF** (online conformal testing with feedback),
  finite-sample FDR/mFDR under instant, delayed, full and bandit feedback. This is the dedicated
  literature our P/PI/AQT threshold controllers are **not** a substitute for; the paper's feedback
  claim must be narrowed to *these controllers under wall-clock delay*. Adjacent: Liu, Xi, Vong & Wei
  (arXiv 2508.13838) online conformal selection with irreversible decisions; Gollapudi et al.
  (arXiv 2605.14953) online conformal selection under bandit feedback.
- **Zhang, Pournaderi, Xiang & Varshney (arXiv 2501.13242)** — distributed multiple testing with FDR
  control under **Byzantine** nodes that corrupt *reported p-values*. Useful contrast for C2: every
  adversarial-testing neighbour reaches the pipeline through the **evidence**; ours perturbs no score
  and corrupts no report.
- **"resolution collapse"** — Hennhöfer & Preisach, arXiv 2603.23205. The discrete conformal
  floor produces zero discoveries; randomised smoothing removes it at the cost of variance.
  Batch, low-data, weighted conformal; no online procedures or wealth dynamics.
- **Zrnic, Jiang, Ramdas & Jordan (AISTATS 2020)**, *The Power of Batching* — Batch-BH,
  Batch-St-BH, BatchPRDS. Frames batching as **power** recovery; does not address rejection
  feasibility or discrete evidence.
- **Online multi-layer FDR control** (arXiv 2506.03406, *Mathematics* 2025) — online
  group-level FDR with group membership not predefined, adapting alpha-investing, LOND and
  LORD. The procedure a grouped formulation needs already exists.
- **Vovk & Wang (Ann. Statist. 2021) Thm 3.2** — admissible **symmetric** e-merging functions
  are convex combinations of the arithmetic mean and 1. **Wang (Biometrika 2025,
  arXiv 2409.19888) Thm 1** — the **asymmetric** generalisation `M_λ(e) = Σλᵢeᵢ + λ_{K+1}`.
  Cite each for its own result. Both fix the arity K.
- **Bates, Candès, Lei, Romano & Sesia (Ann. Statist. 2023)** — conformal p-values are PRDS,
  sufficient for BH but not the independence LORD/SAFFRON/ADDIS assume; and
  calibration-conditional p-values with a δ-guarantee (code: `msesia/conditional-conformal-pvalues`).
- **Rebjock et al. (AISTATS 2022)** — online FDR for anomaly detection under rare
  alternatives and serial dependence.
- **CALIBURN (2026)** — streaming NIDS, conformal risk control, operator alert budgets;
  explicitly applies no multiple-testing correction. Closest neighbour.
- **Transcend (USENIX'17) / Transcendent (USENIX'22) / FIRCE / FADES** — conformal
  calibration in security ML with rolling recalibration.
- **TESSERACT (USENIX'19)** — temporal evaluation constraints.
- **Adversarial hypothesis-testing games** — IEEE 2018; Yasodharan & Loiseau, NeurIPS 2019.
  Simple testing where the adversary selects a distribution; not online multiple testing with
  wealth dynamics. Full pass completed — see §4.18.
- **Chen et al. (2025)** — adversarial robustness of batch BH via test-score perturbation.
  **arXiv 2510.00463** — offline conformal novelty detection under test-time evasion.
- **Engelen et al. (WTMC'21) / Liu et al. (CNS'22)** — 6.67% and 7.53% label corruption in
  CIC-IDS2017 and CSE-CIC-IDS2018, above 75% for some attack classes.

---

# 7. Open items

Items 1, 2, 5, 6, 7, 8 and 10 of the original list are closed by §4.16, §4.18, §4.26, §4.14,
§4.19, §4.27 and §4.25 respectively; the 86,400 s and host-pair-only groupings by §4.29.
**The three items that stood after Phase 2 are now closed: ADDIS's discarding rule as a
second attack surface by §4.33, the alert audit by §4.32, and the cause of the position-0.85
anti-conservatism by §4.31.** What remains:

1. **A human analyst pass over the 152 adjudicated alerts.** §4.32 adjudicates every one
   against the red team's own task record and reaches 96.1% agreement with the labels, and
   emits `out/a2_audit_adjudicated.csv` with all evidence fields and a blank `human_verdict`
   column. What no automated procedure supplies is confirmation against the full exercise
   scoring system. The remaining step is a review of a documented adjudication, and the
   direction of the residual error is known (§4.32: it inflates the reported FDP). `[OPEN]`

2. **Second dataset with genuine flow→campaign labels.** No drop-in option exists; the three
   candidate routes each cost 3–5 days and each introduces a caveat (WORKPLAN T11). The
   zero-cost partial substitute — treating the five window positions as five
   quasi-independent deployments — is already computed throughout §4.15 and §4.22–§4.33.
   **This is the only remaining item that would change a headline number.** `[OPEN]`

3. **A second feedback-controller design.** §4.14 sweeps η and window for one proportional
   controller. An integral term or direct quantile targeting would show the §4.19 comparison
   is not controller-specific. Robustness check, not a contribution. `[OPEN]`

4. **Correcting the LSPR23 labels for the host pairs §4.31 identifies.** The record does not
   do this: rewriting a public dataset's labels from our own detector's tail would be
   circular, and the pairs were identified with test-split information. What is done instead
   is to state the direction of the error and to report FDP as an interval that contains the
   corrected value (§4.32). Correcting the labels would need the exercise's own logs.
   `[OPEN, deliberately]`

## 4.34 Smoothed and continuous conformal evidence (`t34a_E1_derivation.py`, `t34_E1_smoothed.py`) `[EXACT]` / `[REAL]`

The most exposed gap in the record: F1's finite feasibility horizon rests on evidence
**bounded** by `M = (|C|+1)/k`, and the resolution-collapse literature (Hennhöfer & Preisach,
arXiv 2603.23205) removes that bound by randomised smoothing. The record cited it and had
never tested it. Two routes are run, and both are derived in closed form first
(`t34a_E1_derivation.py`, 152 numerical checks) so that any disagreement between derivation
and simulation is diagnosed as a bug rather than recorded as a finding.

Write `G = #{c ∈ C : c > s}` and `E = #{c ∈ C : c = s}`. The record's evidence is the
discrete `p_d = (1+G+E)/M`, floor `1/M`. The smoothed alternative is
`p_u = (G + U(1+E))/M` with `U ~ Unif(0,1)`.

### What smoothing is, exactly `[EXACT]`

Conditioning on the multiset of the `N+1` exchangeable values, `p_u` is uniform on
`(A_ℓ/M, (A_ℓ+n_ℓ)/M]` given that the test point takes the ℓ-th distinct value, and mixing
over ℓ with weights `n_ℓ/M` gives density 1. So:

- **`p_u` is exactly Unif(0,1)**, ties or no ties — finite-sample exact, **marginal** validity.
- `p_d` is the **right endpoint** of `p_u`'s support, hence `p_u ≤ p_d` always, and `p_d` is
  super-uniform with `P(p_d ≤ a) = 0` for every `a < 1/M`. That zero is the feasibility floor.
- Validity is marginal over the calibration draw and **not** conditional on it. An online
  `α_t` depends on the same calibration set through the earlier hypotheses, so
  `P(p_u ≤ α_t) ≠ E[α_t]` in general: with `N = 1`, `α_1 = 0.2` and `α_2 = 0.5`/`0.01`, the
  exact rejection probability is **0.140667 against `E[α_2] = 0.108`**, a factor 1.302.
  This is F10/F11's calibration-conditional failure, unchanged; §4.26's Bates adjustment
  applies to the smoothed evidence exactly as it does to the discrete evidence.

**Route A** (`p_u` straight into a p-value procedure): for a hypothesis with rank `(G, E)`,
`P(reject at level a) = clip((aM − G)/(1+E), 0, 1)`; for ceiling evidence `(G = E = 0)`,

    P(reject) = min(1, a·M) = min(1, α_t·(|C|+1)).

A null hypothesis rejects with probability exactly `a`, so the lift of ceiling evidence over
a null one is exactly `M` — the same number that is the e-value ceiling. **Smoothing creates
no evidence; it spends the level as a lottery ticket at odds `M`:1.**

**Route B** (`p_u` → calibrator `f_λ(p) = λp^{λ−1}` → e-value procedure): `f_λ` is strictly
decreasing, so `e ≥ 1/a ⟺ p_u ≤ (aλ)^{1/(1−λ)}` and

    P(reject) = min(1, (α_t·λ)^{1/(1−λ)}·M).

At λ = ½ (Vovk) this is `α_t²M/4`, i.e. `e = 673.2/√U` at `|C|+1 = 1,813,114` and `U ≤ 1.14×10⁻⁶`
to clear `1/α_t = 6.3×10⁵` — the work plan's arithmetic, confirmed. Since
`(aλ)^{1/(1−λ)} ≤ a` for every `λ ∈ (0,1)`, `a < 1`, **Route B's rejection region is a strict
subset of Route A's at the same level, for every calibrator in the family**, and the gap is a
power law, not a constant. The best λ is far below Vovk's ½ — 0.040 to 0.057 over
`α_t ∈ [10⁻⁹, 10⁻⁶]` — and even there Route B is 27–68× below Route A.

**Boosting is not vacuous here, and it still does not close the gap.** F15/§4.28 shows
`b* = 1` exactly for the two-point e-value. For the calibrated continuous one,
`b* = (τ/λ)^λ`, which at λ = ½ is `√(2τ)` — §4.28's own closed form, recovered independently
and confirming that result from the other direction. The boosted rejection region is exactly
`p_u ≤ λ·α_t`, so boosting collapses the power-law gap to the **constant factor λ**, and
boosted Route B is Route A run at a level λ times smaller. It is therefore dominated by the
Route A arms measured below, and needs no separate run. Finally, the calibrator that
maximises the rejection region at a fixed `τ = 1/a` is the all-or-nothing
`e = (1/a)·1{p ≤ a}` — the **threshold conformal e-value construction the record already
uses**, whose rank-k member is `(M/k)·1{p_d ≤ k/M}`; the two coincide as rules at `a = k/M`.
**The reviewer's route, done optimally, returns to the paper's own construction applied to a
smoothed p, and every smooth calibrator is strictly worse than it.** `[EXACT]`

### Episode-level merges

Episodes need a merge, and the choice turns out to matter more than smoothing does. With the
discrete two-point evidence, if `r` of `m` flows fire the record's mean-e rule gives
`min(1,1/Ev) = m/(M·r)`. **Simes**, `min_k (m/k)·p_(k)`, reproduces that value exactly and is
the faithful p-space analogue; it is strictly smaller only where the minimum is attained at
`k > r` (0, 7, 3 and 4 of the 110, 104, 152 and 152 firing episodes across the four
configurations). Testing Route A under a weaker merge would make E1 a strawman, so Simes is
the primary merge. **Hommel**, `H_m · Simes`, is Simes made valid under **arbitrary**
dependence — the assumption the record's mean-e rule satisfies for free by linearity — and
`H_m ≈ ln m + 0.577` is 12–13 for this stream's largest episodes. **Bonferroni**
`min(1, m·min_i p_i)` and **mean-p** `min(1, 2·mean_i p_i)` are both arbitrary-dependence
valid and are carried as controls. Every smoothed arm has a **discrete control under the same
merge**, so a difference is attributable to smoothing rather than to the merge.

### Position 0.55, the guarantee window, `γ ∝ j^−1.6` (no horizon knowledge) `[REAL]`

LOND, mean over 2 detector seeds × 100 randomisation seeds; `T` = 57,368 episodes of which
275 are malicious, `|C|` = 2,448,993, margin +0.067.

| evidence · merge | rejections | FDP | episode recall | structural silence | alert Jaccard | malicious episodes detected `P ≥ 0.9` | `P > 0` |
|---|---|---|---|---|---|---|---|
| **discrete · mean-e** (the record) | 18.0 | 0.000 | 0.065 | **90.1%** | 1 (deterministic) | **18** | 18 |
| discrete · Simes | 18.0 | 0.000 | 0.065 | 90.1% | 1 (deterministic) | 18 | 18 |
| **smoothed · Simes** | **23.9 ± 2.7** | 0.003 ± 0.011 | **0.087 ± 0.010** | **0.0%** | **0.642** | **18** | **96** |
| smoothed · Bonferroni | 22.6 ± 2.9 | 0.004 ± 0.012 | 0.082 ± 0.011 | 0.0% | 0.604 | 16 | 96 |
| **smoothed · Hommel** (arb. dep.) | **12.0 ± 4.7** | 0.001 ± 0.006 | **0.044 ± 0.017** | 0.0% | **0.428** | **0** | 64 |
| smoothed · mean-p | 12.0 ± 0.0 | 0.000 | 0.044 | 0.0% | 1.000 | 12 | 12 |

**Structural silence goes 90.1% → 0.0% and the absorbing state disappears**, exactly as
derived: `inf p_u = 0`, so `P(reject) = α_t·M > 0` at every step and no state is absorbing.
That much of the reviewer's objection is correct and is now measured.

**What it buys is a lottery, not detections.** Smoothing adds 5.9 expected rejections and
0.022 of episode recall, but **the set of malicious episodes detected with probability ≥ 0.9
is 18 — identical to the discrete rule's deterministic 18**. The extra yield is spread over
78 further malicious episodes, none of which is detected reliably. `Var(R_T) = 7.14` and the
alert set differs by **36% between two randomisation seeds** (Jaccard 0.642, ratio-of-
expectations 0.637). Under the merge that is valid where the record's own rule is valid —
Hommel, arbitrary dependence — the yield is **negative**: 12.0 rejections against the
discrete 18.0, recall 0.044 against 0.065, `Var(R_T) = 22.37`, Jaccard 0.428, and **not one
malicious episode is detected with probability ≥ 0.9.** The mean-p merge annihilates the
smoothing entirely (Jaccard 1.000, `Var(R_T) = 0.00`): with mean episode size in the
thousands the `U`s average out, exactly as the Irwin–Hall form predicts.

### Position 0.85, the instrumented stress window `[REAL]`

Reported separately and never as a guarantee: the evidence here is not a valid e-value
(§4.31). LOND, `γ ∝ j^−1.6`: discrete mean-e gives 71.5 rejections, recall 0.280, silence
65.5%; smoothed Simes gives **119.5 ± 5.0**, FDP 0.006 ± 0.003, recall **0.466 ± 0.020**,
silence 0.0%, Jaccard 0.792, and 74 episodes at `P ≥ 0.9` against the discrete 72. The
qualitative picture is the same — silence removed, two additional reliably-detected episodes,
72 further episodes detected only probabilistically — but the numbers inherit the window's
label anomaly and carry no guarantee.

### Why the smoothed arms exceed q where the discrete arm does not `[REAL]`

The benign tail-validity ratio, computed as the **exact** expectation over the randomisation
(`E[1{p_u ≤ a}] = clip((aM−G)/(1+E),0,1)` averaged over benign test flows, not from one draw):

| level `a` | 1/M | 10/M | 3×10⁻⁵ | 5×10⁻⁵ | **10⁻⁴** | 2×10⁻⁴ | 10⁻³ | 10⁻² | 10⁻¹ |
|---|---|---|---|---|---|---|---|---|---|
| pos 0.55 seed 0 | **1.83×** | 0.81× | 0.63× | 4.87× | **7.94×** | 4.54× | 2.94× | 1.22× | 1.09× |
| pos 0.55 seed 1 | **1.07×** | 2.03× | 1.00× | 7.52× | **7.85×** | 4.49× | 2.92× | 1.86× | 1.11× |
| pos 0.85 seed 0 | **50.90×** | 9.18× | 5.81× | 4.70× | 19.98× | 11.58× | 5.29× | 1.71× | 1.31× |
| pos 0.85 seed 1 | **24.34×** | 10.62× | 7.71× | 12.81× | 14.39× | 8.51× | 5.27× | 1.71× | 1.30× |

At position 0.55, `a = 10⁻⁴` puts **1,817.7 benign flows in the rejection region against
228.8 nominal** (± 42.6 from the benign split, ± 0.5 from the randomisation): decisively
anti-conservative, on a check with ample power. The 1/M column is the ratio the record
already reports — and at position 0.55 it rests on **1.7 expected benign flows against 0.9
nominal**, so it has almost none.

**The discrete rank-1 rule queries exactly one point of the calibration tail, `a = 1/M`, and
that is the one point that is well calibrated.** Smoothing, and any rank-based merge that
uses `p_(k)` for `k > 1`, moves the operating point into the mid-tail, where the conformal
p-value on this stream is 3–8× anti-conservative. That, not the randomisation, is what puts
the smoothed Simes/Bonferroni FDP above q under the horizon-uniform `[ORACLE]` γ (0.089 and
0.094 at position 0.55) — the discrete Simes control shows 0.085 there without any smoothing
at all. **The coarseness of the discrete construction is protecting its own validity.**

### ADDIS's escape is destroyed by the merge, not by smoothing `[REAL]`

F1's surviving escape is ADDIS, whose spending index counts *tested* hypotheses and which the
two-point p-value never produces. Fraction of episode p-values at or below ADDIS's `τ = 0.5`:

| | record mean-e | discrete Simes | smoothed Simes |
|---|---|---|---|
| pos 0.55 seed 0 | **0.0019** | 0.8506 | 0.8506 |
| pos 0.85 seed 0 | **0.0048** | 0.9581 | 0.9581 |

Under the record's rule the index advances on 0.19% of episodes and ADDIS escapes; under any
rank-based merge it advances on 85–96% of them and the escape is gone. **Smoothing changes
this by less than 10⁻⁴.** The escape is a property of the two-point *p-value distribution*,
which the aggregation rule creates, not of the randomisation.

### Route B, measured `[REAL]`

Position 0.55, `γ ∝ j^−1.6`, rejections over 100 randomisation seeds:

| λ | 0.1 | 0.25 | **0.5 (Vovk)** | 0.75 |
|---|---|---|---|---|
| e-LOND | 0.2 ± 0.5 | 0.0 ± 0.1 | **0.0** | **0.0** |
| online e-BH | 1.7 ± 2.2 | 0.0 ± 0.1 | **0.0** | **0.0** |

Route B is dead at the guarantee window without horizon knowledge, at every calibrator
including Vovk's, exactly as the closed form requires. Where it works at all it needs the
`[ORACLE]` horizon-uniform γ and the smallest λ — e-LOND at λ = 0.1 gives 44.4 ± 26.8
rejections with Jaccard 0.429, i.e. a 60% coefficient of variation on the alert count. At
position 0.85, λ = 0.1 gives e-LOND 61.7 ± 1.9 against the discrete rule's 71.5, and λ = 0.75
gives zero everywhere. **The calibrated route is uniformly worse than the discrete rule it
was proposed to replace.**

### Derivation against simulation

Every closed form above is checked against the measured randomisation frequency on the real
scores, at fixed levels (no procedure state, so episodes are independent given the data):
Route A's Bonferroni episode probability `1 − Π_i(1 − clip((aM/m − G_i)/(1+E_i),0,1))` at four
levels, and the per-flow forms at half-integer ranks `p* = (r+½)/M` for `r ∈ {0, 3, 30, 300,
3000}`, where a flow of rank exactly `r` has probability ½ and the check bites hardest.
**116 checks, 0 mismatches, over 5,032,227 individually-checked episode and flow cells**;
worst standardised deviation 4.80 against a Bonferroni-corrected critical value, worst pooled
z 2.00. The `t34a` closed forms and the LSPR23 measurements agree.

### Verdict on the alternative

Finite-sample **exact**, **marginal** validity — the same as the discrete construction, and
with the same calibration-conditional failure (F10/F11). It removes the resolution floor and
with it the absorbing state, and it converts structural silence into detection with
probability `α_t·(|C|+1)`, which decays to zero exactly as `α_t` does. **The hard horizon
becomes a soft one, not a solved problem.** The rejection-free yield beyond the old hard
horizon `t* = 748` (LOND, `γ ∝ j^−1.6`, `R = 0`, `|C|+1 = 1.81×10⁶`) is
`α·M·Σ_{t>t*} γ_t = 1,246.5` expected rejections spread over *all* hypotheses there, benign
and malicious alike — which is why the realised gain in reliably-detected malicious episodes
is zero.

## 4.35 Periodic controller restart and batching (`t35a_E2_derivation.py`, `t35_E2_restart.py`) `[EXACT]` / `[REAL]`

Answers *"a SOC does not run one controller forever — why not reset every hour, shift or
day?"*. Batching is cited (Zrnic et al., *The Power of Batching*) as power recovery; it does
not address rejection feasibility, and restart had never been run. Closed forms are derived
and checked first (`t35a_E2_derivation.py`, 201 numerical checks); the measurement asserts
against them on the real stream (908 checks, 0 mismatches).

**What restart means here.** At each epoch boundary the controller's wealth, rejection count
and spending index reset; the detector and calibration set do not. Epoch boundaries are
floors of the **absolute** clock, the same grid `h_stream.build_episodes` uses for its time
buckets, and every episode is asserted to lie inside a single epoch. A grid offset between
the two — or an epoch narrower than the grouping bucket — lets a straddling episode carry
evidence from a later epoch into a hypothesis tested by the earlier epoch's freshly reset
controller, which inflates restart's apparent power; combinations with `epoch < bucket` are
therefore not run, and the coherent hourly-restart configuration is 1 h grouping × 1 h epoch.

### The scoping constraint, which is itself a result `[REAL]`

LSPR23 spans 161.5 h, but **90% of its flows fall in the final 25.6 h**, so a deployment
window that leaves room for training and calibration is short in time however it is placed:

| split | deployment | span | `\|C\|` |
|---|---|---|---|
| 0.55 | block `[i2, i3)` — the record's guarantee window (**W1**) | 8.52 h | 2,448,993 |
| 0.55 | to end of stream (**W2**) | 13.29 h | 2,448,993 |
| 0.10 | to end of stream (**W3**, weak calibration) | 25.87 h | 813,683 |
| 0.05 | to end of stream — the longest possible | 26.98 h | ~406,870 |

**A 48 h epoch is unmeasurable on this dataset**, and a 24 h epoch is measurable only at an
early split that costs a threefold smaller calibration set. W1 and W2 touch a single UTC day,
so an exercise-day boundary does not fall inside them. This is the same constraint §4.14
meets and is the reason E7 must make an explicit scoping choice.

### E2a — restart restores detection, and nearly replaces horizon knowledge `[REAL]`

Position 0.55, `γ ∝ j^−1.6` (no horizon knowledge), two-hour grouping, mean over two detector
seeds. `T` = 57,368 episodes of which 275 are malicious.

| procedure | epoch | epochs | cold-start margin | rejections | FDP | episode recall | malicious-flow coverage | structural silence |
|---|---|---|---|---|---|---|---|---|
| LOND | none | 1 | +1.134 | 18.0 | 0.000 | 0.065 | 0.007 | **90.1%** |
| LOND | **2 h** | 4 | +7.538 | **95.0 ± 5.7** | 0.000 | **0.345** | **0.377** | 53.9% |
| LOND | 4 h | 3 | +5.403 | 63.0 ± 4.2 | 0.000 | 0.229 | 0.124 | 67.9% |
| LOND | *none, `γ = 1/T`* `[ORACLE]` | 1 | +1.134 | *100.0 ± 5.7* | *0.000* | *0.364* | *0.154* | *0.0%* |
| LORD++ | none | 1 | +0.067 | 19.0 | 0.000 | 0.069 | 0.007 | 87.0% |
| LORD++ | **2 h** | 4 | +3.269 | **99.5 ± 4.9** | 0.000 | **0.362** | 0.381 | 41.9% |
| SAFFRON | none | 1 | — | **0.0** | — | 0.000 | 0.000 | 99.3% |
| SAFFRON | 2 h | 4 | — | 74.0 ± 4.2 | 0.000 | 0.269 | 0.130 | 69.9% |
| ADDIS | none | 1 | — | 107.0 | 0.009 | 0.385 | 0.615 | 0.0% |
| ADDIS | 2 h | 4 | — | 106.5 ± 4.9 | 0.009 | 0.384 | 0.501 | 0.0% |
| online e-BH | none | 1 | — | 18.0 | 0.000 | 0.065 | 0.007 | 0.0% |
| online e-BH | 2 h | 4 | — | 99.0 ± 5.7 | 0.000 | 0.360 | 0.498 | 0.0% |

The cold-start margin is reported with **each procedure's own coefficient**: LOND's level at
`R = 0` is `α·γ_t`, LORD++'s leading term is `γ_t·w₀`, so LOND's requirement is exactly half
LORD++'s and the record's `(|C|+1)w₀/T − 1` is the Family-II convention. SAFFRON, ADDIS and
online e-BH index their levels by counts of *tested* hypotheses or by a fixed point over the
whole history, so a single scalar cold-start margin is not defined for them.

**Restart works, and it works largely by removing the need for the oracle.** A two-hour
restart takes LOND from 18.0 to 95.0 rejections and episode recall from 0.065 to 0.345 at
FDP 0.000 — within 5% of what the **horizon-uniform `[ORACLE]` γ achieves uninterrupted**
(100.0, 0.364). Malicious-flow coverage rises further, 0.007 → 0.377, because the extra
alerts land on large episodes. The two procedures that already escape the §4.13 template
gain nothing: ADDIS is unchanged (107.0 → 106.5), as F1 predicts, since its index never
advances on this evidence.

**The epochs are not silent.** The workplan's prediction was that most epochs would go silent
before their first rejection, since the first-rejection deadline `D_LOND = 902` applies
afresh each epoch against 6,733 episodes/hour. On this stream **no epoch yields zero
discoveries** at any epoch length on W1: attacks are dense enough in the guarantee window
that the 902-hypothesis prefix reaches one. That is a property of LSPR23's attack density,
not a general one — D3b's exchangeable-null reference does not bound the ordered stream in
either direction, because attack prevalence rises steeply through the exercise.

### The daily restart the reviewer actually asks for `[REAL]`

W3 is the only window on which a 24 h epoch is a restart rather than a no-op — 25.87 h, two
epochs, `|C|` = 813,683. `γ ∝ j^−1.6`, LOND:

| epoch | none | 6 h | 12 h | **24 h** |
|---|---|---|---|---|
| epochs | 1 | 5 | 3 | **2** |
| rejections | 36.5 ± 0.7 | 87.0 ± 18.4 | 75.5 ± 6.4 | **48.0 ± 5.7** |
| episode recall | 0.043 | 0.103 | 0.090 | **0.057** |

**The gain is monotone in the number of restarts, so a daily reset is nearly the whole loss.**
At 24 h the deployment gets two controllers and recovers a third of what a 6 h reset does.

### E2b — the trade, in one table `[REAL]`

W1, epoch = grouping bucket = 2 h, `γ ∝ j^−1.6`, LOND. The precommitted allocations divide
`q` over the **scheduled** wall-clock epochs, not the non-empty ones: a deployment cannot
know in advance which hours will carry traffic, and one of the five 2 h epochs here is empty.

| allocation | total α spent | mean per-epoch margin | rejections | episode recall |
|---|---|---|---|---|
| uninterrupted | q | +1.134 | 18.0 | 0.065 |
| precommitted **geometric** (Σ = q) | q | −0.138 | 27.0 | 0.098 |
| precommitted **uniform** q/n (Σ = q) | q | −0.083 | **53.5** | 0.195 |
| **per-epoch full q** (Σ = n·q) | 4q | +3.585 | **95.0** | 0.345 |

**Restart's gain decomposes, and only half of it is free.** Resetting the *spending index*
costs no budget and is worth 18.0 → 53.5 rejections — 46% of the total gain. Resetting the
*budget* as well is worth the remaining 54%, and it is exactly the part that spends `n·q`
instead of `q`. [D4b] predicts that a uniform allocation reproduces the uninterrupted margin
exactly for equal epochs; the realised −0.083 against +1.134 differs only because the epochs
are unequal, and under the horizon-uniform `[ORACLE]` γ the prediction lands: LORD++ goes
98.5 → 28.0 rejections when the budget is divided.

### The guarantee that is lost `[EXACT]`

Per-epoch FDR control does **not** pool. mFDR does, by the mediant inequality: if
`E[V_i] ≤ q·E[R_i]` for every epoch then `ΣE[V_i]/ΣE[R_i] ≤ q`. FDR does not, because pooled
FDP is a weighted average of per-epoch FDPs with **data-dependent** weights `R_i/ΣR_j` —
pointwise `pooled FDP ≤ max_i FDP_i`, but the weights correlate with the FDPs and the
expectation does not aggregate. Let each epoch, independently, reject one hypothesis with
probability `q` and let it be false: every epoch has `FDR_i = q` exactly, yet

    pooled FDR = 1 − (1 − q)^n

which at q = 0.05 is 0.098 at 2 epochs, **0.185 at the 4 epochs of the headline arm**, 0.226
at 5 and 0.676 at the 22 epochs of an hourly restart over W3. LOND, LORD++ and e-LOND control
FDR, not mFDR, so a deployment that restarts them has a per-epoch guarantee and, at the
deployment level, only the trivial `pooled FDR ≤ n·q`. **A SOC that restarts daily and reports
a monthly false-discovery rate is not making the guarantee it thinks it is.** The realised
per-epoch FDP on the headline arm is 0.000 in all four epochs at both detector seeds, so
nothing here demonstrates the failure — the point is that the guarantee no longer excludes it.

### E2c — restart preserves episode resolution; coarsening does not `[REAL]`

W1, LOND, `γ ∝ j^−1.6`. **These arms are not at a matched alert budget**, so episode recall is
reported against the *oracle achievable recall at each arm's own alert count* (§4.19's
frontier), not against another arm's recall.

| grouping | epoch | `T` | alerts | episode recall | oracle @ that budget | malicious-flow coverage |
|---|---|---|---|---|---|---|
| 1 h | none | 65,190 | 18.0 | 0.058 | 0.058 | 0.004 |
| **1 h** | **1 h** | 65,190 | **125.5** | **0.406** | 0.406 | **0.377** |
| 2 h | none | 57,368 | 18.0 | 0.065 | 0.065 | 0.007 |
| 2 h | 2 h | 57,368 | 95.0 | 0.345 | 0.345 | 0.377 |
| 6 h | none | 47,037 | 18.0 | 0.103 | 0.103 | 0.011 |

**Every arm sits exactly on the achievable frontier at its own budget**, which is S6 again:
restart does not beat the frontier, it moves the procedure *along* it to a budget the
uninterrupted controller was structurally prevented from spending. But the comparison that
matters for H2 is the last two rows against the second: coarsening to 6 h buys feasibility
and reaches episode recall 0.103, while **restarting hourly at 1 h grouping reaches 0.406 —
four times the resolution — with no coarsening at all**.

Restart and coarsening are algebraically the *same* feasibility lever: both divide the
hypothesis count a single controller run must survive, and both give
`margin = M·c/T_ep − 1`. They differ only in the price. Coarsening pays in episode
resolution, which is H2's measured cost. Restart pays in the pooled guarantee (above) and in
`n` fresh first-rejection deadlines. **H2's granularity–feasibility tradeoff is therefore a
statement about a single uninterrupted controller, and must be stated that way.**

## 4.36 Deterministic precommitted weights and the ordering attack (`t36a_E3_derivation.py`, `t36_E3_asymmetric.py`) `[EXACT]` / `[REAL]`

Answers *"your impossibility theorem is about symmetric e-merging — why not use an asymmetric
rule?"*. §4.16's corollary already proves the escape (`F(e) = e_slot` for a precommitted slot
is valid under arbitrary dependence and padding-invariant) and §4.12 policy D already prices
it. The record also already names the real condition: **the adversary must not be able to
choose which slot its events occupy.** This section tests that condition and nothing else.

**The class.** A precommitted weight sequence `w_1, w_2, …  ≥ 0`, fixed before any score is
observed and indexed by position within the episode, merged as `F(e) = Σ_i w_i e_i`. By
linearity `E[F] = Σ_i w_i E[e_i] ≤ Σ_i w_i`, so `F` is a valid e-merging function under
**arbitrary dependence** iff `Σ_i w_i ≤ 1` — the same linearity that makes the arithmetic
mean valid, with no independence assumption. Appending zeros leaves positions `1..m`
untouched, so `F` is unchanged for every `r`: padding-invariant by construction. The
single-slot rule is the special case `w = (1, 0, 0, …)`.

### The two legs, in closed form `[EXACT]`

Write `β = 1/(α_t·M)` for the weight mass a detection needs, so that with two-point evidence
`F ≥ 1/α_t ⟺ Σ_{i∈S} w_i ≥ β` over the firing set `S`.

**Power.** Call position `i` *individually detectable* if a lone attack flow there fires the
rule, `w_i ≥ β`. Since `Σ w_i ≤ 1`,

    P = #{i : w_i ≥ β} ≤ 1/β = α_t·M

and the bound is tight (attained by `⌊1/β⌋` positions at exactly weight `β`) and needs no
monotonicity. **`α_t·M` is the same quantity that governs F1's feasibility horizon** — there
the number of stream steps at which a rejection is possible, here the number of within-episode
positions at which one can be triggered — and it decays with `α_t` in the same way.

**Ordering.** Let the attacker prepend `L` flows carrying zero evidence. The most favourable
case for the defender is that every remaining flow fires, so detection is impossible once
`Σ_{i>L} w_i < β`. Define the **front-load cost**

    L*(w, β) = min{ L ≥ 0 : Σ_{i>L} w_i < β }.

> **Proposition.** For every precommitted non-negative weight sequence with `Σ_i w_i ≤ 1` and
> every `β > 0`, `L*(w, β)` is **finite**. Summability gives `Σ_{i>L} w_i → 0`, so the set is
> non-empty. **No choice of precommitted weights escapes.** ∎

This uses the same summable-tail convergence lemma as §4.13's Proposition 2, on the
within-episode position axis rather than the stream-time axis. It is the same *lemma*, not
the same theorem: Proposition 2 additionally needs rejection-free runs, distinct lags and the
absorbing-state argument.

Closed forms, verified against brute force: first-event-only `L* = 1`; uniform over `m₀`
slots `L* = max(0, ⌊m₀(1−β)⌋ + 1)`; exponential decay `L* = max(0, ⌊log β / log ρ⌋ + 1)`.
`⌊·⌋+1`, not `⌈·⌉`: at an exact integer the tail equals `β` rather than falling below it. For
non-increasing `w` the detectable set is a prefix and `L* ≥ P` — the inequality runs this way,
because the positions beyond `P` are individually undetectable yet still carry mass the
attacker must clear (exponential decay at `ρ = 0.99`, `α_t = 10⁻²` has `P = 548`, `L* = 1006`).

**The requirement on the pads is zero evidence, not merely benign labels**: a leading flow
that happened to fire would occupy a high-weight position and help the defender. Operationally
this is mild — a benign flow fires at the conformal floor, probability ≈ 4.4×10⁻⁷ at the
guarantee window (§4.31's 1.07× of `1/M`).

### Measured, position 0.55, `γ ∝ j^−1.6`, LOND, mean over two detector seeds `[REAL]`

`T` = 57,368 episodes, 275 malicious, `|C|` = 2,448,993. The final column is the §4.16
appended-padding cost against the record's arithmetic mean, computed **on the episodes that
arm and the mean arm both detect, at the same levels** — a paired comparison, not each arm's
cost on its own different detections.

| rule | padding-invariant | alerts | episode recall | `L*` (ordering attack) | §4.16 pad vs the mean, paired | ratio |
|---|---|---|---|---|---|---|
| **mean (the record, symmetric)** | — | 18.0 | 0.065 | — | — | — |
| **first-event-only** | yes | 17.0 | 0.062 | **1** | 111 | **112× cheaper** |
| exp-decay ρ = 0.5 | yes | 17.0 | 0.062 | 2 | 111 | 56× cheaper |
| uniform over 10 slots | yes | 17.0 | 0.062 | 8 | 111 | 14× cheaper |
| uniform over 100 slots | yes | **7.5** | **0.027** | 81 | 492 | 6× cheaper |
| exp-decay ρ = 0.99 | yes | **7.5** | **0.027** | 164 | 492 | 3× cheaper |
| last-event-only | **no** | 12.5 | 0.045 | — (one *appended* flow) | 336 | — |
| prior-port, first 10 high-risk `[out of class]` | yes | **0.0** | 0.000 | — | — | — |

**Every padding-invariant scheme that keeps the mean rule's recall is defeated by 1–8 leading
flows.** Buying `L*` up to 164 costs 57% of the episode recall (0.062 → 0.027) and still
leaves the ordering attack three times cheaper than padding the symmetric rule. At the stress
window the same shape holds with larger numbers: the best scheme (exp-decay ρ = 0.99) holds
recall 0.275 against the mean's 0.280 but is defeated by **446** front-loaded flows against
**7,717** appended ones, still 17× cheaper.

Two schemes fail for structural reasons rather than on cost. **Last-event-only is not
padding-invariant at all** — one appended zero moves the counted slot onto the pad — so it is
excluded by the definition, not by a measurement. The **security-prior** scheme (weight the
first ten flows whose destination port is in an a-priori high-risk set) is **out of class**
and is reported as a diagnostic: its weights select slots using an evaluation-time covariate
rather than a precommitted position, so `Σw ≤ 1` does not establish validity without
conditional calibration. It is included because it is the obvious thing a practitioner would
try, and on this stream it fires on **0 of 275** malicious episodes.

**`L*` is an upper bound.** It is quoted at the *unperturbed* level: a sequential attacker
that suppresses earlier episodes leaves LOND with a smaller rejection count, hence a smaller
`α_t`, a larger `β` and a weakly **smaller** `L*`. The real cost is therefore no higher than
the table shows.

### The triangle closes

A precommitted weight scheme cannot have all three of

- **(a) padding-invariance** — needs weights indexed by absolute position;
- **(b) usable power** — needs weight mass `≥ β` where attack flows land;
- **(c) resistance to attacker-controlled ordering** — needs `L*` large.

Validity forces `Σw ≤ 1`; (a) additionally forces the weights to be fixed by absolute
position. Given `Σw ≤ 1`, (b) caps the scheme's reach at `P ≤ α_t·M` positions — the same
quantity as F1's feasibility horizon — and (c) is impossible outright, because `L*` is finite
for every summable `w`. The design choice sets only the **price**, and the price is paid out
of power: concentrating weight early maximises per-position power and drives `L*` to 1;
spreading it raises `L*` and drives every `w_i` below `β`, so no lone attack flow is
detectable anywhere. **The asymmetric escape does not stop the attack; it converts an
appended-padding attack costing hundreds to thousands of flows into a front-loading attack
costing one to a few hundred, and the exchange is unfavourable at every operating point
measured.** This completes C3.

## 4.37 Calibration contamination (`t38a_E4_derivation.py`, `t38_E4_contamination.py`) `[EXACT]` / `[REAL]`

**Reviewer objection.** *"You assume a large clean benign calibration set. In security, how do
you know the calibration period is attack-free?"* — sharpened by A1 (§4.31), which found label
problems in this very dataset. Contaminating flows are drawn from the **calibration window's
own** malicious flows (the physical model of a missed label; the training window would be
in-sample for the detector and the deployment window would leak the evaluation split), under
two injection models and two calibration models, at positions 0.55 and 0.85.

### The tolerable amount is a count, not a rate — and adversarially it is zero

At `k = 1` the entire rule is a single order statistic, the calibration **maximum**: a flow
fires iff its score exceeds it. Contamination can act only through that number. Injecting `j`
attack flows that clear the clean maximum moves the threshold to the `k`-th largest *injected*
score once `j ≥ k`, so **the tolerable number of adversarial mislabels is exactly `k − 1`** —
and F14 fixes `k = 1` as the only feasible rank, so it is **zero**. `k` is not only a power
parameter and a reliability parameter; it is the contamination budget, and feasibility has
already spent it.

| | position 0.55 | position 0.85 |
|---|---|---|
| clean recall / rejections | 0.065 / 18 | 0.282 / 72 |
| **1 adversarial mislabel** | **0.000 / 0** | **0.000 / 0** |
| 1 random mislabel | 0.062 / 17 | 0.125 / 32 |
| 2 random mislabels | 0.000 / 0 | 0.125 / 32 |
| 10 random mislabels | 0.000 / 0 | 0.016 / 4 |

The adversarial arm has **no rate dependence at all**: the top `εN` attack flows share the same
maximum for every `ε > 0`, so the curve is a step at one flow, not a slope. Sweeping `ε` on that
arm measures nothing — verified, the threshold is identical for every `ε` with `a ≥ 1` and for
`j = 1`. The workplan's `ε` grid is also too coarse to see it: at `|C| ≈ 2×10⁶`, even `ε = 10⁻⁷`
rounds to **zero flows**.

### The random arm does have a scale, and it is one flow

`P(threshold moves) = 1 − (1−q₀)^{a}`, where **`q₀` is the exceedance rate of the contamination
pool** against the clean calibration maximum — *not* the deployment window's malicious firing
rate. The two differ whenever the calibration and deployment windows' attack scores are not
exchangeable, which F9 says they are not; a first version of this experiment used the
deployment rate and predicted the transition at 30 flows where the measurement showed 2.

| | `q₀` | `ε* = 1/(N·q₀)` | in flows |
|---|---|---|---|
| position 0.55 | 0.9043 (3,647 of 4,033 pool flows would themselves fire) | 4.5×10⁻⁷ | **1.11** |
| position 0.85 | 0.7623 (487,778 of 639,913) | 7.2×10⁻⁷ | **1.31** |

Checked by Monte Carlo without replacement against the exact hypergeometric at every count:
0.9027/0.9043, 0.9914/0.9909, 0.9991/0.9991 (0.55) and 0.7597/0.7623, 0.9439/0.9435,
0.9859/0.9866 (0.85), all inside 5σ. **Random contamination costs nothing until it injects one
flow the clean detector would itself have fired on** — which, at `q₀` of 0.76–0.90, is very
nearly the first flow. Expressed in flows the two arms are the same statement; expressed as a
rate they look unrelated, and flows are the right unit.

Over 400 draws per count (a single draw reports one sample of a Bernoulli-driven variable):

| random mislabels | 1 | 2 | 3 | 5 | 10 |
|---|---|---|---|---|---|
| median recall, 0.55 (clean 0.065) | 0.051 | 0.000 | 0.000 | 0.000 | 0.000 |
| P(recall = 0), 0.55 | 0.318 [0.274, 0.365] | 0.562 [0.514, 0.610] | 0.705 [0.659, 0.748] | 0.880 [0.844, 0.908] | 0.985 [0.968, 0.993] |
| median recall, 0.85 (clean 0.282) | 0.192 | 0.118 | 0.090 | 0.082 | 0.059 |

(95% Wilson intervals; the run reports FDP as **undefined** rather than 0.000 wherever there
are no rejections, which is most of this sweep.)

### It costs power *and* a bounded amount of validity — the workplan predicted only the first

The prediction was "contamination costs power, not validity". That is right for the *full*
conformal p-value `(1+G)/(N+1)`, which rises under contamination exactly when the injected flows
out-score the point more often than the clean p-value does — i.e. wherever the detector beats
chance (an if-and-only-if: a worse-than-chance region *is* made anti-conservative).

But the pipeline does not use that p-value. It uses the threshold conformal e-value, whose
`p = min(1, n/(M·m))` carries the ceiling `M = |C|+1` in its **denominator**. Contamination
therefore acts through **two channels at once**:

  `Ev_ε / Ev₀ = [1 + ε] × [m_ε / m₀]`

the **firing** channel (`≤ 1`, deflates: power) and the **ceiling** channel (`≥ 1`, inflates:
validity). A contaminating flow that does *not* clear the threshold leaves `m` alone and acts
through the ceiling only, so `p` **falls** by exactly `(1+ε)`. That is anti-conservative, and it
is a genuine validity violation: `E[e] ≤ (N+a+1)/(N+1) = 1+ε`.

Driven deliberately, by injecting only flows scoring *below* the clean maximum:

| position | usable stealth budget | threshold | recall | effective `q` |
|---|---|---|---|---|
| 0.55 | 386 of 4,033 pool flows (9.6%) | **unmoved** | 0.065 (unchanged) | 0.05 → **0.050008** |
| 0.85 | 152,135 of 639,913 (23.8%) | **unmoved** | 0.282 (unchanged) | 0.05 → **0.054195** |

The p-value ratio matches `1/(1+ε)` to 9 decimals at every count, and the threshold does not
move by a single ULP. **The asymmetry is the answer E4 owes the reviewer:** power dies at
`a = 1` flow and is not bounded at all; validity degrades by a factor `(1+ε)` that would need
`a = N` mislabelled flows to double. Under the size-matched **replacement** model the ceiling is
exactly invariant and the channel closes entirely, which is what that arm is for.

Two qualifications travel with `q → q(1+ε)`: it holds for LOND and LORD++, whose bound is a sum
of offered levels, and is **multiplicative on top of** whatever the clean rule already does —
§4.31 measures up to 50.9× nominal benign firing at position 0.85, and `(1+ε)` multiplies *that*.
It is not claimed for online e-BH, whose threshold is a fixed point over the whole history.

### The feasibility margin is not a safety indicator

The margin is `CEIL·w₀/T − 1`, and under the additive model contamination **increases** `|C|`.
Measured, it is constant to six decimal places — **0.999984** at position 0.55 and **0.999978**
at 0.85 — across the entire sweep, while recall goes from 0.065 to 0.000 and from 0.282 to
0.000. Any monitoring built on the margin alone would report health throughout. The margin
measures whether the *arithmetic* admits a rejection, not whether any flow can supply the
evidence; the diagnostic that does move is the benign/malicious firing-rate pair, reported at
every level for exactly this reason.

### Answer to the objection

**The approach stops working at one mislabelled attack flow.** Not a rate — a flow. If an
adversary can place a single high-scoring attack flow into the calibration set, detection goes
to zero at both windows; if labels fail at random, the scale is one flow that the clean detector
would itself have flagged, which the measured `q₀` puts at very nearly the first one. Validity
survives: the only channel that touches it is bounded by `(1+ε)` and requires the attacker to
choose *low*-scoring traffic, which costs them the power attack entirely. Expressed as the
workplan asked — a tolerable `ε` — the answer is **4×10⁻⁷**, three orders of magnitude below
its smallest non-zero grid point, and it is the wrong unit.


## 4.38 Cross-window parameter transfer (`t39a_E6_derivation.py`, `t39_E6_transfer.py`) `[REAL]`

**Reviewer objection.** *"Were the grouping width, family, cap or spending sequence chosen
after looking at the test window?"* Five deployment windows (0.55, 0.62, 0.70, 0.77, 0.85) ×
two detector seeds; E6a selects a configuration on window `j−1` and evaluates on `j` (four
ordered pairs); E6b selects on four and evaluates on the held-out fifth. Prerequisite:
`t26_H4_grouping.py --five`, which extends the grouping grid from two positions to five
(`out/t26_H4_5pos.json`; the default two-position run and `out/t26_H4.json` are unchanged).

**The objective is flow coverage, not episode recall,** and that is not a preference. Episode
recall is `tp/n_mal_episodes` and the *grouping family sets the denominator*: coarser grouping
merges malicious episodes, so a rule that alerts on one coarse episode can out-score one that
alerts on many fine ones while covering fewer attack flows. In the limit of a single episode
containing every malicious flow, recall is 1 whenever it fires. Selecting a grouping by recall
selects coarseness. Measured consequence: **the two objectives pick different configurations at
5 of 5 windows** (seed 0; 4 of 5 at seed 1). This is F4's flow-vs-episode gap doing damage in a
new place.

**Feasibility is not a tuned parameter and is gated out first.** The margin is
`CEIL·w₀/T − 1` — a function of `|C|`, `k` and `T` only (F5), with no scores and no labels — so
the feasible/infeasible verdict for every configuration is available before the deployment
window is observed. Selection is restricted to configurations feasible on the *selection*
windows and the oracle to those feasible on the *evaluation* window; an "oracle" that picks a
configuration the feasibility theorem forbids is an unattainable upper bound, not an oracle,
and using one inflated the reported regret by 0.008 before this was fixed. 30 of 35
configurations are feasible at every window and seed, 2 at none (`src-dst` and `subnet24` at
300 s), and the feasible set moves by at most 3 configurations across windows. **The record's
grouping is feasible everywhere.**

### The grouping axis (family × bucket width, 35 configurations)

| window | oracle | oracle config | worst | spread | **frozen** (`src-dst`, 7200 s) | frozen ρ |
|---|---|---|---|---|---|---|
| 0.55 | 0.6976 | (`subnet24`, 21600) | 0.4894 | 0.2082 | 0.6502 | 0.228 |
| 0.62 | 0.3214 | (`src`, 86400) | 0.0214 | 0.3000 | 0.0216 | 0.999 |
| 0.70 | 0.5943 | (`subnet24`, 3600) | 0.0107 | 0.5836 | **0.0107 (the worst)** | 1.000 |
| 0.77 | 0.3846 | (`subnet24`, 3600) | 0.0055 | 0.3791 | 0.0055 | 1.000 |
| 0.85 | 0.9972 | (`src`, 21600) | 0.9963 | 0.0009 | 0.9964 | 0.925 |

(seed 0; seed 1 is the same picture, and its 0.70 window has zero coverage for every
configuration, so no selection is possible there at all.)

**Two findings, and they point in opposite directions.**

*The headline grouping is not test-window tuned.* It attains the **worst feasible** flow
coverage on the grid at position 0.70 and sits within 10⁻⁴ of the worst at 0.62 and 0.77. No
one tunes on a test window to obtain the worst configuration. The objection is answered — but
by evidence of the opposite of tuning, not by a small regret.

*The grouping optimum does not transfer, and that is a real limitation.* Previous-window
selection has worst regret **0.579** (ρ = 0.991) at seed 0 and 0.290 (ρ = 0.962) at seed 1;
leave-one-out gives 0.284 and 0.376. Window-to-window variation of the oracle itself is 0.676 —
larger than any within-window spread. **Flow coverage at a fixed grouping is not predictable
from the previous window**, and the record's coverage numbers should be read as *what the
deployable grouping achieves*, never as *the best achievable*.

The configurations that win are consistently coarse — `subnet24` at 3600–21600 s, `src` at
86400 s. That is the same trade C2 is about: coarsening buys flow coverage and spends episode
resolution (§4.35 measures the other direction, 0.406 against 0.103). E6 does not overturn the
grouping choice; it prices it.

### The cap axis (`n₀` ∈ {p99, max, p999, p90, p50, mean})

| window | oracle | oracle cap | **frozen** (`p99`) | frozen ρ |
|---|---|---|---|---|
| 0.55 | 0.3200 | p50 | **0.0000 (the worst)** | 1.000 |
| 0.62 | 0.2286 | p50 | 0.0025 | 0.989 |
| 0.70 | 0.2160 | p90 | 0.0070 | 0.968 |
| 0.77 | 0.1748 | p50 | **0.0000 (the worst)** | 1.000 |
| 0.85 | 0.4275 | p90 | 0.0941 | 0.780 |

**The cap transfers well and the record's cap is not the powerful one.** Previous-window
selection has worst regret **0.012** (ρ = 0.070) and leave-one-out 0.010 (ρ = 0.048): whichever
window you select on, you pick p50 or p90 and lose almost nothing. The frozen `p99` is the
worst feasible cap at two of five windows. That is not an error: §4.12 chose `n₀` for
*validity* and *front-load cost*, not power, and the two costs a power-only selection ignores
are stark —

| | p99 | max | p999 | p90 | p50 | mean |
|---|---|---|---|---|---|---|
| `n₀` at 0.85 | 408 | 96,258 | 11,866 | 25 | **2** | 66 |
| raw-rule violating group share | 0.011 | 0.000 | 0.001 | 0.097 | **0.387** | 0.058 |
| median front-load defeat cost (flows) | 122 | — | 3,553 | 8 | **1** | 21 |

A power-only selection lands on `n₀ = 2`, whose median front-load defeat cost is **one flow**
and under whose raw rule 39% of groups are not valid e-values at all.

### Design rules that had to be settled first (`t39a`, `[EXACT]`)

A transfer experiment on a flat grid reports zero regret for every rule including random
selection, so normalised regret is **undefined** (not 0) on a flat grid and the raw spread is
printed beside every regret. Folds whose *selection* window is flat are excluded from the
transfer summary and reported separately — one fold at each seed — because their "selection" is
a tie-break, not an optimisation; before that exclusion the cap axis reported a spurious worst
regret of 0.195. The tie-break priority is declared in the script's source before any file is
opened, and the number of tied winners is reported (up to 32 at the degenerate window). The
selection-window value is a maximum over 35 configurations and overstates: both it and the
evaluation-window value are reported, and the drop — the winner's curse, up to 0.66 — is itself
a number.

**Accept criterion met**, in both directions the criterion allows: the grouping and cap choices
are shown not to require test-window tuning, *and* the one that does not transfer — the
grouping optimum — is named.


## 4.39 A second feedback controller, and disposition delay in real time (`t40_E7_controller.py`) `[REAL]`

Answers *"RQ4 rests on one hand-chosen proportional controller, and latency is measured in
alerts rather than real time."* §4.14's baseline is a single proportional controller on the
episode max-score threshold, updating an exact calibration order statistic only when a
disposition arrives, with latency counted in **alerts**.

### The scoping decision, made explicitly

The work plan offered (a) run on the full 161.5 h stream with a coarser alerting unit, or (b)
report only the short delays. **Neither is available as stated, and §4.35 says why**: LSPR23
spans 161.5 h but 90% of its flows fall in the final 25.6 h, so a deployment window that
leaves room for training and calibration spans **at most 26.98 h** however it is placed. There
is no full-stream deployment window. The decision taken:

- 15 min, 1 h, 4 h and 8 h at the **guarantee window** (position 0.55, span 8.52 h) — 8 h is a
  third of that window and is marginal;
- 24 h only on §4.35's **long-span window** (split 0.10, span 25.87 h), whose calibration set
  is three times smaller; every such row is tagged `[WEAK-CAL]`;
- **72 h is unmeasurable on LSPR23** and is reported as such rather than omitted.

### Three controllers, wall-clock delay, target q = 0.05 `[REAL]`

Two textbook alternatives are added; no control algorithm is invented. **PI** adds an
integral term with anti-windup. **AQT** is Robbins–Monro adaptive quantile targeting: on each
arriving disposition move the threshold up by `step·(1−q)` if the alert was false and down by
`step·q` if it was true, whose fixed point is `FDP = q`. Each controller's gain is selected on
the evaluation stream — as §4.14 does — so every FDP below is a **best case** for its family;
the fixed pre-committed configuration is reported beside it.

Guarantee window, mean ± sd over two detector seeds:

| delay | P | PI | AQT | alerts | % of alerts issued open-loop | % of steps at the actuator limit |
|---|---|---|---|---|---|---|
| 0 | **0.053 ± 0.002** | **0.049 ± 0.004** | 0.172 ± 0.031 | 112–136 | 0.9% | 95–100% |
| 15 min | 0.402 ± 0.005 | 0.402 ± 0.005 | 0.523 ± 0.004 | 179–252 | **51.4%** | 45–87% |
| 1 h | 0.514 ± 0.013 | 0.514 ± 0.013 | 0.592 ± 0.011 | 221–273 | 60.5% | 63–73% |
| 4 h | 0.671 ± 0.017 | 0.671 ± 0.017 | 0.671 ± 0.017 | 329 | 77.8% | 44.7% |
| 8 h | 0.834 ± 0.009 | 0.834 ± 0.009 | 0.834 ± 0.009 | 1,014 | 99.8% | 12.0% |
| no feedback | 0.841 | — | — | 1,082 | 100% | — |

Long-span window `[WEAK-CAL]`, where a 24 h delay is a real delay: P and PI reach FDP 0.075 at
zero delay, 0.514/0.468 at 1 h, 0.676 at 6 h and **0.877 at 24 h** against 0.887 with no
feedback at all. **A daily disposition cycle is indistinguishable from having no feedback.**

### What this settles

**RQ4's conclusion is not controller-specific.** P and PI hold the target at zero delay
(0.053, 0.049) and become numerically identical from 15 min onward; by 4 h all three
controllers agree to three decimals, and by 8 h all three are within 0.007 of the no-feedback
FDP. Whatever the control law, the same thing happens.

**AQT does not hold the target even at zero delay** (0.172 tuned, 0.286 at its fixed
configuration). Reported because it is a standard rule and its failure is informative: its
stationary point is correct in expectation, but at 0.48% episode prevalence the disposition
stream is too sparse for a stochastic-approximation rule to converge inside the window.

**Wall-clock delay is far harsher than alert-counted latency, and that is the new result.**
§4.14 found the proportional controller holding its target to roughly 50 alerts of latency.
In real time it is already at **eight times the target after fifteen minutes** — because
alerts arrive in bursts, so a fifteen-minute delay leaves **51.4%** of them issued before any
disposition returns. Latency measured in alerts flatters the controller; the same system
measured on the clock fails much sooner.

**The controller is mostly not steering.** At zero delay it sits at the actuator limit — the
strictest threshold it can set, the calibration maximum — for **95–100% of steps**, which is
the same threshold the conformal e-value uses. At short delays it stays pinned 87% of the
time. The measured "feedback" advantage is therefore largely the conservative threshold, not
the feedback.

Taken with §4.14, RQ4's answer stands and is now honest in both directions: **direct feedback
is competitive only when dispositions arrive within minutes, and formal no-feedback error
control is what remains under any realistic disposition cycle.**

## Standing caveat: horizon knowledge

The rejection threshold `τ = T/w₀` and the horizon-uniform spending sequence `γ = 1/T` both
use `T`, the number of episodes in the evaluation window. That is knowledge of the deployment
horizon, and it is the same oracle labelled explicitly in §4.20. It is disclosed wherever it
is used, and §4.20's horizon-misspecification sweep quantifies what mis-stating it costs:
LOND and LORD++ tolerate a 2× over-estimate, e-GAI 5×, online e-BH 100×, and ADDIS needs no
horizon at all.

---

## 4.40 Both attacks in operational units (`t41a_E8_derivation.py`, `t41_E8_units.py`) `[REAL]`

Every attack budget in this record is a count of flows. E8 converts them into packets, bytes,
sustained bandwidth and attacker hosts, using the real per-flow packet and byte distributions
of each §4.30 padding pool rather than an average.

**The unit of `Flow Duration` is recovered, not assumed.** The file carries both the totals
and the rates, which overdetermines the unit: `Flow Bytes/s = (fwd + bwd bytes)/(duration/S)`
holds for exactly one `S`. Median |log₁₀ ratio| over the deployment window:

| candidate | seconds | milliseconds | **microseconds** | nanoseconds |
|---|---|---|---|---|
| median \|log₁₀ ratio\| | 6.000 | 3.000 | **8.9×10⁻⁹** | 3.000 |

Microseconds, three decades clear of every alternative, recovered on 84.2% of the deployment
window's flows (those with positive duration, bytes and rate). Assuming it would have been
correct here, but a wrong assumption scales every bandwidth figure below by 10³ or 10⁶, and
the audit procedure has already caught three rescaled headline numbers in this project.

**Per-flow cost of each pool** at position 0.85, p10 / median / p90:

| pool | flows | packets | payload bytes | mean wire bytes | median duration |
|---|---|---|---|---|---|
| generic benign | 1,638,722 | 1 / 4 / 31 | 116 / 256 / 4,156 | 5,955 | 2.9 ms |
| attacker-origin | 301,016 | 3 / 6 / 37 | 192 / 524 / 6,712 | 6,202 | 39.6 ms |
| black-box (most common benign service) | 584,850 | 3 / 4 / 4 | 151 / 232 / 434 | 438 | 2.3 ms |

Byte figures are reported twice throughout: **payload** (LSPR23 columns 14–15) and **wire** =
payload + 40 B/packet, the TCP/IPv4 minimum. The header columns (42–43) are outside
`h_stream`'s cached feature range, so an exact wire figure is not available; quoting payload
alone would understate the attacker's cost, which is the direction that flatters the attacker.

**The budgets, priced against the black-box pool** — the weakest attacker in the record, who
picks the single most common benign service with no detector access at all. Each is at the
pool's median flow (the "typical" model — the i.i.d.-expectation and cheapest-choosable models
are exported alongside it); the window is the one the traffic must fit inside. For padding that
is the **2 h bucket**, since pad flows must land in the same episode. For the state attack it
is **position 0.85's own deployment span, 2.403 h** — *not* §4.35's 26.98 h long-span window,
which is taken at split 0.05 where `|C| ≈ 406,870`, while the 92,015,637-flow figure is
computed at `|C|+1 = 1,813,114`. Pricing an attack from one `|C|` regime over a window from
another understates the required rate elevenfold:

| budget | flows | packets | wire bytes | sustained rate | hosts at 10 Mbit/s |
|---|---|---|---|---|---|
| suppress one alert (median) | 34 | 136 | 13.3 kB | **15 bit/s** | 1 |
| suppress one alert (p90) | 227 | 908 | 89.0 kB | 99 bit/s | 1 |
| suppress all 147 ADDIS detections | 4,998 | 19,992 | 1.96 MB | 2.2 kbit/s | 1 |
| padding at ADDIS's own λ-capped level, one episode | 34,465,311 | 1.38×10⁸ | 13.5 GB | 15.0 Mbit/s | 2 |
| ADDIS spending-state attack (§4.33) | 92,015,637 | 3.68×10⁸ | 36.1 GB | 33.4 Mbit/s | 4 |

**Bandwidth is not what separates the two attack surfaces.** The workplan expected the
sentence to be "padding is plausibly operational; the state attack at 9.2×10⁷ flows is
structural". Priced in bytes that is **false**: the state attack is 36.1 GB spread over 27
hours, i.e. **33.4 Mbit/s from four hosts at 10 Mbit/s each** — well within a small botnet or
one well-provisioned machine. What makes it structural is volume against the *monitored
population*:

| budget | × the deployment window's own flow count | × the whole 161.5 h dataset |
|---|---|---|
| suppress one alert | 1.4×10⁻⁵ | 2.1×10⁻⁶ |
| suppress all 147 alerts | 2.0×10⁻³ | 3.1×10⁻⁴ |
| padding at ADDIS's level | 14.1 | 2.1 |
| ADDIS spending-state attack | **37.5** | **5.6** |

The deployment window carries 2,453,026 flows. An attacker who multiplies a monitored
network's flow count by 37.5 is not hiding, whatever their bit rate — and that, not
bandwidth, is the barrier. Suppressing a single alert is 1.4×10⁻⁵ of the window: **fifteen
bits per second for two hours.** The gap between the two attacks is 2.7×10⁶ in bytes and
2.7×10⁶ in flows, and it is the flow axis that carries the argument.

**Estimator, and which pools.** A budget is `n` flows *drawn from a pool*, and "`n` times a
quantile" is a proxy rather than a model, so four explicit models are computed and named:
i.i.d. expectation (`n·mean`), typical (`n·median`, quoted above), cheapest-repeatable
(`n·min`), and cheapest-distinct (the sum of the `n` smallest, `None` when `n` exceeds the
pool — which it does for both large budgets). They differ materially: the 34-flow black-box
budget is 13.3 kB typical against 14.9 kB in expectation.

Three of §4.30's five pools are priced. `protocol-matched` and `service-matched` are defined
*per episode* (the victim's own modal protocol and destination port), so they have no single
global per-flow cost distribution. §4.30's finding is that the cost is identical across all
five, so the omission does not change the conclusion.

**The black-box pool does not depend on the deployment window.** §4.30 chooses the most
common benign service from the deployment window itself, which uses that window's labels.
Choosing it from the **training window** instead gives the *same service* (UDP/53) at both
positions and therefore the same pool and the same costs — so the dependence is empirically
void here, rather than merely small.


## 4.41 Timestamp-tie sensitivity (`t42a_E9_derivation.py`, `t42_E9_ties.py`) `[REAL]`

`h_stream.build_episodes` orders episodes by `np.lexsort((first_pos, first_ts))` — first
timestamp, ties broken by first occurrence in the stream — specifically so that
equal-timestamp episodes are ordered deterministically (standing mistake 5). E9 measures
the variance that choice suppresses. It is not fixing a bug; it is pricing a convention.

**Exposure, before any seed is spent.** The movable population is a property of the stream's
clock alone — no detector, no labels, no procedure — so it is computable first and decides
whether anything else is worth running:

| window | episodes | distinct `first_ts` | tied blocks | episodes tied | fraction | largest block |
|---|---|---|---|---|---|---|
| 0.55 | 57,368 | 57,042 | 325 | 651 | 1.13% | 3 |
| 0.62 | 49,267 | 49,001 | 265 | 531 | 1.08% | 3 |
| 0.70 | 37,231 | 37,016 | 215 | 430 | 1.15% | 2 |
| 0.77 | 31,672 | 31,495 | 177 | 354 | 1.12% | 2 |
| 0.85 | 31,568 | 31,362 | 206 | 412 | 1.31% | 2 |

At most 1.3% of episodes can move at all, and the first-detection *rank* can shift by at most
`B_max − 1` = 2 ranks.

**Result: nothing moves.** Fifty randomised tie orders at positions 0.55 and 0.85, against
LOND, LORD++ and ADDIS, over discoveries, true positives, FDP, recall, first-detection rank
and first-true-detection rank — **all 36 statistics take a single value across all 50 orders,
equal to the deterministic one.** Not "small variance": zero distinct values.

The randomisation has power, checked rather than assumed: all 50 orders differ from the
deterministic one, and a draw moves 324 of the 651 movable episode positions on average at
0.55 (min 284, max 372) and 205 of 412 at 0.85. A first version of this row reported "4 of 18
statistics vary" at 0.55 — an artefact of testing `np.std(ddof=1) > 0`, which returns ~10⁻¹⁷
on 50 bitwise-identical float64 values. The test is now an exact distinct-value count.

**Why it is zero rather than merely small** (`t42a`, `[EXACT]`). A tie block's permutation
propagates past the block only if it changes the number of rejections made *inside* it: LOND's
state after a block is the single integer `R`, so two orders that agree outside the block and
reject equally often inside it leave every later step bit-identical. With blocks of size 2–3
and 18–110 rejections over 31,568–57,368 episodes, no block straddles the rejection boundary.

One tempting shortcut is **refuted** here rather than assumed: processing the smallest
p-values first does *not* maximise a block's rejection count. Brute force over all `B!` orders
beats it on 127 of 600 random blocks, by as much as 3 rejections — LOND's level rises with `R`
and falls with `t`, so the count-maximising order spends the early, high-`γ` steps on the
*marginal* episodes, not the certain ones. There is no cheap surrogate for the block optimum,
so extremes must be enumerated where `B!` is tractable and labelled as samples otherwise.

**Consequence for the paper.** One appendix sentence, which is the branch the accept criterion
allows: *the deterministic tie-break is stated for reproducibility, and 50 randomised orders
change no reported quantity at either window.* `build_episodes` gained an additive `tie_key`
argument for this; `tie_key=None` reproduces the record exactly (`t22a_stream_selftest.py`).


## 4.42 The padding attack outside the anomalous window (`t43_E10_xwindow_padding.py`) `[REAL]`

**Reviewer objection.** *"The attack only exists in your anomalous label window."* §4.30 costs
the padding attack at positions 0.62 and 0.85, and 0.85 is exactly the window §4.31 diagnoses
as anomalous (50.9× nominal benign firing). E10 runs the reduced experiment — two pools,
generic benign and the black-box most-common-service pool — at all five positions, using
`t28_P5_padding.py`'s own `r90` (AST-imported, so the two cannot drift).

| window | seed | detected | pool | mean e | P(fire) | `r_90` p10 / med / p90 |
|---|---|---|---|---|---|---|
| 0.55 | 0 | 82 | generic | 1.07 | 4.37e-07 | 1 / 3 / 7 |
| 0.55 | 0 | 82 | black-box | **0.00** | **0** | 1 / 3 / 7 |
| 0.55 | 1 | 72 | generic | 1.07 | 4.37e-07 | 1 / 3 / 8 |
| 0.55 | 1 | 72 | black-box | **0.00** | **0** | 1 / 3 / 8 |
| 0.62 | 0 | 93 | generic | 1.16 | 4.72e-07 | 2 / 6 / 52 |
| 0.62 | 0 | 93 | black-box | **0.00** | **0** | 2 / 6 / 52 |
| 0.62 | 1 | 33 | generic | **0.00** | **0** | 2 / 3 / 18 |
| 0.62 | 1 | 33 | black-box | **0.00** | **0** | 2 / 3 / 18 |
| 0.70 | 0 | 64 | generic | 3.79 | 1.65e-06 | 17 / 62 / 78 |
| 0.70 | 0 | 64 | black-box | **0.00** | **0** | 17 / 62 / 78 |
| 0.70 | 1 | **0** | — | — | — | no detections to suppress |
| 0.77 | 0 | 50 | generic | 2.72 | 1.28e-06 | 4 / 35 / 106 |
| 0.77 | 0 | 50 | black-box | **0.00** | **0** | 4 / 35 / 106 |
| 0.77 | 1 | 54 | generic | 2.72 | 1.28e-06 | 2 / 35 / 111 |
| 0.77 | 1 | 54 | black-box | **0.00** | **0** | 2 / 35 / 111 |
| 0.85 | 0 | 116 | generic | 50.90 | 2.81e-05 | 5 / 35 / 268 |
| 0.85 | 0 | 116 | black-box | **0.00** | **0** | 5 / 35 / 268 |
| 0.85 | 1 | 110 | generic | 24.34 | 1.34e-05 | 8 / 36 / 402 |
| 0.85 | 1 | 110 | black-box | **0.00** | **0** | 8 / 36 / 402 |

`r_90` is identical for the two pools in **every** row above — see below.

**The attack is not confined to the anomalous window.** All four non-0.85 positions have a
measurable median cost, against the ≥ 3 the accept criterion asks for. Per window:

| window | 0.55 | 0.62 | 0.70 | 0.77 | **0.85** |
|---|---|---|---|---|---|
| median `r_90` (flows) | 3 | 4.5 | 62 | 35 | **35.25** |

(medians over pool × seed cells; the generic and black-box pools give identical medians at every window)

The pooled median over the other four windows is 6 flows against 35.25 at 0.85, but that
aggregate is driven by the two cheap windows and **must not be read as "cheaper everywhere"**:
0.70 is nearly twice as expensive as 0.85, and 0.77's 35 is indistinguishable from it. Strictly,
three of the four are below 0.85 and one is above. The defensible statement is the one the
objection asks for — the attack exists, and is cheap in absolute terms, at every window that
produces detections at all.

`r_90 − r_mean` is **recorded, not asserted**. "Needing 90% confidence cannot cost less than
needing it in expectation" sounds like a theorem and is not one: `out/t28_P5.json` already
contains 33 rows where `r_90` is one flow *below* `r_mean`, because for rare-fire padding a 90%
quantile can sit below the mean-cost boundary. Here the gap is 0 in every cell except two at
0.85 where it is +1.

**Oracle caveat, inherited.** `μ` and `P(fire)` are computed from the deployment window's own
realised e-values, so the attacker is credited with exact knowledge of the detector's output
on that window. These costs are lower bounds — §4.30 states the same caveat for the same
reason, and it does not change the conclusion because the black-box pool needs no detector
knowledge to *choose*.

**The black-box pool never fires anywhere.** Mean e is exactly 0.00 and P(fire) exactly 0 at
**all five** windows, so §4.30's finding that an attacker padding with the most common benign
service suppresses *deterministically* rather than probabilistically is a property of the
stream, not of position 0.85. `r_90` is **bit-identical** to the generic pool's in all
eighteen rows above, confirming §4.30's "every pool costs the same" across the full span:
`r_90` depends on `μ` only through `τ − μ`, and `τ` runs 1.27×10⁶ to 2.29×10⁶ while the
largest `μ` anywhere is 50.9.


## 4.44 Grouping-independent coverage and the resolution blur (`t47_W7_coverage.py`) `[REAL]`

**Reviewer objection (W7).** *"Episode recall falls as the unit coarsens"* is weakened because the
episode **definition changes with the bucket**, so the recall denominator is not invariant. Freeze a
fine-grained ground truth and measure coverage as the grouping coarsens, so the denominator never
moves.

**Fixed atomic ground truth.** The set of 5-minute src-dst **malicious** episodes (the finest
bucket): **1,899** units at the primary guarantee window 0.55, **1,973** at the stress-test window
0.85. This set is fixed across every alerting grouping. e-LOND, `γ ∝ j⁻¹·⁶` (the paper's primary
spending sequence), seed 0, src-dst family.

| bucket | 0.55 cov(fixed) | 0.55 blur | 0.55 recall(moving) | 0.85 cov(fixed) | 0.85 blur | 0.85 recall(moving) |
|---|---|---|---|---|---|---|
| 5 m | 0.020 | 1.0 | 0.020 | 0.308 | 1.0 | 0.308 |
| 30 m | 0.065 | 3.6 | 0.077 | 0.317 | 4.5 | 0.277 |
| 1 h | 0.068 | 7.2 | 0.058 | 0.322 | 8.8 | 0.238 |
| 2 h | 0.152 | 16.1 | 0.065 | 0.322 | 8.8 | 0.282 |
| 6 h | 0.240 | 25.3 | 0.103 | 0.743 | 20.4 | 0.439 |
| 1 d | 0.385 | 38.5 | 0.123 | 0.743 | 20.4 | 0.439 |

- **cov(fixed)** = fraction of the fixed atomic malicious units covered by ≥1 issued alert.
- **blur** = mean number of distinct atomic malicious units an issued alert lumps together.
- **recall(moving)** = ordinary episode recall, denominator = malicious episodes *at that grouping*.

**Two findings, one of which the worklist did not anticipate.**

1. **The honest resolution cost is the blur, and it is denominator- and γ-invariant.** As the bucket
   coarsens each issued alert blurs from **1** atomic malicious unit to **~20–40**: a 1-day alert
   says "something in this day-long host-pair blob is malicious," covering ~38 distinct 5-minute
   attack windows at once. This is the resolution lost, measured against a constant reference, and it
   rises monotonically under every configuration. **This is the hardened C2 the reviewer asked for.**

2. **The fixed-denominator coverage RISES with coarsening (0.020 → 0.385 at 0.55), and the moving
   recall's fall is γ-dependent.** Under the paper's primary `γ ∝ j⁻¹·⁶`, `recall(moving)` at 0.55
   *rises* (0.077 → 0.123), the OPPOSITE of the C2 "recall falls monotonically" claim. That claim
   holds only under the **oracle uniform γ = 1/T** that `t26_H4_5pos` / `fig3` plot (0.55:
   0.483 → 0.253; 0.85: 0.658 → 0.494). So the "recall falls" direction is an artifact of both the
   moving denominator AND the oracle spending sequence — exactly the reviewer's worry, confirmed.

**Consequence for the paper.** C2's resolution cost is now rested on the **blur** (fixed ground
truth, γ-robust); the body (`§5.1`, abstract, C1/C2 contributions) reports episode recall as the
oracle-sequence, moving-denominator view and names the blur as the cost we rest on. **`recall(moving)`
at 2 h matches `t21c` exactly (0.55 src-dst = 0.065), so the poly numbers are not a bug — they are
the primary spending sequence's genuine behaviour.**

**fig3 re-plotted to the blur (RESOLVED, 31 Aug 2026).** The `fig3` middle panel now plots the
**alert blur** (t47, all five windows) on a log axis instead of the oracle-γ episode recall, so the
headline figure shows a resolution cost that is denominator- and γ-invariant and rises monotonically
under the paper's primary poly γ. `make_figures.py::fig3_granularity()` reads `t47_W7.json` for the
middle panel (top/bottom panels stay on `t26`). This removes the γ-cherry-pick that plotting recall
under the oracle sequence would have invited. t47 now computes all five windows for this reason;
the 0.55/0.85 denominators (1,899 / 1,973) are unchanged.

**Reproduce.** `t47_W7_coverage.py` (importable, `main()`); artifact `out/t47_W7.json`; appendix
table `apptab:w7coverage`; consistency-checked in `t45`.

## 4.45 Controlled padding-dilution on the real detector (`t48_W3_dilution.py`) `[REAL]`

**Reviewer objection (W3).** LSPR23 has **no benign traffic on malicious host pairs** (all 310 are
100% malicious), so the premise that an attacker can send normal-looking padding to the attacked
victim is argued **structurally** from the flow-only feature set, not measured. Demonstrate it
directly on the trained detector.

**Setup (Option A, self-contained).** For each detected malicious episode at a window, append `r`
flows sampled from the **black-box pool** — the window's most common benign service (proto, dport),
chosen with no detector access — run the **shipped HGB detector** over those pad flows, and measure
the group e-value `E(G) = (1/(m+r)) Σ eᵢ` as `r` grows. e-LOND, `γ ∝ j⁻¹·⁶`, src-dst two-hour unit,
seed 0.

| window | pool flows | pad sampled | **pad fire rate** | detected | measured = closed form | median r* |
|---|---|---|---|---|---|---|
| primary (0.55) | 845,691 | 20,000 | **0.000000** | 18 | **18/18** | 118 |
| stress-test (0.85) | 584,850 | 20,000 | **0.000000** | 72 | **72/72** | 5,202 |

**Two things measured, not assumed.**

1. **The pad flows do not fire.** Running 20,000 real black-box-service flows through the shipped
   detector gives a firing rate of **exactly 0** at both windows (mean pad e-value 0.0). The
   structural premise — ordinary victim-service traffic scores like ordinary traffic — is now a
   measurement, not an argument.
2. **The measured dilution matches the closed form on every detected episode.** Because a pad
   contributes `e = 0`, the padded group e-value is exactly `E(G) = S/(m+r)`, and suppression occurs
   at exactly `r* = ⌊S·α_t⌋ − m + 1` on **18/18** guarantee-window detections and **72/72** at the
   stress window. The median `r*` (118 at 0.55, 5,202 at 0.85) reproduces §4.30 / Table I exactly.

**Scope.** This confirms the transfer for a **flow-level** detector. The host-conditioned boundary is
now measured in **§4.47**: at the guarantee window the transfer still holds against a competent
host-conditioned detector, and at the stress window the measurement is out-of-distribution (attacked
pairs are 100% malicious), so the boundary needs a benign-inclusive testbed. So `sec:paddingcost` is
"confirmed by a controlled experiment (flow-level features), transfer holds at the guarantee window
under host conditioning (§4.47), high-volume regime bounded by a testbed."

**Reproduce.** `t48_W3_dilution.py` (importable, `main()`); artifact `out/t48_W3.json` (carries the
full `E(G)`-vs-`r` dilution curve for a representative episode); appendix table `apptab:w3dilution`;
consistency-checked in `t45`.

## 4.46 Poisson intervals on the benign-firing diagnostic (`t50_calib_ci.py`) `[EXACT]`

**Reviewer objection (R3 / review §4.3).** Calling 0.55/0.62 "valid conformal evidence" from a
firing ratio near 1 overstates the evidence: the expected number of firing benign flows is ~1, so at
the guarantee windows only 0–3 events are observed. With counts that small a ratio near 1 is not
statistical proof that exchangeability holds. Separate the **theoretical guarantee** (holds under
Assumption 1) from the **empirical diagnostic** (limited resolution), and attach exact intervals.

**Exact Poisson (Garwood) intervals on the ratio `k/E[k]`, seed 0** (from `t30_A1.json` firing
counts; no detector rerun):

| window | fired benign `k` | expected `E[k]` | ratio | 95% CI | verdict |
|---|---|---|---|---|---|
| 0.55 | 1 | 0.934 | 1.07 | **[0.03, 5.96]** | includes 1 |
| 0.62 | 1 | 0.864 | 1.16 | **[0.03, 6.45]** | includes 1 |
| 0.70 | 3 | 0.792 | 3.79 | **[0.78, 11.06]** | includes 1 |
| 0.77 | 2 | 0.736 | 2.72 | **[0.33, 9.82]** | includes 1 |
| **0.85** | **46** | 0.904 | **50.90** | **[37.26, 67.89]** | **excludes 1** |

(Seed 1: 0.85 is `k=22`, ratio 24.34, CI [15.25, 36.85] — also excludes 1; the guarantee windows have
`k∈{0,1,2}` and all include 1.)

**Finding.** The diagnostic **cannot prove validity at the guarantee windows** — every interval there
includes 1 — it can only **fail to reject** it; at 0.85 the interval excludes 1 by orders of
magnitude, a clear violation. This is exactly the theory-vs-diagnostic separation the reviewer asks
for, and it is why the paper's language moved from "carry valid conformal evidence" to "compatible
with the nominal rate at the resolution this dataset allows … only fail to reject it; at 0.85 the
interval excludes 1." The guarantee itself is now stated as conditional on Assumption 1
(group-evidence validity), with the diagnostic as corroboration of no gross violation, not proof.

**Reproduce.** `t50_calib_ci.py` (importable, `main()`); artifact `out/t50_calib_ci.json`; appendix
table `apptab:tail` (now carries the 95% CI column); consistency-checked in `t45`.

## 4.47 Host-conditioned detector and the padding-transfer boundary (`t49_R7_host_detector.py`) `[REAL]`

**Reviewer objection (R7 / review §5.1, §15).** The padding attack (§4.45) is scoped to flow-level
features; the paper conjectures a host-conditioned detector "would break it" but leaves it to a
testbed. Build that detector, show it detects, and measure whether padding still transfers — does
victim-service traffic still score benign, does padding still dilute, how does the cost change, and
which feature (if any) breaks the transfer?

**Setup.** Augment the 33 flow features with **six strictly-causal host-context features** from
strictly-earlier-timestamp traffic only (ts < ts(flow); timestamp ties excluded — ~1.03M adjacent
flows share a timestamp): per-source prior count / distinct-destinations / failed-conn fraction, and
the same three per-destination. **No** endpoint ground-truth is used (`label_src`=1 and `label_dst`=1
both have attack-rate **1.0000** — verified, excluded as leakage), and no labels enter the features.
Train HGB on `X_aug = [flow | host]`, run e-LOND (`γ ∝ j⁻¹·⁶`, src-dst two-hour unit, seed 0). Because
episodes key on (src,dst), a diluting pad must carry the attacker's host pair and inherits its causal
context; we graft that context onto ordinary black-box pads (pool: the window's most common service
among **detector-non-firing** flows — chosen from detector outputs, no labels) and **replay the
append causally** (each appended pad raises src_cnt/dst_cnt, leaves src_ddst/dst_dsrc pinned — padding
one victim adds no new peer — and fail fractions are tested at the pool's measured rate and at the
adversarial worst 1.0). The feature builder is validated against a strict-ts brute-force reference
(0 mismatches, both sides); the augmented matrix width is asserted (33 flow + 6 host).

| window | AUROC host/flow | e-LOND det host/flow | **real benign fires** | **grafted pad fire** | verdict |
|---|---|---|---|---|---|
| primary (0.55) | 0.954 / 0.916 | 2 / 18 | **0 / 2,287,988** | **0.000** | **holds** |
| stress (0.85) | 1.000 / 0.999 | 37 / 72 | **3 / 1,638,722** | 0.429 | **inconclusive (OOD)** |

**Findings.**

1. **A competent host-conditioned detector.** Higher AUROC than the flow-only detector at both
   windows (0.954 vs 0.916; 0.9997 vs 0.9992) and non-zero e-LOND detections (2, 37) — unlike the
   Isolation Forest arm, which detects nothing. This is the second competent detector the review's
   §5.3 asked for.

2. **At the guarantee window the transfer holds — on a clean pool.** The black-box pad pool (most
   common non-firing service, no labels) is **100% benign** here (`pool_benign_frac = 1.000`).
   Grafting each attacked pair's real causal context onto those pads and densely sweeping the
   accumulation k = 1…min(r*, 10⁵) (120 log-spaced levels), the pads fire at **0** over 4×10⁶
   (episode × pad) trials, and the detector fires on **0 of 2.29M** real benign flows. Both agree:
   ordinary victim-service traffic still scores benign and padding still dilutes. **The cost is
   unchanged:** because the max pad fire rate is a measured 0, μ_pad = 0 exactly, so the suppression
   cost is the *identical* flow-level closed form r* = ⌊S·α_t⌋ − m + 1 (median 108 on the host
   detector's detected episodes vs 118 flow-level — same mechanism, no host penalty). We report a
   host-detector r* **only** where μ_pad = 0 is measured; where pads fire (§ below) HGB non-monotonicity
   makes a mean-μ proxy neither exact nor a bound, so no cost is claimed there.

3. **At the stress window the measurement is doubly unresolvable.** (a) The black-box non-firing pool
   is only **11.7% benign** (`pool_benign_frac = 0.117`) — the anomalous window is so attack-saturated
   that an attacker's "ordinary" traffic is itself mostly attack. (b) Grafted attack-context pads fire
   at 0.43 (ablation names the driver: **dst-distinct-src**, mean fire drop 0.36 when neutralised),
   which would defeat padding on the detected episodes — **but the detector fires on only 3 of 1.64M
   real benign flows (1.8×10⁻⁶).** The grafted vectors (ordinary flow-stats with an attacked host's
   context) never occur in real data, because LSPR23's attacked pairs are **100% malicious**: there is
   no real ordinary-to-victim traffic to validate the response, so the firing is an
   **out-of-distribution** extrapolation. The high-volume boundary cannot be settled on this dataset —
   it needs a benign-inclusive testbed (exactly the one the paper flagged).

**Bottom line.** Host conditioning does not break the padding attack where the online guarantee is
valid (0.55). Whether it breaks it under high-volume attack (0.85) is unanswerable on LSPR23 — the
100%-malicious-pair structure forces the host-conditioned measurement into extrapolation — which
turns the paper's "would need a testbed" caveat from a conjecture into a characterized boundary with
a named mechanism.

**Reproduce.** `t49_R7_host_detector.py` (importable, `main()`); artifact `out/t49_R7.json`; appendix
table `apptab:r7host`; consistency-checked in `t45`.

## 4.48 R7 on a benign-inclusive testbed — resolving the OOD, no graft (`t51_R7_ait.py`) `[REAL]`

**Reviewer objection (R7 continued / single-dataset).** §4.47's stress-window firing was an
out-of-distribution *extrapolation* — LSPR23's attacked pairs are 100% malicious, so no real
ordinary-to-victim traffic exists to test on. Answer the same question on a dataset that *does* have
it, and check whether host conditioning really flags ordinary-to-victim traffic on real data.

**Testbed audit → AIT-LDSv2.0** (Landauer et al., IEEE TDSC 2023; tstat netflows already in
`proto/data/`). Audited: its victims are real servers that serve heavy benign traffic *while* attacked
(attacked servers are **79–99.9% benign**, vs LSPR23's 100% malicious). So the pad analogue — an
ordinary flow to an attacked host — is present as **real data**. AIT's attacks are recon + web-exploit
+ exfil (scans, wpscan, dirb, webshell, cracking, dnsteal, post-exploitation commands): the
**low/moderate** regime. It has **no high-volume DDoS flood**, so it resolves §4.47's moderate regime,
not the flood.

**Setup.** 8 organisations, 1.92M **TCP** flows, **45,001** attack flows (2.34%). Leave-one-org-out
(train the host-conditioned HGB on 7 orgs, test on the 8th — a realistic "deploy on a new network"
test; the shared red-team playbook makes attacks detectable cross-org). Flow features selected **per
fold from the training orgs**, with all identity/label/role **and absolute-time** fields excluded
(`first`,`last`,`req_tm`,`res_tm` are epoch-scale and would leak the attack schedule; plus a
programmatic epoch guard); unknown/empty labels dropped. Six strictly-causal host features (t49's
validated builder; fail = TCP reset). Conformal calibration on the test org's early-benign window.
(TCP-only: DNSteal/data-exfil is UDP and not covered.)

| org | AUROC h/f | atk recall | benign→victim % (host/flow) |
|---|---|---|---|
| fox | 0.995/0.996 | 0.93 | 0.00 / 0.01 |
| harrison | 0.975/0.973 | 0.86 | 0.01 / 0.01 |
| russellmitchell | 0.988/1.000 | 0.47 | 0.00 / 0.02 |
| santos | 0.948/0.980 | 0.36 | 0.00 / 0.01 |
| **shaw** | 0.955/0.932 | 0.47 | **8.92** / 0.05 |
| wardbeck | 0.969/0.907 | 0.39 | 0.14 / 0.01 |
| wheeler | 0.999/0.998 | 0.97 | 0.01 / 0.01 |
| wilson | 0.974/0.984 | 0.85 | 0.07 / 0.00 |

**Findings.**

1. **Competent cross-scenario detector, no time leakage.** Host AUROC 0.948–0.999 (mean 0.975) on the
   held-out org, attack recall mean 0.66 — detection is behavioural (removing the epoch-time fields
   left AUROC high).

2. **Host conditioning adds a real but weak, highly org-dependent effect.** Host vs flow-only fire
   rate on real benign-to-victim traffic: **median delta ≈ 0**, and host is **negligible (≤0.14%) on
   7 of 8 orgs**. The mean host rate (1.14%) is 73× the flow mean (0.016%) — but that is driven almost
   entirely by **one outlier org (shaw, 8.9%)**; host is materially higher on only **1/8**.

3. **The LSPR23 graft was an out-of-distribution *overestimate* — confirmed.** Even the worst real
   host benign→victim fire (shaw, 8.9%) is **~5× below the LSPR23 grafted 43%** (§4.47), and on 7/8
   orgs host ≈ flow. So §4.47's stress-window "27/37 unsuppressible" was an OOD overestimate; host
   conditioning is *not* the strong defence the graft suggested.

**Bottom line.** A second, benign-inclusive dataset resolves R7's open ambiguity for the moderate
regime: on real data host conditioning gives at most a weak, inconsistent defence (negligible on
7/8 orgs, one outlier), far below the LSPR23 graft — so the padding attack **substantially transfers**
and the grafted defence was an extrapolation overestimate. The high-volume flood regime is absent from
AIT and remains open (needs a volume-attack testbed).

**Reproduce.** `t51_R7_ait.py` (importable, `main()`; reads AIT tstat netflows from `proto/data/`
zips); artifact `out/t51_R7_ait.json`; appendix table `apptab:r7ait`; consistency-checked in `t45`.


## 4.49 Full Surface A suppression pipeline on AIT, real victim pads (`t54_ait_suppression.py`) `[REAL]`

Review response (reviewer item 5): t51 measured only the pad-*scoring* premise on AIT. This runs the
whole Surface A chain per organisation: leave-one-organisation-out flow detector, in-org benign
conformal calibration (benign flows before the first attack), (src,dst,2h) episodes, e-LOND
detection, then each detected malicious episode padded with **real** benign flows to the same victim
(no graft). Result across all 8 orgs: e-LOND detects the malicious episodes (AUROC 0.90–1.00), the
real ordinary-to-victim pads fire the detector at ~1e-4, and the per-organisation median minimal
suppression cost is 212–13,142 real flows (first-flow order; round 31 re-run under a fold-keyed RNG —
the previous shared-RNG stream put `wardbeck` at 8,294, and the 1.6x swing between two streams is the
Monte-Carlo spread of a 200-draw median on the most expensive fold, not a change in the mechanism). So the padding attack transfers **end-to-end**, not only in its scoring premise.

**Caveats (blind-codex verified).** Like window 0.85, the AIT deployment's benign firing runs
11–68× nominal (aggregate ~57 observed vs ~2.2 expected) because calibration is pre-attack and
deployment is during-attack — an empirical live-fire split, **not** a validated exchangeable conformal
deployment, so these are attack-cost/mechanism measurements not guarantee-bearing ones (only 4
false-positive episodes across all orgs, so FDP stays low). The pads are benign-*looking* victim
traffic (the fire check uses all benign-to-victim; same-service pools are smaller and prices
replayable pads, not proving the finite captured trace holds enough unique instances). r* is a
one-at-a-time running-level lower bound. TCP-only; the high-volume flood regime remains open.

**Reproduce.** `t54_ait_suppression.py` (importable, `main()`); artifact `out/t54_ait_suppression.json`;
appendix table `apptab:aitsupp`; body §sec:transferattack. Two blind-codex passes.

## 4.50 ADDIS state poisoning on a synthetic guarantee-valid stream (`t52_B1_synthetic.py`) `[SYNTHETIC]`

Review response (reviewer item 4): the real-data ADDIS state attack (§4.33) runs at 0.85 where
ADDIS's null-consistency is violated, confounding the security consequence. **Key subtlety surfaced
in review:** ADDIS's horizon-escape on two-point conformal evidence is *inseparable* from its
guarantee-invalidity — the spending index fails to advance precisely when the p-values never land in
(λ,τ], which is the same reason they are not uniformly conservative. So no two-point stream is both
escape-feasible and guarantee-valid. We therefore use genuinely uniformly-conservative
Uniform(0,1) nulls (ADDIS's assumption holds). Verified: ADDIS controls FDR on this stream — the
honest **all-null** test (every rejection false) gives mean FDP 0.010 ≤ q=0.05 over 200 seeds, mixed
FDP 0.047 with recall 1.00; the selected-null uniform-conservativeness diagnostic is tight. The attack
is adversarial **state poisoning**: injecting precursors with p∈(λ,τ] (non-conservative nulls the
assumption forbids) keeps all 120 detections through B=139 and silences every rejection at B=140 (an
*empirical* synthetic threshold, not thm:addis's two-point closed form). So the security consequence
is a property of the mechanism, not an artefact of the dataset already violating ADDIS's assumptions.

**History.** First attempt used two-point conformal nulls; blind codex caught that these are only
marginally super-uniform (all-null FDR ≈ 0.86), so ADDIS's guarantee did not hold and Part A's low FDP
was a true-positive-dilution artefact. Rewritten with Uniform(0,1) nulls per that guidance; re-review
found no blocking defect.

**Reproduce.** `t52_B1_synthetic.py` (importable, `main()`, no data); artifact
`out/t52_B1_synthetic.json`; appendix table `apptab:addissynth`; body §sec:state; figure Fig 4C.

## 4.51 Within-bucket order-sensitivity of the headline detections (`t53_ordering.py`) `[REAL]`

Review response (reviewer item 2): a group's evidence uses its whole time bucket, so its hypothesis is
emitted at bucket close; the shipped order (`lexsort((first_pos, first_ts))`) is bucket-close order
with same-bucket ties broken by first-flow arrival — a pre-committed, evidence-independent key, so
there is **no look-ahead**. But the within-bucket order is **load-bearing**: re-running the headline
e-LOND detection under alternative pre-committed, evidence-independent within-bucket orders (group-id,
last-flow, fixed-random, hashed key) moves the true-detection count over **0–18** at the guarantee
window and **0–72** at the stress window, and the shipped first-flow order is the **largest** at both.
So the paper's detection counts (and the padding/frontier quantities on the detected set) are the
*generous*, detector-favouring end of the range; a typical order detects fewer, which only sharpens
the low-power finding. Feasibility (C1) is order-invariant (depends on |C|,k,T alone). Because
first-flow order is attacker-influenceable, it is also a timing lever distinct from padding.

**Reproduce.** `t53_ordering.py` (importable, `main()`); artifact `out/t53_ordering.json`; appendix
table `apptab:ordering`; body §sec:transfer + §method. Blind-codex verified (causality sound,
reporting switched to the sensitivity range).

## 4.52 Corrections from the third review round (record)

- **Restart FDR counterexample** (§4.35 / `appendix_proofs.tex`): the earlier wording ("each epoch
  rejects exactly one hypothesis, false w.p. q → pooled FDR 1−(1−q)^n") is wrong (that gives pooled
  FDR = q). Corrected construction: each epoch makes one false rejection w.p. q and no rejection
  otherwise → per-epoch FDR = q, pooled FDP = 1 whenever any epoch fires → FDR = 1−(1−q)^n. The
  body number 0.185 at four epochs is unchanged. Blind-codex verified.
- **Calibration CI** (§4.46 / `t50_calib_ci.py`): switched from an exact Poisson (Garwood) interval to
  the exact **Clopper–Pearson binomial** interval (the count is binomial); numerically ~identical, the
  conclusion (guarantee windows include 1, 0.85 excludes it) is unchanged.
- **Group-evidence validity** (§II-B): the assumption is reformulated to metadata-conditional per-flow
  validity E[e_i | M] ≤ 1 (M = pre-evidence grouping σ-field), a *sufficient* condition; a Lemma
  proves group-level *marginal* e-validity E[Ev(G_j)] ≤ 1 for random membership/arity, which is what
  e-LOND/online e-BH actually require (the p-value procedures need stronger, separate conditions).
  Separated from calibration-conditional (Bates) validity. Blind-codex verified.

## 4.53 Corrections from the fourth review round (record)

Second-pass audit of the §4.49–4.52 fixes. All blind-codex verified.

- **Synthetic ADDIS (§4.50 / `t52`) — precursors are now ALTERNATIVES, not nulls.** The rewrite had
  injected the precursors as *nulls* with p∈(λ,τ], which is the exact assumption violation it was
  meant to avoid, so the attacked stream was not guarantee-valid. Fix: label the precursors
  **alternatives** (non-null). ADDIS constrains only true-null p-values, so alternatives may take any
  value; the legitimate nulls stay U(0,1) and ADDIS's guarantee genuinely holds on the *attacked*
  stream. ADDIS decides on p-values alone, so the run (and B*) is unchanged; only the validity claim
  becomes sound. Codex also flagged B*=140 as a single-seed witness: over **300** guarantee-valid
  streams B* has **median 140, range 140–255** (the tail from a rare null false positive transiently
  restoring wealth), stable above B* on 300/300. Reported as a distribution.
- **Ordering (§4.51 / `t53`) — hash canonical, first-flow = upper bound.** Added a **50 random
  pre-committed order** ensemble: true detections median **1** (IQR 0–2, range 0–10) at 0.55 and
  **23.5** (IQR 20–29, range 0–44) at 0.85; first-flow (18/72) is the **largest over the audited
  orders** → reported as an optimistic *upper bound*, not canonical. Adopted a deterministic
  **metadata-hash** within-bucket order as the recommended canonical (evidence-independent *and* not
  attacker-timing-influenceable, closing the timing lever). Per-order median padding cost stays ~100
  flows at the guarantee window — a **survivorship-conditioned** estimand (zero-detection orders
  contribute none), not an invariant.
- **AIT suppression (§4.49 / `t54`) — empirical pad replay + host-conditioned end-to-end.** Replaced
  the zero-pad closed form with an **empirical replay**: real ordinary-to-victim flows drawn (with
  replacement, 200 draws) at their true 0-or-M evidence, appended until the group mean falls below
  1/level; a firing pad raises the cost. Flow-only: empirical median tracks the closed form, per-draw
  success **0.80–1.00** (santos 0.80, one episode unsuppressible). **Host-conditioned end-to-end**
  (Shaw + wilson): Shaw's ordinary-to-victim flows fire **7%**, so **no episode is suppressible**
  (host conditioning is a real defence there, consistent with its 0.05%→8.9% boundary shift); wilson
  still suppresses. Calibration confirmed chronological (in-org benign strictly precedes deployment).
- **Restart (§4.35)** — added the **preallocation composition**: with pre-committed q_i, Σq_i≤q,
  FDP_global ≤ Σ FDP_i ⇒ FDR_global ≤ q (no epoch independence needed). Budget reset = more power,
  per-epoch FDR; preallocation = deployment-wide FDR preserved, less power (E2b recall 0.195 vs E2c
  0.345). Codex-verified.
- **Presentation.** `\crefname` declarations added (the custom `assumption`/`lemma` theorem envs had
  no cref name, so pdflatex rendered `??`; tectonic already resolved them). Table III (`tab:procedures`)
  validity column → per-procedure required assumptions (no bare "valid"). "silent" defined as the
  structurally-infeasible-step fraction (not "never rejects"). Abstract calibration formula →
  generic kT/c−1 (6.5e8 level-w0, 3.3e8 LOND/e-LOND). "external NetFlow corpus" identified as the AIT
  `wilson` testbed. Grey-box state cost reconciled to **36×** (precursor count = flows; the 54× was
  ungrounded). e-GAI coverage narrowed to e-LORD (=e-SAFFRON λ=0); λ=0.1 not claimed. Victim-transfer
  claim softened (endpoint identity cannot affect the score; response-dependent transfer is empirical).



## 4.54 Corrections from the fifth review round (record)

Third-pass audit, on the §4.53 fixes. All blind-codex verified (four passes). Worklist
`docs/26_review5_worklist.md`. **Two measured results reversed; both reversals were caused by a
measurement artefact the review identified, not by new data.**

- **The "black-box" pad pool was not black-box (`t48`, `t49`).** It had been the modal
  `(proto,dport)` among **benign-labelled** flows (t48) or among **detector-non-firing** flows (t49);
  neither is available to a black-box attacker. Both now select on network-observable frequency
  alone: the modal service on the **training prefix** `[0, i1)`, which precedes both calibration and
  deployment — no labels, no detector output, no self-knowledge. It picks **UDP/53** at both windows,
  the pool is measured **0.0000%** attack-labelled (an audit, not a criterion), and **every
  downstream number is unchanged** (18/18 and 72/72 measured = closed form, medians 118 / 5,201.5).
  The rule matters: the modal service over *all* deployment-window traffic is **TCP/80** at 0.85, a
  pool **90% attack-labelled** — at a heavy-attack window the attacker's own flood is the mode.
- **REVERSAL 1 — the LSPR23 stress-window "graft fires 0.43, inconclusive-OOD" was an artefact.**
  That 0.43 came from the detector-non-firing pool rule, which at 0.85 selects TCP/80, a pool only
  **11.7% benign**. Grafting the attacker's own traffic onto attack context and seeing the detector
  fire is the detector working, not a defence. With the black-box pool the graft fires **0.0 at both
  windows**, the verdict is **holds** at both, and the cost is the exact flow-level closed form
  (r* = 108 vs 118 at 0.55; 11,484 vs 5,202 at 0.85). The two non-black-box rules are retained as a
  recorded `pool_sensitivity` (0.424 and 0.506, on pools 11.7% / 10.0% benign).
- **REVERSAL 2 — AIT Shaw is 3/3 suppressible, not 0/3 (`t54`).** The host arm held the six host
  features **fixed** while replaying pads, which for *causal* features (prior counts, distinct peers,
  failure fractions) is a static-context diagnostic, not a replay. Shaw's 6.97% pad firing is the
  rate of ordinary-to-victim flows **in their own contexts**; a pad is sent to the *attacked* pair and
  carries *its* context. Porting `t49`'s accumulation model (counts +(k−1), distinct-peer counts
  pinned, failure fractions to the pool rate; whole pool scored on a 60-point geometric grid; the
  k-th pad fires w.p. p_k), the same pool fires **0.0% at k=1 and ≤0.48% across accumulation**, so
  **3/3** Shaw episodes suppress at median **269**, and wilson 6/6 at 364.5. Codex caught that the
  first version returned the closed form past the evaluated cap; the curve now always extends past the
  needed cost and `causal_n_capped == 0` is asserted in the table generator.
  Also fixed: `t54` selected flow features from **all** orgs including the held-out one (a
  transductive leak); now per-fold from the training orgs, mirroring `t51`. Flow-arm numbers unchanged.
- **Assumption 1 had a conditional-probability hole.** `E[e_i | M] ≤ 1` against one *global* metadata
  σ-field does **not** imply `E[e_i | M'] ≤ 1` when the adversary enriches the stream's metadata
  (counterexample: `e = 2·1_A`, `Pr(A)=1/2`). Repaired with a **group-specific** `M_j` (that group's
  key, membership, arity, position hence γ_j, and T). Padding then leaves every true-null `M_j`
  *literally unchanged* — **but only under a key-determined order**: codex showed that under the
  shipped first-flow tie-break a pad placed early moves the attacked group and shifts other groups'
  γ_j. Measured in `t53`: one pad at the earliest instant of its own bucket moves **373** other
  episodes at 0.55 (3 at 0.85) under first-flow ordering, **0** under the key-hash. This is a second,
  *validity*, reason to adopt the key-hash order.
- **Ordering (`t53`).** The canonical hash now hashes the group's **own** `(SrcIP,DstIP,bucket)` key
  (splitmix64, collisions broken on the key), not the group *index*, which was only a function of the
  whole key set. Detections 3 / 34 (was 1 / 30 under the index hash). Added a **keyed** variant
  (0 / 24). Framing corrected: a *public* hash of attacker-chosen fields is a timing-independent
  **canonicalization, not a security mechanism** — it replaces timing grinding with metadata grinding;
  a pre-committed **keyed** hash is the grinding-resistant variant, at the price of a new
  threat-model assumption, and we do not analyse what the alert stream leaks about the seed.
- **Numerical/notation fixes.** `max_t t·γ_t = 0.0764` belonged to the **Javanmard–Montanari**
  sequence (a `t15` theory-check family the paper never runs), not to horizon-uniform γ, for which it
  is **1** and for which the asymptotic hypotheses do not hold at all — the pre-rejection level is the
  *constant* c₀/T, so feasibility is all-or-nothing. Generic cold-start coefficient **c₀** now used
  throughout (c₀ = w₀ for LORD++, α = 2w₀ for LOND/e-LOND), with `fig2` plotting both curves.
  ADDIS per-precursor cost is `⌊λ(|C|+1)/k⌋+1 = 453,279` (the reported value already was the rounded
  integer). "Finite resolution of **any** conformal procedure" narrowed to *deterministic rank-based*
  evidence, since §IV-D's smoothing removes the floor.
- **Statistical-standard fixes.** 0 firings in 20,000 is reported as **0 observed, one-sided 95%
  Clopper–Pearson upper bound 1.5×10⁻⁴**, not "confirmed". Fig 4C says **mean FDP = 0.047 ≤ q**
  (ADDIS controls FDR, not per-realisation FDP; the mixed arm's worst realisation is 0.104 > q, which
  the guarantee permits). AIT benign-to-victim firing restated as **13–71×** nominal on the seven orgs
  where it fires (the previous 11–68× was stale). "84 of 85" detections suppressible, not "all eight
  organisations".
- **Claims weakened where the evidence did not reach.** "A deployable layer **must** aggregate" →
  under uninterrupted deployment-wide control for the covered families, aggregation is the *direct
  route* to feasibility (online e-BH and preallocated restart are the alternatives). The Conclusion
  now distinguishes budget reset (forfeits the deployment-wide guarantee) from preallocation (keeps
  it, pays in power). Malicious-flow coverage is no longer "not a granularity effect" — it varies with
  **both** window and bucket (0.001→0.021 at 0.55, 0.301→0.995 at 0.85), so it is not a
  denominator-invariant resolution measure and the cost claim rests on blur.
- **`t41` traceability.** Every padding row in the operational-units table now names its procedure,
  threshold type (running vs static) and detected set, and a running-level e-LOND row (5,202 flows)
  was added so the table reconciles with the per-window padding table. The old "all 147 detections"
  row is labelled *mixed* (a static-threshold median × ADDIS's detected-set size).

## 4.55 Corrections from the sixth review round (record)

Worklist `docs/27_review6_worklist.md`. The round's headline is a **prior-art collision on C1**
(Huo et al., NeurIPS 2024 — see §6), plus two new measurements and a framing consolidation.

- **R4 — the padding attack is now priced under the CANONICAL within-bucket order too
  (`t48_W3_dilution.py`, new `episodes_keyhash` arm).** The headline detected set is the *first-flow*
  order's, which `t53` shows is the largest over the audited orders and which the paper itself
  recommends replacing (under first-flow one early pad moves 373 *other* hypotheses' spending
  weights, so the per-hypothesis `M_j` argument is airtight only under a key-determined order). The
  new arm re-runs the identical chain — same detector, same black-box pool, same pricing — on the
  detected set of the key-hash canonical order (splitmix64 of the group's own (SrcIP,DstIP,bucket)
  key, imported from `t53` so the two stages cannot drift). Result: **3 of 3 suppressible at 0.55**
  (individual costs **23, 24, 33**; median 24) and **34 of 34 at 0.85** (median **115.5**), measured
  = closed form on every one. The two independently written stages agree exactly (`t53` reports the
  same 24.0 / 115.5). The canonical costs are *lower* than first-flow's (24 vs 118) because the two
  orders detect different episodes at different steps of the level sequence — a descriptive
  conditional cost, **not** evidence that the canonical order is weaker. With n=3 at the primary
  window this is three individually priced attacks, not a rate.
- **R5 — metadata-stratified interrogation of Assumption 1 (`t55_a1_strata.py`, NEW).** The paper's
  only support for `E[e_i | M_j] ≤ 1` was the **marginal** benign firing rate, which at a guarantee
  window rests on 0–3 firing flows (0.55: ratio 1.07, CP [0.03, 5.96]). New stage: benign flows of
  **true-null** episodes (the population the assumption constrains — the dataset has 0 mixed
  episodes, verified), stratified on the observable components of `M_j` — **arity** bins (the
  quantity padding manipulates), **service** (proto,dport), equal-flow-count **time** strata,
  high-support **destination host** — read at rank depths k ∈ {1, 10, 100, 1000}. Strata membership
  comes from an **outcome-blind** rule (fixed bin edges, support-ranked top-N): not pre-registered
  identities, but selection that cannot have seen the result.
  - **Two sources of uncertainty, both resampled, jointly, and BOTH CLUSTERED.** The first version
    resampled only the test side and codex correctly called that CRITICAL: every rank in a window is
    computed against ONE realised calibration tail, so a low tail inflates every stratum together and
    no test-side resampling can see it. The shipped rule fires iff the score exceeds the **k-th
    largest calibration score**, so a window's whole diagnostic depends on `C` through one order
    statistic. A resample of `C` gives its order statistics Poisson(1) multiplicities — but codex's
    second pass caught that this assumes i.i.d. calibration *flows*, when they cluster exactly as
    deployment flows do. The resample is therefore over calibration **host pairs** (a pair drawn with
    multiplicity w contributes all its scores w times), taken over the top of the tail, one draw per
    replicate **shared across a window's strata**. Crossed with a Poisson-multiplier cluster
    bootstrap over deployment host pairs. Effect of the calibration-clustering fix alone: the primary
    window's marginal interval at k=100 went from [0.17, 3.47] to [0.15, 26.10]. Still unmodelled:
    the coupling from host pairs appearing in *both* the calibration and deployment windows.
  - **The contrast bootstrap was not actually paired** (codex pass 2, MAJOR). Weights were drawn with
    a shape set by each stratum's *local* present-cluster count, so the same seed gave different
    strata different weights for the same cluster. Weights are now drawn over the window's **global**
    cluster set, so column j means the same host pair in every call. The fix made the contrast
    *stronger*, not weaker (22 → 32 survivors), because the pairing now cancels shared noise as
    intended.
  - **The multiplicity family is EVERY cell** (codex pass 2, CRITICAL). Testability depends on the
    observed fire count, which is the same tail statistic that drives significance — so excluding
    untested cells from the BY denominator is selection on the outcome. Measured: it inflated the
    raw-ratio survivors 65 → 75 and the contrasts 15 → 22. Untested cells now enter at p = 1, which is
    conservative and correct (an untested cell can never reject).
  - **The p-value construction is forced by the correction.** The tests are dependent across strata,
    depths and windows, so BH is invalid and the headline is **Benjamini–Yekutieli**. But a
    percentile-bootstrap p-value floors at 1/(B+1), and BY over ~500 cells needs thresholds an order
    of magnitude lower — measured: it returned **exactly 0 survivors for that reason alone**, a
    measurement of `B` rather than of the evidence. So the bootstrap supplies the **standard error**
    (which is what it estimates well, and which carries both dependence sources) and the tail is read
    from a log-scale normal approximation. A cell firing **fewer than 10 times is not tested**.
  - **The time family was mislabelled** (codex pass 2, MAJOR). "Eight equal-flow-count strata" was
    false: a deployment window here spans a few hours and holds only 2–4 populated two-hour buckets,
    so any bucket-aligned partition into eight is degenerate. Since the bucket *is* the position
    determinant, the family is now **one stratum per bucket**, with the count reported per window.
  - **Result, reported in both directions.** 536 cells over 5 windows; **428 carry no test** (419
    firing fewer than 10 times) — itself the reviewer's point made precisely: at the depth the
    pipeline uses, the data mostly cannot speak. Of the 108 tested, 71 raw ≤ 0.05 (5.4 expected) and
    **40 survive BY over all 536 cells** (55 under the optimistic BH). By depth: k=1000: 26, k=10: 6,
    **k=1: 5**, k=100: 3. All five k=1 survivors are at **0.85**, the already-declared violation — so
    **at the four guarantee windows the diagnostic fails to reject Assumption 1 at the depth the
    pipeline reads**. Per-window BY: 0.55 → 6, 0.62 → 13, 0.70 → **0**, 0.77 → 5, 0.85 → 16.
  - **The load-bearing quantity is the CONTRAST**, a stratum against its OWN window's marginal on the
    same replicates — because a stratum can be anti-conservative merely because its whole window is,
    and because the shared calibration draw largely cancels in a ratio of two rates read at one
    threshold. **32 contrasts survive BY, at all five windows** (0.55 → 5, 0.62 → 9, 0.70 → 3,
    0.77 → 9, 0.85 → 6), including 0.70, which is clean on the raw ratio. Largest **lower bound**:
    arity `m=21–100` at 0.77, k=1000, **9.32 [6.48, 13.69]**, p = 2.3e-33. Largest **point estimate**:
    `proto 6/port 6444` at 0.62, k=10, 14.38 [5.38, 27.22]. The arity family carries 3 of the 32 —
    and arity is exactly the component of `M_j` the padding attack moves. (Report both statistics:
    codex caught the first draft calling the arity cell "the largest", which it is only on the lower
    bound.)
  - **What is still NOT resampled** (codex pass 3, MAJOR — accepted as a stated caveat, not fixed).
    Host-pair clustering absorbs within-pair dependence on both sides but **not a shock shared across
    many pairs at once**, and codex's own probe found a window's retained calibration tail
    concentrates in its 2–4 two-hour buckets, the largest holding **46–74%**. If those are time-block
    effects the intervals are still too narrow and the survivor counts inflated. Two-to-four blocks
    is too few to bootstrap over, so the honest move is a **sensitivity**: the `bucket` family is by
    construction aligned with that confounder, and dropping it leaves **25 of the 32 contrasts, still
    at all five windows**. A contrast is also a ratio of two rates read at ONE threshold in ONE
    window, in which a window-wide shock largely cancels. Also unmodelled: host pairs appearing in
    both the calibration and the deployment window.
  - **The "fails to reject" framing was too strong** (codex pass 3, MAJOR). With 428 of 536 cells
    untested, a k=1 non-rejection is an **inconclusive non-rejection**, not evidence for the
    assumption; the paper and the table caption now say exactly that. Also fixed: the caption said
    "40 strata" where the unit is stratum×depth **cells**, and per-position `n_tests` (which meant
    *cells in that window*) is renamed `n_cells` with `n_tested` added alongside.
  - **What this licenses.** A necessary implication tested where it is estimable, **not** a test of
    the assumption. `M_j` also carries membership and position; no finite sample identifies a
    conditional expectation; and a departure at k=1000 is compatible with a valid rank-1 rate (the
    excess may sit entirely in ranks 2..1000). Conclusion kept **under Assumption 1**; the diagnostic
    is *not* offered as support for it. Codex pass 3 verified all four earlier fixes are real and
    correctly implemented, and confirmed the 22 → 32 contrast rise is the expected direction for
    correcting a pairing bug (the old local remap added variance).
- **R1/R1b/R9 — prior work.** Huo et al. (NeurIPS 2024) cited and the C1 delta stated in two
  sentences in the intro and a paragraph in Related Work; Krönert et al. (arXiv 2312.01969)
  cited and distinguished (exact-level grid alignment for windowed BH vs feasibility over an
  uninterrupted horizon); Lu et al. (GAIF/OCTF) cited for the feedback claim; Zhang et al. (Byzantine
  multiple testing) added as the evidence-side contrast for C2. Five new `refs.bib` entries.
- **R2 — two contributions, not three.** The manuscript said "our three results" while also calling
  C2 "not a third independent result". Now: **C1 feasibility**, **C2 attackability**, with the
  granularity–resolution exchange rate as the explicitly labelled *bridge*. Old C3 → C2 throughout.
- **R3 — the escape→attack link is singular.** "the procedures escaping C1 condition their spending
  index on observed evidence" overstated §IV-D, which distinguishes ADDIS's selection-conditional
  index from online e-BH's history-wide fixed point. Now "one escape mechanism, exemplified by
  ADDIS…", with an explicit statement that the attack is **not** demonstrated against online e-BH.
- **R6 — feedback.** P, PI and AQT were never defined anywhere in the manuscript; they are now
  defined in `app:procedures` (including that `u` is a *calibration-quantile position*, not a raw
  score, and that the gains are chosen by grid search **on the realised test labels** — an ex-post
  oracle, so the reported controller performance is an *upper bound*, the conservative direction for
  the negative conclusion). The claim "analyst feedback is no substitute" is narrowed to these three
  threshold controllers under wall-clock delay, with GAIF/OCTF named as the principled construction.
- **R7 — terminology.** "atomic ground truth" → **"atomic evaluation reference"** (a chosen fixed
  fine-grained denominator; LSPR23 carries no campaign identifier, so it is not externally validated
  incident truth). The denominator-invariance argument is unchanged. 6 sites + 2 generators.
- **R8 — host-conditioning scope.** The Limitations line generalised past the covered setting; it now
  says the *particular* causal host-conditioning tested, on the two organisations and nine episodes
  replayed end-to-end, with the distinct-peer pinning and the absent flood regime named.

## 4.56 The UAI 2026 e-closure / compound-e procedures against the C1 horizon (`t56_uai26_procedures.py`) `[REAL]` / `[EXACT]`

Review round 7, item R1. **Xu, Fischer & Ramdas, *Improving online FDR procedures via online
analogs of e-closure and compound e-values*, UAI 2026 (arXiv 2603.24792v3, 8 Jul 2026)** give
procedures that *strictly improve* e-LOND and r-LOND while keeping SupFDR control under **arbitrary
dependence** — the exact setting our guarantee-bearing claims use. If they escaped
`thm:family1`/`thm:family2`, C1 would be scoped to superseded procedures. They do not.

Four arms implemented in `h6_procs.py`, unit-tested by `proto/t56b_uai26_selftest.py` (**172 checks**),
driven by `t56_uai26_procedures.py` over 5 positions × 2 seeds × 2 spending sequences = **20 rows**.

### Two new propositions, both blind-codex verified `[EXACT]`

- **A — donation e-LOND is inside `thm:family1`, and the constant is sharp.** Every summand of their
  wealth `Wbar_t` (their (26)–(27)) is `gamma_i` times a quantity capped at 1, so
  `Wbar_t <= sum(gamma) <= 1`: **the donation budget IS the spending budget**, which is why
  redistributing wealth cannot manufacture more of it. Hence
  `alpha_t <= d*gamma_t*Rn/(1 - d*Rn)` whenever `d*Rn < 1`. **Scope matters and is stated:** at cold
  start (`Rn = 1`) this is `d*gamma_t/(1-d)`, which is precisely what `cor:budget` needs since `c_0`
  is by definition the pre-first-rejection coefficient — so `c_0` moves `alpha -> alpha/(1-alpha)` and
  the required `|C|` shrinks by a factor `(1-alpha)`, i.e. **5% at alpha = 0.05**. After `Rn >= 1/d`
  rejections the bound is vacuous (the level can become unbounded); that regime **never occurs** here
  (`n_unbounded_level = 0` across all 20 rows), but the bound must never be quoted as all-time.
- **B — closed e-LOND needs a different argument, and it is tight here.** It is **not** covered by the
  letter of `thm:family1`: the `S = {}` candidate `d*gamma_1*Rn` in their (15) does not decay. But with
  `Z_t = #{i < t : E_i = 0}`, the zero-evidence indices form an admissible `S` with `D_t(S) = 1`, so
  **`alpha_t <= d*gamma_{Z_t+1}*Rn`** — e-LOND's decay with the time index rescaled by the non-firing
  fraction. Measured ratio `alpha_t / bound` is **exactly 1.000000 in all 20 rows** (attained, not
  merely bounded), with **99.5–99.8%** of episodes carrying exactly zero evidence.

### Three defects in the source, each pinned as a regression test

- **App. D.2 active set.** Printed as `A_t = {i <= t : d_i <= t}`, described in words as "deadlines
  have not yet passed". Only `d_i >= t` reproduces their own two limiting cases.
- **App. D.2 step-up range.** Printed upper limit `m_t` makes the range `{|R\A|, ..., m_t}` **empty**
  under immediate deadlines once `R >= 2`. Correct limit `|R\A| + m_t`. Under the literal cap the
  claimed e-LOND equivalence breaks at **17** steps of the 0.55 window (**103** under uniform gamma).
- **App. D.1 (102) is internally inconsistent, and we do not resolve it.** The per-step top-`r_t` sets
  are **not nested** — measured instance (`d=0.1, T=7, gamma=1/7`,
  `E=[6.899,78.075,73.067,98.354,66.194,58.858,7.758]`) rejects `{1..6}` at `t=6` and `{2..7}` at
  `t=7`, i.e. it **un-rejects**, contradicting the ARC premise. But the union is **not certified** by
  the balance the source proves control from — measured instance (`d=0.1, T=20, gamma=1/20`, the
  20-value stream in the self-test) has balance `+0.2929` at `r=|snapshot|=10` and **`-0.0412`** at
  `r=|union|=11`. Both readings are computed and reported; the **literal snapshot is the default**.
  **Nothing in the classification depends on the choice** — donation e-BH escapes through a
  history-wide fixed point either way, which is the only property C1 reads — so its rejection *count*
  is never quoted as a power comparison without naming the reading.

### What the improvements actually buy, at `gamma ∝ j^−1.6` `[REAL]`

| | extra true detections vs e-LOND, max over 20 rows |
|---|---|
| donation e-LOND | **+1** (0.85 only, both seeds) |
| closed e-LOND | **+0** anywhere |
| donation e-BH | +1 snapshot / +2 union (0.85 only) |
| e-TOAD(bucket), e-TOAD(arc) = online e-BH | **+19** (0.62 seed 0 only: 13 → 32); +1 at 0.70 s0; 0 elsewhere |

Realised cold-start donation boost **≤ 1.001246** against its own ceiling 1.052632; wealth used
**1.5–2.2 × 10⁻⁴** at the guarantee windows and 0.124 at the stress window, out of a budget of 1.
The mechanism has nothing to redistribute: at most **0.48%** of episodes in any window carry nonzero
evidence.

### The deadline is the axis that matters, and it is paid in latency, not feasibility `[REAL]`

`silent` here is **at-arrival infeasibility computed exactly** — the step-up is re-run on the
counterfactual in which the arriving hypothesis carries `E_t = CEIL` and nothing else is perturbed.
The cheaper test ("does CEIL clear `1/(d gamma_t r)` at the largest conceivable `r`") is only
*necessary*, because reaching `r` needs `r` hypotheses to clear the bar simultaneously.

- **Deferring the decision barely moves at-arrival feasibility.** At 0.55/0.77/0.85 the exact silence
  is **identical** at every deadline from immediate to ARC (e.g. 51,683 of 57,368 at 0.55); at 0.62 s0
  it moves 44,570 → 43,732 and at 0.70 s0 29,832 → 29,683 — **≤ 1.9%**. Deadlines verified applied:
  4 buckets, all members of a bucket share one deadline, median wait **7,170** hypotheses at 0.55.
- **So the escape works purely by revisiting**, which is exactly why its price is **alerting latency**:
  the alert cannot be issued when the hypothesis arrives.
- **New measurement, not a correction:** `run_online_ebh`'s `silent` is the necessary condition only
  and reports **0** at every window; the exact figure is **65.4–97.7%**, the same as e-LOND's. The
  paper has never quoted online e-BH's silence (`procmatrix.tex` reports only its rejections), so no
  published number changes.

### Cross-validation

e-LOND's exact silence fractions reproduce `apptab:detection` **exactly** (90.1 / 90.5 / 97.7 / 77.3 /
65.4%), and every shared arm reproduces `t21c_H6_positions.json` exactly (including 0.62 s0's
e-LOND 13 vs online e-BH 32). At **flow** granularity the `cor:budget` requirement is **≥ 20.0×** the
available `|C|` at every window — the `k/c_0 = 1/alpha` ratio, the same constant that governs the
group-calibration result of R2.

### One existing claim this narrows

`sec:escapes` says online e-BH "adds no power here (72 rejections, as e-LOND)". True at 0.85, but
`t21c` already shows **32 vs 13** at 0.62 seed 0. The sentence must name the window.

**Reproduce.** `t56_uai26_procedures.py` (importable, `main()`); artifact `out/t56_uai26.json`;
unit tests `proto/t56b_uai26_selftest.py`; source text kept at `proto/UAI2026_SOURCE_TEXT.txt`.
Three blind-codex passes; passes 1 and 2 each found a CRITICAL that changed reported numbers (the
final-snapshot ARC bug moved donation e-BH 73 → 74 at 0.85 s0; the necessary-condition silence test
overstated the deferral benefit).

## 4.57 Repairing Assumption 1 by construction, and what the repair costs (`t57_group_calibration.py`) `[REAL]`

Review round 7, item R2. The reviewer's constructive ask: build "at least one construction where
group-level validity is much closer to *by design* rather than assumed", predicting it "may lose
substantial power" and that this would itself strengthen the paper. We built it. **The answer is
worse for the alternative than the reviewer expected, and therefore better for the paper: every
route out of `assump:groupval` we can construct is worse than `assump:groupval`.**

The construction: stop **merging** per-flow e-values and run split conformal on the **grouped unit**,
with the identical `(SrcIP, DstIP, 2h bucket)` protocol applied to the calibration split. Two group
statistics, `max` and `mean` of member scores. 5 positions x 2 seeds; unit tests
`proto/t57b_groupcal_selftest.py`.

### 1. It DOES remove the assumption; what it leaves is fragile, not invalid `[REAL]` `[CORRECTED 2026-09-02, round 8]`

**This section previously said the repair "does not remove the assumption; it relocates it". That was
wrong, and the reviewer who challenged it was right.** Two corrections, both material:

**(a) The premise really is discharged.** Group-level conformal validity needs benign **test** groups
exchangeable with **calibration** groups, and nothing more. A statistic can be arbitrarily strongly
arity-dependent while calibration and null test groups remain perfectly exchangeable. Correlation
with arity is **not** evidence that exchangeability fails, so "arity-conditional group exchangeability
is `assump:groupval` one level up" does not follow and has been retracted.

**(b) The measurement is calibration-internal, and its marginal is arithmetically forced.**
`t57_group_calibration.py:314` computes `frac_in_top1pct = mean(v_cal[m] >= q99)` — it bins the
**calibration** set by arity and scores it against **that same set's** 99th percentile. No test group
enters. Summing the bins back gives a marginal rate of **exactly 1.000%** at every window and seed,
because the top 1% of a set is 1% of that set. The number therefore cannot bear on calibration/test
exchangeability even in principle. To make a genuine conditional-coverage claim the exceedance must be
measured on benign **test** groups against the calibration threshold — see the round-8 worklist item
R1b, not yet run.

Ranges corrected at the same time (all previously quoted as their most favourable cell —
`[[wrong-statistic-failure-mode]]`):

| statistic | rank corr. with arity (10 cells) | top-1% share, singletons | top-1% share, >1000 flows |
|---|---|---|---|
| **max** | **+0.233 to +0.413** (was "+0.35 to +0.41") | 0.26–0.44% | **3.6–15.3%** (was "9.09%") |
| mean | **−0.116 to +0.090** (was "+0.04 to +0.09"; the largest-magnitude cell is *negative*) | 0.00% | 1.2–1.9% |

**What survives, and it is enough.** Group exchangeability is still a *deployment* assumption, and it
is the one this paper's adversary attacks directly: padding enlarges groups and insertion creates
them, so under the threat model the test groups are adversarially constituted and exchangeability
fails **by construction**, not by correlation. The `max` statistic makes that acute, since the
threshold is a marginal quantile over an arity mix the adversary can shift.

**And the two facts are one fact.** Appending flows can only *raise* a maximum. That is why padding
cannot suppress under `max`, and why the arity dependence exists at all. The property that buys
padding robustness is the property that makes the arity mix load-bearing.

Repairing *that* by arity-stratified (Mondrian) calibration restores within-stratum exchangeability
and leaves cold-start windows of **2 to 52 steps** (was "2 to 48", which is the 0.55 row; the maximum
is 52 at 0.70).

**None of this is where the repair fails.** Grant it its validity premise entirely and it still cannot
alert — §2 below. That is the argument the paper now leads with.

### 2. Feasibility is destroyed, in closed form `[REAL]`

`|C|` falls from 1.81-2.45M **flows** to 36,944-57,093 **groups**, so the evidence ceiling falls
**40.1x-49.1x** (the flows-per-group ratio) with `T` unchanged. Margin `+0.067 -> -0.977`; no window is
feasible for e-LOND, whose threshold is margin `>= -0.5` (`eq:margin` is defined for a level-`w0`
procedure, e-LOND's cold-start coefficient is `alpha = 2w0`; both recorded).

| window | flow calibration | group calibration (max / mean) |
|---|---|---|
| 0.55 | 18 | **0 / 0** |
| 0.62 | 13, 12 | **0 / 0** |
| 0.70 | 30, 0 | 1 / 0, 0 / 0 |
| 0.77 | 31, 31 | 2 / 1, 1 / 1 |
| 0.85 (stress) | 72, 71 | 42 / 42 |

**Boundary, not bug — settled by closed form and by position.** The feasible-step count equals
`floor((alpha*CEIL*(R+1)/zeta(1.6))^(1/1.6))` on **all 20 arms** (verified against brute force over the
real gamma sequence for `CEIL` 1e3-1e6, `R` 0-200). At 0.55 the cold-start window is **81** steps and
the **first firing group sits at position 401** (mean: 374) — 110 groups fire, **none inside the
window**. Where fires do land inside it, rejections follow exactly: 0.70 has 1 -> 1 rejection, 0.77 has
2 -> 2, 0.85 has 13 -> 42 once the bootstrap stretches the window by `43^(1/1.6) = 10.5x` to 688 steps.
So the statistic's quality is not what produces the zeros. **0.85's 42 are not guarantee-bearing** —
that window's benign firing rate is already 51x nominal (§4.31).

### 3. The calendar price, and the law it decomposes into `[EXACT]` / `[REAL]`

The scale-free requirement is a **count** ratio `k/c_0 = 20`. The **calendar** requirement is that law
times the two windows' group-rate ratio (measured 0.42-2.35), giving **8.5x-47.0x** the deployment
span here — dataset-specific, and never to be quoted as the law. Identity verified in the artifact.

### 4. Limitations, each measured or named `[REAL]`

- **The exclusion of mixed calibration groups biases the calibration set.** Groups containing any
  attack flow are dropped; they hold up to **26.1%** of all calibration flows (an upper bound on the
  benign evidence discarded) and are **45.4x** the benign mean arity. Dropping high-arity groups
  left-shifts the tail and makes firing *easier* — the direction that would rescue the construction —
  and it still detects nothing at the guarantee windows, so the negative result survives its own bias.
- **Padding invariance is narrow.** It is invariance to *appending* to a *fixed* group. An adversary
  who instead **creates** groups can emit distinct keys ahead of a target and push it past a
  cold-start prefix these same numbers show is only tens of groups wide. Not priced here.
- **The comparison is not purely calibration granularity.** The baseline merges per-flow e-values;
  the group arm conformalises a raw group statistic. The *feasibility* conclusion is immune (it is
  arithmetic in `|C|`), and the first-fire positions show the statistic does not cause the zeros, but
  a fully like-for-like arm would need a two-way calibration split and is a different experiment.

**Reproduce.** `t57_group_calibration.py` (importable, `main()`); artifact
`out/t57_group_calibration.json`; unit tests `proto/t57b_groupcal_selftest.py`. **Two blind-codex
passes.** Pass 1 found two CRITICAL and six MAJOR, of which three changed numbers: an
**anti-conservative tie rule** (`stat >= kth largest` would have over-fired on 3 groups; replaced by
the `K_r = 1 + #{cal >= stat}` rank rule that `h_stream.evalues` uses), a **sign-reversed `r*`** that
reported every suppression cost as 1 pad (now the exact minimal ascending-pad prefix, median **8-28**,
up to 12,309 at 0.85), and an **ordering mismatch** with the baseline's tie-break. Pass 2 confirmed the
fixes, corrected `r*`'s equality case (equality at the threshold already stops firing, so the old form
charged one pad too many) and caught that the `r*` unit tests were **stale** — testing the old closed
form rather than the shipped code. The two decision rules are now nested functions the self-test
AST-lifts, so it drives shipped code rather than a restatement.

## 4.58 The canonical within-bucket order becomes the primary pipeline (`h_stream`, `t28b`, `t53`) `[REAL]`

Review round 7, item R3, answering the reviewer's third priority: *"the headline ordering is the
detector-favourable one."* Verdict on the objection: **valid, and the fix turns out to be the same
finding as C1.**

### 1. What changed in the code `[REAL]`

`h_stream` now OWNS the canonical order (`_mix64`, `key_hash`, `hashed_order`, `KEYED_SEED`) and
`build_episodes` takes `order="first-flow" | "keyhash" | "keyed"`. `t53_ordering` imports those
instead of defining its own copies and **asserts at run time** that its `canonical`/`keyed`
permutations equal what `build_episodes` returns, so the stage that MEASURES order sensitivity and
the stages that RUN under the canonical order cannot drift. `t48` continues to import them through
`t53`. Default stays `first-flow`, so no existing caller changed silently — verified: `t28b`'s
`table1`, `pools`, `fig4a_pools` and `fig4a_guarantee` are **byte-identical** to the pre-R3 artefact.

`t53` now covers **5 positions x 2 seeds** (it covered 0.55 and 0.85 at seed 0 only), and `t28b` —
the stage that produces `tab:main` — records `table1_by_order` for all three orders.

### 2. The result: the headline detections were the top of the distribution `[REAL]`

Seed 0, e-LOND, poly gamma, k=1, 2h host-pair grouping. Nothing differs between arms but the
sequence the controller sees; detector, calibration, e-values, grouping, ceiling and procedure are
identical.

| window | first-flow (shipped) | **key-hash (canonical)** | keyed hash | 50-order median (range) |
|---|---|---|---|---|
| 0.55 | 18 / 118 | **3 / 24** | 0 / -- | 1 (0-10) |
| 0.62 | 13 / 72 | **11 / 6** | 6 / 14.5 | 6 (0-11) |
| 0.70 | 30 / 1,851 | **0 / --** | 3 / 97 | 2.5 (0-12) |
| 0.77 | 31 / 1,165 | **0 / --** | 3 / 323 | 1 (0-6) |
| 0.85 | 72 / 5,202 | **34 / 116** | 24 / 160.5 | 23.5 (0-44) |

(detections / median pad against the running level). **First-flow strictly exceeds the 50-order
ensemble maximum at every window and seed where any order detects anything** (the sole exception is
0.70 seed 1, where nothing detects under any order and it ties at 0). The canonical order is an
ordinary draw from the ensemble, not its top: it sits at the ensemble maximum at 0.62 and below the
median at 0.70/0.77.

**Three stages agree on all 10 configurations through partly different code paths** — `t53`
(permutation applied to group arrays), `t28b` (`build_episodes(order=...)`), and `t48` (its own
`inv`-mapping at 0.55/0.85). `t48`'s pre-existing canonical costs 23/24/33 at 0.55 are reproduced
exactly by `t28b`'s new arm.

### 3. The zeros are the feasibility boundary, and that is the point `[REAL]`

Before its first rejection e-LOND offers exactly `alpha_t = A*gamma_t`, so **the run rejects nothing
IF AND ONLY IF no episode in the feasible prefix `t <= w_cold` clears `Ev >= 1/alpha_t`** — an exact
characterisation, not a necessary condition. `boundary_check()` asserts that biconditional on every
arm (60 arms: 10 configurations x 6 named orders); it holds everywhere, and `w_cold` matches the
closed form `floor((A*CEIL/zeta(1.6))^(1/1.6))` on every one.

| window | T | `w_cold` | prefix as % of stream | first clearing step, canonical |
|---|---|---|---|---|
| 0.55 | 57,368 | 902 | 1.6% | 686 |
| 0.62 | 49,267 | 902 | 1.8% | 90 |
| 0.70 | 37,231 | 865 | 2.3% | **none anywhere** |
| 0.77 | 31,672 | 824 | 2.6% | **none anywhere** |
| 0.85 | 31,568 | 748 | 2.4% | 240 |

At 0.70 and 0.77 the canonical order leaves **not one** episode clearing its own step anywhere in the
stream, which is why those entries are 0 and not a bug. `n_clearing_in_prefix == n_clearing_anywhere`
on all 60 arms, which is the evidence ceiling doing its job: nothing past `w_cold` can clear because
its evidence is capped at `(nCal+1)/k`.

**This is the unification.** Detection requires a near-ceiling episode to land in the first ~2% of
the stream. Under first-flow arrival that is exactly what live-fire attack traffic does — which is
*why* that order flattered the pipeline. Order the same episodes by their own metadata and the
lottery is honest. **Three detections out of 275 malicious episodes at the guarantee window is what
`cor:budget`'s 20x shortfall looks like from the detection side**: the ordering objection and the
feasibility theorem are one finding measured twice.

### 4. What it does to C2 `[REAL]`

C2 gets **stronger**, not weaker. Under the canonical order the suppression costs at the guarantee
window are the three individual values **23, 24, 33** flows (median 24, against 118 under first-flow);
at 0.62 the eleven costs have median **6**. The order changes *which* episodes survive to be attacked,
not whether they can be: across 50 pre-committed orders the per-order median stays at 109.5 / 16 / 93 /
175 / 98 flows. Every detection is suppressible under **both** orders (3/3 and 34/34 canonical, 18/18
and 72/72 first-flow, `t48`).

The abstract's "median ~100 flows" is the across-order figure and stands; the canonical-order figure
is *lower* and is now stated as such. **Caveat carried in the text:** the canonical medians at 0.55
and 0.62 are over n=3 and n=11 detections, so they are reported as individually-priced episodes
rather than as a rate.

### 5. The validity argument now describes the shipped order `[REAL]`

`assump:groupval` is stated per hypothesis against a group-specific metadata sigma-field `M_j`, so
padding must leave every OTHER group's position — hence its spending weight `gamma_j` — untouched.
Injecting one pad at the earliest instant of its own bucket moves **373 / 348 / 4 / 7 / 3** other
hypotheses under first-flow arrival, against **0** under the key-hash at every window and seed. That
argument was previously stated for an order the paper only *recommended*; it now describes the order
the paper *reports*.

The canonical order is also the more **seed**-stable: across detector seeds its count moves by at most
**3**, against **30** for first-flow arrival (0.70, where seed 1 collapses to 0).

### 6. What this does NOT change `[REAL]`

`T`, `nCal`, AUROC, the feasibility margin, malicious-episode counts, benign firing rates and every
calibration quantity are order-invariant by construction. Results that are a *contrast* between two
procedures on one stream (smoothing vs discrete, restart vs none, asymmetric vs symmetric weighting,
controller comparisons) compute both legs under the same order, so the order shifts the level and not
the sign; those remain on first-flow and the conventions paragraph now says so explicitly.

### 7. Blind-codex audit `[REAL]`

One pass, no CRITICAL, five findings, all acted on:

- **MAJOR (real bug).** `build_episodes` never validated key-array **lengths**. A length-1 field
  broadcasts silently through both `np.unique(return_inverse)` and the new per-group scatter
  `v[gid] = a`, so `keys=[np.array([7]), np.arange(N)]` was accepted and treated the first field as
  constant — a coarser partition AND a wrong recovered key for the hash order, with no error. Now
  rejected with the offending field's shape; three shapes regression-tested.
- **MAJOR (stale downstream).** `apptab:padpools` read `table1` — which is *deliberately* the
  first-flow record — and so reported 18/13/30/31/72 unlabelled after the primary flip. Part (a) now
  carries **both orders at both seeds**, explicitly labelled, and asserts its first-flow leg against
  `table1`. This is the failure mode the audit exists for: the artefact was right and the table
  reading it was stale.
- **MAJOR (claim scope).** "The slot is a function of its own metadata alone" was too strong: the
  *sort key* is, but a group's **absolute rank** depends on which other keys exist, so creating keys
  moves ranks even though appending flows does not.
- **MAJOR (claim scope).** The public hash is **grindable**, and the auditor priced it: at a feasible
  prefix of 1.6–2.6%, 100 candidate `(SrcIP,DstIP)` keys land one inside with probability 0.80–0.93 —
  and, the sharper direction for *our* threat model, a single draw lands **outside** it with
  probability >= 0.974, so grinding to *avoid* detection is nearly free. Now stated with the numbers.
  Also: `KEYED_SEED` is a **public constant** in the artifact, so the keyed arm is a reproducibility
  stand-in, not a deployed secret. Said so in the code and in non-claim 25.
- **MINOR.** "Upper bound" now reads "upper bound over the orders we audit" — we have no proof over
  all pre-committed orders.

Verdicts: keyhash correctly implemented and time-invariant **yes**; first-flow record unchanged
**yes**; the 0.70/0.77 zeros real rather than a bug **yes** (the auditor independently reproduced the
ensemble's zero rates, 7/50 at 0.70 and 21/50 at 0.77 against 1/50 at 0.85). On "would you trust these
as primary detection counts" it answered **not without the ensemble and the grinding caveat beside
them** — both of which the table and text now carry.

`out/t53_ordering.json`, `out/t28b_reallevel.json`.

## 4.59 An external semantic anchor for the alert-blur claim (`t58_semantic_blur.py`) `[REAL]`

Review round 7, item R4, answering the reviewer's seventh priority: the blur denominator is **our
own** 5-minute proxy for "one attack action", so the resolution exchange rate could be an artefact of
a unit we chose. LSPR23 ships a denominator nobody on this project chose — the red team's own task
record (288 tasks, 576 steps, **295 with a submission timestamp**, 2023-03-09 07:03–15:08 UTC).
`t31` uses only the step *times* and the compromise *IPs*; task identity, `Category`, `Phase` and
`Segments` were unused.

**Verdict after the blind audit: AGREEMENT IN DIRECTION, WITHOUT DISCRIMINATION — reported as such,
not as corroboration.** The external count rises with the alerting unit exactly as the proxy does, so
the resolution cost survives substituting an attacker-defined unit for ours. But a null that *rotates
the red-team timeline* against the stream reproduces the observed counts at **18 of 19** cells, so the
rise is driven by a wider bucket capturing more submissions rather than by alert-level
correspondence. The record can see the alerts at only 3 of 10 (window, order) cells, and the reason it
cannot see the rest is itself informative.

### 1. The link is corroborated, not assumed (and not *proven*) `[REAL]`

R4 anticipated having to derive and defend a segment→subnet mapping. That turned out to be
unnecessary and the truth is stronger: the dataset's own forensic columns carry per-flow
`seg_src`/`seg_dst`, and the red team's `Segments` vocabulary is **the same vocabulary with a
constant `bt_` prefix**. All six red-team segment names map; the stage aborts if any does not.

The map is then checked against a channel that does not use it. For each machine-readable compromise
report (83 reports, 39 IPv4, **36 appearing as a flow endpoint**), the dataset's modal segment for
that address is compared with its parent task's declared `Segments`: **83 agree, 0 disagree.**

**Audit correction:** this is a *consistency check, not independent verification* — the map is applied
(by stripping `bt_`) and then checked against the stripped names, and the 83 comparisons concentrate
on four segments (`baf_int` 26, `baf_dmz` 22, `beg_int` 18, `beg_dmz` 11) over 36 distinct IPs. A
wrong map would show disagreements, so it is a real smoke test; it is not proof, and the paper now
says "corroborated" rather than "verified".

### 2. The attribution rule (pre-committed) `[REAL]`

A timed step `s` of task `k` is attributed to issued alert `a` iff **(T)** `s`'s submission lies in
`a`'s bucket span, **and (S)** `k`'s segments meet the segments of `a`'s flows, or one of `k`'s
compromise IPs is an endpoint of `a`. Measured against bucket width — the `fig:granularity` x-axis —
for both within-bucket orders, with t47's 5-minute atom blur **recomputed on the same fired set** so
the two curves are comparable rather than merely adjacent.

### 3. Where it works, it tracks `[REAL]`

Within-window Spearman across bucket widths (pooling across windows is the wrong comparison — the
windows sit at different levels, which dilutes the correlation being tested):

| window / order | buckets | steps/alert vs atoms/alert | steps/alert vs bucket width |
|---|---|---|---|
| 0.70 first-flow | 6 | **+1.000** | +0.986 |
| 0.70 key-hash | 4 | +0.800 | +1.000 |
| 0.77 first-flow | 4 | +0.816 | +0.775 |

(Average-rank Spearman. This table first read **+1.000** at 0.77 — see §7: the shipped rank function
used `argsort(argsort(.))`, which hands tied values arbitrary distinct ranks and turned a flat series
(3.00, 3.15, 3.15, 3.15) into a perfectly monotone one.)

At 0.70 first-flow the external count runs 4.31 → 13.23 → 18.77 → 19.08 → 19.08 → 27.0 across
300 s…86400 s while the 5-minute proxy runs 1.00 → 3.51 → 6.51 → 13.0 → 13.0 → 28.33: **both rise
monotonically with the alerting unit.** That is what the reviewer asked for — the exchange rate is
not an artefact of the denominator.

### 4. Why it fails elsewhere, which is the more interesting half `[REAL]`

| cell | alerts overlapping the exercise in time | attributed | diagnosis |
|---|---|---|---|
| 0.55, 0.62 key-hash; 0.62 first-flow | **2%, 2%, 9%** | ~0 | **temporal — and it is C1.** Only a feasible prefix can reject, so issued alerts cluster in the *first minutes* of a deployment window (0.55: 02:24–02:32 of an 02:24–10:55 window). The exercise's first submission is 07:03. The controller and the red team are never in the same room. |
| 0.85 both orders | 37%, 48% | **0** | **spatial — reference sparsity.** Alerts do coincide in time, but only **2 of 17** tasks with a timed step in that window declare a segment or file a compromise report. |
| 0.70 both, 0.77 first-flow | 60–100% | 45–94 | usable |

The temporal failure is worth stating in the paper: **an external record can only corroborate an
alert it overlaps, and the feasibility boundary places the alerts where the record is silent.**

### 5. Four confounds, measured rather than declared `[REAL]`

- **(a) Two nulls.** R4 asked for neither, and they are the load-bearing guard. Segments are coarse
  (`beg_dmz` alone carries 5.5M of 16.4M flows), so a merge count could be pure density. The **label**
  null permutes which task each submission belongs to, holding times fixed — it asks whether *which*
  task acted is informative. Observed beats its 97.5th percentile at **6 of 19** cells, all at 0.70
  and sub-daily. The **shift** null (added after the audit) rotates the whole red-team timeline
  against the stream, preserving task identity, ordering, attributes and inter-arrival structure — it
  asks whether the alignment *in time* is informative. **Observed beats it at 1 of 19.** That is the
  finding that decides how this result may be reported: the rise in steps-per-alert is a wider bucket
  capturing more submissions, not alert-level correspondence. Multiplicity over the 19 nested cells is
  recorded (Binomial(19, 0.025) tail 5.0e-6 if they were independent, which they are not).

  At the 24 h bucket both nulls tie the observation exactly. **Audit correction to the stated reason:**
  it is *not* that the spatial conjunct goes vacuous — at 0.70/first-flow/86400 s the temporal arm sees
  30 alerts and the segment arm 12, so the filter is still biting. It is that every submission falls in
  **one** daily bucket, so neither permuting labels nor rotating times can move a step between alerts:
  the nulls are *degenerate* at that width.
- **(a2) Which conjunct does the work.** Across all rows: temporal-only 1617 alerts, segment-only 215,
  IP-only 28, attributed 215. **The compromise-IP conjunct adds no alert the segment conjunct did not
  already admit** — the entire positive result rests on six coarse segment labels. Unioning `seg_src`
  and `seg_dst` also matters for *how many* alerts attribute (union 215, source-side 45,
  destination-side 174, intersection 0), though per-alert counts are similar across the three.
- **(a3) Temporal extent sensitivity.** Re-pricing the identical rule against each episode's actual
  first-to-last **flow span** instead of its bucket span lowers magnitudes (0.70 key-hash 300 s:
  4.29 → 3.13; 3600 s: 18.50 → 12.00) and preserves every zero-window conclusion. Both are reported.
- **(b) Reporting lag.** A submission time is when the red team *reported*, not when it acted, so the
  localisation error is an upper bound. The compromise reports carry their own `Time`, so the lag is
  estimable: median **170 s** (IQR 115–279 s, max 15.5 h over 83 reports). The median inflation is
  therefore ~3 minutes, small against the bucket widths.
- **(c) Circularity — the one that bites.** `frac_attributed_on_benign == 0.0` **everywhere**: every
  attributed alert sits on a labelled-malicious episode, and the LSPR23 labels were themselves
  derived from this exercise. So the record gives **no label-independent evidence that an alert is a
  true positive** — that part would be circular and is not claimed. What it does give
  non-circularly is the **count of distinct attacker-defined actions inside the alert's cell**, which
  is a decomposition of the attack the labels do not contain.
- **(d) Coverage of the reference itself.** 295 of 576 steps are timed; **126 of the 155** tasks with
  a timed step are attributable at all. Per window: 59/69, 115/126, 65/74, 28/37 and **2/17**
  attributable.

### 6. Verification `[REAL]`

`proto/t58b_semanticblur_selftest.py`, **46 checks, 0 failures**: the shipped `attribute` against a
brute force written from the rule rather than the code (60 cases x 4 spatial variants); the four
variants nest (`seg`, `ip` <= `both` <= temporal-only, and `both` == `seg` OR `ip`); localisation
error <= bucket/2 by construction; `alert_attributes`' bucket index, segment set and endpoint pair
against a direct recompute; the null leaves the temporal structure untouched, and ties the
observation exactly when the spatial conjunct is vacuous; the record re-parsed independently
(288/295/576, the `bt_` strip is exactly a prefix strip, six segments); and the shipped `spearman`
against an independent rank correlation on tie-free *and* heavily tied inputs, with the exact 0.77
series pinned as a regression test.

### 7. Blind-codex audit `[REAL]`

One pass, **1 CRITICAL, 7 MAJOR, 2 MINOR**, all acted on. This is the roughest audit of the round and
it changed what the result is allowed to say.

- **CRITICAL (real bug, changed a reported number).** `spearman` ranked with
  `np.argsort(np.argsort(.))`, which assigns tied values arbitrary distinct ranks. The 0.77 series has
  ties in both legs, so it reported **+1.000** where average ranks give **+0.816** — a flat curve read
  as perfectly monotone. Fixed; the auditor's predicted 0.816 reproduces exactly. **My own self-test
  explicitly generated tie-free data**, which is why it sailed past. Ties are now 200 random cases plus
  the exact flagged series.
- **MAJOR (the finding that reframed the result).** The permutation null tested the wrong thing. A
  timeline-**shift** null is the right one, and observed beats it at **1 of 19** cells. The paper now
  reports agreement in direction *without* discrimination, rather than corroboration.
- **MAJOR (misexplained diagnostic).** The 24 h null tie was attributed to a vacuous spatial conjunct;
  it is actually null degeneracy under a single shared bucket. The wrong explanation had been *encoded
  as a passing self-test* — the worst version of this mistake. Both fixed, and the self-test now checks
  the distinction directly (one shared bucket ties even while the filter still bites; several buckets
  do not tie).
- **MAJOR ×4.** Attribution is entirely segment-driven (the IP conjunct adds nothing); the
  `seg_src`/`seg_dst` union changes the attributed-alert count 45/174 → 215; the segment map is a
  consistency check rather than independent verification; multiplicity over 19 nested cells was
  unhandled; bucket-span vs flow-span was an unreported sensitivity. All measured and carried.
- **MINOR.** A compromise IP appearing only as a *destination* would be silently unmatchable (0 do
  here; now counted and reported). No unit bug in the bucket algebra — the auditor traced
  microseconds→seconds end to end and confirmed the zeros are real.

Verdicts: attribution rule sound **no — too coarse for strong semantic attribution**; segment map
independently verified **no — a consistency check**; the zero windows explained by the stated cause
rather than a bug **yes**; usable as external corroboration **no — report as limited**. The paper now
says exactly that.

`out/t58_semantic_blur.json`.

## 4.60 Realistic-prevalence sensitivity (`t59_prevalence.py`) `[REAL]`

Review round 7, item R5, answering the reviewer's eighth priority: LSPR23's live-fire base rate is
far above an ordinary SOC's, so every number is measured in a regime no deployment inhabits. Measured
on the cache: **10.06% of flows** (1,644,599 / 16,353,511) and **0.48–0.81% of episodes**, against a
SOC's 10⁻⁴–10⁻⁶.

**Verdict: the objection is valid and the direction is favourable to the paper. Feasibility does not
move; detection collapses. Live-fire prevalence is the OPTIMISTIC case.**

### 1. What is thinned, and the confound that had to be removed first `[REAL]`

Malicious **episodes**, not flows: dropping flows would change group arity and evidence sums, the
exact channel attack surface A manipulates, and would confound C1 with C2. Draws are **nested** — one
permutation of the malicious episodes per (window, order, repeat), keeping its first `keep` — so a
lower target keeps a strict subset of a higher one, which is both the physical story and a paired
comparison across π. `keep = π(T−M)/(1−π)`, floored at **one** episode for any positive target (see
§5: rounding it to zero silently duplicated the pure-null arm).

**Two mechanisms, because they are not the same counterfactual.** The blind audit produced the
counterexample: *deleting* a hypothesis shortens the stream, so every later hypothesis shifts one step
earlier into a **higher** `alpha_t`, and a survivor that could not clear its own step can clear its
new one — lower prevalence can *help*. So the primary mechanism is **index-preserving**: the thinned
episode stays in the stream at its own index with evidence resampled from that window's own benign
episodes, holding `T`, the margin and every survivor's level **exactly** fixed. Deletion is kept as
the sensitivity arm.

**The two agree to within 0.02 in bootstrap probability**, so re-indexing is not what drives the
collapse.

### 2. Feasibility does not move; detection collapses `[REAL]`

Mean e-LOND rejections (50 draws), seed 0:

| window / order | observed | π=10⁻³ | π=10⁻⁴ | π=10⁻⁵ | P(ever rejects) at 10⁻⁴ |
|---|---|---|---|---|---|
| 0.55 key-hash | 3.0 | 0.54 | 0.06 | 0.02 | 4% |
| 0.55 first-flow | 18.0 | 1.40 | 0.08 | 0.00 | 6% |
| 0.62 key-hash | 11.0 | 0.18 | 0.02 | 0.02 | 2% |
| 0.62 first-flow | 13.0 | 1.36 | 0.20 | 0.04 | 18% |
| 0.70 first-flow | 30.0 | 3.52 | 0.38 | 0.10 | 28% |
| 0.77 first-flow | 31.0 | 2.22 | 0.06 | 0.04 | 6% |
| 0.85 key-hash | 34.0 | 0.48 | 0.02 | 0.00 | 2% |
| 0.85 first-flow | 72.0 | 8.28 | 0.54 | 0.28 | 40% |

(0.70 and 0.77 key-hash are 0 throughout — they already detect nothing at observed prevalence, §4.58.)

**Feasibility, meanwhile:** in the primary arm the margin shift is **exactly 0** by construction. In
the deletion arm `T` shrinks by at most **0.80%** and the margin *rises* by up to **+0.0129** — so
detection collapses *while feasibility improves*. That is the paper's feasibility-is-not-detection
separation driven by base rate alone, and it is a stronger version than the 0.70-seed-1 instance the
body already carries (which is driven by detector quality).

### 3. The escapes collapse too `[REAL]`

Online e-BH and e-TOAD (bucket-close deadlines) track e-LOND at every window: bootstrap probability at
π=10⁻⁴ is 0–40% for both, against e-LOND's 0–40%. If an escape had survived realistic prevalence while
e-LOND did not, that would be a different paper; it does not. (e-TOAD runs 20 draws against 50, so the
claim is directional, not precise.)

### 4. The pure-null arm, correctly scoped `[REAL]`

At π=0 (every malicious episode replaced) **no stream produces any rejection**, under e-LOND or online
e-BH. This is reported as **consistency, not a test**, for three reasons the audit made explicit: the
10 rows are 5 windows counted under 2 orders and the windows *overlap by construction*, so there are
at most **5** effective streams; **P(zero | true rate 4.5%) = 0.79**, so zero is the likely outcome
even if the body's simulated rate were exactly right; and the comparison is not like-for-like anyway
(the 4.5% is synthetic benign N(0,1) at a stated `|C|`, this is real benign episodes at `|C|` ≈ 1.8–2.4M,
and the simulated 2.2% is LORD++ rather than e-LOND). **The body's 4.5% survives as a scoped
simulation claim and is now labelled as one.**

### 5. Blind-codex audit `[REAL]`

One pass, **0 CRITICAL, 5 MAJOR, 4 MINOR**. It changed the experiment's design, not just its wording.

- **MAJOR (design).** Deletion re-indexes the stream and can *increase* detections — with a concrete
  counterexample. Added the index-preserving mechanism as primary and kept deletion as a sensitivity;
  they agree to 0.02.
- **MAJOR (real bug).** `keep_count` rounded targets below half an episode to **zero**, so several
  π=10⁻⁵ rows were silently duplicates of the pure-null arm — and my printed claim "0 everywhere at
  π=10⁻⁵" was contradicted by a row in my own artefact. Positive targets now keep ≥1 episode and
  overshoot rows are flagged and listed.
- **MAJOR ×2 (the null arm).** "0 of 10" is neither 10 independent trials nor powered to check 4.5%.
  Re-scoped as above, with the power stated in the artefact.
- **MAJOR (self-test asserted a false theorem).** "Thinning never increases true detections" is not a
  theorem; the test passed only because 30 random streams missed the case. Replaced by the auditor's
  counterexample as a **positive** test (deletion *does* increase detections there) plus the
  index-preserving invariant.
- **MINOR ×4.** Seeds omitted π and order (now nested and per-order, which also makes the π sweep a
  paired comparison); `fdp_mean` averages a 0 over silent repeats (conditional FDP now reported
  beside it); the 0.85 40% cell sits in the invalid stress window (labelled); e-TOAD's 20 draws make
  its collapse directional (said so).

`proto/t59b_prevalence_selftest.py`, **35 checks, 0 failures**, including cross-checks that the
observed arm reproduces `t28b`'s detection counts under both orders and that the cold-start windows
match `t53`'s window for window.

`out/t59_prevalence.json`.

## 4.61 Suppression by INSERTION: pricing the group-creation attack (`t60_positional.py`) `[REAL]`

Closes frozen non-claims **21** and **25(i)**, both of which conceded an unpriced lever, and settles
the R2d question *"if the max statistic turns out to be attackable by a different route, report that
instead and drop the trilemma to a two-way statement."* **It is attackable, and the trilemma is
dead.**

`thm:padding` and every cost in `sec:paddingcost` concern **appending** flows to a fixed hypothesis.
This attack appends nothing. It creates hypotheses **ahead of** the target and pushes it out of the
cold-start window, past which no rejection is possible and the state is absorbing.

### 1. Two attack models, kept apart `[REAL]`

The first blind-audit pass found these conflated, which was a CRITICAL and the most important
correction of the round.

- **TARGETED** — insert only immediately ahead of one target. Zero-evidence insertions there leave
  every earlier hypothesis, hence `R_p`, untouched, so the target simply moves to step `p+1+G` and
  fires iff `Ev[p] >= 1/(A*gamma_{p+1+G}*(R_p+1))`. **Closed form**, analytic:
  `G* = floor((A(R_p+1)Ev[p]/zeta(1.6))^(1/1.6)) - p`. Verified by replay (40 targets per cell,
  at `G*-1` and `G*`, zero failures).
- **PREFIX** — insert ahead of *every* hypothesis. This silences the whole window, and is **not** a
  per-episode cost: it also deletes the earlier detections that raised `R`, a channel unavailable to
  an attacker inserting only ahead of itself.

### 2. The result `[REAL]`

| | per EPISODE (targeted) | per WINDOW (prefix) |
|---|---|---|
| insertion | G* median **434–5,674** hypotheses | **217–813** hypotheses silences everything |
| padding | 6–5,202 flows | 80–786,257,264 flows (UPPER bound) |
| verdict | **padding cheaper at 12/12 cells** | **insertion cheaper at 10/12** (7/12 at 2 flows per group) |

So the honest statement is a split one: **insertion does not beat padding for suppressing one alert,
but it silences the entire controller for a few hundred hypotheses.** Ratio median 6x, max
1,058,220x — that maximum is heavy-tail driven (at 0.85 first-flow the top 10 of 72 pad costs carry
~100% of the sum) and both the total and the ratio are labelled UPPER bounds, since padding one
episode lowers `R` and can make later ones cheaper or vanish.

### 3. It breaks the group-MAX construction, which padding provably cannot `[REAL]`

The arm that closes non-claim 21. `t60` AST-lifts `t57`'s own `group_by_key` and `group_fires`, so it
attacks the same construction rather than a re-implementation (firing counts reproduce t57 exactly,
including the 42 detections at 0.85).

| window | firing groups | true detections | cold-start window | targeted G* median |
|---|---|---|---|---|
| 0.55, 0.62 | 110, 109 | **0** | 82, 84 | — (nothing to attack) |
| 0.70 | 69 | 1 | **86** | 81 |
| 0.77 | 60 | 2 | **78** | 76.5 |
| 0.85 | 152 | 42 | **65** | 207 |

The group-level calibration set is *groups*, not flows, so its ceiling — and with it the cold-start
window — collapses from 748–902 steps to **65–86**. Every group-MAX detection is suppressible by
inserting **62–295** hypotheses. **Group validity by design plus padding robustness does not buy
attack resistance; it buys resistance to one attack while making the other far cheaper.**

### 4. What getting ahead of the target costs `[REAL]`

Every detection lands in the **first bucket** of its window, so there is no earlier bucket to occupy
and the attacker must beat the target inside its own bucket.

- **first-flow order**: free — send earlier in the bucket.
- **public key-hash**: an offline search. Priced for the *right* event (audit pass 2): the targeted
  attack needs insertions in the interval between the last earlier rejection and the target, not
  merely anywhere below it. Medians **12,898 / 10,460 / 175,936** trials at 0.55 / 0.62 / 0.85 —
  against **5,675 / 627 / 2,741** for the wider prefix event, so pricing the wide event understates
  the search by up to 64x.
- **keyed hash**: no trial count is defined at all — the order cannot be ranked offline. The keyed
  arm is run, and the attack still works (24 detections at 0.85, silenced at G=518); what the keyed
  seed removes is the *search*, not the attack.

Three conditions are stated rather than hidden: the seed must be public for the search to exist; the
adversary needs that many endpoint pairs it can actually send between; and **the artefact hashes
pandas category codes, not raw IPs**, so introducing addresses would renumber them — the trial counts
are indicative of the search's *size*, not operational figures. A deployment hashing the raw address
has a stable value.

### 5. Blind-codex audit, two passes `[REAL]`

**Pass 1: 1 CRITICAL, 6 MAJOR.** The CRITICAL was the conflation above — I measured a prefix attack
and reported it as per-target suppression, overstating the per-episode cost by 3–8x in the
*attacker's* favour. Also: the group-MAX pipeline was advertised but not actually priced; the cost
comparison mixed hypotheses with flows; the keyed order was omitted; the category-code caveat was
missing; and the self-test's hand cases all collapsed to `G*=1`, so an implementation that suppressed
everything at any `G>0` would have passed.

**Pass 2: 5 MAJOR, 4 MINOR**, on the rework. The closed form silently **capped `G*` at `2T+3`** (now
analytic and unbounded, with a regression test for a target clearing 100x past the stream); the hash
search priced the **wrong event**; the keyed rows used **seed 0** for the hash fraction, contradicting
that arm's own point; the padding window total is an **upper** bound, not the joint cost; and — found
only because the auditor ran it — **the script crashed after writing its JSON** on a stale field
name, which I had missed by grepping the log for expected lines instead of checking the exit status.
It also noted the self-test never drove `targeted_gstar` directly, only through the artefact.

`proto/t60b_positional_selftest.py`, **56 checks, 0 failures**, including cross-checks against `t53`'s
cold-start windows, `t28b`'s detection counts and `t57`'s firing-group counts.

`out/t60_positional.json`.

## 4.62 Closing the paper-vs-artefact gap, and the content the paper was missing `[REAL]`

A completeness audit before the narrative rewrite, prompted by the question *"do we have everything
in main.tex, or is the rest just rephrasing?"* The answer was **no** on two counts, and one of them
was a harness gap rather than a writing gap.

### 1. The unguarded boundary, and the two errors it was hiding `[REAL]`

`t45_record_consistency.py` guards **docs/04 against out/*.json**. Nothing guarded the next boundary,
**main.tex against the artefacts** — and every number in the paper crosses it by hand. One error had survived every other check — and my first attempt at a second one was itself wrong:

- ~~`main.tex` claimed the per-order median padding cost "stays at 16–**178** flows". The artefact
  says 16–175; 178 appears in no JSON.~~ **THIS WAS WRONG, AND THE CORRECTION WAS THE ERROR.** 178.0
  is in the artefact, at position 0.77 **seed 1** — I read `t53_ordering.json`'s `positions` array,
  which is the seed-0 subset kept for backward compatibility, instead of `rows`, which carries both
  seeds. The paper's original 16–178 was the correct both-seed range. I changed it to the seed-0
  range, wrote a false statement into this record, and added a regression test asserting *"178 is
  gone from the paper"* — a guard that certified the very value it was meant to catch. Found by a
  verification agent reading the artefact properly. Now restored to 16–178 and explicitly labelled
  "across both detector seeds"; `t61` reads `rows` and checks that the sentence says which seeds it
  spans. **A partial view of an artefact is more dangerous than no view, because it looks like
  verification.**
- The body claimed every group-MAX detection falls to "$62$–**207**" insertions. **207 is the 0.85
  *median*; the max is 295.** Introduced when writing up §4.61.

The scripts passed, the self-tests passed, both codex audits passed, and `t45` passed 268 checks —
because none of them read `main.tex`. **`proto/t61_paper_consistency.py`** now does: 44 checks tying
quoted strings in `main.tex` to the values in `src/lib/out/*.json`. It caught the second error on its
first run. It fails both when a number *drifts* from its artefact and when a number is silently
*deleted* — the second being the failure a rewrite introduces.

### 2. Seven appendix tables were carrying first-flow counts unlabelled `[REAL]`

`apptab:detection`, `procmatrix`, `grouping`, `qsweep`, `transfer`, `w7coverage` and `groupcal` all
reported first-flow numbers with no order label while `tab:main`'s primary had become canonical
(§4.58). That is exactly the stale-table failure the R3 audit caught in `apptab:padpools` — the same
bug, six more times, because fixing the one the auditor named did not prompt a sweep for its siblings.
All seven now carry the label, and `t61` asserts it. Caveat C1's `\oracle` marker, missing from
`procmatrix` and `qsweep`, is restored.

### 3. Content that was genuinely absent, now written `[REAL]`

| item | was | now |
|---|---|---|
| **R1b** — the two UAI'26 bounds | body prose only; `appendix_proofs.tex` had **zero** theorem environments | `prop:donation` and `prop:closure`, with proofs, including the sharpness argument and the r-LOND transfer |
| **R2b** — the calibration-horizon ratio | prose at the end of `sec:groupcal`, unnamed | `cor:calhorizon` in `sec:feasibility`, named, with the scale-free/calendar split made explicit |
| **R2c** — Assumption 1's scope | only leg (1), scattered | all three legs stated together: the feasibility theorems need no distributional premise; `thm:padding` is an aggregation theorem; only the empirical FDR numbers carry the premise — and the construction that would discharge (3) is priced by (1) |
| non-claims 16, 18, 19, 25 | absent | four scope statements in `sec:nonclaims`, each travelling with its result |
| non-claims 27, 31–39 | table captions only, though the record marks them mandatory | in the body beside the numbers they qualify |
| caveat C10 | absent | two of the audit's four indicators are non-discriminative (100.0% vs 86.0%) |
| §4.57's mixed-group exclusion | absent | up to 26.1% of calibration flows, arity up to 45.4× the benign mean, bias direction stated |

### 4. Two numbers I wrote wrong while adding those caveats `[REAL]`

Both caught by `t61` before they reached a compile: the keyspace search quoted as "1.0–1.8×10⁵" when
the true range is **1.0×10⁴–1.8×10⁵**, and a garbled exclusion sentence that read as though the
construction discarded "45.4× the arity". The gate exists precisely because this is the class of
error that no experiment can catch.

State at the end of this pass: **44/44** paper-consistency, **268/268** record-consistency, five
self-tests at 0 failures, 0 broken references, 0 overfull boxes. Everything the record documents is
in `main.tex` or a table it inputs. What remains is narrative and length.

## 4.63 Full verification sweep of the paper before the rewrite `[REAL]`

Four agents, one per section of the body, checking **every** numeric claim against the artefacts,
`docs/04`, or a recomputation. ~350 claims checked. **Sixteen were wrong.** All are fixed and each is
now pinned in `proto/t61_paper_consistency.py` (**70 checks**).

### 1. The errors, by kind `[REAL]`

**A statistic presented as the wrong statistic (7 of 16).** This is the dominant failure mode and it
is worth naming: a mean, a median or a single-arm value written as though it were a range or an
extremum.

| was | is | what it actually was |
|---|---|---|
| src-host grouping collapses each window to 10³–1.6×10⁴ episodes | **763–24,043** | the endpoints were **means over (pos, seed) cells** |
| Mondrian strata leave a 2–**48** cold start | **2–52** | 48 is the 0.55 row; 52 is at 0.70 |
| e-LOND detections fall from **3**–72 | **0**–72 | the low end dropped the two all-zero rows the very next range in the same sentence included |
| static-τ median **33** flows at 0.85 | **34** | 33 is the *first-flow* value, in a paragraph reporting canonical |
| **99.8%** zero-evidence episodes | **99.5–99.8%** | top of a range |
| "the three controllers reach FDP 0.402" | 0.402 (P, PI), **0.523** (AQT) | two of three |
| **35** feasible groupings | **30** feasible (of 35 in the grid) | grid size, not feasible count |

**Plain factual errors (5).**
- "top three host pairs carry 74–86% of malicious traffic" → recomputed from the cache: **45–87%**.
- "five orders of magnitude below" → 37.51 / 2.1e-3 = 1.8e4, i.e. **four**.
- "15 of 33 features are backward or bidirectional" → **17** (10 `Bwd*` + 7 `Flow*`).
- "service-matched is 1.5–2× dearer" → **1.4–2.0×**.
- "`Category`, `Severity`, `SigID` carry a single constant code" → near-constant; one code covers
  **99.98%**, but SigID has 21 distinct values.

**Two things conflated (3).**
- Deferral "converts to power at **one** window" → **two** (0.62 *and* 0.70). The parenthetical listed
  the windows where nothing happens and omitted the one where something does.
- Contamination: "the margin rises (+0.436→+0.556) while detection goes to zero" → **two different
  sweeps**. In the sweep that destroys detection the margin does not move at all; +0.556 comes from a
  below-threshold injection that leaves all 72 detections standing.
- "four fifths of cells carry no test **at the shipped depth**" → 4/5 is the figure pooled over all
  four depths; at k=1 it is **129 of 134**.

**A self-contradiction (1).** "Four of five pools (generic, attacker-origin, protocol- **and
service-matched**, black-box) coincide … only service-matched is dearer" — the list named the pool the
same sentence excluded.

### 2. Two errors I introduced while *fixing* errors `[REAL]`

Both are more instructive than the originals.

- **The 178 "correction" was itself the error** (see §4.62, retracted in place). 178.0 is in the
  artefact at 0.77 **seed 1**; I read the seed-0 subset, "corrected" a right number to a wrong one,
  wrote a false statement into this record, and added a regression test asserting *"178 is gone from
  the paper"* — a guard enforcing my own mistake.
- **"No run leaves the cold-start prefix"** — written by me an hour earlier as a scope note on
  `prop:donation`, and false: three windows exceed 1/δ = 20 rejections (30, 31, **73**) and the
  realised boost reaches **1.83** against a cold-start ceiling of 1.05. The defensible claim is the
  weaker one the artefact supports: the denominator never *vanishes*, realised wealth staying at most
  0.12 of a budget of 1.

### 3. Two bugs in the checkers themselves `[REAL]`

- `t62_number_sweep.py` first reported **0 unmatched**, which was meaningless: **816 of the 999
  three-digit integers occur somewhere in the 19,212 artefact values**, so a wrong 3-digit number
  matches by coincidence ~80% of the time — it passed both known errors. Now scoped to the tokens
  where the test is sound (≥4 digits or ≥2 decimals: false-match 17%/2.2%/3.9%) and reports the rest
  as `weak` rather than pretending to have checked them. **424 strong, 284 weak, 12 unmatched, all 12
  adjudicated correct.**
- `t61`'s comparison helper stripped `,` before `{,}`, turning LaTeX's `24{,}043` into `24{}043`, so a
  correct number read as wrong.

### 4. Verified by construction `[REAL]`

- All **29 appendix tables regenerate byte-identically** from the current artefacts, so every number
  in the appendix is machine-derived.
- All **4 figures are pixel-identical** when rebuilt from today's artefacts.
- 91 labels / 82 cref targets / 44 citations: **zero dangling** in any direction.
- Dataset facts checked against the flow cache directly: 16,353,511 flows, 1,644,599 malicious,
  161.5 h, 1,630,732 empty `Expoid_dst`, 310 of 310 malicious host pairs 100% malicious.

**The lesson worth carrying:** of sixteen errors, seven were a statistic of the wrong *kind* rather
than a wrong *value* — a mean read as a range, a median as a maximum, one arm's number in another
arm's paragraph. Those survive every check that asks "does this number exist in the data", because it
does. Only asking "is this the number this sentence claims" finds them.

## 4.64 Round-8 review: statistical interpretation and theorem scope `[REAL]`

Round-8 reviewer feedback (2026-09-02), seven scientific points, **all seven valid** — triaged in
`docs/29_review8_worklist.md`. This entry records the writing-only pass; the two authorised
computations (R4 blind-key insertion, R5 canonical-order operational evaluation) and the cheap
recomputation (R1b test-side arity coverage) are **not yet run**.

### 1. Two live errors, not overstatements `[REAL]`

**(a) A contradiction inside the paper.** `main.tex` scope statement (i) said *"No run in our
measurements leaves that regime"* while `sec:escapes`, 700 lines earlier, said *"Runs here **do** pass
that count — 30, 31 and 73 rejections."* Round 7 fixed one of the two copies and missed the other.
The false sentence is gone; what replaces it is the weaker fact we can actually support — the
denominator never vanishes on these streams, donation wealth staying ≤ 0.12 of a budget of 1.

**(b) A second contradiction, six rounds old.** `sec:attack` said of a keyed hash *"the attack still
works. The keyed seed removes the search, not the attack."* `sec:transfer` said of the same mechanism
*"a channel we do not analyse."* Both were ours. The claim is now narrowed everywhere to what is
demonstrated: the insertion attack survives a **public** hash, which is grindable; under a keyed seed
the adversary must insert **blind**, and we make no claim about that channel until R4 measures it.

The sizing already in `t60_positional.json` says the outcome matters: `hash_fraction_below_target`
runs **u = 0.016–0.30** and `targeted_gstar` **G\* = 217–1099**, so a blind budget scales as `G*/u` ≈
**835–50,856 instantiated host pairs** against 217–1,099 with rank knowledge. A 10–60× multiplier,
heavy-tailed in 1/u — and unlike the public-hash search, every one of those keys is traffic the
adversary must actually send. A keyed canonicalization looks like a real *partial* mitigation for
targeted insertion while doing nothing whatever to Surface A padding.

### 2. The group-calibration interpretation was wrong `[REAL]`

See §4.57, corrected in place. Short version: the repair **does** discharge `assump:groupval`;
correlation with arity does not refute exchangeability; and the measurement backing the old claim was
calibration-internal with a marginal rate forced to exactly 1.000%. The section is now carried by
infeasibility — *grant the repair its validity premise, it still cannot alert* — which was always the
stronger argument.

### 3. Theorem scope `[REAL]`

- **`prop:donation`** now states what it proves: *donation cannot rescue a controller that fails to
  obtain its first rejection before the bounded-evidence cold-start horizon.* The categorical "the
  newest procedures do not escape" is narrowed to that, in `sec:escapes` and in Related Work.
- **`cor:closureabsorb`** is new. `prop:closure`'s bound is unconditional; the *conclusion* that the
  state is absorbing is not, and now carries its hypothesis — `Z_t → ∞` fast enough that
  `γ_{Z_t+1} → 0`, with the sufficient condition `liminf Z_t/t ≥ ρ > 0` giving `thm:family1`'s horizon
  rescaled to `ρT`. Our streams give **ρ ≥ 0.995**. The honest converse is stated too: where most
  hypotheses carry positive evidence the bound says little, which is the regime the closure was
  designed for.
- **`p̂` corrected in the appendix proof**: `≤ 2×10⁻³` → **`4.82×10⁻³`** (position 0.85; and exactly 0
  at 0.70 seed 1). The body's "at most 0.48%" was right; the appendix contradicted it.
- **Zero-evidence fraction**: "99.5–99.8%" → **"at least 99.5%"**. Over all ten cells the range is
  99.518–**100.000**% (0.70 seed 1 has no positive evidence at all), so the old upper end was wrong;
  a lower bound is both true and what the corollary needs.

### 4. Window terminology `[REAL]`

`t50_calib_ci.json` says the whole guarantee/stress split rests on **1, 1, 3, 2 and 46** benign
firings out of 1.6–2.3M. At 0.55 the exact Clopper–Pearson interval on the measured/nominal ratio is
**[0.027, 5.96]** — it excludes essentially nothing. Four windows are *not refuted*; only 0.85 is
refuted. Calling two of the four "guarantee-analysis windows" implied an empirical validation that
does not exist, and `docs/SaTML_2027_review_feedback.md:262` shows an *earlier* round asked us to
treat **four** positions that way, so the 2-of-4 split was drift.

New naming, applied at 24 sites in `main.tex` and 10 in `make_appendix_tables.py`:

| position | name | basis |
|---|---|---|
| 0.55 | **primary analysis window** | pre-committed at design time (`docs/03:56`), before any tail diagnostic existed |
| 0.62 | **replication window** | same |
| 0.70, 0.77 | analysis windows | not refuted, not distinguished |
| 0.85 | **known-invalid stress window** | ratio 50.9×, interval [37.3, 67.9], excludes 1 |

and the methodology paragraph now states plainly that **every guarantee-bearing statement, at every
window, is conditional on `assump:groupval`** — the names mark which stream carries which headline
number, not which stream has been validated. No post-hoc selection rule is invented, because there
was none.

### 5. Smaller corrections `[REAL]`

- **e-TOAD wording.** "We report the *corrected reading* of e-TOAD's construction" asserted that a
  weeks-old UAI paper is wrong. Replaced everywhere with: *we use the interpretation consistent with
  the stated limiting cases; the alternate literal interpretation is included as a sensitivity
  analysis and does not affect our conclusion.* The citation itself is sound —
  `proto/UAI2026_SOURCE_TEXT.txt` is the fetched arXiv HTML — only the adjudication was.
- **SOC prevalence.** `10⁻⁴–10⁻⁶` was stated as a fact about SOCs, uncited, at two sites; and the
  sweep does not even reach 10⁻⁶ (`PI_TARGETS` stop at 10⁻⁵ and 0). Both sites reframed as a swept
  parameter — *two to three orders below the exercise* — claiming nothing about any deployment.
- **The canonical order is not a typical draw.** `tab:main` called it "one draw from the 50-order
  ensemble". Seed 0: canonical 3/11/0/0/34 against ensemble medians 1/6/2.5/1/23.5 and maxima
  10/11/12/6/44 — **above the median at three windows, *at the maximum* at 0.62, below it at the two
  where nothing detects.** Now stated that way.

### 6. Gate state after the pass `[REAL]`

```
paper-consistency (main.tex <- artefacts):  81 consistent, 0 INCONSISTENT   (was 70; 11 new pins)
record-consistency (docs/04 <- artefacts): 268 consistent, 0 INCONSISTENT
number sweep:  12 UNMATCHED, all previously adjudicated correct
29 appendix tables regenerate; tectonic build: 0 overfull, 0 undefined refs
```

Three of the eleven new pins are **negative** — they assert a retired over-claim is *absent*
(`"No run in our measurements leaves that regime"`, `"The keyed seed removes the search, not the
attack"`, `"guarantee-analysis window"`). Existence checks cannot catch a claim that should not be
there; only an absence check can.

**Still open (compute):** R1b (test-side arity coverage), R4 (`t63` blind-key insertion), R5a/R5b
(canonical-order frontier and contamination base rates). §VIII still reports the first-flow operating
point — 18 alerts, recall 0.065 — against a canonical headline of 3, and that is the single largest
remaining inconsistency in the paper.


## 4.65 Round-8 compute: the three items the writing pass could not settle `[REAL]`

Three stages, all reviewer-authorised, all blind-audited (`[[blind-codex-review-workflow]]`).

### 1. `t64_frontier_canonical` -- the operational evaluation under the headline order `[REAL]`

Section VIII reported **18 alerts / recall 0.065** at 0.55 while `tab:main`'s headline said **3**. The
frontier itself is an ex-post threshold family, so it *ought* to be order-free -- but
`h_stream.frontier` breaks ties in the max score by `np.arange(T)`, i.e. by stream position, so this is
**measured, not assumed**. It is invariant at both positions; only the controller rows move.

| | first-flow | canonical | keyed |
|---|---|---|---|
| 0.55 e-LOND | 18 alerts, recall 0.065 | **3, 0.011** | 0, 0.000 |
| 0.85 e-LOND | 72, 0.282 | **34, 0.133** | 24, 0.094 |
| 0.55 zero-error frontier | 104 alerts, recall 0.378 | same | same |
| ratio, frontier / controller | 5.8x | **34.7x** | -- |

**The reviewer's prediction holds: the conclusion gets stronger.** The gap between what the ranking
admits at zero error and where the alpha-wealth process actually operates widens from ~6x to ~35x.

Two order-free rows survive as a free consistency check and did not move: the slot rule (an
expectation over slots) and the no-feedback threshold (it never updates). The "every method within
0.040 recall of the frontier" claim becomes **0.047**, the widest gap over all three orders.

**A robustness fact worth keeping.** t20 orders by `argsort(first_ts, mergesort)`; `build_episodes`
uses `lexsort((first_pos, first_ts))`. **The permutations differ** -- 326 episodes share a first
timestamp at 0.55, 206 at 0.85 -- yet all six methods agree to the last digit at both positions. The
tie-break convention is not load-bearing. This was checked rather than assumed precisely because a
silent disagreement between two conventions is how this project has shipped wrong numbers before.

### 2. `t63_blindkey` -- what a SECRET seed costs the insertion attacker `[REAL]`

The paper asserted "the keyed seed removes the search, not the attack" in one section and "a channel we
do not analyse" in another. Now measured. Under a secret seed the adversary cannot rank keys, so it
instantiates blind; the count landing ahead of a target is driven by that target's own hash quantile
`u`, which it also cannot see.

| result | value |
|---|---|
| targets that fall in **every** draw at 10^6 keys | **84 / 84** |
| public-hash cost `G*` (keys instantiated, search free) | **30--813** |
| blind cost `N99` (every trial is real traffic) | up to **3.4x10^4** |
| multiplier at **matched reliability** (`N99` vs certain) | **2.1--89x, median 19x** |
| target hash quantile `u` | 0.016--0.652 |

**The seed does not stop the attack; it changes the currency.** A public hash buys the ranking offline
for free. A keyed one forces every trial to be traffic between distinct endpoint pairs. So a keyed
canonicalization is a **genuine partial mitigation for targeted insertion** -- and it does nothing at
all to Surface A padding, which needs no key.

**Scope, measured not assumed:** the model places insertions in the target's own bucket, which is only
optimal because the target bucket is the **first of its window at every cell** (recorded, and a failure
is raised if not). Where an earlier bucket exists the adversary inserts there and precedes the target
with probability 1, and the seed buys nothing.

### 3. `t57` extension -- arity-conditional coverage, measured on TEST groups `[REAL]`

S4.57's original arity claim rested on a calibration-internal quantity whose marginal is exactly 1% by
construction (max deviation **8.9x10^-5** across ten cells -- confirmed, and it is the whole point).
Scoring benign **test** groups against the calibration threshold is the real question:

| statistic | marginal coverage | by arity stratum |
|---|---|---|
| **max** | 0.55--2.32x nominal | **0.13x -- 24.2x** |
| mean | -- | 0.00x -- 5.6x |

**Marginal validity is roughly right; arity-conditional validity is not, by up to 24x.** That is the
honest claim, it does not contradict exchangeability, and it is exactly the marginal-vs-conditional gap
an adversary who chooses arity exploits.

### 4. `t38` extension -- contamination under the headline order `[REAL]`

The first-flow arm is byte-identical (t45 unchanged at 268/0); the canonical arm is additive.

| | clean recall | one adversarial flow | random a=1 median | P(recall=0) |
|---|---|---|---|---|
| 0.55 canonical | 0.011 (3 rej) | **0.000** | 0.004 | 22.5% |
| 0.85 canonical | 0.133 (34 rej) | **0.000** | 0.035 | 32.25% |
| 0.55 first-flow | 0.065 (18) | 0.000 | 0.051 | 31.8% |
| 0.85 first-flow | 0.282 (72) | 0.000 | 0.192 | 0.0% |

The mechanism is order-free -- one flow above the calibration maximum kills every order -- but the
recall it destroys is not, and the *random* mislabel arm is markedly harsher under the canonical order.

### 5. What the blind audit caught, and what it cost `[REAL]`

The codex pass on t63 returned **five MAJOR and four MINOR** findings, two of which were wrong numbers
already in the artefact and three of which were claims the code did not support:

| finding | what was wrong | fix |
|---|---|---|
| **MAJOR** | `blind_over_public_ratio = N50 / G*` compares **50% blind success against certain public suppression** -- not a cost multiplier | headline ratio is now `N99 / G*`, matched reliability; the median moved **10.8x -> 19.3x** |
| **MAJOR** | "all 84 targets fall at 10^6" was inferred from `N50 is not None`, which only says 50% was reached *somewhere* | read off the last grid row: 84/84 at p = 1.000 |
| **MAJOR** | a 0-to-1 jump between grid points 3,000 and 10,000 was log-interpolated into "**N50 = 5,477**" -- four significant figures of pure interpolation | six points per decade; every N now carries the grid bracket, at most **1.48x** wide |
| **MAJOR** | all targets in a cell were costed using `targets[0]`'s bucket while `same_bucket` was merely *recorded* | enforced, and an earlier-bucket check added, because an earlier bucket makes the seed worthless |
| **MINOR** | the early stop at the first infeasible step is sound **only for non-decreasing shifts**, and `_front` shifted a prefix while leaving later same-bucket episodes in place -- not monotone, and not a realisable attack either | `_front` now shifts the whole bucket; `_elond_prefix` **raises** on a non-monotone shift; regression-tested |
| **MINOR** | 63-bit hashes cast to float64 -- a 53-bit mantissa, so the low 10 bits vanish and ties can appear that the integer lexsort building the order never saw | integer hashes and integer draws throughout |
| **MINOR** | the docstring said inserted hypotheses never firing was "verified, not assumed" while the code returned a **hard-coded zero** | it is a theorem (Ev=0 never clears 1/alpha_t); the docstring says so and the fake counter is gone |
| **MINOR** | printed "never falls below its binomial lower bound" while the summary showed **+0.023** | prints the shortfall against the Monte-Carlo SE: +0.030 at 1.2 SE, i.e. noise |

Two findings were adjudicated **unfounded** and I agree: the `_min_G` bisection is valid (suppression
is monotone in G under each placement), and the binomial's direction is right.

**The lesson matching S4.63's:** the two worst findings were not wrong arithmetic. `N50/G*` and "all 84
fall" were both *the wrong quantity for the claim* -- a 50%-success budget compared against certain
suppression, and a reachability claim read off the wrong field. Neither would fail a check that asks
whether the number exists in the artefact.

### 6. Gate state `[REAL]`

```
paper-consistency (main.tex <- artefacts): 110 consistent, 0 INCONSISTENT   (was 81)
record-consistency (docs/04 <- artefacts): 268 consistent, 0 INCONSISTENT
seven self-tests: 0 failures    (t56b, t57b, t58b, t59b, t60b, t63b, t64b)
30 appendix tables; tectonic: 0 overfull, 0 undefined refs; body ends p17
```


## 4.66 R5c (order labelling) and B (the statistic-kind gate) `[REAL]`

### 1. The labelling audit turned up one more recomputation `[REAL]`

The reviewer permits smoothing, restart, weighting, the sweeps and the feedback controllers to stay
under first-flow **as explicitly labelled paired analyses** -- both legs on the same stream, so the
order shifts the level an alert fires at, not the sign. Six sites now say so: smoothing/restart
(`main.tex:643`), the q/gamma sweep, the P/PI/AQT controllers, the host-detector contrast
(`2 against 18`), asymmetric weighting, and ADDIS's `5 of 31,313`. Each is pinned in `t61`, so a
rewrite that drops a label fails the gate.

**One site could not be labelled away, and recomputing it changed the result.** `sec:escapes` said
deferral *"converts to power at one window of the five --- 13->32 at 0.62 and 30->31 at 0.70"* --
self-contradictory on its face (it says one window, then names two), and both numbers first-flow. So
`t56_uai26_procedures` gained an order arm.

| | converts at | what it buys |
|---|---|---|
| first-flow | **2 of 10** cells: (0.62, s0) and (0.70, s0) | 13 -> 32, and 30 -> 31 |
| **canonical** | **1 of 10** cells: (0.85, s0) | **34 -> 35, i.e. +1** |

**Under the headline order, deferring to bucket close buys exactly one detection, at the window whose
evidence is not a valid e-value anyway.** That is a materially stronger C1 statement than the one the
paper was making. Two more numbers moved with it: at-arrival silence at the primary window is
**96.3%** canonically (90.1% first-flow), and donation/closure buy **+0 and +0** canonically against
+1 and +0 under first-flow.

**And a silent switch, caught by looking.** `t_uai26` builds its row dict keyed on position alone.
With two orders in `rows` that dict took **whichever came last** -- so `apptab:uai26` quietly became
canonical with a first-flow caption. The order is now selected explicitly with a length assertion.
This is the third time in two rounds that adding an arm to an existing stage silently changed a
downstream consumer; the pattern is worth naming.

### 2. The statistic-kind gate `[REAL]`

`t61.cell_num(label, values, tex_string, kind=...)` takes the quantity across **every cell it is
measured on**, not one of them, and the caller must declare what kind of statement the paper makes:

* `kind="point"` -- fails if the value **varies** across cells, and reports the real range. A maximum
  printed as a point value cannot survive this whatever number is printed.
* `kind="range"` -- **both** endpoints must appear in the quoted string. Showing only the favourable
  end is the commonest form of the error.
* `kind="cell"` -- the paper is deliberately quoting one cell and must name which.

Retrofitted onto 13 multi-cell quantities: both arity correlations, test-side coverage (conditional
and marginal), Mondrian cold start, the ceiling collapse, the benign-tail ratios and firing counts,
the cold-start prefix, the zero-evidence bound, public `G*`, the blind multiplier, and the widest
frontier gap.

**It found an error on its first run.** The benign firing counts behind the whole window split were
written as *"1, 1, 3, 2 and 46"* -- the **seed-0** values. Over all ten cells the range is **0 to
46**: two windows fire *nothing* at seed 1. Same shape as every other instance -- a real number from
a real cell, standing in for all of them.

**And the gate was tested against a failure it must catch, not just run.** Injecting the exact round-8
error -- the paper quoting `+0.41` (the maximum) with the existence check pointed at that same string,
so the old check passes -- makes `cell_num` fail with *"the string must carry BOTH endpoints +0.23 and
+0.41; quoting only one end is the failure mode this check exists for"*. A green result from a checker
that cannot fail is what made `t62`'s first version worthless (S4.63); the same test was applied here
before trusting it.

### 3. Gate state `[REAL]`

```
paper-consistency (main.tex <- artefacts): 141 consistent, 0 INCONSISTENT   (was 110)
record-consistency (docs/04 <- artefacts): 268 consistent, 0 INCONSISTENT
number sweep: 470 strong, 12 unmatched (all previously adjudicated)
seven self-tests: 0 failures; 30 tables; tectonic 0 overfull / 0 undefined; body p17
```

**Everything in the round-8 worklist is now closed except the author's manual narrative refit.**


## 4.67 Round-9 review: the order audit, and Corollary 8's exact form `[REAL]`

Five points, all valid. Two went further than the reviewer could see from the PDF.

### 1. The group-exchangeability overstatement had a third instance `[REAL]`

The reviewer's argument: split conformal on the grouped unit needs calibration and **true-null**
test groups to be exchangeable. Padding changes the **attacked** group, which is a **false null** --
the assumption says nothing about it, so padding is not evidence the assumption fails. Two sites
still asserted otherwise (`main.tex:277` "a group exchangeability that adaptive group formation
breaks"; `:1179` and `:1351` "relocates the premise onto arity").

**A third survived inside IX-B itself**, which the reviewer read as fixed: "under our threat model
the test groups are adversarially constituted and exchangeability fails by **construction**, not by
correlation." Same error class. Fixing pages 3 and 13 while leaving it would have left the paper
asserting in section IX exactly what it had just stopped asserting in sections II and X.

All four now carry the governing formulation: group-level calibration replaces Assumption 1 with
ordinary group exchangeability; arity heterogeneity shows that assumption may be fragile under
group-formation shift; **and even granting it completely the construction is infeasible**, which is
the half that does the work and needs no view on the premise at all.

One distinction is kept because it is real and in our favour: *insertion* does bear on true-null
groups -- the adversary instantiates ordinary endpoint pairs which enter the stream as nulls -- while
*padding* does not. That is stated as a reason for fragility, not as a proof of failure.

**No number moves.** This is entirely a claim-strength repair.

### 2. Corollary 8: the "exactly rho" step, and an exact form that costs nothing `[REAL]`

The old proof took `liminf_t Z_t/t >= rho`, derived `Z_t >= rho*t/2` eventually, and concluded the
horizon is "relaxed by **exactly** the factor rho". The displayed step gives rho/2; and the liminf
gives eventual domination *below* its value, never at it. The "exactly" did not follow.

The reviewer offered two repairs. **Both are done, because the exact one turned out to be free.**

**(i) Exact, finite-horizon, pathwise -- no density, no asymptotics.** Let
`P_T = #{i <= T : E_i > 0}` and `H = min{j : gamma_j < 1/(delta*CEIL)}` (Theorem 2's index horizon).
Of the `t-1` hypotheses before step `t` at most `P_T` carry positive evidence, so `Z_t >= t-1-P_T`
for every `t <= T` **by counting alone**. Hence `Z_t >= H-1` as soon as `t >= H + P_T`, i.e.

    t_closed := inf{t : Z_t >= H-1}  <=  H + P_T          (whenever H + P_T <= T)

An **additive** offset of `P_T`, not a multiplicative rescaling. Nothing is assumed about the stream.

**(ii) Asymptotic, corrected.** For every `rho' < liminf_t Z_t/t` there is a `t_1` with
`Z_t >= rho' t` beyond it, giving the horizon rescaled by `rho'` -- for every rho' below the liminf,
and explicitly *not* at rho itself.

**The empirical claim now attaches to a quantity the artefact already carried.** `P_T` is
`t56_uai26.json`'s `n_positive_evidence`, and it is order-invariant (a set property; `t61` asserts
that rather than assuming it):

| window | 0.55 | 0.62 | 0.70 | 0.77 | 0.85 |
|---|---|---|---|---|---|
| P_T (seed 0 / 1) | 110 / 104 | 109 / 110 | 69 / 0 | 60 / 59 | **152 / 152** |
| P_T / T | 0.19% | 0.22% | 0.19% | 0.19% | **0.48%** |

So the closure's horizon exceeds Theorem 2's by at most **152 hypotheses** on every cell measured.
This is strictly stronger than what it replaces: the old sentence was an asymptotic claim resting on
a density, quoted with an "exactly" the argument did not support.

### 3. IV-C's characterisation was universal; the propositions are not `[REAL]`

`main.tex:519` said the horizon binds "**exactly when**" a procedure's spending index advances on
every hypothesis. Theorem 2 leaves a third route -- escape by history-dependent level growth fast
enough to outrun gamma_t -- which neither ADDIS nor online e-BH takes. Narrowed to *among the
procedures studied here*, with the third route named so the gap is visible rather than papered over.

### 4. The order audit: sixteen sites, not the six visible from the PDF `[REAL]`

Ground truth, established by reading every task source rather than trusting the captions: exactly
**ten** artefacts carry an order arm (`t28b`, `t38`, `t48`, `t53`, `t56`, `t58`, `t59`, `t60`,
`t63`, `t64`). Every other task takes `h_stream.py:184`'s default `order="first-flow"` and **none of
them passes `order=`**. So any table sourced from any other artefact is first-flow, full stop.

The blanket convention at `main.tex:321` -- "every **detection count** is reported under the
**canonical** within-bucket order" -- was therefore false, and sixteen tables contradicted it.
Replaced with the reviewer's convention, which is both true and better: *headline absolute results
use canonical order; paired ablations and sensitivity analyses may use first-flow, but every such
table explicitly labels it as the optimistic upper-bound order.*

**The one factual error.** `apptab:units` row 1 called 5,202 flows over 72 detections "the headline
cost ... and the value quoted in `tab:main`". `tab:main`'s 0.85 row is canonical: **34 detections,
median 116 flows**. Both running-level budgets are now READ from `t28b_reallevel.json`'s by-order
arms instead of hard-coded, the canonical row is the headline, and the first-flow row is labelled as
the optimistic arm -- `45x` dearer, because that order detects more episodes and detects them deeper
into the level sequence where `1/alpha_t` is larger. The pre-existing artefact content is
byte-identical; the change is purely additive.

**Two unlabelled first-flow numbers in the body.** `main.tex:989` priced the state attack against
"a median 5,202 flows --- 2.1e-3 of the window's traffic, four orders of magnitude below", which is
first-flow. Canonical is 116 flows, `4.7e-5` of the window -- **almost six orders below**. The
unlabelled number was understating our own result by nearly two orders of magnitude. (The ratio is
derived in `t61` from the artefact now, both arms, rather than written by hand: I first wrote
`4.6e-5` from mental arithmetic and the artefact says `4.729e-5`.)

**`tab:pools` is now generated.** It was hand-written in `main.tex`, which is why it went stale, and
it now prints both order blocks from `t28b.pools_by_order`: canonical detects 11 at 0.62 (median 6
flows) and 34 at 0.85 (median 116); first-flow detects 13 and 72 (medians 72 and 5,202). Rounding is
half-up, not Python's banker's rounding, so `98.5 -> 99` and `5246.5 -> 5247` as the predecessor
reported. `mu` is asserted equal across arms rather than taken from one.

**Stale window names.** `t40`'s window key is literally `"guarantee (0.55)"` -- a round-7 casualty.
That is the **primary analysis window** now; the artefact key stays (it is data), the caption is
prose and was renamed. Figure 4 panel A called 0.62 "a guarantee window" and plotted the first-flow
costs; it is the **replication window**, and the panel title and caption now say which arm is
plotted and what the canonical arm gives.

**`apptab:prevalence`** had reverted to "against an ordinary SOC's 1e-4--1e-6" -- the uncited factual
claim round 8 removed from the body. Reframed as the swept sensitivity parameter it is.

### 5. The registry gate, and the two holes testing it exposed `[REAL]`

The failure here is structural: an experiment's default order is first-flow, a table is added, and
nothing forces the caption to say so. `t61` now carries an **order registry** mapping all 31
generated tables plus the three `main.tex`-embedded ones to a declared order, checking three
independent things:

1. the registry covers exactly what the generator emits -- a new table cannot ship undeclared;
2. the caption declares the order the registry claims;
3. **the declaration is reachable from the source artefact.** An artefact with no order arm cannot
   produce a canonical number, so declaring one is rejected however the caption is worded.

`order-invariant` is an allowed declaration but must carry a stated reason, and an empty reason
fails -- three tables qualify (`apptab:tail` and `apptab:a1strata` score benign *flows* against the
calibration threshold, with no controller and so no sequence to permute; `apptab:addissynth` is a
synthetic p-value stream).

**Tested against seven injected failures, not merely run green -- and two of them exposed real holes
in the gate itself:**

| injected | caught |
|---|---|
| strip a caption's first-flow label | yes |
| declare a first-flow table canonical (the `apptab:units` error) | yes |
| add a table with no registry entry | yes |
| registry names the wrong source artefact | **NO -- hole 1** |
| `order-invariant` with an empty reason | yes |
| reinstate "relaxed by exactly the factor rho" | yes |
| quote the `P_T` range as one endpoint | yes |

**Hole 1:** the artefact-name regex was `[a-z0-9_]+`, lowercase only. Stems like `t25_H5` and
`t21c_H6_positions` carry uppercase, so the map resolved **11 of 31** generators and silently
*skipped* the rest -- the registry could have named any artefact at all. Widened, and an entry the
map cannot resolve is now a **failure rather than a skip**, because a silent skip is exactly how the
hole got in. **Hole 2:** the map required `load()` on the line after the `def`, which a comment line
breaks (`t_frontier85`); it now scans the function body.

This is the same lesson as `t62`'s first version, which reported zero unmatched and was worthless.
A gate that has not been shown to fail is not evidence of anything.

### 6. The keyed-insertion cost is a capability, not a computation `[REAL]`

`N_99` reaches `3.15e4` distinct `(SrcIP,DstIP)` pairs the adversary must **actually be able to
originate traffic between**. The paper stated that condition for the *public*-hash cost but not for
the keyed result, where it bites hardest: on a network offering the attacker a few hundred reachable
pairs, a secret seed is not a partial mitigation but a hard stop. Stated in `sec:attack` and in
`apptab:blindkey`'s caption. No number moves; the scope of the existing numbers narrows.

### Verification

See section 7 below: the blind codex audit added six fixes after this point, so the final figures are
`t61` 260/0, `t45` 268/0, 15 self-tests, 31 tables byte-identical, build clean, body p17.

### 7. The blind codex audit: six findings, all guard strength `[REAL]`

Codex confirmed the mathematics and every printed number, and returned **5 MAJOR + 1 MINOR** --
none of them a wrong value, all of them guards that would not have fired. All six accepted and fixed,
and each re-tested against the concrete failure case codex constructed.

**Confirmed correct:** `t_pools` against `t28b` (canonical 11/34, first-flow 13/72, every median and
`mu` cell, half-up rounding at `98.5 -> 99` and `5246.5 -> 5247`, no silently dropped no-detection
cell); the corollary's counting bound, off-by-one, `t_closed <= H + P_T`, side condition and
absorbing conclusion; the asymptotic form and its refusal to claim `rho` itself; and the `P_T`
empirical claim (`0..152`, order arms agree in every cell, `152/31568 = 0.4815% -> 0.48%`).

| # | finding | fix |
|---|---|---|
| MAJOR 1 | `t41` trusted `table1_by_order[<key>]` but never read the record's own `order` field. A record filed under the wrong shelf would be labelled by the shelf; codex showed both existing guards would still pass. | the record must declare the order it is filed under, and its own `pos`/`seed` |
| MAJOR 2 | `_artefact_has_order_arm` was a **substring search** for `"keyhash"`. `t41_E8.json` matched on a prose provenance string I had written, so `units` passed reachability for the wrong reason. | structural detection only: a config `orders` list, a `canonical_order` string, a mapping keyed BY order name, records carrying `order`, or a top-level key *named* for an order (`t48`'s `episodes_keyhash` -- a third form the first structural version still missed) |
| MAJOR 3 | the embedded-table loop checked three `main.tex` tables; **`apptab:frontier` is a fourth**, order-bearing and unchecked. | `apptab:frontier` registered as `both`; and the list is now **asserted against the file** -- every `\label{tab:...}` in `main.tex` must appear in it, so a fifth embedded table cannot slip past |
| MAJOR 4 | a missing artefact set `SKIP` and every check reading it silently vanished, while the process still **exited 0**. | `sys.exit(1 if (BAD or SKIP) else 0)`, and the summary says the checks were *skipped, not passed* |
| MAJOR 5 | `order-invariant` required a reason **in the registry** but never made the caption tell the reader. A first-flow table with a bogus reason and no "canonical" would pass. | the caption must declare it; four captions gained the declaration (`apptab:tail`, `apptab:a1strata`, `apptab:addissynth`, `tab:terms`) |
| MINOR | `assert` is stripped by `python -O`, and the generator had seven. | the two load-bearing ones became explicit `SystemExit`; both scripts now **refuse to run under `-O`** at all, which covers the remaining five and any added later |

MAJOR 3 also turned up `tab:terms`, a fifth embedded table (a glossary) -- registered order-invariant
with the reason, since it carries no measurement.

**MAJOR 2 is the same mistake twice in one session.** The substring detector was written for the same
reason the lowercase-only regex was: a check that is easy to write rather than one that is hard to
fool. Both passed on the real data and would have passed on wrong data.

**Verification after the audit fixes:** `t61` **260**/0 (215 before round 9), `t45` 268/0, `t62` 470
strong with the same 12 previously-adjudicated tokens, **15 self-tests** 0 failures, 31 tables
byte-identical, build 0 overfull / 0 undefined references, body p17. `t41` re-runs from `t28b` and
its pre-round-9 content is byte-identical; the only change is additive.

Twelve injected failures now caught in total: the eight from the registry's own testing, plus the
five codex constructed (one overlapping).

## 4.68 Reviewer-style claim audit: 14 overclaims, all wording `[REAL]`

A pass over every strong sentence in the abstract, contributions, theorem statements, conclusion and
all 40 figure/table captions, asking one question: *does the theorem or experiment establish exactly
this wording?* Fourteen findings, **no number moved and no experiment was implicated** -- every one
was a result stated more broadly than its support.

### The two that a reviewer would have led with

**The abstract stated `cor:budget`'s special case as the general result.** Both the abstract and the
contributions gave the feasibility requirement as `|C| >= kT/c_0 - 1`. That holds only under
**horizon-uniform gamma**; the general form is `|C| >= k/alpha_T - 1`. And the omission cut *against*
us: horizon-uniform is max-min optimal, so it is the **cheapest** requirement -- the paper's own
horizon-free figure is `3.2e13`, not `6.5e8`. Both now state the general form first, name the
condition, and give the horizon-free comparison.

**Surface B's headline was an unqualified measurement on the known-invalid window.** The abstract and
contributions both said the attacker can "silence ADDIS permanently"; the real-stream demonstration
(`B = 203`) is at position 0.85, and `main.tex`'s verification sentence did not name the window
either. The defence already existed -- `apptab:addissynth` reproduces the mechanism on a synthetic
stream where ADDIS's guarantee genuinely holds -- but it arrived a page later and neither the
abstract nor the contributions mentioned it. All three sites now say the window is forced (ADDIS's
horizon escape and its guarantee-invalidity are the same property on two-point conformal evidence)
and point at the synthetic arm.

### The rest

| # | finding | repair |
|---|---|---|
| A2 | "Take **any** procedure whose level is multiplicative..." drops `thm:family1`'s `gamma_t t^d -> 0` -- which the body then denies two paragraphs later ("must be checked per procedure"; a quadratically-growing level "would escape") -- and merges in `thm:family2`, which needs *no* monotonicity | condition restored, families kept distinct |
| A3 | the abstract's "median `~10^2` flows" compresses eight per-window medians spanning **6 to 5,202** into a point | quoted as the range |
| A4 | "144 of 152 rejections survive a 100x over-estimate" is **one window (0.85, invalid) and one seed**, and compares a count against a bare factor | window, seed and all three procedures' actual behaviour stated |
| B1 | `fig:envelope`'s caption listed **online e-BH among the procedures "covered by"** `thm:family1`/`family2` -- e-BH is one of the two escapes | marked "plotted for comparison and **not** covered" |
| B2 | the abstract's padding blanket gave no signal that the pre-committed cap escapes by leaving the e-merging class | "family" + the escape named |
| B3 | "Evaluated on ... **two detectors**" -- the second appears only in the transfer test | rescoped |
| B4 | "at security scale" (abstract) vs "at LSPR23 scale" (body) for the identical number | "at this dataset's scale" |
| C1 | the conclusion's "a finite discovery horizon, **exceeded by a wide margin**" has no referent -- the horizon is not what is exceeded | says what exceeds what |
| C2 | "$12/12$ **windows**" -- there are five windows; the 12 are window x order **cells**, and the table states the same fact with **inverted polarity** ("0/12") | one polarity, correct noun |
| C3 | "the three windows that detect anything" -- the dearest of the three is 0.85 | named |
| C4 | `apptab:units`, `apptab:addisstate`, `apptab:audit` quote 0.85 with no invalidity qualifier | qualified, each explaining why the window is still the right one |
| C5 | abstract + conclusion carried **no** Assumption 1 conditionality -- which is how a PC triages | restated in the conclusion |
| C6 | `thm:reach` states a quantity and its bound in one breath | "the number `P` ... is *at most*" |

### Two corrections to the audit, found while fixing it

- **A4 was worse than "vague".** "against `2x` for LOND" implies LOND fails at `2x`. `t21d` says LOND
  keeps all 151 rejections at `2x` and **none** at `100x`; it is **LORD++** that fails already at
  `2x`. The audit called this a units mismatch; it was also a wrong attribution.
- **A3's correct range is 6--5,202**, the per-window median across audited orders -- not the
  median-of-medians (116.75) the old wording compressed.

### What the audit cleared

No theorem statement is wrong. **Alert blur is genuinely monotone** in bucket width at all five
windows (`t47_W7.json`, src-dst: 1.0 -> 20.4--38.5, no inversion), so "increasing" is exact.
Horizon-uniform gamma's max-min optimality is **proved** (`appendix_proofs.tex:83`), not asserted.
The round-9 order labelling survives: no caption claims an order its artefact cannot supply.

### Gating

All 14 repairs are pinned in `t61` under `ROUND 9 / CLAIM AUDIT`; **261 -> 288 checks**. Five reverts
injected and all five caught (A1, A2, A3, A5, C2). One pre-existing gate tested for the literal
`$12/12$` and had to be repointed -- it now derives the counts from `t60_positional.json` **and
asserts the denominator is called *cells*, not windows**, gating the noun because the noun was the bug.

**Verification:** `t61` **288**/0, `t45` 268/0, `t62` 470 strong / 12 previously-adjudicated, 15
self-tests 0 failures, 31 tables byte-identical, build 0 errors / 0 overfull / 0 undefined refs, body
still **p17**. Underfull (loose-line) warnings 14 -> 20 from the added qualifying clauses; cosmetic.

## 4.69 Round-10 reviewer feedback: ten items, four of them self-inflicted `[REAL]`

All ten valid on inspection. Again all wording, no number moved. **Four were introduced or preserved
by the round-9 and claim-audit passes** -- the passes that were themselves fixing overclaims.

### 1. The attack-cost convention was internally false `[REAL]`

`main.tex` stated, as a global convention, that *"every reported attack cost is an oracle lower
bound"*. Three shipped quantities contradict it:

| quantity | what it actually is |
|---|---|
| `r*` per-alert padding | oracle **lower** bound (uses the realised evidence sum and the unperturbed trajectory) |
| `L*` front-load (`tab:asym`) | **upper** bound, quoted at the unperturbed level |
| whole-detected-set padding totals (`apptab:insertion`) | **upper** bounds -- suppressing an early rejection lowers `R` |
| `G*`, `B*` | exact closed forms, replay-verified |
| `N_50/90/99` (keyed hash) | empirical **reliability budgets** over 400 draws -- neither bound nor oracle |

The convention now names each kind, and the limitations sentence *"Attack costs are lower bounds"*
narrows to the per-alert cost. The sentence also conflated **two independent qualifiers** -- "oracle"
(the attacker knows the level) and "lower bound" (minimality) -- now separated.

**The gate derives the contradiction rather than matching a string**: if the conventions paragraph
carries the blanket phrasing *and* any attack table reports an upper bound or a reliability budget,
it fails, naming the tables.

### 2. The asymmetry claim exceeded the theorems `[REAL]`

The intro said abandoning symmetry *"only makes the attack cheaper, not impossible"*. `thm:reach` and
`thm:frontload` cover **pre-committed position-indexed weight sequences with `sum w <= 1`**, not
arbitrary asymmetric e-merging. VI-D was already correctly scoped; only the intro over-reached. Now
scoped, with an explicit *"We do not claim this for asymmetric merging in general."*

### 3. The AIT upper-bound transfer -- MINE, from round 9 `[REAL]`

I wrote: *"the canonical order is not measured on this testbed, so these counts carry the same
upper-bound reading."* **That is a non-sequitur.** "First-flow is the optimistic order" is an
*empirical* property of LSPR23 (`t53`: first-flow exceeds all 50 ensemble maxima). It cannot transfer
to another dataset by assertion, and `t51`/`t54` carry no order arm at all.

Both AIT captions now say order sensitivity was **not audited** there, that the counts are neither
canonical nor an upper bound on that testbed, and that every rate is conditional on the detected set
this one order produces. The findings survive untouched: 84 of 85 detections suppressible, and all
nine replayed host-conditioned detections suppress.

The gate ties the concession to the artefacts -- it asserts `t51`/`t54` really have no order arm, so
if either gains one the caption goes stale loudly.

### 4. `apptab:groupcal` out-claimed its own body -- MINE, an incomplete sweep `[REAL]`

Round 9 repaired **four body sites** of the group-exchangeability overclaim and never swept the table
captions. `apptab:groupcal` still read *"group exchangeability is fragile under adaptive group
formation"* against IX-B's *"a reason the assumption may be fragile … not a proof that it fails"*.

This is the "when an audit finds a class of error, sweep the class" lesson already recorded in
`[[paper-vs-artefact-gate]]`, not applied.

### 5-8. Vocabulary and completeness `[REAL]`

- **"guarantee-window designations"** survived at IX-A, three rounds after the concept was retired.
  Gone; the gate now forbids the phrase `guarantee window` anywhere in the sources.
- **`apptab:audit` claimed to be "the diagnostic *of* that invalidity"** -- MINE, written one turn
  earlier in the claim-audit C4 fix. `apptab:tail` establishes invalidity (benign firing rate,
  interval excluding 1); `apptab:audit` is a *later* label-quality adjudication. Corrected, and it
  now points at `apptab:tail` explicitly.
- **"at security prevalence"** twice. The second was a mis-attribution, not tone: *"at security
  prevalence at most 0.48% of episodes carry any evidence"* -- 0.48% is a **measured fact about our
  streams**. Now "on our streams". The first becomes "at the `pi = 1e-4` low-prevalence sensitivity
  point", matching the round-8 prevalence-as-parameter framing. *"not a security stream"* becomes
  *"not the sparse-evidence regime studied here"*.
- **Three "strongest available/current/batched" claims.** A literature-completeness claim is defeated
  by one concurrent preprint and buys nothing; the technical comparison stands without it.

### 9. "across audited orders" -- MINE, from the claim-audit A3 fix `[REAL]`

The paper uses "the orders we audit" for the **50-order ensemble**; the `6`--`5,202` range is the two
reported arms. Now "across the two orders we report".

### 10. Submission hygiene `[REAL]`

- **Tense**: *"We release the complete set of artifacts"* beside *"Artifacts **will be** deposited
  within three days of submission"*. Now future-tense with an explicit statement that the artifacts
  exist and have been run in full at submission time.
- **The consent claim had no source.** *"an authorised cyber-defence exercise in which every
  participant consented to instrumentation"* -- I searched the whole record and there is nothing
  behind it. Replaced with what we can actually support: purpose-built ranges rather than production
  networks, reliance on the publishers' own ethical review and release terms, and an explicit
  statement that we did **not** conduct a separate consent audit and make no claim beyond those
  releases.

### The pattern

Four of ten were self-inflicted, and three of those are the *same shape* as the errors the round-9
and claim-audit passes were fixing: a qualifier attached where it was not earned. The numeric gates
cannot see this class -- they check that numbers match artefacts and that labels survive, not that a
newly written sentence is entitled to its adjective. **Every repair a review pass makes needs the
same audit as the text it repairs.**

### Gating and verification

Ten items pinned in `t61` under `ROUND 10 / REVIEWER FEEDBACK`; **288 -> 309 checks**. Ten reverts
injected, all ten caught.

`t61` 309/0 (exit 0), `t45` 268/0 (exit 0), `t62` 470 strong / 12 previously-adjudicated, 15
self-tests 0 failures, 31 tables byte-identical, build 0 errors / 0 overfull / 0 undefined
references, body still **p17**.

# 8. Reproduction

`t45_record_consistency.py` re-checks the load-bearing numbers **in this document** against
the JSON artefacts they were transcribed from, and `t61_paper_consistency.py` does the same for
**`paper/main.tex`** — a boundary nothing guarded until 2026-09-02, which is how two wrong numbers
reached the paper (S4.62). Run *both* after editing either. Run it after editing any figure here: the
scripts, self-tests and audits cannot catch a transcription error, and it has already caught
one fabricated table row. It reads `proto/out/`, so **copy new JSONs there** or its checks go
stale silently.

**Two environment traps, both of which have already produced a silently-wrong "pass":**

- **The venv has `nbclient` but not `nbconvert`.** `python -m jupyter nbconvert --execute ...`
  therefore prints its help text and **exits 0** without running a single cell, and a rebuild of
  `paper.ipynb` from `tools/build_notebook.py` ships it with *no* outputs. Execute with
  `proto/.venv/bin/python -m jupyter execute --inplace --timeout=1800 paper.ipynb`, then verify by
  reading the notebook JSON (`execution_count` non-null on every code cell, zero `output_type ==
  "error"`) rather than by trusting the exit code.
- **`src/lib/*.py` is generated from `proto/*.py`** by `src/tools/strip_comments.py --keep-doc`, and
  the experiment stages import the *shipped* copy. A fix made in `proto/` that is not regenerated
  never reaches `src/lib/out/*.json`. `proto/t56b_uai26_selftest.py` now regenerates the strip into
  a temporary file and diffs it, so this fails loudly instead of silently.

```
proto/.venv/bin/python  proto/t1_silence.py            # feasibility quantities, sparse-stream sim
proto/.venv/bin/python  proto/t2b.py                   # aggregation, dependence, MC-error guards
proto/.venv/bin/python  proto/t3_calvalidity.py        # calibration-conditional validity
proto/.venv/bin/python  proto/t4_real_calibration.py   # AIT drift measurement
proto/.venv/bin/python  proto/t6_gamma.py              # spending sequences and scale
proto/.venv/bin/python  proto/t7_dilution.py           # dilution, inflation control
proto/.venv/bin/python  proto/t8_split.py              # fragmentation control
proto/.venv/bin/python  proto/t9_threeway.py           # feasibility / robustness / floor
proto/.venv/bin/python  proto/t10_authoritative.py     # consolidated headline numbers
proto/.venv/bin/python  proto/t12_track2.py            # real detector, real attack
proto/.venv/bin/python  proto/t13_floor_crosscheck.py  # floor against real scores
proto/.venv/bin/python  proto/t14_T1_capvalidity.py    # cap-validity policy comparison
proto/.venv/bin/python  proto/t15_T3_theorem.py        # feasibility theorem + e-LOND check
proto/.venv/bin/python  proto/t16_T7_feedback.py      # analyst-feedback baseline
proto/.venv/bin/python  proto/t17_T2_fullstream.py    # full-stream, 5 positions x 2 seeds
proto/.venv/bin/python  proto/t18_T4_padding.py       # padding theorem + checks
proto/.venv/bin/python  proto/t19_T5_T6.py            # procedure comparison + attacker-origin padding
proto/.venv/bin/python  proto/t20_T8_matched.py       # matched operating points + frontier
proto/.venv/bin/python  proto/t21b_h6_selftest.py     # unit tests for the H6 procedures (no data)
proto/.venv/bin/python  proto/t21_H6_procedures.py    # SAFFRON/ADDIS/online e-BH/e-GAI, one window
proto/.venv/bin/python  proto/t21c_H6_positions.py    # the same over 5 positions x 2 seeds
proto/.venv/bin/python  proto/t21d_H6_horizon.py      # horizon misspecification sweep
proto/.venv/bin/python  proto/t21e_H6_frontier.py     # H6 configurations against the 4.19 frontier
proto/.venv/bin/python  proto/t21f_H6_scaling.py      # what the online e-BH escape costs (no data)
proto/.venv/bin/python  proto/t22a_stream_selftest.py  # regression test for the shared pipeline
proto/.venv/bin/python  proto/t22_H1_H2_matrix.py      # H1 second detector + H2 rank-k sweep
proto/.venv/bin/python  proto/t23_H7_bates.py          # H7 Bates calibration-conditional fix
proto/.venv/bin/python  proto/t24_H3_q_gamma.py        # H3 joint (q, gamma) sweep
proto/.venv/bin/python  proto/t25_H5_caps.py           # H5 cap-selection sweep
proto/.venv/bin/python  proto/t26_H4_grouping.py       # H4 grouping families
proto/.venv/bin/python  proto/t34a_E1_derivation.py    # E1 closed forms, 152 checks (no data)
proto/.venv/bin/python  proto/t34b_E1_selftest.py      # unit tests for the E1 machinery (no data)
proto/.venv/bin/python  proto/t34_E1_smoothed.py       # E1 smoothed / continuous evidence, ~62 min
proto/.venv/bin/python  proto/t35a_E2_derivation.py    # E2 closed forms, 201 checks (no data)
proto/.venv/bin/python  proto/t35_E2_restart.py        # E2 periodic restart / batching, ~2 min
proto/.venv/bin/python  proto/t36a_E3_derivation.py    # E3 closed forms, 115 checks (no data)
proto/.venv/bin/python  proto/t36b_E3_selftest.py      # unit tests for the E3 machinery (no data)
proto/.venv/bin/python  proto/t36_E3_asymmetric.py     # E3 precommitted weights + ordering, ~2 min
proto/.venv/bin/python  proto/t37_E5_a1gaps.py         # E5 A1 near-neighbour + per-feature, ~2 min
proto/.venv/bin/python  proto/t40_E7_controller.py     # E7 second controller + wall-clock delay, ~2 min
proto/.venv/bin/python  proto/t32a_E11_derivation.py   # E11 closed forms, 40 checks (no data)
proto/.venv/bin/python  proto/t32b_E11_selftest.py     # unit tests for the E11 export (no data)
proto/.venv/bin/python  proto/t38a_E4_derivation.py    # E4 closed forms, 32 checks (no data)
proto/.venv/bin/python  proto/t38_E4_contamination.py  # E4 calibration contamination, ~20 min
proto/.venv/bin/python  proto/t26_H4_grouping.py --five  # E6 prerequisite: 5 positions, ~5 min
proto/.venv/bin/python  proto/t39a_E6_derivation.py    # E6 design rules, 29 checks (no data)
proto/.venv/bin/python  proto/t39_E6_transfer.py       # E6 cross-window transfer, ~2 s (reads JSON)
proto/.venv/bin/python  proto/t39b_E6_selftest.py      # unit tests for the E6 selection (no data)
proto/.venv/bin/python  proto/t38b_E4_selftest.py      # unit tests for the E4 machinery (no data)
proto/.venv/bin/python  proto/t41a_E8_derivation.py    # E8 unit recovery + cost models, 25 checks (no data)
proto/.venv/bin/python  proto/t41_E8_units.py          # E8 operational units, ~6 s
proto/.venv/bin/python  proto/t42a_E9_derivation.py    # E9 tie-block algebra, 17 checks (no data)
proto/.venv/bin/python  proto/t42_E9_ties.py           # E9 timestamp-tie sensitivity, ~2 min
proto/.venv/bin/python  proto/t43_E10_xwindow_padding.py  # E10 padding at 5 windows, ~4 min
proto/.venv/bin/python  proto/t46_hostpair_padding.py  # can pads reach the target's host pair, ~3 min
proto/.venv/bin/python  proto/t45_record_consistency.py # THIS document's numbers vs out/*.json
proto/.venv/bin/python  proto/t27_H8_labelnoise.py     # H8 label noise + FDP interval
proto/.venv/bin/python  proto/t28_P5_padding.py        # padding pools, problem-space variants
proto/.venv/bin/python  proto/t29_compound_e.py        # boosting / compound-e (no data for parts 1-2)
proto/.venv/bin/python  proto/t30_A1_tailforensics.py   # A1 position-0.85 extreme-tail forensics
proto/.venv/bin/python  proto/t31_A2_alertaudit.py      # A2 adjudicated alert audit vs the red-team record
proto/.venv/bin/python  proto/t32_B1_addis_state.py     # B1 ADDIS spending-state manipulation attack
proto/.venv/bin/python  proto/t33_selftest_A1A2B1.py    # unit tests for A1/A2/B1 (no data)

Shared modules: `proto/h_stream.py` (stream construction; regression-tested by
`t22a_stream_selftest.py` against the numbers in §4.17, §4.19 and §4.20),
`proto/h6_procs.py` (online procedures; unit-tested by `proto/t21b_h6_selftest.py`) and
`proto/h_meta.py` (the raw csv's annotation columns — IPs, ports, service, connection state,
network segment — re-ordered into h_stream's timestamp-sorted row order; §4.31 and §4.32
depend on that alignment, so `h_meta.verify()` checks it on all 16,353,511 rows against the
ports h_stream extracted in a separate independent pass, and raises rather than warning).
It needs one extra extraction, run once from `proto/data/lspr23/`:

```bash
awk -F',' 'NR>1 {print $2","$3","$4","$5","$89","$91","$92","$93","$94","$96","$97","$98","$99}' \
    ls23pr_v1.csv > /tmp/lspr_meta.csv
```
A `.npy` cache of the parsed flow columns is kept in `/tmp/lspr_cache` and rebuilt
automatically; the service-based grouping additionally needs `/tmp/lspr_ports.csv`,
produced by `awk -F',' 'NR>1 {print $4","$5}' ls23pr_v1.csv > /tmp/lspr_ports.csv`.
```

Data fetch: `proto/fetch.sh`. LSPR23 must be unzipped to `proto/data/lspr23/` and sorted by
timestamp before any streaming use.

## 4.70 Round-25 compute: the joint attacked-trajectory rerun (`t75_joint_rerun`) `[REAL]`

**Why.** Every suppression number in the paper is *per alert*: each detected episode is padded alone and
judged against the level it received on the unperturbed trajectory (t48, t74). The round-25 reviewer
read the abstract's "suppresses all 212" as one end-to-end attack run anyway and named a joint rerun
"the single highest-value additional experiment". This stage pads and then **re-runs e-LOND over the
padded stream**, so the controller's own state (its rejection count `R`, hence every later level
`alpha_t = alpha*gamma_t*(R+1)`) responds to the attack. Run 6 Sep 2026. Code: three blind audit rounds,
two independent codex runs each (`[[blind-codex-review-workflow]]`), stopped when findings changed kind
from construction to labelling. Write-up: one further blind round (two runs) on this section, which
found a mislabelled statistic and two overstated mechanisms; this is the corrected text.

**Scope, stated once.** LSPR23 positions 0.55 and 0.62, detector seed 0, two-hour src--dst episodes,
e-LOND with the arithmetic-mean merger, canonical order (first-flow as a labelled sensitivity),
horizon-free `poly` and horizon-aware `uniform` spending. Pads carry **zero evidence**: the black-box pool
has no firing flow at either window (t48/t74 measured this on the shipped detector; t75 asserts it), so
the STATIC arm's 200 pool draws are degenerate and the run is a zero-evidence rerun, not a second
real-flow replay. The oracle attackers know which of *their own* episodes would fire and the live level
(the same knowledge the paper's `r*` already assumes); the state-free attacker knows only its own arity.
Nothing below is claimed for other seeds, windows, controllers, mergers or datasets.

**Design.** Same detector, e-values and `r*` formula as t73/t74; `run_lond` is the only procedure code.
Control: the unperturbed canonical arms must reproduce t73's cells exactly (3/80, 105/627,495, 11/926,
107/977,567) — asserted. Attackers, kept apart by what they know:

* **STATIC** — per-alert oracle pads `r*_j` from the unperturbed run, applied to every true detection at
  once, controller re-run.
* **ADAPTIVE** — greedy sequential oracle: walks the stream and pads each of its own episodes that *would*
  fire at the **live attacked-trajectory level** by the minimum. Its total is the cost of "suppress the
  whole campaign" for *this* attacker on *this* fixed stream; it is not a global minimum over strategies.
* **STATE-FREE** — multiplier `c` on *every* malicious episode (the attacker does not know which will
  alert), `c in {2,3,5,10,100}`; plus the closed-form boundary `c_crit = max_j Ev_j*alpha*gamma_{t_j}`
  (R = 0 throughout), verified just above and below, and at the realisable integer `c_int = floor(c_crit)+1`.
* **CAPPED ADAPTIVE** — the sequential attacker against t74's volume caps {30, 100, 300, 1,000, 3,000,
  10,000}: it pads only if `m + r <= cap`, otherwise the alert fires and raises `R`. Each alert the cap lets
  through is classified **structural** (its pad would not fit even at the cold-start level R = 0) or a
  **cascade victim** (it would have fitted at R = 0 and fires only because earlier alerts raised R). The
  cap grid is sampled; nothing is claimed between grid points.

**The stream permutation is checked, not assumed.** Every attacker overwrites the ordered episode
vector, which is legitimate only if appending the pads as *flows* and regrouping gives the same
permutation and evidence. `check_padded_stream` builds the padded flow stream (target's (src,dst), the
target's *last* timestamp, stable re-sort by time so every pad follows every original flow of its
target), regroups with `h_stream.build_episodes` under the same order, and asserts equal episode count,
equal (src,dst,bucket) key at every position, arities `m + r`, unchanged labels, unchanged first
timestamps and equal evidence. Run on the STATIC, ADAPTIVE and `c_int` pad vectors in all 8 cells; the
other multiplier and cap vectors share the same keys, and the invariance is a property of the keys.

**Results (canonical order, seed 0). "Padded" statistics are over the alerts the attacker actually
padded; alerts spared by the lower level are counted separately.**

| window | regime | true det (FD) | per-alert median `r*` / Σ | joint STATIC | ADAPTIVE Σ (÷ per-alert Σ) | ADAPTIVE median pad, padded alerts | spared | padded arity median, padded alerts (per-alert) | `c_crit` vs ρ | `c_int` (added flows) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.55 | horizon-free | 3 (0) | 24 / 80 | 0 remain | 30 (0.375) | 15 | 1 | 44.5 (63) | 1.55 < 2.13 | 2 (165,038) |
| 0.55 | horizon-aware | 105 (0) | 2,946 / 627,495 | 0 remain | **5,650 (0.009)** | **48.5** | 13 | **91 (2,989)** | **2.134 = ρ** | **3 (330,076)** |
| 0.62 | horizon-free | 11 (0) | 6 / 926 | 0 remain | 859 (0.928) | 859 (one alert) | 10 | 881 (20) | 40.0 > 2.49 | 41 (13,464,320) |
| 0.62 | horizon-aware | 107 (1) | 3,908 / 977,567 | 0 remain, FD gone | **9,992 (0.010)** | **33** | 4 | **55 (3,928)** | **2.485 = ρ** | **3 (673,216)** |

Share of deployment episodes at least as large as the padded-alert median arity: 3.8 % (0.55
horizon-aware), 4.3 % (0.62 horizon-aware); the paper's per-alert figure is 0.22 %. First-flow cells
agree in direction (ADAPTIVE Σ 5,650 / 9,992 on the horizon-aware arms; ratios 0.14–0.17 on the
horizon-free arms, where first-flow issues 18 / 13 alerts). No malicious episode at either window
contains a benign flow (`mixed = 0`), so `m` is the attacker's own flow count.

Volume cap, horizon-aware arms — true detections that **still fire** under the joint attacker, split into
structural + cascade victims, against the per-alert reading and the cap's benign price:

| cap | 0.55 joint (struct. + casc.) | 0.55 per-alert | 0.62 joint (struct. + casc.) | 0.62 per-alert | benign truncated (0.55 / 0.62) |
|---|---|---|---|---|---|
| 30 | 105 (87 + 18) | 105 | 107 (85 + 22) | 107 | 7.36 % / 7.30 % |
| 100 | 96 (44 + 52) | 100 | 79 (33 + 46) | 103 | 3.40 % / 2.86 % |
| 300 | **19 (1 + 18)** | 91 | **60 (22 + 38)** | 95 | 1.04 % / 1.59 % |
| 1,000 | **0** | 80 | **0** | 82 | 0.50 % / 0.41 % |
| 3,000 | 0 | 52 | 0 | 59 | 0.21 % / 0.19 % |

Multiplier, horizon-aware arms: `c = 2` leaves 100 / 107 alerts; `c = 3` leaves **none** at either window
(the per-alert rule `c >= 1 + r*/m` predicted 99 / 106 survivors). Horizon-free 0.62 canonical: `c = 10`
leaves one alert (the first, `m = 22`, `r* = 859`, needs `c >= 1 + 859/22 = 40.05`, so the smallest
integer multiplier is 41 — the JSON's `c_int`), per-alert and jointly.

**What it means.**

1. **The per-alert results hold jointly, in these eight cells.** Padding every true detection with its
   per-alert `r*` and re-running the controller leaves zero true detections in every cell; the surviving
   false discovery at 0.62 disappears too. Table I's "upper bound" caption is now a measurement for the
   two windows it covers.
2. **Under horizon-aware spending the per-alert price is dominated by the controller's own earlier
   rejections.** e-LOND's level carries `(R+1)`. An attacker who suppresses from the first alert keeps
   `R` at zero (no false discovery survives here) and pays the cold-start price for every alert. Of the
   621,845-flow reduction at 0.55, **94.2 %** is the lower level on the 92 alerts still padded and 5.8 %
   is the 13 alerts spared entirely; at 0.62, 99.6 % and 0.4 %. The joint total is 0.9–1.0 % of the
   per-alert sum; the median pad over padded alerts falls from 2,946 / 3,908 to 48.5 / 33. The "24 →
   2,946" contrast is a per-alert statement; the campaign-level contrast for this attacker is 30 → 5,650
   (0.55) and 859 → 9,992 (0.62): still one to two orders of magnitude in total volume.
3. **The padded episodes become far less exceptional.** Sec. V-D's "median padded arity 2,989, which only
   0.22 % of episodes reach" is a per-alert statistic. Over the alerts the sequential attacker pads, the
   median padded arity is **91, reached by 3.8 %** of deployment episodes (0.62: 55, 4.3 %). The
   conspicuity claim holds against the per-alert attacker only.
4. **The volume cap keeps protecting at 100, for two measured reasons, and much less at 300.** At a cap of
   100 the joint attacker still lets 96 / 79 alerts fire (per-alert reading: 100 / 103). Of those, 44 / 33
   are structural — too large to hide even at the cold-start level — and 52 / 46 are cascade victims that
   would have fitted at R = 0 and fire only because earlier alerts raised R. At 300 the per-alert reading
   (91 / 95 fire) overstates the protection: jointly 19 / 60 fire, and at 0.55 all but one of them are
   cascade victims. At 1,000 the joint attacker silences everything where the per-alert reading said 80 /
   82 would fire. The cascade is measured, not inferred; its size depends on the structural seed, and the
   grid is coarse, so no threshold between 100 and 300 is claimed.
5. **A closed form ties the feasibility ratio to the state-free attack.** With `R = 0` the boundary
   multiplier is `c_crit = max_j Ev_j*alpha*gamma_{t_j} <= CEIL*alpha/T = rho` under the horizon-uniform
   allocation; equality holds iff some malicious episode attains the ceiling, which is the case at both
   windows (measured `c_crit = rho = 2.134, 2.485`). Silencing the *live* controller at `c > c_crit`
   additionally needs no false discovery to survive and raise R, which holds here (`exact = true`). The
   realisable integer prescription `c = 3` silences both horizon-aware arms; `c = 2` does not. This is an
   algebraic identity whose conditions are met here, not a coincidence and not a general theorem about
   every stream: the margin grouping buys is, under these conditions, the dilution factor that erases it,
   at (c−1)·Σm ≈ 330k / 673k added flows with no controller state.
6. **0.62 horizon-free is one alert, not eleven, under the canonical order.** Suppressing the first
   canonical alert (859 flows) spares the other ten, which fired only at boosted levels. Under first-flow
   the same window pads 8 and spares 5 (total 152), so this is an ordering-specific reading.
7. **A pre-existing exposure in Sec. V-C.** The body says "c = 10 … suppresses every canonical alert in the
   evaluated state-free arms". t66's multiplier arm covers canonical 0.55 (`c_min = 3`) and 0.85
   (`c_min = 7`) only; at canonical 0.62 the first alert needs `c > 40.05`, i.e. the integer multiplier 41,
   so `c = 10` leaves it standing.
   The sentence is scoped-true and misleading for a window the body uses throughout. It must be fixed
   whether or not the joint result is kept.

**What the blind audits caught, in order.**

* Code, round 1 (no CRITICAL): `c_crit` is a strict boundary under the inclusive rule, not a "smallest
  multiplier"; the padded-stream permutation was assumed. → Boundary wording, integer prescription,
  `check_padded_stream`.
* Code, round 2 (CRITICAL): the first stream check gave pads the target's *first* timestamp while
  appending at the array end — a back-dated insertion, not an append. → Last timestamp + stable re-sort;
  first-timestamp invariance asserted.
* Code, round 3 (labelling): "real pool flow" overstated a zero-evidence rerun; above/below reruns are a
  continuous relaxation, only `c_int` is realisable; equality-case text contradicted itself. → Relabelled,
  `c_int − 1` check, wording. Stopped.
* Write-up (CRITICAL + MAJOR): "padded arity 73" was the median over all 105 detections including 13
  unpadded ones (padded-only: 91); the cap cascade was written as demonstrated but was inferred from
  the level rule; `c_crit = rho` was written as a discovery rather than an identity with conditions;
  "joint minimum" overstated a greedy attacker's cost; the claim that STATIC is the largest checked pad
  vector was false (`c_int` at 0.62 horizon-free is 13.5M flows). → Cascade instrumented (structural vs
  victim), statistics relabelled, scope paragraph added, this section rewritten.
* Declined: running the stream check on every multiplier and cap vector (key-based invariance); an
  audit's remark that a per-episode ownership oracle is assumed — it is the paper's threat model.

**Consequences for the paper** (kept; applied 6 Sep 2026, see `43_r25_worklist.md` Tiers 1–2): abstract cost
sentence (per-alert label) and cap sentence (joint qualifier); Sec. I contribution 3; Sec. V-C: the
`c = 10` sentence (item 7), the joint `c = 3` result, and the sentence "every reported $r^{\star}$ is an
exact attack cost … a lower bound on the attacker's volume" (line ~703–707), which is stated on the
unperturbed trajectory and needs a per-alert label if it survives the repetition cut; Sec. V-D rewritten around per-alert vs
campaign price, padded-only conspicuity and the measured cap cascade; Sec. V-E: the "three orders of
magnitude larger" sentence (line ~773) and the "not a joint rerun" paragraph, which stays true of the
per-alert replay and gains the joint result after it (t65's R22 replay pins name these sentences —
revise them deliberately); Table I (joint column: ADAPTIVE Σ, padded-alert median pad and arity);
`tab:defenses` volume-cap row (scoped to measured caps and cells); Sec. VII-B (qualify, not delete —
it already says per-alert); Conclusion's "expensive enough for external admission control" clause;
`t61`/`t71`/`t65` registration; `runner.py`, `paper.ipynb`, `make_appendix_tables.py` wiring.

## 4.71 Round 26: Corollary 2 promotes the `t75` critical-multiplier identity to a theorem `[THEORY]`

No new compute. The reviewer (round 26, point 11) asked that the `c_int = floor(rho)+1` observation of
§4.70 be stated as a corollary. `paper/satml.tex` now carries `cor:dilution` (Corollary 2, Sec. V-C) with
its proof in `appendix_proofs.tex`: under horizon-uniform e-LOND, arithmetic-mean evidence with flow
e-values ≤ M, no non-attacker hypothesis at or above the cold-start threshold T/α, and every attacker
episode multiplied by an INTEGER c ≥ 1, every c > ρ gives a rejection-free trajectory, no integer c ≤ ρ
does once an attacker episode attains M, and ⌊ρ⌋+1 is the smallest uniformly sufficient integer. The
per-stream threshold is ⌊c_crit⌋+1 with c_crit = max_j Ev_j·α/T ≤ ρ — exactly what `t75` computes
(`critical_multiplier.c_crit`, `c_int`), with c_crit = ρ at both horizon-aware windows because a
malicious episode attains the ceiling at each. The corollary's hypothesis on non-attacker hypotheses is
certified at both windows by `remaining_false_discoveries_int == 0` (the 0.62 false discovery fires only
at a raised level). Audit history: the first statement used a REAL c — two blind audits flagged that
(c−1)m_t is then not an integer, so the sharpness claim lived in the code's continuous relaxation; the
integer restatement passed two further blind audits. The real-valued `above`/`below` checks in the JSON
remain what they were: a continuous relaxation, labelled as such in the appendix prose.

Also in round 26 (no numbers changed): the appendix captions of `apptab:joint`, `apptab:a1strata` and
`apptab:semblur` were split into caption / generated prose companion / notes. The fidelity audit of that
split found a pre-existing error in the semblur caption — "under 10% of alerts overlap the exercise in
time" named windows, not cells, and the 0.55/first-flow cell overlaps at 13.1% (`usability`
`frac_alerts_temporally_overlapping`); the generated prose now names the three temporal cells with their
order and computes the bound (9%).

## 4.72 The joint attack on the benign-inclusive AIT stream (`t76_joint_ait.py`) `[REAL]`

**Why.** Every AIT number in the paper (t51, t54, t67) prices each alert on its own against the level it
received on the *unperturbed* e-LOND trajectory, and the LSPR23 joint rerun (t75, §4.70) propagates
*zero-evidence* pads. Neither shows what happens when real pads can fire, when non-attacker episodes
reject and raise `R`, and when a host-conditioned detector re-scores every later flow to the victim — all
on one trajectory. Design, threat model and five rounds of blind audit: `docs/48_joint_ait_design.md`.
Run 7 Sep 2026, D = 100 pad-sampling trajectories per cell, canonical (metadata-hash) order only.

**How to read every number below.** Each cell reports the **median over 100 trajectories** of a
per-organisation statistic; the totals here are those medians **summed over the eight organisations**.
They are therefore not counts from one joint run, and two of them are fractional before rounding
(244,249.5 and 242,206.5 pad flows). Pad distributions are over **all** attacker-owned episodes, not
only the suppressed ones.

**Scope, stated once.** Eight AIT organisations, leave-one-organisation-out detector, chronological
in-organisation benign calibration preceding the first attack, two-hour host-pair episodes, e-LOND under
horizon-free `poly` and horizon-aware `uniform` spending. Flow-only detector on all eight; the
host-conditioned arm on the two organisations the paper already covers. Pads are inserted after the
attacker's **own** last flow in the episode (co-resident benign flows can end the episode later and the
attacker cannot see them), carry their templates' real evidence, and on the host arm re-score every later
flow on the attacked pair. **Two pools**, and the distinction turns out to carry the result: the
*causal* pool (benign flows to that victim strictly before the pad time) and, for comparability with every
per-alert AIT number in the paper, t54's whole-deployment benign-to-victim pool, which contains flows from
*after* the pad time and is labelled a **non-causal oracle pool** in the artefact.

**Controls.** The stage *asserts* — it does not merely report — that the clean canonical baselines
reproduce `t67`'s canonical rows field by field; that the in-file controller walk equals
`h6_procs.run_lond` on the clean stream and on every state-free attacked stream; that calibration scores,
threshold and every template pool are unchanged by the attack; that on seeds 0–4 of every cell the padded
flow stream regroups to the same episodes with arities `m + r`, unchanged labels, first timestamps and
bucket keys; and, on the host arm, that the lazy host-feature update equals a full rebuild of the padded
stream (features, pad contexts, pad evidence, every deployment row's evidence). Outcome classes conserve
per trajectory. The JSON records the outcomes of these assertions (`control_t67`, `immutability_asserted`,
`conservation_asserted`, 60 `validation` entries per organisation), not the compared data itself.

**Flow-only arm, all eight organisations.** Totals are summed per-organisation medians, as above.

| spending | baseline own alerts (non-attacker) | per-alert Σ r* | joint GREEDY, oracle pool | joint GREEDY, causal pool | state-free c = ⌊ρ⌋+1 |
|---|---|---|---|---|---|
| horizon-free | 79 (4) | 607,802 | **1 remain**, ≈244,250 flows (40%), every own alert silenced in 7/8 orgs | **24 remain**, ≈430,626 flows, in 0/8 orgs | **65 remain** |
| horizon-aware | 80 (5) | 599,967 | **0 remain**, 91,713 flows (15%), 8/8 orgs | **27 remain**, ≈242,207 flows, 0/8 orgs | **60 remain** |

1. **The joint attack transfers to AIT under the paper's own pool.** With the pool every per-alert AIT
   number already uses, the sequential attacker silences all but one and then all of the baseline true
   detections, at 15% and 40% of the per-alert sum (per organisation 0.04–0.57). This is the LSPR23 joint
   finding (§4.70) reproduced on a second dataset with pads that carry real evidence. It is a statement
   about *these* cells and *that* pool, not about AIT in general.
2. **Pads that fire do not stop the attack, at the rates seen here.** In the successful oracle-pool arms
   at most 297 and 13 pads fire in any trajectory. The largest firing count anywhere, 2,909 (harrison,
   horizon-aware), occurs in the *causal* arm, which does not clear every organisation — so firing pads
   are not the reason that arm fails (point 3 is).
3. **Pad provenance separates success from failure.** Restricted to traffic the victim had *already*
   received, the same attacker clears no organisation in either regime: 24 and 27 alerts survive against
   1 and 0. The two arms differ only in the pool, so within this experiment the pool is what changes the
   outcome; the pools differ in more than timing, since the oracle pool also draws from other victims'
   later traffic.
4. **Why the causal arm fails: there is usually nothing to imitate.** 30 of the 95 attacker-owned
   episodes have fewer than the required 20 benign flows to their victim before the attacker's last flow,
   and **18 of those 30 have none at all**; the 65 usable episodes have a median of 515 templates. The
   `pool_unavailable` class accounts for 22 of the 24 and 23 of the 27 surviving alerts. A further 36
   episodes are *pool-extended*: their causal deployment pool is undersized (median 0 deployment
   templates) and is filled out with pre-attack traffic to the same victim, which under k = 1 carries zero
   evidence by the construction of the conformal threshold, so they are reported as a separate stratum.
   A smaller channel is *futility*: 2 and 5 episodes reach the stage's futility rule, meaning at least
   1,024 pads have been sent and their running mean evidence is already at or above the episode's
   threshold, at which point no further pad can bring the episode mean below it.
5. **Corollary 2's state-free prescription does not transfer to these cells, and the reason depends on
   the pool.** The integer multiplier c = ⌊ρ⌋+1 (2–6 by organisation) leaves 65 of 79 and 60 of 80 alerts
   standing under the causal pool. An oracle variant sized on the true total arity `m_total` leaves
   **exactly the same counts in the causal cells** — so where cover traffic is scarce, knowing the
   co-resident benign flow count buys the attacker nothing. Under the richer oracle pool the two variants
   **do** differ, in three cells: `russellmitchell`/horizon-aware 5 → 0, `shaw`/horizon-free 3 → 2,
   `wardbeck`/horizon-free 4 → 3. The precise statement is therefore that arity uncertainty is immaterial
   exactly when the pool is the binding constraint, and matters when it is not. (An earlier draft of this
   section claimed equality "in every cell"; two blind write-up audits showed that to be false, and this
   is the corrected form.)
6. **Non-attacker alerts survive and are concentrated.** Under the causal pool 4 and 5 non-attacker
   rejections remain across the eight organisations, three of them on `shaw` in every regime and pool;
   under the oracle pool it is 4 and 4. The attacker's policies never pad a non-owned episode, so these
   are alerts it cannot remove.
7. **Horizon-aware spending is not the axis that separates outcomes here.** It moves the baseline from
   79 to 80 own alerts. On LSPR23 the same switch moved 3 to 105 (§4.70), because that window holds
   57,368 episodes against AIT's 1,664–5,082 (`T` per organisation, this artefact). Report the regime as
   covered, not as the finding.

**Host-conditioned arm, `shaw` and `wilson` — the two organisations the paper already covers.** Here a
pad re-scores every later flow on the attacked pair, so the detector's own context responds to the attack.
Totals are medians over 100 trajectories, as above.

| org | spending | baseline own (non-attacker) | per-alert Σ r* | GREEDY oracle pool | GREEDY causal pool | state-free c = 3 |
|---|---|---|---|---|---|---|
| shaw | horizon-free | 3 (1) | 286 | **0 remain**, 28 flows | **2 remain**, 258 flows | 2 remain |
| shaw | horizon-aware | 3 (6) | 151 | **0 remain**, 7 flows | **2 remain**, 144 flows | 2 remain |
| wilson | horizon-free | 6 (0) | 73,981 | **0 remain**, 73,337 flows | **1 remains**, 73,454 flows | 6 remain |
| wilson | horizon-aware | 6 (0) | 17,910 | **0 remain**, 16,975 flows | **1 remains**, 17,187 flows | 3 remain |

8. **Causal host-context recomputation does not save the detector.** With the paper's pool the joint
   attacker silences every host-conditioned alert on both organisations, and on `shaw` for 28 and 7 flows
   against the 286 and 151 the per-alert sum requires — the joint saving the LSPR23 rerun predicts,
   reproduced with a detector whose features move as the pads arrive. Re-scoring creates no new alerts in
   any cell (`created_own` and `created_nonown` are zero throughout the host arm).
9. **The same causal-pool wall appears here.** Restricted to the victim's prior traffic the attacker
   clears neither organisation: 2 of 3 survive on `shaw` and 1 of 6 on `wilson`, again because 4 of each
   organisation's own episodes have no usable pool. On `wilson` two pads fire per trajectory and the
   attack still succeeds on five of six alerts, which is the same conclusion as the flow arm: firing pads
   are not what stops it.
10. **`shaw` is where non-attacker alerts bite.** Under horizon-aware spending its host-conditioned
    detector issues six non-attacker rejections, all of which survive the attack because the attacker
    never pads a non-owned episode; under horizon-free spending it issues one. `wilson` has none. This is
    the mechanism the reviewer asked to see, and it is visible on exactly one organisation.
11. **Upper-bound qualification, host arm only.** Where a chunk cannot be proved exact the attacker sends
    bounded bursts of 256 pads and re-tests between them, so its cost is an upper bound on the
    fully-informed oracle's, overshooting by at most one burst per episode. On `shaw` at most one burst is
    ever sent, so the numbers there are exact; on `wilson` 286 and 64 bursts are sent, bounding the
    overshoot at about 0.4% of the reported pad totals. The flow arm is exact throughout.

**Blind write-up audit (two runs, 7 Sep 2026).** Both recomputed every number from the artefact and both
returned *not publishable* on the same three errors, all now corrected above: the false "same alerts in
every cell" oracle-arity claim; "up to 2,706 pads fire", which was a median from one cell rather than the
2,909 maximum; and totals presented as exact counts when they are summed per-organisation medians. Both
also asked that the surviving non-attacker counts name their pool, and that claims resting on other
artefacts (the LSPR23 contrast, the detector chain) cite them. Their remaining objections are that
interpretive words like "dominant cause" and "decides" outrun what one artefact can establish; the
wording above is narrowed accordingly.

## 4.73 Round 31: the host-conditioned AIT arm at all eight folds (`t54_ait_suppression.py`) `[REAL]`

**Why.** The reviewer read `ORGS_HOST = ["shaw", "wilson"]` (comment: "Shaw + typical") as possible
selective evaluation, and it was: the host-conditioned detector had never been run on the other six
folds. `ORGS_HOST` now defaults to every organisation.

**Result (first-flow order, 200 draws, fold-keyed RNG).**

| org | det. | suppr. | per-draw succ. | median r*_emp | closed form |
|---|---:|---:|---:|---:|---:|
| fox | 9 | 9 | 1.000 | 115 | 55 |
| harrison | 7 | 6 | 0.857 | 792.5 | 692 |
| russellmitchell | 9 | 9 | 1.000 | 1,140 | 1,140 |
| santos | 5 | 5 | 1.000 | 43 | 43 |
| shaw | 3 | 3 | 1.000 | 269 | 269 |
| wardbeck | 9 | 8 | 0.744 | 8,471.5 | 8,263.5 |
| wheeler | 15 | 11 | 0.609 | 1,609 | 1,486 |
| wilson | 6 | 6 | 1.000 | 355 | 355 |
| **total** | **63** | **57** | | | |

64 rejections, 63 true, pooled realised FDP 0.016.

**Findings.**

1. **The two-organisation arm was the optimistic end.** shaw and wilson give 9/9; across all eight the
   count is 57/63 at per-draw success 0.61–1.00. The narrow arm did not merely under-report scope, it
   reported the favourable cells.
2. **"Suppressible" is a possibility count, not a reliability one** (blind-audit CRITICAL). It means at
   least one of 200 replay draws cleared the threshold inside the scored accumulation range. The six
   episodes outside it are **censored zero-success simulations, not demonstrated attack failures**; the
   budget is twice the zero-pad cost, at least 1,000 pads. The table notes, the appendix prose and the
   body all say so now, and the per-draw success column carries the reliability the count does not.
3. **Where padding fails, the accumulated context is what stops it.** A pad scored in the victim's
   accumulated context can itself fire, and a firing pad adds the ceiling instead of diluting. Failures
   sit at organisations whose pools fire along the accumulation path; `wheeler` reaches a pad-fire
   probability of 0.77 deep in accumulation. Cost and firing rate interact — no per-organisation
   threshold in either alone separates the folds, so the paper claims the mechanism, not a law.
4. **Fold-order dependence, fixed** (blind-audit CRITICAL). One mutable RNG ran through the flow arm and
   then every host fold, so adding six organisations perturbed the two already published. The generator
   is now keyed to `(organisation, arm, order)`. Consequence: t67's first-flow arm reproduces t54's rows
   **by construction** rather than by coincidence of RNG position, and any subset can be re-run alone.
5. **Headline counts are stable under the RNG change; one cost is not.** 84/85 first-flow, 78/79
   canonical, 12–4,650 canonical median range and "equal for seven of eight" all reproduce exactly.
   `wardbeck`'s first-flow median moved 8,294 → 13,142 — the Monte-Carlo spread of a 200-draw median on
   the most expensive fold. The first-flow range in App. D and §4.49 is updated to 212–13,142.

**Collateral.** `t76_joint_ait.py` read `tuple(t54.ORGS_HOST)`, which became `tuple(None)` under the new
default; its joint host arm is pinned to the two organisations the design note scoped it to. t76 itself
did not need re-running: its t67 control checks only deterministic fields (T, NC, rejections, detections),
all unchanged.

**Reproduce.** `t54_ait_suppression.py` (`main()`), then `t67_ait_order.py`; artifacts
`out/t54_ait_suppression.json`, `out/t67_ait_order.json`; appendix tables `apptab:aitsupp`,
`apptab:aitorder`; body Table III row and §sec:transferattack. Two blind-codex passes (design/code, then
paper-vs-artefact).

## 4.74 Round 32: Corollary 2's premise measured, and joint-attack reliability (`t77_cor2_premise.py`) `[REAL]`

**Why.** The reviewer found two invalid inferences about Corollary 2 on AIT. Sec. V-F said non-attacker
alerts "violate the premise" in `russellmitchell`, `shaw` and `santos`; but the corollary's premise is
that no non-attacker hypothesis carries evidence **at or above the cold-start threshold `T/α`**, and a
baseline non-attacker alert can fire only after earlier rejections have raised the level, so its
existence proves nothing about the premise. Separately, Table V's sums of per-organisation medians hid
the per-trajectory reliability (a median of zero survivors is compatible with many trajectories having
some). Both are answered from the existing streams; nothing was re-run.

**`t77_cor2_premise.py`** rebuilds the ten streams `t76` attacked (flow arm on eight organisations, host
arm on `shaw`/`wilson`) with `t76.prepare_org`, asserts the clean e-LOND walk reproduces `t76`'s stored
baseline field by field in every cell (T, NC, CEIL, ρ, c_int, rejections, true, own and non-attacker
alerts), and records per cell `max_{j∉A} Ev_j / (T/α)`, the number of non-attacker episodes at or above
`T/α`, and for each baseline non-attacker alert its evidence, the `R` it fired at and whether it clears
the `R = 0` level at its own position. 226 s. Artefact `out/t77_cor2_premise.json`; tables
`apptab:cor2diag` (t77 + t76) and `apptab:joint76rel` (t76 only).

| org (arm) | ρ | max other ÷ T/α | n ≥ T/α | other alerts hf/ha (at R=0) | own attains ceiling |
|---|---:|---:|---:|---|---|
| fox | 1.61 | 0 | 0 | 0/0 | yes |
| harrison | 3.48 | 0 | 0 | 0/0 | yes |
| russellmitchell | 2.99 | **1.497** | 1 | 1 (1) / 1 (1) | yes |
| santos | 4.03 | 0.336 | 0 | 0 / 1 (0) | yes |
| shaw | 2.29 | **2.289** | 2 | 3 (1) / 3 (2) | **no** (c_crit = 1.53) |
| wardbeck | 5.48 | 0 | 0 | 0/0 | yes |
| wheeler | 3.31 | 0.019 | 0 | 0/0 | yes |
| wilson | 2.95 | 0 | 0 | 0/0 | yes |
| shaw (host) | 2.29 | **2.289** | 4 | 1 (0) / 6 (4) | **no** (c_crit = 1.53) |
| wilson (host) | 2.95 | 0 | 0 | 0/0 | yes |

**Findings.**

1. **The cold-start premise fails on 3 of 10 cells, not the 3 organisations the paper named.**
   `russellmitchell` (one non-attacker episode at 1.50 T/α) and both `shaw` cells (a non-attacker episode
   attains the ceiling, ratio = ρ) fail it. **`santos` does not**: its one horizon-aware non-attacker alert
   (Ev = 12,610, ratio 0.34) fires at R = 9, i.e. only at a level nine rejections have raised. The paper's
   sentence was wrong for `santos` and right for the wrong reason elsewhere. Of the 16 baseline
   non-attacker alerts over both spending rules, 9 clear the R = 0 level at their own position and 7 fire
   only at a raised level.
2. **The premise is not what makes the multiplier fail.** Where it holds (7 of 10 cells) `c_int` still
   leaves alerts standing — `fox` 5/11 horizon-free and 11/11 horizon-aware. The `t76` outcome classes
   say why: `fox`/horizon-aware has 3 pool-unavailable own episodes (never padded, so they fire and raise
   R) and then **8 cascade** survivors whose `(c−1)m` budget would have sufficed at R = 0. The hypothesis
   that breaks is the corollary's "multiplies **every** one of its own episodes", not the premise on
   other hypotheses — the attacker's own unpaddable episodes play the role the proof assigns to a benign
   rejection. Plus pads that fire: median multiplier firing share 0–5.97% by organisation (0 on
   `russellmitchell`, `shaw`, both host cells).
3. **`c_crit < ρ` on `shaw`.** No `shaw` attacker episode attains the ceiling (largest attacker evidence
   gives c_crit = 1.53 against ρ = 2.29), so the stream-specific integer `⌊c_crit⌋+1 = 2 < c_int = 3`
   there. Everywhere else some attacker episode attains the ceiling and c_crit = ρ. The LSPR23 statement
   "c_crit = ρ at both evaluated windows" is unaffected; the AIT prose no longer implies it.
4. **Horizon-free application of `⌊ρ⌋+1` is a heuristic transfer** (the corollary is proved for
   horizon-uniform spending) and is now labelled so in Sec. V-F, the new table's caption and its prose.

**Reliability over trajectories (`apptab:joint76rel`, from `t76` alone).** Per organisation, spending
rule and attacker arm: P(every own alert silenced), median and 95th percentile of the residual count and
of the flows spent. `t76` stores median/p5/p95/min/max/mean per cell, **not the trajectories**, so the
upper quantile is the 95th; a 90th percentile would need a re-run and was not requested at that price.

5. **The residual count is essentially deterministic given the organisation.** In 58 of 60 cells p5 = p95;
   the two exceptions differ by one alert (`russellmitchell` horizon-free prior 4/5;
   `wilson` horizon-aware prior 4/4.05 interpolated). With the deployment pool the sequential oracle has
   P(all) = 1.00 in 15 of 16 flow-only cells; the exception is `russellmitchell` horizon-free, where
   exactly one alert survives in **every** trajectory (P(all) = 0.00). So the reviewer's worry — a median
   of zero coexisting with a substantial fraction of trajectories having survivors — does not occur here.
6. **Pad sampling moves the cost, not the outcome.** The 95th-percentile cost exceeds the median by up to
   1.90× (`russellmitchell` horizon-free deployment: 68,638 → 130,582) with a median ratio of 1.00 across
   cells. Variation across organisations (costs from 7 to 162,476 flows) dwarfs variation across draws.
   The sums of medians in Table V are eight nearly deterministic per-organisation outcomes added together,
   which the prose now says.

**Also this round (wording only, no numbers moved).** App. H-C's "inflation fails analytically" replaced
by the pathwise `S/(m+r) ≤ S/m` monotonicity at a fixed level (the `E[Ev|M_j] ≤ 1` bound permits large
realisations, so it never implied "no padding turns a benign group into a discovery"); fragmentation
narrowed to "expected group evidence is unchanged" with the binomial rejection probability shown to
depend on m. App. E-F's regroup sentence now states what is asserted unchanged (count, keys/permutation,
first timestamps, labels) and what must equal the independently computed padded stream (arities m+r,
means S/(m+r)) — the code (`t75.check_padded_stream`, `t76.validate_regroup`) was right, the prose was
not. `apptab:joint`'s (the LSPR23 joint table, Table XXXVI in the reviewed build) "benign trunc." → "benign > n" (share of benign episodes above the cap; nothing is
truncated). Sec. III-A's "restore an alert without a rejection" → absorbing-state wording. Sec. II-B now
says member-level metadata-conditional validity is a sufficient condition, not a necessary one, and
App. A-A gains the four-hypothesis Uniform(0,1) construction (nCal = 99, k = 1, T = 4, α = 0.05: threshold
80, attack e = 100 detected, one appended score −1 flow gives mean 50, every null e-value has
E[e | M_j] = 1 exactly by exchangeability).

**Reproduce.** `AIT_DIR=<cache> python t77_cor2_premise.py` after `t76_joint_ait.py`; then
`paper/make_appendix_tables.py` (36 tables). Gates: t61 registry entries `joint76rel`, `cor2diag`.

## 4.75 Submission-package audit of `src/` (12 Sep 2026) `[INFRA]`

Second `src/` audit, against the near-final codex draft. Two stages left for the attic because the draft
no longer quotes them (`t28_P5_padding`, `t43_E10_xwindow_padding`), plus the two-position `t26_H4.json`
(a subset of the five-position file) and the orphan `h8_audit_sample.csv`. The table generator moved into
the package as `src/lib/tables.py` (byte-identical output through the `paper/` and `src/` wrappers), so
the artifact can now rebuild every table it promises, not just every figure. `paper.ipynb` gained cells
for the eleven stages it never exercised (`t21c`, `t21d`, `t22`, `t23`, `t25`, `t29`, `t63`, `t64`,
`t76`, `t77`, and a table rebuild): 54 code cells, 0 errors, 34 s from cache, no artefact changed.
`runner.py` registers `t77`. Record: `docs/53_src_submission_audit.md`.
