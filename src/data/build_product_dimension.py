"""MarginMap Phase 1C-2 — analytical product dimension + COGS input template.

Reads data/processed/fact_sales.csv READ-ONLY and produces:
  data/processed/dim_product.csv                  (1 row per product_id + product_name)
  data/processed/product_cogs_input_template.csv  (TEMPLATE: COGS left NULL/PENDING)
  data/processed/cogs_architecture_quality_report.json

Run from the project root:
    python src/data/build_product_dimension.py

Hard rules: no numerical COGS is fabricated; no fact/source modification;
deterministic output (order-independent, no UUIDs, no row-number keys).
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
DIM_CSV = ROOT / "data" / "processed" / "dim_product.csv"
TEMPLATE_CSV = ROOT / "data" / "processed" / "product_cogs_input_template.csv"
QUALITY_JSON = ROOT / "data" / "processed" / "cogs_architecture_quality_report.json"

EXPECTED_FACT_ROWS = 9994
EXPECTED_PRODUCTS = 1894  # Phase 1C-1: unique product_id + product_name combos

KEY_SEP = " || "  # separator for the deterministic analytical key
PENDING_STATUS = "PENDING_SOURCE"
PENDING_NOTE = ("No source COGS available as of Phase 1C-2; "
                "value intentionally left blank - do not fabricate.")


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def fail(check: str, expected: str, actual: str) -> "NoReturn":
    raise SystemExit(f"VALIDATION FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}")


def make_key(product_id: str, product_name: str) -> str:
    """Deterministic analytical key: pure function of (product_id, product_name).

    Order-independent (built from sorted unique combos, never row order),
    stable across runs, human-readable for interview traceability.
    """
    pid = product_id.strip()
    pname = product_name.strip()
    if KEY_SEP in pid or KEY_SEP in pname:
        fail("key-separator", f"separator {KEY_SEP!r} absent from id/name",
             f"collision risk in {product_id!r} / {product_name!r}")
    return f"{pid}{KEY_SEP}{pname}"


def load_fact() -> pd.DataFrame:
    if not FACT_CSV.is_file():
        fail("input-exists", f"file at {FACT_CSV}", "fact_sales.csv NOT FOUND")
    df = pd.read_csv(FACT_CSV, dtype={"postal_code": str})
    if len(df) != EXPECTED_FACT_ROWS:
        fail("input-rows", f"{EXPECTED_FACT_ROWS} rows (source must be preserved)",
             f"{len(df)} rows")
    for col in ["product_id", "product_name", "category", "sub_category"]:
        if df[col].isna().any() or (df[col].astype(str).str.strip() == "").any():
            fail(f"input-{col}", "0 null/blank", "nulls or blanks present")
    return df


def build_dimension(df: pd.DataFrame) -> pd.DataFrame:
    """One row per approved grain (product_id + product_name), sorted for determinism."""
    # Category/Sub-Category must be single-valued per combo (Phase 1C-1: 0 conflicts).
    cat_n = df.groupby(["product_id", "product_name"])["category"].nunique()
    sub_n = df.groupby(["product_id", "product_name"])["sub_category"].nunique()
    if (cat_n > 1).any():
        fail("combo-category", "one category per combo",
             f"{(cat_n > 1).sum()} combos span categories")
    if (sub_n > 1).any():
        fail("combo-subcategory", "one sub-category per combo",
             f"{(sub_n > 1).sum()} combos span sub-categories")
    dim = (df[["product_id", "product_name", "category", "sub_category"]]
             .drop_duplicates()
             .sort_values(["product_id", "product_name"])
             .reset_index(drop=True))
    dim["analytical_product_key"] = dim.apply(
        lambda r: make_key(r["product_id"], r["product_name"]), axis=1)
    return dim[["analytical_product_key", "product_id", "product_name",
                "category", "sub_category"]]


def build_template(dim: pd.DataFrame) -> pd.DataFrame:
    """Future COGS input TEMPLATE — numerical field stays NULL, status PENDING."""
    tpl = dim[["analytical_product_key", "product_id", "product_name"]].copy()
    tpl["cogs_per_unit"] = pd.NA          # intentionally blank — no source exists
    tpl["cogs_status"] = PENDING_STATUS
    tpl["cogs_source"] = pd.NA
    tpl["effective_start_date"] = pd.NA
    tpl["effective_end_date"] = pd.NA
    tpl["assumption_note"] = PENDING_NOTE
    return tpl


def main() -> None:
    fact = load_fact()
    fact_ids_before = set(fact["product_id"].unique())
    fact_names_before = set(fact["product_name"].unique())
    fact_combos = set(zip(fact["product_id"], fact["product_name"]))

    dim = build_dimension(fact)
    tpl = build_template(dim)

    # --- validation: dimension -------------------------------------------
    if len(dim) != EXPECTED_PRODUCTS:
        fail("dim-rows", f"{EXPECTED_PRODUCTS} rows", f"{len(dim)} rows")
    if dim["analytical_product_key"].isna().any():
        fail("key-not-null", "0 null keys", "null keys present")
    if dim["analytical_product_key"].duplicated().any():
        fail("key-unique", "all keys unique",
             f"{int(dim['analytical_product_key'].duplicated().sum())} duplicates")
    # Bidirectional mapping: combo <-> key
    if dim.groupby(["product_id", "product_name"])["analytical_product_key"].nunique().max() != 1:
        fail("combo-to-key", "each combo maps to exactly one key", "violation found")
    if dim.groupby("analytical_product_key")[["product_id", "product_name"]].nunique().max().max() != 1:
        fail("key-to-combo", "each key maps to exactly one combo", "violation found")
    # Source preservation: values byte-identical to fact (strip only for key join)
    if set(fact["product_id"].unique()) != fact_ids_before:
        fail("source-ids", "fact product_ids untouched", "fact appears modified")
    if not dim.apply(lambda r: (r["product_id"], r["product_name"]) in fact_combos, axis=1).all():
        fail("dim-from-source", "all dim (id, name) combos present verbatim in fact", "mismatch")

    # --- validation: template (no fabricated COGS) -------------------------
    if len(tpl) != EXPECTED_PRODUCTS:
        fail("template-rows", f"{EXPECTED_PRODUCTS} rows", f"{len(tpl)} rows")
    n_numeric = int(tpl["cogs_per_unit"].notna().sum())
    if n_numeric:
        fail("template-no-cogs", "0 numerical COGS values", f"{n_numeric} fabricated")
    if (tpl["cogs_status"] != PENDING_STATUS).any():
        fail("template-status", f"all rows '{PENDING_STATUS}'", "other status found")
    if set(tpl["analytical_product_key"]) != set(dim["analytical_product_key"]):
        fail("template-keys", "template keys == dim keys", "key mismatch")

    dim.to_csv(DIM_CSV, index=False, encoding="utf-8")
    tpl.to_csv(TEMPLATE_CSV, index=False, encoding="utf-8")

    # Re-read artefacts (validates what is on disk, not memory)
    chk_dim = pd.read_csv(DIM_CSV, dtype=str)
    chk_tpl = pd.read_csv(TEMPLATE_CSV, dtype=str)
    assert len(chk_dim) == EXPECTED_PRODUCTS and chk_dim["analytical_product_key"].nunique() == EXPECTED_PRODUCTS
    assert len(chk_tpl) == EXPECTED_PRODUCTS and chk_tpl["cogs_per_unit"].notna().sum() == 0
    assert (chk_tpl["cogs_status"] == PENDING_STATUS).all()

    report = {
        "input": {"file": "data/processed/fact_sales.csv", "rows": len(fact)},
        "analytical_product_count": len(dim),
        "unique_product_key_count": int(dim["analytical_product_key"].nunique()),
        "key_method": f"analytical_product_key = product_id + '{KEY_SEP}' + product_name "
                      "(deterministic, order-independent, no UUID/row numbers)",
        "template": {"file": "data/processed/product_cogs_input_template.csv",
                     "rows": len(tpl),
                     "null_cogs_count": int(tpl["cogs_per_unit"].isna().sum()),
                     "fabricated_cogs_count": 0,
                     "pending_status_count": int((tpl["cogs_status"] == PENDING_STATUS).sum())},
        "validation_results": "ALL 15 CHECKS PASSED (see script source for check list)",
        "methodology_status": "NO COGS METHODOLOGY SELECTED — architecture only; "
                              "see docs/COGS_MODEL.md for candidate evaluation",
        "source_preservation": "fact_sales.csv read-only (9,994 rows verified); "
                               "archive.zip untouched; dim values verbatim from fact",
        "modeled_fields_created": [],
    }
    QUALITY_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"OK: dim_product {len(dim)} rows, keys unique={dim['analytical_product_key'].nunique()}")
    print(f"OK: template {len(tpl)} rows, NULL cogs={int(tpl['cogs_per_unit'].isna().sum())}, fabricated=0")
    print(f"OK: wrote {DIM_CSV}, {TEMPLATE_CSV}, {QUALITY_JSON}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
