# Review 8 worklist — eighth round (statistical interpretation, theorem scope, order consistency)

> Source: reviewer feedback pasted **2026-09-02** (round 8), seven scientific items + an LLM-disclosure
> item the author has **descoped**. Rule unchanged (`[[blind-codex-review-workflow]]`): for each item —
> (a) implement, (b) blind-codex review, (c) edit `paper/main.tex` + `src/paper.ipynb` + `docs/04`, then
> (d) re-run `proto/t61_paper_consistency.py` **and** `proto/t45_record_consistency.py`.
> Builds on `28_review7_worklist.md`. Deadlines unchanged: abstract **22 Sep 2026**, paper **29 Sep 2026**,
> artifacts **2 Oct 2026**.
>
> **STATUS 2026-09-02 — the writing-only pass is DONE.** R1a, R1c, R2a, R2b, R2c, R3a, R6, R7, A and
> R5d are landed in `main.tex`, `appendix_proofs.tex`, `make_appendix_tables.py`, `src/paper.ipynb`,
> `docs/03` (non-claims 39-42) and `docs/04` §4.57 (corrected in place) + §4.64 (new). **R3b is
> descoped by the author — no authors will be contacted.** Gates: `t61` **81/0** (11 new pins, three of
> them *absence* checks), `t45` **268/0**, five self-tests **0 failures**, 29 tables byte-identical,
> tectonic build **0 overfull / 0 undefined**, body ends p16.
>
> **UPDATE 2026-09-02 (later): the three compute items are DONE and blind-audited.** `t64` (canonical
> operational evaluation, Section VIII), `t63` (blind-key insertion), `t57`+`t38` extensions. The codex
> pass on `t63` returned **5 MAJOR + 4 MINOR**, all fixed and re-run — see `docs/04` §4.65.5.
> Headlines: at 0.55 the controller moves 18 → **3** alerts and the frontier gap widens **5.8× → 34.7×**;
> a keyed seed does **not** stop insertion (84/84 targets fall) but costs **2.1–89×** more instantiated
> host pairs; arity-conditional coverage on TEST groups runs **0.13×–24.2×** nominal while marginal
> coverage is fine.
>
> **UPDATE 2026-09-02 (final): R5c and B are DONE. The worklist is closed.** R5c labelled six
> first-flow paired analyses and forced one recomputation — `t56` gained an order arm, and under the
> canonical order **deferral converts at 1 of 10 cells for +1 detection at the invalid window**, against
> 2 cells under first-flow; the old "one window of the five … 13→32 and 30→31" sentence was
> self-contradictory *and* first-flow. B added `cell_num(kind="point"|"range"|"cell")` over 13
> multi-cell quantities, **found an error on its first run** (the benign firing counts were seed-0 only;
> over all ten cells the range is 0–46), and was verified against an injected round-8-shaped error
> rather than merely run green.
>
> Gates: `t61` **141/0**, `t45` **268/0**, seven self-tests **0 failures**, 30 tables byte-identical,
> **0 overfull**, body p17.
>
> **REMAINING: the author's manual narrative refit only.**
>
> **Every one of the seven points is valid.** Three are *stronger* than the reviewer states (1, 4, 6) and
> one is already half-fixed in one section while still wrong in another (2a). Two new computations are
> authorised by the reviewer; I add one cheap recomputation (1b) and one gate upgrade (B).

---

## 0. Validity triage — each point checked against the source before any work starts

