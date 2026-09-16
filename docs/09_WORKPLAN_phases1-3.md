# Work Plan — Remaining Tasks

**Created 26 Aug 2026.** Supersedes the open-items list in `04_EXPERIMENTS_AND_FINDINGS.md` §7.
Deadlines: SaTML 2027 abstract **22 Sep** (27 days), paper **29 Sep** (34 days), 12 pages.

Sources: the external review (`12_review_experiments_and_next_actions.md`), plus corrections
to that review recorded in §1.3 below.

---

# 1. Where things stand

## 1.1 Claim status

| Finding | Status | Blocked on |
|---|---|---|
| F1 feasibility horizon (procedure class) | **live** — T3 done, proved for two families | — |
| F2 first-rejection deadline | **live** — T3 done, stated per procedure | — |
| F3 grouping vs horizon | **live** — restated for horizon dependence | — |
| F4 flow vs episode, 60-point gap | **live** — strongest real-data result | nothing |
| F5 feasibility margin | **live** — T2 done; margins −0.061 to +0.918 over 5 positions | — |
| F6 dilution cost | **live** — T2 done; median 1–134 flows | — |
| F7 padding theorem | **live** — T4 done, two proofs | — |
| F8 → cap-policy result | **live** — T1 done; restated in §4.12 | — |
| F9 drift is mild | **live** | nothing |
| F10 conditional validity = 1/e | **live** | nothing |
| F11 ceiling vs reliability | **live** | nothing |
| F12 inflation/fragmentation fail | **live** | nothing |

Two things must not appear in any abstract until T1 and T2 land: the F5 margin and the F8
floor numbers.

## 1.2 Points from the review adopted as-is

Cap validity (→ T1), full-stream re-run (→ T2), padding formalisation (→ T4), e-value
procedures (→ T5), problem-space attack (→ T6), analyst-feedback baseline (→ T8), matched
operating points (→ T9), episode-not-incident wording (→ T10), defer AIT-ADS, second dataset
with real campaign labels (→ T12).

## 1.3 Corrections to the review

1. **Priority 1 is mostly settleable on paper, not by experiment.** e-LOND rejects `H_t` when
   `E_t ≥ 1/α_t` with `α_t = α·γ_t·(|R_{t−1}|+1)` and γ summable. So the required e-value
   diverges against a finite conformal ceiling — the same mechanism. e-LOND will *confirm*,
   not refute. This becomes T3 (a proof) and demotes the experiment to T5 (measuring
   constants). It should not gate the sprint.
2. **The review's own cap fix is an attack surface.** Enforcing `m ≤ n₀` by counting the
   first `n₀` events lets an attacker front-load benign padding to fill the cap. Every
   candidate policy must be evaluated against that, so T1 includes it.
3. **The subsampling effects oppose each other.** Restoring benign flows raises `T` (worse
   threshold) *and* `|C|` (higher ceiling). Rough scaling: `T` 32k→~50k, threshold
   1.29M→~2.0M, `|C|` 1.06M→~2.1M. They nearly cancel, so the re-run is not obviously biased
   in either direction — which is precisely why it must be run rather than reasoned about.
4. **The problem-space gap is smaller than the review implies.** The grouping key is
   (SrcIP, DstIP, time bucket); an attacker controls all three by making ordinary connections
   to the same host in the same hour. No adversarial crafting, no detector access. The real
   question is narrower: does traffic *originating from an attacker host* score as low as
   random benign traffic? T6 is scoped to that.
5. **The review's Red Light is close to unfalsifiable.** It requires a method that avoids
   silence, resists dilution *and* preserves useful detection; §4.11 indicates dilution
   resistance costs 86–94% of episodes, so those may be jointly unreachable. Gate criteria
   are restated in §3.
6. **The 2% margin is the bigger problem, and the review missed it.** A single-split,
   single-seed 2% margin is not feasibility. T2 adds seed repetition.
7. **F2 goes unmentioned by the review** but carries the same procedure-specific caveat as
   F1. T3 covers both.
8. **`P_fire` is estimated on the evaluation data** in §4.11 — mild circularity. Folded into T1.

---

# 2. Tasks

Ordered by what unblocks what. T1 comes first because it invalidates a number currently in
the record.

