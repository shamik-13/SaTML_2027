"""Build the submission's figures into paper/figures/.

This is a THIN WRAPPER. The drawing code lives in ../src/lib/figures.py, inside the reproduction
package, so that `src/paper.ipynb` and the LaTeX build render the same figures from the same code.
Before that move the figures existed only here, and the notebook could reproduce every number behind
a figure without being able to draw it -- two artifacts that could silently disagree.

Usage:  ../proto/.venv/bin/python make_figures_satml.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # must precede the pyplot import inside figures.py

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src" / "lib"))
import figures                                                    # noqa: E402

figures.OUTDIR = HERE / "figures"

if __name__ == "__main__":
    print("building the submission figures from", figures.RES)
    figures.build_all()
    print(f"Done: {len(figures.SUBMISSION)} figures.")
