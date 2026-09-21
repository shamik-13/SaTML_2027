import glob
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import h_stream as hs
from h6_procs import Ctx, make_gamma, run_lond
import t49_R7_host_detector as t49
import t51_R7_ait as t51
import t54_ait_suppression as t54

A = t54.A; W0 = t54.W0; K = t54.K; BUCKET_US = t54.BUCKET_US
ORDER = "keyhash"                        # canonical; first-flow is not run (docs/48 sec. 3.1)
GAMMAS = ("poly", "uniform")
ORGS_HOST = ("shaw", "wilson")           # host-conditioned JOINT arm; t54's per-alert host arm runs at
                                         # all eight (round 31), this joint arm stays at the two the
                                         # design note scoped it to (docs/48 sec. 9)
D_TRAJ = 100                             # pad-sampling trajectories per (cell, attacker)
N_MIN = 20                               # minimum templates for a pool to count as available
SIM_CAP = 3_000_000                      # per-episode pad ceiling for the greedy attacker (freeze point)
VALIDATE_SEEDS = (0, 1, 2, 3, 4)         # full-rebuild and regrouping checks on these trajectories
VALIDATE_MAX_PADS = 2_000_000            # skip (and record) a rebuild whose padded stream would exceed this
C_CARRIED = 3                            # the LSPR23-carried multiplier (t75: c = 3 silenced both arms)
CHUNK0 = 64                              # first sampling chunk of the greedy pad search (then doubling)
FUTILE_MIN = 1024                        # pads after which a non-decreasing running pad mean is futile
CHUNK_INEXACT = 256                      # burst size when a chunk cannot be proved exact (see pad_until)


def zero_pad(S, n, tau):
    """Minimum zero-evidence additions r with S/(n+r) < tau (t75.zero_pad, verbatim)."""
    x = S / tau - n
    return int(np.floor(x)) + 1 if x >= 0 else 0


# ------------------------------------------------------------------ organisation preparation ---------
def prepare_org(test, scen, names, common, use_host):
    """Fit the leave-one-org-out detector (t54's chain), score the WHOLE scenario, calibrate
    chronologically, and build the canonical episode stream with a flow -> episode map."""
    s = scen[test]; y = s["y"]; ts = s["ts"]; n = len(y)
    n_ties = int((np.diff(ts) == 0).sum())          # strict-time features handle ties; recorded, not assumed away
    Xf = s["Xnum"][common[test]].to_numpy(dtype=np.float32)

    def feats(o):
        X = scen[o]["Xnum"][common[test]].to_numpy(dtype=np.float32)
        return np.concatenate([X, scen[o]["H"]], axis=1).astype(np.float32) if use_host else X

    Xtr = np.vstack([feats(o) for o in names if o != test])
    ytr = np.concatenate([scen[o]["y"] for o in names if o != test])
    clf = t51.fit(Xtr, ytr)
    score_all = clf.decision_function(feats(test))

    t_split = int(ts[y == 1].min())
    cal_mask = (ts < t_split) & (y == 0); dep_mask = ts >= t_split
    assert cal_mask.sum() >= 2000 and dep_mask.sum() >= 50 and int(y[dep_mask].sum()) >= 3
    e_te, NC, CEIL = t54.build_evalues(score_all[cal_mask], score_all[dep_mask])
    thr = float(np.sort(score_all[cal_mask])[-K])                  # fires iff score STRICTLY exceeds it
    e_all = np.where(score_all > thr, CEIL, 0.0)
    assert np.array_equal(e_all[dep_mask], e_te), "closed-form e-values disagree with t54.build_evalues"

    dep = np.flatnonzero(dep_mask)
    ep = episodes_with_gid(e_te, y[dep], ts[dep], s["src"][dep], s["dst"][dep])
    ref = t54.episodes(e_te, y[dep], ts[dep], s["src"][dep], s["dst"][dep], order=ORDER)
    assert ref["T"] == ep["T"] and np.array_equal(ref["nsz"], ep["nsz"]) and \
        np.array_equal(ref["ismal"], ep["ismal"]) and np.allclose(ref["Ev"], ep["Ev"]), \
        "in-file episode builder disagrees with t54.episodes"

    # attacker-observable insertion time and own arity, per episode (controller-order indexed)
    dep_y = y[dep]; dep_ts = ts[dep]
    mal_last = np.full(ep["T"], -1, dtype=np.int64)
    np.maximum.at(mal_last, ep["gid"][dep_y == 1], dep_ts[dep_y == 1])
    m_atk_g = np.bincount(ep["gid"], weights=dep_y.astype(float), minlength=ep["T"]).astype(np.int64)
    ep["t_atk"] = mal_last[ep["order"]]                    # -1 for non-attacker episodes
    ep["m_atk"] = m_atk_g[ep["order"]]
    assert np.all(ep["t_atk"][ep["ismal"]] >= ep["first_ts"][ep["ismal"]])
    own_t = ep["t_atk"][ep["ismal"]]
    n_tatk_coll = int(own_t.size - np.unique(own_t).size)   # same-timestamp events are ranked by controller position

    isf = np.asarray(s["is_fail"]).astype(bool)
    org = dict(name=test, use_host=use_host, clf=clf, thr=thr, NC=int(NC), CEIL=float(CEIL),
               n=n, y=y, ts=ts, src=s["src"], dst=s["dst"], is_fail=isf, Xf=Xf, H=s["H"],
               score_all=score_all, e_all=e_all, t_split=t_split, dep=dep, ep=ep,
               n_ties=n_ties, n_tatk_collisions=n_tatk_coll,
               dst_ip=s["dst_ip"], victims=set(s["victims"]), md5=_md5(s.get("path", "")))
    org["hosts"] = HostIndex(org)
    org["pools"] = Pools(org)
    pool_sig = {int(j): (int(org["pools"].causal(ep["dst"][j], ep["t_atk"][j])[0].size),
                         int(org["pools"].causal(ep["dst"][j], ep["t_atk"][j])[0].sum()))
                for j in np.flatnonzero(ep["ismal"])}
    org["snapshot"] = dict(cal_scores=score_all[cal_mask].copy(), thr=thr, CEIL=float(CEIL), NC=int(NC),
                           t54_pool=org["pools"].t54_rows.copy(), causal_pools=pool_sig)
    return org


def episodes_with_gid(e_te, y_te, ts_te, src_te, dst_te):
    """t54.episodes with the flow -> episode map, the controller-order permutation and the bucket
    per episode (canonical order only).  Kept structurally identical to t54.episodes."""
    bucket = ts_te // BUCKET_US
    key = np.stack([src_te, dst_te, bucket], axis=1)
    _, gid = np.unique(key, axis=0, return_inverse=True)
    gid = gid.reshape(-1)
    T = int(gid.max() + 1)
    sum_e = np.bincount(gid, weights=e_te, minlength=T)
    nsz = np.bincount(gid, minlength=T).astype(np.int64)
    mal = np.bincount(gid, weights=y_te.astype(float), minlength=T)
    first_ts = np.full(T, np.iinfo(np.int64).max); np.minimum.at(first_ts, gid, ts_te)
    gsrc = np.zeros(T, dtype=np.int64); gsrc[gid] = src_te
    gdst = np.zeros(T, dtype=np.int64); gdst[gid] = dst_te
    gbucket = np.zeros(T, dtype=np.int64); gbucket[gid] = bucket
    ordr = hs.hashed_order(hs.key_hash(gsrc, gdst, gbucket, seed=0), gsrc, gdst, gbucket)
    pos_of_gid = np.empty(T, dtype=np.int64); pos_of_gid[ordr] = np.arange(T)
    b_ord = gbucket[ordr]
    assert np.all(np.diff(b_ord) >= 0), "canonical order must be bucket-batched"
    return dict(T=T, gid=gid, order=ordr, pos_of_gid=pos_of_gid,
                Ev=(sum_e / np.maximum(nsz, 1))[ordr], ismal=(mal > 0)[ordr], nsz=nsz[ordr],
                sum_e=sum_e[ordr], src=gsrc[ordr], dst=gdst[ordr], bucket=b_ord,
                first_ts=first_ts[ordr], pos_of_flow=pos_of_gid[gid])


