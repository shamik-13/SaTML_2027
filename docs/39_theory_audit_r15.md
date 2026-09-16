# Round 15: independent theory audit, claim ledger, artifact consistency

Requested as item 5 of the review-14 feedback. Three strands: a formal audit of four items by two
blind agents, a claim ledger, and an artifact-consistency run.

## Method

Both auditors worked from **one self-contained 18KB extract** (`AUDIT_BRIEF.md`), not the repo:
standing notation, the four items' statements and proofs verbatim, and a list of specific questions
per item. Neither could read the paper, the code, or each other. Both were told to falsify, not to
confirm, and that a statement true only under an unstated hypothesis is a DEFECT.

* **Blind codex** --- `codex exec -s read-only --skip-git-repo-check -C <dir>`, foreground, 2m13s.
* **Blind Opus** --- fresh agent, no repo access, 8m32s.
* **A third blind agent** then verified the repairs, with the defects and the fixes described but
  no access to anything else. This is what the `t69` freeze protocol requires: the baseline must
  track what was *audited*, not what is merely current.

## Yield

| | codex | Opus |
|---|---|---|
| Item 1 (Thms 1--2) | SOUND | DEFECT (4 sub-findings) |
| Item 2 (e-LORD coverage) | **DEFECT** | **DEFECT** |
| Item 3 (Cor 1) | SOUND | UNDERSPECIFIED |
| Item 4 (Thm 3) | SOUND | DEFECT (Route B scope) |

They agreed on exactly one finding --- and it is the one I would rank first for correctness. As in
rounds 11 and 13, the two auditors' findings were largely **disjoint**.

## Defects confirmed and repaired

1. **e-LORD coverage** (both auditors, independently). The paper said the reparameterisation
   `gamma_t = omega_t * prod_{j<t}(1 - omega_j)` gives a fixed non-negative sequence with
   `sum gamma_t <= 1` "only when the weights are pre-committed". Pre-commitment gives *fixedness*
   only. A pre-committed `omega_1 = 2` yields `gamma_1 = 2` and `gamma_2 < 0` --- verified directly.
   The paragraph now requires `omega_j in [0,1]` **and** determinism in the index, and gives the
   telescoping identity `sum_{t<=n} gamma_t = 1 - prod_{j<=n}(1 - omega_j) <= 1`.
2. **Theorem 2 used `1/M` without hypothesising `M < infinity`** (Opus). With unbounded evidence
   `1/M = 0`, the set defining `Delta*` is empty and the theorem is **false as written**. The
   hypothesis was inherited from Theorem 1's preamble but was not a hypothesis of Theorem 2.
   *(frozen; repaired and re-frozen)*
3. **Route B's advertised scope** (Opus). The preamble said Route B "establishes the impossibility
   for a negatively-dependent construction". It proves only that a symmetric family maps a
   permutation of a mean-one two-point vector to at most 1 --- which says nothing about the
   **unpadded** value, and so yields no violation of padding-robustness for a family that returns 0
   there. Verified counterexample: `F_N(e) = mean(e) * 1{not all e_i equal}` is symmetric and valid
   (`0 <= F <= mean` pointwise), attains `theta`, and defeats Route B while Route A handles it.
   Route B is now stated as the lemma it is.
4. **The two families are not equally strong** (Opus, top-ranked). Theorem 1's bound uses only
   `R_{t-1} <= t-1`, so absorption holds on *any* history. Theorem 2's is driven by the length of
   the *current* rejection-free gap, so its absorption is conditional on such a gap occurring. A
   LORD++ run with a rejection at every step climbs towards `alpha_t ~ 0.039` and never dies. The
   theorem body was always correctly conditional; the paper never said the asymmetry out loud, and
   a reader could conclude lag-sum procedures die when they need not. Now stated --- and it
   *strengthens* Theorem 1, which absorbs unconditionally.
