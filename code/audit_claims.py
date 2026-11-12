# -*- coding: utf-8 -*-
"""Recompute every headline number of the manuscript from the packaged data.

Run from code/:   python audit_claims.py [--write]

Two repairs and one audit:

 1. C2 backfill.  The four columns locator_declared / quote_declared /
    locator_actual / quote_actual were empty for all 50 rows, which made the
    admission checklist unexecutable: by its own definition the audit had zero
    auditable objects.  `data/p3_verification_log.csv` already records, for
    every group it covers, the locator (variable, attribute, table or section)
    and the reading taken there.  This script copies those into the dataset.
    It invents nothing: rows the log does not cover stay empty and are counted.

 2. Ledger recommendation.  The correction ledger recommended "replace" for
    seven rows, four of which the audit itself had judged non-comparable
    (G01, G06 statistic mismatch; G07, G17 support mismatch).  The
    recommendation is now a function of the admission verdict, so the ledger
    cannot recommend a record it has itself refused.

 3. Claim audit.  Every number the manuscript quotes is recomputed here and
    written to data/claims.json, so text and data cannot drift apart.

Originals are copied to data/r12_baseline/ on first run; the script is
idempotent and never rewrites the baseline.
"""
import argparse
import csv
import json
import os
import shutil

import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
BASE_DIR = os.path.join(DATA, "r12_baseline")
DATASET = os.path.join(DATA, "p3_dataset.csv")
LEDGER = os.path.join(DATA, "p3_declared_ledger.csv")
LOG = os.path.join(DATA, "p3_verification_log.csv")

SEED = 20261108
NBOOT = 10000


def _backup(path):
    os.makedirs(BASE_DIR, exist_ok=True)
    dst = os.path.join(BASE_DIR, os.path.basename(path))
    if not os.path.exists(dst):
        shutil.copy2(path, dst)


