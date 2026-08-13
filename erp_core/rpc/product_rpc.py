# ==============================================================================
# erp_core/rpc/product_rpc.py
# ERP ENTERPRISE PRODUCT RPC v2.0
#
# PRODUCT MASTER + MAKER CHECKER
#
# Supported RPCs:
#
#   update_product_rpc
#
#   request_product_create_rpc
#
#   request_product_bulk_create_rpc
#
#   approve_product_create_rpc
#
# Database Functions:
#
#   request_product_create_rpc(
#       p_product_data jsonb,
#       p_warehouse_id bigint,
#       p_initial_qty integer,
#       p_reason text,
#       p_requested_by uuid
#   )
#
#   request_product_bulk_create_rpc(
#       p_products jsonb,
#       p_warehouse_id bigint,
#       p_initial_qty numeric,
#       p_reason text,
#       p_requested_by uuid
#   )
#
#   approve_product_create_rpc(
#       p_request_id bigint,
#       p_checker_id uuid
#   )
#
# ==============================================================================


from typing import (
    Any,
    Dict,
    Optional,
)


from ..base_repo import (
    db,
    privileged_db,
    log_error,
)


# ==============================================================================
# SAFE HELPERS
# ==============================================================================


def _safe_int(value, default=0):

    try:
        return int(value)

    except Exception:
        return int(default)


def _safe_float(value, default=0):

    try:
        return float(value)

    except Exception:
        return float(default)


def _safe_text(value, default=""):

    if value is None:
        return default

    return str(value).strip()


# ==============================================================================
# UPDATE PRODUCT
# ==============================================================================


def update_product_rpc(

    product_id,

    name,

    sku,

    barcode,

    purchase_price,

    selling_price,

    minimum_stock,

    unit,

    notes,

    is_active=True

):

    try:

        client = db()

        # ------------------------------------------------------------------
        # LOAD OLD PRODUCT
        # ------------------------------------------------------------------

        old_result = (

            client

            .table("products")

            .select(
                """
                id,
                sku,
                barcode,
                minimum_stock,
                unit,
                notes
                """
            )

            .eq(
                "id",
                _safe_int(product_id)
            )

            .maybe_single()

            .execute()
        )

        old_data = old_result.data

        if not old_data:

            return {
                "success": False,
                "message":
                    f"Product ID {product_id} not found"
            }

        # ------------------------------------------------------------------
        # KEEP OLD SKU
        # ------------------------------------------------------------------

        incoming_sku = _safe_text(sku)

        if incoming_sku:

            final_sku = incoming_sku

        else:

            final_sku = old_data.get("sku")

        # ------------------------------------------------------------------
        # KEEP OLD BARCODE
        # ------------------------------------------------------------------

        incoming_barcode = _safe_text(barcode)

        if incoming_barcode:

            final_barcode = incoming_barcode

        else:

            final_barcode = old_data.get("barcode")

        # ------------------------------------------------------------------
        # MINIMUM STOCK
        # ------------------------------------------------------------------

        if minimum_stock is not None:

            final_minimum_stock = _safe_int(
                minimum_stock
            )

        else:

            final_minimum_stock = _safe_int(
                old_data.get(
                    "minimum_stock",
                    0
                )
            )

        # ------------------------------------------------------------------
        # PAYLOAD
        # ------------------------------------------------------------------

        payload = {

            "name":
                _safe_text(name),

            "sku":
                final_sku,

            "barcode":
                final_barcode,

            "purchase_price":
                _safe_float(
                    purchase_price
                ),

            "selling_price":
                _safe_float(
                    selling_price
                ),

            "minimum_stock":
                final_minimum_stock,

            "unit":
                _safe_text(
                    unit,
                    "pcs"
                ) or "pcs",

            "notes":
                notes,

            "is_active":
                bool(is_active),

        }

        print(
            "ERP PRODUCT UPDATE PAYLOAD =",
            payload
        )

        # ------------------------------------------------------------------
        # UPDATE
        # ------------------------------------------------------------------

        result = (

            client

            .table("products")

            .update(payload)

            .eq(
                "id",
                _safe_int(product_id)
            )

            .execute()
        )

        # ------------------------------------------------------------------
        # VERIFY
        # ------------------------------------------------------------------

        verify = (

            client

            .table("products")

            .select(
                """
                id,
                name,
                sku,
                barcode,
                purchase_price,
                selling_price,
                minimum_stock,
                unit,
                notes,
                is_active
                """
            )

            .eq(
                "id",
                _safe_int(product_id)
            )

            .maybe_single()

            .execute()
        )

        return {

            "success": True,

            "message":
                "Product updated successfully",

            "data":
                verify.data

        }

    except Exception as e:

        log_error(
            message=
                "update_product_rpc failed",
            exception=e,
            rpc=
                "update_product_rpc"
        )

        return {

            "success": False,

            "message":
                str(e)

        }


# ==============================================================================
# REQUEST PRODUCT CREATE
# ==============================================================================
#
# MAKER
#
# This function DOES NOT create products directly.
#
# It only creates an approval request.
#
# ==============================================================================


