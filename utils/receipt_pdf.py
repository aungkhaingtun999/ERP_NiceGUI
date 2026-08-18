# ==========================================
# utils/receipt_pdf.py
# ERP ENTERPRISE RECEIPT PDF GENERATOR v5.1
# SALE ID + INVOICE NO
# SALE_ITEMS COMPATIBLE
# ==========================================

import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# ==========================================
# SAFE NUMBER
# ==========================================

def num(val):

    try:

        if val is None:
            return 0.0

        return float(val)

    except Exception:

        return 0.0


# ==========================================
# SAFE SALE ID
# ==========================================

def get_sale_id(receipt_data):

    """
    Resolve Sale ID safely.

    Supported:
        receipt_data["sale_id"]
        receipt_data["id"]

    Returns:
        int / str / None
    """

    if not isinstance(receipt_data, dict):
        return None

    sale_id = receipt_data.get("sale_id")

    if sale_id is None:
        sale_id = receipt_data.get("id")

    if sale_id is None:
        return None

    return sale_id


# ==========================================
# SAFE INVOICE NUMBER
# ==========================================

def get_invoice_no(receipt_data):

    if not isinstance(receipt_data, dict):
        return "INV-UNKNOWN"

    invoice_no = (
        receipt_data.get("invoice_no")
        or receipt_data.get("invoice_number")
        or receipt_data.get("reference_no")
    )

    if not invoice_no:
        invoice_no = "INV-UNKNOWN"

    return str(invoice_no)


# ==========================================
# GENERATE PDF
# ==========================================

