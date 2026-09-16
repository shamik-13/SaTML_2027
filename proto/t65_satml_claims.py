"""Claim -> evidence resolution gate for paper/satml.tex.

Reviewer ask (review 10, point 2): "Every number in the abstract, introduction and conclusion should
resolve to exactly one table/figure or derivation, with the same order, seed, window and status.
Now make it mechanical."

This is that gate, and it is deliberately NARROWER and STRICTER than t61:

  * t61 asks "does this number exist in its artefact?" over the whole of main.tex.
  * t65 asks, for the ABSTRACT and INTRODUCTION of satml.tex only, four questions per number:
        1. does it equal the value its declared source produces (artefact lookup or derivation)?
        2. is the number's declared source UNIQUE -- one artefact path or one closed form?
        3. does the sentence carrying it also carry its order / seed / window / status qualifier,
           or explicitly delegate to a table that does?
        4. is it in the registry at all?  Check 4 is the point: a numeric token that appears in the
           abstract and is NOT registered fails, so a number cannot be added without resolving it.
  * The conclusion must carry NO numeric token.  A number in the conclusion is a number stated far
    from its qualifiers; the fix is to state it where its window and order are.

Run after ANY edit to satml.tex's abstract, introduction or conclusion.
"""
import json, os, pathlib, re, sys

if not __debug__:
    raise SystemExit(f"{__file__} must not run under `python -O`: assertions are its checks")

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TEX = pathlib.Path(os.environ.get("T65_TEX", ROOT / "paper" / "satml.tex"))
OUT = ROOT / "src" / "lib" / "out"
OK, BAD = [], []
S = TEX.read_text()
# Expand the paper's own text macros before any check runs.  A gate must test what the paper SAYS,
# not how it spells it: \statefree renders "state-free" (it exists only to stop a column break
# splitting the compound), and two checks that match the literal string failed the moment it was
# introduced.  Normalise here, once, rather than teaching every check about every macro.
for _m, _t in ((r"\statefree{}", "state-free"), (r"\statefree\ ", "state-free "),
               (r"\statefree", "state-free")):
    S = S.replace(_m, _t)


def seg(a, b):
    i = S.index(a)
    return S[i:S.index(b, i)]


ABSTRACT = seg("\\begin{abstract}", "\\end{abstract}")
INTRO = seg("\\section{Introduction}", "\\section{Statistical Trust Layer")
CONCL = seg("\\section{Conclusion}", "\\section*{Open Science}")
BODY = S[: S.index("\\appendices")]
# RESTRUCTURE (docs/satml_2027_restructure_outline.md).  The ADDIS extension, the claim-dependency
# table, the escape taxonomy and the padding-cost sweeps moved from the body into appendices G, F,
# C and E.  Their CONTENT is unchanged and still gated -- what changed is where it sits -- so the
# checks below that were written against BODY now read PAPER.  Checks that are genuinely about body
# PLACEMENT (the abstract, the conclusion, Sec. IV's wording, the first-flow labelling promise)
# deliberately stay on BODY.


def load(name):
    f = OUT / f"{name}.json"
    assert f.exists(), f"missing artefact {name}"
    return json.load(open(f))


def dig(obj, path):
    """path like 'attainable/2/R=1' -- integers index lists, everything else indexes dicts."""
    for part in path.split("/"):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def q(label, cond, detail=""):
    (OK if cond else BAD).append(f"{label}   {detail}" if detail else label)


# =========================================================================================
# ZETA and the closed forms the paper derives rather than measures.
# =========================================================================================
ZETA_16 = sum(j ** -1.6 for j in range(1, 20_000_000)) + (20_000_000 ** -0.6) / 0.6
T_FLOW, K, ALPHA, W0 = 16_353_511, 1, 0.05, 0.025


def uniform_need(T, c0):
    return K * T / c0 - 1


def horizonfree_need(T, c0):
    return K / (c0 * (T ** -1.6 / ZETA_16)) - 1


# =========================================================================================
# THE REGISTRY.  One row per number that appears in the abstract or the introduction.
#
#   tex        the verbatim string the paper must carry
#   where      'abstract' | 'intro' | 'both'
#   value      the number the string encodes, as the registry reads it
#   source     a one-line human-readable provenance, printed on failure
#   check      callable returning the authoritative value, or None for a dataset/protocol fact
#   tol        relative tolerance when comparing to `check`
#   context    strings that MUST appear in the same paragraph as `tex` (order/seed/window/status).
#              '' means the quantity is order-, seed- and window-independent.
# =========================================================================================
R = []


def reg(tex, where, value, source, check=None, tol=0.02, context=()):
    R.append(dict(tex=tex, where=where, value=value, source=source, check=check, tol=tol,
                  context=tuple(context)))


# --- C1, derivations: algebraic, so no order/seed/window qualifier is owed ---------------
# ROUND 25b: the abstract now carries the scale-free ratio (20 flows per hypothesis at k=1); the
# full-trace extrapolation stays in Sec. III-B, labelled as such, with Fig. 2.
reg("$20$", "abstract", 20, "closed form k/c_0 at k=1, c_0=alpha (LOND/e-LOND)",
    check=lambda: 1 / ALPHA, context=("LOND/e-LOND", "$k=1$"))
reg("$3.3\\times10^{8}$", "body-only", 3.3e8,
    "t21f_H6_scaling attainable[T=16353511]['R=1'] = kT/alpha-1",
    check=lambda: dig(load("t21f_H6_scaling"), "attainable/2/R=1"),
    context=("LOND/e-LOND",))
reg("$6.5\\times10^{8}$", "body-only", 6.5e8,
    "t21f_H6_scaling attainable[T=16353511]['family_I_II'] = kT/w0-1",
    check=lambda: dig(load("t21f_H6_scaling"), "attainable/2/family_I_II"),
    context=("LORD++",))
reg("$1.6\\times10^{13}$", "body-only", 1.6e13,
    "derivation k/(alpha*gamma_T)-1 with gamma_T = T^-1.6/zeta(1.6)",
    check=lambda: horizonfree_need(T_FLOW, ALPHA), context=("LOND/e-LOND",))
reg("$3.2\\times10^{13}$", "body-only", 3.2e13,
    "derivation k/(w0*gamma_T)-1 with gamma_T = T^-1.6/zeta(1.6)  -- LORD++ ONLY",
    check=lambda: horizonfree_need(T_FLOW, W0), context=("LORD++",))
reg("$1.44\\times10^{9}$", "anywhere", 1.44e9,
    "derivation kT/w0-1 at T = 10k flows/s * 3600 s -- LORD++ ONLY",
    check=lambda: uniform_need(10_000 * 3600, W0), context=("LORD++",))
reg("$3.46\\times10^{10}$", "anywhere", 3.46e10,
    "derivation kT/w0-1 at T = 10k flows/s * 86400 s -- LORD++ ONLY",
    check=lambda: uniform_need(10_000 * 86_400, W0), context=("LORD++",))

# --- calibration actually available: measured, seed-independent by construction ----------
reg("$1.8$--$2.4$ million", "body-only", None,
    "min/max NC over the five windows in t28b_reallevel table1")

# --- C2 padding costs: canonical order, seed 0, named window, oracle lower bound ---------
# ROUND 22 (novelty positioning, docs/40_r22_positioning.md): the abstract now carries the cost
# CURVE (24 -> 2,946 at the primary window) instead of the 23--33 endpoints, which stay in Sec. V-D
# where the replay thresholds are stated; that sentence names the order, and the oracle qualifier is
# carried by the abstract's "$24$" row.  212 = 105 + 107 is the horizon-aware replayed total (t74).
reg("$23$--$33$", "body-only", None,
    "t28b table1_by_order/keyhash/0.55_0/pads_real",
    context=("canonical",))
# ROUND 31: the reviewer asked for an abstract carrying three numbers, and named 24 and 2,946 as
# the pair a fresh reader cannot hold ("not trying to remember 24 versus 2,946").  Both endpoints
# move to Sec. V-D, where the cost curve is stated; the rows stay, pinned to the body, so neither
# number can drift and neither can return to the abstract unregistered.
reg("$24$", "body-only", 24,
    "t73_uniform_padding cells/0.55_keyhash_poly/median_pad (the control arm; == t28b med_pad_real)",
    check=lambda: dig(load("t73_uniform_padding"), "cells/0.55_keyhash_poly/median_pad"),
    context=("canonical", "oracle lower bound"))
# ROUND 25: the fourteen/212 replay counts left the abstract (reviewer: per-alert replay must not
# read as one simultaneous attack run, and the abstract keeps three numbers); both live in Sec. V-E
# with their per-alert scope, so the rows are body-only and the R14-2 check below pins the body.
reg("$212$", "body-only", 212,
    "t74_defended_replay n_alerts_always_suppressed summed over the 0.55 and 0.62 uniform cells",
    check=lambda: sum(dig(load("t74_defended_replay"), f"cells/{w}_uniform/n_alerts_always_suppressed")
                      for w in ("0.55", "0.62")),
    context=("horizon-aware",))
# R11-6 replaced the abstract's first-flow AIT number with the CANONICAL one, so the order
# qualification the mock reviewers demanded is gone because the qualification itself is gone.
# The first-flow arm stays in the body as the measured sensitivity.
# ROUND 35: the abstract no longer carries an AIT count at all (it names the method, the body the
# number), so the canonical figure is owed by the PAPER, and the abstract is checked below only for
# not quoting the first-flow one.
reg("78 of 79", "anywhere", None,
    "t67_ait_order canonical arm: suppressible/detected over the flow-only folds")
reg("84 of 85", "body-only", None,
    "t67_ait_order first-flow arm, which reproduces the stored t54 arm")
# ROUND 32/33: the abstract names the attacker capability ladder and its measured gap.  "24 to 65"
# spans the causal sequential oracle (24 own alerts left, horizon-free) and the state-free multiplier
# from the victim-prior pool (65 left, horizon-free); both are t76 sums over the eight flow-only
# organisations of the per-organisation MEDIAN over 100 trajectories (Table V's convention).
if "capability levels" in " ".join(ABSTRACT.split()):   # the ladder is in the codex draft's abstract only
  reg("24 to 65", "abstract", 24,
      "t76_joint_ait: sum over flow orgs of greedy/poly (causal pool) remaining_own median",
      check=lambda: sum(o["flow"]["greedy"]["poly"]["remaining_own"]["median"]
                        for o in load("t76_joint_ait")["orgs"].values()))
  reg("to 65 standing", "abstract", 65,
      "t76_joint_ait: sum over flow orgs of multiplier c_int/k0_m_atk poly remaining_own median",
      check=lambda: sum(o["flow"]["multiplier"]["c_int/k0_m_atk"]["poly"]["remaining_own"]["median"]
                        for o in load("t76_joint_ait")["orgs"].values()))

# --- R16: the cost curve.  The attack was priced only under the horizon-free allocation until
# three independent mock reviewers objected that this is the regime that flatters it.  t73 re-runs
# the identical pipeline with the spending sequence as the only change, so these two numbers are
# what stop the abstract from quoting the cheap end as if it were the system's property.
reg("$105$", "body-only", 105,
    "t73_uniform_padding cells/0.55_keyhash_uniform/detections",
    check=lambda: dig(load("t73_uniform_padding"), "cells/0.55_keyhash_uniform/detections"),
    context=("horizon-aware",))
reg("$2{,}946$", "body-only", 2946,
    "t73_uniform_padding cells/0.55_keyhash_uniform/median_pad",
    check=lambda: dig(load("t73_uniform_padding"), "cells/0.55_keyhash_uniform/median_pad"),
    context=("horizon-aware",))

# --- introduction protocol facts ---------------------------------------------------------
reg("16,353,511 flows", "intro", 16_353_511, "LSPR23 dataset size")
reg("0.55", "intro", None, "primary analysis window")
reg("0.62", "intro", None, "pre-specified secondary window")
reg("0.85", "intro", None, "stress window, evidence not a valid e-value")


# =========================================================================================
# CHECK 1-3: every registered claim
# =========================================================================================
# A paragraph-wide context window is too loose: "LORD++" occurs somewhere in almost every
# paragraph of Section III-B, so dropping the procedure name from the sentence that actually
# carries 3.2e13 still passed.  Scope the qualifier to the SENTENCE.
SENT = re.compile(r"(?<=[.?!])\s+(?=[A-Z\\$])")


def para_of(hay, needle):
    """the sentence of the whitespace-flattened `hay` that contains `needle`."""
    i = hay.index(needle)
    starts = [0] + [m.end() for m in SENT.finditer(hay)]
    a = max(x for x in starts if x <= i)
    later = [x for x in starts if x > i + len(needle) - 1]
    b = min(later) if later else len(hay)
    chunk = hay[a:b]
    # a degenerate split (an abbreviation, a display equation) must not silently widen or
    # narrow the check into uselessness -- fall back to a tight window instead.
    return chunk if len(chunk) >= 40 else hay[max(0, i - 300):i + 300]