5. Smaller, all repaired: the `gamma_{2^n} = c/n^2` counterexample sums to one only at
   `c = 1/zeta(2)` (both auditors); it refutes the *hypothesis*, not the conclusion (the same
   sequence has `gamma_t -> 0` and is absorbed at `d=0`); `c` vs `c_g` in Theorem 1's proof;
   Corollary 1's max-min one-liner "any other allocation places some `gamma_t < 1/T`", false for
   allocations differing only outside `[1,T]`, replaced by `min <= average`; "horizon-uniform falls
   outside the letter of the condition", ill-posed, reworded.
6. The repair verifier added one: Corollary 1's **sufficiency** direction was present in the proof
   but never signposted, resting implicitly on the optimality clause. Now explicit, with the reason
   the two directions coincide only for a constant cold-start level.

## Findings assessed and NOT acted on

* **"Theorem 1's rejection-free qualifier is vacuous"** (Opus, rank 7). Rejected. Proposition 1
  instantiates Theorem 1 at `d=0` *on a rejection-free prefix* --- a review-13 repair. Dropping the
  qualifier would break that instantiation. The qualifier is conservative, not vacuous.
* **"Cold-start feasibility over a horizon T is undefined"** (Opus, rank 5). An artefact of my
  extract, which omitted the body's terminology ladder where the term is defined. Under that
  definition the corollary's general clause is a correct necessary condition.
* **`sum gamma_t <= 1` unused in Theorem 1** (rank 10). True; an unused hypothesis does not make a
  theorem false, and it is the procedure's own normalisation.
* **Boundary requires unanimous group firing** (rank 11). True and interesting, but Corollary 1 is
  about *feasibility*, and `Ev = M` is admissible. Correct as stated.
* **Integrality `ceil(kT/c_0) - 1`** (rank 14). Immaterial: at `k=1` with `c_0 in {0.05, 0.025}`,
  `kT/c_0` is `20T` or `40T`, always an integer.
* **`M` (ceiling) vs `M_K` (mean) collision** (rank 14). Real, but `M_K` is Vovk--Wang's own
  notation inside a quoted dependency; renaming it makes the citation harder to follow.
* **mem-e-LORD** (rank 12). Not in the extract, so not auditable --- my extract's fault.

## Do not trust an auditor's arithmetic

Opus's supporting numbers for its top finding were wrong: it reported `alpha_50 = 0.0465`,
`alpha_500 = 0.0491`, having used `a_j = alpha` for every lag instead of `a_1 = alpha - w_0` for the
most recent rejection. The true values are `0.0356` and `0.0382`. **The conclusion survived; the
arithmetic did not.** Every number an auditor supplied was recomputed here before use.

The same applies in the other direction. My own repair text asserted the all-reject run is feasible
"for any `|C| >= 26`", computed from `alpha_500`. The binding step is the **cold start**, not the
limit: `min_t alpha_t = alpha_1 = 0.0109`, so the correct threshold is `|C| >= 91`. Caught by the
gate written for the claim, not by re-reading the sentence.

## Claim ledger (`proto/t71_claim_ledger.py` -> `docs/38_claim_ledger.md`)

Nine headline claims, each resolved to: value (**recomputed** from the artefact, never transcribed),
the arm actually run, the assumption it needs, the producing script, the table/figure, and the body
wording. It fails if any sentence stating a claim omits a qualifier its arm requires.

It failed on its first run: the abstract's "78 of 79" had lost "canonical" in this session's
compression pass. Fixed. The check was initially written against the *first* occurrence of a claim;
that would have missed this depending on ordering, so it now checks **every** occurrence --- the
abstract's compressed restatement is exactly where a qualifier gets shed.

## Artifact consistency

* **All 33 appendix tables regenerate byte-identical** from `src/lib/out/`.
* **All 6 figures regenerate identical** modulo PDF timestamps.
* Compile clean, 0 undefined references, body ends p.9.

Two honest limits on this pass, neither a paper defect:

* **Full raw-data mode was not exercised.** LSPR23's raw flows are not in the tree (AIT is, 261MB),
  so full mode needs the Zenodo download --- exactly as the Open Science section says.
* **The notebook wrapper was not executed** (no jupyter/nbconvert in this venv). The generators it
  shares were verified instead.