def _md5(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 24), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


class HostIndex:
    """Per-host sorted views of the WHOLE scenario (calibration included), for exact causal base states
    and for the downstream rows a pad event touches.  Global arrays are strictly time-increasing."""

    def __init__(self, org):
        self._base_cache = {}; self._after_cache = {}
        self.ts = org["ts"]; self.isf = org["is_fail"].astype(np.int64)
        self.src = org["src"]; self.dst = org["dst"]
        self.by_src = self._index(self.src); self.by_dst = self._index(self.dst)
        dep = org["dep"]; self.dep = dep
        # exact strict-before fail counts for deployment rows (float32 H would lose integers)
        self.src_fail_before = np.array([self._fail_before(self.by_src, h, t)
                                         for h, t in zip(self.src[dep], self.ts[dep])], dtype=np.int64)
        self.dst_fail_before = np.array([self._fail_before(self.by_dst, h, t)
                                         for h, t in zip(self.dst[dep], self.ts[dep])], dtype=np.int64)
        H = org["H"][dep]
        assert np.array_equal(np.round(H[:, 0] * H[:, 2]).astype(np.int64), self.src_fail_before) and \
            np.array_equal(np.round(H[:, 3] * H[:, 5]).astype(np.int64), self.dst_fail_before), \
            "exact fail counts disagree with the stored host features"
        # deployment rows per host, sorted by time (for downstream offsets)
        self.dep_by_src = self._index(self.src[dep], base=dep)
        self.dep_by_dst = self._index(self.dst[dep], base=dep)

    def _index(self, host, base=None):
        order = np.argsort(host, kind="stable")            # stable keeps time order within a host
        hs_ = host[order]
        starts = np.flatnonzero(np.r_[True, hs_[1:] != hs_[:-1]])
        ends = np.r_[starts[1:], len(hs_)]
        rows = order if base is None else np.arange(len(host))[order]   # local (dep) indices if base
        out = {}
        for h, a, b in zip(hs_[starts], starts, ends):
            r = rows[a:b]
            gts = self.ts[base[r]] if base is not None else self.ts[r]
            fc = np.cumsum(self.isf[base[r]] if base is not None else self.isf[r])
            out[int(h)] = (r, gts, fc)
        return out

    def _fail_before(self, index, h, t):
        r, gts, fc = index[int(h)]
        i = int(np.searchsorted(gts, t, side="left"))     # strictly earlier
        return int(fc[i - 1]) if i > 0 else 0

    def base_state(self, side, h, t):
        """Original-stream counts of host h on `side` ('src'|'dst') with ts <= t: (count, fails, peers).

        Cached on (side, host, t): it depends only on the ORIGINAL stream, so it is the same for every
        pad of an episode and for every trajectory.  Without the cache the distinct-peer count is a
        `np.unique` over tens of thousands of rows per pad, which dominates the host arm."""
        key = (side, int(h), int(t))
        hit = self._base_cache.get(key)
        if hit is not None:
            return hit
        index = self.by_src if side == "src" else self.by_dst
        other = self.dst if side == "src" else self.src
        r, gts, fc = index[int(h)]
        i = int(np.searchsorted(gts, t, side="right"))    # <= t
        out = (i, (int(fc[i - 1]) if i > 0 else 0), int(np.unique(other[r[:i]]).size))
        self._base_cache[key] = out
        return out

    def dep_rows_after(self, side, h, t):
        """Deployment-local row indices of host h on `side` with ts > t (strictly later).  Cached: the
        ORIGINAL stream fixes it, so it is the same for every pad of an episode."""
        key = (side, int(h), int(t))
        hit = self._after_cache.get(key)
        if hit is not None:
            return hit
        index = self.dep_by_src if side == "src" else self.dep_by_dst
        if int(h) not in index:
            out = np.empty(0, dtype=np.int64)
        else:
            r, gts, _ = index[int(h)]
            out = r[int(np.searchsorted(gts, t, side="right")):]
        self._after_cache[key] = out
        return out


class Pools:
    """Template pools.  causal(j): benign flows to j's victim with ts < t_atk(j) over the whole
    scenario.  t54(): benign deployment flows to ANY attacked victim (t54's pad_mask)."""

    def __init__(self, org):
        y = org["y"]; dst = org["dst"]; ts = org["ts"]
        ben = np.flatnonzero(y == 0)
        order = np.argsort(dst[ben], kind="stable")
        b = ben[order]; d = dst[b]
        starts = np.flatnonzero(np.r_[True, d[1:] != d[:-1]]); ends = np.r_[starts[1:], len(d)]
        self.ben_by_dst = {int(d[a]): (b[a:e], ts[b[a:e]]) for a, e in zip(starts, ends)}
        self.t_split = org["t_split"]
        dep = org["dep"]
        vic = np.array([ip in org["victims"] for ip in org["dst_ip"][dep]])
        self.t54_rows = dep[(y[dep] == 0) & vic]

    def causal(self, victim, t_atk):
        if int(victim) not in self.ben_by_dst:
            return np.empty(0, dtype=np.int64), 0, False
        rows, rts = self.ben_by_dst[int(victim)]
        i = int(np.searchsorted(rts, t_atk, side="left"))      # strictly before t_atk
        rows = rows[:i]; rts = rts[:i]
        dep_rows = rows[rts >= self.t_split]
        if dep_rows.size >= N_MIN:
            return dep_rows, int(dep_rows.size), False
        return rows, int(dep_rows.size), True                  # extended with calibration templates


