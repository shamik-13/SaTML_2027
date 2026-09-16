# Round-25 reviewer feedback on paper/satml.tex (received 6 Sep 2026, verbatim)

## 1. A reviewer may regard the feasibility theorem as "obvious once written down"

This is the largest novelty risk. The paper itself acknowledges that previous work had already observed
the finite conformal floor and poor online-testing behaviour. Your novelty is the transition from that
observation to:

- a procedure-and-spending-sequence characterization;
- an absorbing rather than merely low-power state;
- a best-case calibration-to-horizon sizing law;
- an operational chain connecting grouping to an attack surface.

A statistics-oriented reviewer may nevertheless write something like:

> "The finite horizon follows immediately from comparing a bounded e-value with a testing level tending
> to zero; the max-min uniform allocation is a simple averaging argument."

That reviewer could score the paper 4–5 despite agreeing that the result is correct. The paper should
therefore be presented primarily as a systems-composition result, not as claiming that the algebra alone
is mathematically deep.

The strongest novelty sentence is approximately:

> Prior work studies finite conformal resolution and online alpha decay separately. We show that their
> composition has a calculable finite alert lifetime, and that the operational repair—coarsening
> hypotheses—creates a class-wide padding vulnerability.

That relationship is the real contribution.

## 2. The guarantee-bearing empirical interpretation remains conditional

The paper is commendably explicit that group-level marginal e-validity requires a metadata-conditional
assumption stronger than ordinary unconditional split-conformal validity. It also states that the primary
and secondary diagnostics contain only 0–3 benign tail events and therefore neither establish nor
meaningfully support that premise.

A skeptical reviewer could say:

> "The paper motivates the trust layer through formal FDR validity but never establishes that the grouped
> evidence in the showcased NIDS pipeline satisfies the premise needed for the FDR guarantee."

Your response is technically sound—the feasibility theorem and padding impossibility do not depend on
that premise—but this separation currently becomes fully clear relatively late. Put the claim-dependency
distinction prominently on page 2, not only in Section VII and an appendix table.

## 3. The empirical replay is per-alert, not a joint attacked-trajectory rerun

The manuscript correctly says that each alert is replayed at its original controller level and that the
altered controller trajectory is not rerun jointly. That is an important limitation because the abstract's
wording about suppressing "all 212" can initially sound like one simultaneous end-to-end attack run.

This is largely fixable through wording:

- Say "per-alert replay validates the predicted suppression threshold for 212/212 true alerts".
- Avoid saying simply that a single attack "suppresses all 212 alerts."
- Present the state-free fixed-multiplier experiment as the evidence about attacker knowledge, separately
  from the oracle cost calculation.

A full joint attacked-trajectory rerun would be the single highest-value additional experiment, because
it directly closes this objection. I do not think it is mandatory for an acceptance-quality submission,
but it is the most plausible experimental request in a Revision decision.

## 4. Practical severity changes dramatically between regimes

The strongest part of Table I is also a possible reviewer objection. Under horizon-free spending,
suppression is cheap, but the controller detects only three primary-window malicious episodes. Under
horizon-aware spending, it detects 105, but the median exact cost rises from 24 to 2,946 flows, and a
volume cap removes much of the exposure.

A hostile reading is:

> "The weak controller barely works anyway, while the useful controller makes the attack conspicuous and
> mitigable."

The correct and stronger framing is not "padding is always a cheap devastating attack." It is:

> Controller allocation determines whether the system is nearly silent, cheaply suppressible, or expensive
> enough for an external admission-control mechanism to intervene; statistical validity alone determines
> none of these operational properties.

That tradeoff is more credible and more interesting than an unqualified vulnerability claim.

## 5. Empirical independence is limited

The paper uses five LSPR23 windows, but correctly states that they are overlapping, correlated views of
one exercise. AIT is a valuable second transfer dataset, but the host-conditioned arm contains only nine
detections from two organizations.

This is not fatal. Recent SaTML papers do not universally require many unrelated datasets, particularly
when the contribution is partly theoretical. But reviewers should never be allowed to mistake five windows
for five independent replications. Your current wording handles that well.

