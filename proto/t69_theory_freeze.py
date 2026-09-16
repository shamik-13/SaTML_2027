"""Theory freeze gate: the audited mathematics may not change without an explicit re-freeze.

WHY THIS EXISTS.  The theory has been declared "frozen" twice and drifted twice, both times in
Theorem 4:

  * review 11 -- an independent audit found it FALSE without the cap hypothesis
    lambda >= k/(|C|+1), which was added.
  * review 13 -- a second independent audit found its post-rejection clause pointing the WRONG WAY:
    the displayed expression was called an upper bound on B* when it is a lower bound (displayed 313
    where the true budget is 373 at R=1 with a lag of 100).

A freeze recorded in prose is not a freeze.  This gate records the exact audited text of every
statement and proof and FAILS if any of them changes, so a later edit to the mathematics has to be a
deliberate act rather than a side effect of a wording pass or a page refit.

WHAT IS FROZEN.  The 13 statements the round-13 audit covered (Assumption 1, Lemma 1, Theorems 1-6,
Corollaries 1-2, Propositions 1-2, and the padding-robustness Definition) plus every proof in
`paper/appendix_proofs.tex`.  Text is compared with whitespace collapsed, so re-wrapping a line or
reflowing a paragraph is invisible to the gate; changing a symbol, a quantifier, an inequality
direction or a hypothesis is not.

RE-FREEZING, when a change is intended and has been audited:

    python proto/t69_theory_freeze.py --refreeze

That rewrites `proto/theory_freeze.json` from the current sources and prints what moved.  Do this only
after the changed statement has been through a blind audit -- the whole point is that the baseline
tracks what was CHECKED, not what is merely current.  `provenance` in the manifest records which round
cleared each statement.

HIGHEST-RISK ITEM.  `thm:addis` (Theorem 4) has now failed two independent audits.  Treat any diff
touching it as suspect until re-audited, whatever the rest of the paper says.

WHAT ROUND 15 CHANGED THE ODDS ON.  Three of the four objects audited in round 15 came back sound
from both auditors; the defects were all of ONE shape -- a stated hypothesis weaker than the proof
actually needs (`thm:family2` missing `ceil<infinity`, the e-LORD reparameterisation missing
`omega_j in [0,1]`, Route B advertised wider than it proves).  That is now the failure mode to look
for first in anything added here: not arithmetic, but a hypothesis that the surrounding text supplies
implicitly and the statement does not.
"""
import hashlib
import json
import pathlib
import re
import sys

if not __debug__:
    raise SystemExit(f"{__file__} must not run under `python -O`: assertions are its checks")

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEX = ROOT / "paper" / "satml.tex"
PROOFS = ROOT / "paper" / "appendix_proofs.tex"
MANIFEST = pathlib.Path(__file__).resolve().parent / "theory_freeze.json"

# The statements the round-13 blind audit covered, in the order it reported them.
FROZEN = [
    ("assumption",  "assump:groupval",     "Assumption 1 (group-local metadata-conditional validity)"),
    ("lemma",       "lem:groupval",        "Lemma 1 (group-level marginal e-validity)"),
    ("theorem",     "thm:family1",         "Theorem 1 (finite discovery horizon, multiplicative)"),
    ("theorem",     "thm:family2",         "Theorem 2 (finite discovery horizon, lag-sum)"),
    ("corollary",   "cor:budget",          "Corollary 1 (horizon-uniform feasibility)"),
    ("definition",  "def:padding",         "Definition (theta-padding-robustness, attainment)"),
    ("theorem",     "thm:padding",         "Theorem 3 (symmetric padding impossibility)"),
    ("corollary",   "cor:dilution",        "Corollary 2 (horizon-uniform feasibility ratio as a dilution threshold)  <-- rounds 26/28"),
    ("theorem",     "thm:addis",           "Theorem 4 (ADDIS state budget)  <-- twice-repaired"),
    ("proposition", "prop:donation",       "Proposition 1 (donation bounded before first rejection)"),
    ("proposition", "prop:closure",        "Proposition 2 (closure bounded by zero-evidence subset)"),
    ("corollary",   "cor:closureabsorb",   "Corollary 3 (when the closure is absorbing)"),
    ("theorem",     "thm:reach",           "Theorem 5 (reach)"),
    ("theorem",     "thm:frontload",       "Theorem 6 (front-load cost)"),
]


