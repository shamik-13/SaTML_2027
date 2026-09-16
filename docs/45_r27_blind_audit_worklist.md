# Round 27 — eight focused blind audits of the whole draft, aggregated into a worklist

Method (6 Sep 2026): eight independent codex runs (`codex exec -s read-only`), each given ONE part of
the draft and a narrow goal, never the whole file: A opening (abstract, Sec. I), B model and theory
(Secs. II–III, Appendix A scope, the proofs of Thms 1–2 and Cor. 1), C grouping and impossibility
(Secs. IV, V-A, V-B, Route A/B proofs), D empirical numbers against the artefacts (Secs. V-C–V-F,
Tables III–V), E discussion (Secs. VI–VII, Related Work, Conclusion), F compliance (front/back matter,
Open Science, LLM section, Ethics, `refs.bib`, `src/README.md`), G appendix cross-reference fulfilment,
H copy-editing and notation. Briefs and verbatim reports: `docs/r27_briefs/`. Every finding below was
checked against the source or the artefact before triage; §2 lists the ones that did not survive.

## 0. Facts established while triaging

| Finding | What the source says |
|---|---|
| C1 "3→46 detections labelled canonical but grouping.tex is first-flow" | The body's 3→46 / 24→496 come from `t74_defended_replay` (canonical, grouping-key axis; t65 R20 checks them). `apptab:grouping` is a different experiment (`t26`, first-flow, primary window). Body correct; the two are not the same measurement |
| G1 "35 configurations vs 15 rows" | `t26_H4_5pos.json` has 350 rows = 5 families × 7 buckets × 5 positions × 2 seeds, i.e. 35 per (position, seed); `apptab:grouping` shows the primary window at seed 0 only. The body claim is artefact-backed but the appendix shows a subset |
| B1 tie rule | `src/lib/h_stream.py:147`: $K_i = 1 + \#\{c\in\mathcal C: s_c \ge s_i\}$ (`searchsorted(..., side='left')`), so a tied calibration score counts AGAINST the test flow — conservative. The paper does not say so |
| B2 normalisation | The gates use $\zeta(1.6)=2.2857657$; the body writes only $\gamma_j\propto j^{-1.6}$ |
| D1 / G2 "108 vs 118" | `t49_R7.partC[0.55]`: 108 = `median_r_suppress_host`, 118 = `median_r_star_flowlevel` — both medians; `apptab:r7host` has no cost column (the costs sit in the r7host prose companion) |
| D2 `tab:main` AIT cells | 12–4,650 and 269 / 364.5 are EMPIRICAL replay medians (`t67` canonical, `t54` host); closed-form medians are 4,132 (russellmitchell) and 355 (wilson). The header says $r^{\star}_t$, the caption says "exact per-alert cost" |
| F1 "AIT pipeline undocumented" | `src/data/README.md` §AIT-LDSv2.0 documents the zips, the label set and the extraction in `lib/t51_R7_ait.py`; `src/README.md` itself mentions only LSPR23 |
| F2 figure wrapper | `paper/make_figures_satml.py` is a 20-line wrapper over `src/lib/figures.py` and is NOT in `src/`; the notebook draws the same figures |
| F5 footprint proxy | Client logs for this project: Claude Code 48.8 M output tokens, 0.2 M uncached input, 126.7 M cache-creation, 11.4 G cached-prefix reads; Codex 130.2 M total tokens over 138 sessions with the repo as cwd |
| F8 bib | `javanmard2015lond` (arXiv 1502.06197, LOND) and `javanmard2018lord` (AoS 2018, LORD) are different papers, both cited |
| H4 first citations | Table I :200, II :229, tab:main (V) :547, tab:costcurve (III) :554, tab:defenses (IV) :988; fig:attacks first cited :861, placed :698 |

## 1. Worklist (tiered; every item is a wording, table or gate change — no new experiment)

### Tier 1 — correctness and faithfulness

