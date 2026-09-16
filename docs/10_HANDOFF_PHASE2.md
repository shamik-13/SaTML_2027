# Phase 2 Handoff — Hardening the Experiments

> **Superseded for task assignment, 26 Aug 2026. New agents start at `01_HANDOFF_PHASE4.md`.** All of H1–H8 are closed, and so are the
> three Phase 3 items that followed (A1 position-0.85 forensics → §4.31; A2 alert audit →
> §4.32; B1 ADDIS state-manipulation attack → §4.33). **The experiment matrix is frozen** —
> see `09_WORKPLAN_phases1-3.md` §13–§14, `03_FROZEN_CLAIMS.md` for what may be claimed, and
> `05_PAPER_CONTRACT.md` for what the manuscript is written against. §1–§4 and §6–§7 below are
> still current: they are the environment, the established results, the mistakes already
> made, and the mandatory audit procedure. §5 (the task list) is history.


**You are picking up an in-progress research project.** Read §1–§4 before touching anything;
they contain the environment, the established results you must not contradict, and the
mistakes already made. §5 is your task list. §6 is the audit procedure, which is mandatory.

Written 26 Aug 2026. Target: IEEE SaTML 2027, abstract **22 Sep 2026**, paper **29 Sep 2026**.
Drafting starts ~19 Sep. Until then the goal is **experimental robustness**, so that reviewer
objections are already answered rather than argued during the discussion phase.

---

# 1. What the project is

We are testing whether **online false-discovery-rate control** can make machine-learning
intrusion detection alerting trustworthy. The answer so far is largely no, for reasons that
are now proved and measured. The paper is shaping up as a no-go result plus a constructive
alternative.

The pipeline under test: a detector scores each network flow → the score becomes a **conformal
e-value** against a benign calibration set → flows are grouped into **episodes** → an online
procedure (LOND / LORD++ / e-LOND) decides which episodes to alert on.

**Do not re-litigate the framing.** It went through several rounds of external review and two
repositionings. `09_WORKPLAN_phases1-3.md` §1 records the current claim status; `04_EXPERIMENTS_AND_FINDINGS.md`
is the authoritative record.

---

# 2. Environment

```
Project root : /Users/shamik/Work/others/SaTML
Code         : proto/*.py                 (t1…t33; naming is chronological, not thematic)
Outputs      : proto/out/*.json
Python       : proto/.venv/bin/python     numpy 2.5.2, pandas 3.0.5, sklearn 1.9.0, scipy 1.18.1
Scratch      : /private/tmp/claude-501/.../scratchpad
```

**Always run scripts from `proto/`** — several open `out/…json` by relative path.

## Data

| what | where | size |
|---|---|---|
| LSPR23 raw flows | `proto/data/lspr23/ls23pr_v1.csv` | 10.6 GB, 16,353,511 rows, 101 cols |
| LSPR23 attack narratives | `proto/data/lspr23/…narratives.json` | JSONL, 288 red-team task descriptions |
| AIT NetFlows (tstat) | `proto/data/nf_wilson/` | 313 MB |
| **Derived: full feature file** | `/tmp/lspr_full.csv` | 4.68 GB, all 16.35M rows |
| **Derived: 50%-benign feature file** | `/tmp/lspr_feat.csv` | 2.62 GB, 8,999,203 rows |
| **Derived: annotation columns** (`h_meta.py`) | `/tmp/lspr_meta.csv` | 1.22 GB, 16,353,511 rows |
| Red-team task record (external ground truth, §4.32) | `proto/data/lspr23_attacknarratives.json` | 9.7 MB, 288 narratives |

⚠️ **The two `/tmp` files are derived and will vanish if `/tmp` is cleared.** Regenerate with
(from `proto/data/lspr23/`, ~4 min each):

```bash
# full (no subsampling) -> /tmp/lspr_full.csv
awk -F',' 'NR>1 {
   printf "%s,%s,%s,%s,%s", $7,$2,$3,$95,$6
   for(i=9;i<=40;i++){ v=$i; if(v==""||v=="NaN"||v=="Infinity"||v=="-Infinity") v=0; printf ",%s", v }
   printf "\n" }' ls23pr_v1.csv > /tmp/lspr_full.csv
```
Columns: `ts, src, dst, label, proto, f0…f31`. `ts` is microseconds. Add
`if($95!=1 && rand()>0.5) next` after `NR>1` for the 50%-benign variant.

## Dataset facts you need

- 16,353,511 flows; 1,644,599 malicious (10.06%); span 161.5 h.
- **7,381,261 rows are out of timestamp order.** Always `sort_values("ts")` first.
- **90% of flows fall in the final 25.6 h.** Row-index splits therefore give very short time
  windows — the 78% test split spans only 2.8 h. This is why latency in §4.14 is measured in
  *alerts*, not wall-clock.
