"""
AEGIS-0 Phase 1 Core Verification Test Suite
Tests:
1. test_budget_ledger_worst_case_reservation
2. test_budget_ledger_dynamic_down_routing
3. test_budget_ledger_hard_halt
4. test_ast_stubbing_compression
5. test_privacy_guard_entropy_and_taint
6. test_hmac_action_gate
"""

import ast
import os
import sys
import tempfile
import pytest

# Ensure repo root is on Python sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SECURITY_GATE_DIR = os.path.join(REPO_ROOT, "security-gate")
if SECURITY_GATE_DIR not in sys.path:
    sys.path.insert(0, SECURITY_GATE_DIR)

from orchestrator.schemas import (
    ModelTier,
    ModelPricing,
    ActionCategory,
    ActionApprovalRequest,
)
from orchestrator.budget_ledger import BudgetLedger
from orchestrator.ast_pruner import ASTPruner
from privacy_guard import PrivacyGuard


# ==============================================================================
# 1. Budget Ledger Worst-Case Reservation Test
# ==============================================================================
# Ledger arithmetic tests pin explicit prices so they test the math,
# independent of whichever models the registry defaults to.
LEDGER_TEST_PRICING = {
    ModelTier.TIER_2_FRONTIER: ModelPricing(input_per_mtok=3.00, output_per_mtok=15.00),
    ModelTier.TIER_1_MICRO: ModelPricing(input_per_mtok=0.25, output_per_mtok=1.25),
    ModelTier.TIER_0_LOCAL: ModelPricing(input_per_mtok=0.0, output_per_mtok=0.0),
}


def test_budget_ledger_worst_case_reservation():
    """
    Verifies that the pre-call calculator strictly reserves the full worst-case
    output margin (T_max_out * P_out) in advance before dispatch.
    """
    ledger = BudgetLedger(
        pricing_registry=LEDGER_TEST_PRICING,
        default_user_budget_usd=0.50,
        default_session_budget_usd=0.10,
    )
    session_id = "test-session-reservation"
    ledger.register_session(
        session_id=session_id,
        user_id="user_alice",
        user_limit_usd=0.50,
        session_limit_usd=0.10,
    )

    input_tokens = 1000
    max_output_tokens = 1500
    # Tier 2 Frontier: $3.00/Mtok in, $15.00/Mtok out
    # Input cost = 1000 * 3.00 / 1M = $0.0030
    # Reserved output cost = 1500 * 15.00 / 1M = $0.0225
    # Total preflight bound = $0.0255
    estimate = ledger.compute_preflight_cost(
        session_id=session_id,
        input_tokens=input_tokens,
        target_tier=ModelTier.TIER_2_FRONTIER,
        max_output_tokens=max_output_tokens,
    )

    assert estimate.can_dispatch is True
    assert estimate.selected_tier == ModelTier.TIER_2_FRONTIER
    assert estimate.reserved_output_tokens == 1500
    assert estimate.estimated_cost_usd == pytest.approx(0.0255, rel=1e-4)
    assert estimate.halt_reason is None

    # Now verify with a budget of $0.0200:
    # Input alone ($0.003) fits, but with output reservation ($0.0255 total),
    # Tier-2 is rejected.
    tight_session = "test-session-tight"
    ledger.register_session(
        session_id=tight_session,
        user_id="user_alice",
        user_limit_usd=0.020,
        session_limit_usd=0.020,
    )
    estimate_tight = ledger.compute_preflight_cost(
        session_id=tight_session,
        input_tokens=input_tokens,
        target_tier=ModelTier.TIER_2_FRONTIER,
        max_output_tokens=max_output_tokens,
    )
    # Tier 2 does NOT fit ($0.0255 > $0.020), so it must NOT dispatch on Tier 2
    assert estimate_tight.selected_tier != ModelTier.TIER_2_FRONTIER


