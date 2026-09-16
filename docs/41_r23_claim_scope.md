# Round 23 — claim scope, compression, reading order, layout (2026-09-05)

Source: sixteen-point reviewer feedback on `paper/satml.tex` after round 22. No experiment was run
and no number changed; every edit is wording, placement, a heading, or figure presentation.
Pre-edit draft: scratchpad `satml.tex.pre_r23` (session-local); edit script `apply_r23.py`
(31 whitespace-tolerant replacements, each required to match exactly once).

## Validity judgement, point by point

| # | Feedback | Valid? | What was done |
|---|---|---|---|
| 1 | Body says both horizon-aware windows had "no observed false discoveries"; Table I shows FDP 0.009 at 0.62 | **Yes, and the reviewer's fix was itself wrong.** t73 `detections` = `fired & ismal`, i.e. TRUE detections; at 0.62 horizon-aware there are 107 true + 1 false = 108 rejections. "107 alerts" would be false. | Body: "105 true detections … no observed false discovery, and 107 at the secondary alongside one false discovery, realised FDP 0.009"; Table I column renamed **"true det."** (not "alerts"), caption defines it; abstract says "212 true detections under horizon-aware spending". t65 R21-6 now derives FP per cell from t73. |
| 2 | "guarantee-bearing windows" overclaims | Yes | "primary and designated secondary windows" (abstract), "primary and secondary windows" (App. E-C). Negative check added. |
| 3 | Table I "total" must be an upper bound in the caption | Yes | Caption rewritten per feedback; the body's joint-minimum explanation stays. |
| 4 | "attacker-controlled" → "attacker-influenceable" | Yes | Sec. V heading; Fig. 1 label (drawn by `src/lib/figures.py`, re-rendered); t72 pins the label. Sec. IV's "partly attacker-controlled" is accurate and kept. |
| 5 | LLM disclosure is a TODO | Yes | Written: editorial refinement, generation of measurement/evaluation/consistency-checking code, read-only audits of experiment code; not part of the method, pipeline operation or labelling; validated via unit tests, replay, closed-form cross-checks and the consistency gates. Names Claude Code and Codex CLI; no cost figure. **Authors must confirm.** |
| 6 | Abstract −20–25%; "family is suppressed" → alert is | Yes | 354 → 286 tokens (−19%). Every gated qualifier kept (max-min clause, "horizon-free allocations cost more", canonical, oracle lower bound, LSPR23 scope). Theorem sentence now "sufficiently many zero-evidence additions drive an attained alert below threshold". |
| 7 | Remove meta-editorial sentences | Yes | Intro promise deleted (t65 R18 check inverted); "Four terms carry…" → "We use four terms to distinguish…"; "Two further properties…" folded into the Thm 3 note; "The scope of the replay is exact" → the reviewer's sentence; "which are not a contribution" deleted. |
| 8 | Third contribution list is ambiguous | Yes | Reviewer's text, with "on LSPR23" restored on the fixed-multiplier clause (that result does not transfer to AIT). |
| 9 | Compress the Thm 3 note; move vacuity/equivalence/witness to App. A | Yes, mostly | One paragraph in the body; the equivalence, the `F≡1` vacuity example and the all-`M` witness moved into `app:attain`. Kept one clause "vulnerable precisely when it can fire at all" — that is the memorable statement of the equivalence. |
| 10 | Sec. V-E: lead with replay, one ordering sentence, fix "3 and 18 bracket 0–10" | Yes; the bracket claim was arithmetically wrong | Order is now costs → replay (3/3, 11/11, 105/105, 107/107) → scope → one ordering sentence. Fifty-order details moved to App. E-A with "canonical's three lie within the distribution; first-flow's eighteen exceeds all fifty". Body keeps a half-clause that canonical is the 0.62 maximum (round-19 disclosure). |
| 11 | One stable replay phrase; per-window recall | Yes | "per-alert real-flow replay" throughout; the host-context arm no longer says "replaying the append causally". Recall now per window from t73: horizon-free 0.01 / 0.03, horizon-aware 0.38 / 0.27 (the reviewer's "≈0.38" was wrong for 0.62). Gated. |
| 12 | "never blocked" vs the cap; "any cap a defender would set"; "invisible" | Yes | "Within the unbounded-membership model of Theorem 3, spending allocation cannot eliminate padding … Admission control changes that model"; "far below every cap we evaluate"; "cheap and non-exceptional by episode volume"; conclusion "cheap and unremarkable in volume". |
| 13 | Fig. 4 bigger; Table II to Sec. VI, three columns | Yes | Fig. 4 is a two-column `figure*` anchored at Sec. V-C so it lands at the top of p.8; re-rendered at `WIDE` with scaled fonts. While there: the CDF grid stopped at 10⁴ (the horizon-aware curve looked truncated at 78%) and the legend hid part of that curve — grid now reaches the axis limit, legend sits above the curves. Mitigation table moved to the head of Sec. VI, three concise columns; its details already live in Sec. V-D and App. E-E. **Numbering swapped: `tab:main` is now Table II, `tab:defenses` Table III.** |
| 14 | Shorter Table I / core-table captions | Yes | Both shortened; `ρ` values kept in Table I's caption (feasibility of the uniform arm is the precondition for the comparison). |
| 15 | Trim Scope and Limitations | Yes | Totals/front-load/keyed-hash sentence → App. B conventions (with `apptab:blindkey` pointer); host-conditioned order → the table and the V-F point of claim ("under first-flow order"); contamination pointer → App. F opener, so `sec:contamination` stays referenced. |
| 16 | Open Science "cannot disagree" too absolute | Yes | Reviewer's text, keeping "figure-drawing code is part of the library" (t72 pins it) and the tense/existence phrases t61 pins. |

## Gate changes (wording-only re-anchoring; two checks strengthened)

- **t65** — R14-2: "212 … true detections under horizon-aware"; R21-6: FP counts per cell derived
  from t73, the pair-wide "no observed false discoveries" forbidden, Table I header must say
  "true det."; R18: attainment equivalence checked in `app:attain`, intro promise must NOT return;
  R22: replay-scope sentence re-anchored; R16: "spending allocation cannot eliminate padding";
  new R23 block: per-window recall from t73, no "guarantee-bearing window", influenceable heading
  + no "attacker-controlled membership", theorem stated on the alert, Table I caption's upper bound,
  Theorem-3-model vs admission-control wording, V-E reading order, fifty-order details after the
  appendix start, no meta-editorial residue, LLM section has no TODO. `_flatS_nc` is now defined
  next to `_flatS`.
- **t72** — Fig. 1 label pinned in `src/lib/figures.py`.
- **t71** — ledger label "Per-alert real-flow replay …".

## State after the round

t61 205/0 (123 retired), t65 185/0, t68 2/0, t69 0 drift (26 objects), t71 20/0, t72 10/0.
Build (tectonic): 39 pages (appendix grew by the moved paragraphs), 0 overfull, 0 undefined.
Fig. 4 top of p.8 (two columns); core table top of p.9; mitigation table top of p.10; **body ends
p.12 line 8 of 87** (was line 10 of 92) — inside the limit, headroom unchanged at ~0.9 page.
Refit still deferred to the end. The notebook's cached Fig. 1/Fig. 4 PNG outputs predate the
relabel/resize and should be refreshed when the notebook is next executed (no nbconvert here).
