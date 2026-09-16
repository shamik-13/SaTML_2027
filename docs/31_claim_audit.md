# Reviewer-style claim audit of the current manuscript

Method: for every strong sentence in the abstract, contributions, theorem statements, conclusion,
figure captions and table captions, ask *does the theorem or experiment establish exactly this
wording?* No new science proposed. Fourteen findings, ordered by how a reviewer would weight them.

Severity: **A** = a claim the result does not support as worded; **B** = correct but a reviewer can
reasonably read it as more than it is; **C** = internal inconsistency or ambiguity.

---

## A1 — The abstract and contributions state `cor:budget`'s *special case* as the general result

**A.** Both say feasibility over horizon $T$ "needs a calibration set $\nCal \ge kT/c_0 - 1$".
`cor:budget` says that only **under horizon-uniform $\gamma_t = 1/T$**; its general form is
$\nCal \ge k/\alpha_T - 1$. The condition is dropped in both places.

- abstract, `main.tex:76-78`
- contributions, `main.tex:141-143`

This cuts *against* us — horizon-uniform is max-min optimal, so it is the **cheapest** requirement,
and under the horizon-free $\gamma\propto j^{-1.6}$ the paper's own figure is $3.2\times10^{13}$
rather than $6.5\times10^{8}$. A reviewer checking the corollary against the abstract finds a missing
hypothesis; the fix also strengthens the claim.

## A2 — "Take any procedure whose level is multiplicative…" drops `thm:family1`'s $\gamma$ condition

**A.** Contributions (`main.tex:137-140`): *"Take any procedure whose level is multiplicative in a
spending sequence or a lag-sum over rejection times… the set of times at which it can reject during a
rejection-free run is finite, and the infeasible state is absorbing."*

`thm:family1` requires $\gamma_t t^{d} \to 0$ for finiteness and *additionally* eventual
monotonicity for absorbing. The body says so plainly two paragraphs later — *"The degree condition is
asymptotic and must be checked per procedure"*, and *"a procedure whose level grew quadratically in
the rejection count would escape the argument"*. So the contributions assert exactly what the body
then denies. The abstract (`main.tex:73-76`) has the same gap, though it is narrower there because it
names the four procedures.

Same sentence also silently merges the two propositions: the lag-sum family is `thm:family2`, which
needs **no** monotonicity, so the merged wording is wrong for one half and incomplete for the other.

## A3 — The abstract's padding cost is a median of medians spanning three orders of magnitude

**A.** `main.tex:83-85`: *"costing a median $\approx\!10^2$ ordinary flows across audited orders"*.

Verified against `t28b_reallevel.json`: the seed-0 per-window medians across the two audited orders
are $\{6, 24, 72, 115.5, 118, 1165, 1850.5, 5201.5\}$. Their median is $116.75$ — so
"$\approx 10^2$" is arithmetically defensible and **rhetorically not**: it compresses a
$6$–$5{,}202$ spread into a point. This is the failure mode the round-8 `cell_num` gate was built
for, sitting in the one paragraph that gate does not police as a range.

The clause that follows it (*"and only $23$–$33$ for the episodes the canonical order detects at the
primary window"*) is exact and well-scoped — it is the $\approx\!10^2$ that needs the spread.

## A4 — The online e-BH horizon-robustness claim rests entirely on the known-invalid window

**A.** `main.tex:535`: *"its advantage is robustness to a misspecified horizon (144 of 152 rejections
survive a $100\times$ over-estimate, against $2\times$ for LOND)"*.

`t21d_H6_horizon.json` has `config.POS = 0.85` — **one window, and it is the known-invalid one**.
The sentence names neither. It sits in `sec:escapes`, which otherwise carries the C1 argument, so a
reviewer reads it as a general property of the escape.

Two further problems in the same clause:
- **the comparison has mismatched units** — "144 of 152 rejections" (a count) "against $2\times$ for
  LOND" (a factor). What survives $2\times$ for LOND is not stated.
- it is a single seed as well as a single window.

## A5 — Surface B's headline is demonstrated on the invalid window; the abstract and contributions do not say so

