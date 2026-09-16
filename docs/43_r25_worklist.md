# Round 25 — novelty positioning, claim-dependency placement, abstract spine, CFP compliance

Worklist for the sixth external read of `paper/satml.tex` (the draft with body ending p.12,
Conclusion occupying ~21 lines of the p.12 left column). The reviewer's text is
`SaTML_2027_r25_feedback.md`. Every observation was checked against the draft before this plan was
written; where the draft already does what is asked, the item says so and is scoped to placement or
wording only. The plan itself was blind-audited by two codex runs on 6 Sep 2026; their corrections
(line numbers, a false "already present" claim, a gate break in T1-A, and the Tier 2 / Tier 4
inconsistency) are folded in below. **No result is strengthened; no number changes except through
Tier 4, which has run.**

## 0. Facts the plan rests on (verified 6 Sep 2026)

| Fact | Where checked |
|---|---|
| Body ends p.12; the Conclusion uses lines 2–21 of the left column, so roughly 0.7–0.8 page of budget remains. Float wrapping makes table-line estimates optimistic; the compile is the arbiter | `pdftotext -layout satml.pdf` p.12 |
| Abstract is ≈310–320 words depending on extraction (310 between the tags in source; 312–318 from the PDF depending on whether the label and index terms are counted), names 4 controllers, 2 regimes, 2 datasets, 2 knowledge models, and about ten quantitative values (3.3e8, 1.8–2.4M, fourteen, 212, 3→105, 24→2,946, 78 of 79) | `satml.tex:129–155` |
| The claim-dependency table `tab:scope` lives in Appendix E (`satml.tex:1872`); the body carries it only as prose in Sec. II-B and Sec. VII-A | grep `tab:scope` |
| The reviewer's three-state sentence is **not** in the paper. The Conclusion (`:1041`) and Sec. V-D (`:736`) carry two of the three states ("cheap and unremarkable in volume" vs "expensive enough for external admission control"); "nearly silent" is absent | `satml.tex:1032–1049, 718–750` |
| "Per-alert, not a joint rerun" is stated in Sec. V-E (`:780–784`) **after** the counts (`:777–778`); the abstract says "suppresses all fourteen … and all 212" (`:143–145`) | `satml.tex` |
| CFP (fetched 6 Sep 2026): LLM section must "explain experimental choices … why was an LLM necessary, why was a particular model size selected, how the authors minimized the volume of queries made, which hardware was used" and justify environmental footprint (cites Lacoste et al.); "Failure to comply … is grounds for desk rejection". Artifacts: shared within 3 days using a fully anonymised repository, kept accessible throughout review, and "should not be edited" after the 3-day deadline | satml.org/call-for-papers |
| Current LLM section names the assistants (Claude Code, Codex CLI) and covers accountability + validation, but has **no** footprint, query-minimisation, model-version/size or hardware statement | `satml.tex:1073–1085` |
| Open Science says "within three days" but not "unmodified during review" | `satml.tex:1070` |
| `t65` (188 checks, as the gate reports) registers the abstract numbers with **same-sentence context words**: `$3.3\times10^{8}$` ("LOND/e-LOND"), `$1.8$--$2.4$ million` (no context), `$24$` ("canonical", "oracle lower bound"), `$212$`, `$105$`, `$2{,}946$` ("horizon-aware"); `78 of 79` is an exact-phrase check ("78 of 79 true detections", `:259`). The literal sentences it requires to be present, and the concession-opener ban list, are enumerated in §1.5 below | `proto/t65_satml_claims.py:105–170, 245–1284` |
| Hardware on which the runs were made: to be confirmed by the authors (this machine is an Apple M5 Pro, 48 GB, no GPU; full mode ≈2–3 h per `src/README.md`) | `sysctl`, `src/README.md:39` |

Repeated hedges, counted in the **body** (lines < 1116): the reviewer's five, plus the "0–3 tail events" row, which is ours:

| Formulation | Occurrences (body) | Canonical home after this round |
|---|---|---|
| procedure-and-spending-sequence scope | abstract (`:134`); III-A `:413` ("a procedure together with its spending sequence") and `:422` ("procedure-and-sequence pairs"), 9 lines apart | III-A, once, right after Thm 1–2 |
| oracle lower bound | abstract `:146`; II-C `:322` (definition); Fig 4 caption `:688`; V-C `:706` ("a lower bound on the attacker's volume"); VII-B `:952`; `tab:main` caption `:832` | II-C (definition); captions keep the two-word tag |
| windows not independent | II-D `:341`; VII-B `:943` | II-D |
| group validity conditional | II-B `:302–308`; V-B `:674` ("the group-validity premise of Sec. II-B"); VII-A `:932`; VII-B `:969` | new p.2 dependency statement + II-B one sentence |
| 0–3 benign tail events | II-D `:355–357`; VII-A `:936` | II-D |
| "We do not claim that online FDR control is generally unusable" | VII-B `:968` only | keep |

## 1. Tiers and order

**Execution order (user decision 6 Sep 2026, amended after the plan audit):**

1. **Tier 4** — the joint attacked-trajectory rerun. DONE. **The keep-or-drop decision is a
   prerequisite for everything below**: T1-G, T2-A/B/C/D/F and §3 all branch on it.
2. **Tier 5a (if kept)** — integrate `t75` into the artifact **before** its numbers enter the paper:
   `runner.py` stage, `paper.ipynb` cell, `make_appendix_tables.py` table, `t61`/`t71` rows. A body
   claim must not rest on a stage the reproduction package does not run.
3. **Tier 1, then Tier 2** — reframing (p.2 positioning), then rewording/editing. Tier 2 is written
   below in its **post-Tier-4** form; a one-line fallback covers the drop case. Lightweight compile +
   `t65` after each.
