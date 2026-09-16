# Handoff — R7: host-conditioned detector & padding-transfer boundary experiment

**For a fresh agent with no prior session context.** This document is self-contained: it gives you
the goal, the exact prior result you are extending, the codebase machinery to reuse, the
experimental design, the **methodological traps that will sink the experiment if missed**, the
integration checklist, and acceptance criteria. Read it fully before writing code.

Everything you need already exists on disk (warm data caches, the flow-level detector pipeline, and
the flow-level padding experiment this one mirrors). No new data capture is required.

---

## 0. TL;DR

The paper's padding attack (Surface A) works because the shipped detector uses **flow-only**
features carrying **no endpoint identity**, so ordinary victim-service traffic scores like ordinary
traffic (fires 0%) and dilutes the group e-value. Round 1 confirmed this on the real detector
(experiment W3 / `t48_W3_dilution.py`: 20,000 real benign-service pad flows fire **exactly 0**,
dilution matches the closed form on 18/18 and 72/72 detections). The paper **scopes** this to
flow-level detectors and says a **host-conditioned** detector "would break the argument" and "needs a
testbed."

**R7 supplies that measurement.** Build a *competent* detector that conditions on host context, show
it actually detects (unlike the Isolation Forest arm, which detects nothing), then repeat the
padding-transfer experiment against it and report the boundary honestly: **does the transfer hold,
get $X\times$ more expensive, or fail — and which feature is responsible?** Any of the three outcomes
is a publishable, honest scope result; a partial failure is scientifically useful.

This is the single highest-value item in the second-round review
(`SaTML_2027_review_feedback.md` §5.1, §15; item R7 in `22_review2_worklist.md`). Reviewer estimate:
moves acceptance from ~45–55% to ~55–65%.

---

## 1. Environment & where things are

- **Repo root:** `/Users/shamik/Work/others/SaTML`
- **Python:** use the project venv — `**/Users/shamik/Work/others/SaTML/proto/.venv/bin/python**`
  (has numpy 2.5, scikit-learn 1.9, scipy, pandas). The system `python3` does **not** have numpy.
- **Warm caches (do not rebuild):**
  - `/tmp/lspr_cache/` — flow feature matrix `X.npy` (16,353,511 × 33 float32 = proto + 32 flow
    stats), `y.npy` (labels), `ts.npy`, `src.npy`/`dst.npy` (host codes), `perm.npy`, `sport/dport`.
  - `/tmp/lspr_meta_cache/` — forensic metadata, int32 arrays **row-aligned to `X`**: `srcip`,
    `dstip`, `sport`, `dport`, `l3l4`, `conn`, `service`, `seg_src`, `seg_dst`, `label_src`,
    `label_dst`, `ext_src`, `ext_dst`, plus `cats.json` (string decode tables).
- **Library:** `src/lib/` (self-contained; `runner.py` orchestrates). Key modules:
  - `h_stream.py` — data load, chronological splits, **detector training/scoring**, episode building.
  - `h_meta.py` — `load()` returns `(meta, cats)`; `verify(meta, src, dst)` asserts row-alignment
    (run it once — it cross-checks ports and host↔ip bijection).
  - `h6_procs.py` — online procedures (`Ctx`, `make_gamma`, `run_lond`, `run_addis`, …).
- **The experiment you mirror:** `src/lib/t48_W3_dilution.py` (READ IT FIRST — it is the flow-level
  template; R7 is the host-conditioned counterpart). Its artifact is `src/lib/out/t48_W3.json`.
- **Consistency gate:** `proto/t45_record_consistency.py` (currently 107 checks, 0 inconsistent).
- **The frozen-claims contract:** `docs/03_FROZEN_CLAIMS.md`; the authoritative record:
  `docs/04_EXPERIMENTS_AND_FINDINGS.md`.

Sanity commands:
```bash
cd /Users/shamik/Work/others/SaTML
proto/.venv/bin/python - <<'PY'
import sys; sys.path.insert(0,'src/lib')
import h_stream as hs, h_meta as hm
X,y,ts,src,dst = hs.load()
meta,cats = hm.load()
print(hm.verify(meta, src, dst, n=2_000_000))   # must not raise
print(X.shape, len(meta['srcip']))               # (16353511, 33) 16353511
PY
```

---

## 2. The relevant machinery (how the flow-level pipeline works)

Read `src/lib/h_stream.py` for the exact signatures. The flow used by every experiment:

