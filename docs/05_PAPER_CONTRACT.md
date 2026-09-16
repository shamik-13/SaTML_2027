# Paper Contract

**IEEE SaTML 2027.** Abstract 22 Sep 2026, paper 29 Sep 2026. Claims are bounded by
`03_FROZEN_CLAIMS.md`; numbers by `04_EXPERIMENTS_AND_FINDINGS.md`; structure by
`20_satml_paper_outline_and_manuscript_skeleton.md`; LaTeX in `paper/`.

> **The workplan closed on 27 Aug 2026 — all twelve experiments are done.** The contributions
> below are final, subject to the scope conditions in `03_FROZEN_CLAIMS.md`. Four late
> experiments changed a claim rather than confirming one (§4.37, §4.38, §4.40, §4.42); check
> the frozen list rather than this file's wording where they disagree.

## Submission rules, verified against <https://satml.org/call-for-papers/> on 27 Aug 2026

- **Template is mandated**: `\documentclass[conference]{IEEEtran}`, default 10pt and page
  geometry. *"Using a different template, or modifying font size, margins, or spacing to fit
  more content, is grounds for desk rejection."*
- **12 pages of BODY TEXT.** References and appendices are unlimited and do **not** count, and
  neither do the Open Science / Ethical Considerations / LLM sections, which sit before the
  references. But *"reviewers are not required to read appendices"* — nothing load-bearing may
  live only there. The earlier "12 pages + appendices" shorthand understated the budget.
- **Double-blind.** No names or institutions; cite our own prior work in the third person.
- **Open Science is MANDATORY**: name the artifacts released, or justify why not. Anonymised
  artifacts due **3 Oct 2026** (three days after the paper). **Acceptance is conditional** on
  final artifacts reaching zenodo.org by 14 Jan 2027.
- **Ethical Considerations** is optional; include it — this paper describes working attacks.
- **LLM Usage Considerations** is mandatory if LLMs were used.
- ORCIDs and Author Certification via HotCRP by the **abstract** deadline.
- Full date list and build instructions: `paper/README.md`.

---

## 1. Title

**When Guarantees Go Silent: Feasibility and Attackability of Online Error Control for ML
Intrusion Detection**

*Fallbacks:* "Finite Evidence, Long Streams" (technical) · "Flows Are Not Alerts"
(granularity-first).

## 2. Thesis — one sentence

> Online statistical error guarantees for ML intrusion detection face a three-way tension
> between finite evidence resolution, security alert granularity and adversarial robustness:
> fine-grained control becomes infeasible at long security horizons, coarsening the alerting
> unit restores feasibility at a measured cost in episode-level resolution, the aggregation
> that coarsening requires creates a low-cost evasion surface — and the procedures that escape
> the feasibility boundary do so by conditioning their spending state on the observed evidence,
> which hands the adversary a second, exactly priced attack surface.

## 3. Problem statement

A SOC cannot act on a detector's score. It can act on "this alert is a true detection with
probability ≥ 1 − q". Online FDR control promises exactly that over a stream of alerts, and
conformal e-values promise it without distributional assumptions. Putting the two together
gives a *statistical trust layer*: detector → conformal evidence → group aggregation → online
error controller → SOC alert. This paper asks whether that layer survives contact with
security scale, security units of work, and an adversary who knows it is there. It does not
survive intact, and the three ways it fails are structural rather than incidental.

## 4. Contributions

**C1 — A feasibility theorem for online error control under finite-resolution evidence, with
its boundary.** Threshold conformal evidence is bounded by `M = (|C|+1)/k`; rejection needs
`E_t ≥ 1/α_t`; for two structural families of `α_t` the set of feasible times in a
rejection-free run is finite and the state absorbing. Retaining feasibility over horizon `T`
needs `|C| ≥ kT/w₀ − 1`: 6.4×10⁸ at LSPR23 scale, 3.5×10¹⁰ for a day at 10k flows/s. Stated
with its counterexamples: ADDIS and online e-BH escape, by two different mechanisms, and each
escape has a measured price. *(H1 + boundary conditions.)*

**C2 — The granularity–feasibility tradeoff, measured.** `required |C| = kT/w₀ − 1` holds
exactly in every grouping family, so coarsening the alerting unit buys feasibility on a known
exchange rate. What it costs is resolution: across five families × seven bucket widths,
malicious-**flow** coverage is constant at 0.508–0.519 while **episode** recall falls from
0.518 to 0.226. This is a domain-specific trustworthy-ML result, not an implementation
choice — security ML predicts on flows and security operations act on episodes. *(H2.)*

