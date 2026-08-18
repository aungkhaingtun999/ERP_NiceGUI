# ==============================================================================
# utils/thermal_receipt.py
# ERP ENTERPRISE THERMAL RECEIPT ENGINE v5.2
# SALE ID SUPPORTED
# CONFIG + FORMAT + ITEM NORMALIZER + RECEIPT BUILDER + PRINT ENGINE
# ==============================================================================

import json
import os
import tempfile

import streamlit as st

from utils.timezone import format_db_datetime


# ==============================================================================
# OPTIONAL PRINTER IMPORT
# ==============================================================================

try:
    import win32api
    import win32print
except ImportError:
    win32api = None
    win32print = None


try:
    from escpos.printer import Usb, Network
except ImportError:
    Usb = None
    Network = None


# ==============================================================================
# SHOP CONFIG
# ==============================================================================

def get_shop_info():

    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "pages",
        "config.json"
    )

    default = {

        "shop_name":
            "MY POS SYSTEM",

        "address":
            "Tachileik, Shan State, Myanmar",

        "phone":
            "09-267772367",

        "footer_msg":
            "THANK YOU\nVISIT AGAIN",

        "printer_mode":
            "windows",

        "printer_name":
            "",

        "printer_vendor_id":
            "",

        "printer_product_id":
            "",

        "printer_ip":
            "",

        "printer_port":
            9100
    }

    try:

        if os.path.exists(config_path):

            with open(
                config_path,
                "r",
                encoding="utf-8"
            ) as f:

                user = json.load(f)

                return {
                    **default,
                    **user
                }

    except Exception:
        pass

    return default


# ==============================================================================
# PRINTER CONNECTION
# ==============================================================================

def get_printer():

    shop = get_shop_info()

    mode = shop.get(
        "printer_mode",
        "windows"
    )

    # --------------------------------------------------------------------------
    # USB
    # --------------------------------------------------------------------------

    if mode == "usb":

        if Usb is None:

            st.warning(
                "USB printer unavailable"
            )

            return None

        try:

            vendor = shop.get(
                "printer_vendor_id"
            )

            product = shop.get(
                "printer_product_id"
            )

            if vendor and product:

                return Usb(
                    int(vendor, 16),
                    int(product, 16)
                )

        except Exception as e:

            st.error(
                f"USB ERROR : {e}"
            )

    # --------------------------------------------------------------------------
    # NETWORK
    # --------------------------------------------------------------------------

    elif mode == "network":

        if Network is None:

            st.warning(
                "Network printer unavailable"
            )

            return None

        try:

            ip = shop.get(
                "printer_ip"
            )

            port = int(
                shop.get(
                    "printer_port",
                    9100
                )
            )

            if ip:

                return Network(
                    ip,
                    port
                )

        except Exception as e:

            st.error(
                f"NETWORK ERROR : {e}"
            )

    return None


# ==============================================================================
# SAFE NUMBER CONVERTER
# ==============================================================================

def num(value):

    try:

        if value is None:
            return 0.0

        return float(value)

    except Exception:
        return 0.0


# ==============================================================================
# SAFE INTEGER CONVERTER
# ==============================================================================

def safe_int(value, default=0):

    try:

        if value is None:
            return default

        return int(float(value))

    except Exception:
        return default


# ==============================================================================
# TEXT ALIGNMENT
# ==============================================================================

def line(
    left="",
    right="",
    width=32
):

    left = str(left)
    right = str(right)

    space = (
        width
        -
        len(left)
        -
        len(right)
    )

    return (
        left
        +
        (" " * max(space, 1))
        +
        right
    )


# ==============================================================================
# SALE ITEMS NORMALIZER
# ==============================================================================

