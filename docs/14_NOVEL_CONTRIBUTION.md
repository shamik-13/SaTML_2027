# The novel contribution: the adversary generates the hypotheses

Addendum to `13_PLAN_v3.md`. Same verification tags (`[VERIFIED-SIM]`, `[PRIOR]`,
`[UNVERIFIED]`, `[NOVELTY-CHECKED]`, `[REFUTED]`).

---

## 1. The assumption the whole field makes, that security violates

Every online multiple-testing procedure — LORD, SAFFRON, ADDIS, e-LOND, SupLORD, Batch-BH,
online multi-layer FDR — states its guarantee over a hypothesis sequence that **arrives**.
Nature generates hypotheses; the procedure tests them. The sequence is exogenous.

In network security the adversary generates the hypotheses. They choose how many events to
emit, when, with what score distribution, and — once we aggregate to incidents — **which
events land in which group**. That is not an attack on a procedure. It is a violated
modelling assumption, and it is the source of everything below.

`[NOVELTY-CHECKED]` Searched: "adversarial online multiple testing", "alpha wealth
starvation", "adversarial hypothesis selection", "attacker chooses hypothesis sequence".
**Found and must cite:** adversarial hypothesis-testing *games* exist as a field (IEEE 2018
game-theoretic multiple testing; Yasodharan & Loiseau, NeurIPS 2019 nonzero-sum adversarial
hypothesis testing) — but for simple/single testing where the adversary picks a data
distribution, not for online multiple testing with wealth dynamics. The online-FDR survey
literature acknowledges in passing that "some of these dependencies might be adversarial
toward the statistician" without studying it. **Not found:** any treatment of an adversary
who controls *group composition or group size* in a grouped online procedure.

⚠️ **Caveat I am flagging rather than hiding:** I sampled the adversarial-hypothesis-testing
games literature, I did not survey it. A proper related-work pass on that field is required
before the novelty claim goes in a paper.

---

## 2. The core result

### 2.1 The theorem we borrow `[PRIOR]`

Vovk & Wang (*Annals of Statistics* 2021): **all admissible symmetric e-merging functions
are convex combinations of the arithmetic average and the constant 1.** Extended by Wang
(*Biometrika* 2025, arXiv 2409.19888): the only admissible way to merge arbitrary e-values
is a weighted arithmetic average.

So under arbitrary dependence — which is exactly what within-incident evidence has, and
exactly why v2 chose e-values — you have **essentially no choice** in how to aggregate.

### 2.2 The consequence `[VERIFIED-SIM]`

The arithmetic mean's denominator is the group size. The attacker controls the group size.

> **The only statistically admissible way to aggregate within-incident evidence under
> arbitrary dependence is precisely the one an adversary defeats by padding their own
> campaign with benign traffic.**

This is not a bad design choice we made. It is forced by the admissibility theorem. A
reviewer who says "then don't use mean aggregation" is answered by Vovk–Wang: there is no
admissible symmetric alternative.

### 2.3 Measured attacker cost `[VERIFIED-SIM]`

Attack of 40 malicious events, `|C|`=10⁶, k=1, incident-level LORD++, rejection requirement
`E_j ≥ 46,665`:

| pad events | group size | mean-e | detected? |
|---|---|---|---|
| 0 | 40 | 175,000 | **yes** |
| 200 | 240 | 20,833 | no |
| 1,000 | 1,040 | 6,731 | no |
| 100,000 | 100,040 | 50 | no |

Padding required to suppress, as a function of attack strength:

| detector separation μ | pad events needed | pad / attack ratio |
|---|---|---|
| 3.0 | 0 (undetected anyway) | – |
| 4.0 | 112 | **2.8×** |
| 5.0 | 347 | 8.7× |
| 6.0 | 712 | 17.8× |

A few hundred extra benign-looking flows. Free for any real attacker. Cost grows linearly
in the attack's own evidence strength, so **a better detector makes the attack more
expensive but never expensive.**

### 2.4 The trilemma

From §2.1 in two lines: validity under arbitrary dependence **and** symmetry ⇒ arithmetic
mean ⇒ denominator is group size ⇒ dilutable.

> **Pick at most two of: (i) validity under arbitrary within-incident dependence,
> (ii) symmetric/exchangeable aggregation, (iii) robustness to adversarial padding of group
> size.**

`[UNVERIFIED]` as a formal theorem — "padding-robustness" needs a definition before this is
stated as proved. The (i)∧(ii) ⇒ ¬(iii) direction follows immediately from Vovk–Wang; the
formalisation is a half-day of work and should be done before submission, not after.

---

## 3. Negative controls — the two attacks that do *not* work

These matter as much as the positive result. They make the threat model one-directional and
credible, and they are the first two things a reviewer will ask.