# ------------------------------------------------------------------ one attacked trajectory -----------
class Trajectory:

    def __init__(self, org, seed, pool_kind):
        self.org = org; ep = org["ep"]; self.ep = ep; T = ep["T"]
        self.seed = seed; self.pool_kind = pool_kind
        self.pad_cnt = np.zeros(T, dtype=np.int64); self.pad_e = np.zeros(T); self.pad_fail = np.zeros(T, dtype=np.int64)
        self.pad_fired = np.zeros(T, dtype=np.int64)          # pads of j that carried evidence M
        self.sum_e_orig = ep["sum_e"].copy()                    # live evidence of ORIGINAL flows
        n_dep = len(org["dep"])
        self.e_cur = org["e_all"][org["dep"]].copy()
        self.off = np.zeros((n_dep, 4), dtype=np.int64)         # src_cnt, src_fail, dst_cnt, dst_fail
        self.dirty = np.zeros(n_dep, dtype=bool)
        self.events_src = {}; self.events_dst = {}              # host -> list of (t_atk, r, fails)
        self.frozen = set(); self.futile = set(); self.unavailable = set(); self.extended = set()
        self.n_inexact_bursts = 0
        self.templates = {}                                     # j -> list of template rows (validation)
        self.ctx_log = {}                                       # j -> list of pad context vectors (validation)
        self.rngs = {}
        self.pools = {}
        for j in np.flatnonzero(ep["ismal"]):
            if pool_kind == "causal":
                rows, n_dep_pool, extended = org["pools"].causal(ep["dst"][j], ep["t_atk"][j])
                if rows.size < N_MIN:
                    self.unavailable.add(int(j))
                elif extended:
                    self.extended.add(int(j))
            else:
                rows = org["pools"].t54_rows
                if rows.size < N_MIN:
                    self.unavailable.add(int(j))
            self.pools[int(j)] = rows
        self.log_events = []                                    # (j, r, fails, sum_e_pads) in time order
        self._own_rows = {}
        self.exact_batch = {}
        self.exact_level = {}
        for j in np.flatnonzero(ep["ismal"]):
            j = int(j)
            self.exact_batch[j] = (not org["use_host"]) or self.n_after_t_atk(j) == 0
            if not org["use_host"]:
                self.exact_level[j] = True
            else:
                touched = np.concatenate([org["hosts"].dep_rows_after("src", int(ep["src"][j]), int(ep["t_atk"][j])),
                                          org["hosts"].dep_rows_after("dst", int(ep["dst"][j]), int(ep["t_atk"][j]))])
                pos = ep["pos_of_flow"][touched] if touched.size else np.empty(0, dtype=np.int64)
                self.exact_level[j] = not bool(np.any((pos < j) & (ep["bucket"][pos] == ep["bucket"][j]))) \
                    if pos.size else True

    def own_rows(self, j):
        """Deployment-local rows of episode j (cached)."""
        j = int(j)
        if j not in self._own_rows:
            self._own_rows[j] = np.flatnonzero(self.ep["pos_of_flow"] == j)
        return self._own_rows[j]

    def n_after_t_atk(self, j):
        """Original flows of episode j strictly after the attacker's own last flow (co-resident benign
        traffic that a pad event would re-score)."""
        j = int(j); rows = self.own_rows(j)
        return int((self.org["ts"][self.org["dep"][rows]] > self.ep["t_atk"][j]).sum())

    def rng(self, j):
        if j not in self.rngs:
            self.rngs[j] = np.random.default_rng([self.seed, 76, int(j)])
        return self.rngs[j]

    # -- pad contexts and evidence -------------------------------------------------------------
    def pad_contexts(self, j, k0, fails_b):
        """Host-feature vectors seen by pads k0+1 .. k0+B of episode j (B = len(fails_b)), given the
        pads' own sampled fail flags (pad k sees pads 1..k-1's fails)."""
        ep = self.ep; org = self.org; hx = org["hosts"]
        Aj, Vj, t = int(ep["src"][j]), int(ep["dst"][j]), int(ep["t_atk"][j])
        sc, sf, sd = hx.base_state("src", Aj, t)
        dc, df, dd = hx.base_state("dst", Vj, t)
        for (te, r, f, pj) in self.events_src.get(Aj, []):
            if te < t or (te == t and pj < j): sc += r; sf += f
        for (te, r, f, pj) in self.events_dst.get(Vj, []):
            if te < t or (te == t and pj < j): dc += r; df += f
        B = len(fails_b)
        k = k0 + np.arange(1, B + 1)                             # this pad's index within j's event
        prior = self.pad_fail[j] + np.cumsum(fails_b) - fails_b    # fails of pads 1..k-1
        scnt = sc + (k - 1); dcnt = dc + (k - 1)
        ctx = np.column_stack([scnt, np.full(B, sd), (sf + prior) / np.maximum(scnt, 1),
                               dcnt, np.full(B, dd), (df + prior) / np.maximum(dcnt, 1)]).astype(np.float32)
        return ctx

    def pad_evidence(self, j, rows, k0):
        """Evidence (0 or M) and fail flags of templates `rows` appended as pads k0+1.. of episode j."""
        org = self.org
        fails = org["is_fail"][rows].astype(np.int64)
        if not org["use_host"]:
            return org["e_all"][rows], fails, None
        ctx = self.pad_contexts(j, k0, fails)
        X = np.concatenate([org["Xf"][rows], ctx], axis=1).astype(np.float32)
        sc = org["clf"].decision_function(X)
        return np.where(sc > org["thr"], org["CEIL"], 0.0), fails, ctx

    # -- applying pads ------------------------------------------------------------------------
    def append_pads(self, j, rows, e, fails, ctx):
        """Commit pads (templates `rows`) to episode j: evidence, counts, downstream offsets, events."""
        j = int(j); r = len(rows)
        if r == 0:
            return
        ep = self.ep; org = self.org; hx = org["hosts"]
        Aj, Vj, t = int(ep["src"][j]), int(ep["dst"][j]), int(ep["t_atk"][j])
        f = int(fails.sum())
        self.pad_cnt[j] += r; self.pad_e[j] += float(e.sum()); self.pad_fail[j] += f
        self.pad_fired[j] += int((e > 0).sum())
        if self.seed in VALIDATE_SEEDS:
            self.templates.setdefault(j, []).extend(int(x) for x in rows)
            if ctx is not None:
                self.ctx_log.setdefault(j, []).append(ctx)
        for d, h in ((self.events_src, Aj), (self.events_dst, Vj)):
            lst = d.setdefault(h, [])
            for i, (te, rr, ff, pj) in enumerate(lst):
                if pj == j:                                  # one entry per (host, episode): accumulate
                    lst[i] = (te, rr + r, ff + f, pj); break
            else:
                lst.append((t, r, f, j))
        self.log_events.append((j, r, f, float(e.sum())))
        if org["use_host"]:
            rs = hx.dep_rows_after("src", Aj, t)
            if rs.size:
                self.off[rs, 0] += r; self.off[rs, 1] += f; self.dirty[rs] = True
            rd = hx.dep_rows_after("dst", Vj, t)
            if rd.size:
                self.off[rd, 2] += r; self.off[rd, 3] += f; self.dirty[rd] = True

    def rescore(self, mask=None):
        """Re-score dirty deployment rows (optionally restricted by a dep-row mask) with their lazy
        host-feature offsets and update the live original evidence of their episodes."""
        org = self.org
        if not org["use_host"]:
            return 0
        sel = self.dirty if mask is None else (self.dirty & mask)
        rows = np.flatnonzero(sel)
        if rows.size == 0:
            return 0
        Hn = self.features(rows)
        X = np.concatenate([org["Xf"][org["dep"][rows]], Hn], axis=1).astype(np.float32)
        sc = org["clf"].decision_function(X)
        e_new = np.where(sc > org["thr"], org["CEIL"], 0.0)
        delta = e_new - self.e_cur[rows]
        self.e_cur[rows] = e_new
        if np.any(delta):
            g = self.ep["pos_of_flow"][rows]
            np.add.at(self.sum_e_orig, g, delta)
        self.dirty[rows] = False
        return int(rows.size)

    def features(self, rows):
        """Lazy host features of deployment rows `rows` under the current pad events."""
        org = self.org; hx = org["hosts"]
        H = org["H"][org["dep"][rows]].astype(np.float64)
        off = self.off[rows]
        scnt = H[:, 0] + off[:, 0]; dcnt = H[:, 3] + off[:, 2]
        sfail = hx.src_fail_before[rows] + off[:, 1]; dfail = hx.dst_fail_before[rows] + off[:, 3]
        return np.column_stack([scnt, H[:, 1], sfail / np.maximum(scnt, 1),
                                dcnt, H[:, 4], dfail / np.maximum(dcnt, 1)]).astype(np.float32)

    def ev(self, j):
        return (self.sum_e_orig[j] + self.pad_e[j]) / (self.ep["nsz"][j] + self.pad_cnt[j])

    def ev_all(self):
        return (self.sum_e_orig + self.pad_e) / (self.ep["nsz"] + self.pad_cnt)

    # -- greedy pad search for one episode at one live level -------------------------------------
    def pad_until(self, j, lvl):
        j = int(j); thr = 1.0 / lvl
        pool = self.pools[j]; rng = self.rng(j)
        exact = self.exact_batch[j] and self.exact_level[j]
        B = CHUNK0 if exact else CHUNK_INEXACT
        while True:
            room = SIM_CAP - int(self.pad_cnt[j])
            if room <= 0:
                self.frozen.add(j); return "frozen"
            n_sent = int(self.pad_cnt[j])
            if n_sent >= FUTILE_MIN and self.pad_e[j] / n_sent >= thr:
                self.frozen.add(j); self.futile.add(j); return "frozen"
            B = min(B, room)
            rows = rng.choice(pool, size=B, replace=True)
            e, fails, ctx = self.pad_evidence(j, rows, int(self.pad_cnt[j]))
            S0 = self.sum_e_orig[j] + self.pad_e[j]; m0 = self.ep["nsz"][j] + self.pad_cnt[j]
            mean = (S0 + np.cumsum(e)) / (m0 + np.arange(1, B + 1))
            hit = np.flatnonzero(mean < thr)
            if hit.size:
                r = int(hit[0]) + 1
                self.append_pads(j, rows[:r], e[:r], fails[:r], None if ctx is None else ctx[:r])
                return "suppressed"
            self.append_pads(j, rows, e, fails, ctx)              # the whole chunk was really sent
            if not exact:
                self.n_inexact_bursts += 1
                return "step"                        # bounded burst: the caller re-scores and re-tests
            B *= 2


