# Reviewer-feedback worklist — round 2

Actionable items derived from `SaTML_2027_review_feedback.md` (a full review of the current
post-revision draft). Same format as `21_reviewer_feedback_worklist.md`: each item states the
reviewer's point, its **type** (wording / reframe / recompute / audit / **new experiment**), what I
**verified** in the current draft and artifacts, concrete steps, data availability, acceptance
criteria, and effort. File anchors are into `paper/main.tex` unless noted. Review section numbers
are given in parentheses so each item maps back to the review.

**Headline from the review:** the draft is credited as a "credible SaTML main-track submission"
(~40% as-is, ~45–55% after Tier-1, ~55–65% with a host-conditioned experiment + related-work
positioning). The reviewer's advice is explicit: **do not invent another theorem — remove the
reasons a reviewer can distrust the existing contributions.** This worklist is ordered to that end.

**Governance reminder** (`docs/03_FROZEN_CLAIMS.md`): a claim may be *weakened* freely, but any item
that produces a *new headline number* (R3's confidence intervals, R7's new detector) must land a
numeric artifact + a `t45`-style consistency check + an audit pass + a frozen-claims note before it
enters the paper. Wording/reframe/framing items do not.

**PAGE-BUDGET reminder (hard constraint).** The body is currently at **exactly 12 pages**
(Conclusion ends at the bottom of p.12; the CFP calls over-length "grounds for desk rejection").
Several Tier-1/Tier-3 items **add** text (R1 assumption paragraph, R3 CIs, R4 related-work
paragraph, R10 terminology box, R11 definitions). **Every addition must be offset by a compensating
trim, and the 12-page check re-run after each.** Where an item's natural home would overflow the
body, push detail to an appendix (which does not count). This tension is called out per item.

## Summary

| # | Item | Review § | Type | Effort | New data? |
|---|------|----------|------|--------|-----------|
| **R1** | State the group-level e-value **validity assumption** explicitly | 4.2, 13-theory | framing + theory | M | no |
| **R2** | Reconcile the grouping table's **infeasible-but-non-zero** rows | 4.4 | recompute-flag + wording | S–M | recompute (data exists) |
| **R3** | Replace "valid window" language; add **firing-count CIs** | 4.3, 8 | wording + recompute | M | recompute (data exists) |
| **R4** | **Related-work** positioning vs online conformal-FDR work | 4.1 | wording + citations | M | no (needs author refs) |
| **R5** | **Attack-cost audit** + explicit lower-bound labels | 4.5 | audit + wording | M | no |
| **R6** | **Narrow** the ADDIS generalization + drop the silence-monotonicity claim | 4.6, 7.4 | wording | S | no |
| **R7** | **Host-conditioned second detector** / padding-transfer boundary | 5.1, 15 | **new experiment** | L | new |
| **R8** | **Compress** secondary baselines to the appendix | 8 | restructure | M | no |
| **R9** | **Simplify the abstract** to 2–3 headline numbers | 9 | wording | S | no |
| **R10** | Add a **terminology / assumptions box** | 10 | wording | S (page cost) | no |
| **R11** | Precise **horizon-feasibility definitions** + crisp Theorem 6 model class | 7.1, 7.3 | wording | S | no |
| **R12** | **Figure scanability** polish | 13 | polish | S | no |
| **R13** | **Citation audit** + LLM-checklist line-by-line | 11, 12 | audit (author-led) | M | no |

**Suggested execution order.** **R2, R6 first** (cheap credibility fixes, no re-audit, one is a
verified inconsistency the reviewer already spotted). Then **R1, R3** (the two top technical-trust
items; R3 adds numbers → audit). Then **R5** (cost audit) and **R4** (related work; needs author
citations). Then **R9, R8, R10, R11, R12** (framing/space). Then the single big experiment **R7**.
**R13** is a final-pass author task. Do the additive items (R1/R3/R4/R10/R11) with a trim in hand.