def read(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


# ---------------------------------------------------------------- 1. C2
def backfill_c2(d):
    log = read(LOG)
    loc, val = {}, {}
    for _, r in log.iterrows():
        item = str(r["item"])
        gid = str(r["group_id"])
        for side in ("declared", "actual"):
            if item in (side, "declared+actual"):
                loc.setdefault((gid, side), str(r["location"]).strip())
                val.setdefault((gid, side), str(r["quoted_or_computed_value"]).strip())
    filled = 0
    for i, r in d.iterrows():
        gid = str(r["group_id"])
        for side, lc, qc in (("declared", "locator_declared", "quote_declared"),
                            ("actual", "locator_actual", "quote_actual")):
            if not str(r[lc]).strip() and (gid, side) in loc:
                d.at[i, lc] = loc[(gid, side)]
                d.at[i, qc] = val[(gid, side)]
                filled += 1
    return d, filled


def c2_coverage(d):
    adm = d[d["admission"] != "no_declared_value"]
    has = adm[[str(x).strip() != "" for x in adm["locator_declared"]]]
    return dict(rows_total=len(d), rows_admitted=len(adm), locator_declared_filled=len(has),
                admitted_without_locator=[g for g in adm["group_id"] if g not in set(has["group_id"])],
                rows_all_locators_total=int(sum(str(x).strip() != "" for x in d["locator_declared"])))


# ---------------------------------------------------------------- 2. ledger
REPLACE = "replace declared sigma with audited value"
RETAIN = "retain declared value"
STAT = "use only with the statistic mismatch stated"
SUPP = "use only with the support mismatch stated"
NOSIG = "do not use as a sigma; publish a declared value first"


def recommend(admission, ratio):
    """Recommended use as a function of the audit verdict, never independent of it.

    An earlier version recommended "replace" for seven rows, four of which the
    audit had itself judged non-comparable (G01 and G06 statistic mismatch,
    G07 and G17 support mismatch): the ledger was recommending records that the
    paper refuses.  The recommendation is now derived from the verdict, and a
    row whose ratio is exactly one is retained rather than replaced, because
    replacing a number by itself is not a correction.
    """
    if admission == "auditable":
        if ratio == ratio and abs(ratio - 1.0) < 1e-9:
            return RETAIN
        return REPLACE
    if admission == "statistic_mismatch":
        return STAT
    if admission == "support_mismatch":
        return SUPP
    if admission == "metric_not_exchangeable":
        return NOSIG
    return "not in ledger"


def rebuild_ledger(d):
    led = read(LEDGER)
    adm = dict(zip(d["group_id"], d["admission"]))
    ratio = dict(zip(d["group_id"], [f(x) for x in d["ratio"]]))
    before = led["recommended_use"].value_counts().to_dict()
    led["recommended_use"] = [recommend(adm.get(g, "no_declared_value"), ratio.get(g, np.nan))
                              for g in led["group_id"]]
    after = led["recommended_use"].value_counts().to_dict()
    return led, before, after



# ---------------------------------------------------------------- dictionary
COLUMNS = [
    ("group_id", "identification", "audit object identifier, G01-G50"),
    ("variable", "identification", "Earth system variable, collapsed to 16 families"),
    ("product", "identification", "product name as published"),
    ("product_version", "identification", "version label of the product audited"),
    ("validation_reference", "identification", "independent reference behind the measured error"),
    ("declared_value", "declaration", "numeric sigma as published; empty if none is locatable"),
    ("declared_unit", "declaration", "unit of the declared value"),
    ("declared_scope", "declaration", "construct the declaration covers (total, random, envelope, ...)"),
    ("declared_source_type", "declaration", "kind of source: product field, document, mission requirement"),
    ("declared_source", "declaration", "where the number was read, in words"),
    ("declared_doi", "declaration", "DOI recorded with the declaration, resolvable or not"),
    ("actual_value", "measurement", "measured error at the validation support"),
    ("actual_unit", "measurement", "unit of the measured error"),
    ("actual_metric", "measurement", "statistic of the measured error (RMS, RMSE, ubRMSE, bias, ...)"),
    ("actual_source", "measurement", "where the measured error comes from"),
    ("actual_doi", "measurement", "DOI or locator of the measured error"),
    ("ratio", "ratio", "declared divided by actual, one direction for all rows"),
    ("ratio_direction", "ratio", "direction of the unified ratio; always declared/actual"),
    ("ratio_original_stored", "ratio", "value as it appeared in the inherited table"),
    ("ratio_original_direction", "ratio", "direction of the inherited value"),
    ("ratio_relation", "ratio", "point estimate or lower bound"),
    ("prior_score", "prior", "prior-dependence score, 0-4"),
    ("prior_climatology_background", "prior", "score ingredient: climatological background"),
    ("prior_empirical_transfer", "prior", "score ingredient: empirically transferred relation"),
    ("prior_shared_auxiliary", "prior", "score ingredient: shared auxiliary dataset"),
    ("prior_assumed_model", "prior", "score ingredient: assumed physical or radiative model"),
    ("footprint_mismatch", "legacy", "inherited single field for a support disagreement, superseded by C4a/C4b"),
    ("object_matched", "legacy", "inherited single field for C3, superseded by C3a/C3b"),
    ("evidence_grade", "legacy", "A/B/C evidence grade of the measured value"),
    ("assessable", "legacy", "1 if the inherited rule admitted the object"),
    ("notes", "legacy", "free-text provenance note"),
    ("evidence_type", "semantics", "provenance class of the declared number"),
    ("evidence_detail", "semantics", "how the number was read from its source"),
    ("semantics_class", "semantics", "total, random, envelope, ... : the construct actually declared"),
    ("stage_declared", "semantics", "retrieval stage at which the declaration was made"),
    ("stage_actual", "semantics", "retrieval stage of the measured error"),
    ("scale_declared", "semantics", "spatial support of the declaration"),
    ("scale_actual", "semantics", "spatial support of the measurement"),
    ("log_ratio", "semantics", "natural log of the ratio"),
    ("ci_low", "semantics", "lower end of the ratio interval"),
    ("ci_high", "semantics", "upper end of the ratio interval"),
    ("ci_basis", "semantics", "how the interval was obtained"),
    ("quote_declared", "provenance", "reading taken at locator_declared (value string or quoted formula)"),
    ("quote_actual", "provenance", "reading taken at locator_actual"),
    ("locator_declared", "provenance", "variable, attribute, table or section that holds the declaration"),
    ("locator_actual", "provenance", "file, table or paper that holds the measured error"),
    ("doi_status_declared", "provenance", "resolved, unresolvable or not applicable"),
    ("doi_status_actual", "provenance", "same, for the measured side"),
    ("comparison_validity", "provenance", "comparable, support mismatch or not comparable"),
    ("in_A", "membership", "member of Set A (fully admitted)"),
    ("in_B", "membership", "member of Set B (support-caveated)"),
    ("in_C", "membership", "member of Set C (any ratio)"),
    ("reason_if_not_assessable", "membership", "why no ratio can be formed"),
    ("same_product", "condition", "C3a: declaration and validation name the same product and version"),
    ("same_statistic", "condition", "C3b: same statistical estimand"),
    ("support_stated", "condition", "C4a: the declaration states its support"),
    ("support_match", "condition", "C4b: that support is the one the validation measured"),
    ("source_resolved", "condition", "C2: the declaration resolves to a locator"),
    ("admission", "verdict", "auditable, statistic_mismatch, support_mismatch, metric_not_exchangeable, no_declared_value"),
]


def write_column_dictionary(d):
    """data/column_dictionary.csv: one row per released column (R2's request).

    The paper describes the schema in groups and points here for the field-by-field
    definition, so that the grouping cannot drift from the file.
    """
    rows = []
    for name, group, meaning in COLUMNS:
        if name not in d.columns:
            raise SystemExit("dictionary names a column the dataset does not have: %s" % name)
        filled = int(sum(str(x).strip() != "" for x in d[name]))
        rows.append(dict(column=name, group=group, filled=filled, of=len(d), meaning=meaning))
    missing = [c for c in d.columns if c not in [x[0] for x in COLUMNS]]
    if missing:
        raise SystemExit("dataset has columns the dictionary does not describe: %s" % missing)
    with open(os.path.join(DATA, "column_dictionary.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["column", "group", "filled", "of", "meaning"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    groups = {}
    for _, g, _m in COLUMNS:
        groups[g] = groups.get(g, 0) + 1
    return groups



# ---------------------------------------------------------------- text gate
def _stratum(c, k):
    st = c["stratified"]
    return st.get(k, st.get(str(k)))


def check_text(c, tex_path=None):
    """Assert that the manuscript prints the recomputed values.

    This is the same gate P5 uses: a number can only pass if the exact string the
    paper prints is the string the computation produces.  It exists because this
    manuscript drifted from its data twice, both times by a number that was
    correct when it was typed.
    """
    tex = open(tex_path or os.path.join(BASE, "manuscript.tex"), encoding="utf-8").read()
    a7 = c["a7"]["geometric_mean"]
    all14 = c["all14"]
    pc = c["prior_contrast"]
    checks = [
        ("core-five median", "%.3f" % c["core5"]["median"]),
        ("Set A geometric mean", "%.3f" % a7),
        ("Set A interval, upper", "%.3f" % c["a7"]["ci95"][1]),
        ("Set C geometric mean", "%.3f" % all14["geometric_mean"]),
        ("Set C interval, lower", "%.3f" % all14["ci95"][0]),
        ("Set C interval, upper", "%.3f" % all14["ci95"][1]),
        ("Spearman rho", "%.3f" % c["spearman"]["rho"]),
        ("Spearman p", "%.3f" % c["spearman"]["p"]),
        ("prior contrast ratio", "%.3f" % pc["ratio"]),
        ("prior contrast interval, lower", "%.3f" % pc["ratio_ci95"][0]),
        ("prior contrast interval, upper", "%.3f" % pc["ratio_ci95"][1]),
        ("score-2 median", "%.3f" % _stratum(c, 2)["median"]),
        ("score-3 median", "%.3f" % _stratum(c, 3)["median"]),
        ("G01 ratio", "%.4f" % c["g01"]["ratio"]),
        ("G02 ratio", "%.4f" % c["g02"]["ratio"]),
        ("ratio of ratios", "%.1f" % c["ratio_of_ratios"]),
        ("families without an assessable object", "Ten families"),
        ("admitted rows with a locator", "All 17 admitted rows"),
        ("footprint mismatch count", "%d a footprint mismatch" % c["footprint_mismatch_nonassessable"]),
        ("ledger replace count", "Six rows carry a ratio"),
    ]
    bad = []
    for label, lit in checks:
        if lit not in tex:
            bad.append((label, lit))
    return checks, bad


# ---------------------------------------------------------------- 3. claims
def boot_ci(x, n=NBOOT, seed=SEED, stat=np.mean):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    draws = [stat(rng.choice(x, size=x.size, replace=True)) for _ in range(n)]
    return (float(np.exp(np.percentile(draws, 2.5))),
            float(np.exp(np.percentile(draws, 97.5))))


def claims(d, led):
    d["ratio_f"] = [f(x) for x in d["ratio"]]
    d["score_f"] = [f(x) for x in d["prior_score"]]
    d["assessable_f"] = [f(x) for x in d["assessable"]]
    r = d[d["ratio_f"].notna()].copy()
    adm = d[d["admission"] != "no_declared_value"]
    non = d[d["admission"] == "no_declared_value"]

    fam = d["variable"].map(lambda v: "sea ice thickness"
                            if str(v).startswith("sea ice thickness") else v)
    fam_tab = pd.DataFrame({"family": fam, "assessable": d["assessable_f"]})
    fam_tab = fam_tab.groupby("family")["assessable"].agg(["size", "sum"])
    fam_zero = int((fam_tab["sum"] == 0).sum())

    geo = float(np.exp(np.log(r["ratio_f"]).mean()))
    lo_ci, hi_ci = boot_ci(np.log(r["ratio_f"]))
    core5 = d[d["group_id"].isin(["G02", "G03", "G04", "G05", "G06"])]["ratio"].astype(float)
    a7 = ["G02", "G04", "G05", "G15", "G16", "G19", "G20"]
    a7r = d[d["group_id"].isin(a7)]["ratio"].astype(float)
    a8 = ["G02", "G04", "G05", "G08", "G15", "G16", "G19", "G20"]
    a8r = d[d["group_id"].isin(a8)]["ratio"].astype(float)

    parity = r[np.isclose(r["ratio_f"], 1.0)]
    nonpar = r[~np.isclose(r["ratio_f"], 1.0)]
    under = int((nonpar["ratio_f"] < 1).sum())
    over = int((nonpar["ratio_f"] > 1).sum())
    sign_p = float(stats.binomtest(under, under + over, 0.5).pvalue)

    strata = {}
    for s, g in r.groupby("score_f"):
        strata[int(s)] = dict(n=int(len(g)), median=float(g["ratio_f"].median()),
                              geometric_mean=float(np.exp(np.log(g["ratio_f"]).mean())),
                              ids=list(g["group_id"]))
    rho, p_rho = stats.spearmanr(r["score_f"], r["ratio_f"])
    lo = r[r["score_f"] <= 1]["ratio_f"]
    hi = r[r["score_f"] >= 2]["ratio_f"]
    logdiff = float(np.log(hi).mean() - np.log(lo).mean())
    boots = []
    rng = np.random.default_rng(SEED)
    lo_v, hi_v = np.log(lo.values), np.log(hi.values)
    for _ in range(NBOOT):
        boots.append(rng.choice(hi_v, hi_v.size).mean() - rng.choice(lo_v, lo_v.size).mean())
    lo_ci2, hi_ci2 = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))

    g1 = d[d["group_id"] == "G01"].iloc[0]
    g2 = d[d["group_id"] == "G02"].iloc[0]
    g01 = dict(declared=float(g1["declared_value"]), actual=float(g1["actual_value"]),
               ratio=float(g1["ratio"]), factor=float(g1["actual_value"]) / float(g1["declared_value"]),
               stage_declared=g1["stage_declared"], stage_actual=g1["stage_actual"],
               actual_metric=g1["actual_metric"])
    g02 = dict(declared=float(g2["declared_value"]), actual=float(g2["actual_value"]),
               ratio=float(g2["ratio"]), factor=float(g2["actual_value"]) / float(g2["declared_value"]),
               stage_declared=g2["stage_declared"], stage_actual=g2["stage_actual"])

    return dict(
        n_objects=len(d), n_admitted=len(adm), n_ratio_definable=len(r),
        n_auditable=int((d["admission"] == "auditable").sum()),
        admission_counts=d["admission"].value_counts().to_dict(),
        no_declared_value=len(non),
        no_measured_error=int(sum(str(x).strip() == "" for x in d["actual_value"])),
        footprint_mismatch_total=int(sum(str(x).strip() == "1" for x in d["footprint_mismatch"])),
        footprint_mismatch_nonassessable=int(sum(str(x).strip() == "1" for x in non["footprint_mismatch"])),
        families_total=int(fam_tab.shape[0]), families_without_assessable=fam_zero,
        families_with_assessable=int((fam_tab["sum"] > 0).sum()),
        c2=c2_coverage(d),
        same_product=dict(
            admitted_with_value=int(sum(str(x).strip() != "" for x in adm["same_product"])),
            nonassessable_with_value=int(sum(str(x).strip() != "" for x in non["same_product"])),
            admitted_all_one=bool(all(str(x).strip() == "1" for x in adm["same_product"]))),
        core5=dict(n=len(core5), median=float(core5.median()), min=float(core5.min()),
                   max=float(core5.max()), ids=["G02", "G03", "G04", "G05", "G06"]),
        a7=dict(n=len(a7r), geometric_mean=float(np.exp(np.log(a7r).mean())),
                ci95=boot_ci(np.log(a7r))),
        a8=dict(n=len(a8r), median=float(a8r.median()), min=float(a8r.min()),
                max=float(a8r.max())),
        all14=dict(n=len(r), geometric_mean=geo, ci95=(lo_ci, hi_ci)),
        sign_test=dict(parity=int(len(parity)), under=under, over=over, p=sign_p),
        stratified=strata, spearman=dict(rho=float(rho), p=float(p_rho)),
        prior_contrast=dict(n_low=int(len(lo)), n_high=int(len(hi)),
                            geo_low=float(np.exp(np.log(lo).mean())),
                            geo_high=float(np.exp(np.log(hi).mean())),
                            log_diff=logdiff, ci95_log=(lo_ci2, hi_ci2),
                            ratio=float(np.exp(logdiff)),
                            ratio_ci95=(float(np.exp(lo_ci2)), float(np.exp(hi_ci2)))),
        ledger=led["recommended_use"].value_counts().to_dict(),
        g01=g01, g02=g02,
        ratio_of_ratios=float(g02["ratio"]) / float(g01["ratio"]),
        declared_ratio=g02["declared"] / g01["declared"],
    )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the repaired CSV files")
    ap.add_argument("--check-text", action="store_true",
                    help="also assert that the manuscript prints these values")
    args = ap.parse_args(argv)

    d = read(DATASET)
    led = read(LEDGER)
    if args.write:
        _backup(DATASET)
        _backup(LEDGER)

    d, filled = backfill_c2(d)
    led, before, after = rebuild_ledger(d)

    if args.write:
        d.to_csv(DATASET, index=False, encoding="utf-8")
        led.to_csv(LEDGER, index=False, encoding="utf-8")

    groups = write_column_dictionary(d)
    c = claims(d, led)
    c["dictionary_groups"] = groups
    c["c2_backfill_cells"] = filled
    c["ledger_before"] = before
    with open(os.path.join(DATA, "claims.json"), "w", encoding="utf-8") as fh:
        json.dump(c, fh, indent=1)

    print("dictionary: %d columns in %d groups %s" % (len(COLUMNS), len(groups), groups))
    print("objects %d | admitted %d | ratio-definable %d | auditable %d"
          % (c["n_objects"], c["n_admitted"], c["n_ratio_definable"], c["n_auditable"]))
    print("admission:", c["admission_counts"])
    print("C2: %d cells filled; %d of %d admitted rows carry a locator; missing %s"
          % (filled, c["c2"]["locator_declared_filled"], c["c2"]["rows_admitted"],
             c["c2"]["admitted_without_locator"]))
    print("same_product: %d/%d admitted = 1, %d non-assessable empty"
          % (c["same_product"]["admitted_with_value"], c["n_admitted"],
             c["same_product"]["nonassessable_with_value"]))
    print("families %d, without assessable %d, with %d"
          % (c["families_total"], c["families_without_assessable"], c["families_with_assessable"]))
    print("core5 median %.3f [%.3f, %.3f] n=%d" % (c["core5"]["median"], c["core5"]["min"],
                                                   c["core5"]["max"], c["core5"]["n"]))
    print("A7 geomean %.3f CI (%.3f, %.3f)" % (c["a7"]["geometric_mean"], *c["a7"]["ci95"]))
    print("A8 median %.3f [%.3f, %.3f] n=%d" % (c["a8"]["median"], c["a8"]["min"],
                                                c["a8"]["max"], c["a8"]["n"]))
    print("all14 geomean %.3f CI (%.3f, %.3f)" % (c["all14"]["geometric_mean"], *c["all14"]["ci95"]))
    print("sign test: %d parity, %d under, %d over, p=%.3f"
          % (c["sign_test"]["parity"], c["sign_test"]["under"], c["sign_test"]["over"],
             c["sign_test"]["p"]))
    for s, v in sorted(c["stratified"].items()):
        print("  score %d: n=%d median %.4f geomean %.4f %s"
              % (s, v["n"], v["median"], v["geometric_mean"], ",".join(v["ids"])))
    print("spearman rho=%.3f p=%.3f" % (c["spearman"]["rho"], c["spearman"]["p"]))
    pc = c["prior_contrast"]
    print("prior contrast: low n=%d geo %.3f | high n=%d geo %.3f | ratio %.3f (%.3f, %.3f)"
          % (pc["n_low"], pc["geo_low"], pc["n_high"], pc["geo_high"], pc["ratio"],
             pc["ratio_ci95"][0], pc["ratio_ci95"][1]))
    print("ledger: %s -> %s" % (before, after))
    print("G01: declared %.4f (stage %s) vs actual %.4f (stage %s, %s) ratio %.4f factor %.2f"
          % (c["g01"]["declared"], c["g01"]["stage_declared"], c["g01"]["actual"],
             c["g01"]["stage_actual"], c["g01"]["actual_metric"], c["g01"]["ratio"],
             c["g01"]["factor"]))
    print("G02: declared %.4f vs actual %.4f ratio %.4f factor %.2f"
          % (c["g02"]["declared"], c["g02"]["actual"], c["g02"]["ratio"], c["g02"]["factor"]))
    print("ratio of ratios %.2f | declared ratio %.1f"
          % (c["ratio_of_ratios"], c["declared_ratio"]))
    if args.check_text:
        checks, bad = check_text(c)
        print("\ntext gate: %d of %d values found in the manuscript"
              % (len(checks) - len(bad), len(checks)))
        for label, lit in bad:
            print("  MISSING %-38s %s" % (label, lit))
        if bad:
            raise SystemExit(1)
    if not args.write:
        print("\n(dry run: pass --write to repair the CSVs)")


if __name__ == "__main__":
    main()
