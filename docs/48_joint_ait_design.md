# Joint attack on a benign-inclusive AIT stream — readiness assessment and design (round 30)

Reviewer request (7 Sep 2026): run the joint attack on a benign-inclusive AIT stream under
horizon-aware spending, with causal host-context recomputation and empirically sampled pads that may
carry nonzero evidence; use a fixed attack-budget policy chosen before evaluating the stream; report
remaining true alerts and actual total padding, including failures. Offline causal replay, not a live
attack.

This document records (1) what exists, (2) what does not, (3) the design of the new stage `t76`,
(4) the pre-committed budget policies, (5) the probe that checked the horizon-aware baseline is
non-degenerate, and (6) the open decisions. Nothing in the paper changes until the stage has run and
been blind-audited.

## 1. What exists (verified against `src/lib`, 7 Sep 2026)

| ingredient | where | what it does today | reusable as is? |
|---|---|---|---|
| joint controller-state rerun | `t75_joint_rerun.py` (`adaptive_attack`, `check_padded_stream`, multiplier + cap arms) | LSPR23 only; pads carry **zero** evidence (asserted); e-LOND re-run over a padded copy of the episode evidence vector (`Ev0.copy()`); greedy sequential oracle; state-free multiplier; capped attacker with structural/cascade accounting; flow-level permutation check | algorithm yes; the zero-evidence assumption and the LSPR23 loaders no |
| benign-inclusive AIT chain | `t54_ait_suppression.py` (`run_org`, `episodes`, `build_evalues`, `empirical_rstar*`) | leave-one-org-out HGB, chronological in-org benign calibration before the first attack, (src,dst,2h) episodes, e-LOND **horizon-free `poly` only**, per-alert replay of real benign-to-victim pads (flow arm: fixed 0-or-M evidence; host arm: causal fire curve `p_k`) | chain up to the e-values yes; the pricing is per alert against the unperturbed level |
| causal host context | `t49_R7_host_detector.py` (`build_host_features`, `_episode_base_state`, `_replay_ctx`, `_fire_rate`) | six strict-timestamp causal features; accumulation model for the k-th pad (counts += k−1, peers pinned, fail fraction moved toward the pool rate) | yes, plus one extension (§3.3) |
| canonical order on AIT | `t67_ait_order.py` → `t54.episodes(order="keyhash")` via `h_stream.key_hash/hashed_order` | resequencing only | yes |
| horizon-aware allocation | `h6_procs.make_gamma("uniform", T)` | γ_t = 1/T | yes; never applied to AIT so far |
| data | this workstation: `.localdata/ait_cache/<org>/tcp_complete.csv` via `AIT_DIR` (code default `/tmp/ait_cache`); 8 orgs, 123k–418k TCP flows each (environment facts, measured by the probe in §5, not source facts) | loads in ~30 s for all eight | yes |
| compute | this workstation (18 cores / 48 GB); HGB fit per fold 17–27 s measured by the probe (§5, `probe.log`) | — | the stage must record its own timings |

## 2. What does not exist — the gaps the stage must close

1. **No horizon-aware arm on AIT.** Every AIT *controller* result (t54, and t67 which delegates to it) is horizon-free; t51 runs no controller at all. `make_gamma("uniform", T)`
   with T = the organisation's deployment episode count is a one-line change, but the baseline it
   produces (detections, false discoveries) has never been looked at — hence the probe in §5.
2. **No joint rerun on AIT.** t54 prices each detection against `base_lvl[j]` from the unperturbed
   trajectory (`run_org`, the `base_lvl` loop) — exactly the per-alert convention the Limitations
   paragraph names ("the host-conditioned and AIT studies rescore per alert, not jointly", satml.tex:1047).
