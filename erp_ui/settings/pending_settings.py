# ==============================================================================
# erp_ui/settings/pending_settings.py
# ERP PENDING SETTINGS LOADER
# ==============================================================================

import pandas as pd

from erp_core.base_repo import db


def get_pending_settings_df():

    try:

        result = (
            db()
            .table("settings_change_requests")
            .select(
                """
                id,
                setting_key,
                old_value,
                new_value,
                reason,
                status,
                requested_by,
                created_at
                """
            )
            .eq("status", "PENDING")
            .order("created_at", desc=True)
            .execute()
        )

        return pd.DataFrame(result.data or [])

    except Exception as e:

        print("PENDING SETTINGS LOAD ERROR:", e)

        return pd.DataFrame()