1. `X,y,ts,src,dst = hs.load()` — memory-mapped feature matrix + labels + timestamps + host codes.
2. `i1,i2,i3 = hs.split_indices(N, pos)` — chronological train `[0,i1)`, calibration `[i1,i2)`,
   deployment `[i2,i3)` for a window start fraction `pos` (windows: 0.55, 0.62, 0.70, 0.77, 0.85;
   **0.55 is the primary guarantee window, 0.85 the stress-test window** — see caveats in `docs/03`).
3. `score = hs.fit_detector(X, y, i1, seed, kind="hgb")` — trains **HistGradientBoosting** on a
   benign-subsampled training slice; returns a callable `score(rows) -> higher = more attack-like`.
   (`kind="iforest"` is the Isolation Forest that never detects.)
4. `s_cal, s_te = hs.score_windows(score, X, i1, i2, i3)` — scores calibration + deployment windows.
5. `e_te, cal, NC, CEIL = hs.evalues(s_cal, y_cal, s_te, k=1)` — **threshold conformal e-value**:
   a test flow's e-value is `CEIL=(|C|+1)/k` if it beats the `k`-th largest benign calibration score,
   else **exactly 0**. This is why ordinary flows contribute 0 and dilute.
6. `ep = hs.build_episodes(e_te, y_te, ts_w, src_w, dst_w, bucket_s=7200, family="src-dst")` —
   groups flows into 2-hour host-pair episodes; group e-value is the arithmetic mean of member
   e-values. Returns `Ev`, `ismal`, `nsz`, `sum_e`, `gid` (per-flow episode id), `order`, `T`.
7. Run e-LOND (`h6_procs.run_lond` with poly γ) → `fired` mask over ordered episodes.

**W3's padding logic (`t48_W3_dilution.py`):** identify the black-box pad pool (window's most common
benign `(proto,dport)` service), measure its **empirical firing rate** by running its real flows
through the detector (result: 0), then for each detected episode confirm the group e-value
`E(G)=S/(m+r)` crosses the firing threshold `1/α_t` at exactly the closed-form `r* = ⌊S·α_t⌋−m+1`.
Because pads fire 0%, dilution is exact.

---

## 3. The core idea R7 changes

A host-conditioned detector makes a flow's score **depend on the host pair**, not just its 32 flow
stats. So a pad flow sent **to the attacked victim** inherits the victim host pair's context. Two
outcomes are possible and the experiment measures which:

- **Transfer holds:** if host context is built from causal benign history, the victim host looks
  ordinary before the attack, so pads to it still score ~0 and still dilute. The attack survives; the
  paper's flow-level result generalises.
- **Transfer degrades/fails:** if the victim host under attack acquires "bad reputation" (elevated
  recent anomaly, unusual service mix), pads to it score higher → fire → **do not dilute**, so
  suppression needs many more flows or is impossible. Report the cost multiplier and the responsible
  feature.

**The central experimental construct:** to score a pad flow "as if the attacker sent it to the
victim," you must attach the **victim host pair's** host-context features to the pad's flow features,
then score that combined vector. Getting this attribution right is the crux (see §5).

---

## 4. Experimental design (three parts)