def generate_pdf(receipt_data):

    try:

        # ==================================
        # VALIDATION
        # ==================================

        if not receipt_data:
            return None

        if not isinstance(receipt_data, dict):
            return None


        # ==================================
        # RECEIPT IDENTIFIERS
        # ==================================

        invoice_no = get_invoice_no(
            receipt_data
        )

        sale_id = get_sale_id(
            receipt_data
        )


        if sale_id is None:
            sale_id_display = "SALE-UNKNOWN"

        else:
            sale_id_display = str(sale_id)


        # ==================================
        # FILE NAME
        # ==================================

        filename = f"Receipt_{invoice_no}"

        pdf_path = f"{filename}.pdf"


        # ==================================
        # CREATE PDF
        # ==================================

        pdf = canvas.Canvas(
            pdf_path,
            pagesize=letter
        )


        width, height = letter


        # ==================================
        # HEADER
        # ==================================

        pdf.setFont(
            "Helvetica-Bold",
            16
        )

        pdf.drawString(
            50,
            height - 50,
            "MY POS SYSTEM"
        )


        pdf.setFont(
            "Helvetica",
            10
        )


        pdf.drawString(
            50,
            height - 70,
            "Tachileik, Shan State, Myanmar"
        )


        pdf.drawString(
            50,
            height - 85,
            "Tel : 09-267772367"
        )


        # ==================================
        # RECEIPT INFORMATION
        # ==================================

        pdf.drawString(
            50,
            height - 110,
            f"Receipt : {invoice_no}"
        )


        # ==================================
        # SALE ID
        # ==================================

        pdf.drawString(
            50,
            height - 125,
            f"Sale ID : {sale_id_display}"
        )


        # ==================================
        # DATE
        # ==================================

        pdf.drawString(
            50,
            height - 140,
            f"Date : {receipt_data.get('date', '-')}"
        )


        # ==================================
        # CASHIER
        # ==================================

        pdf.drawString(
            50,
            height - 155,
            f"Cashier : {receipt_data.get('cashier', 'Admin')}"
        )


        # ==================================
        # TABLE HEADER
        # ==================================

        y = height - 190


        pdf.setFont(
            "Helvetica-Bold",
            10
        )


        pdf.drawString(
            50,
            y,
            "Item"
        )


        pdf.drawRightString(
            315,
            y,
            "Qty"
        )


        pdf.drawRightString(
            420,
            y,
            "Price"
        )


        pdf.drawRightString(
            550,
            y,
            "Amount"
        )


        y -= 15


        pdf.line(
            50,
            y,
            550,
            y
        )


        # ==================================
        # ITEMS
        # ==================================

        y -= 20


        pdf.setFont(
            "Helvetica",
            10
        )


        items = receipt_data.get(
            "items"
        ) or []


        for item in items:

            if item is None:
                continue

            if not isinstance(item, dict):
                continue


            # ------------------------------
            # PRODUCT NAME RESOLUTION
            # ------------------------------

            product = item.get(
                "products"
            )


            name = (
                item.get("product_name")
                or
                item.get("name")
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
                    f"Product #"
                    f"{item.get('product_id', '')}"
                )


            # ------------------------------
            # QUANTITY
            # ------------------------------

            qty = item.get(
                "quantity",
                0
            )


            try:

                qty = int(
                    float(qty)
                )

            except Exception:

                qty = 0


            # ------------------------------
            # UNIT PRICE
            # ------------------------------

            price = item.get(
                "unit_price",
                0
            )


            try:

                price = float(
                    price
                )

            except Exception:

                price = 0.0


            # ------------------------------
            # AMOUNT
            # ------------------------------

            amount = item.get(
                "total",
                0
            )


            try:

                amount = float(
                    amount
                )

            except Exception:

                amount = 0.0


            # ------------------------------
            # SAFETY CALCULATION
            # ------------------------------

            if amount == 0 and qty > 0:

                amount = (
                    qty * price
                )


            # ==================================
            # NEW PAGE
            # ==================================

            if y < 120:

                pdf.showPage()

                y = height - 50

                pdf.setFont(
                    "Helvetica",
                    10
                )


            # ==================================
            # ITEM ROW
            # ==================================

            pdf.drawString(
                50,
                y,
                str(name)[:30]
            )


            pdf.drawRightString(
                315,
                y,
                f"{qty}"
            )


            pdf.drawRightString(
                420,
                y,
                f"{price:,.0f}"
            )


            pdf.drawRightString(
                550,
                y,
                f"{amount:,.0f}"
            )


            y -= 18


        # ==========================================
        # TOTAL SECTION
        # ==========================================

        y -= 10


        pdf.line(
            300,
            y,
            550,
            y
        )


        y -= 25


        # ==================================
        # SUBTOTAL
        # ==================================

        subtotal = num(
            receipt_data.get(
                "subtotal"
            )
        )


        # ==================================
        # DISCOUNT
        # ==================================

        discount = num(
            receipt_data.get(
                "discount"
            )
        )


        # ==================================
        # TAX RATE
        # ==================================

        tax_rate = num(
            receipt_data.get(
                "tax_rate"
            )
        )


        # ==================================
        # TAX AMOUNT
        # ==================================

        tax = num(
            receipt_data.get(
                "tax_amount"
            )
        )


        # ==================================
        # GRAND TOTAL
        # ==================================

        grand_total = num(
            receipt_data.get(
                "grand_total"
            )
        )


        # ==================================
        # PAID
        # ==================================

        paid = num(
            receipt_data.get(
                "paid"
            )
        )


        # ==================================
        # CHANGE
        # ==================================

        change = num(
            receipt_data.get(
                "change"
            )
        )


        # ==================================
        # SUBTOTAL DISPLAY
        # ==================================

        pdf.drawRightString(
            550,
            y,
            f"Subtotal : {subtotal:,.0f} MMK"
        )


        y -= 18


        # ==================================
        # DISCOUNT DISPLAY
        # ==================================

        pdf.drawRightString(
            550,
            y,
            f"Discount : {discount:,.0f} MMK"
        )


        y -= 18


        # ==================================
        # TAX RATE DISPLAY
        # ==================================

        pdf.drawRightString(
            550,
            y,
            f"Tax Rate : {tax_rate:.2f}%"
        )


        y -= 18


        # ==================================
        # TAX AMOUNT DISPLAY
        # ==================================

        pdf.drawRightString(
            550,
            y,
            f"Tax Amount : {tax:,.0f} MMK"
        )


        y -= 18


        # ==================================
        # GRAND TOTAL
        # ==================================

        pdf.setFont(
            "Helvetica-Bold",
            12
        )


        pdf.drawRightString(
            550,
            y,
            f"GRAND TOTAL : {grand_total:,.0f} MMK"
        )


        y -= 20


        # ==================================
        # PAID
        # ==================================

        pdf.setFont(
            "Helvetica",
            10
        )


        pdf.drawRightString(
            550,
            y,
            f"Paid : {paid:,.0f} MMK"
        )


        y -= 18


        # ==================================
        # CHANGE
        # ==================================

        pdf.drawRightString(
            550,
            y,
            f"Change : {change:,.0f} MMK"
        )


        # ==========================================
        # FOOTER
        # ==========================================

        pdf.drawCentredString(
            width / 2,
            60,
            "Thank you for your business!"
        )


        # ==========================================
        # SAVE PDF
        # ==========================================

        pdf.save()


        # ==========================================
        # READ PDF BYTES
        # ==========================================

        with open(
            pdf_path,
            "rb"
        ) as f:

            pdf_bytes = f.read()


        # ==========================================
        # REMOVE TEMP FILE
        # ==========================================

        if os.path.exists(
            pdf_path
        ):

            os.remove(
                pdf_path
            )


        # ==========================================
        # RETURN
        # ==========================================

        return (
            pdf_bytes,
            filename
        )


    # ==========================================
    # ERROR HANDLING
    # ==========================================

    except Exception as e:

        print(
            "PDF ERROR:",
            e
        )

        # ------------------------------------------
        # Cleanup PDF if it was created
        # ------------------------------------------

        try:

            if (
                "pdf_path" in locals()
                and os.path.exists(pdf_path)
            ):

                os.remove(
                    pdf_path
                )

        except Exception:

            pass


        return None