# ==============================================================================
# 2. Budget Ledger Dynamic Down-Routing Test
# ==============================================================================
def test_budget_ledger_dynamic_down_routing():
    """
    Verifies automatic down-routing from Tier-2 Frontier to Tier-1 Micro
    when remaining balance cannot accommodate Tier-2 but can afford Tier-1.
    """
    ledger = BudgetLedger(pricing_registry=LEDGER_TEST_PRICING)
    session_id = "test-session-downroute"
    # Budget cap = $0.0150
    ledger.register_session(
        session_id=session_id,
        user_id="user_bob",
        user_limit_usd=0.50,
        session_limit_usd=0.015,
    )

    input_tokens = 2000
    max_output_tokens = 1500
    # Tier-2 cost: (2000 * 3.00 + 1500 * 15.00) / 1M = $0.0285 -> Exceeds $0.015
    # Tier-1 Micro cost: (2000 * 0.25 + 1500 * 1.25) / 1M = (500 + 1875) / 1M = $0.002375 -> Fits!
    estimate = ledger.compute_preflight_cost(
        session_id=session_id,
        input_tokens=input_tokens,
        target_tier=ModelTier.TIER_2_FRONTIER,
        max_output_tokens=max_output_tokens,
    )

    assert estimate.can_dispatch is True
    assert estimate.selected_tier == ModelTier.TIER_1_MICRO
    assert estimate.estimated_cost_usd == pytest.approx(0.002375, rel=1e-4)
    assert estimate.halt_reason is None


# ==============================================================================
# 3. Budget Ledger Hard Halt Test
# ==============================================================================
def test_budget_ledger_hard_halt():
    """
    Verifies clean hard-halt state machine activation when session budget ceiling
    is reached, producing a serialized recovery checkpoint with zero overrun.
    """
    ledger = BudgetLedger(pricing_registry=LEDGER_TEST_PRICING)
    session_id = "test-session-halt"
    # Ceiling = $0.0020
    ledger.register_session(
        session_id=session_id,
        user_id="user_charlie",
        user_limit_usd=0.50,
        session_limit_usd=0.002,
    )

    input_tokens = 2000
    max_output_tokens = 1500
    # Even Tier-1 Micro cost is $0.002375 > $0.0020 ceiling
    estimate = ledger.compute_preflight_cost(
        session_id=session_id,
        input_tokens=input_tokens,
        target_tier=ModelTier.TIER_2_FRONTIER,
        max_output_tokens=max_output_tokens,
    )

    assert estimate.can_dispatch is False
    assert estimate.halt_reason == "BUDGET_CAP_EXCEEDED"

    state = ledger.get_session(session_id)
    assert state.is_halted is True
    assert state.recovery_checkpoint is not None
    assert state.recovery_checkpoint["status"] == "HALTED_RECOVERY_READY"
    assert state.recovery_checkpoint["session_id"] == session_id

    # Commit realized turn and ensure cumulative limits enforce hard halt
    session_id2 = "test-session-commit-halt"
    ledger.register_session(
        session_id=session_id2,
        user_limit_usd=0.01,
        session_limit_usd=0.01,
    )
    # Commit $0.014 of actual tokens on Tier-1
    # 6000 in, 10000 out: (6000*0.25 + 10000*1.25)/1M = (1500 + 12500)/1M = 0.014 USD
    updated_state = ledger.commit_turn_cost(
        session_id=session_id2,
        actual_input_tokens=6000,
        actual_output_tokens=10000,
        tier=ModelTier.TIER_1_MICRO,
    )
    assert updated_state.is_halted is True
    assert updated_state.cumulative_cost_usd >= 0.01
    assert updated_state.recovery_checkpoint["status"] == "HALTED_CAP_REACHED"


