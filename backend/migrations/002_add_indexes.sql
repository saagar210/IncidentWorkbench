-- Performance indexes for Incident Workbench

-- Incidents indexes
CREATE INDEX IF NOT EXISTS idx_incidents_source ON incidents(source);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_occurred_at ON incidents(occurred_at);
CREATE INDEX IF NOT EXISTS idx_incidents_external_id ON incidents(external_id);

-- Cluster runs indexes
CREATE INDEX IF NOT EXISTS idx_cluster_runs_created_at ON cluster_runs(created_at);

-- Clusters indexes
CREATE INDEX IF NOT EXISTS idx_clusters_run_id ON clusters(run_id);
CREATE INDEX IF NOT EXISTS idx_clusters_label ON clusters(cluster_label);

-- Cluster members indexes
CREATE INDEX IF NOT EXISTS idx_cluster_members_incident ON cluster_members(incident_id);
CREATE INDEX IF NOT EXISTS idx_cluster_members_cluster ON cluster_members(cluster_id);

-- Reports indexes
CREATE INDEX IF NOT EXISTS idx_reports_run_id ON reports(cluster_run_id);
CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON reports(generated_at);