**A/B.** Abstract (`main.tex:85-87`) and contributions (`main.tex:168-171`) both say the attacker can
*"silence ADDIS permanently"*. The real-stream demonstration (`main.tex:956-958`,
*"$B = 202$ precursor episodes leave all 152 rejections intact, and $B = 203$ leaves none"*) is at
position **0.85**, and that sentence does not name the window either.

The paper **does** have the right defence — `apptab:addissynth` reproduces the mechanism on a
synthetic stream where ADDIS's guarantee genuinely holds — but it arrives a page later, and neither
the abstract nor the contributions mention it. As written, the strongest attack claim in the paper is
first met by the reader as a measurement on the window the paper elsewhere calls known-invalid.

**This is the specific "stress-window measurement sounding guarantee-bearing" case the audit was
looking for, and it is the most damaging one, because it is in the abstract.**

## B1 — `fig:envelope`'s caption puts an *escaping* procedure inside the covered set

**C.** *"linear in $T$ for every procedure covered by `thm:family1,thm:family2`, differing only
through $c_0$ … and, for online e-BH, in $T$ per simultaneous discovery."*

Online e-BH is one of the two procedures the paper identifies as **escaping** those propositions. The
grammar appends it to the covered list. A reviewer who has read §IV-C will read this as a
contradiction; a reviewer who has not will conclude e-BH is covered.

## B2 — "No symmetric e-merging rule that can fire resists adversarial padding" vs the cap

**B.** The abstract's blanket (`main.tex:82-83`) is *literally* consistent with `thm:padding`,
because the pre-committed cap $\sum e/n_0$ "is not an e-merging family above $n_0$". But the cap is
symmetric, does fire, and *is* padding-robust within its cap — the body says exactly that at
`main.tex:816-820`. The abstract gives the reader no signal that the escape-by-inadmissibility exists,
and it is the first thing a multiple-testing reviewer will look for.

## B3 — "two detectors" in the abstract overstates the evaluation's span

**B.** `main.tex:87-88`: *"Evaluated on 16,353,511 live-fire flows over five deployment windows and
two detectors"*. The second (host-conditioned) detector appears only in `sec:transferattack` as a
transfer check, not across the evaluation. Every headline number is the flow-only detector.

## B4 — "at security scale" (abstract) vs "at LSPR23 scale" (body) for the same number

**C.** `main.tex:77-78` calls $6.5\times10^{8}$ / $3.3\times10^{8}$ the requirement *"at security
scale"*; `main.tex:449-450` calls the identical figure *"at LSPR23 scale"*. The body's qualifier is
the honest one — the number is a property of this stream's $T$. The abstract's reads as a general
claim about security deployments.

## C1 — The conclusion's first sentence has an ambiguous referent

**C.** *"Finite conformal evidence and uninterrupted control create a finite discovery horizon,
exceeded by a wide margin at security scale."*

**What is exceeded by what?** The horizon is not exceeded; the *calibration requirement* exceeds what
any available corpus supplies. As written the sentence can be read as saying deployments routinely run
past the horizon, which is a different (and unestablished) claim.

## C2 — The same insertion-vs-padding fact is reported with opposite polarity and the wrong noun

**C.** `main.tex:845` — *"insertion does \emph{not} beat padding for one alert ($12/12$ windows)"*.
`tables/insertion.tex:13` — the same fact as *"(0/12 cells)"*.

Two problems: the polarity is inverted between the two statements of one result, and **"$12/12$
windows" is wrong — there are five windows.** The 12 are window$\times$order *cells*, as the table
correctly says.

## C3 — `sec:paddingcost`'s "cheap" headline averages over an invalid window

**B.** *"suppressing a detected alert is \emph{cheap}: under the canonical order the medians are
$24$, $6$ and $116$ flows at the three windows that detect anything"*. One of those three **is
0.85**. The sentence says "the three windows that detect anything" without noting that the largest of
the three is the known-invalid one. The surrounding subsection does not re-establish the caveat.

## C4 — `apptab:units`, `apptab:addisstate`, `apptab:audit` quote 0.85 with no invalidity qualifier