def normalize_items(items):

    """
    Database:

    sale_items
    ----------------
    id
    sale_id
    product_id
    quantity
    unit_price
    total

    Output:

    {
        name,
        product_id,
        quantity,
        unit_price,
        total
    }
    """

    result = []

    for item in items or []:

        if not item:
            continue

        # ----------------------------------------------------------------------
        # PRODUCT NAME RESOLUTION
        # ----------------------------------------------------------------------

        product = item.get(
            "products"
        )

        name = (
            item.get("product_name")
            or
            item.get("name")
        )

        if not name and isinstance(product, dict):

            name = product.get(
                "name"
            )

        if not name:

            name = (
                f"Product #{item.get('product_id', '')}"
            )

        # ----------------------------------------------------------------------
        # QUANTITY
        # ----------------------------------------------------------------------

        quantity = num(
            item.get(
                "quantity",
                item.get(
                    "qty",
                    0
                )
            )
        )

        # ----------------------------------------------------------------------
        # UNIT PRICE
        # ----------------------------------------------------------------------

        unit_price = num(
            item.get(
                "unit_price",
                item.get(
                    "price",
                    0
                )
            )
        )

        # ----------------------------------------------------------------------
        # TOTAL
        # ----------------------------------------------------------------------

        total = num(
            item.get(
                "total",
                item.get(
                    "amount",
                    0
                )
            )
        )

        # ----------------------------------------------------------------------
        # FALLBACK CALCULATION
        # ----------------------------------------------------------------------

        if total == 0:

            total = (
                quantity
                *
                unit_price
            )

        result.append(

            {

                "id":
                    item.get(
                        "id"
                    ),

                "sale_id":
                    item.get(
                        "sale_id"
                    ),

                "name":
                    name,

                "product_name":
                    name,

                "product_id":
                    item.get(
                        "product_id"
                    ),

                "quantity":
                    safe_int(
                        quantity
                    ),

                "unit_price":
                    unit_price,

                "total":
                    total
            }

        )

    return result


# ==============================================================================
# RECEIPT DATA BUILDER
# ERP STANDARD RECEIPT FORMAT
# FIXED v5.2
# SALE ID INCLUDED
# ==============================================================================

def build_receipt_data(
    sale,
    items
):

    try:

        sale = sale or {}
        items = items or []

        # ======================================================================
        # SALE ID
        # ======================================================================

        sale_id = (
            sale.get("sale_id")
            or
            sale.get("id")
        )

        # ======================================================================
        # NORMALIZE ITEMS
        # ======================================================================

        clean_items = []

        for item in items:

            if not item:
                continue

            quantity = num(

                item.get(
                    "quantity",
                    item.get(
                        "qty",
                        0
                    )
                )

            )

            unit_price = num(

                item.get(
                    "unit_price",
                    item.get(
                        "price",
                        0
                    )
                )

            )

            total = num(

                item.get(
                    "total",
                    item.get(
                        "amount",
                        0
                    )
                )

            )

            if total == 0:

                total = (
                    quantity
                    *
                    unit_price
                )

            # ------------------------------------------------------------------
            # PRODUCT NAME
            # ------------------------------------------------------------------

            product = item.get(
                "products"
            )

            name = (

                item.get(
                    "product_name"
                )

                or

                item.get(
                    "name"
                )

            )

            if not name and isinstance(
                product,
                dict
            ):

                name = product.get(
                    "name"
                )

            if not name:

                name = (
                    f"Product #{item.get('product_id', '')}"
                )

            clean_items.append(

                {

                    "id":
                        item.get(
                            "id"
                        ),

                    "sale_id":
                        item.get(
                            "sale_id",
                            sale_id
                        ),

                    "name":
                        name,

                    "product_name":
                        name,

                    "product_id":
                        item.get(
                            "product_id"
                        ),

                    "quantity":
                        safe_int(
                            quantity
                        ),

                    "unit_price":
                        unit_price,

                    "total":
                        total

                }

            )

        # ======================================================================
        # TAX RATE AUTO RECOVER
        # ======================================================================

        subtotal = num(

            sale.get(
                "subtotal",
                0
            )

        )

        tax_amount = num(

            sale.get(
                "tax",
                sale.get(
                    "tax_amount",
                    0
                )
            )

        )

        tax_rate = num(

            sale.get(
                "tax_rate",
                0
            )

        )

        if (
            tax_rate == 0
            and
            subtotal > 0
            and
            tax_amount > 0
        ):

            tax_rate = round(

                (
                    tax_amount
                    /
                    subtotal
                )
                *
                100,

                2

            )

        # ======================================================================
        # FINAL RECEIPT OBJECT
        # ======================================================================

        receipt = {

            # ------------------------------------------------------------------
            # SALE IDENTIFICATION
            # ------------------------------------------------------------------

            "sale_id":
                sale_id,

            "invoice_no":
                sale.get(
                    "invoice_no",
                    "-"
                ),

            # ------------------------------------------------------------------
            # DATE
            # ------------------------------------------------------------------

            "date":
                format_db_datetime(
                    sale.get("created_at")
                    or
                    sale.get("date")
                ),

            # ------------------------------------------------------------------
            # CASHIER
            # ------------------------------------------------------------------

            "cashier":
                sale.get(
                    "cashier",
                    "Admin"
                ),

            # ------------------------------------------------------------------
            # ITEMS
            # ------------------------------------------------------------------

            "items":
                clean_items,

            # ------------------------------------------------------------------
            # FINANCIAL DATA
            # ------------------------------------------------------------------

            "subtotal":
                subtotal,

            "discount":
                num(
                    sale.get(
                        "discount",
                        0
                    )
                ),

            "tax_rate":
                tax_rate,

            "tax_amount":
                tax_amount,

            "grand_total":
                num(
                    sale.get(
                        "total",
                        0
                    )
                ),

            "paid":
                num(
                    sale.get(
                        "paid_amount",
                        0
                    )
                ),

            "change":
                num(
                    sale.get(
                        "change_amount",
                        0
                    )
                )

        }

        return receipt

    except Exception as e:

        print(
            "BUILD RECEIPT ERROR:",
            e
        )

        return {}


