# ==============================================================================
# erp_pages/pos/checkout.py
# ERP ENTERPRISE POS CHECKOUT ENGINE v13.0
#
# SINGLE SOURCE OF TRUTH
#
# IMPORTANT:
#   Supabase checkout_sale_rpc owns:
#       subtotal
#       tax
#       discount
#       total
#       paid_amount
#       change_amount
#
#   Python NEVER recalculates the final sale total.
# ==============================================================================

from datetime import datetime

from erp_core import checkout_sale_rpc

from erp_core.context import CacheManager

from erp_core.config import CACHE_KEYS

from .engine import get_default_tax_rate


# ==============================================================================
# SAFE NUMBER
# ==============================================================================

def safe_float(value, default=0):

    try:
        if value is None:
            return float(default)

        return float(value)

    except Exception:
        return float(default)


# ==============================================================================
# CART PAYLOAD
# ==============================================================================

def build_cart_payload(cart):

    payload = []

    for item in cart:

        payload.append({

            "id": int(
                item.get("id", 0)
            ),

            "qty": int(
                item.get("qty", 0)
            ),

            "selling_price": safe_float(
                item.get(
                    "selling_price",
                    item.get(
                        "unit_price",
                        0
                    )
                )
            )

        })

    return payload


# ==============================================================================
# RECEIPT BUILDER
#
# IMPORTANT:
# Final monetary totals MUST come from RPC.
# Python only builds line display data.
# ==============================================================================

def build_receipt_data(
    cart,
    rpc_data,
    paid_amount=None,
    tax_rate=None,
    discount=None
):

    if not isinstance(rpc_data, dict):
        rpc_data = {}


    # --------------------------------------------------------------------------
    # RPC IS THE AUTHORITY
    # --------------------------------------------------------------------------

    subtotal = safe_float(
        rpc_data.get("subtotal"),
        0
    )

    tax_amount = safe_float(
        rpc_data.get("tax"),
        0
    )

    discount_amount = safe_float(
        rpc_data.get("discount"),
        0
    )

    grand_total = safe_float(
        rpc_data.get("total"),
        0
    )

    paid = safe_float(
        rpc_data.get(
            "paid_amount",
            paid_amount
        ),
        0
    )

    change = safe_float(
        rpc_data.get("change"),
        rpc_data.get(
            "change_amount",
            max(0, paid - grand_total)
        )
    )

    rpc_tax_rate = safe_float(
        rpc_data.get(
            "tax_rate",
            tax_rate
        ),
        0
    )


    # --------------------------------------------------------------------------
    # ITEMS
    #
    # Line amounts are display-only.
    # They do NOT determine grand total.
    # --------------------------------------------------------------------------

    items = []

    for item in cart:

        price = safe_float(
            item.get(
                "selling_price",
                item.get(
                    "unit_price",
                    0
                )
            )
        )

        qty = int(
            item.get(
                "qty",
                0
            )
        )

        amount = price * qty

        items.append({

            "name": item.get(
                "name",
                "Unknown"
            ),

            "product_id": item.get(
                "id"
            ),

            "quantity": qty,

            "unit_price": price,

            "selling_price": price,

            "price_source": item.get(
                "price_source",
                "SYSTEM"
            ),

            "total": round(
                amount,
                2
            )

        })


    # --------------------------------------------------------------------------
    # INVOICE
    # --------------------------------------------------------------------------

    invoice_no = (

        rpc_data.get(
            "invoice_no"
        )

        or

        rpc_data.get(
            "invoice"
        )

        or

        (
            "INV-"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
        )

    )


    # --------------------------------------------------------------------------
    # RECEIPT DATA
    # --------------------------------------------------------------------------

    return {

        "invoice_no": invoice_no,

        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "cashier": "Admin",

        "items": items,

        # ----------------------------------------------------------------------
        # AUTHORITATIVE RPC VALUES
        # ----------------------------------------------------------------------

        "subtotal": round(
            subtotal,
            2
        ),

        "tax_rate": round(
            rpc_tax_rate,
            4
        ),

        "tax_amount": round(
            tax_amount,
            2
        ),

        "discount": round(
            discount_amount,
            2
        ),

        "grand_total": round(
            grand_total,
            2
        ),

        "paid": round(
            paid,
            2
        ),

        "change": round(
            change,
            2
        ),

        "sale_id": rpc_data.get(
            "sale_id"
        )

    }


