/**
 * Chart export utilities using html2canvas
 */

import html2canvas from "html2canvas";

/**
 * Export a chart element as PNG base64
 * @param elementId - The DOM element ID to capture
 * @returns Base64 encoded PNG string (without data:image/png;base64, prefix)
 */
export async function exportChartAsPng(elementId: string): Promise<string> {
  const element = document.getElementById(elementId);
  if (!element) {
    throw new Error(`Element #${elementId} not found`);
  }

  const canvas = await html2canvas(element, {
    backgroundColor: "#ffffff",
    scale: 2, // Higher DPI for better quality in DOCX
  });

  // Return base64 without the data URL prefix
  return canvas.toDataURL("image/png").split(",")[1];
}

/**
 * Export multiple charts as PNG base64
 * @param elementIds - Array of DOM element IDs to capture
 * @returns Object mapping element IDs to base64 PNG strings
 */
export async function exportChartsAsPng(
  elementIds: string[]
): Promise<Record<string, string>> {
  const result: Record<string, string> = {};

  for (const id of elementIds) {
    result[id] = await exportChartAsPng(id);
  }

  return result;
}
