# Phase 2: NLP Clustering & Pattern Detection - COMPLETE

## Implementation Summary

Phase 2 successfully implements the full NLP clustering pipeline using Ollama embeddings and scikit-learn's Agglomerative Clustering.

## Components Implemented

### Backend Services

**1. `services/ollama_client.py`**
- HTTP client for Ollama API
- Batch embedding support (768-dim nomic-embed-text vectors)
- Text generation with optional JSON schema validation
- Model availability checks
- Proper error handling with custom exceptions

**2. `services/embedder.py`**
- Batch processing (32 incidents at a time)
- Automatic detection of unembed incidents
- Stores embeddings as float32 BLOBs in SQLite
- Text preparation: `"{title}. {description[:500]}"`

**3. `services/clusterer.py`** (CRITICAL IMPLEMENTATION)
- **Ward+cosine guard check** (prevents sklearn crash)
- Agglomerative clustering with:
  - `linkage='average'` (compatible with cosine)
  - `metric='cosine'` (semantic similarity)
- Auto k-selection via silhouette score
- Fixed k-clustering support
- Stores results with UUID identifiers
- Full cluster run retrieval and listing

**4. `services/summarizer.py`**
- LLM-based cluster naming using llama3.2
- JSON schema validation for structured output
- Fallback handling when LLM fails
- Generates 3-6 word names + 1-2 sentence summaries

**5. `services/metrics.py`**
- MTTR calculation (mean time to resolution)
- Percentile calculations (p50, p90)
- Severity breakdown
- MTTR by severity
- Month-over-month grouping

### API Endpoints

**`POST /clusters/run`**
- Pipeline: Embed → Cluster → Name → Store
- Request: `{ n_clusters?: number | null }`
- Response: `ClusterResponse` with full run details
- Auto-embeds new incidents before clustering
- Validates Ollama availability

**`GET /clusters`**
- Lists all cluster runs (newest first)
- Returns: `ClusterRunResult[]`

**`GET /clusters/{run_id}`**
- Get specific run details
- Includes cluster names and incident IDs

### Database Migrations

**`003_fix_cluster_runs_id.sql`**
- Changed `cluster_runs.id` from INTEGER to TEXT (UUID support)
- Updated foreign keys in clusters table

**`004_add_incident_fields.sql`**
- Added `assignee`, `jira_project`, `status` fields for metrics

### Frontend Components

**1. `src/components/ClusterView.tsx`**
- Expandable cluster card
- Shows cluster name (bold, large)
- Shows summary (italic)
- Badge with incident count
- Expands to show incident titles with severity/date

**2. `src/pages/ClustersPage.tsx`**
- Run clustering controls
- Optional cluster count input (auto-detect if empty)
- Loading/error states
- Success feedback with silhouette score
- Latest run display with sorted clusters (largest first)

**3. `src/api/hooks.ts`**
- `useClusterRuns()` - GET /clusters
- `useRunClustering()` - POST /clusters/run mutation
- Auto-invalidates query cache on success

**4. `src/types/index.ts`**
- Added `ClusterResult`, `ClusterRunResult`, `ClusterRequest`, `ClusterResponse`

## Test Coverage

**`test_phase2.py`** - All 11 tests passing:

1. **Ward+Cosine Guard Tests**
   - ✅ Ward+cosine raises ValueError
   - ✅ Average+cosine succeeds
   - ✅ Complete+cosine succeeds
   - ✅ Ward+euclidean succeeds

2. **Auto K-Selection Tests**
   - ✅ Auto k-selection finds optimal clusters
   - ✅ Silhouette score in [-1, 1] range

3. **Error Handling Tests**
   - ✅ InsufficientDataError when < 2 incidents

4. **Summarizer Tests**
   - ✅ LLM cluster naming with JSON schema
   - ✅ Fallback when LLM fails

5. **Embedder Tests**
   - ✅ Batch embedding of incidents
   - ✅ Skips already-embedded incidents

## Algorithm Details

### Clustering Configuration
```python
AgglomerativeClustering(
    n_clusters=None,           # When using auto mode
    distance_threshold=None,   # Not used (prefer n_clusters)
    linkage='average',         # REQUIRED with cosine
    metric='cosine'            # Semantic similarity
)
```

### Critical Guards
```python
if linkage == "ward" and metric == "cosine":
    raise ValueError(
        "Ward linkage is incompatible with cosine distance. "
        "Use 'average' or 'complete' linkage with cosine metric."
    )
```

### Auto K-Selection
- Tests k ∈ [min_clusters, max_clusters]
- Selects k with highest silhouette score
- Silhouette score measures cluster separation quality
- Range: [-1, 1], higher is better

## Verification Checklist

✅ Ward+cosine guard prevents crashes
✅ Average/complete+cosine work correctly
✅ Auto k-selection via silhouette score
✅ Silhouette score in valid range [-1, 1]
✅ LLM cluster naming with JSON schema
✅ Fallback handling for LLM failures
✅ Batch embedding (32/batch)
✅ Skip already-embedded incidents
✅ API endpoints functional
✅ Frontend displays clusters
✅ All 11 tests passing

## Next Steps (Phase 3)

Phase 3 will add visualization:
- Interactive cluster visualization (force-directed graph or t-SNE)
- Metrics dashboard
- Trend analysis charts

## Notes

- Ollama must be running on localhost:11434
- Required models: `nomic-embed-text`, `llama3.2`
- Pull with: `ollama pull nomic-embed-text && ollama pull llama3.2`
- Clustering runs in ~2-5 seconds for 50 incidents
- LLM naming adds ~10-30 seconds depending on cluster count
