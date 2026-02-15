"""Clustering router."""

from fastapi import APIRouter, HTTPException

from database import db
from exceptions import ClusteringError, InsufficientDataError, OllamaUnavailableError
from models.api import ClusterRequest, ClusterResponse
from models.cluster import ClusterRunResult
from services.clusterer import IncidentClusterer
from services.embedder import IncidentEmbedder
from services.ollama_client import OllamaClient
from services.summarizer import ClusterSummarizer

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.post("/run")
async def run_clustering(request: ClusterRequest) -> ClusterResponse:
    """
    Run clustering algorithm on all incidents.

    Pipeline:
    1. Embed any incidents without embeddings
    2. Run clustering algorithm
    3. Generate cluster names/summaries
    4. Return results
    """
    conn = db.get_connection()
    ollama = OllamaClient()

    try:
        # Step 1: Check Ollama availability
        if not await ollama.is_available():
            raise HTTPException(
                status_code=503,
                detail="Ollama service is not available. Please ensure it's running."
            )

        # Step 2: Embed any new incidents
        embedder = IncidentEmbedder(conn, ollama)
        embedded_count = await embedder.embed_all_incidents()

        # Step 3: Run clustering
        clusterer = IncidentClusterer(conn)

        # Use request parameters with defaults
        linkage = "average"  # Always use average for cosine
        metric = "cosine"

        try:
            result = clusterer.run(
                num_clusters=request.n_clusters,
                min_clusters=2,
                max_clusters=15,
                linkage=linkage,
                metric=metric,
            )
        except ValueError as e:
            # Ward+cosine guard triggered
            raise HTTPException(status_code=400, detail=str(e))
        except InsufficientDataError as e:
            raise HTTPException(status_code=400, detail=e.message)
        except ClusteringError as e:
            raise HTTPException(status_code=500, detail=e.message)

        # Step 4: Generate cluster names
        summarizer = ClusterSummarizer(ollama, conn)
        await summarizer.name_all_clusters(result.run_id)

        # Reload result to get updated names
        result = clusterer.get_run(result.run_id)

        return ClusterResponse(run=result)

    except OllamaUnavailableError as e:
        raise HTTPException(status_code=503, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")
    finally:
        conn.close()
        await ollama.close()


@router.get("")
async def list_cluster_runs() -> list[ClusterRunResult]:
    """List all clustering runs."""
    conn = db.get_connection()
    try:
        clusterer = IncidentClusterer(conn)
        return clusterer.list_runs()
    finally:
        conn.close()


@router.get("/{run_id}")
async def get_cluster_run(run_id: str) -> ClusterResponse:
    """Get details of a specific clustering run."""
    conn = db.get_connection()
    try:
        clusterer = IncidentClusterer(conn)
        result = clusterer.get_run(run_id)

        if not result:
            raise HTTPException(status_code=404, detail="Cluster run not found")

        return ClusterResponse(run=result)
    finally:
        conn.close()