- **There is no flow→campaign ground truth.** `Category`, `Severity`, `SigID`, `Expoid_dst`
  are empty for 1,630,732 of 1,644,599 malicious flows. Say **episode**, never *incident*.
  The 288 narratives cannot be joined to individual flows and so cannot supply campaign
  labels — but they are **not** unusable: 83 of them carry a machine-readable compromise
  report (hostname, IP list, timestamp) and 295 carry step-submission times, which §4.32 uses
  as external, label-independent evidence for the alert audit. Join on host IP and on time,
  never on flow identity.
- Attack prevalence by decile: 0.0097, 0.0085, 0.0033, 0.0033, 0.0033, 0.0652, 0.2558,
  0.4688, 0.5532, 0.4564. Detector quality is extremely sensitive to how much ramp-up lands
  in training.

---

# 3. Established results — do not contradict without evidence

Full detail in `04_EXPERIMENTS_AND_FINDINGS.md` (§4.1–§4.19, findings F1–F13). Summary of what
your work must remain consistent with:

- **F1/F2 (§4.13)** — every procedure in two structural families has a finite feasibility
  horizon; covers LOND, LORD++, SAFFRON, ADDIS, e-LOND. `|C| ≥ kT/w₀ − 1` under the best
  admissible spending sequence. LORD++ must make its *first* rejection within 18 hypotheses
  (`|C|`=10⁴) or 334 (10⁶) or it is permanently silent.
- **F5 (§4.15)** — with the full calibration corpus, feasibility margins run −0.061 to +0.918
  over five window positions. Feasible at coarse grouping. **But feasibility ≠ detection**:
  at two positions the fraction of attack flows reaching the ceiling collapses to 0.000–0.030
  despite AUROC 0.83–0.91.
- **F6 (§4.15, §4.17)** — the dilution attack costs a median 1–134 padding flows. Attacker-origin
  traffic fires 4.3× more often than generic benign but the effect is immaterial against the
  threshold.
- **F7 (§4.16)** — theorem: no symmetric e-merging family **that attains τ** is τ-padding-robust,
  for any τ > 1. The attainment condition is required (`F ≡ 1` is a vacuous counterexample
  without it).
- **F8 (§4.12)** — no cap policy is both powerful and unattackable. Four policies measured.
- **F10/F11 (§4.3)** — `P(E[e|C] > 1) = (n/(n+1))^n → 1/e = 0.3679` at k=1, **independent of
  `|C|`**. The evidence ceiling the procedures need is exactly where conditional validity is worst.
- **F13 (§4.19)** — every method sits on the achievable frontier at its own budget. What
  differs is *which point*, and online error control does not let the operator choose: it
  lands at 72 alerts / recall 0.282 / FDP 0.000 where the frontier at the same zero error rate
  offers recall 0.459 on 117 alerts.
- **Refuted:** calibration drift does *not* catastrophically invalidate the evidence (1.3–2.0×,
  and conservative at 10⁻²–10⁻³). Do not revive it.

## Verification tags

Every claim in the findings doc carries one. Keep using them.
`[EXACT]` analytic · `[SIM]` synthetic · `[REAL]` measured on real data · `[PRIOR]` published
elsewhere, cite don't claim · `[OPEN]` not done.

---

# 4. Mistakes already made — do not repeat these

Four independent blind audits (one Opus, three codex) found roughly thirty defects. Two had
**inverted a headline conclusion**. The ones that will bite you again:

1. **Gradient boosting with ~0.6% positives and `l2_regularization=0` explodes.** Leaf values
   reach ±10⁶ instead of ±17 and destroy tail ranking — median attack rank went 3rd → 104th
   and the k=1 firing rate 48.9% → 0%. **Always use
   `HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, l2_regularization=1.0, min_samples_leaf=200, early_stopping=False)`.**
2. **Quantile grids are too coarse in the upper tail.** A 20,001-point grid over `u ∈ [0.5, 1)`
   addresses ~25 calibration order statistics per step and quantises a controller into a fixed
   operating point regardless of gain. **Use exact order statistics: `cal[int(u*(NC-1))]`.**
3. **Randomised rules reported from a single draw.** Policy D was reported as "110/284" from
   one realisation. Report the exact expectation with a Monte-Carlo interval.
4. **Parameters set from the evaluation split.** Caps, thresholds and `P_fire` were all
   computed on test at various points. Derive from training/calibration, or label as oracle.
5. **Unstable sorts.** `np.argsort(-score)` breaks ties arbitrarily and moves the frontier;
   `argsort(first_ts)` ties change the online rejection sequence. Use `np.lexsort`.
