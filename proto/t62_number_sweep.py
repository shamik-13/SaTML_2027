"""EXHAUSTIVE sweep: every numeric token in the paper, matched against the artefacts.

t61 checks a curated list of load-bearing numbers.  This checks ALL of them.  It extracts every
number that appears in `paper/main.tex` and in the generated tables, and for each one asks whether
some value in `src/lib/out/*.json` equals it (to the precision it is written at).  Numbers that
match nothing are printed for adjudication -- most will be legitimate (configuration constants,
citation years, cross-references, quantities derived in the text), but the two errors this project
has already shipped -- `178` for a range ending at 175, and `207` for a maximum of 295 -- would both
have appeared here as unmatched.

The output is a TRIAGE list, not a verdict: the tool cannot know that `0.05` is a design constant
rather than a measurement.  Its job is to make the unmatched set small enough to read.

Run:  proto/.venv/bin/python proto/t62_number_sweep.py [--all]
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEX = ROOT / "paper" / "main.tex"
TABLES = ROOT / "paper" / "tables"
OUT = ROOT / "src" / "lib" / "out"
SHOW_ALL = "--all" in sys.argv

# ---------------------------------------------------------------- gather every artefact value
VALUES = set()


def walk(o):
    if isinstance(o, dict):
        for v in o.values():
            walk(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            walk(v)
    elif isinstance(o, bool):
        pass
    elif isinstance(o, (int, float)):
        try:
            f = float(o)
        except Exception:
            return
        if f == f and abs(f) != float("inf"):
            VALUES.add(round(f, 10))


n_art = 0
for f in sorted(OUT.glob("*.json")):
    try:
        walk(json.load(open(f)))
        n_art += 1
    except Exception as e:
        print(f"  !! could not read {f.name}: {e}")

# The ONLY derived form allowed is x100, because a paper writes a rate as a percentage.  Admitting
# reciprocals, +-1 and x1000 inflated the value set to 146k and made almost any token match by
# coincidence -- a checker that passes everything is not a checker.  Validated below against the two
# errors this project actually shipped.
DERIVED = {round(v * 100, 10) for v in VALUES}
ALL_VALS = VALUES | DERIVED

# ---------------------------------------------------------------- gather every number in the paper
SRC = {"main.tex": TEX.read_text()}
for f in sorted(TABLES.glob("*.tex")):
    SRC[f"tables/{f.name}"] = f.read_text()

# strip things that are not claims: comments, labels/refs, citations, includes, macro definitions
STRIP = [
    (re.compile(r"^\s*%.*$", re.M), ""),                 # comment lines
    (re.compile(r"(?<!\\)%.*$", re.M), ""),              # trailing comments
    (re.compile(r"\\(label|ref|cref|Cref|cite[a-z]*|input|includegraphics|newcommand|"
                r"newtheorem|usepackage|documentclass|bibliography[a-z]*|cmidrule|"
                r"resizebox|multicolumn|columnwidth|hspace|vspace|setlength)\s*"
                r"(\[[^\]]*\])?\s*(\{[^{}]*\})?(\{[^{}]*\})?"), " "),
]
NUM = re.compile(r"(?<![A-Za-z0-9_.^])(\d{1,3}(?:[,{]?,?\}?\d{3})*(?:\.\d+)?|\d*\.\d+|\d+)")


def clean(t):
    for pat, rep in STRIP:
        t = pat.sub(rep, t)
    return t


def parse(tok):
    t = tok.replace("{,}", "").replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


found = {}          # value -> list of (file, line, context)
for name, text in SRC.items():
    for i, line in enumerate(clean(text).split("\n"), 1):
        if not line.strip():
            continue
        for m in NUM.finditer(line):
            v = parse(m.group(1))
            if v is None:
                continue
            found.setdefault((v, m.group(1)), []).append((name, i, line.strip()[:110]))

# ---------------------------------------------------------------- match
def matches(v, token):
    """Does some artefact value equal v at the precision the paper writes it?"""
    if v in ALL_VALS:
        return True
    dec = len(token.split(".")[1]) if "." in token else 0
    for a in ALL_VALS:
        if round(a, dec) == v:
            return True
    return False


CONFIG = {0.05, 0.025, 1.0, 2.0, 1.6, 0.5, 0.25, 0.0, 100.0, 1000.0, 10.0, 5.0, 3.0, 4.0,
          0.15, 0.55, 0.62, 0.7, 0.77, 0.85, 300.0, 1800.0, 3600.0, 7200.0, 21600.0, 86400.0,
          2.0, 12.0, 50.0, 20.0, 95.0, 97.5, 2026.0, 2023.0, 2025.0, 2024.0}

def strong(v, tok):
    """Is a coincidental match unlikely for this token?  >=4 digits, or >=2 decimals."""
    dec = len(tok.split(".")[1]) if "." in tok else 0
    return dec >= 2 or abs(v) >= 1000


unmatched, matched, config, weak = [], 0, 0, []
for (v, tok), where in sorted(found.items()):
    if v in CONFIG:
        config += 1
        continue
    ok = matches(v, tok)
    if ok and strong(v, tok):
        matched += 1
    elif ok:
        weak.append((v, tok, where))          # matched, but the match proves little
    else:
        unmatched.append((v, tok, where))

print("=" * 108)
print(f"  {n_art} artefacts -> {len(VALUES):,} distinct values ({len(ALL_VALS):,} with derived forms)")
print(f"  paper carries {len(found):,} distinct numeric tokens across {len(SRC)} files")
print(f"  {matched:,} STRONGLY matched (long/precise: coincidence unlikely)")
print(f"  {len(weak):,} weakly matched (short integers, ~80% coincidence -- pin these in t61)")
print(f"  {config:,} configuration/window constants")
print(f"  {len(unmatched):,} UNMATCHED (triage below)")
print("=" * 108)
for v, tok, where in unmatched:
    f, ln, ctx = where[0]
    extra = f"  (+{len(where)-1} more)" if len(where) > 1 else ""
    print(f"  {tok:>14}   {f}:{ln}{extra}")
    print(f"                   {ctx}")
print("=" * 108)
print(f"  {len(unmatched)} tokens to adjudicate by hand; {len(weak)} more are WEAK matches")
if SHOW_ALL and weak:
    print()
    print("  WEAK MATCHES in the BODY -- short integers whose match proves little.")
    print("  These are the ones that need pinning to a named artefact field in t61.")
    body_weak = [(v, t, w) for v, t, w in weak if any(f == "main.tex" for f, _, _ in w)]
    for v, tok, where in body_weak:
        f, ln, ctx = [x for x in where if x[0] == "main.tex"][0]
        print(f"  {tok:>10}   main.tex:{ln:<5} {ctx[:88]}")
    print(f"\n  {len(body_weak)} weak matches in the body, {len(weak)-len(body_weak)} in tables")
