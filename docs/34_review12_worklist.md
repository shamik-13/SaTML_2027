# Review 12 worklist — window naming, FDR/FDP hygiene, escape taxonomy, presentation

Source: reviewer feedback on `paper/satml.tex` (2026-09-03), after review 11's theory freeze.
Ten points. Each was **investigated against the source, the artefacts and the compiled PDF before
being entered here**; the verdict column records what the investigation found, not the reviewer's
framing. Every item is to be blind-reviewed by a codex agent before being marked done
(see `blind-codex-review-workflow`).

## Verdicts at a glance

| # | Item | Investigated verdict | Status |
|---|---|---|---|
| R12-1 | Stop calling 0.62 a "replication window" | **VALID — and understated.** Arithmetic confirmed exactly; found a stronger overlap the reviewer missed | **applied, audit pending** |
| R12-2 | Float placements still interrupt sentences | **Substance valid, all four examples STALE.** None of the four cited breaks exists; two *different*, worse ones do | **applied (durable part); cosmetic pass after refit** |
| R12-3 | "Measured FDR of e-LOND" in Table I is an FDP | **VALID** | **applied, audit pending** |
| R12-4 | online e-BH is not an "escape" in the same sense | **VALID — self-contradictory inside one appendix sentence** | **applied, audit pending** |
| R12-5 | Tighten the non-oracle padding claim | **VALID** | **applied, audit pending** |
| R12-6 | Grammar fix in §V-E + copy-edit pass | **VALID** | **applied, audit pending** |
| R12-7 | Abstract: "the full chain" → name the configuration | **VALID (wording only; no rerun)** | **applied, audit pending** |
| R12-8 | Do the independent proof audit, then freeze | **ALREADY DONE in R11** — no action beyond honouring the freeze | done (R11) |
| R12-9 | Claim ledger against the artefacts | **6 of 8 already pinned; 2 real gaps** | **applied, audit pending** |
| R12-10 | Reduce clutter — Table II caption | **VALID — 175 words vs 47–123 for every other body caption** | **applied, audit pending** |
| R12-11 | *(added by investigation)* Body is over the 12-page limit | **NEW — body ends on p.13** | todo |

---

## R12-1 — the 0.62 window is not a replication

**Verdict: valid, and the reviewer understated it.**

Confirmed from `src/lib/h_stream.py:88` (`split_indices(N, pos, cal_f=0.15, test_f=0.15)`) and the
appendix definition at `satml.tex:1332`: `i2=floor(pos*N)`, `i1=i2-floor(0.15N)`,
`i3=min(N,i2+floor(0.15N))`, deployment `[i2,i3)`. Computed on the real `N=16,353,511`:

| pair | deployment overlap | as % of window |
|---|---|---|
| 0.55 vs 0.62 | 1,308,281 flows | **53.3%** |
| 0.62 vs 0.70 | 1,144,745 | 46.7% |
| 0.70 vs 0.77 | 1,308,280 | 53.3% |
| 0.77 vs 0.85 | 1,144,745 | 46.7% |
| any non-adjacent pair | 0 | **0.0% — disjoint** |

So the reviewer's "47–53%" is exact, and the **primary/secondary pair is the worst case in the set.**

**Two things the reviewer did not find, both of which belong in the same disclosure:**

1. **`deployment(pos) == calibration(pos+0.15)`, to within one flow.** `[8994431,11447457)` is
   simultaneously the 0.55 deployment block and the 0.70 calibration block — byte-identical. The other
   two pairs (0.62-dep/0.77-cal, 0.70-dep/0.85-cal) differ by exactly **one flow at each end** from
   integer flooring, so "exactly" is wrong and the paper says "to within one flow of integer
   rounding". (I wrote "exactly" into the paper first and caught it on verification.) The positions are a
   **sliding window over one stream**, which is a sharper statement than "partially overlapping".
   This is *not* leakage within any single window (each is chronologically clean: train < cal < dep),
   and the disclosure must say so or it will read as a much worse finding than it is.