**One artifact recommendation:** `src/README.md` pins no dependency versions
(`pip install numpy scipy scikit-learn pandas jupyter`). scikit-learn version drift moves
HistGradientBoosting scores, which sits awkwardly against a promise of deterministic reproduction.
A pinned requirements file would close that.

## Gate state

`t45` 268, `t61` 201, `t65` **113**, `t68` 2, `t69` 26 objects / **0 drift** (re-frozen),
`t70` 3, `t71` 18. Five new `R15` checks recompute every derived number the repairs introduced.

## Not done

The mock-review exercise (item 6) and any further artifact work in a genuinely clean environment.

---

## Follow-up: the notebook actually renders the figures now, and the environment is pinned

Two items from the audit's artifact strand, done in full.

### The figures were never in the notebook

Executing `src/paper.ipynb` for the first time (headlessly, via `nbclient` --- no install needed,
it was already in the venv) gave **37 code cells, 34.5 s, 0 errors** and **zero figures**. The
notebook contained no matplotlib code at all: `grep` for `plt.`, `savefig`, `matplotlib` returned
0 hits. It reproduced every number *behind* every figure and drew none of them.

Meanwhile the paper said:

> In its default mode the notebook renders every table and figure from shipped results in seconds

and `src/README.md` said "every number and figure in the paper is produced in it". Both false. The
figures had always been drawn by `paper/make_figures.py` and `paper/make_figures_satml.py`, run by
hand, reading the same cached `src/lib/out/*.json`.

**The fix was to make the claim true rather than to weaken it.** The drawing code moved to
`src/lib/figures.py`, inside the reproduction package; `paper/make_figures_satml.py` is now a thin
wrapper that sets an output directory and calls it, and `paper/make_figures.py` re-exports
`fig2_envelope` from the same module rather than keeping a second copy. There is now **one**
implementation, which matters here more than usual: the recurring failure mode in this repo has been
a fix landing in the prose and surviving in a generator, and two copies of a figure would have been
exactly that.

Verification that the refactor changed nothing: **all 6 figures regenerate byte-identical** against
a pre-refactor snapshot. The notebook now executes in 32.1 s with **0 errors and 6 figures rendered
inline**, and ships those renders in its outputs (0.15 MB -> 0.56 MB), so it can still be read
straight through without executing anything, as the README promises.

`figures.OUTDIR` is `None` by default, so the notebook writes nothing to disk --- verified: the run
left `src/lib/out/` byte-identical. The module deliberately does not call `matplotlib.use()`; the
paper build selects Agg before importing it, and the notebook's inline backend survives.

### Pinning

`src/requirements.txt` now pins numpy, scipy, scikit-learn, pandas, matplotlib, nbformat, nbclient
and ipykernel to the versions verified here, and `src/README.md` installs from it.

The file is explicit about the limit of what was checked, because the honest answer is not "these
versions reproduce everything":

* **Verified at these pins:** `MODE="paper"` executes clean in ~32 s and renders all 6 figures; all
  33 appendix tables regenerate byte-identical; all 6 figures regenerate byte-identical.
* **Not verified:** `MODE="full"` was not re-run --- it needs the LSPR23 download. And the shipped
  results in `lib/out/` were produced by an earlier full run **whose library versions were not
  recorded**: the artifacts store their experiment `config` (POS, SEEDS, k, w0, bucket_s, orders),
  not their environment. So these pins are where the cached path is known to reproduce exactly, not
  a certified match to the run that produced the artifacts.

That last point is the residual gap, and it is the reason the pinning mattered: scikit-learn's
`HistGradientBoostingClassifier` decides the scores, hence the conformal ranks, hence which episodes
are detected. Recording the environment alongside future full runs would close it.

### New gate: `proto/t72_artifact_promises.py`

Nine checks, all injection-tested, guarding the Open Science section against the artifact:

1. every `\includegraphics` in the paper is drawn by `lib/figures.py`;
2. `figures.SUBMISSION` lists exactly those figures;
3. the notebook iterates that list and displays each one;
4. the notebook ships at least that many rendered images;
5. `make_figures_satml.py` stays a wrapper (no `plt.`, no `subplots(`);
6. `requirements.txt` pins every third-party library `src/lib` imports;
7. the pins record what was and was not verified;
8. the notebook's default `MODE` is the no-data path the paper advertises;
9. the paper does not re-acquire the pre-audit wording.

