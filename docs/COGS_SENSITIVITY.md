# COGS Sensitivity Analysis (Phase 1C-3)

> Method: every sub-category benchmark shifted **±5 percentage points**
> (clipped to [0, 100]; no clipping bound was hit), COGS/profit/margin
> recomputed from the same formulas. Base model untouched. Data:
> `data/processed/cogs_sensitivity.csv` (17 rows + TOTAL). Margins below are
> `SUM(profit)/SUM(revenue)×100` per scenario — never averaged percentages.

## 1. Results (±5pp, uniform shift)

| sub_category | base margin % | downside (−5pp) | upside (+5pp) | base profit $ | downside profit $ | upside profit $ |
|---|---|---|---|---|---|---|
| Bookcases | 40 | 35 | 45 | 45,952 | 40,208 | 51,696 |
| Chairs | 40 | 35 | 45 | 131,380 | 114,957 | 147,802 |
| Furnishings | 40 | 35 | 45 | 36,682 | 32,097 | 41,267 |
| Tables | 40 | 35 | 45 | 82,786 | 72,438 | 93,134 |
| Appliances | 38 | 33 | 43 | 40,862 | 35,486 | 46,239 |
| Art | 38 | 33 | 43 | 10,305 | 8,949 | 11,661 |
| Binders | 38 | 33 | 43 | 77,297 | 67,126 | 87,467 |
| Envelopes | 38 | 33 | 43 | 6,261 | 5,437 | 7,085 |
| Fasteners | 38 | 33 | 43 | 1,149 | 998 | 1,300 |
| Labels | 38 | 33 | 43 | 4,745 | 4,120 | 5,369 |
| Paper | 38 | 33 | 43 | 29,822 | 25,898 | 33,746 |
| Storage | 38 | 33 | 43 | 85,061 | 73,868 | 96,253 |
| Supplies | 38 | 33 | 43 | 17,736 | 15,402 | 20,070 |
| Accessories | 35 | 30 | 40 | 58,583 | 50,214 | 66,952 |
| Copiers | 30 | 25 | 35 | 44,858 | 37,382 | 52,335 |
| Machines | 25 | 20 | 30 | 47,310 | 37,848 | 56,772 |
| Phones | 25 | 20 | 30 | 82,502 | 66,001 | 99,002 |
| **TOTAL** | **34.97** | **29.97** | **39.97** | **803,291** | **688,431** | **918,151** |

Total modeled profit moves $688k–$918k (≈ ±14% around base); total COGS
moves $1.379M–$1.609M. No scenario hits the 0%/100% clip bounds.

Sensitivity is computed purely on the authoritative revenue-based COGS model
(benchmark margin → COGS % → `net_revenue × COGS %`); the derived
`implied_modeled_cogs_per_unit` field plays no role in any scenario.

## 2. Interpretation — what is actually robust

- **Robust: the tier structure, not the exact ranking.** In every uniform
  scenario the order Furniture (35–45) > Office Supplies (33–43) >
  Accessories (30–40) > Copiers (25–35) > Machines/Phones (20–30) is
  preserved with no rank flips. The top tier (Furniture/Office, worst case
  33–35%) never overlaps the bottom tier (Machines/Phones, best case 30%) —
  that separation survives even asymmetric error and is the safest
  conclusion of this phase.
- **Fragile: Furniture-vs-Office Supplies ordering.** Only 2pp separates
  them (40 vs 38), less than the ±5pp uncertainty — under asymmetric error
  (Furniture −5, Office +5) the order flips (35 vs 43). Report "Furniture and
  Office Supplies form the high-margin tier" — never "Furniture is the
  highest-margin category" as a hard claim.
- **Robust: Phones and Machines are the lowest-margin pool.** Even at upside
  (30%) they only touch Copiers' base (30%) and stay below every other
  group's base. Any low-profit-product triage should start here; that
  conclusion does not depend on the benchmark being exactly right.
- **Fragile: Accessories-vs-Copiers gap (5pp).** Preserved under uniform
  shift but exactly equal to the uncertainty width — asymmetric error could
  erase it. Treat as indicative, not decisive.
- **Robust: the overall margin band.** 29.97%–39.97% — the business is
  modeled in the low-to-mid 30s, not at 20% and not at 50%. Do not quote
  "34.97%" without its ±5pp band; no pricing or portfolio decision should
  hinge on the second significant figure of a modeled margin.
- **Not tested here:** within-sub-category product spread (hidden by design),
  the reseller-vs-manufacturer channel gap (§8 of the methodology note), and
  time-mismatch of 2024–2026 anchors on 2014–2017 sales. Sensitivity bounds
  assumption width, not structural bias — all scenarios share the same
  structure.