2. **Non-adjacent windows are genuinely disjoint.** 0.55 and 0.70 share nothing. That is worth
   stating because it is the honest upside: there *is* an independent view available. It is not usable
   as a replication, because 0.70 and 0.77 are the two positions where no episode clears its own step
   — which is itself a finding, not a convenience.

**Work:**
- Rename globally: `primary` (0.55) / **`secondary pre-specified`** (0.62) / `stress` (0.85).
  Drop "replication" everywhere, including the abstract's "replication-window median is six".
- Delete "quasi-independent views" (`satml.tex:324`) — unsupported by the construction.
- Add one sentence in §II-E giving the overlap number, the sliding-window identity, and the
  no-within-window-leakage clarification.
- **This is a multi-file sweep and that is exactly the failure shape recorded in
  [[satml-tex-submission-draft]] — a rename applied to `satml.tex` but not to a shared generated
  caption has happened three times.** All of the following contain "replication" and must move together:
  - `paper/satml.tex` (14 occurrences)
  - `paper/make_appendix_tables.py` (6) → regenerate `paper/tables/{a1strata,nonoracle,groupcal,pools}.tex`
  - `paper/make_figures_satml.py` (4) and `paper/make_figures.py` (1) → **Fig. 4A's legend prints
    "canonical, 0.62 replication: median 6 (11 alerts)"; the figure must be re-rendered**
  - `proto/t65_satml_claims.py` lines 139, 199–200, 334 (registry entry + abstract check + flat-pad check)
  - `proto/t61_paper_consistency.py` lines 517–518 (`R6` window-names check) and the note at 1192
- Verify with a repo-wide `grep -ri replication` returning only intended hits.

---

## R12-2 — float placement

**Verdict: the substance is valid, but every one of the four cited examples is stale. Do not fix
what the reviewer listed; fix what is actually there.**

Recompiled `satml.tex` and audited the PDF geometry word-by-word. **Every body float is at the top of
its column or page — none is mid-column** (`Table I` capY=53 = colTop, `Fig.2`/`Fig.3`/`Fig.4`/`Fig.1`
graphics all start at colTop). All four sentences the reviewer quotes read **continuously**:

| reviewer's claim | actual current PDF |
|---|---|
| p4 "…no observation after *t* can restore / [TABLE I] / feasibility…" | intact, right col y=385–409, entirely below Table I |
| p9 "…which scores highly and / [TABLE III] / does not dilute." | intact, right col y=225–237 |
| Fig. 4 splits "Treat every data-conditioned module…" on p10–11 | that paragraph is wholly on p11 (y=697→p11 right y=51); **Fig. 4 is on p12** |
| Fig. 2 splits the Krönert sentence on p5 | intact, right col y=567–591 |

This matches `docs/33_review11_worklist.md` R11-5, which fixed the two breaks that did exist. The
reviewer is reading a PDF from before that fix.

