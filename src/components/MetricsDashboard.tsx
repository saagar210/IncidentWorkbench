/**
 * Metrics Dashboard - 4 visualizations for incident data
 */

import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Label,
} from "recharts";
import type { MetricsResult } from "../types";

interface MetricsDashboardProps {
  metrics: MetricsResult;
}

// Severity color mapping
const SEVERITY_COLORS: Record<string, string> = {
  SEV1: "#ef4444", // red
  SEV2: "#f97316", // orange
  SEV3: "#eab308", // yellow
  SEV4: "#3b82f6", // blue
  UNKNOWN: "#9ca3af", // gray
};

export function MetricsDashboard({ metrics }: MetricsDashboardProps) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", padding: "24px" }}>
      <SeverityPieChart metrics={metrics} />
      <MTTRStatCard metrics={metrics} />
      <MonthlyTrendBarChart metrics={metrics} />
      <TopAssigneesBarChart metrics={metrics} />
    </div>
  );
}

/**
 * A. Severity Pie Chart
 */
function SeverityPieChart({ metrics }: MetricsDashboardProps) {
  const data = Object.entries(metrics.by_severity).map(([severity, count]) => ({
    name: severity,
    value: count,
    percentage: ((count / metrics.total_incidents) * 100).toFixed(1),
  }));

  return (
    <div
      id="chart-severity"
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "16px",
        backgroundColor: "#ffffff",
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: "16px", fontSize: "18px", fontWeight: 600 }}>
        Incidents by Severity
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={(entry) => `${entry.name}: ${entry.value} (${entry.percentage}%)`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name] || "#9ca3af"} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * B. Monthly Trend Bar Chart
 */
function MonthlyTrendBarChart({ metrics }: MetricsDashboardProps) {
  // Sort months chronologically
  const data = Object.entries(metrics.by_month)
    .map(([month, count]) => ({ month, count }))
    .sort((a, b) => a.month.localeCompare(b.month));

  return (
    <div
      id="chart-monthly-trend"
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "16px",
        backgroundColor: "#ffffff",
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: "16px", fontSize: "18px", fontWeight: 600 }}>
        Monthly Incident Trend
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis>
            <Label value="Incident Count" angle={-90} position="insideLeft" />
          </YAxis>
          <Tooltip />
          <Legend />
          <Bar dataKey="count" fill="#3b82f6" name="Incidents" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * C. MTTR Stat Card
 */
function MTTRStatCard({ metrics }: MetricsDashboardProps) {
  const mttr = metrics.mean_resolution_hours;
  const p50 = metrics.p50_resolution_hours;
  const p90 = metrics.p90_resolution_hours;

  return (
    <div
      id="chart-mttr"
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "16px",
        backgroundColor: "#ffffff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "200px",
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: "16px", fontSize: "18px", fontWeight: 600 }}>
        Mean Time to Resolution (MTTR)
      </h3>
      <div
        style={{
          fontSize: "48px",
          fontWeight: 700,
          color: "#1f2937",
          marginBottom: "16px",
        }}
      >
        {mttr !== null ? `${mttr.toFixed(1)} hrs` : "N/A"}
      </div>
      <div style={{ display: "flex", gap: "24px", fontSize: "14px", color: "#6b7280" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontWeight: 600, fontSize: "16px", color: "#1f2937" }}>
            {p50 !== null ? `${p50.toFixed(1)} hrs` : "N/A"}
          </div>
          <div>P50 (Median)</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontWeight: 600, fontSize: "16px", color: "#1f2937" }}>
            {p90 !== null ? `${p90.toFixed(1)} hrs` : "N/A"}
          </div>
          <div>P90</div>
        </div>
      </div>
    </div>
  );
}

/**
 * D. Top Assignees Horizontal Bar Chart
 */
function TopAssigneesBarChart({ metrics }: MetricsDashboardProps) {
  // Take top 10 assignees and sort by count
  const data = Object.entries(metrics.by_assignee)
    .map(([assignee, count]) => ({ assignee: assignee || "Unassigned", count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  return (
    <div
      id="chart-top-assignees"
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "16px",
        backgroundColor: "#ffffff",
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: "16px", fontSize: "18px", fontWeight: 600 }}>
        Top 10 Assignees by Incident Count
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="assignee" type="category" width={100} />
          <Tooltip />
          <Legend />
          <Bar dataKey="count" fill="#10b981" name="Incidents" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