## 6. The paper is still denser than it needs to be

The causal structure is now much better than in the earlier drafts, but the abstract currently asks the
reader to absorb:

- four named controllers;
- two spending regimes;
- one calibration law;
- two datasets;
- several attack-knowledge models;
- eight or more quantitative results;
- the merger-class impossibility;
- the mitigation boundary.

That is too much for the abstract. Recent successful SaTML papers tend to make the new object, threat
model, and headline result unmistakable within the first few sentences.

SaTML explicitly states that reviewers are not required to read appendices and that central claims must
stand in the body. Your core theorems and headline experiments are in the body, which is good, but some
highly useful interpretive material—especially the claim-dependency table and full controller
taxonomy—is pushed into the appendices.

# The minimum changes I would make

These require no new experimental campaign, but they are more consequential than ordinary copyediting.

## 1. Make one causal claim the spine of the abstract

Use something close to:

> A statistically valid ML alert pipeline can nevertheless become operationally unable to alert. We show
> that bounded conformal evidence and online error spending create a finite alert horizon; reducing the
> number of hypotheses restores feasibility but exposes group membership to adversarial padding. This
> leads to a class-wide impossibility for symmetric e-merging rules and a measurable
> feasibility–resolution–robustness tradeoff on two intrusion-detection datasets.

Then retain only two or three headline quantitative findings. I would keep:

- 3.3 × 10^8 required versus 1.8–2.4 million available;
- the 24-to-2,946 cost shift;
- 78/79 AIT transfer suppression.

The detailed 14/14 and 212/212 counts can remain in the body unless phrased very carefully as per-alert
replay.

## 2. Put a "known versus new" paragraph or table on page 2

A compact version would be:

| Previously known | New here |
|---|---|
| Finite conformal resolution and alpha-death/low power | An absorbing discovery horizon and an ex-ante optimal deployment-sizing law |
| Fixed-arity characterization of symmetric e-mergers | Cross-arity padding robustness and a class-wide impossibility |
| Grouping can improve online-testing power | Grouping is the feasibility repair and simultaneously creates an attacker-controlled membership surface |

This is the single most important defense against a novelty-based rejection.

## 3. Move the claim-dependency separation earlier

State explicitly near the contribution list:

- Feasibility theorem: requires bounded evidence and the stated level form.
- Padding theorem: requires only the symmetric e-merging class.
- Nominal FDR interpretation of empirical runs: additionally requires group-local validity.
- Empirical attack findings: concern observed scores, groups, and labels and do not depend on nominal FDR
  validity.

The manuscript already makes this distinction correctly. It merely needs to be seen before a reviewer
forms the impression that an unvalidated assumption undermines the entire paper.

## 4. Remove defensive repetition rather than removing limitations

Keep all substantive limitations, but state each once. There are repeated formulations of:

- procedure-and-spending-sequence scope;
- oracle lower-bound status;
- windows not being independent;
- group validity being conditional;
- the result not showing that all online FDR methods fail.

The repetition makes the paper feel less novel because every positive statement is immediately
surrounded by qualifications. Assert the result first, define the boundary once, and refer back to that
boundary thereafter.

## 5. Fix the LLM disclosure before submission

Your current LLM section is strong on accountability, code validation, and author responsibility.
However, SaTML 2027 also requires authors to justify the environmental footprint and explain choices such
as why LLM use was necessary, how query volume was minimized, and relevant hardware/model information
where available. Failure to comply may result in desk rejection.

Add a truthful paragraph along these lines, filling in actual details:

> No model training or fine-tuning was performed. Hosted assistants were used only for targeted
> editorial, implementation, and audit tasks. We limited use by batching related requests, reusing
> generated code and cached results, and avoiding LLM calls during the released pipeline's execution.
> Provider-side energy measurements were unavailable, so we do not estimate emissions; the reported
> experiments themselves ran on [hardware], and reproduction requires no access to an LLM.

Also make sure the anonymized artifact is actually available within the required three-day window and
then remains frozen throughout review. Your Open Science section is already unusually strong and well
aligned with that policy.