6. **Vacuity in a theorem statement.** The padding theorem was initially false as stated
   because `F ≡ 1` satisfies it vacuously. Any "no X can do Y" claim needs a non-triviality
   condition.
7. **Seeds that don't enter the quantity being varied.** A planned 6-config "distribution" of
   feasibility margins would have been three deterministic values duplicated, because the seed
   never enters `NC`, `T` or the margin. Check what your seed actually perturbs.
8. **Single-split, single-seed numbers reported as results.** A "+2% feasibility margin" was
   an artefact of benign subsampling halving `|C|`. Report intervals.
9. **Aggregation validity checked on the typical group, not every group.** `Σe/n₀` is valid
   only for `m ≤ n₀`; at a p99 cap, 1% of groups violated it — and those held 86.2% of all flows.
10. **A conditional rate divided by the wrong denominator.** `((e > 0) & benign).mean()`
    divides by *all* test flows, not the benign ones, and silently scales every benign firing
    rate by the benign fraction. Write `e[benign] > 0`. Found by audit in the A1 repairs
    section, where it would have understated `E[e|benign]` in every repair row.
11. **Corroborating evidence that is computed from the thing being corroborated.** The alert
    audit's structural indicator counts labelled-attack traffic on an episode's endpoints.
    Subtracting the episode's own contribution removes self-corroboration; it does *not* make
    the indicator independent of the labelling process. Separate the tiers explicitly and let
    the weakest, genuinely external one carry the claim (§4.32).
12. **An episode's own flows leaking in through a boundary bucket.** The grouping key is
    `(src, dst, time bucket)`, and `i2`/`i3` cut through whichever buckets they land in, so
    flows of the *same* episode sit outside the deployment window. Any "elsewhere in the
    stream" statistic must subtract the whole global group, not the window fragment.
13. **A statistical test with no power reported as a pass.** A validity check on 3 calibration
    draws saw 6 firings against an expected 3 and "failed"; the deviation was pure Poisson
    noise. Size the check before believing either outcome — `t33_selftest_A1A2B1.py` §4 now
    averages over 2,000 independent strata for exactly this reason.

---

# 5. Your task list

Ordered by rebuttal risk retired per unit of effort. **H6 first** — it is the only task that
could falsify a current claim, and that should surface now rather than in December.

## H6 — SAFFRON, ADDIS, online e-BH, e-GAI `[~1.5 days]` **START HERE**