# ==============================================================================
# 4. AST Stubbing Compression & Syntax Validity Test
# ==============================================================================
SAMPLE_200_LINE_SOURCE = '''"""
Institutional Quantitative Asset Management and Risk Engine
Implements submodular portfolio selection, Level-3 order routing,
Cholesky covariance factorization, and cryptographic audit proofs.
"""

import math
import time
import hashlib
from decimal import Decimal
from typing import List, Dict, Optional, Any, Tuple


class PortfolioOptimizer:
    """Solves constrained Markowitz mean-variance optimization with transaction penalties."""
    risk_aversion: float = 2.5
    turnover_penalty: float = 0.0015

    def __init__(self, target_return: Decimal = Decimal("0.12")) -> None:
        self.target_return = target_return
        self.asset_weights: Dict[str, Decimal] = {}
        self.covariance_matrix: Dict[str, Dict[str, Decimal]] = {}
        self.rebalance_history: List[Dict[str, Any]] = []
        for sym in ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]:
            self.covariance_matrix[sym] = {s: Decimal("0.0004") if s == sym else Decimal("0.0001") for s in ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]}

    def optimize_weights(self, expected_returns: Dict[str, Decimal], max_weight: Decimal = Decimal("0.35")) -> Dict[str, Decimal]:
        """Calculates optimal quadratic portfolio weights under budget and box constraints."""
        symbols = sorted(list(expected_returns.keys()))
        n = len(symbols)
        if n == 0:
            return {}
        raw_weights: Dict[str, Decimal] = {}
        total_score = Decimal("0.0")
        for sym in symbols:
            ret = expected_returns.get(sym, Decimal("0.0"))
            variance = self.covariance_matrix.get(sym, {}).get(sym, Decimal("0.01"))
            score = max(Decimal("0.001"), ret / (Decimal(str(self.risk_aversion)) * variance))
            raw_weights[sym] = score
            total_score += score
        normalized: Dict[str, Decimal] = {}
        for sym in symbols:
            weight = min(max_weight, raw_weights[sym] / total_score)
            normalized[sym] = weight.quantize(Decimal("0.0001"))
        self.asset_weights = normalized
        return normalized

    def compute_portfolio_variance(self, weights: Dict[str, Decimal]) -> Decimal:
        """Computes quadratic form w^T Sigma w."""
        total_variance = Decimal("0.0")
        for s1, w1 in weights.items():
            for s2, w2 in weights.items():
                cov = self.covariance_matrix.get(s1, {}).get(s2, Decimal("0.0"))
                total_variance += w1 * w2 * cov
        return total_variance.quantize(Decimal("0.000001"))


class RiskGovernor:
    """Enforces pre-trade risk controls, portfolio drawdown bounds, and margin requirements."""
    max_leverage: float = 4.0
    risk_multiplier: float = 1.35

    def __init__(self, account_id: str, margin_cap_usd: Decimal = Decimal("5000000.0")) -> None:
        self.account_id = account_id
        self.margin_cap_usd = margin_cap_usd
        self.current_drawdown = Decimal("0.0")
        self.peak_portfolio_equity = Decimal("0.0")
        self.exposure_history: List[Tuple[float, Decimal]] = []
        self.volatility_index: Dict[str, Decimal] = {
            "AAPL": Decimal("0.018"),
            "NVDA": Decimal("0.038"),
            "MSFT": Decimal("0.015"),
            "GOOGL": Decimal("0.021"),
            "AMZN": Decimal("0.024"),
            "META": Decimal("0.029"),
            "TSLA": Decimal("0.045"),
        }

    def compute_portfolio_var(self, positions: Dict[str, int], prices: Dict[str, Decimal], horizon_days: int = 10) -> Decimal:
        """Computes parametric 99% Value-at-Risk using square-root scaling."""
        if horizon_days <= 0:
            raise ValueError("Horizon days must be strictly positive")
        total_var = Decimal("0.0")
        for symbol, qty in positions.items():
            price = prices.get(symbol, Decimal("100.0"))
            notional = Decimal(abs(qty)) * price
            vol = self.volatility_index.get(symbol, Decimal("0.025"))
            component_var = notional * vol * Decimal(str(math.sqrt(horizon_days))) * Decimal("2.326")
            total_var += component_var
        self.exposure_history.append((time.time(), total_var))
        if len(self.exposure_history) > 1000:
            self.exposure_history.pop(0)
        return total_var.quantize(Decimal("0.01"))

    def validate_pre_trade_limits(self, symbol: str, notional_order_size: Decimal, available_equity: Decimal) -> bool:
        """Validates pre-trade leverage caps and capital preservation buffers."""
        if available_equity <= Decimal("0.0") or notional_order_size <= Decimal("0.0"):
            return False
        required_margin = notional_order_size / Decimal(str(self.max_leverage))
        buffered_margin = required_margin * Decimal(str(self.risk_multiplier))
        if buffered_margin > available_equity:
            return False
        if buffered_margin > self.margin_cap_usd:
            return False
        current_exp = sum(exp for _, exp in self.exposure_history[-10:]) if self.exposure_history else Decimal("0.0")
        if current_exp + buffered_margin > self.margin_cap_usd * Decimal("1.2"):
            return False
        return True


class OrderBookL3:
    """High-performance Level 3 Order Book maintaining price levels and order queues."""
    def __init__(self, symbol: str, tick_size: Decimal = Decimal("0.01")) -> None:
        self.symbol = symbol
        self.tick_size = tick_size
        self.bids: Dict[Decimal, List[Dict[str, Any]]] = {}
        self.asks: Dict[Decimal, List[Dict[str, Any]]] = {}
        self.order_index: Dict[str, Tuple[str, Decimal]] = {}
        self.volume_traded: int = 0
        self.vwap_numerator: Decimal = Decimal("0.0")

    def insert_order(self, order_id: str, side: str, price: Decimal, size: int) -> bool:
        """Inserts a limit order into price priority queues."""
        if size <= 0 or price <= Decimal("0.0"):
            return False
        quantized_price = (price / self.tick_size).to_integral_value() * self.tick_size
        queue = self.bids if side.upper() == "BUY" else self.asks
        if quantized_price not in queue:
            queue[quantized_price] = []
        entry = {
            "order_id": order_id,
            "size": size,
            "remaining": size,
            "timestamp": time.time_ns(),
            "flags": {"post_only": False, "iceberg": False},
        }
        queue[quantized_price].append(entry)
        self.order_index[order_id] = (side.upper(), quantized_price)
        return True

    def cancel_order(self, order_id: str) -> bool:
        """Cancels an existing order by identifier."""
        if order_id not in self.order_index:
            return False
        side, price = self.order_index.pop(order_id)
        queue = self.bids if side == "BUY" else self.asks
        if price in queue:
            queue[price] = [o for o in queue[price] if o["order_id"] != order_id]
            if not queue[price]:
                del queue[price]
        return True

    def get_market_depth(self, levels: int = 5) -> Dict[str, List[Tuple[str, int]]]:
        """Extracts top N price levels and aggregate sizes."""
        sorted_bids = sorted(self.bids.keys(), reverse=True)[:levels]
        sorted_asks = sorted(self.asks.keys())[:levels]
        bid_depth = []
        for p in sorted_bids:
            total_sz = sum(o["remaining"] for o in self.bids[p])
            bid_depth.append((str(p), total_sz))
        ask_depth = []
        for p in sorted_asks:
            total_sz = sum(o["remaining"] for o in self.asks[p])
            ask_depth.append((str(p), total_sz))
        return {"bids": bid_depth, "asks": ask_depth}


class ExecutionRouter:
    """TWAP and VWAP algorithmic slice router optimizing market impact."""
    def __init__(self, venues: Optional[List[str]] = None) -> None:
        self.venues = venues or ["BATS", "NASDAQ_ITCH", "NYSE_ARCA", "IEX_DEEP", "MEMX"]
        self.fill_history: List[Dict[str, Any]] = []
        self.venue_latency_ms: Dict[str, float] = {
            "BATS": 0.45,
            "NASDAQ_ITCH": 0.38,
            "NYSE_ARCA": 0.52,
            "IEX_DEEP": 1.20,
            "MEMX": 0.41,
        }

    def compute_twap_slices(self, total_shares: int, duration_minutes: int, interval_seconds: int = 30) -> List[int]:
        """Calculates time-weighted execution slices across uniform trading windows."""
        if total_shares <= 0 or duration_minutes <= 0:
            return []
        total_intervals = max(1, (duration_minutes * 60) // interval_seconds)
        base_slice = total_shares // total_intervals
        remainder = total_shares % total_intervals
        slices = []
        for i in range(total_intervals):
            extra = 1 if i < remainder else 0
            jitter = (i % 3) - 1
            allocated = max(1, base_slice + extra + jitter)
            slices.append(allocated)
        diff = total_shares - sum(slices)
        slices[-1] += diff
        return slices

    def execute_slice(self, slice_id: str, symbol: str, side: str, qty: int, venue: str) -> Dict[str, Any]:
        """Dispatches an individual slice to destination venue socket."""
        fill_price = Decimal("150.25")
        timestamp = time.time()
        latency = self.venue_latency_ms.get(venue, 0.5)
        record = {
            "slice_id": slice_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "venue": venue,
            "fill_price": str(fill_price),
            "simulated_latency_ms": latency,
            "timestamp": timestamp,
            "audit_hash": hashlib.sha256(f"{slice_id}:{symbol}:{qty}".encode()).hexdigest(),
        }
        self.fill_history.append(record)
        return record


class SettlementAuditor:
    """Generates immutable cryptographic audit proofs for clearing houses."""
    def __init__(self, signing_seed: str = "AEGIS-SEC-CLEARING-2026") -> None:
        self.signing_seed = signing_seed
        self.audit_chain: List[str] = []
        self.block_records: Dict[str, List[Dict[str, Any]]] = {}

    def commit_audit_block(self, block_index: int, tx_records: List[Dict[str, Any]]) -> str:
        """Appends a new cryptographically verified block to the local settlement ledger."""
        prev_hash = self.audit_chain[-1] if self.audit_chain else "GENESIS_BLOCK_00000000"
        digest_builder = hashlib.sha256()
        for rec in tx_records:
            digest_builder.update(str(rec).encode("utf-8"))
        records_merkle_root = digest_builder.hexdigest()
        payload = f"{block_index}:{prev_hash}:{records_merkle_root}:{self.signing_seed}"
        block_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.audit_chain.append(block_hash)
        self.block_records[block_hash] = tx_records
        return block_hash

    def verify_chain(self) -> bool:
        """Verifies hash continuity across the entire recorded block sequence."""
        if not self.audit_chain:
            return True
        for i in range(1, len(self.audit_chain)):
            curr = self.audit_chain[i]
            if not curr:
                return False
        return True


class TradingOrchestrator:
    """Top-level trading orchestrator coordinating risk, book, and settlement."""
    def __init__(self, account_id: str) -> None:
        self.account_id = account_id
        self.risk = RiskGovernor(account_id)
        self.router = ExecutionRouter()
        self.auditor = SettlementAuditor()
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        self.cumulative_notional = Decimal("0.0")

    def submit_algorithmic_order(self, order_id: str, symbol: str, side: str, qty: int, limit_price: Decimal) -> Dict[str, Any]:
        """Submits and fulfills an algorithmic parent order with full lifecycle tracking."""
        notional = Decimal(qty) * limit_price
        if not self.risk.validate_pre_trade_limits(symbol, notional, notional * Decimal("2.0")):
            return {"status": "REJECTED", "reason": "RISK_LIMIT_BREACH"}
        slices = self.router.compute_twap_slices(qty, duration_minutes=5)
        fills = []
        for idx, slice_qty in enumerate(slices):
            venue = "NASDAQ_ITCH" if idx % 2 == 0 else "BATS"
            fill = self.router.execute_slice(f"{order_id}_{idx}", symbol, side, slice_qty, venue)
            fills.append(fill)
        block_hash = self.auditor.commit_audit_block(len(self.active_orders) + 1, fills)
        order_record = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "limit_price": str(limit_price),
            "fills_count": len(fills),
            "block_hash": block_hash,
            "status": "FILLED",
        }
        self.active_orders[order_id] = order_record
        self.cumulative_notional += notional
        return order_record


def calculate_sec_fees(shares: int, price: Decimal) -> Decimal:
    """Calculates SEC Section 31 fees and FINRA Trading Activity Fees (TAF)."""
    notional = Decimal(shares) * price
    sec_fee = notional * Decimal("0.0000278")
    taf_rate = Decimal("0.000166")
    taf_cap = Decimal("8.30")
    computed_taf = Decimal(shares) * taf_rate
    taf_fee = min(computed_taf, taf_cap)
    total_regulatory_fee = sec_fee + taf_fee
    return total_regulatory_fee.quantize(Decimal("0.01"))


def format_execution_report(order_id: str, status: str, fills_count: int) -> str:
    """Formats standardized FIX 4.4 execution report text."""
    timestamp = time.strftime("%Y%m%d-%H:%M:%S")
    return f"FIX.4.4|35=8|37={order_id}|39={status}|qty_fills={fills_count}|transact_time={timestamp}|"
'''


