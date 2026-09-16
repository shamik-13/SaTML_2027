# Prototype feasibility results

Ran 25 Aug 2026. Code in `proto/`, raw outputs in `proto/out/*.json`.
Tests 1–3, 5–6 are **simulation but exact** — they test arithmetic properties of the
procedures, not empirical hypotheses, so a real dataset cannot change them.
Test 4 is the only real-data test (AIT testbed NetFlows, 417,672 real flows).

---

## Headline: the plan needs one pivot, and the pivot makes it a much better paper

The revised outline treated **C1 (incident-level control)** as a *misalignment* argument
— event-level FDP measures the wrong thing — and **C2 (structural silence)** as a
*failure mode*. The prototype says both are far stronger than that:

> **Event-level online FDR control on security streams is not merely misaligned, it is
> arithmetically infeasible by 2–5 orders of magnitude. Incident-level aggregation is not
> an improvement, it is the only formulation that can work at all.**

That flips the paper from "here is when the guarantee fails" to an impossibility result
with a constructive escape. Sharper, more surprising, and much harder to scoop.

---

## Verdict per claim

| Claim | Status | Evidence |
|---|---|---|
| **C2** structural silence is real | ✅ **Far stronger than claimed** | LORD++ with \|C\|=10⁴ goes permanently unable to reject after **19 events**. Recall 0.000 at π≤10⁻³ even with a 5σ detector. |
| **C2** at real scale | ✅ **Impossible, not hard** | LSPR23 (16M flows): event-level needs a calibration set of **640,000,000** benign flows under the *best-case* γ; 3×10¹³ under the usual γ~j⁻¹·⁶. |
| **C1** aggregation is the fix | ✅ **Confirmed, dramatic** | Same stream: incident-level recall **0.000 → 1.000**, silence 100% → 0%. LSPR23 incident-level needs only **11,520** calibration flows. |
| **C1** e-value averaging valid under arbitrary dependence | ✅ Sound, but the obstacle moved | Valid by linearity of expectation — confirmed. Dependence is a non-problem. The binding constraint is calibration-conditional validity (below). |
| **C1** event-level FDP is domination-prone | ✅ Structurally confirmed | LSPR23: 1.6M malicious flows across **288** campaigns → mean 5,555 flows/campaign, so 55,556× redundancy. Needs the real per-campaign distribution to quantify. |
| **Finding 4 / §8** drift invalidates calibration | ⚠️ **Much weaker than claimed — do not build on it** | Real data, 5-day chronological split: anti-conservative by only **1.3–2.0×**, and *conservative* (0.86–0.93) at 10⁻²–10⁻³. Rolling calibration: 1.10–1.31. This is not a catastrophe and will not carry a section. |
| **C3** α-wealth exhaustion attack | ⚠️ Needs reframing | Moot at event level (already dead unaided). Survives in a *better* form at incident level: spurious incidents inflate T, which raises required \|C\| linearly. Quantifiable, cheap. |
| **C4** label-latency crossover | ⏳ Untested | Needs labelled real scores. ~2 days once data is in hand. |

## Two findings the plan did not have

**N1 — The evidence ceiling you need is exactly the one you cannot trust, and more data does not help.**
Online control needs a high evidence ceiling ⇒ small rank `k` in the conformal e-value.
Computed exactly (no Monte Carlo error), for the deployed single calibration set:

| k | ceiling | median E[e\|C] | P(E[e\|C] > 1) | p99 | invariant in \|C\|? |
|---|---|---|---|---|---|
| 1 | \|C\|+1 | 0.66–0.72 | **0.37** | **4.1–4.9** | **yes — 10⁴ and 10⁶ identical** |
| 10 | \|C\|/10 | 0.97 | 0.45 | 1.9 | yes |
| 1000 | \|C\|/1000 | 0.999 | 0.49 | 1.07 | yes |

So at the ceiling the procedures require, the guarantee is void ~37% of the time and off by
up to 5×, and **growing the calibration set from 10⁴ to 10⁶ does not improve it at all**
(the relative dispersion of the k-th order statistic depends on k, not on \|C\|).

**N2 — The operative quantiles are un-auditable.**
The procedures operate at p ≈ 10⁻⁶. With 137,832 held-out flows there were **2 events**
below 10⁻⁵ and none below 10⁻⁶. Verifying validity at 10⁻⁶ needs ~10⁷–10⁸ held-out benign
events. You are asked to trust a tail you cannot measure — a trustworthiness argument in
its own right, and a natural SaTML framing.

## The impossibility triangle (the paper's spine)

