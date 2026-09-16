# Review 7 worklist — seventh round (new prior art, Assumption 1, ordering optics, narrative)

> **STATUS: ALL EXPERIMENTS COMPLETE, AND main.tex IS CONTENT-COMPLETE (2026-09-02).** Everything the
> record documents is now in `main.tex` or a table it inputs — see **S4.62** for the completeness pass,
> which also closed the unguarded `main.tex`-vs-artefact boundary (`proto/t61_paper_consistency.py`,
> 44 checks) after it turned out to be hiding two wrong numbers. **What remains is narrative and
> length only**, which the author is doing by hand.
>
> **(superseded)** R1-R5 done and codex-verified (docs/04 S4.56-S4.60), plus
> **S4.61** (`t60_positional`), which closes the last open experimental gap — frozen non-claims 21
> and 25(i). TIER 3 (R6-R10) is presentation only: **no item requires compute**, R8 in particular is
> a signposting fix whose artefacts (t49/t51/t54) already exist. Remaining optional experiment: a
> two-way calibration split to make the group-vs-flow comparison like-for-like (non-claim 22); it
> closes a stated non-claim but changes no conclusion. Body is at p14 against a hard 12pp limit — the refit is R6+R10 and is the next blocking item.** Source: reviewer feedback pasted 2026-09-01 (round 7), nine numbered
> priorities. Rule unchanged (`[[blind-codex-review-workflow]]`): for each item — (a) implement,
> (b) blind-codex review, (c) edit `paper/main.tex` + `src/paper.ipynb` + `docs/04`. Builds on
> `27_review6_worklist.md`.
>
> **Deadlines:** abstract registration **Tue 22 Sep 2026**, full paper **Tue 29 Sep 2026**,
> anonymised artifacts **Fri 2 Oct 2026**. Four weeks from today (1 Sep).
>
> The user's instruction for this round: **tackle the high-effort items first.**

---

## 0. Validity triage — every reviewer point checked against a source before any work starts

| # | reviewer's point | verdict | evidence |
|---|---|---|---|
| **1** | Xu, Fischer & Ramdas (UAI 2026) on online e-closure and compound e-values exists, is in exactly our niche, and is uncited | **VALID — paper located and read** | *Improving online FDR procedures via online analogs of e-closure and compound e-values*, Ziyu Xu (CMU), Lasse Fischer (Bremen), Aaditya Ramdas (CMU). arXiv **2603.24792**, v1 25 Mar 2026, **v3 8 Jul 2026 = UAI 2026 camera-ready**. Strict power improvements over e-LOND and r-LOND **under arbitrary dependence**, controlling **SupFDR**. Not in `refs.bib` (40 entries checked). The reviewer's characterisation is accurate. |
| **1b** | *(our own check)* the same group's two companion papers are also uncited | **VALID** | Xu, Solari, Fischer, de Heide, Ramdas, Goeman, *Bringing closure to FDR control* (arXiv 2504.11759 / 2509.02517) — the **offline** e-closure principle this one is the online analogue of. Fischer, Xu & Ramdas (2025), *An online generalization of the (e-)BH procedure* (arXiv 2407.20683) — this is the **online e-BH / ARC / weighted-self-consistency** result our `sec:escapes` already leans on but attributes only to `xu2024elond`+`wang2022evaluebh`. Both should be cited. |
| **2** | Assumption 1 is the most serious scientific vulnerability; our own diagnostic cannot establish it and finds arity departures deeper in the tail | **VALID — already conceded in the paper, and the reviewer's proposed repair is testable** | `assump:groupval` (`main.tex:245-258`), `sec:tail` (`main.tex:928-941`), `sec:limitations`. §4.55 / `t55_a1_strata`: 536 cells, 428 untestable, 40 survive BY, **32 stratum-vs-own-window contrasts at all five windows**, strongest the arity bin `m=21–100` at 0.77, k=1000, **9.32 [6.48, 13.69]**. The reviewer's constructive ask — *calibrate the grouped unit directly* — **has never been run**, and (see §1 below) it is decisive. |
| **3** | The headline ordering is the detector-favourable one | **VALID and it is the worst optics problem in the paper** | `t53_ordering.json`: at 0.55 first-flow **18**, key-hash **3**, keyed hash **0**, group-id **0**, last-flow **0**, 50 random orders median **1**; at 0.85 first-flow **72**, key-hash 34, keyed 24, random median 23.5. `first_flow_is_upper = True` at both. `tab:main`'s `detected` and `median pad` columns are first-flow at all five windows, and `t53` **only covers 0.55 and 0.85** — there is no canonical-order number at 0.62/0.70/0.77 at all. |
| **4** | Batching is under-confronted; if the SOC gets a batch at bucket close, why is fully sequential LOND/LORD the right architecture? | **VALID — one passing citation, no measurement** | `zrnic2020batching` appears once, in a subordinate clause (`main.tex:1060`). No batched arm anywhere in `src/lib/`. The reviewer's guess at our answer (BatchBH needs independence/PRDS; we deliberately target arbitrary dependence) **is right but is not written down**, and there *is* an arbitrary-dependence batched procedure we should be running — see §1. |
| **5** | Surface A is much stronger than Surface B; re-frame B as a controllability theorem, not a cheap evasion | **VALID, and the paper is already ~80% of the way there** | `sec:state` already says "conspicuous in volume rather than cheap", prices it at 92M flows / 36.1 GB / 33.4 Mbit/s / 37.5× the window, and carries the synthetic guarantee-valid confirmation (`t52`). What is missing is the **framing word** in the abstract, intro and section title, and removing the residual "attack cost" register. Cheap to fix. |
| **6** | Too many stories; cut/appendix the P/PI/AQT feedback experiment; add a claim/assumption/theorem/evidence/limitation table | **VALID** | Body is exactly 12pp ([[readability-refit-12pp]]) and carries: feasibility, granularity, padding, asymmetric merging, ADDIS state, smoothing, restart, ordering, contamination, feedback controllers, frontier, two detectors, two datasets, label audit, A1 diagnostics. `sec:operational` spends ~9 lines on P/PI/AQT which we ourselves label non-FDR threshold controllers with ex-post-oracle gains. `tab:terms` exists but is a glossary, not a claims table. |
| **7** | The blur denominator is our own 5-minute proxy; the red-team record could supply an external anchor | **VALID and feasible — the record is richer than we have used** | `src/lib/data/lspr23_attacknarratives.json`: **288 tasks**, 576 steps, **295 with a submitted timestamp** spanning 2023-03-09 **07:03–15:08 UTC**, plus `Category` (Attacks_WEB 133 / Attacks_CS 82 / Attacks_NET 40 / …), `Phase` (0/1/2), `Segments` on 215 tasks, and machine-readable compromise reports carrying **IPs + hostname + time**. `t31` uses only the step *times* (15-min concurrency) and the compromise *IPs*. Task identity, phase and segment are unused. |
| **8** | LSPR23's live-fire prevalence is far above an ordinary SOC | **VALID, and larger than the reviewer knows** | Measured on the cache: **1,644,599 / 16,353,511 = 10.06% malicious flows**. Episode prevalence 0.48–1.09% (`docs/04` §4.14, §4.39). A SOC base rate is 10⁻⁴–10⁻⁶. `docs/04` §4.1 already has a synthetic prevalence sweep showing the only working configuration is π = 10⁻² — *two hundred times* the realistic base rate — but that is a **simulation** and is not in the body. |
| **9** | Abstract/intro need one primary novelty statement | **VALID** | The intro currently carries C1, a "what is already known / what C1 adds" paragraph, the bridge, C2 with two surfaces, and a non-claim about online e-BH — five moves before §2. |

