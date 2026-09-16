"""R7 on a benign-inclusive testbed (AIT-LDSv2.0) -- the padding-transfer question WITHOUT a graft.

On LSPR23 the R7 measurement ("does ordinary victim-service traffic score benign under a host-
conditioned detector?") could only be done by GRAFTING attack context onto ordinary flow-stats,
because LSPR23's attacked host pairs are 100% malicious -- no real ordinary-to-victim traffic exists.
The graft is out-of-distribution, so the LSPR23 stress-window result was inconclusive.

AIT-LDSv2.0 removes that obstacle: its victims are real servers that serve heavy benign traffic while
being attacked (audited: attacked servers are 79-99.9% benign).  So the R7 question is answered
DIRECTLY on real flows -- no graft, in-distribution.  AIT's attacks are recon + web-exploit + exfil
(scans, wpscan, dirb, webshell, dnsteal, cracking, post-exploitation commands), i.e. the LOW/MODERATE
regime; it has NO high-volume DDoS flood, so it resolves R7's moderate regime, not the flood.

Design (leave-one-scenario-out; 8 orgs share one red-team playbook, so a detector trained on 7 orgs
detects the 8th -- a realistic "deploy on a new network" test):
  - Flow features: numeric tstat statistics, selected PER FOLD from the TRAINING orgs only, with all
    identity/label/role and ABSOLUTE-TIME fields excluded (first,last,req_tm,res_tm are epoch-scale
    and would leak the attack schedule), plus a programmatic epoch-scale guard.
  - Six strictly-causal host features (reused from t49, validated builder): per-host prior count,
    distinct peers, failed-conn fraction (fail = TCP reset), src and dst side, built within scenario.
  - Detector: HGB on the 7 training orgs (flow-only and host-conditioned X_aug=[flow|host]).
  - Conformal calibration: the TEST org's own early benign window (in-distribution, valid); the rest
    of the test org is the deployment window.  Threshold conformal e-value (hs.evalues, strict >).

Decisive measurement (no graft): among the test org's deployment flows, the FIRE RATE of REAL benign
flows whose destination is an attacked victim ("benign->victim", the pad analog), under the flow-only
vs the host-conditioned detector.  The claim rests on how much HOST conditioning ADDS over
flow-only (host - flow benign->victim), and how that compares to the LSPR23 grafted magnitude.  On
real data host conditioning adds a MODEST, org-dependent effect (host mean benign->victim ~1% vs
flow-only ~0.02%; zero on ~half the orgs, up to ~8% on one) -- real but WEAK and INCONSISTENT, and
6-38x below the LSPR23 grafted 43%.  So the graft was an out-of-distribution OVERESTIMATE (not a pure
artifact), host conditioning is not the strong defence it appeared, and padding substantially
transfers.  Reported with per-fold, median, signed, weighted, and mean-absolute deltas.  TCP flows.

Produces out/t51_R7_ait.json.
"""
import numpy as np, pandas as pd, json, time, glob, os, zipfile
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
import h_stream as hs
import t49_R7_host_detector as t49

K = 1; SEED = 0; CAL_FRAC = 0.35; EPOCH_GUARD = 1e11    # drop any feature whose |median| exceeds this
AIT_DIR = os.environ.get("AIT_DIR", "/tmp/ait_cache")   # tstat netflows are extracted to here
# The AIT-LDSv2.0 netflow zips.  Third-party data, not redistributed here: fetch Zenodo 5789064 into
# src/data/ait/, or point AIT_ZIP_DIR at wherever they are kept.  Once extracted, AIT_DIR caches the
# tcp_complete.csv per organisation and the zips are no longer needed.  See src/data/README.md.
AIT_ZIP_DIR = os.environ.get("AIT_ZIP_DIR", "")


def ensure_extracted():
    """Extract each scenario's tcp_complete.csv from src/data/ait/NF__<name>_netflows.zip if absent."""
    data = (Path(AIT_ZIP_DIR) if AIT_ZIP_DIR
            else Path(__file__).resolve().parents[1] / "data" / "ait")
    zips = sorted(data.glob("NF__*_netflows.zip"))
    if not zips and not glob.glob(f"{AIT_DIR}/*/tcp_complete.csv"):
        raise FileNotFoundError(
            f"no AIT netflow zips in {data} and no cache in {AIT_DIR}. Fetch AIT-LDSv2.0 "
            "(Zenodo 5789064) per src/data/README.md.")
    for z in zips:
        name = z.name[len("NF__"):-len("_netflows.zip")]
        out = Path(AIT_DIR) / name / "tcp_complete.csv"
        if out.exists():
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(z) as zf:
            with zf.open("tcp_complete.csv") as src, open(out, "wb") as dst:
                dst.write(src.read())