**One gate hole found by injection**, again of the familiar shape: check 3 first tested for the
substring `figures.SUBMISSION`, which occurs twice in the cell (the loop and the closing count), so
gutting the loop still passed. It now matches the loop form and the `display(getattr(figures, ...))`
call. Same lesson as the `not run` caption and the review-12 rename: **a substring that appears in
more than one role cannot guard any one of them.**

---

## Round 16: the mock review, and the experiment it forced

### Three reviewers, one objection

Three blind agents were given the compiled paper (body pp.1-9, appendices after) with three
different reviewer profiles --- online multiple testing, security/ML systems, empirical evaluation ---
and one instruction: **find the strongest reason to reject.** Each also kept a *findability ledger*:
for every objection formed, was it answered in the body where it arises, far from where it arises, in
an appendix, buried behind two hops, or unanswered.

**All three returned weak reject, and all three led with the same objection**, arrived at
independently: *the negative result and the attack are demonstrated at an operating point the paper's
own theory and appendix identify as avoidable.* Every attack measurement used the horizon-free
`gamma ~ j^-1.6` with no restart, while Corollary 1 proves `gamma_t = 1/T` max-min optimal and
Sec. III-C reports it feasible at every window. Since `r* = floor(S*alpha_t) - m + 1` grows with the
offered level, a controller that alerts more should be dearer to silence --- so the headline
"23--33 added flows" might be a property of the near-dead regime rather than of the system.

Verified before acting: **no padding artefact carries a uniform-allocation or restart arm.** The
objection was factually correct. The paper's own data already pointed the same way --- first-flow
detects 6x more at 0.55 and costs 5x more per alert; the AIT arm, with the healthiest detection in
the paper, runs to a median of 4,650.

### The experiment: `src/lib/t73_uniform_padding.py`

The same stream, detector, e-values, episodes, canonical order and `r*` formula, with **one argument
changed**: the spending sequence. Nothing reimplemented --- it calls `h6_procs.make_gamma` /
`run_lond` and t28b's `zero_pad` verbatim, so the arms are comparable by construction. A **control
arm asserts** that `poly x canonical` reproduces the shipped 3 detections at `r* = 23, 24, 33` and 11
at median 6; if it does not, the run aborts.

Control reproduced exactly. Result, LSPR23 primary 0.55, canonical, seed 0:

| | `gamma ~ j^-1.6` | `gamma_t = 1/T` | |
|---|---:|---:|---|
| detections | 3 | **105** | 35x |
| recall | 0.011 | **0.382** | |
| false positives | 0 | **0** | |
| median `r*` | 24 | **2,946** | 123x |
| total pad for the whole set | 80 | **627,495** | 7,844x |
| median `1/alpha_t` at detection | 1.6e6 | 2.2e4 | |

At 0.62: 11 -> 107 detections, median `r*` 6 -> 3,908 (651x), total 926 -> 977,567, one false positive.

### What this changed in the paper

**The theory is untouched.** Theorem 3 is a statement about merging functions; every alert in both
arms has a finite `r*`. No allocation escapes the impossibility --- it only prices it. `t69` shows
0 drift.

**The headline number was rescoped.** "23--33 added flows" is the cost of erasing three alerts that
fire at `1/alpha ~ 1.6e6`, just under the ceiling `M = 2.4e6`, where almost anything dilutes them.
Sec. V-C now leads with the mechanism --- `r*` is increasing in `alpha_t`, so the cost of suppression
is set by the level the alert fired at --- and reports both ends of the range. New body table
`tab:costcurve`, every cell recomputed from the artefact by `t65`. Fig. 4A gains the horizon-aware
arm, so the curve is visible rather than asserted.

**The "structural silence" narrative took the heavier correction.** Sec. III-D now separates two
things the paper had conflated: the flow-granularity shortfall is **allocation-optimal already** ---
it is what Corollary 1 requires under the *best* sequence, so no reallocation removes it --- whereas
the grouped detection counts are **not**, and under the horizon-aware allocation the same window
detects 105 of 275 malicious episodes at zero false discoveries. The paper now says plainly that it
reports the horizon-free sequence because it needs no horizon knowledge, *not* because it is the
better choice.

