# Declared versus measured uncertainty in Earth observation products

Nearly every satellite product ships a declared uncertainty, and that number is
rarely checked against independent validation. This repository is the audit: 50
declarations across 16 variable families, a five-condition admission checklist,
55 verification records, and a 17-row correction ledger that a user can apply
directly.

## What is here

    data/p3_dataset.csv            50 objects x 59 columns: declaration, locator,
                                   reading, measured error, ratio, admission verdict
    data/column_dictionary.csv     field-by-field definition of all 59 columns
    data/p3_verification_log.csv   55 records: locator, quoted reading, DOI status
    data/p3_declared_ledger.csv    the 17-row correction ledger (Table 4)
    data/p3_reconciliation.csv     each object against the inherited core table
    data/claims.json               every number the article quotes, recomputed
    code/audit_claims.py           repairs the locator columns, derives the ledger
                                   recommendation from the verdict, audits the text
    code/analysis.py, figures.py, make_tables.py, build_dataset.py
    tex/, figures/                 generated tables and figures

## Run it

    pip install numpy pandas scipy matplotlib
    python code/audit_claims.py --write

The `--write` step is idempotent: the two files it edits are backed up once to
`data/r12_baseline/`. Adding `--check-text` asserts 20 headline values against the
manuscript; that flag needs the article source, so it is exercised in the paper
package rather than here. The run prints, among others:

    C2: 55 cells filled; 17 of 17 admitted rows carry a locator
    families 16, without assessable 10, with 6
    core5 median 0.879 [0.544, 1.053]
    A7 geomean 0.888 CI (0.627, 1.140)
    all14 geomean 0.735 CI (0.496, 1.011)

## Reading the checklist

A declaration is auditable when it states a number (C1), ties it to a locator and
a reading (C2), refers to the same product and the same statistic (C3), states the
support at which it was established (C4), and has an independent measured error at
that support (C5). Eight of the 50 objects meet all five. The ledger's
recommendation is derived from the verdict by one rule, so it cannot recommend a
record the audit itself refuses.

## Licence and citation

Code MIT; the audit data CC BY 4.0 (see DATA_LICENSE). Cite the article and this
repository.
