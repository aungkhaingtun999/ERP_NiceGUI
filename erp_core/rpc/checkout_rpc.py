# ==============================================================================
# erp_core/rpc/checkout_rpc.py
# ERP ENTERPRISE CHECKOUT RPC ENGINE v13.0
#
# Responsibilities:
# - Validate checkout request
# - Normalize cart payload
# - Validate numeric values
# - Call Supabase RPC
# - Normalize RPC response safely
# - Refresh ERP cache after successful checkout
#
# Database Function:
#
# checkout_sale_rpc(
#     p_cart,
#     p_paid_amount,
#     p_warehouse_id,
#     p_cashier_id,
#     p_counter_id,
#     p_payment_method,
#     p_tax_rate,
#     p_discount
# )
#
# Architecture:
#
# POS
#   ↓
# erp_core.rpc.checkout_rpc
#   ↓
# Supabase RPC
#   ↓
# checkout_sale_rpc
#
# IMPORTANT:
# - This Python wrapper does NOT calculate stock.
# - This Python wrapper does NOT calculate FIFO / FEFO.
# - Database RPC remains the transaction source of truth.
# ==============================================================================


from typing import (
    Any,
    Dict,
    List,
    Optional,
)


# ==============================================================================
# DATABASE
# ==============================================================================

from ..base_repo import (
    db,
)


# ==============================================================================
# CONFIG / LOGGING
#
# IMPORTANT:
# log_error is owned by config.py.
# Do not import log_error from base_repo.
# ==============================================================================

from ..config import (
    CACHE_KEYS,
    log_error,
)


# ==============================================================================
# CACHE
# ==============================================================================

from ..context import (
    CacheManager,
)


# ==============================================================================
# SAFE CONVERTERS
# ==============================================================================


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.

    Invalid values return default.
    """

    try:

        if value is None:

            return float(default)

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return float(default)


# ------------------------------------------------------------------------------


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Safely convert a value to int.

    Invalid values return default.
    """

    try:

        if value is None:

            return int(default)

        return int(value)

    except (
        TypeError,
        ValueError,
    ):

        return int(default)


# ==============================================================================
# CART NORMALIZER
# ==============================================================================