**Nothing in the nine points was found to be wrong.** Three are stronger than stated (1b, 7, 8); one (5)
is nearly already done.

---

## 1. What the investigation turned up that the feedback did not — three unifications

These change the *shape* of the worklist, so they are stated before the items.

### (a) The new UAI procedures do **not** escape C1 — and one of them **is** the batched architecture

I read the camera-ready and worked the level sequences against `thm:family1`/`thm:family2`.

**Donation e-LOND** (their Eq. 28):
`α_t = δγ_t(|R_{t-1}|+1) / (1 − (δ(|R_{t-1}|+1)·W̄_t ∧ 1))`
with `W̄_t = Σ_{i∈R_{t-1}} γ_i((E_i − 1/(δγ_i(|R_{t-1}|+1))) ∧ 1) + Σ_{i∉R_{t-1}} γ_i(E_i ∧ 1)`.

Every term of `W̄_t` is `γ_i × (something ∧ 1) ≤ γ_i`, so **`W̄_t ≤ Σγ ≤ 1` always**. On a rejection-free
run (`R_{t-1}=∅`) the denominator is therefore `≥ 1 − δ`, giving

> **`α_t ≤ δγ_t / (1 − δ)`** — a *bounded* multiplicative boost, so donation e-LOND lands squarely
> inside `thm:family1` with `c = 1/(1−δ)`, `d = 1`. The horizon stays **finite and absorbing**, and the
> cold-start coefficient moves from `α` to `α/(1−α)`, i.e. the required calibration set shrinks by a
> factor **0.95**. **A 5% relaxation against a 13–22× shortfall.**

The reason is worth a sentence in the paper: *the donation budget is γ-weighted and γ sums to one —
it is the same budget whose exhaustion creates the horizon. Redistributing wealth cannot manufacture it.*

**Closed e-LOND (`e-LOND̄`, their Eqs. 15–16):**
`α_t = min_{S⊆[t−1]: D_t(S)>0} δγ_{|S|+1}(|R_{t-1}|+1)/D_t(S)`, `D_t(S) = 1 + |S∩R_{t-1}| − δE_S(|R_{t-1}|+1)`.
This is **outside the letter** of `thm:family1` (the level is no longer `γ_t ×` a bounded factor: taking
`S=∅` gives the candidate `δγ_1(|R_{t-1}|+1)`, which does not decay). But it does not escape either, by a
two-line argument specific to our evidence: let `Z_t = #{i<t : E_i = 0}`. Under two-point conformal
evidence at security prevalence, **most episodes have `E_i` exactly 0**, and a zero-evidence hypothesis is
never rejected, so `S = {those Z_t indices}` is admissible with `E_S = 0`, `|S∩R_{t-1}| = 0`, `D_t(S) = 1`.
Hence

> **`α_t ≤ δγ_{Z_t+1}(|R_{t-1}|+1)`** — the same decay with the time index rescaled by the
> non-firing fraction. The horizon is finite and absorbing with `T → T(1−p̂)`, and `p̂ ≲ 10⁻²` here.

Zero-evidence hypotheses are exactly what a security stream is made of; the closure gains its power
from *accumulated* evidence, and there is none to accumulate.

**Donation r-LOND / closed r-LOND**: the paper proves donation r-LOND's rejection set *coincides* with
donation e-LOND's on calibrated p-values (their §B.7), so the classification transfers verbatim.

**Donation online e-BH (ARC)** — dominates online e-BH, and online e-BH is already our second escape
(history-wide fixed point). So the new work supplies a **strictly more powerful member of the escaping
class**: the taxonomy gains a row, not a counterexample.

**Donation e-TOAD** *(their App. D.2)* — **this is the item that reorganises the worklist.** e-TOAD
decides hypotheses at *deadlines* `d_t ≥ t`; the rule is a step-up over the active set `A_t`:

`r_t = max{ r ∈ {|R_{t-1}∖A_t|, …, m_t} : Σ_{i∈A_t} 1{E_i ≥ 1/(δγ_i r)} ≥ r − |R_{t-1}∖A_t| }`