**Limitations** now states that every reported cost is configuration-conditional, that our own arms
span two orders of magnitude at one window, and that what is configuration-independent is only
finiteness.

### Gate additions

`t65` grew to **128** checks. The `R16` group registers the two new abstract numbers against the
artefact, recomputes all four rows of `tab:costcurve`, and --- the important one --- **asserts the
direction** from the artefact: at both windows the horizon-aware arm must detect more *and* cost more
per alert. A future edit cannot quietly invert the claim. `t71` gained a tenth headline claim.

### Findability, which was the other half of the exercise

The reviewers' ledgers agree on where the paper is hard to read. Marked BURIED by more than one
reviewer: the restart recall figures (0.065 -> 0.406), the per-window canonical detection counts, and
e-LORD's 101 rejections against e-LOND's 18. Marked UNANSWERED by more than one: rate limits and
volumetric controls that would see a large pad, and --- before this round --- the attack's cost under
any high-recall configuration. The last of those is now answered in the body. The others are recorded
here and not yet addressed.

### Round 16b: the findability ledger's two open items

**Conspicuity — the objection two reviewers marked UNANSWERED.** The paper had one arity percentile
for a 33-flow pad and nothing else, which mattered far more once the horizon-aware arm needed ~10^3
flows. `t73` now measures it from the deployment stream itself, two ways: where the padded episode
sits in the deployment arity distribution, and the tradeoff curve for the control a practitioner
actually reaches for, a per-host-pair cap on flows per bucket.

The answer is symmetric, and it completes the argument rather than damaging it:

| | horizon-free | horizon-aware |
|---|---:|---:|
| median padded arity | 63 | 2,989 |
| share of deployment episodes at least that large | 5.05% | 0.22% |
| pads blocked by a cap of 100 | **0%** | 95% |
| pads blocked by a cap of 300 | **0%** | 87% |
| benign episodes truncated at that cap | 3.4% / 1.0% | 3.4% / 1.0% |

**The attack is cheap and invisible exactly where the controller is weak, and expensive and
conspicuous where it is strong.** A volume cap catches the horizon-aware pad at 87-95% for 1-3.4%
collateral, and catches *nothing* in the horizon-free arm, where the median padded episode is 63
flows -- below any cap a defender would set. Reaching that one needs a cap of 30, which truncates
7.4% of benign traffic. Sec. VI's defence table gains a fourth row for it, marked
*outside the merging class*, because a rate limit is not an e-merging fix and presenting it as one
would be wrong.

**An error found by surfacing a buried number.** The reviewers cited "hourly reset takes recall from
0.065 to 0.406" as evidence that restart cheaply fixes the horizon. Checking it before repeating it:
**0.406 exists nowhere as a restart recall.** It is a *two-seed mean* at **one-hour** grouping with a
total budget of **0.45**, compared against a seed-0, two-hour, `q=0.05` baseline -- three variables
moved at once. This is the [[wrong-statistic-failure-mode]] shape exactly: a mean of one arm dressed
as a like-for-like contrast.

The like-for-like figure, holding grouping, seed and deployment-wide budget fixed, is **18 -> 55
rejections, recall 0.065 -> 0.200, measured FDP zero**. Spending a fresh `q` per epoch reaches 0.360
at a total budget of 0.25, but that is a per-epoch FDR. The paper now says both, and says that the
comparison has to hold grouping, seed and total budget fixed or it measures the wrong thing.

**Corroboration for t73, found while checking.** e-LORD under the horizon-aware e-GAI weighting
(`gamma = egai(w1=1/T)`) reaches **101 detections at recall 0.367 with zero false positives** at the
primary window, seed 0. `t73`'s independent uniform arm reached 105 at 0.382. Two different
procedures, both horizon-aware, landing in the same place -- which is much stronger evidence for the
allocation finding than either alone. Both are now in the body, alongside the five per-window
canonical counts (3, 11, 0, 0, 34), which two reviewers had to hunt for.

