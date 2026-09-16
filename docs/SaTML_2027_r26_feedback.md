# SaTML 2027 — review feedback, round 26 (received 6 Sep 2026, on the draft after round 25b)

Saved verbatim from the user's message. Worklist: docs/44_r26_worklist.md.

1. Tighten the finite-horizon claim in the abstract

The current abstract says:

"bounded conformal evidence and online error spending create a finite alert horizon."

That still sounds like a universal statement about online error spending. However, your strongest exact formulation is narrower:

it covers two specified arrival-time controller forms;
the relevant horizon is the horizon of a rejection-free prefix or gap;
for the lag-sum family, a procedure that keeps rejecting can keep its level feasible.

The appendix explicitly says that Theorem 2's absorption is conditional on a sufficiently long rejection-free gap and that these are fundamentally cold-start claims. The main body already has the more accurate formulation, "every sufficiently long rejection-free run becomes permanently unable to report a discovery."

Replace the abstract sentence with:

For two arrival-time controller families, bounded conformal evidence makes every sufficiently long rejection-free run reach an absorbing discovery horizon.

This also lets you standardize on "discovery horizon" instead of alternating between "alert horizon," "finite alert lifetime," and "discovery horizon."

This is the single most important remaining wording correction because a statistically oriented reviewer could otherwise accuse the abstract of claiming more than Theorem 2 establishes.

2. Scope the grouping claim more carefully

The introduction currently says:

"Grouping is the mechanism that makes the controller feasible."

That is too absolute. Your own appendices discuss restart, smoothing, selective index advancement, online e-BH, and other evidence constructions. Even within the grouping analysis, not every grouping immediately restores feasibility; the group must be sufficiently coarse.

Use:

With the calibration corpus fixed, sufficient coarsening is the operational feasibility repair we study for the covered uninterrupted controllers.

Make the corresponding Table I entry:

Sufficient grouping can restore cold-start feasibility at the exchange rate in (7); for attacker-co-occupiable grouping keys, it also makes membership attacker-influenceable.

There is also a local contradiction in Section IV:

"Nor is the choice of key a defence."

followed almost immediately by:

"A key the attacker cannot cheaply co-occupy would be a real mitigation."

Replace those sentences with:

Coarsening an attacker-co-occupiable key is not by itself a defence: it changes feasibility and attack cost but retains the membership surface. A key the attacker cannot cheaply co-occupy would instead be a genuine membership defence.

That distinction is much cleaner: coarsening the same kind of key is not a defence; changing the key's security property can be.

3. Correct the Figure 1 caption

The caption currently says:

"The attack needs no detector access and changes none of the attacker's own flows."

But the attacker does add its own ordinary flows. The threat model correctly says that the attacker leaves its malicious flows and their scores unchanged.

Replace the final caption sentence with:

The attack needs no detector access and changes neither the malicious flows nor their detector scores; it only appends ordinary flows to the same tested hypothesis.

This is a small change, but the present sentence is visibly self-contradictory once the reader understands the attack.

4. Reconcile "two knowledge levels" with the attack-cost taxonomy

The threat model says there are two attack-knowledge levels:

oracle knowledge of evidence and the live controller level;
state-free knowledge using only the attacker's own episode size.

Section V-D then says:

"We distinguish three attack costs."

But c is not a cost; it is a dimensionless multiplier strategy. Furthermore, the paper now reports four distinct quantities:

r_t^*: per-alert oracle cost;
sum_t r_t^*: sum of independently priced pads;
J_seq: greedy oracle joint cost;
c: state-free multiplier.

The current paragraph mixes attacker knowledge, cost metrics, and attack strategies.

Replace it with:

We use two attacker-knowledge models and report three cost summaries. Under oracle knowledge, r_t^* is the minimum cost of suppressing one alert on the unperturbed trajectory, sum_t r_t^* is the counterfactual sum of those independently priced pads, and J_seq is the total cost of a greedy sequential oracle on the attacked trajectory. Under state-free knowledge, the attacker instead uses a fixed multiplier c and needs only its own episode size.

That is conceptually exact.

5. Define these quantities before Table III

Table III appears on page 7, but the prose that properly defines J_seq and the three attack summaries appears on page 8. The caption technically explains them, but a reader encounters:

median r*, sum r*, J_seq

before receiving the conceptual distinction.

