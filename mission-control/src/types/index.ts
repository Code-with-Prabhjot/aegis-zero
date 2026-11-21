export type GatewayStatus = "ONLINE" | "FAILOVER_ACTIVE" | "CHAOS_INJECTED";

export type ModelTier = "tier-2-frontier" | "tier-1-micro" | "tier-0-local";

export interface ASTGraphNode {
  id: string;
  name: string;
  type: "function" | "class" | "import" | "module";
  file: string;
  tokenCost: number;
  stubTokenCost: number;
  tokensSaved: number;
  selected: boolean;
  relevance: number;
  stubCode: string;
  fullCode: string;
  x: number;
  y: number;
  connections: string[];
}

export interface FreshnessClaim {
  claim_id: string;
  statement: string;
  confidence_score: number; // 0 to 100
  is_stale: boolean;
  status: "FRESH" | "STALE";
  citation_url: string;
  citation_title: string;
  delta_t_days: number;
  semantic_agreement: number;
  deprecation_indicator: number;
  suggested_patch: string;
  applied?: boolean;
}

export interface QuarantinedAction {
  action_id: string;
  category: "write" | "shell" | "git" | "read";
  command_or_path: string;
  diff_payload: string;
  original_payload: string;
  hmac_token: string;
  signed_payload?: string;
  is_quarantined: boolean;
  is_approved: boolean;
  acoustic_prompt: string;
  passphrase: string;
}

export interface TelemetryState {
  gatewayStatus: GatewayStatus;
  activeModel: string;
  activeTier: ModelTier;
  tokenSavingsPct: number;
  cumulativeCostUsd: number;
  userLimitUsd: number;
  remainingBudgetUsd: number;
  failoverLatencyMs: number;
  airGapLock: boolean;
  circuitBreakerTripped: boolean;
  isHalted: boolean;
  haltReason?: string;
  claims: FreshnessClaim[];
  quarantinedAction: QuarantinedAction | null;
  nodes: ASTGraphNode[];
  rawTotalTokens: number;
  prunedTotalTokens: number;
}
