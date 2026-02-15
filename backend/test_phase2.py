"""Phase 2 tests: NLP Clustering & Pattern Detection."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from sklearn.cluster import AgglomerativeClustering

from database import Database
from exceptions import InsufficientDataError
from services.clusterer import IncidentClusterer
from services.embedder import IncidentEmbedder
from services.ollama_client import OllamaClient
from services.summarizer import ClusterSummarizer


class TestWardCosineGuard:
    """Test that Ward+cosine combination is properly guarded."""

    def test_ward_cosine_raises_error(self, test_db):
        """Ward linkage with cosine metric must raise ValueError."""
        clusterer = IncidentClusterer(test_db)

        with pytest.raises(ValueError) as exc_info:
            clusterer.run(num_clusters=2, linkage="ward", metric="cosine")

        assert "Ward linkage is incompatible with cosine" in str(exc_info.value)

    def test_average_cosine_succeeds(self, test_db_with_embeddings):
        """Average linkage with cosine metric should work."""
        clusterer = IncidentClusterer(test_db_with_embeddings)

        # Should not raise
        result = clusterer.run(num_clusters=2, linkage="average", metric="cosine")
        assert result is not None
        assert result.n_clusters == 2

    def test_complete_cosine_succeeds(self, test_db_with_embeddings):
        """Complete linkage with cosine metric should work."""
        clusterer = IncidentClusterer(test_db_with_embeddings)

        # Should not raise
        result = clusterer.run(num_clusters=2, linkage="complete", metric="cosine")
        assert result is not None
        assert result.n_clusters == 2

    def test_ward_euclidean_succeeds(self, test_db_with_embeddings):
        """Ward linkage with euclidean metric should work."""
        clusterer = IncidentClusterer(test_db_with_embeddings)

        # Should not raise
        result = clusterer.run(num_clusters=2, linkage="ward", metric="euclidean")
        assert result is not None
        assert result.n_clusters == 2


class TestClusterAutoSelection:
    """Test automatic k selection via silhouette score."""

    def test_auto_k_selection(self, test_db_with_embeddings):
        """Auto k-selection should find optimal cluster count."""
        clusterer = IncidentClusterer(test_db_with_embeddings)

        result = clusterer.run(
            num_clusters=None,  # Auto mode
            min_clusters=2,
            max_clusters=5,
            linkage="average",
            metric="cosine",
        )

        assert result.n_clusters >= 2
        assert result.n_clusters <= 5
        assert result.parameters["silhouette_score"] is not None

    def test_silhouette_score_range(self, test_db_with_embeddings):
        """Silhouette score should be in [-1, 1]."""
        clusterer = IncidentClusterer(test_db_with_embeddings)

        result = clusterer.run(num_clusters=3, linkage="average", metric="cosine")

        score = result.parameters["silhouette_score"]
        assert score is not None
        assert -1.0 <= score <= 1.0


class TestInsufficientData:
    """Test insufficient data handling."""

    def test_insufficient_data_error(self, test_db):
        """Should raise error when not enough incidents."""
        clusterer = IncidentClusterer(test_db)

        with pytest.raises(InsufficientDataError) as exc_info:
            clusterer.run(num_clusters=2, min_clusters=2)

        assert "at least 2 incidents" in str(exc_info.value)

    def test_auto_mode_requires_three_incidents(self, test_db):
        """Auto mode should require at least 3 incidents for silhouette scoring."""
        # Add exactly two incidents with embeddings.
        for i in range(2):
            test_db.execute(
                """
                INSERT INTO incidents (external_id, source, severity, title, description, occurred_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"AUTO-{i}",
                    "jira",
                    "SEV2",
                    f"Auto incident {i}",
                    "Description",
                    "2024-01-01T00:00:00Z",
                    "{}",
                ),
            )
            incident_id = test_db.execute("SELECT last_insert_rowid()").fetchone()[0]
            vector = np.random.randn(768).astype(np.float32).tobytes()
            test_db.execute(
                """
                INSERT INTO embeddings (incident_id, embedding, model)
                VALUES (?, ?, ?)
                """,
                (incident_id, vector, "nomic-embed-text"),
            )
        test_db.commit()

        clusterer = IncidentClusterer(test_db)
        with pytest.raises(InsufficientDataError) as exc_info:
            clusterer.run(num_clusters=None, min_clusters=2, max_clusters=15)

        assert "at least 3 incidents" in str(exc_info.value)