Move the attack-taxonomy paragraph to immediately after Equation (8), before Table III. Then move the table source to Section V-D so that it appears after the terminology has been introduced.

Also shorten the caption. The present caption is almost a paragraph. A cleaner version is:

TABLE III. Detection and padding costs under horizon-free and horizon-aware allocation, with detector, grouping, canonical order, and seed fixed. r_t^* is the per-alert oracle cost, sum_t r_t^* the independent sum, and J_seq the greedy-oracle cost on the rerun attacked trajectory. FDP is realized, not guaranteed.

Put the remaining details in the surrounding prose.

6. Standardize the notation

Equation (8) defines r*, while Section V-D introduces r_t^*, and tables often use r*/alert. Since the cost explicitly depends on the live level alpha_t, r_t^* is the more informative notation.

I would use consistently:

r_t^* = floor(S_t alpha_t) - m_t + 1,   sum_{t in R} r_t^*,   J_seq.

Also typeset J_seq throughout rather than Jseq.

One sentence should be corrected semantically. The paper currently says:

"the joint window-level cost J_seq stays near the cold-start price."

A total window-level cost cannot literally be "near" a per-alert price. What stays near the cold-start condition is the later level and therefore the per-episode pad size.

Use:

Suppressing early detections keeps subsequent testing levels at or near their cold-start values; consequently, the sequential pads remain small and their joint total J_seq is far below the independent sum sum_t r_t^*.

7. Make the oracle status of J_seq unmistakable

The abstract presently refers to a "greedy joint cost." The sequential attack reads the live controller level and pads by the exact minimum at each step, so it is a greedy oracle strategy, not a demonstrated black-box attacker.

Add "oracle" in three places:

"greedy oracle joint cost" in the abstract;
"greedy oracle sequential attacker" in the Table III caption;
"one greedy oracle strategy and therefore an upper bound on the minimum joint cost" in Section V-D.

The paper already describes that knowledge relationship correctly in the detailed paragraph; it should be visible in the headline result too.

Abstract-specific cleanup
8. Separate what is measured on LSPR23 from what transfers to AIT

The abstract currently describes a:

"measured feasibility–resolution–robustness tradeoff on two datasets."

That can imply that the complete feasibility-resolution tradeoff, including alert blur and grouping sweeps, is measured on both datasets. In practice, LSPR23 supplies that systems tradeoff, while AIT supplies the benign-inclusive padding transfer.

Use:

This yields a class-wide impossibility and, on LSPR23, a measured feasibility–resolution–robustness tradeoff; AIT-LDSv2.0 supplies a benign-inclusive transfer test.

Likewise, the current AIT sentence:

"the canonical pipeline suppresses 78 of 79 true detections"

appears directly after discussion of the joint controller rerun and can be read as another joint-trajectory result. The body is clear that these are per-alert replay results.

Change it to:

On the benign-inclusive AIT-LDSv2.0 testbed, per-alert benign-to-victim replay suppresses 78 of 79 true detections under the canonical order.

9. Remove or narrow the state-free multiplier sentence in the abstract

The current sentence says:

"On LSPR23's attack-only host pairs a state-free episode-size multiplier suppresses the evaluated arms."

The underlying result is more nuanced:

c=10 covers the stored canonical primary and stress arms;
a secondary canonical alert requires c=41;
c=3 suffices for both evaluated horizon-aware joint reruns;
one first-flow stress arm is not suppressed by any multiplier up to 100.

The sentence therefore invites the question, "Which evaluated arms, and was one fixed c used everywhere?"

The cleanest option is to remove this sentence from the abstract. The abstract already has the theorem, sizing rule, per-alert result, joint result, and AIT transfer. The state-free result is useful but secondary.

If retained, use:

On LSPR23's attack-only host pairs, precommitted episode-size multipliers suppress the evaluated canonical-order configurations without access to live controller state; the appendix records an adversarial-order stress configuration that requires a larger multiplier than those tested.

10. Add the membership assumption to the class-wide security phrasing

Theorem 3 is class-wide mathematically, but its operational interpretation requires that the attacker be allowed to append sufficiently many zero-evidence members. The paper later shows that admission control changes that model.

Use "under the unbounded-membership threat model" the first time the security consequence is summarized:

Under attacker-influenceable, unbounded membership, this yields a class-wide impossibility for alert-capable symmetric e-merging rules.

