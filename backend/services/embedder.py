"""Incident embedding service."""

import sqlite3
import numpy as np

from services.ollama_client import OllamaClient


BATCH_SIZE = 32


class IncidentEmbedder:
    """Service for embedding incidents using Ollama."""

    def __init__(self, db_conn: sqlite3.Connection, ollama: OllamaClient) -> None:
        self.db = db_conn
        self.ollama = ollama

    async def embed_all_incidents(self, model: str = "nomic-embed-text") -> int:
        """
        Embed all incidents that don't yet have embeddings.

        Returns:
            Number of incidents embedded.
        """
        # Find incidents without embeddings
        cursor = self.db.execute("""
            SELECT i.id, i.title, i.description
            FROM incidents i
            LEFT JOIN embeddings e ON i.id = e.incident_id
            WHERE e.incident_id IS NULL
            ORDER BY i.id
        """)
        rows = cursor.fetchall()

        if not rows:
            return 0

        # Prepare texts for embedding (title + truncated description)
        incident_ids = []
        texts = []
        for row in rows:
            incident_id = row["id"]
            title = row["title"] or ""
            description = row["description"] or ""

            # Concatenate: "title. description[:500]"
            text = f"{title}. {description[:500]}"
            incident_ids.append(incident_id)
            texts.append(text)

        # Batch embed
        count = 0
        for i in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[i:i + BATCH_SIZE]
            batch_ids = incident_ids[i:i + BATCH_SIZE]

            # Get embeddings from Ollama
            embeddings = await self.ollama.embed_batch(batch_texts, model=model)

            # Store embeddings
            for incident_id, embedding in zip(batch_ids, embeddings):
                # Convert to numpy float32 and store as BLOB
                vector_blob = np.array(embedding, dtype=np.float32).tobytes()

                self.db.execute("""
                    INSERT OR REPLACE INTO embeddings (incident_id, embedding, model)
                    VALUES (?, ?, ?)
                """, (incident_id, vector_blob, model))
                count += 1

        self.db.commit()
        return count

    def get_embedding_count(self) -> int:
        """Get count of incidents with embeddings."""
        cursor = self.db.execute("SELECT COUNT(*) as cnt FROM embeddings")
        return cursor.fetchone()["cnt"]

    def clear_embeddings(self) -> None:
        """Delete all embeddings (for testing/reprocessing)."""
        self.db.execute("DELETE FROM embeddings")
        self.db.commit()
