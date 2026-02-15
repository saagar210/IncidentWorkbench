/**
 * Chart Exporter - Renders dashboard and exports charts as PNG
 */

import { useState } from "react";
import { MetricsDashboard } from "./MetricsDashboard";
import { exportChartsAsPng } from "../utils/chartExport";
import type { MetricsResult } from "../types";

interface ChartExporterProps {
  metrics: MetricsResult;
  onChartsExported: (chartPngs: Record<string, string>) => void;
}

const CHART_IDS = [
  "chart-severity",
  "chart-monthly-trend",
  "chart-mttr",
  "chart-top-assignees",
];

export function ChartExporter({ metrics, onChartsExported }: ChartExporterProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportedCharts, setExportedCharts] = useState<Record<string, string> | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      // Wait a bit for charts to fully render
      await new Promise((resolve) => setTimeout(resolve, 500));

      const chartPngs = await exportChartsAsPng(CHART_IDS);
      setExportedCharts(chartPngs);
      onChartsExported(chartPngs);
    } catch (error) {
      console.error("Failed to export charts:", error);
      alert(`Failed to export charts: ${error}`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <button
          onClick={handleExport}
          disabled={isExporting}
          style={{
            padding: "12px 24px",
            fontSize: "16px",
            fontWeight: 600,
            backgroundColor: "#3b82f6",
            color: "#ffffff",
            border: "none",
            borderRadius: "8px",
            cursor: isExporting ? "not-allowed" : "pointer",
            opacity: isExporting ? 0.6 : 1,
          }}
        >
          {isExporting ? "Exporting Charts..." : "Export Charts for Report"}
        </button>
        {exportedCharts && (
          <span style={{ marginLeft: "16px", color: "#10b981", fontWeight: 600 }}>
            ✓ Charts exported successfully
          </span>
        )}
      </div>

      <MetricsDashboard metrics={metrics} />
    </div>
  );
}
