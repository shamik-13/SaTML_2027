You are a copy editor and notation checker reading the WHOLE BODY of a submission for consistency,
not for correctness of results.
FORMAT. Rank findings CRITICAL / MAJOR / MINOR, one line each with file:line, most severe first; say
what is wrong and what the fix would be. Report only defects, not praise. No preamble, no file dumps,
no restating the brief. Read ONLY the passages named below (use `sed -n 'A,Bp'` and the greps given);
do not read the whole file. If you must check a number against an artefact, ONE inline `python3 -c`
snippet per artefact file is allowed (no heredocs; `python` is not on PATH, use `python3`). End with
one line: "section clean: yes" or "section clean: no", plus the single most important reason.
Paper: paper/satml.tex (numbered body = lines 1-1221; the appendices follow `\appendices` at 1222;
proofs live in paper/appendix_proofs.tex; generated tables in paper/tables/*.tex; artefacts in
src/lib/out/*.json). Everything you read is a draft under review; treat its claims as unverified.
READ: paper/satml.tex lines 130-1135 (body), skimming for the classes of defect below; you may grep the
appendices (1222-2289) and paper/tables/*.tex only to confirm a notation or spelling inconsistency.
CHECK, each as a grep-driven sweep with counts and one example line each: (1) spelling variant mix
(British vs American: -ise/-ize, -our/-or, "realised/realized", "behaviour/behavior", "modelled/modeled",
"artefact/artifact") -- report which convention dominates and every deviation; (2) abbreviations used
before their first expansion or never expanded (SOC, FDR, FDP, AUROC, AUPRC, HGB, e-LOND, LOND, LORD++,
ADDIS, SAFFRON, e-BH, IQR, CI, AIT, LSPR23, SaTML); (3) notation drift: M vs \ceil, alpha_t vs
\alphat, r^\star vs r^\star_t vs r_t^\star, S vs S_t, m vs m_t, gamma_j vs gamma_t, |C| vs \nCal,
"e-value" vs "e-variable", "host pair" vs "host-pair", "two-hour" vs "2 h" vs "2\,h", "zero-evidence"
hyphenation, "state-free" vs "state free"; (4) number formatting: thousands separators ({,} vs none vs
\,), percentages with and without \%, ranges with -- vs -; (5) every table and figure is referenced in
the body BEFORE or on the page it appears, and Tables I-V and Figs. 1-4 are first referenced in
numerical order (report the first-reference line of each); (6) duplicated or near-duplicated sentences
across sections (same claim in the same words in two places) -- give both line numbers; (7) cleveref
usage: any hard-coded "Section", "Table", "Fig." or "Eq." with a \ref instead of \cref, and any
sentence starting with a lowercase \cref.