This heads off the otherwise predictable objection that a hard admission cap trivially prevents arbitrary padding. The paper already handles caps well; the qualifier merely makes the abstract align with that analysis.

One optional substantive improvement
11. Promote the rho-multiplier connection into a named proposition

The strongest newly visible connection is currently buried in Section V-C and the caption of Table XXXIV:

c_int = floor(rho) + 1,   rho = M alpha / T,

for horizon-uniform e-LOND in the pure-attacker zero-evidence setting. The appendix explains that the strict inequality is necessary because rejection is inclusive.

This directly connects the two halves of the paper:

rho measures whether bounded evidence can clear the cold-start level;
the same rho is the dilution factor needed to erase every cold-start alert.

That is an elegant composition-level result. I would state it as either a short corollary or a visibly labelled observation in Section V-C:

Corollary 2 (Feasibility ratio as a dilution threshold). Under horizon-uniform e-LOND, zero-evidence padding, and pure attacker-owned groups, multiplying every attacker episode by any c > rho = M alpha / T yields a rejection-free trajectory. Hence the smallest universally sufficient integer multiplier is c_int = floor(rho) + 1.

A two-line induction is enough: with no earlier rejection R_{t-1} = 0; padded evidence is at most M/c < T/alpha = 1/alpha_t; therefore no rejection occurs and the cold-start state persists.

This is the only substantive addition I would currently consider. It needs no experiment and strengthens the paper's central "composition" story more than another appendix comparison would.

Organization and visual cleanup
12. Update the terminology table

Appendix Table VI still lists only generic "padding cost" and "state-attack cost." It does not reflect the now-central distinction among:

per-alert padding cost r_t^*;
independent sum sum r_t^*;
joint padding cost J_seq;
state-free multiplier c;
ADDIS controller-state attack cost.

Add those rows. This is especially important because "joint controller-state rerun" and "controller-state attack" are not the same thing: the former propagates padding through e-LOND's rejection state, while the latter manipulates ADDIS's spending index.

13. Keep Table V inside Section VI

In the rendered PDF, Section VII starts on page 10, but Table V—belonging to Section VI—floats to the top of page 11 and interrupts the continuation of the limitations section.

Use a \FloatBarrier before Section VII, or move the Table V source earlier and force a top-of-page placement before the Section VII heading. The revised table itself is readable; only its placement remains awkward.

The same principle applies to Table III: it should not appear before its terminology is introduced.

14. Reduce appendix-caption length

Tables XXXIV and XXXVII have captions that function as entire methodological subsections. Table XXXVII's caption nearly fills page 38 before the actual table appears. Table XXXIV similarly combines definitions, threat models, interpretation, and implementation checks in one all-caps block.

For each:

Keep a one- or two-sentence caption stating what is measured.
Move definitions and interpretation into ordinary prose immediately before the table.
Put only column-specific qualifications in a short "Notes:" paragraph after the table.

This will make the appendix look like a paper rather than a generated results ledger, while retaining all the useful qualifications.

Page 41 contains only Table XLV with substantial unused space. Move it onto page 40 or reduce preceding float spacing. You should be able to reduce the appendix by at least one page without removing content.

Final technical checks
15. Complete the LLM disclosure placeholders

Two placeholders remain on page 12:

[AUTHORS: EXACT MODEL NAMES AND VERSIONS USED ACROSS THE PROJECT]
[AUTHORS: MACHINE, CPU, MEMORY]

These are submission blockers. Report the exact information that was logged. Where an exact hosted-model version was not recorded, say so directly rather than reconstructing or guessing it.

I would also replace:

"no smaller special-purpose model was available to us"

unless you can document that comparison. A safer statement is:

We used the general-purpose assistants already available in our development environment; no model was trained or fine-tuned, and no LLM is required to execute or reproduce the released pipeline.

Add one explicit sentence such as:

LLMs were used for editorial and coding assistance, and all generated outputs were inspected and validated by the authors.

Your surrounding text already supports that statement; this simply makes the disclosure unambiguous.

16. Regenerate the figures without Type 3 fonts

My PDF preflight still finds Type 3 fonts inside some figure objects, including DejaVu Sans variants and Times New Roman. They are embedded, but this is worth fixing before the final submission build.

For Matplotlib-generated PDFs, set before figure creation:

import matplotlib as mpl

mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42

Then rebuild every figure rather than post-processing the PDF.