# ------------------------------------------------------------------ controller ------------------------
def test_positions(tr, positions, R, g1):
    """e-LOND over `positions` (controller order) from rejection count R; returns fired mask (per
    position), live level per position, and R after.  Mirrors h6_procs.run_lond exactly."""
    CEIL = tr.org["CEIL"]
    fired = np.zeros(len(positions), dtype=bool); lvl_at = np.zeros(len(positions))
    for i, p in enumerate(positions):
        lvl = A * g1[p + 1] * (R + 1); lvl_at[i] = lvl
        if lvl <= 0 or CEIL < 1.0 / lvl:                    # Ctx.infeasible
            continue
        if tr.ev(p) >= 1.0 / lvl:
            fired[i] = True; R += 1
    return fired, lvl_at, R


def clean_run(org, g1):
    ep = org["ep"]
    ctx = Ctx(ep["Ev"], ep["ismal"], org["CEIL"], alpha=A, w0=W0)
    fired = np.zeros(ep["T"], dtype=bool)
    rej, tp, sil, _ = run_lond(ctx, g1, fired=fired)
    R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(float)
    lvl = A * g1[np.arange(1, ep["T"] + 1)] * (R_before + 1.0)
    return fired, lvl, dict(rejections=int(rej), true=int(tp), false_discoveries=int(rej - tp),
                            silent=int(sil))


def bucket_ranges(ep):
    b = ep["bucket"]
    starts = np.flatnonzero(np.r_[True, b[1:] != b[:-1]]); ends = np.r_[starts[1:], len(b)]
    return list(zip(starts, ends))


# ------------------------------------------------------------------ attackers --------------------------
def greedy_attack(org, g1, seed, pool_kind):
    """K1 oracle: bucket fixed point (docs/48 sec. 3.4).  Returns the trajectory and per-position
    fired mask / live level of the attacked run."""
    tr = Trajectory(org, seed, pool_kind); ep = tr.ep; T = ep["T"]
    fired = np.zeros(T, dtype=bool); lvl_at = np.zeros(T); R = 0; steps = 0
    own = ep["ismal"]
    dep_bucket = ep["bucket"][ep["pos_of_flow"]]              # bucket of each deployment row
    for a, b in bucket_ranges(ep):
        positions = np.arange(a, b)
        own_here = positions[own[a:b]]
        F = set(int(j) for j in own_here if int(j) in tr.unavailable)
        in_bucket = dep_bucket == ep["bucket"][a]
        while True:
            tr.rescore(in_bucket)                              # rows this bucket owns that pads touched
            f, l, Rn = test_positions(tr, positions, R, g1)
            cands = [int(j) for j, fj in zip(positions, f) if fj and own[j] and int(j) not in F
                     and int(j) not in tr.frozen]
            if not cands:
                break
            j = min(cands, key=lambda q: ep["t_atk"][q])
            steps += 1
            if tr.pad_until(j, l[j - a]) == "frozen":         # only a SIM_CAP freeze ends the attempt
                F.add(j)
        fired[a:b] = f; lvl_at[a:b] = l; R = Rn
    tr.rescore()                                               # anything left dirty in later buckets (none)
    tr.steps = steps
    return tr, fired, lvl_at


def multiplier_attack(org, seed, c, variant, pool_kind="causal"):
    """K0 state-free: (c-1)*m_x pads on EVERY own episode at its t_atk, in time order, no controller
    read.  variant 'theory' uses m_total, 'operational' uses m_atk.  Returns the trajectory."""
    tr = Trajectory(org, seed, pool_kind); ep = tr.ep
    own = np.flatnonzero(ep["ismal"])
    for j in own[np.argsort(ep["t_atk"][own], kind="stable")]:
        j = int(j)
        if j in tr.unavailable:
            continue
        m_x = int(ep["nsz"][j]) if variant == "oracle_m_total" else int(ep["m_atk"][j])
        r = (c - 1) * m_x
        rng = tr.rng(j); pool = tr.pools[j]
        done = 0
        while done < r:                                        # chunked so contexts stay exact
            B = min(4096, r - done)
            rows = rng.choice(pool, size=B, replace=True)
            e, fails, ctx = tr.pad_evidence(j, rows, int(tr.pad_cnt[j]))
            tr.append_pads(j, rows, e, fails, ctx)
            done += B
    tr.rescore()
    return tr


def evaluate(tr, g1, base_fired, base_lvl, budget_of):
    """Run the controller over the padded stream, classify surviving own baseline alerts, count
    created alerts.  `budget_of(j)` gives B_j for the class rule."""
    ep = tr.ep; T = ep["T"]; own = ep["ismal"]
    Ev = tr.ev_all()
    ctx = Ctx(Ev, own, tr.org["CEIL"], alpha=A, w0=W0)
    fired = np.zeros(T, dtype=bool); run_lond(ctx, g1, fired=fired)
    R_before = np.concatenate([[0], np.cumsum(fired)[:-1]]).astype(float)
    lvl = A * g1[np.arange(1, T + 1)] * (R_before + 1.0)
    f_walk, l_walk, _ = test_positions(tr, np.arange(T), 0, g1)      # in-file walk on the SAME stream
    assert np.array_equal(f_walk, fired) and np.allclose(l_walk, lvl), \
        "K0 attacked run: test_positions disagrees with run_lond"
    return classify(tr, g1, fired, lvl, base_fired, budget_of)


