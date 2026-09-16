"""Layout gate for the compiled paper/satml.pdf  (review 12, point 2).

WHY THIS EXISTS.  Review 12 asked to "fix the remaining float placement -- it still interrupts
sentences", listing four page/sentence pairs.  All four were STALE: they had been fixed in review 11
and the reviewer was reading an older PDF.  Checking that by hand cost a full pass over the rendered
geometry, and the answer went out of date the moment the next edit reflowed the paper.  So the check
is mechanical from here on.

WHAT IS AND IS NOT A DEFECT.  In a two-column layout a paragraph that crosses a column or page
boundary is split by whatever sits at the top of the destination column -- including every `[t]`
float.  That is ordinary typesetting, not a defect: this body has ~17 mid-sentence column breaks and
would have them with no floats at all.  Chasing them means moving float anchors, which changes which
page a float lands on, and the page refit undoes the result anyway.  Two things ARE defects and are
enforced here:

  1. HYPHEN-SPLIT AT A BREAK -- a column/page break immediately after a hyphenated word, so the
     reader crosses a boundary mid-word ("secondary win-" / "dow").  Review 12 found one of these
     across Table II; a later compile had two, one of them introduced by the review-12 rename itself.
     Fixed by `\\brokenpenalty=5000` plus `\\hyphenation{window windows}` in the preamble -- chosen
     because `\\brokenpenalty=10000` also reaches zero but adds two badness-10000 stretched pages,
     one in the body, which is the worse trade.

  2. MID-COLUMN FLOAT -- a float with body text above AND below it inside one column.  Nothing in
     this paper does that (every float is `[t]`/`[!t]`), and if one ever does it is a real placement
     bug rather than ordinary column flow.

Run after any edit that reflows the body, and in particular after the page refit.

    python proto/t68_layout.py            # or: T68_PDF=... python proto/t68_layout.py
"""
import html
import os
import pathlib
import re
import subprocess
import sys
from collections import Counter, defaultdict

if not __debug__:
    raise SystemExit(f"{__file__} must not run under `python -O`: assertions are its checks")

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = pathlib.Path(os.environ.get("T68_PDF", ROOT / "paper" / "satml.pdf"))
# The numbered body ends where the unnumbered, page-limit-exempt sections begin.
BODY_ENDS_AT = "Open Science"
COL_SPLIT_X = 311.0          # page is 612pt wide; the gutter sits either side of 306
SPAN_MIN_X = 301.0
HYPHENATED = re.compile(r"[A-Za-z]{2,}[-‐‑]$")
SENTENCE_END = re.compile(r"[.!?]$")
CAPTION = re.compile(r"^(TABLE\b|Fig\.\s*\d+\.)")
PROSE_MIN_WIDTH = 170.0      # pt; a justified body line runs the full column measure
PROSE_INDENT_TOL = 12.0      # pt; a paragraph's first line is indented ~10pt, figure text far more

OK, BAD = [], []


def q(label, cond, detail=""):
    (OK if cond else BAD).append(f"{label}   {detail}" if detail else label)


def _pages():
    if not PDF.exists():
        raise SystemExit(f"missing {PDF}; compile the paper first")
    xml = subprocess.run(["pdftotext", "-bbox", str(PDF), "-"],
                         capture_output=True, text=True).stdout
    return re.findall(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', xml, re.S)


PAGES = _pages()


def columns(pno):
    """(left, right, spanning) line lists for one page, each ordered top to bottom."""
    _w, _h, pg = PAGES[pno - 1]
    lines = defaultdict(list)
    for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
                         r'yMax="([\d.]+)">([^<]*)</word>', pg):
        xmin, ymin, xmax, _ymax, word = m.groups()
        xmin, ymin, xmax = float(xmin), float(ymin), float(xmax)
        col = 0 if xmax <= COL_SPLIT_X else (1 if xmin >= SPAN_MIN_X else 2)
        lines[(col, round(ymin))].append((xmin, xmax, html.unescape(word)))
    out = {0: [], 1: [], 2: []}
    for (col, y), words in sorted(lines.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        ws = sorted(words)
        out[col].append((y, " ".join(w for _, _, w in ws), ws[0][0], max(x1 for _, x1, _ in ws)))
    return out


def body_last_page():
    """Last page of the NUMBERED body -- the page-limit-exempt sections start on it or after."""
    txt = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True, text=True).stdout
    for i, page in enumerate(txt.split("\f"), start=1):
        if BODY_ENDS_AT in page:
            return i
    return len(PAGES)


