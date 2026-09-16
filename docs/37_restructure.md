# Reviewer-centred restructure of `paper/satml.tex`

**Input:** `docs/satml_2027_restructure_outline.md`.
**Constraint honoured throughout:** no new experiments, no changed numbers. Every measured value in the
restructured paper is the value the pre-restructure draft carried; the six gates below prove it.
**Backup of the pre-restructure draft:** `paper/satml.tex.backup.tex`.

## What changed

The paper was reorganised around **one causal chain** instead of two co-equal attack surfaces:

> bounded evidence -> finite alert horizon -> grouping restores feasibility -> the grouped hypothesis
> is attacker-controlled -> symmetric padding impossibility -> end-to-end and transfer evidence.

| Old body | New location |
|---|---|
| Abstract (ADDIS + defence catalogue in it) | rewritten to the outline's six-sentence structure; ADDIS and the defence catalogue removed |
| Intro `C1 / Bridge / C2` | three contribution paragraphs; the self-undermining novelty framing replaced by a positive one |
| Assumption 1, Lemma 1, the sigma-field construction | Appendix A-A, with a four-line *Guarantee scope* note left in Sec. II-B |
| Table I (claim dependency) | Appendix F, replaced in the body by the four-sentence Sec. VII-A |
| Theorem 1/2 edge cases (non-monotone counterexample, e-LORD reparameterisation) | Appendix A-B; the two statements stay in the body, presented as two forms of one result |
| Sec. III-D detail (Isolation Forest, prevalence sweep, seed contrast, 0.70/0.77 counts) | Appendix C-A; one contrast (the host detector) stays in the body |
| Sec. III-E escape survey **and Table II** | Appendix C-B; one paragraph stays in the body |
| Padding-cost sweeps (tuned `c=3`, flat pad, first-flow stress exception, pool variants) | Appendix E-B/E-C; the body keeps the exact cost, the oracle caveat and one state-free result |
| Sec. V-F defence prose | Sec. VI-A three-row table + Appendix E-D |
| **Sec. VI, Surface B (ADDIS), Theorem 4** | **Appendix G**, framed as an extension. The body cites it twice (Sec. III-D, Sec. VII-C) and leans on it nowhere |
| Fig. 1 Surface-B arrow | removed; a muted dashed note points at Appendix G |
| Fig. 4 (3 panels, full width) | split: `fig4_padding_body.pdf` (padding only, body) and `figA_addis_state.pdf` (panels B/C, Appendix G) |
| Fig. 3 (five equal windows) | primary emphasised, secondary as the lighter check, other three thin |
| Table III (5 rows, full width) | `tab:main`, four rows, single column |

Title: *Feasibility and **Evasion*** -> *Feasibility and **Padding** Evasion*, the outline's conservative
alternative. With ADDIS demoted, "Evasion" promised two main attacks the body no longer delivers.

Each appendix now opens with a *Question answered* / *Takeaway* pair, as the outline asked.

## Deliberate deviations from the outline

1. **Fig. 2 keeps the horizon-free `T^1.6` curve** (the outline suggested moving it). Review 13
   established that "the requirement is linear in `T`" is true only for the horizon-uniform
   allocation -- under `gamma ~ j^-1.6` it grows as `T^1.6`, a 48,663x gap at LSPR23 flow scale. The
   curve is what makes the abstract's "horizon-free allocations cost more" visible. Removing it would
   re-open a defect a previous round fixed. `t65` gates this in both directions.
2. **Theorems 1 and 2 keep their exact audited statements** rather than being merged into one
   statement. The outline's own escape clause permits this ("if combining would risk mathematical
   imprecision, retain separate theorem statements but introduce them as two cases"), and merging
   would have broken the `t69` freeze on text that two independent audits cleared.
3. **The intro still names the 0.85 stress window** (the outline said not to). One clause, and
   dropping a disclosure to satisfy a structural guideline is the wrong trade.
4. **The conclusion keeps the Assumption 1 conditionality** as one clause. `t61`'s AUDIT-C5 exists
   because a previous round found that abstract + conclusion is how a PC triages, and neither carried
   it. The outline's "do not repeat caveats in the conclusion" does not outrank that.
5. **The full deployment-window overlap disclosure stays in Sec. II-D**, not compressed to one
   sentence. It is the review-12 finding, blind-audited, and `t61`'s R12-1 pins all five clauses.
6. **Appendix tables are not renumbered `A1/A2/C1`.** It would touch all 35 generated table files and
   two gates for a presentational gain; not worth the regression surface at this stage.

## Result

Body ends on **page 10** (was 12.56 pages, over the limit by 0.56). ~2.7 pages of headroom against the
12-page limit. Two sentences were deliberately restored into Sec. V after the cut -- pad-pool
insensitivity and first-flow order sensitivity -- because each answers a live reviewer objection that
would otherwise be answered only in an appendix. The rest of the headroom is left unused: a tight body
is the point of the exercise.

## Gate state (all green, after the restructure)

