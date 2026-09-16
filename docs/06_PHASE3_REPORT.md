# Phase 3 Report — Response to `11_next_actions_updated_experiments.md`

**26 Aug 2026.** Written for review. Every number here is reproducible from
`proto/out/t3{0,1,2}_B1.json` / `t3{0,1}_A{1,2}.json` and the run logs beside them; the
authoritative record is `04_EXPERIMENTS_AND_FINDINGS.md` §4.31–§4.33.

This document exists so the plan can be checked against what was actually done, including
the places where a result is weaker than it first appeared and the places where the plan asked
for something that was not delivered. §9 lists the questions I would most like an answer to.

---

# 0. Disposition of every item in the plan

| Plan § | Asked for | Status | Where |
|---|---|---|---|
| §1, §17-A1, §20 | Diagnose the position-0.85 anti-conservatism | **Done** | §4.31, F9 rewritten · `t30_A1_tailforensics.py` |
| §2, §17-A2 | Manually audit the ~152-alert sample | **Done, with a residual** | §4.32, new F16 · `t31_A2_alertaudit.py` |
| §3–§6, §17-B1 | ADDIS spending-state manipulation attack | **Done — the attack works** | §4.33, new F17 · `t32_B1_addis_state.py` |
| §7, §17-C | Freeze the experiment set | **Done** | `09_WORKPLAN_phases1-3.md` §14 |
| §8, §9, §11, §12, §13, §19 | Freeze three contributions, demote the rest, thesis, RQs, figures, title | **Done** | `03_FROZEN_CLAIMS.md`, `05_PAPER_CONTRACT.md` |
| §10, §17-D | One-page paper contract | **Done** | `05_PAPER_CONTRACT.md` |
| §18 | Decision gate after the ADDIS experiment | **Resolved: it works** → strongest version of the paper | below, §3.6 |
| §14 | Second dataset, in parallel, not a blocker | **Not done, deliberately** | §6.1 |
| §15 | Second feedback controller, low priority | **Not done, deliberately** | §6.2 |
| §16 | What not to do | **Complied with** | §6.4 |
| §17-E | Begin the manuscript | **Not started** — was not in scope for this phase | §6.3 |

Three items in the plan's inspection lists were **not** covered and are flagged as gaps, not
silently dropped: near-duplicate (as opposed to exact-duplicate) detection, per-feature
distribution comparison, and the "proximity to attack periods" metric, which turned out to be
degenerate on this window. All three are in §1.5.

---

# 1. A1 — the position-0.85 anti-conservatism

## 1.1 What the plan asked

> Extract all benign-labelled deployment flows satisfying `s(x) > max_{z∈C} s(z)`. Then compare
> them with ordinary benign flows. […] The goal is to distinguish between three explanations:
> distribution shift / systematic label error / new benign traffic mode.

with a thirteen-item inspection list, and a decision rule: if the cause is identifiable,
explain it and correct/stratify/recalibrate or treat it as a deployment-shift case study; if
not, move the headline comparison elsewhere and keep 0.85 as an explicit failure case.

## 1.2 Coverage of the thirteen-item inspection list

| Asked | Done | Result |
|---|---|---|
| source IP | yes | 4 distinct hosts in the tail of 728 in benign traffic; top-1 share **73.9%** |
| destination IP | yes | 5 distinct of 9,561; top-1 share 73.9% |
| source and destination port | yes | dport: 3 values, top-1 **78.3%** (443); sport: 42 values, top-1 6.5% — dispersed, as expected for ephemeral ports |
| protocol | yes | one value (`L3/L4 Protocol` = 0) for 100% of the tail |
| service | yes | 3 values, top-1 **78.3%** (TLS); LDAP present |
| timestamp | yes | full UTC timestamps in `out/a1_extreme_tail_seed{0,1}.csv`; **39 of 46 flows in the last two deciles** of the 2.4 h window |
| does the source appear in malicious traffic | yes | **78.3%** of tail flows, against a **29.7%** benign baseline; unchanged when restricted to flows *before* the deployment window (26.1% baseline) |
| does the destination appear in malicious traffic | yes | 21.7% against 28.4% — *below* baseline |
| proximity to attack periods | yes, **but the metric is degenerate** | seconds-to-nearest-malicious-flow is p10/median/p90 = 0.0/0.0/0.0 for both the tail *and* ordinary benign flows: the window is saturated with attack traffic, so temporal proximity carries no information here. See §1.5 |
| duplicated records | **exact only** | 0 of 46 byte-identical to any malicious flow anywhere in the stream; 0 of 46 identical to any of 1,813,113 calibration benign flows; 46 distinct feature vectors, largest repeat 1. **Near-duplicate detection was not done** — see §1.5 |
| network segment | yes | seg_src: 3 values, top-1 76.1% (`beg_int`); seg_dst: 2 values, top-1 78.3% |
| feature distributions | **partial** | the score's distance past the ceiling is characterised (median gap = 2.04× the top calibration order-statistic spacing, 0.143× the calibration IQR; 34.8% of the tail within one spacing). **Per-feature comparison of tail vs benign vs malicious was not done** — see §1.5 |
| does a single service/class dominate | yes | HHI by service **0.651**, by dport 0.636, by src→dst pair 0.575; 2 services cover 90% of the tail |