**Splitting is counterproductive for the attacker.** `[VERIFIED-SIM]` Fragmenting 400
malicious events across more groups *increases* detections (1 → 2 → 5 → 19 → 52 → 87 groups
rejected as G goes 1 → 400), because each fragment retains strong evidence and each
rejection earns wealth. So the vulnerability is specifically **dilution within a group**,
not fragmentation across groups.

**Inflation fails at every k tested.** `[VERIFIED-SIM]` Padding a purely benign group never
forced a false discovery (mean-e ≤ 10, sum/n₀ ≤ 550, against a threshold of 46,665) at
k ∈ {1, 100, 10⁴}. So the attack surface is **suppression only** — an adversary can hide,
but cannot flood the SOC with false alerts through this channel.

---

## 4. The defense, and the tension it creates

**Defense:** cap group size at a pre-committed `n₀` and use `Σe/n₀`. Padding beyond the cap
forces the attacker to split — and §3 shows splitting helps the defender. The two
experiments close on each other.

**The tension `[UNVERIFIED]` — and this is the most interesting open thread.** Capping group
size raises the number of groups. At `n₀ = 200` on a 16M-flow stream, `T` becomes ~80,000
groups, so under horizon-uniform γ, `α_T ≈ 3.1×10⁻⁷` and the required ceiling is ~3.2×10⁶ —
*above* the 10⁶ that `|C|`=10⁶ at k=1 provides. **The cap that defends against dilution can
push the controller back into the infeasible region characterised in `13_PLAN_v3.md` §1.1.**

If that holds, the paper has a genuinely tight three-way bind:

```
feasibility  requires  few hypotheses  →  large groups
padding-robustness  requires  bounded groups  →  many hypotheses
arbitrary-dependence validity  forces  mean aggregation  →  dilutable groups
```

**This is the experiment to run next.** It is cheap (a variant of code already written) and
it either produces the paper's central figure or eliminates the claim.

---

## 5. How the paper restructures

Contributions, replacing `13_PLAN_v3.md` §2:

**C1 — Adversarial hypothesis generation as a threat model.** Online error control assumes
an exogenous hypothesis stream; security does not provide one. Formalise what the adversary
controls (count, timing, score distribution, group membership) and what it does not
(`α_t`, calibration set, weights).

**C2 — The admissibility–dilution result.** The only admissible dependence-robust
aggregation is defeatable by padding, at 2.8–17.8× the attack's own event count. With the
trilemma, the negative controls, and the capped-group defense.

**C3 — The three-way bind** between feasibility, padding-robustness and dependence-validity
(§4) — pending the experiment.

**C4 — Feasibility envelope** (was C2 in v3): the coupling of alpha-death and resolution
collapse at security stream lengths, with the k-dimension. Still ours, still differentiated
from Zrnic et al. (power, not feasibility) and Hennhöfer & Preisach (batch, low-data).

**C5 — Operational bound**: the label-latency crossover against the disposition-feedback
controller.

Demoted to robustness subsections: drift/calibration aging (`[REFUTED]` as a headline),
dependence (dissolved), granularity-vs-power (largely `[PRIOR]`).

**Retitle:** *"Padding the Evidence: Adversarial Hypothesis Generation Against Online Error
Control for Intrusion Detection"* — or keep "Flows Are Not Incidents" as the subtitle, since
the incident-level fix is what creates the attack surface.

---

## 6. Why this is stronger than v3

v3's honest position was that two of three pillars were pre-empted and the paper depended on
an unimplemented attack. This changes that:

- The attack is **implemented and works**, with measured cost.
- It rests on a **published theorem**, so the vulnerability is fundamental rather than a
  consequence of one construction choice — which is the difference between "we broke our own
  method" and "the admissible class is broken."
- It comes with **two negative controls**, a **defense**, and a **tension the defense creates**.
- It attacks an assumption the entire online-testing field shares, which makes the finding
  relevant beyond security.

## 7. What is still not done

1. The three-way bind experiment (§4). **Highest priority — it is the central figure.**
2. Formalise padding-robustness so the trilemma is a theorem, not an observation.
3. Related-work pass on adversarial hypothesis-testing games (§1 caveat).
4. Everything is simulation. μ values are **assumed**; real per-family separation on LSPR23
   is unmeasured and drives every number in §2.3. LSPR23 flows still downloading.
5. A principled asymmetric aggregation rule — the crude "top-10 mean" tested was
   non-monotone in pad size, so it is not yet a defense, only a direction.
6. SAFFRON/ADDIS unimplemented. Their null-proportion estimators are a plausible second
   attack surface (adversary feeds the estimator that makes them powerful) — `[UNVERIFIED]`,
   and worth one day of work if C3 holds.
