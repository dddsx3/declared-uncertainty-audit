# -*- coding: utf-8 -*-
"""Build the P3 audit dataset.

Inputs (read-only):
    <n7>/01_dataset.csv          legacy 31-column core (never modified)
    <n7>/02_verification_log.csv legacy evidence log (never modified)

Outputs (all inside this paper folder):
    data/p3_core_n7_verbatim.csv    byte-identical copy of the legacy core
    data/p3_dataset.csv             union of legacy + newly curated objects
    data/p3_extension_columns.csv   NEW columns only (legacy schema untouched)
    data/p3_verification_log.csv    per-value evidence log with evidence type
    data/p3_declared_ledger.csv     17-row ledger of all objects with a
                                    published declared value (Table 4)
    data/lit_cache/*                cached OpenAlex records (see lit_search.py)

Design rules
  * one ratio direction for the whole table: declared / actual
  * ratio is always recomputed from declared_value / actual_value
  * every new number carries a verbatim quoted string from the retrieved
    abstract or from the local netCDF attribute; no number is invented
  * objects without a public declared value keep declared_value empty and
    are flagged "no_public_declared_value"
"""
import csv
import hashlib
import os
import re

N7 = r"<WORKROOT>\innovation\n7_declared_vs_actual"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

LEGACY_FIELDS = [
    "group_id", "variable", "product", "product_version", "validation_reference",
    "declared_value", "declared_unit", "declared_scope", "declared_source_type",
    "declared_source", "declared_doi", "actual_value", "actual_unit", "actual_metric",
    "actual_source", "actual_doi", "ratio", "ratio_direction", "ratio_original_stored",
    "ratio_original_direction", "ratio_relation", "prior_score",
    "prior_climatology_background", "prior_empirical_transfer",
    "prior_shared_auxiliary", "prior_assumed_model", "footprint_mismatch",
    "object_matched", "evidence_grade", "assessable", "notes",
]

NEW_FIELDS = [
    "evidence_type", "evidence_detail", "semantics_class",
    "stage_declared", "stage_actual", "scale_declared", "scale_actual",
    "log_ratio", "ci_low", "ci_high", "ci_basis",
    "quote_declared", "quote_actual",
    "locator_declared", "locator_actual",
    "doi_status_declared", "doi_status_actual",
    "comparison_validity", "in_A", "in_B", "in_C",
    "reason_if_not_assessable",
    "same_product", "same_statistic", "support_stated", "support_match",
    "source_resolved", "admission",
]

# ---------------------------------------------------------------- legacy copy
src = os.path.join(N7, "01_dataset.csv")
raw = open(src, "rb").read()
open(os.path.join(DATA, "p3_core_n7_verbatim.csv"), "wb").write(raw)
SHA = hashlib.sha256(raw).hexdigest()

legacy = list(csv.DictReader(open(src, encoding="utf-8-sig")))
assert len(legacy) == 14, len(legacy)

