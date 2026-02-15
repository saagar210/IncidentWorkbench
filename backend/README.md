# Incident Workbench Backend

FastAPI backend for the Incident Workbench application.

## Phase 0 Status ✅

Phase 0 is **complete** and fully functional:

- ✅ Application boots successfully
- ✅ Database migrations run automatically
- ✅ Health check endpoint working
- ✅ Jira connection testing working
- ✅ Slack connection testing working
- ✅ All router stubs in place
- ✅ Exception handling configured
- ✅ CORS middleware configured

## Setup

```bash
# Install dependencies
cd backend
pip install -e .

# Run the application
python main.py
```

The server will:
1. Find a free port on `127.0.0.1`
2. Print the port number to stdout (first line)
3. Run database migrations automatically
4. Start the FastAPI server

## Testing

```bash
# Run Phase 0 smoke tests
python test_phase0.py
```

## Database

SQLite database located at: `~/.incident-workbench/incidents.db`

Schema includes:
- `incidents` - Core incident data
- `embeddings` - Text embeddings for clustering
- `cluster_runs` - Clustering run metadata
- `clusters` - Individual clusters
- `cluster_members` - Many-to-many relationship
- `reports` - Generated report metadata
- `_migrations` - Migration tracking

## API Endpoints

### Health
- `GET /health` - System health check

### Settings
- `POST /settings/test-jira` - Test Jira connection
- `POST /settings/test-slack` - Test Slack connection

### Ingestion (Stubs)
- `POST /ingest/jira` - Ingest from Jira
- `POST /ingest/slack` - Ingest from Slack
- `POST /ingest/slack-export` - Ingest from Slack export

### Incidents (Stubs)
- `GET /incidents` - List incidents
- `GET /incidents/{id}` - Get incident
- `DELETE /incidents` - Delete all incidents

### Clustering (Stubs)
- `POST /clusters/run` - Run clustering
- `GET /clusters` - List cluster runs
- `GET /clusters/{run_id}` - Get cluster run

### Reports (Stubs)
- `POST /reports/generate` - Generate report
- `GET /reports` - List reports
- `GET /reports/{id}/download` - Download report

## Configuration

Environment variables (prefix `WORKBENCH_`):
- `WORKBENCH_DB_PATH` - Database path (default: `~/.incident-workbench/incidents.db`)
- `WORKBENCH_OLLAMA_URL` - Ollama URL (default: `http://127.0.0.1:11434`)

## Next Steps

Phase 1 implementation will add:
- Jira ingestion functionality
- Slack ingestion functionality
- Embedding generation
- Incident storage and retrieval