## T1 — Fix cap validity, re-run the floor `[DONE 26 Aug]` — F8 restated in §4.12

**Problem.** `Σe/n₀` is a valid e-value only when group occupancy `m ≤ n₀`. §4.11 sets
`n₀` = p99 group size, so ~1% of groups violate it — and they are the largest groups, the
ones most likely to carry a real attack. `E[Σe/n₀] = m/n₀ > 1` there, so control is void
exactly where it matters.

**Do.** Implement and compare four policies:

| policy | validity | expected cost |
|---|---|---|
| A. `n₀` = max group size | valid | large power loss; floor scales with `n₀` |
| B. truncate — count only the first `n₀` events | valid | **front-load attack**: attacker fills the cap with benign traffic |
| C. deterministic split of oversized groups into ⌈m/n₀⌉ sub-groups | valid | raises `T`, worsens feasibility |
| D. pre-committed slots, `F(e) = e_{slot}` | valid, asymmetric — escapes the trilemma | slot assignment must not be attacker-choosable |

For each: measure the floor, episode detection, and **the front-load attack cost** (pad
events needed to fill the cap ahead of the malicious flows).

Also: re-estimate `P_fire` on the calibration split rather than the test split.

**Accept when.** A policy exists with `m ≤ n₀` guaranteed for every group, its floor and
detection rate are measured, and its front-load cost is quantified. §4.11 rewritten.

---

## T2 — Full-stream re-run with seed repetition `[DONE 26 Aug]` — F5, F6 restated; §4.15

**Problem.** Benign was subsampled 50% *before* the chronological split, so `T`, group sizes,
prevalence and `|C|` are all affected. And the headline "+2%" feasibility margin is one split
with one seed.

**Do.**
1. Define the chronological split on the **full, timestamp-sorted 16,353,511-flow stream**,
   before any subsampling. Benign subsampling permitted **only inside the training window**.
2. Retain every flow in the calibration and deployment windows.
3. Repeat over ≥5 splits/seeds. Report the **distribution** of: feasibility margin, episodes
   detected, dilution cost, floor.
4. Replace every point estimate in F5/F6/F8 with an interval.

**Accept when.** The feasibility margin is reported as an interval across seeds, and either
excludes zero (feasible), includes zero (indeterminate — say so), or lies below (infeasible).
**"Feasible by 2%" does not survive this task in any form.**

---

## T3 — General feasibility theorem `[DONE 26 Aug]` — F1, F2 restated; proof in §4.13

**Statement to prove.** Let a procedure reject `H_t` when the evidence exceeds
`1/(α·γ_t·g(H_{t−1}))`, with `Σγ < ∞` and `g` polynomially bounded in the rejection count.
Let the evidence be bounded above by `(|C|+1)/k`. Then there is a finite horizon beyond
which, absent rejections, no rejection is possible; and the state is absorbing.

Instantiate per procedure — LOND, LORD++, SAFFRON, ADDIS, e-LOND — with each one's `α_t`:

| procedure | `α_t` | note |
|---|---|---|
| LOND | `α·γ_t·(1+D_{t−1})` | implemented |
| LORD++ | `γ_t·w₀ + (α−w₀)γ_{t−τ₁} + αΣ_{j≥2}γ_{t−τⱼ}` | implemented; `S(Δ)` bound in §4.1 |
| e-LOND | `α·γ_t·(\|R_{t−1}\|+1)` | verified against Xu & Ramdas |
| SAFFRON / ADDIS | candidate-based wealth | constants to derive |

**Accept when.** A written proof plus the per-procedure table, and F1/F2 restated in terms of
the procedure class rather than "online error control" generally.

---

## T4 — Formalise padding-robustness `[DONE 26 Aug]` — theorem in §4.16; F7 restated

Vovk & Wang Thm 3.2 fixes the arity `K`; padding changes it, so the result does not follow
from admissibility alone. Two routes:

- **A. Essential domination.** `F_m(x) ≤ max(1, mean(x))`; the padded mean `S/(a+r) → 0`, so
  eventually `F_m(x) < c` for any `c > 1`.
- **B. Direct construction.** With `eᵢ = (N/m)·1{i∈S}` for a uniformly random size-`m` subset
  `S` (valid, perfectly negatively dependent), symmetry forces
  `F_N((N/m)·1_m, 0^{N−m}) ≤ 1` for every symmetric e-merging function of arity `N`.

