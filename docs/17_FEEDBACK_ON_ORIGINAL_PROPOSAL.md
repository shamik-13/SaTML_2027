# Feedback on `19_fdr_trustworthy_ids_research_idea.md`

Reviewed against the literature (Aug 2026) and against a working prototype
(`proto/`, results in `15_PROTOTYPE_FINDINGS.md`). Section numbers below refer to the
original document.

---

## 1. Overall assessment

The proposal is scientifically sound, well-organised, and its instincts are mostly right.
The pipeline it describes works. Its problem is not correctness but **positioning**: the
premise is 27 years old, the method is established, and the three findings it nominates as
headlines (§20 Findings 1–4) had each already been published, two of them within the last
18 months.

More importantly, the document already contains the two strongest ideas in the project —
§14 (event- vs incident-level) and §3.7 (adaptive attackers) — but ranks them as an
afterthought and a single paragraph respectively, while promoting to headline status the
one claim that the prototype went on to refute (§17, calibration drift). The revision is
mostly a **re-ranking of the proposal's own content**, not a replacement of it.

---

## 2. What worked — kept unchanged

| § | What | Why it held |
|---|---|---|
| §6 | Statistical formulation (`s_t → p_t → H_t → R_t, V_t, FDP_t`) | Correct as written. The conformal construction is the right primitive; nothing needed fixing. |
| §7 | Clean separation of detector from decision layer | The right experimental design, and the reason the study is interpretable at all. Everything downstream depends on it. |
| §8 | Chronological train/calibrate/stream protocol, no random splits | Correct, and has strong precedent — TESSERACT (USENIX Sec'19) formalised these constraints for security ML. Cite it rather than re-deriving. |
| §14 | Event-level vs incident-level distinction | **The single best idea in the document.** Under-ranked — see §4 below. |
| §3.7 | Adaptive attackers manipulating the alerting procedure | Second best idea. Under-ranked — see §4. |
| §15.3 | AIT-ADS used as *alert-level* control (existing IDS alert → statistical layer → analyst) | The best dataset instinct in the proposal. It is the honest deployment position: a filter over an existing SIEM, not a new NIDS. |
| §21 | "A strong negative result is also useful" | Correct research posture, and it is what saved the project when the drift hypothesis failed. |
| §24 | Minimal experimental version | Right instinct. This is essentially what we ran, and it settled the core questions in an afternoon. |
| §26 | Nominal guarantee vs empirical control | The most intellectually honest passage in the document. Promoted from a risk note to the paper's framing. |

---

## 3. What didn't work — and why

### 3.1 Novelty (the main problem)

**§1–2, the premise.** "SOCs consume alerts, not AUROC; the operational quantity is the
fraction of alerts that are false" is Axelsson's base-rate fallacy argument (CCS 1999 /
TISSEC 2000), which showed that `P(intrusion | alarm)` — i.e. `1 − FDP` — is the binding
quantity and that the base rate makes it brutally hard. Presenting this as the novel
reframing invites a one-line rejection. It is the *motivation*, not the contribution.

**§5 RQ2 and RQ3.** Already answered. Rebjock et al. (AISTATS 2022) proposed online FDR
rules for anomaly detection specifically to handle *exceedingly rare alternatives* and
*serially dependent test statistics* — the two conditions RQ3 nominates as open. They had
to propose new rules because the established ones fail, which means §20's Finding 3
("some procedures lose control under dependence") is a known result, not a finding.

