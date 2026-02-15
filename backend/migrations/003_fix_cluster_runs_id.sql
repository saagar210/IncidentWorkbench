-- Fix cluster_runs to support UUID strings as IDs

-- Create new table with TEXT id
CREATE TABLE IF NOT EXISTS cluster_runs_new (
    id TEXT PRIMARY KEY,
    n_clusters INTEGER NOT NULL,
    method TEXT NOT NULL,
    parameters TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Copy existing data if any
INSERT INTO cluster_runs_new (id, n_clusters, method, parameters, created_at)
SELECT CAST(id AS TEXT), n_clusters, method, parameters, created_at
FROM cluster_runs;

-- Drop old table
DROP TABLE cluster_runs;

-- Rename new table
ALTER TABLE cluster_runs_new RENAME TO cluster_runs;

-- Update clusters table to use TEXT foreign key
CREATE TABLE clusters_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    cluster_label INTEGER NOT NULL,
    summary TEXT,
    centroid_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES cluster_runs(id) ON DELETE CASCADE,
    UNIQUE(run_id, cluster_label)
);

-- Copy existing data
INSERT INTO clusters_new (id, run_id, cluster_label, summary, centroid_text, created_at)
SELECT id, CAST(run_id AS TEXT), cluster_label, summary, centroid_text, created_at
FROM clusters;

-- Drop old table
DROP TABLE clusters;

-- Rename new table
ALTER TABLE clusters_new RENAME TO clusters;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_clusters_run_id ON clusters(run_id);
CREATE INDEX IF NOT EXISTS idx_clusters_label ON clusters(cluster_label);