**C3 — The trust layer as an attack surface, at two levels, one of them new.**
*Within-hypothesis:* a theorem — for any τ > 1 no symmetric e-merging family that attains τ is
τ-padding-robust — plus a real-data attack costing 1–134 flows, unchanged across five padding
pools including one chosen without any detector access. *Across-hypothesis:* the procedures
that escape C1 do so by conditioning the spending index on the observed evidence, and that
index is adversarially reachable. For ADDIS the budget has a closed form, verified against the
implementation: `B = 202` precursor episodes leave all 152 rejections intact, `B = 203` leaves
none, permanently. For 101 of ADDIS's 147 detections the cheapest padding that suppresses the
alert *already* advances the index, so the two surfaces are one operation. *(H3.)*

## 5. Research questions

**RQ1 — Feasibility.** Under what combinations of evidence resolution `k`, calibration size
`|C|`, stream horizon `T` and online procedure can a security alert still be rejected at all?
→ C1; §4.13, §4.15, §4.20, §4.21, §4.23, §4.24, §4.26.

**RQ2 — Granularity.** How does changing the alerting unit from flows to deployable episodes
affect feasibility, recall and operational resolution? → C2; §4.9, §4.29.

**RQ3 — Attackability.** Can an adversary manipulate the *composition* of a statistically
controlled alert, or the *sequential state* of the controller, to suppress detection?
→ C3; §4.16, §4.17, §4.30, §4.33.

**RQ4 — Operational value.** What does formal online error control provide against
matched-budget thresholds and feedback-based alert controllers? → §4.14, §4.19, §4.20;
answer: every method is on the achievable frontier at its own budget, and what error control
removes is the operator's *choice* of point — γ moves recall by 0.188 where a twenty-fold q
sweep moves it by 0.088.

## 6. Threat model

- **Goal.** Suppress the alert on the adversary's own activity; secondarily, delay it or
  silence the controller for everyone.
- **Capability.** The adversary generates network flows. It controls the grouping key
  `(SrcIP, DstIP, time bucket)` by construction — ordinary connections to the same host in the
  same hour — so no crafting and no detector access are needed to *place* traffic in a group.
- **Knowledge, three settings.** *White-box:* λ, τ, k, `|C|` and controller state.
  *Grey-box:* procedure and parameters, not `|C|` and not the state — the admissible precursor
  size is a `τ/λ`-wide interval, so a ±33% estimate of `|C|` suffices, and unknown state costs
  only 36× over-provisioning. *Black-box:* no detector access; sends ordinary traffic of a
  chosen volume from common services.
- **Not assumed.** No model access, no gradient access, no training-set poisoning, no ability
  to modify labels, no ability to drop or reorder other parties' flows.
- **Cost metric.** Padding flows emitted. Reported as a lower bound where detector output is
  used to estimate it (`03_FROZEN_CLAIMS.md` C.4).
- **Out of scope.** Feature-space perturbation of the adversary's own flows; the attacks here
  need none.

## 7. Figures and tables — seven, and no more

| # | Item | Content | Source |
|---|---|---|---|
| **F1** | System model | flow → detector → conformal evidence → grouping → online controller → SOC alert, with the two attack surfaces marked: within-group padding, across-time state manipulation | schematic |
| **F2** | Feasibility envelope | minimum `\|C\|` against deployment horizon `T`, curves for LOND, LORD++, e-LOND/e-GAI, online e-BH, ADDIS; LSPR23 and 10k-flows/s markers | §4.13, §4.21 |
| **F3** | Granularity–feasibility tradeoff | x = bucket width; panels: feasibility margin, episode recall, malicious-flow coverage; five grouping families | §4.29 |
| **F4** | The two attacks, one axis | padding flows against P(episode suppressed) for five pools; and precursor count `B` against P(target detected) with the `B* = 203` cliff | §4.30, §4.33 |
| **T1** | Procedures and assumptions | procedure · evidence type · spending index · horizon knowledge · dependence assumption · does the C1 theorem apply · is the guarantee valid on this evidence · observed power | §4.20, §4.26 |
| **T2** | Main real-data results | detector · grouping · procedure · alerts · FDP (label and audited) · episode recall · flow coverage · feasibility margin · structural silence | §4.15, §4.20, §4.32 |
| **F5/T3** | Operational frontier | online error control vs fixed threshold vs matched-budget threshold vs feedback controller, on one achievable score frontier | §4.19, §4.20 |

