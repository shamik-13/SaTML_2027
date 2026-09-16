# Review 13 — independent proof audit (blind Opus + blind codex)

Reviewer ask: hand Lemma 1, Theorems 1–4, Corollaries 1–2, Theorem 3's Vovk–Wang dependency and
Propositions 1–2 to an independent reader and ask **only** "try to falsify each statement; check every
quantifier, boundary inequality, indexing convention and cited theorem dependency."

## Method — what the auditors were given

Not the paper. A single **36 KB self-contained extract**: the 13 statements, their proofs verbatim, and
exactly the notation they need (conformal construction, ceiling $M$, feasibility, absorption, the reject
rule, the spending sequences), plus a macro key. Verified **verbatim against the sources — 13 statement
blocks, zero drift** — so every finding maps onto the real text. Neither auditor read `satml.tex`,
`appendix_proofs.tex` or any code. Both could run python to test candidate counterexamples numerically,
and were told a counterexample that does not actually violate the statement is worse than none.

Two independent auditors (blind Opus subagent; blind `codex exec` scoped to the extract's directory).
**They found disjoint defects** — the pattern `blind-codex-review-workflow` predicts and the reason for
running two.

## Opus — 1 CRITICAL, 2 INCOMPLETE

**Theorem 4 post-rejection bound points the WRONG WAY.** The paper said the displayed expression
"upper-bounds $B^{\star}$ rather than giving it exactly" after $R\ge1$ rejections. It is a **lower**
bound. ADDIS's reward terms sit at their own selected-non-candidate lags $\ell_j\ge0$, at index
$D-\ell_j$; $\gamma$ is decreasing, so each lagged term is $\ge\gamma_D$ and the drive is *larger* than
the collapsed expression — feasibility survives longer, so **more** precursors are needed. Verified
numerically:

| case | displayed | true $B^{\star}$ |
|---|---|---|
| $R=0$ (pre-rejection — where the attack is mounted) | 203 | **203, exact** |
| $R=1$, lag 0 | 313 | 313 |
| $R=1$, lag 10 | 313 | **318** |
| $R=1$, lag 100 | 313 | **373** |

The headline claim is unaffected: the attack is mounted pre-rejection, where the collapse is exact and
$B^{\star}=203$ is confirmed. This is the **second** time an independent audit has found a defect in
Theorem 4 (review 11 found it false without the cap hypothesis).

**Proposition 1 was instantiated at the wrong $d$.** It claimed \cref{thm:family1} with $d=1$. Theorem 1's
conclusion is conditional on $\gamma_t t^d\to0$; at $d=1$ that is $t\gamma_t\to0$, which summability does
**not** give ($\gamma_{2^j}=2^{-j}$, zero elsewhere: sums to one, $t\gamma_t=1$ infinitely often) and
which **fails outright for the paper's own horizon-uniform arm** $\gamma_t=1/T$. Verified: at $T=1000$,
$|\Cal|+1=20T$, donation e-LOND offers $\ge\delta\gamma_t=1/M$ at every $t\le T$, so nothing is absorbed.
The repair is one character: on a rejection-free prefix $R_{t-1}=0$ leaves $g$ constant, so **$d=0$** is
the right instantiation, and then $\sum\gamma_t\le1\Rightarrow\gamma_t\to0$ delivers absorption for every
summable $\gamma$.

**Proposition 2 needs $E_S=0$ on all-zero input, and it is not automatic.** The proof's certificate
$S=\{i<t:E_i=0\}$ requires it, but validity does not imply it — the paper's *own* counterexample family
$\kappa+(1-\kappa)\,\mathrm{mean}$ is symmetric and valid with $F(0)=\kappa>0$. With $\kappa=1,R=19$ the
certificate's denominator is $0$ and the subset is inadmissible, furnishing no bound at all.

**Vovk–Wang dependency (the reviewer's specific ask).** The case split is the *right* use of essential
domination and the cited result is strong enough. One caveat the auditor could flag but not resolve
without the source: VW state Proposition 3.1 for strictly positive vectors, whereas Theorem 3 applies it
at $(x,0^r)$, a boundary point. It supplied a short self-contained replacement, which we verified and
adopted — it also removes any need for monotonicity or measurability of $F_N$.

## codex — 1 "CRITICAL" (overstated), 6 INCOMPLETE/UNDERSPECIFIED

Both of its concrete counterexamples needed correcting, **one in its favour and one against**:

- Its CRITICAL claimed Corollary 1 false via $k=T=1$, $\nCal=19$. The arithmetic is right, the target is
  wrong: the displayed $\nCal\ge kT/c_0-1$ is exact. What fails is the prose gloss — "20 calibration
  units per hypothesis" overstates the total by exactly one at every $T$ (needs $20T-1$).
- Its Proposition 1 counterexample uses $\gamma=(1.8,1.0)$, so $\sum\gamma=2.8>1$ — not a legal e-LOND
  spending sequence. But it points at a real gap: the proof's first move is
  $\bar W_t\le\sum_{i<t}\gamma_i\le1$, so the **normalisation is load-bearing and was unstated**
  (Theorem 1 states it; Proposition 1 did not).
- The Definition quantified "every $r\ge0$" while $F_{m+r}$ and $0^r$ need **integer** $r$ (Theorem 3
  already said integer).
- Theorems 5–6 left $\alpha_t$ unbound, so a reader can take the level to vary with the flow position $i$.
- Its Theorem 4 "uncheckable" verdict was an artefact of our extract, which omitted §VI's definition of
  $S^t-C_{0+}$; the proof does address the collapse.

## Applied (10 changes)

| # | statement | change |
|---|---|---|
| 1 | **Theorem 4** | post-rejection clause corrected to a **lower** bound, with the $313$ vs $373$ counterexample stated; proof rewritten with the lag argument |
| 2 | **Proposition 1** | $d=1\to d=0$, with why: $d=0$ needs only $\gamma_t\to0$; $d=1$ would need $t\gamma_t\to0$, false for $\gamma_t=1/T$ |
| 3 | Proposition 1 | spending normalisation $\sum_t\gamma_t\le1$ now stated |
| 4 | **Proposition 2** | $E_S=0$ on all-zero input now a stated hypothesis, with the $\kappa+(1-\kappa)\mathrm{mean}$ reason it is not automatic |
| 5 | Proposition 2 proof | empty-subset case ($Z_t=0$) stated |
| 6 | **Theorem 3 proof** | self-contained boundary argument replacing reliance on VW's domain; removes monotonicity/measurability needs |
| 7 | Definition | `every $r\ge0$` → `every integer $r\ge0$` |
| 8 | Corollary 1 | gloss now "exactly $20T-1$ and $40T-1$ over a horizon $T$, the ratio being the rate rather than the count" |
| 9 | Theorem 5 | "Fix one hypothesis, offered level $\alpha_t$" — $i$ indexes flow positions, not hypotheses |
| 10 | Theorem 6 | "At that same hypothesis" |

Statements confirmed **SOUND by both auditors**: Assumption 1, Lemma 1, Theorems 1–2, Corollary 2.

## Gating

`313` and `373` are derived from the closed form and stored in **no** artefact, so five `t65` checks now
recompute them and pin the three repaired statements. All injection-tested: reversing the bound
direction, changing $373$, weakening Prop 2's hypothesis, and reverting $d=0\to d=1$ each fail the gate.
Two initially matched nothing because `BODY` stops at `\appendices` and both propositions live after it —
rescoped to the full document.

**Final:** `t45` 268, `t61` 200, `t65` **90**, `t68` 2 — all green; 0 errors, 0 undefined refs.
Body still ends p.13; the page refit remains the last item.

---

# The freeze, made enforceable

The theory has been declared frozen twice and drifted twice, both times in Theorem 4. A freeze recorded
in prose is not a freeze. `proto/t69_theory_freeze.py` turns it into an enforced invariant.

**What is frozen:** 26 objects — the 13 audited statements plus all 13 proofs — recorded in
`proto/theory_freeze.json` by SHA of their whitespace-normalised text, with `provenance` naming which
round cleared what. Five statements are recorded as cleared **sound by both round-13 auditors**
independently: `assump:groupval`, `lem:groupval`, `thm:family1`, `thm:family2`, `cor:closureabsorb`.

**Whitespace-insensitive on purpose.** Re-wrapping a line or reflowing a paragraph does not trip it —
which matters because the page refit is still to come and will reflow the whole body. Changing a
symbol, a quantifier, an inequality direction or a hypothesis does trip it.

**Injection-tested against the actual history**, not invented faults:

| reverted change | gate |
|---|---|
| Thm 4's bound direction (`lower` → `upper`) — the round-13 CRITICAL | **FAIL** |
| Thm 4's cap hypothesis `λ ≥ k/(\|C\|+1)` weakened — the round-11 CRITICAL | **FAIL** |
| Prop 1's `d=0` → `d=1` — the round-13 INCOMPLETE | **FAIL** |
| Definition's `integer r` quantifier dropped | **FAIL** |
| Thm 3's boundary argument broken (in the proof file) | **FAIL** |
| whitespace-only re-wrap of Theorem 4 | **PASS**, as required |

**Re-freezing** is deliberate and documented: `python proto/t69_theory_freeze.py --refreeze` rewrites the
baseline and prints exactly what moved. The module says to do this only after a blind audit clears the
change, because the baseline is meant to track what was *checked*, not what is merely current.

**Standing caveat recorded in the module:** `thm:addis` has now failed two independent audits. Any diff
touching it is suspect until re-audited, whatever the rest of the paper says.

**Gate set is now five:** `t45` 268, `t61` 200, `t65` 90, `t68` 2, `t69` 26 objects / 0 drift.

---

# Round-13 follow-up: four reviewer points, all valid

| # | point | verdict | fix |
|---|---|---|---|
| 1 | Limitations still said "distinct deployments" | **valid** — contradicted §II-E's overlap disclosure | now "overlapping views within that exercise", with a `\cref` to §II-E |
| 1b | "pre-specified secondary window" overclaims | **valid** — the paper only supports "fixed before any validity diagnostic existed" | → "designated secondary window"; the precise provenance stays where it is stated |
| 2 | "pre-declared grid" is not documented | **valid** — the grid appears nowhere a reader can check | → "the smallest of the multipliers we evaluate, $c\in\{2,3,5,10,100\}$" |
| 3 | Table I: nominal guarantee with labels = yes | **valid** — a nominal guarantee turns on e-validity and A1, not labels | row → "Nominal e-LOND FDR guarantee", labels **no**; intro → "Any claim that the nominal FDR guarantee applies to these empirical runs" |
| 4 | "linear in $T$" stated unconditionally | **valid, and the paper contradicted itself** | scoped in all four places |

## Point 4 was the substantive one

`\nCal >= k/alpha_T - 1` is general; `kT/c_0 - 1` is what it becomes **under horizon-uniform spending**.
Under the horizon-free `gamma ~ j^-1.6` the requirement grows as `T^1.6`:

| $T$ | horizon-uniform | horizon-free $j^{-1.6}$ | ratio |
|---|---|---|---|
| $10^4$ | 199,999 | 114,831,676 | 574x |
| 57,368 (episode horizon) | 1,147,359 | 1,879,027,958 | 1,638x |
| 16,353,511 (flow horizon) | 327,070,219 | 1.59e13 | **48,663x** |

The paper's own quoted figures ($3.3\times10^{8}$ vs $1.6\times10^{13}$) already showed this, so the
unqualified wording contradicted Fig. 2 rather than merely overstating it. Fixed in the **abstract**
("Even under the max-min-optimal horizon-uniform allocation... horizon-free allocations cost more"),
the **Fig. 2 caption** (names the $T^{1.6}$ growth and says linearity is the best case), **§IV**
(`\emph{minimum}` calibration size over pre-committed allocations), and the **conclusion**
("at best, linear"). As the reviewer noted, this strengthens the argument: linear is the optimistic
lower envelope, and the allocation actually run is far worse.

## Self-inflicted error caught in the same pass

Rewriting the abstract clause left a dangling sentence -- "...horizon-free allocations cost more. At
flow granularity on the LSPR23 live-fire trace is about $3.3\times10^{8}$..." (no subject, from
changing "which at" to "At"). Repaired.

## Gating

Seven new `t65` checks, all injection-tested: dropping the abstract qualifier, dropping "at best" from
the conclusion, reverting §IV to "required", removing the $T^{1.6}$ fact from the caption, reverting
Table I's labels column, and re-asserting the pre-registration claim each fail the gate. One check
recomputes the super-linear ratio from the closed form, so the qualifier rests on arithmetic rather
than on assertion. Table I's labels column was initially ungated and is now covered.

`t68` caught the reflow stranding a third hyphenated word ("the re-|cent") -- exactly the whack-a-mole
this class was documented to be. Re-measured on the current text, `\brokenpenalty=10000` still costs
more than it buys (it adds a badness-10000 stretched page in the **body**, p.6), so the standing
`\hyphenation` list was extended instead, at zero cost in overfull lines or badness.

**Final:** `t45` 268, `t61` 200, `t65` **97**, `t68` 2, `t69` 26/0 drift, `t70` 3 -- all green,
0 errors. Body ends p.13; the page refit is still the one open item.
