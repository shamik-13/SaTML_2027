# Round-9 reviewer worklist

Triage of the round-9 feedback. Every point verified against the source before being
accepted. Verdict column: **valid** = the reviewer is right and the fix is as they
describe; **valid+** = right, and the investigation found more instances or a stronger
repair than proposed.

| # | point | verdict | evidence |
|---|---|---|---|
| A | group-exchangeability overstatement survives at 2 sites | **valid+** (3rd site found) | `main.tex:277`, `:1179`, `:1351`, and `:1193-1197` |
| B | Corollary 8's "exactly $\rho$" does not follow | **valid+** (exact finite-horizon route available free) | `appendix_proofs.tex:139-144`, `main.tex:581-586`, `:592-596` |
| C | IV-C "exactly when" is broader than Prop 2-3 prove | **valid** | `main.tex:519-521` |
| D | global stale-number / order audit | **valid** — 16 sites | see D-table below |
| E | keyed-insertion capability assumption must travel | **valid** | `main.tex:822-824`, `tables/blindkey.tex` |

---

## A. Group exchangeability — the safe claim, everywhere

**The reviewer's argument is correct.** Split conformal on the grouped unit needs
calibration and *true-null* test groups to be exchangeable. Padding changes the
**attacked** group, which is a **false null** — the assumption says nothing about it, so
padding is not evidence that the assumption fails. Three surviving formulations assert
that it does.

The governing formulation, used verbatim at every site from here on:

> group-level calibration replaces Assumption 1 with ordinary group exchangeability;
> arity heterogeneity shows that assumption may be fragile under group-formation shift,
> but even granting it completely, the construction is infeasible.

| site | current | action |
|---|---|---|
| `main.tex:277` (p3) | "replaced by a group exchangeability that adaptive group formation breaks" | drop the "breaks" clause |
| `main.tex:1179` (p13, non-claims) | "relocates the premise onto arity" | drop; keep the `cor:calhorizon` half |
| `main.tex:1351` (limitations) | "relocates the premise onto arity and silences..." | drop the first conjunct |
| `main.tex:1193-1197` (IX-B) — **found here, not flagged** | "under our threat model the test groups are adversarially constituted and exchangeability fails by **construction**, not by correlation" | same error class. Not fixing it would leave IX-B asserting exactly what pages 3 and 13 are being made to stop asserting. Rewrite to fragility-under-shift. |

Note on IX-B: insertion *does* bear on true-null groups (the adversary instantiates
ordinary endpoint pairs, which enter the stream as nulls), unlike padding. But
"adversary-constituted" is not the same as "not exchangeable" — inserted ordinary traffic
may well be exchangeable with calibration. Fragility, not failure, is what we can support.

**The infeasibility half is untouched and does all the work.** No number moves.

## B. Corollary 8 — proof repair, and a stronger exact form

Current proof: $\liminf_t Z_t/t \ge \rho$ gives $Z_t \ge \rho t/2$ eventually, then claims
the horizon is "relaxed by **exactly** the factor $\rho$". The displayed step yields
$\rho/2$, not $\rho$; "exactly" does not follow.

The reviewer offers two repairs. **Both are done**, because the exact one costs nothing:

1. **Asymptotic (their suggestion, correct as stated).** For every
   $\rho' < \liminf_t Z_t/t$ there is a $t_1$ with $Z_t \ge \rho' t$ for $t \ge t_1$,
   giving the horizon rescaled by $\rho'$ — for every $\rho'$ below the liminf, not
   "exactly $\rho$".

2. **Exact, finite-horizon, pathwise — no density and no asymptotics at all.**
   Let $P_T = \#\{i \le T : E_i > 0\}$. Then $Z_t \ge t - 1 - P_T$ for every $t \le T$
   *by counting alone*. With $H = \min\{j : \gamma_j < 1/(\delta\,\ceil)\}$ the index
   horizon of `thm:family1`, the closure's real-time horizon satisfies
   $$t_{\text{closed}} = \inf\{t : Z_t \ge H-1\} \ \le\ H + P_T .$$
   An **additive offset of $P_T$**, not a multiplicative rescaling. Nothing is assumed.

   $P_T$ is already in the artefact (`t56_uai26.json`, `n_positive_evidence`), and is
   order-invariant as it must be:

   | window | 0.55 | 0.62 | 0.70 | 0.77 | 0.85 |
   |---|---|---|---|---|---|
   | $P_T$ (seed 0 / 1) | 110 / 104 | 109 / 110 | 69 / 0 | 60 / 59 | 152 / 152 |
   | $P_T/T$ | 0.19% | 0.22% | 0.19% | 0.19% | **0.48%** |

   So $t_{\text{closed}} \le H + 152$ on every window and seed measured.

This replaces a claim that did not follow with one that is exact and measured. The
empirical sentence ("$\rho \ge 0.995$, the rescaling is negligible") is restated as the
additive offset.

Sites: `main.tex:581-586` (statement), `main.tex:592-596` (prose), `appendix_proofs.tex:139-144`.

