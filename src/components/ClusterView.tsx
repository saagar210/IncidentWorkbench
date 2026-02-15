/**
 * Expandable cluster card component
 */

import { useState } from "react";
import type { ClusterResult } from "../types";
import { useIncidents } from "../api/hooks";

interface ClusterViewProps {
  cluster: ClusterResult;
  runId: string;
}

export function ClusterView({ cluster }: ClusterViewProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Fetch incident details if expanded
  const { data: incidentsData } = useIncidents({});

  // Filter incidents by cluster membership
  const clusterIncidents = incidentsData?.incidents.filter(
    (inc) => cluster.incident_ids.includes(inc.id!)
  ) || [];

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="border border-gray-300 rounded-lg mb-4 overflow-hidden">
      {/* Header */}
      <div
        className="bg-gray-50 p-4 cursor-pointer hover:bg-gray-100 transition-colors flex items-center justify-between"
        onClick={handleToggle}
      >
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900">
            {cluster.summary || `Cluster ${cluster.cluster_id}`}
          </h3>
          {cluster.centroid_text && (
            <p className="text-sm text-gray-600 italic mt-1">
              {cluster.centroid_text}
            </p>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            {cluster.size} incident{cluster.size !== 1 ? "s" : ""}
          </span>
          <svg
            className={`w-5 h-5 text-gray-500 transition-transform ${
              isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="p-4 bg-white border-t border-gray-200">
          {clusterIncidents.length > 0 ? (
            <ul className="space-y-2">
              {clusterIncidents.map((incident) => (
                <li key={incident.id} className="flex items-start gap-2">
                  <span className="text-gray-400 mt-1">•</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {incident.title}
                    </p>
                    <p className="text-xs text-gray-500">
                      {incident.external_id} • {incident.severity} •{" "}
                      {new Date(incident.occurred_at).toLocaleDateString()}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">
              Loading incident details...
            </p>
          )}
        </div>
      )}
    </div>
  );
}
