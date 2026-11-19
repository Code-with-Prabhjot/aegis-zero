"""
AEGIS-0 Model Registry

Single place for every model ID and per-tier price the orchestrator uses.
All values can be overridden with environment variables, so the gateway can
follow provider releases without code changes.

Defaults (Claude prices are Anthropic first-party API rates):
- Frontier tier:  claude-opus-5-5   ($4.00 in / $20.00 out per MTok, cache read $0.20)
- Micro tier:     claude-haiku-5-5  ($0.10 in / $0.50 out per MTok, prompts <= 100K)
- Cross-provider failover: AEGIS_FALLBACK_MODEL (default "gpt-5.6", an alias;
  confirm against the provider's current model list for your account)
- Local enclave:  deepseek-coder-v2 via Ollama ($0)

Price overrides use "input,output[,cache_read[,cache_write]]" in USD per MTok,
e.g. AEGIS_FRONTIER_PRICE="2,10,0.10,2.5" to run the frontier tier on Sonnet.
"""

import os
from typing import Dict, List

from orchestrator.schemas import ModelPricing, ModelTier


def _env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


FRONTIER_MODEL = _env("AEGIS_FRONTIER_MODEL", "claude-opus-5-5")
FRONTIER_PROVIDER = _env("AEGIS_FRONTIER_PROVIDER", "anthropic")

FALLBACK_MODEL = _env("AEGIS_FALLBACK_MODEL", "gpt-5.6")
FALLBACK_PROVIDER = _env("AEGIS_FALLBACK_PROVIDER", "openai")

MICRO_MODEL = _env("AEGIS_MICRO_MODEL", "claude-haiku-5-5")
MICRO_PROVIDER = _env("AEGIS_MICRO_PROVIDER", "anthropic")

LOCAL_MODEL = _env("AEGIS_LOCAL_MODEL", "deepseek-coder-v2")


def _price(env_name: str, default: ModelPricing) -> ModelPricing:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    parts = [float(p) for p in raw.split(",")]
    fields = ["input_per_mtok", "output_per_mtok", "cache_read_per_mtok", "cache_write_per_mtok"]
    return default.model_copy(update=dict(zip(fields, parts)))


TIER_PRICING: Dict[ModelTier, ModelPricing] = {
    ModelTier.TIER_2_FRONTIER: _price("AEGIS_FRONTIER_PRICE", ModelPricing(
        input_per_mtok=4.00, output_per_mtok=20.00,
        cache_read_per_mtok=0.20, cache_write_per_mtok=5.00,
    )),
    ModelTier.TIER_1_MICRO: _price("AEGIS_MICRO_PRICE", ModelPricing(
        input_per_mtok=0.10, output_per_mtok=0.50,
        cache_read_per_mtok=0.01, cache_write_per_mtok=0.125,
    )),
    ModelTier.TIER_0_LOCAL: ModelPricing(
        input_per_mtok=0.0, output_per_mtok=0.0, cache_read_per_mtok=0.0, cache_write_per_mtok=0.0,
    ),
}


def frontier_chain() -> List[Dict]:
    return [
        {"model": FRONTIER_MODEL, "tier": ModelTier.TIER_2_FRONTIER, "provider": FRONTIER_PROVIDER},
        {"model": FALLBACK_MODEL, "tier": ModelTier.TIER_2_FRONTIER, "provider": FALLBACK_PROVIDER},
        {"model": LOCAL_MODEL, "tier": ModelTier.TIER_0_LOCAL, "provider": "ollama"},
    ]


def micro_chain() -> List[Dict]:
    return [
        {"model": MICRO_MODEL, "tier": ModelTier.TIER_1_MICRO, "provider": MICRO_PROVIDER},
        {"model": LOCAL_MODEL, "tier": ModelTier.TIER_0_LOCAL, "provider": "ollama"},
    ]


def airgap_chain() -> List[Dict]:
    return [{"model": LOCAL_MODEL, "tier": ModelTier.TIER_0_LOCAL, "provider": "ollama"}]
