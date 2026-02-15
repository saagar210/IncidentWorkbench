/**
 * Table component for displaying incidents
 */

import { useState } from "react";
import type { Incident } from "../types";

interface IncidentTableProps {
  incidents: Incident[];
  loading?: boolean;
}

export function IncidentTable({ incidents, loading }: IncidentTableProps) {
  const [sortBy, setSortBy] = useState<"occurred_at" | "resolved_at">("occurred_at");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  if (loading) {
    return <div className="loading">Loading incidents...</div>;
  }

  if (incidents.length === 0) {
    return <div className="empty-state">No incidents found</div>;
  }

  // Sort incidents
  const sortedIncidents = [...incidents].sort((a, b) => {
    const aDate = new Date(sortBy === "occurred_at" ? a.occurred_at : a.resolved_at || "");
    const bDate = new Date(sortBy === "occurred_at" ? b.occurred_at : b.resolved_at || "");

    if (sortDirection === "asc") {
      return aDate.getTime() - bDate.getTime();
    }
    return bDate.getTime() - aDate.getTime();
  });

  const handleSort = (column: "occurred_at" | "resolved_at") => {
    if (sortBy === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortDirection("desc");
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "N/A";
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const calculateDuration = (incident: Incident) => {
    if (!incident.resolved_at) return "Ongoing";

    const occurred = new Date(incident.occurred_at);
    const resolved = new Date(incident.resolved_at);
    const durationMs = resolved.getTime() - occurred.getTime();
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "SEV1":
        return "#ef4444";
      case "SEV2":
        return "#f97316";
      case "SEV3":
        return "#eab308";
      case "SEV4":
        return "#3b82f6";
      default:
        return "#6b7280";
    }
  };

  return (
    <div className="incident-table-container">
      <table className="incident-table">
        <thead>
          <tr>
            <th>Source</th>
            <th>ID</th>
            <th>Title</th>
            <th>Severity</th>
            <th>
              <button
                onClick={() => handleSort("occurred_at")}
                className="sort-button"
              >
                Occurred {sortBy === "occurred_at" && (sortDirection === "asc" ? "↑" : "↓")}
              </button>
            </th>
            <th>
              <button
                onClick={() => handleSort("resolved_at")}
                className="sort-button"
              >
                Resolved {sortBy === "resolved_at" && (sortDirection === "asc" ? "↑" : "↓")}
              </button>
            </th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {sortedIncidents.map((incident) => (
            <tr key={incident.id || incident.external_id}>
              <td>
                <span className="source-badge">{incident.source}</span>
              </td>
              <td className="external-id">{incident.external_id}</td>
              <td className="title">{incident.title}</td>
              <td>
                <span
                  className="severity-badge"
                  style={{
                    backgroundColor: getSeverityColor(incident.severity),
                    color: "white",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "12px",
                    fontWeight: "bold",
                  }}
                >
                  {incident.severity}
                </span>
              </td>
              <td>{formatDate(incident.occurred_at)}</td>
              <td>{formatDate(incident.resolved_at)}</td>
              <td>{calculateDuration(incident)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <style>{`
        .incident-table-container {
          width: 100%;
          overflow-x: auto;
          margin-top: 1rem;
        }

        .incident-table {
          width: 100%;
          border-collapse: collapse;
          background: white;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .incident-table th {
          background: #f9fafb;
          padding: 12px;
          text-align: left;
          font-weight: 600;
          font-size: 14px;
          color: #374151;
          border-bottom: 1px solid #e5e7eb;
        }

        .incident-table td {
          padding: 12px;
          border-bottom: 1px solid #f3f4f6;
          font-size: 14px;
          color: #1f2937;
        }

        .incident-table tbody tr:hover {
          background: #f9fafb;
        }

        .sort-button {
          background: none;
          border: none;
          cursor: pointer;
          font-weight: 600;
          font-size: 14px;
          color: #374151;
          padding: 0;
        }

        .sort-button:hover {
          color: #1f2937;
        }

        .source-badge {
          display: inline-block;
          padding: 4px 8px;
          background: #e5e7eb;
          color: #374151;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          text-transform: uppercase;
        }

        .external-id {
          font-family: monospace;
          font-size: 12px;
          color: #6b7280;
        }

        .title {
          max-width: 400px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .loading, .empty-state {
          text-align: center;
          padding: 2rem;
          color: #6b7280;
        }
      `}</style>
    </div>
  );
}
