# Round 26 — abstract exactness, attack-cost taxonomy, Corollary 2, appendix hygiene

Worklist for the seventh external read of `paper/satml.tex` (draft after round 25b: body ends p.12,
41 pages). The reviewer's text is `SaTML_2027_r26_feedback.md` (16 points). Every point was checked
against the draft, the gates and the artefacts before this plan was written (6 Sep 2026).
**Nothing is strengthened without a new experiment**; the one substantive addition (Corollary 2) is a
theorem whose conclusion the existing artefact `t75_joint_rerun.json` already verifies numerically
(`critical_multiplier`: `c_crit_equals_rho`, `remaining_true_above == 0`, `remaining_true_int == 0`).

## 0. Facts the plan rests on (verified 6 Sep 2026)

| Fact | Where checked |
|---|---|
| Equation numbers: (7) = `eq:exchange`, (8) = `eq:rstar`; the reviewer's references are right | `grep begin{equation}` |
| "Jseq" does not occur in any source; the 7 hits in `pdftotext` output are subscript flattening of `$J_{\mathrm{seq}}$` | tex, tables, generator |
| Table III (`tab:costcurve`) source sits at the top of Sec. V-A (`:645`); its caption is 10 lines; t65 pins two caption strings (R23 "upper bound on the cost of jointly suppressing that set", R24-2 "one false discovery is not in that sum") via `_blk("Effect of spending allocation…")` | `t65:1172–1187` |
| Table V (`tab:defenses`) is a `table*` at the top of Sec. VI (`:944`); in the current build it lands at the top of p.11 above Sec. VI-B's continuation; Sec. VII starts p.11 | render p.10–11 |
| Table VI = `tab:terms` (p.20); XXXIV = `apptab:joint` (p.38, 341-word caption); XXXVII = `apptab:a1strata` (p.39, 529 words — the caption fills two thirds of the page and the right column is blank); XLV = `apptab:feedback` (p.41). Other captions > 300 words: semblur 550, aitsupp 402, r7host 359, prevalence 339, w3dilution 330, blindkey 324 | layout text, word counts |
| t61 reads `tables/*.tex` into `ALL_TEX`, so a phrase moved from a caption into the appendix prose stays findable; but its ORDER registry reads the table FILE for the order words ("canonical"/"first-flow" for semblur; "order-invariant" for a1strata) | `t61:54, 803, 834, 1131` |
| t69 freezes 13 labelled statements + every `\begin{proof}` in `appendix_proofs.tex`; adding a corollary and its proof requires a `--refreeze` after a blind audit; `cor:closureabsorb` is referenced by label only, never as "Corollary 2" | `t69:56–70`, grep |
| Type 3 fonts in the PDF come only from the six matplotlib figures (TimesNewRoman, DejaVuSans, STIXNonUnicode); `src/lib/figures.py` sets no `pdf.fonttype`; `paper/make_figures_satml.py` is the wrapper that rebuilds them | `pdffonts` |
| Logged LLM use (client session logs, this project only): Claude Code 2.1.246–2.1.261 with model ids `claude-opus-5`, `claude-opus-4-8`, `claude-fable-5-1`, `claude-fable-5`; Codex CLI 0.142.3 and 0.152.1 with model ids `gpt-5.5`, `gpt-5.6-terra`, `gpt-5.6-sol`. Provider-side snapshot dates are not recorded by either client | `~/.claude/projects/<repo>/*.jsonl`, `~/.codex/sessions` filtered by cwd |
| Hardware: this workstation is a MacBook Pro, Apple M5 Pro (18 cores), 48 GB, no discrete GPU; no artefact JSON records a platform, so "all runs were on this machine" is an author assertion, flagged | `sysctl`, `system_profiler`, JSON scan |
| Abstract pins (t65): ≤235 words; "attacker-influenceable", "cold-start values", "per-alert", "78 of 79 true detections", "Per-alert real-flow replay validates the zero-evidence pad model", "joint controller-state rerun", "sufficiently many zero-evidence additions drive an attained alert below threshold", "Even under the max-min-optimal horizon-uniform allocation", "horizon-free allocations cost more"; and the two that this round RETIRES: "On LSPR23's attack-only host pairs a state-free episode-size multiplier", "attack-only host pairs" | `t65` grep |
| Body pins touched: "We distinguish three attack costs" (t65:1073); "the cost of one greedy strategy on this stream, an upper bound on the minimum joint cost" (t65:1067); t71 rows anchored on "$5{,}650$ flows in total", "multiplying \emph{every} own episode by $c=3$ silences it at both windows", "where $m+r^{\star}>n$ predicts $91$ and $95$"; t61 quotes "horizon-free totals of $30$ and $859$", "so $c=3$ suffices and $c=2$ does not" | gates |

