"""Clustering result models."""

from datetime import datetime

from pydantic import BaseModel, Field


class ClusterResult(BaseModel):
    """Single cluster within a run."""

    cluster_id: int
    incident_ids: list[int] = Field(default_factory=list)
    size: int
    summary: str | None = None
    centroid_text: str | None = None


class ClusterRunResult(BaseModel):
    """Complete clustering run result."""

    run_id: str
    n_clusters: int
    method: str
    parameters: dict = Field(default_factory=dict)
    clusters: list[ClusterResult] = Field(default_factory=list)
    noise_incident_ids: list[int] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