# ==============================================================================
# THERMAL RECEIPT TEXT GENERATOR
# ==============================================================================

def create_receipt_text(data):

    shop = get_shop_info()

    text = ""

    # ==========================================================================
    # SHOP HEADER
    # ==========================================================================

    text += (
        shop.get(
            "shop_name",
            "MY POS SYSTEM"
        )
        +
        "\n"
    )

    text += (
        shop.get(
            "address",
            ""
        )
        +
        "\n"
    )

    text += (
        "Tel : "
        +
        shop.get(
            "phone",
            ""
        )
        +
        "\n"
    )

    text += (
        "-" * 32
        +
        "\n"
    )

    # ==========================================================================
    # RECEIPT / SALE INFORMATION
    # ==========================================================================

    text += (
        "Receipt : "
        +
        str(
            data.get(
                "invoice_no",
                "-"
            )
        )
        +
        "\n"
    )

    # --------------------------------------------------------------------------
    # SALE ID
    # --------------------------------------------------------------------------

    sale_id = data.get(
        "sale_id"
    )

    if sale_id is not None and str(
        sale_id
    ).strip():

        text += (
            "Sale ID : "
            +
            str(sale_id)
            +
            "\n"
        )

    # --------------------------------------------------------------------------
    # DATE
    # --------------------------------------------------------------------------

    text += (
        "Date : "
        +
        str(
            data.get(
                "date",
                "-"
            )
        )
        +
        "\n"
    )

    # --------------------------------------------------------------------------
    # CASHIER
    # --------------------------------------------------------------------------

    text += (
        "Cashier : "
        +
        str(
            data.get(
                "cashier",
                "Admin"
            )
        )
        +
        "\n"
    )

    text += (
        "-" * 32
        +
        "\n"
    )

    # ==========================================================================
    # ITEMS HEADER
    # ==========================================================================

    text += (
        line(
            "Item",
            "Amount",
            32
        )
        +
        "\n"
    )

    # ==========================================================================
    # ITEMS
    # ==========================================================================

    for item in data.get(
        "items",
        []
    ):

        name = (

            item.get("name")
            or
            item.get("product_name")
            or
            item.get("product")
            or
            f"Product #{item.get('product_id', '')}"

        )

        qty = item.get(
            "quantity"
        )

        if qty is None:

            qty = item.get(
                "qty",
                0
            )

        qty = num(
            qty
        )

        price = item.get(
            "unit_price"
        )

        if price is None:

            price = item.get(
                "selling_price"
            )

        if price is None:

            price = item.get(
                "price",
                0
            )

        price = num(
            price
        )

        amount = num(
            item.get(
                "total",
                0
            )
        )

        # ----------------------------------------------------------------------
        # PRODUCT NAME
        # ----------------------------------------------------------------------

        text += (
            str(name)[:32]
            +
            "\n"
        )

        # ----------------------------------------------------------------------
        # QTY x PRICE + AMOUNT
        # ----------------------------------------------------------------------

        text += (
            line(
                f"{safe_int(qty)} x {price:,.0f}",
                f"{amount:,.0f}",
                32
            )
            +
            "\n"
        )

    # ==========================================================================
    # TOTALS
    # ==========================================================================

    text += (
        "-" * 32
        +
        "\n"
    )

    # --------------------------------------------------------------------------
    # SUBTOTAL
    # --------------------------------------------------------------------------

    text += (
        line(
            "Subtotal",
            f"{num(data.get('subtotal')):,.0f}",
            32
        )
        +
        "\n"
    )

    # --------------------------------------------------------------------------
    # DISCOUNT
    # --------------------------------------------------------------------------

    discount = num(
        data.get(
            "discount",
            0
        )
    )

    if discount != 0:

        text += (
            line(
                "Discount",
                f"{discount:,.0f}",
                32
            )
            +
            "\n"
        )

    # --------------------------------------------------------------------------
    # TAX
    # --------------------------------------------------------------------------

    tax_rate = num(
        data.get(
            "tax_rate"
        )
    )

    tax_amount = num(
        data.get(
            "tax_amount"
        )
    )

    text += (
        line(
            f"Tax ({tax_rate:.2f}%)",
            f"{tax_amount:,.0f}",
            32
        )
        +
        "\n"
    )

    # --------------------------------------------------------------------------
    # GRAND TOTAL
    # --------------------------------------------------------------------------

    text += (
        line(
            "TOTAL",
            f"{num(data.get('grand_total')):,.0f}",
            32
        )
        +
        "\n"
    )

    # --------------------------------------------------------------------------
    # PAID
    # --------------------------------------------------------------------------

    text += (
        line(
            "Paid",
            f"{num(data.get('paid')):,.0f}",
            32
        )
        +
        "\n"
    )

    # --------------------------------------------------------------------------
    # CHANGE
    # --------------------------------------------------------------------------

    text += (
        line(
            "Change",
            f"{num(data.get('change')):,.0f}",
            32
        )
        +
        "\n"
    )

    # ==========================================================================
    # FOOTER
    # ==========================================================================

    text += (
        "-" * 32
        +
        "\n"
    )

    text += (
        shop.get(
            "footer_msg",
            "THANK YOU"
        )
        +
        "\n\n\n"
    )

    return text