**B.** Mechanical sweep of all 36 captions for "0.85 named, invalidity not": three hits, all in the
attack appendix. Each is a table whose *entire* content is the stress window. `apptab:addisstate`
("$B^\ast=203$ precursor episodes permanently silence the controller (position 0.85)") is the one
that reads as a standalone result.

*(Not findings: `apptab:semblur` and `apptab:uai26` also matched the sweep but carry the caveat in a
different form — semblur's "0.70/first-flow" phrasing and uai26's per-row window column.)*

## C5 — The conclusion never restates that every FDR number is conditional on Assumption 1

**B.** The conventions paragraph, `tab:main`, §IX and §X-Limitations all carry it. The conclusion
recommends that *"these guarantees must be evaluated as properties of the composed system"* without
noting that our own FDR statements rest on `assump:groupval`. A reviewer reading abstract +
conclusion only — which is how a program committee triages — sees no conditionality at all.

## C6 — `thm:reach`'s statement conflates the quantity with its bound

**C.** *"the number of positions at which a lone attack flow can fire the rule is $P \le \alphat
\ceil$"*. $P$ is defined as that number and then given as an inequality in the same breath. Reads as
a definition that is also a bound. One-word fix ("is at most").

---

## What the audit did **not** find

- No theorem statement is wrong. `thm:padding`, `thm:family2`, `cor:calhorizon`, `thm:frontload` and
  the repaired `cor:closureabsorb` all say exactly what their proofs give.
- **Alert blur is genuinely monotone** in bucket width at all five windows (checked against
  `t47_W7.json`, src-dst family: 1.0 to 20.4–38.5, no inversion), so "increasing" and "from one to
  tens" are exact, not approximate.
- Horizon-uniform $\gamma$'s **max-min optimality is proved**, not asserted
  (`appendix_proofs.tex:83`) — the abstract may rely on it.
- The order labelling introduced in round 9 survives this audit: no caption claims an order its
  artefact cannot supply, and the `t61` registry now enforces that.

## STATUS: all 14 fixed (2026-09-02)

Every finding is repaired in `main.tex` / `make_appendix_tables.py`, and **every repair is pinned by
a `t61` check** under the `ROUND 9 / CLAIM AUDIT` banner --- because a compression pass removes
qualifying clauses first, which is precisely how these overclaims arose. `t61` went 261 -> 288
checks.

Five reverts were injected to confirm the new gates fail when they should: dropping the
horizon-uniform condition (A1), restoring "any procedure whose level is multiplicative" (A2),
recompressing the padding spread to a point (A3), removing the invalid-window qualifier from the
abstract (A5), and putting back "$12/12$ windows" (C2). All five caught.

One pre-existing gate had to be repointed rather than repaired: it tested for the literal string
`$12/12$`, which C2 removed. It now derives both numbers from `t60_positional.json` **and asserts
the denominator is called *cells*, not windows** --- gating the noun, since the wrong noun was the bug.

Two corrections to the audit itself, found while fixing:
- **A4's comparison was wrong in the paper, not merely vague.** "against $2\times$ for LOND" implied
  LOND fails at $2\times$. `t21d` says LOND keeps all $151$ rejections at $2\times$ and **none** at
  $100\times$; it is **LORD++** that fails already at $2\times$. The repaired sentence states all
  three.
- **A3's abstract range is $6$--$5{,}202$**, the per-window median across audited orders --- not the
  median-of-medians ($116.75$) the old text compressed to "$\approx\!10^2$".

Build after the repairs: 0 errors, 0 overfull, 0 undefined references, body still ends **p17**.
Underfull (loose-line) warnings rose from 14 to 20, since several sentences gained qualifying
clauses; cosmetic, and the refit absorbs them.

## Suggested order of work

1. **A5, A4, A3** — the three places a stress-window or compressed statistic is doing work in a
   headline. A5 first: it is in the abstract.
2. **A1, A2** — restore the dropped hypotheses. Both are one clause each and A1 makes C1 stronger.
3. **B1, C2, C1, C6** — internal contradictions and wrong nouns; cheap and each is exactly the sort
   of thing a reviewer quotes back.
4. **B2, B3, B4, C3, C4, C5** — qualifier consistency.

Every item is a wording change. **No number moves and no experiment is implicated**, so this can be
folded into the narrative refit rather than done before it.
