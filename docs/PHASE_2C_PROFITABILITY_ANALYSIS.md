# Phase 2C Profitability Analysis (baseline, scenarios OFF)

> Built by `src/data/build_phase2c_profitability.py` → 5 CSVs +
> `profitability_summary.json` (all checks A–O pass; deterministic).
> Definitions: **gross profit = revenue − COGS** (no freight);
> **contribution profit = revenue − COGS − freight − 0 − 0** (scenarios OFF).
> "Profit" is never used ambiguously. Medians split quadrants (revenue
> 2,256.39; contribution 544.02; n = 793). No causal claims, no
> recommendations — patterns only.

## 1. Highest-revenue customers

SM-20320 Sean Miller (25,043.05) · TC-20980 Tamara Chand (19,052.22) ·
RB-19360 Raymond Buch (15,117.34) · TA-21385 Tom Ashbrook (14,595.62) ·
AB-10105 Adrian Barton (14,473.57). Top 10 take **6.70%** of revenue —
revenue is unconcentrated (no dominant account).

## 2. Highest-contribution customers

SM-20320 (6,265.59) · TC-20980 (5,351.90) · RB-19360 (4,398.71) · KL-16645
Ken Lonsdale (4,371.96) · AB-10105 (4,371.55). Top 10 take **7.62%** of
contribution. Revenue and contribution top-10 lists overlap **8/10** —
scale and efficiency largely coincide at the top.

## 3. High-revenue customers with weak contribution

Quadrant HIGH_REVENUE_LOW_CONTRIBUTION: **30 customers**, revenue
**85,264.92 (3.71%)**, contribution **12,472.19** — the primary margin-risk
cohort (representative: SA-20830 at 4,767.34 revenue → 531.01 contribution).
HIGH_REVENUE_NEGATIVE_CONTRIBUTION: **empty** — no high-revenue customer is
currently loss-making.

## 4. Loss-making customers

**None: 0 of 793** (minimum contribution 1.43, TS-21085; minimum margin
0.32%). Loss-making revenue and contribution are therefore 0.00. This is a
structural finding, not proof of safety: modeled gross margins are positive
by construction on every line and observed freight never exceeds any
customer's gross profit — so baseline contribution cannot go negative at
customer grain here. Loss visibility awaits return/support scenarios and
finer freight attribution. 50 individual orders ARE contribution-negative
today; aggregation absorbs them.

## 5. Products generating the most gross profit

Canon imageCLASS 2200 copier (18,479.95 on 61,599.82 revenue) · Fellowes
PB500 binding machine (10,432.29) · HON 5400 task chairs (8,748.23) · GBC
DocuBind TL300 (7,532.92) · GBC Ibimaster 500 (7,229.31). Top 10 products:
10.65% of revenue, 10.50% of gross profit. 93 single-order products flagged
`low_volume_flag` — their margins are arithmetic, not evidence.

## 6. Products generating negative gross profit

**None: 0 of 1,894** (minimum 0.62) — structurally guaranteed, since every
benchmark margin sits below 100%. Negative-product analysis becomes
meaningful only with actual costs or scenario layers.

## 7. Sub-categories generating the most gross profit

Chairs (131,379.64) · Storage (85,060.57) · Tables (82,786.21) · Phones
(82,501.76) · Binders (77,296.84). No sub-category is gross-negative
(margins equal benchmarks 25–40% by construction — this table restates
assumption × mix, not discovery; labeled gross, never contribution).

## 8. Revenue concentration

Customers top-10: 6.70% revenue / 7.62% contribution. Products top-10:
10.65% / 10.50%. Neither customers nor products concentrate — the business
is broad-based in this sample.

## 9. Contribution concentration

Mirrors revenue (7.62% top-10) because freight is roughly proportional and
margins are benchmark-driven; the 8/10 top-list overlap confirms no hidden
concentration break between scale and efficiency.

## 10. Ranking differences (revenue vs profit)

8/10 shared IDs at customer level; divergences are informative, not
alarming (e.g. TA-21385 ranks 4th by revenue but lower by contribution —
the precise customers where freight/mix bite, listed in the risk file).

## 11. Revenue from negative-contribution customers

**0.00** — no negative-contribution customers exist (§4).

## 12. High-revenue/low-contribution cohort size

30 customers · 85,264.92 revenue (3.71%) · 12,472.19 contribution (2.21% of
total contribution) · implied cohort margin ≈ 14.6% vs 24.60% overall. This
— not a loss list — is the actionable baseline-risk pool, pending scenarios.

## Grain honesty appendix

- Customer contribution uses complete order economics (A–D reconciled).
- Customer × sub-category carries gross profit ONLY; freight/contribution
  columns are explicitly NULL (`FREIGHT_NOT_ATTRIBUTABLE_BELOW_ORDER_GRAIN`).
- Product/sub-category figures are gross only; no product contribution
  metric exists anywhere (asserted in-script).
- Region per customer = revenue-dominant (`multi_region_flag` where mixed);
  segment and names are 1:1. Volumes (`order_count`, `quantity`) ship with
  every table; nothing was removed.
