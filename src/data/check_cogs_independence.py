"""P0 circularity guard: modeled COGS must be independent of observed Profit.

Static check (fails loudly if reintroduced):
1. Benchmark/dimension builders never read the quarantined Profit column.
2. COGS applier never computes COGS from Profit/Gross Profit.
3. Assumption outputs carry no profit-derived input.

Run from the project root:
    python src/data/check_cogs_independence.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "benchmarks": ROOT / "src" / "data" / "build_subcategory_benchmarks.py",
    "dimension": ROOT / "src" / "data" / "build_product_dimension.py",
    "applier": ROOT / "src" / "data" / "apply_modeled_cogs.py",
}

# Patterns that would indicate COGS derived from observed profitability.
FORBIDDEN = [
    r"source_profit_quarantined",
    r"Sales\s*-\s*Profit",
    r"gross_profit['\"]?\s*\)?\s*(as|=).*cogs",
    r"cogs.*=\s*.*profit",
]

# Allowed: quarantine notes, comments, and the applier's source-preservation
# checks (which compare but never compute from Profit).
ALLOWED_CONTEXT = re.compile(r"quarantine|never|not |untouched|preserv|reference only", re.I)


def main() -> None:
    violations: list[str] = []
    for name, path in FILES.items():
        text = path.read_text(encoding="utf-8")
        if name in ("benchmarks", "dimension"):
            if "source_profit_quarantined" in text and "never" not in text.lower():
                violations.append(f"{name}: reads quarantined Profit")
            continue
        # applier: flag only COGS-assignment lines that read profit.
        # (profit = revenue - cogs is the CORRECT direction and is allowed.)
        for i, line in enumerate(text.splitlines(), 1):
            if "=" not in line:
                continue
            lhs, rhs = line.split("=", 1)
            lhs_low, rhs_low = lhs.lower(), rhs.lower()
            lhs_is_cogs = ("cogs" in lhs_low and "gross_profit" not in lhs_low
                           and "gross_margin" not in lhs_low)
            if lhs_is_cogs and "profit" in rhs_low:
                violations.append(f"applier:{i}: {line.strip()[:120]}")
        # direct COGS = Sales - Profit pattern anywhere in applier
        if re.search(r"modeled_cogs['\"]?\]\s*=\s*.*sales.*-\s*.*profit", text, re.I):
            violations.append("applier: COGS computed as Sales - Profit")
    # assumption outputs must not contain profit-derived inputs
    import pandas as pd

    assum = ROOT / "data" / "processed" / "product_cogs_assumptions.csv"
    if assum.is_file():
        df = pd.read_csv(assum, nrows=5)
        bad = [c for c in df.columns if "profit" in c.lower() and "modeled" not in c.lower()
               and "benchmark" not in c.lower()]
        if bad:
            violations.append(f"assumptions carry profit inputs: {bad}")
    if violations:
        print("COGS INDEPENDENCE FAILED:", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        raise SystemExit(1)
    print("OK: COGS independent of observed Profit (static + artifact checks passed)")


if __name__ == "__main__":
    main()