| # | reviewer's point | verdict | evidence |
|---|---|---|---|
| **1** | Arity-correlation does not invalidate group exchangeability | **VALID — and the measurement is weaker than the reviewer realised** | `t57_group_calibration.py:307-319`: the arity bins are computed **inside the calibration set** (`frac_in_top1pct = mean(v_cal[m] >= q99)`, `q99` that same set's own 99th percentile). No test group enters. The marginal rate is therefore **exactly 1.000%** at every window and seed *by construction*. It is not evidence about exchangeability at all — it is a description of how one fixed set decomposes by arity. |
| **1c** | *(my own check)* the two correlations quoted are extremes of a range | **VALID — the `[[wrong-statistic-failure-mode]]` again, inside the disputed sentence** | `max` Spearman is **+0.233…+0.413** over 10 cells; the paper prints "+0.41" (the max). `mean` Spearman is **−0.116…+0.090**; the paper prints "+0.09" (again the max, and the largest-magnitude cell is **negative**). Top bin runs **3.56%…15.29%**; the paper prints "9.09%" (0.55 seed 0 only), and "0.36%" is likewise one cell of 0.26–0.44%. |
| **2a** | "No run leaves that regime" contradicts the reported 30/31/73 rejections | **VALID — still live** | `main.tex:1261` (scope statement (i)) says *"No run in our measurements leaves that regime."* `main.tex:570-573` says *"Runs here **do** pass that count — 30, 31 and 73 rejections … the realised boost reaches 1.83 against the cold-start ceiling 1.05."* One of the two copies was fixed last round; this one was missed. |
| **2b** | "Donation e-LOND does not escape C1" is broader than Prop. 6 proves | **VALID** | `main.tex:545` heads the block *"Do the newest procedures escape? No."*; `main.tex:1308` (Related Work) classifies them against C1 categorically. Prop. 6 is a **rejection-free-prefix** bound and says so. What is proved is the cold-start barrier, not a global cap. |
| **2c** | Prop. 7's conclusion needs a pathwise/density hypothesis | **VALID** | `prop:closure` (`main.tex:575`) states the bound unconditionally — which is fine, the bound *is* unconditional. The **conclusion** drawn from it (finite horizon, absorbing state) needs `Z_t → ∞` fast enough that `γ_{Z_t+1} → 0`. The body supplies that empirically ("99.5–99.8% of episodes carry exactly zero evidence") but the statement does not carry it as a hypothesis. |
| **3** | "Corrected reading" of a weeks-old paper invites a hostile referee | **VALID as risk management** | `main.tex:581-584` and `main.tex:1262-1264`. The citation itself is sound — `proto/UAI2026_SOURCE_TEXT.txt` is the fetched arXiv HTML of *Improving Online FDR Procedures via Online Analogs of e-Closure and Compound e-Values* (Xu, Fischer, Ramdas; arXiv 2603.24792v3 = UAI 2026 camera-ready), and `refs.bib:296` records the verification. Nothing is fabricated. The exposure is purely the word **"corrected"**, which asserts the source is wrong. |
| **4** | "The attack still works" under a keyed hash is not demonstrated | **VALID — and the paper already contradicts itself on it** | `main.tex:790-791` (§ padding): *"under a keyed hash the ranking cannot be computed offline at all, **and the attack still works**. The keyed seed removes the search, not the attack."* `main.tex:1216-1218` (§ transfer): *"A keyed hash removes grinding only at the price of a seed the adversary can neither learn nor infer — **a channel we do not analyse**."* Both sentences are ours; they cannot both stand. |
| **5** | §VIII still reports the first-flow operating point | **VALID — three sites, confirmed** | `main.tex:1062` "e-LOND operates at **18 alerts, recall 0.065**"; `main.tex:1701` `apptab:frontier` row "online FDR (mean rule) **18** … **0.065**"; `main.tex:1160-1162` §contamination "(from **0.065** at 0.55, **0.282** at 0.85)". `tab:main`'s headline at 0.55 is **3**. (`apptab:detection` *is* correctly labelled first-flow — that one is fine.) |
| **6** | Two of four non-refuted windows get "guarantee" status | **VALID — and the diagnostic has essentially no power** | `t50_calib_ci.json`: the benign firing counts behind the whole split are **1, 1, 3, 2, 46** out of 1.6–2.3M. At 0.55 the exact CI on the ratio is **[0.027, 5.96]**; at 0.62 seed 1 and 0.70 seed 1 the count is **0**. Only 0.85 excludes 1. A "compatible" verdict on `n_fired = 1` cannot discriminate anything — which `main.tex:1099` already concedes ("an *inconclusive non-rejection*, not support") without carrying that into the terminology. |
| **6b** | *(my own check)* is there a pre-committed rule? | **PARTLY — and it points the other way** | `docs/03_FROZEN_CLAIMS.md:56` fixes 0.55 as the analysis window "with 0.62 as a second" — a design-time pair, pre-dating the tail diagnostic. But `docs/SaTML_2027_review_feedback.md:262` records an **earlier round asking us to write "four positions … are treated as the guarantee-analysis windows."** The current 2-of-4 split is drift, and it is drift in the direction of claiming more validation. |
| **7** | \(10^{-4}\)–\(10^{-6}\) SOC prevalence is uncited | **VALID, mild** | `main.tex:484`, one occurrence, no citation. Everything downstream of it is already correctly framed ("This is a sensitivity, not a full counterfactual", `main.tex:497`). Only the bare figure is exposed. |

**Nothing in the seven points was found to be wrong.**

---

## 1. Two things the triage turned up that the feedback did not

### (a) The arity measurement is arithmetically forced

`t57` bins the **calibration** groups by arity and reports each bin's share of that same set's top 1%.
Summing the bins back:

| window | seed | marginal top-1% rate | ×nominal | min bin | max bin |
|---|---|---|---|---|---|
| 0.55 | 0 | 1.000% | 1.000 | 0.358% | 9.091% |
| 0.55 | 1 | 1.000% | 1.000 | 0.371% | **15.289%** |
| 0.85 | 0 | 1.002% | 1.002 | 0.347% | 3.558% |

The marginal is 1.000 because the top 1% of a set is 1% of that set. So the number cannot bear on
calibration/test exchangeability *even in principle*, and a statistics referee who noticed would be
entitled to say the paragraph is not measuring what it claims. **The reviewer's proposed rewrite is not
a concession — it is the only reading the artefact supports.**

The claim the paper *wants* — coverage is not arity-conditional, and arity is the adversary's lever — is
real and reachable, but it must be measured on **benign test** groups against the calibration threshold.
That is item **1b**, ~30 lines inside a pipeline that already loads both sides.

### (b) The keyed hash is probably a partial mitigation, and the artefact already says so

`t60_positional.json` already carries `hash_fraction_below_target` (call it `u`) and `targeted_gstar`
(`G*`). Under a secret seed an attacker's blindly-injected key lands ahead of the target with
probability `u`, so the count landing ahead is `Bin(N, u)` and the budget needed scales as `G*/u`:

| window | order | targets | `u` range | `G*` range | `G*/u` (expected blind budget) |
|---|---|---|---|---|---|
| 0.55 | keyhash | 3 | 0.037–0.072 | 217–628 | 5,935 – 16,423 |
| 0.62 | keyhash | 11 | 0.016–0.297 | 218–813 | 835 – 50,856 |
| 0.85 | keyed | 24 | 0.016–0.045 | 518–1,099 | 24,528 – 36,731 |

A **10–60× multiplier on instantiated host pairs**, heavy-tailed in `1/u`. And these are pairs the
attacker must actually *send traffic between* — unlike the public-hash case, where the search is offline
and free. **This is a mitigation result, and the reviewer is right that we have not earned the sentence
we wrote.** (Figures above are the analytic shape from existing fields, *not* a result — item 4 measures
the success curve properly, including the attacker's ignorance of `u` itself.)

---

## 2. Items

Ordered as the reviewer ordered them: the two Criticals first.

### R1 — Correct the group-calibration interpretation *(Critical; writing + 1 cheap recomputation)*

**R1a (writing).** Rewrite the *"premise moves rather than disappears"* paragraph (`main.tex:1144-1150`)
to the three-part structure the reviewer proposes, conceding the first part outright:

1. Direct group calibration **does** remove `assump:groupval`. Ordinary calibration/test **group**
   exchangeability suffices, and the group statistic's dependence on arity does not contradict it.
2. Group exchangeability is still a deployment assumption, and it is the one **adaptive group
   formation** breaks — which is this paper's threat model, not a defect of the statistic. Under the
   threat model the test groups are adversarially constituted, so exchangeability fails *by
   construction*, not by correlation.
3. **Even granting it entirely, the construction cannot alert**: `CEIL` falls 40–49×, no window is
   feasible, detection goes to zero, and `cor:calhorizon` prices the gap at 20 groups per hypothesis.

Frame (3) as the load-bearing argument — *"grant the repair its validity premise; it still cannot
alert"* — exactly as the reviewer says. `apptab:groupcal` already proves it.

**R1b (cheap recomputation, ~30 lines in `proto/t57_group_calibration.py`).** Replace the
calibration-internal bins with a genuine conditional-coverage measurement: score **benign test** groups
against the calibration `q99`, bin by arity, report per-bin exceedance against nominal 1% **and** the
marginal. Then the surviving sentence is a coverage statement, not a tautology.
*Fallback if it does not separate:* delete the arity sentence. R1a part (3) carries the section alone,
so nothing downstream depends on it.

**R1c (correction).** Whatever survives must be reported as a **range over the ten window–seed cells**,
not as its most favourable cell — see triage 1c. The `mean` statistic in particular must not be
described by "+0.09" when the range is −0.116…+0.090.

**Blocks:** nothing. **Touches:** `main.tex:1144-1150`, `tables/groupcal.tex`, `docs/04` §4.57.

---

### R2 — Tighten the scope of Propositions 6 and 7 *(Critical; writing + one new corollary)*

**R2a.** Delete the false sentence at `main.tex:1261` and replace it with what we actually observe:
> *the denominator never vanishes on these streams — realised donation wealth stays at most 0.12 of a
> budget of 1.*

This is already the correct wording at `main.tex:572-574`; scope statement (i) must be made to agree
with it. **This is a factual error currently in the paper, not a presentation choice.**

**R2b.** Narrow every categorical "does not escape" to what Prop. 6 proves:
> *donation cannot rescue a controller that fails to obtain its first rejection before the
> bounded-evidence cold-start horizon.*

Sites: the `"Do the newest procedures escape? No."` head (`main.tex:545`), and Related Work's
"strongest current procedures … do not escape the horizon" (`main.tex:1308`). Keep the strength — the
cold-start barrier *is* C1's headline — but stop implying a post-rejection global claim we did not prove.

**R2c.** Restate the closure result as **proposition + corollary**:

- **Prop. 7 (unchanged):** `α_t ≤ δ γ_{Z_t+1} (R_{t-1}+1)`, `Z_t = #{i<t : E_i = 0}`.
- **New corollary (pathwise):** if along a rejection-free run `Z_t → ∞` fast enough that
  `γ_{Z_t+1} → 0`, closed e-LOND enters the absorbing infeasible state. **Stronger sufficient
  condition:** a positive lower asymptotic density of zero-evidence hypotheses,
  `liminf Z_t/t ≥ ρ > 0`, gives the `thm:family1` horizon with `T → ρT`.
- Then the empirical line: *"our streams satisfy this extremely strongly — 99.5–99.8% of hypotheses
  carry exactly zero evidence"* — as **verification of the hypothesis**, not as the proof.
- Add the honest converse in one clause: where most hypotheses carry positive evidence, `Z_t` stays
  small and the bound says little. The appendix already reasons this way; the statement must too.

**Touches:** `main.tex:545, 555-585, 1259-1264, 1308`; `appendix_proofs.tex`; `docs/03` non-claims.

---

### R3 — Neutralise the e-TOAD wording *(High; writing — plus one action only the author can take)*

**R3a (mine, do now, unconditionally).** Replace both "corrected reading" sites (`main.tex:582`,
`main.tex:1263`) with language that asserts nothing about the source:
> *We implement the interpretation consistent with the source's own stated limiting cases
> (`d_t = t` ⇒ e-LOND, `d_t = ∞` ⇒ online e-BH); the alternative literal reading is reported as a
> sensitivity analysis in `apptab:uai26` and changes no conclusion.*

Same treatment for scope statement (iii) on the compound-e equation — keep "two readings, we report
both", drop any implication that one is an error. We do not rely on the power difference either way, so
nothing is lost.

**R3b — DESCOPED by the author (2026-09-02).** No prior-work authors will be contacted. R3a was
written to stand without a reply, which is why this costs nothing: the paper now asserts only which
interpretation it uses and why, and reports the alternative as a sensitivity analysis. Nothing
downstream depends on the power difference either way.

---

### R4 — Blind-key insertion experiment *(High; NEW COMPUTATION — reviewer-authorised)*

New stage `src/lib/t63_blindkey.py` + `proto/t63b_blindkey_selftest.py`. The attacker does **not** know
the seed, therefore does not know `u` either.

- **Model.** Target with hash quantile `u`, suppression requirement `G*` (both from `t60`). The attacker
  instantiates `N` genuinely accessible group keys and injects blindly; `K ~ Bin(N, u)` land ahead.
  Success ⇔ `K ≥ G*`.
- **Report.** `N` required for **50 / 90 / 99%** success, per target, per window, per order — measured
  by replay against the real stream, not only from the binomial (the binomial ignores that inserted
  keys also shift each other's ranks and consume steps, which `t60`'s replay already handles).
- **Attacker-blind marginal.** `u` is unknown to the attacker, so also report the budget under
  `u ~ Uniform(0,1)`: `E[N] = G*·E[1/u]` **diverges**, so quantiles are the only honest summary. Say so.
- **Key budget is the binding constraint.** Parameterise by the number of `(SrcIP, DstIP)` pairs the
  adversary can actually instantiate — a source–destination grouping means real endpoints, real traffic.
  Report success probability **at a budget**, not just the budget for a success. Cross-reference the
  three conditions `main.tex:788-790` already states.
- **Control.** Re-run the same measurement under the public hash, where the attacker knows `u` and needs
  exactly `G*`. The ratio between the two columns **is** the value of the secret seed.

**Either outcome improves the paper**, and the reviewer says so: cheap blind insertion ⇒ a stronger
attack result; expensive blind insertion ⇒ *a keyed canonicalization is a real mitigation for targeted
insertion, while doing nothing whatever to Surface A padding* — which is a cleaner story than the one we
have, because it makes the two surfaces genuinely asymmetric in their defences.

**Then fix the sentence** at `main.tex:790-791` to whatever was measured, and reconcile it with
`main.tex:1216-1218` and scope statement (iv) at `main.tex:1269-1270`. **The two sentences must agree
regardless of the experiment's outcome** — that part is not optional.

---

### R5 — Make the canonical order consistent through the operational evaluation *(High; NEW COMPUTATION — reviewer-authorised)*

**R5a (recompute).** Re-run the operating-point / frontier analysis under the **canonical** order at the
primary window. The frontier itself is an ex-post threshold family and is **order-independent**, so only
the controller rows move: `apptab:frontier`'s "online FDR" row goes from 18 alerts / recall 0.065 to
**3 alerts / recall 0.011**, and the gap must be recomputed at the new budget.

The reviewer predicts this strengthens the conclusion, and the arithmetic agrees: the zero-error oracle
reaches recall 0.378 on 104 alerts, so the "choice of point" gap widens from **≈6×** to **≈35×**. Confirm
by measurement, do not assume. Same for `apptab:frontier85` (0.85: 72 → 34).

**R5b (recompute).** §contamination's base recalls (`main.tex:1160-1162`) are first-flow. Recompute
under canonical, or label them explicitly as a first-flow paired analysis. Recomputing is better: the
one-mislabel-kills-it result is *sharper* at 3 detections, not weaker.

**R5c (labelling audit).** Sweep every detection count and recall in the body and classify each as
canonical / first-flow-paired / order-free. Smoothing (24.1 vs 18), restart (0.065 → 0.345 / 0.195),
asymmetric (−58%), and the `q`/`γ` sweeps may all stay first-flow **as explicitly labelled paired
analyses** — the reviewer permits this — but each needs the label, and `apptab:detection` shows the
right wording to copy. Add a `t61` check per site so a rewrite cannot silently drop a label.

**R5d (small, found in triage).** `tab:main`'s caption calls the canonical column *"an ordinary draw
from that ensemble"*. At 0.62 seed 0 the canonical count is **11 and the ensemble maximum is also 11** —
it is the extreme, not an ordinary draw. At 0.70/0.77 it is below the median. Say what it is per window,
or drop the characterisation.

---

### R6 — Retire "guarantee-analysis window" *(Medium–high; writing only)*

Adopt the reviewer's naming exactly:

| position | name | basis |
|---|---|---|
| 0.55 | **primary analysis window** | pre-committed at design time (`docs/03:56`) |
| 0.62 | **replication window** | pre-committed as the second window, same source |
| 0.70, 0.77 | analysis windows | not refuted; not distinguished |
| 0.85 | **known-invalid stress window** | tail ratio 50.9×, CI [37.3, 67.9], excludes 1 |

and state that **all FDR guarantee statements at every window remain conditional on
`assump:groupval`** — which is already the truth, and already what `sec:limitations` says.

Two things to state plainly rather than let a referee find:

1. The selection was **pre-committed as design, not derived from the diagnostic.** `docs/03:56` fixes
   0.55 + 0.62 before the tail counts existed. Say that; do not invent a rule after the fact.
2. **The diagnostic has almost no power.** It rests on 1, 1, 3, 2 benign firings out of ~2M; the 0.55
   interval is [0.027, 5.96]. It can refute 0.85 and essentially nothing else. `main.tex:1099` already
   says "inconclusive non-rejection, not support" — promote that from a buried clause to the paragraph
   that defines the terminology (`main.tex:1004-1010`).

This is a **rename plus a demotion of a claim**, ~30 sites (`grep -n "guarantee.window\|guarantee-analysis"`
returns 24 in `main.tex` plus table captions). Mechanical, but it must not be done with blind
search-and-replace: the tables' captions carry the assumption clause too.

---

### R7 — Attribute or de-claim the SOC prevalence figure *(Medium; writing only)*

`main.tex:484` states \(10^{-4}\)–\(10^{-6}\) as a fact about SOCs with no citation. Two acceptable fixes,
in order of preference:

1. **Reframe as the sweep's parameter range**, claiming nothing about real SOCs: *"we sweep episode
   prevalence down to \(10^{-6}\), four to six orders below this exercise's 0.48–0.81%"*. The result —
   feasibility unmoved, detection collapsing — is a statement about the *procedure's* response to base
   rate and needs no external anchor at all.
2. If a number is wanted, hang it on the base-rate literature already cited
   (`axelsson1999baserate`, `axelsson2000baserate`, `main.tex:102`) and say **explicitly** what unit it
   is in — Axelsson's figures are per-*event* rates and ours are per-*episode*, so a bare transfer is
   exactly the unit mismatch the reviewer is warning about.

Do **not** go looking for a citation to make the stronger claim survive; the sensitivity framing is
already what the surrounding text says (`main.tex:497`).

---

## 3. Two additions of my own

### A — Reconcile the two keyed-hash sentences regardless of R4

`main.tex:790` and `main.tex:1216` currently make opposite claims about the same mechanism. Whatever R4
returns, exactly one wording survives and both sites plus scope statement (iv) carry it. Pin all three in
`t61`. *(This is the only item on the list that is a live internal contradiction rather than an
overstatement, alongside R2a.)*

### B — Add a statistic-**kind** gate to `t61`

Triage 1c found three more instances of `[[wrong-statistic-failure-mode]]` — a max over cells printed as
a point value — **inside the paragraph this review round is about**, and `t61` passed all three because
the values do exist in the artefacts. Existence checks cannot catch kind errors; that was the finding of
last round's sweep (7 of 16) and it has now recurred.

Extend `num()` with a `kind=` argument taking `"point" | "range" | "cell"`, and for any value drawn from
a multi-cell artefact require the caller to declare which:

- `kind="cell"` must name the cell (`pos`, `seed`) and the check asserts the paper says so too;
- `kind="range"` asserts **both** endpoints appear;
- `kind="point"` asserts the value is genuinely constant across cells — and **fails if it is not**.

Retrofit the ~40 multi-cell numbers in the body. This is the single highest-yield gate change available:
it is the one failure mode that has survived every round so far.

---

## 4. Shape of the round

| item | kind | new compute | blocks the rewrite? |
|---|---|---|---|
| R1a / R1c | writing + correction | no | yes |
| R1b | recomputation (~30 lines, existing pipeline) | small | no |
| R2a | **factual error, live in the paper** | no | yes |
| R2b / R2c | theorem scope + new corollary | no | yes |
| R3a | wording | no | yes |
| R3b | author emails | — | no |
| **R4** | **new stage `t63`** | **yes** | yes |
| **R5a/R5b** | **rerun frontier + contamination, canonical** | **yes** | yes |
| R5c / R5d | labelling audit | no | yes |
| R6 | rename + demote a claim | no | yes |
| R7 | attribution | no | yes |
| A | reconcile contradiction | no | yes |
| B | `t61` kind gate | no | no |

**Two new computations, both reviewer-authorised** (R4, R5a/b), plus one cheap recomputation (R1b).
Everything else is writing — but R2a and A are *errors*, not polish, and R1a changes a scientific
interpretation rather than a phrasing.

**Order:** R2a + A first (they are wrong, and they are two-line fixes) → R1 → R2b/R2c → R5 → R4 →
R6 → R7 → R3a → B. The page-limit refit stays where the author put it: **last, and by hand**
(`[[paper-refit-at-the-end]]`).