**§6 + §11, the pipeline.** conformal p-values → LORD → time-averaged FDR on a stream
already exists (C-PP-COAD, 2025), in healthcare and O-RAN rather than security. And
conformal calibration *in security ML* is well established: Transcend (USENIX Sec'17),
Transcendent (USENIX Sec'22), FIRCE and FADES (2026) all do conformal p-values on
security streams with rolling calibration and drift-triggered recalibration — which is
§18's mitigation list.

**§16.1, prevalence stress testing.** CALIBURN (2026) is the closest neighbour: streaming
NIDS, operator-specified alert budgets instead of validation-set threshold tuning,
conformal risk control, and *its central claimed finding is regime-dependence on attack
prevalence*. It explicitly applies no multiple-testing correction — so the FDR version is
genuinely unclaimed — but "the FDR version of CALIBURN using Rebjock's rules" is a
workshop paper, not a main-track one.

*Process note:* the novelty check should have preceded the experimental design. Roughly
40% of the document (§5, §11, §16, §18, §20) plans work whose conclusions are already in
print.

### 3.2 Method

**§10 vs §11 is not a comparison.** Given a fixed score function, *every* alerting rule is
a threshold sequence, and online FDR is one particular adaptive schedule. Comparing "LORD
at q=0.05" against "`s_t > 0.5`" picks two arbitrary points on one ROC. As specified, the
entire empirical section is unfalsifiable. Fix: report only at matched analyst budget, at
matched realised FDP, or as a full Pareto frontier.

**§10 omits the baseline that would make the method unnecessary.** In any operating SOC,
analyst dispositions arrive as delayed labels. Given those, you can estimate FDP directly
and hold it at target with a trivial feedback controller — no multiple-testing theory, no
exchangeability, no dependence assumption. This baseline plausibly wins at any realistic
label latency, which would bound the honest scope of the whole programme to the
label-scarce regime. It must be in the table.

**§18 is an undirected sweep.** Six mitigation mechanisms with no principle for choosing
among them. The dependence problem is in fact *doubly* broken — conformal p-values sharing
a calibration set are PRDS (enough for BH, per Bates et al. 2023) but not independent,
which is what LORD/SAFFRON/ADDIS assume — so the e-value branch is the only one where the
stated guarantee holds. Derive the mitigation set; don't sweep it.

### 3.3 Data

**§12's limitation is backwards.** It says benchmark labels are "much cleaner than
real-world labels". Measured label corruption is **7.53%** on CSE-CIC-IDS2018 and 6.67% on
CIC-IDS2017, with some attack classes above 75% (Liu et al., CNS 2022; Engelen et al.,
WTMC 2021), and the NF-* NetFlow rebuilds inherit it. Against a `q = 0.05` target this is
not a limitation, it is an **identification failure**: the quantity being measured is
smaller than the error in the instrument measuring it. Label error also concentrates in
ambiguous flows — exactly the ones near a detector's threshold — so the rate *among alerts*
is worse than the global rate.

**§3.4 contradicts §15.** §3.4 asserts `P(attack) ≪ 1%`. The chosen datasets run at
~22% (CIC-IDS2017), ~64% (UNSW-NB15) and ~10% (LSPR23). Reaching 0.01% requires
subsampling, which destroys the temporal dependence that §3.1–3.2 nominate as the other
central claim. **You cannot obtain realistic base rates and realistic dependence from the
same benchmark**, and the proposal does not acknowledge the trade.

**§15.5 argues against its own inclusions.** It concedes that LANL's ground truth is not
exhaustive enough to estimate false positives and that WitFoo's labels come from a vendor
correlation pipeline. Both are disqualifying for a paper whose headline metric is FDP.
They should have been dropped in the same paragraph that identified the problem.

### 3.4 Scope

§5 + §9 + §10 + §11 + §15 + §16 multiply out to 4 detectors × 6 procedures × 6 baselines
× 6 datasets × 5 prevalences × 6 stress axes. That is a three-paper programme. SaTML
allows 12 pages of body text.

---

## 4. What the prototype changed — findings unavailable from reading alone

These are the substantive reasons for the revision, as distinct from the positioning
problems above.

**(a) §20 Finding 4 (calibration drift → invalid evidence → FDR violation) is refuted.**
This was slated as a main result. On real AIT testbed NetFlows with a 5-day chronological
split, conformal p-values were anti-conservative by only **1.3–2.0×**, and *conservative*
(0.86–0.93) at the 10⁻²–10⁻³ levels; rolling calibration gave 1.10–1.31. Drift is real but
modest. A section built on it would have been built on sand. Also note the original claim
was close to tautological: the chronological protocol deliberately breaks exchangeability,
so *some* violation is guaranteed a priori. The publishable question was always
quantitative, and the quantity turns out to be small.

**(b) §20 Finding 3 (dependence breaks control) dissolves rather than confirming.** Using
conformal *e-values* and averaging within incidents, validity under arbitrary dependence
follows from linearity of expectation alone — no exchangeability, no PRDS, no mixing
condition. Dependence, the proposal's most-emphasised obstacle (§3.1, §3.2, §3.6, §16.2),
is a non-problem once the evidence type is chosen correctly. The binding constraint is
elsewhere.

**(c) §14's idea is far stronger than the proposal claims for it.** §14 argues incident-level
evaluation "may expose important gaps between statistical validity and operational
usefulness". The prototype says something much harder: event-level online FDR on security
streams is **arithmetically infeasible**. On LSPR23 (16M flows), event-level control would
need a calibration set of **640 million** benign flows under the best-case γ — and 3×10¹³
under the conventional γ ∝ j⁻¹·⁶. Incident-level, at LSPR23's real 288 red-team campaigns,
needs **11,520**. On the same stream, recall goes from 0.000 to 1.000 and structural
silence from 100% to 0%. §14 is not a robustness check; it is the only formulation that
can work at all.

**(d) A failure mode absent from the proposal.** The conformal p-value floor `1/(|C|+1)`
collides with α-wealth decay so that after a rejection drought the procedure **cannot
reject any input regardless of its score**, while continuing to report perfect FDR control.
With `|C| = 10⁴` this happens after **19 events**. A detector that provably cannot detect
is a trustworthiness failure no classifier metric can express, and it is caused by the
guarantee itself.

**(e) Two further findings that replace the drift story.** (i) The evidence ceiling the
procedures require corresponds to the smallest calibration rank, where the deployed
e-value is anti-conservative ~37% of the time with a p99 of 4.1–4.9× — and this **does not
improve as `|C|` grows** from 10⁴ to 10⁶. (ii) The procedures operate at p ≈ 10⁻⁶;
137,832 held-out flows produced 2 events below 10⁻⁵ and none below 10⁻⁶, so validity at
the operative quantiles cannot be audited without ~10⁷–10⁸ events.

**(f) One dataset dependency is worse than assumed.** AIT-ADS (§15.3), the best idea in
the dataset plan, ships **unlabelled**. Labels must be reconstructed from AIT-LDSv2 attack
windows — a 137 GB dependency and 3–5 days of work. It should be deferred, not because the
idea is wrong but because the schedule cannot absorb it.

---

## 5. Disposition of each section

| § | Disposition |
|---|---|
| §1–2 Core idea, premise | **Demote to motivation.** Cite Axelsson 1999. |
| §3.1–3.6 Security complications | **Keep as background; stop treating dependence as the obstacle.** e-values handle it. |
| §3.7 Adaptive attackers | **Promote to a core contribution.** Best SaTML fit in the document. |
| §4 Hypotheses | Rewrite: hypotheses 2 and 3 are refuted / already known. |
| §5 RQ1 | Keep, but only under matched-budget comparison. |
| §5 RQ2, RQ3 | **Largely answered in the literature.** Reframe as the feasibility envelope. |
| §5 RQ4 | Keep. |
| §5 RQ5 | **Cut the detector zoo** to two. Conclusions were never detector-specific. |
| §6 Formulation | Keep; add the p-value floor and the assumption ledger per procedure. |
| §7 Pipeline | Keep unchanged. |
| §8 Chronological protocol | Keep; cite TESSERACT. |
| §9 Detectors | Cut from 4(+3) to 2. |
| §10 Baselines | Keep 1–5, **add the disposition-feedback controller.** |
| §11 Procedures | Cut to 5; add SupLORD (FDX at stopping times) and e-LOND (arbitrary dependence). |
| §12–13 Metrics | Keep; **add structural-silence rate**; report every FDR number beside a power number. |
| §14 Event vs incident | **Promote to the central contribution.** |
| §15.1–15.2 | Keep, using corrected label releases. |
| §15.3 AIT-ADS | Right idea, **defer** — unlabelled, 3–5 days to fix. |
| §15.4 LSPR23 | **Promote to primary.** 288 labelled multi-step campaigns, ready to use. |
| §15.5 LANL, WitFoo | **Cut**, for the reasons §15.5 itself gives. |
| §16.1 Prevalence | Keep, demoted; CALIBURN has the FPR analogue. Use incident-preserving subsampling only. |
| §16.2 Burstiness | Keep, redesigned as order-permutation at fixed evidence multiset. |
| §16.3–16.5 | Fold into two axes; drop calibration-age from 5 points to 3. |
| §16.6 Attack families | Keep — the prototype gives it a mechanism (weak-signal families are suppressed: recall 0.41 at μ=1.5 vs 1.00 at μ=3). |
| §17 Calibration validity | **Demote to a subsection.** Empirically 1.3–2.0×, not catastrophe. |
| §18 Adaptation strategies | Replace the sweep with a derived choice: e-values plus horizon-aware γ. |
| §19 Headline figure | Replace with the feasibility envelope (min `\|C\|` vs stream length). |
| §20 Findings 1, 2, 5, 6 | Keep. **Finding 3 is known; Finding 4 is refuted.** |
| §21 Success criteria | Keep. |
| §22 C1–C4 | Rewrite: C1 and C3 as stated are not contributions; C2 and C4 are execution. |
| §23 Structure | Rework to 12 pages. |
| §24 Minimal version | Keep — it worked. |
| §25 Phase 2 | Cut by ~60%. |
| §26 Technical risk | **Promote to framing.** The best passage in the document. |
| §27 Novelty risk | Correct diagnosis; the seven listed items were not sufficient mitigation. |
| §28–30 | Rewrite around the impossibility result. |

---

## 6. Three process points for next time

1. **Run the novelty check before designing experiments.** Four searches would have found
   Rebjock, CALIBURN, C-PP-COAD and Transcendent, and would have redirected §5, §11, §16
   and §18 before they were written in detail.
2. **Budget the measurement error of the headline metric first.** The proposal targets
   `q = 0.05` on datasets with 7.53% label corruption. That check belongs on page one of
   the plan, not in §12's limitations.
3. **Always include the baseline that would make the method unnecessary.** Here, a feedback
   controller on analyst dispositions. If it wins, that is the most useful result the
   project can produce; if it loses, the contribution is real. Either way you need it.

## 7. What the proposal got right that mattered most

It contained both winning ideas (§14, §3.7), the correct honest framing (§26), the right
dataset instinct (§15.3, §15.4), and the discipline to specify a minimal first experiment
(§24) — which is what made the core questions answerable in a single afternoon. The
revision re-ranks the document; it does not replace its thinking.