def normalize_cart(
    cart: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Normalize POS cart into the exact payload expected by
    checkout_sale_rpc.

    Input example:

        {
            "id": 10,
            "qty": 2,
            "selling_price": 1500
        }

    Output:

        {
            "id": 10,
            "qty": 2,
            "selling_price": 1500.0
        }

    Invalid items are skipped.
    """

    result: List[Dict[str, Any]] = []

    if not isinstance(
        cart,
        list,
    ):

        return result


    for item in cart:

        # ----------------------------------------------------------------------
        # Item must be a dictionary
        # ----------------------------------------------------------------------

        if not isinstance(
            item,
            dict,
        ):

            continue


        # ----------------------------------------------------------------------
        # Product ID
        # ----------------------------------------------------------------------

        product_id = safe_int(
            item.get("id"),
            0,
        )

        if product_id <= 0:

            continue


        # ----------------------------------------------------------------------
        # Quantity
        # ----------------------------------------------------------------------

        qty = safe_int(
            item.get(
                "qty",
                0,
            ),
            0,
        )

        if qty <= 0:

            continue


        # ----------------------------------------------------------------------
        # Selling price
        #
        # Support both:
        #
        # selling_price
        # unit_price
        # ----------------------------------------------------------------------

        selling_price = safe_float(
            item.get(
                "selling_price",
                item.get(
                    "unit_price",
                    0,
                ),
            ),
            0.0,
        )

        if selling_price < 0:

            continue


        # ----------------------------------------------------------------------
        # Normalized item
        # ----------------------------------------------------------------------

        result.append(
            {
                "id":
                    product_id,

                "qty":
                    qty,

                "selling_price":
                    selling_price,
            }
        )


    return result


# ==============================================================================
# CACHE REFRESH
# ==============================================================================


def refresh_checkout_cache() -> None:
    """
    Bump ERP cache versions after successful checkout.

    Checkout changes:
    - Inventory
    - Product stock
    - Sales

    CacheManager only changes version numbers.
    It does not directly manipulate database data.
    """

    # --------------------------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------------------------

    try:

        CacheManager.bump(
            CACHE_KEYS["inventory"]
        )

    except Exception as e:

        log_error(
            message="Checkout inventory cache refresh failed.",
            exception=e,
        )


    # --------------------------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------------------------

    try:

        CacheManager.bump(
            CACHE_KEYS["products"]
        )

    except Exception as e:

        log_error(
            message="Checkout product cache refresh failed.",
            exception=e,
        )


    # --------------------------------------------------------------------------
    # SALES
    # --------------------------------------------------------------------------

    try:

        CacheManager.bump(
            CACHE_KEYS["sales"]
        )

    except Exception as e:

        log_error(
            message="Checkout sales cache refresh failed.",
            exception=e,
        )


# ==============================================================================
# RPC RESPONSE NORMALIZER
# ==============================================================================


def _normalize_rpc_response(
    result: Any,
) -> Dict[str, Any]:
    """
    Normalize different Supabase RPC response shapes.

    Supported:

        dict
        [dict]
        list
        scalar
        None
    """

    # --------------------------------------------------------------------------
    # EMPTY
    # --------------------------------------------------------------------------

    if result is None:

        return {
            "success":
                False,

            "message":
                "Empty RPC response.",
        }


    # --------------------------------------------------------------------------
    # DICT
    # --------------------------------------------------------------------------

    if isinstance(
        result,
        dict,
    ):

        return result


    # --------------------------------------------------------------------------
    # LIST
    # --------------------------------------------------------------------------

    if isinstance(
        result,
        list,
    ):

        # Supabase may return:
        #
        # [
        #     {
        #         "success": true
        #     }
        # ]

        if (
            len(result) == 1
            and isinstance(
                result[0],
                dict,
            )
        ):

            return result[0]


        # Multiple rows / records

        return {
            "success":
                True,

            "data":
                result,
        }


    # --------------------------------------------------------------------------
    # OTHER
    # --------------------------------------------------------------------------

    return {
        "success":
            True,

        "data":
            result,
    }


# ==============================================================================
# CHECKOUT RPC
# ==============================================================================


def checkout_sale_rpc(
    cart: List[Dict[str, Any]],
    paid_amount: Any = 0,
    warehouse_id: Optional[int] = None,
    cashier_id: Optional[str] = None,
    counter_id: int = 1,
    payment_method: str = "CASH",
    tax_rate: Any = 0,
    discount: Any = 0,
) -> Dict[str, Any]:
    """
    Execute checkout_sale_rpc through Supabase.

    Python responsibilities:
    - Validate request
    - Normalize payload
    - Call database RPC
    - Normalize response
    - Refresh cache after success

    Database responsibilities:
    - Transaction
    - Stock deduction
    - Sale creation
    - Sale items
    - Inventory accounting
    - FIFO / FEFO logic where applicable
    - Payment validation
    """


    try:

        # ======================================================================
        # BASIC VALIDATION
        # ======================================================================

        if not cart:

            return {
                "success":
                    False,

                "message":
                    "Cart is empty.",
            }


        if warehouse_id is None:

            return {
                "success":
                    False,

                "message":
                    "Warehouse not selected.",
            }


        normalized_warehouse_id = safe_int(
            warehouse_id,
            0,
        )

        if normalized_warehouse_id <= 0:

            return {
                "success":
                    False,

                "message":
                    "Invalid warehouse ID.",
            }


        if not cashier_id:

            return {
                "success":
                    False,

                "message":
                    "Cashier not found.",
            }


        # ======================================================================
        # NORMALIZE CART
        # ======================================================================

        rpc_cart = normalize_cart(
            cart
        )


        if not rpc_cart:

            return {
                "success":
                    False,

                "message":
                    "Invalid cart data.",
            }


        # ======================================================================
        # NUMERIC VALUES
        # ======================================================================

        normalized_paid_amount = safe_float(
            paid_amount,
            0.0,
        )


        normalized_tax_rate = safe_float(
            tax_rate,
            0.0,
        )


        normalized_discount = safe_float(
            discount,
            0.0,
        )


        normalized_counter_id = safe_int(
            counter_id,
            1,
        )


        # ----------------------------------------------------------------------
        # Basic numeric validation
        # ----------------------------------------------------------------------

        if normalized_paid_amount < 0:

            return {
                "success":
                    False,

                "message":
                    "Paid amount cannot be negative.",
            }


        if normalized_tax_rate < 0:

            return {
                "success":
                    False,

                "message":
                    "Tax rate cannot be negative.",
            }


        if normalized_discount < 0:

            return {
                "success":
                    False,

                "message":
                    "Discount cannot be negative.",
            }


        if normalized_counter_id <= 0:

            return {
                "success":
                    False,

                "message":
                    "Invalid counter ID.",
            }


        # ======================================================================
        # PAYMENT METHOD
        # ======================================================================

        normalized_payment_method = str(
            payment_method
            if payment_method is not None
            else "CASH"
        ).strip().upper()


        if not normalized_payment_method:

            normalized_payment_method = "CASH"


        # ======================================================================
        # CASHIER
        # ======================================================================

        normalized_cashier_id = str(
            cashier_id
        ).strip()


        if not normalized_cashier_id:

            return {
                "success":
                    False,

                "message":
                    "Cashier not found.",
            }


        # ======================================================================
        # RPC PAYLOAD
        # ======================================================================

        payload: Dict[str, Any] = {

            "p_cart":
                rpc_cart,

            "p_paid_amount":
                normalized_paid_amount,

            "p_warehouse_id":
                normalized_warehouse_id,

            "p_cashier_id":
                normalized_cashier_id,

            "p_counter_id":
                normalized_counter_id,

            "p_payment_method":
                normalized_payment_method,

            "p_tax_rate":
                normalized_tax_rate,

            "p_discount":
                normalized_discount,
        }


        # ======================================================================
        # EXECUTE SUPABASE RPC
        # ======================================================================

        response = (
            db()
            .rpc(
                "checkout_sale_rpc",
                payload,
            )
            .execute()
        )


        # ======================================================================
        # EXTRACT RESPONSE DATA
        # ======================================================================

        result = getattr(
            response,
            "data",
            None,
        )


        # ======================================================================
        # NORMALIZE RESPONSE
        # ======================================================================

        normalized_result = _normalize_rpc_response(
            result
        )


        # ======================================================================
        # CACHE REFRESH
        # ======================================================================
        #
        # IMPORTANT:
        #
        # Only refresh cache when database RPC explicitly reports success.
        #
        # Do NOT refresh cache merely because a list/scalar was returned.
        #
        # ======================================================================

        if normalized_result.get(
            "success",
            False,
        ):

            refresh_checkout_cache()


        return normalized_result


    # ==========================================================================
    # ERROR HANDLING
    # ==========================================================================

    except Exception as e:

        log_error(
            message=
                "checkout_sale_rpc execution failed.",
            exception=e,
            rpc=
                "checkout_sale_rpc",
        )


        return {
            "success":
                False,

            "message":
                str(e),

            "data":
                None,
        }


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================


__all__ = [

    "safe_float",

    "safe_int",

    "normalize_cart",

    "refresh_checkout_cache",

    "checkout_sale_rpc",

]