and the paper states it plainly: **`d_t = t` ⇒ e-LOND; `d_t = ∞` ⇒ online e-BH.** So:

> **Our escape taxonomy is not a dichotomy — it is a one-parameter family, and the parameter is the
> decision deadline, i.e. the SOC's alerting latency budget.** "Advance the index on every hypothesis"
> and "defer the decision" are the two ends of a line, and every point on it is a valid
> arbitrary-dependence procedure with a published strict improvement.

And **e-TOAD with `d_t` = bucket close is exactly the batched architecture of reviewer point 4** — the
SOC receives a batch when the time bucket closes, and the batch is decided jointly. This means:

- Reviewer point **4** (batching) is answered by *running a procedure*, not by a defensive paragraph.
- It is **arbitrary-dependence valid** (SupFDR, via weighted self-consistency), so it does not have
  BatchBH/BatchSt-BH's independence/PRDS problem — the reviewer's guessed answer is right, and we get
  to say it *and* show the strongest applicable batched method.
- It is **order-free within the bucket**, so it dissolves the within-bucket ordering lever that reviewer
  point 3 is about. Points 3 and 4 are the same story told from two ends.
- The feasibility algebra is different in kind and *quotable*: firing needs `M ≥ 1/(δγ_i r)`, so the
  batch must supply **`r` simultaneous discoveries to afford any**. The escape is self-referential —
  which is precisely why our existing online e-BH row shows it "adds no power here (72 rejections, as
  e-LOND)". At security base rates the batch does not supply the simultaneity.

**Net:** one new experiment stage answers reviewer priorities **1, 4, and half of 3**, and turns the
escape classification from a list into a **frontier: alerting latency against feasibility**.

### (b) Repairing Assumption 1 is not merely expensive — it is *provably* infeasible, and the proof is scale-free

The reviewer asks for "at least one construction where group-level validity is much closer to by design",
and predicts it "may lose substantial power". Measured on the cache (2h host-pair grouping, benign
calibration flows only):

| pos | `\|C\|` flows | **`\|C\|` groups** | T (episodes) | margin at group calibration | required `\|C\|` groups (e-LOND, `c₀=α`) | shortfall |
|---|---|---|---|---|---|---|
| 0.55 | 2,448,993 | **52,279** | 57,368 | **−0.977** | 1,147,359 | **21.9×** |
| 0.62 | 2,449,031 | **53,897** | 49,267 | **−0.973** | 985,339 | 18.3× |
| 0.70 | 2,287,988 | **57,093** | 37,231 | **−0.962** | 744,619 | 13.0× |
| 0.77 | 2,116,418 | **48,869** | 31,672 | **−0.961** | 633,439 | 13.0× |
| 0.85 | 1,813,113 | **36,944** | 31,568 | **−0.971** | 631,359 | 17.1× |

Calibrating the *grouped unit* — the construction that makes `lem:groupval` hold by design, needing only
exchangeability of calibration groups with test groups and **no metadata-conditional premise at all** —
collapses the evidence ceiling from `M = 2.45M` to `M = 52k` while leaving `T` untouched. The feasibility
margin goes from **+0.067 to −0.977**. It is silent at every window.

And the reason is **structural, not a property of LSPR23**: calibration and deployment windows are both
15% of the stream, so they produce comparable group counts, `|C|_groups/T ≈ 1` (measured 0.91–1.54). The
requirement is `|C|_groups ≥ kT/c₀ − 1`, i.e. **a ratio of `k/c₀ = 20`**. No dataset size changes this.
Restating C1 in calendar time:

> **To alert at aggregation granularity `g` over a deployment period `P` with a deployment-wide
> guarantee, you must have observed attack-free traffic at granularity `g` for at least `(k/c₀)·P` —
> twenty times the deployment window at `k=1, c₀=α`.** Calibrate at flow granularity instead and you buy
> the ceiling back, but you have re-introduced exactly the metadata-conditional premise of
> `assump:groupval`.

This is the **cleanest statement of C1 in the whole paper** and it is a *cost*, in the units a SOC
budgets in, not an abstract bound. It also closes the C1/C2 loop: group-level calibration with a
**max**-score group statistic is *padding-invariant* (padding cannot lower a maximum), so the three
properties — group validity by design, padding robustness, feasibility — appear to be a **trilemma:
pick two.** If that survives the write-up it is a genuinely new result and the strongest single answer
to reviewer point 2.

### (c) Consequence for the narrative (reviewer point 6)

(a) and (b) both *reduce* the number of stories rather than adding to them: the escape taxonomy becomes
one latency axis, and Assumption 1 becomes a priced point on the same exchange rate as C1. The
simplification the reviewer asks for is achievable **by adding these two results**, not despite them.

---

## TIER 1 — the two high-effort experiments (start immediately, in parallel)

### R1 — Xu/Fischer/Ramdas UAI 2026: classify, implement, and turn the escape taxonomy into a latency frontier

**Effort: high (~3 days). Impact: very high. Answers reviewer 1, 4, and the architecture half of 3.**

- [x] **R1a — refs.** Add three `refs.bib` entries: `xu2026eclosure` (UAI 2026; arXiv 2603.24792v3,
      8 Jul 2026), `xu2025closure` (offline e-closure, arXiv 2504.11759 / 2509.02517),
      `fischer2025onlineebh` (arXiv 2407.20683 — and re-attribute `sec:escapes`'s online-e-BH fixed
      point to it, which is currently carried by `xu2024elond`+`wang2022evaluebh` alone).
