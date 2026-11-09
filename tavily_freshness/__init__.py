"""
AEGIS-0 Tavily Freshness Module Alias (allows import tavily_freshness)
"""

import sys
import os

# Link to tavily-freshness implementation
pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tavily-freshness"))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from freshness_engine import (
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
