# Review 11 worklist — theory freeze, rhetorical precision, float repair

Source: reviewer feedback on `paper/satml.tex` (2026-09-03), after review 10's correctness round.
Six points in the reviewer's own priority order. Every point is reviewed by a **blind codex agent**
before it is marked done (see `blind-codex-review-workflow`).

| # | Item | Status |
|---|---|---|
| R11-1 | **Independent mathematical proof audit, then freeze the theory.** Give a strong reader only §II–III, §V-A, §VI and Appendix A. Ask *only*: find a counterexample or a quantifier/scope error. Targets named by the reviewer: Thm. 1's absorption definition, the revised $\delta<1$ donation restriction, the closure, Thm. 3's attainment qualification, Thm. 4's pre-/post-rejection distinction. No general paper feedback. | todo |
| R11-2 | **Two logical/rhetorical sentences.** (a) "C1 is therefore also the premise C2 needs" overstates — C2's padding theorem does not mathematically require C1; C1 explains why aggregation becomes operationally necessary. (b) §III-D's "Four constructions that might be expected to rescue feasibility do not" contradicts the next two sentences (smoothing dissolves absorption; restart recovers real power) → "alter the boundary, but none removes the tradeoff for free". (c) Scope "the barrier is a property of the evidence, not of the controller's sophistication" to the elapsed-time/cold-start procedures, since online e-BH is presented as a genuine escape. | todo |
| R11-3 | **Two abstract wordings.** (a) "every escape we measure pays elsewhere" — "escape" means escaping the finite horizon everywhere else in the paper (ADDIS/e-BH), but here means aggregation fixes → "the aggregation fixes we measure each pay elsewhere". (b) "In the deployed pipeline" → "evaluated"/"end-to-end", since the Ethics section says all measurements are on research datasets, so "deployed" invites a factual objection. | todo |
| R11-4 | **Remove revision-history language from the appendices.** "the earlier version of this proof assumed…", "the earlier reading…", "the 0.43 … once reported…", and repeated "the pipeline originally shipped". Keep every mathematical clarification, delete the historical framing. | todo |
| R11-5 | **Two float interruptions.** Table I lands between "We sort by" (p.3) and "timestamp…" (p.4); worse, the §V-D sentence ends p.8 at "higher AUROC … (0.954" and resumes p.9 after Table III with "against 0.916…". Fix by float placement, not by changing content. | todo |
| R11-6 | **AIT canonical-order rerun — only if cheap.** The 84/85 abstract number is first-flow-only and its order sensitivity was never audited on AIT. Do it *iff* it is resequencing existing groups / replaying existing scores; skip if it is a new experimental branch. No third dataset, no extra detector, no extra FDR procedure. | todo |

## Findings log

(appended per item, with the blind review verdict for each)

## Progress

### R11-2 — three logical/rhetorical sentences  **applied, review pending**

- **(a) "C1 is therefore also the premise C2 needs."** Correct: \cref{thm:padding} is a statement
  about symmetric e-merging functions and does not depend on C1 at all. Now: *"C1 therefore motivates
  the operational setting in which C2 becomes consequential --- \cref{thm:padding} does not depend on
  it --- and it is why the repair C2 attacks is the one a deployment reaches for."* The
  ranking-quality/margin clause is kept, since §III-C does support it.
- **(b) §III-D's opening contradicted its own next two sentences.** "Four constructions that might be
  expected to rescue feasibility do not" sat immediately before "smoothing *dissolves the absorbing
  state*" and "restart *recovers real power*". Now: *"Four constructions alter the boundary, but none
  removes the tradeoff for free."*
- **(c) The barrier sentence was unscoped** while online e-BH is presented two paragraphs earlier as
  a genuine escape. Now scoped: *"Among the elapsed-time procedures bound by
  \cref{thm:family1,thm:family2}, the cold-start barrier is therefore a property of the evidence
  rather than of the controller's sophistication; escaping it takes a different spending mechanism,
  not a better one."*

### R11-3 — abstract wording  **applied, review pending**

- "every escape we measure pays elsewhere" → **"the aggregation fixes we measure each pay
  elsewhere"**. The reviewer is right that *escape* is a load-bearing term elsewhere (escaping the
  finite horizon: ADDIS, online e-BH), so reusing it for aggregation fixes collided with it.
