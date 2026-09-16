# SaTML 2027 submission — LaTeX

Verified against <https://satml.org/call-for-papers/> on 27 Aug 2026.

## Files

| | |
|---|---|
| `satml.tex` | **submission draft** (rewrite of `main.tex`): nine body sections on one causal chain, body ends p.11 of the 12-page limit; structure follows `../docs/satml_2027_rewrite_plan.json` and `../docs/satml_2027_rewrite_main_body.md`; shares `refs.bib`, `appendix_proofs.tex`, `tables/` and `figures/` with `main.tex`. The LLM Usage section is a TODO stub. Build: `tectonic -X compile satml.tex` |
| `main.tex` | first full draft, all twelve sections written (the log of everything done; 17-page body); structure follows `../docs/20_satml_paper_outline_and_manuscript_skeleton.md` |
| `make_figures_satml.py` | builds the three figure variants `satml.tex` uses (`fig1_chain`, `fig3_granularity_body`, `fig4_attacks_body`) from `../src/lib/out/`, reusing `make_figures.py`'s styling; leaves the four `main.tex` figures untouched |
| `refs.bib` | 32 entries, each verified against a primary source (arXiv/publisher/proceedings/Zenodo) |
| `main.pdf` | built output |
| `figures/` | `fig1`--`fig4` as PDF (used by the build) and PNG (for quick viewing) |
| `make_figures.py` | regenerates `figures/` from `../src/lib/out/`; Overleaf ignores it |
| `appendix_proofs.tex` | full proofs (Appendix A); `\input` by `main.tex` |
| `tables/` | the 25 appendix measurement tables (`apptab:*`), `\input` by `main.tex` |
| `make_appendix_tables.py` | regenerates `tables/*.tex` from `../src/lib/out/`; every value is read from the JSON artifacts, none hardcoded |
| `IEEEtran.cls` | V1.8b, from CTAN — **required**, do not substitute |
| `IEEEtran.bst` | matching bibliography style |

## Building

`tectonic` is installed and builds this directory as-is (it fetches packages on first run):

```bash
tectonic -X compile main.tex        # -> main.pdf
```

Alternatives: `latexmk -pdf main.tex` under MacTeX/BasicTeX, or upload the directory to
Overleaf, which already has IEEEtran (the local `.cls`/`.bst` copies then sit unused, and are
kept so the build is self-contained either way).

### Page budget, measured

The body is everything up to the Open Science heading. To measure it:

```bash
tectonic -X compile main.tex && pdftotext main.pdf - | \
  awk 'BEGIN{RS="\f"} /^Open Science$/ {print "body ends on page", NR-1; exit}'
```

## Figures

All four are generated, not hand-drawn, and every plotted number comes from the artifact
results in `../src/lib/out/`:

| | source | content |
|---|---|---|
| `fig1_system.pdf` | schematic | the pipeline with both attack surfaces marked |
| `fig2_envelope.pdf` | closed form | required \|C\| against horizon T, per procedure family |
| `fig3_granularity.pdf` | `t26_H4.json` | margin / episode recall / flow coverage against bucket width |
| `fig4_attacks.pdf` | `t28_P5.json`, `t32_B1.json` | padding suppression curves; the B* = 203 cliff |

To rebuild the figures **and the appendix tables** after the artifact results change:

```bash
../proto/.venv/bin/python make_appendix_tables.py   # regenerates tables/*.tex from ../src/lib/out/
../proto/.venv/bin/python make_figures.py     # any env with matplotlib + numpy works
```

Fig. 3 marks infeasible configurations with **open** markers and does not join them to the
line: they have no operating point, so their recall and coverage are not achievable numbers.

## Uploading to Overleaf

The directory is self-contained — zip `paper/` and upload it. `IEEEtran.cls`/`.bst` are
included so the build does not depend on Overleaf's TeX Live version, and `\graphicspath`
points at `figures/`, so nothing needs re-pathing.

## The rules that constrain writing

**Template is mandated.** `\documentclass[conference]{IEEEtran}`, default 10pt and geometry.
Quoting the CFP: *"Using a different template, or modifying font size, margins, or spacing to
fit more content, is grounds for desk rejection."* The page budget cannot be recovered by
formatting.

**12 pages of _body text_.** References and appendices are unlimited and do **not** count.
Neither do the Open Science / Ethical Considerations / LLM sections, which sit before the
references. But: *"reviewers are not required to read appendices, and papers are assessed on
the body text"* — so nothing load-bearing may live only in an appendix.

**Double-blind.** No names, no institutions, and cite our own prior work in the third person.
`\satmlanon` is `1` for submission; set it to `0` at camera-ready.

**Open Science is mandatory** — describe the artifacts being released, or explain why sharing
is not possible. Anonymised artifacts are due **3 Oct 2026**, within three days of the paper
deadline. Acceptance is *conditional* on final artifacts reaching zenodo.org by 14 Jan 2027.

**Ethical Considerations is optional**, but this paper describes working attacks against a
deployed decision layer, so it should be present. The CFP points at the Menlo report.

**LLM Usage Considerations is mandatory if LLMs were used** — disclosure, motivation, and a
statement on accountability/correctness, transparency and responsibility. The section is
stubbed out (commented) in `main.tex`; decide it deliberately rather than by omission.

## Dates

| | |
|---|---|
| Abstract registration (mandatory) | Tue 22 Sep 2026, 23:59 AoE |
| Paper submission | Tue 29 Sep 2026, 23:59 AoE |
| Anonymised artifacts | Fri 2 Oct 2026 |
| Early reject notification | Wed 4 Nov 2026 |
| Interactive discussion / revision | 25 Nov – 9 Dec 2026 |
| Decision | Wed 16 Dec 2026 |
| Final artifacts on Zenodo | Thu 14 Jan 2027 |
| Revisions due | Thu 21 Jan 2027 |
| Camera-ready | mid-Feb 2027 (TBC) |
| Conference | early May 2027, Reykjavík |

ORCIDs and Author Certification go through HotCRP by the **abstract** deadline. The
submission link was still TBC when this was checked.

## Before writing

Read `../docs/03_FROZEN_CLAIMS.md` first — it bounds what the paper may assert, and §C's
caveats have to travel with the numbers they qualify. `../docs/04_EXPERIMENTS_AND_FINDINGS.md`
is the authoritative source for every figure; `proto/t45_record_consistency.py` checks that
document's numbers against the artefacts they came from and should be re-run after edits.
