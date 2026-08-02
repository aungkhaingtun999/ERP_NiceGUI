# ==============================================================================
# CATEGORY LOADER
# ERP ENTERPRISE
# ==============================================================================


from ..base_repo import db, log_error



def get_categories():

    try:

        result = (
            db()
            .table("categories")
            .select("*")
            .order("name")
            .execute()
        )


        return result.data or []


    except Exception as e:

        log_error(
            message="Category loading failed",
            exception=e
        )

        return []
