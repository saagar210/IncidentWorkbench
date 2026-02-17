"""Cluster summarization service."""

import json
import sqlite3

from models.cluster import ClusterResult
from models.report import MetricsResult
from services.ollama_client import OllamaClient


class ClusterSummarizer:
    """Service for generating cluster summaries using LLM."""

    CLUSTER_NAME_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Short cluster name, 3-6 words"},
            "summary": {"type": "string", "description": "1-2 sentence summary"},
        },
        "required": ["name", "summary"],
    }

    def __init__(self, ollama: OllamaClient, db_conn: sqlite3.Connection) -> None:
        self.ollama = ollama
        self.db = db_conn

    async def name_cluster(self, incident_titles: list[str]) -> tuple[str, str]:
        """
        Generate a name and summary for a cluster.

        Args:
            incident_titles: List of incident titles in the cluster

        Returns:
            Tuple of (name, summary)
        """
        # Limit to first 20 titles to avoid context overflow
        titles_text = "\n".join(f"- {t}" for t in incident_titles[:20])

        prompt = (
            "You are an IT incident analyst. Below are titles of related IT incidents "
            "that have been grouped into a cluster. Generate a short descriptive name "
            "(3-6 words) and a 1-2 sentence summary of their common theme.\n\n"
            f"Incident titles:\n{titles_text}\n\n"
            "Respond with JSON containing 'name' and 'summary' fields."
        )

        try:
            response = await self.ollama.generate(
                prompt=prompt,
                model="llama3.2",
                format_schema=self.CLUSTER_NAME_SCHEMA,
            )
            parsed = json.loads(response)
            return parsed["name"], parsed["summary"]
        except (json.JSONDecodeError, KeyError):
            # Fallback if LLM fails
            return f"Cluster of {len(incident_titles)} incidents", "Auto-naming failed."

    async def name_all_clusters(self, run_id: str) -> None:
        """
        Generate names and summaries for all clusters in a run.

        Args:
            run_id: UUID of the cluster run
        """
        # Get run database ID
        cursor = self.db.execute(
            """
            SELECT id FROM cluster_runs WHERE id = ?
        """,
            (run_id,),
        )
        run_row = cursor.fetchone()
        if not run_row:
            return

        db_run_id = run_row["id"]

        # Get all clusters for this run
        cursor = self.db.execute(
            """
            SELECT id, cluster_label
            FROM clusters
            WHERE run_id = ?
        """,
            (db_run_id,),
        )
        cluster_rows = cursor.fetchall()

        for cluster_row in cluster_rows:
            cluster_db_id = cluster_row["id"]

            # Get incident titles for this cluster
            cursor = self.db.execute(
                """
                SELECT i.title
                FROM cluster_members cm
                JOIN incidents i ON i.id = cm.incident_id
                WHERE cm.cluster_id = ?
                ORDER BY i.title
            """,
                (cluster_db_id,),
            )
            title_rows = cursor.fetchall()
            titles = [r["title"] for r in title_rows]

            if not titles:
                continue

            # Generate name and summary
            name, summary = await self.name_cluster(titles)

            # Update cluster
            self.db.execute(
                """
                UPDATE clusters
                SET summary = ?, centroid_text = ?
                WHERE id = ?
            """,
                (name, summary, cluster_db_id),
            )

        self.db.commit()

    async def generate_executive_summary(
        self,
        quarter: str,
        metrics: MetricsResult,
        clusters: list[ClusterResult],
        trends: dict | None = None,
    ) -> str:
        """
        Generate LLM-powered executive summary.

        Args:
            quarter: Quarter label (e.g., "Q1 2024")
            metrics: Calculated metrics result
            clusters: List of cluster results
            trends: Optional additional trend data

        Returns:
            Executive summary as a string
        """
        # Build cluster information
        cluster_info = "\n".join(
            f"- {c.summary or f'Cluster {c.cluster_id}'} ({c.size} incidents): {c.centroid_text or 'No description'}"
            for c in clusters[:10]  # Limit to top 10 clusters
        )

        # Build severity breakdown text
        severity_text = (
            f"SEV1: {metrics.sev1_count}, "
            f"SEV2: {metrics.sev2_count}, "
            f"SEV3: {metrics.sev3_count}, "
            f"SEV4: {metrics.sev4_count}"
        )

        # Build monthly trend text if available
        monthly_text = ""
        if metrics.by_month:
            monthly_text = ", ".join(
                f"{month}: {count}" for month, count in sorted(metrics.by_month.items())
            )

        prompt = (
            f"You are an IT operations analyst writing an executive summary for the "
            f"{quarter} Quarterly Incident Review.\n\n"
            f"Key metrics:\n"
            f"- Total incidents: {metrics.total_incidents}\n"
            f"- Mean resolution time: {metrics.mean_resolution_hours:.1f} hours\n"
            f"- Median resolution time: {metrics.median_resolution_hours:.1f} hours\n"
            f"- P90 resolution time: {metrics.p90_resolution_hours:.1f} hours\n"
            f"- Severity breakdown: {severity_text}\n"
        )

        if monthly_text:
            prompt += f"- Monthly trend: {monthly_text}\n"

        prompt += (
            f"\nIncident clusters:\n{cluster_info}\n\n"
            f"Write a professional 3-4 paragraph executive summary covering: "
            f"overall trends, top incident categories, resolution performance, "
            f"and recommendations. Use a direct, factual tone suitable for technical leadership."
        )

        return await self.ollama.generate(prompt=prompt, model="llama3.2")
