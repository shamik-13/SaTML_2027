## Quick start

```bash
pip install -r requirements.txt  
jupyter notebook paper.ipynb      # MODE = "paper", runs in about half a minute
```

To run it headlessly instead:

```bash
python -c "import nbformat; from nbclient import NotebookClient; \
  nb = nbformat.read('paper.ipynb', as_version=4); \
  NotebookClient(nb, kernel_name='python3').execute()"
```
## Two modes

`MODE` is set in the notebook's first code cell.

| MODE | what it does | needs | time |
|---|---|---|---|
| `"paper"` | loads the cached results in `lib/out/` | nothing | about half a minute |
| `"full"` | recomputes every result  | the dataset, ~27 GB | ~2-3 h |

## Getting the data

Both datasets are third-party and neither is redistributed here. See `data/README.md` for the
details. In outline:

1. Download `ls23pr_v1.csv` (10.6 GB) from the LSPR23 Zenodo record.
2. Run the two recipes in `data/README.md`  to produce the feature and port files.
3. For the AIT transfer test, fetch the eight netflow zips (Zenodo 5789064) into `data/ait/`,
   or point `AIT_ZIP_DIR` at them.
4. Set `MODE = "full"` and run the notebook. The flow cache is built on first use (~1 min)
   and reused afterwards.


## Layout

```
paper.ipynb      the paper's implementation
runner.py        py version of ipynb
make_tables.py   the same for the generated tables (lib/tables.py)
lib/             one script per result, each exposing main()
lib/figures.py   every figure; lib/tables.py every generated table
lib/out/         the cached results, one JSON per stage
lib/data/        red-team attack narratives
data/README.md   how to obtain LSPR23 and AIT-LDSv2.0
data/ait/        the AIT extraction recipe and label mapping
```

`runner.py` is an alternative entry point for running everything headless:

```bash
python runner.py --theory     # the no-data stages, ~1 min
python runner.py              # everything, ~2-3 h
python runner.py --list       # the stage list
```

## Notes

- Results are deterministic given the seeds fixed in each script. Detector seeds 0 and 1 are
  reported throughout; where a result depends on randomisation the notebook shows the spread
  rather than a single draw.
- Episode counts, calibration sizes and margins depend only on the stream and the grouping,
  not on the detector, so they are identical across seeds by construction.
- The scripts write to `lib/out/`. Re-running overwrites; move the directory aside first if
  you want to compare against the shipped artifacts.