# ==============================================================================
# THERMAL PRINT ENGINE
# ==============================================================================

def print_thermal(data):

    try:

        if not data:

            st.error(
                "No receipt data available"
            )

            return False

        shop = get_shop_info()

        mode = shop.get(
            "printer_mode",
            "windows"
        )

        # ==========================================================================
        # CREATE RECEIPT TEXT
        # ==========================================================================

        receipt_text = create_receipt_text(
            data
        )

        # ==========================================================================
        # WINDOWS PRINT
        # ==========================================================================

        if mode == "windows":

            temp_path = None

            try:

                temp = tempfile.NamedTemporaryFile(

                    delete=False,

                    suffix=".txt",

                    mode="w",

                    encoding="utf-8"

                )

                temp.write(
                    receipt_text
                )

                temp.close()

                temp_path = temp.name

                if win32api:

                    win32api.ShellExecute(

                        0,

                        "print",

                        temp_path,

                        None,

                        ".",

                        0

                    )

                    return True

                else:

                    st.warning(
                        "pywin32 not installed. Receipt text created only."
                    )

                    return True

            finally:

                pass

        # ==========================================================================
        # ESC/POS USB / NETWORK
        # ==========================================================================

        printer = get_printer()

        if printer:

            printer.text(
                receipt_text
            )

            try:

                printer.cut()

            except Exception:

                pass

            return True

        st.warning(
            "Printer not connected"
        )

        return False

    except Exception as e:

        st.error(
            f"THERMAL PRINT ERROR : {e}"
        )

        return False


# ==============================================================================
# SIMPLE REPRINT HELPER
# ==============================================================================

def reprint_receipt(
    sale,
    items
):

    try:

        receipt = build_receipt_data(
            sale,
            items
        )

        return print_thermal(
            receipt
        )

    except Exception as e:

        st.error(
            f"REPRINT ERROR : {e}"
        )

        return False


# ==============================================================================
# OPTIONAL: GET RECEIPT SALE ID
# ==============================================================================

def get_receipt_sale_id(
    sale
):

    """
    Safely resolve Sale ID from a sale dictionary.

    Priority:
        1. sale_id
        2. id
    """

    if not sale:
        return None

    return (
        sale.get("sale_id")
        or
        sale.get("id")
    )
