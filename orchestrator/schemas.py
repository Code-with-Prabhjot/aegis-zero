"""
AEGIS-0 Domain Schemas & Type System
Defines core representations for model tiers, pricing, AST nodes,
financial ledger budget states, pre-flight cost estimates, action approvals,
circuit breaker states, and orchestration payloads.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ModelTier(str, Enum):
    TIER_0_LOCAL = "tier-0-local"
    TIER_1_MICRO = "tier-1-micro"
    TIER_2_FRONTIER = "tier-2-frontier"


class ModelPricing(BaseModel):
    """
    Pricing structure per million tokens (Mtok).
    """
    input_per_mtok: float = Field(..., description="Cost in USD per 1M input tokens")
    output_per_mtok: float = Field(..., description="Cost in USD per 1M output tokens")
    cache_read_per_mtok: Optional[float] = Field(
        None, description="Cost per 1M prompt-cache read tokens (defaults to 0.1x input)"
    )
    cache_write_per_mtok: Optional[float] = Field(
        None, description="Cost per 1M prompt-cache write tokens (defaults to 1.25x input)"
    )

    @property
    def cache_read_rate(self) -> float:
        return self.cache_read_per_mtok if self.cache_read_per_mtok is not None else 0.1 * self.input_per_mtok

    @property
    def cache_write_rate(self) -> float:
        return self.cache_write_per_mtok if self.cache_write_per_mtok is not None else 1.25 * self.input_per_mtok


# Per-tier prices and model IDs live in orchestrator/model_registry.py.


class ASTNode(BaseModel):
    """
    Represents a granular parsed AST code symbol (function, class, or import)
    with exact token costs and pre-rendered 1-line stubs.
    """
    node_id: str
    name: str
    node_type: str  # "function" | "class" | "method" | "constant" | "statement" | "import" | "fallback"
    file_path: str
    raw_source: str
    stub_source: str
    token_cost: int
    stub_token_cost: int
    dependencies: List[str] = Field(default_factory=list)
    # node_id of the enclosing class for methods; None for top-level symbols
    parent_id: Optional[str] = None


class BudgetState(BaseModel):
    """
    Maintains financial and token consumption state for an active session.
    """
    user_id: str
    session_id: str
    user_limit_usd: float
    session_limit_usd: float
    cumulative_cost_usd: float = 0.0
    cumulative_tokens: int = 0
    is_halted: bool = False
    recovery_checkpoint: Optional[Dict[str, Any]] = None


class PreFlightCostEstimate(BaseModel):
    """
    Result of deterministic pre-call financial evaluation.
    """
    input_tokens: int
    reserved_output_tokens: int
    estimated_cost_usd: float
    selected_tier: ModelTier
    can_dispatch: bool
    halt_reason: Optional[str] = None


class ActionCategory(str, Enum):
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    GIT = "git"


class ActionApprovalRequest(BaseModel):
    """
    Cryptographic action approval record for zero-trust tool execution.
    """
    action_id: str
    category: ActionCategory
    command_or_path: str
    diff_payload: Optional[str] = None
    hmac_token: str
    signed_payload: Optional[str] = None
    expires_at: Optional[str] = None
    is_quarantined: bool = True
    is_approved: bool = False


class CircuitBreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class FailoverEvent(BaseModel):
    """
    Telemetry event capturing circuit-breaker provider switch.
    """
    timestamp: str
    from_model: str
    to_model: str
    from_tier: ModelTier
    to_tier: ModelTier
    status_code: int
    latency_ms: float
    reason: str


class BifrostCompletionResponse(BaseModel):
    """
    Canonical response from Bifrost AI Gateway / local enclave.
    """
    id: str
    model: str
    tier: ModelTier
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    failover_occurred: bool = False
    failover_chain: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    cached: bool = False


class FreshnessClaimVerification(BaseModel):
    """
    Verification record for extracted SDK/API version claim.
    """
    claim: str
    freshness_score: float
    is_stale: bool
    status: str  # "FRESH" | "STALE"
    delta_t_days: float
    semantic_agreement: float
    deprecation_indicator: int
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    documentation_snippets: List[str] = Field(default_factory=list)
    patch: Optional[Dict[str, Any]] = None


class OrchestrateRequest(BaseModel):
    """
    Master request payload for AEGIS-0 Orchestrator.
    """
    session_id: str = "default_session"
    user_id: str = "default_user"
    prompt: str
    repository_path: Optional[str] = None
    repo_path: Optional[str] = None
    max_token_budget: int = 8000
    file_context: Optional[Dict[str, str]] = None
    target_tier: Optional[ModelTier] = ModelTier.TIER_2_FRONTIER
    budget_limit_usd: Optional[float] = None
    proposed_action: Optional[str] = None  # e.g., "write_file", "apply_diff", "exec_shell", "read_file"
    proposed_target: Optional[str] = None


class OrchestrateResponse(BaseModel):
    """
    Master response payload from AEGIS-0 Orchestrator.
    """
    session_id: str
    status: str  # "SUCCESS" | "QUARANTINED" | "HALTED"
    model_used: str
    model_tier: ModelTier
    failover_occurred: bool = False
    failover_chain: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    raw_tokens: int = 0
    pruned_tokens: int = 0
    tokens_saved: int = 0
    compression_ratio: float = 0.0
    cost_usd: float = 0.0
    budget_remaining_usd: float = 0.0
    privacy_tainted: bool = False
    airgap_locked: bool = False
    generated_code: str = ""
    original_code: Optional[str] = None
    freshness_verifications: List[Dict[str, Any]] = Field(default_factory=list)
    action_quarantine: Optional[ActionApprovalRequest] = None
    recovery_checkpoint: Optional[Dict[str, Any]] = None
    ast_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    # On-demand expansion of stubbed symbols requested by the model
    expansions: List[Dict[str, Any]] = Field(default_factory=list)
    expansion_tokens: int = 0
    expansion_rounds: int = 0
    expansion_skipped_reason: Optional[str] = None


class RedTeamRequest(BaseModel):
    """
    Payload for adversarial red-team simulation attack vector.
    """
    attack_type: str = Field(..., description="prompt_injection | secret_exfiltration | scope_escape")
    payload: str = Field(..., description="Adversarial attack payload or probe string")


class RedTeamResponse(BaseModel):
    """
    Containment verification response from Zero-Trust Red-Team Engine.
    """
    blocked: bool = True
    defense_triggered: str
    entropy_score: float
    airgap_enforced: bool = True
    audit_log: str


class ChaosInjectRequest(BaseModel):
    """
    Payload to trigger live circuit-breaker failover chaos testing.
    """
    status_code: int = 429
    target_model: Optional[str] = None


class ActionApproveRequest(BaseModel):
    """
    Cryptographic action approval request payload.
    """
    action_id: str
    hmac_token: str
    payload: str
    target_path: Optional[str] = None
    diff_payload: Optional[str] = None
