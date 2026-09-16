# Round-27 blind audit reports (verbatim, one codex run each, 6 Sep 2026)

## Audit A

CRITICAL — paper/satml.tex:289 — Fig. 1 claims grouping inherently makes hypotheses attacker-facing, contradicting the abstract/Table I’s attacker-influenceable/co-occupiable-key condition; qualify the causal chain by attacker control and unbounded membership.

MAJOR — paper/satml.tex:139 — The abstract’s 20-flow, 24/2,946-flow, “both windows,” and 78/79 results lack reproducibility scope (window identities, allocation/controller parameters, seed/replay regime); attach those qualifiers or point precisely to a scoped table.

MAJOR — paper/satml.tex:205 — The feasibility criterion is said to depend on only \(\nCal,k,T\), although the delivered theorem also requires an uninterrupted/no-restart regime and controller/spending conditions; state those assumptions and relevant controller parameters.

MAJOR — paper/satml.tex:166 — “e-values permit FDR control under arbitrary dependence” is presented unconditionally, while Table II says the empirical e-LOND interpretation requires valid e-values and unverified group-local A1; make the statement explicitly conditional and distinguish theorem-level from empirical control.

MAJOR — paper/satml.tex:215 — The operational contribution asserts broadly scoped empirical mechanisms and mitigation effects (“evaluated windows,” transfer, exact costs) without naming datasets, windows, order, seed, or regimes; add those scopes to each claimed result.

MAJOR — paper/satml.tex:133 — “arrival-time controller,” “absorbing discovery horizon,” “cold-start feasibility,” “horizon-aware/free,” “canonical order,” and “arity” are used before an opening-level definition; add brief operational definitions before the contributions.

MINOR — paper/satml.tex:288 — “shrinking level” overstates the delivered result, whose theorem explicitly does not require monotone spending; say eventual tail decay on rejection-free runs instead.

MINOR — paper/satml.tex:191 — The novelty claim that prior work treats the ingredients separately sits beside citations to prior composed conformal/online-control systems; specify the missing finite-horizon/padding analysis in each relevant prior work.

section clean: no — the figure overclaims attacker-facing membership as an automatic consequence of grouping.

## Audit B

MAJOR — paper/satml.tex:304: \(K_i\) has no tie rule or admissible range for \(k\); with tied scores, “rank from the top” can invalidate the claimed e-/p-value validity. Define \(1\le k\le|\Cal|+1\) and use randomized or conservative tie handling.

MAJOR — paper/satml.tex:334: \(\gamma_j\propto j^{-1.6}\) leaves its normalization unspecified, although the stated prefixes and calibration requirements depend on it and the theorems require a budgeted sequence. State the exact normalized sequence (e.g. \(j^{-1.6}/\zeta(1.6)\)).

MAJOR — paper/satml.tex:507: \(\rho_p\ge1\) is claimed to be exactly cold-start feasibility for any plotted controller, but it is equivalent only for the horizon-uniform allocation; for general \(\gamma\), feasibility depends on \(\min_{t\le T}\gamma_t\). Restrict the claim to uniform spending or redefine the ratio using that minimum.

MINOR — paper/satml.tex:436: Theorem 1 and its proof divide by \(\alpha c_g\ceil\) without assuming \(\alpha>0\), \(c_g>0\), and \(\ceil>0\) (and do not state that the level multiplier is nonnegative). Add these hypotheses.

MINOR — paper/satml.tex:449: \(\Delta\) is used without being defined as the current consecutive rejection-free gap, while the proof and absorption conclusion require precisely that meaning. Define it in the theorem statement.

section clean: no — the feasibility ratio is overstated as an exact criterion outside horizon-uniform spending.

## Audit C

