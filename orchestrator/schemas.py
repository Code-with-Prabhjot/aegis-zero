"""
AEGIS-0 Domain Schemas & Type System
Defines core representations for model tiers, pricing, AST nodes,
financial ledger budget states, pre-flight cost estimates, and action approvals.
"""

from enum import Enum
from typing import Optional, List, Dict
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


# Default Pricing Registry
DEFAULT_MODEL_PRICING: Dict[ModelTier, ModelPricing] = {
    ModelTier.TIER_2_FRONTIER: ModelPricing(
        input_per_mtok=3.00,
        output_per_mtok=15.00
    ),
    ModelTier.TIER_1_MICRO: ModelPricing(
        input_per_mtok=0.25,
        output_per_mtok=1.25
    ),
    ModelTier.TIER_0_LOCAL: ModelPricing(
        input_per_mtok=0.00,
        output_per_mtok=0.00
    ),
}


class ASTNode(BaseModel):
    """
    Represents a granular parsed AST code symbol (function, class, or import)
    with exact token costs and pre-rendered 1-line stubs.
    """
    node_id: str
    name: str
    node_type: str  # "function" | "class" | "import"
    file_path: str
    raw_source: str
    stub_source: str
    token_cost: int
    stub_token_cost: int
    dependencies: List[str] = Field(default_factory=list)


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
    recovery_checkpoint: Optional[Dict] = None


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
    is_quarantined: bool = True
    is_approved: bool = False
