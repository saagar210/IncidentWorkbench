/**
 * Axios client configured for Tauri backend
 */

import axios from "axios";
import { invoke } from "@tauri-apps/api/core";

let apiClient: ReturnType<typeof axios.create> | null = null;

/**
 * Get or create the configured axios instance
 */
export async function getApiClient() {
  if (apiClient) {
    return apiClient;
  }

  // Get backend port from Tauri
  const port = await invoke<number>("get_backend_port");

  apiClient = axios.create({
    baseURL: `http://127.0.0.1:${port}`,
    timeout: 60000, // 60 seconds for long operations
    headers: {
      "Content-Type": "application/json",
    },
  });

  return apiClient;
}

/**
 * Reset the client (useful for testing or reconnection)
 */
export function resetApiClient() {
  apiClient = null;
}
