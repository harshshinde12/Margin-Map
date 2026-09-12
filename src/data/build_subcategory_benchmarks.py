"""MarginMap Phase 1C-3 — sub-category gross-margin benchmark input table.

Builds the AUTHORITATIVE input for modeled COGS:
    data/processed/subcategory_margin_benchmarks.csv      (17 rows, one per sub-category)
    data/processed/benchmark_quality_report.json          (coverage + validation report)

Run from the project root:
    python src/data/build_subcategory_benchmarks.py

CRITICAL RULES (Phase 1C-3, sections 5-8):
- No benchmark is invented. Every row carries source metadata
  (source_name / source_url / source_date / methodology_note).
- benchmark_level = SUB_CATEGORY only where the evidence genuinely names the
  sub-category product. Otherwise CATEGORY with fallback_used = TRUE and an
  explicit methodology_note. Category evidence is never dressed up as
  sub-category evidence.
- benchmark_gross_margin_pct = NULL + confidence LOW marks an unresolved row.
  This run resolves all 17 rows; any future NULL must be reported, never filled.
- Units: percentages as plain numbers (40 = 40%). No false precision:
  whole-percent centrals only.
- fact_sales.csv / dim_product.csv are READ-ONLY inputs (sub-category list
  cross-checked, never modified). Source Profit is never read or used.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DIM_CSV = ROOT / "data" / "processed" / "dim_product.csv"
FACT_CSV = ROOT / "data" / "processed" / "fact_sales.csv"
BENCH_CSV = ROOT / "data" / "processed" / "subcategory_margin_benchmarks.csv"
QUALITY_JSON = ROOT / "data" / "processed" / "benchmark_quality_report.json"

EXPECTED_SUBCATEGORIES = 17

DAMODARAN_URL = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html"

# ----------------------------------------------------------------------------
# Benchmark definitions.
# Each tuple: (sub_category, selected %, low %, high %, level, fallback,
#              confidence, source_name, source_url, source_date, methodology_note)
# Evidence researched 2026-09-11; full discussion in
# docs/SUBCATEGORY_BENCHMARK_METHODOLOGY.md. "Owner range" = the Phase 1C-3
# brief's researched ranges (treated as inputs requiring documentation,
# never as standalone proof — every row below also cites public evidence).
# ----------------------------------------------------------------------------
BENCHMARKS: list[tuple] = [
    # ---- Furniture: owner range 35-45%, central 40% -------------------------
    ("Bookcases", 40, 35, 45, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Margins by Sector (US), Furn/Home Furnishings gross "
     "margin 30.28% (Jan 2026); corroborated by MillerKnoll FY2024 gross margin "
     "39.1% and HNI FY2024 gross profit 40.9%",
     "https://news.millerknoll.com/2024-06-26-MillerKnoll,-Inc-Reports-Fourth-Quarter-and-Fiscal-2024-Results",
     "2024-06-26",
     "Category-level evidence only (no published bookcase-specific margin); "
     "owner range 35-45% applied as documented fallback. Central 40% sits at "
     "the owner central and between MillerKnoll 39.1% / HNI 40.9% (contract "
     "casegoods makers) and the CSIMarket Furniture & Fixtures industry 35.5%. "
     "Damodaran broad-furnishings 30.28% noted below range (manufacturing-heavy mix)."),
    ("Chairs", 40, 35, 45, "CATEGORY", True, "MEDIUM",
     "MillerKnoll FY2024 gross margin 39.1% (seating-led contract maker); "
     "Steelcase gross margin ~31-34% (FY2024-Q2 FY2026); CSIMarket Furniture & "
     "Fixtures industry gross margin TTM 35.49%",
     "https://news.millerknoll.com/2024-06-26-MillerKnoll,-Inc-Reports-Fourth-Quarter-and-Fiscal-2024-Results",
     "2024-06-26",
     "Category-level evidence only (no published chair-specific margin); owner "
     "range 35-45% applied as documented fallback. Central 40% equals the "
     "owner central and rounds MillerKnoll 39.1%; Steelcase ~31-34% and "
     "CSIMarket 35.5% sit inside the documented 35-45% range."),
    ("Furnishings", 40, 35, 45, "CATEGORY", True, "MEDIUM",
     "CSIMarket Furniture & Fixtures industry gross margin TTM 35.49% "
     "(Jul 2026); NYU Stern Damodaran Furn/Home Furnishings 30.28% (Jan 2026)",
     "https://csimarket.com/Industry/Industry_Profitability.php?ind=407",
     "2026-07-22",
     "Category-level evidence only; owner range 35-45% applied as documented "
     "fallback. Central 40% equals the owner central; industry aggregates "
     "(CSIMarket 35.5%, Damodaran 30.3%) anchor the low end of the range."),
    ("Tables", 40, 35, 45, "CATEGORY", True, "MEDIUM",
     "HNI FY2024 gross profit 40.9% of net sales (workplace furnishings incl. "
     "tables/casegoods); MillerKnoll FY2024 gross margin 39.1%",
     "https://s27.q4cdn.com/224070551/files/doc_financials/2024/q4/v2/HNI-Q4-FY24-news-release-final.pdf",
     "2025-02-20",
     "Category-level evidence only (no published table-specific margin); owner "
     "range 35-45% applied as documented fallback. Central 40% equals the "
     "owner central and the rounded HNI 40.9%; MillerKnoll 39.1% corroborates."),
    # ---- Office Supplies: owner range 30-45%, central 38% -------------------
    ("Appliances", 38, 30, 45, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Office Equipment & Services gross margin 41.43% "
     "(Jan 2026); Retail (Special Lines) 35.30%; owner range 30-45%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback. Central 38% is the owner central, sitting between Damodaran "
     "Office Equipment & Services 41.4% and Retail (Special Lines) 35.3%. "
     "ODP Corp FY2024 reseller gross margin ~20.7% (incl. occupancy, declining "
     "footprint) noted as below-range channel caveat, not used as anchor."),
    ("Art", 38, 30, 45, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Office Equipment & Services gross margin 41.43% "
     "(Jan 2026); Retail (Special Lines) 35.30%; owner range 30-45%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback. Central 38% is the owner central, between Damodaran 41.4% and "
     "Retail (Special Lines) 35.3%. No art-supply-specific margin published."),
    ("Binders", 38, 30, 45, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Office Equipment & Services gross margin 41.43% "
     "(Jan 2026); Retail (Distributors) 30.57%; owner range 30-45%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback. Central 38% is the owner central; Damodaran 41.4% (above) and "
     "Retail (Distributors) 30.6% (range floor) bracket it."),
    ("Envelopes", 38, 30, 45, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Packaging & Container gross margin 24.27% and Office "
     "Equipment & Services 41.43% (Jan 2026); owner range 30-45%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback. Central 38% is the owner central. Packaging & Container 24.3% "
     "(commodity packaging) noted as below-range adjacent anchor; converted "
     "stationery carries higher margins than commodity packaging."),
    ("Fasteners", 38, 30, 45, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Office Equipment & Services gross margin 41.43% "
     "(Jan 2026); Retail (Special Lines) 35.30%; owner range 30-45%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback. Central 38% is the owner central, between Damodaran 41.4% and "
     "Retail (Special Lines) 35.3%. No fastener-specific margin published."),
    ("Labels", 38, 30, 45, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Office Equipment & Services gross margin 41.43% "
     "(Jan 2026); Retail (Special Lines) 35.30%; owner range 30-45%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback. Central 38% is the owner central, between Damodaran 41.4% and "
     "Retail (Special Lines) 35.3%. No label-specific margin published."),
    ("Paper", 38, 30, 45, "CATEGORY", True, "LOW",
     "NYU Stern Damodaran Paper/Forest Products gross margin 17.14% (Jan 2026, "
     "commodity pulp/paper, n=6) vs Office Equipment & Services 41.43%; owner "
     "range 30-45%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback with LOW confidence: the only paper-specific anchor "
     "(Damodaran Paper/Forest 17.14%) is commodity pulp manufacturing, far "
     "below converted-stationery economics, so it is recorded as a caveat, "
     "not the anchor. Central 38% follows the owner central like other "
     "office-supply sub-categories. Flagged for future calibration against "
     "actual procurement costs."),
    ("Storage", 38, 30, 45, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Office Equipment & Services gross margin 41.43% "
     "(Jan 2026); Retail (Distributors) 30.57%; owner range 30-45%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback. Central 38% is the owner central; Damodaran 41.4% (above) and "
     "Retail (Distributors) 30.6% (range floor) bracket it."),
    ("Supplies", 38, 30, 45, "CATEGORY", True, "MEDIUM",
     "ODP Corp FY2024 gross profit $1,445M on $6,990M sales (~20.7%, incl. "
     "occupancy) as reseller context; NYU Stern Damodaran Retail (Special "
     "Lines) 35.30%; owner range 30-45%",
     "https://www.businesswire.com/news/home/20250226935130/en/The-ODP-Corporation-Announces-Fourth-Quarter-and-Full-Year-2024-Results",
     "2025-02-26",
     "Category-level evidence only; owner range 30-45% applied as documented "
     "fallback. Central 38% is the owner central. ODP 20.7% is a pure-reseller "
     "margin (incl. occupancy, shrinking store base) and is recorded as a "
     "below-range channel caveat: modeled COGS here uses category economics, "
     "not ODP's distressed-retail margin."),
    # ---- Technology ---------------------------------------------------------
    ("Accessories", 35, 30, 40, "SUB_CATEGORY", False, "MEDIUM",
     "Logitech FY2025 GAAP gross margin 43.1% (computer-accessories maker: "
     "mice/keyboards/webcams/headsets); Damodaran Computers/Peripherals "
     "38.36% and Electronics (Consumer & Office) 38.77% (Jan 2026)",
     "https://ir.logitech.com/press-releases/press-release-details/2025/Logitech-Announces-Q4-and-Full-Fiscal-Year-2025-Results/default.aspx",
     "2025-04-30",
     "SUB_CATEGORY evidence: Logitech manufactures exactly this sub-category. "
     "Central 35% is set BELOW brand-manufacturer levels (43.1%/38-39%) to "
     "reflect reseller positioning, and ABOVE core-tech 25% per the owner "
     "input that accessories carry higher margins. Range 30-40 spans "
     "core-tech top to manufacturer levels."),
    ("Copiers", 30, 25, 35, "SUB_CATEGORY", False, "MEDIUM",
     "Xerox Q3 2024 total gross margin 32.4% (equipment 28.5%, post-sale "
     "33.5%); FY2024 GAAP total ~31.5% (adjusted ~32.3%)",
     "https://www.sec.gov/Archives/edgar/data/108772/000177045024000045/ex991xrx930248-ker.htm",
     "2024-10-29",
     "SUB_CATEGORY evidence: Xerox is a printer/copier company. Central 30% "
     "rounds below Xerox 31.5-32.4% to reflect reseller positioning while "
     "staying at the top of the owner core-tech 20-30% range. Range 25-35 "
     "spans equipment-margin low to post-sale high. (2025 Xerox figures "
     "excluded: distorted by the Lexmark acquisition.)"),
    ("Machines", 25, 20, 30, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Electronics (General) gross margin 26.76% (Jan "
     "2026); Best Buy FY2025 enterprise gross margin 22.6% (reseller); owner "
     "core-tech range 20-30%",
     "https://s204.q4cdn.com/864376893/files/doc_earnings/2025/q4/earnings-result/Best-Buy-Reports-Fiscal-Fourth-Quarter-Results.pdf",
     "2025-03-04",
     "Category-level evidence only (no published office-machine margin); owner "
     "core-tech range 20-30% applied as documented fallback. Central 25% is "
     "the range midpoint, corroborated by Damodaran Electronics (General) "
     "26.8% and Best Buy reseller 22.6%. Damodaran Machinery 37.5% rejected "
     "as industrial-machinery mismatch."),
    ("Phones", 25, 20, 30, "CATEGORY", True, "MEDIUM",
     "NYU Stern Damodaran Electronics (General) gross margin 26.76% (Jan "
     "2026); Best Buy FY2025 enterprise gross margin 22.6% with computing/"
     "mobile ~45% of mix; owner core-tech range 20-30%",
     DAMODARAN_URL,
     "2026-01",
     "Category-level evidence only (no published reseller-handset margin); "
     "owner core-tech range 20-30% applied as documented fallback. Central "
     "25% is the range midpoint, corroborated by Damodaran 26.8% and Best Buy "
     "22.6%. Damodaran Telecom Equipment 58.1% explicitly rejected: it covers "
     "network-gear makers, not handsets."),
]

COLUMNS = ["sub_category", "benchmark_gross_margin_pct", "benchmark_low_pct",
           "benchmark_high_pct", "benchmark_level", "source_name", "source_url",
           "source_date", "methodology_note", "confidence", "fallback_used"]


def fail(check: str, expected: str, actual: str) -> "NoReturn":
    raise SystemExit(f"VALIDATION FAILED [{check}]\n  Expected: {expected}\n  Actual:   {actual}")


def build_frame() -> pd.DataFrame:
    rows = [ {"sub_category": b[0], "benchmark_gross_margin_pct": b[1],
              "benchmark_low_pct": b[2], "benchmark_high_pct": b[3],
              "benchmark_level": b[4], "source_name": b[7],
              "source_url": b[8], "source_date": b[9],
              "methodology_note": b[10], "confidence": b[6],
              "fallback_used": b[5]} for b in BENCHMARKS ]
    df = pd.DataFrame(rows, columns=COLUMNS)
    # booleans serialize as TRUE/FALSE strings for CSV transparency
    df["fallback_used"] = df["fallback_used"].map({True: "TRUE", False: "FALSE"})
    return df


def validate(df: pd.DataFrame) -> dict:
    # 1. universe: exactly the 17 Superstore sub-categories, no more, no fewer
    for src, label in [(DIM_CSV, "dim_product.csv"), (FACT_CSV, "fact_sales.csv")]:
        if not src.is_file():
            fail("input-exists", f"file at {src}", "NOT FOUND")
    dim_subs = set(pd.read_csv(DIM_CSV, dtype=str)["sub_category"].unique())
    fact_subs = set(pd.read_csv(FACT_CSV, dtype=str)["sub_category"].unique())
    if dim_subs != fact_subs:
        fail("input-universe", f"dim == fact sub-categories",
             f"dim={sorted(dim_subs)} fact={sorted(fact_subs)}")
    bench_subs = set(df["sub_category"].tolist())
    if bench_subs != dim_subs:
        fail("coverage-17", f"benchmarks == {sorted(dim_subs)}",
             f"missing={sorted(dim_subs - bench_subs)} extra={sorted(bench_subs - dim_subs)}")
    if len(df) != EXPECTED_SUBCATEGORIES:
        fail("row-count", f"{EXPECTED_SUBCATEGORIES} rows", f"{len(df)} rows")
    # 2. no duplicates
    if df["sub_category"].duplicated().any():
        fail("no-duplicates", "0 duplicate sub-categories",
             f"{df.loc[df['sub_category'].duplicated(), 'sub_category'].tolist()}")
    # 3. margins in (0, 100); low <= selected <= high; no NULL centrals
    for col in ["benchmark_gross_margin_pct", "benchmark_low_pct", "benchmark_high_pct"]:
        if df[col].isna().any():
            fail(f"{col}-resolved", "0 NULL (or mark row unresolved)",
                 f"NULLs in {col}")
        bad = df[~df[col].between(0, 100, inclusive="both")]
        if len(bad):
            fail(f"{col}-range", "all between 0 and 100",
                 f"{bad[['sub_category', col]].to_dict('records')}")
    viol = df[(df["benchmark_low_pct"] > df["benchmark_gross_margin_pct"]) |
              (df["benchmark_gross_margin_pct"] > df["benchmark_high_pct"])]
    if len(viol):
        fail("low-sel-high", "low <= selected <= high",
             f"{viol['sub_category'].tolist()}")
    # 4. source metadata present on every row
    for col in ["source_name", "source_url", "source_date", "methodology_note"]:
        blank = df[col].isna() | (df[col].astype(str).str.strip() == "")
        if blank.any():
            fail(f"meta-{col}", "present on all 17 rows",
                 f"missing for {df.loc[blank, 'sub_category'].tolist()}")
    # 5. source URLs valid / traceable (correction review)
    from urllib.parse import urlparse
    KNOWN_DOMAINS = ("stern.nyu.edu", "csimarket.com", "globenewswire.com",
                     "prnewswire.com", "millerknoll.com", "q4cdn.com", "hnicorp.com",
                     "businesswire.com", "sec.gov", "logitech.com",
                     "bestbuy.com")
    for _, r in df.iterrows():
        url = str(r["source_url"]).strip()
        parts = urlparse(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            fail("url-valid", f"absolute http(s) URL for {r['sub_category']}", url)
        if any(ch.isspace() or ch in "()" for ch in url):
            fail("url-clean", f"bare URL without prose/punctuation for {r['sub_category']}", url)
        if not any(d in parts.netloc for d in KNOWN_DOMAINS):
            fail("url-traceable", f"URL domain matching the cited source for {r['sub_category']}",
                 parts.netloc)
    # 6. level enum + fallback consistency
    if not df["benchmark_level"].isin(["SUB_CATEGORY", "CATEGORY", "OTHER"]).all():
        fail("level-enum", "SUB_CATEGORY/CATEGORY/OTHER only",
             f"{df['benchmark_level'].unique().tolist()}")
    if not df["confidence"].isin(["HIGH", "MEDIUM", "LOW"]).all():
        fail("confidence-enum", "HIGH/MEDIUM/LOW only",
             f"{df['confidence'].unique().tolist()}")
    if not df["fallback_used"].isin(["TRUE", "FALSE"]).all():
        fail("fallback-enum", "TRUE/FALSE only",
             f"{df['fallback_used'].unique().tolist()}")
    sub_lvl = df[df["benchmark_level"] == "SUB_CATEGORY"]
    if (sub_lvl["fallback_used"] != "FALSE").any():
        fail("level-fallback-consistency", "SUB_CATEGORY rows have fallback_used=FALSE",
             f"{sub_lvl.loc[sub_lvl['fallback_used'] != 'FALSE', 'sub_category'].tolist()}")
    cat_lvl = df[df["benchmark_level"] != "SUB_CATEGORY"]
    if (cat_lvl["fallback_used"] != "TRUE").any():
        fail("level-fallback-consistency", "CATEGORY/OTHER rows have fallback_used=TRUE",
             f"{cat_lvl.loc[cat_lvl['fallback_used'] != 'TRUE', 'sub_category'].tolist()}")
    return {
        "sub_category_count": int(len(df)),
        "subcategory_level_count": int((df["benchmark_level"] == "SUB_CATEGORY").sum()),
        "category_fallback_count": int((df["benchmark_level"] == "CATEGORY").sum()),
        "other_level_count": int((df["benchmark_level"] == "OTHER").sum()),
        "unresolved_count": int(df["benchmark_gross_margin_pct"].isna().sum()),
        "confidence_distribution": df["confidence"].value_counts().to_dict(),
        "selected_margin_min": float(df["benchmark_gross_margin_pct"].min()),
        "selected_margin_max": float(df["benchmark_gross_margin_pct"].max()),
        "selected_margin_mean": round(float(df["benchmark_gross_margin_pct"].mean()), 2),
    }


def main() -> None:
    df = build_frame()
    stats = validate(df)
    df.to_csv(BENCH_CSV, index=False, encoding="utf-8")

    # Re-read the artefact (validates what is on disk, not memory)
    chk = pd.read_csv(BENCH_CSV, dtype=str)
    assert len(chk) == EXPECTED_SUBCATEGORIES
    assert chk["sub_category"].nunique() == EXPECTED_SUBCATEGORIES

    report = {
        "input_universe": {"dim_product": str(DIM_CSV), "fact_sales": str(FACT_CSV),
                           "sub_categories": EXPECTED_SUBCATEGORIES},
        "number_of_sub_categories": stats["sub_category_count"],
        "sourced_subcategory_benchmarks": stats["subcategory_level_count"],
        "category_level_fallbacks": stats["category_fallback_count"],
        "other_level_fallbacks": stats["other_level_count"],
        "unresolved_benchmarks": stats["unresolved_count"],
        "unresolved_list": [],
        "confidence_distribution": stats["confidence_distribution"],
        "range_statistics": {
            "selected_min_pct": stats["selected_margin_min"],
            "selected_max_pct": stats["selected_margin_max"],
            "selected_mean_pct": stats["selected_margin_mean"],
        },
        "benchmark_values": df[["sub_category", "benchmark_gross_margin_pct",
                                "benchmark_low_pct", "benchmark_high_pct",
                                "benchmark_level", "confidence",
                                "fallback_used"]].to_dict("records"),
        "validation_results": "ALL BENCHMARK CHECKS PASSED (coverage-17, no-duplicates, "
                              "margins 0-100, low<=selected<=high, metadata present, "
                              "URL valid/traceable, level/fallback consistency)",
        "units": "percentages as plain numbers (40 = 40%); modeled COGS % = 100 - benchmark %",
        "quarantine_note": "source Profit was not read, not used, and plays no role in any benchmark.",
    }
    QUALITY_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"OK: {len(df)} sub-category benchmarks "
          f"({stats['subcategory_level_count']} SUB_CATEGORY, "
          f"{stats['category_fallback_count']} CATEGORY fallbacks, "
          f"{stats['unresolved_count']} unresolved)")
    print(f"OK: wrote {BENCH_CSV}, {QUALITY_JSON}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        raise
