/**
 * API Service Layer — centralized backend communication
 * All pipeline API calls go through here.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }
  return response.json();
}

export const pipelineAPI = {
  /** Upload a customer file for processing */
  upload: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/pipeline/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(res);
  },

  /** Trigger pipeline execution with selected steps */
  execute: async (runId, enabledSteps) => {
    const res = await fetch(`${API_BASE}/pipeline/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: runId, enabled_steps: enabledSteps }),
    });
    return handleResponse(res);
  },

  /** Get pipeline status (polled by frontend) */
  getStatus: async (runId) => {
    const res = await fetch(`${API_BASE}/pipeline/status/${runId}`);
    return handleResponse(res);
  },

  /** Download step result as file */
  download: async (runId, stepId) => {
    const res = await fetch(
      `${API_BASE}/pipeline/download/${runId}/${stepId}`
    );
    if (!res.ok) throw new Error("Download failed");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${stepId}_result.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  /** Upload corrected data for a step */
  uploadStepData: async (runId, stepId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(
      `${API_BASE}/pipeline/upload/${runId}/${stepId}`,
      { method: "POST", body: formData }
    );
    return handleResponse(res);
  },

  /** Get progressive analytics */
  getAnalytics: async (runId) => {
    const res = await fetch(`${API_BASE}/pipeline/analytics/${runId}`);
    return handleResponse(res);
  },

  /** Health check */
  health: async () => {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse(res);
  },
};