def block_of(hay, needle, span=1400):
    """a paragraph-sized window -- for checks whose subject legitimately spans sentences."""
    i = hay.index(needle)
    return hay[max(0, i - 200):i + span]


def flat(t):
    """collapse LaTeX line wrapping: a claim must not become unfindable because it wrapped."""
    return re.sub(r"\s+", " ", t)


PAPER = flat(S)          # body + appendices: "the paper says this somewhere, and it is right"

HAY = {k: flat(v) for k, v in
       {"abstract": ABSTRACT, "intro": INTRO, "both": ABSTRACT + INTRO, "body-only": BODY,
        "anywhere": S}.items()}
for r in R:
    hay = HAY[r["where"]]
    present = flat(r["tex"]) in hay
    q(f"[{r['where']:9}] {r['tex']!r} present", present, f"source: {r['source']}")
    if not present:
        continue
    if r["check"] is not None:
        got = float(r["check"]())
        rel = abs(got - r["value"]) / abs(got)
        q(f"           {r['tex']!r} == {r['source']}", rel <= r["tol"],
          f"registry says {r['value']:.4g}, source gives {got:.6g} (rel {rel:.3%})")
    for c in r["context"]:
        q(f"           {r['tex']!r} qualified by {c!r}", c in para_of(hay, flat(r["tex"])),
          "the qualifier is not in the same SENTENCE as the number")

# the abstract's 23--33 must be exactly the canonical seed-0 primary pads
pads = dig(load("t28b_reallevel"), "table1_by_order/keyhash/0.55_0/pads_real")
q("23--33 is min/max of canonical seed-0 primary pads", [min(pads), max(pads)] == [23, 33],
  f"artefact pads_real = {pads}")
med62 = dig(load("t28b_reallevel"), "table1_by_order/keyhash/0.62_0/med_pad_real")
q("secondary-window median 6 is the canonical seed-0 median", med62 == 6.0, f"artefact = {med62}")
# ROUND 22: the secondary-window median left the abstract (contribution-forward abstract, fewer
# numbers, on reviewer instruction); it remains a headline claim in the body, where t71 pins
# "median cost of six" to the artefact together with its order qualifier.
q("the body states the secondary-window median as six",
  "median cost of six" in flat(BODY) or "median is six" in flat(BODY))
ait = load("t54_ait_suppression")["flow"]
det, sup = sum(o["n_detected"] for o in ait), sum(o["n_suppressible"] for o in ait)
q("84 of 85 matches t54 flow folds", (sup, det) == (84, 85), f"artefact = {sup} of {det}")
# the canonical arm, and the read-back check that it is the same chain as the stored first-flow one
t67 = load("t67_ait_order")
_c, _f = t67["summary"]["canonical"], t67["summary"]["first_flow"]
q("78 of 79 matches t67's canonical AIT arm",
  (_c["n_suppressible"], _c["n_detected"]) == (78, 79),
  f"artefact = {_c['n_suppressible']} of {_c['n_detected']}")
q("t67 reproduces the stored first-flow arm",
  t67["summary"]["reproduces_stored_first_flow"] is True and
  (_f["n_suppressible"], _f["n_detected"]) == (sup, det),
  "the canonical arm is only comparable if the same chain reproduces the stored arm")
q("the abstract's AIT number, if it carries one, is the canonical one, not first-flow, and names its arm",
  "84 of 85" not in flat(ABSTRACT) and "78 of 79 detected episodes" not in flat(ABSTRACT)
  and ("78 of 79" not in flat(ABSTRACT) or "78 of 79 flow-only true detections" in flat(ABSTRACT)),
  "the whole point of R11-6 was to put the headline external number on the reported order")
q("the body keeps first-flow as a labelled sensitivity",
  "gives 84 of 85" in flat(BODY) and "first-flow arrival" in flat(BODY))
# --- R13-3: a NOMINAL guarantee does not depend on dataset labels -----------------------------
# Table I's columns are (valid e, A1, labels, windows).  Labels are what you need to compute a
# realised FDP; whether the nominal FDR guarantee APPLIES turns on e-validity and A1, not on labels.
q("R13-3: the claim-dependency table's e-LOND row claims a nominal guarantee, not a realised FDP",
  "Nominal e-LOND $\\FDR$ guarantee & yes & yes & no &" in PAPER
  and "Nominal e-LOND $\\FDR$ guarantee on data" not in PAPER,
  "labels=yes would make it a realised-FDP row, which is a different claim")
q("R13-3: the intro says what is conditional is the guarantee's APPLICABILITY",
  "Any claim that the nominal $\\FDR$ guarantee applies to these empirical runs" in flat(BODY)
  and "Every $\\FDR$ reading of" not in flat(BODY),
  "'FDR reading of the empirical results' still reads as a measured FDR")

# --- R13-4: 'linear in T' is the HORIZON-UNIFORM BEST CASE, not the general requirement --------
# nCal >= k/alpha_T - 1 is general; kT/c0 - 1 is what it becomes under gamma_t = 1/T.  Under the
# horizon-free gamma ~ j^-1.6 the requirement grows as T^1.6, which the paper's own numbers already
# show (3.3e8 vs 1.6e13 at LSPR23 scale -- a 5-order-of-magnitude gap).  All four places that state
# the rate must carry the qualifier, or the paper contradicts its own Fig. 2.
_Z16 = 2.2857657
_k, _c0, _T = 1, 0.05, 16_353_511
_unif = _k * _T / _c0 - 1
_free = _k * _Z16 * _T ** 1.6 / _c0 - 1
q("R13-4: the horizon-free requirement really is super-linear, so the qualifier is needed",
  _free / _unif > 1e4,
  f"at T={_T:,}: horizon-uniform {_unif:.3g} vs horizon-free {_free:.3g} ({_free/_unif:,.0f}x)")
# ROUND 31: "max-min-optimal horizon-uniform allocation" was the reviewer's example of jargon a
# fresh reader meets before the system.  What must survive is the SUBSTANCE, not the phrase: the
# rate is the best case over allocations, and the abstract must say the others cost more.  Both
# halves are still required, in whatever wording; only the pinned phrasing was relaxed.
q("R13-4: the abstract scopes the linear rate to the best allocation and says others cost more",
  "most favourable budget allocation" in flat(ABSTRACT)
  and "allocations blind to the horizon need more" in flat(ABSTRACT),
  "unqualified 'costs calibration units linear in T' contradicts the paper's own Fig. 2 curve")
q("R13-4: Fig. 2's caption says linearity is the best case, not the general rule",
  "grows as $T^{1.6}$" in flat(S) and "linearity is the" in flat(S)
  and "For every procedure covered by \\cref{thm:family1,thm:family2} the requirement is linear"
      not in flat(S),
  "the caption plots the horizon-free curve; it must not call the requirement linear for everything")
q("R13-4: SS IV says MINIMUM calibration size over pre-committed allocations",
  "\\emph{minimum} calibration size over pre-committed spending allocations" in flat(BODY),
  "eq:exchange is nCal_min under the cheapest allocation, not the requirement for every gamma")
q("R13-4: the conclusion says 'at best, linear'",
  "at best, linear in the number of tested hypotheses" in flat(BODY),
  "the conclusion restated the unqualified rate")

# --- R13: Theorem 4's post-rejection bound DIRECTION ------------------------------------------
# A blind audit found the theorem's post-rejection clause backwards: it called the displayed
# expression an UPPER bound on B*, but ADDIS's reward terms sit at their own lags, gamma decreases,
# so the drive is LARGER and feasibility survives longer -- the expression is a LOWER bound.  These
# numbers are derived from the closed form, not stored in any artefact, so recompute them here.
def _zeta16():
    N = 2_000_000
    return sum(n ** -1.6 for n in range(1, N + 1)) + N ** -0.6 / 0.6 - 0.5 * N ** -1.6

_Z = _zeta16()
_lam, _tau, _k, _al, _w0 = 0.25, 0.5, 1, 0.05, 0.025
_N1 = 1.8e6                      # |C|+1 at the stress window
_floor = _k / _N1
_g = lambda j: (j + 1) ** -1.6 / _Z


def _displayed(W):
    thr = ((_tau - _lam) * W * _N1 / (_k * _Z)) ** (1 / 1.6)
    D = 0
    while not D + 1 > thr:
        D += 1
    return D


def _true_bstar(R, lag):
    """ADDIS's actual budget: coefficients sum to alpha*R but each term sits at index D-lag."""
    def lvl(D):
        terms = _w0 * _g(D) + (_al - _w0) * _g(max(D - lag, 0))
        return min(_lam, (_tau - _lam) * terms)
    D = 0
    while lvl(D) >= _floor:
        D += 1
    return D


q("R13: Theorem 4 is exact in the pre-rejection state (B*=203)",
  _displayed(_w0) == 203 and "$B^{\\star}=203$" not in PAPER,
  f"closed form gives {_displayed(_w0)}")
q("R13: the post-rejection expression is a LOWER bound, and the paper says so",
  _displayed(_al) == 313 and _true_bstar(1, 100) == 373
  and "a \\emph{lower} bound on $B^{\\star}$" in PAPER
  and "upper-bounds $B^{\\star}$ rather than giving it exactly" not in PAPER,
  f"displayed={_displayed(_al)}, true B* at R=1 lag=100 is {_true_bstar(1, 100)}")
q("R13: Prop 2 states the zero-on-all-zero-input hypothesis its proof needs",
  all(x in flat(S) for x in ("$E_S=0$ whenever $E_i=0$ for",
                             "including $S=\\emptyset$",
                             "not implied by e-merging validity")),
  "kappa+(1-kappa)mean is symmetric and valid yet returns kappa>0 on all-zero input, so the "
  "zero-evidence subset certifies nothing without this hypothesis")
q("R13: Prop 1 is instantiated at d=0, not d=1",
  "and $d=0$, because" in flat(S) and "$t\\gamma_t\\to0$, which it does" in flat(S),
  "d=1 would demand t*gamma_t -> 0, which summability does not give and which fails for the "
  "horizon-uniform arm gamma_t=1/T")
q("R13: the paper quotes both numbers of that counterexample",
  "it returns $313$ where $B^{\\star}=373$" in PAPER,
  "313 and 373 are derived from the closed form, not stored in an artefact, so they are gated here")

# --- R12-4: the escape taxonomy must stay exact -----------------------------------------------
# The paper says the absorption predicate is NOT DEFINED for online e-BH.  A blind audit found that
# the III-D rewrite left two places still saying e-BH "escapes the horizon" -- Fig. 2's caption and
# Sec. VI.  Guard the class, not the two sentences: no "escape" verb may take online e-BH as subject.
# strip \cref targets first: the label `sec:escapes` is not prose and must not trip the check
_fb = flat(BODY)
_fb_noref = re.sub(r"\\c?ref\{[^}]*\}", " ", _fb)
# e-BH as the SUBJECT of an escape verb, within one clause (no . ; or --- in between)
_ebh_escape = re.findall(r"e-BH[^.;]{0,50}?\bescapes?\b(?!\s+mechanism)", _fb_noref)
q("R12-4: no sentence says online e-BH 'escapes' -- the predicate is undefined for it, not escaped",
  not _ebh_escape,
  f"{len(_ebh_escape)} occurrence(s): {_ebh_escape[:2]}")
# A pronoun subject defeats the regex above ("...so IT escapes the absorbing horizon"), so guard the
# two captions/sentences that make the positive statement, by content rather than by subject parsing.
_fig2cap = block_of(_fb, "Calibration size needed to keep a rejection possible", span=900)
# The figure used to plot online e-BH beside the covered families, which needed three caption lines
# to say it did not belong.  It is no longer plotted, so the requirement is conditional: IF the
# caption names e-BH it must say the predicate is undefined for it, and either way it must never say
# e-BH "escapes" the horizon.
q("R12-4: Fig. 2 does not present online e-BH as an escaping member of the covered families",
  ("e-BH" not in _fig2cap or "predicate is not defined" in _fig2cap)
  and "escapes the absorbing horizon" not in _fig2cap,
  "online e-BH is outside the predicate; it does not escape it")
q("R12-4: III-D states the predicate is undefined for online e-BH and names two distinct mechanisms",
  ("is simply not defined for it" in _fb
   or "is not defined for a decision that is not taken against a level fixed at arrival" in _fb)
  and ("Two mechanisms avoid the practical consequence" in _fb
       or "Two mechanisms fall outside that class, and they differ in kind" in _fb
       or ("Selective index advancement" in _fb and "fall outside the arrival-time predicate" in _fb))
  and "Two genuine escapes remain" not in _fb,
  "ADDIS escapes arrival-time absorption; online e-BH is outside the predicate -- different kinds")