## 1.3 What was found

**The tail is 46 flows out of 1,638,722 benign test flows at seed 0** (22 at seed 1), and it is
extremely concentrated:

| src → dst | flows | service / dport | direction | pattern |
|---|---|---|---|---|
| 10.5.1.3 → 100.101.1.32 | 34 | TLS / 443 | internal → **external** | 15:12–15:41 UTC, one flow every 20–60 s, source ports incrementing monotonically 54057 → 54423 |
| 100.96.5.5 → 10.5.1.2 | 7 | LDAP / 389 and Global Catalog / 3268 | DMZ → internal | directory enumeration |
| 100.96.5.5 → 10.5.1.3 | 3 | Global Catalog / 3268 | DMZ → internal | directory enumeration |
| 10.5.1.2 → 100.101.1.24 | 1 | TLS / 443 | internal → external | — |
| one IPv6 pair | 1 | TLS / 443 | internal → external | — |

**100.96.5.5 and 10.5.1.2 both appear in the red team's own confirmed-compromise list**
(the external source described in §2). 10.5.1.3 is the LDAP / Global Catalog / Kerberos target,
i.e. a domain controller.

**The inflation is localised in three host pairs of 25,864.** Removing them:

| pairs removed | tail covered (seed 0) | ratio to nominal | seed 1 |
|---|---|---|---|
| 0 | 0/46 | **50.90×** | **24.34×** |
| 1 | 34/46 | 13.28× | 7.75× |
| 2 | 41/46 | 5.54× | 5.54× |
| 3 | 44/46 (96%) | **2.22×** | 4.43× |
| 5 | 46/46 | 0.00× | 2.22× |

The other four window positions measure **1.07–3.79×**, so removing three host pairs puts 0.85
inside the range of every other position. This is `[ORACLE]` — the pairs are chosen from the
test-split score tail, so it measures how *localised* the cause is, not a deployable fix.

**Discrimination between the three explanations:**

| candidate | verdict | basis |
|---|---|---|
| new benign traffic mode | **not supported** | 0.00% / 0.00% / 0.00% of the tail's src hosts / dst hosts / (service, dport) pairs are unseen in the benign calibration window (seed 1: 0 / 0 / 4.55%), against 1.22% / 0.67% / 0.14% for ordinary benign flows |
| duplicated records | **ruled out** | 0 exact collisions with malicious traffic; every tail vector distinct |
| broad distribution shift | **not the primary explanation** | measured/nominal `P(rank ≤ k)` decays 50.90 → 9.18 → 4.49 → 6.80 → 2.05 → **1.44** across k = 1 … 10⁵ (seed 1: 24.34 → 1.51). A uniformly moved distribution would keep the ratio flat in k |
| systematic label error | **best supported, not proved** | see §1.4 |

**Two repairs, both measured, neither works:**

| repair | oracle? | fire rate | `E[e\|benign]` | feasibility margin |
|---|---|---|---|---|
| baseline | — | 2.807×10⁻⁵ | 50.90 | +0.436 |
| Mondrian (stratified) conformal by `Service` | no | 9.337×10⁻⁵ | 21.66 | **−1.000 … −0.842** |
| Mondrian by `Conn_state` | no | 9.825×10⁻⁵ | 20.11 | **−1.000 … −0.753** |
| drop dport 443 from calibration *and* deployment | `[ORACLE]` | 6.911×10⁻⁶ | 11.07 | +1.587 |

**Mondrian conformal makes it worse.** Stratifying shrinks each stratum's calibration set, so
the per-stratum ceiling collapses from 1,813,114 to a range of 4 … 769,720 and the per-episode
feasibility margin goes from +0.436 to between −1.000 and −0.842. The conditional-validity
gain is real and is paid for in exactly the currency §4.26 predicted: the evidence ceiling.

## 1.4 The decision rule from §1, and which branch we took

The plan's rule was binary. The honest answer is neither branch cleanly:

- **The cause is identified to the level of named host pairs and named protocols**, and the
  pattern (Global Catalog / LDAP enumeration from a red-team-confirmed compromised host to
  internal domain controllers; periodic outbound TLS with incrementing source ports from
  internal hosts to single external addresses) is post-compromise activity by description.
- **The mechanism that would produce the mislabel is specific and checkable**: LSPR23's
  labelling attributes flows to the red team by *endpoint identity*, so it cannot mark actions
  taken by a compromised **blue-team** host. All 46 tail flows carry `Label_src = Label_dst = 0`,
  which is consistent with that.
- **But it is not proved.** A distribution shift confined to the extreme tail would produce the
  same rank-depth profile and the same concentration. Nothing available separates the two
  without the exercise's own logs.

So the record takes a deliberately narrower position than the plan's first branch: **the excess
is localised, reproducible, identified down to named host pairs, and consistent with
mislabelled post-compromise traffic** — and position 0.85 is presented as a case study in
*evidence validity collapsing under label error*, with the residual uncertainty stated. The
FDP numbers there remain measurements against labels, and §2 establishes their **direction**.

**Effect on the other conclusions: none, and in the conservative direction.**
Anti-conservative evidence can only make procedures fire *more*, so every infeasibility and
silence result at position 0.85 is conservative.

## 1.5 Gaps in A1 — flagged, not hidden

1. **Near-duplicate detection was not done.** Only exact byte-identical feature-vector
   collisions were tested. A near-duplicate test (e.g. nearest-neighbour distance in
   standardised feature space to the nearest malicious flow) would strengthen or weaken the
   label-error reading and is cheap on a 46-flow tail. *This is the gap I would close first.*
2. **Per-feature distribution comparison was not done.** The plan asked for it; what was
   delivered is a score-space characterisation only. A per-feature tail-vs-benign-vs-malicious
   comparison would say whether the tail flows look like attack traffic in feature space, not
   just to the detector.
3. **"Proximity to attack periods" is uninformative on this window** and should not be quoted:
   the deployment window is saturated with labelled-malicious traffic, so both the tail and
   ordinary benign flows have a nearest malicious flow at distance 0.0 s. A useful version
   would need attack *episodes* or exercise phases rather than flows.
4. **The external host-identity test does not adjudicate on its own** and this is stated in the
   record: 11 of 46 tail flows (23.9%) touch a confirmed-compromise host against an **18.5%**
   base rate — an enrichment of essentially 1×, because a compromised host also sends a great
   deal of ordinary traffic. Excluding those flows moves the ratio only 50.90 → 47.51.

---

# 2. A2 — the alert audit

## 2.1 What the plan asked

Five verdict levels; record timestamp, source/destination, service/protocol, detector score,
grouping identifier, dataset label, analyst judgement, evidence; **cross-reference the Locked
Shields exercise documentation if possible**; report agreement rate, clearly incorrect labels,
ambiguous fraction, and qualitative causes of disagreement.

## 2.2 What made this possible

The exercise documentation was already in the repository and had been written off as
unusable. `proto/data/lspr23_attacknarratives.json` contains **288 narratives**, of which:

- **83 carry a machine-readable compromise report** — hostname, IP list, timestamp,
  privilege flag — covering **39 IPv4 addresses**;
- **295 timestamped red-team step submissions**, spanning **07:03–15:08 UTC on 9 Mar 2023**,
  of which **20 fall inside the deployment window** (13:17–15:41 UTC).

These cannot be joined to individual flows — so they still cannot supply campaign labels, and
the "episode, never incident" rule stands. They *can* be joined on host IP and on time, which
is what the audit does. Crucially, they are produced by the attackers, **not** by the
flow-labelling pipeline, so they are independent of the `Label` column being audited.

## 2.3 The evidence tiers, and their honest provenance

| tier | content | independence |
|---|---|---|
| **E1** | endpoint is a red-team confirmed-compromise host; red-team step submissions within ±15 min of the episode's span | **fully external** — owes the audited labels nothing |
| **E2** | an endpoint, or the targeted (service, dport), carries labelled-attack traffic in *other* episodes, with this episode's own contribution subtracted exactly over its whole `(src, dst, bucket)` group across the entire stream | independent of **this episode's** label, **not** of the labelling process |
| **E3** | the `Label` column | the thing being audited |

The rule is pre-registered (fixed before the numbers were seen) and uses E1 and E2 only.

## 2.4 The four outputs the plan asked for