- [x] **R1b — new propositions**  *(DONE 2026-09-02: `prop:donation`, `prop:closure`, with proofs in `appendix_proofs.tex`)*  **R1b — new propositions (`appendix_proofs.tex`, stated in `sec:escapes`).** Both are short and
      both were derived above; write them properly and machine-check them:
  - **Donation e-LOND ∈ `thm:family1`** with `c = 1/(1−δ)`, because `W̄_t ≤ Σγ ≤ 1`. State the
    consequence as a *sharp constant*: the calibration requirement is relaxed by exactly `(1−δ)`.
  - **Closed e-LOND is covered by a zero-evidence-subset argument**: `α_t ≤ δγ_{Z_t+1}(|R_{t-1}|+1)`
    where `Z_t` counts prior hypotheses with `E_i = 0`. Note explicitly that this is a **new** covered
    case, not an instance of `thm:family1` — the closure's level is not `γ_t ×` bounded — so C1's scope
    genuinely widens.
  - Donation r-LOND / closed r-LOND by their rejection-set equivalence (their §B.7).
- [x] **R1c — new stage `t56_uai26_procedures.py`.** Implement in `h6_procs.py`, alongside the existing
      runners, then drive from `t56`:
  - `run_donation_elond` (their Eq. 26–28) — O(log t) not needed at our T; the direct sum is fine, but
    keep the augmented-prefix-sum version if the naive one is too slow at T=57k.
  - `run_closed_elond` (Eqs. 15–16 via their §2.2 dynamic program, O(t²)) — **T = 57,368 makes the exact
    DP ~10⁹ ops/step; do not attempt the full stream.** Run it on the *first N* hypotheses (N ≈ 2,000,
    which covers the entire cold-start window and the absorbing transition, which is the only place it
    matters) and state that scoping. Their own runtime figure shows `e-LOND̄` reaching hours at m=3000.
  - `run_etoad(deadlines)` (their App. D.2 step-up) and `run_donation_etoad`.
  - **The deliverable is a deadline sweep**: `d_t ∈ {t (=e-LOND), bucket close, 2h, 6h, 24h, ∞ (=online
    e-BH)}` × 5 windows × 2 seeds, reporting rejections, true detections, realised FDP, silent fraction,
    and first-silent index. **This is the latency–feasibility frontier**, and it replaces the current
    prose dichotomy in `sec:escapes`.
  - Re-run each of the above under the same padding attack (`r*` pricing, black-box pool) so the
    C2 rows exist for the new procedures too. **Do not let the new procedures enter the paper without an
    attack row** — that was exactly the R4 gap of round 6.
- [x] **R1d — batched baselines and why they are not the answer (reviewer 4).** One paragraph in
      `sec:related` + one measured row:
  - BatchBH / BatchSt-BH / BatchPRDS (`zrnic2020batching`) need independence or PRDS **within** the
    batch. Our within-bucket dependence is exactly what we cannot defend (co-located flows, shared
    hosts, shared calibration tail), which is why the e-value route is taken. Say this **prominently**,
    in the body, not in a subordinate clause.
  - The **strongest applicable batched method under arbitrary dependence is e-TOAD with bucket-close
    deadlines** (equivalently, batched weighted e-BH), which R1c already runs. Report it as the batched
    baseline. Include a batch-BY / batch-e-BH arm at bucket close if it is free.
  - State the feasibility algebra: batching with a **deployment-wide** budget (`Σ_b α_b ≤ α`) obeys the
    same exchange rate — the max-min allocation `γ_b ∝ n_b` reproduces `cor:budget` exactly; batching
    escapes **only** when the guarantee is reset per batch, which is our restart escape under another
    name (`sec:restart`). Cross-reference it, do not re-derive it.
- [x] **R1e — rewrite `sec:escapes` around the latency axis.** Escapes are no longer "two procedures";
      they are "**advance the index only on tested hypotheses** (ADDIS — and it is this conditioning that
      Surface B attacks) or **defer the decision** (e-TOAD/online e-BH — priced in alerting latency, and
      the self-referential `r` simultaneous discoveries the base rate does not supply)". Add the new
      procedures as rows in `tab:procedures`.
- [x] **R1f — the honest headline for the intro (reviewer's own suggested framing).** *"The newest
      strict power improvements over e-LOND and r-LOND, published at UAI 2026 under arbitrary
      dependence, move the feasibility boundary by a factor of `1/(1−α) ≈ 1.05`; the barrier is a
      property of the evidence, not of the controller's cleverness."* This sentence is worth more to the
      novelty review than any other in the paper — it is only available because the classification is a
      classification.

### R2 — Group-level calibration: repair Assumption 1 by construction and price the repair

**Effort: medium-high (~1.5 days). Impact: very high. Answers reviewer 2, strengthens C1, closes C1↔C2.**

- [x] **R2a — new stage `t57_group_calibration.py`.** Build the calibration set out of **groups**, not
      flows, using the identical grouping protocol on the calibration split:
  - group statistic: run **both** `max` of member flow scores and `mean`, since they differ in exactly
    the property C2 cares about (see R2d);
  - `M_group = (|C|_groups + 1)/k`; group e-value `= M_group · 1{group statistic ≥ k-th largest
    calibration group statistic}`;
  - run e-LOND / online e-BH / (from R1) e-TOAD on the resulting stream at all five windows × 2 seeds;
  - report `|C|_groups`, `M_group`, margin, rejections, detections, silent fraction, first-silent index.
  - Expected (pre-computed above, so this is a **confirmation** run, not a fishing expedition):
    `|C|_groups` 36,944–57,093, margin **−0.96 to −0.98**, silent everywhere.
- [x] **R2b — new corollary**  *(DONE 2026-09-02: now `cor:calhorizon` in `sec:feasibility`, named)*  **R2b — new corollary in `sec:feasibility`, and it is the best restatement of C1 we have.**
      Calibrating at hypothesis granularity forces `|C| ≈ (cal span / test span) · T`, so `cor:budget`
      becomes a requirement on **observation time**: the attack-free calibration period must exceed the
      deployment horizon by `k/c₀` (= **20×** at `k=1, c₀=α`). Scale-free — no dataset size escapes it.
      Give it a name (*calibration-horizon ratio*) and put it in the abstract.
- [x] **R2c — restructure the Assumption-1 discussion**  *(DONE 2026-09-02: all three legs stated together at the end of `sec:tail`)*  **R2c — restructure the Assumption-1 discussion into the reviewer's three-way split.** Make it
      explicit and unmissable, as its own short paragraph in §2.2 and repeated in `sec:limitations`:
  1. **C1 is distribution-free** and conditional only on the evidence bound `M` — it uses no
     distributional premise at all (already true; `sec:tail` says so, but it is buried).
  2. **`thm:padding` is an aggregation theorem** about e-merging functions — no data assumption.
  3. **Only the FDR numbers on the empirical stream** are conditional on `assump:groupval`.
  Then: *"and the construction that discharges (3) by design is priced in (1)"* — R2a/R2b. That sentence
  is the answer the reviewer is asking for, and it is now a measurement rather than a promise.
- [x] **R2d — the trilemma, if it survives.** Under group-level calibration with the **max** statistic,
      appended zero-evidence flows cannot lower the group statistic, so `thm:padding` does not bite.
      Verify this directly in `t57` (replay the R1c/`t48` pads against the group-calibrated pipeline and
      confirm `r* = ∞`). If it holds, state it as: **group validity by design, padding robustness, and
      feasibility — any two.** Flow-level calibration + mean = feasible + attackable + assumed;
      group-level + max = valid + robust + silent. **Verify before claiming**; if the max statistic turns
      out to be attackable by a different route (e.g. arity-driven threshold shift), report that instead
      and drop the trilemma to a two-way statement.
  - Caveat to state, not hide: group-level exchangeability is *itself* an assumption, just a much weaker
    and more defensible one (calibration groups vs test groups formed by the same protocol, no
    metadata-conditional per-flow claim). Do not oversell it as assumption-free.

### R3 — Make a canonical, non-attacker-timed ordering the primary pipeline  **[DONE 2026-09-01, codex-verified — see docs/04 S4.58]**

**Effort: high (~2–3 days, mostly mechanical re-runs). Impact: very high. Answers reviewer 3.**

Sequenced *after* R1c starts, because R1's e-TOAD arm partially dissolves the problem (a batched
procedure has no within-bucket order) and that changes what the primary table should say.

