// Runtime configuration for the Mission Control workbench.
// NEXT_PUBLIC_* values are inlined at build time; set them in .env.local.

const trimSlash = (url: string) => url.replace(/\/+$/, "");

/** Base URL of the AEGIS-0 orchestrator (FastAPI). */
export const API_BASE = trimSlash(process.env.NEXT_PUBLIC_AEGIS_API ?? "http://localhost:8000");

/** WebSocket base, derived from API_BASE unless set explicitly. */
export const WS_BASE = trimSlash(
  process.env.NEXT_PUBLIC_AEGIS_WS ?? API_BASE.replace(/^http/, "ws")
);

export const apiUrl = (path: string) => `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
export const wsUrl = (path: string) => `${WS_BASE}${path.startsWith("/") ? path : `/${path}`}`;

/** Model labels. Keep defaults in sync with orchestrator/model_registry.py. */
export const MODELS = {
  frontier: process.env.NEXT_PUBLIC_AEGIS_FRONTIER_MODEL ?? "claude-opus-5-5",
  fallback: process.env.NEXT_PUBLIC_AEGIS_FALLBACK_MODEL ?? "gpt-5.6",
  micro: process.env.NEXT_PUBLIC_AEGIS_MICRO_MODEL ?? "claude-haiku-5-5",
  local: process.env.NEXT_PUBLIC_AEGIS_LOCAL_MODEL ?? "deepseek-coder-v2",
};
