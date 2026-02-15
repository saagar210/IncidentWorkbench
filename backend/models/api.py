"""API request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from models.cluster import ClusterRunResult
from models.incident import Incident, Severity
from models.report import MetricsResult


# Request schemas
class JiraIngestRequest(BaseModel):
    """Request to ingest incidents from Jira."""

    url: str = Field(..., description="Jira instance URL")
    email: str = Field(..., description="Jira user email")
    api_token: str = Field(..., description="Jira API token")
    jql: str = Field(..., description="JQL query to find incidents")


class SlackIngestRequest(BaseModel):
    """Request to ingest incidents from Slack."""

    bot_token: str = Field(..., description="Slack bot token")
    channel_id: str = Field(..., description="Channel ID to search")
    days_back: int = Field(default=30, ge=1, le=365, description="Days to look back")


class SlackExportIngestRequest(BaseModel):
    """Request to ingest from Slack export JSON."""

    json_path: str = Field(..., description="Path to Slack export JSON file")
    channel_name: str = Field(..., description="Channel name to extract")


class ClusterRequest(BaseModel):
    """Request to run clustering."""

    method: str = Field(default="dbscan", description="Clustering method (dbscan, kmeans)")
    min_samples: int = Field(default=3, ge=1, description="Minimum samples for DBSCAN")
    eps: float = Field(default=0.3, ge=0.0, le=1.0, description="Epsilon for DBSCAN")
    n_clusters: int | None = Field(default=None, ge=2, description="Number of clusters for K-means")


class ReportGenerateRequest(BaseModel):
    """Request to generate a report."""

    cluster_run_id: str = Field(..., description="Cluster run ID (UUID)")
    title: str = Field(default="Incident Analysis Report", description="Report title")
    quarter_label: str = Field(..., description="Quarter label (e.g., 'Q1 2024')")
    chart_pngs: dict[str, str] = Field(default_factory=dict, description="Chart names to base64-encoded PNG data")


class TestConnectionRequest(BaseModel):
    """Request to test external service connection."""

    url: str | None = None
    email: str | None = None
    api_token: str | None = None
    bot_token: str | None = None


# Response schemas
class IngestResponse(BaseModel):
    """Response from ingestion operation."""

    incidents_ingested: int
    incidents_updated: int
    errors: list[str] = Field(default_factory=list)


class ClusterResponse(BaseModel):
    """Response from clustering operation."""

    run: ClusterRunResult


class ReportResponse(BaseModel):
    """Response with report metadata."""

    report_id: str
    cluster_run_id: str
    metrics: MetricsResult
    file_path: str
    generated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class IncidentResponse(BaseModel):
    """Single incident response."""

    incident: Incident


class IncidentListResponse(BaseModel):
    """List of incidents response."""

    incidents: list[Incident]
    total: int
    severity_filter: Severity | None = None


class TestConnectionResponse(BaseModel):
    """Test connection response."""

    success: bool
    message: str
    details: dict = Field(default_factory=dict)