**What is actually broken now** (pagination drifted after the R11-4 and conventions-paragraph edits,
so R11-5's careful landing was lost):

| float | break falls at | severity |
|---|---|---|
| **Table II** (p7, span) | p6 ends `"…for the covered procedures under unin-"` → **a hyphenated word split across the float** | **worst — fix** |
| **Table III** (p9, span) | p8 ends `"15.7×"` → resumes `"at the primary window and 5.1× at the stress window"` — a number severed from its comparator | **fix; this is the exact class R11-5 fixed and drift reintroduced** |
| Fig. 4 (p12, span) | p11 ends `"an attacker without that"` → `"state must over-provision"` | mid-sentence |
| Table I (p4, right col) | left col ends `"Every per-alert padding cost is"` → `"an oracle lower bound"` | mid-sentence |
| Fig. 2 (p5, right col) | `"(an attack-free observation period"` → `"of 8.5–47×"` | mid-parenthetical |
| Fig. 1 (p3), Fig. 3 (p8) | mid-list / mid-formula | cosmetic |

**Work:** land the two flagged breaks on clause boundaries. Note the residual recorded in R11-5 —
a full-width `table*` in two columns *always* falls between one page's last line and the next page's
continuation, so the goal is to choose *where* the break lands, never to remove it. **Do this item
near-last: it is pure pagination and every earlier text edit invalidates it.**

---

## R12-3 — FDR vs FDP

**Verdict: valid.** `satml.tex:369`, Table I row: `Measured $\FDR$ of e-LOND`. One realised labelled
run yields an FDP; FDR is its expectation over repetitions. The paper is careful about this everywhere
else — `:903` correctly pairs "empirical all-null $\FDR$ is 0.010" (repeated streams) with
"mixed-stream mean $\FDP$ is 0.047", and `:1289` correctly labels the stress-window column $\FDP$.

**Work:** change the Table I row to a guarantee-bearing label (`Nominal e-LOND FDR guarantee on data`),
then sweep every FDR/FDP occurrence against the three-way rule: theory/expectation → FDR; one realised
stream → FDP; repeated-simulation estimate → empirical/estimated FDR or mean FDP.
`:191` ("Every empirical FDR interpretation … is conditional on the group-validity premise") is about
the *guarantee* and is correct as written — do not over-apply the rule.

---

## R12-4 — the escape taxonomy is not exact

**Verdict: valid, and one appendix sentence contradicts itself.**

`satml.tex:517`: "Two genuine escapes remain." The section then correctly explains that online e-BH
does not decide against a level fixed at arrival, so `\eqref{eq:feas}` and the absorption predicate
are **not defined** for it. `satml.tex:1295` is worse — it asserts *"Only ADDIS and online e-BH are
genuine escapes"* and then, in the same sentence, *"the absorption predicate does not apply to it."*
A theory reviewer will ask what an undefined predicate is being escaped from.

**Work:** replace "escape" as the genus with the consequence, then name two distinct mechanisms:
- genus: "Two mechanisms avoid the practical consequence of the finite arrival-time horizon."
- **Selective index advancement** — ADDIS (a genuine escape from arrival-time absorption).
- **History-wide reconsideration** — online e-BH (outside the predicate; avoids *permanence*).

Check Table II's absorption column still reads `n/a` for e-BH (it does) and that §III-D's own
`\emph{}` run-in headings match the new genus wording.

---

## R12-5 — tighten the non-oracle padding claim

**Verdict: valid.**

`satml.tex:761`: *"A single multiplier chosen \emph{in advance} therefore suffices: $c=10$…"*
`src/lib/t66_nonoracle_padding.py:57` pre-commits the **grid** `CS=[2,3,5,10,100]`, and the module's
own `note_multiplier_selection` says the per-window minimum "is chosen AFTER seeing the realised
overshoot factors and is an oracle-informed floor". So the grid was fixed in advance; *which grid
element to headline* was not. "Chosen in advance" claims prospective selection the experiment does
not establish.

**Work:**
- `:761` → lead with the knowledge claim, demote `c=10` to an example: "A fixed multiplier requires no
  access to $S$, $\alphat$ or $\nCal$ at attack time. For example, $c=10$ suppresses every canonical
  alert in the two evaluated windows…"
- `:308` "dropping to knowledge-free sizing costs a small constant" → **"state-free"**, and prefer
  "a modest measured factor on the evaluated windows" over "a small constant". "Knowledge-free" is
  too broad: the multiplier attacker still knows $m$ and which host pair/bucket it is attacking.
- `:998` (Limitations) carries the same "knowledge-free" wording — sweep both.
- Keep the existing honest caveats: the flat pad reads the realised $r^\star$ distribution, and the
  first-flow stress arm where overshoot reaches 4,302 and no tested multiplier suffices.

---

## R12-6 — grammar and a copy-edit pass

**Verdict: valid.** `satml.tex:837`: *"caps large enough to preserve the intended validity domain
issue no detection at the median window--seed cell"* → **"yield zero detections at the median
window--seed cell"** (the reviewer's second, stronger option; "issue no detections" keeps an awkward
verb).

**Work:** make the fix, then one meticulous copy-edit pass over the body looking for this *class*
(subject–verb agreement across a long qualifier, singular/plural of "detection"), **not** stylistic
rewriting — the reviewer explicitly asks for proofreading rather than re-drafting, and R11's theory
freeze means no scope changes.

