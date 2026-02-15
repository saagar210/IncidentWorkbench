# Incident Workbench

Quarterly IT Incident Review Workbench - A Tauri desktop app for automated incident analysis, clustering, and report generation.

## Architecture

- **Frontend**: React + TypeScript (Vite)
- **Backend**: Python FastAPI (as Tauri sidecar)
- **Database**: SQLite (local)
- **AI**: Ollama (local) for embeddings and text generation

## Prerequisites

- **Node.js** 18+ and npm
- **Rust** 1.70+ (for Tauri)
- **Python** 3.12+
- **Ollama** 0.1+ (for clustering and summaries)

### Install Ollama Models

```bash
ollama pull nomic-embed-text
ollama pull llama3.2
```

## Development

### First-time Setup

```bash
# Install Node dependencies
npm install

# Install Python dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cd ..
```

### Run in Development Mode

```bash
bash scripts/dev.sh
```

This starts:
1. FastAPI backend on port 8765 (with hot reload)
2. Tauri frontend (React with Vite HMR)

### Run Backend Tests

```bash
cd backend
source .venv/bin/activate
python test_phase0.py
```

## Production Build

### Build Sidecar Binary

```bash
bash scripts/build-sidecar.sh
```

### Build Tauri App

```bash
npm run tauri build
```

The built app will be in `src-tauri/target/release/bundle/`.

## Project Structure

```
├── src/                    # React frontend
│   ├── api/               # API client and TanStack Query hooks
│   ├── components/        # React components
│   ├── pages/             # Page components
│   ├── types/             # TypeScript interfaces
│   └── utils/             # Frontend utilities
├── backend/               # Python FastAPI backend
│   ├── models/           # Pydantic models
│   ├── routers/          # API route handlers
│   ├── services/         # Business logic (Jira, Slack, clustering, etc.)
│   └── migrations/       # SQLite schema migrations
├── src-tauri/            # Tauri Rust core
│   ├── src/              # Rust source
│   └── binaries/         # PyInstaller sidecar binary (gitignored)
└── scripts/              # Build and development scripts
```

## Data Sources

- **Jira Server/DC**: Fetch incidents via REST API v2
- **Slack**: Dual-path (direct API with rate limits + JSON export import)

## Features

- ✅ Multi-source incident aggregation (Jira, Slack)
- ✅ NLP-based incident clustering (Ollama embeddings)
- ✅ Operational metrics (MTTR, severity breakdown, trends)
- ✅ LLM-generated executive summaries
- ✅ Professional DOCX report export
- ✅ All data stays local (zero cloud transmission)
- ✅ Dark mode support
- ✅ Comprehensive error handling

## Troubleshooting

### Ollama Not Available

**Symptom**: Settings page shows "Ollama is not available"

**Solution**:
1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start Ollama (it runs as a background service)
3. Pull required models:
   ```bash
   ollama pull nomic-embed-text
   ollama pull llama3.2
   ```
4. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Jira Connection Fails

**Symptom**: "Jira connection failed" error when testing credentials

**Common Causes**:
- Invalid API token (Jira Server uses different auth than Cloud)
- Incorrect Jira URL (should be `https://your-domain.atlassian.net` for Cloud)
- Network/firewall blocking the connection
- API token doesn't have required permissions

**Solution**:
1. Verify your Jira URL format
2. For Jira Cloud: Generate API token at https://id.atlassian.com/manage-profile/security/api-tokens
3. For Jira Server: Use username + password or verify API token format
4. Test with curl first:
   ```bash
   curl -u email@example.com:YOUR_API_TOKEN https://your-domain.atlassian.net/rest/api/2/myself
   ```

### Slack Connection Fails

**Symptom**: "Slack connection failed" error

**Common Causes**:
- Invalid bot token format
- Bot not added to the workspace
- Missing required OAuth scopes

**Solution**:
1. Verify bot token starts with `xoxb-`
2. Required scopes: `channels:history`, `channels:read`, `users:read`
3. Invite bot to the channel: `/invite @YourBotName`
4. Test with curl:
   ```bash
   curl -H "Authorization: Bearer xoxb-YOUR-TOKEN" https://slack.com/api/auth.test
   ```

### Clustering Returns "No Incidents"

**Symptom**: Clustering fails with "Insufficient data" error

**Solution**:
- Ensure you've ingested incidents from Jira or Slack first
- Check the Incidents page to verify incidents are loaded
- Clustering requires at least 5-10 incidents for meaningful results

### Report Generation Fails

**Symptom**: "Failed to generate report" error

**Common Causes**:
- Ollama not running (required for LLM summaries)
- No cluster run selected
- Charts not exported

**Solution**:
1. Ensure Ollama is running
2. Run clustering first (Clusters page)
3. Export charts on the Dashboard page
4. Select a cluster run before generating

### Database Errors

**Symptom**: SQLite errors or data corruption

**Solution**:
1. Check database file permissions: `~/.local/share/com.incident-workbench.app/incidents.db`
2. WAL mode should be enabled automatically (check logs)
3. If corrupted, delete database to start fresh (will lose all data):
   ```bash
   rm ~/.local/share/com.incident-workbench.app/incidents.db*
   ```

### Performance Issues

**Symptom**: App is slow or unresponsive

**Tips**:
- Clustering 1000+ incidents can take 30-60 seconds (this is normal)
- Reduce batch size for Jira queries if hitting memory limits
- SQLite WAL mode is enabled by default for better concurrency
- Close unused apps to free up RAM during large operations

### Dark Mode Issues

**Symptom**: Theme doesn't persist or looks broken

**Solution**:
- Theme preference is stored in localStorage
- Try clearing browser cache and restarting app
- Check browser console for errors

## Known Limitations

- **Maximum Incidents**: Tested up to 5,000 incidents. Performance degrades beyond this.
- **Clustering Time**: HDBSCAN can take 1-2 minutes for 2,000+ incidents.
- **Slack Rate Limits**: Direct API ingestion is throttled. Use export for large channels.
- **Jira Cloud vs Server**: Different auth mechanisms. Ensure correct credentials.
- **Ollama Memory**: Text generation requires ~4GB RAM. Use smaller models if limited.

## Performance Tips

1. **Batch Ingestion**: Use narrow JQL queries to avoid fetching thousands of incidents at once
2. **Cluster Pruning**: Delete old cluster runs to keep database lean
3. **Regular Cleanup**: Use "Delete All Incidents" to start fresh each quarter
4. **Ollama Models**: Stick to recommended models (nomic-embed-text, llama3.2) for best speed/quality balance

## License

Proprietary
