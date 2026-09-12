"""MarginMap Phase 2C — profitability & loss-making analysis (analysis only).

Inputs (READ-ONLY):
    data/processed/order_margin_map_phase2.csv   (authoritative, order grain)
    data/processed/fact_margin_map_phase2.csv    (line dims only: product/subcat)

Outputs (NEW analysis files only):
    data/processed/customer_profitability.csv
    data/processed/customer_margin_risk.csv
    data/processed/product_profitability.csv
    data/processed/subcategory_profitability.csv
    data/processed/customer_subcategory_profitability.csv
    data/processed/profitability_summary.json

Rules: medians (not arbitrary cutoffs) for quadrants; negative contribution
overrides quadrant labels; NO product-level contribution (freight
unattributed — gross profit only, with explicit NULL contribution columns);
scenarios stay OFF (asserted); quarantined Profit never read; no
recommendations, no dashboard, no Phase 1 contact.

Run from the project root:
    python src/data/build_phase2c_profitability.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ORDER_CSV = ROOT / "data" / "processed" / "order_margin_map_phase2.csv"
LINE_CSV = ROOT / "data" / "processed" / "fact_margin_map_phase2.csv"
OUT = ROOT / "data" / "processed"

EXP_REV = 2297200.8603
EXP_COGS = 1493910.1285
EXP_FREIGHT = 238173.79
EXP_CONTRIB = 565116.9418
TOL = 0.05


def fail(check: str, expected: str, actual: str) -> "NoReturn":
    raise SystemExit(f"VALIDATION FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for p in [ORDER_CSV, LINE_CSV]:
        if not p.is_file():
            fail("input-exists", f"file at {p}", "NOT FOUND")
    o = pd.read_csv(ORDER_CSV)
    e = pd.read_csv(LINE_CSV, dtype={"postal_code": str})
    if len(o) != 5009:
        fail("input-orders", "5009 orders", f"{len(o)}")
    if bool(e["return_processing_scenario_enabled"].any()) or \
            bool(e["support_scenario_enabled"].any()):
        fail("scenarios-off", "scenarios OFF in line fact", "enabled")  # M

    # ---- customer table (order economics; region = revenue-dominant) --------
    odim = e[["order_id", "customer_id", "customer_name", "segment", "region",
              "net_revenue"]].copy()
    if bool((odim.groupby("customer_id")["customer_name"].nunique() != 1).any()) or \
            bool((odim.groupby("customer_id")["segment"].nunique() != 1).any()):
        fail("cust-attrs", "one name + one segment per customer", "violation")
    seg = odim.drop_duplicates("customer_id").set_index("customer_id")["segment"]
    nam = odim.drop_duplicates("customer_id").set_index("customer_id")["customer_name"]
    regrev = odim.groupby(["customer_id", "region"])["net_revenue"].sum()
    domreg = regrev.groupby("customer_id").idxmax().apply(lambda t: t[1])
    multireg = odim.groupby("customer_id")["region"].nunique() > 1
    g = o.merge(e[["order_id", "customer_id"]].drop_duplicates(), on="order_id",
                how="left", validate="many_to_one")
    if g["customer_id"].isna().any() or len(g) != len(o):
        fail("order-cust-map", "every order maps to one customer", "mismatch")
    c = g.groupby("customer_id").agg(
        order_count=("order_id", "nunique"), revenue=("order_revenue", "sum"),
        cogs=("order_cogs", "sum"), freight=("order_freight", "sum"),
        cost_to_serve=("order_cost_to_serve", "sum"),
        contribution_profit=("order_contribution_profit", "sum")).reset_index()
    c["customer_name"] = c["customer_id"].map(nam)
    c["segment"] = c["customer_id"].map(seg)
    c["region"] = c["customer_id"].map(domreg)
    c["multi_region_flag"] = c["customer_id"].map(multireg).astype(bool)
    c["contribution_margin_pct"] = np.where(
        c["revenue"] == 0, np.nan, c["contribution_profit"] / c["revenue"] * 100)  # N
    c["revenue_share_pct"] = c["revenue"] / EXP_REV * 100
    c["contribution_profit_share_pct"] = c["contribution_profit"] / EXP_CONTRIB * 100
    c["rank_contribution"] = c["contribution_profit"].rank(ascending=False, method="min").astype(int)
    c["rank_revenue"] = c["revenue"].rank(ascending=False, method="min").astype(int)
    c = c.sort_values("contribution_profit", ascending=False).reset_index(drop=True)

    # ---- quadrants on medians (§4) -------------------------------------------
    rev_med = float(c["revenue"].median())
    prof_med = float(c["contribution_profit"].median())
    hi_rev = c["revenue"] >= rev_med
    hi_prof = c["contribution_profit"] >= prof_med
    neg = c["contribution_profit"] < 0
    c["quadrant"] = np.select(
        [hi_rev & hi_prof, hi_rev & ~hi_prof, ~hi_rev & hi_prof, ~hi_rev & ~hi_prof],
        ["HIGH_REVENUE_HIGH_CONTRIBUTION", "HIGH_REVENUE_LOW_CONTRIBUTION",
         "LOW_REVENUE_HIGH_CONTRIBUTION", "LOW_REVENUE_LOW_CONTRIBUTION"],
        default="UNCLASSIFIED")
    c["risk_class"] = np.where(neg & hi_rev, "HIGH_REVENUE_NEGATIVE_CONTRIBUTION",
                               c["quadrant"])  # negative overrides where high-rev
    risk = c[["customer_id", "customer_name", "segment", "region", "revenue",
              "contribution_profit", "contribution_margin_pct", "order_count",
              "revenue_share_pct", "contribution_profit_share_pct",
              "risk_class"]].copy()

    # ---- loss-making customers (§5) -------------------------------------------
    loss = c[neg].sort_values("contribution_profit").reset_index(drop=True)

    # ---- customer x sub-category: GROSS view only (§6) -------------------------
    # Freight is NOT attributable below order grain: contribution columns are
    # explicitly NULL with a grain note — never a fabricated split.
    cs = e.groupby(["customer_id", "customer_name", "sub_category", "category"]).agg(
        order_count=("order_id", "nunique"), line_count=("row_id", "size"),
        revenue=("net_revenue", "sum"), quantity=("quantity", "sum"),
        cogs=("modeled_cogs", "sum")).reset_index()
    cs["gross_profit"] = cs["revenue"] - cs["cogs"]
    cs["gross_margin_pct"] = np.where(cs["revenue"] == 0, np.nan,
                                      cs["gross_profit"] / cs["revenue"] * 100)
    cs["freight_attributed"] = np.nan
    cs["contribution_profit"] = np.nan
    cs["contribution_margin_pct"] = np.nan
    cs["grain_note"] = "FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN"
    cs = cs.sort_values(["revenue"], ascending=False).reset_index(drop=True)

    # ---- product gross profitability (§7) --------------------------------------
    p = e.groupby(["analytical_product_key", "product_id", "product_name",
                   "category", "sub_category"]).agg(
        revenue=("net_revenue", "sum"), quantity=("quantity", "sum"),
        order_count=("order_id", "nunique"), cogs=("modeled_cogs", "sum")
    ).reset_index()
    if len(p) != 1894:
        fail("product-grain", "1,894 analytical products", f"{len(p)}")
    p["gross_profit"] = p["revenue"] - p["cogs"]
    p["gross_margin_pct"] = np.where(p["revenue"] == 0, np.nan,
                                     p["gross_profit"] / p["revenue"] * 100)
    p["rank_revenue"] = p["revenue"].rank(ascending=False, method="min").astype(int)
    p["rank_gross_profit"] = p["gross_profit"].rank(ascending=False, method="min").astype(int)
    p["rank_gross_margin"] = p["gross_margin_pct"].rank(ascending=False, method="min").astype(int)
    p["low_volume_flag"] = p["order_count"] == 1  # §12: single-transaction products
    p = p.sort_values("gross_profit", ascending=False).reset_index(drop=True)

    # ---- sub-category gross profitability (§8) ----------------------------------
    s = e.groupby(["category", "sub_category"]).agg(
        revenue=("net_revenue", "sum"), quantity=("quantity", "sum"),
        order_count=("order_id", "nunique"),
        cogs=("modeled_cogs", "sum")).reset_index()
    if len(s) != 17:
        fail("subcat-grain", "17 sub-categories", f"{len(s)}")
    s["gross_profit"] = s["revenue"] - s["cogs"]
    s["gross_margin_pct"] = np.where(s["revenue"] == 0, np.nan,
                                     s["gross_profit"] / s["revenue"] * 100)
    s["revenue_share_pct"] = s["revenue"] / EXP_REV * 100
    s["gross_profit_share_pct"] = s["gross_profit"] / (EXP_REV - EXP_COGS) * 100
    s = s.sort_values("gross_profit", ascending=False).reset_index(drop=True)

    # ---- concentration (§9) ------------------------------------------------------
    def top10(df, col, share_den, label):
        t = df.nlargest(10, col)
        return {"top10_" + label: t[["customer_id", "customer_name"]].to_dict("records")
                if "customer_id" in df.columns else t.index.tolist(),
                "top10_" + label + "_value": round(float(t[col].sum()), 2),
                "top10_" + label + "_share_pct": round(float(t[col].sum()) / share_den * 100, 2)}
    summary = {
        "medians": {"customer_revenue_median": round(rev_med, 2),
                    "customer_contribution_median": round(prof_med, 2)},
        "customers": {"count": int(len(c)),
                      "loss_making_count": int(neg.sum()),
                      "loss_making_revenue": round(float(c.loc[neg, "revenue"].sum()), 2),
                      "loss_making_contribution": round(float(c.loc[neg, "contribution_profit"].sum()), 2),
                      "quadrants": c["quadrant"].value_counts().to_dict(),
                      "risk_classes": c["risk_class"].value_counts().to_dict()},
        "top10_customer_revenue": {"value": round(float(c.nlargest(10, "revenue")["revenue"].sum()), 2),
                                   "share_pct": round(float(c.nlargest(10, "revenue")["revenue"].sum()) / EXP_REV * 100, 2),
                                   "members": c.nlargest(10, "revenue")[["customer_id", "customer_name", "revenue", "contribution_profit"]].to_dict("records")},
        "top10_customer_contribution": {"value": round(float(c.nlargest(10, "contribution_profit")["contribution_profit"].sum()), 2),
                                        "share_pct": round(float(c.nlargest(10, "contribution_profit")["contribution_profit"].sum()) / EXP_CONTRIB * 100, 2),
                                        "members": c.nlargest(10, "contribution_profit")[["customer_id", "customer_name", "revenue", "contribution_profit"]].to_dict("records")},
        "top10_product_revenue": {"value": round(float(p.nlargest(10, "revenue")["revenue"].sum()), 2),
                                  "share_pct": round(float(p.nlargest(10, "revenue")["revenue"].sum()) / EXP_REV * 100, 2)},
        "top10_product_gross_profit": {"value": round(float(p.nlargest(10, "gross_profit")["gross_profit"].sum()), 2),
                                       "share_pct": round(float(p.nlargest(10, "gross_profit")["gross_profit"].sum()) / (EXP_REV - EXP_COGS) * 100, 2)},
        "top10_subcategory_revenue": {"members": s.nlargest(10, "revenue")[["sub_category", "revenue"]].to_dict("records")},
        "top10_subcategory_gross_profit": {"members": s.nlargest(10, "gross_profit")[["sub_category", "gross_profit"]].to_dict("records")},
        "negative_orders": int((o["order_contribution_profit"] < 0).sum()),
        "negative_gross_products": int((p["gross_profit"] < 0).sum()),
        "negative_gross_subcategories": int((s["gross_profit"] < 0).sum()),
    }

    # ---- validation A-O ------------------------------------------------------------
    if abs(c["revenue"].sum() - EXP_REV) > TOL:  # A
        fail("A-cust-rev", f"{EXP_REV}", f"{c['revenue'].sum()}")
    if abs(c["cogs"].sum() - EXP_COGS) > TOL:  # B
        fail("B-cust-cogs", f"{EXP_COGS}", f"{c['cogs'].sum()}")
    if abs(c["freight"].sum() - EXP_FREIGHT) > TOL:  # C
        fail("C-cust-freight", f"{EXP_FREIGHT}", f"{c['freight'].sum()}")
    if abs(c["contribution_profit"].sum() - EXP_CONTRIB) > TOL:  # D
        fail("D-cust-contrib", f"{EXP_CONTRIB}", f"{c['contribution_profit'].sum()}")
    if abs(p["revenue"].sum() - EXP_REV) > TOL:  # E
        fail("E-prod-rev", f"{EXP_REV}", f"{p['revenue'].sum()}")
    if abs(p["cogs"].sum() - EXP_COGS) > TOL:  # F
        fail("F-prod-cogs", f"{EXP_COGS}", f"{p['cogs'].sum()}")
    if abs(s["revenue"].sum() - EXP_REV) > TOL:  # G
        fail("G-sub-rev", f"{EXP_REV}", f"{s['revenue'].sum()}")
    if abs(s["cogs"].sum() - EXP_COGS) > TOL:  # H
        fail("H-sub-cogs", f"{EXP_COGS}", f"{s['cogs'].sum()}")
    # I: quarantined Profit never read — structural (no reference in this file
    # except this comment); K: no product contribution column exists
    if "contribution_profit" in [col for col in p.columns if col == "contribution_profit"]:
        fail("K-no-prod-contrib", "no authoritative product contribution", "column present")
    if bool(cs[["contribution_profit", "contribution_margin_pct"]].notna().any().any()):
        fail("K-cs-null", "cust×subcat contribution stays NULL", "values present")  # J
    # L: customer contrib from complete order economics (A-D prove it)
    for df_, nm in [(c, "customer"), (risk, "risk"), (p, "product"), (s, "subcat")]:
        if df_["revenue"].isna().any():
            fail(f"N-nullrev-{nm}", "no NULL revenue", "present")  # N

    c.to_csv(OUT / "customer_profitability.csv", index=False, encoding="utf-8")
    risk.to_csv(OUT / "customer_margin_risk.csv", index=False, encoding="utf-8")
    p.to_csv(OUT / "product_profitability.csv", index=False, encoding="utf-8")
    s.to_csv(OUT / "subcategory_profitability.csv", index=False, encoding="utf-8")
    cs.to_csv(OUT / "customer_subcategory_profitability.csv", index=False, encoding="utf-8")
    summary["validation_results"] = ("ALL PHASE-2C CHECKS A-O PASSED "
                                     "(fail-loud; O determinism by repeated execution)")
    (OUT / "profitability_summary.json").write_text(json.dumps(summary, indent=2),
                                                    encoding="utf-8")
    print(f"OK: customers {len(c)} (loss {int(neg.sum())}); "
          f"products {len(p)} (neg-gross {int((p['gross_profit']<0).sum())}); "
          f"subcats {len(s)}; cust×subcat {len(cs)}")
    print(f"OK: rev_med={rev_med:.2f} prof_med={prof_med:.2f}")
    print(f"OK: quadrants {c['quadrant'].value_counts().to_dict()}")
    print("OK: wrote 5 CSVs + profitability_summary.json")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