**(a) Agreement rate.** 152 alerts adjudicated; **146 agree = 96.1%**, with **0 ambiguous**.
Under a `[POST-HOC]` strict rule that keeps only the two discriminative branches: 148 called
malicious, 145 of them also labelled malicious = **98.0%**.

| verdict | n | % | label = malicious | label = benign |
|---|---|---|---|---|
| clearly malicious | 49 | 32.2% | 46 | 3 |
| probably malicious | 102 | 67.1% | 100 | 2 |
| ambiguous | 0 | 0.0% | — | — |
| probably benign | 1 | 0.7% | 1 | 0 |
| clearly benign | 0 | 0.0% | — | — |

**(b) Clearly incorrect labels.** Six disagreements, all listed in full in §4.32. Five run one
way — alerts the label calls **false** that carry corroborating evidence of being real attacks:

| rank | src → dst | flows | service | E1 | verdict |
|---|---|---|---|---|---|
| 14876 | 100.96.5.5 → 10.5.1.2 | 1,078 | LDAP / 389 | ✔ | clearly malicious |
| 15147 | 100.96.5.5 → 10.5.1.3 | 1,152 | krb5 / 88 | ✔ | clearly malicious |
| 28006 | 10.5.1.2 → 100.101.1.24 | 188 | TLS / 443 | ✔ | clearly malicious |
| 26766 | IPv6 pair | 13 | TLS / 443 | ✘ | probably malicious |
| 27820 | 10.5.1.3 → 100.101.1.32 | 563 | TLS / 443 | ✘ | probably malicious |

**These are the same host pairs A1 identified from the score tail, reached from a completely
different direction.** That convergence is the strongest single piece of evidence in either
experiment. The one disagreement in the other direction (rank 23253, labelled malicious,
verdict "probably benign") is an episode whose source sends attack traffic in no other episode,
so the rule declines to corroborate it — that is the rule being conservative, not evidence
against the label.

**(c) Ambiguous fraction.** 0.0%. That is a property of the rule, not a strength: with only
four indicators and a permissive branch, almost everything resolves. The informative statistic
is the rule's own false-call rate, below.

**(d) Qualitative causes of disagreement.** All six trace to one cause: **the labelling marks
flows by red-team endpoint identity, so traffic originating from a compromised blue-team host
is labelled benign.** Every one of the three strongest disagreements is a compromised host
performing directory enumeration or outbound TLS against/through a host the red team reported
owning.

## 2.5 The audit auditing itself

The plan did not ask for this and it changed the conclusion, so it is worth calling out. The
same rule was run on control sets the procedures did **not** alert on:

| set | n | E1 host | E2 either | **E2 both** | concurrent | rule says malicious | strict rule |
|---|---|---|---|---|---|---|---|
| alerted | 152 | 32.2% | 99.3% | **94.7%** | 100.0% | 99.3% | 97.4% |
| not alerted, labelled malicious | 108 | 15.7% | 98.1% | 75.9% | 87.0% | 96.3% | 81.5% |
| not alerted, labelled benign | 300 | 16.3% | 52.0% | **1.0%** | 86.0% | **46.7%** | **15.7%** |

- **E2 on both endpoints is highly discriminative**: 94.7% against 1.0%, a 95× enrichment.
- **Temporal concurrency is nearly useless**: 100.0% against 86.0%, because the entire window
  sits inside the exercise. The branch that relies on it is what pushes the rule's false-call
  rate on benign controls to 46.7%.

So the pre-registered rule over-calls, and the record says so and reports the strict variant
(15.7% false-call rate) alongside it.

## 2.6 FDP, in three tiers

| method | R | FDP by label | E1+E2 rule | strict E1+E2 | **external-only (E1)** |
|---|---|---|---|---|---|
| e-LOND, horizon-uniform γ | 151 | 0.0265 | [0.0066, 0.0066] | [0.0000, 0.0265] | [0.0132, 0.6821] |
| ADDIS, γ ∝ j^−1.6 | 152 | 0.0329 | [0.0066, 0.0066] | [0.0000, 0.0263] | [0.0132, 0.6776] |

I originally reported only the middle column and concluded "measured FDP is an over-estimate".
That was too strong, because E2 is computed from the very label column being audited — it is
independent of each episode's own label but not of a systematic bias in the labelling process,
which is precisely the failure mode A1 suspects. The record now reports all three tiers. The
claim that survives:

> **The label-derived FDP is not an under-estimate, and the specific alerts it counts as false
> are individually documented with their evidence.** Without circularity, what is established
> is that **3 of the 5** label-false alerts sit on a red-team confirmed-compromise host — a fact
> a reader can check against the narrative file directly.

## 2.7 What remains open

