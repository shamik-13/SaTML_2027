# Review 10 worklist — theorem correctness, claim→evidence mechanics, presentation

Source: reviewer feedback on `paper/satml.tex` (2026-09-02, after the 12-page rewrite).
Seven points, in the reviewer's own priority order. Point 7 is run as a **blind codex review**
(see `blind-codex-review-workflow` memory).

| # | Item | Status |
|---|---|---|
| R10-1 | **Theorem/claim correctness audit.** Blind, adversarial read of Thm 1–4, Lemma 1, Cor 1 and Appendix A. Scrutinise quantifiers, consistent use of "absorbing", sufficient vs necessary, and exactly what *family* each theorem covers. Brief: find a counterexample, not an opinion. | **done** — 2 blind audits, 2 CRITICAL + 4 MAJOR fixed |
| R10-2 | **Mechanical claim→evidence audit.** Every number in abstract, intro and conclusion resolves to exactly one table/figure/derivation, carrying the same order, seed, window and validity status. Build the resolution table; gate the mapping. | **done** — `t65` gate, 45 checks, 10 injected failures caught |
| R10-3 | **Cross-reference and notation pass.** Every `\ref`/`\cref`, theorem number, equation number and appendix reference in one dedicated pass. Two known defects: (a) the 0.70/0.77 zero-detection sentence cites Table III, which has no 0.70/0.77 rows; (b) appendix subsections render as "section F-C", "section D-A", "section F-B" instead of "Appendix F-C" etc. | **done** — 0 undefined refs; 4 notation collisions; 118 lowercase table refs |
| R10-4 | **Density reduction ≈10%.** Compress §III-D (ADDIS / online e-BH / deadlines / smoothing / restart / closure / donation all arrive before C2) and §V-E (caps / asymmetric weighting / group-MAX / direct group calibration / insertion). Keep the taxonomy and the decisive result; push numeric detail to the appendix. Target ≈0.4–0.6 page. | **done** — 925→796 words; see the log on the page estimate |
| R10-5 | **Rework Fig. 4A.** Panel A plots the first-flow arm (median ≈72) while its annotation gives the canonical median 6. Make canonical the visually dominant series and first-flow a dashed sensitivity arm. No new experiment. Figs. 1–2 untouched. | **done** — canonical is now the dominant series |
| R10-6 | **Shorten the abstract.** Keep three memorable numbers — the calibration/horizon mismatch, the 23–33 / 6 low-footprint attack, the 84/85 transfer. Drop the 3.2e13 horizon-free figure and procedural detail to the body. | **done** — 346→333 words, 8 numbers→5 |
| R10-7 | **Two blind mock reviews**, pages 1–11 only at first. (a) multiple-testing/statistics: *is C1 actually new relative to the known conformal-floor / α-death story, and are the theorem scopes airtight?* (b) security/ML-systems: *is the padding threat model operationally credible, and is it obvious why this is more than attacking an already-low-power controller?* Appendices released only after their first reaction. | **done (phase 1)** — both reviewers weak reject; phase 2 deferred, see log |
| R10-8 | **Close-out.** Refit to the 12-page body limit once (see `paper-refit-at-the-end`), re-run the number gates against `src/lib/out/`, recompile, confirm 0 undefined refs / 0 overfull. | open — re-audit of the fixed theorems running |

## Findings log

(appended as each item completes)

---

## R10-2 — claim→evidence resolution table (abstract, introduction, conclusion)

Every number in the abstract and introduction, resolved to exactly one source, with the order, seed,
window and validity status it carries. The conclusion carries **no** numbers (verified by token sweep),
which is the correct state and should stay that way.

| id | claim text | value | unique source | order | seed | window | status |
|---|---|---|---|---|---|---|---|
| A1 | calibration flows, LOND/e-LOND, flow granularity | 3.3e8 | `t21f_H6_scaling.json` `attainable[T=16353511]["R=1"]`=327,070,219; $=kT/\alpha-1$ | n/a | n/a | whole trace, flow unit | derivation (algebraic, Cor. 1) |
| A2 | same, LORD++ | 6.5e8 | same artefact, `family_I_II`=654,140,439; $=kT/w_0-1$ | n/a | n/a | same | derivation |
| A3 | calibration available | 1.8–2.4M | $\nCal$ over five windows: 1,813,113–2,449,031 (`t28b_reallevel.json` `table1`) | n/a | seed-independent by construction | all five | measured |
| A4 | horizon-free $\gamma\propto j^{-1.6}$ requirement | 3.2e13 | paper-side derivation $k/(c_0\gamma_T)-1$, $\gamma_T=T^{-1.6}/\zeta(1.6)$: **3.183e13 at $c_0=w_0$**; at $c_0=\alpha$ it is **1.59e13** | n/a | n/a | whole trace, flow unit | derivation — **procedure not named in the paper (DEFECT R10-2-a)** |
| A5 | primary-window suppression cost | 23–33 | `t28b` `table1_by_order/keyhash/0.55_0/pads_real`=[23,24,33] | canonical | **seed 0** | primary 0.55 | oracle lower bound |
| A6 | replication-window median | 6 | `t28b` `table1_by_order/keyhash/0.62_0/med_pad_real`=6.0, 11 detections | canonical | **seed 0** | replication 0.62 | oracle lower bound |
| A7 | transfer suppression | 84 of 85 | `t54_ait_suppression.json` `flow`: $\sum$`n_detected`=85, $\sum$`n_suppressible`=84 | first-flow (only arm on AIT) | n/a | AIT-LDSv2.0, 8 orgs | measured, benign-inclusive |
| A8 | ADDIS silenced permanently | (no number in abstract) | `t32_B1.json` (real, $B^\star$=203) + `t52_B1_synthetic.json` (median 140) | first-flow | 0 | stress 0.85 (mechanism) + synthetic (guarantee valid) | mechanism / guarantee-valid |
| I1 | trace size | 16,353,511 flows | LSPR23 dataset fact | — | — | — | dataset |
| I2 | window roles | 0.55 P / 0.62 R / 0.85 S | §II-E, Table I | — | — | — | protocol |

