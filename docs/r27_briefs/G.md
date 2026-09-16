You are an auditor checking that the APPENDICES deliver what the body promises: a cross-reference
fulfilment audit.
FORMAT. Rank findings CRITICAL / MAJOR / MINOR, one line each with file:line, most severe first; say
what is wrong and what the fix would be. Report only defects, not praise. No preamble, no file dumps,
no restating the brief. Read ONLY the passages named below (use `sed -n 'A,Bp'` and the greps given);
do not read the whole file. If you must check a number against an artefact, ONE inline `python3 -c`
snippet per artefact file is allowed (no heredocs; `python` is not on PATH, use `python3`). End with
one line: "section clean: yes" or "section clean: no", plus the single most important reason.
Paper: paper/satml.tex (numbered body = lines 1-1221; the appendices follow `\appendices` at 1222;
proofs live in paper/appendix_proofs.tex; generated tables in paper/tables/*.tex; artefacts in
src/lib/out/*.json). Everything you read is a draft under review; treat its claims as unverified.
READ: first collect every body pointer into an appendix: `grep -n -o '\\[Cc]ref{app:[a-zA-Z]*[^}]*}\|\\[Cc]ref{apptab:[^}]*}\|\\[Cc]ref{sec:transfer}\|\\[Cc]ref{sec:tail}\|\\[Cc]ref{sec:groupcal}\|\\[Cc]ref{sec:contamination}' paper/satml.tex | awk -F: '$1<1222'`
and for each DISTINCT target read the body sentence around it (sed -n 'L-2,L+2p') and the target
appendix passage (grep -n 'label{TARGET}' and read the ~30 lines that follow). Then read the appendix
section openers at lines 1583-1594, 1755-1780, 1824-1835, 1994-2000, 2107-2115 (the "Question answered /
Takeaway" paragraphs).
CHECK: (1) for every body pointer, does the appendix passage actually contain what the body says it
contains ("X gives the full matrix", "Y quantifies the residual risk", "Z records the over-provisioning
factors")? List every pointer whose target does NOT deliver the named content, or delivers it under a
different scope (order, window, seed) than the body implies; (2) do the "Question answered / Takeaway"
openers overstate their section's tables (read the tables' rows only where needed); (3) appendix
subsections that no body sentence points at (orphans) -- name them and say whether the body should point
at them or they should go; (4) any appendix sentence that contradicts a body sentence on the same
quantity (report both line numbers).