> **STATUS — cheap-fix pass done 31 Aug 2026 (page limit intentionally ignored for now).**
> **Done and verified** (compile clean, `t45` 107/107, notebook 24/24 cells, all refs resolved):
> **R1** (Assumption 1 group-validity, §2.2), **R2** (grouping-table caption reconciled),
> **R3** (valid-window language + exact Poisson CIs — new `t50_calib_ci.py`/artifact/`apptab:tail`
> column/`t45`/record §4.46), **R4** (related-work novelty reframed — *carries a visible `[Author: …]`
> flag for the exact recent citation*), **R5** (lower-bound labels present at every cost number),
> **R6** (ADDIS generalization narrowed + silence-monotonicity dropped), **R9** (abstract trimmed to
> 3 numbers), **R10** (terminology box `tab:terms`), **R11** (feasibility definitions + Theorem 6
> model class). **Deferred:** **R7** (host-conditioned detector — big experiment), **R8** (trim to
> 12 pages — do last), **R12** (figure-caption polish — minor), **R13** (citation audit + LLM
> checklist — author-led). **The body is now over 12 pages by design; R8 is the reconciliation step
> once content is settled.**

**Already addressed by round 1** (the review credits these — do **not** redo): FDR-as-queue framing,
exchangeability stated, primary-vs-stress-window split (W2), the fixed-denominator "alert blur" (W7),
"known vs. established here" (W4), theorem-family narrowing (W1), Prop 1 wording (W5), Route-B
special-case framing (W5), Surface A/B separation (W6), the controlled padding-dilution experiment
(W3), Isolation-Forest honesty (W9-wording), state-attack as structural controllability (W6). The
LLM editorial-use statement and back-matter ordering are also in place (pending R13's checklist
check).

---

## R1 — State the group-level e-value validity assumption explicitly (do early)

**Reviewer point (4.2, flagged a *top-priority technical audit item*).** The paper moves quickly
from "the arithmetic mean of valid e-values is an e-value" (algebra) to a valid group-level e-value,
without stating that the *conditional* validity required by the online procedures is preserved under
the deployment filtration, the grouping, temporal structure, and any dependence between group
formation and evidence. If a reviewer believes the group e-values don't satisfy the required form of
validity, it threatens a large part of the paper, not one experiment.