# --- R12-9: two ledger values that only t61's EXISTENCE sweep covered ------------------------
# The reviewer's claim ledger listed eight headline values; six were already pinned here.  These two
# were reachable only by t61's "does this number appear in some artefact?" sweep, which cannot catch
# a mean/median/one-arm value dressed as the wrong statistic.  Both are recomputed from the artefact
# and scoped to the sentence that makes the claim.
_host = load("t54_ait_suppression")["host"]
_hd, _hs = sum(o["n_detected"] for o in _host), sum(o["n_suppressible"] for o in _host)
# ROUND 31: the host-conditioned arm ran on a hard-coded pair, which a reviewer read as possible
# selective evaluation.  It now runs at every organisation the flow arm covers, so the check is that
# the arm is COMPLETE and that the body states the artefact's own two numbers, whatever they are.
_horgs = {o["org"] for o in _host}
_forgs = {o["org"] for o in load("t54_ait_suppression")["flow"] if o.get("n_detected")}
q("the host-conditioned AIT arm covers every organisation the flow arm detects on",
  _horgs == _forgs and len(_horgs) == 8,
  f"host arm on {sorted(_horgs)}; flow arm detects on {sorted(_forgs)}")
_hsent = para_of(flat(BODY), "host-conditioned true detections")
q("the body states the host-conditioned transfer as the artefact's own counts",
  f"${_hd}$ host-conditioned true detections" in _hsent and f"${_hs}$" in _hsent,
  f"artefact = {_hs} of {_hd} over {sorted(_horgs)}")
q("the body does not present the unsuppressed host episodes as demonstrated attack failures",
  _hs == _hd
  or ("a bound on the replay budget, not a demonstration that they cannot be padded"
      in flat(BODY)[flat(BODY).index("host-conditioned true detections"):][:900]),
  "n_suppressible counts episodes with at least one successful draw, so a zero-success episode is "
  "censored at the replay budget, not proved unpaddable -- and the caveat belongs in the sentence "
  "that states the count, not only in the limitations")
# ROUND 23: the limitations no longer restate the arm's order (reviewer: implementation detail); the
# label now sits at the point of claim itself (Sec. V-F) and in tab:main's row, which is what the
# conventions paragraph promises.
q("the host-conditioned arm is labelled first-flow where it is claimed",
  "first-flow" in _hsent
  and f"AIT host-cond., 8 orgs & first-flow & {_hd} &" in flat(BODY),
  "the conventions paragraph promises a first-flow label at the point of claim")

_b1 = load("t32_B1")
_bstar = _b1["bstar"][0]["bstar"]
q("ADDIS B* = 203 is the artefact's first target and matches its own closed form",
  _bstar == 203 and _b1["bstar"][0]["bstar_closed"] == 203,
  f"artefact bstar={_bstar}, closed={_b1['bstar'][0]['bstar_closed']}")
q("the 152 baseline rejections ADDIS keeps are the artefact's baseline",
  _b1["baseline"]["rejections"] == 152,
  f"artefact baseline rejections = {_b1['baseline']['rejections']}")
q("the paper states 203 next to the 202-precursor boundary that makes it a threshold",
  all(s in para_of(PAPER, "$203$") for s in ("$202$", "152")),
  "203 is a threshold: 202 leaves all 152 rejections intact, 203 silences the target")

_med = _c["median_rstar_by_org"]
q("the paper quotes the canonical per-org median range",
  f"${min(_med.values()):g}$--${max(_med.values()):,}".replace(",", "{,}") in flat(BODY)
  or "$12$--$4{,}650$" in flat(BODY),
  f"artefact range {min(_med.values()):g}--{max(_med.values()):g}")
# The service-matched premium is order-dependent: 1.17-1.52x canonical, 1.37-1.98x first-flow.
# The paper quoted 1.4-2.0 -- the first-flow range -- in a sentence that reads as canonical.
pb = load("t28b_reallevel")["pools_by_order"]
ratios = {o: [pb[o][c]["real"]["service-matched"]["med"] / pb[o][c]["real"]["black-box"]["med"]
              for c in ("0.62_0", "0.85_0")] for o in ("keyhash", "first-flow")}
q("service-matched premium is quoted per order",
  "$1.2$--$1.5\\times$ under the canonical order, $1.4$--$2.0\\times$" in PAPER,
  f"artefact ratios: canonical {ratios['keyhash']}, first-flow {ratios['first-flow']}")
for o, lo, hi in (("keyhash", 1.2, 1.5), ("first-flow", 1.4, 2.0)):
    got = ratios[o]
    q(f"quoted {o} premium brackets the artefact",
      lo - 0.05 <= min(got) and max(got) <= hi + 0.05, f"artefact {got}")
# The 50-order median is conditioned on the order having produced a detection.
q("the 50-order median declares its survivorship conditioning",
  "conditioned on the order having produced a detection" in PAPER,
  "some pre-committed orders detect nothing, so 16--178 is a conditional estimand")
# Table II must not present donation/closure as an unconditional family member.
q("the taxonomy table carries the donation/closure conditions",
  "Donation's bound needs $\\delta<1$" in PAPER and "$H+P_T\\le T$" in PAPER)
q("the taxonomy table carries the mem-e-LORD error-rate caveat",
  "mem-$\\FDR$ rather than $\\FDR$" in PAPER)
# The abstract's escape-price claim: the asymmetric branch keeps recall (0.062 vs 0.065) and pays
# in ordering fragility instead, so "at a priced cost in power" was wrong for it.
# Substance, not phrasing: the asymmetric branch keeps recall (0.062 vs the mean's 0.065) and pays
# in ordering fragility (L* = 1), so the abstract must price it as LEADING flows and must not say
# the escapes cost power.
asym = flat(ABSTRACT)
# RESTRUCTURE: the defence catalogue left the abstract for Sec. VI, so the pricing is checked where
# it is now made.  The negative check below stays on the abstract, which is what it was guarding.
q("the paper prices the asymmetric escape as ordering, not as power",
  "\\emph{leading} flows" in flat(BODY),
  "the ordering price is the asymmetric branch's real cost")
q("abstract does not price every escape as power",
  "at a priced cost in power" not in asym,
  "first-event-only weighting keeps the mean's recall; only the cap loses power")

nc = [v["NC"] for v in load("t28b_reallevel")["table1"].values()]
q("1.8--2.4 million brackets the realised NC range",
  1_800_000 <= min(nc) and max(nc) <= 2_450_000, f"NC range {min(nc)}--{max(nc)}")

# =========================================================================================
# REVIEW 14: the reviewer-centred compression pass.  Four things it changed are load-bearing and
# are pinned here, because each replaced a quantity or a scope that the earlier gates guarded.
# =========================================================================================
# --- R14-1: the body reports a CONTROLLER-ALIGNED feasibility ratio, not the level-w0 margin ----
# The level-w0 margin is a cross-controller scale on which e-LOND (c_0 = 2*w_0) stays feasible down
# to -1/2, so a negative row could still detect and every caption had to explain that.  rho_p has
# its threshold at 1 for the procedure being plotted.  Recompute the quoted range from NC and T --
# the same two numbers the margin comes from -- so the body's range cannot drift from the artefact.
_t28 = load("t28b_reallevel")["table1"]
_C0_ELOND = 0.05                      # c_0 = alpha = 2*w_0
_rho = {k: (v["NC"] + 1) * _C0_ELOND / v["T"] for k, v in _t28.items() if k.endswith("_0")}
q("R14-1: the body's rho range is recomputed from the artefact's NC and T",
  f"$\\rho={min(_rho.values()):.2f}$--${max(_rho.values()):.2f}$" in flat(BODY),
  f"artefact gives rho = {min(_rho.values()):.4f}--{max(_rho.values()):.4f} over "
  f"{sorted(_rho)}; the body must quote that range")
q("R14-1: rho is defined with its threshold at 1, and the level-w0 margin is kept in the appendix",
  "\\rho_p\\ge1$ is exactly cold-start feasibility through $T$" in flat(S)
  and "\\label{eq:rho}" in S and "\\label{eq:margin}" in S
  and S.index("\\label{eq:rho}") < S.index("\\appendices")
  and S.index("\\label{eq:margin}") > S.index("\\appendices"),
  "eq:rho belongs in the body and eq:margin in the appendix; swapping them reinstates the "
  "negative-margin-but-still-feasible explanation the compression pass removed")

# --- R14-2: the abstract's replay claim is scoped to the window replay was actually RUN on ------
# tab:main shows replay for the primary window only.  An abstract that puts the primary and
# secondary costs next to "controlled replay reproduces the closed form" invites the reading that
# both were replayed.
# Review 16 closed the gap this used to guard: the replay had never been run at 0.62 (that window
# was simply absent from t48's POS list), so tab:main said "not run" and the abstract had to be
# scoped to the primary window.  It has now been run, 11/11.  The check therefore inverts: derive
# the replayed windows FROM THE ARTEFACT and require the abstract's count to match, so the claim
# cannot drift in either direction.
_w3 = load("t48_W3")["episodes_keyhash"]
_replayed = {w: _w3[w] for w in ("0.55", "0.62") if w in _w3}
_n_replayed = sum(r["n_suppressible"] for r in _replayed.values())
_ALL_SUPPRESSED = all(r["n_suppressible"] == r["n_detected"] == r["n_match"]
                      for r in _replayed.values())
q("R14-2: both non-stress windows were replayed, all alerts suppressed at the closed form",
  set(_replayed) == {"0.55", "0.62"} and _ALL_SUPPRESSED and _n_replayed == 14,
  f"artefact: {[(w, r['n_suppressible'], r['n_detected']) for w, r in _replayed.items()]}")
# ROUND 22: the abstract states BOTH regimes' replayed counts -- the horizon-free fourteen (t48) and
# the horizon-aware total (t74) -- and no longer the secondary median, which moved to the body.
_t74_ab = load("t74_defended_replay")["cells"]
_n_uniform = sum(_t74_ab[f"{w}_uniform"]["n_alerts_always_suppressed"] for w in ("0.55", "0.62"))
# ROUND 23: t73/t74's `detections` are TRUE detections (fired & ismal); the 0.62 horizon-aware arm
# also has one false discovery, so 212 is a true-detection count and the abstract must say so.
# ROUND 25: the abstract names the method -- per-alert replay AND a joint rerun -- and carries no
# count; the body carries fourteen and 212 with their per-alert scope.  "suppresses all" is banned
# from the abstract because a reviewer read it as one simultaneous end-to-end attack run.
q("R14-2/R25: abstract states per-alert replay + joint rerun without counts; body carries the counts",
  _n_replayed == 14
  and "per-alert" in flat(ABSTRACT).lower()
  and "joint controller-state rerun" in flat(ABSTRACT)
  and "suppresses all" not in flat(ABSTRACT)
  and "covers fourteen horizon-free alerts" in flat(BODY)
  and f"and ${_n_uniform}$ horizon-aware true detections" in flat(BODY),
  f"the artefacts replay {_n_replayed} horizon-free (t48) and {_n_uniform} horizon-aware (t74) "
  f"canonical alerts across 0.55 and 0.62; the abstract states the method, the body the counts")
q("R25: the abstract is the spine plus three findings, not a results list",
  len(flat(ABSTRACT).replace("\\begin{abstract}", "").replace("\\end{abstract}", "").split()) <= 250
  and "per-alert" in flat(ABSTRACT).lower()
  and "cold-start values" in flat(ABSTRACT)
  and "campaign" not in flat(ABSTRACT)
  and "attacker-influenceable" in flat(ABSTRACT)
  # ROUND 26: the state-free multiplier sentence LEFT the abstract (point 9: "which evaluated arms,
  # and was one fixed c used everywhere?" -- the honest answer needs three clauses, so the sentence
  # is gone and Sec. I / V-C carry the scoped result).  The remaining spine is pinned instead:
  # ROUND 31: reworded, not weakened.  Every scope the earlier rounds won is still asserted --
  # the families are arrival-time, the horizon is absorbing, the impossibility needs unbounded
  # membership and attainment, LSPR23 and AIT stay separate -- only the pinned phrasing moved.
  and "two families of arrival-time controllers" in flat(ABSTRACT)
  and "absorbing discovery horizon" in flat(ABSTRACT)
  and "finite alert" not in flat(ABSTRACT)
  and "no symmetric e-merging family can both attain an alert" in flat(ABSTRACT)
  and "Under unbounded membership" in flat(ABSTRACT)
  and "On LSPR23" in flat(ABSTRACT) and "on two\ndatasets" not in ABSTRACT
  and "two datasets" not in flat(ABSTRACT)
  and "greedy oracle joint cost" in flat(ABSTRACT)
  and "per-alert benign-to-victim replay suppresses 78 of 79 flow-only true detections under\nthe canonical order"
  .replace("\n", " ") in flat(ABSTRACT),
  "reviewer (rounds 25/25b/26): spine + three numbers; the joint result stated as measured (levels near "
  "cold-start values), no 'campaign' (LSPR23 has no campaign ground truth), grouping conditional on "
  "attacker-influenceable membership; round 26: the horizon claim scoped to two arrival-time families "
  "and rejection-free runs, the impossibility scoped to unbounded membership, LSPR23 vs AIT separated, "
  "J_seq marked oracle, the AIT number marked per-alert, the state-free sentence removed")
