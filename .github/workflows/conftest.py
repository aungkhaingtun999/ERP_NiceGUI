# ==============================================================================
# conftest.py
# ERP ENTERPRISE TEST CONFIGURATION
#
# Purpose:
# - Prevent Streamlit secrets errors during pytest collection
# - Allow ERP Core modules to import in CI/CD
# - No real Supabase credentials required for unit tests
# ==============================================================================

import os


# ==============================================================================
# CI TEST ENVIRONMENT
# ==============================================================================

os.environ.setdefault(
    "ERP_TEST_MODE",
    "1"
)


# ==============================================================================
# STREAMLIT SECRET SAFETY
#
# Some ERP Core modules access:
#
#     st.secrets["SUPABASE_URL"]
#     st.secrets["SUPABASE_KEY"]
#
# during module import.
#
# Provide harmless test values so pytest collection does not fail.
# ==============================================================================

import streamlit as st


class TestSecrets(dict):
    """
    Minimal Streamlit-compatible secrets container
    for CI unit tests.
    """

    def __getitem__(self, key):

        if key == "SUPABASE_URL":
            return os.getenv(
                "SUPABASE_URL",
                "https://test.supabase.local"
            )

        if key == "SUPABASE_KEY":
            return os.getenv(
                "SUPABASE_KEY",
                "test-key"
            )

        if key == "SUPABASE_SERVICE_ROLE_KEY":
            return os.getenv(
                "SUPABASE_SERVICE_ROLE_KEY",
                "test-service-role-key"
            )

        return super().get(key)


# ==============================================================================
# INSTALL TEST SECRETS
# ==============================================================================

try:

    st.secrets._secrets = TestSecrets()

except Exception:
    pass


# ==============================================================================
# PYTEST CONFIGURATION
# ==============================================================================

def pytest_configure(config):

    config.addinivalue_line(
        "markers",
        "unit: isolated unit test"
    )

    config.addinivalue_line(
        "markers",
        "integration: integration test requiring external services"
    )


# ==============================================================================
# END
# ==============================================================================
