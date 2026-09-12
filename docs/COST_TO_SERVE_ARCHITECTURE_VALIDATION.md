# Cost-to-Serve Architecture Validation (Phase 2A — design checks, no estimates)

> Method: static verification of the design against Phase 1 contracts and the
> Phase 2A brief. **No numerical cost estimates were generated** — there is
> nothing to reconcile numerically yet, so every check below is structural
> (definitions, lineage, grain, controls) rather than arithmetic. Each check
> cites the exact model-doc section that implements the requirement.

## Results (re-run after D2A-11 observed-freight update)

- [x] **Compatibility with Phase 1.** Formulas extend frozen definitions
  verbatim (model §1); frozen files untouched (re-verified hashes:
  `fact_sales.csv d7478eb5…`, `fact_sales_cogs.csv 4d8de717…`,
  `dim_product.csv 354417cb…`, benchmarks `37e213f8…`, `archive.zip
  574F496D…`). Serve fields exist only as dictionary specifications; no
  implementation outputs created.
- [x] **Observed freight provenance.** `freight_cost` = Dataset 1-US
  `Shipping Cost`, joined by the approved composite signature with a
  documented 9,994/9,994 — 0-unmatched audit (`PHASE_2_DATA_COMPATIBILITY_
  REPORT.md` §4). Status OBSERVED with an explicit methodology caveat
  (in-file computation undocumented); never called allocated or modeled.
- [x] **No freight allocation double counting.** Allocation machinery is
  withdrawn for freight (model §2.1, §5.1; D2A-11): freight joins
  line-to-line, so there is no pool to double-split and no order-charge to
  mis-sum. Line grain verified (varies across all 2,471 multi-line orders),
  US total 238,173.79. XOR/direct-charge conflict class is structurally
  absent for freight; controls retained for future scenario pools.
- [x] **Single ambiguity explicitly controlled.** The 21.59/3.46 pair
  (Phase 1 rows 3406/3407) is flagged, never silently assigned; order total
  25.05 invariant so all aggregates stay reliable. Loader contract:
  `freight_match_status` / `freight_ambiguity_flag` / `freight_method`
  non-nullable on every line; any `UNMATCHED` line fails loudly.
- [x] **No fabricated freight values.** No per-mode charges, splits, or
  totals invented — the only freight figure in the design (238,173.79 and
  the 25.05 pair) is quoted from the investigated source, not constructed.
- [x] **No source Profit dependency.** `source_profit_quarantined` appears
  solely in control §10.6 as forbidden input. No new scripts exist in this
  task; nothing computes from Profit.
- [x] **Returns remains non-authoritative.** Dataset 2 Returns rejected
  (0/1,970 universe match); Returned status, refunded revenue, and returned
  quantity all specified UNAVAILABLE; processing cost scenario-only, OFF by
  default, no rate.
- [x] **Support remains modeled/OFF.** No default rate, no ticket feed;
  proxies scenario-only with stated biases (D2A-05).
- [x] **COGS remains separate.** Serve lineage excludes `modeled_cogs` and
  `implied_*` by dictionary rule; contribution identities (`Net − COGS −
  serve` ≡ `Gross − serve`) specified as dual-checked assertions.
- [x] **Contribution formulas remain consistent.** Frozen Phase 1A
  waterfall restated with prefixes and NULL guards; SUM/SUM margins;
  averaging percentages forbidden.
- [x] **Future Power BI drilldowns remain feasible.** Line grain + frozen
  keys + `scenario_layer` separation + tier labels unchanged; order-level
  ambiguity treatment keeps drill paths exact at every aggregate.
- [x] **Reproducibility and provenance documented.** Deterministic join key
  (composite signature, names excluded by rule); file hash recorded at load
  (`freight_source`); versioned assumptions; fail-loud on unmatched lines
  and all-zero pool weights; comparator/scenario outputs retained.

## Design risks carried forward (not failures)

1. ~~F-H's per-mode charges are unsourced — the single largest future
   assumption surface.~~ **RESOLVED by D2A-11** (observed freight; the
   largest remaining assumption surface is return/support scenarios).
2. Returns/support are scenario-or-nothing until event data — early
   contribution views will be freight-only + labeled partials (D2A-04/05).
3. No weight or origin data bounds freight *interpretation* (e.g.
   efficiency benchmarking), though not freight *measurement* — the design
   says so openly; Shipping Cost methodology itself remains unverified.
4. The single ambiguous order pair requires the flagged order-level
   treatment in every implementation and BI view — a reviewer must be able
   to find the flag, not just the totals.

**ARCHITECTURE VALIDATED — PHASE 2A READY FOR REVIEW** (pending owner
decisions in `COST_TO_SERVE_DECISION_LOG.md`, final-report §E).
