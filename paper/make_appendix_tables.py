"""Build the submission's generated tables into paper/tables/.

This is a THIN WRAPPER. The generator lives in ../src/lib/tables.py, inside the reproduction package,
next to figures.py and for the same reason: the shipped artifact must regenerate every table the paper
\input{}s from the shipped result objects, with the LaTeX build and the artifact sharing one
implementation.  Every value is read from ../src/lib/out/*.json; nothing is hardcoded here.

Usage:  ../proto/.venv/bin/python make_appendix_tables.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src" / "lib"))
import tables                                                     # noqa: E402

tables.OUTDIR = HERE / "tables"

if __name__ == "__main__":
    tables.build_all()