### Defects found

- **R10-2-a (MAJOR).** `3.2e13` is the **LORD++** ($c_0=w_0$) figure. The LOND/e-LOND figure for the
  same horizon-free sequence is `1.6e13`. Both the abstract and §III-B attach it to "the same horizon"
  with no procedure named, immediately after a sentence that names *both* procedures. Same for the
  parenthetical `1.44e9` / `3.46e10` link-rate figures, which are also $c_0=w_0$.
- **R10-2-b (MAJOR).** `23–33` and the replication median `6` are **seed-0** values (seed 1 gives
  [23, 30] over 2 detections and median 5 over 8). `satml.tex` has **no conventions statement** naming
  the reporting seed — `main.tex` has one, the rewrite dropped it — and Table III has no seed column
  and no seed in its caption.
- **R10-2-c (MINOR).** Wilson's host-conditioned median $r^\star$ is 364.5 in the artefact and prints
  as `364` in both Table III and `tables/aitsupp.tex`: `int(round(364.5))` is 364 under Python's
  round-half-to-even. Immaterial to the claim; still a number in the paper that is in no artefact.
- **R10-2-d (check, deferred to R10-6).** The abstract says "Feasibility through $T$ hypotheses
  requires…", dropping **cold-start** from Cor. 1, and asserts the absorbing property at family level
  without Thm 1's *eventually non-increasing* hypothesis.

---

## Progress log

### R10-3 — cross-reference and notation pass  **DONE**

Structural audit (`refaudit.py`, all of `satml.tex` + `appendix_proofs.tex` + `tables/*.tex`):
102 labels, 78 referenced, **0 undefined, 0 duplicate**. So the defects were semantic and stylistic:

1. **The Table III miscitation the reviewer found.** "at positions 0.70 and 0.77 no episode clears
   its own step anywhere in the stream (Table III)" — Table III has no 0.70/0.77 rows. The canonical
   five-window order matrix is `apptab:ordering` (canonical row `3 / 11 / 0 / 0 / 34`). The sentence
   is now split: Table III for the primary/replication counts, `apptab:ordering` for the zeros.
2. **"section F-C" → "Appendix F-C".** `\crefalias{section}{appendix}` was set after `\appendices`
   but not `\crefalias{subsection}{appendix}`, so appendix *subsections* kept cleveref's lowercase
   `subsection` default. Both aliases (plus `subsubsection`) are now set, and because `\crefalias`
   is positional, body subsections keep "Section III-D" while appendix ones read "Appendix F-C".
   Verified in the PDF: `Appendix D-A ×4, F-A ×4, F-B ×4, F-C ×1`, no lowercase `section X-Y` left.
3. **IEEE naming.** `crefname` was left at cleveref defaults, so the PDF carried **118 lowercase
   "table XI"** references and lowercase "fig. 4C". Now `Table`/`Fig.`/`Section`: 123 capitalised
   table references, 9 "Fig.", 0 lowercase.
4. **Notation collisions, all in body statements.**
   - `\tau` meant three things: rejection times $\tau_j$ (Thm. 2), the padding-robustness threshold
     (Def. 1 / Thm. 3), and ADDIS's selection threshold (§III-D, Thm. 4). Two of the three are body
     statements two pages apart. The padding threshold is now $\theta$; the other two are standard
     in their literatures and keep $\tau$.
   - `\lambda` was both ADDIS's candidate threshold and the mixing weight in Thm. 3's
     counterexample $\lambda+(1-\lambda)\,\mathrm{mean}$ → the mixing weight is now $\kappa$.
   - `c` was Thm. 1's polynomial constant next to $c_0$, the cold-start coefficient → $c_g$.
   - `d` was Thm. 1's degree and Thm. 2's summation dummy $\sum_{d\ge\Delta}\gamma_d$ → dummy is $u$;
     the appendix's tail sum $S(\Delta)$ (colliding with $S=\sum e_i$ and the closure's subset $S$)
     is now $\Gamma(\Delta)$.
   - Theorem 4 defined the budget as "the smallest $D$" and every result then called it $B^\star$,
     which the statement never introduced. The statement now names $B^\star$ and $B^\star m^\star$.

### R10-5 — Figure 4A  **DONE**

Panel A plotted only the first-flow arm (five pool ECDFs, median 72) under an annotation announcing
the canonical median of 6. Now: the **canonical** order is the visually dominant series (thick, the
0.62 replication arm, 11 alerts) with the canonical 0.85 stress arm beside it; the five first-flow
pool curves are a thin dashed *sensitivity* family; and all three medians (6 / 116 / 72) moved into
the legend, which removed the label collisions that made the panel hard to read. The pool-realism
claim is carried in the canonical order too — ticks at the five canonical pool medians, which span
6–7. Panel height 1.55→1.72 in; Figs. 1–3 untouched. Caption rewritten to match.

### R10-6 — abstract  **DONE**

346 → 333 words, and the numeric load from **eight quantities to five**: kept the calibration/horizon
mismatch ($3.3\times10^{8}$ vs $1.8$–$2.4$M), the low-footprint attack (23–33 / six) and the transfer
(84 of 85). Dropped $6.5\times10^{8}$, $3.2\times10^{13}$ and the intermediate $k/\alpha_T-1$ form to
the body. Two dropped hypotheses restored while there (R10-2-d): the corollary is about **cold-start**
feasibility, and absorption needs Thm. 1's monotonicity, now "under the spending sequences these
procedures use".

