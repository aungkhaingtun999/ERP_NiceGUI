# ==============================================================================
# tests/conftest.py
# ERP ENTERPRISE TEST CONFIGURATION
#
# Purpose:
# - Make project root importable in GitHub Actions
# - Prevent Streamlit application startup during unit tests
# - Provide a clean test environment
# ==============================================================================

import os
import sys


# ==============================================================================
# PROJECT ROOT
# ==============================================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


if PROJECT_ROOT not in sys.path:

    sys.path.insert(
        0,
        PROJECT_ROOT
    )


# ==============================================================================
# TEST ENVIRONMENT
# ==============================================================================

os.environ.setdefault(
    "ERP_TEST_MODE",
    "1"
)