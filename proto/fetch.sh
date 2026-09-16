#!/bin/bash
cd "$(dirname "$0")/data"
log(){ echo "[$(date +%H:%M:%S)] $*"; }
get(){ # url  outfile
  if [ -s "$2" ]; then log "SKIP $2 (exists $(du -h "$2"|cut -f1))"; return; fi
  log "GET $2"
  curl -sS -L --retry 3 --max-time 3600 -o "$2.part" "$1" && mv "$2.part" "$2" && log "OK $2 $(du -h "$2"|cut -f1)" || log "FAIL $2"
}
# AIT Alert Data Set (96MB) - alerts w/ multi-step scenario ground truth
curl -sS --max-time 60 "https://zenodo.org/api/records/8263181" -o ait_ads_meta.json
# AIT Netflow Data Set (274MB) - flows from same testbeds
curl -sS --max-time 60 "https://zenodo.org/api/records/13168643" -o ait_nf_meta.json
python3 - <<'PY'
import json,subprocess,os
for meta,tag in [("ait_ads_meta.json","ADS"),("ait_nf_meta.json","NF")]:
    d=json.load(open(meta))
    for f in d.get("files",[]):
        url=f["links"]["self"]; key=f["key"]; sz=f.get("size",0)
        out=f"{tag}__{key}"
        if os.path.exists(out) and os.path.getsize(out)>0: print("skip",out); continue
        print(f"downloading {out} {sz/1e6:.1f}MB")
        subprocess.run(["curl","-sS","-L","--retry","3","--max-time","3600","-o",out,url])
PY
log "AIT done"
# LSPR23 attack narratives (incident ground truth) + flows
get "https://zenodo.org/records/8042347/files/ls23pr_attacknarratives_v1.json?download=1" "lspr23_attacknarratives.json"
get "https://zenodo.org/records/8042347/files/ls23pr_flows.zip?download=1" "lspr23_flows.zip"
log "ALL DONE"
ls -la