---

## R12-7 — abstract: name the configuration

**Verdict: valid, wording only.** Abstract currently: *"the full chain suppresses 78 of 79 detected
episodes on a second, benign-inclusive dataset."* "The full chain" does not say which configuration
produced 78/79.

**Work:** → *"the same canonical-order pipeline suppresses 78 of 79 detected episodes on a second
benign-inclusive dataset."* Update `proto/t65_satml_claims.py`'s abstract check to pin the new phrase.

**Explicitly out of scope:** the reviewer states the AIT canonical-order change was the right call and
that the host-conditioned AIT rerun should **not** be done. No new compute in this round.

---

## R12-8 — proof audit and theory freeze

**Verdict: already done, in review 11.** R11-1 ran the independent adversarial proof audit on
Lemma 1, Thms 1–4, Cors 1–2, Thm 3's Vovk–Wang dependency and Props 1–2, using **two** blind codex
agents on the identical brief. It found Thm 4 false as written without the cap hypothesis
`λ ≥ k/(|C|+1)`, which is now in the statement; the closure result now carries the onset `t_1` and the
`1/ρ'` stretch. `memory/review11-theory-freeze.md` records the freeze (AIT canonical, 78/79).

**Work: none.** The action this point implies is *negative* — **honour the freeze.** None of R12-1…7
touches a theorem statement, and none may. If any item appears to require a theorem change, stop and
raise it rather than editing.

---

## R12-9 — claim ledger

**Verdict: 6 of the reviewer's 8 values are already pinned by `proto/t65_satml_claims.py`; 2 are
real gaps.** Current gate state: `t61` 197 + 129 retired, `t65` 74, `t45` 268 — all green.

| ledger value | pinned by t65? |
|---|---|
| `3.3e8` calibration flows | yes |
| primary costs 23, 24, 33 | yes (`23--33`) |
| secondary median 6 | yes |
| AIT canonical 78/79 | yes |
| AIT first-flow 84/85 | yes |
| synthetic median 140 | yes |
| **host-conditioned 9/9** | **no** |
| **ADDIS 203** | **no** |

Both gaps are covered only by `t61`'s *existence* sweep, which is precisely the weakness recorded in
[[wrong-statistic-failure-mode]]: an existence check cannot catch a mean/median/one-arm value dressed
as the wrong statistic. I verified both by hand during this investigation and **both are correct**:
- ADDIS 203 → `out/t32_B1.json` `bstar[0].bstar == bstar[0].bstar_closed == 203`, with
  `baseline.rejections == 152`, matching `satml.tex:894`.
- host-conditioned 9/9 → `satml.tex:723` Table III row, `9` detections / `9/9` suppressed.

**Work:** add claim-level `t65` checks for these two, each recomputed from its artefact and scoped to
the sentence that makes the claim (`para_of`, per the §V-D scoping bug fixed in an earlier round).
Do **not** hand-build the spreadsheet the reviewer describes — the registry already is that ledger,
and a parallel manual copy would drift.

---

## R12-10 — Table II caption density

**Verdict: valid and measurable.** Body caption word counts: Fig.1 76, Table I 47, Fig.2 76,
**Table II 175**, Fig.3 59, Table III 123, Fig.4 123. Table II is 44% longer than the next densest and
carries `†/‡/§` footnote machinery.

**Work:** move the `†` SAFFRON explanation and the e-BH `n/a` rationale into the §III-D prose that
already discusses both (R12-4 rewrites exactly that passage — **sequence R12-10 immediately after
R12-4** so the prose lands once). Keep in the caption only what a reader needs to parse the columns.
This is the one item that *buys* page budget, which R12-11 needs.

---

## R12-11 — page budget *(added by this investigation; not in the reviewer's list)*

**The body is over the 12-page limit.** `satml.tex:16` scopes the budget to body text, excluding
references, appendices and the Open Science / LLM Usage / Ethics sections. Measured on the current
compile: §VIII Related Work ends p13 left column y=255, **§IX Conclusion runs p13 y=278→512**, and
the excluded Open Science section starts at y=535. So the numbered body is ≈**12.35 pages — roughly
39 column-lines over.**