def request_product_create_rpc(

    product_data: Dict[str, Any],

    warehouse_id,

    initial_qty,

    reason,

    requested_by

):

    try:

        if not product_data:

            return {
                "success": False,
                "message":
                    "Product data is required."
            }

        if not requested_by:

            return {
                "success": False,
                "message":
                    "Requester ID is required."
            }

        payload = {

            "p_product_data":
                product_data,

            "p_warehouse_id":
                _safe_int(
                    warehouse_id
                ),

            "p_initial_qty":
                _safe_int(
                    initial_qty
                ),

            "p_reason":
                _safe_text(
                    reason
                ),

            "p_requested_by":
                requested_by,

        }

        print(
            "ERP PRODUCT CREATE REQUEST =",
            payload
        )

        # ------------------------------------------------------------------
        # SERVER SIDE RPC
        # ------------------------------------------------------------------

        client = privileged_db()

        response = (

            client

            .rpc(
                "request_product_create_rpc",
                payload
            )

            .execute()
        )

        result = getattr(
            response,
            "data",
            response
        )

        # ------------------------------------------------------------------
        # NORMALIZE
        # ------------------------------------------------------------------

        if isinstance(result, dict):

            return result

        if isinstance(result, list):

            if (
                len(result) == 1
                and isinstance(
                    result[0],
                    dict
                )
            ):

                return result[0]

            return {
                "success": True,
                "data": result
            }

        return {
            "success": True,
            "data": result
        }

    except Exception as e:

        log_error(
            message=
                "request_product_create_rpc failed",
            exception=e,
            rpc=
                "request_product_create_rpc"
        )

        return {

            "success": False,

            "message":
                str(e)

        }


# ==============================================================================
# REQUEST PRODUCT BULK CREATE
# ==============================================================================
#
# MAKER
#
# Creates approval requests.
#
# DOES NOT directly create products.
#
# ==============================================================================


def request_product_bulk_create_rpc(

    products,

    warehouse_id,

    initial_qty,

    reason,

    requested_by

):

    try:

        if not products:

            return {
                "success": False,
                "message":
                    "Product list is empty."
            }

        if not requested_by:

            return {
                "success": False,
                "message":
                    "Requester ID is required."
            }

        if not isinstance(
            products,
            list
        ):

            return {
                "success": False,
                "message":
                    "Products must be a list."
            }

        payload = {

            "p_products":
                products,

            "p_warehouse_id":
                _safe_int(
                    warehouse_id
                ),

            "p_initial_qty":
                _safe_float(
                    initial_qty
                ),

            "p_reason":
                _safe_text(
                    reason
                ),

            "p_requested_by":
                requested_by,

        }

        print(
            "ERP BULK PRODUCT CREATE REQUEST =",
            payload
        )

        # ------------------------------------------------------------------
        # SERVER SIDE RPC
        # ------------------------------------------------------------------

        client = privileged_db()

        response = (

            client

            .rpc(
                "request_product_bulk_create_rpc",
                payload
            )

            .execute()
        )

        result = getattr(
            response,
            "data",
            response
        )

        # ------------------------------------------------------------------
        # NORMALIZE
        # ------------------------------------------------------------------

        if isinstance(result, dict):

            return result

        if isinstance(result, list):

            if (
                len(result) == 1
                and isinstance(
                    result[0],
                    dict
                )
            ):

                return result[0]

            return {
                "success": True,
                "data": result
            }

        return {
            "success": True,
            "data": result
        }

    except Exception as e:

        log_error(
            message=
                "request_product_bulk_create_rpc failed",
            exception=e,
            rpc=
                "request_product_bulk_create_rpc"
        )

        return {

            "success": False,

            "message":
                str(e)

        }


# ==============================================================================
# APPROVE PRODUCT CREATE
# ==============================================================================
#
# CHECKER
#
# IMPORTANT:
# p_request_id
# p_checker_id
#
# The actual database function performs the final product creation.
#
# ==============================================================================


def approve_product_create_rpc(

    request_id,

    checker_id

):

    try:

        if not request_id:

            return {
                "success": False,
                "message":
                    "Request ID is required."
            }

        if not checker_id:

            return {
                "success": False,
                "message":
                    "Checker ID is required."
            }

        payload = {

            "p_request_id":
                _safe_int(
                    request_id
                ),

            "p_checker_id":
                checker_id,

        }

        print(
            "ERP PRODUCT APPROVAL REQUEST =",
            payload
        )

        # ------------------------------------------------------------------
        # SERVER SIDE RPC
        # ------------------------------------------------------------------

        client = privileged_db()

        response = (

            client

            .rpc(
                "approve_product_create_rpc",
                payload
            )

            .execute()
        )

        result = getattr(
            response,
            "data",
            response
        )

        # ------------------------------------------------------------------
        # NORMALIZE
        # ------------------------------------------------------------------

        if isinstance(result, dict):

            return result

        if isinstance(result, list):

            if (
                len(result) == 1
                and isinstance(
                    result[0],
                    dict
                )
            ):

                return result[0]

            return {
                "success": True,
                "data": result
            }

        return {
            "success": True,
            "data": result
        }

    except Exception as e:

        log_error(
            message=
                "approve_product_create_rpc failed",
            exception=e,
            rpc=
                "approve_product_create_rpc"
        )

        return {

            "success": False,

            "message":
                str(e)

        }


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================


__all__ = [

    "update_product_rpc",

    "request_product_create_rpc",

    "request_product_bulk_create_rpc",

    "approve_product_create_rpc",

]