- [x] **R3a — thread the order through the pipeline.** `hs.build_episodes` already takes `tie_key`, but
      its primary sort is `first_ts`, so `tie_key` only breaks exact timestamp ties — it is **not** the
      canonical order. `t53` builds its own (`hashed_order`: bucket-batched, then splitmix64 of the raw
      `(SrcIP,DstIP,bucket)` key, collisions on the key). Promote that into `h_stream` as
      `build_episodes(..., order="first-flow" | "keyhash" | "keyed")`, importing `t53`'s hash so the two
      cannot drift (the same discipline used for `t48`'s key-hash arm in round 6). Default stays
      `first-flow` so nothing silently changes; each caller opts in.
- [x] **R3b — re-run under `order="keyhash"`.** 25 stages call `build_episodes`. Re-run the ones whose
      numbers reach the **body**: `t22` (main matrix), `t26`/`t47` (granularity, blur, coverage),
      `t28`/`t28b`/`t46`/`t48` (padding cost, placement, dilution), `t43` (cross-window), `t36`
      (asymmetric), `t35` (restart), `t34` (smoothing), `t21c`/`t21e` (positions, frontier), `t31`
      (audit), `t55` (A1 strata), `t32` (ADDIS state). Appendix-only stages can follow.
- [x] **R3c — extend `t53` to all five positions and both seeds.** It currently covers **0.55 and 0.85
      only**. `tab:main` needs a canonical `detected`/`median pad` at 0.62, 0.70 and 0.77, and the
      50-order ensemble at each.
- [x] **R3d — reverse the presentation.**
  - `tab:main`'s `detected` column becomes **canonical key-hash**, with the 50-order ensemble
    median/IQR beside it. First-flow moves to a clearly labelled **optimistic upper-bound sensitivity**
    row/appendix table.
  - Update the `\emph{Conventions for the results.}` paragraph (§2.3): detection counts are no longer
    "the largest over audited orders" but "the canonical metadata-hash order, with the audited-order
    distribution reported".
  - `sec:paddingcost` leads with the canonical numbers (**3/3 at 0.55, 34/34 at 0.85** — already
    measured in `t48`'s keyhash arm, costs 23/24/33 and median 115.5) and demotes the 18/72.
  - Abstract and intro: the median padding cost `≈100 flows` still stands (it is steady across orders,
    `rstar_median_over_orders` 109.5 at 0.55 / 98.0 at 0.85), so the C2 headline **does not weaken** —
    only the detection counts do. Say so.
- [x] **R3e — turn the smaller numbers into the argument, exactly as the reviewer frames it.**
      *"Conditional on the already-small set of discoveries the statistically defensible configuration
      produces, every discovery remains suppressible."* Add one sentence noting that **3 detections out
      of 275 malicious episodes at the primary guarantee window is itself C1's empirical face** — the
      canonical-order result and the feasibility theorem are the same finding measured two ways. And
      note the keyed-hash instance detects **0** at 0.55: the ordering with the best security properties
      has no power at all there.
- [x] **R3f — the `M_j` argument becomes clean.** Under a key-determined order a pad moves **0** other
      hypotheses (`t53`: `others_moved_hashed_key = 0` vs `others_moved_first_flow = 373`). The
      `assump:groupval`-preservation argument at `main.tex:270-276` is currently stated for an order the
      paper does not ship. After R3 it is stated for the order it does ship. Say that plainly.

---

> **R3 outcome (2026-09-01).** The reviewer's objection was valid and the fix turned out to be the
> *same finding as C1*. `h_stream` now owns the canonical order and `build_episodes` takes
> `order="first-flow"|"keyhash"|"keyed"`; `t53` covers 5 positions x 2 seeds; `t28b` — which is the
> stage that actually produces `tab:main` — records all three orders. **The headline counts go
> 18/13/30/31/72 -> 3/11/0/0/34.** The zeros are the feasibility boundary, proven by an exact
> biconditional (zero rejections iff nothing clears inside the feasible prefix) that holds on all 60
> arms: the prefix is only **1.6-2.6% of the stream**, so detection needs a near-ceiling episode to
> land inside it, and first-flow arrival is favourable precisely because live-fire attack traffic
> arrives early. Three stages agree on all 10 configurations. C2 gets *stronger* (suppression costs
> fall to 23/24/33 flows at the guarantee window). **R3b was scoped by measurement, not by the
> worklist's guess:** an inventory of every order-dependent number in the body found `t28b` (11
> claims) and `t53` (7) at ranks 1-2, covering `tab:main`, the abstract and `sec:paddingcost`; the
> remaining stages carry *contrasts* between two procedures on one stream, which compute both legs
> under the same order, and the conventions paragraph now says so. Codex: 0 CRITICAL, 5 findings,
> all fixed (a real unvalidated-key-length bug, a stale `apptab:padpools`, two claim-scope
> over-reaches including a quantified grinding exposure, one wording).


## TIER 2 — medium-effort measurements

### R4 — External semantic anchor for the resolution claim  **[DONE 2026-09-02, codex-verified — see docs/04 S4.59]**

**Effort: medium (~1 day). Impact: medium-high. Answers reviewer 7.**

- [x] **New stage `t58_semantic_blur.py`** using the fields `t31` leaves on the floor: 288 tasks,
      295 timed step submissions (07:03–15:08 UTC on 2023-03-09), `Category`, `Phase`, `Segments`, and
      the machine-readable compromise reports (IP + hostname + time).
- [x] Three external quantities, each computed against bucket width (the same x-axis as `fig:granularity`),
      to sit **beside** the 5-minute proxy rather than replace it:
  1. **red-team actions merged per issued alert** — distinct timed steps (and distinct *tasks*, the
     coarser unit) whose submission falls inside the alert's bucket span and whose target segment /
     compromise IP intersects the alert's host pair;
  2. **temporal localisation error** — |alert bucket midpoint − nearest step submission|, median and IQR;
  3. **task-level coverage** — how many of the 288 tasks any alert touches at all.
- [x] **State the confounds honestly, they are real:** a step *submission* time is when the red team
      **reported**, not when it executed, so (2) is an upper bound with an unknown lag; `Segments` needs
      a segment→subnet mapping we must derive and state; only 295/576 steps are timed; and 99 of `t31`'s
      152 verdicts already rest on label-generating identities (the circularity noted in `sec:tail`) —
      check whether the same circularity infects this reference and say so if it does.
- [x] If (1) tracks the 5-minute blur curve, the exchange rate stops being an artefact of our
      denominator — that is the whole point. If it does **not** track, report the divergence; a
      disagreeing external reference is still worth more than none, and the paper's honesty record is
      its main asset with this reviewer.

> **R4 outcome (2026-09-02).** Built as `t58_semantic_blur.py` (+ `proto/t58b_semanticblur_selftest.py`,
> 46 checks). Two things came out better than the item expected and one much worse.
> **Better:** the segment link needed no derivation — the red team's `bt_<seg>` vocabulary IS the
> dataset's own per-flow `seg_src`/`seg_dst` under a constant prefix, and it agrees with the
> compromise reports 83/0. And all five windows overlap the exercise's timed span, not just one.
> **Worse:** the answer to R4's own question ("does it track?") is *yes in direction, no in
> discrimination*. The external count rises with the alerting unit in rank agreement with the proxy
> (+1.000 at 0.70 over six widths, +0.816 at 0.77), but a **timeline-shift null** — added after the
> blind audit demanded it — reproduces the observed counts at **18 of 19** cells. The rise is bucket
> width capturing more submissions, not alert-level correspondence. Reported as agreement, not
> corroboration.
> **The unexpected finding, and it is C1 again:** the record can see the alerts at only 3 of 10
> (window, order) cells, because issued alerts sit in the *feasible prefix* — the first minutes of a
> deployment window — and at 0.55/0.62 that predates the exercise's first submission (only 2% overlap
> in time). *An external record can only speak about an alert it coincides with, and the feasibility
> boundary puts the alerts where the record is silent.*
> Codex: **1 CRITICAL** (average-rank Spearman — the tied 0.77 series read +1.000 instead of +0.816,
> and my own self-test had generated tie-free data), 7 MAJOR (including the shift null, and a
> *misexplained* 24 h null tie whose wrong explanation I had encoded as a passing test), 2 MINOR. All
> acted on.