This corrects what I reported at the end of the previous round ("body p.12"); the drift came from the
R11-4 appendix edits and the conventions-paragraph fix, and it is the same drift that undid R11-5's
float landing (R12-2).

**Work:** per [[paper-refit-at-the-end]], **do not trim per item.** Complete R12-1…10 — several of
which add text (R12-1's overlap sentence, R12-4's taxonomy) and one of which removes it (R12-10) —
then refit once, then do R12-2's float landing last, since the refit moves every page break.

---

## Ordering

1. **R12-1** window rename + overlap disclosure — highest credibility risk; largest blast radius
   (tex + 2 figure generators + table generator + 2 gates); do it first while the page budget is
   still going to be re-cut anyway.
2. **R12-3** FDR/FDP sweep — small, self-contained, high reviewer value.
3. **R12-4** escape taxonomy, then **R12-10** Table II caption — adjacent text, one edit.
4. **R12-5** non-oracle tightening.
5. **R12-7** abstract configuration wording.
6. **R12-9** two `t65` ledger checks.
7. **R12-6** typo + copy-edit pass — after all text edits, so the pass sees final prose.
8. **R12-11** single page refit.
9. **R12-2** float landing — genuinely last; pure pagination.

Gate discipline: `t45`, `t61`, `t65` after every item, plus a `grep -ri replication` sweep after
R12-1 and a full recompile check (0 overfull, 0 undefined refs) before R12-11 is judged.

## Findings log

(appended per item, with the blind review verdict for each)

---

# Progress — R12-1, 3, 4, 5, 6, 7, 9, 10 applied

Page-limit work (R12-11) and float landing (R12-2) deferred by the author's instruction: finish all
content first, then refit once seeing the whole picture.

## Blind audits

Four `codex exec` runs. **The first two produced nothing** — a broad seven-item brief made them burn
their budget on `ripgrep` dumps of the whole paper, and backgrounding them via `nohup … &` killed them
mid-run. **Lesson: run codex in the FOREGROUND, one tightly-scoped brief, and forbid file dumps.**
Two tight foreground briefs then completed and each found something the other did not — the pattern
[[blind-codex-review-workflow]] predicts.

**Audit 1 (overlap arithmetic) — 1 FALSE, 2 IMPRECISE, and one finding I had missed entirely:**
- `47`--`53\%` is **wrong at both ends**: the true adjacent overlaps are 46.667% and 53.333%. I had
  dropped the reviewer's "approximately". Now stated as `46.7`--`53.3\%`.
- **The training pools are nested.** `[0,i_1)` grows with position, so every earlier position trains on
  a prefix of every later one's data. My disclosure said "positions two or more apart are disjoint" —
  true of the *deployment blocks*, but the *analyses* are not independent, because the fitted detectors
  share training data across all five. This is the sharper form of the reviewer's objection and it was
  not in the reviewer's list either. Now disclosed.
- (d)/(e)/(f) verified TRUE, including the one-flow rounding qualifier.

**Audit 2 (current state, five statements) — 1 FALSE:**
- The R12-4 taxonomy fix was **incomplete**. §III-D and the Table II caption were corrected, but
  Fig. 2's caption still said e-BH "escapes the absorbing horizon" and §VI still said "online e-BH
  escapes the horizon" — both contradicting "the predicate is not defined for it". A third use in the
  introduction ("the two controller-internal escapes") had the same problem. All three fixed.
- [A] [B] [C] [E] verified TRUE, including that `c=10` is the smallest **grid** value defeating all in
  both windows and that 15.7/5.1 are medians of added/oracle over defeated alerts.

## Self-caught before the audits

- I wrote "**exactly**" for `deployment(pos) == calibration(pos+0.15)`. Only **one** of the three pairs
  is byte-identical; the other two differ by one flow at each end from integer flooring. Now "to within
  one flow".
- I wrote `c=10` as "the smallest value defeating every canonical alert", which reads absolutely — the
  true real-valued minimum at the stress window is **7**. Rescoped to "the smallest value in a
  pre-declared grid".
