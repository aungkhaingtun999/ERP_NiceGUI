# ==========================================
# utils/receipt_pdf.py
# ERP ENTERPRISE RECEIPT PDF GENERATOR v5
# SALE_ITEMS COMPATIBLE
# ==========================================

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


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
# GENERATE PDF
# ==========================================

def generate_pdf(receipt_data):

    try:

        if not receipt_data:
            return None


        invoice_no = receipt_data.get(
            "invoice_no",
            "INV-UNKNOWN"
        )


        filename = f"Receipt_{invoice_no}"


        pdf_path = f"{filename}.pdf"



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
            height-50,
            "MY POS SYSTEM"
        )


        pdf.setFont(
            "Helvetica",
            10
        )


        pdf.drawString(
            50,
            height-70,
            "Tachileik, Shan State, Myanmar"
        )


        pdf.drawString(
            50,
            height-85,
            "Tel : 09-267772367"
        )



        pdf.drawString(
            50,
            height-110,
            f"Receipt : {invoice_no}"
        )


        pdf.drawString(
            50,
            height-125,
            f"Date : {receipt_data.get('date','-')}"
        )


        pdf.drawString(
            50,
            height-140,
            f"Cashier : {receipt_data.get('cashier','Admin')}"
        )



        # ==================================
        # TABLE HEADER
        # ==================================

        y = height-175


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


        items = receipt_data.get("items") or []


        for item in items:

            if item is None:
                continue


            # ------------------------------
            # PRODUCT NAME
            # ------------------------------

            # PRODUCT NAME RESOLUTION

            product = item.get("products")

            name = (
                item.get("product_name")
                or
                item.get("name")
            )

            if not name and isinstance(product, dict):
                name = product.get("name")


            if not name:
                name = f"Product #{item.get('product_id','')}"


            # ------------------------------
            # QUANTITY
            # ------------------------------

            qty = item.get("quantity", 0)


            try:
                qty = int(qty)
            except:
                qty = 0



            # ------------------------------
            # UNIT PRICE
            # ------------------------------

            price = item.get(
                "unit_price",
                0
            )


            try:
                price = float(price)

            except:
                price = 0



            # ------------------------------
            # AMOUNT
            # ------------------------------

            amount = item.get(
                "total",
                0
            )


            try:
                amount = float(amount)

            except:
                amount = 0



            # safety calculation

            if amount == 0 and qty > 0:

                amount = qty * price



            if y < 120:

                pdf.showPage()

                y = height - 50



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



                # ==================================
        # TOTAL
        # ==================================

        y -= 10


        pdf.line(
            300,
            y,
            550,
            y
        )


        y -= 25



        subtotal = num(
            receipt_data.get("subtotal")
        )


        discount = num(
            receipt_data.get("discount")
        )


        tax_rate = num(
            receipt_data.get("tax_rate")
        )


        tax = num(
            receipt_data.get("tax_amount")
        )


        grand_total = num(
            receipt_data.get("grand_total")
        )


        paid = num(
            receipt_data.get("paid")
        )


        change = num(
            receipt_data.get("change")
        )



        pdf.drawRightString(
            550,
            y,
            f"Subtotal : {subtotal:,.0f} MMK"
        )

        y -= 18


        pdf.drawRightString(
            550,
            y,
            f"Discount : {discount:,.0f} MMK"
        )

        y -= 18


        pdf.drawRightString(
            550,
            y,
            f"Tax Rate : {tax_rate:.2f}%"
        )

        y -= 18


        pdf.drawRightString(
            550,
            y,
            f"Tax Amount : {tax:,.0f} MMK"
        )

        y -= 18



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


        pdf.drawRightString(
            550,
            y,
            f"Change : {change:,.0f} MMK"
        )



        # ==================================
        # FOOTER
        # ==================================

        pdf.drawCentredString(
            width/2,
            60,
            "Thank you for your business!"
        )



        pdf.save()



        with open(
            pdf_path,
            "rb"
        ) as f:

            pdf_bytes = f.read()



        if os.path.exists(pdf_path):

            os.remove(pdf_path)



        return (
            pdf_bytes,
            filename
        )



    except Exception as e:

        print(
            "PDF ERROR:",
            e
        )

        return None
