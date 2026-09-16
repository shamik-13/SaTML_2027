# Round 22 — novelty positioning and claim hierarchy (2026-09-04)

Source: reviewer feedback on `paper/satml.tex` after the round-17 horizon-aware experiments
(t73/t74). No experiment was run and no number changed; every edit is wording, placement or a
heading. Pre-edit draft: scratchpad `satml.tex.pre_r22` (session-local); the edit script was a
list of whitespace-tolerant replacements each required to match exactly once.

## The objection

The round-18 fix (prior art credited AT each theorem, per three mock reviewers) was executed by
opening each contribution note with what was *not* new — "What is new here. The phenomenon is
not." / "Not the inequality." / "the step from there is short" / "The same inequality is already
in the literature" — and the ethics section said an adversary reading the component papers would
reach the same conclusions. A reviewer could lift those sentences verbatim into a novelty
rejection ("combines known finite conformal resolution, known alpha-death, and a short corollary
of an existing e-merging result"). The intro also said "Our contribution is to connect them",
i.e. synthesis.

## The stance adopted

Security/trustworthy-ML *systems* paper with formal results. One sentence: bounded evidence
limits the reporting lifetime of arrival-time controllers; grouping restores reporting by reducing
the horizon but makes membership in the attacker's own hypothesis influenceable; no alert-capable
symmetric e-merger can eliminate the resulting padding vulnerability; controller design changes
the cost of exploitation, not the incompatibility. Reviewer-memory phrase: **allocation prices the
attack; symmetric aggregation creates the vulnerability.**

Three affirmative contributions replace "feasibility / bridge / padding+transfer":
1. a deployment-level feasibility law (Thms 1–2 + Cor 1; the Sec. IV exchange folded in);
2. a cross-arity security impossibility (Def 1 + Thm 3);
3. an operational cost-and-mitigation boundary (both spending regimes, replay, transfer, cap).

## What changed, and what I deliberately did NOT do

| Feedback item | Applied | Judgement |
|---|---|---|
| Title → "When Statistical Trust Layers Go Silent: …" | yes | the paper's own term; "Online Guarantees" invited the online-FDR-theory novelty question. One-line revert if disliked. |
| Abstract: contribution-forward, shorter | yes, ~370 → ~330 words | kept every gated qualifier the reviewer's draft dropped: "max-min-optimal horizon-uniform", "horizon-free allocations cost more", "canonical", "oracle lower bound", the LSPR23 scope of the state-free result. Replaced 23–33 and the secondary median with the cost curve 24 → 2,946 and the replayed counts fourteen + 212 (both artefact-derived). |
| Intro: drop "we connect them" | yes | affirmative framing + three contributions; "Each formal result below states…" kept (round-18 promise). |
| Thms 1–2 note | yes | prior work → delta → consequence; Huo still cited at the theorem. |
| Cor 1: move Krönert to Related Work, state 20/40 once | **partly** | the duplicate 20/40 prose is gone (the frozen corollary keeps it). Krönert keeps a one-clause attribution AT the claim ("algebraically related … Sec. VIII states how the two objects differ") because three mock reviewers demanded attribution at the claim; the full different-object-and-consequence comparison is in Related Work. |
| Thm 3 note + heading | yes | "Symmetric alerting and arbitrary padding invariance are incompatible"; Vovk–Wang credited as ingredient; attainment ⟺ vulnerability kept (that IS the contribution). |
| Co-primary regimes | yes | defined together in Sec. II-A; Sec. III-C "the two regimes answer different questions"; Sec. V-C split so the cost curve has its own heading "A stronger controller raises the attack price, not padding robustness" (`sec:costcurve`). Conventions now name horizon-free as the default regime, because the AIT transfer and all appendix sweeps ARE horizon-free only — "co-primary" is honest for the LSPR23 cost analysis, not for the whole evidence base. |
| Remove rebuttal language in ordering/replay | yes | facts kept (median one detection, 19/50 none, 0.62 canonical = ensemble max, replay scope on the unperturbed trajectory, service-level pool); the Clopper–Pearson residual-risk simulation moved to App. E-C. "end-to-end demonstration" → "per-alert real-flow replay at the original controller level". |
| Volume cap as mitigation boundary | yes | VI-A heading "Theorem 3 localises where a defence must act"; "the only mitigation that bites" gone from abstract and table; residual (5/105, 14/105) and benign truncation (1.0–3.4%) kept. |
| Conclusion not ending on Assumption 1 | yes | t61 AUDIT-C5 re-scoped: the conclusion asserts no FDR guarantee, so needs no conditionality; the gate now also asserts Sec. II-B and VII-A still carry it. |
| Ethics | yes | "would reach the same conclusions" removed; compositional-consequence framing. |

## Gate changes (wording-only; no value check weakened)

- t65: registry — `$23$--$33$` moved to body-only (context: canonical); `$24$` and `$212$` added
  for the abstract, both recomputed from t73/t74. R14-2 now requires both regimes' replayed counts
  in the abstract, derived from t48 and t74. R18 anchors re-pointed at the new passage openers and
  the Krönert comparison split into an at-claim check and a Related-Work check. New R22 checks:
  every concession/rebuttal phrase is forbidden by string (comments stripped first); the three
  contribution headings exist; the two regimes are defined and priced together; the replay is
  named per-alert and "end-to-end demonstration" is gone.
- t61: AUDIT-C5 as above.
- t68 caught two hyphen-split breaks the new sentences introduced ("repair-to-|attack" across
  p1→p2, "unper-|turbed" across a column): rephrased the first, appended `unperturbed` to the
  standing `\hyphenation` list for the second.

## State after the round

All gates green: t61 205/0, t65 174/0, t68 2/0, t69 0 drift (26 objects), t71 20/0, t72 9/0.
Build (tectonic): 38 pages, 0 overfull, 0 undefined references. **Body now ends on p.12 (line 13
of 61)**, up from p.11 line 43 — inside the 12-page limit with ~0.8 page of headroom, down from
~1.25. Refit still deferred to the end per the standing rule.
