// Runtime configuration for the Mission Control workbench.
// NEXT_PUBLIC_* values are inlined at build time; set them in .env.local.

export const trimSlash = (url: string) => url.replace(/\/+$/, "");

/** Return normalized HTTP API base URL with trailing slashes stripped. */
export function getApiBaseUrl(override?: string): string {
  if (override) return trimSlash(override);
  const envUrl = process.env.NEXT_PUBLIC_AEGIS_API || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl) return trimSlash(envUrl);
  if (typeof window !== "undefined" && window.location.protocol === "https:") {
    return "https://aegis-zero.onrender.com";
  }
  return "http://localhost:8000";
}

/** Return normalized WebSocket base URL converting http(s) to ws(s). */
export function getWsBaseUrl(override?: string): string {
  const explicit = override || process.env.NEXT_PUBLIC_AEGIS_WS || process.env.NEXT_PUBLIC_WS_BASE_URL;
  if (explicit) {
    return trimSlash(explicit);
  }
  const api = getApiBaseUrl();
  if (api.startsWith("https://")) {
    return api.replace(/^https:\/\//, "wss://");
  }
  if (api.startsWith("http://")) {
    return api.replace(/^http:\/\//, "ws://");
  }
  return api.replace(/^http/, "ws");
}

/** Base URL of the AEGIS-0 orchestrator (FastAPI). */
export const API_BASE = getApiBaseUrl();

/** WebSocket base, derived from API_BASE unless set explicitly. */
export const WS_BASE = getWsBaseUrl();

export const apiUrl = (path: string) => `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
export const wsUrl = (path: string) => `${WS_BASE}${path.startsWith("/") ? path : `/${path}`}`;

/** Model labels. Keep defaults in sync with orchestrator/model_registry.py. */
export const MODELS = {
  frontier: process.env.NEXT_PUBLIC_AEGIS_FRONTIER_MODEL ?? "claude-sonnet-4-20250514",
  fallback: process.env.NEXT_PUBLIC_AEGIS_FALLBACK_MODEL ?? "gpt-4o",
  micro: process.env.NEXT_PUBLIC_AEGIS_MICRO_MODEL ?? "gpt-4o",
  local: process.env.NEXT_PUBLIC_AEGIS_LOCAL_MODEL ?? "deepseek-coder-v2",
};