# Scope this to the tab:main ROW.  A body-wide "is 'not run' present?" test passes on a reverted
# table, because the caption that EXPLAINS the phrase also contains it -- verified by injection.
_tabmain = re.search(r"\\begin\{table\}(?:(?!\\end\{table\}).)*?\\label\{tab:main\}"
                     r"(?:(?!\\end\{table\}).)*\\end\{table\}", S, re.S)
_sec_row = next((ln for ln in (_tabmain.group(0).split("\n") if _tabmain else [])
                 if "0.62 secondary" in ln), "")
_r62 = _w3["0.62"]
q("R14-2: tab:main's secondary row carries the artefact's replay result",
  f"{_r62['n_suppressible']}/{_r62['n_detected']}" in _sec_row
  and not re.search(r"&\s*-+\s*\\\\", _sec_row),
  f"expected {_r62['n_suppressible']}/{_r62['n_detected']}; row is {_sec_row!r}. A bare dash here "
  f"reads as zero, missing, or failed suppression -- which is why it may never return.")
q("R14-2: no row of tab:main leaves a replay cell as a bare dash",
  not re.search(r"&\s*-+\s*\\\\", _tabmain.group(0) if _tabmain else ""),
  "every cell must say what happened")

# --- R14-3: the fixed-multiplier result is an LSPR23 result -------------------------------------
# On AIT the attacked episode also contains benign flows the attacker cannot count, so it knows only
# a lower bound on m and the multiplier claim does not transfer as stated.
# ROUND 25: the arms are now NAMED (primary and stress windows, the two with stored per-episode
# arities) and the secondary-window exception is stated: its first canonical alert needs c = 41, so
# c = 10 does not cover it.  t75 confirmed this per-alert and jointly.
q("R14-3: the state-free multiplier claim names LSPR23 and the arms it was evaluated on",
  "on LSPR23, $c=10$" in flat(BODY)
  and "at the primary and stress windows, the two arms with stored per-episode arities" in flat(BODY)
  and "at the secondary window one canonical alert ($m_t=22$, $r^{\\star}_t=859$) needs $c=41$" in flat(BODY),
  "an unscoped 'a fixed multiplier suppresses every canonical alert' generalises to AIT, where the "
  "attacker cannot count the benign flows in its own episode")
q("R14-3: the abstract carries the same scope",
  ("multiplier" not in flat(ABSTRACT) and "state-free" not in flat(ABSTRACT)
   and "statefree" not in flat(ABSTRACT))
  or "On LSPR23's attack-only host pairs" in flat(ABSTRACT),
  "the abstract must not generalise the state-free result past the dataset it was measured on; "
  "round 26 removed the sentence (reviewer point 9), so any return must carry the LSPR23 scope")

# --- R14-4: 'oracle' names ONE thing --------------------------------------------------------
# gamma_t = 1/T knows the horizon; an oracle attack cost knows the realised evidence and the live
# level.  Marking the first "[oracle]" made the two indistinguishable in tables and figures.
# A LaTeX comment does not render, and this file's own comments discuss the retired marker by name,
# so strip comment lines before asking what the PAPER says.
_nocomment = "\n".join(ln for ln in S.split("\n") if not ln.lstrip().startswith("%"))
q("R14-4: the horizon-uniform allocation is not called an oracle",
  "[oracle]" not in flat(_nocomment),
  "the macro must render [horizon-aware]; 'oracle' is reserved for exact r* sizing")
_fbody = flat("\n".join(ln for ln in BODY.split("\n") if not ln.lstrip().startswith("%")))
_bad_oracle = [_fbody[max(0, i - 25):i + 45] for i in range(len(_fbody))
               if _fbody.startswith("oracle", i)
               and not (_fbody.startswith("oracle lower bound", i)
                        or _fbody.startswith("oracle-informed", i)
                        # round 26 (points 4 and 7): the taxonomy's knowledge model and the greedy
                        # sequential attacker are named oracles -- the same attack-cost sense
                        or _fbody.startswith("oracle knowledge", i)
                        or _fbody.startswith("oracle cost", i)
                        or _fbody.startswith("oracle joint cost", i)
                        or _fbody.startswith("oracle strategy", i)
                        or _fbody.startswith("oracle sequential attacker", i)
                        # round 29: the labels serve as the OWNERSHIP oracle (Table II caption) and
                        # Fig. 1 contrasts oracle sizing with the state-free implementation
                        or _fbody.startswith("oracle for which episodes", i)
                        or _fbody[max(0, i - 10):i].endswith("sizing is ")
                        or _fbody[max(0, i - 7):i] in ("greedy ", "ential ")
                        or _fbody[max(0, i - 4):i].endswith("non")
                        # the macro's own DEFINITION names it; its expansion is checked above
                        or _fbody[max(0, i - 14):i].endswith("\\newcommand{\\"))]
q("R14-4: 'oracle' in the body is only ever the attack-cost sense",
  not _bad_oracle,
  f"{len(_bad_oracle)} other use(s): {_bad_oracle[:2]}")

# =========================================================================================
# REVIEW 15: the blind theory audit (two auditors) forced three repairs to frozen mathematics and
# rewrote the e-LORD coverage paragraph.  The repaired text introduces four DERIVED numbers that
# exist in no artefact, so they are recomputed here -- the same treatment Theorem 4's 313/373 got.
# =========================================================================================
def _zeta(s, N=4_000_000):
    return sum(n ** -s for n in range(1, N + 1)) + N ** (1 - s) / (s - 1)


# --- R15-1: the e-LORD reparameterisation needs omega_j in [0,1], not just pre-commitment -------
# A pre-committed omega_1 = 2 is deterministic, hence "pre-committed", yet breaks both gamma >= 0
# and the mass budget.  Both blind auditors found this independently; it is the reason the
# paragraph now states the range constraint.
def _gam(omegas):
    out, prod = [], 1.0
    for w in omegas:
        out.append(w * prod)
        prod *= (1 - w)
    return out


_bad = _gam([2.0, 0.5, 0.5])
_good = _gam([0.3, 0.4, 0.5, 0.6])
q("R15-1: a pre-committed omega_1=2 really does break gamma>=0 and the budget",
  abs(_bad[0] - 2.0) < 1e-12 and _bad[1] < 0 and sum(_bad) > 1,
  f"gamma = {[round(x, 4) for x in _bad]}, sum = {sum(_bad)}")
q("R15-1: under omega_j in [0,1] the partial sums telescope to 1 - prod(1-omega_j) <= 1",
  abs(sum(_good) - (1 - 0.7 * 0.6 * 0.5 * 0.4)) < 1e-12 and sum(_good) <= 1,
  f"sum = {sum(_good):.6f}")
q("R15-1: the paper states both conditions, not just pre-commitment",
  "$\\omega_j\\in[0,1]$" in flat(S)
  and "deterministic\nfunctions of the index".replace("\n", " ") in flat(S)
  and "a pre-committed $\\omega_1=2$ yields" in flat(S)
  and "$\\sum_{t\\le n}\\gamma_t=1-\\prod_{j\\le n}(1-\\omega_j)\\le1$" in flat(S),
  "pre-commitment alone gives fixedness only; without the range constraint the sequence need be "
  "neither non-negative nor summable to one")

# --- R15-2: the sparse counterexample sums to one only at c = 1/zeta(2) -------------------------
_z2 = _zeta(2)
q("R15-2: gamma_{2^n} = n^-2/zeta(2) sums to exactly one, and 2^n gamma_{2^n} diverges",
  abs(sum(n ** -2 for n in range(1, 200_000)) / _z2 - 1) < 1e-4
  and 2 ** 40 / 40 ** 2 > 1e8,
  f"zeta(2) = {_z2:.6f}; an unqualified constant c makes the sum c*zeta(2), not 1")
q("R15-2: the paper carries the normalising constant and scopes the example to d=1",
  "$\\gamma_{2^n}=n^{-2}/\\zeta(2)$" in flat(S)
  and "sums to exactly one" in flat(S)
  and "not enough for \\cref{thm:family1} at $d=1$" in flat(S)
  and "refutes the \\emph{hypothesis}, not the conclusion" in flat(S),
  "'c/n^2 sums to one' is true only at c = 1/zeta(2), and the example refutes the hypothesis, "
  "not the conclusion -- the same sequence has gamma_t -> 0 and is absorbed at d=0")

# --- R15-3: family II's absorption is CONDITIONAL on a rejection-free gap -----------------------
# thm:family1's bound uses only R_{t-1} <= t-1, so it holds on any history; thm:family2's is driven
# by the current gap.  A lag-sum procedure that keeps rejecting keeps its level up.  Recompute the
# limit the paper quotes for LORD++ under gamma ~ j^-1.6 with a rejection at every step.
_Z16 = _zeta(1.6)
_g16 = lambda j: j ** -1.6 / _Z16
_W0, _AL = 0.025, 0.05
import math as _math
_limit = (_AL - _W0) * _g16(1) + _AL * (1 - _g16(1))   # a_1 = alpha - w0, a_j = alpha for j >= 2


def _alpha_all_reject(t):
    if t == 1:
        return _W0 * _g16(1)                            # cold start: no prior rejection yet
    return (_W0 * _g16(t) + (_AL - _W0) * _g16(1)
            + _AL * sum(_g16(u) for u in range(2, t)))


# The BINDING step is the cold start, not the limit: alpha_t climbs, so min_t alpha_t = alpha_1.
# Quoting |C| from the limit (or from any interior t) understates the requirement -- caught by this
# check when the prose first said 26, computed from t=500.
_lo = min(_alpha_all_reject(t) for t in range(1, 3001))
_ncal_needed = _math.ceil(1 / _lo) - 1
q("R15-3: LORD++ rejecting every step climbs towards 0.039 and is feasible from |C|>=91",
  abs(_limit - 0.039) < 0.0015 and _ncal_needed == 91
  and abs(_lo - _alpha_all_reject(1)) < 1e-12,
  f"limit = {_limit:.6f}, min over the run = {_lo:.6f} at t=1, so |C| >= {_ncal_needed}")
q("R15-3: the paper states the asymmetry between the two families",
  "feasible once $\\nCal\\ge91$, the binding step being the cold start itself" in flat(S)
  and "absorption does not depend on the run being" in flat(S)
  and "its absorption is conditional on such a gap occurring" in flat(S),
  "thm:family2 proves conditional absorption, not an unconditional horizon; without this a reader "
  "concludes lag-sum procedures die when they need not")

# --- R15-4: thm:family2 must hypothesise a finite ceiling -------------------------------------
q("R15-4: thm:family2 hypothesises bounded evidence, which its 1/M threshold needs",
  re.search(r"\\begin\{theorem\}\[Finite discovery horizon, lag-sum family\]\s*"
            r"\\label\{thm:family2\}\s*Let the evidence be bounded by \$\\ceil<\\infty\$", S),
  "with unbounded evidence 1/M = 0, the set defining Delta* is empty and Delta* is not finite, "
  "so the theorem was false as written")

# --- R15-5: Route B is presented as the lemma it is, not as a second proof of the class result --
q("R15-5: Route B's scope is stated exactly",
  "That yields the impossibility only for" in flat(PROOFS := pathlib.Path(
      str(TEX).replace("satml.tex", "appendix_proofs.tex")).read_text())
  and "not for the class" in flat(PROOFS)
  and "Route B establishes the impossibility for a negatively-dependent construction" not in flat(PROOFS),
  "Route B proves F_N <= 1 on a mean-one two-point vector; it says nothing about the UNPADDED "
  "value, so it yields no violation for a family that returns 0 on that vector")

# =========================================================================================
# R16: every cell of the cost-curve table is recomputed from t73, and the control arm must
# reproduce the shipped numbers -- without that the comparison is meaningless.
# =========================================================================================
_t73 = load("t73_uniform_padding")
q("R16: t73's control arm reproduces the shipped canonical numbers",
  _t73.get("control_reproduced") is True
  and dig(_t73, "cells/0.55_keyhash_poly/pads") == [23, 24, 33]
  and dig(_t73, "cells/0.62_keyhash_poly/detections") == 11,
  "the uniform arm is only comparable if the poly arm reproduces 3/[23,24,33] and 11 exactly")

