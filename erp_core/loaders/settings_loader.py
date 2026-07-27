# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v30
# ==============================================================================


from ..base_repo import (
    db,
    log_error
)


from ..config import (
    Tables
)





def get_setting(
    key: str,
    default=None
):
    """
    ERP Settings Reader
    """

    try:

        result = (
    db()
    .table(
        Tables.SETTINGS
    )
    .select("*")
    .eq(
        "key",
        key
    )
    .order(
        "created_at",
        desc=True
    )
    .limit(1)
    .execute()
)


    if result.data:

    return result.data[0].get(
        "value",
        default
    )


        if result.data:

            return result.data.get(
                "value",
                default
            )


    except Exception as e:

        log_error(
            f"get_setting error: {e}"
        )


    return default
