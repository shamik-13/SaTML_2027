import json
from collections import Counter, defaultdict

for path in ["proto/out/t28_P5.json", "proto/out/t43_E10.json"]:
    d = json.load(open(path))
    print("==", path)
    if path.endswith("t28_P5.json"):
        diffs = Counter()
        by_pool = defaultdict(Counter)
        n = Counter()
        for row in d["rows"]:
            for pool, p in row["pools"].items():
                r9 = p.get("r_90")
                rm = p.get("r_mean")
                if r9 is None or rm is None:
                    continue
                delta = r9 - rm
                diffs[delta] += 1
                by_pool[pool][delta] += 1
                n[pool] += 1
        print("r90-rmean all", sorted(diffs.items()))
        for pool in sorted(n):
            print(pool, n[pool], sorted(by_pool[pool].items()))
    else:
        per_pos_pool = defaultdict(list)
        allcells = []
        for s in d["summary"]:
            if s["r_90_median"] is not None:
                per_pos_pool[(s["pos"], s["pool"])].append(s["r_90_median"])
                allcells.append((s["pos"], s["pool"], s["seed"], s["r_90_median"]))
        for key, vals in sorted(per_pos_pool.items()):
            print(key, vals, "median", sorted(vals)[len(vals)//2] if len(vals) % 2 else sum(sorted(vals)[len(vals)//2-1:len(vals)//2+1])/2)
        print("cells", allcells)