def test_ast_stubbing_compression():
    """
    Validates that a sample 200+ line multi-class Python file is pruned by >= 75%
    token reduction while producing 100% syntactically valid Python code.
    """
    pruner = ASTPruner()
    nodes = pruner.parse_source("sample_service.py", SAMPLE_200_LINE_SOURCE)

    assert len(nodes) > 5, "Expected multiple classes, functions, and imports"
    assert len(SAMPLE_200_LINE_SOURCE.splitlines()) >= 200, "Expected at least 200 lines"

    # Query focused on format_execution_report
    query = "How is execution reporting formatted under FIX 4.4 protocol?"
    seed_symbols = ["format_execution_report"]

    # Budget calibrated to keep seed function in full context and collapse classes to stubs
    max_token_budget = 400
    hybrid_code, metrics = pruner.prune_context(
        nodes=nodes,
        query=query,
        seed_symbols=seed_symbols,
        max_token_budget=max_token_budget,
    )

    # 1. Compression Ratio >= 75% (0.75)
    assert (
        metrics["compression_ratio"] >= 0.75
    ), f"Expected >= 75% compression, got {metrics['compression_ratio'] * 100:.1f}%"
    assert metrics["tokens_saved"] > 0

    # 2. Syntactic validity: Must parse cleanly with Python ast.parse
    parsed_tree = ast.parse(hybrid_code)
    assert parsed_tree is not None, "Hybrid pruned buffer must be valid Python syntax"

    # 3. Seed symbol retained with full context
    assert "def format_execution_report" in hybrid_code
    assert "FIX.4.4|35=8" in hybrid_code  # Full body preserved

    # 4. Non-seed nodes collapsed to 1-line stubs
    assert "[AST-STUB:" in hybrid_code


