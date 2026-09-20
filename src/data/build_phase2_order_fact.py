"""MarginMap Phase 2B.1 — order-level contribution fact (ambiguity-safe).

Input (READ-ONLY): data/processed/fact_margin_map_phase2.csv (line grain).
Output (NEW):      data/processed/order_margin_map_phase2.csv (ONE ROW = ONE ORDER).

Rationale: rows 3406/3407 carry NULL line freight (individually unknowable),
so line-level SUM understates project contribution by 200.0476. Order-level
freight is fully known (ambiguous pair totals 25.05; the order totals 26.55),
hence order grain is the authoritative aggregation for overall/order/
customer-level contribution. NOTHING is allocated to the ambiguous lines:
their NULLs are preserved in the line fact, untouched by this script.

Formulas (scenarios OFF):
    order_cost_to_serve = order_freight + 0 + 0
    order_contribution_profit = order_revenue - order_cogs - order_cost_to_serve
    order_contribution_margin_pct = profit / revenue * 100 (NULL if revenue 0)
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LINE_CSV = ROOT / "data" / "processed" / "fact_margin_map_phase2.csv"
FACT1 = ROOT / "data" / "processed" / "fact_sales_cogs.csv"
OUT_CSV = ROOT / "data" / "processed" / "order_margin_map_phase2.csv"

EXPECTED_ORDERS = 5009
EXPECTED_REV = 2297200.8603
EXPECTED_COGS = 1493910.1285
EXPECTED_FREIGHT = 238173.79
EXPECTED_PROFIT = 565116.9418
AMBIG_ORDER = "US-2014-150119"
AMBIG_ORDER_FREIGHT = 26.55
AMBIG_PAIR_TOTAL = 25.05
TOL = 0.05


def fail(check: str, expected: str, actual: str) -> "NoReturn":
    raise SystemExit(f"VALIDATION FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not LINE_CSV.is_file():
        fail("input-exists", f"file at {LINE_CSV}", "NOT FOUND")
    line_hash_before = sha256(LINE_CSV)
    fact1_hash_before = sha256(FACT1)
    e = pd.read_csv(LINE_CSV, dtype={"postal_code": str})
    if len(e) != 9994:
        fail("input-rows", "9994 lines", f"{len(e)}")

    # scenarios must be OFF in the input (else baseline formulas invalid)
    if bool(e["return_processing_scenario_enabled"].any()) or \
            bool((e["return_processing_cost_scenario"] != 0).any()) or \
            bool(e["support_scenario_enabled"].any()) or \
            bool((e["support_cost_scenario"] != 0).any()):
        fail("scenarios-off", "return+support OFF/zero in line fact", "enabled")

    # order freight = uniquely-assigned line freight + ambiguous-pair total
    # where applicable. The pair total is used ONLY at order level; no line
    # assignment is created, read, or implied.
    ambig = e[e["freight_ambiguity_flag"]]
    if set(ambig["order_id"].unique().tolist()) != {AMBIG_ORDER} or len(ambig) != 2:
        fail("ambiguity-scope", f"only {AMBIG_ORDER} rows 3406/3407 flagged",
             f"{len(ambig)} rows in {ambig['order_id'].unique().tolist()}")
    if bool(ambig["freight_cost_observed"].notna().any()):
        fail("no-silent-choice", "flagged lines carry NULL freight", "value present")

    g = e.groupby("order_id", sort=True)
    o = pd.DataFrame({
        "order_revenue": g["net_revenue"].sum(),
        "order_cogs": g["modeled_cogs"].sum(),
        "order_freight": g["freight_cost_observed"].sum(min_count=1),
        "order_return_processing_cost_scenario": 0.0,
        "order_support_cost_scenario": 0.0,
    }).reset_index()
    # add the ambiguous-pair total to its order ONLY (order-level fact, not a split)
    amb_pair = float(AMBIG_PAIR_TOTAL)
    o.loc[o["order_id"] == AMBIG_ORDER, "order_freight"] += amb_pair

    # cross-check against the line fact's own order totals (independent path)
    xtab = e.drop_duplicates("order_id").set_index("order_id")["freight_order_total"]
    gap = (o.set_index("order_id")["order_freight"] - xtab).abs().max()
    if gap > 1e-6:
        fail("order-freight-xcheck", "matches line-fact order totals ±1e-6", f"{gap}")

    # return status at order level (YES > UNKNOWN > NOT_RETURNED; never mixed)
    rs = e.groupby("order_id")["return_status"].unique()
    def rollup(v):
        v = set(v.tolist())
        if v == {"YES"}:
            return ("YES", "candidate Returns via suffix crosswalk", "CROSSWALK_VERIFIED")
        if v == {"UNKNOWN"}:
            return ("UNKNOWN", "suffix unmappable — never defaulted", "CROSSWALK_UNMAPPABLE")
        if v == {"NOT_RETURNED"}:
            return ("NOT_RETURNED", "completeness assumption (absence)", "NOT_RETURNED_ASSUMED")
        return (None, None, None)
    rolled = rs.apply(rollup)
    if bool(rolled.apply(lambda t: t[0] is None).any()):
        bad = rs[rolled.apply(lambda t: t[0] is None)]
        fail("return-rollup", "unmixed YES/UNKNOWN/NOT_RETURNED per order", str(bad.to_dict()))
    o["order_return_status"] = [t[0] for t in rolled.loc[o["order_id"]].tolist()]
    o["return_status_source"] = [t[1] for t in rolled.loc[o["order_id"]].tolist()]
    o["return_crosswalk_flag"] = [t[2] for t in rolled.loc[o["order_id"]].tolist()]

    o["order_cost_to_serve"] = (o["order_freight"]
                                + o["order_return_processing_cost_scenario"]
                                + o["order_support_cost_scenario"])
    o["order_contribution_profit"] = (o["order_revenue"] - o["order_cogs"]
                                      - o["order_cost_to_serve"])
    o["order_contribution_margin_pct"] = np.where(
        o["order_revenue"] == 0, np.nan,
        o["order_contribution_profit"] / o["order_revenue"] * 100.0)
    o = o[["order_id", "order_revenue", "order_cogs", "order_freight",
           "order_return_status", "order_return_processing_cost_scenario",
           "order_support_cost_scenario", "order_cost_to_serve",
           "order_contribution_profit", "order_contribution_margin_pct"]]
    o = o.sort_values("order_id").reset_index(drop=True)

    # ---- validation 1-15 ------------------------------------------------------
    if len(o) != EXPECTED_ORDERS or o["order_id"].nunique() != EXPECTED_ORDERS:  # 1,2
        fail("1-2-orders", f"{EXPECTED_ORDERS} unique orders", f"{len(o)}")
    if set(o["order_id"]) != set(e["order_id"].unique()):
        fail("2-coverage", "every MarginMap order exactly once", "mismatch")
    tr, tc, tf, tp = (o["order_revenue"].sum(), o["order_cogs"].sum(),
                      o["order_freight"].sum(), o["order_contribution_profit"].sum())
    if abs(tr - EXPECTED_REV) > TOL:  # 3
        fail("3-revenue", f"{EXPECTED_REV}", f"{tr}")
    if abs(tc - EXPECTED_COGS) > TOL:  # 4
        fail("4-cogs", f"{EXPECTED_COGS}", f"{tc}")
    if abs(tf - EXPECTED_FREIGHT) > TOL:  # 5
        fail("5-freight", f"{EXPECTED_FREIGHT}", f"{tf}")
    if abs(tp - EXPECTED_PROFIT) > TOL:  # 6
        fail("6-profit", f"{EXPECTED_PROFIT}", f"{tp}")
    om = tp / tr * 100  # 7
    if abs(om - EXPECTED_PROFIT / EXPECTED_REV * 100) > 1e-6:
        fail("7-margin", "SUM/SUM margin", f"{om}")
    ao = o[o["order_id"] == AMBIG_ORDER].iloc[0]  # 8
    if abs(ao["order_freight"] - AMBIG_ORDER_FREIGHT) > TOL:
        fail("8-ambig-order", f"freight {AMBIG_ORDER_FREIGHT}", f"{ao['order_freight']}")
    # 9,10: line fact untouched + still ambiguous (checked via hashes + flags above)
    # 11,12: scenarios OFF (asserted on input + constants written)
    # 13: source Profit never read — structural (only column passthrough in line fact)
    # 14: separation — CTS sums freight only
    if abs((o["order_cost_to_serve"] - o["order_freight"]).abs().max()) > 1e-12:
        fail("14-separation", "CTS == freight (scenarios OFF)", "mismatch")
    if sha256(LINE_CSV) != line_hash_before or sha256(FACT1) != fact1_hash_before:  # 15
        fail("15-preserved", "line fact + Phase 1 fact byte-identical", "MODIFIED")

    o.to_csv(OUT_CSV, index=False, encoding="utf-8")
    chk = pd.read_csv(OUT_CSV)
    if len(chk) != EXPECTED_ORDERS or chk["order_id"].nunique() != EXPECTED_ORDERS:
        fail("artefact-reread", "5,009 unique orders on disk", "mismatch")

    print(f"OK: {len(o)} orders -> {OUT_CSV}")
    print(f"OK: revenue={tr:,.4f} cogs={tc:,.4f} freight={tf:,.2f}")
    print(f"OK: contrib={tp:,.4f} margin={om:.4f}% | ambig order freight={ao['order_freight']:.2f}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
