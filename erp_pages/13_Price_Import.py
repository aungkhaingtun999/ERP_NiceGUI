# ==============================================================================
# erp_pages/13_Price_Import.py
#
# ERP ENTERPRISE PRICE IMPORT CENTER v1.0
#
# Features:
# - CSV Price Import
# - Price Preview
# - Markup Calculation
# - Queue Import
# - Pending Approval View
#
# ==============================================================================


import streamlit as st
import pandas as pd



from erp_core.services.price_import_service import (

    bulk_import_prices,

    pending_imports

)



from auth import (
    is_authenticated
)





# ==============================================================================
# MONEY
# ==============================================================================


def money(value):

    try:

        return f"{float(value):,.0f} MMK"

    except Exception:

        return "0 MMK"





# ==============================================================================
# PAGE
# ==============================================================================


def main():



    # --------------------------------------------------------------------------
    # AUTH
    # --------------------------------------------------------------------------

    if not is_authenticated():

        st.warning(
            "Please login first."
        )

        st.stop()





    # --------------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------------


    st.title(
        "💰 ERP Price Import Center"
    )


    st.caption(
        "Bulk Product Price Management"
    )



    st.divider()





    # ==========================================================================
    # UPLOAD SECTION
    # ==========================================================================


    st.subheader(
        "📂 Import Price File"
    )



    uploaded_file = st.file_uploader(

        "Upload CSV File",

        type=[
            "csv"
        ]

    )





    if uploaded_file:



        df = pd.read_csv(
            uploaded_file
        )



        st.success(
            f"{len(df)} Products Loaded"
        )



        st.dataframe(

            df,

            use_container_width=True,

            hide_index=True

        )



        st.divider()





        if st.button(

            "🚀 Import To Queue",

            type="primary",

            use_container_width=True

        ):



            products = df.to_dict(

                orient="records"

            )




            user = st.session_state.get(

                "user",

                {}

            )



            user_id = user.get(

                "id"

            )




            result = bulk_import_prices(

                products,

                created_by=user_id

            )





            success_count = sum(

                1

                for x in result

                if x.get(
                    "success"
                )

            )



            st.success(

                f"{success_count} items added to approval queue"

            )







    # ==========================================================================
    # TEMPLATE
    # ==========================================================================


    st.divider()


    st.subheader(
        "📄 CSV Format"
    )


    template = pd.DataFrame(

        [

            {

                "id":1,

                "name":"Milk Tea",

                "barcode":"TEA-001",

                "sku":"TEA-001",

                "purchase_price":2000,

                "selling_price":2500

            }

        ]

    )



    st.dataframe(

        template,

        hide_index=True

    )






    # ==========================================================================
    # PENDING QUEUE
    # ==========================================================================


    st.divider()



    st.subheader(

        "⏳ Pending Approval"

    )



    queue = pending_imports()



    if not queue:


        st.info(

            "No pending price imports"

        )



    else:



        queue_df = pd.DataFrame(

            queue

        )



        if "old_selling_price" in queue_df.columns:


            queue_df["old_selling_price"] = (

                queue_df["old_selling_price"]

                .apply(money)

            )



        if "new_selling_price" in queue_df.columns:


            queue_df["new_selling_price"] = (

                queue_df["new_selling_price"]

                .apply(money)

            )




        st.dataframe(

            queue_df,

            use_container_width=True,

            hide_index=True

        )







# ==============================================================================
# STREAMLIT ENTRY
# ==============================================================================


main()