_rows = [("0.55 primary & horizon-free", "0.55_keyhash_poly"),
         ("\\quad & horizon-aware", "0.55_keyhash_uniform"),
         ("0.62 secondary & horizon-free", "0.62_keyhash_poly"),
         ("\\quad & horizon-aware", "0.62_keyhash_uniform")]
# ROUND 25: the table gained a "joint Sigma" column -- the sequential attacker's total when the
# controller is re-run over the padded stream (t75) -- so each row now ends with that value.
_t75r = load("t75_joint_rerun")
for _label, _cell in _rows:
    _r = dig(_t73, f"cells/{_cell}")
    _joint = dig(_t75r, f"cells/{_cell}/adaptive/total_cost")
    _fdp = _r["false_positives"] / max(1, _r["detections"] + _r["false_positives"])
    _line = (f"{_label} & {_r['detections']} & {_fdp:.3f} & "
             f"${_r['median_pad']:,.0f}$ & ${_r['total_pad']:,}$ & ${_joint:,}$ \\\\").replace(",", "{,}")
    q(f"R16: tab:costcurve row {_cell} is the artefact's",
      flat(_line) in flat(S), f"expected row: {_line}")

# The whole point of the table: a controller that alerts more is dearer to silence.  Assert the
# DIRECTION from the artefact, so a future edit cannot quietly invert the claim.
for _pos in ("0.55", "0.62"):
    _p = dig(_t73, f"cells/{_pos}_keyhash_poly")
    _u = dig(_t73, f"cells/{_pos}_keyhash_uniform")
    q(f"R16: at {_pos} the horizon-aware arm detects more AND costs more per alert",
      _u["detections"] > _p["detections"] and _u["median_pad"] > _p["median_pad"],
      f"poly {_p['detections']} det / r*={_p['median_pad']}; "
      f"uniform {_u['detections']} det / r*={_u['median_pad']}")
# ROUND 23: "no allocation escapes it" sat in the sentence that also said the attack is "never
# blocked", two lines before a cap that blocks most horizon-aware pads; the claim is now scoped to
# Theorem 3's unbounded-membership model (wording only, same artefact side).
q("R16: the body states the cost is set by the level the alert fired at",
  "increasing in $\\alphat$, so \\emph{the cost of suppression is set by the level the" in flat(S)
  and "spending allocation cannot eliminate padding" in flat(S),
  "without the mechanism the two arms read as an unexplained discrepancy")
q("R16: III-D says the grouped counts are an allocation property, the flow shortfall is not",
  "Those counts are a property of the spending sequence, not of the evidence ceiling" in flat(S)
  and "allocation-optimal already" in flat(S),
  "the flow-granularity shortfall is what cor:budget requires under the BEST sequence; the grouped "
  "detection counts are not, and conflating them is the objection three mock reviewers raised")

# =========================================================================================
# R17: conspicuity, and the buried numbers the mock-review findability ledgers flagged.
# Two reviewers marked "would anyone notice a pad this size?" UNANSWERED; it matters far more
# now that the horizon-aware arm needs ~10^3 flows.  Everything here recomputes from t73/t35.
# =========================================================================================
_c73 = load("t73_uniform_padding")["cells"]
_pp, _uu = _c73["0.55_keyhash_poly"], _c73["0.55_keyhash_uniform"]
_cap = lambda r, n: next(x for x in r["ratelimit_curve"] if x["cap"] == n)

q("R17: the two arms really do sit on opposite sides of the conspicuity question",
  _pp["median_deployment_exceedance"] > 20 * _uu["median_deployment_exceedance"]
  and _cap(_uu, 100)["pads_blocked"] > 0.9 and _cap(_pp, 100)["pads_blocked"] == 0.0,
  f"poly pad is at the {100*_pp['median_deployment_exceedance']:.2f}% exceedance and unblockable "
  f"at cap 100; uniform pad at {100*_uu['median_deployment_exceedance']:.2f}% and "
  f"{100*_cap(_uu,100)['pads_blocked']:.0f}% blocked")
q("R17: the body quotes the padded arities and the exceedances from the artefact",
  f"median arity {_pp['median_padded_arity']:.0f} against the horizon-free" in flat(S)
  and f"{100*_pp['median_deployment_exceedance']:.0f}\\%" in flat(S)
  and f"only ${100*_uu['median_deployment_exceedance']:.2f}\\%$ of episodes reach" in flat(S),
  "conspicuity numbers must be the artefact's, not transcribed")
# R20 supersedes the pad-SIZE framing with the attacker-relevant one (can it suppress UNDER the
# cap?), measured in t74 against worst-draw pricing.  Keep only the defender-cost half here.
_uu62 = _c73["0.62_keyhash_uniform"]
q("R17/R25: the body quotes the cap's cost to the defender from the artefact (cap 100, both windows)",
  f"${100*_cap(_uu,100)['benign_truncated']:.1f}\\%$ and "
  f"${100*_cap(_uu62,100)['benign_truncated']:.1f}\\%$ of benign episodes truncated at $100$" in flat(S),
  "a volume cap is the practitioner's first defence; its cost to the defender must be measured")
q("R17: the defence table carries the cap as a row outside the merging class",
  "Per-host-pair volume cap" in flat(S) and "outside the merging class" in flat(S),
  "a rate limit is not an e-merging fix; presenting it inside the class would be wrong")

# --- R17b: the restart comparison must hold grouping, seed and TOTAL BUDGET fixed -------------
# The paper said "hourly reset takes recall from 0.065 to 0.406".  0.406 is a TWO-SEED MEAN at
# ONE-hour grouping with a total budget of 0.45 -- compared against a seed-0, two-hour, q=0.05
# baseline.  Three variables moved at once.  Pin the like-for-like row instead.
_t35 = load("t35_E2_restart")["rows"]


def _row(**kw):
    hits = [r for r in _t35 if all(r.get(k) == v for k, v in kw.items())]
    assert len(hits) >= 1, f"no t35 row for {kw}"
    return hits[0]


_base = _row(pos=0.55, dseed=0, proc="LOND", gamma="poly", grouping_h=2, epoch_h=None,
             alloc="per-epoch", alpha_total=0.05)
_rest = _row(pos=0.55, dseed=0, proc="LOND", gamma="poly", grouping_h=2, epoch_h=2,
             alloc="uniform", alpha_total=0.05)
q("R17b: like-for-like restart (same grouping, seed, deployment-wide budget) is 18 -> 55",
  (_base["rejections"], _rest["rejections"]) == (18, 55)
  and abs(_base["recall"] - 0.065) < 0.001 and abs(_rest["recall"] - 0.200) < 0.001
  and _rest["fdp"] == 0.0,
  f"artefact: {_base['rejections']}@{_base['recall']:.3f} -> "
  f"{_rest['rejections']}@{_rest['recall']:.3f}, fdp={_rest['fdp']}")
q("R17b: the paper quotes the like-for-like figures and no longer the mismatched 0.406",
  "e-LOND from 18 rejections to 55, recall $0.065$ to $0.200$" in flat(S)
  and "hourly reset takes recall from $0.065$ to $0.406$" not in flat(S)
  and "has to hold grouping, seed and total budget fixed" in flat(S),
  "0.406 is a two-seed mean at 1h grouping and a 0.45 total budget; the baseline it was compared "
  "against is seed 0, 2h grouping, q=0.05")

# --- R17c: the per-window canonical counts, which two reviewers had to hunt for ---------------
_kh = load("t28b_reallevel")["table1_by_order"]["keyhash"]
_counts = [_kh[f"{p}_0"]["detected_elond"] for p in (0.55, 0.62, 0.7, 0.77, 0.85)]
q("R17c: the body gives all five canonical per-window counts, including the zeros",
  _counts == [3, 11, 0, 0, 34]
  and "detect $3$, $11$, $0$, $0$ and $34$ episodes" in flat(S),
  f"artefact counts {_counts}; two mock reviewers marked these BURIED")
q("R17c: e-LORD's horizon-aware count is stated where the allocation claim is made",
  "e-LORD under the horizon-aware e-GAI weighting reaches 101 detections" in flat(S),
  "a procedure in the same covered family, same premise, reaching 101 corroborates t73")

# =========================================================================================
# R18: novelty positioning.  All three mock reviewers independently observed that the prior art
# closest to each formal result is disclosed only in Related Work, three to five pages after the
# result itself -- so a reader forms a novelty judgement before meeting the attribution.  The
# substance was already correct (review 6 verified the Huo and Kroenert collisions); what these
# pin is that the delta is stated AT each claim, and that it never overclaims priority.
# =========================================================================================
_flatS = flat(S)
# The paper's own preamble comment discusses this round, so ask what the PAPER says, not its comments.
_flatS_nc = flat("\n".join(ln for ln in S.split("\n") if not ln.lstrip().startswith("%")))


def _blk(anchor, span=900):
    """block_of, but a MISSING anchor fails the check instead of raising.

    Deleting the anchor is the most likely regression here -- a compression pass drops the
    paragraph header -- and an unhandled exception reports that as a crash rather than as the
    finding it is.  Verified by injection.
    """
    return block_of(_flatS, anchor, span=span) if anchor in _flatS else ""


# ROUND 22 (novelty positioning).  A later review read the round-18 passages as the paper supplying
# the language for its own rejection -- each opened by conceding what was NOT new.  The attribution
# stays AT the claim (the round-18 requirement), but each passage now opens with the contribution and
# runs prior work -> delta -> consequence.  Both halves are pinned: citation and delta present, and
# the concession openers must not return (negative check at the end of this block).
_thm12 = _blk("Contribution relative to prior observations.}")
q("R18: the finite-horizon theorems state the delta over Huo et al. where they are stated",
  "\\cite{huo2024realtime}" in _thm12
  and "structural infeasibility" in _thm12
  and "\\emph{absorbing}" in _thm12
  and "procedure-and-sequence pairs" in _thm12,
  "the phenomenon is prior art; the paper may claim the characterisation, never the observation")
q("R18: and that passage precedes Related Work in the document",
  bool(_thm12) and _flatS.index("Contribution relative to prior observations.}")
  < _flatS.index("\\section{Related Work}"),
  "a delta stated only in Sec. VIII arrives after the reader has judged the theorem")

_cor = _blk("gives the best achievable cold-start scaling", span=900)
q("R18: Corollary 1 credits Kroenert et al. at the claim and points to the full comparison",
  "\\cite{kronert2024fdr}" in _cor and "algebraically related" in _cor
  and "\\cref{sec:related}" in _cor,
  "the attribution stays at the claim; the object-and-consequence distinction is in Related Work")
_corrw = _blk("derive an algebraically related equality, $n=\\nu m/\\alpha-1$", span=900)
q("R18: Related Work states Kroenert's identical algebra as a different object and consequence",
  "\\cite{kronert2024fdr}" in _corrw and "opposite direction" in _corrw
  and "different object and consequence" in _corrw and "restart escape" in _corrw
  and "\\emph{uninterrupted}" in _corrw,
  "n = nu*m/alpha-1 is algebraically cor:budget; the distinction is the direction it is read in")

_pad = _blk("Contribution of \\cref{thm:padding}.}")
q("R18: Theorem 3 credits Vovk-Wang at the theorem and claims the cross-arity property, not the bound",
  # ROUND 31: the reviewer asked for the exact Vovk-Wang result number rather than a bare [8],
  # so the precise pointer is now REQUIRED here and at the proof idea.  Prop. 3.1 is "the
  # arithmetic mean M_K essentially dominates any symmetric e-merging function" (AoS 49(3), Sec. 3).
  "\\cite[Prop.~3.1]{vovk2021evalues}" in _pad and "which we use rather than reprove" in _pad
  and "cross-arity robustness property" in _pad and "but not both" in _pad
  and "\\cite[Prop.~3.1]{vovk2021evalues}" in _flatS_nc.split("Contribution of")[0],
  "the proof is two lines given the domination result; credit it, then state the new property")
# ROUND 23: the equivalence argument (vacuity, the all-M witness) moved to app:attain on reviewer
# instruction; the body keeps the one-clause statement and points there.
_attain = _blk("Attainment and the symmetric class}", span=1400)
q("R18: and the claimed contribution is the attainment equivalence, which is a real characterisation",
  "vulnerable at precisely the alert thresholds it can attain" in _pad
  and "\\cref{app:attain}" in _pad
  # R24-5: "can fire at all" read as OPERATIONAL firing on the deployed evidence support, which is
  # strictly stronger than attaining theta -- app:attain's own 1/2-mean witness attains theta and
  # cannot fire.  The equivalence is exact only at a FIXED theta, so the slogan must name it.
  and "vulnerable precisely when it can fire at all" not in _flatS_nc
  and "same condition" in _attain and "all-firing group" in _attain
  and "make the result load-bearing" not in _flatS_nc,
  "{not theta-padding-robust} <=> {attains theta}: a family reaching theta nowhere is vacuously "
  "robust, so the theorem says exactly which families are exposed")
