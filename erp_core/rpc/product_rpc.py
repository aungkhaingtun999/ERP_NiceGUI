# ==============================================================================
# erp_core/rpc/product_rpc.py
# ERP ENTERPRISE PRODUCT RPC v2.0
#
# Product Master RPC Gateway
#
# Supports:
#     update_product_rpc
#
# Maker / Checker:
#     request_product_create_rpc
#     request_product_bulk_create_rpc
#     approve_product_create_rpc
#
# IMPORTANT:
#     Real product creation is NOT performed by request functions.
#
#     request_product_create_rpc()
#         -> product_create_requests
#         -> PENDING
#
#     request_product_bulk_create_rpc()
#         -> product_create_requests
#         -> PENDING
#
#     approve_product_create_rpc()
#         -> Supabase approve RPC
#         -> create_product_full()
#
# ==============================================================================


from ..base_repo import db, privileged_db, log_error


# ==============================================================================
# INTERNAL HELPERS
# ==============================================================================


def _get_client(privileged=False):

    """
    Return the appropriate Supabase client.

    Maker / Checker RPCs are server-side protected operations.
    Prefer privileged_db() for those RPC calls.

    update_product_rpc() keeps the existing normal db() behavior.
    """

    if privileged:

        return privileged_db()

    return db()


def _execute_rpc(client, function_name, params):

    """
    Execute a Supabase RPC and normalize the response.
    """

    try:

        result = (
            client
            .rpc(
                function_name,
                params
            )
            .execute()
        )

        return result.data

    except Exception as e:

        log_error(
            message=f"{function_name} failed",
            exception=e
        )

        return {
            "success": False,
            "status": "ERROR",
            "message": str(e)
        }


# ==============================================================================
# REQUEST PRODUCT CREATE
# MAKER
# ==============================================================================


def request_product_create_rpc(

    product_data,

    warehouse_id,

    initial_qty,

    reason,

    requested_by

):

    """
    Submit ONE product creation request.

    IMPORTANT:
        This function does NOT create a product.

    Database flow:

        request_product_create_rpc()
                    ↓
        product_create_requests
                    ↓
                  PENDING
                    ↓
              Checker Approval
    """

    if product_data is None:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Product data is required."
        }

    if warehouse_id is None:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Warehouse ID is required."
        }

    if requested_by is None:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Requester ID is required."
        }

    try:

        qty = int(initial_qty or 0)

    except Exception:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Initial quantity must be an integer."
        }

    if qty < 0:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Initial quantity cannot be negative."
        }

    params = {

        "p_product_data":
        product_data,

        "p_warehouse_id":
        int(warehouse_id),

        "p_initial_qty":
        qty,

        "p_reason":
        reason
        or "Product creation request",

        "p_requested_by":
        requested_by

    }

    return _execute_rpc(
        _get_client(privileged=True),
        "request_product_create_rpc",
        params
    )


# ==============================================================================
# REQUEST PRODUCT BULK CREATE
# MAKER
# ==============================================================================


def request_product_bulk_create_rpc(

    products,

    warehouse_id,

    initial_qty=0,

    reason="Product Master bulk import request",

    requested_by=None

):

    """
    Submit MULTIPLE product creation requests.

    IMPORTANT:
        This function does NOT create real products.

    Each product is passed to:

        request_product_create_rpc()

    inside the database bulk RPC.

    Product creation happens only after Checker approval.
    """

    if products is None:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Products are required."
        }

    if not isinstance(products, list):

        return {
            "success": False,
            "status": "ERROR",
            "message": "Products must be a list."
        }

    if len(products) == 0:

        return {
            "success": False,
            "status": "ERROR",
            "message": "No products supplied."
        }

    if warehouse_id is None:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Warehouse ID is required."
        }

    if requested_by is None:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Requester ID is required."
        }

    try:

        qty = int(initial_qty or 0)

    except Exception:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Initial quantity must be an integer."
        }

    if qty < 0:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Initial quantity cannot be negative."
        }

    params = {

        "p_products":
        products,

        "p_warehouse_id":
        int(warehouse_id),

        "p_initial_qty":
        qty,

        "p_reason":
        reason
        or "Product Master bulk import request",

        "p_requested_by":
        requested_by

    }

    return _execute_rpc(
        _get_client(privileged=True),
        "request_product_bulk_create_rpc",
        params
    )


# ==============================================================================
# APPROVE PRODUCT CREATE
# CHECKER
# ==============================================================================


def approve_product_create_rpc(

    request_id,

    checker_id

):

    """
    Approve ONE pending product creation request.

    IMPORTANT:

        Python does NOT call create_product_full() directly.

    Database flow:

        PENDING
           ↓
        Checker
           ↓
        approve_product_create_rpc()
           ↓
        create_product_full()
           ↓
        products
        warehouse_stock
        inventory_batches
        inventory_cost_layers
    """

    if request_id is None:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Request ID is required."
        }

    if checker_id is None:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Checker ID is required."
        }

    try:

        request_id = int(request_id)

    except Exception:

        return {
            "success": False,
            "status": "ERROR",
            "message": "Request ID must be an integer."
        }

    params = {

        "p_request_id":
        request_id,

        "p_checker_id":
        checker_id

    }

    return _execute_rpc(
        _get_client(privileged=True),
        "approve_product_create_rpc",
        params
    )


# ==============================================================================
# UPDATE PRODUCT
# ==============================================================================
#
# Existing Product Master update.
#
# This is NOT Maker-Checker product creation.
#
# Existing behavior is preserved:
#     Empty SKU     -> keep old SKU
#     Empty Barcode -> keep old Barcode
#
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

        # ==============================================================
        # LOAD OLD PRODUCT
        # ==============================================================

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
                int(product_id)
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

        # ==============================================================
        # KEEP OLD VALUES
        # ==============================================================

        final_sku = (

            str(sku).strip()

            if sku and str(sku).strip()

            else old_data.get("sku")

        )

        final_barcode = (

            str(barcode).strip()

            if barcode and str(barcode).strip()

            else old_data.get("barcode")

        )

        final_min_stock = (

            int(minimum_stock)

            if minimum_stock is not None

            else int(
                old_data.get(
                    "minimum_stock",
                    0
                )
            )

        )

        # ==============================================================
        # UPDATE PAYLOAD
        # ==============================================================

        payload = {

            "name":
            str(name).strip(),

            "sku":
            final_sku,

            "barcode":
            final_barcode,

            "purchase_price":
            float(purchase_price or 0),

            "selling_price":
            float(selling_price or 0),

            "minimum_stock":
            final_min_stock,

            "unit":
            str(unit).strip()
            if unit
            else "pcs",

            "notes":
            notes,

            "is_active":
            bool(is_active)

        }

        print(
            "ERP PRODUCT UPDATE PAYLOAD =",
            payload
        )

        # ==============================================================
        # UPDATE
        # ==============================================================

        client.table("products") \
            .update(payload) \
            .eq(
                "id",
                int(product_id)
            ) \
            .execute()

        # ==============================================================
        # VERIFY
        # ==============================================================

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
                notes
                """

            )

            .eq(
                "id",
                int(product_id)
            )

            .maybe_single()

            .execute()

        )

        return {

            "success":
            True,

            "message":
            "Product updated successfully",

            "data":
            verify.data

        }

    except Exception as e:

        log_error(

            message=
            "update_product_rpc failed",

            exception=e

        )

        return {

            "success":
            False,

            "message":
            str(e)

        }
