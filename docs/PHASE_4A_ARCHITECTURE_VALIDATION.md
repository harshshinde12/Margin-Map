# Phase 4A Architecture Validation (design checks, no estimates)

> Method: static verification of the Phase 4A design against frozen Phase
> 1–3 contracts, the inspected schemas, and the Phase 4A mandate
> (architecture only; no implementation, no outputs, no elasticity, no
> quantity-response values, no fixed-unit-cost method, no dashboards, no
> frozen-artifact changes, no Git operations). **No calculations were
> implemented and no scenario artifacts were generated** — there is nothing
> to reconcile numerically, so every check below is structural
> (definitions, lineage, grain, controls, boundaries, and gate
> completeness). Each check cites the architecture section that implements
> the requirement.

## Results

- [x] **Phase boundary held.** The three documents contain observed,
  derived, modeled, and *specified-hypothetical* structures only. No
  scenario calculation, output, dashboard, elasticity estimate,
  quantity-response value, customer-reaction assumption, or fixed-unit-cost
  method exists anywhere in them. pricing-scenario, elasticity, and causal
  machinery appear solely as deferred or forbidden items with their
  activation bars stated.
- [x] **Purpose taxonomy enforced.** Arithmetic sensitivity and labeled
  illustration permitted; demand-response modeling, causal evaluation, and
  optimization declared outside the evidence base with reasons
  (architecture §1; D4A-01). Exposure-vs-response is the load-bearing
  distinction and is stated before any mechanics.
- [x] **Grain and authority map preserved.** Line-level application with
  strictly bottom-up order aggregation; authoritative contribution
  reporting at order grain and above; initial scope order × band and
  Segment × band (ORDER basis) with customer-level separately gated;
  category/sub-category gross-only companions; product contribution never
  licensed; no freight allocation below order grain (architecture §2;
  D4A-02, D4A-03). Consistent with Phase 2B.1 authority and the Phase 3B
  basis discipline.
- [x] **Discount input design guarded.** Observed vs hypothetical values
  never merged; pp-change primary with a single reconciled alternative
  form; valid range [0, 0.80] capped at observed support with no
  extrapolation machinery; `d' = 1` impossible by construction with
  fail-loud handling for NULL/negative/over-bound; zero-discount
  participation and B0 identifiability preserved; near-bound over-increases
  excluded per line with counts (never clipped); out-of-scope passthrough
  keeps baseline reconciliation exact. No business values chosen
  (architecture §3; D4A-04).
- [x] **Revenue recalculation honest.** Observed net, reconstructed gross,
  discount amount, and hypothetical net kept distinct with correct lineage
  labels; constant-quantity arithmetic (`gross × (1 − d')`) specified in
  closed form and labeled scenario-not-forecast; quantity movement assigned
  exclusively to a separate assumption layer (architecture §4; D4A-05).
- [x] **Quantity framework surveys without selecting.** All five approaches
  recorded with standing; statistical and elasticity estimation blocked on
  the carried Phase 3A §7 grounds; constant quantity the only active
  assumption (labeled as such); the five-condition §5.2 activation bar
  specified before any non-constant response may enter (D4A-05). No
  coefficient, rate, or default exists in the design.
- [x] **COGS treatment does not misrepresent the model.** Default
  hypothetical-COGS rule recomputes from frozen benchmarks with the
  margin-constancy consequence required on-output; benchmark model never
  presented as fixed unit cost; gated comparator specified as conditions
  and labeling only (activation requires an approved per-unit source that
  does not exist; implied per-unit value explicitly disqualified); actual-
  cost arrival routed to the Phase 1C-2 input contract as a data path
  (architecture §6; D4A-06). No method selected, nothing implemented.
- [x] **Cost-to-serve treatment invents nothing.** Freight passthrough
  unchanged; ambiguous pair NULL/flagged at line grain under all scenarios
  (25.05 via order aggregation only); return status filter-only with
  UNKNOWN never defaulted; return/support OFF with zero-means-excluded;
  future rate layers confined to permitted families (R-C/S-D still
  rejected); hidden defaults forbidden (architecture §7; D4A-07).
- [x] **Contribution claims leveled.** Frozen waterfall restated on
  hypothetical inputs with dual reconciliation, SUM/SUM margins, and
  percentage-point changes; arithmetic scenario contribution producible
  beside its baseline, forecast and causal-impact claims forbidden
  (architecture §8; D4A-08).
- [x] **Taxonomy bounded.** Six scenario structures with scope-plus-form
  definitions, combinations as scoped instances, one identifier per
  instance; no activation, no values (architecture §9; D4A-09).
- [x] **Guardrails and wording specified as requirements.** Eleven
  fail-loud safeguards and the permitted/prohibited wording regime with
  hypothetical naming, tier labeling, and on-visual caveats; prohibited
  phrases occur in the design solely inside the prohibition list
  (architecture §§10–11; D4A-10).
- [x] **Approval gates complete.** All ten required gates enumerated with
  their Phase 4B preconditions; Phase 4A closure conditioned on no build
  starting before gate decisions (architecture §12; decision-log questions).
- [x] **All twelve mandated topics covered.** Purpose (§1), grain (§2),
  discount inputs (§3), revenue recalculation (§4), quantity framework
  (§5), COGS (§6), cost-to-serve (§7), contribution (§8), scenario types
  (§9), guardrails (§10), reporting (§11), approval gates (§12) — each with
  a dedicated architecture section and at least one D4A decision.
- [x] **Terminology and lineage consistent with Phases 1–3.** Frozen
  waterfall, denominators, quarantine, OFF defaults, ambiguity controls,
  NULL reasons, flag disciplines, and evidence tiers reused verbatim;
  observed / derived / modeled / hypothetical layers distinguished
  throughout; no definition redefined.
- [x] **No invented numbers.** No scenario value, elasticity, response
  coefficient, cost rate, or threshold constant created anywhere in the
  three documents; the only figures cited are frozen observed evidence
  (9,994 lines; 5,009 orders; bands and counts; baseline 565,116.9418 /
  24.6002%; freight 238,173.79; ambiguity 25.05; thresholds 30/10) reused
  as design anchors, never as new analytical outputs.
- [x] **No frozen artifacts changed; no implementation started.** No Phase
  1–3 data file, script, document, or schema modified, regenerated,
  renamed, or overwritten; no scripts, CSVs, JSON, tables, visuals, or
  scenario outputs created; no Git operations performed.

## Design risks carried forward (not failures)

1. The constant-quantity label must survive into every future output —
   readers will otherwise read arithmetic as prediction (D4A-05, §11).
2. Within-benchmark-group margin constancy under the default COGS rule will
   tempt unit-cost readings — the on-output constancy statement is
   load-bearing (D4A-06).
3. ORDER-basis vs LINE-basis discipline from Phase 3B must be honored in
   scenario reporting; the two bases must never be mixed in one average
   (D4A-02, D4A-03).
4. Scope creep (customer level, above-0.80 discounts, response defaults) is
   the principal future risk — each is explicitly gated, and ungated
   extension fails validation by design (§12).

**ARCHITECTURE VALIDATED — PHASE 4A READY FOR REVIEW** (pending owner
decisions in `PHASE_4A_DECISION_LOG.md`, final section; no Phase 4B build
before §12 gates are decided).
