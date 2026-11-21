// Runtime configuration for the Mission Control workbench.
// NEXT_PUBLIC_* values are inlined at build time; set them in .env.local.

const trimSlash = (url: string) => url.replace(/\/+$/, "");

/** Base URL of the AEGIS-0 orchestrator (FastAPI). */
export const API_BASE = trimSlash(
  process.env.NEXT_PUBLIC_AEGIS_API ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000"
);

/** WebSocket base, derived from API_BASE unless set explicitly. */
export const WS_BASE = trimSlash(
  process.env.NEXT_PUBLIC_AEGIS_WS ||
  process.env.NEXT_PUBLIC_WS_BASE_URL ||
  API_BASE.replace(/^http/, "ws")
);

export const apiUrl = (path: string) => `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
export const wsUrl = (path: string) => `${WS_BASE}${path.startsWith("/") ? path : `/${path}`}`;

/** Model labels. Keep defaults in sync with orchestrator/model_registry.py. */
export const MODELS = {
  frontier: process.env.NEXT_PUBLIC_AEGIS_FRONTIER_MODEL ?? "claude-sonnet-4-20250514",
  fallback: process.env.NEXT_PUBLIC_AEGIS_FALLBACK_MODEL ?? "gpt-4o",
  micro: process.env.NEXT_PUBLIC_AEGIS_MICRO_MODEL ?? "gpt-4o",
  local: process.env.NEXT_PUBLIC_AEGIS_LOCAL_MODEL ?? "deepseek-coder-v2",
};
