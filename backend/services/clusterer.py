"""Clustering service."""

import json
import sqlite3
from uuid import uuid4

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

from exceptions import ClusteringError, InsufficientDataError
from models.cluster import ClusterResult, ClusterRunResult


class IncidentClusterer:
    """Service for clustering incidents based on embeddings."""

    def __init__(self, db_conn: sqlite3.Connection) -> None:
        self.db = db_conn

    def run(
        self,
        num_clusters: int | None = None,
        min_clusters: int = 2,
        max_clusters: int = 15,
        linkage: str = "average",
        metric: str = "cosine",
    ) -> ClusterRunResult:
        """
        Run clustering on all incidents with embeddings.

        CRITICAL: linkage must be 'average' or 'complete' when metric='cosine'.
        Ward linkage requires metric='euclidean' and WILL CRASH with cosine.

        Args:
            num_clusters: Fixed number of clusters (None = auto-determine)
            min_clusters: Minimum clusters for auto mode
            max_clusters: Maximum clusters for auto mode
            linkage: Linkage method ('average', 'complete', 'ward')
            metric: Distance metric ('cosine', 'euclidean')

        Returns:
            ClusterRunResult with cluster assignments and metrics.

        Raises:
            ValueError: If ward linkage used with cosine metric
            InsufficientDataError: If not enough incidents
            ClusteringError: If clustering fails
        """
        # GUARD CHECK - MUST HAVE THIS
        if linkage == "ward" and metric == "cosine":
            raise ValueError(
                "Ward linkage is incompatible with cosine distance. "
                "Use 'average' or 'complete' linkage with cosine metric."
            )

        # Load embeddings from database
        cursor = self.db.execute("""
            SELECT e.incident_id, e.embedding
            FROM embeddings e
            JOIN incidents i ON i.id = e.incident_id
            ORDER BY e.incident_id
        """)
        rows = cursor.fetchall()

        # Auto-k mode uses silhouette score, which requires >=3 samples.
        if num_clusters is None:
            min_required = max(min_clusters, 3)
            if len(rows) < min_required:
                raise InsufficientDataError(
                    f"Need at least {min_required} incidents with embeddings for auto clustering, got {len(rows)}"
                )

        if len(rows) < min_clusters:
            raise InsufficientDataError(
                f"Need at least {min_clusters} incidents with embeddings, got {len(rows)}"
            )

        if num_clusters is not None and len(rows) < num_clusters:
            raise InsufficientDataError(
                f"Need at least {num_clusters} incidents with embeddings, got {len(rows)}"
            )

        # Build embedding matrix
        incident_ids = [row["incident_id"] for row in rows]
        matrix = np.array(
            [np.frombuffer(row["embedding"], dtype=np.float32) for row in rows]
        )  # Shape: (n_incidents, 768)

        # Run clustering
        try:
            if num_clusters is not None:
                # Fixed cluster count
                labels, score = self._cluster_fixed(matrix, num_clusters, linkage, metric)
            else:
                # Auto-determine via silhouette score
                labels, num_clusters, score = self._cluster_auto(
                    matrix, min_clusters, max_clusters, linkage, metric
                )

        except Exception as e:
            raise ClusteringError(
                f"Clustering failed: {e}",
                details={"error": str(e), "linkage": linkage, "metric": metric},
            )

        # Store results in database
        run_id = self._store_cluster_run(incident_ids, labels, num_clusters, linkage, metric, score)

        # Build result object
        return self._build_result(
            run_id, incident_ids, labels, matrix, num_clusters, score, linkage, metric
        )

    def _cluster_fixed(
        self, matrix: np.ndarray, n_clusters: int, linkage: str, metric: str
    ) -> tuple[np.ndarray, float | None]:
        """Cluster with fixed k."""
        model = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage=linkage,
            metric=metric,
        )
        labels = model.fit_predict(matrix)

        # Calculate silhouette score (only if k > 1)
        score = None
        if n_clusters > 1:
            score = silhouette_score(matrix, labels, metric=metric)

        return labels, score

    def _cluster_auto(
        self, matrix: np.ndarray, min_k: int, max_k: int, linkage: str, metric: str
    ) -> tuple[np.ndarray, int, float]:
        """Auto-determine k via silhouette score."""
        best_score = -1.0
        best_labels = None
        best_k = min_k

        max_candidate_k = min(max_k, len(matrix) - 1)
        if max_candidate_k < min_k:
            raise InsufficientDataError(
                f"Need at least {min_k + 1} incidents for auto clustering, got {len(matrix)}"
            )

        for k in range(min_k, max_candidate_k + 1):
            model = AgglomerativeClustering(
                n_clusters=k,
                linkage=linkage,
                metric=metric,
            )
            labels = model.fit_predict(matrix)
            score = silhouette_score(matrix, labels, metric=metric)

            if score > best_score:
                best_score = score
                best_labels = labels
                best_k = k

        if best_labels is None:
            raise ClusteringError("Failed to determine clusters in auto mode")

        return best_labels, best_k, best_score

    def _store_cluster_run(
        self,
        incident_ids: list[int],
        labels: np.ndarray,
        n_clusters: int,
        linkage: str,
        metric: str,
        score: float | None,
    ) -> str:
        """Store cluster run and assignments in database."""
        run_id = str(uuid4())

        # Store cluster run metadata
        params = {
            "linkage": linkage,
            "metric": metric,
            "silhouette_score": score,
        }

        self.db.execute(
            """
            INSERT INTO cluster_runs (id, n_clusters, method, parameters)
            VALUES (?, ?, ?, ?)
        """,
            (run_id, n_clusters, "agglomerative", json.dumps(params)),
        )

        # Group incidents by cluster label
        clusters_map: dict[int, list[int]] = {}
        for incident_id, label in zip(incident_ids, labels):
            label = int(label)
            if label not in clusters_map:
                clusters_map[label] = []
            clusters_map[label].append(incident_id)

        # Store clusters and members
        for cluster_label, member_ids in clusters_map.items():
            # Insert cluster
            cursor = self.db.execute(
                """
                INSERT INTO clusters (run_id, cluster_label, summary, centroid_text)
                VALUES (?, ?, NULL, NULL)
            """,
                (run_id, cluster_label),
            )

            cluster_db_id = cursor.lastrowid

            # Insert cluster members
            for incident_id in member_ids:
                self.db.execute(
                    """
                    INSERT INTO cluster_members (cluster_id, incident_id, distance_to_centroid)
                    VALUES (?, ?, NULL)
                """,
                    (cluster_db_id, incident_id),
                )

        self.db.commit()
        return run_id

    def _build_result(
        self,
        run_id: str,
        incident_ids: list[int],
        labels: np.ndarray,
        matrix: np.ndarray,
        n_clusters: int,
        score: float | None,
        linkage: str,
        metric: str,
    ) -> ClusterRunResult:
        """Build ClusterRunResult from clustering output."""
        # Group incidents by cluster
        clusters_map: dict[int, list[int]] = {}
        for incident_id, label in zip(incident_ids, labels):
            label = int(label)
            if label not in clusters_map:
                clusters_map[label] = []
            clusters_map[label].append(incident_id)

        # Build ClusterResult objects
        clusters = []
        for cluster_id, member_ids in clusters_map.items():
            clusters.append(
                ClusterResult(
                    cluster_id=cluster_id,
                    incident_ids=member_ids,
                    size=len(member_ids),
                    summary=None,
                    centroid_text=None,
                )
            )

        return ClusterRunResult(
            run_id=run_id,
            n_clusters=n_clusters,
            method="agglomerative",
            parameters={
                "linkage": linkage,
                "metric": metric,
                "silhouette_score": score,
            },
            clusters=clusters,
            noise_incident_ids=[],
        )

    def get_run(self, run_id: str) -> ClusterRunResult | None:
        """Retrieve a cluster run by ID."""
        cursor = self.db.execute(
            """
            SELECT id, n_clusters, method, parameters, created_at
            FROM cluster_runs
            WHERE id = ?
        """,
            (run_id,),
        )
        run_row = cursor.fetchone()

        if not run_row:
            return None

        params = json.loads(run_row["parameters"])

        # Get clusters for this run
        cursor = self.db.execute(
            """
            SELECT id, cluster_label, summary, centroid_text
            FROM clusters
            WHERE run_id = ?
            ORDER BY cluster_label
        """,
            (run_id,),
        )
        cluster_rows = cursor.fetchall()

        clusters = []
        for cluster_row in cluster_rows:
            cluster_db_id = cluster_row["id"]

            # Get members
            cursor = self.db.execute(
                """
                SELECT incident_id
                FROM cluster_members
                WHERE cluster_id = ?
                ORDER BY incident_id
            """,
                (cluster_db_id,),
            )
            member_rows = cursor.fetchall()
            member_ids = [r["incident_id"] for r in member_rows]

            clusters.append(
                ClusterResult(
                    cluster_id=cluster_row["cluster_label"],
                    incident_ids=member_ids,
                    size=len(member_ids),
                    summary=cluster_row["summary"],
                    centroid_text=cluster_row["centroid_text"],
                )
            )

        return ClusterRunResult(
            run_id=run_id,
            n_clusters=run_row["n_clusters"],
            method=run_row["method"],
            parameters=params,
            clusters=clusters,
            noise_incident_ids=[],
            created_at=run_row["created_at"],
        )

    def list_runs(self) -> list[ClusterRunResult]:
        """List all cluster runs."""
        cursor = self.db.execute("""
            SELECT id, n_clusters, method, parameters, created_at
            FROM cluster_runs
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = self.get_run(row["id"])
            if result:
                results.append(result)

        return results
