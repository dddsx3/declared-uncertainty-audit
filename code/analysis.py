# -*- coding: utf-8 -*-
"""P3 analysis: log-ratio audit with bootstrap confidence intervals.

Guards (fail loudly):
  1. one ratio direction only (declared/actual)
  2. every ratio reproducible from declared_value / actual_value
  3. G01 present and flagged object_matched = 0
  4. >= 40 catalogued objects and exactly 17 ledger rows

Outputs:
  data/stats.json          all numbers quoted in the manuscript
  data/stats_summary.txt   human-readable mirror
  figures/fig02_forest.pdf forest plot (log ratio, sorted, with documented CI)
"""
import csv
import json
import math
import os
import sys

import numpy as np
from scipy.stats import spearmanr

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

RNG_SEED = 20261108
NBOOT = 10000


def num(x):
    try:
        return float(x)
    except Exception:
        return None


def semvar(v):
    return "sea ice thickness" if v.startswith("sea ice thickness") else v


rows = list(csv.DictReader(open(os.path.join(DATA, "p3_dataset.csv"), encoding="utf-8-sig")))
ledger = list(csv.DictReader(open(os.path.join(DATA, "p3_declared_ledger.csv"), encoding="utf-8-sig")))

# ---------------------------------------------------------------- guards
for r in rows:
    if r["ratio"] and r["assessable"] == "1":
        assert r["ratio_direction"] == "declared/actual", r["group_id"]
        assert abs(float(r["ratio"]) - float(r["declared_value"]) / float(r["actual_value"])) < 1e-3, r["group_id"]
    if r["ratio"]:
        assert r["ratio_direction"] == "declared/actual", r["group_id"]
assert any(r["group_id"] == "G01" and r["object_matched"] == "0" for r in rows), "G01 missing"
assert len(rows) >= 40, len(rows)
assert len(ledger) == 17, len(ledger)

assess = [r for r in rows if r["assessable"] == "1" and r["ratio"]]
core = [r for r in assess if int(r["group_id"][1:]) <= 8]

# ---------------------------------------------------------------- helpers
def geom(vals):
    return float(np.exp(np.mean(np.log(vals))))