def classify(tr, g1, fired, lvl, base_fired, budget_of):
    ep = tr.ep; T = ep["T"]; own = ep["ismal"]
    base_own = np.flatnonzero(base_fired & own)
    remaining_own = np.flatnonzero(fired & base_fired & own)
    suppressed_own = int(base_own.size - remaining_own.size)
    classes = dict(pool_unavailable=0, structural=0, cascade=0, pad_fired=0)
    per = []
    for j in remaining_own:
        j = int(j)
        S_live = float(tr.sum_e_orig[j]); m = int(ep["nsz"][j])
        need_R0 = zero_pad(S_live, m, 1.0 / (A * g1[j + 1]))
        need_live = zero_pad(S_live, m, 1.0 / lvl[j]) if lvl[j] > 0 else None
        B = budget_of(j)
        if j in tr.unavailable:
            cls = "pool_unavailable"
        elif B < need_R0:
            cls = "structural"
        elif need_live is not None and B < need_live:
            cls = "cascade"
        else:
            cls = "pad_fired"
        classes[cls] += 1
        per.append(dict(pos=j, cls=cls, pads=int(tr.pad_cnt[j]), pads_fired=int(tr.pad_fired[j]),
                        need_R0=need_R0, need_live=need_live, budget=int(B) if B is not None else None,
                        m_total=m, m_atk=int(ep["m_atk"][j]), evidence_shift=bool(S_live != ep["sum_e"][j]),
                        R_at=int(round(lvl[j] / (A * g1[j + 1]) - 1)) if g1[j + 1] > 0 else None))
    created = fired & ~base_fired
    nonown_fired = np.flatnonzero(fired & ~own)
    first_nonown = int(nonown_fired[0]) if nonown_fired.size else None
    mixed = ep["m_atk"] < ep["nsz"]
    ua = tr.unavailable & set(np.flatnonzero(own).tolist())
    ext = tr.extended & set(np.flatnonzero(own).tolist())
    return dict(remaining_own=int(remaining_own.size), classes=classes, per_survivor=per,
                remaining_own_mixed=int((fired & base_fired & own & mixed).sum()),
                remaining_nonown=int((fired & base_fired & ~own).sum()),
                created_own=int((created & own).sum()), created_nonown=int((created & ~own).sum()),
                nonown_alerts_total=int((fired & ~own).sum()), rejections=int(fired.sum()),
                own_alerts=int((fired & own).sum()), total_pads=int(tr.pad_cnt.sum()),
                pads_fired=int(tr.pad_fired.sum()), pads_on_survivors=int(tr.pad_cnt[remaining_own].sum()),
                pads_on_extended=int(tr.pad_cnt[sorted(ext)].sum()) if ext else 0,
                own_baseline_alerts=int(base_own.size), suppressed_own=suppressed_own,
                n_futile=len(tr.futile & set(np.flatnonzero(own).tolist())),
                n_inexact_bursts=int(tr.n_inexact_bursts),
                attempted_own=int((tr.pad_cnt[np.flatnonzero(own)] > 0).sum()),
                spared_own=int(sum(1 for j in np.flatnonzero(own) if tr.pad_cnt[j] == 0 and base_fired[j])),
                pads_on_failures=int(tr.pad_cnt[remaining_own].sum()),
                extended_suppressed=int(sum(bool(base_fired[j] and not fired[j]) for j in ext)),
                first_nonown_pos=first_nonown, n_unavailable=len(ua), n_extended=len(ext),
                n_own_padded=int((tr.pad_cnt[np.flatnonzero(own)] > 0).sum()),
                extended_remaining=int(sum(bool(fired[j] and base_fired[j]) for j in ext)),
                extended_baseline_alerts=int(sum(bool(base_fired[j]) for j in ext)),
                pads_per_own_episode=[int(x) for x in tr.pad_cnt[np.flatnonzero(own)]], fired=fired)


# ------------------------------------------------------------------ validation -------------------------
def validate_rebuild(tr):
    org = tr.org; ep = tr.ep
    total = int(tr.pad_cnt.sum())
    if total == 0:
        return dict(ok=True, note="no pads")
    if total > VALIDATE_MAX_PADS:
        return dict(ok=False, skipped=True,
                    note=f"NOT VALIDATED: {total} pads exceed VALIDATE_MAX_PADS")
    ts = org["ts"]; ts_min = int(ts.min())
    # pads sharing one original timestamp are serialised by controller position, then k
    js = sorted(tr.templates, key=lambda q: (int(ep["t_atk"][q]), q))
    rank0 = {}; per_t = {}
    for j in js:
        t_ = int(ep["t_atk"][j]); rank0[j] = per_t.get(t_, 0); per_t[t_] = rank0[j] + int(tr.pad_cnt[j])
    P = max(per_t.values())
    scale = P + 1
    assert (int(ts.max()) - ts_min) * scale + P < 2**63 - 1, "rescaled timestamps would overflow int64"
    ts_o = (ts - ts_min) * scale
    pad_src, pad_dst, pad_ts, pad_fail = [], [], [], []
    for j in js:
        rows = tr.templates[j]
        r = len(rows); assert r == tr.pad_cnt[j]
        pad_src.append(np.full(r, ep["src"][j])); pad_dst.append(np.full(r, ep["dst"][j]))
        pad_ts.append((int(ep["t_atk"][j]) - ts_min) * scale + rank0[j] + np.arange(1, r + 1))
        pad_fail.append(org["is_fail"][np.asarray(rows)].astype(np.float64))
    src2 = np.concatenate([org["src"]] + pad_src); dst2 = np.concatenate([org["dst"]] + pad_dst)
    ts2 = np.concatenate([ts_o] + pad_ts); isf2 = np.concatenate([org["is_fail"].astype(np.float64)] + pad_fail)
    perm = np.argsort(ts2, kind="mergesort")
    assert np.unique(np.concatenate(pad_ts)).size == len(perm) - len(ts_o) and \
        not np.isin(np.concatenate(pad_ts), ts_o).any(), "a pad shares a rescaled timestamp with another row"
    H2 = t49.build_host_features(src2[perm], dst2[perm], ts2[perm], isf2[perm])
    inv = np.empty_like(perm); inv[perm] = np.arange(len(perm))
    n = org["n"]
    H_dep_rebuilt = H2[inv[org["dep"]]]
    H_dep_lazy = tr.features(np.arange(len(org["dep"])))
    cnt_ok = np.array_equal(H_dep_rebuilt[:, [0, 1, 3, 4]], H_dep_lazy[:, [0, 1, 3, 4]])
    frac_ok = np.allclose(H_dep_rebuilt[:, [2, 5]], H_dep_lazy[:, [2, 5]], atol=2e-6, rtol=1e-5)
    # pad contexts: compare in the order the pads were scored
    pad_ok = True; n_pad_checked = 0
    if org["use_host"]:
        start = n
        for j in js:
            rows = tr.templates[j]; r = len(rows)
            ctx = np.concatenate(tr.ctx_log[j], axis=0)
            Hp = H2[inv[start:start + r]]
            pad_ok &= np.array_equal(Hp[:, [0, 1, 3, 4]], ctx[:, [0, 1, 3, 4]]) and \
                np.allclose(Hp[:, [2, 5]], ctx[:, [2, 5]], atol=2e-6, rtol=1e-5)
            n_pad_checked += r; start += r
    # scores: every deployment row's evidence under the rebuilt features equals the lazy e_cur
    if org["use_host"]:
        X = np.concatenate([org["Xf"][org["dep"]], H_dep_rebuilt], axis=1).astype(np.float32)
        e_re = np.where(org["clf"].decision_function(X) > org["thr"], org["CEIL"], 0.0)
        e_ok = np.array_equal(e_re, tr.e_cur)
    else:
        e_ok = True
    # pad EVIDENCE, independently: score the rebuilt pad rows and compare each episode's pad sum
    pad_e_ok = True
    if org["use_host"]:
        start = n
        for j in js:
            rows = tr.templates[j]; r = len(rows)
            Xp = np.concatenate([org["Xf"][np.asarray(rows)], H2[inv[start:start + r]]], axis=1).astype(np.float32)
            e_p = np.where(org["clf"].decision_function(Xp) > org["thr"], org["CEIL"], 0.0)
            pad_e_ok &= bool(abs(float(e_p.sum()) - float(tr.pad_e[j])) <= 1e-6 * max(1.0, float(tr.pad_e[j])))
            pad_e_ok &= bool(int((e_p > 0).sum()) == int(tr.pad_fired[j]))
            start += r
    ok = bool(cnt_ok and frac_ok and pad_ok and e_ok and pad_e_ok)
    return dict(ok=ok, skipped=False, counts_equal=bool(cnt_ok), fracs_close=bool(frac_ok),
                pad_contexts_equal=bool(pad_ok), evidence_equal=bool(e_ok), pad_evidence_equal=bool(pad_e_ok),
                n_pads=total, n_pad_contexts_checked=n_pad_checked)