A human pass with the full exercise scoring system. `out/a2_audit_adjudicated.csv` carries all
152 alerts with every evidence field, the machine verdict, its reason, and blank
`human_verdict` / `human_notes` columns, so the remaining step is reviewing a documented
adjudication rather than starting from nothing.

One deviation from the plan's field list: the CSV records the **episode e-value** rather than a
per-flow detector score, because the alerting unit is the episode. Per-flow scores are
available but were not exported.

---

# 3. B1 — the ADDIS spending-state manipulation attack

## 3.1 What the plan asked

Define `B` = number of attacker-generated precursor groups with `p ∈ (λ, τ]`; find
`B* = min B` such that a later target attack is no longer detected; measure
`P(target detected | B)`; test four objectives (A suppress, B delay, C force structural
silence, D reduce campaign recall) and three knowledge levels (white / grey / black-box); if it
works, make it a core security contribution.

## 3.2 Mechanism and the closed form

ADDIS indexes its spending sequence by `D_t = #{i < t : λ < P_i ≤ τ}` — hypotheses **selected
but not candidates**. Under threshold conformal evidence at k = 1 an episode p-value is either
exactly 1 (discarded, never selected) or small enough to be a candidate, so `D_t ≡ 0` and the
level never decays. That is the escape §4.20 found. An adversary who manufactures episodes with
`p ∈ (λ, τ]` advances `D` at will, and such episodes are **never rejected** (`p > λ ≥ α_t`), so
they cost the attacker no discoveries.

> `B*(R)` = the smallest integer `D` with
> `D + 1 > [ (τ−λ)·W·(|C|+1) / (k·ζ(1.6)) ]^{1/1.6}`,
> with `W = w₀` before the first rejection and `W = αR` after `R` of them.

**Verified against the implementation rather than against a re-derivation.**
`t33_selftest_A1A2B1.py` asserts that `h6_procs.run_addis` reports its first infeasible step at
exactly `R + B*(R) + 1`, at four calibration sizes × four values of `R` — sixteen cells, all
passing.

| prior rejections R | 0 | 1 | 2 | 10 | 50 | 152 |
|---|---|---|---|---|---|---|
| `B*` numeric | **203** | 314 | 485 | 1,326 | 3,626 | 7,266 |
| `B*` closed form | **203** | 314 | 485 | 1,326 | 3,626 | 7,266 |

## 3.3 The four objectives

| B | flows spent | rejections | recall | **P(target detected)** | silent | first true detection |
|---|---|---|---|---|---|---|
| 0 | 0 | 152 | 0.576 | 1.000 | 0.0% | rank 4 |
| 200 | 90,655,800 | 152 | 0.576 | 1.000 | 0.0% | rank 4 |
| 202 | 91,562,358 | 152 | 0.576 | 1.000 | 0.0% | rank 4 |
| **203** | **92,015,637** | **0** | **0.000** | **0.000** | **99.4%** | **never** |
| 512 | 232,078,848 | 0 | 0.000 | 0.000 | 99.4% | never |

- **A. Suppress detection** — achieved completely: `P(target detected)` goes 1.000 → 0.000.
- **B. Delay detection** — **measured, and the answer is that no delay regime exists.** The
  first true detection is at rank 4 for every `B ≤ 202` and never for every `B ≥ 203`. The
  attack is all-or-nothing, because the level is a deterministic function of `D` and the
  feasibility test is a threshold. This is a negative answer to a question the plan asked, and
  it is worth stating as such rather than omitting.
- **C. Force structural silence** — achieved, and it is **absorbing**: `D` never decreases, so
  once the level is under the conformal floor no later episode can recover it. Verified
  directly (200 ceiling-valued episodes after the precursors yield zero rejections).
- **D. Reduce campaign recall** — 0.576 → 0.000. Per-target `B*` over all 147 episodes ADDIS
  detects: **min 203, median 4,024, max 7,176**, i.e. 9.2×10⁷ to 3.3×10⁹ flows. The cost rises
  with the target's position because ADDIS banks wealth as it rejects, so the front-loaded
  attack is both the cheapest and the only one a realistic adversary would mount.

## 3.4 Cost, and the three knowledge levels

An episode of `n` flows containing `m` ceiling-reaching flows has `Ev = CEIL·m/n`, so
`p ∈ (λ, τ]` ⟺ `n ∈ (λ·CEIL·m, τ·CEIL·m]`. The cheapest precursor takes `m = 1`:
`n ∈ (453,278, 906,557]`, i.e. **453,279 flows per precursor**, and
`203 × 453,279 = 92,015,637` flows total — **5.6× the entire 16.35M-flow dataset**.

