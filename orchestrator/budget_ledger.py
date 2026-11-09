"""
AEGIS-0 Deterministic Pre-Call Financial Ledger (PS-01 Enforcement)
Guarantees mathematical budget ceilings, worst-case pre-call cost reservation,
dynamic down-routing across model tiers, and hard-halt state machine transitions.
"""

from datetime import datetime, timezone
from typing import Dict, Optional
from orchestrator.schemas import (
    ModelTier,
    ModelPricing,
    DEFAULT_MODEL_PRICING,
    BudgetState,
    PreFlightCostEstimate,
)


class BudgetLedger:
    """
    Deterministic Financial Ledger enforcing hard token and USD ceilings
    prior to any network dispatch.
    """

    def __init__(
        self,
        pricing_registry: Optional[Dict[ModelTier, ModelPricing]] = None,
        default_user_budget_usd: float = 0.50,
        default_session_budget_usd: float = 0.10,
    ):
        self.pricing = pricing_registry or DEFAULT_MODEL_PRICING
        self.default_user_budget_usd = default_user_budget_usd
        self.default_session_budget_usd = default_session_budget_usd
        self.sessions: Dict[str, BudgetState] = {}

    def register_session(
        self,
        session_id: str,
        user_id: str = "default_user",
        user_limit_usd: Optional[float] = None,
        session_limit_usd: Optional[float] = None,
    ) -> BudgetState:
        """
        Registers or retrieves a session budget state.
        """
        if session_id in self.sessions:
            return self.sessions[session_id]

        state = BudgetState(
            user_id=user_id,
            session_id=session_id,
            user_limit_usd=user_limit_usd
            if user_limit_usd is not None
            else self.default_user_budget_usd,
            session_limit_usd=session_limit_usd
            if session_limit_usd is not None
            else self.default_session_budget_usd,
            cumulative_cost_usd=0.0,
            cumulative_tokens=0,
            is_halted=False,
        )
        self.sessions[session_id] = state
        return state

    def get_session(self, session_id: str) -> BudgetState:
        """
        Retrieves active session state or initializes default if missing.
        """
        if session_id not in self.sessions:
            return self.register_session(session_id)
        return self.sessions[session_id]

    def _calculate_bound_cost(
        self, input_tokens: int, output_tokens: int, tier: ModelTier
    ) -> float:
        """
        Computes cost in USD given tokens and tier pricing per Mtok:
        Cost = (T_in * P_in + T_out * P_out) / 1,000,000
        """
        pricing = self.pricing.get(tier, self.pricing[ModelTier.TIER_0_LOCAL])
        cost = (
            input_tokens * pricing.input_per_mtok
            + output_tokens * pricing.output_per_mtok
        ) / 1_000_000.0
        return cost

    def compute_preflight_cost(
        self,
        session_id: str,
        input_tokens: int,
        target_tier: ModelTier,
        max_output_tokens: int = 1500,
    ) -> PreFlightCostEstimate:
        """
        Evaluates worst-case upper bound completion cost:
        C_hat_i = (T_in * P_in(m)) + (T_max_out * P_out(m))

        Enforces invariant:
        sum_{k=1}^{i-1} C_k + C_hat_i <= min(L_user, L_session)

        Down-routes to TIER_1_MICRO if TIER_2_FRONTIER breaches budget cap.
        Halts execution if even down-routed cost breaches budget cap.
        """
        state = self.get_session(session_id)
        budget_cap = min(state.user_limit_usd, state.session_limit_usd)

        # Check if already halted
        if state.is_halted:
            return PreFlightCostEstimate(
                input_tokens=input_tokens,
                reserved_output_tokens=max_output_tokens,
                estimated_cost_usd=self._calculate_bound_cost(
                    input_tokens, max_output_tokens, target_tier
                ),
                selected_tier=target_tier,
                can_dispatch=False,
                halt_reason="BUDGET_CAP_EXCEEDED",
            )

        # 1. Evaluate target tier
        target_cost = self._calculate_bound_cost(
            input_tokens, max_output_tokens, target_tier
        )
        projected_total = state.cumulative_cost_usd + target_cost

        if projected_total <= budget_cap:
            return PreFlightCostEstimate(
                input_tokens=input_tokens,
                reserved_output_tokens=max_output_tokens,
                estimated_cost_usd=target_cost,
                selected_tier=target_tier,
                can_dispatch=True,
                halt_reason=None,
            )

        # 2. Down-Routing State Machine:
        # If target is TIER_2_FRONTIER, evaluate TIER_1_MICRO
        if target_tier == ModelTier.TIER_2_FRONTIER:
            micro_cost = self._calculate_bound_cost(
                input_tokens, max_output_tokens, ModelTier.TIER_1_MICRO
            )
            projected_micro_total = state.cumulative_cost_usd + micro_cost
            if projected_micro_total <= budget_cap:
                return PreFlightCostEstimate(
                    input_tokens=input_tokens,
                    reserved_output_tokens=max_output_tokens,
                    estimated_cost_usd=micro_cost,
                    selected_tier=ModelTier.TIER_1_MICRO,
                    can_dispatch=True,
                    halt_reason=None,
                )

        # 3. Halt State Machine:
        # Violates budget cap even after down-routing attempt
        state.is_halted = True
        remaining_budget = max(0.0, budget_cap - state.cumulative_cost_usd)
        state.recovery_checkpoint = {
            "session_id": session_id,
            "user_id": state.user_id,
            "cumulative_cost_usd": state.cumulative_cost_usd,
            "cumulative_tokens": state.cumulative_tokens,
            "budget_cap_usd": budget_cap,
            "remaining_budget_usd": remaining_budget,
            "attempted_tier": target_tier.value,
            "projected_cost_usd": target_cost,
            "halt_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "HALTED_RECOVERY_READY",
        }

        return PreFlightCostEstimate(
            input_tokens=input_tokens,
            reserved_output_tokens=max_output_tokens,
            estimated_cost_usd=target_cost,
            selected_tier=target_tier,
            can_dispatch=False,
            halt_reason="BUDGET_CAP_EXCEEDED",
        )

    def commit_turn_cost(
        self,
        session_id: str,
        actual_input_tokens: int,
        actual_output_tokens: int,
        tier: ModelTier,
    ) -> BudgetState:
        """
        Deducts realized cost from ledger and updates cumulative metrics.
        """
        state = self.get_session(session_id)
        realized_cost = self._calculate_bound_cost(
            actual_input_tokens, actual_output_tokens, tier
        )
        total_tokens = actual_input_tokens + actual_output_tokens

        state.cumulative_cost_usd += realized_cost
        state.cumulative_tokens += total_tokens

        budget_cap = min(state.user_limit_usd, state.session_limit_usd)
        if state.cumulative_cost_usd >= budget_cap:
            state.is_halted = True
            state.recovery_checkpoint = {
                "session_id": session_id,
                "user_id": state.user_id,
                "cumulative_cost_usd": state.cumulative_cost_usd,
                "cumulative_tokens": state.cumulative_tokens,
                "budget_cap_usd": budget_cap,
                "remaining_budget_usd": 0.0,
                "last_tier": tier.value,
                "halt_timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "HALTED_CAP_REACHED",
            }

        return state
