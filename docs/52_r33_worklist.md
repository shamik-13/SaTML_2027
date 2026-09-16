# Round 33 worklist — positioning and first-page feedback on `paper/satml_codex_edit.tex`

Eight points, all wording and placement; no experiment. Tone brief from the user: natural, not
defensive, the paper is still being polished. Applied 12 Sep 2026, immediately after round 32
(`docs/51_r32_worklist.md`).

## Validation and action

| # | Point | Where it landed | Notes |
|---|---|---|---|
| 1 | First contribution bullet around the deployment boundary, not alpha-death; say the ingredients are known and the criterion + composed-system consequence are the contribution | Intro, bullet 1 (title `A deployment-level feasibility law` kept, body rewritten) | the criterion is stated as "given \|C\|, k, T decide before deployment whether a covered controller can possibly report an alert throughout the horizon"; "The mathematical ingredients are known ... the criterion ... are the contribution" |
| 2 | Name the three-level capability ladder on the first page; the gap is an empirical result | Abstract and bullet 3 | rungs: sequential oracle with realised controller state → retrospective real-flow replay → causal, state-free. "24 to 65 standing" (Table V: 24/27 prior pool, 65/60 state-free) registered in t65 against t76 |
| 3 | One sentence after the first statement of Assumption 1 | Sec. II-B, right after "The group-level premise is stated as Assumption 1." | "Neither the discovery-horizon results nor Theorem 3 requires it; it is needed only to read the empirical e-LOND runs as nominally FDR-controlled." |
| 4 | Fewer concepts in the first three pages; introduce by the causal chain only | Intro chain paragraph | chain extended to six links incl. controller-state feedback, tied to Fig. 1; one sentence says every other quantity attaches to a link and is introduced there. **No cuts made** — see Layout |
| 5 | Attach "under attacker-controlled, unbounded membership" wherever the symmetric-family claim appears | abstract, bullet 2, Sec. V-A lead-in, Sec. V-B discussion (two places), Sec. VI, Conclusion | theorem statement itself untouched (frozen, t69 0 drift) |
| 6 | Elevate the grouping trade-off (3→46 detections, 24→496 median exact cost) into the contribution summary | bullet 1, last sentence | t65 required "oracle lower bound" in the same sentence as `$24$`; added |
| 7 | Section VI as a deployment checklist | Sec. VI-B `A deployment checklist`, five numbered items | compute ρ first; no cheaply co-occupiable key; membership limits/admission in the threat model; restart → say which guarantee; no merger swap fixes padding (+ order/keyed-hash remark) |
| 8 | Surface one escape result from App. C in the body | Sec. III-C, after "horizon-aware spending or restart restores substantial power" | e-LORD horizon-aware 101 detections, 0 FP; two-hour restart with the deployment-wide budget 18 → 55 rejections; **labelled first-flow on both legs** — both numbers come from first-flow arms (t21c procmatrix, t35 restart), unlike the canonical 3/105 beside them. The detector-quality point was already in the next paragraph |

## Gate regressions this round, and their fixes

| gate | what it caught | fix |
|---|---|---|
| t71 claim ledger | occurrence 2 of "78 of 79" (bullet 3) omitted `canonical` | added "under the canonical order" |
| t65 | `$24$` without "oracle lower bound" in the same sentence | added the qualifier in bullet 1 |
| t65 R14-4 | "algebraic oracle" is a sense of *oracle* an earlier reviewer had reserved for exact r* sizing | renamed the rung "sequential oracle that sizes each pad exactly from the realised controller state" (an allowed form) |
| t65 abstract sweep | `65` unregistered | two guarded registry rows tied to t76 sums (guard: only when the abstract carries the ladder, so `satml.tex` does not regress) |
| t68 layout | column break inside "zero-|evidence" (round-32 sentence in V-F) | rephrased "are not zero-evidence" → "do not all carry zero evidence" |
| t65 anchor | `\subsection{Is the result an artefact` no longer exists in the codex draft (Sec. V-F renamed) | anchor moved to `\label{sec:transferattack}`, which both drafts carry; this also un-broke one pre-existing miss |

Final state: t61 247/0, t68 2/0, t69 0 drift, t70 3/0, t71 38/0, t72 10/0; t65 on `satml.tex` unchanged; t65 on the codex draft **57 pre-existing misses, none from rounds 32–33**.

## Layout — the body now overruns