**Verified.** No such assumption paragraph exists (`grep` for "grouping rule is fixed / filtration /
conditional e-value / group-evidence validity" in `main.tex` returns nothing). §2.2 states the mean
is valid "at every arity" and moves on; the closest hedge is the calibration premise in §2.1.

**Steps.**
1. Add a **Group-evidence validity assumption** paragraph to §2.2 (Security-semantic grouping),
   stating: the grouping key $(\mathrm{SrcIP},\mathrm{DstIP},\text{bucket})$ is **pre-committed** and
   is a function of metadata available independently of the detector scores; under the null each
   per-flow e-value satisfies the required conditional e-value property w.r.t. the pre-group
   filtration; therefore the pre-specified mean is a valid group e-value under arbitrary within-group
   dependence; **if this conditional validity fails the downstream FDR guarantee does not attach**,
   and \cref{sec:tail}'s diagnostics test exactly this premise.
2. Cross-reference this assumption from §4 (feasibility) and §6 (attack) so every guarantee-bearing
   claim points back to it.
3. Make the statement match the exact theorem invoked (Vovk–Wang e-merging / the online-procedure
   validity conditions). **Flag for an author/expert with e-value & sequential-testing background to
   verify the precise conditional-validity wording** — do not ship an over-strong version.

**Data/feasibility.** None; pure statement. **Page cost ~5–7 lines in §2.2 → offset elsewhere.**

**Acceptance.** A named assumption in the main text that a sequential-testing reviewer would accept;
every FDR claim references it; the failure mode ("guarantee does not attach") is explicit.

**Effort:** ~half a day incl. expert check. **Re-audit:** none (assumption, not a number).

---

## R2 — Reconcile the grouping table's infeasible-but-non-zero rows (do first)

**Reviewer point (4.4).** Rows marked infeasible (negative margin) are described in the caption as
ones "where the controller cannot run and recall/coverage are therefore 0," yet some infeasible rows
report non-zero recall/coverage. "Exactly the type of small-looking inconsistency that can cause a
reviewer to distrust many tables."

**Verified — this is a real inconsistency, not a misreading.** In `paper/tables/grouping.tex`:
`subnet24 & 300\,s & $-0.451^{\dagger}$ & 0.448 & 0.697` — infeasible dagger, but recall $0.448$ and
coverage $0.697$; meanwhile `src-dst & 300\,s & $-0.637^{\dagger}$ & 0.000 & 0.000`. So some
daggered rows are zero and others are not. **Root cause (already understood from W7):** the margin
column is the **level-$w_0$ (LORD++) cold-start** margin, but `elond_recall`/`flow_cov_elond` are
**e-LOND under the uniform (oracle) $\gamma$**, whose cold-start coefficient is $\alpha=2w_0$, so
e-LOND fires in a band where the level-$w_0$ margin is mildly negative. The margin and the metric are
computed under different conditions, so the caption's "therefore 0" is false.

**Steps (pick 2b; it is the honest, minimal fix).**
1. **(2a, not recommended)** Recompute a per-procedure feasibility flag (e-LOND's $\alpha=2w_0$
   condition) so the dagger matches whether e-LOND can fire; then no daggered row shows non-zero
   metrics. This changes which rows are daggered.
2. **(2b, recommended)** Keep the level-$w_0$ margin but **fix the caption/labels**: rename the
   dagger to "negative **level-$w_0$** margin; e-LOND can still fire because its cold-start
   coefficient is $\alpha=2w_0$ (\cref{eq:margin} discussion)," and drop "recall/coverage are
   therefore 0." Add a note that the metric columns are e-LOND under \oracle\ $\gamma$. This makes
   every row unambiguous and matches the per-procedure caveat the body already states at
   \cref{eq:margin}.
3. Sweep every other table that pairs a margin/feasibility flag with a metric (`apptab:detection`,
   `tab:main`, `apptab:procmatrix`) and confirm the feasibility label and the metric's procedure/γ
   are stated in one place. `tab:main`'s caption already says "position 0.70 … detections 30→0 at the
   same margin," so the feasibility-≠-detection point is made — extend that clarity to `apptab:grouping`.

**Data/feasibility.** No rerun for 2b (caption/label edit in `make_appendix_tables.py::t_grouping`);
2a is a flag recompute from `t26_H4_5pos`. **No page cost (appendix).**

**Acceptance.** Every row of `apptab:grouping` (and the other margin+metric tables) has one
unambiguous reading; no caption claims a value the cell contradicts; the level-$w_0$-vs-e-LOND
distinction is explicit.

**Effort:** ~1–2h. **Re-audit:** none for 2b (wording); 2a would re-touch `t26` labels only.

---

## R3 — Replace "valid window" language; add firing-count confidence intervals

**Reviewer point (4.3, 8).** Calling 0.55/0.62 "valid conformal evidence" from benign firing ratios
~1.07–3.79× overstates the empirical evidence: the expected firing count is tiny (one/two/three
events), so a ratio near one is not statistical proof that exchangeability holds. Separate **the
theoretical guarantee (holds under the assumption)** from **the empirical diagnostic (limited
resolution)**, and report exact binomial/Poisson intervals.

**Verified.** `main.tex:772` — "Four of the five positions carry valid conformal evidence (benign
firing $1.07$--$3.79\times$ nominal)…"; §Robustness (`sec:tail`) reports the ratios but no interval
on the small firing counts.

**Steps.**
1. **Rewrite the register.** Replace "carry valid conformal evidence" with assumption-aware wording,
   e.g.: *"At four positions the benign firing counts are compatible with the nominal rate at the
   resolution this dataset allows; 0.85 shows a clear violation. We treat 0.55/0.62 as the
   guarantee-analysis windows **under the stated exchangeability assumption (R1)**, and 0.85 as a
   stress-test."* Apply the same softening wherever "valid window" appears (methodology, `tab:main`
   caption, §Robustness).
2. **Add uncertainty.** For each position compute an exact **Poisson** (or binomial) interval on the
   number of firing benign flows vs the nominal expectation, from the counts already in
   `t30_A1.json` (`n_fired_benign`, nominal rate). Report the interval in `apptab:tail` and cite it
   where the ratios appear. This is new computation on existing data — a new number → `t45` + audit.
3. State once that the guarantee is assumption-conditional and the diagnostic only *rejects* gross
   violation (0.85), it does not *prove* validity at the others.

**Data/feasibility.** `t30_A1.json` already carries the firing counts and nominal rates; the CIs are
a closed-form add-on (extend `t30` or a tiny post-processor). **New artifact/number → audit.** Body
page cost is small (a clause + an appendix column).

**Acceptance.** No sentence asserts empirical "validity" from sparse counts; each guarantee window
carries an interval; theory-vs-diagnostic separation is explicit and tied to R1.

