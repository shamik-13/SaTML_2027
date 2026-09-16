"""Completeness gate: everything the paper needs must live in src/, and src/ must not need proto/.

WHY THIS EXISTS.  The repository has two trees that look interchangeable and are not:

  * `src/lib/` is the reproduction package -- what `src/paper.ipynb` imports, what writes
    `src/lib/out/*.json`, and what every table and figure in the paper is built from.
  * `proto/` is the working tree: the gates (t45, t61, t65, t68, t69, this one), the `*_selftest.py`
    files, early exploratory scripts, and STALE DUPLICATES of much of `src/lib`.

`src/tools/` contains a proto -> src/lib pipeline (`strip_comments.py`, then `make_importable.py`),
which makes proto look like the source of truth.  It is not, any more:

  * 46 of the 48 same-named files differ, and for several the divergence is real code, not stripped
    comments -- `src/lib/t48_W3_dilution.py` carries the `episodes_keyhash` (canonical-order) arm that
    `proto/t48_W3_dilution.py` does not contain at all, and the paper's headline order convention
    depends on it.
  * Five paper-critical modules exist ONLY in src/lib and have no proto ancestor: `t52_B1_synthetic`,
    `t53_ordering`, `t54_ait_suppression`, `t66_nonoracle_padding`, `t67_ait_order` -- between them the
    AIT transfer (78/79), the ordering arms, the non-oracle padding analysis and the synthetic ADDIS run.
  * `strip_comments.py` currently fails its own AST self-check on these files, so the pipeline cannot
    be run even if someone wanted to.

So regenerating `src/lib` from `proto` would silently revert the paper's implementation.  This gate
pins the invariants that make that impossible to do by accident:

  1. every artefact the paper's build/validation chain reads has a producer in `src/lib`
  2. nothing in `src/lib` imports from, or reads a path inside, `proto/`
  3. every intra-package import in `src/lib` resolves inside `src/lib`

Divergent proto duplicates are reported as INFO, not failure: proto is allowed to hold history.

    python proto/t70_src_completeness.py
"""
import ast
import io
import pathlib
import re
import sys
import tokenize

if not __debug__:
    raise SystemExit(f"{__file__} must not run under `python -O`: assertions are its checks")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "lib"
OUT = SRC / "out"
PROTO = ROOT / "proto"

# Everything that builds the paper or validates it against the artefacts.
CONSUMERS = [
    ROOT / "paper" / "make_appendix_tables.py",
    SRC / "tables.py",                         # the table generator itself (paper/make_appendix_tables.py wraps it)
    ROOT / "src" / "make_tables.py",
    # The figure-drawing code moved into the reproduction package so the notebook and the LaTeX
    # build render the same figures from one implementation; paper/make_figures*.py are now thin
    # wrappers that name no artefacts, so the artefact coverage is read from lib/figures.py.
    SRC / "figures.py",
    ROOT / "paper" / "make_figures_satml.py",
    ROOT / "paper" / "make_figures.py",
    ROOT / "src" / "make_figures.py",          # the wrapper the Open Science section promises to ship
    ROOT / "src" / "paper.ipynb",
    ROOT / "src" / "runner.py",
    PROTO / "t45_record_consistency.py",
    PROTO / "t61_paper_consistency.py",
    PROTO / "t65_satml_claims.py",
]
THIRD_PARTY = {"numpy", "scipy", "sklearn", "pandas", "matplotlib"}
STDLIB_OK = set(sys.stdlib_module_names) | THIRD_PARTY

OK, BAD, INFO = [], [], []


def q(label, cond, detail=""):
    (OK if cond else BAD).append(f"{label}   {detail}" if detail else label)


src_files = {p.name: p.read_text() for p in SRC.glob("*.py")}
artefacts = sorted(p.stem for p in OUT.glob("*.json"))

# --- 1: every artefact the paper reads is produced inside src/lib -----------------------------
used = set()
for c in CONSUMERS:
    if not c.exists():
        INFO.append(f"consumer missing (skipped): {c.relative_to(ROOT)}")
        continue
    text = c.read_text()
    if c.suffix == ".ipynb":
        # the notebook stores cell sources as JSON strings, so a quoted artefact name arrives as
        # \"t15_T3.json\" and the quote-anchored pattern below would miss it
        import json as _json
        text = "\n".join("".join(cell["source"]) for cell in _json.loads(text)["cells"])
    for a in artefacts:
        if re.search(r'["\']' + re.escape(a) + r'(\.json)?["\']', text) or f"out/{a}.json" in text:
            used.add(a)