q("R22: no concession opener or rebuttal phrase survives -- lead with the contribution, credit inside it",
  all(x not in _flatS_nc for x in (
      "What is new here.", "The phenomenon is not.", "Not the inequality.",
      "the step from there is short", "The same inequality is already in the literature",
      "would reach the same conclusions", "the honest statement is",
      "The arm that matters is the other one", "worth stating rather than leaving to be inferred",
      "not because it is the better choice", "the only mitigation we measure that bites",
      "the only measured defence that bites", "Our contribution is to connect them")),
  "each of these handed a reviewer the first line of a novelty-critical review (round-22 feedback)")
q("R22: the introduction states the contribution affirmatively, as an emergent failure mode",
  "We identify an emergent failure mode of statistical trust layers" in _flatS
  and "\\emph{A deployment-level feasibility law" in _flatS
  and "\\emph{A cross-arity security impossibility" in _flatS
  and "\\emph{An operational cost and mitigation boundary" in _flatS,
  "the three contributions must read as one result, not as three literatures placed side by side")
q("R22: the two spending regimes are defined together in Sec. II and priced together in Sec. V",
  "We evaluate two deployment regimes" in _flatS
  and "The two regimes answer different questions" in _flatS
  and "\\label{sec:costcurve}" in S
  and "not padding robustness}" in _flatS,
  "the horizon-aware arm is a co-primary regime, not a defensive control added after review")
q("R22: the replay is named for what it is -- per-alert, at the original controller level",
  "per-alert real-flow replay" in _flatS
  and "evaluates each alert separately at the controller level it received on the unperturbed run"
      in _flatS
  and "not a joint rerun of the altered controller trajectory" in _flatS
  and "end-to-end demonstration" not in _flatS_nc
  and "The scope of the replay is exact" not in _flatS_nc,
  "the controller trajectory is not re-run under attack, so 'end-to-end' overstates the replay")

# ROUND 23: the intro's promise read as a response-to-reviewers instruction embedded in the paper;
# the contribution passages perform the function themselves, so the sentence is gone and stays gone.
q("R18/R23: the introduction does not announce the attribution scheme",
  "Each formal result below states" not in _flatS_nc,
  "the passages credit prior art at the claim; announcing that in the intro reads as rebuttal text")
q("R18: no priority claim over the phenomenon itself survives anywhere",
  "we are the first" not in _flatS.lower() and "for the first time" not in _flatS.lower()
  and "novel observation" not in _flatS.lower(),
  "docs/03 non-claim: never imply priority over the conformal-floor incompatibility")

# =========================================================================================
# R19: two findings from the second mock-review round, both about counting.
# =========================================================================================
# --- R19-1: the number-word must agree with the list it introduces --------------------------
# The body said "three of the five are zero" beside the list 3, 11, 0, 0, 34 -- two zeros -- and
# the very next sentence said "the two that detect nothing".  Every gate checked the LIST; none
# checked the word.  Derive the word from the artefact.
_khc = load("t28b_reallevel")["table1_by_order"]["keyhash"]
_cnts = [_khc[f"{p}_0"]["detected_elond"] for p in (0.55, 0.62, 0.7, 0.77, 0.85)]
_nzero = sum(1 for c in _cnts if c == 0)
_WORD = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
q("R19-1: the count word beside the per-window list matches the artefact",
  f"{_WORD[_nzero]} of the five are zero" in flat(S)
  and f"detect ${_cnts[0]}$, ${_cnts[1]}$, ${_cnts[2]}$, ${_cnts[3]}$ and ${_cnts[4]}$ episodes"
      in flat(S),
  f"artefact counts {_cnts}: {_nzero} zeros, so the word must be {_WORD[_nzero]!r}")

# --- R19-2: the flow-granularity shortfall must be quoted at ONE scale ------------------------
# 3.3e8 is the requirement for T = the WHOLE stream; 1.8-2.4M is the calibration accompanying a
# 15% deployment block.  Juxtaposing them reads as a ~134x shortfall when the scale-consistent
# figure is k/c_0 = 20x -- short even if every flow in the exercise were calibration.
_T, _k, _c0 = 16_353_511, 1, 0.05
_need = _k * _T / _c0 - 1
q("R19-2: the requirement really is k/c_0 times the whole exercise",
  abs(_need / _T - _k / _c0) < 0.01 and abs(_k / _c0 - 20) < 1e-9,
  f"need {_need:.4g} = {_need/_T:.2f}x the {_T:,}-flow stream")
q("R19-2: the body states the shortfall against the whole exercise, not against a 15% block",
  "$20$ times the entire exercise" in flat(S)
  and "would not be met by devoting \\emph{every}" in flat(S)
  and "The shortfall is the count ratio $k/c_0$ itself" in flat(S),
  "comparing a full-stream horizon against a 15%-block calibration inflates 20x to ~134x")

# --- R19-3: the 50-order spread, stated as the alert set and not only as the costs -----------
# The body said orders "move those costs but not the conclusion".  The artefact says the median is
# ONE detection and that 19 of 50 orders detect nothing -- so the canonical three is not a typical
# draw, and the conditional claim (wherever an alert exists it is suppressible) is what survives.
_ens = load("t53_ordering")["rows"][0]["ensemble"]
_none = 50 - _ens["n_orders_with_detection"]
q("R19-3: the body states the order spread from the artefact, not just that costs move",
  _ens["tp_median"] == 1.0 and _ens["tp_min"] == 0 and _ens["tp_max"] == 10
  and f"median is \\emph{{one}} detection" in flat(S)
  and f"${_none}$ of the fifty produce none at all" in flat(S)
  and "move those costs but not the\nconclusion" not in S,
  f"artefact: median {_ens['tp_median']}, range {_ens['tp_min']}-{_ens['tp_max']}, "
  f"{_none}/50 orders with no detection")

# --- R19-4: the canonical order is the ensemble MAX at the secondary window ------------------
# A reviewer asked whether the headline order was chosen after seeing outcomes.  It was not -- it is
# chosen so that padding moves no other hypothesis -- but at 0.62 it happens to be the best of the
# fifty draws, and a paper that does not say so invites the inference.
_r62 = [r for r in load("t53_ordering")["rows"]
        if abs(float(r["pos"]) - 0.62) < 1e-9 and r["seed"] == 0][0]
_c62 = _r62["named"]["bucket, hashed-key (canonical)"]["tp"]
q("R19-4: the paper discloses that the canonical order is the ensemble max at 0.62",
  _c62 == _r62["ensemble"]["tp_max"]
  and "the canonical order is the ensemble \\emph{maximum}" in flat(S)
  and "not because it detects more" in flat(S),
  f"artefact: canonical {_c62} vs ensemble max {_r62['ensemble']['tp_max']}, "
  f"median {_r62['ensemble']['tp_median']}")

# =========================================================================================
# R20: the defended replay (t74).  Two rounds of mock review said the horizon-aware arm was
# priced by closed form alone and that a volume cap outside the merging class blocked it.  t74
# replays real pool flows against that arm stochastically and prices the cap the way the attacker
# experiences it -- can it suppress UNDER the cap, m + r <= n -- rather than by pad size.
# =========================================================================================
_t74 = load("t74_defended_replay")
_c74, _f74 = _t74["cells"], _t74["families"]
_cap74 = lambda r, n: next(c for c in r["cap_curve"] if c["cap"] == n)
q("R20: t74's control reproduces the shipped canonical numbers",
  _t74.get("control_reproduced") is True
  and _c74["0.55_poly"]["r_closed_sorted"] == [23, 24, 33],
  "without the control the horizon-aware arm is not comparable")

_u55, _u62 = _c74["0.55_uniform"], _c74["0.62_uniform"]
q("R20: real-flow replay suppresses every horizon-aware alert on every draw",
  _u55["n_alerts_always_suppressed"] == _u55["detections"]
  and _u62["n_alerts_always_suppressed"] == _u62["detections"]
  and _u55["per_draw_success_min"] == 1.0 and _u62["per_draw_success_min"] == 1.0
  and _u55["pad_fire_rate"] == 0.0,
  f"artefact: {_u55['n_alerts_always_suppressed']}/{_u55['detections']} and "
  f"{_u62['n_alerts_always_suppressed']}/{_u62['detections']}, pool firing rate "
  f"{_u55['pad_fire_rate']}")
q("R20: the body states the horizon-aware replay result",
  f"${_u55['n_alerts_always_suppressed']}/{_u55['detections']}$ and "
  f"${_u62['n_alerts_always_suppressed']}/{_u62['detections']}$" in flat(S)
  and "pool flow reaching the conformal" in flat(S),
  "the arm that matters was priced by closed form alone until this experiment")
# The pool contains NO firing flow, so resampling it is deterministic and cannot bound the risk.
# The paper must separate the observed fact from the residual risk, and quantify the latter at the
# Clopper-Pearson limit -- otherwise "per-draw success 1.000" reads as a probabilistic result when
# it is an arithmetic one.
q("R20: the replay's zero-firing pool is stated as a fact, not as a probabilistic test",
  _u55["pool_firing_count"] == 0 and _u62["pool_firing_count"] == 0
  and "\\emph{none} reaches the tail" in flat(S)
  and "replay cannot bound" in flat(S),
  f"pool firing counts {_u55['pool_firing_count']}, {_u62['pool_firing_count']} over the FULL pool")
q("R20: and the residual risk is quantified at the Clopper-Pearson upper limit",
  _u55["per_draw_success_at_ub_min"] < 1.0
  and f"{100*_u55['per_draw_success_at_ub_min']:.1f}\\%" in flat(S)
  and f"{100*_u62['per_draw_success_at_ub_min']:.1f}\\%" in flat(S)
  and "Clopper--Pearson upper limit" in flat(S),
  f"worst-alert success at the CP bound: {_u55['per_draw_success_at_ub_min']:.3f} (0.55), "
  f"{_u62['per_draw_success_at_ub_min']:.3f} (0.62)")

# ROUND 25: t75 re-runs the controller under each cap; the paper quotes the JOINT outcome (alerts that
# still fire = structural + cascade victims) and keeps the per-alert reading as the labelled comparison.
_t75c = load("t75_joint_rerun")["cells"]
_cj = lambda w, n: next(r for r in _t75c[f"{w}_keyhash_uniform"]["capped_adaptive"] if r["cap"] == n)
_det55 = _t75c["0.55_keyhash_uniform"]["unperturbed"]["true_detections"]
_det62 = _t75c["0.62_keyhash_uniform"]["unperturbed"]["true_detections"]
q("R20/R25: the cap is priced against the sequential attacker, from the artefact",
  f"${_cj('0.55',100)['remaining_true']}$ of the ${_det55}$ horizon-aware primary-window alerts still fire"
  in flat(S)
  and f"${_cj('0.55',100)['n_fired_structural']}$ because their pad would not fit even at the cold-start level"
  in flat(S)
  and f"and ${_cj('0.55',100)['n_fired_cascade_victims']}$ because those first alerts raise $R$" in flat(S)
  and f"${_cj('0.62',100)['remaining_true']}$ of ${_det62}$ fire (${_cj('0.62',100)['n_fired_structural']}$ and "
      f"${_cj('0.62',100)['n_fired_cascade_victims']}$)" in flat(S)
  and f"${_cj('0.55',300)['remaining_true']}$ and ${_cj('0.62',300)['remaining_true']}$ alerts firing" in flat(S)
  and f"predicts ${_det55 - _cj('0.55',300)['per_alert_suppressible_under_cap']}$ and "
      f"${_det62 - _cj('0.62',300)['per_alert_suppressible_under_cap']}$" in flat(S)
  and _cj("0.55", 1000)["remaining_true"] == 0 and _cj("0.62", 1000)["remaining_true"] == 0
  and "at $1{,}000$ the sequential attacker silences both windows" in flat(S),
  f"artefact (t75): cap 100 -> {_cj('0.55',100)['remaining_true']}/{_det55} and "
  f"{_cj('0.62',100)['remaining_true']}/{_det62} fire; cap 300 -> {_cj('0.55',300)['remaining_true']} "
  f"and {_cj('0.62',300)['remaining_true']}; per-alert reading at 300: "
  f"{_det55 - _cj('0.55',300)['per_alert_suppressible_under_cap']} / "
  f"{_det62 - _cj('0.62',300)['per_alert_suppressible_under_cap']}")
