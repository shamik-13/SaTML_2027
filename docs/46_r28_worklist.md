# Round 28 — citation precision, membership qualification, ρ definition, notation (feedback points 2–13)

Feedback received 6 Sep 2026 (points 2–13 of a numbered list; point 1 was not included). Validated
against the source before planning:

| Point | Validation | Decision |
|---|---|---|
| 2 [10]–[14] cluster | `refs.bib` titles: [10] online FDR for anomaly detection in time series; [11] context-aware online conformal anomaly detection; [12] online multi-layer FDR; [13] CALIBURN, operationally calibrated streaming IDS (conformal risk control); [14] conformal novelty detection at the decision boundary — the reviewer's characterisations fit the titles. Cited at Sec. I :174 and Related Work :1086 with the same over-broad sentence | ACCEPT both sentences as proposed; **authors re-read the five papers before freezing the bibliography** |
| 3 membership qualification | Sec. I :197 "creates a class-wide padding vulnerability"; Conclusion :1116 "every alert-capable symmetric rule" | ACCEPT both replacements |
| 4 VI-B implication | :992 "no other procedure from the covered families under uninterrupted operation" | ACCEPT the procedure–sequence-pair wording |
| 5 ρ definition | eq. (6) and its lead-in; Corollary 2 says "write ρ … as in (6)" | ACCEPT: define ρ_p as the allocation-optimal (horizon-uniform) ratio, give ρ_p(γ)=M c_{0,p} min γ_t ≤ ρ_p, state once that ρ denotes the horizon-uniform ratio throughout; Corollary 2 writes ρ = ρ_{e-LOND} = Mα/T. t65 pin "ρ_p ≥ 1 is exactly cold-start feasibility through T" kept as a substring; t69 re-freeze (statement text changes, proof does not) |
| 6 Corollary 2 summary + title | contribution 3 :228; title :736 | ACCEPT reviewer's sentence and title "Horizon-uniform feasibility ratio as a dilution threshold" (t69 re-freeze) |
| 7 notation | "Jseq" occurs in NO source file (pdftotext flattens the subscript) — no action; Σ_t r*_t appears at :721, :769, :778, :798, :821, Terms :1412, joint table; "independent sum" at :770, :814, :821, :1028, :1412, joint notes | ACCEPT: index set 𝒟 (baseline true detections) and "per-alert sum" everywhere; t65 pins at :1106, :1211, :1213 re-anchored |
| 8 Terms table ADDIS row | :1415 "which moves no state of its own" | ACCEPT reviewer's clause |
| 9 two zero-firing bounds | 1.5e-4 at :857 (20,000 sample), 845,691 at :869, 3.5e-6 in VII-B and App. E | ACCEPT: one explanatory sentence in V-E; VII-B wording "the full-pool zero count gives a one-sided 95% upper bound" |
| 10 Table V placement | current build: Table IV (main) and the Sec. VI heading on p.10, Table V (defences) at the top of p.11 above Sec. VI-B's continuation, Sec. VII heading on p.11 below it | Try `\FloatBarrier` before Sec. VII first, as asked; keep only if the body stays on p.12; otherwise keep the current placement (already before Sec. VII) and record why |
| 11 eq. (7) lead-in | :589 "plus one, falls in the same proportion" | ACCEPT: eq. (7) becomes |C|_min + 1 = kT_group/c_0 with the reviewer's lead-in; the t65-pinned phrase "minimum calibration size over pre-committed spending allocations" stays inside it |
| 12 abstract split | 234 words; t65 caps at 235 | ACCEPT the two sentences; cap raised to 240; pins on the old sentence re-anchored |
| 13 appendix packing | 41 pages; cosmetic | Check the last pages once; no structural change. PDF eXpress: author item |

Budget: the additions are ~9 body lines against zero slack (body ends at the foot of p.12) — cuts first,
recorded below. Gates re-anchored: t65 (abstract cap and three joint/sum pins, R23 impossibility
phrase), t69 (Corollary 2 title and ρ clause). Blind confirmation run at the end of the round.

## Execution log

**Applied 6 Sep 2026 (points 2–12).**
- 2: both cluster sentences replaced with the reviewer's per-work characterisation (Sec. I keeps the
  "we do not assume commercial SOCs deploy this stack" thought out; it was ours, not the reviewer's).
  Author item stands: re-read the five papers before the bibliography freezes.
- 3: Sec. I contribution summary and the Conclusion now condition the vulnerability on an
  attacker-co-occupiable key and unbounded membership and say "symmetric e-merging".