# ==============================================================================
# 5. Zero-Trust Privacy Guard Entropy & Air-Gap Taint Test
# ==============================================================================
def test_privacy_guard_entropy_and_taint():
    """
    Validates that injected mock API keys trigger H >= 4.5 Shannon entropy
    and mandate TIER_0_LOCAL routing with X-Bifrost-Privacy-Lock.
    """
    guard = PrivacyGuard()

    # 1. Shannon entropy verification
    high_entropy_secret = "AKIA" + "IOSFODNN7EXAMPLE1234567890abcdef"
    h = guard.calculate_shannon_entropy(high_entropy_secret)
    assert h >= 4.5, f"Expected Shannon entropy >= 4.5, got {h:.3f}"

    low_entropy_str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert guard.calculate_shannon_entropy(low_entropy_str) < 1.0

    # 2. Repository inspection with injected secrets
    with tempfile.TemporaryDirectory() as temp_dir:
        # Injected mock file with AWS key
        secret_file = os.path.join(temp_dir, "config.py")
        dummy_aws = "AKIA" + "IOSFODNN7EXAMPLE"
        dummy_openai = "sk-" + "proj-" + "abc123456789012345678901234567890xyz"
        with open(secret_file, "w", encoding="utf-8") as f:
            f.write(
                f'AWS_ACCESS_KEY = "{dummy_aws}"\n'
                f'OPENAI_API_KEY = "{dummy_openai}"\n'
            )

        report = guard.inspect_repository(temp_dir)
        assert report["taint_status"] is True
        assert report["routing_target"] == ModelTier.TIER_0_LOCAL
        assert report["headers"].get("X-Bifrost-Privacy-Lock") == "local_only"
        assert len(report["violations"]) >= 1

    # 3. Policy-driven confidential taint verification (.aegis-policy.yml)
    with tempfile.TemporaryDirectory() as temp_dir:
        policy_file = os.path.join(temp_dir, ".aegis-policy.yml")
        with open(policy_file, "w", encoding="utf-8") as f:
            f.write("confidential: true\n")

        clean_file = os.path.join(temp_dir, "app.py")
        with open(clean_file, "w", encoding="utf-8") as f:
            f.write("def hello():\n    return 'clean public code'\n")

        policy_report = guard.inspect_repository(temp_dir)
        assert policy_report["taint_status"] is True
        assert policy_report["routing_target"] == ModelTier.TIER_0_LOCAL
        assert policy_report["headers"].get("X-Bifrost-Privacy-Lock") == "local_only"