def validate_regroup(tr):
    org = tr.org; ep = tr.ep; dep = org["dep"]
    y = org["y"][dep]; ts = org["ts"][dep]; src = org["src"][dep]; dst = org["dst"][dep]
    e = tr.e_cur
    pj = np.flatnonzero(tr.pad_cnt > 0)
    rep = np.repeat(pj, tr.pad_cnt[pj])
    pad_e = np.concatenate([np.repeat(tr.pad_e[j] / tr.pad_cnt[j], tr.pad_cnt[j]) for j in pj]) if pj.size else np.empty(0)
    ts2 = np.concatenate([ts, ep["t_atk"][rep]])
    perm = np.argsort(ts2, kind="mergesort")
    padded = (np.concatenate([e, pad_e])[perm], np.concatenate([y, np.zeros(len(rep), dtype=y.dtype)])[perm],
              ts2[perm], np.concatenate([src, ep["src"][rep]])[perm], np.concatenate([dst, ep["dst"][rep]])[perm])
    assert np.all(np.diff(padded[2]) >= 0)
    ep2 = t54.episodes(*padded, order=ORDER)
    ok = ep2["T"] == ep["T"] and np.array_equal(ep2["src"], ep["src"]) and np.array_equal(ep2["dst"], ep["dst"]) \
        and np.array_equal(ep2["nsz"], ep["nsz"] + tr.pad_cnt) and np.array_equal(ep2["ismal"], ep["ismal"]) \
        and np.allclose(ep2["Ev"], tr.ev_all(), rtol=1e-9, atol=1e-6)
    ep3 = episodes_with_gid(*padded)
    first_ok = bool(np.array_equal(ep3["first_ts"], ep["first_ts"]))
    key_ok = bool(np.array_equal(ep3["bucket"], ep["bucket"]) and
                  np.array_equal(ep3["src"], ep["src"]) and np.array_equal(ep3["dst"], ep["dst"]) and
                  np.array_equal(ep3["nsz"], ep2["nsz"]))
    return dict(ok=bool(ok and first_ok and key_ok), first_ts_unchanged=first_ok,
                bucket_keys_unchanged=key_ok, n_pads=int(len(rep)))


# ------------------------------------------------------------------ summaries --------------------------
def _q(x):
    x = np.asarray(x, dtype=float)
    return dict(median=float(np.median(x)), p5=float(np.percentile(x, 5)), p95=float(np.percentile(x, 95)),
                min=float(x.min()), max=float(x.max()), mean=float(x.mean()))


def summarise(results):
    """Summaries over trajectories of `classify` outputs (fired masks dropped)."""
    keys = ("remaining_own", "remaining_own_mixed", "remaining_nonown", "created_own", "created_nonown",
            "nonown_alerts_total", "rejections", "own_alerts", "total_pads", "pads_fired",
            "pads_on_survivors", "pads_on_extended", "n_own_padded", "extended_remaining",
            "suppressed_own", "attempted_own", "spared_own", "pads_on_failures", "extended_suppressed",
            "n_futile", "n_inexact_bursts")
    out = {k: _q([r[k] for r in results]) for k in keys}
    out["p_all_silenced"] = float(np.mean([r["remaining_own"] == 0 for r in results]))
    out["classes_mean"] = {c: float(np.mean([r["classes"][c] for r in results]))
                           for c in ("pool_unavailable", "structural", "cascade", "pad_fired")}
    out["classes_any"] = {c: int(sum(r["classes"][c] > 0 for r in results))
                          for c in ("pool_unavailable", "structural", "cascade", "pad_fired")}
    out["n_unavailable"] = results[0]["n_unavailable"]; out["n_extended"] = results[0]["n_extended"]
    out["extended_baseline_alerts"] = results[0]["extended_baseline_alerts"]
    out["pads_per_own_episode_median"] = ([float(x) for x in
                                           np.median([r["pads_per_own_episode"] for r in results], axis=0)]
                                          if results[0]["pads_per_own_episode"] else [])
    # conservation, asserted per trajectory: own baseline alerts = suppressed + the four classes
    for r in results:
        assert r["suppressed_own"] + sum(r["classes"].values()) == r["own_baseline_alerts"], \
            f"outcome classes do not conserve: {r['suppressed_own']} + {r['classes']} != {r['own_baseline_alerts']}"
    out["conservation_asserted"] = True
    out["denominators"] = dict(own_episodes=len(results[0]["pads_per_own_episode"]),
                               own_baseline_alerts=results[0]["own_baseline_alerts"],
                               pool_unavailable_own=results[0]["n_unavailable"],
                               pool_extended_own=results[0]["n_extended"],
                               note="medians are over ALL trajectories; pad distributions are over ALL "
                                    "own episodes, not only the suppressed ones")
    out["first_nonown_pos_seed0"] = results[0]["first_nonown_pos"]
    out["seed0_survivors"] = results[0]["per_survivor"]
    out["n_traj"] = len(results)
    return out


def precommit(org):
    T = org["ep"]["T"]; rho = org["CEIL"] * A / T
    return dict(T=int(T), NC=int(org["NC"]), CEIL=float(org["CEIL"]), rho=float(rho),
                c_int=int(np.floor(rho)) + 1, c_carried=C_CARRIED, alpha=A, k=K,
                n_own_episodes=int(org["ep"]["ismal"].sum()), d_traj=D_TRAJ, seeds=[0, D_TRAJ - 1],
                validate_seeds=list(VALIDATE_SEEDS), n_min=N_MIN, sim_cap=SIM_CAP,
                input_md5=org["md5"], written_before_attacks=True)