§4.17 covers only LOND, e-LOND and LORD++. SAFFRON/ADDIS are Family II with unknown constants.
**Online e-BH ([arXiv 2407.20683](https://arxiv.org/pdf/2407.20683)) and e-GAI
([arXiv 2506.01452](https://arxiv.org/pdf/2506.01452)) have different threshold structures and
are the candidates most likely to escape the §4.13 template.**

Run each on the real episode stream (mirror `t19_T5_T6.py`) and report feasibility boundary,
rejections, FDP, recall, silence rate. **If any procedure escapes the template, F1 must be
narrowed** — say so loudly rather than quietly.
*Retires:* "you only broke the procedures you chose to implement."

## H1 — Second detector `[~0.5 day]`

Every real-data result uses HistGradientBoosting alone; the original plan called for two.
Add Isolation Forest (unsupervised) and re-run §4.15, §4.17, §4.19. Note that an unsupervised
detector needs no attack labels in training, which changes the split design — document it.
*Retires:* "your conclusions are an artefact of one classifier." First thing a reviewer checks.

## H7 — Apply the Bates calibration-conditional adjustment `[~1 day]`

F10 states conditional validity fails with probability 1/e **and** that Bates et al. supply
the fix (calibration-conditional conformal p-values, valid with probability ≥ 1−δ over the
calibration draw; reference code `msesia/conditional-conformal-pvalues`). We have never applied
it. Apply at a stated δ and measure the power cost as a function of k.
*Retires:* "you identified a known problem and ignored its known solution." No answer currently.

## H2 — Sweep k on real data `[~0.5 day]`

Every real-data experiment fixes `k = 1`. §4.3 sweeps k analytically but F11's ceiling-vs-
reliability trade-off has never been measured on real scores. Sweep `k ∈ {1, 10, 100, 10³}`
through §4.15 and §4.19. *Retires:* "you picked the most extreme rank."

## H3 — Sweep the error target q `[~0.5 day]`

Everything runs at `q = 0.05`, `w₀ = q/2`. Sweep `q ∈ {0.01, 0.05, 0.10, 0.20}`. The bound
`|C| ≥ kT/w₀ − 1` predicts a linear improvement in q — verify it holds empirically.
*Retires:* "the boundary is an artefact of a strict target."

## H4 — More grouping families `[~1 day]`

F3 rests on (src, dst, time-bucket) alone. Add host-only (src, bucket), /24-subnet pairs,
service-based (src, dst-port, bucket), and finish the 86,400 s and host-pair-only runs that
timed out earlier. *Retires:* "one grouping definition."

## H5 — Cap-selection sweep `[~0.5 day]`

§4.12 tested `n₀` = p99 and max only, and §4.11 shows the floor scales with `n₀`. Sweep
mean → p50 → p90 → p99 → p999 → max. *Retires:* "you picked the cap that makes it look worst."

## H8 — Label-noise interval and audit `[~1 day]`

LSPR23 labels come from exercise instrumentation and are probably cleaner than CIC's measured
7.53% corruption, but we have never quantified them, and FDP is the headline metric. Hand-audit
200–300 alerts, estimate `ε_R`, report FDP as an interval.
*Retires:* "your FDP is measured against labels you never validated."

## H9 / H10 — only if time remains

**H9** second dataset — no drop-in option exists (see `09_WORKPLAN_phases1-3.md` T11). Zero-cost partial
substitute: reframe the five window positions as five quasi-independent deployments, which is
already computed. **H10** a second feedback-controller design (integral term, or direct
quantile targeting) to show §4.14's comparison is not controller-specific.

---

# 6. Mandatory: audit every result before it enters the record

This is not optional overhead. It is why the numbers are trustworthy, and it has twice caught
an inverted conclusion.

**After writing a script and before believing its output**, run a blind adversarial audit:

```bash
cd /Users/shamik/Work/others/SaTML
cat > /tmp/audit.txt <<'EOF'
You are auditing numerical/statistical code for LATENT BUGS. FIND ERRORS. Be adversarial
and specific. Do not summarise what the code does.

Working dir: /Users/shamik/Work/others/SaTML
Python: proto/.venv/bin/python
AUDIT: proto/<your_script>.py
DO NOT read proto/data/ or /tmp/lspr_full.csv or /tmp/lspr_feat.csv (multi-GB; it will
waste your context). Reason about the code and write small synthetic tests in /tmp.

<state the setup: what an e-value is here, what the procedure does, what each quantity means>

CHECK SPECIFICALLY:
1. <list the specific things you are unsure about — be concrete>
...
N. Any use of test-split information to set a parameter evaluated on the same test split.

Report: file:line, what is wrong, why it changes a number, corrected code. One line for
things that are correct.
EOF
nohup codex exec --skip-git-repo-check --sandbox workspace-write "$(cat /tmp/audit.txt)" \
  < /dev/null > proto/out/codex_<task>.log 2>&1 &
```

Notes: `codex` is at `~/.local/bin/codex` (v0.142.3). **Redirect stdin from /dev/null** or it
blocks. Always tell it not to read the multi-GB data files — one early audit burned its context
grepping 2 GB of JSON. Audits take 5–20 minutes; work on something else meanwhile.

**Ask it to check the things you are least sure about, by name.** The generic prompt finds
less. The most productive questions have been: is this parameter derived from the evaluation
split? is this randomised statistic reported from one draw? is this grid fine enough in the
tail? does the seed actually perturb the quantity being varied?

---

# 7. Recording results

1. Add a `## 4.N <title> (script.py) [TAG]` section to `04_EXPERIMENTS_AND_FINDINGS.md` with the
   full tables — that document is the authoritative record and is written as **current state
   only**, not as a change log. State what is, not what was fixed.
2. Update the affected finding F1–F13 if the result changes it.
3. Update the claim-strength table in §5 of that file.
4. Add the script to the reproduction list in §8.
5. Mark the task done in `09_WORKPLAN_phases1-3.md` §12.

## Other files, for orientation only

`09_WORKPLAN_phases1-3.md` — task tracker, claim status, standing rules.
`13_PLAN_v3.md` — the plan T1–T11 came from; superseded but explains the reasoning.
`17_FEEDBACK_ON_ORIGINAL_PROPOSAL.md`, `12_review_experiments_and_next_actions.md` — external
reviews and our responses. `fdr_trustworthy_ids_research_idea*.md`, `14_NOVEL_CONTRIBUTION.md`,
`15_PROTOTYPE_FINDINGS.md` — earlier stages, superseded; read only for history.

---

# 8. Things not to do

- Do not start drafting the paper. That begins ~19 Sep.
- Do not add a detector zoo. Two detectors is the target, not five.
- Do not revive the calibration-drift hypothesis. It is measured and refuted.
- Do not say "incident" when you mean "episode."
- Do not report a single-seed or single-draw number as a result.
- Do not reconstruct AIT-ADS labels (3–5 days, 137 GB dependency) without asking first.
- Do not skip the audit because a script "looks obviously right." The two inverted
  conclusions both came from scripts that looked obviously right.