| Gate | Result |
|---|---|
| `t45_record_consistency` | 268 consistent |
| `t61_paper_consistency` | 202 consistent, 125 retired |
| `t65_satml_claims` | 95 consistent |
| `t68_layout` | 2 consistent (no hyphen-split break, every float at a column top) |
| `t69_theory_freeze` | 26 objects, **0 drift** |
| `t70_src_completeness` | 3 consistent |

`t69` reporting zero drift is the load-bearing check here: **the audited mathematics moved sections
without changing by a single token.** The statements were spliced back verbatim from extracts taken
before the rewrite, not retyped.

## Gate scope changes (and why each is not a weakening)

Content that moved from the body into an appendix is still gated -- what changed is the haystack.
Each of these was a *location* change, never a *content* change.

* `t65` gained `PAPER = flat(S)` (body + appendices). Checks for the claim-dependency table row,
  Theorem 4's bound direction, the ADDIS `B*` numbers, the taxonomy table's conditions, and the
  padding-cost sweeps now read `PAPER`. Checks that are genuinely about body *placement* -- the
  abstract, the conclusion's no-numbers rule, Sec. IV's wording, the first-flow labelling promise --
  deliberately still read `BODY`.
* `t65`'s registry gained a `where="anywhere"` scope, used only for the two 10k-flows/s calendar
  derivations that moved to Appendix C.
* `t61`: the `tab:main` detection-count and `nCal` checks now read `ALL_TEX`, because `tab:main` is a
  four-row summary and the five-window matrix lives in `apptab:ordering`/`apptab:padpools`. The five
  per-window `nCal` values are listed explicitly in Appendix C so the "no elided column" guard keeps
  its teeth. The insertion-cost and service-matched-premium checks lost their `"body"` scope.
* `t61`'s `AUDIT-A1` on the contribution paragraphs is now conditional on those paragraphs actually
  quoting the `kT/c_0` form. They no longer do -- the algebra is stated once, in Sec. III-B, where the
  qualifier is still mandatory.
* `t61`'s `CONTRIB` slice was re-anchored: it used to start at `\emph{C1:`, which no longer exists.

## Two defects found and fixed during the restructure

* `fig:attacks` was **never cited** in the new body after the figure split. Caught by an uncited-float
  sweep, not by a gate. Now cited in Sec. V-D, and the anchor was moved to the head of Sec. V-C so the
  float lands at a column top (`t68` had flagged it mid-column).
* Two single-column tables overflowed the column measure (`tab:main` by 48.7pt, `tab:defenses` by
  17.3pt). Both narrowed rather than `\resizebox`-ed.

---

# Round 2: the reviewer-centred compression pass

Second feedback round on the restructured draft. The audit items (independent proof audit, claim
ledger, clean-environment artifact run) were explicitly deferred by the user and are **not** done.

## The cut-and-move table, as executed

| Location | Moved to | Note |
|---|---|---|
| Abstract | --- | 313 -> 276 words (-12%). The floor is gated: the review-13 scoping clauses and the six numbers' in-sentence qualifiers cannot be cut without failing `t65` |
| II-A procedure catalogue | one sentence + `app:feasibility` | "We use e-LOND as the guarantee-bearing baseline and instantiate the finite-horizon results on LOND, e-LOND, e-LORD and LORD++" |
| II-C keyed-hash pricing | `sec:transfer` pointer | one clause left: "a canonical order is not a security mechanism, and we do not treat it as one" |
| II-D split geometry (46.7--53.3%, nested pools) | **`app:splits`** (new) | body keeps "correlated chronological views of one exercise ... adjacent blocks overlap, and the training pools are nested" |
| II-D "Conventions for the reported numbers" | **`app:conventions`** (new) | it read as documentation on page 3; body keeps one sentence |
| III-A non-monotonicity, counterexample, e-LORD reparameterisation | `app:horizonscope` | body keeps the two theorems and one scope sentence |
| III-B repeated ratio explanation | --- | "reviewer-memorable" deleted; the 20/40 ratio is stated once |
| III-D SAFFRON/smoothing/restart/deadlines/closure/donation | `app:taxonomy` | III-D is now one paragraph |
| V-C the "objection this invites" paragraph | `app:nonoracle` | body states the state-free result directly |
| V-D fifty-order range, first-flow comparison | `app:padwindows` | |
| V-D five pad pools, stress-window replay | `app:pools` | |
| V-E AIT first-flow arm, 212--8,294 range, the `shaw` case | **`app:ait`** (new) | |
| VI-A prose under the defence table | table only | prose is now a two-sentence synthesis; section retitled *Representative padding defences shift the tradeoff* |
| V-E scope caveat | `sec:limitations` | stated once, where the other caveats are |

## Figures, redesigned

* **Fig. 2** --- the `[oracle]` marker is gone. It labelled `gamma_t = 1/T`, which knows only the
  horizon, with the same word the paper uses for an attack cost that knows the realised evidence and
  the live level. The macro now renders `[horizon-aware]`, which relabels the four generated tables
  that use it without regenerating anything. **Online e-BH was removed from the figure**: the
  absorbing-horizon predicate is not defined for it, and the old legend called it an escape that is
  "still linear in $T$" --- a live contradiction with the review-12 fix, sitting inside a figure.
