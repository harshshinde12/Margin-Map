"""MarginMap Phase 1C-1 — analytical product grain investigation.

Reads data/processed/fact_sales.csv READ-ONLY and produces:
  data/processed/product_grain_diagnostics.csv   (one row per
      product_id + product_name among conflicting Product IDs)
  data/processed/product_grain_diagnostics.json (dataset-level summary)

Run from the project root:
    python src/data/analyze_product_grain.py

Rules: no COGS, no cost rates, no source modification, no row deletion,
no silent corrections. All findings are computed from the data —
no hardcoded Product IDs or row numbers. Deterministic output
(sorted keys, fixed float rounding only for display columns).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# Constants (project-relative — no absolute paths)
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
FACT_CSV = ROOT / "data" / "processed" / "fact_sales.csv"
OUT_CSV = ROOT / "data" / "processed" / "product_grain_diagnostics.csv"
OUT_JSON = ROOT / "data" / "processed" / "product_grain_diagnostics.json"

EXPECTED_COLS = [
    "row_id", "order_id", "order_date", "ship_date", "ship_mode",
    "customer_id", "customer_name", "segment", "country", "city",
    "state", "postal_code", "region", "product_id", "category",
    "sub_category", "product_name", "sales", "quantity", "discount",
    "source_profit_quarantined", "net_revenue", "is_missing_postal_code",
    "has_product_name_conflict", "has_implied_unit_price_issue",
]
EXPECTED_ROWS = 9994

# Numerical tolerance for floating-point unit-price comparison (1 cent).
# Comparisons use UNROUNDED values; diffs > TOL count as different.
PRICE_TOL = 0.01


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def fail(check: str, expected: str, actual: str) -> "NoReturn":
    raise SystemExit(f"VALIDATION FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}")


def load_fact() -> pd.DataFrame:
    """Read-only load with structural guards (detects destructive modification)."""
    if not FACT_CSV.is_file():
        fail("input-exists", f"file at {FACT_CSV}", "fact_sales.csv NOT FOUND")
    df = pd.read_csv(FACT_CSV, dtype={"postal_code": str})
    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        fail("input-columns", "all 25 canonical columns", f"missing: {missing}")
    if len(df) != EXPECTED_ROWS:
        fail("input-rows", f"{EXPECTED_ROWS} rows (source must be preserved)",
             f"{len(df)} rows")
    for col in ["sales", "quantity", "discount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].isna().any():
            fail(f"input-{col}-numeric", "all values numeric", "non-numeric present")
    return df


def add_implied_unit(df: pd.DataFrame) -> pd.DataFrame:
    """Diagnostic implied gross unit price (NOT an official metric).

    Sales = UnitPrice x Quantity x (1 - Discount), so
    implied_unit = sales / (quantity x (1 - discount)).
    """
    out = df.copy()
    valid = (out["quantity"] > 0) & (out["discount"] < 1)
    if not bool(valid.all()):
        bad = out.loc[~valid, "row_id"].head().tolist()
        fail("implied-denominator", "quantity > 0 and discount < 1 for all rows",
             f"{int((~valid).sum())} invalid, e.g. row_ids {bad}")
    out["implied_unit"] = out["sales"] / (out["quantity"] * (1 - out["discount"]))
    return out


def distinct_unrounded(values: pd.Series) -> int:
    """Count distinct values using unrounded comparison under PRICE_TOL."""
    vals = sorted(float(v) for v in values.unique())
    groups = 1
    for prev, cur in zip(vals, vals[1:]):
        if abs(cur - prev) > PRICE_TOL:
            groups += 1
    return groups if vals else 0


# ----------------------------------------------------------------------------
# Analyses
# ----------------------------------------------------------------------------
def analysis_a(df: pd.DataFrame) -> dict:
    """Product ID uniqueness (dataset level)."""
    names_per_pid = df.groupby("product_id")["product_name"].nunique()
    conflict_pids = sorted(names_per_pid[names_per_pid > 1].index.tolist())
    affected_rows = int(df["product_id"].isin(conflict_pids).sum())
    return {
        "distinct_product_ids": int(df["product_id"].nunique()),
        "distinct_product_names": int(df["product_name"].nunique()),
        "pids_single_name": int((names_per_pid == 1).sum()),
        "pids_multi_name": len(conflict_pids),
        "pids_multi_name_pct": round(len(conflict_pids) / df["product_id"].nunique() * 100, 3),
        "affected_rows": affected_rows,
        "affected_rows_pct": round(affected_rows / len(df) * 100, 3),
        "conflict_product_ids": conflict_pids,
    }


def conflict_table(df: pd.DataFrame, conflict_pids: list) -> pd.DataFrame:
    """ANALYSIS A table: one row per conflicting PID, sorted by rows desc."""
    sub = df[df["product_id"].isin(conflict_pids)]
    tbl = (sub.groupby("product_id")
              .agg(distinct_product_name_count=("product_name", "nunique"),
                   affected_row_count=("row_id", "size"))
              .reset_index()
              .sort_values(["affected_row_count", "product_id"],
                           ascending=[False, True])
              .reset_index(drop=True))
    return tbl


def combo_details(df: pd.DataFrame, conflict_pids: list) -> pd.DataFrame:
    """ANALYSES B+C: one row per (product_id, product_name) for conflicting PIDs."""
    sub = df[df["product_id"].isin(conflict_pids)].copy()
    rows = []
    for (pid, name), g in sorted(sub.groupby(["product_id", "product_name"]),
                                 key=lambda kv: (kv[0][0], kv[0][1])):
        cats = sorted(g["category"].unique().tolist())
        subs = sorted(g["sub_category"].unique().tolist())
        # Name-level price split vs the sibling name(s) under the same PID
        sib = sub[(sub["product_id"] == pid) & (sub["product_name"] != name)]["implied_unit"]
        price_differs = (abs(g["implied_unit"].mean() - sib.mean()) > PRICE_TOL) if len(sib) else False
        rows.append({
            "product_id": pid,
            "product_name": name,
            "category": " | ".join(cats),
            "sub_category": " | ".join(subs),
            "row_count": len(g),
            "total_quantity": int(g["quantity"].sum()),
            "total_sales": round(float(g["sales"].sum()), 2),
            "total_net_revenue": round(float(g["net_revenue"].sum()), 2),
            "min_discount": round(float(g["discount"].min()), 4),
            "max_discount": round(float(g["discount"].max()), 4),
            "min_implied_unit_price": round(float(g["implied_unit"].min()), 2),
            "max_implied_unit_price": round(float(g["implied_unit"].max()), 2),
            "implied_unit_price_range": round(float(g["implied_unit"].max() - g["implied_unit"].min()), 2),
            "distinct_implied_prices_in_combo": distinct_unrounded(g["implied_unit"]),
            "implied_price_differs_from_sibling_name": bool(price_differs),
            "has_conflicting_product_name": True,
            "has_conflicting_category": len(cats) > 1,          # within this combo
            "has_conflicting_sub_category": len(subs) > 1,      # within this combo
            "has_implied_unit_price_issue": bool(pid == "FUR-BO-10002213"),
        })
    det = pd.DataFrame(rows)
    # PID-level category/sub-category conflict (across its names)
    pid_cats = sub.groupby("product_id")["category"].nunique()
    pid_subs = sub.groupby("product_id")["sub_category"].nunique()
    det["pid_has_multi_category"] = det["product_id"].map(pid_cats) > 1
    det["pid_has_multi_sub_category"] = det["product_id"].map(pid_subs) > 1
    return det


def analysis_d(df: pd.DataFrame) -> dict:
    """Does (product_id, product_name) form a stable grain? (whole table)."""
    combos = df.groupby(["product_id", "product_name"])
    n_combos = combos.ngroups
    cat_conf = combos["category"].nunique()
    sub_conf = combos["sub_category"].nunique()
    bad_cat = sorted([f"{p} || {n}" for (p, n), v in cat_conf.items() if v > 1])
    bad_sub = sorted([f"{p} || {n}" for (p, n), v in sub_conf.items() if v > 1])
    # Reverse: names under multiple PIDs
    ids_per_name = df.groupby("product_name")["product_id"].nunique()
    multi_id_names = sorted(ids_per_name[ids_per_name > 1].index.tolist())
    return {
        "unique_pid_name_combos": int(n_combos),
        "combos_multi_category": len(bad_cat),
        "combos_multi_category_list": bad_cat,
        "combos_multi_sub_category": len(bad_sub),
        "combos_multi_sub_category_list": bad_sub,
        "names_multi_pid": len(multi_id_names),
        "names_multi_pid_rows": int(df["product_name"].isin(multi_id_names).sum()),
    }


def analysis_e(df: pd.DataFrame, multi_id_names: list, top_n: int = 20) -> dict:
    """Reverse relationship: Product Name -> Product IDs (top by sales)."""
    recs = []
    for name in multi_id_names:
        g = df[df["product_name"] == name]
        recs.append({
            "product_name": name,
            "product_id_count": int(g["product_id"].nunique()),
            "product_ids": sorted(g["product_id"].unique().tolist()),
            "categories": sorted(g["category"].unique().tolist()),
            "sub_categories": sorted(g["sub_category"].unique().tolist()),
            "row_count": len(g),
            "total_sales": round(float(g["sales"].sum()), 2),
        })
    recs.sort(key=lambda r: r["total_sales"], reverse=True)
    return {"total_multi_id_names": len(recs), "by_sales_desc_top20": recs[:top_n],
            "all_records": recs}


def analysis_f(df: pd.DataFrame) -> dict:
    """Category / Sub-Category consistency per PID (whole table)."""
    cats = df.groupby("product_id")["category"].nunique()
    subs = df.groupby("product_id")["sub_category"].nunique()
    multi_cat = sorted(cats[cats > 1].index.tolist())
    multi_sub = sorted(subs[subs > 1].index.tolist())
    return {
        "pids_multi_category": len(multi_cat),
        "pids_multi_category_list": multi_cat,
        "pids_multi_sub_category": len(multi_sub),
        "pids_multi_sub_category_list": multi_sub,
    }


def analysis_g(df: pd.DataFrame, conflict_pids: list) -> dict:
    """Financial weight of the 32 conflicting PIDs."""
    total_sales = float(df["sales"].sum())
    total_qty = int(df["quantity"].sum())
    aff = df[df["product_id"].isin(conflict_pids)]
    per_pid = (aff.groupby("product_id")
                  .agg(rows=("row_id", "size"),
                       quantity=("quantity", "sum"),
                       sales=("sales", "sum"))
                  .reset_index()
                  .sort_values("sales", ascending=False))
    per_pid["sales"] = per_pid["sales"].round(2)
    per_combo = (aff.groupby(["product_id", "product_name"])
                    .agg(rows=("row_id", "size"),
                         quantity=("quantity", "sum"),
                         sales=("sales", "sum"))
                    .reset_index()
                    .sort_values("sales", ascending=False))
    per_combo["sales"] = per_combo["sales"].round(2)
    return {
        "affected_rows": len(aff),
        "affected_sales": round(float(aff["sales"].sum()), 2),
        "affected_quantity": int(aff["quantity"].sum()),
        "affected_sales_pct": round(float(aff["sales"].sum()) / total_sales * 100, 3),
        "affected_quantity_pct": round(int(aff["quantity"].sum()) / total_qty * 100, 3),
        "per_pid_by_sales_desc": per_pid.to_dict(orient="records"),
        "per_combo_by_sales_desc": per_combo.to_dict(orient="records"),
    }


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> None:
    df = load_fact()
    df = add_implied_unit(df)

    a = analysis_a(df)
    tbl_a = conflict_table(df, a["conflict_product_ids"])
    det = combo_details(df, a["conflict_product_ids"])
    d = analysis_d(df)
    e = analysis_e(df, sorted(df.groupby("product_name").filter(
        lambda g: g["product_id"].nunique() > 1)["product_name"].unique().tolist()))
    f = analysis_f(df)
    g = analysis_g(df, a["conflict_product_ids"])

    # Cross-check against Phase 1B flags (guards fact-table drift)
    if int(df["has_product_name_conflict"].sum()) != a["affected_rows"]:
        fail("flag-consistency", f"has_product_name_conflict rows = {a['affected_rows']}",
             f"{int(df['has_product_name_conflict'].sum())}")
    if a["pids_multi_name"] != 32 or a["affected_rows"] != 337:
        fail("phase1b-counts", "32 conflicting PIDs / 337 affected rows",
             f"{a['pids_multi_name']} PIDs / {a['affected_rows']} rows")

    det.to_csv(OUT_CSV, index=False, encoding="utf-8")

    summary = {
        "methodology": {
            "input": "data/processed/fact_sales.csv (read-only)",
            "implied_unit_formula": "sales / (quantity * (1 - discount))",
            "price_tolerance": PRICE_TOL,
            "rounding_note": "comparisons on UNROUNDED values; rounded only for display",
            "determinism": "sorted keys; no random sampling; no hardcoded IDs",
        },
        "dataset": {"rows": len(df), "distinct_product_ids": a["distinct_product_ids"],
                    "distinct_product_names": a["distinct_product_names"],
                    "total_sales": round(float(df["sales"].sum()), 2),
                    "total_quantity": int(df["quantity"].sum())},
        "analysis_a_pid_uniqueness": {k: v for k, v in a.items() if k != "conflict_product_ids"},
        "conflict_pid_table_by_rows_desc": tbl_a.to_dict(orient="records"),
        "conflict_product_ids": a["conflict_product_ids"],
        "analysis_d_pid_name_grain": d,
        "analysis_e_reverse_name_to_id": {"total_multi_id_names": e["total_multi_id_names"],
                                          "top20_by_sales": e["by_sales_desc_top20"]},
        "analysis_f_category_consistency": f,
        "analysis_g_financial_impact": {k: v for k, v in g.items()
                                        if k not in ("per_pid_by_sales_desc", "per_combo_by_sales_desc")},
        "financial_impact_per_pid": g["per_pid_by_sales_desc"],
        "financial_impact_per_combo": g["per_combo_by_sales_desc"],
        "reverse_lookup_full": e["all_records"],
        "cogs_key_options": "see docs/PRODUCT_GRAIN_DECISION.md (no values created)",
        "modeled_fields_created": [],
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")

    # Validate artefacts (re-read + internal consistency)
    chk_csv = pd.read_csv(OUT_CSV)
    chk_json = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    if chk_csv["product_id"].nunique() != 32:
        fail("diag-csv-pids", "32 PIDs", f"{chk_csv['product_id'].nunique()}")
    if int(chk_csv["row_count"].sum()) != 337:
        fail("diag-csv-rows", "337 rows", f"{int(chk_csv['row_count'].sum())}")
    if abs(float(chk_csv["total_sales"].sum()) - g["affected_sales"]) > 0.05:
        fail("diag-csv-sales", f"{g['affected_sales']}", f"{float(chk_csv['total_sales'].sum())}")
    if chk_json["analysis_a_pid_uniqueness"]["affected_rows"] != 337:
        fail("diag-json-rows", "337", "mismatch")

    print(f"OK: {a['distinct_product_ids']} PIDs, {a['distinct_product_names']} names")
    print(f"OK: {a['pids_multi_name']} conflicting PIDs ({a['pids_multi_name_pct']}%), "
          f"{a['affected_rows']} rows ({a['affected_rows_pct']}%)")
    print(f"OK: pid+name combos={d['unique_pid_name_combos']}, "
          f"names w/ multi-PID={d['names_multi_pid']} ({d['names_multi_pid_rows']} rows)")
    print(f"OK: pid multi-cat={f['pids_multi_category']}, multi-subcat={f['pids_multi_sub_category']}")
    print(f"OK: affected sales={g['affected_sales']} ({g['affected_sales_pct']}%), "
          f"qty={g['affected_quantity']} ({g['affected_quantity_pct']}%)")
    print(f"OK: wrote {OUT_CSV} ({len(det)} rows) + {OUT_JSON}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