### R10-4 — density  **DONE (partial against the reviewer's page estimate)**

§III-D 593 → 498 words, §V-E 332 → 298; 925 → 796 overall (−14%). The structural change is that the
two "this does not rescue feasibility" paragraphs (smoothing/restart and closure/donation) are now
**one** paragraph that defers its reasons to Appendix A and its numbers to Tables IX–XI, and §V-E now
opens by announcing three fixes instead of arriving at them one at a time. The reviewer estimated
0.4–0.6 page; 129 words is ≈0.12 page. Getting to 0.4 would mean cutting ~43% of those two sections,
which is the "remove content wholesale" the same feedback rules out, so the cut stops here.

**A regression this pass caused and the gate that now prevents it.** Compressing §V-E silently
stripped "(first-flow on both legs)" from the cap and weighting claims — the exact failure mode
`claim-audit-overclaim-patterns` records (a compression pass strips qualifying clauses first). A
sweep for the class found four body paragraphs citing a first-flow-**only** appendix table without
saying so; all are now labelled, and `t65` check 6 enforces it mechanically.

### R10-2 — mechanical claim→evidence audit  **DONE**

New gate: **`proto/t65_satml_claims.py`** (45 checks). It is narrower and stricter than `t61`:
for the abstract and introduction of `satml.tex` it asks four questions per number — does it equal
what its declared source produces (artefact lookup *or* re-derived closed form, including
$\zeta(1.6)$ computed at run time); is that source unique; does the **same sentence** carry the
number's order / seed / window / status qualifier; and **is the number in the registry at all**.
The last check is the mechanism the reviewer asked for: an unregistered numeric token in the abstract
fails, so a number cannot be added without resolving it. It also requires the conclusion to carry no
numeric result, and enforces the reporting convention and the first-flow labelling promise
(check 6, added after this pass's own regression).

**Ten injected failures, all caught** (the round-8 lesson: never just run a gate green):
value drift 3.2e13→3.9e13; an unregistered "47" in the abstract; a number planted in the conclusion;
the conventions paragraph deleted; the procedure qualifier stripped from the horizon-free sentence
(the R10-2-a defect reinstated); the seed removed from Table III's caption; "canonical" dropped from
the abstract's 23–33 sentence; "oracle lower bound" downgraded to "measured"; and the first-flow
label stripped from the caps claim and from the smoothing/restart paragraph.

**One hole the injections exposed and closed.** The context check was originally paragraph-scoped,
and "LORD++" occurs somewhere in nearly every paragraph of §III-B — so keeping both horizon-free
numbers while deleting *both* procedure names still passed. Context is now scoped to the sentence.

Defects found and fixed: **R10-2-a** (3.2e13, 1.44e9 and 3.46e10 are all the $c_0=w_0$ LORD++
figures, attached to no procedure; the LOND/e-LOND horizon-free figure, 1.6e13, was missing entirely
and is now stated), **R10-2-b** (`satml.tex` had no conventions paragraph, so the abstract's 23–33
and median-6 were unattributed seed-0 values and Table III had no seed — both fixed), **R10-2-c**
(wilson's median $r^\star$ is 364.5 and printed as 364, because `int(round(364.5))` is 364 under
round-half-to-even; the generator now prints half-integers as half-integers, in `1{,}412.5` style),
**R10-2-d** (handled in R10-6). `t61` (309 checks) and `t45` (268) stay green, so `main.tex` is
unaffected by the shared-table change.

### Also found in the reference pass (not on the reviewer's list)

Fig. 1's causal chain said "(Sec. 4)" and "(Sec. 5--6)" in **arabic**, while IEEEtran numbers
sections in roman — the labels pointed at nothing. Now "(Sec. IV)" and "(Sec. V--VI)".

### R10-1 — theorem/claim correctness audit  **DONE (two independent blind audits)**

Two blind codex audits were run on the same brief ("find a counterexample, not an opinion"), with no
hint of what I believed. They agree on the substance, and each found something the other missed —
which is the argument for running two.

| # | Finding | Both? | Verdict | Fix |
|---|---|---|---|---|
| C1 | **`prop:donation` is false at the stated endpoint $\delta=1$.** Two different counterexamples: $\gamma_t=2^{-t}$, $E_t\ge1$, no rejections gives $\bar W_t=1-2^{-(t-1)}$ and $\alpha_t=\tfrac12$ **forever** — the level never decays, so nothing is absorbed. | **yes** | **valid** | $\delta\in(0,1)$, with the counterexample and the realised $\delta=0.05$ stated in App. A |
| C2 | **`thm:frontload` asserts an exact minimum but proves a sufficient threshold.** The preamble defines $\beta$ via a *lone* firing flow; the proof uses total tail mass. For $w=(0.4,0.3,0.3)$, $\beta=0.5$: $L^\star=2$, yet a lone firing flow cannot fire even at $L=0$. | audit 2 | **valid** | restated as sufficient, exact only under a full-firing episode, upper bound otherwise — matching the conventions paragraph, which already called $L^\star$ an upper bound |
| M1 | **`thm:addis`'s $W=\alpha R$ needs a state quantifier.** Collapsing ADDIS's reward sum to one $W\gamma_D$ is exact only when every active term shares the index; after $R$ rejections each carries its own lag. | **yes** | **valid** | exact pre-rejection (the state the attack is mounted in); $\alpha R$ upper-bounds the coefficient, so $B^\star$ becomes an upper bound |
| M2 | **mem-e-LORD is internally contradictory:** App. B says the feasibility bound is *not* extended to it, while Table II (body) and Table V both mark it covered by Thm. 1. | **yes** | **valid** | its level *has* the family-I form so Thm. 1 bounds its feasibility; what does not transfer is the error-rate reading (mem-$\FDR$, not $\FDR$). Tables unchanged, prose fixed |
| M3 | **e-LORD coverage rests on a reparametrisation stated as a remark.** $\gamma_t=\omega_t\prod_{j<t}(1-\omega_j)$ is a fixed non-negative summable sequence only if the $\omega_j$ are pre-committed. | audit 1 | **valid** | promoted from remark to explicit hypothesis |
| M4 | **"Absorbing" was defined as a first-failure property but proved as a tail property.** Counterexample: $\gamma=(0.01,0.2,0,\dots)$, $d=0$, threshold $0.1$ — infeasible at $t=1$, feasible at $t=2$, and $\gamma_t t^d$ is still eventually non-increasing. | **yes** | **valid** | definition rewritten: a run is *absorbed from step $t$* when \eqref{eq:feas} fails at $t$ and every later step; Thms. 1–2 now conclude absorption from $t^\star+1$ / from $\Delta^\star$ |
| m1 | **`eq:margin` drops $k$.** The paper prints $((\nCal+1)w_0)/T-1$ and then calls it "a function of $\nCal$, $k$ and $T$ alone" — while the implementation computes `CEIL*W0/T-1`, i.e. **with** $k$. | **yes** | **valid** | now $\ceil w_0/T-1=((\nCal+1)w_0)/(kT)-1$; every printed value is unchanged because $k=1$ throughout |
| m2 | Thm. 1 omits $d\ge0$ (the proof's $(R+1)^d\le t^d$ fails for $d<0$); Thm. 2 omits $\gamma\ge0$. | audit 1 | **valid** | both hypotheses stated |
| m3 | Cor. 1's inequality is necessary in general and necessary *and sufficient* under horizon-uniform $\gamma$. | **yes** | valid, strengthening | stated, plus "$\alpha_T$ is the level offered at step $T$" |
| m4 | Def. 1 / Thm. 3 should say $m\ge1$ ($F_0$ and $N/m$ are otherwise undefined). | **yes** | valid | stated |
| m5 | The donation proof's $\sum_{i\notin R_{t-1}}$ reads as including future indices. | audit 2 | valid | both sums now range over $i<t$ |

**What neither audit could break**, after naming their strongest attacks: Lemma 1 / Assumption 1
(the tower argument survives random membership and arity, and shared calibration only creates
dependence, which marginal validity tolerates); Theorem 2 (lag distinctness, LORD++'s coefficients);
Theorem 3 (the essential-domination case split, the strict boundary, $r=0$, mean-$<1$ inputs, and
Route B's random-permutation vector — audit 2 confirmed the threshold is tight for the mean);
Theorem 4's algebra, $0$-indexing and the $0.625$ / $k^{1.625}$ scaling; Prop. 2, Cor. 2, Thm. 5;
and the restart FDR composition proof including the $1-(1-q)^n$ counterexample and the no-rejection
case. My own independent reading agreed on all of these before the audits landed.

One point from audit 1 I did **not** treat as a defect: it read Cor. 1's `|C| >= k/α_T - 1` as
possibly sufficient. The paper says "requires", which is the necessary direction, and the appendix
proof states the min-level condition correctly. What *was* worth fixing is the notation — see below.

### R10-7 — two blind mock reviews, pages 1–11 only  **DONE (phase 1)**

Both reviewers were run in an isolated directory containing **only** `paper_pages_1_to_11.txt`, so
the 18-page appendix was physically unavailable, not merely discouraged. **Both say weak reject**,
for different and mutually reinforcing reasons.

**Reviewer 1 (multiple testing / statistics) — weak reject.**
- *On C1 novelty, bluntly negative.* "Most of C1 is not new as mathematical statistics." They
  decompose it into three things a competent reader already knows — alpha-death in
  alpha-investing/LORD/LORD++, the split-conformal $1/(n+1)$ floor, and the immediate consequence
  that a shrinking level against a floor eventually cannot reject — and read the exchange rate as
  "one line of algebra, not a substantial theorem" (they reproduce it: $M\ge T/c_0$). The escape
  taxonomy they credit as "systematization plus empirical pricing, not new multiple-testing theory".
  They also note the body **hands them the argument**: it says the finite-resolution problem is
  "known" and that related work has "the same algebra". Their words: "the broader claim of an *exact
  calibration–horizon exchange rate* oversells what is mathematically novel."
- *Scope findings*, all independently reproduced by the theorem audits above: "absorbing" is used in
  two senses (immediate-decision vs online e-BH's revisiting); Thm. 4 is "the least airtight from the
  body alone" and rated **high severity for body self-containment**; the mem-e-LORD placement cannot
  be credited from pages 1–11.
- *A notation stumble worth having:* they read Cor. 1's `k/α_T − 1` as `k/(αT)`, because $\alpha$ is
  the target level and $\alpha_t$ the offered one. Fixed by an explicit convention sentence in §II-C
  and by naming $\alpha_T$ in the corollary.
- Single highest-value change, in their view: "sharply downgrade C1's novelty claim and reframe it as
  a clear operational synthesis", and make Thm. 4 and the taxonomy self-contained in the body.

**Reviewer 2 (security / ML systems) — weak reject.**
- *On the threat model:* "partly credible, but not turnkey operationally credible". They accept that a
  compromised internal host or an external host hitting a public service can open extra connections to
  the same destination before bucket close, but list what has to hold and is not stated: the pad's
  source must be the same source (or indistinguishable under the telemetry — "spoofing generally will
  not work for ordinary completed service flows"), the victim must answer a usable service, the pad
  must land before bucket close ("if the SOC emits alerts during the bucket rather than only at close,
  later padding cannot unsend an alert"), and segmentation, authentication, allowlists,
  service-specific or direction-aware grouping, or NAT/proxy normalisation could each break it. Their
  ask: **say which attack classes actually satisfy the capability.**
- *On oracle sizing:* "honest in wording but the operational attack is weaker than the headline
  numbers suggest… that is also the hard part". They note the body says a stateless attacker must
  over-provision but never evaluates a conservative or adaptive black-box strategy for Surface A.
- *On the grouping key:* "plausible but too convenient" — `(src IP, dst IP, 2 h)` plus an arithmetic
  mean over all flows is "especially padding-friendly", and they list what a competent deployment
  might key or aggregate on instead (service/port, direction, asset role, authenticated user, sensor
  zone, detection type, attack stage; max/top-$k$/count-above-tail instead of mean). They accept the
  theorem survives for symmetric rules, but say "the empirical *six flows* story depends heavily on
  this broad, attacker-controllable group".
- *On Q2, which they call the main weakness:* 3 of 275 "makes the attack look parasitic on an already
  failing pipeline", and because LSPR23 has no campaign identifier the paper cannot claim that
  suppressing a few episode alerts suppresses detection of the operation. They **do** buy the
  structural argument in part — they single out the AUROC $0.916\to0.954$ contrast reducing detections
  from 18 to two as convincing that "detector ranking quality does not determine online alert
  feasibility" — but not that it absolves the deployment, noting the paper's own hourly restart takes
  recall $0.065\to0.406$ and "many SOCs would accept a per-epoch guarantee if it produced usable
  alerts".
- Single highest-value change, in their view: "demonstrate a non-oracle padding attack against a
  SOC-plausible, reasonably powered deployment, reporting baseline alert workload, false positives,
  malicious-flow or campaign coverage, attacker over-provisioning, and whether the padding itself is
  detected."

**Both** independently flagged that the stress window must carry no security conclusion (it does not),
and both said the evaluation is adequate for mechanism and cost scale but not for the breadth of the
operational claim.

**Phase 2 (appendix release) is not yet run** — and on this evidence it will not answer either
reviewer, because neither objection is an appendix-lookup: C1's novelty framing is an introduction
decision, and the non-oracle powered-deployment experiment does not exist in the artefact.

### R10-1 round 2 — re-audit of the corrected statements

Re-ran the same blind brief against the fixed file. **0 CRITICAL** — both criticals are closed. It
then found three MAJORs, and **the sharpest was in a sentence this pass had just written**, which is
the `claim-audit-overclaim-patterns` lesson landing again: a repair pass's own output needs the same
audit as the text it repairs.

1. **My Theorem 3 attainment claim was false.** I had written that on any evidence-feasible step the
   all-firing group $x=(\ceil,\dots,\ceil)$ attains $\theta$ inside the deployed two-point support,
   "so the theorem applies exactly when a symmetric rule is capable of issuing an alert". The
   counterexample: $F_N=\tfrac12\mathrm{mean}$ is a valid symmetric e-merging family
   ($\mathbb E[F]\le\tfrac12$); at $\ceil=10$ and $\theta=1/\alphat=9$ the step is evidence-feasible,
   yet every two-point input gives $F\le5<9$. The all-firing witness is **the mean's, not the
   class's**. Rewritten: attainment is exactly the "can fire" condition (if a family ever alerts,
   some received input has $F\ge\theta$), the mean's witness is given explicitly as such, and the
   scaled-mean counterexample is now stated in the paper.
2. **Donation's family-I membership is a prefix property, not a global one.** Prop. 1 said "donation
   e-LOND satisfies Thm. 1 with $c_g=1/(1-\delta)$" while its own next sentence says the denominator
   can vanish past $1/\delta$ rejections. Now: satisfies the hypotheses *along a rejection-free
   prefix* — which is all Thm. 1 needs, since its conclusion is a rejection-free-run statement — and
   explicitly **not** a global member.
3. **e-LORD's $\omega_t$ was still "the e-GAI weight update" in App. B** after the body gained the
   pre-committed hypothesis. App. B now says pre-committed, and says that is the only specialisation
   the coverage claims.

Minors, all applied: Thm. 3's statement now carries $m\ge1$ (Def. 1 already did); Thm. 4 states the
precursor-existence condition $m^\star\le\tau\ceil$ (guaranteed by $(\tau-\lambda)\ceil\ge1$, met by
six orders of magnitude here); Cor. 2's proof names the decreasing $\gamma$ it uses and adds the
subset-minimum repair for a general $\gamma$.

**A hypothesis was removed, not added.** With absorption corrected to a tail property, Theorem 1's
"eventually non-increasing" condition became redundant — a set of feasible steps that is finite
already has a maximum. Thm. 1 is now stated and proved without it, and the proof records why the
earlier version needed it (it was proving the stronger "the *first* infeasible step is permanent",
which is false for non-monotone $\gamma$ and is not what the paper defines).

Still green after both rounds: body p.11, 0 overfull, 0 undefined refs, `t65` 45, `t61` 309, `t45` 268.
A third blind round is running on the twice-corrected file.

### R10-7 phase 2 — appendices released  **DONE**

Each reviewer was given the full 32 pages plus their own first reaction, and asked per objection
whether the appendix *resolves* it, resolves it only by *deferring load-bearing content out of the
body*, or *leaves it open*.

**Statistics reviewer: weak reject → weak accept, narrowly.** In their words, what moved it "is not
C1 novelty" — that assessment is unchanged ("the appendix makes C1 cleaner and more defensible, but
not deeper", and they quote the paper's own two concessions back at it). What moved it is that the
theorem-scope gaps closed: **absorbing — resolved**; **$\alpha$ vs $\alpha_T$ — resolved**;
**Definition 1's deployed support — "mostly resolved… That fixes my main objection"**; Theorem 4
"much more checkable"; mem-e-LORD resolved by the appendix but the caveat "should be in the body
table". They newly credit Theorem 4 plus the synthetic ADDIS result as the cleanest contribution —
but note that is C2, not C1.

**Security reviewer: still weak reject, "closer to borderline than before."** What moved up: the
black-box pool construction (0 of 20,000 pad fires, selected on network-observable frequency alone)
and the AIT real ordinary-to-victim replay "materially improve the padding threat model — the attack
is no longer just *append zeros in a theorem*". What did not move: non-oracle Surface A sizing
(**left open** — black-box *construction* is evaluated, black-box *sizing* is not), the campaign
denominator (**left open**), and the parasitic-on-a-weak-controller objection (**left open**, and
they say the appendix makes it worse: the matched-operating-point table shows online FDR at 3 alerts
and recall 0.011 where an ex-post zero-FDP frontier reaches 0.378).

**Three claim→evidence defects the appendix release exposed, all verified against the artefacts and
all now fixed and gated:**

1. **The abstract's "84 of 85" carried no order qualifier** — flagged independently by *both*
   reviewers. The AIT folds run under that testbed's arrival order and its order sensitivity was
   never audited, so under this paper's own new conventions paragraph an unqualified 84/85 reads as
   canonical. Now "under the one arrival order we audit there".
2. **"service-matched padding is $1.4$--$2.0\times$ dearer" is the first-flow range**, in a sentence
   that reads as canonical. Artefact ratios: canonical 1.17 (0.62) and 1.52 (0.85); first-flow 1.37
   and 1.98. The quoted range excluded the canonical headline cell entirely. Now
   "$1.2$--$1.5\times$ under the canonical order, $1.4$--$2.0\times$ under first-flow, and on a
   smaller episode subset".
3. **"the per-order median stays at $16$--$178$ flows" is survivorship-conditioned** — some
   pre-committed orders detect nothing, which the appendix says and the body did not. Now stated.

Plus two presentation fixes they asked for: Table II marked donation/closure and mem-e-LORD with
footnotes carrying the conditions Appendix A reveals ($\delta<1$, rejection-free prefix only, not a
global family member; the closure's $H+P_T\le T$ sparse-evidence condition; mem-e-LORD's feasibility
yes but mem-$\FDR$ not $\FDR$), so Table II can no longer be read as an unconditional
"nothing rescues it".

**And a fourth defect, again in this pass's own output.** The R10-6 abstract compression had written
"every escape we measure either leaves the class or abandons symmetry, at a priced cost in power".
The statistics reviewer caught that the asymmetric branch does **not** pay in power — first-event-only
weighting has recall 0.062 against the mean's 0.065 — it pays in ordering fragility ($L^\star=1$).
The abstract now prices the two escapes separately, and `t65` gates the substance (the abstract must
price the asymmetric escape in *leading* flows and must not say the escapes cost power).

**Abstract length after the accuracy fixes.** They pushed it to 361 words, i.e. longer than the 346
it started at, which would have undone R10-6. Compressed back to **344** with every new qualifier
kept — numbers still 8→5. The honest summary of R10-6 is therefore: the numeric load is down a
third, the length is essentially unchanged, and two correctness qualifiers were added.

`t65` is now **54 checks with 15 injected failures caught**.

### R10-1 round 3 — audit of the twice-corrected statements

**0 CRITICAL** again. Two MAJORs, and **both were in text this pass had written** — the round-2 fix
was itself imprecise, which is the second instance of the same pattern in this worklist.

1. **The attainment sentence was still a wrong biconditional.** Round 2's replacement said attainment
   "is precisely the condition that the rule can fire". It is not: the implication runs one way.
   Counterexample: at $\theta=2$ and $\ceil=3$, $\tfrac12\mathrm{mean}$ attains $\theta$ at $x=(4)$
   but every two-point input gives $F\le1.5<2$, so it can never fire. **Attainment is strictly the
   weaker condition.** Rewritten to state the implication in the one direction that holds (can fire
   $\Rightarrow$ attains $\Rightarrow$ Thm. 3 applies), to say the converse fails, and to give the
   general condition for the scaled-mean case ($\theta>\ceil/2$).
2. **Prop. 1's Theorem 1 constant is wrong unless $\delta=\alpha$.** Thm. 1 writes the level as
   $\alpha\gamma_t g$, so a bound of $\delta\gamma_t/(1-\delta)$ needs
   $c_g=\delta/[\alpha(1-\delta)]$, not $1/(1-\delta)$ — the two coincide exactly at $\delta=\alpha$,
   which is what the runs use ($\delta=\alpha=0.05$, verified in `src/lib/h6_procs.py`, where the
   donation parameter is `ctx.A`). Corrected in the proposition and the proof, and the $5\%$
   cold-start figure in §III-D is unaffected because it is computed at $\delta=\alpha$.

One minor, applied: Cor. 2 called $H=\min\{j:\gamma_j<1/(\delta\ceil)\}$ "Thm. 1's index horizon",
which is literally true only for decreasing $\gamma$ (for non-monotone $\gamma$ Thm. 1's absorbing
index is after the last feasible spike, not the first dip). Renamed and the monotonicity noted.

One minor needed **no** change: the audit's converse-failure example for Cor. 1 ($T=2$, $\nCal=99$,
$\alpha_1=0.001$, $\alpha_2=0.02$) is exactly what round 2's wording already says — necessary in
general, necessary *and* sufficient under horizon-uniform spending.

**Convergence across four rounds:** 2 CRITICAL → 0 CRITICAL / 3 MAJOR → 0 CRITICAL / 2 MAJOR, with
the residual findings moving from "the statement is false" to "this sentence's logical connective is
too strong". A fourth confirmation round is running.

### R10-8 — close-out state

- Body ends **p.11** of 12; 32 pages total; **0 overfull**, **0 undefined refs**, 0 duplicate labels.
- `t65_satml_claims` **54 checks / 15 injected failures caught**; `t61` **309**; `t45` **268**.
- `main.tex` still builds off the shared `refs.bib` / `appendix_proofs.tex` / `tables/`.
- No refit needed: the body never exceeded the limit, so `paper-refit-at-the-end` does not bind.

**Two decisions left to the author, neither an evidence gap this worklist can close:**

1. **C1's framing.** The statistics reviewer's phase-2 verdict is that the appendix does *not* help
   C1's novelty — "the appendix makes C1 cleaner and more defensible, but not deeper". So this is a
   writing decision: soften C1 to an operational synthesis plus design equation plus escape pricing,
   or hold the current framing and defend the structural characterisation. Note the body currently
   supplies the objection twice, in the intro ("known") and in Related Work ("the same algebra").
2. **The security reviewer's non-oracle experiment.** A padding attack sized without the realised
   group evidence or the live level, against a deployment at a workable alert rate, reporting alert
   workload and whether the pad is itself detected. It does not exist in the artefact. Either run it
   or scope it out explicitly in §VII-C.

### R10-1 round 4 — confirmation round, and where the loop stops

**0 CRITICAL.** 1 MAJOR, 5 MINOR, and the character of the findings has changed from "the statement
is false" to quantifier and wording hygiene — which is the signal to stop.

**MAJOR (valid, applied): coverage is a procedure *together with* its spending sequence.** The body
said "\cref{thm:family1} covers LOND, e-LOND and e-LORD", which reads as coverage of named
procedures. Summability alone is not enough: $\gamma_{2^n}=c/n^2$ with $\gamma_t=0$ elsewhere is a
valid LOND sequence summing to one, yet $2^n\gamma_{2^n}\to\infty$, so Thm. 1's decay hypothesis
fails. The counterexample is now in the paper and the coverage claim is stated per (procedure,
$\gamma$) pair. The pre-existing caveat covered the *degree* $d$, not $\gamma$'s decay, which is why
three earlier rounds missed it.

**MINOR 5 was an error in a counterexample this pass wrote into the paper.** The $\delta=1$ donation
example said "no rejections and $E_t\ge1$" — but at $\alphat=\tfrac12$ rejection needs $E_t\ge2$, so
$E_t\ge1$ does not keep the run rejection-free. The evidence must be pinned at exactly $E_t=1$, and
the proof now says so and says why. **Third instance in this worklist of a repair introducing its own
defect** — the pattern is now recorded in `blind-codex-review-workflow`.

Other minors applied: Thm. 1's empty-feasible-set case (absorbed from step 1, since $t^\star$ is
undefined there); Thm. 3's displayed inequality now quantifies "every integer $r\ge0$"; Thm. 4 states
$0<\lambda<\tau<1$ and reads "after $R\ge1$ rejections".

**One minor needed no change, for the third round running:** the Cor. 1 converse. Rounds 3 and 4 both
offered converse-failure examples; the corollary already says necessary in general, necessary *and*
sufficient under horizon-uniform spending. Two independent audits confirming the same correct wording
is the useful outcome.

**Where the loop stops.** Four rounds: 2 CRITICAL / 0 CRITICAL+3 MAJOR / 0 CRITICAL+2 MAJOR / 0
CRITICAL+1 MAJOR, with the residual MAJOR each round being a narrower scope-wording point than the
last. Every finding was verified against the source or the implementation before being applied, and
one hypothesis was *removed* rather than added. Another round is cheap if wanted, but the marginal
finding is now hygiene, not correctness.

**Final state:** body **p.11** of 12, 32 pages, **0 overfull**, **0 undefined refs**, 0 duplicate
labels, abstract **344** words with five numeric quantities. `t65` **54/15 injections**, `t61`
**309**, `t45` **268**, `main.tex` still builds.

---

## C1 reframing (author decision, applied 2026-09-03)

The statistics reviewer's decisive objection was that C1 "oversells what is mathematically novel".
Both claim sites had the same shape --- *[prior art] is known … our contribution is [three things]*
--- which invites the reader to weigh the delta against the concession. The reviewer did, and the
concession won. Note they moved to **weak accept while still holding the novelty view**, so the
novelty claim was earning nothing and costing an attack surface.

**Four moves applied.**

1. **Prior art first, then a change of *kind*, not of degree.** The contributions paragraph now opens
   "Neither ingredient of this result is new" and cites the four sources itself (bounded conformal
   resolution; level decay on a rejection-free run; the observed consequence for online testing).
   The delta is stated as a type change: bounded evidence turns vanishing **power** into a question
   of **feasibility**, and once the procedure and its spending sequence are fixed that question is
   settled by $\nCal$, $k$ and $T$ alone, before a detector is chosen or a stream is seen.
2. **Tightness cashed instead of "exact".** Cor. 1 became necessary *and* sufficient under
   horizon-uniform spending during R10-1 round 2, and the framing was not using it. It now says the
   boundary is *attained, not merely bounded* --- a characterisation, which is a much harder sentence
   to dismiss than "the exact exchange rate", which reads as a boast about one line of algebra. Every
   `exact` tied to C1 is gone (contributions, §III-B heading, §IV bridge, Related Work), and
   `impossibility` is now reserved for \cref{thm:padding}, which is the paper's one genuine
   impossibility result.
3. **The classification sold as a predictive criterion, not a list.** The axis --- what advances the
   spending index --- is checkable by inspection, it placed the closure and donation constructions on
   the bound side before they were measured ($+0$ detections confirming), and it isolated the escape
   whose state C2 attacks. A taxonomy that generates the paper's second contribution is not a survey.
4. **C1 named as the premise C2 needs.** This also answers the *security* reviewer's "parasitic on an
   already failing pipeline" objection: C1 is what makes the low counts structural rather than a bad
   detector. Stated as the claim §III-C actually supports --- ranking quality moves the counts, not
   the margin.

Related Work now opens "We claim none of these ingredients" and names the composed question the
literature leaves open, rather than asserting novelty after a concession.

**Two overclaims caught in this rewrite, by me, before the audit ran** --- the fourth and fifth of
this worklist:
- "settled in advance by $\nCal$, $k$ and $T$" dropped the round-4 finding that coverage is a
  procedure *together with* its spending sequence. Now "once the procedure and its spending sequence
  are fixed".
- "makes the low detection counts a structural property rather than a weak detector" over-reached:
  the counts move with order and seed; the **margin** does not. Now "ranking quality can move the
  detection counts, but it cannot move the feasibility margin behind them", which is exactly what
  §III-C shows.

Body still ends **p.11**, 0 overfull, 0 undefined refs; `t65` 54, `t61` 309, refs clean. A blind
claim-entitlement audit of the two rewritten paragraphs is running --- including a check for
**under**-claiming, since giving away something Theorems 1--2 genuinely establish would also be an
error.

---

## Non-oracle padding cost (t66) — the security reviewer's open item, closed

The reviewer's "single change that would most move my score" was a padding attack sized **without**
oracle state. It turned out to be a **re-analysis, not an experiment**: `t48_W3.json` already stores
per-episode $m$, $S$, $\alphat$ and $r^{\star}$, and `t25_H5.json` the group-size quantiles. New stage
`src/lib/t66_nonoracle_padding.py` re-derives $r^{\star}$ from the stored fields on all 127 episodes
as a read-back check before computing anything.

**The finding.** Padding defeats an alert iff the padded arity exceeds $S\alphat$, so the attacker
never needs $\alphat$ — only the factor by which its own group overshot its threshold, which it can
cover by multiplying its own arity. That factor has median $1.57$ at the canonical primary window.
**A single multiplier fixed in advance, $c=10$, suppresses every canonical alert at both windows**,
at $15.7\times$ the oracle cost at the primary window and $5.1\times$ at the stress window. Not
knowing $\alphat$ therefore costs a factor of about ten, not the $10^{4}$--$10^{6}$ span of
$1/\alphat$ the old Limitations sentence implied. Surface B already carried a grey-box sizing
analysis; Surface A did not, and that asymmetry is now closed.

**Two blind verification rounds, and the first found a CRITICAL in this new work.**

| finding | verdict | resolution |
|---|---|---|
| **CRITICAL — the conspicuity population was wrong.** I claimed padded arity $120$ against "a benign 99th percentile of $413$". `t25_H5` computes $n_0$ from `cal_group_sizes(ts[i1:i2], ...)` — the calibration slice, **unfiltered by label**, while only the e-value calibration takes `y_cal`. The auditor also showed the deployment true-null percentile is $313$, so the figure was the wrong population *and* anti-conservative. | valid | claim re-anchored on a deployment quantity the artefacts store (`viol_frac`): the padded episode is exceeded by $0.9$--$9.9\%$ of **deployment** episodes. Honest reading: large but not anomalous, not "hidden" |
| **MAJOR — the flat pad is not knowledge-free.** Choosing $N=33$ needs the realised $r^{\star}$ distribution. | valid | reframed as what the realised distribution *demands*, not a derivable rule |
| **MAJOR (round 2) — the multiplier was still post-hoc.** The per-window $c$ was the first tested value defeating that realised cell. | valid | headline moved to the **pre-committed** constant $c=10$ that works at both windows; the per-window $c=3$ is kept and labelled an oracle-informed floor |
| MINOR — the $m$ premise was asserted | valid | now cites 674/674 (`t46_hostpair`); the auditor separately verified all 127 padded episodes carry no benign flows and stored $m$ equals the malicious flow count in every case |
| MINOR ×3 — stale `$n_0$ column` caption reference; a docstring line still saying "benign calibration block"; the absolute arm described as covering cells it skips (`keyed`) | valid | all corrected |

**Verified as correct by both rounds:** the defeat criterion $c\ge1+r^{\star}/m$ re-derived
independently including the $+1$ boundary; every quoted number recomputed from `t48_W3`; the
bracketing direction (a lower $n_0$ gives a higher exceedance, and the paper's $0.9$--$9.9\%$ is
oriented low-to-high); and the C1/Related Work rewrite "appropriately scoped… I did not find an
underclaim that matters".

**Gate:** `t65` is now **69 checks / 22 injected failures caught**, including two that reinstate the
post-hoc multiplier claim as the headline and understate the pre-committed constant's cost.
`t61` 312 (the new table is in its order registry and `\input` by `main.tex`), `t45` 268.

**Page budget.** The body is at **12 of 12** pages. It was 11 at the start of review 10; the round's
correctness work — theorem hypotheses, the conventions paragraph, order/status qualifiers, the C1
reframing and this result — cost the page. Compliant, but with no buffer. Any further addition needs
a matching cut, and the cut should not come from anything added this round.