* **Fig. 3** --- the top panel now plots the controller-aligned feasibility ratio
  `rho_p = M*c_{0,p}/T`, threshold at 1, instead of the level-`w_0` margin, on which e-LOND
  (`c_0 = 2 w_0`) stays feasible down to `-1/2`. That is what forced every caption to explain why a
  negative-margin row could still detect. `rho` is computed from the same stored `NC` and `T` the
  margin comes from; **nothing was re-measured**. The level-`w_0` margin is now defined in
  `app:feasibility` (`eq:margin`), which is what the appendix tables are built on, with the exact
  conversion `rho_eLOND = 2(margin+1)` stated there. The three context windows became one shaded
  range rather than three more equal series.
* **Fig. 4** --- redesigned. It used to foreground the secondary window, the **known-invalid** 0.85
  stress window and the first-flow arm; a reviewer skimming it would have associated the paper's
  principal attack evidence with the window the paper itself says carries no valid e-value. Panel A
  is now the three primary-window costs (23/24/33, the alerts replay actually suppresses) plus the
  secondary distribution; panel B is the AIT transfer, median cost per organisation, annotated
  78/79. The stress and first-flow arms moved to `figE_padding_sensitivity` in `app:pools`.
* **Table II** --- one representative per escape route, columns *Defence / Robustness gained / Cost
  paid*; the duplicate prose beneath it is gone.

## Language

* Deleted: "reviewer-memorable", "The objection this invites".
* One terminology ladder, defined in one place: **evidence-feasible step** -> **discovery horizon**
  `t*` -> **absorbed** -> **structural silence**, plus **cold-start feasible through `T`**. The
  section title changed from "Finite Alert Horizon" to "Finite Discovery Horizon" to remove the last
  synonym. Attack costs use only **exact attack cost `r*`** and **state-free over-provisioning**.

## Two claim-alignment fixes

* **Replay** was run at the primary window, not the secondary. The abstract now says controlled
  replay "suppresses all three primary-window alerts at the predicted 23--33-flow thresholds", and
  the secondary median of six is stated as an analytic cost. `tab:main`'s secondary replay cell
  reads **"not run"**, not a dash, with the caption saying that means the experiment was not
  performed rather than that it failed.
* **The fixed multiplier is an LSPR23 result.** On AIT the attacked episode contains benign flows the
  attacker cannot count, so it knows only a lower bound on `m`. Both the abstract and Sec. V-C now
  scope the claim to LSPR23 and to the evaluated state-free arms.

## Result

Body ends on **page 9** (from page 10, and 12.56 before the restructure). Roughly 3.5 pages of
headroom against the 12-page limit.

The four objections the mock-review table anticipates are all answerable from the body without
following an appendix reference: the novelty framing and "attained rather than merely bounded" in
Sec. VIII, the state-free result in Sec. V-C where the oracle objection arises, the 3/11/79 detection
counts in `tab:main` and Fig. 4B, and the claim-dependency paragraph in Sec. VII-A.

## Gates: 6 green, and six new checks

`t45` 268, `t61` 201, `t65` **104**, `t68` 2, `t69` **0 drift**, `t70` 3.

New `R14` group in `t65`, all six injection-tested:

1. the body's `rho` range is **recomputed** from the artefact's `NC` and `T`, not string-matched;
2. `eq:rho` must be in the body and `eq:margin` in the appendix, with `rho`'s threshold at 1;
3. the abstract scopes controlled replay to the primary window;
4. `tab:main`'s secondary **row** says "not run";
5. the state-free multiplier claim names LSPR23 and the evaluated arms (abstract and body);
6. "oracle" names one thing --- `[oracle]` may not reappear as a spending-sequence marker, and every
   body occurrence must be an oracle lower bound or an oracle-informed floor.

**One gate hole found by injection.** Check 4 was first written as "is `not run` present in the
body?" --- which passes on a reverted table, because the caption that *explains* the phrase also
contains it. Scoped to the `tab:main` row. This is the same existence-check failure mode as the
review-12 rename; a phrase that appears in its own explanation cannot be guarded by presence.

## Gate scope changes this round

* `t61`: the `CONV` slice re-anchored from `\emph{Conventions for the reported numbers.}` to
  `\subsection{Reporting conventions}`; the 50-order median (`$16$`/`$178$`) and the 96.3%
  at-arrival figure lost their `"body"` scope.
* `t65`: the conventions block, the survivorship qualifier, the 1.57/15.7x/5.1x factors, the padded
  arity, and the "state-free" vocabulary check now read `PAPER`; the Fig. 2 e-BH check became
  conditional on e-BH being plotted at all (it no longer is); Sec. III-D's two-mechanism check
  accepts the compressed phrasing.
* Two paper-side fixes were made *to keep* gates honest rather than by rescoping them: the
  `t61` absence gate on "replication" licenses the exact phrase *"rather than confirmatory
  replication"*, so both the body and `app:splits` use it verbatim; and `app:splits` opens with
  "The five deployment positions are overlapping chronological views of one exercise" so the
  review-12 disclosure gate still has its anchor.
