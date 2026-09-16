# Documentation Index

**Online statistical error control for ML intrusion detection.** Target IEEE SaTML 2027 —
abstract **22 Sep 2026**, paper **29 Sep 2026**, internal gate **experiments complete 15 Sep**.

Files are numbered in **read order**, not chronological order: the low numbers are what you need
now, the high numbers are why things are the way they are.

---

## Start here

**A new agent or collaborator reads `01` and `02`, in that order, and nothing else until those
are done.** `01` tells you which of the remaining files matter and which will actively mislead
you.

---

## Tier 1 · Active — 01–05

| # | File | What it is |
|---|---|---|
| **01** | `01_HANDOFF_PHASE4.md` | **Start here.** Environment, shared modules, established results, the twenty-five mistakes already made, settled framing decisions, the mandatory audit procedure, how to record results |
| **02** | `02_WORKPLAN_PHASE4.md` | **The active task list.** Twelve experiments E1–E12 with tickable boxes, pre-assigned section and finding numbers, acceptance criteria, decision logic |
| **03** | `03_FROZEN_CLAIMS.md` | What may be claimed and at what strength: 3 headline claims, 16 supporting, 7 caveats, 10 non-claims, 12 refuted hypotheses. **E1, E2, E3 and E12 have landed; all three headline claims are closed** |
| **04** | `04_EXPERIMENTS_AND_FINDINGS.md` | **The authoritative record.** §1 = findings F1–F24; §4.1–§4.42 = the experiments (§4.37 reserved for E4); §5 = claim strength; §8 = reproduction. ~200 KB — **grep it, don't read it end to end** |
| **05** | `05_PAPER_CONTRACT.md` | Title, thesis, three contributions, four RQs, threat model, seven figures, exclusions, writing order. **Do not draft against it until Tier 1 experiments close** |

## Tier 2 · Current reviews, already processed — 06–08

Inputs that produced the Phase 4 plan. Read for an experiment's original motivation; do not act
on them directly.

| # | File | Note |
|---|---|---|
| 06 | `06_PHASE3_REPORT.md` | What Phase 3 closed (A1, A2, B1), item-by-item against the plan it answered, plus its own self-identified gaps |
| 07 | `07_phase3_next_step_recommendation.md` | ⚠️ **Says "start writing the manuscript now" — that was overruled.** Its *claim-framing* decisions were adopted and live in `01` §5 |
| 08 | `08_satml_reviewer_gap_experiment_checklist.md` | Source of E1–E12. Digested into `02` with three corrections |

## Tier 3 · Superseded plans and trackers — 09–13

| # | File | Superseded by |
|---|---|---|
| 09 | `09_WORKPLAN_phases1-3.md` | `02`. Records T1–T11 and H1–H8; its §14 freeze note points forward |
| 10 | `10_HANDOFF_PHASE2.md` | `01`. §5's task list is history; the rest is folded into `01` |
| 11 | `11_next_actions_updated_experiments.md` | `06` answers it item by item |
| 12 | `12_review_experiments_and_next_actions.md` | The external review that produced T1–T11 |
| 13 | `13_PLAN_v3.md` | Explains where T1–T11 came from |

## Tier 4 · Origin and history — 14–19

Read only to answer "why was this decided". Two repositionings happened after these were written.

| # | File |
|---|---|
| 14 | `14_NOVEL_CONTRIBUTION.md` |
| 15 | `15_PROTOTYPE_FINDINGS.md` |
| 16 | `16_detailed_feedback_revised_fdr_ids_project.md` |
| 17 | `17_FEEDBACK_ON_ORIGINAL_PROPOSAL.md` |
| 18 | `18_fdr_trustworthy_ids_research_idea_corrected.md` |
| 19 | `19_fdr_trustworthy_ids_research_idea.md` |

---

## Where everything else lives

```
proto/*.py          55 scripts, t1…t40 (chronological, not thematic) + shared modules
                    h_stream.py · h6_procs.py · h_meta.py
proto/out/E12_triage.md   the E12 second-dataset triage record (verdict: no such dataset)
proto/out/*.json    every experiment's raw output
proto/out/*.log     run logs and codex audit transcripts
proto/data/         LSPR23, the red-team narratives, AIT NetFlows
/tmp/lspr_*         derived feature files and .npy caches — regenerate per 01 §2.2
```

## Conventions

- **Verification tags** on every claim: `[EXACT]` analytic · `[SIM]` synthetic · `[REAL]`
  measured · `[PRIOR]` published elsewhere · `[ORACLE]` uses information a deployment lacks ·
  `[OPEN]` not done.
- **Findings** are `F1`–`F24`; new ones continue at `F25`. **Experiment sections** run to
  `§4.42`, with `§4.37` reserved for E4 and `§4.43` for E12's triage record. Both are
  pre-assigned in `02` §8.
- Say **episode**, never *incident* — LSPR23 has no flow→campaign ground truth.
- `04` is written as **current state only**, never as a change log.
- Nothing enters the record without a blind adversarial audit first (`01` §7).