## 1. Decisions, point by point

| # | Point | Decision | Action |
|---|---|---|---|
| 1 | Abstract finite-horizon sentence over-general | **ACCEPT** (highest priority) | Replace with the reviewer's sentence; "finite alert lifetime" / "that lifetime" in Sec. I → "finite discovery horizon" / "that horizon"; "alert horizon" occurs only in the abstract |
| 2 | Grouping claim too absolute; Sec. IV local contradiction | **ACCEPT** | Sec. I sentence, Table I row 3, Sec. IV two sentences as proposed (the worked example stays between them) |
| 3 | Fig. 1 caption self-contradictory | **ACCEPT** | Last sentence replaced verbatim |
| 4 | "three attack costs" mixes knowledge, metric, strategy | **ACCEPT** | Paragraph replaced verbatim (`\statefree` macro); t65:1073 re-pinned |
| 5 | Define before Table III; shorten caption | **ACCEPT** | Taxonomy paragraph moves to directly after (8); Table III source moves to the head of V-D; caption cut to the reviewer's three sentences (+ "greedy oracle sequential attacker", point 7); ρ values, the FD-not-in-sum remark and the upper-bound remark move into V-D prose; t65 `_cap1` pins re-anchored to the prose |
| 6 | Notation r*_t, Σ_t r*_t; "Jseq"; "J_seq near the cold-start price" | **ACCEPT** for the body; **partial** for the appendix | (8) becomes $r^{\star}_t=\lfloor S_t\alphat\rfloor-m_t+1$; body uses $r^{\star}_t$ / $\sum_t r^{\star}_t$ (Table III header, tab:main header, Fig. 4 caption, V-C/D, VII-B); the joint appendix table follows. The other 33 generated tables keep $r^{\star}$ (several price it at the STATIC level, where a step subscript would be wrong); one sentence in the reporting conventions says so. "Jseq": nothing to do (extraction artefact). The semantic sentence is replaced as proposed |
| 7 | "oracle" visible in the headline | **ACCEPT** | abstract "greedy oracle joint cost"; Table III caption; V-D "one greedy oracle strategy and therefore an upper bound on the minimum joint cost"; t65 re-pinned |
| 8 | Abstract: LSPR23 vs AIT | **ACCEPT** | "and, on LSPR23, a measured feasibility–resolution–robustness tradeoff"; AIT sentence replaced by the reviewer's per-alert wording. The clause "AIT-LDSv2.0 supplies a benign-inclusive transfer test" is not duplicated: the AIT sentence two lines later names the testbed and the method |
| 9 | State-free multiplier sentence in the abstract | **ACCEPT (remove)** | Sentence deleted; t65 R14-3-abstract and the R25 "attack-only host pairs" pin retired in favour of an absence check (no unscoped "multiplier"/"state-free" claim in the abstract). Sec. I and V-C keep the scoped result |
| 10 | Unbounded-membership qualifier | **ACCEPT** | Folded into the abstract impossibility sentence ("Under unbounded membership … alert-capable symmetric e-merging rules"; the preceding sentence already says attacker-influenceable) |
| 11 | Promote c_int = ⌊ρ⌋+1 to a corollary | **ACCEPT** | `cor:dilution` in Sec. V-C (becomes Corollary 2; `cor:closureabsorb` becomes Corollary 3), proof in `appendix_proofs.tex`; hypotheses stated explicitly: horizon-uniform e-LOND, arithmetic mean, evidence ≤ M, every attacker-owned episode multiplied by c, and NO other hypothesis attaining the cold-start threshold T/α (needed for "rejection-free"; certified at both windows by `remaining_false_discoveries_int == 0`). t69 FROZEN gains the object; re-freeze only after the blind audit |
| 12 | Terms table | **ACCEPT** | Rows: per-alert padding cost $r^{\star}_t$; independent sum $\sum_t r^{\star}_t$; joint padding cost $J_{\mathrm{seq}}$ (joint controller-state rerun, Surface A); state-free multiplier $c$; controller-state attack cost $B^{\star}$ (ADDIS, Surface B) — with the rerun/attack distinction spelled out |
| 13 | Table V placement | **ACCEPT** | Source moves to the head of Sec. V-F so the `table*` lands on p.10, the page Sec. VI starts on; verified by render and t68 |
| 14 | Appendix captions; page 41 | **ACCEPT, scoped to three tables** | joint, a1strata (the two named) and semblur (the longest, 550 words): 1–2-sentence caption, definitions/interpretation as prose before the table (generator writes `tables/<key>_prose.tex`, `\input` before the table so the numbers stay artefact-derived), column qualifications in a `Notes:` paragraph under the tabular. Order words stay in the table file for t61's registry. **Deferred**: aitsupp 402, r7host 359, prevalence 339, w3dilution 330, blindkey 324 words. Target: appendix shorter by ≥1 page |
| 15 | LLM placeholders; "no smaller model" | **ACCEPT** (blocker) | Filled from the client logs above, with the snapshot-date gap stated; hardware from this workstation, flagged for author confirmation; the undocumented comparison replaced by the reviewer's sentence; the explicit editorial/coding sentence added |
| 16 | Type 3 fonts | **ACCEPT** | `pdf.fonttype = 42`, `ps.fonttype = 42` in `src/lib/figures.py` rcParams; all six figures rebuilt through the wrapper; `pdffonts` must report no Type 3 |

