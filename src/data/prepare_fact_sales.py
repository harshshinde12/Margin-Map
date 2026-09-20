"""MarginMap Phase 1B — build the canonical fact_sales table.

Pipeline:
    archive.zip -> read Sample - Superstore.csv (latin1) -> validate ->
    clean/type -> flags -> fact_sales.csv + data_quality_report.json

Run from the project root:
    python src/data/prepare_fact_sales.py

Rules (locked decisions):
- Source archive/CSV are never modified (read-only access inside the ZIP).
- Net Revenue = Sales (alias column only, no new math).
- Source Profit is kept as `source_profit_quarantined` (reference only).
- No COGS / freight / returns / support / contribution columns are created.
- Any validation failure FAILS LOUDLY (non-zero exit, expected vs actual).
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# Constants (project-relative — no absolute paths)
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]  # repo root: .../Margin Map
ARCHIVE_PATH = ROOT / "archive.zip"
CSV_NAME = "Sample - Superstore.csv"
ENCODING = "latin1"  # Phase 0: file is NOT UTF-8 (0xa0 byte present)

PROCESSED_DIR = ROOT / "data" / "processed"
FACT_CSV = PROCESSED_DIR / "fact_sales.csv"
QUALITY_JSON = PROCESSED_DIR / "data_quality_report.json"

EXPECTED_COLUMNS = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
    "Customer ID", "Customer Name", "Segment", "Country", "City",
    "State", "Postal Code", "Region", "Product ID", "Category",
    "Sub-Category", "Product Name", "Sales", "Quantity", "Discount",
    "Profit",
]

CANONICAL_MAP = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "Country": "country",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
    "Quantity": "quantity",
    "Discount": "discount",
    "Profit": "source_profit_quarantined",
}

# Audit reference values (Phase 0) — used for reconciliation, not as inputs.
REF_ROWS = 9994
REF_SALES_TOTAL = 2_297_200.86
REF_PROFIT_TOTAL = 286_397.02
RECON_TOLERANCE = 0.05  # absolute currency tolerance for float rounding

FUR_FLAG_ID = "FUR-BO-10002213"  # Phase 0 flagged ID collision


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def fail(check: str, expected: str, actual: str) -> "NoReturn":
    """Fail loudly with expected-vs-actual context."""
    raise SystemExit(f"VALIDATION FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}")


def locate_source() -> zipfile.ZipFile:
    if not ARCHIVE_PATH.is_file():
        fail("source-archive", f"file exists at {ARCHIVE_PATH}", "archive.zip NOT FOUND")
    zf = zipfile.ZipFile(ARCHIVE_PATH)
    names = zf.namelist()
    if CSV_NAME not in names:
        fail("source-csv", f"'{CSV_NAME}' inside archive.zip", f"found: {names}")
    csv_files = [n for n in names if n.lower().endswith(".csv")]
    if len(csv_files) != 1:
        fail("source-unambiguous", "exactly 1 CSV in archive.zip", f"found: {csv_files}")
    return zf


def read_source(zf: zipfile.ZipFile) -> pd.DataFrame:
    try:
        with zf.open(CSV_NAME) as f:
            df = pd.read_csv(f, encoding=ENCODING, engine="c")
    except Exception as exc:  # malformed CSV / decode error
        raise SystemExit(f"VALIDATION FAILED [read-csv]\n  Could not read '{CSV_NAME}' "
                         f"with encoding={ENCODING}: {exc}")
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        fail("expected-columns", f"all {len(EXPECTED_COLUMNS)} columns present", f"missing: {missing}")
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if extra:
        fail("unexpected-columns", "no unexpected columns", f"extra: {extra}")
    return df[EXPECTED_COLUMNS].copy()


def to_postal_string(series: pd.Series) -> pd.Series:
    """Postal codes as strings; missing stays missing (never 0, never inferred)."""

    def conv(v):
        if pd.isna(v):
            return pd.NA
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return pd.NA
            # US ZIPs are 5 digits; raw CSV mixes '05408' with '1040'
            # (leading zero lost). Pad pure-digit codes so geo joins compare.
            if v.isdigit():
                return v.zfill(5)
            return v
        try:
            iv = int(float(v))  # handles int- or float-read codes
            return str(iv).zfill(5)
        except (ValueError, TypeError):
            return str(v).strip()

    return series.map(conv).astype("string")


def clean_and_type(df: pd.DataFrame) -> pd.DataFrame:
    out = df.rename(columns=CANONICAL_MAP).copy()

    # Strip whitespace on text fields (whitespace only — values preserved).
    for col in ["order_id", "ship_mode", "customer_id", "customer_name",
                "segment", "country", "city", "state", "region",
                "product_id", "category", "sub_category", "product_name"]:
        out[col] = out[col].astype("string").str.strip()

    # Integers / numerics — coerce so bad values become NaN and are caught.
    out["row_id"] = pd.to_numeric(out["row_id"], errors="coerce").astype("Int64")
    out["quantity"] = pd.to_numeric(out["quantity"], errors="coerce").astype("Int64")
    for col in ["sales", "discount", "source_profit_quarantined"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")

    # Postal code -> string (never numeric, never zero-filled).
    out["postal_code"] = to_postal_string(out["postal_code"])

    # Dates — explicit format matching the verified source (M/D/YYYY).
    for col in ["order_date", "ship_date"]:
        out[col] = pd.to_datetime(out[col].astype("string").str.strip(),
                                  format="%m/%d/%Y", errors="coerce")

    # Approved alias ONLY: net_revenue = sales (source-derived, not calculated).
    out["net_revenue"] = out["sales"]

    return out


def validate(df: pd.DataFrame, raw_rows: int) -> dict:
    """Run all checks. Returns a dict of observed stats; raises on failure."""
    stats: dict = {}

    # --- grain / keys -------------------------------------------------------
    if len(df) != raw_rows:
        fail("row-count", f"{raw_rows} rows preserved", f"{len(df)} rows")
    if df["row_id"].isna().any():
        fail("row_id-not-null", "0 null row_id", f"{int(df['row_id'].isna().sum())} nulls")
    if df["row_id"].duplicated().any():
        fail("row_id-unique", "all row_id unique",
             f"{int(df['row_id'].duplicated().sum())} duplicates")
    for col in ["order_id", "customer_id", "product_id"]:
        n_null = int(df[col].isna().sum() + (df[col].str.strip() == "").sum())
        if n_null:
            fail(f"{col}-not-null", "0 null/blank", f"{n_null}")
    stats["rows"] = len(df)
    stats["unique_row_id"] = int(df["row_id"].nunique())
    stats["unique_orders"] = int(df["order_id"].nunique())
    lines_per_order = df.groupby("order_id").size()
    stats["single_line_orders"] = int((lines_per_order == 1).sum())
    stats["multi_line_orders"] = int((lines_per_order > 1).sum())
    stats["unique_customers"] = int(df["customer_id"].nunique())
    stats["unique_products"] = int(df["product_id"].nunique())

    # --- dates --------------------------------------------------------------
    for col in ["order_date", "ship_date"]:
        n_bad = int(df[col].isna().sum())
        if n_bad:
            fail(f"{col}-parseable", "0 unparseable dates", f"{n_bad} NaT in {col}")
    bad_ship = df[df["ship_date"] < df["order_date"]]
    if len(bad_ship):
        fail("ship-gte-order", "ship_date >= order_date for all rows",
             f"{len(bad_ship)} violations, e.g. row_ids {bad_ship['row_id'].head(5).tolist()}")
    stats["order_min"] = str(df["order_date"].min().date())
    stats["order_max"] = str(df["order_date"].max().date())
    stats["ship_min"] = str(df["ship_date"].min().date())
    stats["ship_max"] = str(df["ship_date"].max().date())

    # --- numerics -----------------------------------------------------------
    for col in ["sales", "quantity", "discount", "source_profit_quarantined"]:
        n_null = int(df[col].isna().sum())
        if n_null:
            fail(f"{col}-numeric", "0 null/non-numeric", f"{n_null}")
        if bool(pd.Series(df[col]).apply(lambda v: v != v or v in (float("inf"), float("-inf"))).any()):
            fail(f"{col}-finite", "all values finite", "infinite values present")
    checks = [
        ("sales-gte-0", df["sales"] < 0, "Sales >= 0"),
        ("quantity-gt-0", df["quantity"] <= 0, "Quantity > 0"),
        ("discount-gte-0", df["discount"] < 0, "Discount >= 0"),
        ("discount-lt-1", df["discount"] >= 1, "Discount < 1"),
    ]
    stats["numeric_violations"] = {}
    for name, mask, expected in checks:
        n = int(mask.sum())
        stats["numeric_violations"][name] = n
        if n:
            fail(name, expected, f"{n} violations, e.g. row_ids {df.loc[mask, 'row_id'].head(5).tolist()}")
    stats["sales_total"] = round(float(df["sales"].sum()), 4)
    stats["quantity_total"] = int(df["quantity"].sum())
    stats["profit_quarantined_total"] = round(float(df["source_profit_quarantined"].sum()), 4)

    # --- postal codes -------------------------------------------------------
    n_missing_postal = int(df["postal_code"].isna().sum())
    stats["missing_postal"] = n_missing_postal
    stats["missing_postal_pct"] = round(n_missing_postal / len(df) * 100, 3)

    # --- product name consistency -------------------------------------------
    names_per_id = df.groupby("product_id")["product_name"].nunique()
    conflict_ids = sorted(names_per_id[names_per_id > 1].index.tolist())
    stats["product_ids_multi_name"] = len(conflict_ids)
    stats["product_ids_multi_name_list"] = conflict_ids

    # --- implied unit-price diagnostic (NOT an official metric) -------------
    diag = df[(df["quantity"] > 0) & (df["discount"] < 1)].copy()
    diag["implied_unit"] = (diag["sales"] / (diag["quantity"] * (1 - diag["discount"]))).round(2)
    units_per_id = diag.groupby("product_id")["implied_unit"].nunique()
    multi_price_ids = sorted(units_per_id[units_per_id > 1].index.tolist())
    stats["product_ids_multi_implied_price"] = len(multi_price_ids)
    fur = diag[diag["product_id"] == FUR_FLAG_ID].copy()
    stats["fur_rows"] = len(fur)
    stats["fur_names"] = sorted(fur["product_name"].unique().tolist())
    stats["fur_implied_prices"] = sorted(fur["implied_unit"].unique().tolist())

    # --- reconciliation vs Phase 0 audit ------------------------------------
    if abs(stats["sales_total"] - REF_SALES_TOTAL) > RECON_TOLERANCE:
        fail("reconcile-sales", f"total within {RECON_TOLERANCE} of {REF_SALES_TOTAL}",
             f"{stats['sales_total']}")
    if abs(stats["profit_quarantined_total"] - REF_PROFIT_TOTAL) > RECON_TOLERANCE:
        fail("reconcile-profit", f"total within {RECON_TOLERANCE} of {REF_PROFIT_TOTAL}",
             f"{stats['profit_quarantined_total']}")
    if stats["rows"] != REF_ROWS:
        fail("reconcile-rows", f"{REF_ROWS} rows", f"{stats['rows']}")

    return stats


def add_flags(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    """Boolean flags only — source values are never modified."""
    out = df.copy()
    out["is_missing_postal_code"] = out["postal_code"].isna()
    conflict_ids = set(stats["product_ids_multi_name_list"])
    out["has_product_name_conflict"] = out["product_id"].isin(conflict_ids)
    # Narrow, evidenced flag: the confirmed ID collision (name AND price split).
    out["has_implied_unit_price_issue"] = out["product_id"] == FUR_FLAG_ID
    return out


def main() -> None:
    zf = locate_source()
    with zf:
        raw = read_source(zf)
    raw_rows = len(raw)

    fact = clean_and_type(raw)
    stats = validate(fact, raw_rows)
    fact = add_flags(fact, stats)

    column_order = list(CANONICAL_MAP.values()) + [
        "net_revenue",
        "is_missing_postal_code",
        "has_product_name_conflict",
        "has_implied_unit_price_issue",
    ]
    fact = fact[column_order]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    fact.to_csv(FACT_CSV, index=False, encoding="utf-8")

    # Independent re-read of the written file (validates the artefact itself).
    check = pd.read_csv(FACT_CSV, encoding="utf-8")
    if len(check) != stats["rows"]:
        fail("output-row-count", f"{stats['rows']} rows in CSV", f"{len(check)}")
    if check["row_id"].nunique() != stats["unique_row_id"]:
        fail("output-row_id-unique", f"{stats['unique_row_id']} unique", f"{check['row_id'].nunique()}")

    report = {
        "source": {"archive": "archive.zip", "csv": CSV_NAME, "encoding": ENCODING},
        "grain": "one row = one product line within an order (row_id)",
        "rows": stats["rows"],
        "columns": column_order,
        "stats": stats,
        "flags": ["is_missing_postal_code", "has_product_name_conflict",
                  "has_implied_unit_price_issue"],
        "quarantine_note": ("source_profit_quarantined is preserved for reference but "
                            "quarantined because its original calculation methodology "
                            "has not been established."),
        "modeled_fields_created": [],
    }
    QUALITY_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"OK: {stats['rows']} rows x {len(column_order)} cols -> {FACT_CSV}")
    print(f"OK: quality report -> {QUALITY_JSON}")
    print(f"sales_total={stats['sales_total']} profit_q_total={stats['profit_quarantined_total']}")
    print(f"multi-name PIDs={stats['product_ids_multi_name']} "
          f"multi-price PIDs={stats['product_ids_multi_implied_price']} "
          f"missing_postal={stats['missing_postal']}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