| # | Source | Action | Gate impact |
|---|---|---|---|
| 1 | A1, A7 | Fig. 1 caption: "and thereby makes the composition of each tested hypothesis attacker-facing" → conditional on an attacker-co-occupiable key; "against the shrinking level of an arrival-time controller" → "against a level that decays along a rejection-free run" | none |
| 2 | C2 | Sec. V-A :652 "rules out any symmetric aggregation rule that would ignore the padding while retaining validity" → "any alert-capable symmetric aggregation rule" ($F\equiv1$ is the counterexample the paper itself names) | none |
| 3 | B3 | Sec. III-B :507–512: "$\rho_p\ge1$ is exactly cold-start feasibility through $T$" holds only under the horizon-uniform allocation (Cor. 1 sufficiency); add that clause. Fig. 3 and III-C already use it that way | t65 R13-4 neighbourhood; check |
| 4 | D2 | `tab:main`: header "$r^{\star}_t$ per alert" → "cost per alert"; caption: LSPR23 rows are the exact per-alert cost \eqref{eq:rstar}, AIT rows the empirical replay median, which exceeds the closed form where a pad fires (russellmitchell 4,650 vs 4,132; wilson 364.5 vs 355) | t61 EMBEDDED order words unchanged |
| 5 | D1, G2 | Sec. V-F :935 "$r^{\star}_t=108$ against 118" → "a median suppression cost of 108 flows against the flow-level closed-form median of 118"; add a "median cost host / flow" column to `apptab:r7host` from `partC` so the cross-reference delivers the number | t61 registry unchanged (same artefact) |
| 6 | B1 | Sec. II-A eq. (1): define $K_i=1+\#\{c\in\mathcal C:s_c\ge s_i\}$, ties counted against the test flow (conservative), and $1\le k\le\nCal+1$ | none |
| 7 | B2 | Sec. II-A :334: "$\gamma_j\propto j^{-1.6}$" → "$\gamma_j=j^{-1.6}/\zeta(1.6)$" once, keep "∝" elsewhere | none |
| 8 | G1 | Sec. IV :610: "35 configurations in all (\cref{app:granularity})" → "…35 configurations per window and seed; \cref{apptab:grouping} shows the primary window at seed 0, and feasibility, which depends on $T$ alone, is order-invariant" | none |
| 9 | F2, F1 | Ship `paper/make_figures_satml.py` in `src/` (as `src/make_figures.py`, 20 lines) so the Open Science sentence is literally true, and add one line to `src/README.md` pointing at `data/README.md` for the AIT inputs | t70 (src completeness) re-run |

### Tier 2 — scope statements and limitations (each one clause)

| # | Source | Action |
|---|---|---|
| 10 | E1 | VII-B "Empirical breadth": add that the third LSPR23 window used is the known-invalid stress window, mechanism and cost only |
| 11 | E2 | VII-B "Attack cost is a curve": add that the joint rerun assumes the attacker pads exactly the episodes it owns (identified by the labels; on LSPR23 those host pairs carry no benign traffic) |
| 12 | E3 | Same paragraph: the joint rerun propagates zero-evidence pads; a pool with a positive firing rate would raise $J_{\mathrm{seq}}$, and the replay bounds that rate at $3.5\times10^{-6}$ but the rerun does not sample it |
| 13 | E6 | Conclusion :1127: "per-alert pricing does not characterise the joint cost" → "on the two windows we re-ran, per-alert pricing did not characterise…" |
| 14 | E7 | Related Work :1073: "the published fix~\cite{egai2025} equals e-LORD before the first rejection" → neutral: "the mem-e-LORD construction of~\cite{egai2025} coincides with e-LORD before the first rejection" |
| 15 | D3, D4, D5 | Table III caption "seed fixed" → "seed 0"; V-F host-context sentence adds "primary window, seed 0, horizon-free"; V-C $c=10$ sentence adds "horizon-free" (t65 pins "on LSPR23, $c=10$" — keep the prefix) |
| 16 | A3, A4 | Sec. I contribution 1: "evaluable from $\nCal$, $k$ and $T$ alone" → add "for the covered controllers under uninterrupted operation"; :166 "e-values permit FDR control under arbitrary dependence" → "given valid e-values" |
| 17 | A6, A8 | Sec. I: one-clause glosses at first use of "horizon-aware" (knows the stream length) and "canonical order" (a metadata-hash tie-break); :191 "Prior work studies … separately" → add "and the pipelines that compose them do not analyse the composition's horizon or its membership surface" |
| 18 | C3 | Sec. IV :595: "falls in the same proportion" → "$\nCal_{\min}+1$ falls in the same proportion" |

### Tier 3 — presentation

| # | Source | Action |
|---|---|---|
| 19 | H1–H3 | Expand at first use: LSPR23 (Locked Shields 2023 live-fire exercise), AIT-LDSv2.0 (Austrian Institute of Technology log data set v2.0), AUROC, AUPRC, FDP; one sentence in Sec. II-A or the Procedure-definitions appendix expanding LOND, LORD, SAFFRON, ADDIS, e-BH |
| 20 | H4 | Float order: change :547's \cref{tab:main} to \cref{tab:costcurve} (Table III carries the same 3 and 11); put `tab:main`'s source before the defences table in Sec. V-F so `tab:main` becomes Table IV and the defences table Table V, matching first-citation order; add a forward \cref{fig:attacks} in Sec. V-C so Fig. 4 is cited before it appears |
| 21 | H5, H6 | $S\to S_t$ at :737, :767, :877 (keep the pinned prefix "A fixed multiplier requires no access to"); one sentence fixing the index convention (sequence $\gamma_j$, level at step $t$ uses $\gamma_t$) |
| 22 | F4, F5 | LLM section: one sentence that no smaller model was evaluated and the choice was availability; optionally the logged footprint proxy (49 M generated + 127 M uncached input tokens for Claude Code, 130 M total for Codex, plus 11.4 G cached-prefix reads) — **author decision** |