def run_org(org, t67_rows):
    """All arms for one prepared organisation."""
    ep = org["ep"]; T = ep["T"]; name = org["name"]; tag = "host" if org["use_host"] else "flow"
    rho = org["CEIL"] * A / T; c_int = int(np.floor(rho)) + 1
    out = dict(org=name, arm=tag, T=T, NC=org["NC"], CEIL=org["CEIL"], rho=float(rho), c_int=c_int,
               pool_labels=dict(causal="primary: benign flows to the victim strictly before t_atk",
                                t54="NON-CAUSAL ORACLE comparability pool: t54's whole-deployment "
                                    "benign-to-victim rows, which include flows after the pad time"),
               n_timestamp_ties=org["n_ties"], n_tatk_collisions=org["n_tatk_collisions"],
               n_own=int(ep["ismal"].sum()), n_mixed=int((ep["m_atk"] < ep["nsz"])[ep["ismal"]].sum()),
               md5=org["md5"], baseline={}, greedy={}, greedy_t54pool={}, multiplier={}, validation=[])
    g = {k: make_gamma(k, T)[0] for k in GAMMAS}
    base = {}
    for k in GAMMAS:
        fired, lvl, summ = clean_run(org, g[k])
        tr_clean = Trajectory(org, 0, "causal")            # in-file walk must agree with run_lond
        f_walk, l_walk, _ = test_positions(tr_clean, np.arange(T), 0, g[k])
        assert np.array_equal(f_walk, fired) and np.allclose(l_walk, lvl), \
            f"{name}: test_positions disagrees with run_lond on the clean stream"
        base[k] = (fired, lvl)
        own_alerts = fired & ep["ismal"]
        summ.update(own_alerts=int(own_alerts.sum()), nonown_alerts=int((fired & ~ep["ismal"]).sum()),
                    own_alerts_mixed=int((own_alerts & (ep["m_atk"] < ep["nsz"])).sum()),
                    rstar_sum=int(sum(zero_pad(ep["sum_e"][j], ep["nsz"][j], 1.0 / lvl[j])
                                      for j in np.flatnonzero(own_alerts))))
        out["baseline"][k] = summ
    # control: canonical flow-only baseline reproduces t67's stored canonical row
    if not org["use_host"] and t67_rows is not None:
        row = t67_rows[name]
        ctrl = (row["T"] == T and row["NC"] == org["NC"] and row["elond_rej"] == out["baseline"]["poly"]["rejections"]
                and row["n_detected"] == out["baseline"]["poly"]["true"])
        assert ctrl, f"{name}: clean canonical baseline does not reproduce t67 ({row} vs {out['baseline']['poly']})"
        out["control_t67"] = True
    tr0 = Trajectory(org, 0, "causal")
    out["own_episodes"] = [dict(pos=int(j), m_total=int(ep["nsz"][j]), m_atk=int(ep["m_atk"][j]),
                                t_atk=int(ep["t_atk"][j]), victim=int(ep["dst"][j]),
                                n_templates=int(tr0.pools[int(j)].size),
                                n_templates_deployment=int(org["pools"].causal(ep["dst"][j], ep["t_atk"][j])[1]),
                                own_originals_after_t_atk=int(tr0.n_after_t_atk(int(j))),
                                pool_unavailable=int(j) in tr0.unavailable, pool_extended=int(j) in tr0.extended,
                                base_alert={k: bool(base[k][0][j]) for k in GAMMAS})
                           for j in np.flatnonzero(ep["ismal"])]
    t0 = time.time()
    # greedy, both pools, both regimes
    for pool_kind, slot in (("causal", "greedy"), ("t54", "greedy_t54pool")):
        for k in GAMMAS:
            res = []; steps = []
            for seed in range(D_TRAJ):
                tr, fired, lvl = greedy_attack(org, g[k], seed, pool_kind)
                # the fixed point's final decisions must equal run_lond on the final evidence
                ctx = Ctx(tr.ev_all(), ep["ismal"], org["CEIL"], alpha=A, w0=W0)
                chk = np.zeros(T, dtype=bool); run_lond(ctx, g[k], fired=chk)
                assert np.array_equal(chk, fired), "fixed point disagrees with run_lond on the final stream"
                r = classify(tr, g[k], fired, lvl, base[k][0], lambda j: SIM_CAP)
                r.pop("fired"); res.append(r); steps.append(tr.steps)
                if seed in VALIDATE_SEEDS:
                    v = dict(arm=tag, attacker=f"greedy/{k}/{pool_kind}", seed=seed,
                             noncausal_oracle_pool=(pool_kind != "causal"), regroup=validate_regroup(tr))
                    if org["use_host"]:
                        v["rebuild"] = validate_rebuild(tr)
                    out["validation"].append(v)
            s = summarise(res); s["fixed_point_steps"] = _q(steps)
            s["noncausal_oracle_pool"] = (pool_kind != "causal")
            out[slot][k] = s
            print(f"    [{name:15s}|{tag}] greedy/{pool_kind:6s}/{k:7s}: remaining own med {s['remaining_own']['median']:.0f} "
                  f"[{s['remaining_own']['min']:.0f},{s['remaining_own']['max']:.0f}] P(all)={s['p_all_silenced']:.2f} "
                  f"pads med {s['total_pads']['median']:.0f} [{s['total_pads']['p5']:.0f},{s['total_pads']['p95']:.0f}] "
                  f"fired {s['pads_fired']['median']:.0f} nonown surv/new {s['remaining_nonown']['median']:.0f}/{s['created_nonown']['median']:.0f} "
                  f"created own {s['created_own']['median']:.0f}  [{time.time()-t0:.0f}s]", flush=True)
    # multipliers: regime-independent padded stream, evaluated under both regimes
    for c, ctag, pool_kind in ((c_int, "c_int", "causal"), (C_CARRIED, "c3", "causal"),
                               (c_int, "c_int", "t54"), (C_CARRIED, "c3", "t54")):
        for variant in ("oracle_m_total", "k0_m_atk"):
            res = {k: [] for k in GAMMAS}
            for seed in range(D_TRAJ):
                tr = multiplier_attack(org, seed, c, variant, pool_kind)
                for k in GAMMAS:
                    r = evaluate(tr, g[k], base[k][0], base[k][1],
                                 lambda j, tr=tr: int(tr.pad_cnt[j]))
                    r.pop("fired"); res[k].append(r)
                if seed in VALIDATE_SEEDS:
                    v = dict(arm=tag, attacker=f"multiplier/{ctag}/{variant}/{pool_kind}", seed=seed,
                             noncausal_oracle_pool=(pool_kind != "causal"), regroup=validate_regroup(tr))
                    if org["use_host"]:
                        v["rebuild"] = validate_rebuild(tr)
                    out["validation"].append(v)
            key = f"{ctag}/{variant}" + ("" if pool_kind == "causal" else "/t54pool")
            out["multiplier"][key] = dict(c=c, variant=variant, pool=pool_kind,
                                          noncausal_oracle_pool=(pool_kind != "causal"),
                                          k0=(variant == "k0_m_atk"),
                                          knowledge=("K0: own flow count m_atk only" if variant == "k0_m_atk"
                                                     else "NOT K0: sizes on the observed total arity "
                                                          "m_total, which includes co-resident benign "
                                                          "flows; an oracle probe that isolates firing "
                                                          "pads and non-attacker rejections"),
                                          **{k: summarise(res[k]) for k in GAMMAS})
            for k in GAMMAS:
                s = out["multiplier"][key][k]
                print(f"    [{name:15s}|{tag}] mult/{key:22s}/{k:7s}: remaining own med "
                      f"{s['remaining_own']['median']:.0f} [{s['remaining_own']['min']:.0f},{s['remaining_own']['max']:.0f}] "
                      f"P(all)={s['p_all_silenced']:.2f} pads {s['total_pads']['median']:.0f} nonown "
                      f"{s['remaining_nonown']['median']:.0f}/{s['created_nonown']['median']:.0f} classes {s['classes_mean']}  [{time.time()-t0:.0f}s]", flush=True)
    snap = org["snapshot"]; cal_now = org["score_all"][(org["ts"] < org["t_split"]) & (org["y"] == 0)]
    assert np.array_equal(cal_now, snap["cal_scores"]) and org["thr"] == snap["thr"] and \
        org["CEIL"] == snap["CEIL"] and org["NC"] == snap["NC"] and \
        np.array_equal(org["pools"].t54_rows, snap["t54_pool"]) and \
        snap["causal_pools"] == {int(j): (int(org["pools"].causal(ep["dst"][j], ep["t_atk"][j])[0].size),
                                          int(org["pools"].causal(ep["dst"][j], ep["t_atk"][j])[0].sum()))
                                 for j in np.flatnonzero(ep["ismal"])}, \
        f"{name}: calibration, threshold or a template pool changed during the run"
    out["immutability_asserted"] = True
    bad = [v for v in out["validation"] if not v["regroup"]["ok"] or (v.get("rebuild") and not v["rebuild"]["ok"])]
    assert not bad, f"{name}: validation failed: {bad[:2]}"
    return out