# complete malicious TCP flow-label set (NF__label_info.txt), exact match. This experiment is
# TCP-only (tcp_complete.csv); the sole UDP malicious label "data exfiltration" (DNSteal) is NOT
# covered here, so it is deliberately excluded and no DNS-exfil coverage is claimed.
MAL = set("""service_scan online_cracking host_discover_dmz host_discover_local wpscan dirb_scan
upload_rce_shell check_user_id check_netstat_t read_resolv check_network_config check_ps_a
check_release read_group read_passwd check_date list_web_dir check_wp_config dump_wp_users
read_profile dns_brute_force_start list_www check_who clear check_last check_id vpn_connect
check_whoami check_uname_r check_meminfo check_uname_a check_df check_netstat_nat list_home
check_netstat_l check_cpuinfo check_uptime check_pwd list_l""".split())
# known BENIGN TCP labels (NF__label_info.txt); rows whose label is in neither set (e.g. empty) are
# dropped as unknown rather than silently counted benign.
BENIGN = {"browsing/update", "benign_share", "broken flow - benign", "mail", "monitoring",
          "HTTP(S) intra", "HTTP(S) DMZ", "HTTP", "HTTPS", "DNS", "SSH", "proxy",
          "update/command on unassigned port"}
# identity / label / role / ABSOLUTE-TIME columns never used as features
EXCL = {"c_ip", "s_ip", "c_port", "s_port", "timestamp", "first", "last", "req_tm", "res_tm",
        "role_cli", "ipv4_address_cli", "network_cli", "role_serv", "ipv4_address_serv",
        "network_serv", "label", "fqdn", "c_tls_SNI", "s_tls_SCN", "dns_rslv", "c_npnalpn",
        "s_npnalpn", "c_tls_sesid"}


def _is_mal(lab):
    return lab.apply(lambda s: s in MAL).to_numpy().astype(int)     # EXACT label match (labels atomic)


def load_scenario(path):
    """One AIT tstat tcp_complete.csv -> time-sorted arrays + numeric frame + causal host features."""
    df = pd.read_csv(path, low_memory=False)
    df.columns = [c.lstrip("#").split(":")[0] for c in df.columns]
    df = df.rename(columns={df.columns[0]: "c_ip"})
    lab = df["label"].fillna("").astype(str)
    known = lab.isin(MAL | BENIGN)                          # drop unknown/empty labels (not benign)
    if not known.all():
        df = df[known.to_numpy()].reset_index(drop=True); lab = lab[known.to_numpy()].reset_index(drop=True)
    y = _is_mal(lab)
    ts = (pd.to_datetime(df["timestamp"]).astype("int64") // 1000).to_numpy()
    order = np.argsort(ts, kind="stable")
    df = df.iloc[order].reset_index(drop=True); y = y[order]; ts = ts[order]
    src = pd.factorize(df["c_ip"])[0].astype(np.int64)
    dst = pd.factorize(df["s_ip"])[0].astype(np.int64)
    rst = (pd.to_numeric(df.get("c_rst_cnt"), errors="coerce").fillna(0).to_numpy() +
           pd.to_numeric(df.get("s_rst_cnt"), errors="coerce").fillna(0).to_numpy())
    is_fail = (rst > 0).astype(np.float64)
    numcols = [c for c in df.columns if c not in EXCL]
    Xnum = df[numcols].apply(pd.to_numeric, errors="coerce")
    good = set(c for c in numcols if Xnum[c].notna().mean() > 0.9 and Xnum[c].nunique() > 1)
    H = t49.build_host_features(src, dst, ts, is_fail)
    return dict(y=y, ts=ts, Xnum=Xnum.fillna(0.0), good=good, H=H, is_fail=is_fail,
                src=src, dst=dst,                       # integer codes (added for t54)
                src_ip=df["c_ip"].to_numpy(), dst_ip=df["s_ip"].to_numpy(),
                victims=set(np.unique(df["s_ip"].to_numpy()[y == 1])))


def fit(Xtr, ytr):
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, l2_regularization=1.0,
                                          min_samples_leaf=20, random_state=SEED,
                                          early_stopping=False).fit(Xtr, ytr)


