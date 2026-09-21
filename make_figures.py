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