def main(quick=False):
    global D_TRAJ
    if quick:
        D_TRAJ = 3
    t0 = time.time()
    Path("out").mkdir(exist_ok=True)
    t51.ensure_extracted()
    paths = sorted(glob.glob(f"{t51.AIT_DIR}/*/tcp_complete.csv"))
    names = [Path(p).parent.name for p in paths]
    print(f"  loading {len(names)} AIT scenarios: {names}", flush=True)
    scen = {}
    for n_, p in zip(names, paths):
        scen[n_] = t51.load_scenario(p); scen[n_]["path"] = p
    common = {test: sorted(set.intersection(*[scen[n_]["good"] & set(scen[n_]["Xnum"].columns)
                                              for n_ in names if n_ != test])) for test in names}
    try:
        t67_rows = {r["org"]: r for r in json.load(open("out/t67_ait_order.json"))["arms"]["keyhash"]["rows"]}
    except FileNotFoundError:
        t67_rows = None
    manifest = dict(stage="t76_joint_ait", design="docs/48_joint_ait_design.md v3.1 + reviewer scope",
                    alpha=A, w0=W0, k=K, bucket_s=BUCKET_US // 1_000_000, order=ORDER, orders=[ORDER],
                    canonical_order=ORDER, gammas=list(GAMMAS),
                    orgs=names, orgs_host=list(ORGS_HOST), d_traj=D_TRAJ, n_min=N_MIN, sim_cap=SIM_CAP,
                    c_carried=C_CARRIED, c_rule="c_int = floor(rho) + 1, rho = (NC+1) * alpha / T",
                    validate_seeds=list(VALIDATE_SEEDS), chunk0=CHUNK0,
                    pools=dict(primary="benign flows to the episode's victim with ts < t_atk (whole scenario)",
                               comparability="t54: benign deployment flows to any attacked victim"),
                    insertion="after the attacker's own last flow t_atk; virtual times t_atk + k*eps",
                    attackers=dict(greedy="K1 bucket fixed point, freeze at SIM_CAP / pool-unavailable",
                                   multiplier="K0, (c-1)*m_x on every own episode; theory m_total, operational m_atk"),
                    written_before_results=True)
    out = dict(config=manifest, orgs={})
    json.dump(out, open("out/t76_joint_ait.json", "w"), indent=1)      # manifest first (pre-registration)
    print(f"  manifest written  [{time.time()-t0:.0f}s]", flush=True)
    for test in names:
        org = prepare_org(test, scen, names, common, use_host=False)
        print(f"  [{test:15s}|flow] T={org['ep']['T']} NC={org['NC']} rho={org['CEIL']*A/org['ep']['T']:.3f} "
              f"own={int(org['ep']['ismal'].sum())}  [{time.time()-t0:.0f}s]", flush=True)
        out["orgs"].setdefault(test, {})["flow_precommit"] = precommit(org)
        json.dump(out, open("out/t76_joint_ait.json", "w"), indent=1, allow_nan=True)   # BEFORE the attacks
        out["orgs"][test]["flow"] = run_org(org, t67_rows)
        json.dump(out, open("out/t76_joint_ait.json", "w"), indent=1, allow_nan=True)
    for test in ORGS_HOST:
        if test not in scen:
            continue
        org = prepare_org(test, scen, names, common, use_host=True)
        print(f"  [{test:15s}|host] T={org['ep']['T']} NC={org['NC']} own={int(org['ep']['ismal'].sum())}  "
              f"[{time.time()-t0:.0f}s]", flush=True)
        out["orgs"][test]["host_precommit"] = precommit(org)
        json.dump(out, open("out/t76_joint_ait.json", "w"), indent=1, allow_nan=True)   # BEFORE the attacks
        out["orgs"][test]["host"] = run_org(org, t67_rows)
        json.dump(out, open("out/t76_joint_ait.json", "w"), indent=1, allow_nan=True)
    out["summary"] = summary_table(out)
    out["control_reproduced"] = all(o["flow"].get("control_t67", False) for o in out["orgs"].values())
    out["all_validations_ok"] = all(v["regroup"]["ok"] and (v.get("rebuild") is None or v["rebuild"]["ok"])
                                    for o in out["orgs"].values() for arm in o.values() for v in arm["validation"])
    json.dump(out, open("out/t76_joint_ait.json", "w"), indent=1, allow_nan=True)
    print(f"\n  control reproduced: {out['control_reproduced']}   validations ok: {out['all_validations_ok']}")
    print(f"  [{time.time()-t0:.0f}s]  wrote out/t76_joint_ait.json")
    return out


def summary_table(out):
    rows = []
    for name, o in out["orgs"].items():
        for arm, r in ((a, o[a]) for a in ("flow", "host") if a in o):   # skip the precommit records
            for k in GAMMAS:
                b = r["baseline"][k]; gr = r["greedy"][k]
                mt = r["multiplier"]["c_int/oracle_m_total"][k]; mo = r["multiplier"]["c_int/k0_m_atk"][k]
                rows.append(dict(org=name, arm=arm, gamma=k, base_own=b["own_alerts"], base_nonown=b["nonown_alerts"],
                                 rho=round(r["rho"], 3), c_int=r["c_int"],
                                 greedy_remaining_med=gr["remaining_own"]["median"], greedy_p_all=gr["p_all_silenced"],
                                 greedy_pads_med=gr["total_pads"]["median"], greedy_pads_p5=gr["total_pads"]["p5"],
                                 greedy_pads_p95=gr["total_pads"]["p95"], greedy_pads_fired_med=gr["pads_fired"]["median"],
                                 greedy_remaining_nonown_med=gr["remaining_nonown"]["median"],
                                 greedy_created_nonown_med=gr["created_nonown"]["median"],
                                 greedy_created_own_med=gr["created_own"]["median"],
                                 mult_oracle_arity_remaining_med=mt["remaining_own"]["median"],
                                 mult_oracle_arity_classes=mt["classes_mean"],
                                 mult_k0_remaining_med=mo["remaining_own"]["median"], mult_k0_classes=mo["classes_mean"],
                                 mult_k0_pads=mo["total_pads"]["median"]))
    return rows


if __name__ == "__main__":
    import sys
    main(quick="--quick" in sys.argv)
