# ==============================================================================
# pages/11_Pricing_Report.py
# ERP ENTERPRISE PRICING REPORT
# ==============================================================================


import streamlit as st
import pandas as pd

from decimal import Decimal

from erp_core import get_products



st.set_page_config(

    page_title="Pricing Report",

    page_icon="💰",

    layout="wide"

)



def money(v):

    try:

        return f"{Decimal(str(v)):,.2f}"

    except:

        return "0.00"



def run():


    st.title(
        "💰 Product Pricing Report"
    )


    products = get_products(
        limit=5000
    )


    if not products:

        st.warning(
            "No products found"
        )

        return



    rows = []


    for p in products:


        cost = Decimal(
            str(
                p.get(
                    "purchase_price",
                    0
                )
            )
        )


        selling = Decimal(
            str(
                p.get(
                    "selling_price",
                    0
                )
            )
        )


        profit = selling - cost



        rows.append(

            {

            "Product":
                p.get("name"),


            "SKU":
                p.get("sku",""),


            "Purchase Cost":
                float(cost),


            "Markup %":
                p.get(
                    "markup_percent",
                    0
                ),


            "Selling Price":
                float(selling),


            "Profit":
                float(profit)

            }

        )



    df = pd.DataFrame(rows)



    st.dataframe(

        df,

        use_container_width=True

    )



    st.divider()



    # Excel Download

    excel = df.to_csv(
        index=False
    ).encode(
        "utf-8"
    )


    st.download_button(

        "⬇️ Download Pricing Report CSV",

        excel,

        "product_pricing_report.csv",

        "text/csv"

    )




if __name__ == "__main__":

    run()
