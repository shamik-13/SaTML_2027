# Reviewer-feedback worklist

Actionable items derived from external feedback on the first full draft, in the reviewer's own
priority order. Each item states: the reviewer's point, its **type** (wording / reframe / recompute
/ **new experiment**), what I verified in the current draft and artifacts, the concrete steps, data
availability, acceptance criteria, and effort. File anchors are into `paper/main.tex` unless noted.

**Governance reminder** (`docs/03_FROZEN_CLAIMS.md`): a claim may be *weakened* freely, but any item
that produces a *new headline number* (W2's recomputes at a new window, W3, W7, W9's new detector)
must land a numeric artifact + a `t45`-style consistency check and an audit pass before it enters the
paper. Wording/reframe items do not.

## Summary

| # | Item | Type | Effort | New data? |
|---|------|------|--------|-----------|
| W1 | Fix four statistical statements | wording | S | no |
| W2 | Make a **valid** window primary; label 0.85 as stress-test | reframe + recompute | L | recompute (data mostly exists) |
| W3 | Controlled testbed/synthetic padding-dilution experiment | **new experiment** | L | new |
| W4 | Sharpen C1 novelty ("known vs. established here") | wording/framing | S | no |
| W5 | Audit two formal statements (Prop 1 wording, "two proofs") | wording | S | no |
| W6 | Distinguish Surface A (evasion) from Surface B (structural) | framing | S | no |
| W7 | C2: grouping-independent fixed-unit coverage metric | **new experiment** | M | recompute (data exists) |
| W8 | Reduce breadth; one spine (validity→operational→attacker-facing) | restructure | M | no |
| W9 | Soften "two detectors"; add a competent + host-feature detector | wording + **new experiment** | L | new |

Suggested execution order: **W1, W5, W4, W6 first** (low-risk wording, no re-audit), then **W2** (the
biggest single review-risk reduction; uses mostly existing data), then **W8** (narrative), then the
three genuinely new experiments **W3, W7, W9** in parallel.

---

## W1 — Fix statistical statements (wording, do first)

**Reviewer point.** Several statements a statistics reviewer will seize on.

**Verified locations / current text:**
- `main.tex:90-91` — *"it acts on a statement of the form ``this alert is a true detection with
  probability at least $1-q$''."* FDR does **not** attach a per-alert posterior $1-q$; it controls
  the expected proportion of false discoveries among discoveries. The next paragraph defines
  FDP/FDR correctly, which makes the opening especially risky.
- `main.tex:103` — *"supplies the evidence without distributional assumptions"* — too loose for a
  paper whose empirical story is about loss of exchangeability/validity.
- `main.tex:289` — *"Every online procedure drives $\alphat$ down over a rejection-free run"* —
  contradicted later: ADDIS's level is pinned (never decays) and online e-BH's threshold is a
  history fixed point.
- `main.tex:292` — *"Two structural families cover every procedure we test."* — the escapes section
  shows ADDIS and online e-BH are **not** covered.

**Steps.**
1. Rewrite the opening to target the queue quantity, e.g.: *"A SOC cares not only about ranking
   quality but about how much of the alert queue is false; online FDR procedures directly target
   that quantity — the false discovery proportion."*
2. Change "without distributional assumptions" → *"distribution-free under the exchangeability of
   calibration and test scores"* (and cross-reference §Robustness/tail where exchangeability
   loss is exactly the failure mode).
3. Line 289 → *"Every procedure in the two families below drives $\alphat$ down over a
   rejection-free run"* (scope it to the covered families).
4. Line 292 → *"Two structural families cover four of the six procedures we test; the other two
   (ADDIS, online e-BH) escape, and locating them is part of the result (\cref{sec:escapes})."*

**Acceptance.** No sentence implies a per-alert probability; conformal claim is qualified;
feasibility framing is consistent with the escapes. Rebuild clean.

**Effort:** ~1h. **Re-audit:** none (weakening).

---

## W2 — Stop the invalid-e-value window (0.85) from reading as the headline