**Gates.** `t65` is at **136**. The `R17` group recomputes every conspicuity number and the cap
tradeoff from `t73`, `R17b` pins the like-for-like restart row and forbids the mismatched 0.406, and
`R17c` requires all five per-window counts and the e-LORD corroboration. Three floats had to be
re-anchored to keep `t68` green; the cost-curve table is now a full-width float, which is the only
placement LaTeX cannot defer into a column interior.

### Round 16c: the secondary-window replay ("not run" -> 11/11)

Two mock reviewers flagged that the paper's only end-to-end demonstration on its headline dataset
rested on **three events**, while the eleven secondary-window alerts sat in `tab:main` marked
*not run* with no reason given anywhere.

The reason turned out to be trivial: `t48_W3_dilution.py` had `POS = [0.55, 0.85]`. The secondary
window was **never in the list**. Not a failure, not a limitation -- an omission.

Adding `0.62` and re-running the identical script, with nothing else changed:

* **11 detected, 11/11 suppressible, measured cost == closed form on 11/11, median `r*` = 6.**
* first-flow arm: 13/13, median 72.
* the pad pool fires **0 of 20,000** at that window (95% CP upper bound `1.5e-4`), as at the others.
* all **8 pre-existing entries unchanged**, so the 0.55 and 0.85 numbers the paper already quotes
  are untouched.

The replayed set is now **fourteen canonical alerts across the two guarantee-bearing windows**, not
three. `tab:main`'s cell reads `11/11`; the abstract says so; and the appendix reports every arm.

**The gate had to be inverted, not deleted.** `R14-2` existed to stop the abstract implying both
windows were replayed when only one had been -- it required the string *"not run"* in the table row
and an explanation in the caption. With the gap closed, that check would have been enforcing a
falsehood. It now derives the replayed windows **from the artefact**, requires the abstract's count to
match, and separately forbids any bare dash in the replay column -- since a dash reads as zero,
missing, or failed suppression. The claim can no longer drift in either direction.

This is the cheapest fix in the whole review cycle and it removes the single most quotable line an
unsympathetic reviewer had: *"the end-to-end security evidence on the primary dataset is n = 3."*

### Round 16d: novelty positioning

All three mock reviewers, independently, made the same structural complaint: the prior art closest to
each formal result is disclosed only in Related Work, three to five pages after the result. A reader
meets Theorem 1 on p.4 and does not learn until p.9 that the phenomenon is published.

The *substance* was already right --- review 6 established both collisions, one of them found by our
own lit sweep rather than by a reviewer --- so this round moved the attribution, it did not change it.
The delta now appears **at each claim**:

**Theorems 1--2 (Huo et al., NeurIPS 2024).** Their Appendix B.2 states the conformal floor
`1/(|C|+1)` and its consequence for p-value-based online testing verbatim, and their Section 4.1
reports the behaviour for LOND, SAFFRON and ADDIS. **The phenomenon is prior art and the paper now
says so where the theorems are stated.** What the theorems add: which *procedure-and-sequence pairs*
it binds, that the state is *absorbing* rather than a gradual loss of power, that it covers the
e-value procedures too, and the rate at which calibration must grow --- so the criterion can be
evaluated from `|C|`, `k` and `T` in advance rather than discovered in a run.

**Corollary 1 (Krönert et al., arXiv 2312.01969).** Their Corollary 1 is `n = nu*m/alpha - 1`,
algebraically identical. The difference is the *direction it is read in*: they tune the calibration
size **upward** so a **windowed** procedure's realised level is exact --- a power statement about a
procedure that restarts --- and we read the same inequality **downward**, as the size below which an
**uninterrupted** controller cannot reject at all. Their windowing is, in our terms, the restart
escape.