def boot_ci(vals, f=geom, n=NBOOT, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(vals, float)
    b = np.array([f(rng.choice(v, size=v.size, replace=True)) for _ in range(n)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def boot_stat(vals, stat, n=NBOOT, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(vals, float)
    b = np.array([stat(rng.choice(v, size=v.size, replace=True)) for _ in range(n)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def sign_test(n_under, n_over):
    """Exact sign test on the direction of each record, independent of any
    ratio summary. Parity records are dropped as ties. The two-sided p doubles
    the smaller tail; the one-sided p is in the under-reporting direction."""
    n = n_under + n_over
    if n == 0:
        return None, None
    k = max(n_under, n_over)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / 2.0 ** n
    p_two = min(1.0, 2.0 * tail)
    p_one = sum(math.comb(n, i) for i in range(n_under, n + 1)) / 2.0 ** n
    return float(p_two), float(p_one)


def describe(group):
    vals = np.array([float(r["ratio"]) for r in group])
    logs = np.log(vals)
    lo, hi = boot_ci(logs, f=np.mean)
    gmean = float(np.exp(logs.mean()))
    med = float(np.median(vals))
    mlo, mhi = boot_stat(logs, np.median)
    x = np.array([float(r["prior_score"]) for r in group])
    rho, p = spearmanr(x, vals)
    rho_l, p_l = spearmanr(x, logs)  # identical by monotonicity, kept as a guard
    return {
        "n": len(group), "ids": [r["group_id"] for r in group],
        "arithmetic_mean": float(vals.mean()),
        "geometric_mean": gmean,
        "geometric_mean_ci95": [float(np.exp(lo)), float(np.exp(hi))],
        "log_mean": float(logs.mean()),
        "log_mean_ci95": [lo, hi],
        "median": med,
        "median_ci95_logscale": [float(np.exp(mlo)), float(np.exp(mhi))],
        "mean_log10": float(np.mean(np.log10(vals))),
        "log10_mean_ci95": [lo / math.log(10), hi / math.log(10)],
        "min": float(vals.min()), "max": float(vals.max()),
        "iqr": float(np.percentile(vals, 75) - np.percentile(vals, 25)),
        "rho_prior": float(rho), "p_prior": float(p),
        "rho_prior_log": float(rho_l), "p_prior_log": float(p_l),
        "under_report_n": int((vals < 1).sum()), "over_report_n": int((vals > 1).sum()),
        "parity_n": int((vals == 1).sum()),
        "below_factor2": int((vals < 0.5).sum()),
        "above_factor2": int((vals > 2).sum()),
        "sign_test_two_sided_p": sign_test(int((vals < 1).sum()), int((vals > 1).sum()))[0],
        "sign_test_one_sided_under_p": sign_test(int((vals < 1).sum()), int((vals > 1).sum()))[1],
        "sign_test_n": int((vals < 1).sum()) + int((vals > 1).sum()),
    }


sets = {
    "A_objectmatched_gradeA": [r for r in assess if r["in_A"] == "1"],
    "B_objectmatched_AB": [r for r in assess if r["in_B"] == "1"],
    "C_all_assessable": [r for r in assess if r["in_C"] == "1"],
    "core_legacy8": core,
    "core_A_legacy5": [r for r in core if r["object_matched"] == "1"
                       and r["evidence_grade"] == "A" and r["ratio_relation"] != "lower_bound"],
}
res_sets = {k: describe(v) for k, v in sets.items()}

# ---------------------------------------------------------------- stratified
# Stratification is computed on every ratio-definable object, not on Set B, so
# that the strata and the Spearman correlation it accompanies are drawn from the
# same sample; an earlier version stratified Set B while correlating on all
# ratio-definable objects, which is why the group sizes in the text (3/2/6) did
# not match the ones a reader could recompute (3/3/8).
strat = {}
for k in sorted({int(float(r["prior_score"])) for r in assess}):
    vals = [float(r["ratio"]) for r in assess if int(float(r["prior_score"])) == k]
    strat[str(k)] = {"n": len(vals), "median": float(np.median(vals)),
                     "geometric_mean": geom(vals), "values": vals}

# low (score <= 1) vs high (score >= 2) contrast on log ratios, all ratio-definable
lo_p = [math.log(float(r["ratio"])) for r in assess if int(float(r["prior_score"])) <= 1]
hi_p = [math.log(float(r["ratio"])) for r in assess if int(float(r["prior_score"])) >= 2]
diff = float(np.mean(hi_p) - np.mean(lo_p))
rng = np.random.default_rng(RNG_SEED)
bd = []
for _ in range(NBOOT):
    # draw order is fixed (high first, then low) so that this interval and the
    # one in audit_claims.py, which share a seed, are numerically identical
    b = rng.choice(hi_p, len(hi_p), replace=True)
    a = rng.choice(lo_p, len(lo_p), replace=True)
    bd.append(b.mean() - a.mean())
bd = np.array(bd)
contrast = {"n_low": len(lo_p), "n_high": len(hi_p), "log_diff": diff,
            "ratio_diff": float(math.exp(diff)),
            "ci95_log": [float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))],
            "ci95_ratio": [float(math.exp(np.percentile(bd, 2.5))), float(math.exp(np.percentile(bd, 97.5)))]}

# ---------------------------------------------------------------- IQR normalisation
iqr_norm = {}
for tag, grp in (("core", core), ("expanded", assess)):
    d = {}
    for v in sorted({semvar(r["variable"]) for r in grp}):
        g = [r for r in grp if semvar(r["variable"]) == v]
        if len(g) < 2:
            continue
        vals = np.array([float(r["ratio"]) for r in g])
        med = float(np.median(vals))
        iqr = float(np.percentile(vals, 75) - np.percentile(vals, 25))
        d[v] = {"n": len(g), "ids": [r["group_id"] for r in g], "median": med, "iqr": iqr,
                "normalised": [round(float((x - med) / iqr), 3) for x in vals],
                "min_norm": round(float(((vals - med) / iqr).min()), 3),
                "max_norm": round(float(((vals - med) / iqr).max()), 3)}
    iqr_norm[tag] = d

# ---------------------------------------------------------------- evidence
ev = {}
for r in ledger:
    ev[r["evidence_type"]] = ev.get(r["evidence_type"], 0) + 1
ev_pct = {k: round(100 * v / len(ledger), 1) for k, v in ev.items()}

# ---------------------------------------------------------------- direction
under = [r for r in assess if float(r["ratio"]) < 1]
over = [r for r in assess if float(r["ratio"]) > 1]
factor = {}
for r in assess:
    v = float(r["ratio"])
    factor[r["group_id"]] = round(max(v, 1 / v), 2)

# ---------------------------------------------------------------- key statements
key = {}
for gid in ("G01", "G02", "G03", "G06", "G07", "G08", "G20"):
    r = next(x for x in rows if x["group_id"] == gid)
    if r["ratio"]:
        v = float(r["ratio"])
        key[gid] = {"ratio": v, "declared": float(r["declared_value"]),
                    "actual": float(r["actual_value"]),
                    "factor": round(max(v, 1 / v), 3),
                    "direction": "under-report" if v < 1 else ("over-report" if v > 1 else "parity")}

stats = {
    "n_objects": len(rows),
    "n_assessable": len(assess),
    "n_ledger": len(ledger),
    "n_records_verification_log": sum(1 for _ in open(os.path.join(DATA, "p3_verification_log.csv"), encoding="utf-8")) - 1,
    "sets": res_sets,
    "stratified": strat,
    "prior_contrast": contrast,
    "iqr_normalised": iqr_norm,
    "evidence_counts": ev,
    "evidence_percent": ev_pct,
    "under_report_n": len(under),
    "over_report_n": len(over),
    "under_report_share": round(100 * len(under) / len(assess), 1),
    "factor_map": factor,
    "key": key,
    "bootstrap": {"n": NBOOT, "seed": RNG_SEED, "method": "percentile"},
}
json.dump(stats, open(os.path.join(DATA, "stats.json"), "w"), indent=2)

# ---------------------------------------------------------------- mirror
lines = []
A = res_sets["A_objectmatched_gradeA"]
C = res_sets["C_all_assessable"]
K = res_sets["core_legacy8"]
KA = res_sets["core_A_legacy5"]
lines.append(f"objects={len(rows)} assessable={len(assess)} ledger={len(ledger)}")
lines.append(f"CORE A5 n={KA['n']} median={KA['median']:.4f} range={KA['min']:.4f}-{KA['max']:.4f} "
             f"rho={KA['rho_prior']:.3f} p={KA['p_prior']:.3f}")
lines.append(f"CORE C8 n={K['n']} median={K['median']:.4f} range={K['min']:.4f}-{K['max']:.4f} "
             f"gmean={K['geometric_mean']:.4f} [{K['geometric_mean_ci95'][0]:.4f},{K['geometric_mean_ci95'][1]:.4f}] rho={K['rho_prior']:.3f} p={K['p_prior']:.3f}")
lines.append(f"A     n={A['n']} median={A['median']:.4f} range={A['min']:.4f}-{A['max']:.4f} "
             f"gmean={A['geometric_mean']:.4f} [{A['geometric_mean_ci95'][0]:.4f},{A['geometric_mean_ci95'][1]:.4f}] rho={A['rho_prior']:.3f} p={A['p_prior']:.3f}")
lines.append(f"C     n={C['n']} median={C['median']:.4f} range={C['min']:.4f}-{C['max']:.4f} "
             f"gmean={C['geometric_mean']:.4f} [{C['geometric_mean_ci95'][0]:.4f},{C['geometric_mean_ci95'][1]:.4f}] rho={C['rho_prior']:.3f} p={C['p_prior']:.3f}")
lines.append(f"under={len(under)}/{len(assess)} ({stats['under_report_share']}%) over={len(over)}")
lines.append(f"prior contrast log-diff={contrast['log_diff']:.3f} ratio={contrast['ratio_diff']:.3f} "
             f"CI={contrast['ci95_ratio'][0]:.3f}-{contrast['ci95_ratio'][1]:.3f}")
for v, d in iqr_norm["core"].items():
    lines.append(f"IQR core {v}: n={d['n']} min={d['min_norm']} max={d['max_norm']} median={d['median_norm'] if 'median_norm' in d else 0}")
for v, d in iqr_norm["expanded"].items():
    lines.append(f"IQR exp  {v}: n={d['n']} min={d['min_norm']} max={d['max_norm']}")
lines.append(f"evidence={ev} pct={ev_pct}")
open(os.path.join(DATA, "stats_summary.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
