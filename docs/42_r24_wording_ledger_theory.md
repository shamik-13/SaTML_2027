# Round 24 — seven wording corrections, a claim-ledger audit, and a specialist theory audit

Three-part reviewer worklist. Part 1 was applied as given; parts 2 and 3 were run as blind
`codex exec` audits — two independent runs per brief, then three further verification runs on the
repairs, each of which found something the previous one did not.

## Part 1 — seven surgical wording corrections (all applied)

| # | Where | Change |
|---|---|---|
| 1 | abstract | "no admissible observation can alert" → "…can trigger an alert" |
| 2 | contributions | "E-merging theory fixes the arity of the rule; an adversary that controls group membership does not" → "analyses each rule at a fixed arity; in our threat model the adversary can increase the arity of its own hypothesis". Aligns with Fig. 1 and the Sec. V title, which already say *attacker-influenceable*. |
| 3 | abstract | volume cap scoped to "the evaluated configurations … high-cost horizon-aware regime but not the horizon-free regime"; closing sentence now names the property actually proved impossible: *arbitrary-padding invariance*, "supplied outside the alert-capable symmetric e-merging class" |
| 4 | Sec. III-B | "no larger release of the same kind fixes it" → "so scaling calibration and deployment in the same proportion leaves it unchanged" (the invariant actually established) |
| 5 | Sec. IV | "the same proportionality again, on a third axis" → "coarsening the key therefore changes feasibility, alert semantics and the cost of exploitation at once"; "the keys a SOC actually uses" → "the operational keys we evaluate" |
| 6 | Sec. V-D | "expensive and conspicuous where it is strong" → "much larger — and therefore more amenable to volume-based admission control — in the horizon-aware regime" (episode volume is what was measured) |
| 7 | Sec. VI | "None removes the tradeoff" → "Each evaluated response shifts the tradeoff rather than removing it", with benign-traffic disruption added as the fourth price |
| 8 | `refs.bib` | ref. [12] rendered "aIT-LDSv2.0". IEEEtran's `format.note` lowercases the first character of a mid-sentence note; brace-protecting `{AIT}` fixes it. **The `.bbl` on disk was stale — tectonic keeps intermediates in memory, so verify in the PDF, not the `.bbl`.** |

## Part 2 — claim-ledger audit (two blind runs, `briefA.md`)

Both runs agreed on one finding; each found one the other missed. Three real defects:

* **Table I's `Total` named the wrong population.** `t73_uniform_padding.py` builds
  `det = fired & ismal`, so `total_pad` sums TRUE detections only. At 0.62 horizon-aware there
  are 107 true detections **and one rejection outside that sum**, so "an upper bound on the cost
  of jointly suppressing *the alert set*" named a set the column does not have. Caption now names
  the true-detection set and says the false discovery is excluded.
* **`tab:defenses` labelled a canonical result first-flow.** Its caption said "the cap and
  weighting sweeps run under first-flow order". True for the aggregation-cap sweep (`t25_H5`, no
  order arm) and the weighting sweep (`t36_E3`, no order arm), but the **per-host-pair volume
  cap** comes from `t74_defended_replay.json`, whose `config.order` is `keyhash` — canonical.
  This is exactly the defect the order registry exists to stop, sitting in an explicit caption
  that overrides the global convention.
* **The AIT transfer never disclosed its rejection count.** The canonical flow-only arm issues
  **83 rejections for 79 true detections** — four false discoveries, pooled realised FDP 0.048
  (first-flow: 89/85, 0.045). The body reported only true detections. Now disclosed at the point
  of claim and in `apptab:aitorder`'s caption, both derived from the artefact by the generator.
  The abstract's "78 of 79 detected episodes" also became "78 of 79 **true detections**", the
  paper's own noun.

`t65` gained R24-2/3/4 (each injection-tested against its own revert) and the R24-5 slogan pin.
`t71` gained three ledger rows the reviewer asked for and the ledger did not carry — the
3 → 105 detection contrast, the 105/105 and 107/107 horizon-aware replay, and the volume-cap
curve — each with its arm, its per-alert-not-joint scope, and its false-discovery status.
`docs/38_claim_ledger.md` regenerated: 13 claims.

