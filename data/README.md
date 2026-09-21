# Obtaining the data

## LSPR23

- record: <https://zenodo.org/records/8042347>
- file: `ls23pr_v1.csv` — 10.6 GB, 16,353,511 flows, 101 columns

## AIT-LDSv2.0 (the transfer test)


- record: <https://zenodo.org/records/5789064>
- what the pipeline reads: `NF__<org>_netflows.zip`, one per organisation, each containing
  `tcp_complete.csv` (tstat netflows). Eight organisations: `fox`, `harrison`, `russellmitchell`,
  `santos`, `shaw`, `wardbeck`, `wheeler`, `wilson`. **The zips are not redistributed here** (as with
  LSPR23), so fetch them from the Zenodo record above.
- in `ait/`: the dataset's own extraction notebooks
  (`NF__1_format_dataset_info.ipynb`, `NF__2_label_logs.ipynb`), `NF__label_info.txt` (the malicious
  flow-label set the extraction matches against, reproduced exactly in `lib/t51_R7_ait.py`) and
  `NF__README.md` (the dataset's own notes). That is everything needed to turn the released record
  into the eight-organisation netflow inputs.

Put the zips in `data/ait/`, or point `AIT_ZIP_DIR` at wherever you keep them. On first use
`lib/t51_R7_ait.py` extracts each `tcp_complete.csv` into `AIT_DIR` (default `/tmp/ait_cache`) and
reuses that cache thereafter.

The experiment is **TCP-only**: the sole UDP malicious label (`data exfiltration`, DNSteal) is
deliberately excluded, and no DNS-exfiltration coverage is claimed.

## Deriving the inputs

Two `awk` passes over the raw CSV produce what the pipeline reads. Each takes a few minutes.

```bash
# features: ts, src, dst, label, proto, then columns 9-40
awk -F',' 'NR>1 {
   printf "%s,%s,%s,%s,%s", $7,$2,$3,$95,$6
   for(i=9;i<=40;i++){ v=$i; if(v==""||v=="NaN"||v=="Infinity"||v=="-Infinity") v=0; printf ",%s", v }
   printf "\n" }' ls23pr_v1.csv > /tmp/lspr_full.csv

# ports, in the original row order
awk -F',' 'NR>1 {print $4","$5}' ls23pr_v1.csv > /tmp/lspr_ports.csv
```

The forensics sections additionally use annotation columns:

```bash
awk -F',' 'NR>1 {print $2","$3","$4","$5","$89","$91","$92","$93","$94","$96","$97","$98","$99}' \
    ls23pr_v1.csv > /tmp/lspr_meta.csv
```

## Where the pipeline looks

The paths above are the defaults, and match the recipes on this page.

| variable | default | what it moves |
|---|---|---|
| `LSPR_DIR` | `/tmp` | all three derived CSVs and both caches |
| `LSPR_CSV`, `LSPR_PORTS`, `LSPR_META_CSV` | under `LSPR_DIR` | one file each |
| `LSPR_CACHE`, `LSPR_META_CACHE` | under `LSPR_DIR` | one cache each |
| `AIT_ZIP_DIR` | `data/ait` | the AIT zips |
| `AIT_DIR` | `/tmp/ait_cache` | the extracted AIT netflows |


## Caches

On first use the pipeline builds `.npy` caches under `/tmp/lspr_cache` (~2.6 GB) and
`/tmp/lspr_meta_cache` (~0.8 GB). They rebuild automatically if deleted.

Total working set with the raw file: about 27 GB.

## Already included

`lib/data/lspr23_attacknarratives.json` (9.7 MB) — the red-team task record, 288 narratives.