Declined: none. Every point is either applied or (14) applied to the named tables with the rest listed.

## 2. Order of work

A. Wording and moves (1–10, 12, 13) → compile, t65/t61/t71/t68.
B. Corollary 2 (11) + proof → blind codex audit (two runs) → repairs → `t69 --refreeze`.
C. Appendix restructure (14) → compile → t61 registry → render p.38–41.
D. Figures (16), LLM section (15).
E. Full compile, all gates, one refit if the body left p.12, blind codex audits of the wording/coverage
   and of the caption→prose fidelity, docs/04 note, memory.

## 3. Outcome

(filled in as the tiers close)

### Executed 6 Sep 2026 (all tiers)

**Body.** Abstract 234 words; body ends p.12 (Open Science begins at layout line 52 of 57 on p.12);
40 pages in all (41 before). Refit cuts, all content-neutral: Sec. I dependency paragraph to two lines
and the ADDIS pointer removed (Sec. VII-C keeps it); Sec. II-B campaign sentence (Sec. VII-B keeps the
limitation) and the guarantee-scope tail; Sec. II-D detector sentence; Sec. III-C appendix pointer;
Sec. V-A opening; Sec. V-C proof-idea sentence; Sec. V-D cap sentence; Sec. V-E pool and ordering
paragraphs; Sec. V-F closing; Sec. VI-A closing sentence (duplicated the Conclusion); Sec. VI-B two
implications; Sec. VII-B detector scope; Related Work Krönert sentence (kept "different object and
consequence", which t65 R18 pins); Conclusion one sentence; Fig. 1 at 0.86, Fig. 2 at 0.82, Fig. 4 at
0.88 of their measures (Fig. 3 must stay at full width, see round 25b).

**Floats.** Table III source now heads Sec. V-D and lands on p.9, after the taxonomy paragraph (p.8).
The defences table (now Table IV; `tab:main` is Table V) sits at the head of Sec. V-F in the source and
lands at the top of p.11 above Sec. VI's continuation (Sec. VI starts p.10, Sec. VII follows on p.11). A `table*` cannot land on the page where it is placed, so
its page is fixed only relative to the refit; re-check after any reflow.

**Corollary 2 (`cor:dilution`).** Two blind codex audits of the first statement: CRITICAL, a real
multiplier makes $(c-1)m_t$ non-integral, so the sharpness claim lived in a continuous relaxation;
MAJOR, the e-LOND level form and $R_0=0$ were not stated; MAJOR, the uniform-over-streams quantifier
needed the per-stream $c_{\mathrm{crit}}$ remark. Restated for integer $c\ge1$ (sufficiency $c>\rho$;
necessity for integer $c\le\rho$ once an attacker episode attains the ceiling; smallest uniformly
sufficient integer $\lfloor\rho\rfloor+1$), with the per-stream remark in the proof. Two further blind
audits: sound; two minor wordings applied. t69 re-frozen: 28 objects (14 statements + 14 proofs);
`cor:closureabsorb` is now Corollary 3.

**Appendix restructure (point 14).** joint (341→45 caption words), a1strata (529→46), semblur (550→48);
prose companions `tables/{joint,a1strata,semblur}prose.tex` are generated next to the tables and
`\input` in Appendices E (new subsection `app:joint`), F and D. Blind fidelity audit found: two dropped
joint clauses (silences the state-free arm; inclusive rejection needs strict exceedance) — restored;
three undefined joint columns — defined in the notes; and a PRE-EXISTING error inherited from the old
semblur caption: "under 10% of them overlap it in time" was true of the three temporal cells but the
sentence named windows, not cells, and 0.55/first-flow (a "thin" cell) overlaps at 13.1%. Now the
cells are named with their order and the bound is computed from the artefact ("at most 9%"). The
timestamp range of the task record and "six coarse segment labels" remain literals (not in the JSON;
carried over from the old caption, flagged by the audit).

**Gates.** t65 194/0 (9 pins re-anchored: R25 abstract spine, R14-3 body+abstract, R14-4 oracle
allow-list, R25 joint, R21-1, R23, R24-2, `_cap1` anchor); t61 238/0 (ORDER registry unchanged: prose
companions are written through `write_prose`, which the registry regex does not match; captions keep
the order words); t71 34/0 (cap row re-anchored to $m_t+r^{\star}_t$); t68 2/0 (stacked-float rule
rewritten: a column that OPENS with a float caption has only float material above any later caption,
because every float here is [t]/[!t]; the indent test could not separate a table*'s left half from
prose); t69 0 drift after `--refreeze`; t45 268/0; t70 ok. `pdffonts`: 0 Type 3 fonts (six figures
rebuilt with `pdf.fonttype=42`).

**LLM section.** Placeholders filled from the clients' session logs (model identifiers; snapshot dates
stated as not recorded); hardware from this workstation — **authors to confirm every reported run was
made on it**; the undocumented "no smaller special-purpose model" comparison replaced by the reviewer's
sentence; explicit editorial/coding-assistance sentence added.