**Appendix tables** (do not count against the seven): the 152-alert adjudication (§4.32), the
46-flow extreme-tail listing (§4.31), the cap-policy sweep (§4.25), the (q, γ) sweep (§4.24),
the Bates cost curve (§4.26), the horizon-misspecification sweep (§4.20).

## 8. Data and methods

- **LSPR23**, Locked Shields Partner Run 2023: 16,353,511 flows, 1,644,599 malicious (10.06%),
  161.5 h, 101 columns. Timestamp-sorted; 90% of flows fall in the final 25.6 h, so window
  positions are chronological slices, not random splits. **No flow→campaign labels** — units
  are *episodes*.
- **Red-team task record** (`lspr23_attacknarratives.json`): 288 narratives, 83
  machine-readable compromise reports over 39 IPv4 addresses, 295 timestamped step
  submissions. Used as **external ground truth for the alert audit only**, never as a feature.
- **AIT NetFlows**: calibration-drift measurement only (§4.4).
- **Detectors**: HistGradientBoosting (supervised) and Isolation Forest (unsupervised), the
  latter to show the feasibility margin does not depend on the scores.
- **Evidence**: threshold conformal e-value at rank k, `e = ((|C|+1)/k)·1{K ≤ k}`.
- **Aggregation**: arithmetic mean over the episode (`Σe/n`); cap policies in §4.12, §4.25.
- **Procedures**: LOND, LORD++, e-LOND, SAFFRON, ADDIS, online e-BH, e-LORD, e-SAFFRON,
  mem-e-LORD. Two spending sequences throughout: `γ ∝ j^−1.6` (no horizon) and `γ = 1/T`
  (max-min optimal, **oracle**).
- **Repetition**: five window positions × two detector seeds. Every number an interval or a
  min/median/max, never a single draw.
- **Verification**: every result blind-audited before it entered the record; four independent
  audits found ~30 defects, two of which had inverted a headline conclusion.

## 9. Exclusions — stated in the paper, not silently

- No second dataset with genuine campaign labels (none exists as a drop-in; three candidate
  routes each cost 3–5 days and each adds a caveat). Five window positions are presented as
  five quasi-independent deployments of one exercise, which is weaker and is said so.
- No detector zoo; two detectors, and the reason is given.
- No SAFFRON/ADDIS constants derived beyond what the escape argument needs.
- No AIT-ADS label reconstruction.
- No incident-level or campaign-level claims.
- No correction of LSPR23's labels; the direction of the error is stated instead.

## 10. Explicit non-claims

Reproduced verbatim from `03_FROZEN_CLAIMS.md` §D — ten items, all of which appear in the paper
in a "what this paper does not claim" paragraph in the discussion, not buried in limitations.

## 11. Writing order

1. Problem formulation → 2. feasibility theorem (C1) → 3. padding theorem (C3a) →
4. experimental setup → 5. results → 6. discussion → 7. introduction → 8. related work →
9. abstract.

The introduction goes last: the contribution is now much sharper than the project's original
motivation, and writing it first would import the old framing.

## 12. Reviewer objections already retired, with the pointer

| "…" | Retired by |
|---|---|
| your conclusions are an artefact of one classifier | §4.22 — a second, unsupervised detector, identical margin, zero detections |
| you picked the most extreme rank | §4.23 — k ∈ {1, 10, 10², 10³}; k = 1 is the only feasible one |
| the boundary is an artefact of a strict error target | §4.24 — twenty-fold q sweep; improvement is exactly linear and no faster |
| one grouping definition | §4.29 — five families × seven bucket widths |
| you picked the cap that makes it look worst | §4.25 — mean → p50 → p90 → p99 → p999 → max |
| you only broke the procedures you chose to implement | §4.20 — SAFFRON, ADDIS, online e-BH, e-GAI; two escape, and that is in the result |
| you identified a known problem and ignored its known solution | §4.26 — Bates calibration-conditional p-values applied and priced |
| why not modern e-value boosting | §4.28 — `b* = 1` exactly for two-point e-values |
| your FDP is measured against labels you never validated | §4.27, §4.32 — 0.0042% inconsistency bound, then 152 alerts adjudicated against the red team's own record |
| your headline window violates the validity condition and you don't know why | §4.31 — localised to three named host pairs, enumerated flow by flow, with the two rival explanations tested and the residual uncertainty stated |
| the ADDIS escape means the problem is solved | §4.33 — the escape is itself an attack surface, with a closed-form budget |
