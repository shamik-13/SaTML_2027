"""Does the artifact actually do what the Open Science section promises?

WHY THIS EXISTS.  The audit ran the reproduction notebook for the first time and found that it
rendered ZERO figures, while the paper said it "renders every table and figure from shipped results
in seconds".  Every number behind every figure was reproduced; the figures themselves were drawn by
separate scripts under paper/, which the notebook never touched.  The claim was checkable, false,
and had never been checked -- the one class of promise a reviewer tests first.

The repair was to move the drawing code into the reproduction package (`src/lib/figures.py`) and
make `paper/make_figures_satml.py` a thin wrapper over it, so there is ONE implementation and the
notebook and the LaTeX build cannot disagree about what a figure shows.  This gate pins that:

  1. every figure the paper includes is produced by lib/figures.py
  2. the notebook actually renders them (so "renders every figure" is true, not aspirational)
  3. paper/make_figures_satml.py stays a WRAPPER -- no second copy of the drawing code
  4. requirements.txt pins every third-party library src/lib imports
  5. the notebook's default MODE is the one the paper says needs no data

    python proto/t72_artifact_promises.py
"""
import ast
import json
import pathlib
import re
import sys

if not __debug__:
    raise SystemExit(f"{__file__} must not run under `python -O`: assertions are its checks")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, LIB = ROOT / "src", ROOT / "src" / "lib"
TEX = ROOT / "paper" / "satml.tex"
NB = SRC / "paper.ipynb"
REQ = SRC / "requirements.txt"
OK, BAD = [], []


def q(label, cond, detail=""):
    (OK if cond else BAD).append(f"{label}   {detail}" if detail else label)


S = TEX.read_text()
figsrc = (LIB / "figures.py").read_text()
nb = json.loads(NB.read_text())
nbcode = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")

# --- 1: every figure the paper includes is produced inside the reproduction package -----------
included = sorted({m.group(1) for m in
                   re.finditer(r"\\includegraphics\[[^\]]*\]\{([^}]+?)(?:\.pdf)?\}", S)})
produced = {n.name for n in ast.parse(figsrc).body if isinstance(n, ast.FunctionDef)}
missing = [f for f in included if f not in produced]
q(f"every figure the paper includes is drawn by lib/figures.py ({len(included)} figures)",
  not missing, f"not produced there: {missing}")

# the declared SUBMISSION list must match what the paper actually includes -- a figure drawn but
# not listed would never be rendered by the notebook loop, which is check 2's whole basis
declared = re.findall(r'\("([A-Za-z0-9_]+)",\s*"', figsrc[figsrc.index("SUBMISSION = ["):])
q("lib/figures.SUBMISSION lists exactly the figures the paper includes",
  sorted(declared) == included,
  f"declared {sorted(declared)} vs included {included}")

# --- 2: the notebook renders them -----------------------------------------------------------
# Match the LOOP, not the bare name: "figures.SUBMISSION" appears twice in the cell (the iteration
# and the closing count), so a substring test passes on a notebook whose loop has been gutted --
# verified by injection.  The loop plus a display call is what makes the claim true.
_renders = re.search(r"for\s+\w+\s*,\s*\w+\s+in\s+figures\.SUBMISSION\s*:", nbcode)
_displays = re.search(r"display\(\s*getattr\(figures", nbcode)
q("the notebook imports the figure module and renders every declared figure",
  "import figures" in nbcode and _renders and _displays,
  "the Open Science section claims the notebook renders every figure; it must iterate "
  "figures.SUBMISSION and display each one")
q("the notebook ships those renders in its outputs",
  sum(1 for c in nb["cells"] for o in c.get("outputs", [])
      if "image/png" in (o.get("data") or {})) >= len(included),
  "the README says the notebook can be read straight through without executing anything")

# --- 3: exactly one implementation of the drawing code ---------------------------------------
wrapper = (ROOT / "paper" / "make_figures_satml.py").read_text()
q("paper/make_figures_satml.py is a wrapper, not a second copy of the drawing code",
  "plt." not in wrapper and "subplots(" not in wrapper and "import figures" in wrapper,
  "two copies of a figure is the drift this move was made to prevent")

# --- 4: the pinned environment covers what src/lib actually imports ---------------------------
third = set()
for p in LIB.glob("*.py"):
    for n in ast.walk(ast.parse(p.read_text())):
        mods = ([a.name for a in n.names] if isinstance(n, ast.Import)
                else [n.module] if isinstance(n, ast.ImportFrom) and n.module else [])
        for mod in mods:
            root = mod.split(".")[0]
            if root not in sys.stdlib_module_names and not (LIB / f"{root}.py").exists():
                third.add(root)
DIST = {"sklearn": "scikit-learn"}          # import name -> distribution name
req = REQ.read_text() if REQ.exists() else ""
pinned = {m.group(1).lower() for m in re.finditer(r"^([A-Za-z0-9_.\-]+)==", req, re.M)}
unpinned = sorted(d for d in (DIST.get(m, m) for m in third) if d.lower() not in pinned)
q(f"requirements.txt pins every third-party library src/lib imports ({len(third)} imported)",
  REQ.exists() and not unpinned, f"unpinned: {unpinned}")
q("the pins record what was verified at them, and what was not",
  "WHAT WAS VERIFIED" in req and "WHAT WAS NOT VERIFIED" in req,
  "an unqualified pin implies the full path was re-run at these versions; it was not")

# --- 5: the notebook's default mode is the one the paper says needs no data -------------------
m = re.search(r'MODE\s*=\s*["\']([a-z]+)["\']', nbcode)
q("the notebook's default MODE is the no-data path the paper advertises",
  m and m.group(1) == "paper", f"default MODE = {m.group(1) if m else '?'}")
# ROUND 23: Fig. 1's padding label said "attacker-controlled membership"; the threat model grants
# influence over the attacker's own hypothesis, not control of the group.  The label is drawn by the
# reproduction package, so pin it there.
q("Fig. 1 labels membership as attacker-influenceable, matching the threat model",
  "attacker-influenceable membership" in figsrc and "attacker-controlled membership" not in figsrc,
  "src/lib/figures.py draws the label the paper shows")
q("the paper does not claim the notebook renders figures it cannot",
  "renders every\ntable and figure" not in S or "figure-drawing code is part of the library" in S,
  "the pre-audit wording promised figures the notebook never drew")

print("=" * 92)
for line in OK:
    print(f"  ok     {line}")
for line in BAD:
    print(f"  BAD    {line}")
print("=" * 92)
print(f"  {len(OK)} consistent, {len(BAD)} INCONSISTENT")
if BAD:
    print("  The artifact does not do what the Open Science section promises.")
    sys.exit(1)
print("  the artifact delivers what the paper says it delivers")
print("=" * 92)