### Tier 4 — author-only

| # | Source | Action |
|---|---|---|
| 23 | F7, F9 | `refs.bib`: complete pages/volume for the nine `@inproceedings` entries at lines 173, 192, 274, 285, 298, 326, 365, 375, 398; `kronert2024fdr` from `@article{journal={arXiv preprint}}` to `@misc` with eprint |
| 24 | F3 | Ethics: decide whether to add a release-safeguard sentence (the attack is a statistical composition attack demonstrated on public exercise data; the artefact is analysis code, not a tool) |

## 2. Findings declined, with the reason

- A2, A5 (abstract and contribution scopes): the abstract is at 234 of 235 words and carries dataset, window, order and regime for every number; the round-26 reviewer accepted this form.
- B4 (positivity hypotheses in Thm 1) and B5 ($\Delta$ undefined): $\alpha,c_g,\ceil>0$ are implicit in the definitions; $\Delta$ is introduced in the statement as the run length. Both statements are t69-frozen; a change would need a re-freeze for no substantive gain. Record for the next theory audit.
- C1: the body's 3→46 is a canonical `t74` measurement; the auditor compared it with a different experiment.
- E4 (cap sentence "overreads"): Sec. VI already says "can", Sec. V-D says "on the two windows and the sampled caps we evaluate", and t65 pins the residual-set concession.
- E5 (order dependence understated): Sec. V-E states the fifty-order distribution and t65 pins that sentence.
- F1 as stated: the AIT pipeline is documented in `src/data/README.md` (item 9 adds the pointer).
- F6 (`python` vs `python3`): the README's commands run inside the pinned virtual environment, where `python` exists; the sandbox lacks it.
- F8 (duplicate Javanmard entries): two different papers, both cited.
- G3 (orphan appendix subsections): each is reached through its parent section's body pointer; direct pointers would cost body lines for no reader benefit.
- H7 (`\S\ref` in Table II, `Theorem~\ref` in a subsection title): `\S\ref` was chosen to keep Table II inside its column; cleveref in a section title is fragile.
- H8 (repeated cold-start sentence): abstract, contribution and limitation each need the statement; the wording is already the compressed form.

## 3. Execution notes

Order: Tier 1 → Tier 2 → Tier 3, one compile and gate run per tier; the body ends at layout line 52 of
57 on p.12, so Tier 2's added clauses (about six lines) will need a matching cut — take it from Sec.
VI-B or VII-B, not from the results. Item 20 moves floats: re-check with a render, not only t68. Pins
to re-anchor: t65 R14-3 ($c=10$ sentence gains "horizon-free"), t61 EMBEDDED `tab:main` caption (order
word "canonical" must stay), t70 after item 9. Then one blind confirmation run per tier (brief: the
item list, ask FIXED / PARTLY / NOT and for new inaccuracies).

## 4. Execution log

**Tier 1 — done 6 Sep 2026.** All nine items applied as specified in §1. Blind confirmation run
(`docs/r27_briefs/../confirm_T1.md`, report in the scratchpad): eight FIXED, one PARTLY — the new
`tab:main` caption said the AIT empirical median "exceeds the closed form where a pad fires", which is
false at the median for six of eight organisations (equal medians; only russellmitchell and wilson
exceed). Reworded to "at or above the closed form by construction", which is exact because the closed
form is a per-episode lower bound. Also in this tier: `src/make_figures.py` shipped (t70 lists it),
`src/README.md` names it and points to the AIT inputs, `apptab:r7host` gained a "median cost h/f"
column. Tier 1 added about seven body lines; absorbed by sentence-level trims in Secs. I, II-C, III-B,
III-C, IV, V-D, VI-A, VII-B, VII-C and the Conclusion, plus Fig. 4 at 0.85. The body now ends exactly
at the foot of p.12 (Open Science opens p.13), so Tier 2's added clauses need matching cuts before they
go in. Gates: t61 239/0, t65 194/0, t71 34/0, t68 2/0, t69 0 drift, t45, t70 (3 consumers incl. the new
wrapper); 41 pages; 0 Type 3 fonts.