Both need the threshold quantifier `τ > 1`, else the constant rule `F ≡ 1` is a counterexample.

**Accept when.** A theorem with a precise definition of padding-robustness, or a written
record of why it fails. Either outcome closes the item.

---

## T5 — e-value procedures `[DONE 26 Aug]` — §4.17 (SAFFRON/ADDIS/e-GAI still open)

Not a kill test — T3 settles the mechanism. This measures **where** each procedure's boundary
sits and whether any escapes the template.

Implement: **e-LOND**, **online e-BH** ([arXiv 2407.20683](https://arxiv.org/pdf/2407.20683)),
**e-GAI** ([arXiv 2506.01452](https://arxiv.org/pdf/2506.01452)), and one compound-e /
e-closure method. Compare against LORD++ on the same stream.

Also replaces `min(1, 1/e)` (valid by Markov but lossy) with native e-value procedures.

**Accept when.** Feasibility boundary and episode detection reported per procedure, with any
procedure that escapes the T3 template identified explicitly.

---

## T6 — Attacker-origin padding `[DONE 26 Aug]` — §4.17

Current padding is drawn from the benign pool at large. The attacker controls the group key
(SrcIP, DstIP, time bucket) by construction, so injection is not the question. The question
is whether traffic **originating from an attacker-controlled host** scores as low as random
benign traffic.

**Do.** Redraw padding from benign flows whose source IP also appears as an attack source.
Compare cost against benign-pool padding. Optionally add protocol-matched and service-matched
variants.

**Accept when.** Attack cost reported for attacker-origin padding, and the gap to benign-pool
padding quantified. If attacker-origin traffic scores materially higher, the attack cost rises
and F6 must be restated.

---

## T7 — Analyst-feedback baseline `[DONE 26 Aug]` — see §4.14, F13

`τ_{t+1} = τ_t + η(FDP̂_window(t−L) − q)`, latency `L ∈ {0, 1h, 1d, 1w, ∞}`. No multiplicity
theory, no exchangeability, no dependence assumption.

**Accept when.** The crossover `L*` is located. If B6 dominates at every finite latency, that
becomes a headline result and the honest scope of the whole approach is `L = ∞`.

---

## T8 — Matched operating points `[DONE 26 Aug]` — §4.19; F13 restated

Every comparison at matched analyst budget, matched realised FDP, or as a Pareto frontier of
episode recall against FDP and against alerts/day. No unmatched comparison enters the paper.

---

## T9 — Terminology and claim restatement `[DONE 26 Aug]` — F3 restated for horizon dependence

- F3 headline: "Deployable **incident** grouping" → **episode** grouping.
- §4.5: drop or relabel the "288 incidents" row — it invites an inference we established is
  unsupported (LSPR23 has no flow→campaign labels).
- F1 → "Finite-resolution conformal evidence makes procedures in the class of T3 structurally
  infeasible at event-level cybersecurity horizons under realistic calibration budgets."
- F3 → "The tested host-pair/time-bucket grouping family does not restore feasibility on LSPR23."
- F4 keeps "episode" throughout — it is already correct.

---

## T10 — Related-work pass `[DONE 26 Aug]` — §4.18; novelty claim survives, narrowed

The adversarial hypothesis-testing-games literature (IEEE 2018; Yasodharan & Loiseau, NeurIPS
2019) was sampled, not surveyed. Required before any novelty claim about attacking the
decision layer.

---

## T11 — Second dataset with real campaign ground truth `[ASSESSED 26 Aug — no drop-in option]`

Searched for a public flow-level dataset with genuine flow→campaign labels. None found that
avoids a multi-day pipeline: **ConCap** (arXiv 2509.16038) is a traffic *generator*, so using it
replaces live-fire data with synthetic; **AIT-LDSv2** needs label reconstruction from a 137 GB
download (3–5 days); **ProvAttack1/2** (NDSS 2026) are provenance graphs, not flows, requiring a
different pipeline entirely. Decision deferred to §12 below.

### superseded scope

Only after G2 (§3). The requirement is genuine flow→campaign labels, which LSPR23 lacks —
that is the single limitation preventing F4 from being an incident-level result. Do not
substitute another dataset that also lacks them.

---

# 3. Decision gates

**G1 — after T1 + T2.** Do the headline numbers survive a valid rule and the full stream?
- Feasibility margin interval excludes zero, and dilution cost stays under ~10² flows →
  **proceed**.
- Margin interval includes zero → F5 becomes "at or below the feasibility boundary", which is
  still a result; proceed but restate.
- Dilution cost rises above ~10³ flows on the full stream → the attack weakens to a
  large-scale-adversary result; reassess whether it can still lead.

**G2 — after T3 + T4.** Is the theory defensible?
- Both close → the paper has an exact core plus real-data confirmation. Start the outline.
- T4 fails → drop F7 to an observation about the arithmetic mean specifically, and lead with
  T3 + F4 + F6.

**G3 — after T5 + T6.** Is the attack a security result?
- Attacker-origin padding stays cheap → lead with the attack.
- It becomes expensive → the attack is a mechanism demonstration; lead with feasibility (T3)
  and the flow-vs-episode gap (F4).

**Stop criterion.** If T5 finds a procedure outside the T3 template that both stays feasible
at security scale *and* resists dilution at reasonable power, the central story is gone —
reassess the target venue rather than continuing. Note this is stricter than "resists
dilution" alone, since §4.11 suggests resistance costs 86–94% of episodes.

---

# 4. Schedule

| Days | Tasks | Gate |
|---|---|---|
| 27–29 Aug | T1, T3 | — |
| 30 Aug – 2 Sep | T2 | **G1** |
| 3–4 Sep | T4, T9 | **G2** |
| 5–8 Sep | T5, T6 | **G3** |
| 9–12 Sep | T7, T8 | — |
| 13–16 Sep | T10, T11 (if G2 green) | — |
| 17–21 Sep | Draft; regenerate all figures under T8 | — |
| **22 Sep** | **Abstract registration — mandatory, regardless of state** | — |
| 23–29 Sep | Finish draft, threats to validity, appendices, submit | — |

**Descope order, from the bottom:** T11 → T10 → T5's compound-e method → T6's protocol/service
variants → T7's finest latency grid. **Never descope:** T1, T2, T8, T9.

---

# 5. Not doing

- **AIT-ADS label reconstruction** — 3–5 days against a 137 GB dependency. Journal version.
- **SAFFRON / ADDIS implementation** — only if T3 needs their constants empirically.
- **Detector zoo** — two detectors is enough; the paper is not about classifier comparison.
- **More datasets beyond T11** — one with real campaign labels, or none.
- **Full paper draft before G2** — the claims are not stable enough to write against.
- **LANL, WitFoo, UNSW-NB15** — incomplete negative ground truth, vendor labels, 64% prevalence.

---

# 6. Standing rules

1. No claim enters the record without a verification tag and its scope stated inline.
2. No comparison at unmatched operating points (T8).
3. Every FDR number printed beside a power number in the same table.
4. Oracle-derived results labelled as such in every figure caption.
5. Single-split, single-seed numbers are not results — report intervals.
6. Any aggregation rule used must be checked for validity on **every** group it is applied
   to, not on the typical group.

---

# 12. Phase 2 — hardening the experiments

Ten of T1–T11 are closed. The work below exists to retire specific reviewer objections
before they are made, ordered by rebuttal risk retired per unit of effort. Nothing here
blocks a draft; all of it strengthens one.

## Tier 1 — cheap, and each closes an obvious hole `[~2 days total]`

**H1. Second detector.** `[DONE 26 Aug]` — §4.22; F5 strengthened. Isolation Forest,
unsupervised, gives tail reach **0.000 at all ten configurations** — not one attack flow, at
any position or seed, scores above all 1.8–2.4 M benign calibration scores — and therefore
zero true detections for every procedure, at a feasibility margin *identical* to
HistGradientBoosting's (the margin depends only on |C|, k and T, never on the scores). ADDIS,
the one procedure that escapes the §4.13 template, fires 4 times across 10 configurations and
every alert is false. The objection is retired in the strongest direction: a second detector
makes the picture worse, not better.
*Retires:* "your conclusions are an artefact of one classifier."

**H2. Sweep k on real data.** `[DONE 26 Aug]` — §4.23; new finding F14. k = 1 is the only
feasible rank (margin +0.436 → −0.999; zero rejections at every k ≥ 10 in every one of ten
configurations) and it is also the least reliable (worst-case benign firing 50.9× nominal at
k = 1 against 6.8× at k = 1000). Raising k does not trade power for validity; it removes the
operating point. *Retires:* "you chose the most extreme rank and it happens to fail."

**H3. Sweep the error target q.** `[DONE 26 Aug]` — §4.24; F13 strengthened. Run as a joint
(q, γ) sweep per the H6 finding. The corollary holds **exactly**: measured (margin+1) ratios
0.200 / 1.000 / 2.000 / 4.000 against predicted 0.2 / 1 / 2 / 4, so relaxing q buys
feasibility strictly linearly and no faster. A twenty-fold q sweep moves median recall by
0.088; changing γ moves it by 0.188. *Retires:* "the feasibility boundary is an artefact of a
strict target."

**H4. More grouping families.** `[DONE 26 Aug]` — §4.29; **F3 narrowed**, F4 strengthened.
Five families × seven bucket widths. `required |C|` is exactly `kT/w₀ − 1`, so every family
becomes feasible once the bucket is coarse enough. **Host-only (SrcIP, bucket) is feasible at
every bucket tested** (margins +2.232 to +55.891) *and* has higher episode recall than the
host-pair family — so the feasibility barrier can be bought off by coarsening the alerting
unit to one a SOC would recognise. What it costs is F4's gap: malicious-flow coverage stays
at 0.508–0.519 across every family while episode recall falls 0.518 → 0.226. The 86,400 s and
host-pair-only runs coincide exactly, because the deployment window is shorter than a day.
*Retires:* "one grouping definition."

**H5. Cap-selection sweep.** `[DONE 26 Aug]` — §4.25; F8 strengthened. Truncation is valid at
every cap, so validity is not the binding constraint; the two failure modes move in opposite
directions with `n₀`. At p50 (`n₀` = 2) it detects 71/275 and costs the attacker **one**
padding flow; at p999 the attack costs 3,560 flows and detection falls to 6; at max it
detects nothing. *Retires:* "you picked the cap that makes the rule look worst."

## Tier 2 — moderate, and one could break a theorem `[~3 days total]`

**H6. SAFFRON, ADDIS, online e-BH, e-GAI.** `[DONE 26 Aug]` — §4.20; **F1 narrowed**, F2 and
F13 restated. **Two procedures escape the §4.13 template.** ADDIS escapes because its γ index
counts *tested* hypotheses, and threshold conformal p-values are either 1 (discarded) or
candidates, so the index is identically 0 — but its uniform-conservativeness assumption is
violated maximally, so its FDP is empirical-only, and under the max-min optimal γ its
`(τ−λ)` discount leaves it 100% silent. online e-BH escapes because `k*_t` is a fixed point
over the whole history, making the rejection-free state non-absorbing and weakening
feasibility by exactly the horizon T. e-GAI does **not** escape — its own §3.2 proves
e-LORD = e-LOND under a reparameterised γ — and mem-e-LORD, the published α-death fix, is
identical to e-LORD before the first rejection. Also found: the 61–65% silence of §4.17 is
specific to γ ∝ j^−1.6, and so is F13's "dominated point" claim.
*Retires:* "you only broke the procedures you chose to implement."

**H7. Apply the Bates calibration-conditional adjustment.** `[DONE 26 Aug]` — §4.26; F11
strengthened. The fix works (δ held in every cell) and costs 38–78% of the ceiling at k = 1
against 4% at k = 1000 — cheapest exactly where the ceiling is already useless, so it is
priced by the same quantity that creates the problem. Applying it at k = 1, δ = 0.10 moves
the median configuration from feasible (+0.436) to **infeasible (−0.376)**. The DKW form is
unusable in this tail (×0.0005). Also established there: **ADDIS does not control FDR once
k > 1** (FDP 0.033 → 0.246 → 0.707 at k = 1 / 100 / 1000), which removes the last reason to
concede error control to the one procedure that escapes the §4.13 template.
*Retires:* "you identified a known problem and ignored its known solution."

**H8. Label-noise interval and audit.** `[DONE 26 Aug; manual pass OPEN]` — §4.27. Measured
label inconsistency on LSPR23 is **0.0042%** (byte-identical feature vectors carrying
disagreeing labels), roughly three orders of magnitude below CIC's 6.67–7.53%. FDP reported
as an interval: e-LOND [0.0245, 0.0998], ADDIS [0.0304, 0.1057] over ε ∈ [0, 0.0753]². At
LSPR23's measured level the correction is immaterial; at CIC level q = 0.05 could not be
certified. A 152-alert audit sample is emitted to `out/h8_audit_sample.csv`; the manual pass
needs the exercise ground truth and stays `[OPEN]`.
*Retires:* "your FDP is measured against labels you never validated."

## Tier 3 — expensive, judgement call `[~3–5 days]`

**H9. Second dataset.** No drop-in option exists (T11). The three routes each cost 3–5 days
and each introduces a caveat. Alternative that costs nothing: reframe LSPR23's five window
positions as five quasi-independent deployments and say so explicitly — weaker than a second
dataset, but honest and already done.

**H10. A second feedback-controller design.** §4.14 sweeps η and window for one proportional
controller. A different form (integral term, or direct quantile targeting) would show the
comparison is not controller-specific.

## Items from the external review, not in the original Phase 2 list

**Compound-e / e-closure comparator** (review Priority 1, item 3). `[DONE 26 Aug]` — §4.28;
new finding F15. Boosting, the strongest general power-recovery technique for e-value
procedures, is **exactly vacuous** on threshold conformal evidence: `b* = 1` for any
two-point e-value, against `b* = √(2τ)` for a genuine continuous one. On real scores the
optimal factor is below 1 (median 0.368) because the measured benign firing rate exceeds
nominal. e-closure needs several e-values per hypothesis; here the aggregation step *is* the
compound operation, which §4.16's theorem already covers. This closes the review's Priority 1.

**Problem-space padding variants** (review Priority 5). Protocol-matched, service-matched and
black-box pools added to §4.17's generic and attacker-origin pools, with the cost restated as
the pads needed to suppress with probability ≥ 0.90 rather than in expectation — §4.30.

**Standing caveat introduced by these runs.** The rejection threshold `τ = T/w₀` and the
horizon-uniform γ both use `T`, the number of episodes in the evaluation window. That is
horizon knowledge, and it is the same oracle labelled in §4.20. It is disclosed wherever it
is used; §4.20's horizon-misspecification sweep quantifies what mis-stating it costs.

## Suggested order

H6 `[DONE]` → H1 → H2 → H7 → H3 → H4 → H5 → H8, with H9/H10 only if time remains after
drafting begins. H6 was taken first because it was the only remaining task that could
*falsify* a current claim; it did narrow F1, so the narrowed statement is what the rest of
Phase 2 must stay consistent with.

**New item raised by H6, not in the original Phase 2 list.** §4.20 shows the spending
sequence γ moves the realised operating point by 2.0× in recall — a larger effect than the
error target q has. H3 (sweep q) must therefore be run as a **joint sweep over (q, γ)**, not
over q alone, or it will attribute to q an effect that belongs to γ. Every result quoting an
operating point must name its spending sequence.

# 13. Phase 3 — credibility closure and the final security experiment

From `11_next_actions_updated_experiments.md`. All three are done; the experiment matrix is
frozen (§14).

**A1. Diagnose the position-0.85 anti-conservatism.** `[DONE 26 Aug]` — §4.31; **F9
rewritten**. The cause is a **localised label error**, not drift. Exactly 46 benign-labelled
flows of 1,638,722 fire at seed 0, and **three host pairs of 25,864 carry 44 of them**;
removing those three takes the ratio from 50.90× to **2.22×**, inside the 1.07–3.79× range
of the other four window positions. The flows are periodic outbound TLS from an internal host
to one external address, and LDAP / Global Catalog enumeration from a red-team
confirmed-compromise host against internal domain controllers — post-compromise activity that
endpoint-identity labelling cannot mark. The other two candidate explanations are ruled out
directly: 0.00% of tail hosts and services are unseen in calibration (so not a new benign
mode), 0 of 46 collide with any malicious flow (so not duplicated records), and the
measured/nominal ratio decays 50.9 → 1.44 as the rank k grows (so not a moved distribution).
Two repairs measured: **Mondrian conformal makes it worse** (per-stratum ceilings 4–769,720,
margin +0.436 → −1.000…−0.842); excluding the dominant service stratum halves it and does not
fix it. *Retires:* "your headline window does not satisfy the validity condition and you don't
know why."

**A2. Manually audit the alert sample.** `[DONE 26 Aug]` — §4.32; new finding **F16**. The
Locked Shields red team's own task record is in the repository —
`data/lspr23_attacknarratives.json`, 83 machine-readable compromise reports covering 39 IPv4
addresses and 295 timestamped step submissions — and is independent of the `Label` column.
A pre-registered rule adjudicates all 152 alerts: **96.1% agreement, no alert ambiguous,
98.0% under the stricter rule**. All **five** alerts the label calls false carry independent
evidence of being real attack traffic, and three involve a confirmed-compromise host — the
same host pairs A1 found from the score tail, reached independently. **Measured FDP is
therefore an over-estimate**, not an under-estimate. The audit is self-critical about its own
evidence: the discriminative indicator separates 94.7% from 1.0%, temporal concurrency
separates 100.0% from 86.0% and is useless. What stays open is a human pass with the exercise
scoring system; `out/a2_audit_adjudicated.csv` reduces it to reviewing an adjudication.
*Retires:* "your FDP is measured against labels you never validated."

**B1. ADDIS spending-state manipulation attack.** `[DONE 26 Aug]` — §4.33; new finding
**F17**. **The attack works and is exact.** `B*` has a closed form verified against the
`h6_procs` implementation itself, and on the real stream **B = 202 leaves all 152 rejections
intact while B = 203 leaves none, permanently**. It survives grey-box (a ±33% estimate of
`|C|` suffices; the admissible group size is a `τ/λ`-wide interval) and needs only 36×
over-provisioning when the controller state is unknown. Black-box is blocked on *this* stream
by the very anti-conservatism A1 diagnoses. **It is not cheap in absolute terms** — 9.2×10⁷
flows, 5.6× the whole dataset — and the price is set by the calibration budget,
`λ|C|·[(τ−λ)w₀|C|]^0.625/k^1.625`. Two things make it matter anyway: against ADDIS it is the
**cheaper** attack (break-even at 2.7 episodes; the window holds 255), and for **101 of ADDIS's
147 detections the minimal suppressing pad also advances the index**, so the two attack
surfaces are one operation.

**Decision gate (next_actions §18): the attack works, so the paper is the strongest version —
feasibility + granularity tradeoff + two attack surfaces.** The claim to make is structural:
any procedure that escapes α-death by conditioning its spending index on a property of the
observed evidence exposes that property to the adversary, at a price fixed by the calibration
budget.

---

# 14. Experiment matrix — freeze LIFTED, see `02_WORKPLAN_PHASE4.md`

> **Superseded 26 Aug 2026.** The freeze below held for about an hour. Two external reviews
> arrived: `07_phase3_next_step_recommendation.md` (start writing) and
> `08_satml_reviewer_gap_experiment_checklist.md` (close five P0 reviewer gaps first). With a month
> to the deadline the decision was to **finish all experiments before writing**, so the matrix is
> reopened for exactly the twelve items in **`02_WORKPLAN_PHASE4.md`**, which is now the active
> tracker. Nothing outside that queue is in scope, and the text below still records what was
> frozen and why.

## 14.1 The original freeze note

A1, A2 and B1 are done. **No further core experiments.** See `03_FROZEN_CLAIMS.md` for the
accepted headline claims, supporting claims, caveats and non-claims, and `05_PAPER_CONTRACT.md`
for the one-page contract the manuscript is written against.

Only two things may still be added, and only against a concrete objection:

1. a second dataset with genuine flow→campaign labels (§7 item 2) — the only open item that
   could change a headline number;
2. a second feedback-controller design (§7 item 3) — a robustness check.

Not to be added: more classifiers, more online FDR procedures, more spending sequences, more
cap variants, more q sweeps, more grouping families, more padding pools.

---

## Standing rule for Phase 2

Every result added here goes through the same audit as T1–T11 before it enters the record.
Four independent blind audits have so far found roughly thirty defects, two of which had
inverted a headline conclusion. The audit is not optional overhead; it is what the numbers
rest on.
