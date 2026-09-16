You are a sceptical reviewer reading the DISCUSSION of a submission: design alternatives, limitations,
related work and conclusion.
FORMAT. Rank findings CRITICAL / MAJOR / MINOR, one line each with file:line, most severe first; say
what is wrong and what the fix would be. Report only defects, not praise. No preamble, no file dumps,
no restating the brief. Read ONLY the passages named below (use `sed -n 'A,Bp'` and the greps given);
do not read the whole file. If you must check a number against an artefact, ONE inline `python3 -c`
snippet per artefact file is allowed (no heredocs; `python` is not on PATH, use `python3`). End with
one line: "section clean: yes" or "section clean: no", plus the single most important reason.
Paper: paper/satml.tex (numbered body = lines 1-1221; the appendices follow `\appendices` at 1222;
proofs live in paper/appendix_proofs.tex; generated tables in paper/tables/*.tex; artefacts in
src/lib/out/*.json). Everything you read is a draft under review; treat its claims as unverified.
READ: paper/satml.tex lines 981-1135 (Sec. VI with the defences discussion; Sec. VII scope and
limitations; Related Work; Conclusion). For context on what the body actually showed, read the abstract
(lines 130-152) and the Table IV (defences) source at `grep -n 'label{tab:defenses}'` (read 25 lines).
CHECK: (1) LIMITATIONS: which limitation that the body's own results imply is MISSING or understated
here -- consider: one seed for the joint rerun; the attacker-ownership oracle (the attacker knows which
episodes are its own); zero-evidence pads as the model; e-LOND only for the joint rerun; two windows;
the AIT host-conditioned arm of nine episodes; the known-invalid stress window; label quality; the
canonical order being a choice; the cap grid being sampled; (2) each limitation stated is honest about
what was measured (no "we show" where "we observe on two windows" is meant); (3) Sec. VI: every
sentence about a defence matches the defences table row and does not promise more than the appendix
measured; (4) Related Work: sentences that attribute a specific claim to a cited work in a way the body
does not support, or that could read as disparaging prior work; the "what this literature leaves open"
sentence -- is the gap stated as a gap in THEIR question, not a defect in their work; (5) Conclusion vs
abstract: any claim in one absent from or stronger than in the other.
