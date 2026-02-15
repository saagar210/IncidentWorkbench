"""Report result models."""

from datetime import datetime

from pydantic import BaseModel, Field


class MetricsResult(BaseModel):
    """Metrics calculation result."""

    total_incidents: int
    sev1_count: int
    sev2_count: int
    sev3_count: int
    sev4_count: int
    unknown_count: int
    mean_resolution_hours: float | None = None
    median_resolution_hours: float | None = None
    p50_resolution_hours: float | None = None
    p90_resolution_hours: float | None = None
    mttr_by_severity: dict[str, float] = Field(default_factory=dict)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    by_month: dict[str, int] = Field(default_factory=dict)
    by_assignee: dict[str, int] = Field(default_factory=dict)
    by_project: dict[str, int] = Field(default_factory=dict)


class ReportResult(BaseModel):
    """Generated report metadata."""

    report_id: str
    cluster_run_id: str
    title: str
    executive_summary: str
    metrics: MetricsResult
    docx_path: str | None = None
    created_at: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
