"""Pydantic response schemas (Phase 8).

Every column in the frozen Phase 6 tables is TEXT, so every field here
is ``str``. Values are passed through verbatim -- no numeric coercion,
no recalculation -- to preserve frozen semantics (including empty-string
N/A markers, flag strings, and label values).
"""

from __future__ import annotations

from pydantic import BaseModel


class BaselineMetric(BaseModel):
    output_name: str
    scenario_status: str
    grain: str
    source_artifact: str
    metric_name: str
    metric_value: str
    unit: str
    definition_ref: str
    limitation: str


class ContributionRecord(BaseModel):
    output_name: str
    scenario_status: str
    grain: str
    basis: str
    band: str
    source_artifact: str
    metric_name: str
    metric_value: str
    unit: str
    definition_ref: str
    limitation: str


class ScenarioRecord(BaseModel):
    output_name: str
    scenario_status: str
    grain: str
    scenario_id: str
    block: str
    source_artifact: str
    metric_name: str
    metric_value: str
    unit: str
    definition_ref: str
    limitation: str


class VarianceRecord(BaseModel):
    output_name: str
    scenario_status: str
    grain: str
    scenario_id: str
    band: str
    block: str
    source_artifact: str
    metric_name: str
    metric_value: str
    unit: str
    definition_ref: str
    limitation: str


class OrderReading(BaseModel):
    output_name: str
    scenario_status: str
    grain: str
    order_id: str
    discount_band: str
    return_status: str
    neg_flag: str
    ambiguity_note: str
    source_artifact: str
    metric_name: str
    metric_value: str
    unit: str
    definition_ref: str
    limitation: str


class QualityCheck(BaseModel):
    output_name: str
    scenario_status: str
    grain: str
    artifact: str
    check_id: str
    metric_name: str
    metric_value: str
    unit: str
    status: str
    expected: str
    actual: str
    source_artifact: str
    definition_ref: str
    limitation: str


class HealthResponse(BaseModel):
    status: str
    database: str
    read_only: bool


class BaselineList(BaseModel):
    data: list[BaselineMetric]
    count: int


class ContributionList(BaseModel):
    data: list[ContributionRecord]
    count: int


class ScenarioList(BaseModel):
    data: list[ScenarioRecord]
    count: int


class VarianceList(BaseModel):
    data: list[VarianceRecord]
    count: int


class OrdersPage(BaseModel):
    data: list[OrderReading]
    count: int
    limit: int
    offset: int


class QualityList(BaseModel):
    data: list[QualityCheck]
    count: int
