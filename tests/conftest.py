"""
Shared pytest configuration.

Approved write actions are applied to the orchestrator's workspace. Point it
at a throwaway directory before any test imports orchestrator.main, so test
runs never write into the developer's checkout.
"""

import os
import tempfile

_TEST_WORKSPACE = tempfile.mkdtemp(prefix="aegis-test-workspace-")
os.environ["AEGIS_WORKSPACE_ROOT"] = _TEST_WORKSPACE