LAST = body_last_page()


def _margins():
    """Left text margin of each column, measured from the document rather than assumed.

    Width alone cannot separate body prose from figure internals: an axis row like
    "10 3 10 4 10 5 10 6" is both wide and word-rich.  Body text is distinguished by starting at
    the column MARGIN (or one paragraph indent in from it); tick labels, legends and panel titles
    are indented much further.  The modal left edge of the wide lines in each column IS that margin.
    """
    seen = {0: Counter(), 1: Counter()}
    for pg in range(1, LAST + 1):
        c = columns(pg)
        for ci in (0, 1):
            for _y, _s, x0, x1 in c[ci]:
                if (x1 - x0) >= PROSE_MIN_WIDTH:
                    seen[ci][round(x0)] += 1
    return {ci: (seen[ci].most_common(1)[0][0] if seen[ci] else 0.0) for ci in (0, 1)}


MARGIN = _margins()


def _right_edges():
    """Right text edge of each column: the modal right end of the wide lines.  A justified body line
    ends here; a table cell's wrapped line, a ragged caption line or a paragraph's LAST line does not."""
    seen = {0: Counter(), 1: Counter()}
    for pg in range(1, LAST + 1):
        c = columns(pg)
        for ci in (0, 1):
            for _y, _s, x0, x1 in c[ci]:
                if (x1 - x0) >= PROSE_MIN_WIDTH:
                    seen[ci][round(x1)] += 1
    return {ci: (seen[ci].most_common(1)[0][0] if seen[ci] else 1e9) for ci in (0, 1)}


RIGHT = _right_edges()


def _is_prose(text, x0, x1, col):
    """A body-text line, as opposed to a figure's axis labels, legend or panel title."""
    if col not in MARGIN:
        return False
    return ((x1 - x0) >= PROSE_MIN_WIDTH
            and len(text.split()) >= 8
            and -2.0 <= (x0 - MARGIN[col]) <= PROSE_INDENT_TOL)

# reading order across the body: page by page, left column then right column
reading = []
for p in range(1, LAST + 1):
    c = columns(p)
    for ci in (0, 1):
        if c[ci]:
            reading.append((p, "L" if ci == 0 else "R", c[ci]))

# --- 1: no column/page break may land immediately after a hyphenated word --------------------
splits = []
for i, (p, ci, lines) in enumerate(reading[:-1]):
    last = lines[-1][1].strip()
    if HYPHENATED.search(last):
        nxt_p, nxt_c, nxt_lines = reading[i + 1]
        splits.append(f"p{p}{ci} ...{last[-40:]!r} -> p{nxt_p}{nxt_c} {nxt_lines[0][1][:34]!r}")
q("no column/page break falls inside a hyphenated word",
  not splits,
  f"{len(splits)} split(s): {splits[:3]}"
  if splits else f"checked {len(reading) - 1} breaks over body pages 1-{LAST}")

