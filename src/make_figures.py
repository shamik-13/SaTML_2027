"""Write the paper's figures from the shipped result objects.

Thin wrapper: the drawing code is lib/figures.py, which paper.ipynb also uses, so the notebook and the
LaTeX build render the same figures from one implementation.  Output directory: ./figures/ by default,
or the path given as the first argument (the paper source passes its own figures/ directory).

    python make_figures.py [OUTDIR]
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # must precede the pyplot import inside figures.py

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import figures                                                    # noqa: E402

figures.OUTDIR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "figures"

if __name__ == "__main__":
    print("building the figures from", figures.RES, "into", figures.OUTDIR)
    figures.build_all()
    print(f"Done: {len(figures.SUBMISSION)} figures.")