def main():
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    ensure_extracted()
    paths = sorted(glob.glob(f"{AIT_DIR}/*/tcp_complete.csv"))
    names = [Path(p).parent.name for p in paths]
    if len(names) < 3:
        raise FileNotFoundError(f"need AIT scenarios under {AIT_DIR}/<name>/tcp_complete.csv; found {names}")
    print(f"  loading {len(names)} AIT scenarios: {names}")
    scen = {n: load_scenario(p) for n, p in zip(names, paths)}
    tot_mal = sum(int(s["y"].sum()) for s in scen.values())
    tot = sum(len(s["y"]) for s in scen.values())
    print(f"  pooled flows={tot:,} malicious={tot_mal:,} ({100*tot_mal/tot:.2f}%)  [{time.time()-t0:.0f}s]")

    folds = {}
    for test in names:                                    # leave-one-scenario-out
        tr = [n for n in names if n != test]
        feat = sorted(set.intersection(*[scen[n]["good"] for n in tr]))   # PER-FOLD, training orgs only
        # epoch-scale guard on training data (drop any absolute-time-like feature that slipped through)
        med = pd.concat([scen[n]["Xnum"][feat] for n in tr]).abs().median()
        feat = [c for c in feat if med[c] < EPOCH_GUARD]
        def flowX(n): return scen[n]["Xnum"][feat].to_numpy(np.float32)
        Xf_tr = np.vstack([flowX(n) for n in tr]); ya_tr = np.concatenate([scen[n]["y"] for n in tr])
        Xa_tr = np.vstack([np.concatenate([flowX(n), scen[n]["H"]], axis=1) for n in tr]).astype(np.float32)
        s = scen[test]; yte = s["y"]; Xf_te = flowX(test)
        Xa_te = np.concatenate([Xf_te, s["H"]], axis=1).astype(np.float32)
        nte = len(yte); ncal = int(CAL_FRAC * nte)
        cal_mask = np.zeros(nte, bool); cal_mask[:ncal] = True; cal_mask &= (yte == 0)
        dep_mask = np.zeros(nte, bool); dep_mask[ncal:] = True
        ycal, ydep = yte[cal_mask], yte[dep_mask]
        vic_dep = np.array([ip in s["victims"] for ip in s["dst_ip"][dep_mask]])
        ben = ydep == 0
        res = {}
        for tag, Xtr, Xall in (("flow", Xf_tr, Xf_te), ("host", Xa_tr, Xa_te)):
            clf = fit(Xtr, ya_tr); sc = clf.decision_function(Xall)
            e_dep, cal, NC, CEIL = hs.evalues(sc[cal_mask], ycal, sc[dep_mask], k=K)
            res[tag] = dict(
                auroc=float(roc_auc_score(ydep, sc[dep_mask])) if np.unique(ydep).size == 2 else None,
                n_features=int(Xall.shape[1]),
                attack_fire=float((e_dep[ydep == 1] > 0).mean()) if (ydep == 1).any() else None,
                benign_to_victim_fire=float((e_dep[ben & vic_dep] > 0).mean()) if (ben & vic_dep).any() else None,
                benign_to_nonvictim_fire=float((e_dep[ben & ~vic_dep] > 0).mean()) if (ben & ~vic_dep).any() else None,
                n_benign_to_victim=int((ben & vic_dep).sum()), n_attacks=int((ydep == 1).sum()))
        res["host_minus_flow_b2v"] = ((res["host"]["benign_to_victim_fire"] or 0)
                                      - (res["flow"]["benign_to_victim_fire"] or 0))
        folds[test] = res
        print(f"  [{test:16s}] AUROC h/f={res['host']['auroc']:.3f}/{res['flow']['auroc']:.3f} "
              f"atk_fire={res['host']['attack_fire']:.3f} feats={len(feat)} | benign->victim "
              f"host={res['host']['benign_to_victim_fire']:.4f} flow={res['flow']['benign_to_victim_fire']:.4f} "
              f"(delta {res['host_minus_flow_b2v']:+.4f}, n={res['host']['n_benign_to_victim']})  [{time.time()-t0:.0f}s]")

    # ---- honest aggregation: signed / weighted / mean-abs delta, and per-fold spread ----
    deltas = np.array([folds[n]["host_minus_flow_b2v"] for n in names])
    wts = np.array([folds[n]["host"]["n_benign_to_victim"] for n in names], float)
    hb = np.array([folds[n]["host"]["benign_to_victim_fire"] or 0 for n in names])
    fb = np.array([folds[n]["flow"]["benign_to_victim_fire"] or 0 for n in names])
    signed_mean = float(deltas.mean())
    weighted_mean = float(np.average(deltas, weights=wts)) if wts.sum() else None
    mean_abs = float(np.abs(deltas).mean())
    median_delta = float(np.median(deltas))
    n_folds_host_higher = int((deltas > 0.005).sum())
    LSPR23_GRAFT = 0.43        # host-detector grafted benign-to-victim fire at the LSPR23 stress window
    summary = dict(
        mean_auroc_host=float(np.mean([folds[n]["host"]["auroc"] for n in names if folds[n]["host"]["auroc"] is not None])),
        mean_attack_fire_host=float(np.mean([folds[n]["host"]["attack_fire"] for n in names if folds[n]["host"]["attack_fire"] is not None])),
        host_benign_to_victim=dict(mean=float(hb.mean()), per_fold={n: float(folds[n]["host"]["benign_to_victim_fire"] or 0) for n in names}, max=float(hb.max())),
        flow_benign_to_victim=dict(mean=float(fb.mean())),
        host_minus_flow_delta=dict(signed_mean=signed_mean, weighted_mean=weighted_mean,
                                   median=median_delta, mean_abs=mean_abs,
                                   n_folds_host_higher=n_folds_host_higher,
                                   per_fold={n: folds[n]["host_minus_flow_b2v"] for n in names}),
        lspr23_grafted_fire=LSPR23_GRAFT,
        max_real_host_fire_vs_grafted=f"{hb.max():.3f} real vs {LSPR23_GRAFT} grafted (~{LSPR23_GRAFT/max(hb.max(),1e-6):.0f}x)")
    # Honest verdict: host conditioning DOES add a real, org-dependent effect (host mean benign->victim
    # >> flow mean; zero on ~half the orgs, up to `hb.max()` on one) -- so NOT "adds nothing". But it
    # is weak/inconsistent and 6-38x below the LSPR23 grafted magnitude, so the graft was an OOD
    # OVERESTIMATE (not a pure artifact), and host conditioning is not the strong defence it appeared.
    far_below_graft = float(hb.max()) < 0.25 * LSPR23_GRAFT
    verdict = (f"host conditioning adds a REAL but WEAK and INCONSISTENT defence against ordinary-to-"
               f"victim traffic on real in-distribution data: it fires zero on ~half the orgs (median "
               f"delta {median_delta:+.4f}) but materially more on {n_folds_host_higher}/{len(names)} "
               f"(host mean benign->victim {hb.mean():.4f} vs flow-only {fb.mean():.4f}, ~{hb.mean()/max(fb.mean(),1e-9):.0f}x; "
               f"max {hb.max():.3f}). This is {LSPR23_GRAFT/max(hb.max(),1e-6):.0f}-{LSPR23_GRAFT/max(hb.mean(),1e-9):.0f}x "
               f"BELOW the LSPR23 grafted {LSPR23_GRAFT}, so the grafted stress-window firing was an "
               f"OUT-OF-DISTRIBUTION OVERESTIMATE, and host conditioning is not the strong defence it "
               f"appeared -- padding substantially transfers. [MODERATE regime; TCP flows; AIT has no "
               f"high-volume flood, which remains open]"
               + ("" if far_below_graft else "  [WARNING: a real host fire approached the graft magnitude]"))

    Hall = np.vstack([s["H"] for s in scen.values()]); yall = np.concatenate([s["y"] for s in scen.values()])
    corr = {nm: float(np.corrcoef(Hall[:, i], yall)[0, 1]) for i, nm in enumerate(t49.FEAT_NAMES)}
    out = dict(
        config=dict(dataset="AIT-LDSv2.0", scenarios=names, design="leave-one-scenario-out",
                    host_features=t49.FEAT_NAMES, k=K, seed=SEED, cal_frac=CAL_FRAC,
                    feature_selection="per-fold from training orgs; identity/label/role/ABSOLUTE-TIME "
                                      "excluded (first,last,req_tm,res_tm are epoch-scale) + epoch guard",
                    fail_def="TCP reset (c_rst_cnt+s_rst_cnt>0)", n_malicious_flows=int(tot_mal),
                    regime="low/moderate (recon+web-exploit+exfil); NO high-volume DDoS flood"),
        host_feature_corr=corr, per_fold=folds, summary=summary, verdict=verdict,
        note=("R7 on AIT (TCP flows): benign-inclusive so the padding-transfer question is measured on "
              "REAL benign-to-victim flows, not a graft (no OOD). Cross-scenario detector (train 7 orgs, "
              "test 1), in-scenario benign calibration, per-fold feature selection with absolute-time "
              "fields excluded, unknown/empty labels dropped. The load-bearing claim: host conditioning "
              "adds a real but WEAK, INCONSISTENT effect over flow-only against ordinary-to-victim "
              "traffic (host mean ~1% vs flow ~0.02%, zero on ~half the orgs, max ~8%), which is 6-38x "
              "below the LSPR23 grafted 43% -- so the graft was an OOD OVERESTIMATE and padding "
              "substantially transfers. Moderate (recon/web-exploit) regime; no high-volume flood."))
    json.dump(out, open("out/t51_R7_ait.json", "w"), indent=1, allow_nan=True)
    print(f"\n  SUMMARY benign->victim: host mean={hb.mean():.5f} vs flow mean={fb.mean():.5f} "
          f"({hb.mean()/max(fb.mean(),1e-9):.0f}x) | median delta={median_delta:+.5f} host higher {n_folds_host_higher}/{len(names)} | "
          f"max host={hb.max():.3f} vs grafted {LSPR23_GRAFT} ({LSPR23_GRAFT/max(hb.max(),1e-6):.0f}x below)")
    print(f"  VERDICT: {verdict}")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t51_R7_ait.json")
    return out


if __name__ == "__main__":
    main()
