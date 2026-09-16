/**
 * TypeScript mirrors of the Phase 8 FastAPI response schemas.
 * Every analytical field is a string because the frozen SQLite layer
 * stores all columns as TEXT; values pass through verbatim.
 */

export interface BaselineMetric {
  output_name: string;
  scenario_status: string;
  grain: string;
  source_artifact: string;
  metric_name: string;
  metric_value: string;
  unit: string;
  definition_ref: string;
  limitation: string;
}

export interface ContributionRecord {
  output_name: string;
  scenario_status: string;
  grain: string;
  basis: string;
  band: string;
  source_artifact: string;
  metric_name: string;
  metric_value: string;
  unit: string;
  definition_ref: string;
  limitation: string;
}

export interface ScenarioRecord {
  output_name: string;
  scenario_status: string;
  grain: string;
  scenario_id: string;
  block: string;
  source_artifact: string;
  metric_name: string;
  metric_value: string;
  unit: string;
  definition_ref: string;
  limitation: string;
}

export interface VarianceRecord {
  output_name: string;
  scenario_status: string;
  grain: string;
  scenario_id: string;
  band: string;
  block: string;
  source_artifact: string;
  metric_name: string;
  metric_value: string;
  unit: string;
  definition_ref: string;
  limitation: string;
}

export interface OrderReading {
  output_name: string;
  scenario_status: string;
  grain: string;
  order_id: string;
  discount_band: string;
  return_status: string;
  neg_flag: string;
  ambiguity_note: string;
  source_artifact: string;
  metric_name: string;
  metric_value: string;
  unit: string;
  definition_ref: string;
  limitation: string;
}

export interface QualityCheck {
  output_name: string;
  scenario_status: string;
  grain: string;
  artifact: string;
  check_id: string;
  metric_name: string;
  metric_value: string;
  unit: string;
  status: string;
  expected: string;
  actual: string;
  source_artifact: string;
  definition_ref: string;
  limitation: string;
}

export interface HealthResponse {
  status: string;
  database: string;
  read_only: boolean;
}

export interface ListResponse<T> {
  data: T[];
  count: number;
}

export interface OrdersPage {
  data: OrderReading[];
  count: number;
  limit: number;
  offset: number;
}

/** Units observed in the frozen outputs. */
export type Unit = 'CUR' | 'PCT' | 'PP' | 'DEC' | 'CT' | 'Flag' | 'Label' | string;
