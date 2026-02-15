/**
 * Clusters page - NLP-based incident clustering
 */

import { useState } from "react";
import { useClusterRuns, useRunClustering, getErrorMessage } from "../api/hooks";
import { ClusterView } from "../components/ClusterView";
import { useToastContext } from "../contexts/ToastContext";

export function ClustersPage() {
  const toast = useToastContext();
  const [numClusters, setNumClusters] = useState<string>("");
  const [isRunning, setIsRunning] = useState(false);

  const { data: clusterRuns, isLoading, error } = useClusterRuns();
  const runClusteringMutation = useRunClustering();

  const handleRunClustering = async () => {
    setIsRunning(true);
    try {
      const result = await runClusteringMutation.mutateAsync({
        n_clusters: numClusters ? parseInt(numClusters, 10) : null,
      });
      const clusterCount = result.run.num_clusters ?? result.run.n_clusters;
      const incidentCount = result.run.num_incidents ?? result.run.clusters.reduce((sum, c) => sum + c.size, 0);
      toast.success(
        `Clustering complete! Generated ${clusterCount} clusters from ${incidentCount} incidents`
      );
    } catch (err) {
      console.error("Clustering failed:", err);
      toast.error(`Clustering failed: ${getErrorMessage(err)}`);
    } finally {
      setIsRunning(false);
    }
  };

  const latestRun = clusterRuns?.[0];

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: "bold", marginBottom: "0.5rem" }}>
          Incident Clustering
        </h1>
        <p style={{ color: "#666" }}>
          Automatically group related incidents using NLP embeddings
        </p>
      </div>

      {/* Run clustering controls */}
      <div
        style={{
          backgroundColor: "#f9fafb",
          border: "1px solid #e5e7eb",
          borderRadius: "0.5rem",
          padding: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <h2 style={{ fontSize: "1.25rem", fontWeight: "600", marginBottom: "1rem" }}>
          Run Clustering
        </h2>
        <div style={{ display: "flex", gap: "1rem", alignItems: "end" }}>
          <div style={{ flex: 1 }}>
            <label
              htmlFor="numClusters"
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: "500",
                marginBottom: "0.5rem",
              }}
            >
              Number of Clusters (optional)
            </label>
            <input
              id="numClusters"
              type="number"
              min="2"
              max="15"
              value={numClusters}
              onChange={(e) => setNumClusters(e.target.value)}
              placeholder="Auto-detect optimal clusters"
              style={{
                width: "100%",
                padding: "0.5rem",
                border: "1px solid #d1d5db",
                borderRadius: "0.375rem",
              }}
              disabled={isRunning}
            />
            <p style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.25rem" }}>
              Leave empty for automatic detection using silhouette score
            </p>
          </div>
          <button
            onClick={handleRunClustering}
            disabled={isRunning}
            style={{
              padding: "0.5rem 1.5rem",
              backgroundColor: isRunning ? "#9ca3af" : "#3b82f6",
              color: "white",
              border: "none",
              borderRadius: "0.375rem",
              fontWeight: "500",
              cursor: isRunning ? "not-allowed" : "pointer",
            }}
          >
            {isRunning ? "Running..." : "Run Clustering"}
          </button>
        </div>

        {runClusteringMutation.isError && (
          <div
            style={{
              marginTop: "1rem",
              padding: "0.75rem",
              backgroundColor: "#fef2f2",
              border: "1px solid #fecaca",
              borderRadius: "0.375rem",
              color: "#991b1b",
            }}
          >
            Error: {(runClusteringMutation.error as any)?.message || "Clustering failed"}
          </div>
        )}

        {runClusteringMutation.isSuccess && (
          <div
            style={{
              marginTop: "1rem",
              padding: "0.75rem",
              backgroundColor: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: "0.375rem",
              color: "#166534",
            }}
          >
            Clustering complete! Found {runClusteringMutation.data.run.n_clusters} clusters.
            {runClusteringMutation.data.run.parameters.silhouette_score && (
              <span>
                {" "}
                (Silhouette score:{" "}
                {runClusteringMutation.data.run.parameters.silhouette_score.toFixed(3)})
              </span>
            )}
          </div>
        )}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div style={{ textAlign: "center", padding: "2rem" }}>
          <p style={{ color: "#6b7280" }}>Loading cluster runs...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div
          style={{
            padding: "1rem",
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "0.5rem",
            color: "#991b1b",
          }}
        >
          Error loading clusters: {(error as any)?.message}
        </div>
      )}

      {/* Latest cluster run results */}
      {latestRun && (
        <div>
          <div style={{ marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: "600", marginBottom: "0.5rem" }}>
              Latest Clustering Results
            </h2>
            <p style={{ fontSize: "0.875rem", color: "#6b7280" }}>
              Run on {new Date(latestRun.created_at).toLocaleString()} •{" "}
              {latestRun.n_clusters} clusters •{" "}
              {latestRun.method} clustering
              {latestRun.parameters.silhouette_score && (
                <span>
                  {" "}
                  • Silhouette: {latestRun.parameters.silhouette_score.toFixed(3)}
                </span>
              )}
            </p>
          </div>

          {/* Cluster cards */}
          <div>
            {latestRun.clusters
              .sort((a, b) => b.size - a.size) // Sort by size descending
              .map((cluster) => (
                <ClusterView key={cluster.cluster_id} cluster={cluster} runId={latestRun.run_id} />
              ))}
          </div>
        </div>
      )}

      {/* No runs yet */}
      {!isLoading && !latestRun && (
        <div
          style={{
            textAlign: "center",
            padding: "3rem",
            backgroundColor: "#f9fafb",
            border: "1px solid #e5e7eb",
            borderRadius: "0.5rem",
          }}
        >
          <p style={{ fontSize: "1.125rem", color: "#6b7280" }}>
            No clustering runs yet. Run your first clustering above!
          </p>
        </div>
      )}
    </div>
  );
}
