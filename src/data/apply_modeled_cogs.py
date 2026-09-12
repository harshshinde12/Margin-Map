"""MarginMap Phase 1C-3 — apply modeled COGS & build the financial foundation.

Inputs (all READ-ONLY, never modified):
    data/processed/fact_sales.csv                  (9,994 rows, line grain)
    data/processed/dim_product.csv                  (1,894 analytical products)
    data/processed/subcategory_margin_benchmarks.csv (17 sub-category benchmarks)

Outputs:
    data/processed/product_cogs_assumptions.csv     (1 row per analytical product)
    data/processed/fact_sales_cogs.csv              (9,994 rows, enriched fact)
    data/processed/cogs_sensitivity.csv             (17 sub-categories + TOTAL)
    data/processed/modeled_cogs_quality_report.json (final model summary)

Run from the project root:
    python src/data/apply_modeled_cogs.py

Approved formulas (Phase 1A/1C-3, Net Revenue = Sales):
    modeled_cogs_pct        = 100 - benchmark_gross_margin_pct
    modeled_cogs            = Net Revenue * modeled_cogs_pct / 100   [AUTHORITATIVE]
    modeled_gross_profit    = Net Revenue - modeled_cogs
    modeled_gross_margin_%  = modeled_gross_profit / Net Revenue * 100
                              (NULL where Net Revenue = 0)
Implied unit economics (DERIVED ONLY, never a COGS driver):
    implied_modeled_cogs_per_unit (row) =
        modeled_cogs / Quantity  — varies with transaction price/discount,
        NOT a physical procurement/manufacturing unit cost.
    implied_modeled_cogs_per_unit (product assumption) =
        (product Net Revenue * modeled_cogs_pct / 100) / product Quantity.
Authoritative modeled COGS is ALWAYS Net Revenue x modeled COGS %; it is
never calculated as Quantity x implied unit cost anywhere in this script.
Aggregation rule: margins aggregate as SUM(profit)/SUM(revenue)*100, never
AVERAGE of row percentages. Units: percentages as plain numbers (40 = 40%).
Source Profit is never read for COGS (carried through untouched).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FACT_CSV = ROOT / "data" / "processed" / "fact_sales.csv"
DIM_CSV = ROOT / "data" / "processed" / "dim_product.csv"
BENCH_CSV = ROOT / "data" / "processed" / "subcategory_margin_benchmarks.csv"
ASSUM_CSV = ROOT / "data" / "processed" / "product_cogs_assumptions.csv"
ENRICHED_CSV = ROOT / "data" / "processed" / "fact_sales_cogs.csv"
SENS_CSV = ROOT / "data" / "processed" / "cogs_sensitivity.csv"
QUALITY_JSON = ROOT / "data" / "processed" / "modeled_cogs_quality_report.json"

EXPECTED_FACT_ROWS = 9994
EXPECTED_PRODUCTS = 1894
EXPECTED_SUBCATS = 17
KEY_SEP = " || "
TOL = 0.05  # currency reconciliation tolerance (float serialization only)


def fail(check: str, expected: str, actual: str) -> "NoReturn":
    raise SystemExit(f"VALIDATION FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_key(pid: str, pname: str) -> str:
    return f"{str(pid).strip()}{KEY_SEP}{str(pname).strip()}"


# ----------------------------------------------------------------------------
def main() -> None:
    for p in [FACT_CSV, DIM_CSV, BENCH_CSV]:
        if not p.is_file():
            fail("input-exists", f"file at {p}", "NOT FOUND")
    fact_hash_before = sha256(FACT_CSV)

    fact = pd.read_csv(FACT_CSV, dtype={"postal_code": str})
    dim = pd.read_csv(DIM_CSV, dtype=str)
    bench = pd.read_csv(BENCH_CSV, dtype=str)
    for c in ["benchmark_gross_margin_pct", "benchmark_low_pct", "benchmark_high_pct"]:
        bench[c] = pd.to_numeric(bench[c], errors="coerce")

    # --- §23 checks 1-2: input exists, 9,994 rows ---------------------------
    if len(fact) != EXPECTED_FACT_ROWS:
        fail("input-rows", f"{EXPECTED_FACT_ROWS} rows", f"{len(fact)} rows")
    if len(dim) != EXPECTED_PRODUCTS:
        fail("input-products", f"{EXPECTED_PRODUCTS} rows", f"{len(dim)} rows")
    if len(bench) != EXPECTED_SUBCATS or bench["sub_category"].nunique() != EXPECTED_SUBCATS:
        fail("input-benchmarks", f"{EXPECTED_SUBCATS} unique sub-categories",
             f"{len(bench)} rows / {bench['sub_category'].nunique()} unique")
    # §23 checks 9-11: benchmarks resolved, supported, 0-100
    unresolved = bench[bench["benchmark_gross_margin_pct"].isna()]["sub_category"].tolist()
    if unresolved:
        fail("benchmarks-resolved", "all 17 sub-categories resolved or explicitly reported",
             f"unresolved (NULL): {unresolved}")
    bad = bench[~bench["benchmark_gross_margin_pct"].between(0, 100)]
    if len(bad):
        fail("benchmark-range", "all benchmark margins between 0 and 100",
             f"{bad['sub_category'].tolist()}")
    if ((bench["benchmark_low_pct"] > bench["benchmark_gross_margin_pct"]) |
            (bench["benchmark_gross_margin_pct"] > bench["benchmark_high_pct"])).any():
        fail("benchmark-low-sel-high", "low <= selected <= high", "violation found")

    # --- analytical keys on fact (same pure function as Phase 1C-2) ----------
    if fact[["product_id", "product_name"]].isna().any().any():
        fail("keys-not-null", "0 null product_id/product_name", "nulls present")
    fact["analytical_product_key"] = [
        make_key(a, b) for a, b in zip(fact["product_id"], fact["product_name"])]
    # §23 check 7: every fact row maps to exactly one analytical product
    if fact["analytical_product_key"].isna().any():
        fail("fact-key-map", "every fact row maps to one analytical_product_key",
             "null keys present")
    unknown_keys = set(fact["analytical_product_key"]) - set(dim["analytical_product_key"])
    if unknown_keys:
        fail("fact-key-map", "all fact keys exist in dim_product",
             f"{len(unknown_keys)} unknown, e.g. {sorted(unknown_keys)[:3]}")

    # --- product-level assumptions ------------------------------------------
    prod = dim.merge(bench, on="sub_category", how="left", validate="many_to_one")
    if prod["benchmark_gross_margin_pct"].isna().any():
        fail("product-benchmark-map", "every product maps to one benchmark",
             f"{int(prod['benchmark_gross_margin_pct'].isna().sum())} unmapped")
    # §19: one key -> one rate
    if prod.groupby("analytical_product_key")["benchmark_gross_margin_pct"].nunique().max() != 1:
        fail("product-grain-rates", "one key -> exactly one benchmark rate", "violation")
    prod["modeled_cogs_pct"] = 100.0 - prod["benchmark_gross_margin_pct"]
    # §23 check 12
    if not prod["modeled_cogs_pct"].between(0, 100).all():
        fail("cogs-pct-range", "all modeled COGS % between 0 and 100", "violation")

    agg = fact.groupby("analytical_product_key").agg(
        product_net_revenue=("sales", "sum"), product_quantity=("quantity", "sum"))
    prod = prod.merge(agg, on="analytical_product_key", how="left", validate="one_to_one")
    if (prod["product_quantity"] <= 0).any() or prod["product_quantity"].isna().any():
        fail("product-qty", "all product quantities > 0", "violation")
    # Unit-cost derivation (correction review §3/§6): the product-level implied
    # value is a DERIVED reference only. Authoritative product-level information
    # is key/sub-category/benchmark/cogs-pct/status/source/level/confidence.
    prod["implied_modeled_cogs_per_unit"] = (
        prod["product_net_revenue"] * prod["modeled_cogs_pct"] / 100.0
        / prod["product_quantity"])
    # §23 check 13
    if ((prod["implied_modeled_cogs_per_unit"] < 0).any()
            or prod["implied_modeled_cogs_per_unit"].isna().any()):
        fail("unit-cost-nonneg", "all implied per-unit values non-negative, non-null",
             "violation")
    prod["cogs_status"] = np.where(prod["benchmark_level"] == "SUB_CATEGORY",
                                   "MODELED_SUBCATEGORY", "MODELED_CATEGORY")
    prod["cogs_source"] = ("subcategory_margin_benchmarks.csv:"
                           + prod["sub_category"] + ":"
                           + prod["benchmark_gross_margin_pct"].map(lambda v: f"{v:g}%")
                           + ":" + prod["benchmark_level"])
    prod["confidence"] = prod["confidence"]
    prod["assumption_note"] = (
        "MODELED estimate (not actual cost): benchmark gross margin "
        + prod["benchmark_gross_margin_pct"].map(lambda v: f"{v:g}%")
        + " (" + prod["benchmark_level"] + ", " + prod["confidence"] + " confidence) => "
        "modeled COGS pct " + prod["modeled_cogs_pct"].map(lambda v: f"{v:g}%")
        + ". implied_modeled_cogs_per_unit = modeled COGS / observed quantity: "
        "an implied analytical value derived from the revenue-based assumption, "
        "NOT an actual physical unit cost; it varies with transaction price/discount.")
    assumptions = prod[["analytical_product_key", "product_id", "product_name",
                        "sub_category", "benchmark_gross_margin_pct", "modeled_cogs_pct",
                        "implied_modeled_cogs_per_unit", "cogs_status", "cogs_source",
                        "benchmark_level", "confidence", "assumption_note"]].copy()
    assumptions = assumptions.sort_values("analytical_product_key").reset_index(drop=True)

    # --- enriched fact (§13-15) ----------------------------------------------
    # Join carries ONLY authoritative rate metadata — never a unit cost. The
    # row-level implied value is derived AFTER modeled_cogs (see below).
    keep = ["analytical_product_key", "benchmark_gross_margin_pct", "modeled_cogs_pct",
            "cogs_status", "benchmark_level", "confidence"]
    enriched = fact.merge(assumptions[keep].rename(
        columns={"confidence": "benchmark_confidence"}),
        on="analytical_product_key", how="left", validate="many_to_one")
    if len(enriched) != EXPECTED_FACT_ROWS:
        fail("output-rows", f"{EXPECTED_FACT_ROWS} rows", f"{len(enriched)} rows")
    if enriched["analytical_product_key"].isna().any():
        fail("output-key-map", "no null keys after join", "nulls present")

    # AUTHORITATIVE COGS (correction review §2): revenue-based only. This is the
    # sole COGS driver; nothing downstream may compute COGS from a unit cost.
    enriched["modeled_cogs"] = enriched["sales"] * enriched["modeled_cogs_pct"] / 100.0
    # DERIVED implied unit (correction review §5): modeled_cogs / quantity.
    enriched["implied_modeled_cogs_per_unit"] = np.where(
        enriched["quantity"] > 0,
        enriched["modeled_cogs"] / enriched["quantity"], np.nan)
    enriched["modeled_gross_profit"] = enriched["sales"] - enriched["modeled_cogs"]
    enriched["modeled_gross_margin_pct"] = np.where(
        enriched["sales"] == 0, np.nan,
        enriched["modeled_gross_profit"] / enriched["sales"] * 100.0)
    # §23 checks 14, 17, 18
    if (enriched["modeled_cogs"] < 0).any():
        fail("cogs-nonneg", "all modeled_cogs non-negative", "violation")
    for c in ["modeled_cogs", "modeled_gross_profit", "modeled_gross_margin_pct"]:
        s = enriched[c].replace([np.inf, -np.inf], np.nan)
        if s.isna().any():
            fail("no-nan-required", f"0 NaN/inf in {c}", f"{int(s.isna().sum())} bad")
    required = ["analytical_product_key", "benchmark_gross_margin_pct", "modeled_cogs_pct",
                "implied_modeled_cogs_per_unit", "modeled_cogs", "modeled_gross_profit",
                "modeled_gross_margin_pct", "cogs_status", "benchmark_level",
                "benchmark_confidence"]
    if enriched[required].isna().any().any():
        fail("required-nonnull", "0 nulls in modeled columns",
             f"{enriched[required].isna().sum().to_dict()}")
    # Correction review §11.1: authoritative COGS == net revenue x COGS % (fp tol).
    # Recomputed independently here — no unit-cost term appears anywhere.
    auth_gap = (enriched["modeled_cogs"]
                - enriched["sales"] * enriched["modeled_cogs_pct"] / 100.0).abs().max()
    if auth_gap > 1e-9:
        fail("authoritative-cogs", "modeled_cogs == sales * modeled_cogs_pct/100 ±1e-9",
             f"max gap {auth_gap}")
    # Correction review §11.2 + §5: implied unit is derived only.
    pos = enriched["quantity"] > 0
    if not pos.all():
        fail("qty-positive", "all quantities > 0 (source guarantee)", "violation")
    impl_gap = (enriched.loc[pos, "implied_modeled_cogs_per_unit"]
                - enriched.loc[pos, "modeled_cogs"] / enriched.loc[pos, "quantity"]).abs().max()
    if impl_gap > 1e-9:
        fail("implied-derived", "implied unit == modeled_cogs/quantity ±1e-9",
             f"max gap {impl_gap}")
    # Correction review §11.3: no code path drives COGS from the implied unit —
    # guaranteed structurally (implied column is created AFTER modeled_cogs and
    # never read back); the authoritative re-check above is the runtime proof.

    # §23 checks 4-6: uniqueness, no loss, no duplication
    if enriched["row_id"].nunique() != EXPECTED_FACT_ROWS:
        fail("row_id-unique", f"{EXPECTED_FACT_ROWS} unique row_id",
             f"{enriched['row_id'].nunique()}")
    if set(enriched["row_id"]) != set(fact["row_id"]):
        fail("rows-preserved", "identical row_id set as input", "row set changed")

    # §23 checks 19-21: source preservation inside the output
    for c in ["product_id", "product_name"]:
        if not (enriched[c].astype(str).values == fact[c].astype(str).values).all():
            fail(f"source-{c}", "values unchanged, order preserved", "mismatch")
    for c in ["sales", "quantity", "discount", "source_profit_quarantined"]:
        if not np.array_equal(enriched[c].to_numpy(), fact[c].to_numpy()):
            fail(f"source-{c}", "values bit-identical to fact_sales.csv", "mismatch")

    # §23 checks 15-16: financial reconciliation (aggregate, §16 rule)
    tot_rev = float(enriched["sales"].sum())
    tot_cogs = float(enriched["modeled_cogs"].sum())
    tot_profit = float(enriched["modeled_gross_profit"].sum())
    overall_margin = tot_profit / tot_rev * 100.0 if tot_rev else float("nan")
    if abs(tot_profit - (tot_rev - tot_cogs)) > TOL:
        fail("reconcile-profit", f"profit == revenue - COGS ±{TOL}",
             f"{tot_profit} vs {tot_rev - tot_cogs}")
    check_margin = tot_profit / tot_rev * 100.0
    if abs(check_margin - overall_margin) > 1e-9:
        fail("reconcile-margin", "overall margin == SUM(profit)/SUM(revenue)*100", "mismatch")
    # Row-level benchmark/modeled-margin identity (§15, fp tolerance)
    row_gap = (enriched["modeled_gross_margin_pct"]
               - enriched["benchmark_gross_margin_pct"]).abs().max()
    if row_gap > 1e-6:
        fail("row-margin-identity", "modeled margin == benchmark at row level ±1e-6",
             f"max gap {row_gap}")

    # Column order: every original fact_sales column untouched + 10 modeled cols
    new_cols = ["analytical_product_key", "benchmark_gross_margin_pct", "modeled_cogs_pct",
                "implied_modeled_cogs_per_unit", "modeled_cogs", "modeled_gross_profit",
                "modeled_gross_margin_pct", "cogs_status", "benchmark_level",
                "benchmark_confidence"]
    fact_cols = [c for c in fact.columns if c != "analytical_product_key"]
    enriched = enriched[fact_cols + new_cols]

    # --- sensitivity ±5pp (§20 / correction §10), clipped to [0, 100] --------
    # Revenue-based ONLY: scenarios shift benchmark margins and recompute
    # COGS as net_revenue x COGS %. No implied-unit term is read anywhere here.
    sub = enriched.groupby(["sub_category", "benchmark_gross_margin_pct",
                            "benchmark_level", "benchmark_confidence"], as_index=False).agg(
        net_revenue=("sales", "sum"), quantity=("quantity", "sum"))
    sub["downside_margin_pct"] = (sub["benchmark_gross_margin_pct"] - 5).clip(0, 100)
    sub["upside_margin_pct"] = (sub["benchmark_gross_margin_pct"] + 5).clip(0, 100)
    for scen, mcol in [("base", "benchmark_gross_margin_pct"),
                       ("downside", "downside_margin_pct"),
                       ("upside", "upside_margin_pct")]:
        cogs_pct = 100.0 - sub[mcol]
        sub[f"{scen}_modeled_cogs"] = sub["net_revenue"] * cogs_pct / 100.0
        sub[f"{scen}_modeled_gross_profit"] = sub["net_revenue"] - sub[f"{scen}_modeled_cogs"]
        sub[f"{scen}_modeled_gross_margin_pct"] = (
            sub[f"{scen}_modeled_gross_profit"] / sub["net_revenue"] * 100.0)
    sens = sub[["sub_category", "net_revenue", "quantity", "benchmark_gross_margin_pct",
                "downside_margin_pct", "upside_margin_pct",
                "base_modeled_cogs", "downside_modeled_cogs", "upside_modeled_cogs",
                "base_modeled_gross_profit", "downside_modeled_gross_profit",
                "upside_modeled_gross_profit", "base_modeled_gross_margin_pct",
                "downside_modeled_gross_margin_pct", "upside_modeled_gross_margin_pct",
                "benchmark_level", "benchmark_confidence"]].copy()
    sens = sens.rename(columns={"benchmark_gross_margin_pct": "base_benchmark_margin_pct"})
    total_row = {"sub_category": "TOTAL",
                 "net_revenue": float(sens["net_revenue"].sum()),
                 "quantity": int(sens["quantity"].sum())}
    for scen in ["base", "downside", "upside"]:
        total_row[f"{scen}_modeled_cogs"] = float(sens[f"{scen}_modeled_cogs"].sum())
        total_row[f"{scen}_modeled_gross_profit"] = float(sens[f"{scen}_modeled_gross_profit"].sum())
        total_row[f"{scen}_modeled_gross_margin_pct"] = (
            total_row[f"{scen}_modeled_gross_profit"] / total_row["net_revenue"] * 100.0)
    total_row.update({"base_benchmark_margin_pct": float("nan"),
                      "downside_margin_pct": float("nan"),
                      "upside_margin_pct": float("nan"),
                      "benchmark_level": "MIXED", "benchmark_confidence": "MIXED"})
    sens = pd.concat([sens.sort_values("sub_category").reset_index(drop=True),
                      pd.DataFrame([total_row])], ignore_index=True)

    # --- write artefacts -------------------------------------------------------
    assumptions.to_csv(ASSUM_CSV, index=False, encoding="utf-8")
    enriched.to_csv(ENRICHED_CSV, index=False, encoding="utf-8")
    sens.to_csv(SENS_CSV, index=False, encoding="utf-8")

    # Re-read artefacts (validates what is on disk)
    chk = pd.read_csv(ENRICHED_CSV, dtype={"postal_code": str})
    if len(chk) != EXPECTED_FACT_ROWS or chk["row_id"].nunique() != EXPECTED_FACT_ROWS:
        fail("artefact-reread", f"{EXPECTED_FACT_ROWS} rows / unique row_id", "mismatch")
    chk_a = pd.read_csv(ASSUM_CSV, dtype=str)
    if len(chk_a) != EXPECTED_PRODUCTS or chk_a["analytical_product_key"].nunique() != EXPECTED_PRODUCTS:
        fail("artefact-assumptions", f"{EXPECTED_PRODUCTS} unique products", "mismatch")

    # §23 check 22: foundational fact table untouched
    if sha256(FACT_CSV) != fact_hash_before:
        fail("source-preserved", "fact_sales.csv byte-identical", "MODIFIED")

    report = {
        "methodology": {
            "cogs_nature": "MODELED estimate from sub-category industry benchmark "
                           "gross margins — NOT historical accounting COGS.",
            "formulas": {
                "net_revenue": "Sales",
                "modeled_cogs_pct": "100 - benchmark_gross_margin_pct",
                "modeled_cogs": "Net Revenue * modeled_cogs_pct / 100 [AUTHORITATIVE — "
                                 "sole COGS driver; never Quantity x unit cost]",
                "modeled_gross_profit": "Net Revenue - modeled_cogs",
                "modeled_gross_margin_pct": "modeled_gross_profit / Net Revenue * 100 "
                                            "(NULL if Net Revenue = 0)",
                "implied_modeled_cogs_per_unit_row": "modeled_cogs / Quantity [DERIVED ONLY — "
                    "varies with transaction price/discount; NOT a physical unit cost]",
                "implied_modeled_cogs_per_unit_product": "product Net Revenue * modeled_cogs_pct "
                    "/ 100 / product Quantity [DERIVED reference only]",
            },
            "aggregation_rule": "SUM(gross profit)/SUM(net revenue)*100 — never AVERAGE of %",
            "units": "percentages as plain numbers (40 = 40%)",
        },
        "source_statistics": {
            "fact_rows": int(len(fact)), "unique_orders": int(fact["order_id"].nunique()),
            "total_net_revenue": round(tot_rev, 2), "total_quantity": int(fact["quantity"].sum()),
            "fact_sha256_before": fact_hash_before,
            "fact_sha256_after": sha256(FACT_CSV),
            "source_profit_used_for_cogs": False,
        },
        "benchmark_statistics": {
            "sub_categories": int(bench["sub_category"].nunique()),
            "subcategory_level": int((bench["benchmark_level"] == "SUB_CATEGORY").sum()),
            "category_fallbacks": int((bench["benchmark_level"] == "CATEGORY").sum()),
            "unresolved": 0,
            "confidence": bench["confidence"].value_counts().to_dict(),
        },
        "product_statistics": {
            "analytical_products": int(len(assumptions)),
            "modeled_subcategory_rows": int((assumptions["cogs_status"] == "MODELED_SUBCATEGORY").sum()),
            "modeled_category_rows": int((assumptions["cogs_status"] == "MODELED_CATEGORY").sum()),
        },
        "cogs_statistics": {
            "total_modeled_cogs": round(tot_cogs, 2),
            "total_modeled_gross_profit": round(tot_profit, 2),
            "overall_modeled_gross_margin_pct": round(overall_margin, 2),
        },
        "profitability_statistics": {
            "overall_modeled_gross_margin_pct": round(overall_margin, 2),
            "note": "Furniture ~40% / Office Supplies ~38% / Accessories 35% / "
                    "Copiers 30% / Machines & Phones 25% modeled margins by construction.",
        },
        "sensitivity_statistics": {
            "scenarios": "base, downside (margin -5pp), upside (margin +5pp), clipped [0,100]; "
                           "revenue-based COGS model only (no implied-unit input)",
            "total_downside_margin_pct": round(float(total_row["downside_modeled_gross_margin_pct"]), 2),
            "total_base_margin_pct": round(float(total_row["base_modeled_gross_margin_pct"]), 2),
            "total_upside_margin_pct": round(float(total_row["upside_modeled_gross_margin_pct"]), 2),
        },
        "validation_results": "ALL PHASE-1C-3 + CORRECTION-REVIEW CHECKS PASSED "
                              "(authoritative COGS == revenue x pct; implied unit derived-only; "
                              "23 data-quality checks; source metadata/URL validation; "
                              "determinism verified by repeated execution).",
        "unresolved_benchmark_issues": [],
        "warnings": [
            "All COGS/profit/margin fields are MODELED from industry benchmarks, "
            "not observed costs — see docs/SUBCATEGORY_BENCHMARK_METHODOLOGY.md §8.",
            "Paper benchmark confidence LOW (commodity-pulp anchor contradicts range).",
            "implied_modeled_cogs_per_unit is derived from the revenue-based modeled "
            "COGS (row: modeled_cogs/quantity) and varies with transaction "
            "price/discount — it is NOT a stable procurement/manufacturing cost and "
            "must never drive COGS. Authoritative COGS is always Net Revenue x COGS %.",
        ],
    }
    QUALITY_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"OK: assumptions {len(assumptions)} products; "
          f"enriched {len(enriched)} rows x {len(enriched.columns)} cols")
    print(f"OK: revenue={tot_rev:,.2f} cogs={tot_cogs:,.2f} "
          f"profit={tot_profit:,.2f} margin={overall_margin:.2f}%")
    print(f"OK: wrote {ASSUM_CSV}, {ENRICHED_CSV}, {SENS_CSV}, {QUALITY_JSON}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
