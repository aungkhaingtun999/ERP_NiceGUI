# ==============================================================================
# reports/pricing_report_excel.py
# ERP ENTERPRISE PRICING EXCEL REPORT ENGINE v2.0
# Product / Category / Global Markup Analysis
# ==============================================================================


from io import BytesIO

from datetime import datetime


from openpyxl import Workbook


from openpyxl.styles import (
    Font,
    Alignment,
    Border,
    Side,
    PatternFill
)


from openpyxl.utils import (
    get_column_letter
)



# ==============================================================================
# STYLE
# ==============================================================================


thin_border = Border(

    left=Side(style="thin"),

    right=Side(style="thin"),

    top=Side(style="thin"),

    bottom=Side(style="thin")

)



header_font = Font(
    bold=True
)



title_font = Font(
    bold=True,
    size=16
)



center = Alignment(
    horizontal="center",
    vertical="center"
)



# ==============================================================================
# CREATE EXCEL REPORT
# ==============================================================================


def create_pricing_excel_report(
    products,
    company_name="MYANMAR ERP"
):


    """
    ERP Enterprise Product Pricing Report


    Expected product format:

    {
        name,
        sku,
        category,

        purchase_price,

        product_markup,

        category_markup,

        default_markup,

        final_markup,

        markup_source,

        selling_price,

        profit
    }

    """



    wb = Workbook()


    ws = wb.active


    ws.title = "Pricing Report"



    # ==========================================================================
    # TITLE
    # ==========================================================================


    ws.merge_cells(
        "A1:L1"
    )


    ws["A1"] = (

        company_name

        +

        " - PRODUCT PRICING REPORT"

    )


    ws["A1"].font = title_font


    ws["A1"].alignment = center




    ws.merge_cells(
        "A2:L2"
    )


    ws["A2"] = (

        "Generated : "

        +

        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    )



    # ==========================================================================
    # HEADER
    # ==========================================================================


    headers = [

        "No",

        "Product",

        "SKU",

        "Category",

        "Cost",

        "Product Markup %",

        "Category Markup %",

        "Default Markup %",

        "Applied Source",

        "Final Markup %",

        "Selling Price",

        "Profit"

    ]



    row = 4



    for col, header in enumerate(
        headers,
        start=1
    ):


        cell = ws.cell(

            row=row,

            column=col

        )


        cell.value = header


        cell.font = header_font


        cell.alignment = center


        cell.border = thin_border




    # ==========================================================================
    # DATA
    # ==========================================================================


    total_profit = 0


    total_sales_value = 0



    row += 1



    for index, product in enumerate(
        products,
        start=1
    ):



        cost = float(

            product.get(
                "purchase_price",
                0
            )
            or 0

        )



        selling = float(

            product.get(
                "selling_price",
                0
            )
            or 0

        )



        profit = (

            selling

            -

            cost

        )



        total_profit += profit


        total_sales_value += selling




        data = [

            index,

            product.get(
                "name",
                ""
            ),

            product.get(
                "sku",
                ""
            ),

            product.get(
                "category",
                "-"
            ),


            cost,


            product.get(
                "product_markup",
                0
            ),


            product.get(
                "category_markup",
                0
            ),


            product.get(
                "default_markup",
                0
            ),


            product.get(
                "markup_source",
                "GLOBAL"
            ),


            product.get(
                "final_markup",
                0
            ),


            selling,


            profit

        ]



        for col, value in enumerate(
            data,
            start=1
        ):


            cell = ws.cell(

                row=row,

                column=col

            )


            cell.value = value


            cell.border = thin_border




            if col in [

                5,
                11,
                12

            ]:

                cell.number_format = (
                    '#,##0.00'
                )



            if col in [

                6,
                7,
                8,
                10

            ]:

                cell.number_format = (
                    '0.00"%"'
                )



        row += 1



    # ==========================================================================
    # SUMMARY
    # ==========================================================================


    row += 2



    summary = [

        (
            "Total Products",
            len(products)
        ),

        (
            "Total Selling Value",
            total_sales_value
        ),

        (
            "Total Profit",
            total_profit
        )

    ]



    for label, value in summary:


        ws.cell(
            row=row,
            column=1
        ).value = label



        ws.cell(
            row=row,
            column=2
        ).value = value



        if isinstance(
            value,
            float
        ):

            ws.cell(
                row=row,
                column=2
            ).number_format = (
                '#,##0.00'
            )



        row += 1




    # ==========================================================================
    # AUTO WIDTH
    # ==========================================================================


    for column in ws.columns:


        max_length = 0



        column_letter = get_column_letter(

            column[0].column

        )



        for cell in column:


            try:

                length = len(
                    str(
                        cell.value
                    )
                )


                if length > max_length:

                    max_length = length



            except:

                pass




        ws.column_dimensions[
            column_letter
        ].width = max_length + 4





    # ==========================================================================
    # RETURN FILE
    # ==========================================================================


    output = BytesIO()



    wb.save(
        output
    )



    output.seek(
        0
    )



    return output