### R5 — Realistic-prevalence sensitivity  **[DONE 2026-09-02, codex-verified — see docs/04 S4.60]**

**Effort: low-medium (~0.5 day). Impact: medium. Answers reviewer 8.**

- [x] **New stage `t59_prevalence.py`.** Report LSPR23's actual base rate in the body — **10.06% of
      flows, 0.48–1.09% of episodes** — against a SOC's 10⁻⁴–10⁻⁶, and then thin the malicious
      **episodes** (not flows: thinning flows changes group composition and confounds C2) to
      π ∈ {10⁻², 10⁻³, 10⁻⁴} by dropping whole malicious episodes, re-running e-LOND / online e-BH /
      e-TOAD, and reporting detections, FDP and silent fraction at each.
- [x] **The expected direction helps C1 and must be stated as such:** thinning reduces `T` only
      negligibly (malicious episodes are ≤1% of the stream) while removing the rare high-evidence
      hypotheses that bootstrap the controller, so the cold-start bootstrap probability falls further
      below the `≈0.3%` already reported in `sec:feasibility`. Live-fire prevalence is therefore the
      **optimistic** case, and every detection count in the paper is an upper bound in one more respect.
- [x] Promote `docs/04` §4.1's existing synthetic prevalence sweep (LORD++/LOND at π = 10⁻⁴…10⁻², only
      π = 10⁻² with `|C|` = 10⁶ works — 200× a realistic base rate) from the record into the body or a
      cited appendix table. It is a strong number that currently lives nowhere a reviewer will see it.

