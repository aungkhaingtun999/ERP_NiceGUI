# ==============================================================================
# erp_core/services/audit_service.py
# ERP ENTERPRISE AUDIT SERVICE
# VERSION 1.0 PRODUCTION
# ==============================================================================


from typing import (
    Optional,
    Any,
    Dict
)


from datetime import (
    datetime,
    timezone
)


from ..config import (
    Tables
)


from ..base_repo import (
    validate_uuid,
    db
)





# ==============================================================================
# AUDIT SERVICE CLASS
# ==============================================================================


class AuditService:


    def __init__(
        self,
        client: Any
    ):

        self.client = client





    # --------------------------------------------------------------------------
    # CREATE AUDIT LOG
    # --------------------------------------------------------------------------

    def create_audit_log(
        self,
        action: str,
        details: Any,
        user_id: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[Any] = None

    ) -> bool:


        try:


            payload = {


                "action":

                    str(
                        action
                    ),



                "details":

                    str(
                        details
                    ),



                "user_id":

                    validate_uuid(
                        user_id
                    ),



                "table_name":

                    table_name,



                "record_id":

                    record_id,



                "created_at":

                    datetime
                    .now(
                        timezone.utc
                    )
                    .isoformat()

            }



            result = (

                self.client

                .table(
                    Tables.AUDIT_LOGS
                )

                .insert(
                    payload
                )

                .execute()

            )



            return bool(
                result.data
            )



        except Exception as e:


            print(
                f"[AUDIT SERVICE ERROR] {e}"
            )


            return False





# ==============================================================================
# MODULE LEVEL FUNCTION
# Compatibility Layer
# Required by:
# from erp_core.services.audit_service import create_audit_log
# ==============================================================================


def create_audit_log(
    action: str,
    details: Any,
    user_id: Optional[str] = None,
    table_name: Optional[str] = None,
    record_id: Optional[Any] = None

) -> bool:


    service = AuditService(
        db
    )


    return service.create_audit_log(

        action=action,

        details=details,

        user_id=user_id,

        table_name=table_name,

        record_id=record_id

    )