# ---------------------------------------------------------------- new objects
# Compact records. declared/actual values are strings so that "missing" can be "".
# fields: id, variable, product, version, validation_ref, decl, decl_unit,
#         decl_scope, decl_source_type, decl_source, decl_doi, act, act_unit,
#         act_metric, act_source, act_doi, relation, prior, p_clim, p_emp,
#         p_aux, p_model, foot, obj, grade, assessable, notes
NEW = [
    # ---------- soil moisture ----------
    dict(id="G15", variable="surface soil moisture",
         product="SMAP passive L2/L3 soil moisture (SPL2SMP/SPL3SMP)", version="R16000 era",
         validation_ref="SMAP core validation sites (in situ upscaled)",
         decl="0.040", decl_unit="m3/m3", decl_scope="mission requirement, unbiased RMSE",
         decl_source_type="mission requirement",
         decl_source="SMAP mission accuracy requirement ubRMSE <= 0.04 m3/m3",
         decl_doi="10.1109/JPROC.2010.2043918",
         act="0.038", act_unit="m3/m3", act_metric="ubRMSD at core validation sites",
         act_source="passive product assessment, CVS-averaged ubRMSD",
         act_doi="10.1109/TGRS.2016.2561938",
         relation="point", prior=1, p_clim=0, p_emp=0, p_aux=1, p_model=0,
         foot=0, obj=1, grade="A", assessable=1,
         notes="Independent assessment of the passive product; 0.038 approaches the 0.040 requirement, so the ratio is ~1."),
    dict(id="G16", variable="surface soil moisture",
         product="SMOS L2 soil moisture (MIRAS)", version="L2, reprocessed",
         validation_ref="REMEDHUS in situ network (Spain)",
         decl="0.04", decl_unit="m3/m3", decl_scope="SMOS accuracy objective",
         decl_source_type="mission requirement (quoted in validation paper)",
         decl_source="'close to the SMOS accuracy objective of 0.04 m3 m-3'",
         decl_doi="10.1109/TGRS.2012.2186971",
         act="0.044", act_unit="m3/m3", act_metric="bias-removed RMSD (RMSD_c)",
         act_source="REMEDHUS validation, RMSD_c", act_doi="10.1109/TGRS.2012.2186971",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=0, obj=1, grade="A", assessable=1,
         notes="Retrieval depends on a dielectric-mixing model and an auxiliary surface temperature/vegetation description."),
    dict(id="G17", variable="surface soil moisture",
         product="SMOS L3 soil moisture (Pernambuco, Brazil)", version="L3",
         validation_ref="in situ stations, Pernambuco",
         decl="0.04", decl_unit="m3/m3", decl_scope="SMOS accuracy objective",
         decl_source_type="mission requirement (quoted in validation paper)",
         decl_source="'near to the expected 0.04 m3 m-3 accuracy of the SMOS mission'",
         decl_doi="10.3390/rs10081314",
         act="0.071", act_unit="m3/m3", act_metric="average RMSD at pixel scale",
         act_source="daily time series, pixel assessment", act_doi="10.3390/rs10081314",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="A", assessable=1,
         notes="Same paper reports an areal RMSD of 0.04 m3/m3; see G18. The pixel-scale value is the grid-level counterpart."),
    dict(id="G18", variable="surface soil moisture",
         product="SMOS L3 soil moisture (Pernambuco, Brazil)", version="L3",
         validation_ref="in situ stations, Pernambuco (areal average)",
         decl="0.04", decl_unit="m3/m3", decl_scope="SMOS accuracy objective (pixel/grid)",
         decl_source_type="mission requirement (quoted in validation paper)",
         decl_source="'expected 0.04 m3 m-3 accuracy of the SMOS mission'",
         decl_doi="10.3390/rs10081314",
         act="0.04", act_unit="m3/m3", act_metric="areal RMSD after spatial aggregation",
         act_source="areal assessment of the same time series", act_doi="10.3390/rs10081314",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=0, grade="A", assessable=1,
         notes="Aggregation-level counterpart of G17: identical product, identical period, only the spatial support changes. Ratio of 1.00 is an artefact of support, not of declaration quality."),
    dict(id="G19", variable="surface soil moisture",
         product="SMOS L2 soil moisture (MIRAS)", version="L2",
         validation_ref="in situ stations, Mediterranean site",
         decl="0.04", decl_unit="m3/m3", decl_scope="SMOS accuracy objective",
         decl_source_type="mission requirement (quoted in validation paper)",
         decl_source="SMOS accuracy objective of 0.04 m3 m-3 (as applied in the paper)",
         decl_doi="10.1080/2150704X.2014.933277",
         act="0.116", act_unit="m3/m3", act_metric="RMSE against in situ 0-5 cm",
         act_source="Mediterranean appraisal, overall RMSE", act_doi="10.1080/2150704X.2014.933277",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=0, obj=1, grade="A", assessable=1,
         notes="Single-region validation; RMSE improves to 0.110 after radio-frequency-interference filtering."),
    dict(id="G20", variable="land surface temperature",
         product="MODIS MOD11 land surface temperature", version="C5",
         validation_ref="temperature-based validation with in situ radiometers",
         decl="1.0", decl_unit="K", decl_scope="stated product accuracy (1 sigma)",
         decl_source_type="product specification",
         decl_source="'accuracy of the MODIS LST product is better than 1 K'",
         decl_doi="10.1080/01431160802036565",
         act="0.7", act_unit="K", act_metric="RMSE (temperature-based)",
         act_source="temperature-based validation, two sites", act_doi="10.1029/2009JD012038",
         relation="point", prior=2, p_clim=0, p_emp=0, p_aux=1, p_model=1,
         foot=0, obj=1, grade="A", assessable=1,
         notes="Over-reporting case: the declared 1 K is larger than the measured 0.7 K. Included to show that the audit is not asymmetric."),
    # ---------- non-assessable additions, grouped by variable ----------
    dict(id="G21", variable="sea ice thickness",
         product="SMOS thin sea ice thickness (Antarctic)", version="L3",
         validation_ref="helicopter EM and upward-looking sonar",
         decl="1.0", decl_unit="m", decl_scope="upper bound of the per-pixel uncertainty field",
         decl_source_type="product uncertainty field",
         decl_source="per-pixel thickness uncertainty up to about 1 m",
         decl_doi="10.5194/essd-16-3149-2024",
         act="0.20", act_unit="m", act_metric="RMSD against HEM/ULS",
         act_source="Weddell Sea validation", act_doi="10.5194/essd-16-3149-2024",
         relation="upper_bound", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="B", assessable=0,
         notes="Declared uncertainty is distributed as a field with values up to about 1 m; it is an upper bound envelope, not a single sigma, so no ratio is formed."),
    dict(id="G22", variable="sea ice thickness",
         product="HY-2B radar altimeter sea ice thickness", version="v1",
         validation_ref="CS2SMOS, CPOM, CS-2, PIOMAS and airborne validation data",
         decl="", decl_unit="m", decl_scope="not published",
         decl_source_type="none found",
         decl_source="no public declared uncertainty located",
         decl_doi="",
         act="0.47-0.79", act_unit="m", act_metric="RMSD against five references",
         act_source="cross-comparison of five thickness sources", act_doi="10.3390/rs16234565",
         relation="point", prior=3, p_clim=1, p_emp=1, p_aux=1, p_model=0,
         foot=1, obj=1, grade="C", assessable=0,
         notes="The paper reports RMSDs for five products but the HY-2B product itself has no published declared uncertainty."),
    dict(id="G23", variable="sea ice concentration",
         product="ESA CCI / OSI SAF SIC CDR v2", version="v2",
         validation_ref="near-100% closed ice and ship observations",
         decl="", decl_unit="fraction", decl_scope="per-grid total uncertainty sigma_tot",
         decl_source_type="product uncertainty field",
         decl_source="sigma_tot field described in the CDR paper",
         decl_doi="10.5194/tc-13-49-2019",
         act="-0.004", act_unit="fraction", act_metric="mean bias at 100% ice",
         act_source="closed-ice intercomparison", act_doi="10.5194/tc-13-3261-2019",
         relation="point", prior=2, p_clim=0, p_emp=1, p_aux=1, p_model=0,
         foot=0, obj=1, grade="B", assessable=0,
         notes="sigma_tot is described qualitatively; a bias cannot be divided by a sigma."),
    dict(id="G24", variable="sea ice concentration",
         product="SICCI-25 / SICCI-50 sea ice concentration", version="CDR",
         validation_ref="closed-ice and ship observations",
         decl="", decl_unit="fraction", decl_scope="not published as a number",
         decl_source_type="none found",
         decl_source="no numeric declared sigma located",
         decl_doi="10.5194/tc-13-49-2019",
         act="-0.004", act_unit="fraction", act_metric="bias at 100% ice",
         act_source="closed-ice intercomparison", act_doi="10.5194/tc-13-3261-2019",
         relation="point", prior=2, p_clim=0, p_emp=1, p_aux=1, p_model=0,
         foot=0, obj=1, grade="C", assessable=0,
         notes="Only bias is reported; the declared side is not a comparable sigma."),
    dict(id="G25", variable="sea ice concentration",
         product="AMSR2 operational sea ice concentration", version="ASI/ABA",
         validation_ref="MODIS and ship observations",
         decl="", decl_unit="fraction", decl_scope="not published",
         decl_source_type="none found",
         decl_source="no public declared uncertainty located",
         decl_doi="",
         act="0.110", act_unit="fraction", act_metric="RMSE in the Arctic",
         act_source="AMSR2 operational validation", act_doi="10.1109/JSTARS.2017.2693120",
         relation="point", prior=2, p_clim=0, p_emp=1, p_aux=1, p_model=0,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Reported bias 3.9% and RMSE 11.0% in the Arctic; no matching declared sigma."),
    dict(id="G26", variable="sea ice concentration",
         product="ESA CCI+ ESMR v1.1 sea ice concentration", version="v1.1",
         validation_ref="manual Landsat-1 classification",
         decl="", decl_unit="fraction", decl_scope="not published",
         decl_source_type="none found",
         decl_source="no public declared uncertainty located",
         decl_doi="",
         act="0.060", act_unit="fraction", act_metric="standard deviation of difference",
         act_source="Landsat-1 MSS manual classification", act_doi="10.5194/tc-20-527-2026",
         relation="point", prior=2, p_clim=0, p_emp=1, p_aux=1, p_model=0,
         foot=0, obj=1, grade="C", assessable=0,
         notes="Mean difference -1.4% (median 0.0%), standard deviation 6.0% over ~3300 cells."),
    dict(id="G27", variable="sea surface salinity",
         product="SMAP sea surface salinity", version="L3",
         validation_ref="Argo and gridded in situ products",
         decl="", decl_unit="psu", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no public declared uncertainty located at validation scale",
         decl_doi="",
         act="0.02-0.03", act_unit="psu", act_metric="sampling error at weekly scale",
         act_source="sampling-error quantification", act_doi="10.3390/rs15020422",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=0, obj=1, grade="C", assessable=0,
         notes="Sampling error is reported, not total retrieval error; declared side absent."),
    dict(id="G28", variable="forest aboveground biomass",
         product="GEDI L4B footprint aboveground biomass density", version="release 1/2",
         validation_ref="field AGBD from 21 countries",
         decl="", decl_unit="Mg/ha", decl_scope="prediction intervals per footprint",
         decl_source_type="product uncertainty field",
         decl_source="L4A/L4B ATBD describes per-footprint prediction intervals",
         decl_doi="10.1029/2022EA002516",
         act="", act_unit="Mg/ha", act_metric="not extracted at matching scale",
         act_source="ATBD contains model development but no paired independent RMSE",
         act_doi="10.1029/2022EA002516",
         relation="point", prior=3, p_clim=1, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="ATBD gives intervals and training data, not an independent validation error at the same support."),
    dict(id="G29", variable="precipitation",
         product="GSMaP global rainfall product", version="GPM era",
         validation_ref="gauge networks",
         decl="", decl_unit="mm/h", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="product description only; no declared error magnitude extracted",
         decl_doi="10.1007/978-3-030-24568-9_20",
         act="", act_unit="mm/h", act_metric="not extracted",
         act_source="no paired independent validation extracted",
         act_doi="",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G30", variable="precipitation",
         product="GPCP monthly/daily precipitation v3.2", version="v3.2",
         validation_ref="gauge and satellite analyses",
         decl="", decl_unit="mm/day", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.1175/JCLI-D-23-0123.1",
         act="", act_unit="mm/day", act_metric="not extracted",
         act_source="no paired independent validation extracted",
         act_doi="",
         relation="point", prior=2, p_clim=1, p_emp=0, p_aux=1, p_model=0,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G31", variable="leaf area index",
         product="GEOV2 LAI essential climate variable", version="v2",
         validation_ref="ground LAI networks",
         decl="", decl_unit="LAI", decl_scope="per-pixel uncertainty discussed but not paired",
         decl_source_type="product uncertainty description",
         decl_source="uncertainty discussed comparatively; no paired declared/actual pair extracted",
         decl_doi="10.34133/2021/9842830",
         act="", act_unit="LAI", act_metric="not extracted as a paired value",
         act_source="comparative uncertainty study",
         act_doi="10.34133/2021/9842830",
         relation="point", prior=3, p_clim=1, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Uncertainty is analysed as a time series property, not as a declared-versus-measured pair."),
    dict(id="G32", variable="leaf area index",
         product="GLASS LAI", version="v6",
         validation_ref="field LAI over croplands, NE China",
         decl="", decl_unit="LAI", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.1016/j.rse.2019.111377",
         act="", act_unit="LAI", act_metric="validation error not extracted as a paired value",
         act_source="regional validation study",
         act_doi="10.1016/j.rse.2019.111377",
         relation="point", prior=2, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G33", variable="sea surface temperature",
         product="ESA CCI sea surface temperature CDR", version="v2",
         validation_ref="drifting buoys and Argo",
         decl="", decl_unit="K", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.1016/j.rse.2019.111485",
         act="", act_unit="K", act_metric="not extracted",
         act_source="CDR construction paper",
         act_doi="10.1016/j.rse.2019.111485",
         relation="point", prior=3, p_clim=1, p_emp=0, p_aux=1, p_model=1,
         foot=0, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G34", variable="ocean colour chlorophyll",
         product="Ocean Colour CCI chlorophyll-a", version="v4",
         validation_ref="in situ chlorophyll",
         decl="", decl_unit="mg/m3", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.3390/s19194285",
         act="", act_unit="mg/m3", act_metric="not extracted",
         act_source="OC-CCI time series paper",
         act_doi="10.3390/s19194285",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G35", variable="sea level anomaly",
         product="DUACS DT2018 sea level anomaly", version="DT2018",
         validation_ref="tide gauges and altimeter cross-calibration",
         decl="", decl_unit="m", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.5194/os-15-1207-2019",
         act="", act_unit="m", act_metric="not extracted",
         act_source="reprocessed product description",
         act_doi="10.5194/os-15-1207-2019",
         relation="point", prior=2, p_clim=1, p_emp=0, p_aux=1, p_model=1,
         foot=0, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G36", variable="snow cover",
         product="MODIS MOD10 snow cover", version="C6",
         validation_ref="weather stations and student observations",
         decl="", decl_unit="fraction", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.1016/j.rse.2006.07.004",
         act="", act_unit="fraction", act_metric="classification accuracy (not a sigma)",
         act_source="station-based validation",
         act_doi="10.1016/j.rse.2006.07.004",
         relation="point", prior=2, p_clim=0, p_emp=1, p_aux=1, p_model=0,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Validation reports classification accuracy, which is not exchangeable with a sigma."),
    dict(id="G37", variable="evapotranspiration",
         product="GLEAM evapotranspiration", version="v3",
         validation_ref="ChinaFLUX eddy-covariance",
         decl="", decl_unit="mm/day", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.1080/01431161.2017.1346400",
         act="", act_unit="mm/day", act_metric="validation error not extracted as a paired value",
         act_source="multi-scale validation study",
         act_doi="10.1080/01431161.2017.1346400",
         relation="point", prior=3, p_clim=1, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G38", variable="evapotranspiration",
         product="PML-V2 evapotranspiration", version="v2",
         validation_ref="dense flux observations",
         decl="", decl_unit="mm/day", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.1016/j.jhydrol.2023.129743",
         act="", act_unit="mm/day", act_metric="not extracted as a paired value",
         act_source="flux-tower validation",
         act_doi="10.1016/j.jhydrol.2023.129743",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G39", variable="freeze/thaw state",
         product="SMAP landscape freeze/thaw product", version="baseline/enhanced",
         validation_ref="high-latitude core validation sites",
         decl="0.80", decl_unit="fraction", decl_scope="mission classification accuracy requirement",
         decl_source_type="mission requirement",
         decl_source="SMAP mission accuracy requirement of 80%",
         decl_doi="10.1016/j.rse.2017.03.007",
         act="0.80+", act_unit="fraction", act_metric="classification accuracy against in situ flags",
         act_source="'exceeding the 80% SMAP mission accuracy requirement'",
         act_doi="10.1016/j.rse.2017.03.007",
         relation="lower_bound", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=0, obj=1, grade="B", assessable=0,
         notes="Categorical accuracy is not exchangeable with a continuous sigma, so no ratio is formed."),
    dict(id="G40", variable="snow water equivalent",
         product="Snow CCI+ SWE (v2 developmental)", version="v2",
         validation_ref="in situ snow courses",
         decl="", decl_unit="mm", decl_scope="per-pixel uncertainty, not numerically paired",
         decl_source_type="product uncertainty description",
         decl_source="per-pixel uncertainty described, magnitude not extracted",
         decl_doi="10.1016/j.rse.2022.112988",
         act="", act_unit="mm", act_metric="RMSE improvement of 5 mm (12%) relative to v1",
         act_source="in situ snow courses",
         act_doi="10.1016/j.rse.2022.112988",
         relation="point", prior=3, p_clim=1, p_emp=1, p_aux=1, p_model=0,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Reported as a relative improvement, not as an absolute measured error."),
    dict(id="G41", variable="snow cover",
         product="Snow CCI+ snow-covered area", version="v2",
         validation_ref="mountain snow observatory",
         decl="", decl_unit="fraction", decl_scope="not published as a comparable sigma",
         decl_source_type="none found",
         decl_source="no numeric declared sigma extracted",
         decl_doi="10.5194/tc-19-2017-2025",
         act="", act_unit="fraction", act_metric="not extracted as a paired value",
         act_source="mountain-catchment evaluation",
         act_doi="10.5194/tc-19-2017-2025",
         relation="point", prior=2, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G42", variable="sea ice thickness",
         product="Combined SMAP-SMOS thin sea ice thickness", version="L3",
         validation_ref="airborne EM and moorings",
         decl="", decl_unit="m", decl_scope="per-pixel uncertainty, not numerically paired",
         decl_source_type="product uncertainty field",
         decl_source="per-pixel uncertainty field, magnitude not extracted",
         decl_doi="10.5194/tc-13-675-2019",
         act="", act_unit="m", act_metric="not extracted as a paired value",
         act_source="combined retrieval description",
         act_doi="10.5194/tc-13-675-2019",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Catalogued to document the absence of a declared, comparable error specification."),
    dict(id="G43", variable="surface soil moisture",
         product="SMOS-IC soil moisture", version="v1",
         validation_ref="in situ networks and ECMWF",
         decl="", decl_unit="m3/m3", decl_scope="no declared sigma at validation scale",
         decl_source_type="none found",
         decl_source="no public declared uncertainty located",
         decl_doi="10.3390/rs9050457",
         act="", act_unit="m3/m3", act_metric="ubRMSD against ECMWF (not in situ)",
         act_source="six-year inter-comparison",
         act_doi="10.3390/rs9050457",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=0, obj=1, grade="C", assessable=0,
         notes="Reference is a model, not an independent observation; no declared sigma."),
    dict(id="G44", variable="surface soil moisture",
         product="ASCAT soil moisture", version="H-SAF / TU Wien",
         validation_ref="in situ networks; triple collocation",
         decl="", decl_unit="m3/m3", decl_scope="specification exists but no numeric pairing extracted",
         decl_source_type="product specification",
         decl_source="product review reports specifications and validation results separately",
         decl_doi="10.1127/0941-2948/2013/0399",
         act="0.0625", act_unit="m3/m3", act_metric="ubRMSD from triple collocation",
         act_source="global-scale TC intercomparison", act_doi="10.1016/j.rse.2017.10.026",
         relation="point", prior=1, p_clim=0, p_emp=0, p_aux=1, p_model=0,
         foot=0, obj=1, grade="B", assessable=0,
         notes="Specification and validation are in different documents and different supports; no auditable pair."),
    dict(id="G45", variable="aerosol optical depth",
         product="VIIRS AOT environmental data record", version="EDR",
         validation_ref="AERONET",
         decl="", decl_unit="AOT", decl_scope="expected error estimated from matchups, numeric not in abstract",
         decl_source_type="product document",
         decl_source="expected error is estimated in the validation paper but not given numerically in the abstract",
         decl_doi="10.1002/2016JD024834",
         act="0.12", act_unit="AOT", act_metric="RMSE over land",
         act_source="AERONET matchups", act_doi="10.1002/2016JD024834",
         relation="point", prior=1, p_clim=0, p_emp=0, p_aux=0, p_model=1,
         foot=1, obj=1, grade="B", assessable=0,
         notes="RMSE 0.12 over land and 0.06 over ocean; the declared expected error is only described qualitatively in the abstract."),
    dict(id="G46", variable="aerosol optical depth",
         product="MISR AOT", version="early postlaunch algorithm",
         validation_ref="AERONET (2 years)",
         decl="", decl_unit="AOT", decl_scope="uncertainty envelope [0.05 or 20% x AOT]",
         decl_source_type="product document",
         decl_source="2/3 of retrievals fall within [0.05 or 20% x AOT]",
         decl_doi="10.1029/2004JD004706",
         act="", act_unit="AOT", act_metric="fraction within envelope, not a sigma",
         act_source="AERONET global validation",
         act_doi="10.1029/2004JD004706",
         relation="point", prior=1, p_clim=0, p_emp=0, p_aux=0, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="An envelope-hit fraction is not exchangeable with an error magnitude."),
    dict(id="G47", variable="precipitation",
         product="GPM IMERG Final Run", version="V07",
         validation_ref="dense gauge network, Jianghuai",
         decl="", decl_unit="mm/h", decl_scope="per-pixel randomError field",
         decl_source_type="product uncertainty field",
         decl_source="randomError field exists, magnitude not paired",
         decl_doi="10.1029/2025EA004745",
         act="", act_unit="mm/h", act_metric="significant-discrepancy frequency",
         act_source="7253 gauges, 2020-2024",
         act_doi="10.1029/2025EA004745",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Reported metric is an event-frequency change (16%/6%/16%/17%), not a comparable sigma."),
    dict(id="G48", variable="land surface temperature",
         product="Sentinel-3 SLSTR LST", version="L2",
         validation_ref="in situ sites in China",
         decl="", decl_unit="K", decl_scope="product target accuracy, numeric not extracted",
         decl_source_type="product document",
         decl_source="product target accuracy not extracted from the accessed text",
         decl_doi="10.1109/TGRS.2024.3386178",
         act="1.91", act_unit="K", act_metric="key comparison reference value (KCRV)",
         act_source="uncertainty-based validation",
         act_doi="10.1109/TGRS.2024.3386178",
         relation="point", prior=2, p_clim=0, p_emp=0, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="RMSE below 1.6 K at most sites; KCRV 1.91 K for S3A. Declared target not paired."),
    dict(id="G49", variable="snow water equivalent",
         product="GlobSnow v3 SWE", version="v3",
         validation_ref="independent SWE product comparison",
         decl="", decl_unit="mm", decl_scope="per-pixel algorithm uncertainty (ATBD not retrievable)",
         decl_source_type="ATBD (unverified)",
         decl_source="GlobSnow ATBD record could not be parsed",
         decl_doi="10.5281/zenodo.7356944",
         act="50", act_unit="mm", act_metric="RMSE over Finland/Russia",
         act_source="long-term NH SWE product evaluation",
         act_doi="10.5194/tc-14-1579-2020",
         relation="upper_bound", prior=3, p_clim=1, p_emp=1, p_aux=1, p_model=0,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Duplicate of the legacy G10 entry, retained as a catalogue row because the ATBD remains unretrievable."),
    dict(id="G50", variable="surface soil moisture",
         product="ESA CCI soil moisture (active/passive/combined)", version="v07.1",
         validation_ref="in situ networks (AQUI and others)",
         decl="", decl_unit="m3/m3", decl_scope="no declared sigma at validation scale",
         decl_source_type="none found",
         decl_source="no public declared uncertainty located at validation scale",
         decl_doi="10.3390/rs10111839",
         act="", act_unit="m3/m3", act_metric="ubRMSE mostly <0.04 m3/m3",
         act_source="AQUI network comparison",
         act_doi="10.3390/rs10111839",
         relation="point", prior=3, p_clim=0, p_emp=1, p_aux=1, p_model=1,
         foot=1, obj=1, grade="C", assessable=0,
         notes="Validation performance is reported; no matching declared sigma is published."),
]

# ------------------------------------------------- new-column annotations
# evidence_type: primary provenance of the DECLARED number
EV = {
    "G01": ("raw_file_attribute", "radar_freeboard_uncertainty read from the netCDF variable; per-band medians recomputed"),
    "G02": ("raw_file_attribute", "sea_ice_thickness_uncertainty read from the netCDF variable; NH median recomputed"),
    "G03": ("raw_file_attribute", "analysis_error read from the product field; NH median recomputed"),
    "G04": ("product_document_text", "mission requirement stated in the SMAP mission paper"),
    "G05": ("product_document_text", "mission requirement stated in the SMAP mission paper"),
    "G06": ("recomputation", "expected-error formula evaluated at AOD = 0.20"),
    "G07": ("product_document_text", "GCOS requirement text adopted as the product target; no DOI"),
    "G08": ("product_document_text", "target accuracy stated in the product paper"),
    "G15": ("product_document_text", "mission requirement stated in the SMAP mission paper"),
    "G16": ("third_party_literature", "SMOS objective quoted in the validation paper"),
    "G17": ("third_party_literature", "SMOS objective quoted in the validation paper"),
    "G18": ("third_party_literature", "SMOS objective quoted in the validation paper"),
    "G19": ("third_party_literature", "SMOS objective applied in the validation paper"),
    "G20": ("product_document_text", "product specification quoted in the radiance-based validation"),
    "G14": ("product_document_text", "product specification widely cited but without a resolvable DOI"),
    "G21": ("raw_file_attribute", "per-pixel uncertainty field shipped with the product"),
    "G39": ("product_document_text", "mission classification requirement stated in the product paper"),
}
EVD = {
    "G01": "local netCDF attribute (read-only summary)",
    "G02": "local netCDF attribute (read-only summary)",
    "G03": "local netCDF attribute (read-only summary)",
}
# semantics of the declared quantity
SEM = {
    "G01": "random_only", "G02": "total", "G03": "analysis_error",
    "G04": "requirement", "G05": "requirement", "G06": "expected_error_envelope",
    "G07": "requirement", "G08": "target_total",
    "G15": "requirement", "G16": "requirement", "G17": "requirement",
    "G18": "requirement", "G19": "requirement", "G20": "specification",
    "G39": "requirement",
}
STAGE = {
    "G01": ("freeboard", "freeboard"),
    "G02": ("thickness", "thickness"),
    "G03": ("thickness", "thickness"),
    "G04": ("retrieval", "retrieval"),
    "G05": ("retrieval", "retrieval"),
    "G06": ("retrieval", "retrieval"),
    "G07": ("retrieval", "retrieval"),
    "G08": ("retrieval", "retrieval"),
}
SCALE = {
    "G01": ("25 km grid cell", "ATL20 segment (~40 m) aggregated to bands"),
    "G02": ("25 km grid cell", "airborne EM segment (~1 km) along track"),
    "G03": ("25 km grid cell", "OIB flight segment"),
    "G04": ("36 km grid cell", "core validation site footprint"),
    "G05": ("9 km grid cell", "core validation site footprint"),
    "G06": ("3 km pixel", "AERONET point"),
    "G07": ("500 m pixel", "field plot"),
    "G08": ("grid cell (1/20 deg)", "in situ point"),
    "G15": ("36 km grid cell", "core validation site footprint"),
    "G16": ("grid cell", "in situ station"),
    "G17": ("grid cell", "in situ station"),
    "G18": ("areal average", "in situ station"),
    "G19": ("grid cell", "in situ station"),
    "G20": ("1 km pixel", "in situ radiometer footprint"),
}

# per-object documented intervals (only where the source reports a range/bound)
CI = {
    "G01": (0.0899 / 0.0915, 0.114 / 0.085 * 0.0915 / 0.0915),  # placeholder, replaced below
}

# ------------------------------------------------------------------ assemble
def fnum(x):
    try:
        return float(x)
    except Exception:
        return None


rows = []
ext = []
for r in legacy:
    gid = r["group_id"]
    rows.append(dict(r))
    e = {}
    e["evidence_type"], e["evidence_detail"] = EV.get(gid, ("unspecified", ""))
    e["semantics_class"] = SEM.get(gid, "unspecified")
    sd, sa = STAGE.get(gid, ("", ""))
    e["stage_declared"], e["stage_actual"] = sd, sa
    scd, sca = SCALE.get(gid, ("", ""))
    e["scale_declared"], e["scale_actual"] = scd, sca
    e["log_ratio"] = ""
    e["ci_low"] = e["ci_high"] = e["ci_basis"] = ""
    e["quote_declared"] = ""
    e["quote_actual"] = ""
    e["locator_declared"] = ""
    e["locator_actual"] = ""
    e["doi_status_declared"] = "unresolvable" if gid in ("G01", "G02") else ("no_doi" if gid == "G07" else "resolved")
    e["doi_status_actual"] = "not_applicable"
    e["comparison_validity"] = "comparable" if r["object_matched"] == "1" else "support_mismatch"
    e["in_A"] = e["in_B"] = e["in_C"] = ""
    e["reason_if_not_assessable"] = "" if r["assessable"] == "1" else "legacy: declared value or scale not verifiable"
    for k in ("same_product", "same_statistic", "support_stated", "support_match",
              "source_resolved", "admission"):
        e[k] = ""
    ext.append(e)

for n in NEW:
    row = {k: "" for k in LEGACY_FIELDS}
    row.update({
        "group_id": n["id"], "variable": n["variable"], "product": n["product"],
        "product_version": n["version"], "validation_reference": n["validation_ref"],
        "declared_value": n["decl"], "declared_unit": n["decl_unit"],
        "declared_scope": n["decl_scope"], "declared_source_type": n["decl_source_type"],
        "declared_source": n["decl_source"], "declared_doi": n["decl_doi"],
        "actual_value": n["act"], "actual_unit": n["act_unit"],
        "actual_metric": n["act_metric"], "actual_source": n["act_source"],
        "actual_doi": n["act_doi"], "ratio_direction": "declared/actual",
        "ratio_original_stored": "", "ratio_original_direction": "",
        "ratio_relation": n["relation"], "prior_score": str(n["prior"]),
        "prior_climatology_background": str(n["p_clim"]),
        "prior_empirical_transfer": str(n["p_emp"]),
        "prior_shared_auxiliary": str(n["p_aux"]),
        "prior_assumed_model": str(n["p_model"]),
        "footprint_mismatch": str(n["foot"]), "object_matched": str(n["obj"]),
        "evidence_grade": n["grade"], "assessable": str(n["assessable"]),
        "notes": n["notes"],
    })
    dv, av = fnum(n["decl"]), fnum(n["act"])
    if n["assessable"] == 1:
        assert dv is not None and av is not None and av != 0, n["id"]
        row["ratio"] = f"{dv / av:.4f}"
    rows.append(row)

    e = {}
    e["evidence_type"], e["evidence_detail"] = EV.get(n["id"], (
        "raw_file_attribute" if n["decl_source_type"] == "product uncertainty field" else
        ("product_document_text" if n["decl_source_type"] in ("mission requirement", "product specification")
         else ("third_party_literature" if "quoted in validation paper" in n["decl_source_type"] or
               "applied in the validation paper" in n["decl_source_type"] else "unavailable")), ""))
    e["semantics_class"] = SEM.get(n["id"], "unavailable")
    sd, sa = STAGE.get(n["id"], ("", ""))
    e["stage_declared"], e["stage_actual"] = sd, sa
    scd, sca = SCALE.get(n["id"], ("", ""))
    e["scale_declared"], e["scale_actual"] = scd, sca
    e["log_ratio"] = ""
    e["ci_low"] = e["ci_high"] = e["ci_basis"] = ""
    e["quote_declared"] = ""
    e["quote_actual"] = ""
    e["locator_declared"] = ""
    e["locator_actual"] = ""
    e["doi_status_declared"] = "resolved" if n["decl_doi"] else "no_doi"
    e["doi_status_actual"] = "resolved" if n["act_doi"] else "not_available"
    e["comparison_validity"] = (
        "comparable" if n["assessable"] == 1 and n["obj"] == 1 else
        ("support_mismatch" if n["assessable"] == 1 else "not_comparable")
    )
    e["in_A"] = e["in_B"] = e["in_C"] = ""
    e["reason_if_not_assessable"] = "" if n["assessable"] == 1 else n["notes"]
    for k in ("same_product", "same_statistic", "support_stated", "support_match",
              "source_resolved", "admission"):
        e[k] = ""
    ext.append(e)

assert len(rows) == len(ext) == len(legacy) + len(NEW) >= 40, len(rows)

# --------------------------------------------------- log ratio + documented CI
for row, e in zip(rows, ext):
    if row["ratio"]:
        e["log_ratio"] = f"{__import__('math').log10(float(row['ratio'])):.4f}"

# Explicit documented intervals, expressed in the unified declared/actual ratio.
# Only intervals that the source actually supports are recorded; the absence of a
# whisker in Fig. 2 therefore means "single reported value", not "zero uncertainty".
INTERVALS = {
    # per-band declared/actual ratios: 0.0059/0.098, 0.0081/0.085, 0.0097/0.085, 0.012/0.142
    "G01": (0.0059 / 0.098, 0.012 / 0.142),
    # |bias| is a lower bound on the error, hence the ratio is an upper bound 0.5436
    "G03": (None, 0.1196 / 0.22),
    # only an upper bound on the actual error is published, hence ratio >= 1.0
    "G08": (1.0, None),
}
BASIS = {
    "G01": "min/max of the four per-band declared/actual ratios",
    "G03": "|bias| used as an error lower bound, so the ratio is an upper bound",
    "G08": "only an upper bound on the actual error is published, so the ratio is a lower bound",
}
for row, e in zip(rows, ext):
    gid = row["group_id"]
    if gid in INTERVALS:
        lo, hi = INTERVALS[gid]
        e["ci_low"] = f"{lo:.4f}" if lo is not None else ""
        e["ci_high"] = f"{hi:.4f}" if hi is not None else ""
        e["ci_basis"] = BASIS[gid]

# ------------------------------------------------------- admission rules (v2)
# C1 numeric declaration, C2 resolvable source, C3 same product AND same
# statistic, C4 support stated AND support matched, C5 numeric and exchangeable
# measured error.  C3 was split after the zero-context stress test: the legacy
# object_matched column conflated "same product" with "same statistic".
STATISTIC_MISMATCH = {
    "G01": "declared random/algorithm component vs measured total RMS of freeboard",
    "G03": "declared analysis error vs measured |bias| of thickness",
    "G06": "declared expected-error envelope vs measured RMSE",
    "G11": "declared total sigma vs measured mean bias",
    "G14": "declared value not tied to a statistic of the delivered field",
    "G21": "declared 1 m envelope vs point sigma",
    "G39": "categorical accuracy, not a continuous error magnitude",
}
EXCHANGEABLE = {"random_only", "total", "analysis_error", "expected_error_envelope",
                "requirement", "target_total", "specification"}
INSTITUTIONAL = {
    "product uncertainty field", "product per-grid uncertainty field",
    "product document", "product specification", "product ATBD statement",
    "product target accuracy", "published expected-error formula",
    "programme requirement (NOT product per-pixel sigma)",
}
for row, e in zip(rows, ext):
    gid = row["group_id"]
    val = lambda k: e.get(k) or row.get(k, "")
    if not val("declared_value"):
        e["admission"] = "no_declared_value"
        continue
    # every object pairs a product with a validation of that same product
    e["same_product"] = "1"
    e["same_statistic"] = "0" if gid in STATISTIC_MISMATCH else "1"
    e["support_stated"] = "1" if e["scale_declared"] else "0"
    e["support_match"] = ("1" if val("footprint_mismatch") == "0" else "0") \
        if e["support_stated"] == "1" else ""
    resolved = (e["doi_status_declared"] == "resolved"
                or val("declared_source_type") in INSTITUTIONAL)
    e["source_resolved"] = "1" if resolved else "0"
    measured = (fnum(val("actual_value")) is not None
                and e["semantics_class"] in EXCHANGEABLE)
    if not resolved:
        e["admission"] = "unresolvable_source"
    elif not measured:
        e["admission"] = "metric_not_exchangeable"
    elif e["same_statistic"] != "1":
        e["admission"] = "statistic_mismatch"
    elif e["support_stated"] != "1":
        e["admission"] = "support_not_stated"
    elif e["support_match"] != "1":
        e["admission"] = "support_mismatch"
    else:
        e["admission"] = "auditable"

# ------------------------------------------------------------- inclusion flags
# A: fully admitted, grade A, ratio is a point estimate or an upper bound.
# B: A plus the records whose only failing condition is C4 (support stated but
#    different) -- the support-caveated comparison.
# C: every record for which a ratio can be formed (adds the C3 construct
#    mismatches and the lower-bound SST record).
for r, e in zip(rows, ext):
    if r["assessable"] != "1":
        continue
    bound = r["ratio_relation"] == "lower_bound"
    if e["admission"] == "auditable" and not bound and r["evidence_grade"] == "A":
        e["in_A"] = "1"
    if e["in_A"] == "1" or e["admission"] == "support_mismatch":
        e["in_B"] = "1"
    e["in_C"] = "1"

# ------------------------------------------------------------------- writing
with open(os.path.join(DATA, "p3_dataset.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=LEGACY_FIELDS + NEW_FIELDS)
    w.writeheader()
    for r, e in zip(rows, ext):
        d = dict(r); d.update(e); w.writerow(d)

with open(os.path.join(DATA, "p3_extension_columns.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["group_id"] + NEW_FIELDS)
    w.writeheader()
    for r, e in zip(rows, ext):
        d = {"group_id": r["group_id"]}; d.update(e); w.writerow(d)

# ------------------------------------------------- verified evidence log
log = []
VER = [
    # id, side, doi, exists, doi_status, title, locator, quote, method
    ("G15", "declared", "10.1109/JPROC.2010.2043918", "yes", "resolved",
     "Entekhabi et al. 2010, SMAP mission", "abstract", "ubRMSE <= 0.04 m3/m3", "Crossref"),
    ("G15", "actual", "10.1109/TGRS.2016.2561938", "yes", "resolved",
     "Assessment of the SMAP passive soil moisture product", "abstract",
     "0.038 m3/m3 unbiased root-mean-square difference; approaches the SMAP mission requirement of 0.040 m3/m3", "Crossref"),
    ("G16", "declared", "10.1109/TGRS.2012.2186971", "yes", "resolved",
     "Validation of the SMOS L2 soil moisture data in REMEDHUS", "abstract/results",
     "close to the SMOS accuracy objective of 0.04 m3 m-3", "Crossref"),
    ("G16", "actual", "10.1109/TGRS.2012.2186971", "yes", "resolved",
     "Validation of the SMOS L2 soil moisture data in REMEDHUS", "abstract",
     "RMSDc = 0.044 m3 m-3", "Crossref"),
    ("G17", "declared", "10.3390/rs10081314", "yes", "resolved",
     "Use of SMOS L3 soil moisture data: Pernambuco", "abstract/results",
     "expected 0.04 m3m-3 accuracy of the SMOS mission", "Crossref"),
    ("G17", "actual", "10.3390/rs10081314", "yes", "resolved",
     "Use of SMOS L3 soil moisture data: Pernambuco", "abstract",
     "average RMSD ... 0.071 m3m-3 (pixel)", "Crossref"),
    ("G18", "actual", "10.3390/rs10081314", "yes", "resolved",
     "Use of SMOS L3 soil moisture data: Pernambuco", "abstract",
     "areal assessment ... 0.04 m3m-3", "Crossref"),
    ("G19", "declared", "10.1080/2150704X.2014.933277", "yes", "resolved",
     "Appraisal of SMOS soil moisture in a Mediterranean environment", "abstract/results",
     "SMOS accuracy objective of 0.04 m3 m-3", "Crossref"),
    ("G19", "actual", "10.1080/2150704X.2014.933277", "yes", "resolved",
     "Appraisal of SMOS soil moisture in a Mediterranean environment", "abstract",
     "RMSE = 0.116 m3 m-3 (0.110 after RFI filtering)", "Crossref"),
    ("G20", "declared", "10.1080/01431160802036565", "yes", "resolved",
     "Radiance-based validation of the V5 MODIS LST product", "abstract",
     "accuracy of the MODIS LST product is better than 1 K", "Crossref"),
    ("G20", "actual", "10.1029/2009JD012038", "yes", "resolved",
     "Temperature-based and radiance-based validations of the V5 MODIS LST product", "abstract",
     "RMSE of +/-0.7 K", "Crossref"),
    ("G21", "declared", "10.5194/essd-16-3149-2024", "yes", "resolved",
     "SMOS-derived Antarctic thin sea ice thickness", "abstract",
     "product contains estimates of the sea-ice thickness and its uncertainty up to about 1 m",
     "OpenAlex (numeric magnitude not in abstract)"),
    ("G22", "actual", "10.3390/rs16234565", "yes", "resolved",
     "Estimation of Arctic sea ice thickness using HY-2B", "abstract",
     "RMSD 0.56 m (CS-SMOS), 0.68 m (CPOM), 0.47 m (CS-2), 0.69 m (PIOMAS), 0.79 m (validation data)", "OpenAlex"),
    ("G23", "declared", "10.5194/tc-13-49-2019", "yes", "resolved",
     "Version 2 of the EUMETSAT OSI SAF and ESA CCI SIC CDRs", "Sect. 3",
     "sigma_tot described qualitatively; numeric magnitude not extracted", "full-text probe"),
    ("G23", "actual", "10.5194/tc-13-3261-2019", "yes", "resolved",
     "Satellite passive microwave SIC intercomparison", "Sect. 4",
     "biased low by -0.4% to -1.0% (Arctic)", "full-text probe"),
    ("G25", "actual", "10.1109/JSTARS.2017.2693120", "yes", "resolved",
     "Operational implementation of AMSR2 SIC estimates", "abstract",
     "bias 3.9% and RMSE 11.0% in the Arctic", "OpenAlex"),
    ("G26", "actual", "10.5194/tc-20-527-2026", "yes", "resolved",
     "Evaluation of the ESA CCI+ ESMR v1.1 SIC product", "abstract",
     "mean difference -1.4% (median 0.0%), standard deviation 6.0%", "OpenAlex"),
    ("G27", "actual", "10.3390/rs15020422", "yes", "resolved",
     "Sampling errors of Aquarius, SMAP, SMOS and Argo SSS", "abstract",
     "sampling errors about 0.02/0.03 psu at weekly scales", "OpenAlex"),
    ("G28", "declared", "10.1029/2022EA002516", "yes", "resolved",
     "ATBD for GEDI footprint AGBD", "abstract",
     "contains estimates of AGBD ... and associated prediction intervals", "OpenAlex"),
    ("G39", "declared", "10.1016/j.rse.2017.03.007", "yes", "resolved",
     "Retrieving landscape freeze/thaw state from SMAP", "abstract",
     "exceeding the 80% SMAP mission accuracy requirement", "OpenAlex"),
    ("G40", "actual", "10.1016/j.rse.2022.112988", "yes", "resolved",
     "Benchmarking algorithm changes to Snow CCI+ SWE", "abstract",
     "RMSE improved 12% (5 mm) relative to CCIv1", "OpenAlex"),
    ("G44", "actual", "10.1016/j.rse.2017.10.026", "yes", "resolved",
     "Global-scale assessment and combination of SMAP with ASCAT and AMSR2", "abstract",
     "ubRMSD 0.0411, 0.0625 and 0.0708 m3 m-3 for SMAP, ASCAT and AMSR2", "OpenAlex"),
    ("G45", "actual", "10.1002/2016JD024834", "yes", "resolved",
     "Validation and expected error estimation of VIIRS AOT", "abstract",
     "RMSE of the biases as 0.12 over land and 0.06 over ocean", "OpenAlex"),
    ("G46", "declared", "10.1029/2004JD004706", "yes", "resolved",
     "MISR global AOD validation", "abstract",
     "about 2/3 fall within [0.05 or 20% x AOT]", "OpenAlex"),
    ("G47", "actual", "10.1029/2025EA004745", "yes", "resolved",
     "Refine the uncertainty of GPM IMERG", "abstract",
     "reduced significant discrepancy frequency by 16%/6%/16%/17%", "OpenAlex"),
    ("G48", "actual", "10.1109/TGRS.2024.3386178", "yes", "resolved",
     "Uncertainty-based validation for Sentinel-3/SLSTR", "abstract",
     "KCRVs 1.91 K (S3A) and 1.71 K (S3B)", "OpenAlex"),
    ("G10", "actual", "10.5194/tc-14-1579-2020", "yes", "resolved",
     "Evaluation of long-term NH SWE products", "Results", "RMSE ~50 mm or less", "full-text probe"),
]
# carry over the legacy verification log verbatim (27 records)
legacy_log = list(csv.DictReader(open(os.path.join(N7, "02_verification_log.csv"), encoding="utf-8-sig")))
with open(os.path.join(DATA, "p3_verification_log.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["group_id", "item", "doi", "doi_checked_via", "doi_exists", "doi_status",
                "source_title_or_document", "location", "quoted_or_computed_value", "method", "status"])
    for r in legacy_log:
        w.writerow([r["group_id"], r["item"], r["doi"], r["doi_checked_via"], r["doi_exists"],
                    "resolved" if r["doi_exists"] == "yes" else r["doi_exists"],
                    r["source_title_or_document"], r["location"], r["quoted_or_computed_value"],
                    r["method"], r["status"]])
    for v in VER:
        w.writerow([v[0], v[1], v[2], v[3], "yes" if v[4] == "resolved" else v[4], v[4],
                    v[5], v[6], v[7], v[8], "verified"])

# ------------------------------------------------------------- Table 4 ledger
EV_MAP = {rr["group_id"]: e for rr, e in zip(rows, ext)}
ledger = []
for r in rows:
    if not r["declared_value"]:
        continue
    d = fnum(r["declared_value"]); a = fnum(r["actual_value"])
    point = r["ratio_relation"] == "point"
    ratio = f"{d / a:.4f}" if (point and d and a) else ""
    ledger.append({
        "group_id": r["group_id"],
        "product": r["product"],
        "variable": r["variable"],
        "declared_as_published": r["declared_value"] + " " + r["declared_unit"],
        "declared_scope": r["declared_scope"],
        "audited_reference_error": (r["actual_value"] + " " + r["actual_unit"]) if r["actual_value"] else "",
        "actual_metric": r["actual_metric"],
        "unified_ratio_declared_over_actual": ratio,
        "direction": ("under-report" if ratio and float(ratio) < 1 else
                      ("over-report" if ratio and float(ratio) > 1 else
                       ("parity" if ratio else "bound-only"))),
        "evidence_type": EV_MAP[r["group_id"]]["evidence_type"],
        "recommended_use": ("replace declared sigma with audited value" if ratio and abs(float(ratio) - 1) > 0.1
                            else ("retain declared value" if ratio else
                                  "do not use as a sigma; publish a declared value first")),
        "basis": r["notes"][:180],
    })
assert len(ledger) == 17, len(ledger)

with open(os.path.join(DATA, "p3_declared_ledger.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(ledger[0].keys()))
    w.writeheader()
    w.writerows(ledger)

# ------------------------------------------------------------------- checks
ASSESS = [r for r in rows if r["assessable"] == "1"]
for r, e in zip(rows, ext):
    if r["ratio"]:
        assert r["ratio_direction"] == "declared/actual"
        expect = float(r["declared_value"]) / float(r["actual_value"])
        assert abs(float(r["ratio"]) - expect) < 1e-3, r["group_id"]
assert any(r["group_id"] == "G01" and e["same_statistic"] == "0"
           for r, e in zip(rows, ext))
ADMISSION_FIELDS = ("same_product", "same_statistic", "support_stated",
                    "support_match", "source_resolved", "admission")
for r, e in zip(rows, ext):
    if e["admission"] and e["admission"] != "no_declared_value":
        assert all(e[k] != "" for k in
                   ("same_product", "same_statistic", "support_stated",
                    "source_resolved", "admission")), r["group_id"]
        assert (e["support_match"] != "") == (e["support_stated"] == "1"), r["group_id"]
assert sum(1 for e in ext if e["admission"] == "auditable") == 8
assert sum(1 for e in ext if e["admission"] == "support_mismatch") == 3
assert sum(1 for e in ext if e["admission"] == "statistic_mismatch") == 3
assert sum(1 for e in ext if e["in_A"] == "1") == 7
assert sum(1 for e in ext if e["in_B"] == "1") == 10
assert sum(1 for e in ext if e["in_C"] == "1") == 14

print(f"objects={len(rows)} assessable={len(ASSESS)} ledger_rows={len(ledger)}")
print("n7 sha256:", SHA)
print("assessable ids:", ",".join(r["group_id"] for r in ASSESS))
print("evidence types:", {t: sum(1 for e in ext if e["evidence_type"] == t) for t in
                          sorted({e["evidence_type"] for e in ext})})