q("R25: the joint sequential cost and the padded-alert statistics are the artefact's, and scoped",
  f"pays ${_t75c['0.55_keyhash_uniform']['adaptive']['total_cost']:,}$ flows in total".replace(",", "{,}")
  .replace("{,}{,}", "{,}") in flat(S)
  and "under the canonical order this attacker pays" in flat(S)
  and "the cost of one greedy oracle strategy on this stream and therefore an upper bound on the minimum "
      "joint cost" in flat(S)
  # round 26 (point 6): a window total cannot be "near" a per-alert price; what stays near cold start
  # is the LEVEL, and hence the pad size
  and "stays near the cold-start price" not in flat(S)
  and "keeps subsequent testing levels at or near their cold-start values" in flat(S)
  # "campaign" survives only in the dataset-limitation sense (no flow-to-campaign identifier); the
  # empirical claims say "attacker-controlled episodes in the window" / "joint window-level cost".
  and not any(x in flat(BODY) for x in ("whole campaign", "campaign price", "campaign minimum",
                                        "its campaign", "a campaign from", "silencing a campaign",
                                        "campaign-wide", "campaign cost"))
  # round 26 (point 4): c is a strategy, not a cost -- two knowledge models, three cost summaries
  and "We use two attacker-knowledge models and report three cost summaries" in flat(BODY)
  and "We distinguish three attack costs" not in flat(BODY)
  and "$\\sum_{t\\in\\mathcal D} r^{\\star}_t$" in flat(BODY) and "$J_{\\mathrm{seq}}$" in flat(BODY)
  # and the taxonomy is stated BEFORE the table that uses it (point 5)
  and BODY.index("We use two attacker-knowledge models") < BODY.index("\\label{tab:costcurve}")
  and "on the two windows and the sampled caps we evaluate" in flat(S),
  "the joint result must carry its arm (canonical, two windows) and its status (greedy, upper bound)")
q("R20: and the paper concedes the cap leaves a residual set, rather than claiming it closes",
  "leaves the attacker a residual set it can still silence" in flat(S)
  and _cap74(_u55, 300)["n_fits"] > 0,
  "13% of alerts remain suppressible at a 1% collateral rate; 'blocked' would overstate it")

q("R20: the grouping-key axis shows the same proportionality, from the artefact",
  _f74["0.55_src_poly"]["detections"] > _f74["0.55_src-dst_poly"]["detections"]
  and _f74["0.55_src_poly"]["median_r"] > _f74["0.55_src-dst_poly"]["median_r"]
  and f"from ${_f74['0.55_src-dst_poly']['detections']}$ to "
      f"${_f74['0.55_src_poly']['detections']}$" in flat(S),
  f"src-dst {_f74['0.55_src-dst_poly']['detections']} det / r*="
  f"{_f74['0.55_src-dst_poly']['median_r']}; src {_f74['0.55_src_poly']['detections']} det / r*="
  f"{_f74['0.55_src_poly']['median_r']}")

# =========================================================================================
# R21: findings from the blind pre-finalisation audit of t73/t74.  It confirmed the r* arithmetic
# and that the two spending arms differ in exactly one thing, and every number matched the JSON --
# but it found five places where the WORDING claimed more than the measurement establishes.  Each
# repair weakens a sentence without moving a number, so each is pinned by an absence as well as a
# presence: the overclaiming form must not come back.
# =========================================================================================
q("R21-1: the summed set-clearing cost is an upper bound, not a joint minimum",
  "an upper bound on the cost of jointly suppressing that set rather than a joint minimum" in flat(S)
  and "lowers the rejection count and so lowers the level" in flat(S)
  and "with $627{,}495$ needed to clear the whole set" not in flat(S),
  "alpha_t = alpha*gamma_t*(R+1), so removing an early alert lowers R, lowers alpha_t, raises tau "
  "and CHEAPENS every later alert: the sum over the unperturbed path over-counts")
q("R21-2: the replay's scope is stated -- measured e-values, arithmetic aggregation",
  "the aggregation and the controller level are\nthen arithmetic on the unperturbed trajectory".replace("\n", " ")
  in flat(S)
  and "the joint controller-state rerun of \\cref{sec:costcurve} then propagates zero-evidence" in flat(S)
  and "not a joint rerun of the altered controller trajectory" in flat(S),
  "the per-alert replay's e-values are measured and its controller is not re-run; round 25 added the "
  "joint rerun (t75) as a separate, zero-evidence measurement and the sentence points at it")
q("R21-3: the CP stress figures are labelled as Monte Carlo estimates under an iid assumption",
  "Monte Carlo estimates over $200$ draws" in flat(S)
  and "treat pool flows as\nindependent draws from a common firing rate".replace("\n", " ") in flat(S)
  and "which the pool's composition does not establish" in flat(S),
  "a zero-count CP bound needs iid Bernoulli sampling, and 200 draws estimate rather than prove")
q("R21-4: the LSPR23 pool is disclosed as service-level, not victim-local",
  "the pool is service-level" in flat(S)
  and "supplies no such traffic" in flat(S)
  and "precisely the gap the AIT transfer closes" in flat(S),
  "the threat model says traffic to the attacked host pair; the LSPR23 pool cannot be that, "
  "because every attacked pair there is 100% malicious")
q("R21-5: the cap's benign cost is labelled an arity-disruption rate",
  "an arity-disruption rate; we do not model what" in flat(S),
  "benign_arity > n counts episodes a cap would truncate, not the effect on their scores")
# ROUND 23: the body said BOTH horizon-aware windows had "no observed false discoveries" while
# Table I showed FDP 0.009 at 0.62 (one benign episode rejected alongside 107 true detections).
# Derive both counts from t73 and require the sentence to match each cell.
_fp55 = dig(_t73, "cells/0.55_keyhash_uniform/false_positives")
_fp62 = dig(_t73, "cells/0.62_keyhash_uniform/false_positives")
_fdp62 = _fp62 / (_fp62 + dig(_t73, "cells/0.62_keyhash_uniform/detections"))
q("R21-6: false-discovery counts are described as observed, per horizon-aware cell",
  _fp55 == 0 and _fp62 == 1
  and "zero observed false discoveries" in flat(S)
  and "true detections at the primary window with no observed false discovery" in flat(S)
  and f"alongside one false discovery, realised FDP ${_fdp62:.3f}$" in flat(S)
  and "no observed false discoveries" not in flat(S)
  and "at zero false discoveries," not in flat(S),
  f"artefact: FP {_fp55} at 0.55, {_fp62} at 0.62 (FDP {_fdp62:.3f}); a pair-wide 'no false "
  f"discoveries' is false at 0.62")
q("R21-6: Table I names its count column for what t73 counts -- TRUE detections",
  "& true det. & FDP &" in S and "true det.'' counts rejected malicious episodes" in flat(S),
  "t73 `detections` = fired & ismal; at 0.62 horizon-aware there are 108 rejections, 107 true")

# =========================================================================================
# R23: claim-scope and reading-order review (docs/41_r23_claim_scope.md).
# =========================================================================================
# --- the replay's recall values are the per-window artefact values, both regimes --------------
_rc = {k: dig(_t73, f"cells/{k}/recall") for k in
       ("0.55_keyhash_poly", "0.62_keyhash_poly", "0.55_keyhash_uniform", "0.62_keyhash_uniform")}
q("R23: the replay coverage sentence quotes per-window recall from t73, not a paired summary",
  f"at recall ${_rc['0.55_keyhash_poly']:.2f}$ and ${_rc['0.62_keyhash_poly']:.2f}$" in flat(S)
  and f"at recall ${_rc['0.55_keyhash_uniform']:.2f}$ and ${_rc['0.62_keyhash_uniform']:.2f}$"
      in flat(S)
  and "recall $0.38$ and $0.01$" not in flat(S) and "$226$ canonical alerts" not in flat(S),
  f"artefact recalls: {[(k, round(v, 3)) for k, v in _rc.items()]}; 0.38/0.01 paired the two "
  f"primary-window arms and dropped the secondary")
# --- the windows are pre-specified, not "guarantee-bearing" ---------------------------------
q("R23: the primary and secondary windows are never called guarantee-bearing",
  "guarantee-bearing window" not in _flatS_nc,
  "the nominal guarantee on those runs is conditional on Assumption 1 (Sec. VII-A)")
# --- the threat model grants influence over membership, not control -------------------------
q("R23: membership is attacker-influenceable, not attacker-controlled, in heading and figure",
  "\\section{Attacker-Influenceable Group Membership Enables Padding Evasion}" in S
  and "Attacker-Controlled" not in _flatS_nc and "attacker-controlled membership" not in _flatS_nc,
  "the adversary adds members to its own host-pair hypothesis; it does not control the group")
# --- a family is not suppressed; an attained alert is ----------------------------------------
# ROUND 31: reworded to "no symmetric e-merging rule can both attain an alert and survive enough
# zero-evidence additions".  The object is still the ATTAINED ALERT (a rule attains, then fails to
# survive); what stays banned is the reading in which a family is the thing suppressed.
q("R23: the abstract states Theorem 3 on the alert, not on the family",
  "attain an alert and survive enough zero-evidence additions" in flat(ABSTRACT)
  and "is suppressed by appending zero-evidence members" not in flat(ABSTRACT),
  "'every symmetric family ... is suppressed' misplaces the object of the theorem")
# --- every set total is an upper bound IN THE CAPTION THAT SHOWS IT -------------------------
_cap1 = _blk("Detection and padding costs under horizon-free and horizon-aware allocation", span=700)
# ROUND 26 (point 5): the reviewer asked for a three-sentence caption with the qualifications in the
# surrounding prose.  The caption now names the column "the independent sum"; the upper-bound
# statement sits in the V-D paragraph that reads the table, and the Terms table repeats it.
q("R23: Table I's caption names 'total' as the independent sum and the prose says it bounds the joint cost",
  "the per-alert sum over the true detections in the row" in _cap1
  and "an upper bound on the cost of jointly suppressing that set" in flat(BODY)
  and "Per-alert sum $\\sum_{t\\in\\mathcal D} r^{\\star}_t$ & the per-alert costs of the baseline true detections" in flat(S)
  and "is the volume to suppress every detection" not in _flatS_nc,
  "a reader should not discover several lines later that the column is not a joint minimum")
# R24-2.  t73 builds `det` as `fired & ismal`, so `total_pad` sums TRUE detections only.  At
# 0.62 horizon-aware there is one rejection outside that sum, so "the alert set" named a
# population the column does not have.  The caption must name the set it actually sums.
q("R24-2: Table I's 'total' names the true-detection set, not the rejection set",
  "over the true detections in the row" in _cap1
  and "one false discovery is not in that sum" in flat(BODY)
  and "jointly suppressing the alert set" not in _flatS_nc,
  f"t73 0.62 uniform: {dig(load('t73_uniform_padding'), 'cells/0.62_keyhash_uniform/detections')} "
  f"true detections + "
  f"{dig(load('t73_uniform_padding'), 'cells/0.62_keyhash_uniform/false_positives')} FP, "
  f"total_pad={dig(load('t73_uniform_padding'), 'cells/0.62_keyhash_uniform/total_pad')}")
# R24-3.  The per-host-pair volume cap is measured in t74, whose order is the CANONICAL keyhash;
# only the aggregation-cap (t25) and weighting (t36) sweeps are first-flow.  A blanket "the cap
# ... sweeps run under first-flow order" mislabelled a canonical result -- the exact defect the
# order registry exists to stop.
_capdef = _blk("One representative of each way out of", span=700)
q("R24-3: tab:defenses labels the volume cap canonical and the aggregation-cap sweep first-flow",
  "aggregation-cap and weighting sweeps run under first-flow order" in _capdef
  and "per-host-pair volume cap" in _capdef and "under the canonical order" in _capdef
  and "the cap and weighting sweeps run under first-flow order" not in _flatS_nc,
  f"t74 order={dig(load('t74_defended_replay'), 'config/order')} (canonical); "
  f"t25_H5 has no order arm, so it is first-flow")
# R24-4.  The AIT canonical arm issues more rejections than true detections; the body reported
# only the true detections, so the realised FDP of the external transfer was never disclosed.
_a67 = load("t67_ait_order")["arms"]
_ait = {k: (sum(r["elond_rej"] for r in v["rows"]), sum(r["elond_true"] for r in v["rows"]))
        for k, v in _a67.items()}
q("R24-4: the AIT transfer discloses its rejection count and realised FDP at the point of claim",
  f"issue ${_ait['keyhash'][0]}$" in _flatS
  and f"{(_ait['keyhash'][0] - _ait['keyhash'][1]) / _ait['keyhash'][0]:.3f}" in _flatS,
  f"canonical: {_ait['keyhash'][0]} rejections, {_ait['keyhash'][1]} true, "
  f"FDP {(_ait['keyhash'][0]-_ait['keyhash'][1])/_ait['keyhash'][0]:.3f}")