- 4: VI-B's first implication speaks of procedure–sequence pairs under their stated decay conditions.
- 5: eq. (6) is defined as the allocation-optimal (horizon-uniform) ratio; ρ_p(γ) = M c_{0,p} min γ_t ≤ ρ_p
  stated; "Throughout, ρ denotes this horizon-uniform ratio". Corollary 2 writes ρ = ρ_{e-LOND} = Mα/T
  and is retitled "Horizon-uniform feasibility ratio as a dilution threshold" (6). t69 re-frozen; the
  provenance entry records that hypotheses, conclusion and proof are unchanged.
- 6: contribution 3 carries the reviewer's summary sentence for Corollary 2.
- 7: Σ_{t∈𝒟} r*_t with 𝒟 = baseline true detections in the taxonomy paragraph, Table III (caption and
  header), Sec. V-D, VII-B, the Terms table and the joint appendix table; "independent sum" → "per-alert
  sum" everywhere. "Jseq" occurs in no source file (pdftotext flattens the subscript) — no action.
- 8: Terms table ADDIS row carries the reviewer's clause.
- 9: Sec. V-E attributes 1.5e-4 to the 20,000-flow sample and 3.5e-6 to the full 845,691-flow pool;
  VII-B says "the full-pool zero count gives a one-sided 95% upper bound".
- 10: no `\FloatBarrier` needed in the current build: Table V renders at the top of p.11 above Sec. VI-B's
  continuation, and Sec. VII begins below it on the same page (Sec. VI starts p.10). A `\FloatBarrier`
  before a `table*` would force a page break and leave a half-empty column; recorded rather than tried.
- 11: eq. (7) reads |C|_min + 1 = kT_group/c_0 with the reviewer's lead-in and follow-up sentence; the
  t65-pinned phrase "minimum calibration size over pre-committed spending allocations" sits inside the
  lead-in.
- 12: abstract split as proposed; 230 words (the split shortened it), cap stays 235.
- 13: appendix tail checked: p.41 (last page) holds Tables XLIV and XLV with the usual end-of-document
  white space; nothing to pack. PDF eXpress: author item.

**Budget.** The additions cost ~16 lines against zero slack. Paid with unpinned trims and merges (Sec. I
paras 1 and 3, the cluster tail, contribution 3's joint clause; II-C canonical-order merge; II-D seeds
and stress sentences; III intro "four terms"; III-B ρ tail and "one scale"; III-C "direction",
per-window counts; IV opener and coverage sentence; V-C proof sentence; V-D lead-in and horizon-free-cap
clause; V-E selection rule and ordering clause; V-F appendix pointer; VI-A cap sentence; Related Work
batching and Krönert tail; Fig. 4 caption) and Figs. 1 (0.78), 2 (0.74), 4 (0.78). Body ends p.12 at
layout line 52 of 57. Two gate pins moved with the text (t65 R19-1 count word restored as "two of the
five are zero"; "membership" added to the no-split hyphenation list). Gates: t61 240/0, t65 194/0,
t71 34/0, t68 2/0, t69 28 objects re-frozen / 0 drift, t45 268/0, t70 ok.

**Blind confirmation (one codex run, `confirm_r28.md`).** Eleven of twelve items FIXED with no new
inaccuracy; the twelfth (the citation cluster) is PARTLY: the reviewer's characterisations of [11]
(farzaneh2025coad, "combines conformal p-values with online FDR-controlled anomaly detection") and [14]
(gao2026boundary, "conformal novelty detection with batch FDR control") are not verifiable from the
bibliography titles alone ("Context-Aware Online Conformal Anomaly Detection with Prediction-Powered
Data Acquisition"; "Reliable Conformal Novelty Detection at the Decision Boundary"). The wording is the
reviewer's own, so it is kept; but this sharpens the author item: **when re-reading [10]–[14], confirm
specifically that [11] uses an online FDR controller and that [14] uses BH-style batch FDR control; if
either does not, fall back to the title-level description** ("online conformal anomaly detection";
"conformal novelty detection at the decision boundary").

**CLOSED, 8 Sep 2026 (round 31).** Both verified against the arXiv abstracts. [11]
(`farzaneh2025coad`, arXiv:2505.01783) builds "active conformal p-value statistics" that "support online
testing with formal FDR control" — conformal p-values plus an online FDR controller, as our sentence
says; its abstract names no specific procedure, and neither does ours. [14] (`gao2026boundary`,
arXiv:2601.02610) opens "Novelty detection via conformal p-values and BH procedure provides
distribution-free global false discovery rate (FDR) control" — conformal novelty detection with
BH-style batch FDR control, as our sentence says. No fallback needed; both characterisations stand.