**Theorem 3 (Vovk--Wang).** The proof is two lines given their domination result, and all three
reviewers spotted it unprompted. Conceding it at the theorem is stronger than being caught by it, so
the paper now does: *"Not the inequality. It rests on Vovk and Wang's domination result, which we use
rather than reprove, and the step from there is short."* What it claims instead is the security
reading, and one genuine characterisation: **not being `theta`-padding-robust and attaining `theta`
are the same condition** --- a family that reaches `theta` nowhere satisfies the definition vacuously
--- so a symmetric rule is vulnerable *precisely when it can fire at all*. That equivalence, not the
bound, is what closes off looking for a better symmetric merger.

The introduction now promises this, so the reader knows the attribution is coming before meeting the
first theorem.

**Gates.** `t65` is at **144**. The `R18` group requires each delta at its claim site, requires the
Huo passage to *precede* Related Work in document order, and forbids priority language
(`"we are the first"`, `"for the first time"`, `"novel observation"`) anywhere --- the standing
non-claim from `docs/03`. Injection-tested: deleting any of the three deltas, dropping the Krönert
direction, removing the Vovk--Wang concession, or inserting a priority claim all fail.

**One gate-design fix found by injection.** The R18 checks used `block_of`, which *raises* when its
anchor is missing --- and deleting the anchor paragraph is the most likely regression. An unhandled
exception reports a finding as a crash. They now use a wrapper that returns empty and fails the check
with its message.

**Layout churn, again.** The added text displaced three floats and split `state-free` across a column.
`\hyphenation{}` cannot help with an explicit hyphen, and document-wide `\exhyphenpenalty=10000` fixed
the class but cost six overfull lines; a `\statefree` macro using `\nobreakdash` costs nothing. That
in turn broke two gates matching the literal string, which was the right prompt to make `t65` expand
the paper's text macros once at read time --- a gate should test what the paper says, not how it
spells it.

---

## Round 17: the defended replay (`t74`) — the experiment two review rounds asked for

Both mock-review rounds converged on the same gap once `t73` had confirmed the allocation finding: the
105-alert horizon-aware arm was priced by **closed form alone**, and a volume cap outside the merging
class appeared to block it. `t74_defended_replay.py` runs the identical pipeline with the same pool
construction as `t48` (modal proto/port over the training prefix — no labels, no detector, no
self-knowledge), and asserts a control: `poly x canonical x src-dst` must reproduce 3 alerts at
`r* = 23, 24, 33`. It does.

### 1. The attack survives contact with a controller worth attacking

| primary window 0.55, canonical, seed 0 | horizon-free | horizon-aware |
|---|---:|---:|
| alerts | 3 | **105** |
| real-flow replay, 200 draws each | 3/3, per-draw 1.000 | **105/105, per-draw 1.000** |
| secondary window | 11/11 | **107/107** |
| pool firing rate | 0 / 20,000 | 0 / 20,000 |

This was the gap that mattered. The pad is three orders of magnitude larger at the horizon-aware arm
(~2,946 flows against ~24), so the *draw* rather than the expectation is the question — one pool flow
reaching the conformal tail adds the whole ceiling `M` to `S`. **None does.** The end-to-end
demonstration now covers **226 canonical alerts against a controller running at recall 0.38**, not
fourteen against one running at 0.01.

### 2. The cap bites, and the paper says so — but it does not close

Priced the way the attacker experiences it (**can it suppress *under* the cap**, `m + r <= n`, against
worst-draw `r`) rather than by pad size:

| cap (flows / host pair / bucket) | horizon-aware alerts still suppressible | benign episodes truncated |
|---:|---:|---:|
| 100 | **5 / 105** | 3.40% |
| 300 | **14 / 105** | 1.04% |
| 3,000 | 53 / 105 | 0.21% |
| 10,000 | 82 / 105 | 0.07% |

Against the **horizon-free** arm the same caps cost the attacker nothing: all three alerts stay
suppressible at any cap of 100 or more, and reaching them needs a cap of 30 at 7.4% benign truncation.

So the honest synthesis, which is now the body's: **the only measured defence that bites sits outside
the class `thm:padding` covers, it costs benign traffic, and it still leaves a residual set the
attacker can silence** — 14 of 105 at ~1% collateral. "Blocked" would have overstated it.

### 3. The grouping key is a third axis of the same law