# ==============================================================================
# PROCESS CHECKOUT
# ==============================================================================

def process_checkout(
    cart,
    paid_amount,
    warehouse_id,
    cashier_id,
    payment_method="CASH",
    discount=0,
    counter_id=None
):

    try:

        # ======================================================================
        # 1. CART VALIDATION
        # ======================================================================

        if not cart:

            return {
                "success": False,
                "message": "Cart is empty."
            }


        # ======================================================================
        # 2. TAX
        # ======================================================================

        tax_rate = get_default_tax_rate()


        # ======================================================================
        # 3. BUILD PAYLOAD
        # ======================================================================

        cart_payload = build_cart_payload(
            cart
        )


        # ======================================================================
        # 4. SUPABASE CHECKOUT RPC
        #
        # THIS IS THE ONLY TRANSACTION AUTHORITY.
        # ======================================================================

        result = checkout_sale_rpc(

            cart=cart_payload,

            paid_amount=paid_amount,

            warehouse_id=warehouse_id,

            cashier_id=cashier_id,

            counter_id=counter_id,

            payment_method=payment_method,

            tax_rate=tax_rate,

            discount=discount

        )


        # ======================================================================
        # 5. RPC FAILURE
        # ======================================================================

        if not isinstance(result, dict):

            return {
                "success": False,
                "message": "Invalid checkout RPC response."
            }


        if not result.get(
            "success",
            False
        ):

            return {

                "success": False,

                "message": result.get(
                    "message",
                    "Checkout failed."
                )

            }


        # ======================================================================
        # 6. RPC DATA
        # ======================================================================

        rpc_data = result.get(
            "data",
            {}
        )


        if isinstance(
            rpc_data,
            list
        ):

            rpc_data = (
                rpc_data[0]
                if rpc_data
                else {}
            )


        if not isinstance(
            rpc_data,
            dict
        ):

            return {

                "success": False,

                "message":
                    "Checkout succeeded but RPC returned invalid sale data."

            }


        # ======================================================================
        # 7. AUTHORITATIVE TOTAL VALIDATION
        #
        # Ensure RPC actually returned total.
        # ======================================================================

        required_fields = (
            "sale_id",
            "invoice_no",
            "subtotal",
            "tax",
            "discount",
            "total"
        )


        missing_fields = [

            field

            for field in required_fields

            if field not in rpc_data

        ]


        if missing_fields:

            return {

                "success": False,

                "message":
                    "Checkout RPC returned incomplete sale totals: "
                    + ", ".join(
                        missing_fields
                    )

            }


        # ======================================================================
        # 8. CACHE INVALIDATION
        # ======================================================================

        try:

            CacheManager.bump(
                CACHE_KEYS["inventory"]
            )

            CacheManager.bump(
                CACHE_KEYS["products"]
            )

            CacheManager.bump(
                CACHE_KEYS["sales"]
            )

        except Exception:

            pass


        # ======================================================================
        # 9. RECEIPT
        #
        # IMPORTANT:
        # No recalculation of grand total.
        # ======================================================================

        receipt_data = build_receipt_data(

            cart,

            rpc_data,

            paid_amount,

            tax_rate,

            discount

        )


        # ======================================================================
        # 10. FINAL RESULT
        # ======================================================================

        return {

            "success": True,

            "data": receipt_data

        }


    except Exception as e:

        return {

            "success": False,

            "message": str(e)

        }