> **R5 outcome (2026-09-02).** `t59_prevalence.py` (+ `proto/t59b_prevalence_selftest.py`, 35 checks).
> The predicted direction holds and is now separated cleanly from its confound. **Feasibility does not
> move; detection collapses.** Mean e-LOND rejections go 3-72 (observed) -> 0-8 at pi=1e-3 -> a 0-40%
> chance of *ever* rejecting at pi=1e-4. Both escapes (online e-BH, e-TOAD) collapse with it.
> **The audit forced a design change, not just wording.** Deleting a hypothesis shortens the stream and
> shifts survivors into a HIGHER alpha_t, so lower prevalence can *help* — with a concrete
> counterexample. The primary mechanism is now index-preserving (the episode stays at its own index
> with benign evidence, holding T, the margin and every level exactly fixed); deletion is the
> sensitivity arm, and under it the margin RISES by +0.0129 while detection still collapses. The two
> agree to within 0.02, so re-indexing is not what does the work.
> Also fixed: `keep_count` rounded pi=1e-5 targets to ZERO, silently duplicating the pure-null arm and
> contradicting my own printed claim; and the "0 of 10 pure-null streams reject" line was re-scoped —
> it is 5 overlapping windows, P(zero | the simulated 4.5%) = 0.79, so it is consistency and cannot
> test that number. The body's 4.5% is now labelled a simulation claim.
> Codex: 0 CRITICAL, 5 MAJOR, 4 MINOR. One MAJOR was my self-test asserting a FALSE THEOREM
> ("thinning never increases detections"), which passed only because 30 random streams missed the case.


### R2d follow-through — the group-creation attack  **[DONE 2026-09-02, codex-verified x2 — docs/04 S4.61]**

- [x] **New stage `t60_positional.py`** (+ `proto/t60b_positional_selftest.py`, 56 checks).
      Prices the lever non-claim 21 left open: *creating* hypotheses ahead of a target instead of
      appending flows to it.

> **Outcome.** R2d asked to verify the trilemma "group validity by design, padding robustness, and
> feasibility — any two" *before* claiming it, and to report the alternative attack if the max
> statistic turned out to be attackable another way. **It is, and the trilemma is dropped.**
> Calibrating on *groups* shrinks the ceiling, so the group-MAX cold-start window collapses from
> 748-902 steps to **65-86**, and every group-MAX detection is suppressed by **62-207** inserted
> hypotheses — while padding provably cannot touch it at all. *Validity by design plus padding
> robustness buys resistance to one attack while making the other far cheaper.*
> On the shipped pipeline the verdict splits: insertion does **not** beat padding for one alert
> (0/12 cells) but silences the **whole window** for 217-813 hypotheses against 80-7.9e8 flows.
> **Two audit passes, 1 CRITICAL + 11 MAJOR.** The CRITICAL: I measured a *prefix* attack and
> reported it as per-target suppression, overstating the per-episode cost 3-8x in the attacker's
> favour. Pass 2 then found the corrected closed form silently **capped G\* at 2T+3**, the keyspace
> search priced the **wrong event** (understating it up to 64x), the keyed rows used **seed 0**, the
> padding window total is an **upper** bound not a joint cost, and — found only because the auditor
> ran the script — **it crashed after writing its JSON**, which I had missed by grepping the log for
> expected lines instead of checking the exit status.


---

## TIER 3 — presentation (do last, but do not skip: reviewer 9 rates this "high for review perception")

### R6 — Cut the narrative to one causal chain

**Effort: low-medium (edits only). Impact: high. Answers reviewer 6.**

- [ ] **Cut P/PI/AQT from the body to `app:baselines`.** ~9 lines of `sec:operational` (`main.tex:900-909`)
      plus the `sec:discussion` practitioner clause. Keep **one sentence** in the body: analyst feedback
      does not rescue the operating point unless labels arrive in minutes, and the principled
      construction is GAIF/OCTF (`lu2026gaif`), whose input our disposition-delay measurement prices.
      We already concede these are not finite-sample-FDR methods with ex-post-oracle gains, which is
      exactly why they cannot carry body space.
- [ ] **Enforce the reviewer's chain as the body's spine**, in this order, with every subsection
      answering to it:
      *finite conformal resolution ⇒ uninterrupted online FDR control is infeasible ⇒ security-semantic
      aggregation restores feasibility ⇒ that aggregation exposes attacker-controlled hypothesis
      composition ⇒ mechanisms that instead adapt controller state expose that state too.*
      R1 and R2 both attach cleanly (R1: the third arrow now has a latency axis; R2: the second arrow
      has a validity price).
- [ ] **Add the claim/assumption/theorem/evidence/limitation table** the reviewer asks for. One row per
      claim: C1, `cor:budget`, the calibration-horizon ratio (R2b), the granularity bridge,
      `thm:padding`, `thm:reach`/`thm:frontload`, `thm:addis`. Columns: claim | assumption it needs |
      where proved | empirical evidence | stated limitation. This is the single highest
      review-legibility-per-column-inch item in the paper and it pays for the space R6 frees.
- [ ] **Prune the pre-emptive-rebuttal register.** Named by the reviewer: "what C1 adds", "two
      clarifications keep this honest", "this is not a third result", and the repeated
      what-this-number-does-and-does-not-mean constructions. Keep the *distinctions*, delete the
      *announcements* of them — most survive as a clause instead of a sentence.

### R7 — Re-frame Surface B as controllability, not evasion

**Effort: low (edits only). Impact: medium-high. Answers reviewer 5.**

- [ ] Retitle `sec:state` to name it a **controller-state controllability** result, and lead with the
      structural claim rather than the cost: *an escape mechanism that conditions on observed evidence
      creates a manipulable state variable, and nominal FDR control can remain valid while it is
      manipulated.*
