# Round 29 — AIT cost semantics, SaTML LLM statement, dependency rows, Table V/VI floats (points 1–12)

Validated 6 Sep 2026 before planning:

| Point | Validation | Decision |
|---|---|---|
| 1 AIT cost definition | `t67_ait_order.summary.canonical.median_rstar_by_org` — what Fig. 4B plots and Table XXXII lists — equals the EMPIRICAL per-organisation medians (`arms.keyhash.rows[*].median_rstar_empirical`; russellmitchell 4,650 vs closed-form 4,132; the other seven organisations coincide). Fig. 4B's caption and axis and Table XXXII's caption call them oracle lower bounds: mislabelled. Table IV already says "empirical replay median" for AIT | ACCEPT: one convention — AIT body/appendix figures and tables report the empirical replay cost, written $r^{\star}_{t,\mathrm{emp}}\ge r^{\star}_t$ and labelled so (Fig. 4B caption and axis, Table IV cells "(emp.)", Table XXXII caption/header, App. E prose, Table XXXI headers); the closed-form lower bound stays alongside in Table XXXI |
| 2 SaTML statement | absent; "Large language model assistants (Claude Code and Codex CLI)" is a client/model category error; log re-check: Claude Code client versions 2.1.241–2.1.261 (paper said 2.1.246), models `claude-opus-5`, `claude-opus-4-8`, `claude-fable-5-1`, `claude-fable-5`; Codex CLI 0.142.3 and 0.152.1, models `gpt-5.5`, `gpt-5.6-terra`, `gpt-5.6-sol` | ACCEPT: verbatim checklist sentence inserted; clients-vs-models sentence; one duplicate review sentence removed; version range corrected to 2.1.241–2.1.261 |
| 3 dependency rows | Table II and Table XXXV lack the joint rerun and the aggregate rows; ownership via labels stated only in VII-B | ACCEPT the five-row scheme (column "labels / ownership"); same in `tab:scope` with windows |
| 4 Table V float | current build: Table V at the top of p.11 above Sec. VI-A's continuation, Sec. VII below it — the reviewer's PDF (previous build) had it splitting VII-B | Try `[!t]` + `\FloatBarrier` before Sec. VII; then moving the source; keep whichever leaves the body on p.12 with the table on Sec. VI's page; no font change |
| 5 abstract phrases | "On LSPR23, this produces" and "horizon-free allocations cost more" are both t65-pinned | ACCEPT both substitutions; pins re-anchored; cap 240 if needed |
| 6 contribution 3 | "establish the mechanism beyond the original configuration"; one sentence carries three claims | ACCEPT "support transfer of the mechanism beyond the baseline configuration"; split into three sentences |
| 7 post-corollary sentence | :752 drops the corollary's assumptions | ACCEPT reviewer's sentence |
| 8 Table I row | "Batching and grouping recover online power [18]" | ACCEPT "Batching can recover online-testing power"; right cell as proposed |
| 9 "a third position" | :283 | ACCEPT "The 0.85 position has a benign tail…" |
| 10 Fig. 1 caption | "needs no detector access" contradicts the oracle sizing | ACCEPT reviewer's two sentences |
| 11 "exact per-alert costs" | contribution 3 :228 | ACCEPT the two-part LSPR23 / AIT statement (also resolves point 1's prose side) |
| 12 Table VI placement | floats through the procedure definitions on p.20 | ACCEPT: `placeins`, `\FloatBarrier` before the Procedure-definitions subsection |

Budget: ~5 body lines of additions against ~5 lines of slack. Gates: t65 (two abstract pins, cap),
t61 (tab:main rows unchanged in the checked fields), t68 after the float changes, t69 untouched.

## Execution log

**Applied 6 Sep 2026 (points 1–12).**
- 1: AIT costs are the empirical replay medians $r^{\star}_{t,\mathrm{emp}}$ everywhere they appear in the
  body and appendix (Fig. 4B caption and axis label in `src/lib/figures.py`, Table IV cells marked
  "(emp.)" with the caption defining both quantities, Table XXXII caption and header, Table XXXI headers,
  App. E prose, Terms table); Sec. V-F defines $r^{\star}_{t,\mathrm{emp}}\ge r^{\star}_t$. Artefact check:
  `t67.summary.canonical.median_rstar_by_org` equals the per-organisation `median_rstar_empirical`; the
  closed-form median differs only for russellmitchell (4,132 vs 4,650), which Fig. 4's caption states
  ("equal for seven of eight organisations").
- 2: SaTML's editorial-use sentence inserted verbatim; opening rewritten as hosted LLMs accessed through
  the two clients; two duplicate review sentences removed; client range corrected to 2.1.241–2.1.261 after
  re-reading the logs (models and Codex versions unchanged).
- 3: Table II and Table XXXV carry the five-row scheme with "labels / ownership"; the caption says the
  labels serve as the ownership oracle.
- 4: no `\FloatBarrier` in the body: Table V renders at the top of p.11, above Sec. VI-A's continuation
  and VI-B, with the Sec. VII heading below it on the same page (Sec. VI starts p.10). The reviewer's
  paragraph-split complaint concerned the previous build (VII-B); a top float always splits the
  paragraph that runs across the page break, which t68 accepts by design.
- 5–11: applied as proposed (abstract 235 words, cap 240; contribution 3 split into three sentences with
  "support transfer"; post-corollary sentence carries the assumptions; Table I attributes only batching to
  [18]; "The 0.85 position…"; Fig. 1 caption's oracle-vs-state-free sentence; two-part LSPR23/AIT replay
  statement).
- 12: `placeins` loaded; `\FloatBarrier` before the Procedure-definitions subsection; Table VI now
  precedes that subsection (p.21 top, immediately after the Terms text).

**Budget.** ~10 body lines added (Table II rows, contribution split, Fig. 1/4 captions, V-F definition);
paid by: Sec. VII-C folded into one sentence at the end of VII-B (label kept), Related Work Huo sentence
pointing at Sec. III-A, II-D's calibration-range sentence (the appendix lists the five values),
sentence merges in II-B, III-A, III-C, V-F, Table I's cell shortened, Fig. 2 at 0.70. Body ends p.12 at
layout line 50 of 57. Gate pins: t65 R13-4 and R25 abstract strings re-anchored, cap 240, the oracle
allow-list gained "oracle for which episodes" and "sizing is oracle"; an explicit hyphen in
"zero-evidence" at a column break is now `\nobreakdash`. Gates: t61 240/0, t65 194/0, t71 34/0,
t68 2/0, t69 0 drift, t45 268/0, t70 ok; 41 pages; 0 Type 3 fonts.

**Blind confirmation (one codex run, `confirm_r29.md`).** Ten FIXED, two PARTLY, repaired: Table XXXV's
caption now says the labels serve as the ownership oracle (the body's Table II already did), and
contribution 3 is three sentences as asked (LSPR23 replay + multiplier; Corollary 2; AIT replay +
transfer). The auditor's source-text word count of the abstract is 241; t65's whitespace count is 235
against a cap of 240 — the difference is tokenisation of hyphenated compounds, not extra words.
Re-compiled and re-gated after the repairs.
