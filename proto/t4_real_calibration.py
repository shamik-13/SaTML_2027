"""
TEST 4 (REAL DATA, AIT testbed netflows, tstat format).
THE decisive question: are conformal p-values VALID at the extreme quantiles that
Test 1/2b say the online procedures require (1e-4 .. 1e-6)?
If day-2 benign traffic produces p <= 1e-5 far more often than 1e-5 of the time,
the guarantee is void from drift alone, before any procedure is even chosen.
No labels needed: we test benign-vs-benign across time.
"""
import numpy as np, pandas as pd, re, sys, json
from sklearn.ensemble import IsolationForest

def load(path, nrows=None):
    hdr = open(path).readline().strip()
    names=[]
    for tok in hdr.split(','):
        tok = re.sub(r'^#\d+#','',tok)
        names.append(tok.rsplit(':',1)[0])
    df = pd.read_csv(path, skiprows=1, names=names, nrows=nrows,
                     low_memory=False, on_bad_lines='skip')
    return df

def main():
    df = load("data/nf_wilson/tcp_complete.csv")
    print(f"loaded {len(df):,} flows, {df.shape[1]} cols")
    df = df.sort_values('first').reset_index(drop=True)
    t = pd.to_datetime(df['first'], unit='ms')
    print(f"time span: {t.min()}  ->  {t.max()}   ({(t.max()-t.min()).days} days)")

    # numeric features only, drop identifiers/timestamps
    drop = {'c_ip','s_ip','first','last','c_port','s_port'}
    num = df.select_dtypes(include=[np.number]).columns.difference(list(drop))
    X = df[num].replace([np.inf,-np.inf], np.nan).fillna(0.0).to_numpy(dtype=np.float32)
    print(f"features: {X.shape[1]}")

    n = len(X)
    # chronological thirds: TRAIN | CALIBRATE | TEST  (all benign-dominated)
    i1, i2 = int(0.34*n), int(0.67*n)
    Xtr, Xcal, Xte = X[:i1], X[i1:i2], X[i2:]
    ttr, tcal, tte = t[:i1], t[i1:i2], t[i2:]
    print(f"\ntrain {len(Xtr):,} [{ttr.min()} .. {ttr.max()}]")
    print(f"cal   {len(Xcal):,} [{tcal.min()} .. {tcal.max()}]")
    print(f"test  {len(Xte):,} [{tte.min()} .. {tte.max()}]")

    print("\nfitting IsolationForest on TRAIN ...")
    det = IsolationForest(n_estimators=200, max_samples=min(65536,len(Xtr)),
                          random_state=0, n_jobs=-1).fit(Xtr)
    s_cal = -det.score_samples(Xcal)     # higher = more anomalous
    s_te  = -det.score_samples(Xte)

    cal_sorted = np.sort(s_cal); nc = len(cal_sorted)
    ge = nc - np.searchsorted(cal_sorted, s_te, side='left')
    p  = (1.0 + ge)/(nc+1.0)

    print("\n" + "="*92)
    print("VALIDITY OF CONFORMAL p-VALUES ON HELD-OUT LATER BENIGN TRAFFIC")
    print(f"|C| = {nc:,}  ->  p-value floor = {1/(nc+1):.2e}")
    print("under exchangeability, P(p <= x) should be <= x. Ratio > 1 = ANTI-conservative.")
    print("="*92)
    print(f"{'nominal x':>12} {'observed P(p<=x)':>18} {'ratio obs/nom':>15} {'#events':>9}")
    print("-"*60)
    rows=[]
    for x in [0.5,0.1,0.05,1e-2,1e-3,1e-4,1e-5,1/(nc+1)]:
        obs=(p<=x).mean(); cnt=int((p<=x).sum())
        rows.append(dict(x=float(x),obs=float(obs),ratio=float(obs/x),count=cnt))
        print(f"{x:>12.2e} {obs:>18.3e} {obs/x:>15.2f} {cnt:>9,}")

    # rolling calibration: does recency fix it?
    print("\n" + "="*92)
    print("DOES ROLLING CALIBRATION FIX IT?  (calibrate on the W flows immediately prior)")
    print("="*92)
    print(f"{'window W':>10} {'P(p<=1e-3)/1e-3':>18} {'P(p<=1e-4)/1e-4':>18} {'floor':>10}")
    print("-"*62)
    roll=[]
    s_all = -det.score_samples(X[i1:])          # cal+test contiguous, chronological
    for W in (10_000, 50_000, 137_000):
        rats=[]
        for xlev in (1e-3,1e-4):
            hits=tot=0
            step=max(1, W//4)
            for start in range(0, len(s_all)-W-step, step):
                c=np.sort(s_all[start:start+W]); blk=s_all[start+W:start+W+step]
                if len(blk)==0: break
                g=len(c)-np.searchsorted(c,blk,side='left')
                pp=(1.0+g)/(len(c)+1.0)
                hits+=int((pp<=xlev).sum()); tot+=len(blk)
            rats.append((hits/tot)/xlev if tot else float('nan'))
        roll.append(dict(W=W,ratios=rats))
        print(f"{W:>10,} {rats[0]:>18.2f} {rats[1]:>18.2f} {1/(W+1):>10.2e}")

    json.dump(dict(fixed=rows, rolling=roll), open("out/t4_real.json","w"), indent=1)
    print("\nwrote out/t4_real.json")

main()