**Not done / deferred.** Point 14 for the five other >300-word captions (aitsupp 402, r7host 359,
prevalence 339, w3dilution 330, blindkey 324). Point 6's notation change is body-wide but not
appendix-wide (33 generated tables keep $r^{\star}$; one conventions sentence says so).

**Blind coverage audit of the finished revision (one codex run, brief `brief_r26cov.md`).** Verdict
"no" on one CRITICAL, repaired: Sec. I still said the composition "has a calculable finite discovery
horizon" without the two-family / rejection-free scope the abstract had gained, and the Fig. 1 caption
said "against a shrinking level"; both now carry the scope. MAJOR repaired: two bare $r^{\star}$ left in
the body (threat-model definition, host-conditioned result) → $r^{\star}_t$; the Terms caption said
"no quantity here is measured on a sequenced stream" while the new $J_{\mathrm{seq}}$ row defines a
rerun → caption now says the table reports no measurement. Two MAJORs were source-only limits of the
audit, verified here instead: the defences table (Table IV) renders at the top of p.11 above Sec. VI's
continuation, with Sec. VI starting on p.10 and Sec. VII below the table on p.11, so it no longer
interrupts the limitations section (the auditor saw only source order; its source now heads Sec. V-F);
`pdffonts` reports 0 Type 3 fonts (the auditor could not run it). MINOR
accepted: prose companions sit in the section text, not physically adjacent to the floating table.
Body still ends p.12 (layout line 52 of 57) after the repairs; all gates re-run green.