4. **Tier 5b** — the release-cleanliness audit of `src/`, including the check that the released
   pipeline makes no LLM call (Tier 0 asserts it).
5. **Tier 0** — LLM Usage section, Open Science clause, artifact freeze. Its hardware/query statements
   describe the final code, so it follows Tier 5b.
6. **Tier 3 last** — full compile, gates, layout, blind codex pass on the final prose.

Per `paper-refit-at-the-end`: **do not trim per item; finish all content, then refit once.**

### 1.5 Pinned sentences (`t65`) the edits touch — keep verbatim or re-pin in the same commit

Extracted from `proto/t65_satml_claims.py` on 6 Sep 2026 (`grep '" in flat\|" in _flatS'`). Per edited
passage:

* **Abstract:** "Even under the max-min-optimal horizon-uniform allocation"; "horizon-free allocations
  cost more" (`:290–291`); "On LSPR23 a fixed multiple of the" (`:551`); "sufficiently many zero-evidence
  additions drive an attained alert below threshold" (`:1102`); registry numbers with their context words.
* **Introduction:** "We identify an emergent failure mode of statistical trust layers"; the three
  `\emph{…}` contribution titles (`:873–876`).
* **Sec. III-C:** "Those counts are a property of the spending sequence, not of the evidence ceiling";
  "allocation-optimal already" (`:717–718`). **Sec. IV:** "\emph{minimum} calibration size over
  pre-committed spending allocations" (`:299`).
* **Sec. V-C:** "on LSPR23, $c=10$" (`:546`); "A fixed multiplier requires no access to"; "the smallest of
  the multipliers we evaluate, $c\in\{2,3,5,10,100\}$" (`:1255–1256`); "all 674 detected episodes sit
  on host pairs carrying no benign traffic" (`:1284`).
* **Sec. V-D and `tab:defenses`:** the list in T2-F.
* **Sec. V-E:** "per-alert real-flow replay"; "evaluates each alert separately at the controller level it
  received on the unperturbed run"; "not a joint rerun of the altered controller trajectory"
  (`:885–888`); "pool flow reaching the conformal"; "\emph{none} reaches the tail"; "replay cannot
  bound" (`:989–998`); "Clopper--Pearson upper limit" (`:1004`); "not that a live controller re-run under
  attack behaves identically" (`:1043`, **the one deliberate re-pin**, T2-B); "Monte Carlo estimates
  over $200$ draws"; "which the pool's composition does not establish" (`:1046–1048`); "the pool is
  service-level"; "supplies no such traffic"; "precisely the gap the AIT transfer closes" (`:1051–1053`);
  "median cost of six" / "median is six" (`:245`); "exceeds all fifty audited metadata orders" (`:1162`).
* **Sec. VII-A:** "Any claim that the nominal $\FDR$ guarantee applies to these empirical runs" (`:273`).
* **Conclusion:** "at best, linear in the number of tested hypotheses" (`:302`); no numbers (`:1192`).
* **LLM section:** "take responsibility for all content" (`:1173`).
* **Ban list (must not appear anywhere):** "What is new here."; "The phenomenon is not."; "Not the
  inequality."; "the step from there is short"; "The same inequality is already in the literature";
  "would reach the same conclusions"; "the honest statement is"; "The arm that matters is the other one";
  "worth stating rather than leaving to be inferred"; "not because it is the better choice"; "the only
  mitigation we measure that bites"; "the only measured defence that bites"; "Our contribution is to
  connect them" (`:863`).