orphans = []
for a in sorted(used):
    produced = any(f"out/{a}.json" in t or f'"{a}.json"' in t or f"'{a}.json'" in t
                   for t in src_files.values())
    if not produced:
        in_proto = [p.name for p in PROTO.glob("*.py") if f"out/{a}.json" in p.read_text()]
        orphans.append(f"{a}.json produced only by proto/{in_proto}" if in_proto
                       else f"{a}.json has no producer anywhere")
q(f"every artefact the paper reads has a producer in src/lib ({len(used)} used of {len(artefacts)})",
  not orphans, f"{len(orphans)}: {orphans[:3]}")

# --- 2: src/lib must not reach into proto/ ----------------------------------------------------
# "proto" is also the network-protocol column name, so match the PATH or an import, not the word.
# Check CODE, not comments: a comment cannot create a dependency, and the word "proto" is also
# the network-protocol column name.  Drop comment tokens, keep string literals -- a real path
# lives in a literal.
def decomment(src):
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return src
    return tokenize.untokenize([t for t in toks if t[0] != tokenize.COMMENT])


PROTO_PATH = re.compile(r'/\s*["\']proto["\']|["\']proto["\']\s*/|["\'][^"\']*proto/'
                        r'|(?:^|\n)\s*(?:from|import)\s+proto\b')
reaches = []
for name, text in src_files.items():
    for m in PROTO_PATH.finditer(decomment(text)):
        reaches.append(f"{name}: {m.group(0).strip()[:60]!r}")
q("no file in src/lib imports or path-references proto/",
  not reaches, f"{len(reaches)}: {reaches[:3]}")

# --- 3: intra-package imports resolve inside src/lib ------------------------------------------
# Parse imports with ast, not a regex: prose inside a docstring ("...from a host already
# talking to it...") matches a regex and is not an import.
unresolved = []
for name, text in src_files.items():
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        unresolved.append(f"{name} does not parse: {e}")
        continue
    for node in ast.walk(tree):
        mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                else [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
        for mod in mods:
            root = mod.split(".")[0]
            if root in STDLIB_OK or f"{root}.py" in src_files:
                continue
            unresolved.append(f"{name} -> {mod}")
q("every intra-package import in src/lib resolves inside src/lib",
  not unresolved, f"{len(unresolved)}: {sorted(set(unresolved))[:5]}")

# --- INFO: stale proto duplicates (allowed, but worth seeing) ---------------------------------
def norm(s):
    return re.sub(r"[ \t]+\n", "\n", s).strip()


shared = sorted(set(src_files) & {p.name for p in PROTO.glob("*.py")})
diverged = [f for f in shared if norm((PROTO / f).read_text()) != norm(src_files[f])]
src_only = sorted(set(src_files) - {p.name for p in PROTO.glob("*.py")})
INFO.append(f"{len(shared)} modules exist in both trees; {len(diverged)} have diverged "
            f"(src/lib is canonical -- proto is history, and its pipeline no longer runs)")
INFO.append(f"{len(src_only)} modules exist ONLY in src/lib, including the paper-critical "
            f"{[f[:-3] for f in src_only if f[:-3] in ('t52_B1_synthetic', 't53_ordering', 't54_ait_suppression', 't66_nonoracle_padding', 't67_ait_order')]}")
INFO.append(f"{len(artefacts) - len(used)} artefacts in src/lib/out are unused by the paper (legacy)")

print("=" * 92)
for line in INFO:
    print(f"  [info] {line}")
print("-" * 92)
for line in OK:
    print(f"  ok     {line}")
for line in BAD:
    print(f"  BAD    {line}")
print("=" * 92)
print(f"  {len(OK)} consistent, {len(BAD)} INCONSISTENT")
if BAD:
    print("  The reproduction package is incomplete: the paper depends on something outside src/.")
    sys.exit(1)
print("  src/ is self-contained: the paper needs nothing from proto/")
print("=" * 92)