**Reviewer point (biggest review risk).** The spectacular results — 72 detections, the 5,202-flow
median padding attack, the ADDIS experiments — are all at **position 0.85**, whose benign firing
rate is **50.9× nominal**, so the evidence is *not a valid e-value there* (Table III/`tab:procedures`
says none of its FDP values are theorem-backed). A skeptic can say: *"the paper about statistical
guarantees gets its strongest results where its guarantee does not hold."* Make a **valid** window
primary; label 0.85 explicitly as a stress-test; use the cross-window results to show the attack
survives valid settings.

**Verified — the attack survives valid windows (this is the strong replacement):**
| window | validity | detections (e-LOND, seed 0/1) | median padding cost (flows, real level) |
|---|---|---|---|
| **0.55** | valid (1.07×) | 18 / 18 | **118 / 101** |
| **0.62** | valid | 13 / 12 | **72 / 69** |
| 0.85 | **invalid (50.9×)** | 72 / 71 | 5,202 / 6,802 |
(from `src/lib/out/t28b_reallevel.json`, `t21c_H6_positions.json`; matches the reviewer's 118/101 and 72/69.)

**What is currently pinned to 0.85 (needs relocating or dual-reporting):**
- `tab:procedures` (Full Experiment Matrices) — the escape/power comparison. `t21c` already has all
  five positions, so a 0.55 version is a **re-tabulation, no rerun**.
- `tab:frontier` (`main.tex:850`, Operational Evaluation, matched operating points) — 0.85 only.
  Source `t20_T8_matched` is 0.85-hardcoded → **needs a rerun at 0.55** (cheap, ~2 min).
- ADDIS state attack (`sec:state`, `apptab:addisstate`, Fig 4B) — 0.85 only (`t32_B1`, |C|=1,813,113).
  Reviewer accepts 0.85 as a stress-test here **if labelled as such** and paired with the valid-window
  attack survival; optionally recompute `t32` at 0.55 to show $B^\star$ scales as the closed form predicts.

**Steps.**
1. Adopt consistent labels throughout: **0.55 = primary / guarantee window; 0.85 = stress-test
   window (evidence not a valid e-value)**. Audit every "guarantee window" / "stress window" / bare
   "position 0.85" mention (24 lines flagged) and make the register uniform.
2. Move the **primary** procedure comparison and matched-operating-points to 0.55: re-tabulate
   `tab:procedures` from `t21c` at 0.55; rerun `t20_T8_matched` at 0.55 for `tab:frontier`. Keep the
   0.85 versions in the appendix as the stress-test.
3. Rewrite the abstract/§6 headline so the padding result leads with the **valid-window** numbers
   ("118/101 flows at the guarantee window, 72/69 at 0.62"), then presents 0.85 as the stress case.
4. State once, prominently, that 0.85 is retained because it is the instrumented stress window and
   because anti-conservative evidence makes its silence/non-detection results **conservative**
   (already argued in `sec:tail`) — but the guarantee-bearing claims rest on 0.55/0.62.

**Data/feasibility.** `t21c` (all positions) and `t28b` (all positions) already exist. Only
`t20_T8_matched` (frontier) and optionally `t32_B1` (ADDIS) need a rerun at 0.55 — both `[REAL]`,
minutes each with the cache warm.

**Acceptance.** The abstract, Table I, the procedure comparison, and the matched-operating-points
all lead with a valid window; 0.85 is labelled stress-test at every occurrence; the padding
result's headline numbers are the valid-window ones; ADDIS is explicitly framed as a stress-test.

**Effort:** ~1 day (recompute + reframe). **Re-audit:** yes for the new-window frontier/ADDIS numbers.

---

## W3 — Controlled testbed / synthetic padding-dilution experiment (highest-value new experiment)

**Reviewer point.** The single new experiment most likely to raise acceptance. The paper's own weak
point (`sec:paddingcost`, `sec:limitations`): LSPR23 has **no benign traffic on malicious host
pairs** (all 310 malicious pairs are 100% malicious), so the premise that an attacker can send
normal-looking padding to the attacked victim is argued **structurally from the flow-only feature
set**, not measured. A detector using host reputation / per-host baselines could break the transfer.

**Steps (modest controlled setup — no new 16M-flow dataset needed).**
1. Construct a controlled scenario: one attacker→victim service, a fixed set of genuine attack
   flows for the victim's episode, plus an increasing number $r$ of ordinary connections to the
   **same victim** (drawn to match a real benign service's flow-feature distribution).
2. Run the **actual trained detector** (`h_stream.fit_detector`, HGB) and the grouping+aggregation
   layer over the constructed episode; plot the group e-value / firing decision against $r$.
3. Show the group e-value dilutes as $\Ev(G)=\frac1{m+r}\sum e_i$ predicts, and that suppression
   occurs at the $r$ the closed form gives — i.e. the transfer the paper argues structurally is
   directly demonstrated for a flow-level detector.
4. (Ties to W9.) Repeat with a host-conditioned detector to show where the transfer **fails** — this
   is the honest scope boundary the reviewer wants.

**Data/feasibility.** No new capture required. Option A (recommended, self-contained): synthesize pad
flows by sampling feature vectors from a chosen benign service in the deployment window (the
`black-box` pool already identifies "the window's most common benign service") and inject them into a
target episode — this reuses `t28`/`t28b` machinery and the real detector, and is fully reproducible.
Option B (stronger, more work): a small real testbed (e.g. victim service + generated attack + benign
via a traffic generator), extract the same 32 flow features, run the shipped detector. Start with A;
present B as future work or add if bandwidth allows.

**Acceptance.** A figure/table showing measured group e-value vs. pad count for a flow-level detector,
matching the predicted dilution curve, with the pad flows drawn to look like ordinary victim traffic;
the structural argument in `sec:paddingcost` is downgraded from "by construction" to "confirmed by a
controlled experiment (flow-level features) and bounded by W9 (host features)".

**Effort:** Option A ~1–2 days; Option B ~1 week + testbed. **New artifact + audit** required.

---

## W4 — Sharpen C1 novelty ("known vs. established here")

**Reviewer point.** C1 can read as "obvious" — you write *"The argument is elementary"*
(`main.tex:287`). Bounded evidence vs. a shrinking threshold is elementary; the *contribution* is
specific and currently only surfaces in Related Work.

**Steps.** Add a compact **"Known vs. established here"** paragraph immediately before the C1
contribution (or as the first paragraph of §4). Enumerate what is new:
- the exact structural conditions (multiplicative / lag-sum families) under which common online-FDR
  procedures enter the silent state, and the classification of the two escape mechanisms;
- the **absorbing** nature and the cold-start deadline (first rejection unreachable);
- the max-min **calibration scaling** $\nCal\ge kT/\alpha_T-1$ tied to a security-scale horizon;
- that $\alpha$-**investing does not cure it** here, because earning wealth requires a rejection that
  the floor forbids, and the published fix equals e-LORD before the first rejection.
Keep "elementary" only for the one-line intuition, then pivot to "what is not elementary is…".

**Acceptance.** A reader reaching C1 sees the delta from known $\alpha$-death + conformal
discreteness before the theorem. **Effort:** ~2h. **Re-audit:** none.

---

## W5 — Audit two formal statements

**Reviewer point + verified locations.**
- `appendix_proofs.tex:13` (Proof of Prop 1): *"…is an initial segment $\{1,\dots,t^\star\}$, so no
  step after $t^\star$ is feasible…"*. Eventual non-increasingness does **not** rule out earlier
  gaps, so "initial segment" overclaims. The **body** statement was already softened
  (`main.tex` Prop 1: "feasibility ends at a last time after which no later step is feasible") — the
  appendix must match. **Fix:** replace "is an initial segment $\{1,\dots,t^\star\}$" with "has a
  finite last feasible index $t^\star$, beyond which feasibility cannot return".
- `appendix_proofs.tex:43` — *"We give two proofs; the second uses no domination result."* Route B is
  a **negatively-dependent special case**; it does not establish the full arbitrary-$x$ quantitative
  statement (Route A does). The main text already says "an independent special case", which is
  correct. **Fix:** reword to *"We give a full proof (Route A) and an independent special-case
  argument (Route B) that needs no domination result"*, and make the Route B heading say
  "special case" so it is not read as a second full proof.

**Acceptance.** Appendix Prop 1 matches the body; the padding-theorem appendix no longer claims two
full proofs. **Effort:** ~30 min. **Re-audit:** none.

---

## W6 — Distinguish "practical evasion" (Surface A) from "structural vulnerability" (Surface B)

**Reviewer point.** Surface A is a plausible low-footprint evasion (tens–thousands of flows, black-box
pool tracks the others). Surface B is conceptually strong but operationally very different: 203
precursor episodes ≈ **92M flows = 37.5× the window's volume**, which the paper already calls
"conspicuous". Make the distinction prominent so a security reviewer doesn't dismiss C3-B as a
glorified DoS.

**Steps.** In the abstract, §6 intro, and the discussion, frame explicitly:
- **Surface A** = a low-footprint alert-suppression **evasion** that works at valid windows.
- **Surface B** = a demonstration that the controller's **adaptive state is attacker-controllable**
  and can be forced into permanent failure — a *structural* property — while the measured
  global-silencing instance is **conspicuous in volume**, not a cheap attack.
Keep the existing honest "conspicuous, not unaffordable" language; elevate it from a caveat to the
framing. The coincidence result (101/147, state attack "comes free" with padding where the cap binds)
remains the bridge that makes B more than a DoS.

**Acceptance.** Abstract and §6 separate "evasion" (A) from "structural controllability" (B); B is not
presentable as a bandwidth attack. **Effort:** ~2–3h. **Re-audit:** none.

---

## W7 — C2: a grouping-independent semantic metric (new experiment, data exists)

**Reviewer point.** "Episode recall falls as the unit coarsens" is weakened because the **episode
definition changes with the bucket**, so recall denominators are not invariant. Malicious-flow
coverage is invariant in spirit but dominated by a few enormous episodes. Freeze a fine-grained
**fixed** ground truth and measure the fraction of those units covered by ≥1 alert as grouping
coarsens — then the denominator never changes.

**Steps.**
1. Define atomic units that do **not** change with the alerting grouping. Two options:
   - **(a) 5-minute host-pair attack episodes** (the finest bucket already computed in
     `t26_H4_5pos`) as the fixed ground truth.
   - **(b, stronger) red-team task steps** — 295 timestamped step submissions / 288 narratives in
     `src/lib/data/lspr23_attacknarratives.json`, already used by the alert audit (`t31_A2`), mapped
     to (src,dst,time) so an alert can be said to "cover" a step.
2. For each coarser alerting grouping, compute the fraction of fixed atomic units (a) or task steps
   (b) that are covered by at least one issued alert. Plot coverage vs. grouping coarseness with a
   **constant denominator**.
3. Present this as the hardened C2 "resolution cost", alongside (not replacing) the existing
   malicious-flow coverage, and note the volume-concentration caveat is now controlled for.

**Data/feasibility.** (a) needs only `t26_H4_5pos` plus a re-aggregation. (b) needs the narratives
JSON (present, 9.7 MB) and the `t31` alert↔step mapping logic. Both are new computation on existing
data — **no rerun of the detector**. New script + artifact.

**Acceptance.** A coverage-vs-coarseness result with a fixed denominator (atomic episodes and/or
task steps) that shows the resolution cost independent of the moving episode definition.

**Effort:** ~2–3 days. **New artifact + audit** required.

---

## W8 — Reduce breadth; let one story dominate

**Reviewer point.** The abstract packs the feasibility theorem, 6.5×10⁸, granularity, episode recall,
flow coverage, padding, five pools, controller-state, 203 precursors, 101/147, smoothing, restart,
asymmetric aggregation, analyst feedback, two detectors, 16.35M flows — it reads like three papers +
five robustness studies.

**Steps.**
1. Recast the spine as three linked beats: **(i) validity ≠ feasibility (C1); (ii) making the layer
   operational forces aggregation + adaptivity (C2 is the bridge); (iii) those mechanisms become
   attacker-facing (C3).** C2 is explicitly the bridge from C1 to C3, not a third independent result.
2. Trim the abstract to that spine + one quantitative anchor per beat; move the enumerations
   (five pools, 101/147, smoothing/feedback/contamination specifics) out of the abstract.
3. Demote smoothing, analyst feedback, contamination, and configuration transfer to clearly-secondary
   "robustness/boundary" status in the section ordering and the abstract, so they do not compete with
   the spine.

**Acceptance.** Abstract states the three-beat spine with one anchor each; robustness studies are
visibly secondary; C2 is framed as the bridge. **Effort:** ~half a day. **Re-audit:** none (wording).

---

## W9 — Soften "two detectors"; add a competent (and host-feature) second detector

**Reviewer point.** "Two detectors" oversells: Isolation Forest has **zero tail reach in all ten
configurations** (no attack flow exceeds the calibration maximum) → **zero detections** at the same
feasibility margin. That is a clean "feasibility necessary, not sufficient" demonstration but does
**not** independently validate either attack. If bandwidth allows, add a competent second detector
that actually detects — ideally one with **host-conditioned / endpoint-derived features** — to test
the boundary of the padding-placement claim (W3): maybe the attack gets more expensive or transfer
fails. A negative scope result there strengthens the threat model.

**Steps.**
1. **Wording (now):** reframe the Isolation Forest as a *feasibility-vs-sufficiency* demonstration,
   not a robustness detector; drop/soften "two detectors" in the abstract (`main.tex` abstract and
   Detectors subsection) to avoid implying independent attack validation.
2. **New experiment:** train a second **competent** detector that produces detections — e.g. a
   different supervised model, and separately one using **host-conditioned features** derived from
   the metadata (`h_meta` has `srcip/dstip/service/segment/ext/label_src/label_dst`; derive per-host
   rate/reputation/baseline features).
3. Run the padding-placement transfer (W3) against the host-feature detector and report whether the
   pad-scores-like-ordinary-traffic transfer **holds, gets more expensive, or fails**. Report the
   boundary honestly as a scope result.

**Data/feasibility.** Endpoint/service/segment metadata is available (`src/lib/h_meta.py`,
`/tmp/lspr_meta_cache`), so host-conditioned features are constructible without new capture.
The competent-detector training reuses `h_stream`. New modeling + artifact.

**Acceptance.** Abstract no longer implies two independently-validating detectors; a competent
detector produces detections at a valid window; the padding-placement claim has an explicit measured
boundary under host-conditioned features (transfer holds / degrades / fails).

**Effort:** ~3–5 days. **New artifact + audit** required.

---

## Cross-cutting notes for the executing agent

- **Reproducibility:** any new artifact goes in `src/lib/out/`, its generator as an importable
  `src/lib/*.py` with `main()` (mirror the `t28b_reallevel_padding` pattern), registered in
  `src/runner.py`, and wired into `src/tools/build_notebook.py` + `paper/make_appendix_tables.py`
  where a table is produced. `src/` must stay self-contained (no `proto/` references).
- **Consistency:** rerun `proto/t45_record_consistency.py` after any record edit; rerun the notebook
  paper-mode smoke test and `tectonic -X compile` after any paper edit; keep the **body at 12 pages**.
- **Frozen claims:** update `docs/03_FROZEN_CLAIMS.md` for W2/W3/W7/W9 (new numbers) with an audit
  note; W1/W4/W5/W6/W8 are weakenings/rewording and need no new audit.
- **Priority for acceptance:** W2 (de-risk the invalid-window headline) and W3 (measure the padding
  premise) are the two highest-leverage items; W1/W5 are cheap credibility fixes to do first.