- "In the deployed pipeline" → **"In the end-to-end pipeline we evaluate"**.

**Swept the class rather than fixing only the abstract.** `deployed` appeared four times, and the
sharpest was not the abstract: the **Ethics section opened** with *"working attacks against a
deployed statistical decision layer"* while its own Beneficence paragraph says the class is *"not yet
widely deployed"* and its Respect-for-persons paragraph says *"No attack was executed against any
live network"*. That is the factual objection the reviewer warned about, stated against itself inside
one section. Now "a statistical trust layer for intrusion detection". The two "the deployed mean"
uses in §V became "the mean rule we evaluate" / "that mean rule". One use remains, and it is the
correct one: "not yet widely deployed".

### R11-5 — float interruptions  **applied, review pending**

Both reported breaks are gone, but only the second was fixed *deliberately* — worth recording
honestly.

- **Table I / "We sort by | timestamp".** Already resolved by the reflow from R11-2/R11-3: Table I and
  the intact sentence now share p.4. Not a fix I made; verified rather than engineered.
- **Table III / the AUROC sentence.** This one was real and is fixed by **float placement, not
  content**. `tab:main` was declared at source line 762, inside §V-C, but first cited at line 492
  (§III-C) and again at 709 (§V-B) — so LaTeX had no legal early slot and pushed it to p.10. Moving
  the `table*` block to just before §V-B's subsection heading puts it at the top of p.9, and
  *"higher AUROC at both headline windows (0.954 against 0.916 at the primary window)"* is now intact
  on a single page. `[!t]` was tested and places identically, so `[t]` was kept.
- **Residual, stated rather than hidden:** a full-width `table*` in a two-column layout always sits
  between one page's last line and the next page's continuation, so *something* is interrupted unless
  the break falls on a paragraph boundary. After the move the break falls on the short clause "The
  pad is large | but not anomalous", which costs the reader nothing comparable to splitting a number
  from its comparator. Chasing it further would mean editing content, which this point explicitly
  rules out.

### R11-6 — AIT canonical order  **feasibility: CHEAP, running**

The reviewer's test was "merely resequencing existing groups / replaying existing scores" vs "a
significant new experimental branch". It is the former:
- all eight AIT scenarios are already on disk (`proto/data/NF__*_netflows.zip`, 261 MB) and already
  extracted to the cache, so no download;
- in `t54`, everything expensive — leave-one-org-out feature selection, the per-fold detector fit,
  the scores, the chronological in-org calibration, the e-values — happens **before** episodes are
  ordered. Only the permutation, the controller run and the replay pricing depend on the order.

Implementation: `episodes()` and `run_org()` in `t54` gained an `order` kwarg **defaulting to
first-flow**, so every previously reported AIT number is untouched (verified: the default branch is
the identical `lexsort`, checked against the explicit argument on synthetic input). The canonical
branch calls `h_stream`'s own `key_hash`/`hashed_order`, so "canonical" cannot come to mean different
things on the two datasets. New stage `src/lib/t67_ait_order.py` runs the flow-only folds under both
orders and **re-derives the stored first-flow arm as a read-back check** that it is running the same
chain, not merely a similar one.

### R11-1 — proof audit  **DONE, two rounds, theory now freezable**

**Round 1: 1 CRITICAL, 1 MAJOR, 2 MINOR.**

- **CRITICAL — Theorem 4 was false without a hypothesis.** ADDIS's level is
  $\alphat=\min\{\lambda,\cdots\}$. If the cap sits *below* the conformal floor the controller is
  already silent at $D=0$ and the true budget is zero, while the displayed $B^\star$ is positive.
  Verified counterexample: $k=1$, $\nCal=899$, $w_0=W=0.025$, $\lambda=0.001$, $\tau=0.999$ gives
  formula $B^\star=4$ against a true $0$. Fixed by stating $\lambda\ge k/(\nCal+1)$ in the theorem
  and the proof, plus the degenerate case. **No number moves**: our configuration satisfies it by
  $\lambda\ceil=4.5\times10^{5}$.
- **MAJOR — "absorbing" carried two senses**, and round 2 held the freeze until it carried one.
  §III-A's predicate compares a level *fixed at step $t$* against the ceiling; online e-BH's
  threshold is a joint fixed point over the history, so the predicate is **not defined** for it
  rather than false. Table II's cell is now `n/a` with a footnote; the prose says what it escapes
  (the *permanence* of an early infeasible prefix) and what it does not (bounded evidence still
  leaves an index no attainable step-up count can reach).