**Tier 2 — done 6 Sep 2026.** Items 10–18 applied as specified (breadth limitation names the
known-invalid 0.85 window; the joint-rerun limitation states the ownership assumption, the
zero-evidence pad model and the replay's $3.5\times10^{-6}$ firing-rate bound; the Conclusion's
joint-cost sentence is scoped to the two re-run windows; "published fix" → "the mem-e-LORD construction
of~\cite{egai2025} coincides with e-LORD before the first rejection"; Table III caption "at seed 0";
the V-F host-context sentence names window, seed, regime and the two-target denominator; the $c=10$
sentence names the horizon-free regime; contribution 1 scopes its criterion to the covered controllers
under uninterrupted operation; "valid e-values"; a gloss for horizon-aware; the novelty sentence names
what the composed pipelines did not analyse; "$\nCal_{\min}$, plus one, falls in the same proportion").
The additions cost about eight lines; paid for by sentence-level cuts that removed no claim: Sec. I
repair paragraph merged, contribution 3's cap clause shortened (the full statement stays in V-D), III-B's
calendar-form and "squeeze" sentences, III-D's list of appendix procedures, V-F's summary paragraph
(VII-B carries the scope), VI-B's implications 2–3 tightened, VI-A and II-A/II-C/III-A sentence merges;
Fig. 1 at 0.82, Fig. 2 at 0.78. Two hyphen splits at column breaks ("hori-zon", "un-interrupted") were
introduced by the reflow and fixed by extending the standing `\hyphenation` list. Body ends p.12
(layout line 53 of 57). Gates: t61 240/0, t65 194/0, t71 34/0, t68 2/0, t69 0 drift, t45, t70.
Blind confirmation of Tier 2 (`confirm_T2.md`): seven FIXED, two PARTLY — the $c=10$ sentence still
lacked its seed, and the cuts had dropped "under uninterrupted operation" from VI-B's first implication
and the reason from III-B's calendar-form clause. All three restored ("(seed 0)", "under uninterrupted
operation", "because calibration and deployment produce units at different rates"); III-D's "complete
taxonomy" now reads "the taxonomy of the procedures we evaluate". Re-compiled and re-gated after the
restorations.

**Tier 3 (items 19–21; item 22, the LLM section, deferred by the user) — done 6 Sep 2026.**
Expansions at first body use: AUROC/AUPRC, FDR, FDP (Table II caption), LSPR23 (Locked Shields Partner
Run 2023), AIT-LDSv2.0 (Austrian Institute of Technology log data set), LOND/LORD (levels based on the
number / recency of discoveries); SAFFRON, ADDIS and online e-BH expanded in the appendix procedure
definitions where they are defined. Float order: Sec. III-C now cites Table III (same 3 and 11), `tab:main`'s
source precedes the defences table so the numbering is I, II, III (costcurve), IV (main), V (defences)
in first-citation order, and Fig. 4 is forward-cited from Sec. V-C. Notation: the three remaining bare
$S$ are $S_t$; Sec. II-A states the $(\gamma_j)$ / $\gamma_t$ convention. The additions cost about five
lines, paid with: the Sec. I "What each claim depends on" paragraph folded into Table II's caption
("A1 …, which only the nominal FDR reading needs"), III-D's appendix pointer folded into a parenthesis,
and sentence merges in Secs. I, II-B, II-D, III (intro, III-A, III-C), IV, Related Work; Fig. 4 at 0.82.
Body ends at the foot of p.12 (Open Science opens p.13). One t65 pin had to move with the notation
(the non-oracle knowledge sentence now reads $S_t$).
Blind confirmation of Tier 3 (`confirm_T3.md`): notation, float numbering and the qualifier-preserving
cuts FIXED; the expansions were placed after earlier body uses for three abbreviations, and Fig. 4's
forward citation sat after its label in the source. Repaired: LSPR23 is expanded at its first body use
(contribution 3) and plain afterwards; the LOND/LORD gloss moved to contribution 1; AIT reads "the
Austrian Institute of Technology (AIT) log data set, version 2.0"; SAFFRON and ADDIS carry a pointer to
their appendix definitions at first body use (Sec. III-A); Fig. 4 is now cited in Sec. V-B (line 689)
before its label (702). Body ends at the foot of p.12; gates re-run green (t65 194/0 after moving the
"needing no estimate of $S_t$" pin, t61 240/0, t71 34/0, t68 2/0, t69 0 drift, t45 268/0).
Item 22 (LLM section: model-size sentence, footprint proxy) remains deferred at the user's request;
Tier 4 (bibliography metadata, ethics sentence) is author-only.