| primary window, horizon-free | src--dst (headline) | src (source host) |
|---|---:|---:|
| detections | 3 | **46** |
| median `r*` | 24 | **496** |

Coarsening the key detects more *and* costs more to pad. That is the third independent confirmation of
the proportionality: **allocation, order and grouping key all move detections and suppression cost
together**, because `r* = floor(S*alpha_t) - m + 1` scales with the level an alert fires at. What the
paper claims is now a law with three measured axes rather than a point estimate at the cheapest one.

### What this does to the mock reviewers' case

Their shared round-2 objection was: *cheap where the system is worthless, expensive and rate-limitable
where it works.* Half of that is now answered — the attack is validated with real flows against a
controller at recall 0.38 with zero false discoveries. The other half is conceded precisely: a cap
does bite, it is outside the theorem's reach, and it leaves a residual.

`t65` is at **155** checks. The `R20` group asserts the control, the per-draw success, the
suppress-under-cap counts, the concession that a residual survives, and the direction of the
grouping-key result — all recomputed from the artefact.

### Round 17b: blind pre-finalisation audit of `t73`/`t74` — verdict DEFECTIVE, six repairs

A blind codex agent was given a self-contained brief: both scripts, their results JSON with
per-episode detail stripped, the paper's verbatim claims, and six questions. No hint of the expected
answer. It returned **DEFECTIVE**.

**What it confirmed.** The `r*` arithmetic in both scripts, including the `x >= 0` guard, the
`floor(x)+1` form and strictness under an inclusive rejection rule. That the two spending arms differ
in exactly one thing and that `alpha_t` is reconstructed consistently with the run that produced
`fired`. And that **every stated number matches the JSON exactly**.

**What it found — all overclaiming in wording, no number wrong.**

1. **"627,495 needed to clear the whole set" is not a minimum.** Since
   `alpha_t = alpha*gamma_t*(R+1)`, removing an early alert lowers `R`, lowers `alpha_t`, raises
   `tau`, and *cheapens* every later alert. Verified numerically: at the same `S`, `m`, `gamma_t`,
   `r*` runs -55 / 162 / 816 for R = 0 / 5 / 20. The sum over the unperturbed trajectory therefore
   over-counts. The paper's own conventions already say whole-set totals are upper bounds; the new
   sentence had said "needed". Now stated as an upper bound, with the mechanism.
2. **The replay's scope was overstated.** The e-values are measured -- real flows, shipped detector --
   but the aggregation and the controller level are arithmetic on the unperturbed trajectory. What is
   demonstrated is that real ordinary traffic carries no evidence, *not* that a live controller
   re-run under attack behaves identically. Now said.
3. **The Clopper--Pearson stress figures needed their assumptions.** The bound is correct for zero
   successes, and the binomial simulation is the right model *under iid Bernoulli sampling* -- which
   the pool's composition does not establish. 90.5% / 82.5% are also Monte Carlo estimates over 200
   draws, not proofs. Both now labelled.
4. **The LSPR23 pool is service-level, not victim-local.** The threat model says traffic to the
   attacked host pair; the pool is the modal training-prefix protocol/port across the window. It
   cannot be victim-local on LSPR23, because every attacked pair there is 100% malicious -- which is
   exactly the gap the AIT transfer closes. Disclosed at the claim now, not only in Sec. V-E.
5. **The cap's benign cost is an arity-disruption rate.** `benign_arity > n` counts episodes a cap
   would truncate; it does not model what truncation does to their scores. Labelled.
6. **"Zero false discoveries" -> "zero observed false discoveries."**

Its finding 10 -- that the 50-order, 674-episode, `c=10` and AIT claims are not evaluated by these
two scripts -- is correct but not a defect: those come from other experiments, and the brief did not
include them.

**Every repair weakens a sentence without moving a number**, which is the right direction for a
pre-finalisation pass. `t65` gained the `R21` group, which pins each repair by an **absence** as well
as a presence, so the overclaiming form cannot come back: `"needed to clear the whole set"`,
`"at zero false discoveries,"` and the unqualified replay wording are all now forbidden strings.

`t65` is at **163**. All eight gates green, compile clean, 0 undefined references, body p.11.
