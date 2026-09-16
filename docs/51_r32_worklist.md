# Round 32 worklist — reviewer feedback on `paper/satml_codex_edit.tex`

Five points, worked in the reviewer's recommended order: App. H-C → Corollary 2 diagnostics →
constructive example → joint-run reliability → consistency pass. Each was validated against the draft
and the artefacts before anything was changed. Experiment record: `docs/04` §4.74.

## Validation

| # | Point | Verdict | Evidence |
|---|---|---|---|
| 1 | App. H-C: `E[Ev|M_j] ≤ 1 < 1/α_t` does not imply a benign group cannot be rejected; "fragmentation fails analytically" overreaches | **valid, both** | the expectation bound permits large realisations (the reviewer's 100-w.p.-0.01 example); the binomial rejection probability depends on `m`; nothing in the repo establishes a fragmentation *detection* result (t8 is a `[SIM]` proto-era stage with no artefact in `src/lib/out`) |
| 2 | Sec. V-F tested a proxy (a baseline non-attacker alert) instead of Corollary 2's premise (`max_{j∉A} Ev_j ≥ T/α`) | **valid, and the paper's sentence was wrong for `santos`** | `t77` measures the premise: `santos`'s horizon-aware non-attacker alert has Ev = 0.34 T/α and fires at R = 9; it fails on `russellmitchell` (1.50) and both `shaw` cells (a non-attacker episode attains the ceiling) |
| 3 | No "valid but suppressible" construction for the e-LOND mean mechanism; Sec. II-B presents the member-level premise as necessary | **valid** | App. A-A had the assumption and lemma only; Sec. II-B said "every benign member must remain e-valid" |
| 4 | Table V's sums of medians hide per-trajectory reliability | **valid; p95 not p90** | `t76` stores median/p5/p95/min/max/mean per cell, not the 100 trajectories, so the 95th percentile is the upper quantile available without a re-run |
| 5a | App. E-F says regrouping preserves the evidence of the *unperturbed* stream | **valid — prose error, code correct** | `t75.check_padded_stream` asserts `Ev == Ev_expect`, the padded vector the attacker was run on; `t76.validate_regroup` asserts `Ev == tr.ev_all()` likewise |
| 5b | `apptab:joint` (Table XXXVI in the reviewed build; now XXXVII) "benign trunc." defined as truncated episodes | **valid** | `t75` computes `(benign_arity > n).mean()`; nothing is truncated (Limitations already said so) |
| 5c | Sec. III-A "restore an alert without a rejection" | **valid** | a rejection is what the absorbing state precludes |

## Executed (12 Sep 2026)

1. **App. H-C** rewritten: pathwise `S/(m+r) ≤ S/m` at a fixed level; the expectation bound named as
   insufficient (with the reviewer's example); fragmentation narrowed to "expected group evidence is
   unchanged", with `Pr(Ev ≥ θ) = Pr(Binomial(m, φ) ≥ ⌈mθ/M⌉)` shown to depend on `m`; "fail analytically"
   removed.
2. **`src/lib/t77_cor2_premise.py`** (new stage, 226 s, reads the AIT cache): rebuilds the ten `t76`
   streams, asserts every stored baseline, records `max_{j∉A} Ev_j / (T/α)`, episodes at or above `T/α`,
   and per non-attacker alert whether it clears the `R = 0` level at its position. New table
   `apptab:cor2diag` (+ generated prose) joins that with `t76`'s no-pool counts, pad firing shares and
   residual alerts. Sec. V-F's premise sentence replaced by the measured statement (3 of 10 cells fail;
   `santos` does not; the multiplier fails where the premise holds because unpaddable own episodes raise
   `R` — the "multiplies every own episode" hypothesis is the one that breaks); horizon-free
   `⌊ρ⌋+1` labelled a heuristic transfer in the body, caption and prose.
3. **App. A-A** gains the Uniform(0,1) construction (nCal = 99, k = 1, T = 4, α = 0.05; threshold 80;
   attack e = 100 → detected; one appended score −1 flow → mean 50 → suppressed; null
   `E[e | M_j] = 1` exactly by exchangeability; checked numerically, 2×10⁶ draws give 0.992). Sec. V-A
   points to it; Sec. II-B now says the member-level premise is a sufficient condition, not a necessary
   one.
4. **`apptab:joint76rel`** (+ generated prose): per organisation, spending rule and attacker arm, P(all own
   alerts silenced), median/p95 residual count, median/p95 flows. Finding: residual counts are
   deterministic given the organisation (58 of 60 cells p5 = p95); P(all) = 1.00 in 15 of 16
   deployment-pool flow cells, and the exception (`russellmitchell` horizon-free) has exactly one survivor
   in every trajectory. Pad sampling moves cost (p95/median up to 1.90×), not outcome. Table V's caption
   and Limitations point to it.
5. **Consistency pass**: E-F regroup sentence states what is asserted unchanged vs. what must match the
   independently computed padded stream (generator + `t75` docstring); "benign trunc." → "benign > n"
   with a corrected note (generator); Sec. III-A absorbing-state wording.

## Gates (run against `satml_codex_edit.tex` / `.pdf` via the `T61_TEX` / `T65_TEX` / `T68_PDF` overrides)

| gate | before | after |
|---|---|---|
| t61 numbers | 241 consistent, 0 inconsistent | 0 inconsistent, `joint76rel` and `cor2diag` registered (canonical; t77 carries `config.orders`) |
| t65 wording | crashes: anchor `\subsection{Is the result an artefact` no longer exists in the codex draft; with the anchor patched, **58 pre-existing misses** | same 58, no new one (`diff` of BAD lines empty) |
| t68 layout | — | 2 consistent |
| t69 theory freeze | (pointed at the codex draft) 0 drift, 28 objects | unchanged — no frozen object touched |
| t70, t72 | green | green |
| t71 claim ledger | (pointed at the codex draft) 38 consistent | unchanged |

The 58 t65 misses predate this round: they are wording pins from earlier reviewers that the codex
rewrite moved or rephrased (e.g. `tab:main`'s caption naming seed and order, the c = 10 "smallest
evaluated" phrasing, the 674/674 purity count, the knowledge assumption on the non-oracle claim). They
need the style-pin/accuracy-assertion triage of `gate-vs-reviewer-conflict`, not this round's fixes; the
four listed are accuracy assertions and worth restoring.

## Layout

44 pages (was 43), 0 overfull boxes. The Conclusion still ends on p. 12, but the **Open Science heading
moved from p. 12 to p. 13**: the body gained about six lines (Sec. V-A pointer, Sec. V-F premise
paragraph, Sec. II-B qualifier, Table V caption and Limitations pointers). If the Open Science section
must stay inside the 12 pages, the cheapest trims are the Sec. V-A pointer sentence (2 lines) and the
Limitations pointer (1 line); the Sec. V-F paragraph is the substantive fix and should stay.

## Not done, by choice

- No `t76` re-run for a 90th percentile (the stage did not retain trajectories; a re-run is 1–3 h and
  would only add a quantile the 95th already bounds).
- No admission-control implementation (the reviewer did not make it mandatory; the narrowed claim
  stands).