45 pages, 0 overfull. The numbered body ends on **p. 13**: about 175 words (≈20 column lines) of
Related Work tail and the Conclusion sit above the Open Science heading. Rounds 32 and 33 added roughly
35 body lines (ladder, first bullet, chain paragraph, Assumption-1 sentence, escape sentence, Theorem 3
scoping, the checklist, and the round-32 pointers). Candidate trims, in the order I would take them,
with rough savings:

1. The "key distinction is between weak evidence and an impossible decision" paragraph after Table I
   (4 lines) — bullet 1 now says the same thing.
2. Bullet 3's closing sentence on the capacity-constrained attacker (2 lines) — checklist item 3 covers it.
3. "Prior work combines subsets of this chain ... every stage" (intro, 5 lines) — can lose 2.
4. Sec. V-A's pointer to the App. A-A construction (2 lines) — Sec. II-B now points there too.
5. Checklist item 5's order/keyed-hash sentence (2.5 lines) — App. D has it.
6. The Limitations pointer to `apptab:joint76rel` (1 line).

That is 13–15 lines; the rest would have to come from Sec. V-F or Related Work. Not applied — the
refit is a content decision (`paper-refit-at-the-end`).

## Round 34 (same day): four wording points

| # | Point | Action |
|---|---|---|
| 1 | "causal, state-free attacker" overstates observability; the paper itself calls these rows capability bounds | abstract: "victim-prior, state-free capability arm" / "the victim-prior and state-free arms"; bullet 3: "temporally restricted, state-free attacker" / "victim-prior and state-free arms"; for consistency the threat model now says "not as demonstrated online attacks" and the Conclusion "a temporally restricted, low-information attack". No attacker-sense "causal" remains (the host-feature sense — strictly causal features, causal accumulation — is untouched). Abstract is at exactly 250 words, the t65 cap |
| 2 | Fig. 6 caption carried revision-history residue | sentence deleted; panels stay B and C |
| 3 | Open Science: "on Zenodo for the camera-ready" | "and, if accepted, deposited on Zenodo by the venue's final-artifact deadline" (SaTML 2027 final artifacts are due 14 Jan 2027, before the mid-February camera-ready) |
| 4 | (optional) state Assumption 1 formally in the body | Sec. II-B now ends the premise sentence with $\mathbb E[e_i\mid\mathcal M_j]\le1$ for every benign $i\in G_j$, defining $\mathcal M_j$ inline |

Gates unchanged: t61 247/0, t68 2/0, t69 0 drift, t71 38/0, t72 10/0, t65 57 pre-existing misses on the
codex draft and 0 on `satml.tex`. Body still ends on p. 13 (about 180 words above Open Science); the trim
list above stands.

## 16 Sep 2026: abstract replaced (author text)

The author supplied a new abstract (191 words, five short paragraphs; the previous one sat at the
250-word cap). Applied verbatim apart from LaTeX conventions (`$k=1$`, `$20$`). It drops every dataset
count (78 of 79, 24 to 65) and keeps three claims the body supports: the 20-units-per-hypothesis rate
at `k=1` under the best cold-start allocation (Cor. 2 / `cor:budget`), the class-wide symmetric
impossibility (Thm. 3), and the roughly two-orders-of-magnitude joint-vs-per-alert cost gap (Sec. V-D,
5,650 vs 627,495 at the primary window, horizon-aware). "Campaign cost" is already the body's term
(Sec. V-D, VII). Two round-33 phrases are no longer in the abstract: "under attacker-controlled,
unbounded membership" on the Theorem-3 sentence, and any AIT number.

Gates: t61 247/0, t68 2/0, t69 0 drift, t71 38/0 (codex copy), t72 10/0. t65 on the codex draft
58 → 56 misses: the swap fixed two (`$20$` now shares its sentence with "LOND/e-LOND" and "$k=1$";
R14-3 abstract scope) and introduced none. Two R11-6 pins that required "78 of 79" IN the abstract were
made conditional (if the abstract carries an AIT number it must be the canonical one); satml.tex still
passes 0. One miss that appeared between 12 and 16 Sep is unrelated to the abstract: bullet 1 of the
introduction lost "an oracle lower bound" from the sentence carrying `$24$`…`$496$`, which t65 requires
(the costs are exact sequential-oracle costs). The three overfull warnings from `tables/joint76rel` (45 pt)
pre-date the swap. 45 pages both before and after.