* **Computed-string checks (not literal, so a grep for quoted strings misses them; found on the third
  audit round):**
  - `:520–523` R14-2 — the abstract must contain "suppresses all fourteen horizon-free alerts" and
    "all $212$ true detections under horizon-aware" (212 computed from t74). **T2-A removes both**, so
    this check is rewritten in the same commit to the new invariant: the abstract's replay clause
    contains "per-alert" and no count, and the body carries fourteen and 212 with their per-alert scope.
  - `:738–740` V-D conspicuity — "median arity 63 against the horizon-free", "5\%", "only $0.22\%$ of
    episodes reach" (computed from t73). **T2-F replaces the conspicuity sentence**: keep the per-alert
    numbers in one sentence (the pin stays satisfied) and add the padded-alert joint numbers (91 / 3.8 %,
    55 / 4.3 %) from t75 in the next, with a new pin on them.
  - `:746` and `:1009–1010` cap — "$1.0\%$ of benign episodes truncated", "only $5$ of the $105$ alerts
    remain", "at $300$ only $14$" (computed from t74). **T2-F replaces the cap paragraph**: re-pin to the
    joint numbers from t75 (96 fire at 100 = 44 structural + 52 cascade; 19 at 300; 0 at 1,000) and keep
    the per-alert reading as the explicitly labelled comparison so `:1014` ("leaves the attacker a
    residual set it can still silence") stays true.
  - `:988` "$107/107$", `:1002–1003` the Clopper–Pearson percentages, `:1069` "alongside one false
    discovery, realised FDP $0.009$" — V-E/V-D sentences that stay; do not disturb.
  - `:1186–1188` abstract numeric sweep — every number token in the abstract must be a registry row;
    the new abstract adds none, and any dropped row is retired with a comment naming this round.
  - `:486`, `:915`, `:943–944` — Sec. III-C and the ordering paragraph; untouched.

Rule: an edit that removes or rewords a pinned sentence changes the pin in `t65` in the same commit,
with the reason recorded in this file. `t65` is run after every Tier 1 and Tier 2 item, not only at the end.
The register above was built from two greps (`'" in flat\|" in _flatS'` and `f"…{…}" in flat`); before
Tier 2 starts, re-run both and diff against this list.

### Tier 0 — CFP compliance (no page cost; desk-rejection risk)

**T0-1 LLM Usage Considerations (`satml.tex:1073–1085`).** Keep the existing accountability and
validation sentences. Add one paragraph covering, truthfully, each CFP item:

* *Necessity* — already present; keep.
* *Model choice* — name the assistants and models actually used (`[AUTHORS: fill exact model
  names/versions]`; the CLI is Codex 0.152.1 as of today). State that no model was trained or fine-tuned.
* *Query minimisation* — batching related requests into a session, reusing generated code and cached
  result objects, running gates locally rather than by LLM, **no LLM call inside the released pipeline**
  (verified in Tier 5 by grepping `src/` for LLM SDK imports).
* *Footprint* — provider-side energy figures unavailable, so no emissions estimate; the experiments are
  CPU-only scikit-learn on one workstation (`[AUTHORS: confirm machine]`, full mode ≈2–3 h, cached mode
  — reconcile the paper's "about half a minute" (`:1057`) with `src/README.md`'s "~1 min" during Tier 5
  and state one figure — no GPU); reproduction needs no LLM.
* Optional: cite Lacoste et al. (`lacoste2019quantifying` in `refs.bib`).
* Keep the pinned closing "take responsibility for all content" (`t65:1173`).

Acceptance: every clause of the CFP quote is answered by a sentence. The two `[AUTHORS: …]` items are
**not** submission-ready; they must be resolved (exact model names/versions, actual machine) before the
deadline, not left as placeholders.

**T0-2 Open Science (`satml.tex:1070`).** "…within three days of submission, **kept accessible for the
duration of review and not edited after that deadline**, and on Zenodo for the camera-ready."

**T0-3 Artifact freeze (operational).** Build the anonymised copy from a clean clone; grep for author
names, e-mail, `/Users/…` paths and git history; run cached mode from that copy; tag it; record the tag here.

### Tier 1 — positioning on p.2

**T1-A Novelty spine (Intro, `satml.tex:193–198`).** **Keep** the opener "We identify an emergent
failure mode of statistical trust layers…" — `t65:872` requires that exact phrase, and the plan audit
rated replacing it with a prior-work opener as the change most likely to hurt. Insert the composition
pair **after** it: *Prior work studies finite conformal resolution and online alpha decay separately.
We show that their composition has a calculable finite alert lifetime, and that the operational repair,
coarsening hypotheses, creates a class-wide padding vulnerability.* Then the existing "We formalise this
chain…" sentence. Check the literal ban list at `t65:863` before committing wording; "Prior work
studies…" is not on it, but it must not become the paragraph's first sentence.

**T1-B Known-versus-new table (float, after the contribution list, before `:225` "We evaluate
16,353,511 flows").** Three rows, citations in the "known" column, `\cref`s in the "new" column:

| Previously known | New here |
|---|---|
| Finite conformal resolution [vovk2005alrw, hennhofer2026resolution, huo2024realtime]; alpha-death / low power [foster2008alpha, ramdas2017lordpp] | Absorbing discovery horizon for two arrival-time families (Thm 1–2) and the ex-ante calibration-to-horizon sizing law (Cor 1) |
| Fixed-arity characterisation of symmetric e-mergers [vovk2021evalues] | Cross-arity padding robustness (Def 1) and a class-wide impossibility (Thm 3) |
| Batching/grouping recovers online power [zrnic2020batching] | Grouping is the feasibility repair at the exchange rate (eq:exchange) and simultaneously an attacker-controlled membership surface (Sec IV–V) |

Word every "new" cell positively; no numbers (the intro registry then needs no change). **Placement
acceptance check:** after compiling, `pdftotext -f 2 -l 2` must contain the table's caption; if the
float drifts to p.3, force `[!t]`/`[h]` or fall back to a non-floating paragraph.

**T1-C Claim-dependency statement (non-floating, immediately after the contribution list).** Because a
float can drift, the load-bearing version is **prose**: one four-clause sentence or a compact `itemize`
in the reviewer's form (feasibility theorem needs bounded evidence + the stated level form; padding
theorem needs only the symmetric e-merging class; the nominal FDR reading additionally needs group-local
validity; the empirical attack findings concern observed scores, groups and labels). Optionally a 5-row
`tab:deps` float (the `tab:scope` rows minus windows and the ADDIS rows); Appendix E keeps `tab:scope`
in full. Same p.2 placement check as T1-B. Sec. II-B and VII-A then point here.

**T1-D "Obvious once written down" pre-emption (Sec. III-A contribution note, `:417–426`).** One
mid-paragraph sentence, never an opener, and not the banned "the step from there is short": *The value
of Thm 1–2 is the deployment criterion they yield — which procedure-and-sequence pairs are bound, that
the infeasible state is absorbing, and the rate at which calibration must grow — evaluated before a
detector is chosen.* `t69` freezes statements and proofs only; confirm this paragraph is not in its
object list before editing.

**T1-E Related Work back-reference (`:991–1002`).** The "What this literature leaves open…" sentence
duplicates T1-B; reduce to one sentence pointing at the p.2 table; keep the Krönert contrast in full.

**T1-G Repetition cut (pays for T1-B/C).** Apply the table in §0:

* II-B `:302–308` → two sentences: the premise is A1, audited in App. E; the p.2 statement records which
  result rests on it.
* V-B `:674` keep "independent of the detector, the dataset and the group-validity premise"; drop the rest of the clause.
* VII-A `:926–938` → keep only what is not on p.2: the "0–3 tail events do not support it either"
  reasoning and the `sec:groupcal` pointer, **and** the pinned sentence "Any claim that the nominal
  $\FDR$ guarantee applies to these empirical runs…" (`t65:273`) — either verbatim here or moved to the
  p.2 statement with the pin re-pointed in the same commit.
* VII-B "Empirical breadth" `:942–946` → one sentence + `\cref{sec:data}`; keep the atom sentence.
* VII-B "Attack cost is a curve" `:948–955` → drop the oracle-lower-bound repetition (defined in II-C);
  keep the benign-inclusive "lower bound on $m$" point; **add** the per-alert vs campaign qualifier
  from Tier 4 (this paragraph already says "per-alert" at `:952`, so qualify, do not delete).
* VII-B "Theorem scope" `:964–969` → one sentence + `\cref{sec:horizon}`; keep the "generally unusable"
  sentence; drop "and the group-validity premise is assumed, not established".
* V-C `:704–707` → drop "so every reported $r^{\star}$ is an exact attack cost … not a turnkey budget"
  (not pinned); if any of it survives, label it per-alert (it is computed on the unperturbed trajectory).
* III-A `:413` vs `:422` → keep one statement of the procedure-plus-sequence scope.

Expected saving 25–35 source lines. Compile after T1 and record the body end.

### Tier 2 — abstract spine, replay wording, allocation framing (post-Tier-4 form)

Written assuming Tier 4 is **kept**. If dropped: T2-A keeps the per-alert cost pair with the word
"per-alert", T2-C fixes only the `c = 10` sentence, T2-D uses the two-state form the paper already has,
and T2-E/F are skipped.

**T2-A Abstract rewrite (`:129–155`).** Target ≤ 200 words on the reviewer's spine:

> A statistically valid ML alert pipeline can nevertheless become operationally unable to alert. We
> show that bounded conformal evidence and online error spending create a finite alert horizon;
> reducing the number of hypotheses restores feasibility but exposes group membership to adversarial
> padding. This leads to a class-wide impossibility for symmetric e-merging rules and a measurable
> feasibility–resolution–robustness tradeoff on two intrusion-detection datasets.

Exactly **three** quantitative findings, as the reviewer asked, each with the context words `t65`
requires in the same sentence: `$3.3\times10^{8}$` required for LOND/e-LOND vs `$1.8$--$2.4$ million`
available; the **per-alert** oracle-lower-bound cost at the primary window under the canonical order
rising from `$24$` (horizon-free) to `$2{,}946$` (horizon-aware); `78 of 79 true detections` on AIT.
The joint-rerun result enters the abstract as a clause without a number ("a sequential attacker who
suppresses its campaign from the first alert pays only the cold-start price"); the 1 % figure belongs
in Sec. V-D. Drop the four controller names ("two families of arrival-time controllers"), the
fourteen/212/105 counts (retire or re-point their registry rows), the volume-cap sentence (folded
into T2-D). The replay clause carries no count: "per-alert real-flow replay and a joint
attacked-trajectory rerun confirm the predicted suppression". **Pinned abstract clauses that must
survive or be re-pinned in the same commit:** R13-4's pair ("Even under the max-min-optimal
horizon-uniform allocation", "horizon-free allocations cost more"); "On LSPR23 a fixed multiple of the"
(`t65:551`, the state-free clause); "sufficiently many zero-evidence additions drive an attained alert
below threshold" (`t65:1102`). **Checks to rewrite in the same commit:** R14-2 at `:520–523` (the
fourteen/212 abstract wording, see §1.5). New pins: word count ≤ 200; contains "per-alert"; no
"suppresses all"; conclusion numberless.

**T2-B Replay wording sweep (body).** Sec. V-E: the three R22-pinned sentences stay **verbatim** —
"per-alert real-flow replay", "evaluates each alert separately at the controller level it received on
the unperturbed run", "not a joint rerun of the altered controller trajectory" (`t65:885–888`) — because
they remain true of the per-alert replay; the joint result is **added after them** as a separately
scoped sentence (zero-evidence pads, two windows, seed 0, canonical). One pinned sentence must be
revised together with its pin: "not that a live controller re-run under attack behaves identically"
(`t65:1043`) becomes "…which the joint rerun of Sec. V-D then supplies for zero-evidence pads".
Qualify "the pad is three orders of magnitude larger" (`:773`) as per-alert (and note 2,946/24 ≈ 123×,
so "two orders" is the honest magnitude). Sec. V-F `:819`: "suppresses all nine" → "suppresses each of
the nine, replayed per alert". Grep the body for `suppresses all|every canonical alert` and name the
unit at each hit.

**T2-C State-free paragraph (Sec. V-C, `:709–717`).** Two changes. (i) **Fix** "c = 10 … suppresses
every canonical alert in the evaluated state-free arms": t66's multiplier arm covers canonical 0.55 and
0.85; at canonical 0.62 the first alert (m = 22, r* = 859) needs c > 40.05, i.e. the integer multiplier
41, so scope the sentence to the two windows t66 evaluates and state the 0.62 exception. The literal
"on LSPR23, $c=10$" (`t65:546`), "A fixed multiplier requires no access to" and "the smallest of the
multipliers we evaluate, $c\in\{2,3,5,10,100\}$" (`t65:1255–1256`) and "all 674 detected episodes sit on
host pairs carrying no benign traffic" (`t65:1284`) must survive the rewrite. (ii) Add the joint result,
**scoped to the two evaluated horizon-aware cells**: multiplying every own episode by 3 = ⌈ρ⌉ silences
the controller at both windows with no controller state; the identity `c_crit ≤ ρ` (equality when a
malicious episode attains the ceiling) is stated as the one-line algebra that explains the measurement,
not as a general theorem. Promoting it to a numbered proposition would be a new frozen object: it needs
a proof in `appendix_proofs.tex`, a blind theory audit, and a `t69 --refreeze` with provenance. Give
the paragraph a topic sentence separating attacker knowledge from the oracle cost.

**T2-D Allocation sentence, qualified, scoped.** The three-state form goes in the **Conclusion**
(`:1041`, replacing the two-state clause; keep the pinned "at best, linear in the number of tested
hypotheses", `t65:302`) **without generalising the joint result**: *Controller allocation determines
whether the system is nearly silent, cheaply suppressible, or expensive enough per alert that a tight
volume cap intervenes; per-alert pricing does not characterise the cost of suppressing a whole
campaign, and statistical validity alone determines none of these properties.* The measured campaign
figures (5,650 / 9,992, 0.9–1.0 %, two windows, seed 0) live in V-D with their scope and nowhere else;
the words "collapses" and "manufactured" do not enter the paper. The abstract closing gets the
**short** form only ("allocation sets the per-alert price, not padding invariance"). Contribution 3
(`:213–221`) gets one clause; its pinned title "\emph{An operational cost and mitigation boundary"
(`t65:876`) stays. No copy in V-D, which is rewritten in T2-F.

**T2-E Hostile reading (Sec. V-D).** Replaced by T2-F; the joint cap numbers answer it.

**T2-F Sec. V-D rewrite and Table I.** Structure: (1) per-alert cost curve as now (Table I, per-alert);
(2) the joint rerun: per-alert set jointly suppressed; sequential attacker pays 5,650 / 9,992, 0.9–1.0 %
of the per-alert sum, 94–99.6 % of the reduction being the `(R+1)` level effect; padded-alert median
pad 48.5 / 33 and padded arity 91 / 55 (3.8 % / 4.3 % of episodes reach it) — replacing the 2,989 /
0.22 % conspicuity sentence; (3) the cap, measured jointly: at 100, 96 / 79 fire (44 / 33 structural +
52 / 46 cascade victims); at 300, 19 / 60; at 1,000, 0 — replacing "at 100 only 5 of the 105 alerts
remain suppressible, at 300 only 14"; scoped to the sampled grid and these cells; (4) the thesis kept:
allocation prices the attack and does not remove it. Tables by label, not number: `tab:costcurve`
(Table I, both regimes, per-alert) gains joint rows or a companion table generated from
`t75_joint_rerun.json`, whose caption **names** seed 0, canonical order, the two windows, the
horizon-aware allocation and "joint attacked trajectory" — the Sec. II-D convention (`:363–365`)
defaults to horizon-free and per-alert, so the caption must override it explicitly; `tab:main`
(Table II) keeps its "horizon-free regime" caption and is not touched. `tab:defenses` row 4 → "holds
where the first unhidden alert prices the rest over the cap; measured at caps ≤ 100 in the evaluated
cells". Appendix: `apptab:joint` from t75 via `make_appendix_tables.py`. **Pinned V-D sentences that
must survive the rewrite** (`t65:713–718, 749, 1014, 1035–1036, 1057, 1067–1068, 1145–1146`): "increasing
in $\alphat$, so \emph{the cost of suppression is set by the level the…"; "spending allocation cannot
eliminate padding"; "Those counts are a property of the spending sequence, not of the evidence ceiling"
and "allocation-optimal already" (III-C); "Per-host-pair volume cap" / "outside the merging class"
(`tab:defenses`); "leaves the attacker a residual set it can still silence"; "which is an upper bound
rather than a joint minimum" and "lowers the rejection count and so lowers the level" (both still true,
now measured); "an arity-disruption rate; we do not model what"; "zero observed false discoveries" and
"true detections at the primary window with no observed false discovery"; "Within the
unbounded-membership model of \cref{thm:padding}" and "Admission control changes that model".
Anything on this list that the rewrite genuinely needs to change is changed together with its pin and
the reason recorded here. **Computed-string checks this rewrite necessarily changes:** `:738–740`
(conspicuity numbers), `:746` and `:1009–1010` (cap numbers) — see §1.5 for the replacement invariants.

### Tier 3 — verification (LAST, after Tier 0)

Lightweight checkpoints run earlier: a compile + body-end + p.2-placement check after Tier 1 and again
after Tier 2, so drift is caught where it is made. The full pass below is last.

1. `tectonic -X compile paper/satml.tex`; body end via `pdftotext … awk '/Open Science/'`; must be ≤ p.12.
   If p.13: refit **once**, starting with the T1-C table (keep the prose statement).
2. p.2 placement check for T1-B/T1-C (`pdftotext -f 2 -l 2`).
3. `proto/.venv/bin/python proto/t65_satml_claims.py` with the pin changes of T2-A/T2-B recorded here.
4. `t61_paper_consistency.py`, `t71_claim_ledger.py --markdown` (new rows: joint 0 remaining; joint Σ
   ratio; cap-300 joint; c = ρ; the c = 10 scope fix); regenerate `docs/38_claim_ledger.md`.
5. `t69_theory_freeze.py` green with **no** `--refreeze`; `t45`, `t70`.
6. `t68_layout.py`; append any new hyphen-split offender to the `\hyphenation` list.
7. Blind codex pass on the final p.1–2 and Sec. V-D with the reviewer's three hostile sentences verbatim
   plus "does the abstract read as one simultaneous attack run?" and "is any abstract number a
   one-arm value dressed as a range?" (`wrong-statistic-failure-mode`).

### Tier 4 — joint attacked-trajectory rerun — DONE (6 Sep 2026); decision: KEEP (user, 6 Sep 2026)

`src/lib/t75_joint_rerun.py` → `src/lib/out/t75_joint_rerun.json`; full write-up with the audit history
in `04_EXPERIMENTS_AND_FINDINGS.md` §4.70. Code: three blind codex rounds × 2. Write-up: one further
round × 2, which found a mislabelled statistic (padded arity over all detections) and two mechanisms
written as demonstrated that were inferred; both fixed, the cascade is now instrumented.

**Scope:** LSPR23 0.55 / 0.62, seed 0, e-LOND, arithmetic mean, canonical order (first-flow as
sensitivity), zero-evidence pads (pool has no firing flow), oracle attackers that know which of their
own episodes would fire and the live level (the paper's existing `r*` knowledge), state-free attacker
knows only its arity.

**Outcome (canonical, seed 0):**

* Per-alert pads applied together and re-run: **0 true detections remain** in all 8 cells; the 0.62
  horizon-aware false discovery disappears too.
* Greedy sequential oracle: joint cost **0.9–1.0 % of the per-alert sum** under horizon-aware spending
  (5,650 vs 627,495; 9,992 vs 977,567); 94.2 % / 99.6 % of the reduction is the `(R+1)` level effect on
  still-padded alerts, the rest is alerts spared outright. Median pad over padded alerts 48.5 / 33.
  This is the cost of one greedy strategy on the fixed stream, an upper bound on the campaign minimum,
  not a global minimum over attacker strategies.
  Padded-alert arity median **91 / 55**, reached by 3.8 % / 4.3 % of episodes (paper: 2,989, 0.22 %).
* Volume cap, joint attacker: cap 100 lets 96 / 79 fire, of which 44 / 33 are structural and 52 / 46
  cascade victims (measured); cap 300 lets 19 / 60 fire (per-alert reading: 91 / 95); cap 1,000 → 0.
* State-free: c = 3 = ⌈ρ⌉ silences both horizon-aware arms; `c_crit ≤ ρ`, equality here because an
  episode attains the ceiling; needs no surviving false discovery (holds).
* 0.62 horizon-free canonical: suppressing the first alert (859 flows) spares the other ten.
* **Pre-existing exposure:** Sec. V-C's "c = 10 suppresses every canonical alert in the evaluated
  state-free arms" — t66 covers 0.55 and 0.85; at canonical 0.62 c = 10 leaves one alert (needs
  c > 40.05, integer 41). Fix regardless of the decision (T2-C).

**Does it help?** It closes the most plausible revision request, strengthens the attack, and yields a
closed form linking the two contributions. It also corrects two of our own claims in the honest
direction: the cap's protection at 300 and above is overstated by the per-alert reading, and the
horizon-aware pads are not conspicuous against a campaign-wide attacker. **Downside, stated plainly:**
the result is two windows, one seed, one controller and merger, zero-evidence pads and an ownership
oracle; the "24 → 2,946" headline must be relabelled per-alert; Sec. V-D is a rewrite, not an edit; the
page budget must be re-measured after it. Recommendation: **keep**, with the scope stated at the point
of claim.

**If dropped:** T2-B's wording remains the complete answer; the JSON and §4.70 stay as a record; the
`c = 10` fix (T2-C i) is still required.

### Tier 1 and Tier 2 — DONE (6 Sep 2026), post-Tier-4 form

Applied as specified above, with these recorded deviations and gate changes:

* **Abstract:** 211 words (pin set at ≤ 215, not 200 — the four pinned clauses and three numbers with
  their context words do not fit in 200). Numbers kept: `$3.3\times10^{8}$`, `$1.8$--$2.4$ million`,
  `$24$`/`$2{,}946$`, `78 of 79 true detections` ("the canonical pipeline suppresses", restored after
  `t71` flagged the missing qualifier). Dropped: fourteen, 212, 105; their registry rows are now
  `body-only`. The joint result is a clause ("pays only the cold-start price"), no number.
* **`t65` checks rewritten in the same commit:** R14-2 (abstract names per-alert replay + joint rerun,
  no counts; body carries fourteen and 212); R17 cap cost (both windows at cap 100); R20 cap (joint
  outcome from t75: fire = structural + cascade, per-alert reading kept as the labelled comparison);
  R21-2 (the "not that a live controller re-run…" half re-pinned to "the joint rerun of Sec. V-D then
  supplies the re-run controller"); R16 (Table I rows carry the joint Σ column from t75); R14-3 (the
  state-free arms are named and the 0.62 exception stated). New pin: abstract ≤ 215 words, contains
  "per-alert" and "cold-start price". Result: 190 consistent, 0 inconsistent.
* **`t61`:** R25 block of value checks for every joint number in the body; `quotes()` now matches up to
  line wrapping (the raw-text match made every multi-line quotation fragile); `joint` registered in the
  order registry as canonical from t75. 238 consistent.
* **`t71`:** three new rows (joint static, sequential total, cap 100 joint) and the c = 3 row; the cap
  row re-anchored to the per-alert reading sentence; the detection-count row re-anchored to Sec. III-C
  ("detects $105$ of 275…"); the c = 10 row's arm now says "primary and stress windows". 17 claims.
* **Wording:** "oracle cost" in the new V-C topic sentence → "exact attack cost" (R14-4 keeps "oracle"
  to one sense). V-E's "three orders of magnitude larger" → "two orders" (2,946/24 ≈ 123×).
* **Layout after Tier 2:** body ends p.12 at layout line 48 of the left column (slack nearly used);
  both p.2 tables land on p.2; `t68` flags two floats not at a column top (p.2 col 1 the dependency
  table, p.8 Fig. 4) — for the Tier 3 refit.
* **t69, t45, t70:** green, no refreeze.

### Tier 5 — public artifact audit of `src/` (after content is final, before Tier 0)

Inventory every module under `src/lib`, every notebook cell in `src/paper.ipynb` and every result
object under `src/lib/out/` against the paper (body + appendices + tables + figures). Three bins:
**cited** (keep), **infrastructure the cited code imports or the reproduction needs** (keep — do not
delete reproducibility scaffolding merely because prose does not name it), **neither** (remove).
Known gaps: `t73`, `t74` and `t75` are absent from `runner.py`'s stage list. Also grep `src/` for LLM
SDK imports (`anthropic`, `openai`) so Tier 0's "no LLM call in the pipeline" is verified. After
removal: cached mode from a clean copy, `make_appendix_tables.py`, `make_figures_satml.py`, `t70`, `t61`.
Record the removed list here.

### Tier 5 — DONE (6 Sep 2026)

Inventory method: every `src/lib/*.py` classified by (runner stage? notebook `result()`? imported by
another module? produces a JSON some consumer reads?) and every `lib/out/*.json` by (read by
`make_appendix_tables.py`, `figures.py`, `make_figures*.py`, `paper.ipynb`, `t61`, `t65`, `t71`, `t45`?).
For every unreferenced JSON the t61 sweep tokens were recomputed to confirm no body or appendix number
resolves only through it (none did). Moves are to `.attic/` at the repo root (not shipped, has its own
README), so every step is reversible.

* **Kept and wired in:** `t66_nonoracle_padding` and `t67_ait_order` were missing from `runner.py` and
  the notebook although the paper depends on them (the non-oracle table; the abstract's 78 of 79) —
  added to both, with `t73`, `t74`, `t75`. `t17_T2` stays (read by `t18_T4_padding`); `t22_H1_H2` and
  `t29_compound_e` stay (Isolation Forest contrast; compound e-values are described); `t28_P5_padding.py`
  stays (`t43` imports its cost rule by source).
* **Moved to `.attic/src_lib_out_orphans/` (13 JSONs, no producer in `src/lib`, no consumer):**
  t11_real_attack, t12_track2_{1h,2h,6h}, t13_floor_crosscheck, t14_T1, t19_T5T6, t1_silence,
  t2_incident, t2a, t2b, t4_real, t5_realscale.
* **Moved to `.attic/src_lib_superseded/` (5 stages + their JSONs, no consumer, not described in the
  paper, superseded by a later stage):** t16_T7_feedback (→ t40), t21_H6_procedures (→ t21c),
  t21e_H6_frontier (→ t20/t64), t27_H8_labelnoise (→ t31 audit), t37_E5_a1gaps (→ t30/t31/t55).
  Runner entries removed.
* **Moved to `.attic/src_tools/`:** the proto→src pipeline (`strip_comments.py`, `make_importable.py`,
  `build_notebook.py`) — not described by the paper, cannot run (`docs/36`), and `build_notebook.py`
  would clobber the hand-maintained notebook.
* **Removed:** `__pycache__` directories.
* **Identity leak fixed:** the figures cell printed an absolute local path in its output; now prints
  `lib/out`. No LLM SDK import anywhere in `src/` (grep for anthropic/openai/claude/codex/gpt-).
* **Notebook** re-executed headlessly in paper mode: 43 code cells, 33 s, 0 errors; outputs refreshed
  (new cells for t66, t67, t73, t74, t75). `src/README.md` cached-mode time reconciled to "about half a
  minute" (paper's Open Science already said so).
* Gates after the audit: t61 238, t65 190, t45 268, t70 self-contained — all green.

### Tier 0 — DONE (6 Sep 2026), two author facts outstanding

LLM Usage: added the necessity / model choice / query-minimisation / footprint paragraph; the pinned
"take responsibility for all content" sentence kept. **Two placeholders remain and must be filled
before submission:** `[authors: exact model names and versions used across the project]` and
`[authors: machine, CPU, memory]`. Open Science: "kept accessible for the duration of review and not
edited after that deadline" added. T0-3 (anonymised repository build and freeze) is operational and
not yet done.

### Tier 3 — DONE (6 Sep 2026), one item blocked

Final state of `paper/satml.tex` (41 pages; body ends on p.12 at layout line 48 of the left column):

| Gate | Result |
|---|---|
| `t65` claims | 190 consistent, 0 inconsistent |
| `t61` paper vs artefacts | 238 consistent, 0 inconsistent, 0 artefacts missing |
| `t71` claim ledger | 17 claims, 34 checks consistent; `docs/38_claim_ledger.md` regenerated |
| `t69` theory freeze | 0 drift, no refreeze |
| `t45` record vs artefacts | 268 consistent |
| `t70` src completeness | self-contained |
| `t68` layout | 2 consistent; both p.2 tables and Fig. 4 land at a column top |

`t68` change: its float check counted the rows and caption text of an upper float as "prose above" a
lower float stacked beneath it (p.2: `tab:knownnew` over `tab:deps`; p.8: `tab:costcurve` over Fig. 4).
It now recognises a stacked float when the column opens with a float (caption title, gutter-spanning
line, or a spanning float's centred title above) and no line above the caption is a paragraph start
(indent > 8 pt; table cells sit ~5 pt in). Accepted blind spot: an unindented continuation paragraph
between two floats would also pass. The diagnostic message now prints the offending offsets.

**Blocked:** the blind codex reviewer pass on the final opening and Sec. V-D (Tier 3 item 7) could not
run — `codex exec` returned "Your workspace is out of credits" on both attempts. The brief is saved at
the scratchpad `brief_final.md`; run it once credits are restored, before the freeze.

**Not done, needs the authors:** the two `[authors: …]` placeholders in the LLM section (model
names/versions; machine); T0-3 (build, check and freeze the anonymised repository). A pre-round copy of
the source is `paper/satml.tex.pre_r25` (not shipped).

## 1.9 Round 25b — thirteen follow-up points (6 Sep 2026), all applied

| # | Point | Action in `satml.tex` |
|---|---|---|
| 2 | "campaign" in empirical claims | Removed from abstract, contribution 3, Sec. V-D, `apptab:joint`, VII-B, Conclusion; replaced by "attacker-controlled episodes in the window" / "joint window-level cost". Kept only in the dataset-limitation sense (no flow-to-campaign identifier). `t65` bans the empirical phrasings ("whole campaign", "campaign price", …). |
| 3 | Three attack costs | Definition paragraph opens Sec. V-D ($r^\star_t$, $J_{\mathrm{seq}}$, multiplier $c$); Table III columns renamed "median $r^\star$ / $\Sigma$ independent $r^\star$ / $J_{\mathrm{seq}}$"; caption rewritten; `apptab:joint` header matches. |
| 4 | Name the experiment for what it is | "joint controller-state rerun" throughout; abstract: "Per-alert real-flow replay validates the zero-evidence pad model, after which a joint controller-state rerun propagates those pads through the e-LOND trajectory"; `apptab:joint` titled "Joint zero-evidence controller-state rerun"; limitation sentence added to VII-B (host-conditioned and AIT studies rescore per alert, not jointly). |
| 5 | Soften "cold-start price" | Abstract and contribution 3 now: suppressing early detections keeps later levels near their cold-start values, reducing the greedy joint cost by roughly two orders of magnitude relative to independently priced pads. |
| 6 | $3.3\times10^8$ in the abstract | Replaced by the scale-free ratio (20 calibration flows per hypothesis at $k=1$ for LOND/e-LOND); Sec. III-B labels the extrapolation "for an uninterrupted horizon equal to all 16,353,511 flows in the trace". `t65` registry: `$20$` added to the abstract, `$3.3\times10^{8}$` and `$1.8$--$2.4$ million` moved to body-only. |
| 7 | Qualify two abstract claims | "when group membership is attacker-influenceable, the resulting hypothesis admits padding"; Table I "attacker-influenceable"; "On LSPR23's attack-only host pairs a state-free episode-size multiplier suppresses the evaluated arms" (R14-3 abstract pin re-pointed). |
| 8 | Affirmative novelty sentence | Sec. III-A ends with the reviewer's sentence (Theorems 1–2 and Corollary 1 turn prior qualitative observations into an ex-ante systems criterion…); Related Work states the gap directly again (the table reference removed). |
| 9 | Target-system motivation early | Sentence added in Sec. I after the pipeline is introduced, citing the prior compositions and disclaiming universal SOC deployment. |
| 10 | Repeated validity disclaimers | VII-A compressed to two sentences (keeps the pinned "Any claim that the nominal FDR guarantee…" and the literal "conditional on the group-validity premise" t61 requires); the intro dependency paragraph shortened to point at Table II. |
| 11 | Table V redesign | Now a `table*` with ragged-right cells and one-phrase entries; volume-cap row per the suggestion; the feedback cascade explained in Sec. VI prose ("a tight cap can force an early alert to remain visible; that rejection increases later e-LOND levels…"). |
| 12 | $\lceil\rho\rceil$ edge case | `apptab:joint` caption: $c_{\mathrm{int}}=\lfloor\rho\rfloor+1$, equal to 3 at both windows; the code already used floor+1. |
| 13 | "labels" column | Table II row split: "Mechanical suppression and exact cost" (labels no) / "True-detection rates, replay counts, FDP" (labels yes); the appendix `tab:scope` split the same way. |

**Refit (once, at the end):** the additions pushed the body onto p.13 by ten lines. Cuts, all
content-neutral and unpinned: the intro's section roadmap (Fig. 1's caption carries it); the Sec. III-B
sentence about the appendix margin (the appendix defines it); Sec. I para 3 and para 4 tightened; the
V-B "independent of the detector…" clause (Table II carries it); the V-F closing sentence; the Sec. VI
restart aside and two phrasings; Fig. 1 and Fig. 4 at 0.92\textwidth, Fig. 2 at 0.9\columnwidth.
Fig. 3 must stay at full width: at 0.9 its axis text shifts ~10 pt in and `t68` reads it as an indented
paragraph above the caption. Result: body ends p.12, left column line 46 (≈ 16 lines of slack).

**Gate changes this round:** `t65` — `$20$` registered (abstract, context "LOND/e-LOND", "$k=1$");
R14-2/R25 replay pin → "validates the zero-evidence pad model" + "joint controller-state rerun";
abstract pin ≤ 235 words, requires "cold-start values", "attacker-influenceable", "attack-only host
pairs", bans the empirical "campaign" phrases; R14-3 abstract pin → "On LSPR23's attack-only host pairs
a state-free episode-size multiplier"; R21-2 → "then propagates zero-evidence"; R25 joint pin → "an
upper bound on the minimum joint cost", requires "We distinguish three attack costs", the
"$\Sigma$ independent $r^{\star}$" and "$J_{\mathrm{seq}}$" column names. Abstract: 229 words.
Final: t65 194, t61 238, t71 17 claims, t68, t69, t45, t70 all green; 41 pages.

## 2. Declined or scoped down, with reasons

* **Full controller taxonomy into the body.** Not affordable within 12 pages. Acceptance check instead:
  Sec. III-E must name which procedures escape (ADDIS's selective index; history-wide e-BH) and that each
  escape has a measured price — it does (`:529–541`); keep that paragraph intact through the refit.
* **Calling the algebra "elementary" in the paper.** Not adopted; T1-D frames value without
  self-deprecation.
* **More independent datasets.** Reviewer agrees current wording is adequate; only the repetition cut
  touches it.
* **Restating seed/order/window per sentence.** Declined in round 24 for the same page-budget reason.

## 3. Page budget

Source-line estimates do not predict rendered pages (floats wrap, tables render taller than their
source, cut sentences are partly replaced by qualifiers), so no arithmetic is offered. What is known:
the current body ends ≈ 21 lines into p.12, leaving roughly 0.7–0.8 page; Tier 1 adds two p.2 objects
and removes repetition; Tier 2 shortens the abstract and, with Tier 4 kept, adds joint rows and a
rewritten V-D, while the V-E limitation sentences are **retained** (pinned) and gain a sentence.
Direction is therefore slightly positive (more text), not neutral; the compile is the arbiter and a
refit at the end is likely. Checkpoints: compile after Tier 1 and after Tier 2 (Tier 3 preamble); if the body ends on
p.13 at the final pass, refit **once**, at the end, starting with the T1-C table.