def flat(s):
    """Collapse whitespace: a re-wrap must not trip the gate, a token change must."""
    return re.sub(r"\s+", " ", s).strip()


def digest(s):
    return hashlib.sha256(flat(s).encode()).hexdigest()[:16]


def statement(src, env, label):
    m = re.search(r"\\begin\{" + env + r"\}(\[[^\]]*\])?\s*\\label\{" + re.escape(label) + r"\}"
                  r"(.*?)\\end\{" + env + r"\}", src, re.S)
    assert m, f"statement {label} ({env}) not found in {TEX.name}"
    return m.group(0)


def proofs(src):
    """Each \\begin{proof}...\\end{proof}, keyed by its optional argument (or its index)."""
    out = {}
    for i, m in enumerate(re.finditer(r"\\begin\{proof\}(\[[^\]]*\])?(.*?)\\end\{proof\}", src, re.S)):
        tag = flat(m.group(1) or "")[:60] or f"proof#{i}"
        key = tag if tag not in out else f"{tag}#{i}"
        out[key] = m.group(0)
    return out


def current():
    tex, prf = TEX.read_text(), PROOFS.read_text()
    items = {}
    for env, label, title in FROZEN:
        items[label] = {"kind": env, "title": title, "sha": digest(statement(tex, env, label)),
                        "chars": len(flat(statement(tex, env, label)))}
    for key, body in proofs(prf).items():
        items[f"proof::{key}"] = {"kind": "proof", "title": key, "sha": digest(body),
                                  "chars": len(flat(body))}
    return items