## C. IV-C — narrow the characterisation

`main.tex:519-521` states the boundary as a **universal** characterisation ("binds a
procedure **exactly when** its spending index advances on every hypothesis"). `thm:family1`
admits escape through sufficiently fast history-dependent level growth, which is a third
route neither of the two named. Narrow to *among the procedures studied here*. Nothing
else in the subsection changes: ADDIS and online e-BH remain the two measured escapes.

## D. Global stale-number / order audit

The headline switched to canonical order in round 7. Pieces of the first-flow story
survived. Ground truth, established by inspection of every task source: exactly **ten**
artefacts carry an order arm — `t28b`, `t38`, `t48`, `t53`, `t56`, `t58`, `t59`, `t60`,
`t63`, `t64`. **Every other task defaults to `order="first-flow"`** (`h_stream.py:184`);
none of them passes `order=`. So any table sourced from any other artefact is first-flow,
full stop.

### D1 — the blanket convention is false as written

`main.tex:321-324`: "every **detection count** is reported under the **canonical**
within-bucket order". Sixteen tables contradict it. Replace with the reviewer's
convention, which is both true and better:

> headline absolute results use canonical order; paired ablations and sensitivity
> analyses may use first-flow, but every such table explicitly labels it as the
> optimistic upper-bound order.

### D2 — unlabelled tables carrying order-dependent numbers

| # | table | source | order-dependent quantity | state |
|---|---|---|---|---|
| III | `tab:procedures` | `t21c` | 18 / 72 rejections, FDP, silence % | unlabelled |
| XI | `apptab:smoothing` | `t34` | 18.0 / 24.1 / 12.5 rejections | unlabelled |
| XII | `apptab:restart` | `t35` | 18/18 baseline, recall 0.065 | unlabelled |
| XIV | `tab:pools` | `t28b` | 13 / 72 detected, all costs | unlabelled |
| XV | `tab:asym` | `t36` | recall 0.065, $L^\star$, appended | unlabelled |
| XVII | `apptab:caps` | `t25` | det. raw / det. trunc. | unlabelled |
| XVIII | `apptab:addisstate` | `t32` | $B^\ast$, 147 detections, break-even | unlabelled |
| XX | `apptab:units` | `t41` | 5,202 / 72 | unlabelled **+ factually wrong**, see D3 |
| XXII | `apptab:r7host` | `t49` | 2 vs 18; 118 / 5,202 | unlabelled |
| XXIII | `apptab:r7ait` | `t51` | detections per organisation | unlabelled (AIT) |
| XXIV | `apptab:aitsupp` | `t54` | 84 of 85, $r^\star$ | unlabelled (AIT) |
| XXVII | `apptab:feedback` | `t40` | FDP under P/PI/AQT | unlabelled **+ stale window name**, see D6 |
| XXXV | `apptab:audit` | `t31` | $R = 151/152$, FDP by method | unlabelled |
| XXXVI | `apptab:bates` | `t23` | median rejections, nominal vs $\beta$ | unlabelled |
| Fig 4 | `fig:attacks` | `t28b` | panel A's ~72-flow costs | unlabelled **+ stale window name** |

Order-**invariant**, correctly carrying no label — recorded so the gate does not demand one:
`apptab:tail`, `apptab:a1strata` (benign flows scored against the calibration threshold; no
controller, no stream order), `apptab:addissynth` (synthetic stream, no LSPR23 ordering).

Already labelled, no action: `apptab:detection`, `apptab:procmatrix`, `apptab:grouping`,
`apptab:qsweep`, `apptab:transfer`, `apptab:w7coverage`, `apptab:groupcal`, and every
order-armed table.

### D3 — `apptab:units` row 1 is factually wrong

Caption: "Row 1 is the headline cost --- the median over e-LOND's own 72 detections at
0.85 ... **and the value quoted in `tab:main`**". `tab:main`'s 0.85 row is canonical: **34
detections, median pad cost 116**. The 5,202/72 pair is first-flow. The cross-reference to
`apptab:padpools` is correct (that table carries both arms); the one to `tab:main` is not.

Fix, and better than a fix: `t28b` **already ships the canonical arm**
(`table1_by_order.keyhash["0.85_0"]`: 34 detections, `med_pad_real` 115.5). Add a canonical
row to `t41`'s budget list so the operational-units table actually carries the headline,
and demote the first-flow row to the labelled optimistic arm.

### D4 — `tab:pools` gets its canonical block

Hand-written in `main.tex`, so no gate covers it. `t28b.pools_by_order["keyhash"]` has the
canonical medians for all five pools at both windows (0.62: $n$=11, medians 6/6/6/7/6;
0.85: $n$=34). Add the canonical block, keep first-flow as the labelled optimistic arm, and
put the numbers under `t61`.

### D5 — two unlabelled first-flow numbers in the body prose

- `main.tex:989` (`sec:state`): "Suppressing one e-LOND alert, by contrast, costs a median
  5,202 flows --- $2.1\times10^{-3}$ of the window's traffic, four orders of magnitude
  below." First-flow, unlabelled. Canonical is **116** flows, which makes the padding-vs-state
  gap *larger*, so the current text understates our own result.
- `main.tex:895` (`sec:transferattack`): "$r^\star=108$ against $118$" — first-flow,
  unlabelled.

### D6 — `apptab:feedback`: "guarantee window" is a round-7 casualty

`t40`'s window key is literally `"guarantee (0.55)"`. That is the **primary analysis
window** under the current naming. The artefact key stays (it is data); the caption is
prose and must be renamed. Same for `fig:attacks` panel A, where 0.62 is the **replication
window** — the string lives in `make_figures.py:211` as well as the LaTeX caption.

### D7 — `apptab:prevalence` reverted to a factual claim

Caption: "against an **ordinary SOC's** $10^{-4}$--$10^{-6}$". Round 8 removed exactly this
framing from the body — the targets are a swept sensitivity parameter, and the figure is
uncited. Reframe to match the body.

### D8 — a gate, so this cannot recur

The failure mode here is structural: an experiment's default order is first-flow, a table
is added, and nothing forces the caption to say so. Add to `t61` an explicit **order
registry** mapping every generated table to one of `canonical` / `first-flow` / `both` /
`order-invariant (with a stated reason)`, asserting the caption carries the matching
declaration, and asserting the registry covers every table the generator emits. A new table
then cannot ship without declaring its order.

Gate must be **tested against the failure it exists to catch**, not merely run green:
stripping the label from a labelled caption must make it fail with a diagnostic naming the
table.

## E. Keyed insertion — the capability assumption travels with the number

$N_{99}$ reaches $3.15\times10^{4}$ (0.77) and the body quotes $3.4\times10^{4}$. Those are
**distinct $(\mathrm{SrcIP},\mathrm{DstIP})$ pairs the adversary must actually send traffic
between** — a capability, not a compute cost. The paper states this condition for the
*public*-hash cost (`main.tex:815-816`, "enough endpoint pairs the adversary can actually
send between") but not for the keyed result, which is where it bites hardest. Without it a
reviewer can fairly say a secret seed is much stronger on a network where the attacker
controls few reachable pairs — and they would be right.

Add one sentence to `sec:attack` and one clause to `apptab:blindkey`'s caption. No number
moves.

---

## Verification

- Implementation items (D3 `t41` canonical row, D4 `tab:pools` numbers, D8 the `t61`
  registry gate, B's exact finite-horizon corollary) go to a **blind codex audit** before
  being trusted.
- `t61` (paper vs artefacts) and `t45` (record vs artefacts) after every edit.
- 30 appendix tables must regenerate byte-identically except where a change is intended.
- Build: 0 overfull, 0 undefined references.

## Not doing

Nothing descoped. All five points accepted.

## Status

- [x] investigation
- [x] A -- four sites (three flagged, one found here in IX-B)
- [x] B -- corollary statement, proof, prose; BOTH forms, the exact one primary
- [x] C -- narrowed to "among the procedures studied here", third route named
- [x] D1 -- convention replaced with the headline/ablation split
- [x] D2 -- 16 captions labelled (13 generated, 2 main.tex tables, Figure 4)
- [x] D3 -- `t41` canonical row; both budgets now READ from `t28b`, not hard-coded
- [x] D4 -- `tab:pools` moved into the generator, both order blocks
- [x] D5 -- two unlabelled body numbers; the ratio derived in `t61`, not by hand
- [x] D6 -- `apptab:feedback` and Figure 4 window names
- [x] D7 -- `apptab:prevalence` "ordinary SOC" reframed
- [x] D8 -- order registry gate in `t61`, tested against 7 injected failures
- [x] E -- capability assumption in `sec:attack` and `apptab:blindkey`

**Two holes in my own gate were found by testing it** (a lowercase-only regex that skipped 20 of
31 generators, and a def-to-load adjacency assumption). Both fixed; an unresolvable registry entry
now fails rather than skipping.

**Blind codex audit:** confirmed the corollary mathematics and every printed number; returned
5 MAJOR + 1 MINOR, all guard strength, none a wrong value. All six fixed and each re-tested against
the failure case codex constructed. The sharpest: `_artefact_has_order_arm` was a **substring**
search, so `t41_E8.json` matched on a prose provenance string I had written and passed reachability
for the wrong reason; and a missing artefact made every check reading it vanish while the process
still exited 0. `apptab:frontier` was a fourth embedded `main.tex` table with no order check, and
`tab:terms` a fifth.

**Verification:** `t61` **260**/0, `t45` 268/0, `t62` 470 strong / 12 previously-adjudicated,
**15** self-tests 0 failures, 31 tables byte-identical, build 0 overfull / 0 undefined refs, body
p17. Twelve injected failures caught in total.

Recorded in `docs/04` section 4.67.

**REMAINING: the author's manual narrative refit only.**
