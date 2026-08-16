# ==============================================================================
# erp_pages/pos/checkout.py
# ERP ENTERPRISE POS CHECKOUT ENGINE v13.0 FINAL
#
# Responsibilities:
# - Cart validation
# - RPC checkout bridge
# - Canonical RPC totals
# - Receipt data builder
# - Cache refresh
#
# IMPORTANT:
# Supabase checkout_sale_rpc is the canonical source for:
#   subtotal
#   tax
#   discount
#   total
#   paid_amount
#   change
#
# ==============================================================================


from datetime import datetime


from erp_core import checkout_sale_rpc


from erp_core.context import (
    CacheManager
)


from erp_core.config import (
    CACHE_KEYS
)


from .engine import (
    get_default_tax_rate
)


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

        product_id = item.get(
            "id",
            0
        )

        qty = item.get(
            "qty",
            0
        )

        selling_price = item.get(
            "selling_price",
            item.get(
                "unit_price",
                0
            )
        )

        payload.append(
            {
                "id": int(product_id),

                "qty": int(qty),

                "selling_price": safe_float(
                    selling_price
                )
            }
        )

    return payload


# ==============================================================================
# RECEIPT BUILDER
# ==============================================================================


def build_receipt_data(
    cart,
    rpc_data,
    paid_amount,
    tax_rate,
    discount
):

    # ==========================================================================
    # LOCAL FALLBACK CALCULATION
    #
    # Used only if RPC does not return a value.
    # RPC remains the canonical source.
    # ==========================================================================

    calculated_subtotal = 0

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

        calculated_subtotal += amount

        items.append(
            {
                "name":
                    item.get(
                        "name",
                        "Unknown"
                    ),

                "product_id":
                    item.get(
                        "id"
                    ),

                "quantity":
                    qty,

                "unit_price":
                    price,

                "selling_price":
                    price,

                "price_source":
                    item.get(
                        "price_source",
                        "SYSTEM"
                    ),

                "total":
                    round(
                        amount,
                        2
                    )
            }
        )

    # ==========================================================================
    # RPC CANONICAL VALUES
    # ==========================================================================

    subtotal = safe_float(
        rpc_data.get(
            "subtotal",
            calculated_subtotal
        )
    )

    tax_amount = safe_float(
        rpc_data.get(
            "tax",
            subtotal
            * safe_float(tax_rate)
            / 100
        )
    )

    rpc_discount = safe_float(
        rpc_data.get(
            "discount",
            discount
        )
    )

    grand_total = safe_float(
        rpc_data.get(
            "total",
            subtotal
            + tax_amount
            - rpc_discount
        )
    )

    rpc_paid_amount = safe_float(
        rpc_data.get(
            "paid_amount",
            paid_amount
        )
    )

    rpc_change = safe_float(
        rpc_data.get(
            "change",
            rpc_paid_amount
            - grand_total
        )
    )

    # Never allow negative change in receipt.
    rpc_change = max(
        0,
        rpc_change
    )

    # ==========================================================================
    # INVOICE
    # ==========================================================================

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

    # ==========================================================================
    # SALE ID
    # ==========================================================================

    sale_id = rpc_data.get(
        "sale_id"
    )

    # ==========================================================================
    # FINAL RECEIPT DATA
    # ==========================================================================

    return {

        "invoice_no":
            invoice_no,

        "date":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "cashier":
            "Admin",

        "items":
            items,

        # ----------------------------------------------------------------------
        # TOTALS
        # ----------------------------------------------------------------------

        "subtotal":
            round(
                subtotal,
                2
            ),

        "tax_rate":
            safe_float(
                tax_rate
            ),

        "tax_amount":
            round(
                tax_amount,
                2
            ),

        "discount":
            round(
                rpc_discount,
                2
            ),

        # IMPORTANT:
        # Both keys are provided for UI compatibility.
        "grand_total":
            round(
                grand_total,
                2
            ),

        "total":
            round(
                grand_total,
                2
            ),

        # ----------------------------------------------------------------------
        # PAYMENT
        # ----------------------------------------------------------------------

        "paid":
            round(
                rpc_paid_amount,
                2
            ),

        "paid_amount":
            round(
                rpc_paid_amount,
                2
            ),

        "change":
            round(
                rpc_change,
                2
            ),

        # ----------------------------------------------------------------------
        # SALE
        # ----------------------------------------------------------------------

        "sale_id":
            sale_id,

        "warehouse_id":
            rpc_data.get(
                "warehouse_id"
            ),

        "counter_id":
            rpc_data.get(
                "counter_id"
            ),

        "payment_method":
            rpc_data.get(
                "payment_method"
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
    discount=0
):

    try:

        # ======================================================================
        # 1. CART VALIDATION
        # ======================================================================

        if not cart:

            return {
                "success":
                    False,

                "message":
                    "Cart is empty."
            }

        # ======================================================================
        # 2. TAX
        # ======================================================================

        tax_rate = get_default_tax_rate()

        # ======================================================================
        # 3. BUILD RPC CART
        # ======================================================================

        cart_payload = build_cart_payload(
            cart
        )

        # ======================================================================
        # 4. CHECKOUT RPC
        # ======================================================================

        result = checkout_sale_rpc(

            cart=
                cart_payload,

            paid_amount=
                paid_amount,

            warehouse_id=
                warehouse_id,

            cashier_id=
                cashier_id,

            payment_method=
                payment_method,

            tax_rate=
                tax_rate,

            discount=
                discount
        )

        # ======================================================================
        # 5. RPC FAILURE
        # ======================================================================

        if not isinstance(
            result,
            dict
        ):

            return {
                "success":
                    False,

                "message":
                    "Invalid checkout response."
            }

        if not result.get(
            "success",
            False
        ):

            return {
                "success":
                    False,

                "message":
                    result.get(
                        "message",
                        "Checkout failed."
                    )
            }

        # ======================================================================
        # 6. CACHE REFRESH
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

            # Cache failure must never
            # make a successful sale fail.
            pass

        # ======================================================================
        # 7. EXTRACT RPC DATA
        # ======================================================================

        rpc_data = result.get(
            "data",
            {}
        )

        if rpc_data is None:

            rpc_data = {}

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

            rpc_data = {}

        # ======================================================================
        # 8. BUILD RECEIPT
        #
        # IMPORTANT:
        # RPC total is now the canonical total.
        # ======================================================================

        receipt_data = build_receipt_data(

            cart,

            rpc_data,

            paid_amount,

            tax_rate,

            discount
        )

        # ======================================================================
        # 9. FINAL SUCCESS RESPONSE
        # ======================================================================

        return {

            "success":
                True,

            "message":
                result.get(
                    "message",
                    "Sale completed"
                ),

            "data":
                receipt_data
        }

    # ==========================================================================
    # GLOBAL PYTHON ERROR
    # ==========================================================================

    except Exception as e:

        return {

            "success":
                False,

            "message":
                str(e)
        }