- The generated table `tables/nonoracle.tex` still carried "**a pre-committed flat pad, needs no
  knowledge at all**" — the same overclaim I had already fixed in the prose, surviving in a generator.
  Choosing `N` reads the realised `r^\star` distribution. Fixed in `make_appendix_tables.py`.

## Gate work — the rename was NOT protected

Injection-testing showed the existing `t61` R6 check and the `t65` registry entry **both passed** when
a sentence was reverted to "replication window": R6 was an *existence* test that a dozen other
occurrences satisfied, and `t65`'s third argument is a description, not a pinned string. A rename needs
an **absence** check. Added, over `ALL_TEX` (body + generated tables; `main.tex` deliberately out of
scope), licensing only the two phrases that *deny* replication.

New checks, all injection-tested:
- `t61` R12-1: no "replication" window name anywhere; overlap disclosure present with its numbers
- `t65` R12-4: no escape verb takes online e-BH as subject; Fig. 2 caption states the predicate is
  undefined (a *pronoun* subject defeated the regex, so the caption is guarded by content)
- `t65` R12-5: `c=10` presented as fixed, not prospectively chosen; "knowledge-free" forbidden
- `t65` R12-9: host-conditioned 9/9 (= shaw 3/3 + wilson 6/6) and ADDIS `B*=203` with its 152-rejection
  baseline, each recomputed and scoped to its own sentence

**Final:** `t45` **268**, `t61` **199**, `t65` **85**, all green; 0 errors, 0 undefined refs,
0 overfull boxes. Body still ends on p.13 — the refit is R12-11.

---

## R12-2 — float landing **(done, durable part)**

Done ahead of the refit at the author's request, so it was deliberately scoped to what **survives**
repagination rather than to hand-placing floats that the refit will move anyway.

**What the defect actually is.** Re-measuring after the R12 edits, the earlier `unin-|terrupted` split
was gone (pagination had moved) — but a purpose-built detector found **two hyphen-splits at column
breaks**, one of them *introduced by my own R12-1 rename*:

| break | text |
|---|---|
| p2L → p2R | `…0.62 a pre-specified secondary win-` \| `dow. Position 0.85 has…` |
| p12R → p13L | `…TESSERACT's temporal evaluation con-` \| `straints [27]…` |

The other 17 mid-sentence column breaks are **not** defects: a paragraph crossing a column boundary is
ordinary two-column flow and would happen with no floats at all. Chasing them means moving float
anchors, which changes which page a float lands on — and the refit undoes it.

**The fix, chosen by measurement not by taste.** Tuning `\brokenpenalty` against the real metric:

| setting | hyphen-splits | badness-10000 vbox |
|---|---|---|
| none (baseline) | 2 | 8 |
| `\brokenpenalty=10000` | **0** | 12 — adds two stretched pages, one in the body |
| `\brokenpenalty=5000` | 1 | 8 |
| **`5000` + `\hyphenation{window windows}`** | **0** | **8 — no cost at all** |

So `10000` reaches zero but pays two badness-10000 pages (p2 in the body). Forbidding hyphenation of
the paper's most-repeated word instead reaches zero **at baseline cost**. Both settings are
pagination-independent — they forbid a *class* of break rather than placing one float — so they
survive the refit.

**New gate: `proto/t68_layout.py`.** Checks the rendered PDF for the two things that *are* defects:
(1) no column/page break inside a hyphenated word; (2) every body float at the top of its column or
page. Reports mid-sentence breaks as information only, with the reasoning in the docstring, so the
next reviewer report of "floats interrupt sentences" can be answered in one command instead of a
manual geometry pass.

**Three detector bugs found by injection-testing, all mine:**
- Word count cannot separate body prose from figure internals — an axis row `10 3 10 4 10 5 …` counts
  14 "words". Neither can width alone. **Left-margin alignment** does: prose starts at the column
  margin (x≈49 / x≈312, measured from the document); ticks, legends and panel titles are indented
  ≥15pt further.