def refreeze():
    items = current()
    prev = json.loads(MANIFEST.read_text())["items"] if MANIFEST.exists() else {}
    MANIFEST.write_text(json.dumps({
        "note": "Audited text of the frozen mathematics. Regenerate ONLY after a blind audit "
                "clears the change: `python proto/t69_theory_freeze.py --refreeze`.",
        "provenance": {
            "review 28": "cor:dilution RETITLED 'Horizon-uniform feasibility ratio as a dilution threshold' "
                         "and its rho clause now reads 'rho = rho_{e-LOND} = M alpha / T, the horizon-uniform "
                         "ratio (6) for e-LOND' (reviewer: the generic rho_p must not be read as any controller's "
                         "ratio).  Hypotheses, conclusion and proof unchanged; no re-audit of the mathematics.",
            "review 26": "cor:dilution ADDED (feasibility ratio as a dilution threshold: under "
                         "horizon-uniform e-LOND, zero-evidence padding and no non-attacker hypothesis at "
                         "the cold-start threshold, every integer c > rho silences the stream and no integer "
                         "c <= rho does once an attacker episode attains the ceiling; c_int = floor(rho)+1). "
                         "First two blind codex audits: CRITICAL, the statement multiplied by a REAL c, so "
                         "(c-1)m_t flows were not integers and the sharpness claim lived in a continuous "
                         "relaxation; MAJOR, the level form and R_0 = 0 were not stated; MAJOR, the "
                         "uniform-over-streams quantifier needed the per-stream c_crit remark.  Restated for "
                         "integer c >= 1 with the hypotheses explicit and the c_crit remark in the proof; two "
                         "further blind audits: sound (minor: 'it is not rejection-free', and max_u needs at "
                         "least one attacker episode -- both applied).  The 13-statement list becomes 14; "
                         "cor:closureabsorb renumbers to Corollary 3.",
            "review 15": "third independent audit (blind Opus + blind codex over a self-contained "
                         "extract, then a SECOND blind agent to verify the repairs). Three frozen "
                         "objects changed: thm:family2 gained the ceil<infinity hypothesis its 1/M "
                         "threshold needs (it was FALSE as written for unbounded evidence); "
                         "thm:family1's proof named one constant c and c_g; cor:budget's max-min "
                         "one-liner ('any other allocation places some gamma_t<1/T') was replaced by "
                         "min<=average, and the sufficiency direction was signposted. Non-frozen "
                         "prose also changed: e-LORD coverage now requires omega_j in [0,1] AND "
                         "determinism (BOTH auditors found this independently), Route B is stated as "
                         "the lemma it is rather than a second proof of the class result, and the "
                         "asymmetry between the two families is stated (family I absorbs on any "
                         "history; family II only on a rejection-free gap).",
            "review 11": "independent two-agent proof audit; Thm 4 was FALSE without the cap "
                         "hypothesis lambda >= k/(|C|+1), which was added",
            "review 13": "second independent audit (blind Opus + blind codex) over a self-contained "
                         "36KB extract; Thm 4's post-rejection clause was a LOWER bound stated as an "
                         "upper bound; Prop 1 was instantiated at d=1 where d=0 is required; Prop 2 "
                         "needed E_S=0 on all-zero input; Thm 3's Vovk-Wang step was made "
                         "self-contained at the zero boundary",
            "cleared sound by both round-13 auditors": ["assump:groupval", "lem:groupval",
                                                        "thm:family1", "thm:family2",
                                                        "cor:closureabsorb"],
            "cleared sound by both round-15 auditors": ["thm:family1", "cor:budget", "thm:padding"],
            "round-15 repairs verified by a third blind agent": ["thm:family2",
                                                                 "proof::[\\cref{thm:family1}]",
                                                                 "proof::[\\cref{cor:budget} and "
                                                                 "max-min optimality of "
                                                                 "$\\gamma_t=1/T$]"],
        },
        "items": items,
    }, indent=1) + "\n")
    added = sorted(set(items) - set(prev))
    gone = sorted(set(prev) - set(items))
    moved = sorted(k for k in set(items) & set(prev) if items[k]["sha"] != prev[k]["sha"])
    print(f"  re-froze {len(items)} objects")
    for k in moved:
        print(f"    CHANGED  {k}  {prev[k]['sha']} -> {items[k]['sha']}")
    for k in added:
        print(f"    NEW      {k}")
    for k in gone:
        print(f"    REMOVED  {k}")
    if not (moved or added or gone):
        print("    (identical to the previous baseline)")


def check():
    if not MANIFEST.exists():
        raise SystemExit(f"no baseline at {MANIFEST}; create one with --refreeze")
    base = json.loads(MANIFEST.read_text())["items"]
    now = current()
    drift, missing, extra = [], [], []
    for key, rec in base.items():
        if key not in now:
            missing.append(f"{key} ({rec['title']}) is GONE from the sources")
        elif now[key]["sha"] != rec["sha"]:
            drift.append(f"{key} ({rec['title']}): {rec['sha']} -> {now[key]['sha']} "
                         f"[{rec['chars']} -> {now[key]['chars']} chars]")
    for key in now:
        if key not in base:
            extra.append(f"{key} ({now[key]['title']}) is NEW and unaudited")
    bad = drift + missing + extra
    print("=" * 92)
    print(f"  {len(base)} frozen objects checked "
          f"({len(FROZEN)} statements + {len(base) - len(FROZEN)} proofs)")
    for line in bad:
        print(f"  DRIFT  {line}")
    print("=" * 92)
    if bad:
        print(f"  {len(bad)} FROZEN OBJECT(S) CHANGED.")
        print("  The audited mathematics moved. If the change is deliberate AND has been through a")
        print("  blind audit, re-baseline with:  python proto/t69_theory_freeze.py --refreeze")
        print("  If it was not deliberate, revert it -- this is the drift the freeze exists to catch.")
        sys.exit(1)
    print(f"  0 drift: every audited statement and proof is byte-identical to its cleared text")
    print("=" * 92)


if __name__ == "__main__":
    if "--refreeze" in sys.argv:
        refreeze()
    else:
        check()