**Effort:** ~half a day. **Re-audit:** yes (the CIs are new numbers).

---

## R4 — Related-work positioning vs recent online conformal-FDR work

**Reviewer point (4.1, a Tier-1 item).** "Prior work targets the detector or calibration; we target
the decision layer" is too broad; there is close recent work combining conformal evidence, sequential
anomaly decisions, and FDR-style control. A reviewer who knows this literature may react badly.
Replace the "first to target the decision layer" framing with a narrower, harder-to-attack delta.

**Verified.** §Related Work (`sec:related`) has the "Trustworthy ML intrusion detection" paragraph
citing TESSERACT/Transcend/Transcendent/`caliburn2026`/`rebjock2021online`/`wang2025multilayer` and
says "all target the detector or calibration, whereas our target is the decision layer after both."
That is the exact sentence the review flags.

**Steps.**
1. Add a short paragraph with three explicit categories: (i) online FDR for anomaly detection;
   (ii) **streaming/online conformal anomaly detection with FDR-style control** — name the closest
   recent predecessor(s); (iii) **this paper's difference**: finite calibration resolution × long
   online horizon; semantic aggregation into alerting units; adversarial control of group
   composition; adversarial control of adaptive sequential state; security-specific feasibility and
   attack-cost analysis.
2. Adopt the review's recommended novelty wording (narrower "we study a different failure mode of the
   composed pipeline …" instead of "first to target the decision layer").
3. **Author input required:** supply/confirm the *specific* 2025/2026 conformal-FDR predecessor
   citations. I can draft the paragraph and the contrast, but the exact closest-neighbour papers must
   come from the authors (my training cutoff cannot guarantee the current closest work). Add them to
   `refs.bib` and verify (feeds R13).

**Data/feasibility.** None; wording + citations. **Page cost:** modest; the existing broad sentence
can be replaced in place so net-neutral is achievable.

**Acceptance.** Related Work names the closest online conformal-FDR work and states a narrow,
defensible delta; no "first to …" claim remains.

**Effort:** ~half a day once the citations are supplied. **Re-audit:** none.

---

## R5 — Attack-cost consistency audit + explicit lower-bound labels