- I estimated line width as `5.2·len(word)` when the true `xMax` was in the bbox and I had discarded it.
- My first two injections **failed to create the defect** rather than exposing a blind gate: `[!h]`
  and even `[H]` both landed at a column top, because those anchors sit at boundaries. Forcing a float
  mid-paragraph put it at the **foot** of a column — 20 prose lines above, none below — which my
  "prose above AND below" rule missed. Broadened to *any prose above*, which is the real condition.

**Remaining, for after the refit:** 4 of 7 float landings fall mid-sentence (p3 Fig. 1, p6 Fig. 2,
p7 Fig. 3, p9 Table III); Table I and Fig. 4 land on sentence boundaries and Table II lands after a
display. These are cosmetic and repagination-dependent — re-run `t68` after the refit and improve
whatever remains.

**Final:** `t45` 268, `t61` 199, `t65` 85, `t68` 2 — all green. 0 errors, 0 undefined refs,
0 overfull boxes, underfull vbox back at the baseline 16. Body still ends p.13 (R12-11).

---

# Re-validation pass (2026-09-04)

The same seven points were sent again. Each was re-checked against the **current** compile rather than
against the earlier log. All seven hold; two things were found and fixed.

| point | verdict on re-check |
|---|---|
| 1 window naming | done — 0 occurrences of "replication window"/"quasi-independent"; §II-E discloses 46.7–53.3% overlap, the 53.3% worst pair, one-flow cal/deploy coincidence, and nested training pools |
| 2 float placement | **all four cited sentences verified intact again** on the new pagination — each lies wholly within one column with no float between its words |
| 3 FDR vs FDP | Table I row is the guarantee; **one residue found and fixed this pass** (below) |
| 4 escape taxonomy | done — genus reworded in §III-D, intro and appendix; both run-in headings present; no "e-BH escapes" anywhere |
| 5 non-oracle | done — leads with the knowledge requirement, `c=10` scoped to a pre-declared grid, "state-free" |
| 6 §V-E grammar | done — "yield zero detections" |
| 7 abstract wording | done — "the same canonical-order pipeline"; host-conditioned AIT **not** rerun, still first-flow, artefacts untouched |

## Two findings

**Point 3 residue.** A full sweep for "FDR attached to a realised single run" still matched twice:
*"Every empirical FDR interpretation at the other windows…"* and *"guarantee-bearing readings of
empirical $\FDR$…"*. Both are defensible — the thing that is conditional is the FDR *reading* of the
results, not a measured FDR — but "empirical FDR" sitting adjacent reads as a measured quantity, which
is exactly what the reviewer said a multiple-testing reader would catch. Reworded to *"Every $\FDR$
reading of the empirical results…"* and *"guarantee-bearing $\FDR$ readings of the empirical
results…"*. The sweep is now 0.

**`t68` caught its first real regression.** That two-sentence edit reflowed p2 and stranded a *different*
hyphenated word across the column break — `a pre-specified secondary window. Posi-` / `tion 0.85…`.
The gate failed, as designed. Re-measuring the options on the new text:

| setting | hyphen-splits | overfull hbox | badness-10000 vbox |
|---|---|---|---|
| `5000` + `{window windows}` | 1 | 0 | 8 |
| **`5000` + broader core list** | **0** | **0** | **8** |
| `10000` (with or without list) | 0 | 0 | 12 |

`\brokenpenalty=10000` still buys nothing the word list does not, and still costs two badness-10000
stretched pages. So the list was widened from the one word that broke last to the paper's repeated
vocabulary (`window(s) position(s) calibration deployment detection(s) secondary canonical`), which
costs no overfull line and pre-empts the reflow the page refit will cause. **The lesson is that this
class is whack-a-mole by nature** — each reflow strands a different word — which is precisely why the
fix is a gate plus a vocabulary list rather than a one-off repair.

**Final:** `t45` 268, `t61` 199, `t65` 85, `t68` 2 — all green. 0 errors, 0 undefined refs,
0 overfull hbox, underfull vbox at the baseline 16. Body ends p.13; the refit (R12-11) is the last item.
