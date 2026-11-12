# -*- coding: utf-8 -*-
"""Emit the four manuscript tables as LaTeX fragments from the CSV sources."""
import csv
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
TEX = os.path.join(BASE, "tex")
os.makedirs(TEX, exist_ok=True)

rows = list(csv.DictReader(open(os.path.join(DATA, "p3_dataset.csv"), encoding="utf-8-sig")))
ledger = list(csv.DictReader(open(os.path.join(DATA, "p3_declared_ledger.csv"), encoding="utf-8-sig")))
stats = json.load(open(os.path.join(DATA, "stats.json")))

ESC = {"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#", "$": r"\$"}


def e(s):
    for k, v in ESC.items():
        s = s.replace(k, v)
    return s


def fam(v):
    return "sea ice thickness" if v.startswith("sea ice thickness") else v


def short(s, n):
    s = e(s).replace("/", "\\slash ")
    if len(s) <= n:
        return s
    cut = s[:n]
    return (cut[:cut.rfind(" ")] if cut.rfind(" ") > n // 2 else cut[:-1]) + "."


# ---------------------------------------------------------------- table 1
DISPLAY = {"forest aboveground biomass": "forest biomass",
           "ocean colour chlorophyll": "ocean colour"}
EV = {"raw_file_attribute": "RFA", "product_document_text": "PDT",
      "third_party_literature": "TPL", "recomputation": "REC"}
fams = sorted({fam(r["variable"]) for r in rows})
lines = []
for f in fams:
    g = [r for r in rows if fam(r["variable"]) == f]
    a = [r for r in g if r["assessable"] == "1"]
    l = [r for r in ledger if fam(r["variable"]) == f]
    evt = ", ".join(sorted({EV.get(r["evidence_type"], e(r["evidence_type"])) for r in l})) if l else "--"
    lines.append(f"{e(DISPLAY.get(f, f))} & {len(g)} & {len(a)} & {len(l)} & {evt} \\\\")
open(os.path.join(TEX, "table1_composition.tex"), "w").write(
    "\\begin{table}[t]\n\\caption{Composition of the compilation by variable family: "
    "catalogued objects, assessable objects, records in the declared-uncertainty ledger, "
    "and the provenance class of the declared value (RFA, raw file attribute; PDT, product "
    "documentation text; TPL, third-party literature; REC, recomputation).}\\label{tab:1}\n"
    "\\footnotesize\n\\setlength{\\tabcolsep}{4pt}\n"
    "\\resizebox{\\linewidth}{!}{%\n"
    "\\begin{tabular}{@{}p{4.3cm}rrrp{2.6cm}@{}}\n\\toprule\n"
    "Variable family & Catalogued & Assessable & Ledger & Provenance \\\\\n"
    "\\midrule\n" + "\n".join(lines) + "\n\\midrule\n"
    f"Total & {len(rows)} & {len([r for r in rows if r['assessable']=='1'])} & {len(ledger)} & four classes \\\\\n"
    "\\bottomrule\n\\end{tabular}}\n\\end{table}\n")

# ---------------------------------------------------------------- table 2
VAR = {"sea ice thickness": "SIT", "sea ice concentration": "SIC",
       "surface soil moisture": "SM", "aerosol optical depth": "AOD",
       "leaf area index": "LAI", "sea surface temperature": "SST",
       "sea surface salinity": "SSS", "snow water equivalent": "SWE",
       "snow cover": "SCA", "forest aboveground biomass": "AGB",
       "precipitation": "PREC", "land surface temperature": "LST",
       "ocean colour chlorophyll": "CHL", "sea level anomaly": "SLA",
       "evapotranspiration": "ET", "freeze/thaw state": "FT"}
lines = []
DOI2KEY = {v: k for k, v in json.load(open(os.path.join(DATA, "ref_keys.json"), encoding="utf-8")).items()}


def src(r):
    ks = []
    for f in ("declared_doi", "actual_doi"):
        k = DOI2KEY.get((r.get(f) or "").strip())
        if k and k not in ks:
            ks.append(k)
    return "\\citep{" + ",".join(ks) + "}" if ks else "--"


for r in rows:
    decl = r["declared_value"] + " " + r["declared_unit"] if r["declared_value"] else "no public value"
    act = r["actual_value"] + " " + r["actual_unit"] if r["actual_value"] else "--"
    ratio = r["ratio"] if r["ratio"] else "--"
    if ratio != "--" and r.get("ratio_relation") != "point":
        ratio = ratio + "$^{*}$"
    lines.append(f"{r['group_id']} & {short(r['product'], 38)} & {VAR.get(fam(r['variable']), '--')} & "
                 f"{e(decl)} & {e(act)} & {ratio} & {src(r)} \\\\")
CAP2 = ("Inventory of the 50 catalogued objects. Declared and audited values are in "
        "the product's own unit; an asterisk in the Ratio column marks a record whose "
        "ratio is a bound rather than a point estimate; a dash marks a row with no "
        "public declared value or no numeric measured error (catalogue only); the last "
        "column cites the source of the declared and audited values.")
open(os.path.join(TEX, "table2_inventory.tex"), "w").write(
    "\\scriptsize\n\\setlength{\\tabcolsep}{3pt}\n"
    "\\begin{longtable}{@{}l p{2.4cm} l r r r p{2.3cm}@{}}\n"
    "\\caption{" + CAP2 + "}\\label{tab:2}\\\\\n"
    "\\toprule\n"
    "ID & Product & Var. & Declared & Audited & Ratio & Source \\\\\n\\midrule\n\\endfirsthead\n"
    "\\toprule\nID & Product & Var. & Declared & Audited & Ratio & Source \\\\\n\\midrule\n\\endhead\n"
    + "\n".join(lines) + "\n\\bottomrule\n\\end{longtable}\n")

# ---------------------------------------------------------------- table 3
S = stats["sets"]


def fmt(x, nd=3):
    return f"{x:.{nd}f}"


def ci(d, key="geometric_mean_ci95"):
    a, b = d[key]
    return f"[{fmt(a)}, {fmt(b)}]"


rows3 = []
for label, key in (("Core set, A (object matched, grade A)", "core_A_legacy5"),
                   ("Core set, all assessable", "core_legacy8"),
                   ("Set A: auditable core, grade A", "A_objectmatched_gradeA"),
                   ("Set B: adds support-caveated records", "B_objectmatched_AB"),
                   ("Set C: all ratio-definable records", "C_all_assessable")):
    d = S[key]
    rows3.append(f"{label} & {d['n']} & {fmt(d['median'])} & {fmt(d['geometric_mean'])} {ci(d)} & "
                 f"{fmt(d['min'])}--{fmt(d['max'])} & {fmt(d['rho_prior'],2)} ({fmt(d['p_prior'],2)}) & "
                 f"{d['under_report_n']}/{d['over_report_n']}/{d['parity_n']} \\\\")
open(os.path.join(TEX, "table3_statistics.tex"), "w").write(
    "\\begin{table}[t]\n\\caption{Ratio statistics for the nested sets: number of "
    "records, median, geometric mean with a 95\\,\\% percentile bootstrap interval, "
    "range, Spearman correlation with the prior-dependence score ($p$ value), and the "
    "count of under-reporting, over-reporting and parity records.}\\label{tab:3}\n"
    "\\footnotesize\n\\resizebox{\\linewidth}{!}{%\n"
    "\\begin{tabular}{@{}p{4.0cm} r r l l l r@{}}\n\\toprule\n"
    "Set & $n$ & Median & Geom. mean [95\\% CI] & Range & $\\rho$ ($p$) & under/over/parity \\\\\n\\midrule\n"
    + "\n".join(rows3) + "\n\\bottomrule\n\\end{tabular}}\n\\end{table}\n")

# ---------------------------------------------------------------- table 4
EVID_SHORT = {
    "raw_file_attribute": "raw attribute",
    "product_document_text": "product doc.",
    "recomputation": "recomp.",
    "third_party_literature": "literature",
}
USE_SHORT = {
    "replace declared sigma with audited value": "replace",
    "retain declared value": "retain",
    "use only with the statistic mismatch stated": "caveat (stat.)",
    "use only with the support mismatch stated": "caveat (supp.)",
    "do not use as a sigma; publish a declared value first": "no sigma",
}
lines = []
for r in ledger:
    ratio = r["unified_ratio_declared_over_actual"] or "--"
    use = USE_SHORT.get(r["recommended_use"], e(r["recommended_use"]))
    lines.append(f"{r['group_id']} & {short(r['product'], 38)} & {e(r['declared_as_published'])} & "
                 f"{e(r['audited_reference_error'] or '--')} & {ratio} & {e(r['direction']).replace('/', '\\slash ')} & "
                 f"{use} & {EVID_SHORT.get(r['evidence_type'], e(r['evidence_type']).replace('_', ' '))} \\\\")
open(os.path.join(TEX, "table4_ledger.tex"), "w").write(
    "\\scriptsize\n\\setlength{\\tabcolsep}{3pt}\n"
    "\\begin{longtable}{@{}l p{2.05cm} p{1.6cm} p{1.6cm} r p{1.25cm} p{1.4cm} p{1.35cm}@{}}\n"
    "\\caption{The 17-row correction ledger: declared value as published, audited "
    "reference error, unified ratio (declared divided by actual), direction, "
    "recommended use and provenance class. Use is derived from the audit verdict, so "
    "the ledger cannot recommend a record this paper refuses: \\emph{replace} = the "
    "audited value supersedes the declared one; \\emph{retain} = the declaration is "
    "confirmed; \\emph{caveat} (stat.\\ or supp.) = usable only with the stated "
    "statistic or support mismatch; \\emph{no sigma} = the declaration cannot be "
    "exchanged with an error magnitude. A dash in the Ratio column marks a bound-only "
    "record, whose ratio is not a point estimate and is shown in Table~\\ref{tab:2} and Fig.~\\ref{fig:2}.}"
    "\\label{tab:4}\\\\\n\\toprule\n"
    "ID & Product & Declared & Audited & Ratio & Direction & Use & Source \\\\\n\\midrule\n\\endfirsthead\n"
    "\\toprule\nID & Product & Declared & Audited & Ratio & Direction & Use & Source \\\\\n\\midrule\n\\endhead\n"
    + "\n".join(lines) + "\n\\bottomrule\n\\end{longtable}\n")

print("tables written")
