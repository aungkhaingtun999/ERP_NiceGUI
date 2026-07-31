# ==============================================================================
# erp_core/repositories/price_import_repo.py
#
# ERP ENTERPRISE PRICE IMPORT REPOSITORY v1.0
#
# Responsibilities:
# - Price Import Queue Database Access
# - Insert Import Records
# - Read Pending Imports
# - Update Import Status
#
# ==============================================================================


from typing import (
    Dict,
    List,
    Any
)


from erp_core.base_repo import (
    db,
    safe_execute,
    serialize_json
)


from erp_core.config import (
    Tables
)





# ==============================================================================
# TABLE NAME
# ==============================================================================


PRICE_IMPORT_TABLE = "price_import_queue"





# ==============================================================================
# CREATE IMPORT QUEUE RECORD
# ==============================================================================


def create_price_import(
    data: Dict[str, Any]
):


    def action():

        result = (

            db()
            .table(
                PRICE_IMPORT_TABLE
            )
            .insert(
                serialize_json(
                    data
                )
            )
            .execute()

        )


        if result.data:

            return result.data[0]


        return None



    return safe_execute(
        action,
        "Create price import failed"
    )







# ==============================================================================
# GET PENDING IMPORTS
# ==============================================================================


def get_pending_price_imports() -> List[Dict]:


    def action():

        result = (

            db()
            .table(
                PRICE_IMPORT_TABLE
            )
            .select(
                "*"
            )
            .eq(
                "status",
                "PENDING"
            )
            .order(
                "created_at",
                desc=True
            )
            .execute()

        )


        return result.data or []



    return safe_execute(
        action,
        "Load pending price imports failed"
    ) or []








# ==============================================================================
# GET ALL IMPORT HISTORY
# ==============================================================================


def get_price_import_history(
    limit=100
):


    def action():

        result = (

            db()
            .table(
                PRICE_IMPORT_TABLE
            )
            .select(
                "*"
            )
            .order(
                "created_at",
                desc=True
            )
            .limit(
                limit
            )
            .execute()

        )


        return result.data or []



    return safe_execute(
        action,
        "Load price import history failed"
    ) or []









# ==============================================================================
# UPDATE STATUS
# ==============================================================================


def update_price_import_status(

    import_id: int,

    status: str,

    user_id=None,

    reason=None

):


    def action():


        payload = {


            "status":
                status

        }



        if user_id:


            payload[
                "approved_by"
            ] = user_id



        if status == "APPROVED":


            payload[
                "approved_at"
            ] = "now()"



        if reason:


            payload[
                "reason"
            ] = reason





        result = (

            db()
            .table(
                PRICE_IMPORT_TABLE
            )
            .update(
                serialize_json(
                    payload
                )
            )
            .eq(
                "id",
                import_id
            )
            .execute()

        )



        return result.data



    return safe_execute(
        action,
        "Update price import status failed"
    )








# ==============================================================================
# DELETE IMPORT RECORD
# ==============================================================================


def delete_price_import(
    import_id: int
):


    def action():

        result = (

            db()
            .table(
                PRICE_IMPORT_TABLE
            )
            .delete()
            .eq(
                "id",
                import_id
            )
            .execute()

        )


        return result.data



    return safe_execute(
        action,
        "Delete price import failed"
    )






# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "create_price_import",

    "get_pending_price_imports",

    "get_price_import_history",

    "update_price_import_status",

    "delete_price_import"

]