| `\|C\|+1` | 10⁴ | 10⁵ | 10⁶ | 1,813,114 | 10⁷ |
|---|---|---|---|---|---|
| `B*` | 7 | 33 | 140 | 203 | 592 |
| flows / precursor | 2,501 | 25,001 | 250,001 | 453,279 | 2,500,001 |
| **total flows** | 17,507 | 825,033 | 35,000,140 | **92,015,637** | 1,480,000,592 |

Cost scales as `λ|C|·[(τ−λ)w₀|C|]^{0.625}/k^{1.625}` — **the same quantity that buys feasibility
buys resistance to this attack**, super-linearly. It falls fast in `k`, but every `k > 1` is
already infeasible (F14), so the attacker cannot reach the cheap regime. `(λ, τ)` also price
it: λ = 0.05 costs 26,652,864 flows; λ = 0.4 costs 83,403,290.

| setting | works? | detail |
|---|---|---|
| **white-box** (λ, τ, k, `\|C\|`, state) | yes | sets `n = 453,279`, `m = 1`; every precursor lands in the window |
| **grey-box** (procedure + parameters only) | **yes** | the admissible size is an interval `τ/λ = 2×` wide, so a `\|C\|` estimate within **[0.667, 1.333]** suffices — a ±33% tolerance. Unknown state costs only over-provisioning: `B*(R=152)/B*(R=0) = 36×` |
| **black-box** (no detector access) | **no, on this stream** | at the *nominal* firing rate the per-group success probability is 0.195–0.303, so a well-calibrated stream would cost ≈5× the white-box budget. Here, with the firing rate estimated on the first half of the window and the attack priced on the held-out second half, `CEIL·f = 94.2` against `1/λ = 4.0`: an ordinary-looking group of the required size lands *past* the window, not inside it |

The black-box result is worth reading carefully: **the attack is blocked by the very
anti-conservatism A1 diagnoses.** That is not a defence anyone would choose or could rely on.

## 3.5 Two findings the plan did not anticipate

**(a) Against ADDIS, state manipulation is the *cheaper* attack.** Padding priced against the
levels ADDIS actually offered — traced out of `run_addis` itself via a new `levels=` output
parameter, running 2.734×10⁻³ up to the λ cap:

| attack | flows |
|---|---|
| suppress one detected episode by padding (median) | 34,465,311 |
| suppress all 147 detected episodes | 127,485,670,015 |
| **silence the controller permanently** | **92,015,637** |

Break-even is **2.7 episodes** — from the third onward, state manipulation wins. This window
holds 255. The reason is the same property that makes ADDIS escape §4.13: a procedure that
spends a large level per hypothesis has a *low* rejection threshold, so it is hard to suppress
by dilution and cheap to defeat through the state that keeps the level large.

**(b) The two attack surfaces coincide.** ADDIS caps its level at λ, and the state-advancement
window **starts** at λ. Wherever the cap binds, the cheapest padding that suppresses an alert
lands the episode in `(λ, τ]`:

- **101 of the 147** detected episodes have `α_t = λ` exactly;
- for **all 101**, the minimal suppressing pad puts the episode inside `(λ, τ]`.

So for 69% of ADDIS's detections, suppressing the alert *also* advances the spending index —
the two attack surfaces are one operation and the state attack comes free with the padding
attack. This does not hold for e-LOND, whose level is five orders of magnitude smaller.

## 3.6 §18's decision gate

**The attack works**, so the plan's strongest version is available: feasibility + granularity
tradeoff + two attack surfaces. But the claim I would make is structural rather than
operational, because 9.2×10⁷ flows is not an operational threat on this network:

> Any procedure that escapes α-death by conditioning its spending index on a property of the
> observed evidence exposes that property to the adversary, and the price of the exposure is
> fixed by the calibration budget.

---

# 4. Phase C — the experiment matrix is frozen

`09_WORKPLAN_phases1-3.md` §14. `03_FROZEN_CLAIMS.md` records what may be asserted and at what strength:
**3 headline claims** with their boundary conditions, **11 supporting claims**, **7 caveats that
must travel with their numbers**, **10 explicit non-claims**, and **8 refuted hypotheses** to be
reported as negative results.

Two additions are still permitted, and only against a concrete objection: a second dataset with
genuine flow→campaign labels, and a second feedback-controller design. Explicitly excluded:
more classifiers, more procedures, more spending sequences, more cap variants, more q sweeps,
more grouping families, more padding pools.

---

# 5. Phase D — the paper contract