1. Stream of T hypotheses ⇒ test level α_T ≤ w₀/T at best (γ must sum to 1).
2. Rejecting anything needs evidence ceiling ≥ 1/α_T ⇒ **\|C\| ≥ T/w₀**.
3. High ceiling ⇒ small k ⇒ guarantee void ~37% of the time, and \|C\| does not fix it (N1).
4. Validity at those quantiles is unverifiable below ~10⁷ events (N2).
5. **Escape:** aggregate to incidents. T drops 10²–10⁵×, α_T rises correspondingly, a
   feasible \|C\| and a *reliable* k both become available.

## Feasibility envelope (measured)

Minimum calibration flows needed to be *able* to alert, best-case γ:

| Operating point | T | min \|C\| | Feasible |
|---|---|---|---|
| 1 hour @ 10k flows/s | 36M | 1.4×10⁹ | no |
| CIC-IDS2018 event-level | 18M | 7.2×10⁸ | no |
| LSPR23 event-level | 16M | 6.4×10⁸ | no |
| AIT wilson event-level | 418k | 1.7×10⁷ | borderline |
| incident-level, 50k incidents | 50k | 2.0×10⁶ | yes |
| **LSPR23 incident-level** | **288** | **11,520** | **yes** |

Incident-level at LSPR23 scale with a realistic detector (μ = attack-vs-benign separation
in benign SDs; \|C\|=10⁶, k=1):

| μ | incident recall | silence | note |
|---|---|---|---|
| 1.5 | 0.407 | 0% | hard families suppressed — the §16.6 question, now with a mechanism |
| 2.0 | 0.800 | 0% | |
| 3.0 | 1.000 | 0% | |
| 5.0 | 1.000 | 0% | |

With k=100 at μ=1.5, recall collapses to 0.006 with 90% silence — the N1 tension in action.
γ choice matters hugely: horizon-aware uniform γ needs 640M vs 3×10¹³ for γ~j⁻¹·⁶ at
event level. **Recommend horizon-aware γ** — a cheap practical contribution.

---

## Recommended pivot

**Retitle around the impossibility result.** Working title:
*"You Cannot Control False Discoveries Per Packet: Why Online Error Control for Intrusion
Detection Must Be Incident-Level"*

- **Promote C2 → central result.** It is exact, cheap, and reviewers can verify it in ten lines.
- **Promote C1 → the constructive escape**, with the feasibility envelope as the deliverable.
- **Add N1 and N2** as the trustworthiness core. They replace the drift story.
- **Demote drift/calibration-aging to a subsection.** Real data says ~1.3–2×, not catastrophe.
  Building §8 on it would have been building on sand.
- **Keep C3** but reframe: the attack inflates T (creating spurious incidents) rather than
  draining wealth, since at event level there is no wealth left to drain.
- **Keep C4.** Still the honest practical bound.

## Data status and effort

| Item | Status | Effort |
|---|---|---|
| AIT NetFlows (8 testbeds, real, timestamped) | ✅ downloaded, parsed, working | done |
| LSPR23 narratives — **288 campaigns, multi-step, phased** | ✅ downloaded, parsed | done |
| LSPR23 flows (1.9 GB, 16M flows, labelled) | ⏳ downloading (~64/1925 MB) | let it finish |
| AIT-ADS alerts (2.7 GB, 8 testbeds) | ⚠️ **downloaded but UNLABELLED** | labels must be reconstructed from AIT-LDSv2 attack windows (137 GB) — **3–5 days, real risk** |
| NF-*-v3 (UQ) | ❌ not scriptable — landing pages need a browser | manual download, ~1 hour |

**Recommendation: drop AIT-ADS from this submission.** It was the most novel dataset in the
plan, but label reconstruction is a multi-day dependency on a 137 GB download with five
weeks on the clock. LSPR23 already supplies what C1 needs — real multi-step campaign ground
truth — and its labels are ready. Defer AIT-ADS to the journal version.

Remaining to a submittable paper: LSPR23 end-to-end with a real detector and the 288 real
campaigns (~1 week), B6 controller (~2 days), C3 attacks (~3 days), writing (~1 week).
Fits, without AIT-ADS.

## Honest limitations of this prototype

- Tests 1–3, 5–6 are simulation. For the structural claims this is appropriate (they are
  properties of the procedures' arithmetic), but the **μ values are assumed** — real
  per-attack-family separation on LSPR23 is not yet measured, and it determines the recall
  column entirely.
- Test 4 used one testbed, 5 days, 418k flows, IsolationForest only. It cannot speak to
  10⁻⁶ (see N2) and it is not evidence about drift over months.
- The 1.6M/288 LSPR23 figures are published totals; the per-campaign flow distribution
  needed for the C1 domination figure requires the flows download to finish.
- LORD++ and LOND implemented exactly; SAFFRON/ADDIS not implemented. Their wealth
  bookkeeping differs, so per-procedure constants will differ — the T/w₀ scaling will not.
- Proposition 1's rate is confirmed for the two γ families tested; state it per-γ, not universally.