**Declined.** Both auditors also asked for the seed/order/window to be restated inside individual
sentences (e.g. the abstract's 3 → 105). The paper carries a global convention in the body
(Sec. II-D) and in `app:conventions`: *unless a sentence, caption or table says otherwise, every
measured number is seed 0, canonical order, at the stated window, horizon-free*. Restating it per
sentence would cost the page budget and weaken the convention. The convention is what makes the
`tab:defenses` caption a defect rather than an omission: an explicit label that contradicts it.

## Part 3 — specialist mathematical audit (two blind runs + three verification runs)

Five briefs: `briefB.md` (quantifiers/scope, x2), `briefC.md` (verify the repairs, x2),
`briefD.md` (finite-support notation sweep), `briefE.md` (verify again, x2). **Six frozen objects
changed; `t69` re-frozen with provenance.**

* **`thm:family2` was missing `w_0 >= 0`.** The proof multiplies `gamma_t <= Gamma(Delta)` through
  by `w_0`. Counterexample at `w_0 = -1`: the displayed bound fails. Same defect *shape* and the
  same object as round 15's missing `ceil < infinity`.
* **`cor:budget`'s "necessary *and* sufficient" did not say what for.** Both auditors independently
  read it as sufficiency for an *actual* rejection and called it the paper's worst error — the
  ceiling decides feasibility, not detection power. The statement now says so inline. The proof
  was already correct.
* **`gamma_t = 1/T` read as a constant sequence has infinite mass**, so it sits outside the
  mass-<=1 class the max-min claim optimises over. Now `gamma_t = T^{-1} 1{t <= T}` in the
  corollary and at the max-min claim, with the shorthand defined once in Sec. II-A.
* **`prop:donation`'s reason for `d = 0` was FALSE.** "`R_{t-1} = 0` on such a prefix leaves `g`
  constant" — `g` is not constant, it rises with the donated wealth (1.000 -> 1.053 at
  `delta = alpha = 0.05`, verified numerically). `d = 0` needs a constant *bound*, which the
  preceding display supplies. **This survived rounds 13 and 15.**
* Two clauses claiming the horizon-uniform arm refutes the `d = 1` decay condition became false
  under finite support (`t*gamma_t = 0` past `T`) and were deleted; the `gamma_{2^j} = 2^-j`
  counterexample carries the point alone.
* `prop:closure`'s proof cited `cor:budget` for a `gamma ~ j^-1.6` computation that belongs to
  `thm:family1`.
* Non-frozen prose: the e-LORD reparameterisation no longer claims `omega in [0,1]` gives
  `thm:family1` everything it asks (it gives non-negativity and the budget, **not** the decay);
  `tab:taxonomy`'s caption now says "Covered by" is coverage of a *(procedure, sequence)* pair;
  the abstract names the pair too.
* **The slogan.** "a symmetric rule is vulnerable precisely when it can fire at all" ->
  "**vulnerable at precisely the alert thresholds it can attain**". At a fixed `theta` the
  equivalence {attains theta} <=> {not theta-padding-robust} is exact, but "can fire at all" reads
  as operational firing on the deployed evidence support, which is strictly stronger —
  `app:attain`'s own `(1/2)mean` witness attains `theta` and can never fire. The conclusion's
  one-way variant gained "at any threshold it can alert on".

**Process note.** Every verification round broke text written to fix the previous round: C1 broke
the counterexample I added for B (`t*gamma_t -> inf` is false for a sparse-support sequence — it is
`limsup`), D1 found the finite-support notation had made two other sentences false, and E1 found
the pre-existing `g`-constancy CRITICAL. Findings only changed *kind* — from "this is false" to
"this cross-reference points at the wrong theorem" — at E2. That is the stopping rule.

## State

Body ends p.12 (Conclusion p.12 l.1, Open Science p.12 l.72); 0 overfull, 0 undefined refs.
`t45`, `t65` (188), `t68`, `t69` (26 objects, re-frozen), `t70`, `t71` (13 claims) all green.
The page refit remains deferred.