`05_PAPER_CONTRACT.md`, one page, covering everything §10 asked for plus datasets, methods and
exclusions. Mapping to the plan:

| Plan asked | Contract has |
|---|---|
| §19 title | **When Guarantees Go Silent: Feasibility and Attackability of Online Error Control for ML Intrusion Detection**, with two fallbacks |
| §11 thesis | the plan's thesis, extended with the ADDIS clause the plan said to add if the attack worked |
| §8 three contributions | C1 feasibility theorem + boundary · C2 granularity–feasibility tradeoff · C3 two attack surfaces |
| §9 demotions | k=1 reliability, Bates cost, boosting vacuity, γ-vs-q — all in `03_FROZEN_CLAIMS.md` §B as supporting claims, none a contribution |
| §12 four RQs | RQ1 feasibility · RQ2 granularity · RQ3 attackability · RQ4 operational value, each pointed at its sections |
| §6 threat model | goal, capability, three knowledge settings, what is *not* assumed, cost metric, out-of-scope |
| §13 six or seven figures | four figures + two tables + one figure-or-table = **seven**, with an appendix list that does not count against it |
| §10 explicit non-claims | ten, reproduced from `03_FROZEN_CLAIMS.md` §D, to appear in the discussion rather than buried in limitations |
| — | plus: writing order, and a table of reviewer objections already retired with pointers |

---

# 6. What was deliberately not done

## 6.1 Second dataset (§14)
Not done. No drop-in option exists: ConCap is a generator (replaces live-fire data with
synthetic), AIT-LDSv2 needs label reconstruction from a 137 GB download, ProvAttack1/2 are
provenance graphs rather than flows. The zero-cost partial substitute the plan itself
suggests — five window positions as five quasi-independent deployments — is already computed
throughout. **This is the only open item that could still change a headline number.**

## 6.2 Second feedback controller (§15)
Not done; the plan called it low priority and a robustness check. §4.14 sweeps η and window for
one proportional controller.

## 6.3 Phase E manuscript (§17-E)
Not started. Phase D (the contract) was the stated stopping point before drafting.

## 6.4 Compliance with §16 "what not to do"
No new classifiers, no new datasets, no additional FDR procedures, no additional q sweeps, no
additional spending sequences, no new cap policies, no hyperparameter searches. The three
scripts added measure the three things the plan asked for and nothing else.

---

# 7. Verification history

The plan does not mention this, but it is where most of the elapsed effort went, and it changed
two conclusions.

**Round 1 — three blind adversarial audits, run before any experiment was executed** (per the
mandatory procedure in `10_HANDOFF_PHASE2.md` §6). Found, among others:

| bug | consequence if unfixed |
|---|---|
| benign firing rates computed as `((e > 0) & benign).mean()` — dividing by *all* test flows | every number in the A1 repairs table understated by the benign fraction |
| `(service, dport)` key aliased a missing port (−1) with port 0 | wrong novelty and E2-service counts |
| an episode could corroborate itself through the boundary time bucket | E2 contaminated for episodes at the window edges |
| padding priced at ADDIS's opening level rather than its actual level | per-episode padding cost understated by up to 91× |
| `mondrian()` crashed on an empty calibration stratum | run failure |
| the metadata alignment check was a sampled partition test that a block permutation would pass | silent host mis-attribution |

**Round 2 — a re-audit of the fixed code.** Confirmed all twelve fixes correct and complete,
and found seven more issues. Two were interpretive and are the reason §1.4 and §2.6 above are
narrower than my first write-up:

1. **E2 is derived from the `Label` column**, so calling the whole audit "independent evidence"
   was too strong → three-tier reporting, and the claim restated as "not an under-estimate".
2. **§4.31 overstated "label error rather than distribution shift"** → softened to
   "best-supported explanation, not proved", with the seed-1 figures (4.55% unseen service)
   included rather than only seed 0's zeros, and the weak external-host enrichment stated.

Five were mechanical (an exclusive interval boundary, a self-test path relative to `cwd`, a
misleading comment, an unguarded empty-array path, a print statement that had drifted next to
the wrong block). All fixed; both A1 and A2 re-run afterwards with numbers unchanged.

**Alignment verification.** `h_meta.verify()` requires the SrcPort/DstPort columns extracted for
the forensics to agree, **on all 16,353,511 rows**, with the ones `h_stream` extracted in a
separate independent pass, *and* requires the IP-string codes to induce the same host partition
as the cached host codes. It raises rather than warning. Both checks pass.