class TestClusterSummarizer:
    """Test LLM-based cluster naming."""

    @pytest.mark.asyncio
    async def test_cluster_naming(self, test_db):
        """Test cluster name generation."""
        mock_ollama = MagicMock(spec=OllamaClient)
        mock_ollama.generate.return_value = '{"name": "Database Connection Issues", "summary": "Incidents related to DB timeouts."}'

        summarizer = ClusterSummarizer(mock_ollama, test_db)
        name, summary = await summarizer.name_cluster([
            "Database timeout in prod",
            "Connection pool exhausted",
            "Slow query causing timeout",
        ])

        assert name == "Database Connection Issues"
        assert "DB timeouts" in summary

    @pytest.mark.asyncio
    async def test_cluster_naming_fallback(self, test_db):
        """Test fallback when LLM fails."""
        mock_ollama = MagicMock(spec=OllamaClient)
        mock_ollama.generate.return_value = "invalid json"

        summarizer = ClusterSummarizer(mock_ollama, test_db)
        name, summary = await summarizer.name_cluster(["Incident 1", "Incident 2"])

        assert "2 incidents" in name
        assert "Auto-naming failed" in summary


class TestEmbedder:
    """Test incident embedding."""

    @pytest.mark.asyncio
    async def test_batch_embedding(self, test_db):
        """Test batch embedding of incidents."""
        # Add test incidents
        test_db.execute("""
            INSERT INTO incidents (external_id, source, severity, title, description, occurred_at, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("INC-1", "jira", "SEV2", "Test incident", "Description", "2024-01-01T00:00:00Z", "{}"))
        test_db.commit()

        mock_ollama = MagicMock(spec=OllamaClient)
        mock_ollama.embed_batch.return_value = [
            [0.1] * 768,  # Mock 768-dim embedding
        ]

        embedder = IncidentEmbedder(test_db, mock_ollama)
        count = await embedder.embed_all_incidents()

        assert count == 1
        assert embedder.get_embedding_count() == 1

    @pytest.mark.asyncio
    async def test_skip_already_embedded(self, test_db):
        """Test that already-embedded incidents are skipped."""
        # Add incident and embedding
        test_db.execute("""
            INSERT INTO incidents (external_id, source, severity, title, description, occurred_at, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("INC-1", "jira", "SEV2", "Test", "Desc", "2024-01-01T00:00:00Z", "{}"))
        incident_id = test_db.execute("SELECT last_insert_rowid()").fetchone()[0]

        vector = np.array([0.1] * 768, dtype=np.float32).tobytes()
        test_db.execute("""
            INSERT INTO embeddings (incident_id, embedding, model)
            VALUES (?, ?, ?)
        """, (incident_id, vector, "nomic-embed-text"))
        test_db.commit()

        mock_ollama = MagicMock(spec=OllamaClient)
        embedder = IncidentEmbedder(test_db, mock_ollama)
        count = await embedder.embed_all_incidents()

        assert count == 0
        mock_ollama.embed_batch.assert_not_called()


# Fixtures

@pytest.fixture
def test_db():
    """Create temporary test database."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"

    db_instance = Database(db_path)
    db_instance.run_migrations()

    conn = db_instance.get_connection()
    yield conn
    conn.close()


@pytest.fixture
def test_db_with_embeddings(test_db):
    """Test database with incidents and embeddings."""
    # Add 10 test incidents
    for i in range(10):
        test_db.execute("""
            INSERT INTO incidents (external_id, source, severity, title, description, occurred_at, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (f"INC-{i}", "jira", "SEV2", f"Incident {i}", f"Description {i}", "2024-01-01T00:00:00Z", "{}"))

        incident_id = test_db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Create semi-random embeddings
        np.random.seed(i)
        vector = np.random.randn(768).astype(np.float32).tobytes()

        test_db.execute("""
            INSERT INTO embeddings (incident_id, embedding, model)
            VALUES (?, ?, ?)
        """, (incident_id, vector, "nomic-embed-text"))

    test_db.commit()
    return test_db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
