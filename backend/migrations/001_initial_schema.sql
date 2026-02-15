-- Initial database schema for Incident Workbench

-- Incidents table
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL,
    source TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    occurred_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    raw_data TEXT NOT NULL,  -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(external_id, source)
);

-- Embeddings table (one-to-one with incidents)
CREATE TABLE IF NOT EXISTS embeddings (
    incident_id INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL,  -- Serialized numpy array
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
);

-- Cluster runs table
CREATE TABLE IF NOT EXISTS cluster_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    n_clusters INTEGER NOT NULL,
    method TEXT NOT NULL,
    parameters TEXT NOT NULL,  -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clusters table
CREATE TABLE IF NOT EXISTS clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    cluster_label INTEGER NOT NULL,  -- -1 for noise
    summary TEXT,
    centroid_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES cluster_runs(id) ON DELETE CASCADE,
    UNIQUE(run_id, cluster_label)
);

-- Cluster members table (many-to-many)
CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id INTEGER NOT NULL,
    incident_id INTEGER NOT NULL,
    distance_to_centroid REAL,
    PRIMARY KEY (cluster_id, incident_id),
    FOREIGN KEY (cluster_id) REFERENCES clusters(id) ON DELETE CASCADE,
    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_run_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    metrics TEXT NOT NULL,  -- JSON blob
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cluster_run_id) REFERENCES cluster_runs(id) ON DELETE CASCADE
);