**Unit tests.** `t33_selftest_A1A2B1.py` — 40 assertions over the permutation direction, the
ADDIS closed form against the implementation (16 cells), the absorbing property, the precursor
size window at both endpoints, Mondrian conformal against a brute-force reference, marginal
validity averaged over 2,000 independent calibration draws, the `levels=` trace, the
(service, dport) key, and the episode index algebra. `t21b` (procedures) and `t22a` (stream
regression) also still pass.

One methodological note from this: an early version of the Mondrian validity test used three
calibration draws, saw 6 firings against an expected 3, and "failed". The deviation was pure
Poisson noise, and the test had no power to detect a rank off-by-one. It now averages over
2,000 strata. **A statistical check whose power you have not computed is not a check.**

---

# 8. What changed in the record

| Change | Where |
|---|---|
| **F9 rewritten** — "drift is mild" now holds everywhere; position 0.85 becomes a localised label-error case study rather than a drift case study | §1 findings |
| **F16 added** — the alert labels are not an under-estimate of truth | §1 findings |
| **F17 added** — the procedure that escapes the feasibility horizon exposes its spending state instead, and against it the two attack surfaces coincide | §1 findings |
| §4.31, §4.32, §4.33 added | ~19k characters |
| Claim-strength table | 7 rows added, 2 of them at **Moderate** rather than Strong |
| Open items | 3 of 5 closed; the residual human audit pass, the second dataset, the second controller, and one deliberate non-action (not rewriting LSPR23's labels) remain |
| Reproduction list | 4 scripts and one shared module (`h_meta.py`) added, with the one-off `awk` extraction |
| `10_HANDOFF_PHASE2.md` | marked superseded for task assignment; **4 new entries in the mistakes list**, including the two above and the underpowered-test lesson |

## Reproduction

```
proto/.venv/bin/python proto/t33_selftest_A1A2B1.py     # ~2 s, no data
proto/.venv/bin/python proto/t30_A1_tailforensics.py    # ~190 s  (10 detector fits)
proto/.venv/bin/python proto/t31_A2_alertaudit.py       # ~30 s
proto/.venv/bin/python proto/t32_B1_addis_state.py      # ~235 s  (~3,700 ADDIS runs)
```

Run from `proto/`. `h_meta.py` needs a one-off extraction from `proto/data/lspr23/`:

```bash
awk -F',' 'NR>1 {print $2","$3","$4","$5","$89","$91","$92","$93","$94","$96","$97","$98","$99}' \
    ls23pr_v1.csv > /tmp/lspr_meta.csv
```

---

# 9. Questions I would most like feedback on

1. **Is "localised anomaly, best explained by label error, not proved" the right resting place
   for A1?** The alternative readings are (a) assert label error and put the burden on a
   reviewer to disprove it, or (b) drop the interpretation and present only the localisation.
   The convergence with A2 on the same three host pairs is what makes me lean to the middle
   position, but it is a judgement call.
2. **Does the paper still use position 0.85 as its headline window?** The plan's fallback was
   to move the guaranteed comparison to a cleaner window and keep 0.85 as an explicit failure
   case. I did not move it, on the grounds that (i) anti-conservatism only makes procedures
   fire *more*, so every infeasibility result there is conservative, and (ii) it is the only
   position where the detector's tail reach is high enough for *any* procedure to fire, so
   moving would mean reporting a window with no detections. If that reasoning is wrong, the
   whole procedure-comparison table moves.
3. **Is the ADDIS attack a contribution at 9.2×10⁷ flows?** It is exact, grey-box-feasible,
   closed-form, and the cheapest attack against ADDIS — but 5.6× the whole dataset in absolute
   volume. My framing is structural ("escaping α-death by conditioning on the evidence exposes
   that property"). A reviewer could reasonably call it a curiosity.
4. **Is the coincidence of the two attack surfaces (§3.5b) the better headline than the state
   attack itself?** "For 101 of 147 detections, the cheapest suppression already advances the
   controller's state" is a stronger sentence than any of the cost numbers, and it needs no
   volumetric assumption.
5. **How much should the E2-provenance problem discount A2?** The informative indicator is
   label-derived; the label-independent one is weak (32.2% of alerts vs 16.3% of controls).
   96.1% agreement reads well but is partly self-referential.
6. **Which of the three A1 gaps in §1.5 is worth reopening**, given the matrix is frozen? My
   own ranking is near-duplicate detection first, per-feature distributions second, and the
   proximity metric not at all.
7. **Is the seven-item figure budget in `05_PAPER_CONTRACT.md` §7 the right seven?** In particular,
   whether the operational frontier (F5/T3) earns main-paper space or belongs in an appendix,
   which would free a slot for the two attack surfaces to get a figure each.