**Reviewer point (4.5).** Many cost numbers across abstract/body/figures/tables mix thresholds
(running $1/\alphat$ vs static $T/w_0$ vs ADDIS's capped level) and bound types. Build one internal
sheet and verify every number against it; and **wherever a number is a lower bound, say why next to
it**, so a reviewer doesn't read it as a full adaptive end-to-end simulation.

**Verified.** The distinctions exist and are largely correct (`t45` already checks the load-bearing
numbers), but lower-bound labelling is uneven: `sec:paddingcost` and the Limitations state it, while
individual in-line numbers (e.g. the abstract's "median ≈100 flows", `tab:main`'s "median pad") do
not each carry the "why" clause.

**Steps.**
1. Build a reconciliation sheet (script or table) with columns: attack, procedure, window, level used
   ($1/\alphat$ running vs static $T/w_0$ vs ADDIS $\lambda$), bound type (lower/exact), group size,
   pad-pool mean $\mu$, flows, bytes, span, rate. Populate from `t28b`, `t32_B1`, `t41_E8`, `t43`.
2. Verify every cost number in the abstract, §6, figures, and tables against the sheet (extend `t45`
   with a few cross-artifact equalities where practical).
3. Add a short "why lower bound" clause at each lower-bound number, e.g. *"118 flows — a lower bound:
   levels are read from the unperturbed run, so earlier suppressions that would lower later levels are
   not charged."* Keep it once per context, not per occurrence, to protect the page budget.

**Data/feasibility.** All numbers already exist; this is an audit + labelling pass. **No new data.**

**Acceptance.** Every cost number traces to one sheet with a stated threshold and bound type; each
lower bound carries its reason at least once per section it appears in.

**Effort:** ~half a day. **Re-audit:** none (no new numbers; optional `t45` cross-checks).

---

## R6 — Narrow the ADDIS generalization; drop the silence-monotonicity claim

**Reviewer point (4.6, 7.4).** Two over-broad statements. (a) "*any* procedure escaping α-death by
conditioning its spending index on observed evidence exposes that property" reads as a universal
theorem it is not. (b) The claim that anti-conservative 0.85 evidence makes *every* silence/
non-detection result conservative asserts a monotonicity (pointwise dominance of the sequential path)
that is not proved for the grouped evidence.

**Verified.** (a) appears in `sec:coincide` ("any procedure that escapes $\alpha$-death by
conditioning its spending index on a property of the observed evidence exposes that property…").
(b) appears in `sec:tail` ("anti-conservative evidence can only make a procedure fire *more*, so
silence and non-detection at 0.85 are lower bounds").

**Steps.**
1. **(a)** Reword to the review's "security principle" framing: *"The ADDIS example illustrates a
   broader principle: when the state variable controlling future decisions is a deterministic
   function of attacker-influenced evidence, that state variable must be in the threat model,"* rather
   than a claim for every adaptive procedure.
2. **(b)** Drop the general monotonicity. Keep only: *"The severe anti-conservatism at 0.85 means the
   FDR guarantee does not attach; we use 0.85 only as a stress-test for mechanism and attack-cost
   measurement, not for guarantee-bearing conclusions."* If the "conservative for detection"
   statement is wanted, it must be proved under the exact perturbation model — otherwise cut it.

**Data/feasibility.** None; wording (weakening — governance-free). **Page cost:** neutral/negative.

**Acceptance.** No universal-adaptive-procedure claim; no unproved monotonicity; 0.85 framed purely
as a stress-test.

**Effort:** ~1h. **Re-audit:** none (weakening).

---

## R7 — Host-conditioned second detector / padding-transfer boundary (the one big experiment)

**Reviewer point (5.1, and §15: "the single additional experiment I would choose").** The largest
remaining empirical weakness is single-dataset scope + one detector that actually detects. A
**competent host-conditioned detector**, with the padding experiment repeated against it, directly
targets the paper's own scope boundary and would move acceptance the most. This is the W9-experiment
half deferred from round 1 (round 1 delivered the flow-level confirmation, R/W3, and scoped this
boundary explicitly).

**Steps.**
1. Derive host-conditioned features from the metadata cache (`/tmp/lspr_meta_cache`:
   `srcip/dstip/service/segment/label_src/label_dst`) — per-host rate/reputation/baseline features —
   via a new `src/lib/h_meta`-backed feature builder.
2. Train a **competent** supervised detector on flow features + host features (reuse `h_stream`
   plumbing; it must actually detect, unlike Isolation Forest).
3. Re-run the padding-placement transfer (mirror `t48_W3`): do ordinary victim-service pad flows still
   score benign under host features? Does the group evidence still dilute? Report the boundary
   honestly — **transfer holds / gets $X\times$ more expensive / fails under condition Y** — and which
   feature breaks it.
4. Fold the result into the Limitations/threat-model scope (it currently says this "needs a testbed";
   R7 supplies the measurement) and, if it degrades/fails, present it as the honest scope result the
   review wants.

**Data/feasibility.** Metadata is available (`src/lib/h_meta.py`, `/tmp/lspr_meta_cache`), so
host-conditioned features are constructible with no new capture. New modeling + artifact + audit +
frozen-claims. **Outcome-uncertain by design** (that is the point). New script `src/lib/t49_*`,
registered in `runner.py`, wired into `build_notebook.py` + `make_appendix_tables.py`, `t45` checks.

**Acceptance.** A competent detector that produces detections at a valid window; the padding-transfer
claim carries an explicit **measured** boundary under host-conditioned features (holds/degrades/fails
with the responsible feature named).

**Effort:** ~3–5 days. **New artifact + audit + frozen-claims** required.

---

## R8 — Compress secondary baselines to the appendix

**Reviewer point (8).** The paper does feasibility theory + granularity + merging impossibility +
padding + asymmetric weights + controller-state + contamination + matched thresholds + feedback +
smoothing + restart + data-quality auditing — "a lot." Keep in the body: matched operating point at
the primary window + one concise feedback result. Move/compress: full feedback comparison, the q/γ
sweep, secondary negative results.

**Verified.** Round 1 (W8) already compressed the feedback subsection to a pointer at
`apptab:feedback`, moved the frontier stress-window table to the appendix, and shortened the negative
results. The q/γ lever is one paragraph in §Operational. So this is mostly *done*; the remaining
lever is to demote any lingering secondary detail if page pressure from R1/R3/R4 needs it.

**Steps.**
1. Use R8 as the **offset budget** for the additive Tier-1 items: if R1/R3/R4 push over 12 pages,
   move the q/γ lever detail and any remaining feedback specifics fully into `app:baselines`, leaving
   a one-line body pointer.
2. Keep the matched-operating-point (primary window) and the one-line feedback headline in the body —
   they translate statistics into operator cost, which the review calls the reason to keep them.

**Data/feasibility.** None; restructure. **This is the primary page-budget release valve.**

**Acceptance.** Body retains the primary matched-operating-point + one feedback headline; secondary
sweeps live in the appendix; body ≤ 12 pages after the Tier-1 additions.

**Effort:** ~2–3h (mostly bookkeeping against the page budget). **Re-audit:** none.

---

## R9 — Simplify the abstract to 2–3 headline numbers

**Reviewer point (9).** The abstract is still dense. Cut 20–25% of the numeric detail; keep a clean
problem → feasibility → systems consequence → security consequence → evidence → takeaway structure
with only 2–3 headline numbers.

**Verified.** Round 1 (W8) already recast the abstract to the three-beat spine and removed the
enumerations. It still carries ~4 numbers ($6.5\times10^{8}$, ≈100 flows, $37.5\times$, 16.4M).

**Steps.** Trim to the two or three that carry the argument (keep $6.5\times10^{8}$ for the
feasibility scale and the ≈100-flow valid-window padding cost; consider dropping the $37.5\times$ and
the 16.4M from the abstract, deferring them to the body). Preserve the spine and C2-as-bridge.

**Data/feasibility.** None; wording. **Page-neutral/negative.**

**Acceptance.** Abstract carries ≤3 headline numbers and the six-beat narrative; no enumerations.

**Effort:** ~1h. **Re-audit:** none.

---

## R10 — Terminology / assumptions box

**Reviewer point (10).** The paper moves between validity / guarantee / feasibility / power /
detection / resolution / coverage without reminding the reader they differ. A small terminology
table would help interdisciplinary SaTML reviewers. (Review supplies a candidate 8-row table.)

**Verified.** No terminology box exists; the terms are used precisely but densely.

**Steps.** Add a compact table (validity, feasibility, detection power, episode recall, atomic
coverage, alert blur, padding cost, state-attack cost) near the end of §2 or as a boxed float.
**Page cost is real** — a table is ~8–10 lines; only add it if R8 has released the room, otherwise
place it in an appendix and point to it once from §2.

**Data/feasibility.** None; wording. **Page cost: yes — gate on R8.**

**Acceptance.** A one-glance terminology reference exists and is cited once from the system model.

**Effort:** ~1h. **Re-audit:** none.

---

## R11 — Precise horizon-feasibility definitions + crisp Theorem 6 model class

**Reviewer point (7.1, 7.3).** Several related notions (step-feasible, finite last feasible time,
absorbing silence, cold-start feasibility, reject-at-every-$t\le T$, deployment-wide feasibility) are
used without explicit definitions; add short ones so Corollary 3 is easy to read. Separately, make
Theorem 6 (symmetric padding impossibility) impossible to misread: spell out that "padding" = attacker
flows with e-value 0 under the two-point construction, and distinguish valid-at-arbitrary-arity
e-merging families, the capped rule (valid only under a pre-committed max group size), and asymmetric
position-weighted rules.

**Verified.** The concepts are used across §4 but not collected as definitions; Theorem 6's model
class is stated in the theorem + proof but the "padding = zero-evidence appended flow" identity is
implicit.

**Steps.**
1. Add three one-line definitions (step-feasible; cold-start-feasible through $T$; absorbing silence)
   at the top of §4, matching the review's phrasing.
2. In §6.2 add one sentence tying "padding" to appended zero-evidence flows and one sentence
   distinguishing the three rule classes.

**Data/feasibility.** None; wording. **Page cost: small — gate on R8.**

**Acceptance.** A reader can point at the exact definition behind each feasibility phrase; Theorem 6's
model class and the meaning of "padding" are unambiguous.

**Effort:** ~2h. **Re-audit:** none.

---

## R12 — Figure scanability polish

**Reviewer point (13).** Each main figure should answer one question at a glance.

**Verified.** `fig3` was reworked in round 1 (blur middle panel); `fig1`/`fig2`/`fig4` are unchanged.

**Steps.** One pass over `make_figures.py`: ensure each figure has a one-line takeaway annotation
(fig3 now does), consistent axis labels, and a caption whose first sentence states the single
question answered. No structural change.

**Data/feasibility.** None; figure polish. **No page cost.**

**Acceptance.** Each main figure's first caption sentence is a single question/answer; annotations
are consistent.

**Effort:** ~2–3h. **Re-audit:** none.

---

## R13 — Citation audit + LLM-checklist compliance (final author-led pass)

**Reviewer point (11, 12).** Because LLM assistance is disclosed, reviewers may scrutinise the
bibliography closely; manually verify every reference (title/authors/venue/year/volume/pages/arXiv id,
and every theorem/proposition number cited), especially the e-merging domination result, the e-GAI
equivalence used in Prop 1, calibration-conditional results, and any 2025/2026 arXiv work. And compare
the LLM-usage section line-by-line with the **current SaTML 2027 mandatory checklist** — exact
editorial-use sentence, which model, why necessary, prompt-sensitivity, query minimisation, citation
verification confirmation — following the CFP exactly, not an improvised version.

**Verified.** The editorial-use statement and back-matter ordering (Open Science → LLM → Ethical →
References) are in place from the interim fix; the *exact* SaTML 2027 checklist wording is **not in
the repo** and could not be confirmed, so this remains open pending the CFP text.

**Steps.**
1. **Author task (or I can help mechanically):** verify every `refs.bib` entry and every in-text
   theorem/proposition attribution against the primary sources.
2. **Author task:** paste the current SaTML 2027 LLM checklist; then reconcile the section
   line-by-line and drop in the exact required sentence(s) verbatim (I flagged the standard editorial
   sentence is a placeholder for the official one). Add: which model, why necessary, prompt-sensitivity
   statement, query-minimisation, and a "citations manually verified" line if requested.

**Data/feasibility.** None; verification. Requires the CFP checklist text and primary-source access.

**Acceptance.** Every reference and cited result checked against source; LLM section matches the CFP
checklist verbatim where wording is mandated.

**Effort:** ~half a day (author-led). **Re-audit:** none.

---

## Cross-cutting notes for the executing agent

- **Page budget is the binding constraint.** The body is at exactly 12 pages. Do the additive items
  (R1, R3, R4, R10, R11) **only with a matching trim in hand**, and re-run the 12-page check
  (`Conclusion ends on p.12`, `Open Science on p.13`) after each. **R8 is the release valve** — bank
  its appendix moves before spending on R1/R3/R4/R10/R11.
- **Reproducibility:** any new artifact (R3 CIs, R7 detector) goes in `src/lib/out/`, its generator as
  an importable `src/lib/*.py` with `main()`, registered in `src/runner.py`, wired into
  `src/tools/build_notebook.py` + `paper/make_appendix_tables.py`, and consistency-checked in
  `proto/t45_record_consistency.py` (copy the artifact + script into `proto/` as done for `t47`/`t48`).
  Keep `src/` self-contained (no `proto/` references).
- **Consistency gates after any edit:** rerun `proto/t45_record_consistency.py` (currently 100 checks,
  0 inconsistent); rebuild + smoke-test `src/paper.ipynb` in paper mode; regenerate tables/figures
  (`make_appendix_tables.py`, `make_figures.py`); `tectonic -X compile`; confirm body ≤ 12 pages.
- **Frozen claims:** update `docs/03_FROZEN_CLAIMS.md` with an audit note for R3 and R7 (new numbers);
  R1/R2/R4/R5/R6/R8/R9/R10/R11/R12/R13 are wording/reframe/audit and need no new audit.
- **Items needing input I cannot supply:** R4 (the exact closest recent conformal-FDR citations),
  R1 (expert sign-off on the conditional-validity wording), R13 (the official SaTML 2027 LLM checklist
  text + primary-source citation checks). Flag these to the authors rather than guessing.
- **Priority for acceptance (per the review):** R1 (group-validity), R2 (table consistency), R3
  (valid-window language + CIs), R4 (related work), R5 (cost audit) are the Tier-1 trust fixes; R7 is
  the single highest-value new experiment. The review is explicit that **removing reasons to distrust
  the existing results beats adding another theorem.**
