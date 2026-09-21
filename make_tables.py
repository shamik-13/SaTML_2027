import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import tables                                                     # noqa: E402

tables.OUTDIR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "tables"

if __name__ == "__main__":
    print("building the tables from", tables.RES, "into", tables.OUTDIR)
    written = tables.build_all(verbose=False)
    print(f"Done: {len(written)} files.")