### Extension (user request, 6 Sep 2026): the two deferred items

**Point 14 for the remaining five long captions.** aitsupp (402→71 caption words), r7host (359→47),
prevalence (339→62), w3dilution (330→39), blindkey (324→39); prose companions
`tables/{w3dilution,r7host,aitsupp,prevalence,blindkey}prose.tex` are generated by the same
`write_prose()` mechanism and `\input` in Appendices E (`app:pools`, `app:ait` ×2), C
(`app:feasnotpower`) and D (`sec:transfer`). Two blind fidelity audits, then a repair pass and a
confirmation audit. What the audits caught — every item was inherited from the OLD captions, so the
restructure surfaced them rather than caused them:
- blindkey said the replay "must dominate" its binomial lower bound; the artefact records a shortfall
  of up to 0.030 (`max_binomial_lower_bound_violation`). Now stated as a Monte Carlo tolerance,
  interpolated.
- blindkey "matched reliability" compares $N_{99}$ with CERTAIN public suppression; now "the nearest
  matched-reliability comparison the grid offers ($99\%$ against $100\%$)", and the $N_p$ cells are
  labelled medians. (The body's "at matched reliability" is pinned by t61 R4 and unchanged.)
- The body's sec:transfer sentence "$N_{99}$ up to $3.4\times10^{4}$" matched no artefact statistic
  (per-window median max 31,502; per-target max 67,865). Now "a per-window median $N_{99}$ of up to
  $3.2\times10^{4}$", with a new t61 check (R26).
- aitsupp "Host conditioning does not stop it" now scoped to the two host-conditioned organisations
  (shaw, wilson; nine episodes); the flow-only 84/85 sentence says flow-only; success range and draw
  count interpolated.
- prevalence "two to three orders of magnitude below the exercise" was false for $\pi=10^{-3}$ (under
  one order below 0.48–0.81%); now computed from the grid: 0.7 to 2.7 orders.
- r7host "the transfer holds at both" now carries the scored range (up to `pad_feasible_cap`
  appended flows, 4,000,000 pad scorings at the primary window) and says costs above the cap are
  closed-form values, not replayed; "TCP/80" and the host-feature count come from the artefact.
- Undefined headers defined in the notes: AUROC, pos, observed, online e-BH / e-TOAD.
Not changed: "33 flow features", "six-points-per-decade" and the task-record timestamp range remain
literals with no artefact field; each matches the body or the dataset documentation.

**Point 6 across the appendix.** Every $r^{\star}$ that prices at the running level of the alert's own
step now carries the subscript: nonoracle (caption and the flat-pad row), aitorder (caption and
header), aitsupp (header and notes), w3dilution (header and notes), r7host (costs), the joint table,
and the appendix prose in `app:nonoracle` and `app:ait`. Rows priced against the static cold-start
threshold (`apptab:padpools` part (b), `apptab:units` rows 3–5) never used the symbol; they say
"static" in words, and the reporting conventions now state that rule. The only bare $r^{\star}$ left is
the conventions sentence that introduces the symbol, which t61 R10-1 pins. Body untouched.

**State.** 41 pages (the moved prose adds one appendix page), body still ends p.12; t61 239/0,
t65 194/0, t71 34/0, t68 2/0, t69 0 drift, t45 268/0, t70 ok.

**Confirmation audit of the seven repairs (one blind codex run, `brief_captions3.md`).** (a)–(e) and
(g) FIXED with the numbers spliced from the artefacts; (f) "partly fixed": the body's
$3.2\times10^{4}$ is a typed literal. That is the convention for every number in `satml.tex` — body
numbers are typed and guarded by a t61 check, never generated — and the new t61 R26 check is that
guard; no further change. No repair introduced a new inaccuracy against the artefacts.