- [ ] Delete any remaining register that invites cost comparison with Surface A. Keep the 92M flows /
      36.1 GB / 33.4 Mbit/s / 37.5× figures — they are the *point* now, not a caveat.
- [ ] Promote the synthetic guarantee-valid experiment (`t52`, median `B* = 140` over 300 streams) from
      an artefact-rebuttal to **the** result: the phenomenon is a property of the mechanism, not of the
      0.85 window's validity failure. The reviewer flagged this as "particularly important" — currently
      it reads as a defensive move.
- [ ] Keep the online e-BH non-claim exactly as it is.

### R8 — Second detector / second deployment for Surface A

**Effort: none (already done) — this is a visibility fix. Reviewer 7's item.**

- [ ] The reviewer's "add if inexpensive" is **already satisfied and they appear not to have registered
      it**: `sec:transferattack` carries the host-conditioned detector (AUROC 0.954 vs 0.916) *and*
      AIT-LDSv2.0 across eight organisations (**84/85** episodes suppressed with real benign-to-victim
      pads; all **9** host-conditioned detections suppressed under causal replay). If a careful reviewer
      missed it, it is under-signposted. Surface it in the **abstract** and the contributions block, and
      give `sec:transferattack` a heading that says "second detector and second dataset" rather than
      asking it as a question. **No new experiment.**

### R9 — One primary novelty statement in the abstract and introduction

**Effort: low (edits only). Impact: high for review perception. Answers reviewer 9. Do this LAST**,
after R1/R2/R3 land, because they change what the primary statement is.

- [ ] The novelty sentence to build around — the reviewer's own formulation, now backed by R1 and R2:
      **not** "bounded evidence plus shrinking threshold ⇒ silence" (elementary, and prior art per
      `huo2024realtime`), but *a taxonomy of when the loss becomes an absorbing structural impossibility,
      the exact horizon/calibration scaling, which online-controller architectures fall into that class,
      which escape it, and what those escapes cost* — now including the UAI 2026 procedures and a
      latency-parameterised escape frontier.
- [ ] Add the calibration-horizon ratio (R2b) to the abstract: it is the most memorable single number
      the paper owns and it is expressed in a unit a practitioner budgets in.
- [ ] Trim the intro from five moves to three: the boundary, the bridge, the attack surfaces. The
      "what is already known / what C1 adds" paragraph shrinks to one sentence now that the
      classification does the work the paragraph was doing defensively.

### R10 — Page refit to 12pp

**Effort: medium. Do absolutely last, per the standing instruction.**

- [ ] Body is exactly 12pp today. R1/R2/R4/R5 add material; R6/R7/R9 remove it. Re-measure with the
      README awk on "Open Science" after every tier, not only at the end, so the overshoot never
      compounds the way it did in round 6 (p14).
- [ ] Techniques that worked last time are recorded in [[readability-refit-12pp]] — narrative-first,
      lead with the plain claim, subordinate the numbers, defer fine numbers to the existing appendix
      tables. Do **not** recover pages by formatting: the CFP calls that grounds for desk rejection.

---

## Schedule against the two deadlines

| week | dates | work |
|---|---|---|
| 1 | 1–7 Sep | **R1a–R1c** (UAI procedures + deadline sweep) and **R2a–R2b** (group calibration) in parallel — both are experiments and both gate the framing. Codex-audit each before believing it. |
| 2 | 8–14 Sep | **R3a–R3c** (order threading + re-runs; the long pole is compute, start it early and let it run), **R1d–R1f**, **R2c–R2d**, **R4**. |
| 3 | 15–21 Sep | **R3d–R3f** (re-presentation), **R5**, **R6**, **R7**, **R8**. |
| — | **22 Sep** | **abstract registration (mandatory)** — the abstract must already carry the R9 novelty statement and the R2b ratio, so R9's abstract half lands here, not in week 4. |
| 4 | 22–28 Sep | **R9** (intro), **R10** (refit), full `t45` consistency chain, notebook re-run, tectonic clean build. |
| — | **29 Sep** | paper deadline. **2 Oct**: anonymised artifacts. |

**Cut line, if week 3 slips:** R1, R2, R3, R6 and R9 are the acceptance-relevant block and none of them
can be dropped — R1/R2/R3 are the reviewer's own top three, R6/R9 are what makes them legible. **R4
(semantic anchor) and R5 (prevalence) are the ones to cut**, in that order; both can be replaced by two
honest sentences in `sec:limitations` naming what was not done and why, which costs far less credit with
this reviewer than a rushed measurement would.

---

## Standing rules for this round

- Every new experiment gets a **blind codex audit before its numbers enter the paper**
  ([[blind-codex-review-workflow]]). Round 6's R5 changed its statistics on **all three** passes and
  every fix was a real defect — assume the same here, and budget for it. R2d (the trilemma) and R1b
  (the two new propositions) are the highest-risk claims in this worklist.
- `docs/03_FROZEN_CLAIMS.md` bounds what may be asserted; add the new non-claims as they arise. At
  minimum, expected new non-claims: (i) we do **not** claim the UAI 2026 procedures are without value —
  they are strict improvements, and the point is that the improvement is orthogonal to feasibility;
  (ii) we do **not** claim group-level calibration is assumption-free, only that its assumption is
  weaker and checkable; (iii) we do **not** claim the red-team record is incident ground truth.
- `paper/tables/*.tex` are generated from JSON and are authoritative — after any re-run, regenerate with
  `make_appendix_tables.py` and `make_figures.py` before touching prose, and re-run
  `proto/t45_record_consistency.py` (from `proto/`, reading `proto/out/` — **copy new JSONs there** or
  its checks go stale).
- Environment unchanged: `proto/.venv/bin/python`, stages run from `src/lib` with `PYTHONPATH=.`,
  notebook built and run from `src/`, `tectonic -X compile main.tex`.