# --- Theorem 3's model versus admission control: no apparent contradiction -------------------
q("R23: allocation cannot eliminate padding WITHIN Theorem 3's model; admission control changes the model",
  "Within the unbounded-membership model of \\cref{thm:padding}" in _flatS
  and "Admission control changes that model" in _flatS
  and "The attack is never blocked" not in _flatS_nc
  and "any cap a defender would set" not in _flatS_nc
  and "cheap and invisible" not in _flatS_nc and "cheap and inconspicuous" not in _flatS_nc,
  "'never blocked' two sentences before a cap that blocks most horizon-aware pads read as a "
  "contradiction; and episode-size conspicuity is what was measured, not invisibility")
# --- Sec. V-E reads costs -> replay -> scope -> ordering; the 50-order details are appendix ---
_ve = _flatS.index("Those costs are arithmetic on stored evidence")
q("R23: Sec. V-E leads with the replay result and closes with one ordering sentence",
  _ve < _flatS.index("The horizon-aware regime replays the same way")
  < _flatS.index("Replay evaluates each alert separately")
  < _flatS.index("Ordering changes which alerts are issued, not the conditional result")
  < _flatS.index("\\label{sec:transferattack}"),   # round 32: anchor on the shared label, not the heading text
  "the empirical climax must not be qualified before it is stated")
q("R23: the fifty-order distribution is stated once, in the appendix, with the corrected comparison",
  S.index("$19$ of the fifty produce none at all") > S.index("\\appendices")
  and "exceeds all fifty audited metadata orders" in _flatS
  and "bracket that spread" not in _flatS_nc,
  "3 and 18 do not bracket a 0--10 range; canonical lies within it and first-flow exceeds it")
# --- no editorial or rebuttal residue ---------------------------------------------------------
q("R23: no meta-editorial sentence survives",
  all(x not in _flatS_nc for x in (
      "Four terms carry this argument", "make the result load-bearing", "The scope of the replay",
      "which are not a contribution", "cannot disagree", "TODO (authors)")),
  "each of these told the reviewer how to read the paper instead of stating the result")
q("R23: the LLM disclosure is written, not a placeholder",
  "TODO" not in S[S.index("\\section*{LLM Usage Considerations}"):S.index("\\section*{Ethical")]
  and "take responsibility for all content" in _flatS,
  "the CFP requires the section; a literal TODO is a desk-reject risk")

# =========================================================================================
# CHECK 4: no UNREGISTERED number in the abstract, and NO number in the conclusion
# =========================================================================================
REGISTERED = " ".join(r["tex"] for r in R)
NUM = re.compile(r"(?<![A-Za-z0-9_^{-])\d[\d,.]*")
ALLOW_ABS = {"1"}          # "$\ge1$", "$>1$" and the like: thresholds, not results
for m in NUM.finditer(flat(re.sub(r"\\cite\{[^}]*\}|\\label\{[^}]*\}|\\ref\{[^}]*\}", "", ABSTRACT))):
    tok = m.group(0).rstrip(".,;")
    if tok in ALLOW_ABS or tok in REGISTERED:
        continue
    q(f"abstract number {tok!r} is registered", False,
      "every number in the abstract must have a registry row resolving it to one source")
q("abstract numeric sweep", True)

concl_nums = [m.group(0) for m in NUM.finditer(
    re.sub(r"\\cite\{[^}]*\}|\\label\{[^}]*\}|\\ref\{[^}]*\}|12-page", "", CONCL))]
q("conclusion carries no numeric result", not concl_nums, f"found {concl_nums}")

# =========================================================================================
# CHECK 5: the reporting convention exists and names both the seed and the order
# =========================================================================================
_CONV_ANCHORS = ("Conventions for the reported numbers", "\\subsection{Reporting conventions}")
_conv_anchor = next((a for a in _CONV_ANCHORS if flat(a) in PAPER), None)
q("satml.tex declares a reporting convention",
  _conv_anchor is not None,
  "without it, 23--33 and the median 6 are seed-0 values the paper never attributes to a seed")
conv = block_of(PAPER, flat(_conv_anchor)) if _conv_anchor else ""
for token in ("seed 0", "canonical", "oracle", "upper bound"):
    q(f"convention names {token!r}", token in conv)
# ROUND 23: tab:main is now Table II (tab:defenses moved after it) and its caption was shortened.
q("tab:main's caption names the seed and the order",
  "at detector seed 0, under the canonical order" in flat(S))

# =========================================================================================
# CHECK 5b: the NON-ORACLE sizing result (t66).  This is the one place the paper answers the
# "oracle sizing is the hard part" objection, so every number in that paragraph is pinned to the
# re-analysis, including the two that make the argument work: the required multiplier and the
# padded arity against the benign 99th percentile.
# =========================================================================================
t66 = load("t66_nonoracle")
m55, m85 = t66["multiplier"]["canonical@0.55"], t66["multiplier"]["canonical@0.85"]
a55 = t66["absolute"]["canonical@0.55_0"]
a62 = t66["absolute"]["canonical@0.62_0"]
ff85 = t66["multiplier"]["first-flow@0.85"]
by = lambda v, c: next(r for r in v["by_c"] if r["c"] == c)

q("t66 re-derived the closed form as a read-back check",
  t66["summary"]["closed_form_selfcheck_episodes"] > 0,
  "without this the re-analysis could be reading the wrong artefact fields")
q("required multiplier median at the canonical primary window is 1.57",
  abs(m55["c_required_median"] - 1.57) < 0.005, f"artefact {m55['c_required_median']}")
q("paper quotes that median", "median $1.57$ at the canonical primary window" in PAPER)
c3 = by(m55, 3)
q("c=3 suppresses all three canonical primary alerts",
  c3["defeated"] == c3["of"] == 3, f"artefact {c3['defeated']}/{c3['of']}")
q("paper quotes the per-window figure and labels it oracle-informed",
  abs(c3["median_added"] - 80) < 0.5 and abs(c3["median_overprovision"] - 3.5) < 0.05
  and "median of 80 added flows, $3.5\\times$" in PAPER
  and "reads the realised costs and is reported as an" in PAPER,
  f"artefact added {c3['median_added']}, overprovision {c3['median_overprovision']:.2f}")
# THE headline claim: one FIXED multiplier defeating every canonical alert without reading S or
# alpha_t.  R12-5: the GRID [2,3,5,10,100] was pre-committed, but c=10 is the smallest grid element
# that defeats all -- a choice made after seeing the realised overshoots.  So the claim the paper may
# make is "a fixed multiplier needs no controller state", NOT "c=10 was chosen in advance"; the
# wording check below enforces that the sentence leads with the knowledge requirement.
p10, s10 = by(m55, 10), by(m85, 10)
q("a single fixed c=10 defeats every canonical alert at both windows",
  p10["defeated"] == p10["of"] and s10["defeated"] == s10["of"],
  f"artefact primary {p10['defeated']}/{p10['of']}, stress {s10['defeated']}/{s10['of']}")
q("the paper quotes that multiplier's cost at both windows",
  abs(p10["median_overprovision"] - 15.7) < 0.1 and abs(s10["median_overprovision"] - 5.1) < 0.05
  and "a median $15.7\\times$ the oracle at the primary window and $5.1\\times$ at the stress window"
      in PAPER,
  f"artefact primary {p10['median_overprovision']:.2f}x, stress {s10['median_overprovision']:.2f}x")
# R13-2: the paper may not assert PRE-REGISTRATION of the multiplier, because the grid appears
# nowhere a reader can check.  It states the evaluated set instead, which is checkable and enough.
q("R12-5/R13-2: c=10 is presented as the smallest EVALUATED multiplier, not a pre-registered one",
  "chosen \\emph{in advance}" not in flat(BODY)
  and "pre-declared" not in flat(BODY) and "pre-committed grid" not in flat(BODY)
  and "A fixed multiplier requires no access to" in flat(BODY)
  and "the smallest of the multipliers we evaluate, $c\\in\\{2,3,5,10,100\\}$" in flat(BODY),
  "the grid is not documented anywhere a reader can check, so the claim must be about what was "
  "evaluated, not about what was registered in advance")
q("R12-5: 'knowledge-free' is not used for a strategy that still needs m",
  "knowledge-free" not in PAPER
  and ("state-free sizing" in PAPER or "state-free over-provisioning" in PAPER),
  "the multiplier attacker knows its own arity m and its host pair/bucket")
q("flat pad of 33 suppresses every canonical primary alert",
  a55["N_for_all"] == 33 and "33 flows suffice at the primary window" in PAPER,
  f"artefact N_for_all={a55['N_for_all']}")
q("flat pad of 17 suppresses 90% at the secondary window",
  a62["N_for_90pct"] == 17 and "17 for $90\\%$ of the secondary window's eleven" in PAPER,
  f"artefact N_for_90={a62['N_for_90pct']} over {a62['n_alerts']} alerts")
# The conspicuity claim must rest on a DEPLOYMENT population.  t25's n0 is a calibration-slice
# quantile, unfiltered by label -- an earlier version of this paragraph called it "the benign 99th
# percentile", which was the wrong population; the blind audit caught it.  Gate the corrected form.
_br = c3.get("arity_bracket", {})
_lo, _hi = _br.get("upper_deployment_exceedance"), _br.get("lower_deployment_exceedance")
q("padded primary arity is 120 and is bracketed in the DEPLOYMENT arity distribution",
  c3["median_padded_arity"] == 120 and _lo is not None and _hi is not None
  and abs(100 * _lo - 0.9) < 0.1 and abs(100 * _hi - 9.9) < 0.1,
  f"artefact arity {c3['median_padded_arity']}, exceedance {_lo}--{_hi}")
q("paper states the deployment exceedance, not a benign-calibration percentile",
  "arity $120$, is exceeded by $0.9$--$9.9\\%$ of deployment episodes" in PAPER,
  "the calibration-slice quantile is not a benign deployment population")
q("the paper no longer calls it a benign calibration percentile",
  "benign calibration block" not in PAPER)
q("the purity premise cites its artefact count",
  "all 674 detected episodes sit on host pairs carrying no benign traffic" in flat(BODY),
  "t46_hostpair records 674/674; the paper asserted the premise without it")
q("the first-flow stress arm is reported as the exception",
  abs(ff85["c_required_max"] - 4302) < 1
  and "overshoot reaches $4{,}302$" in PAPER,
  f"artefact max multiplier {ff85['c_required_max']:.1f}")
# "100\% malicious" also appears in Sec. V-D, so a body-wide test passes on the WRONG sentence --
# the same scoping hole the paragraph-vs-sentence fix closed earlier.  Scope it to the claim.
_no = "needing no estimate of $S_t$"   # round 27: the group sum carries its step subscript body-wide
q("the non-oracle claim names its knowledge assumption",
  _no in flat(BODY)
  and "carrying no benign traffic" in para_of(flat(BODY), _no),
  "the multiplier strategy needs m; the sentence making the claim must say why m is free on LSPR23")

# =========================================================================================
# CHECK 6: the reporting convention promises the first-flow label is AT THE POINT OF CLAIM.
# A compression pass strips qualifying clauses first, so hold the promise mechanically: any body
# paragraph citing a first-flow-ONLY appendix table must contain the words "first-flow".
# =========================================================================================
MARK = "All counts here use the \\textbf{first-flow} within-bucket order"
TABLES = ROOT / "paper" / "tables"
ffonly = []
for f in sorted(TABLES.glob("*.tex")):
    t = f.read_text()
    m = re.search(r"\\label\{([^}]+)\}", t)
    if m and MARK in t:
        ffonly.append(m.group(1))
q("first-flow-only tables were found at all", len(ffonly) >= 10, f"found {len(ffonly)}")
# apptab:grouping is cited only for its margin / hypothesis-count columns, which are
# order-invariant by construction (the margin is a function of |C|, k and T alone).
ORDER_INVARIANT_USE = {"apptab:grouping"}
for para in re.split(r"\n\s*\n", BODY):
    flat_p = flat(para)
    for lab in ffonly:
        if lab in flat_p and lab not in ORDER_INVARIANT_USE:
            q(f"body paragraph citing {lab} says 'first-flow'", "first-flow" in flat_p,
              "the conventions paragraph promises this label at the point of claim")

print(f"\n{len(OK)} consistent, {len(BAD)} INCONSISTENT\n")
for b in BAD:
    print("  BAD   ", b)
if not BAD:
    for o in OK:
        print("  ok    ", o)
sys.exit(1 if BAD else 0)