MAJOR — paper/satml.tex:603 — Labels the 3→46 detections and 24→496 median-cost comparison “canonical,” but paper/tables/grouping.tex:10 says its grouping counts use first-flow order; provide canonical-order grouping results or relabel/use one ordering throughout.  
MAJOR — paper/satml.tex:652 — Claims the result rules out any valid symmetric rule that ignores padding, but the theorem requires attainment; \(F\equiv1\) is the stated valid symmetric padding-invariant counterexample, so qualify this as alert-capable/threshold-attaining rules.  
MINOR — paper/satml.tex:595 — “Falls in the same proportion” is not exact under \(\nCal_{\min}=kT/c_0-1\), and an integer calibration count needs rounding; say \(\nCal_{\min}+1\) scales linearly and use \(\lceil kT/c_0-1\rceil\) for a count.  

section clean: no — the grouping comparison mixes canonical and first-flow scopes.

## Audit D

MAJOR — paper/satml.tex:935 — Calls 108 an \(r_t^\star\), but it is the median host-context replay cost; the flow-level closed-form median is 118. Fix: label both as medians and reserve \(r_t^\star\) for the per-alert closed form.

MAJOR — paper/satml.tex:959 — Table V labels AIT empirical replay medians as exact \(r_t^\star\) oracle costs; e.g., canonical RussellMitchell is 4,650 empirical versus 4,132 closed-form, and host-conditioned Wilson is 364.5 versus 355. Fix: relabel the column as per-organisation median replay cost or replace entries with consistently defined closed-form values.

MINOR — paper/satml.tex:776 — Table III says only that the seed is “fixed”; its reported rows are seed 0. Fix: name seed 0 explicitly in the caption.

MINOR — paper/satml.tex:931 — The host-context result omits its 0.55 window and seed-0 scope, making “every evaluated target” read broader than the reported arm. Fix: state window, seed, horizon-free e-LOND regime, and the two-target denominator.

MINOR — paper/satml.tex:737 — The fixed-multiplier result names canonical order and windows but not the seed-0, horizon-free polynomial arm. Fix: state that full arm alongside the \(c=10\) claim.

section clean: no — Table V conflates empirical replay medians with exact per-alert \(r_t^\star\).

## Audit E

MAJOR — paper/satml.tex:1025-27 omits that one evaluated window is known-invalid and usable only for stress/mechanism costs, yet presents the two-window evidence as empirical breadth; state this restriction and exclude it from validation-supporting claims.

MAJOR — paper/satml.tex:1030-35 reports oracle-priced joint suppression without disclosing the attacker-ownership oracle (knowing which alerts/episodes belong to it); state the assumption and measure or bound performance when ownership is uncertain.

MAJOR — paper/satml.tex:1047 treats zero-evidence pads in the only joint e-LOND rerun as if it establishes an attacked real-score trajectory; explicitly limit joint-cost conclusions to this idealized model and test score-bearing pads jointly.

MAJOR — paper/satml.tex:992-94 overreads a sampled volume-cap configuration as a cap that can preserve an alert, while Table IV retains residual suppression; report the sampled grid and residual outcomes, and weaken this to a configuration-specific observation.

MAJOR — paper/satml.tex:1046 understates order dependence by calling first-flow a sensitivity check without identifying the canonical order as a consequential choice; report the precommitted-order distribution and avoid treating the canonical result as representative.

MAJOR — paper/satml.tex:1127 generalizes the joint-cost warning beyond the single-seed, two-window baseline e-LOND rerun; qualify it to that experiment and carry the benign-inclusive AIT scope into the conclusion.

MINOR — paper/satml.tex:1073 calls cited work “the published fix” and asserts equivalence to e-LORD without stating conditions; use neutral language and specify the regime of the equivalence.

section clean: no — the empirical joint-suppression claims rely on undisclosed oracle and zero-evidence modeling assumptions.

## Audit F

MAJOR — paper/satml.tex:1150 — The artifact promises AIT-LDSv2.0 extraction and label mapping, but src/README.md:50 documents only LSPR23; ship and document the AIT pipeline or narrow the full-reproduction claim.

MAJOR — paper/satml.tex:1142 — The claimed figure-writing wrapper is absent from `src/` despite src/README.md:5 naming `paper/make_figures_satml.py`; include it in the artifact or remove the claim.

