"""
AEGIS-0 Tavily Freshness & Deprecated API Engine (PS-06 Integration)
Canonical Package Module.
"""

from .freshness_engine import (
    FreshnessEngine,
    extract_code_claims,
    verify_claim_freshness,
    auto_patch_code,
)

__all__ = [
    "FreshnessEngine",
    "extract_code_claims",
    "verify_claim_freshness",
    "auto_patch_code",
]