# ==============================================================================
# 6. Cryptographic Action Approval Gate Test
# ==============================================================================
def test_hmac_action_gate():
    """
    Validates HMAC-SHA256 signature generation and tamper verification
    for destructive write/shell/git operations.
    """
    guard = PrivacyGuard()
    secret_key = "aegis-kernel-cryptographic-signing-key"

    action_id = "act-9843-git-push"
    payload = "git push -u origin feat/phase1-foundation-core"

    # 1. Token generation
    token = guard.generate_hmac_action_token(action_id, payload, secret_key)
    assert isinstance(token, str)
    assert len(token) == 64  # SHA-256 hex digest length

    # 2. Legitimate verification
    assert guard.verify_action_token(token, action_id, payload, secret_key) is True

    # 3. Tampering detection
    tampered_payload = "git push -u origin feat/phase1-foundation-core --force"
    assert guard.verify_action_token(token, action_id, tampered_payload, secret_key) is False

    tampered_action_id = "act-0000-tampered"
    assert guard.verify_action_token(token, tampered_action_id, payload, secret_key) is False

    wrong_secret = "attacker-compromised-key"
    assert guard.verify_action_token(token, action_id, payload, wrong_secret) is False

    # 4. ActionApprovalRequest schema integration
    approval_req = ActionApprovalRequest(
        action_id=action_id,
        category=ActionCategory.GIT,
        command_or_path=payload,
        diff_payload=None,
        hmac_token=token,
        is_quarantined=True,
        is_approved=False,
    )
    assert approval_req.is_quarantined is True
    assert approval_req.is_approved is False
    assert approval_req.category == ActionCategory.GIT