# --- 2: no float sits mid-column (body text both above and below it in one column) -----------
midcol, stacked = [], []
for p in range(1, LAST + 1):
    c = columns(p)
    for ci in (0, 1, 2):
        for idx, (y, text, _x0, _x1) in enumerate(c[ci]):
            if not CAPTION.match(text.strip()):
                continue
            # A caption at the top of its column has no BODY PROSE above it -- only the float's own
            # graphic text.  Word count cannot tell those apart (an axis row "10 3 10 4 10 5 ..."
            # counts 14 "words"); column-spanning WIDTH can.  Justified body text runs the full
            # measure and starts at the column margin; figure internals are short and scattered.
            # ANY body prose above the caption in its own column means the float did not land at
            # the top: it is mid-column, or at the column foot with the paragraph resuming in the
            # next column.  Both make the reader cross the float inside a paragraph, which is the
            # placement defect; requiring prose BELOW as well would miss the column-foot case
            # (verified by injecting a forced [H] float, which landed at the foot of a column).
            above = [(s, x0, x1) for _, s, x0, x1 in c[ci][:idx]
                     if _is_prose(s, x0, x1, ci) and not CAPTION.match(s)]
            # ROUND 25: two floats stacked at the top of one column are legitimate (p.2: the
            # known-vs-new table over the dependency table; p.8: Table III over Fig. 4), but the rows
            # and caption text of the UPPER float read as "prose above" the lower caption.  A column
            # that BEGINS with a caption has a float at its top, and body text resuming after a float
            # starts with an indented paragraph line; so when the column opens with a caption and no
            # line above this caption is indented, the lines above belong to the upper float.  Blind
            # spot, accepted: an unindented continuation paragraph between two floats would also pass.
            # The column opens with a float if its first line is a caption title, or a line that
            # spans the gutter (the caption text of a table*/figure* whose centred "TABLE N" title
            # is assigned to the spanning column).  Table cell text sits ~5pt in; a paragraph's
            # first line sits ~10pt in, so 8pt separates the two.
            _first = c[ci][0] if c[ci] else None
            # a two-column float's centred "TABLE N" title lands in the spanning bucket (index 2);
            # if one sits above this caption on the page, the column opens under that float.
            _span_caption_above = (len(c) > 2 and any(CAPTION.match(t.strip()) and yy < y
                                                      for yy, t, _a, _b in c[2]))
            col_opens_with_float = bool(_first) and (bool(CAPTION.match(_first[1].strip()))
                                                     or (ci == 0 and _first[3] > SPAN_MIN_X)
                                                     or _span_caption_above)
            # ROUND 26: a wrapped cell line of a table*'s first p-column can sit 9-10pt in (6pt colsep
            # plus the side bearing of an italic parenthesis), which the 8pt indent test read as a
            # paragraph start.  A paragraph's FIRST line is justified to the column's right edge; a cell
            # line, a ragged caption line or a paragraph's last line is not -- so a paragraph start must
            # be indented AND reach the right edge.  Blind spot, accepted: a one-line paragraph.
            any_paragraph_start = (any((x0 - MARGIN[ci]) > 8.0 and x1 >= RIGHT[ci] - 2.5
                                       for _, x0, x1 in above) if ci in MARGIN else True)
            # ROUND 26, second refinement: `columns()` assigns each WORD to a column by its own x-range,
            # so a table*'s rows and caption split into a col-0 half and a col-1 half, and the col-0
            # half of a row can start 9-10pt in AND end within 3pt of the column's right edge -- exactly
            # the signature of a paragraph's first line.  The indent test therefore cannot separate a
            # spanning float's left half from body text.  What can: every float in this paper is [t] or
            # [!t], and LaTeX sets a column's top floats contiguously, so a column that OPENS with a
            # float caption has no body text above any later caption in it -- whatever sits between two
            # captions is the upper float's own material.  Blind spot, accepted and stated: an [h]/[b]
            # float, or body text between two floats, would need a placement specifier this paper does
            # not use (grep '\\begin{table' / '\\begin{figure' for anything but [t] and [!t]).
            if above and col_opens_with_float:
                stacked.append(f"p{p} col{ci} {text.strip()[:26]!r} (stacked under the column's top float"
                               f"{'; indented full lines above, read as the upper float' if any_paragraph_start else ''})")
            elif above:
                midcol.append(f"p{p} col{ci} {text.strip()[:26]!r} "
                              f"({len(above)} prose lines above it in the same column; column opens "
                              f"with {c[ci][0][1].strip()[:20]!r} caption={col_opens_with_float}; "
                              f"x0 offsets {[round(x0 - MARGIN.get(ci, x0), 1) for _, x0, _x1 in above]}; "
                              f"x1 short of the right edge by {[round(RIGHT.get(ci, x1) - x1, 1) for _, _x0, x1 in above]})")
q("every body float lands at the top of its column or page",
  not midcol,
  f"{len(midcol)}: {midcol[:3]}" if midcol else
  "every float sits at the top of its column or page" + (f"; stacked floats: {stacked}" if stacked else ""))

# --- 3: informational -- where the body ends, for the page refit -----------------------------
print(f"  [info] numbered body ends on page {LAST}; page-limit-exempt sections start there")
print(f"  [info] mid-sentence column breaks: "
      f"{sum(1 for i, (p, ci, l) in enumerate(reading[:-1]) if not SENTENCE_END.search(l[-1][1].strip()))}"
      f" of {len(reading) - 1} -- ordinary two-column flow, NOT a defect (see module docstring)")

print("=" * 92)
for line in OK:
    print(f"  ok     {line}")
for line in BAD:
    print(f"  BAD    {line}")
print("=" * 92)
print(f"  {len(OK)} consistent, {len(BAD)} INCONSISTENT")
if BAD:
    sys.exit(1)
print("  the rendered layout carries no hyphen-split break and no mid-column float")
print("=" * 92)
