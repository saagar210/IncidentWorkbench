-- Update reports table with new columns for Phase 4

-- Drop old reports table and recreate with new schema
DROP TABLE IF EXISTS reports;

CREATE TABLE reports (
    id TEXT PRIMARY KEY,
    cluster_run_id TEXT NOT NULL,
    title TEXT NOT NULL,
    executive_summary TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    docx_path TEXT,
    FOREIGN KEY (cluster_run_id) REFERENCES cluster_runs(id) ON DELETE CASCADE
);