- **MINOR — Corollary 2's rescaling direction** was backwards: rescaling the index by $\rho'$
  stretches the absorption *time* by $1/\rho'$. Round 2 then caught that the liminf gives its bound
  only past an onset $t_1$, so absorption is by $\max\{t_1,\lceil(H-1)/\rho'\rceil\}$ — a positive
  liminf permits an arbitrarily long transient.
- **MINOR — the margin boundary is inclusive.** e-LOND fires at margin $=-\tfrac12$, not only above
  it, since the rejection rule is $\Ev\ge1/\alphat$.

**Round 2: 0 CRITICAL.** It re-derived the $\delta=1$ donation counterexample, confirmed
$c_g=\delta/[\alpha(1-\delta)]$, closure form (i), Theorem 3's attainment argument and the
$\tfrac12\mathrm{mean}$ separating example, and Lemma 1's tower argument, and found **no new error
introduced by the corrections**.

### R11-6 — AIT canonical order  **DONE, reviewed**

**Result: 78 of 79 suppressible under the canonical order**, against 84 of 85 under first-flow, and
the canonical alerts are the *cheaper* to suppress — per-organisation median $r^\star$ falls from
$212$–$8{,}294$ flows to $12$–$4{,}650$. The LSPR23 pattern (canonical detects fewer, and cheaper)
reproduces on the second dataset. The abstract now carries the canonical figure with **no order
qualification at all**: the caveat is gone because the gap is gone.

**Blind review: 1 CRITICAL, 1 MAJOR, 1 MINOR — all valid, all fixed.**

- **CRITICAL — `main.tex` still stated 84/85 as the AIT headline** in two places while printing the
  shared `apptab:aitorder` that reports canonical 78/79. It is a buildable source carrying a
  superseded result. Both sites now report canonical with first-flow as the sensitivity.
- **MAJOR — my RNG comment claimed a pairing that does not hold.** Identical seeds do not pair the
  arms: the orders detect different numbers of episodes, consume different numbers of draws, and
  attach a given draw to different episodes. What is identical is the *deterministic* part (fit,
  scores, calibration, e-values, closed-form $r^\star$ given the order); the replay success rates are
  independent Monte Carlo estimates per arm. Comment corrected, and §V-D's "so only the permutation
  changes" became "are identical across the two arms", which is what is actually true.
- **MINOR — the read-back check compared only aggregates**, so a wrong canonical branch could pass.
  Strengthened to per-organisation field-by-field equality over eight fields, and the same comparison
  is enforced in `t61` directly from the two stored artefacts so the guarantee does not wait on a
  re-run. Verified it passes: **0 field mismatches across all orgs**.

**Verified correct by the review:** the default `episodes()` path is the original lexsort; the
canonical branch calls `hs.key_hash`/`hs.hashed_order` with the same fields, field order and seed 0
that `h_stream.build_episodes(order="keyhash")` uses for LSPR23; all seven returned arrays are
indexed by the same permutation; and the abstract, §V-D, Table III and `tables/aitorder.tex` all
match the artefact.

**Two captions had become false, not merely stale** — they said "We did not audit order sensitivity
on this testbed" — and a `t61` check was actively *enforcing* that concession. Both flipped to point
at the measurement.

**Gates:** `t61` 321 (new: per-row read-back, both-arms presence, table registry), `t65` 74 (new:
canonical/first-flow registry rows, two injections caught), `t45` 268.

### R11-2/3/4/5 — blind review  **0 CRITICAL, 1 MAJOR, 2 MINOR; MAJOR and one MINOR fixed**

- **MAJOR — the `deployed` and revision-history sweeps were applied to `satml.tex` but not
  `main.tex`.** `main.tex` still opened Ethics with "attacks against a deployed statistical decision
  layer" — contradicting its own next paragraph — and still said "the pipeline originally shipped".
  Both fixed. Same shape as the R11-6 CRITICAL: `main.tex` shares the appendix and is buildable, so a
  sweep that stops at the submission source leaves a second compilable paper making the claim the
  sweep was for.
- **MINOR — `escape` was not globally horizon-specific.** Two non-horizon uses remained: "it escapes
  \cref{thm:padding} by leaving the class" and "the damage escapes the attacker's own hypothesis".
  Both reworded ("falls outside", "reaches beyond"). All 32 remaining uses in `satml.tex` were then
  audited individually and every one is the finite-horizon sense.
- **MINOR — `tab:main` is `\cref`'d at line 491 before its declaration at 700.** Not acted on. LaTeX
  resolves forward float references normally, and moving the declaration before §III-C would place
  Table III around p.5, far from the §V content it supports and undoing the fix that motivated the
  move. The "declared before every `\cref`" condition was framing in the review prompt, not a
  requirement.

**Verified correct by the review:** `thm:padding` and its proof depend only on symmetric e-merging,
attainment, padding and $\theta>1$ — **not** on Section III — so the rewritten C1/C2 bridge is
sound; "Four constructions alter the boundary, but none removes the tradeoff for free" matches what
the following paragraph reports for all four; the scoped barrier claim correctly excludes SAFFRON,
ADDIS, online e-BH and the deadline family; no targeted revision-history phrase remains anywhere in
`satml.tex`, `appendix_proofs.tex`, the generator or the generated captions, and no mathematical
content was lost with the history (Theorem 1 still says no monotonicity is required; the restart proof
still carries the alternative always-rejecting epoch construction and its pooled-FDR conclusion);
Table III is still a `table*` and now sits coherently between the padding theorem and the next
subsection.

## Close-out

- Body ends **p.12** of 12; 34 pages; **0 overfull**, **0 undefined refs**, 0 duplicate labels; both
  `satml.tex` and `main.tex` build.
- `t61` **321**, `t65` **74**, `t45` **268**, all green.
- Theory: **freezable**. Two audit rounds on the statements plus a third review pass on the prose
  that surrounds them; the residual findings are a forward float reference and nothing else.

**Standing risk for the next round:** three of this round's findings (R11-6 CRITICAL, R11-2/3/4/5
MAJOR, and review 10's table-caption case) were all the same shape — *a change applied to the
submission source but not to `main.tex` or to a generated caption that shares it*. Any future sweep
should be run over `satml.tex`, `main.tex`, `make_appendix_tables.py` and `tables/*.tex` together.

## t61 re-pointed at satml.tex

`main.tex` is abandoned, so the 321-check artefact gate now guards the submission. Re-pointing needed
the two span anchors changed (`\textbf{Contributions.}`/`\section{Background` → the `\emph{C1:}`
block; `Conventions for the results` → `Conventions for the reported numbers`), and `\appendices`
occurs exactly once as a real token, so the truncation trap did not bite.

**Result: 129 mismatches, ZERO value drift.** Every one was main.tex-era *wording* the 12-page
rewrite intentionally changed. Of the 50 "string absent" cases, 16 exist in satml's appendix or a
table and 33 are genuinely gone; the other 79 are bespoke claim-audit checks pinning main.tex
sentences. Several — `AUDIT-A1` for instance — demand abstract text the R10 reviewer explicitly asked
to cut, so **porting them would have re-imposed superseded requirements**.

They are retired in `RETIRED_MAINTEX_WORDING`, reported separately rather than deleted, under one
enforced rule: **only a paper-side wording miss may be retired; a value mismatch still fails.**

**The durable addition is a wording-independent body sweep**, because coverage that quotes exact
sentences decays with every rewrite: every distinctive number in the body (decimals, ≥4 digits, or
`{,}` separators) must resolve to an artefact or generated table — 100 of 103 do, and the three
exemptions are declared (exercise duration, two Zenodo ids) — plus a by-value check of the
scientific-notation quantities.

**Testing it found two bugs in my own check.** The sci-notation comparison sliced to the mantissa, so
`9.9e8` matched any artefact value with mantissa 9.9; and one injection I wrote was a bad test
(`91.7` occurs in an artefact by chance). Both are now correct, and the **limitation is documented in
the file**: these are existence checks. `7.7e8` collides with two unrelated artefact values, so
swapping `6.5e8` for it passes t61 — `t65` catches it, because it ties each headline claim to one
artefact path. Verified in both directions.

**Final:** `t61` **197 + 129 retired**, `t65` **74**, `t45` **268**, body p.12, 0 overfull,
0 undefined refs.