Write one importable `src/lib/t49_R7_host_detector.py` with `main()` (mirror `t48`'s structure).
Do it at the **primary guarantee window 0.55** (valid e-values) and the **stress window 0.85**, seed
0 (extend to seed 1 if cheap). Everything below reuses the warm caches; no detector-from-scratch data
work.

### Part A — build causal, non-leaking host-context features

For each flow, derive host-context features from **past** traffic only (strictly `ts < ts(flow)`, or
computed on the training/calibration prefix and frozen). Candidate features (pick a small, defensible
set — 4–8):

- per-**src** host: rolling flow rate, distinct destinations contacted, fraction of `conn` states in
  {S0, REJ, RSTO, …} (failed/aborted), mean of the flow-level detector score over the host's recent
  history (a "reputation"/baseline), share of unusual services.
- per-**dst** host: same, from the destination's perspective; plus segment (`seg_dst`) one-hot/low-card
  code.
- optionally the `(src,dst)` pair's recent flow count.

Use `h_meta.load()` for `service`, `conn`, `seg_src/seg_dst`. Aggregate causally (e.g., expanding or
windowed counts over `ts`-sorted flows; the arrays are already sorted).

### Part B — train a *competent* host-conditioned detector and prove it detects

- Augment the flow feature matrix: `X_aug = concat(X, host_features)` (float32).
- Train HGB on `X_aug` over the same chronological training slice (`hs.train_index` for the
  benign-subsampled rows; reuse `fit_detector`'s HGB settings). You may add a `kind="hgb_host"` branch
  to `h_stream.fit_detector` **or** train inline in `t49` — inline is cleaner and keeps `h_stream`
  untouched.
- Compute e-values and run e-LOND exactly as in §2. **Acceptance for Part B:** the detector produces
  **non-zero true-positive detections at the valid window** (unlike Isolation Forest's 0). Report
  AUROC, tail reach (`(e_te[y_te==1]>0).mean()`), and e-LOND detections vs the flow-only detector.

### Part C — the padding-transfer boundary (the headline)

Mirror `t48`'s two measurements, but with the host-conditioned detector and the **victim-context**
attribution from §3/§5:

1. **Empirical pad firing rate.** Take real black-box-service pad flows; attach the **victim host
   pair's** context features (for each detected episode's victim); score with the host detector; report
   the firing rate. (Under the flow-only detector this was 0. Here it may be > 0 — that is the point.)
2. **Dilution / suppression cost.** For each detected episode, inject `r` pads (with victim context)
   and recompute the group e-value `E(G)`; find the `r` at which it drops below `1/α_t`. Compare to
   the flow-level `r*` from `t48`. Because pads may now carry nonzero e-value `μ_pad>0`, use the
   general closed form `r > (S − τ·m)/(τ − μ_pad)` (τ = 1/α_t); **if `μ_pad ≥ τ` the pads never
   suppress — transfer fails**. Report per-window: pad firing rate, median cost multiplier vs `t48`,
   and the fraction of episodes where suppression becomes impossible.
3. **Attribute the boundary.** If cost rises or the attack fails, identify which host feature drives
   it (e.g., ablate features / report feature importances), so the paper can name the responsible
   mechanism.

---

## 5. Methodological traps — READ THIS TWICE

These will invalidate the experiment if missed. The reviewers will look for exactly these.

1. **LABEL LEAKAGE — do NOT use `label_src`, `label_dst`, `ext_src`, `ext_dst` as features.**
   Verified in this repo: `label_src=1` → attack-rate **1.0000** (13,880 flows), `label_dst=1` →
   attack-rate **1.0000** (1,630,719 flows). These are endpoint ground-truth tags; a detector using
   them "detects" trivially and the whole experiment is meaningless (and dishonest). Build host
   features from **behaviour/history**, never from these columns or from `y`.
2. **CAUSALITY — host features must use only the past.** A per-host "reputation" that peeks at the
   flow's own episode (or future) leaks the attack. Compute features from strictly earlier flows
   (expanding/rolling over the `ts`-sorted arrays) or freeze them on the train+calibration prefix.
   State the exact temporal cutoff in the code and the record.
3. **VICTIM-CONTEXT ATTRIBUTION (the crux).** A pad flow the attacker sends to the victim must be
   scored with the **victim host pair's** context, not the pad source's original context. If you score
   pads with their donor host's context you are measuring the wrong thing. Make this explicit: for
   detected episode with victim `(src*,dst*)`, the pad's host-context columns are `(src*,dst*)`'s.
4. **DILUTION IS EXACT ONLY IF `μ_pad = 0`.** With host features `μ_pad` may be > 0; use the general
   suppression formula (§4 C.2) and handle `μ_pad ≥ τ` (no suppression) explicitly. Do **not** reuse
   `t48`'s zero-pad shortcut.
5. **DON'T CLAIM MORE THAN YOU MEASURE.** This is still one dataset, one exercise. Frame the result as
   a **scope boundary for a flow-level vs host-conditioned detector on LSPR23**, not a universal law.
   Whatever the outcome (holds / degrades / fails), report it honestly — a negative-for-the-attack
   result strengthens the threat-model discussion; a transfer-holds result strengthens the attack.
6. **Windows:** headline at **0.55** (valid). 0.85 is the stress-test window (evidence not a valid
   e-value); numbers there are measurements against labels, never guarantees (see `docs/03` caveat 2).

---

## 6. Codebase integration & reproducibility (do all of these)

Follow the pattern `t47`/`t48` used, exactly:

1. **New script:** `src/lib/t49_R7_host_detector.py`, importable, with `main()` writing
   `src/lib/out/t49_R7.json` (`allow_nan=True` if needed). Keep `src/` self-contained (no `proto/`
   references). Run `h_meta.verify(...)` once inside and assert it passes.
2. **Register** in `src/runner.py` `EXPERIMENTS` list (after `t48`), one line.
3. **Sync to proto** so the consistency gate can read it: copy `src/lib/out/t49_R7.json` →
   `proto/out/` and `src/lib/t49_R7_host_detector.py` → `proto/`. (Also copy any new `h_meta`-derived
   helper if you add one.)
4. **Appendix table:** add a `t_r7host()` generator to `paper/make_appendix_tables.py` (read
   `t49_R7.json`), and `\input{tables/r7host}` + a `\cref` in the appendix of `paper/main.tex`.
   Regenerate with `proto/.venv/bin/python paper/make_appendix_tables.py`.
5. **Notebook:** add a cell in `src/tools/build_notebook.py` (near the padding section) that prints
   the R7 result; rebuild `proto/.venv/bin/python src/tools/build_notebook.py` and smoke-test all
   code cells in paper mode.
6. **Consistency checks:** add a `d = load("t49_R7.json")` block to
   `proto/t45_record_consistency.py` asserting the load-bearing numbers (detector detects > 0; pad
   firing rate; cost multiplier / transfer verdict). Keep `quoted(...)` strings on **one line** in the
   record (multi-line markdown wrapping breaks the literal match — a known gotcha).
7. **Record:** add a `## 4.47 …` section to `docs/04_EXPERIMENTS_AND_FINDINGS.md` (mirror §4.45/§4.46
   style: reviewer objection, setup, results table, finding, reproduce line). Governance: this
   produces **new headline numbers** → it needs the `t45` checks + a **frozen-claims note in
   `docs/03`** with an audit line (see the W2/W3/R3 notes for the format).
8. **Paper body:** update the padding-placement scope in `sec:paddingcost` and `sec:limitations`
   (`paper/main.tex`) from "would need a testbed" to the measured boundary. Also adjust the
   "single competent detector" limitation (the review's §5.3) since you now have a second competent
   detector.
9. **Compile & verify:** `cd paper && tectonic -X compile main.tex`; check 0 undefined refs/citations
   and 0 `??` in `pdftotext`. **Page budget:** the body is currently ~13 pages and R8 (trim to 12) is
   deferred — do **not** spend effort trimming here; just don't add gratuitous body text (put detail
   in the appendix table + record).

Gate to green before finishing: `proto/.venv/bin/python proto/t45_record_consistency.py` shows
`0 INCONSISTENT`; the notebook runs all cells in paper mode; the paper compiles.

---

## 7. Acceptance criteria (from review §5.1/§15 and worklist R7)

- A **competent host-conditioned detector** that produces **non-zero true-positive detections at the
  valid window** (contrast with Isolation Forest's 0), with reported AUROC / tail reach / detections.
- The **padding-transfer boundary is measured**: pad firing rate under host conditioning, and whether
  suppression **holds / costs $X\times$ more / becomes impossible**, per window, with the general
  (`μ_pad>0`) formula.
- The **responsible feature** is identified when the transfer changes (ablation or importances).
- **No leakage** (labels excluded, features causal) — stated explicitly in code + record.
- Full reproducibility wiring (§6) and `t45` green; frozen-claims note added.

---

## 8. Suggested first steps (day 1)

1. Read `src/lib/t48_W3_dilution.py` end to end; run it once
   (`proto/.venv/bin/python -c "import sys;sys.path.insert(0,'src/lib');import t48_W3_dilution as t;t.main()"`)
   to see the flow-level baseline you're extending (pad fire rate 0, `r*` = 118 @0.55).
2. Run the §1 sanity block; confirm `h_meta.verify` passes and eyeball 3–4 candidate host features on
   a slice; **confirm each is uncorrelated with `y` once the label columns are excluded**.
3. Prototype the causal host-feature builder on the 0.55 window only; train HGB on `X_aug`; check it
   detects (Part B acceptance) before touching the padding experiment.
4. Only then implement Part C (victim-context pads) and the boundary measurement.

---

## 9. Pointers

- Prior worklist & what's already done: `docs/22_review2_worklist.md` (R7 is the deferred item).
- The review itself: `docs/SaTML_2027_review_feedback.md` (§5.1 highest-value experiment; §15 the
  exact questions to answer: does victim-service traffic still score benign? does padding still
  dilute? how does cost change? which feature breaks transfer?).
- The flow-level result you extend: `docs/04_EXPERIMENTS_AND_FINDINGS.md` §4.45 (W3) and the paper's
  `sec:paddingcost` "Can the attacker put the pad flows where they have to go?" subsection.
- Frozen-claims caveat 5 (`docs/03`) already states the flow-level scope and that a host-conditioned
  detector "would break the argument" — R7 turns that caveat into a measured result; update it.