3. **Pads with nonzero evidence inside a joint rerun.** t75 asserts a zero-firing pool and overwrites
   the episode evidence vector; on AIT the pool fires (flow arm 4e-5–5e-4 per flow; host arm up to 7%
   in the pad's own context on `shaw`). The joint attacker therefore has to *sample* pads one at a time
   and stop on the realised mean, not on a closed form, and a suppression can *fail* within a budget.
4. **Downstream host-context recomputation.** t54's host arm recomputes the context of the *pads* only
   (`causal_fire_curve`). Appending r pads (A→V at the target's last timestamp) also raises
   `src_cnt` for every later flow from A and `dst_cnt` for every later flow to V — including the
   attacker's own later malicious flows and every benign flow to the victim server — and moves their
   fail fractions. Those flows must be re-scored (same HGB, same conformal threshold) so that later
   episodes' evidence, malicious and benign, responds to the attack. This is the "causal host-context
   recomputation" the reviewer asks for and the interaction the current pipeline cannot see.
5. **Host arm on all eight organisations.** `ORGS_HOST = ["shaw", "wilson"]` in t54 was a scope choice,
   not a compute limit (the fit is ~20 s per fold). The joint stage should run the host arm on all
   eight so that "non-attacker alerts" has eight streams to show up in.
6. **A pre-committed budget policy.** t75's attackers are oracle (adaptive) or state-free (multiplier).
   Neither is a *budget* policy with failures. §4 defines the policies to be fixed before the stream is
   evaluated.

## 3. Design of `t76_joint_ait.py` (v3, after two blind audit rounds, §8)

> **Scope note.** §3 fixes the SEMANTICS. The cells actually run are the narrowed set in
> **§9 (Adopted scope, 7 Sep 2026)**: canonical order only, host arm on two organisations, no cap
> grid. Read §9 before judging what is missing here.

Notation: `m_total` = flows in an episode (attacker-owned + co-resident benign), `m_atk` = the
attacker's own flows in it, `r` = pads appended, `S` = the episode's summed evidence, `|C|` = the
calibration set size, `M = (|C|+1)/k` = the evidence ceiling (`CEIL = (NC+1)/k` in `t54.build_evalues`; k = 1 throughout, so M = |C|+1).

### 3.0 Event model (one timeline, stated once)
- The deployment stream is the time-sorted flow list after the first attack; two-hour buckets close in
  time order; at a bucket's close the controller tests that bucket's episodes in the pre-committed
  within-bucket order (canonical key hash, or first-flow as sensitivity) with e-LOND's running R.
- **Insertion time is attacker-observable.** Pads for own episode j are inserted immediately after the
  attacker's **own last flow** in j, `t_atk(j) ≤ t_end(j)`, at virtual times `t_atk(j) + k·ε`,
  k = 1..r_j, ε infinitesimal: strictly after every original flow with `ts ≤ t_atk(j)`, strictly before
  every original flow with `ts > t_atk(j)`, in pad order. (On LSPR23, where no malicious episode has a
  benign flow, `t_atk = t_end` and this is t75's rule.) Co-resident benign flows of j after `t_atk(j)`
  therefore see the pads, as they would in reality. Same key, same bucket, first timestamp unchanged, so
  the grouping is unaffected (checked, below).
- Strict-time causal features (`t49.build_host_features` semantics) on this virtual timeline: originals
  with `ts ≤ t_atk(j)` see no pad; originals with `ts > t_atk(j)` on the pair's src or dst see all `r_j`
  (counts `+r_j`, fail sums `+Σ is_fail` of the *sampled* templates; distinct peers unchanged, the pair
  exists); pad k sees every original with `ts ≤ t_atk(j)`, every earlier pad event on its src or dst,
  and pads 1..k−1 of its own event with their sampled `is_fail` prefix. This generalises t54's
  `_episode_base_state` (`ts <= t_end`) + `_replay_ctx(k)` (which uses the pool-mean fail rate); t76
  implements it as a new function, not by calling `_replay_ctx`.
- **Serialisation at equal timestamps.** All pads of all events sharing one original timestamp get one
  global rank (event order = controller position, then k). Correction to v3: AIT does have timestamp
  ties, 22–175 per organisation (about 4e-4 of flows; the earlier "1.000" was a rounded fraction), but
  no two malicious flows in different own episodes tie, so every organisation has distinct `t_atk`
  across own episodes. The stage implements the rank rule anyway and records both counts per
  organisation instead of asserting their absence.
- Implementation is lazy (per-host event lists of (t_atk, r, Σ is_fail prefix); a flow's six features get
  the cumulative offsets of events strictly before its time on its src / dst; a later target's base state
  gets the same offsets) and is **validated against a full rebuild** on predetermined seeds 0–4 of every
  (cell, attacker): the padded stream is materialised over the **whole organisation's flow list**
  (calibration period included — host context is historical), with integer timestamps rescaled as
  `(ts − ts_min)·(P+1)` and the pads of a timestamp at `+rank`, where P = the maximum total pads at any
  one timestamp; `build_host_features` is re-run and all deployment rows re-scored; episode aggregation
  uses the **original immutable episode ids** (`gid`) plus each pad's target id, never re-derived buckets.
  Lazy and rebuilt features, scores and episode evidence are asserted equal. Deployment spans are
  4.0–6.0 days, so the rescaled timestamps stay below 1.6e18 even at P = SIM_CAP = 3e6 (asserted).
- Grouping check (both arms): `t75.check_padded_stream` ported to `t54.episodes`: same episode count,
  same key at every position, arities `m_total + r`, unchanged labels and first timestamps.
- Invariants asserted every run: calibration scores, conformal threshold and template statistics are
  byte-identical before and after; the unperturbed arms reproduce t54's (first-flow) and t67's
  (canonical) rows field by field (the t75 CONTROL pattern); the md5 of each `tcp_complete.csv` is
  written to the JSON. No subset-of-baseline assertion (rescoring can create alerts).

### 3.1 Cells
organisation (8) × detector arm {flow-only, host-conditioned} × order {canonical, first-flow} ×
spending {horizon-free poly, horizon-aware uniform}. Primary cell, fixed here: host-conditioned,
canonical, horizon-aware, all eight organisations. Flow-only is the context-free control; first-flow and
horizon-free are labelled sensitivities. All 64 cells are reported; none is selected after the fact.

### 3.2 Ownership and attacker knowledge
Ownership: one attacker per organisation (AIT's scripted red-team campaign) owns every episode
containing a malicious flow, across its 3–5 source hosts; the labels are the ownership oracle and are
used for nothing else. Pads for episode j are sent from j's own src to j's own dst.

**What the pads are made of is an evaluation device, not attacker knowledge.** Every real-flow replay in
the paper (t48, t54, t74) represents "ordinary-looking traffic the attacker generates" by real ordinary
flows to the victim; the attacker is never modelled as reading them. t76 keeps that convention and says
so. The knowledge sets below concern the **controller and the scores**:
- **K0 — state-free.** Knows its own flows (`m_atk`, times, src/dst) and the defender's public
  configuration: α, k, the calibration size |C| (hence M) and the declared horizon T of the horizon-aware
  controller — exactly what the paper's state-free multiplier and Corollary 2 already assume (ρ = Mα/T).
  Reads no score, no other flow, no controller state. Runs P1 and P2.
- **K1 — oracle.** Additionally knows each own episode's final `(S, m_total)` on the attacked stream,
  the controller's state at the close of the previous bucket, and the current bucket's test outcomes at
  the fixed point (§3.4). This is t75's greedy oracle (`adaptive_attack`: live level and own evidence)
  extended by the one thing AIT adds — pads change other episodes' evidence within a bucket — and is
  labelled **non-causal within a bucket**. K1 is a cost reference, not a budget policy.

### 3.3 Pad templates (primary = causal)
Templates for the pads of episode j are deployment flows to j's victim with `ts < t_atk(j)` that are
not the attacker's own; each sampled template contributes its flow statistics and `is_fail`; on the
flow arm its stored e-value, on the host arm a fresh score in the pad's virtual-time context. Sampling
with replacement from one pre-drawn seeded sequence per (trajectory, episode); seeds 0..D−1.
- **Pool too small (< N_min = 20 templates):** extend with calibration-period flows to the same victim
  (all before the first attack, so causal), whose flow-arm e-value is recomputed under the fixed
  deployment threshold (strict >; under k = 1 it is 0 by construction, since no calibration score exceeds
  the calibration maximum) and whose host-arm score is fresh. The episode is flagged `pool-extended` and
  **every outcome table reports the pool-extended episodes as a separate stratum** (count, pads,
  suppressed / remaining), since on the flow arm their pads cannot fire.
- **Still < N_min:** the episode is not padded and is recorded as `pool-unavailable` — its own outcome
  class, never treated as zero-firing (t54's empty-pool fallback is not reused).
- Sensitivity, labelled **non-causal oracle pool**: t54's whole-deployment benign-to-victim pool, kept
  only for comparability with the per-alert AIT numbers.

### 3.4 Attackers
- **P1, P2 (K0, pre-committed):** append `(c−1)·m_atk` pads to every own episode at its `t_atk`, in time
  order, with the lazy context propagation; then run the controller once over the padded stream. No
  controller read, so no within-bucket problem arises.
- **SEQ-ORACLE (K1, reference):** bucket fixed point with explicit state. State = the pad-count vector
  `p` over the bucket's own episodes (initially 0), a frozen set F (initialised with the bucket's
  `pool-unavailable` own episodes, which are never padded), and one pre-drawn template sequence per
  own episode with a pool. Step: recompute the bucket's evidence under `p` (lazy offsets), test
  the bucket in controller order with the carried R, take the **first** own episode in `t_atk` order that
  fires and is not in F, append its next template (one pad); if its pad count reaches SIM_CAP put it in F.
  Stop when no own episode outside F fires. `p` is componentwise non-decreasing and bounded by
  SIM_CAP·|own|, so the loop terminates; the step count is recorded. Episodes in F that still fire are
  `pad-fired` failures.
- **CAP-ORACLE (K1, t75's capped adaptive attacker with sampled pads):** SEQ-ORACLE with the extra rule
  that an episode enters F when `m_total + p_j + 1 > cap`, cap ∈ {30, 100, 300, 1000, 3000, 10000}
  (t74/t75's grid, all reported).
- D = 100 trajectories per (cell, attacker); the template draws are the only randomness.

### 3.5 Outcomes and estimands
Alert identity = the immutable (src, dst, bucket) key. *Remaining* = baseline-rejected identities still
rejected on the attacked run; *created* = rejected identities not rejected at baseline; both split into
own / non-owned (true / false) and, for own, pure / mixed with the attacker-owned flow share.
Per (cell, attacker), over the D trajectories: median and [min, max] of remaining own alerts, created own
alerts, remaining and created non-owned alerts, total pads appended (successes and failures), pads spent
on failures. Denominators, always stated: all own episodes; own baseline alerts; attempted (K0: all own
episodes with a pool; K1: own episodes that fired at some step); spared (K1 only: never fired). Per-
episode pad distributions are over all own episodes, never the successes alone (t54's success-conditional
median is not reused). Realised false-discovery counts are reported as realised, never as a guarantee:
the attacked feature process is not the one the conformal calibration certifies.

### 3.6 Outcome classes for own baseline alerts that still fire (ordered, exhaustive, same sampled pads)
Definitions, all **total** quantities measured from the episode's original flows: *live evidence*
`S'` = the summed evidence of the episode's original `m_total` flows on the attacked stream when its
bucket is tested (own flows may have been rescored on the host arm; K0: after all pads; K1: at the fixed
point); *need_R0* = the total zero-evidence pad count `zero_pad(S', m_total, τ_R0)` at the cold-start
level; *need_live* = the same at the live level `τ_live` of the episode's controller position; *budget*
`B_j` = the total pads the attacker may append to j: K0 `(c−1)·m_atk`; SEQ-ORACLE `SIM_CAP`;
CAP-ORACLE `min(cap − m_total, SIM_CAP)` (0 if negative). At the end of a trajectory the pads actually
appended are `p_j ≤ B_j` (K0: `p_j = B_j`; K1: `p_j = B_j` for every frozen episode that still fires,
because the fixed point only leaves a firing own episode when it is frozen). Classes, first match wins:
(0) **pool-unavailable** (`p_j = 0`, never padded);
(1) **structural** — `B_j < need_R0`: the budget could not suppress it even at R = 0 with zero-evidence pads;
(2) **cascade** — `need_R0 ≤ B_j < need_live`: it would have fitted at R = 0 and fails only because R was
    raised (by non-attacker alerts or earlier own failures);
(3) **pad-fired** — `B_j ≥ need_live`: zero-evidence pads of that count would have suppressed it, so the
    residual firing is the sampled pads' own evidence.
The three inequalities partition the firing episodes with a pool, so the classes are exhaustive and
exclusive without reference to `SIM_CAP` or the cap beyond `B_j`. A flag records whether `S'` differs
from the baseline evidence (host-context shift). Conservation, per trajectory: own baseline alerts =
suppressed + (0) + (1) + (2) + (3); created own alerts are reported separately and are not in this sum.

## 4. Pre-committed attack-budget policies (K0)

Fixed by the defender's public configuration (α, |C|, declared horizon T) or a constant carried from
LSPR23, and by the attacker's own flow counts. Nothing is read from scores, other flows or controller
state. The stage writes the full manifest (α, k, M and T per organisation, c per organisation, seeds,
D, N_min, caps, pool rule) to the JSON before any result.

| policy | rule | what it tests |
|---|---|---|
| **P1 LSPR23-carried multiplier** | c = 3 on every own episode: append 2·m_atk pads (the integer that silenced both LSPR23 horizon-aware arms) | does the LSPR23 prescription transfer without re-tuning |
| **P2 Corollary-2 multiplier** | c = ⌊ρ_org⌋ + 1 with ρ_org = M α / T, append (c−1)·m_atk pads | the paper's own state-free prescription on a stream that violates both of its hypotheses (zero-evidence pads, no other cold-start rejection) and where m_atk < m_total on 37/95 episodes. Corollary 2 is a horizon-uniform statement, so P2 carries that name only in the uniform cells; in the poly cells the same c is reported as a heuristic sensitivity |

t75's multiplier arm divides every malicious episode's evidence by c, i.e. appends (c−1)·m_total zero-evidence flows; on LSPR23 m_total = m_atk. Here P1/P2 deliberately use m_atk, the count the attacker knows, so on the 37 mixed episodes they under-provision relative to t75's construction — that is the measured effect, not an inconsistency.

On T: horizon-uniform spending exists only for a horizon the *defender* declares before testing
(`make_gamma("uniform", T)`); in this offline replay, as in the paper's LSPR23 horizon-aware arm, the
declared horizon is the window's episode count. K0 reads it as configuration, not as a count it derives
from other flows. The capped attacker is **not** a budget policy: it reads the live level (K1). It is
reported as CAP-ORACLE next to SEQ-ORACLE, as t75 reports it, so "including failures" is answered for
both the pre-committed policies and the oracle reference under caps.

## 5. Probe: is the horizon-aware AIT baseline non-degenerate? (7 Sep 2026, scratchpad, not a stage)

Script: scratchpad `probe_ait_uniform.py` (reads the AIT cache, writes nothing in the repo; NOT a
paper stage — its numbers are recorded here only to decide the design). Same chain as t54 up to the
e-values (leave-one-org-out HGB, chronological pre-attack benign calibration, k = 1), then episodes under
both orders and e-LOND under both allocations. 16 fits, 399 s wall clock for everything.

| org | arm | order | T | rho | poly: rej/true/FD | uniform: rej/true/FD | uniform cold-start thr | uniform r* median / sum | mixed mal ep | benign share in mixed (med/max) | pool | pool fire (own ctx) | dep benign firing flows |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fox | flow | keyhash | 3662 | 1.613 | 11/11/0 | 11/11/0 | 73240 | 64.0 / 139908 | 5/14 | 0.00/0.50 | 47840 | 1.3e-04 | 6 |
| fox | flow | first-flow | 3662 | 1.613 | 13/13/0 | 11/11/0 | 73240 | 161.0 / 19782 | 5/14 | 0.00/0.50 | 47840 | 1.3e-04 | 6 |
| fox | host | keyhash | 3662 | 1.613 | 2/2/0 | 8/8/0 | 73240 | 102.5 / 97623 | 5/14 | 0.00/0.50 | 47840 | 0.0e+00 | 0 |
| fox | host | first-flow | 3662 | 1.613 | 9/9/0 | 8/8/0 | 73240 | 90.0 / 5288 | 5/14 | 0.00/0.50 | 47840 | 0.0e+00 | 0 |
| harrison | flow | keyhash | 2270 | 3.484 | 9/9/0 | 9/9/0 | 45400 | 104.0 / 138300 | 4/14 | 0.00/0.71 | 27401 | 1.8e-04 | 5 |
| harrison | flow | first-flow | 2270 | 3.484 | 10/10/0 | 9/9/0 | 45400 | 206.0 / 51392 | 4/14 | 0.00/0.71 | 27401 | 1.8e-04 | 5 |
| harrison | host | keyhash | 2270 | 3.484 | 7/7/0 | 7/7/0 | 45400 | 263.0 / 78839 | 4/14 | 0.00/0.71 | 27401 | 2.9e-04 | 8 |
| harrison | host | first-flow | 2270 | 3.484 | 7/7/0 | 7/7/0 | 45400 | 220.0 / 50207 | 4/14 | 0.00/0.71 | 27401 | 2.9e-04 | 8 |
| russellmitchell | flow | keyhash | 1664 | 2.994 | 15/14/1 | 15/14/1 | 33280 | 253.5 / 16137 | 3/14 | 0.00/0.09 | 17250 | 5.2e-04 | 9 |
| russellmitchell | flow | first-flow | 1664 | 2.994 | 15/14/1 | 15/14/1 | 33280 | 407.5 / 9219 | 3/14 | 0.00/0.09 | 17250 | 5.2e-04 | 9 |
| russellmitchell | host | keyhash | 1664 | 2.994 | 9/9/0 | 8/8/0 | 33280 | 74.5 / 4288 | 3/14 | 0.00/0.09 | 17250 | 0.0e+00 | 0 |
| russellmitchell | host | first-flow | 1664 | 2.994 | 9/9/0 | 9/9/0 | 33280 | 170.0 / 1620 | 3/14 | 0.00/0.09 | 17250 | 0.0e+00 | 0 |
| santos | flow | keyhash | 1877 | 4.031 | 8/8/0 | 10/9/1 | 37540 | 57.0 / 8383 | 6/9 | 0.04/0.50 | 21327 | 4.7e-04 | 12 |
| santos | flow | first-flow | 1877 | 4.031 | 9/9/0 | 9/8/1 | 37540 | 106.5 / 5340 | 6/9 | 0.04/0.50 | 21327 | 4.7e-04 | 12 |
| santos | host | keyhash | 1877 | 4.031 | 4/4/0 | 4/4/0 | 37540 | 34.0 / 2322 | 6/9 | 0.04/0.50 | 21327 | 0.0e+00 | 0 |
| santos | host | first-flow | 1877 | 4.031 | 5/5/0 | 4/4/0 | 37540 | 29.5 / 609 | 6/9 | 0.04/0.50 | 21327 | 0.0e+00 | 0 |
| shaw | flow | keyhash | 4417 | 2.289 | 6/3/3 | 6/3/3 | 88340 | 10.0 / 671 | 3/6 | 0.17/0.50 | 1880 | 0.0e+00 | 7 |
| shaw | flow | first-flow | 4417 | 2.289 | 6/3/3 | 6/3/3 | 88340 | 23.0 / 58 | 3/6 | 0.17/0.50 | 1880 | 0.0e+00 | 7 |
| shaw | host | keyhash | 4417 | 2.289 | 4/3/1 | 9/3/6 | 88340 | 5.0 / 151 | 3/6 | 0.17/0.50 | 1880 | 7.0e-02 | 144 |
| shaw | host | first-flow | 4417 | 2.289 | 4/3/1 | 8/2/6 | 88340 | 7.0 / 14 | 3/6 | 0.17/0.50 | 1880 | 7.0e-02 | 144 |
| wardbeck | flow | keyhash | 2021 | 5.483 | 8/8/0 | 8/8/0 | 40420 | 638.0 / 12032 | 5/9 | 0.05/0.54 | 18901 | 3.2e-04 | 6 |
| wardbeck | flow | first-flow | 2021 | 5.483 | 9/9/0 | 8/8/0 | 40420 | 430.5 / 7883 | 5/9 | 0.05/0.54 | 18901 | 3.2e-04 | 6 |
| wardbeck | host | keyhash | 2021 | 5.483 | 8/8/0 | 9/8/1 | 40420 | 638.0 / 12114 | 5/9 | 0.05/0.54 | 18901 | 1.3e-03 | 24 |
| wardbeck | host | first-flow | 2021 | 5.483 | 9/9/0 | 9/8/1 | 40420 | 430.5 / 7949 | 5/9 | 0.05/0.54 | 18901 | 1.3e-03 | 24 |
| wheeler | flow | keyhash | 3371 | 3.308 | 15/15/0 | 15/15/0 | 67420 | 423.0 / 238488 | 5/16 | 0.00/0.27 | 38679 | 2.1e-04 | 8 |
| wheeler | flow | first-flow | 3371 | 3.308 | 15/15/0 | 15/15/0 | 67420 | 540.0 / 364052 | 5/16 | 0.00/0.27 | 38679 | 2.1e-04 | 8 |
| wheeler | host | keyhash | 3371 | 3.308 | 14/14/0 | 15/15/0 | 67420 | 368.0 / 236050 | 5/16 | 0.00/0.27 | 38679 | 3.6e-04 | 14 |
| wheeler | host | first-flow | 3371 | 3.308 | 15/15/0 | 14/14/0 | 67420 | 489.0 / 319402 | 5/16 | 0.00/0.27 | 38679 | 3.6e-04 | 14 |
| wilson | flow | keyhash | 5082 | 2.95 | 11/11/0 | 11/11/0 | 101640 | 409.0 / 46048 | 6/13 | 0.00/0.50 | 93587 | 4.3e-05 | 4 |
| wilson | flow | first-flow | 5082 | 2.95 | 12/12/0 | 11/11/0 | 101640 | 215.0 / 69721 | 6/13 | 0.00/0.50 | 93587 | 4.3e-05 | 4 |
| wilson | host | keyhash | 5082 | 2.95 | 6/6/0 | 6/6/0 | 101640 | 256.5 / 17910 | 6/13 | 0.00/0.50 | 93587 | 0.0e+00 | 0 |
| wilson | host | first-flow | 5082 | 2.95 | 6/6/0 | 6/6/0 | 101640 | 255.0 / 17347 | 6/13 | 0.00/0.50 | 93587 | 0.0e+00 | 0 |

| org | flows | mal flows | cal | dep | victims | attacker src hosts | dep flows to victims | dep flows from attackers | dep benign flows to victims |
|---|---|---|---|---|---|---|---|---|---|
| fox | 184521 | 8901 | 118153 | 66368 | 10 | 4 | 56741 | 29986 | 47840 |
| harrison | 204134 | 9745 | 158160 | 45974 | 8 | 4 | 37146 | 28455 | 27401 |
| russellmitchell | 123332 | 629 | 99635 | 23697 | 11 | 4 | 17879 | 9711 | 17250 |
| santos | 178744 | 737 | 151319 | 27425 | 8 | 4 | 22064 | 7885 | 21327 |
| shaw | 280536 | 220 | 202200 | 78336 | 3 | 5 | 2100 | 31266 | 1880 |
| wardbeck | 246907 | 1084 | 221624 | 25283 | 8 | 4 | 19985 | 11024 | 18901 |
| wheeler | 284035 | 13510 | 223034 | 61001 | 8 | 3 | 52189 | 28270 | 38679 |
| wilson | 417672 | 10175 | 299808 | 117864 | 10 | 4 | 103762 | 46161 | 93587 |

**Aggregates over the eight organisations, canonical order (true / false discoveries / Σ per-alert r\*):**
flow-only horizon-free 79 / 4 / 607,802; flow-only horizon-aware 80 / 5 / 599,967; host-conditioned
horizon-free 53 / 1 / 349,165; host-conditioned horizon-aware 59 / 7 / 449,297. 37 of the 95 malicious
episodes contain benign flows (`mixed`), median benign share 0, maximum 0.50–0.71 per organisation. In
every cell with a false discovery, none precedes the first true detection in the test order.

**What the probe settles.**
1. *The horizon-aware baseline is non-degenerate but is not the LSPR23 contrast.* On LSPR23 uniform
   spending turned 3 alerts into 105 because T = 57,368 made the polynomial tail bind. On AIT T is
   1,664–5,082 and ρ is 1.6–5.5, so the horizon-free controller already detects most malicious episodes
   and the uniform allocation adds one flow-only detection and six host-conditioned ones. The horizon-aware
   arm is cheap to run and should be run (the reviewer asked for it), but the experiment's information
   will come from the other two channels, not from the spending regime. Say so in the write-up.
2. *The "non-attacker alert" channel exists and is concentrated.* Under host-conditioned horizon-aware
   spending `shaw` issues 6 false discoveries (arity ~37, evidence ~1.4e5, i.e. episodes with about two
   thirds of their flows firing) and `wardbeck` 1; the flow-only arm has 1 each on `russellmitchell`,
   `santos`, `shaw`. These raise R for every later own alert and cannot be padded by the attacker.
3. *The firing-pad channel exists on the host arm.* Pool fire in the pad's own context: 0 on four
   organisations, 2.9e-4–1.3e-3 on three, 7.0% on `shaw` (t54's known case). On the flow arm 4e-5–5e-4.
4. *m_atk < m on 37/95 episodes.* The state-free policies must pad from the attacker's own flow count;
   the probe shows the resulting under-provisioning is usually nil (median share 0) but reaches 50–71%.
5. *Compute is not a constraint.* Downstream rows a pad event can touch: at most 104k (wilson, flows to
   victims) per organisation; HGB scoring runs at ~1e6 rows/s. With the lazy cumulative-offset scheme in
   §3.3 one joint trajectory costs well under a second; D = 100 trajectories × 64 cells × 7 attackers is
   under an hour on this workstation, less with one process per organisation.
6. *Ownership is multi-host.* 3–5 attacker source hosts and 3–11 victims per organisation; pads are
   identified per episode by that episode's own (src, dst), so no single-attacker assumption is needed
   beyond the pinned-peer rule already in the paper.

## 6. Open decisions for the authors

1. **Cell scope and draws.** Proposed: all 64 cells (8 orgs × 2 arms × 2 orders × 2 allocations),
   D = 100 pad-sampling trajectories per (cell, attacker). Primary cell for the body: host-conditioned,
   canonical, horizon-aware; the flow-only arm is the context-free control; first-flow and horizon-free
   are labelled sensitivities. Alternative: D = 200 to match t54's `D_REPLAY`.
2. **Budget policies (§4).** P1 (c = 3, carried from LSPR23) is expected to fail widely on AIT because
   the host arm's own arities are 3–28 flows while per-alert costs are tens to hundreds; that failure is
   informative (the LSPR23 prescription does not transfer) and cheap. P2 (⌊ρ_org⌋+1 = 2–6) is the paper's
   own prescription evaluated where both of Corollary 2's hypotheses fail. Optional third K0 policy if
   the reviewer wants a *total* budget: a per-organisation flow budget B spread over own episodes in
   proportion to m_atk — not proposed, since P2 already is a total budget (c−1)·Σ m_atk.
3. **Pad pool causality — decided after the audits.** Primary = causal pool (§3.3); t54's whole-deployment
   pool is the labelled non-causal sensitivity. Reversing this would make the "causal replay" attacker
   clairvoyant (both audits called it CRITICAL).
4. **Within-bucket rule — decided after the audits.** K0 policies never read the controller, so the
   problem does not arise for P1/P2. The K1 arms use the bucket fixed point (§3.4) and are labelled
   non-causal within a bucket, which is the knowledge the paper's oracle `r*_t` already grants.
5. **Downstream update scope.** Rescore only flows with the padded pair's src or dst after t_atk (exact
   for the six features on the virtual timeline of §3.0, validated against a full rebuild on seeds 0–4 of
   every cell and attacker). Flows at or before t_atk do not see the pads.
6. **Body space.** A short paragraph in Sec. V-F plus one Table IV row, paid for by retiring the
   Limitations clause "the host-conditioned and AIT studies rescore per alert, not jointly" and the
   per-alert 108-vs-118 host-context sentence, which the joint result supersedes. Table II/XXXV gain a row
   only if the reviewer's dependency framing needs one (joint AIT: valid e no, A1 no, labels/ownership
   yes, windows AIT).
7. **What the paper may claim afterwards.** Only what the cells show: per-cell remaining true alerts and
   total padding under each pre-committed policy, with failure classes. No "the mechanism survives"
   sentence unless every primary-cell organisation shows it, and no strengthening of the LSPR23 numbers.

## 7. Wiring the stage will need (same as every prior stage)
`src/runner.py` EXPERIMENTS entry; `src/paper.ipynb` result cell; `paper/make_appendix_tables.py`
table + prose companion; `proto/t61` ORDER registry + numeric checks; `proto/t65` claim pins for any
body sentence; `proto/t71` ledger row; `docs/04` §4.72; t70 (producer in `src/lib`). Body space:
the body ends on p.12 at layout line 50 of 57, so a body paragraph plus a Table IV row needs a
same-size cut (candidates: the per-alert host-context sentence in V-F once the joint host result
supersedes it; the Limitations clause "rescore per alert, not jointly", which the result retires).

## 8. Blind audit log

**Round 1 (7 Sep 2026, two independent `codex exec` runs on the v1 note, brief `brief_design_audit.md`).**
Both confirmed every factual claim about the code except three wording points (t75 works on
`Ev0.copy()`, not in place; t51 runs no controller; the data path and timings are environment facts) and
both returned **No** with the same four CRITICALs, all accepted:
1. Pads at `t_end` collided with the strict-timestamp feature semantics (`build_host_features` excludes
   ties; t54's `_episode_base_state` uses `ts <= t_end`; `_replay_ctx(k)` adds k−1) → §3.0 virtual-time
   model, stated explicitly, plus validation against a full rebuild.
2. The primary pool leaked the future (templates later than the pad time) → causal pool primary (§3.3),
   t54's pool demoted to a labelled non-causal sensitivity.
3. P3 was adaptive, not pre-committed; the "size in t_end order, test in controller order" rule had no
   defined live level → P1/P2 are the only budget policies (K0); the capped attacker is CAP-ORACLE (K1)
   with the bucket fixed point (§3.4).
4. The attacker information set was undefined within a bucket → K0/K1 stated (§3.2); K1 labelled
   non-causal within a bucket.
MAJORs accepted: later targets' base context must include earlier pad events on shared hosts (§3.0);
no subset-of-baseline assertion, count created alerts separately (§3.0); realised FDs carry no
guarantee (§3.5); pure/mixed decomposition (§3.5); exclusive ordered failure classes with conservation
(§3.6); estimands and uncertainty defined, t54's success-conditional median not reused (§3.5); seeds,
D, cap grid and primary cell fixed here (§3.1, §3.3, §3.4). MINORs accepted: `m_total`/`m_atk`/`r`
naming; calibration invariants asserted; environment-specific data/compute wording.

**Round 2 (7 Sep 2026, two independent runs on v2, brief `brief_design_audit_v2.md`).** Both again
returned **No**, but the findings changed kind — from soundness to executability/completeness. Accepted
and applied in v3: the attacker cannot know `t_end` when co-resident benign flows end its episode →
pads are inserted after the attacker's **own** last flow `t_atk` (§3.0); the template pool is an
evaluation device shared with t48/t54/t74, not attacker knowledge, and the K0/K1 sets are about
controller and score knowledge only (§3.2); an empty causal pool must never fall back to t54's
zero-firing default → `pool-extended` / `pool-unavailable` classes with N_min = 20 (§3.3); equal-
timestamp serialisation by global rank (moot on AIT: no ties, asserted) (§3.0); the fixed point's
state, frozen set, pre-drawn sequences, single-pad steps and stopping rule (§3.4); alert identity,
denominators and ordered exhaustive classes with conservation (§3.5–§3.6); `M = |C|+1` everywhere;
T is the defender's declared horizon read as configuration (§4); full rebuild over the whole
organisation stream with original episode ids, predetermined seeds 0–4, input md5s in the JSON (§3.0).
Not accepted: relabelling P1/P2 as "stronger than K0" — the paper's state-free attacker already knows
the controller's configuration (ρ = Mα/T), and t76 inherits that definition rather than inventing a
weaker one; the note now says so instead of implying K0 knows less than it does.

**Round 3 (7 Sep 2026, two independent runs on v3, brief `brief_design_audit_v3.md`).** Q1 (insertion at
`t_atk`) and Q6 (full-rebuild validation) SOUND in both; Q5 (K0 framing, P1/P2 pre-commitment) SOUND in
one, the other asking for scope wording. Both verdicts still "No", on the same two remaining
specification gaps, both closed in v3.1: (a) the fixed point had no transition for a `pool-unavailable`
own episode → F is initialised with them and they never consume a template (§3.4); (b) "need" was
ambiguous between total-from-original and additional-from-current, and the SEQ/CAP budgets were not
named → total quantities from the original flows, one budget `B_j` per attacker, three inequalities
that partition the firing episodes (§3.6). MAJORs applied: `pool-extended` is a reported stratum (§3.3);
`M = (|C|+1)/k`; P2 is Corollary 2 only in the uniform cells (§4); `m_atk` vs t75's `m_total` stated as
deliberate (§4). No fourth design round: the findings have moved from soundness (round 1) to
executability (round 2) to corner-case transitions (round 3), and the last two are now specified. The
CODE of t76 gets its own blind audits before any number enters the paper.

**Status: v3.1 is the implement-from version, pending the author decisions in §6 (cell scope / D, the
non-causal-pool sensitivity, body-space cut).**

## 9. Adopted scope (7 Sep 2026) — the "joint AIT stress test", as implemented in `src/lib/t76_joint_ait.py`

The author's review of this note (7 Sep) narrowed it to a hypothesis-driven stress test and this is what
runs. Question: when pads can carry evidence and unrelated alerts can replenish e-LOND's rejection state,
does joint suppression still collapse the trajectory, and what makes it fail when it does not?

| arm | scope |
|---|---|
| clean baseline | R, own alerts, non-attacker alerts, per organisation, both spending regimes, canonical order only |
| GREEDY (K1) | the LSPR23 sequential oracle with sampled real pads; flow-only on all eight organisations, host-conditioned on the two the paper already covers (`shaw`, `wilson`); per-bucket fixed point on the host arm (§3.4), which reduces to the plain sequential walk on the flow arm because context-free pads change only their own episode |
| MULTIPLIER (K0) | c = ⌊ρ⌋+1 (Corollary 2's integer prescription) and c = 3 (LSPR23-carried), each in a THEORY variant sized on the observed total arity m_total and an OPERATIONAL variant sized on the attacker's own m_atk; no controller read; the padded stream is regime-independent and is evaluated under both spending sequences |
| pools | primary causal pool (§3.3) for every attacker; t54's whole-deployment benign-to-any-victim pool as the labelled comparability arm for every attacker, so template availability can be separated from non-attacker alerts |
| not run | first-flow order, the cap grid (answered jointly on LSPR23), host arm beyond two organisations, any new detector or dataset |
| reporting | per organisation and regime: baseline own / non-attacker alerts, ρ, c_int, greedy remaining (median, 5–95%), greedy total pads (median, 5–95%), P(all silenced), pads that fired, non-attacker alerts and created alerts on the attacked trajectory, multiplier remaining with the four outcome classes; one figure panel (organisation on the x-axis, baseline own alerts falling to joint remaining, annotated with non-attacker alerts) |

Wording adopted from the review: the multiplier arm *stress-tests the sufficiency boundary outside the
conditions of Corollary 2 and identifies which conditions are operationally load-bearing*; it does not
"test the corollary where its hypotheses fail".

Deviations from the review's sketch, each carrying an audit finding from §8: pads are inserted after the
attacker's own last flow, not the episode's end; the primary pool is causal, with the existing pool as
the comparability arm; the host arm uses the per-bucket fixed point rather than a chronological walk in
controller order, which is not chronological within a bucket.

## 10. Implementation and code audits (7 Sep 2026)

Stage: `src/lib/t76_joint_ait.py`, registered in `src/runner.py`. Artefact `src/lib/out/t76_joint_ait.json`
(manifest written before any result; per-organisation pre-commitment record — declared horizon T, |C|,
ceiling, ρ, c_int, seeds, input md5 — written before that organisation's attackers run).

**Round 4 (two blind runs, brief `brief_code_audit.md`).** Both returned *No*. The scope complaints
(64 cells, eight-organisation host arm, cap grid) were **rejected**: the brief pointed the auditors at
§3 instead of §9, so they audited a superseded spec; §3 now cross-references §9. Accepted and fixed:
the greedy pad search committed doubling chunks before re-scoring (design says one pad per fixed-point
step); the causal pool concatenated calibration templates into *every* pool instead of only undersized
ones (they are zero-evidence by construction under k = 1, so they diluted the firing rate everywhere —
the visible effect of the fix is fox's horizon-aware causal arm going from 46k pads with 16 firing to
62k with ~2.4k firing); the `m_total` multiplier was emitted under the state-free heading (now
`oracle_m_total`, flagged `k0: false`, with the knowledge it uses spelled out in the JSON); non-attacker
alerts were reported as an attacked-run total (now split into surviving and created); a skipped rebuild
validation counted as a pass.

**Round 5 (two blind runs on the fixed code, brief `brief_code_audit_v2.md`, scoped to §9).** One found
no CRITICAL; the other found one, accepted: on the host arm a pad of episode j can re-score a flow of an
episode **earlier in j's own bucket**, which changes R before j and hence j's own live level, so a batch
sized at the pre-pad level is stale. Fixed by computing, per episode, whether that is structurally
possible (`exact_level`) and falling back to one pad per fixed-point step when it is; the flow arm is
provably exact because a pad there touches only its own episode. Also applied: both pool kinds are
validated and the comparability pool is labelled `noncausal_oracle_pool` everywhere; attempted / spared /
suppressed denominators, pads spent on failures and the pool-extended stratum are reported; conservation
(own baseline alerts = suppressed + the four classes) is asserted per trajectory; the in-file controller
walk is compared with `run_lond` on every K0 attacked stream; the causal pools are hashed and asserted
unchanged. A vacuous assertion introduced during the fix was removed rather than left in place.

**Two defects found by running it, after the audits (7 Sep 2026).** Both were introduced by the round-5
repairs and are recorded because neither audit could have seen them without execution:
1. *Return-contract bug.* Making `pad_until` append a single pad meant it returned "not suppressed",
   which the caller read as "freeze this episode": the host arm stopped after one pad and reported three
   surviving alerts at a cost of one flow. The function now returns `suppressed` / `step` / `frozen` and
   only `frozen` ends the attempt.
2. *No futility rule.* With a causal pool whose flows fire, the mean pad evidence can exceed the
   episode's threshold, in which case no number of pads can dilute the mean below it and the greedy
   attacker pads to `SIM_CAP` one flow at a time. The stage now stops an attempt once at least
   `FUTILE_MIN = 1024` pads have been sent and their running mean is at or above the threshold — sound
   because the episode mean is bounded below by the pad mean as the count grows — and records those
   episodes as `n_futile` within the `pad_fired` class. This is a measurement, not a workaround: on
   `shaw`'s host-conditioned arm the causal pool is exactly this case.

## 11. What the result changes in the paper (plan, for the author's decision)

The body ends on p.12 with about seven layout lines of slack, so the additions below are costed against
cuts the result itself retires.

**Retired by the result (cuts that pay for it).**
- Limitations, `sec:limitations`: "The joint rerun covers zero\nobreakdash-evidence pads on the baseline
  e-LOND trajectory; the host-conditioned and AIT studies rescore per alert, not jointly." The second
  clause is now false; the sentence shrinks to the zero-evidence scope of `t75`.
- Sec. V-F's per-alert host-context sentence (median suppression cost 108 against the flow-level 118) is
  superseded by a joint number on the same two organisations.

**Added.**
1. One short paragraph in Sec. V-F (the AIT transfer subsection), reporting: the joint attacker with the
   pool every per-alert AIT number uses silences 78/79 and 80/80 baseline detections at 15–40% of the
   per-alert sum; restricted to cover traffic the victim had already received, the same attacker clears
   no organisation and 24 / 27 alerts survive, chiefly because 30 of 95 attacker-owned episodes have
   fewer than 20 prior benign flows to their victim; and the state-free multiplier of \cref{cor:dilution}
   leaves 65 / 60 alerts standing, with an oracle-arity variant leaving exactly the same ones.
2. One row in Table IV (`tab:main`) for the joint AIT arm, or a column if the table can carry it.
3. Figure 4 gains a third panel: organisation on the x-axis, baseline own alerts falling to joint
   remaining under each pool, annotated with the non-attacker alert count. It is already a `figure*`.
4. `tab:scope` and the Sec. I dependency table gain a joint-AIT row: valid e-value no, A1 no,
   labels/ownership yes, windows AIT.

**Claims that must be re-worded, not merely extended.**
- Anything that presents the AIT per-alert suppression counts without naming the pool. The counts hold
  for a pool drawn from the whole deployment window; they do not hold for one restricted to the victim's
  prior traffic, and the paper should say which it uses.
- \Cref{cor:dilution}'s empirical companion sentence: the corollary is a horizon-uniform statement whose
  hypotheses AIT violates, and the run now measures *which* violated hypothesis matters. The honest
  phrasing is that the run stress-tests the sufficiency boundary outside the corollary's conditions and
  identifies the operationally load-bearing one, which is neither arity uncertainty nor firing pads but
  the absence of usable cover traffic for a third of attacker-owned episodes.

**Gates to update after the wording lands:** `t61` (a new artefact and its numbers), `t65` (any new
pinned body sentence), `t71` (a ledger row for the joint AIT claim), `t45`/`t70` (the new stage is
already registered in `src/runner.py`), plus `paper.ipynb` and `make_appendix_tables.py` for the
appendix table and its prose companion.

**A third defect execution found: single-pad stepping is intractable where the pool never fires.**
`wilson`'s host-conditioned pool fires at zero, so the futility rule never applies and the greedy
attacker genuinely needs tens of thousands of pads per alert; at one controller re-test per pad, with 11
baseline alerts and 100 trajectories, one greedy arm ran for over 80 minutes without finishing. The fix
is a **bounded burst**: where a chunk cannot be proved exact, the attacker sends `CHUNK_INEXACT = 256`
pads and the caller re-scores and re-tests between bursts. This makes that attacker act on state up to
one burst old, so its reported cost is an **upper bound** on the fully-informed oracle's — a burst is
only ever sent while the episode was still firing at its start, so the count can overshoot by at most one
burst per episode and never undershoot. `n_inexact_bursts` is reported per cell. Where a chunk *is*
provably exact — the flow arm always, and on the host arm any episode with no original flow after `t_atk`
and no earlier-position episode in its bucket that its pads could re-score — doubling chunks are used and
the result is identical to appending one pad at a time. The flow-arm numbers are therefore unchanged by
this fix; only the host arm's oracle costs acquire the upper-bound qualification, and they must be
labelled that way wherever they appear.

## 12. What actually went into the paper (7 Sep 2026)

Decisions taken by the author: the causal-pool failure and the joint transfer are stated together as one
boundary; the state-free negative goes to the appendix with one body clause; a Table I row rather than a
Figure 4 panel; no abstract change.

**Body (Sec. V-F, two sentences added to the AIT paragraph).** "Both counts price each alert at the level
it received on the unperturbed run. Re-running the controller over the padded stream prices the campaign:
at 40% and 15% of the per-alert sums it leaves one and none of the 79 and 80 canonical-order detections
standing, and 24 and 27 when the attacker may draw only on traffic the victim already had." Plus a Table I
row (`244,250` total, 78/79) with a one-clause caption, and in Sec. V-C the corollary sentence now ends
"and \cref{app:ait} measures it where they fail".

**Appendix.** `apptab:joint76` (per organisation, both pools, both spending rules) and a generated prose
companion carrying the totals, the pool definitions, the host-conditioned arm and the arity-oracle
comparison. Both are produced by `make_appendix_tables.py`, so every number is artefact-derived.

**Cuts that paid for it.** The Limitations clause "the host-conditioned and AIT studies rescore per alert,
not jointly" is now false and was replaced by the zero-evidence/upper-bound scope; the LSPR23
host-context parenthetical (108 vs 118 flows) moved into `apptab:r7host`, keeping its "seed 0,
horizon-free, first-flow" label because `t65` requires the order label at the point of claim; and the
first-flow resequencing sentence was shortened while keeping the pinned "gives 84 of 85".

**Space, measured rather than assumed.** The body had about eleven rendered rows of slack, not the eight
that source-line counting suggested, and a two-column paragraph break costs rows of its own. The first
draft of the addition ran the body onto p.13; it fits only as two sentences merged into the existing
paragraph. The `padded arity 91 / 55` sentence in Sec. V-D was considered as a cut and rejected: `t61`
pins it, and trading a pinned claim for space is the failure mode the round-27 notes warn about.

**Verification.** All seven gates pass (t45, t61, t65, t68, t69, t70, t71), including two new `t71`
ledger rows for the joint campaign cost and the causal-pool survivors, and a `t61` ORDER-registry entry
for the new table. The stage's manifest now declares `orders`/`canonical_order` so the registry can see
that it runs one order; the artefact's manifest was aligned to what that code emits, which changes the
description of the run and no result. Body ends on p.12; 42 pages total.