MAJOR — paper/satml.tex:1154 — Public release of working attack code and red-team narratives lacks a concrete dual-use release safeguard; specify a staged/minimal-PoC release and misuse mitigation.

MAJOR — paper/satml.tex:1172 — The LLM disclosure names models but does not justify the selected model sizes/tier; add a contemporaneous, task-specific selection rationale.

MAJOR — paper/satml.tex:1186 — It provides neither hosted-inference hardware nor an environmental-footprint estimate; report provider hardware/energy data or a documented proxy and scope its limitations.

MAJOR — src/README.md:19 — The documented reproduction commands use `python`, which is unavailable in the supplied environment; replace with `python3`.

MAJOR — paper/refs.bib:173,192,274,285,298,326,365,375,398 — Multiple published proceedings entries omit pages, and some omit volume as well; complete their proceedings metadata.

MINOR — paper/refs.bib:155 — The 2015 arXiv entry is a near-duplicate of the published Javanmard–Montanari entry at line 162; cite the published version unless a distinct preprint version is specifically needed.

MINOR — paper/refs.bib:406 — An arXiv preprint is formatted as a journal article; use an `@misc`/eprint entry instead.

section clean: no — the promised full artifact cannot reproduce the AIT transfer results from the supplied README.

## Audit G

CRITICAL — paper/satml.tex:610 — The claimed 35-configuration grouping result inherits canonical/horizon-free reporting, but paper/tables/grouping.tex:5,10 reports only first-flow, horizon-uniform rows (and only 15 family×bucket rows); add the full canonical/horizon-free 35-cell matrix or narrow and qualify the body claim.

MAJOR — paper/satml.tex:936 — `\cref{apptab:r7host}` is cited for the specific \(r_t^\star=108\) versus 118 comparison, but paper/tables/r7host.tex:11–16 has no padding-cost field; add those costs to the table or cite the passage/table that reports them.

MINOR — paper/satml.tex:1279,1336,1398,1429,1539,1595,1908,1924,2029,2087,2199,2249,2275 — `app:horizonscope`, `app:further`, Terms, Procedure definitions, Datasets and preprocessing, `app:feasnotpower`, `app:ait`, `app:defences`, `sec:tail`, `sec:contamination`, Matched operating points, Analyst-feedback controllers, and Negative results have no direct body pointer; add targeted body references where their evidence is used, or fold/remove them.

section clean: no — the granularity evidence is presented under a different order and spending regime than the body’s default scope.

## Audit H

MAJOR paper/satml.tex:138 — LSPR23 is used before its later Locked Shields identification (line 383), and AIT is used 12 times without expansion; expand both at first use.  
MAJOR paper/satml.tex:140 — LOND/e-LOND, LORD++, SAFFRON, ADDIS, and e-BH are never expanded; spell out each procedure name at its first occurrence.  
MAJOR paper/satml.tex:158 — AUROC/AUPRC (3/1 uses) and FDP (5 uses; first at line 271) are never expanded in the body; define each at first use.  
MAJOR paper/satml.tex:547 — Table first references are I:200, II:229, III:554, IV:988, V:547, so Table V precedes III–IV; reorder first citations/numbering. Fig. 4 (env. 698; first cited 861) and Table IV (env. 904; first cited 988) can appear before citation; introduce each before its float.  
MAJOR paper/satml.tex:737 — `$S_t$` is defined at line 716, but unindexed `$S$` appears at lines 737, 767, and 877; use `$S_t$` consistently or define `$S$` separately.  
MINOR paper/satml.tex:334 — Spending weights switch between `\gamma_j` (lines 334, 336, 459) and `\gamma_t` (from line 437); standardize the index.  
MINOR paper/satml.tex:267 — Four `\S\ref` references (lines 267–271) and `Theorem~\ref` (line 983) bypass cleveref; replace with `\cref`/`\Cref`.  
MINOR paper/satml.tex:144 — The claim that suppressing early detections keeps later levels near cold-start values is repeated nearly verbatim at lines 219 and 1035; retain the detailed result once and condense the summaries.  

section clean: no — several core abbreviations are never expanded.
