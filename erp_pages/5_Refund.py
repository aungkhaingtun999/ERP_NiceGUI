# ==============================================================================
# ERP ENTERPRISE REFUND SYSTEM
#
# Refund Request UI
#
# UI Enhancement:
#   - Invoice No displayed once
#   - Sale Date displayed once
#   - Original Total displayed once
#   - Product Name displayed per item
#   - Product ID is no longer the primary display
#
# IMPORTANT:
#   Refund RPC / approval workflow is NOT changed here.
# ==============================================================================

import streamlit as st

from database import db
from auth import require_login


# ==============================================================================
# MAIN
# ==============================================================================

def run():

    # ==========================================================================
    # AUTHENTICATION
    # ==========================================================================

    user = require_login()

    st.title(
        "↩️ Refund System (ERP Mode)"
    )


    # ==========================================================================
    # SESSION INITIALIZATION
    # ==========================================================================

    if "selected_sale" not in st.session_state:

        st.session_state.selected_sale = None


    if "refund_cart" not in st.session_state:

        st.session_state.refund_cart = []


    # ==========================================================================
    # SEARCH SALE
    # ==========================================================================

    st.subheader(
        "🔍 Search Sale"
    )


    input_id = st.text_input(
        "Enter Sale ID",
        key="refund_sale_input",
        placeholder="Enter Sale ID",
    )


    if st.button(
        "🔎 Search Sale",
        type="secondary",
    ):

        if (
            not input_id
            or not input_id.isdigit()
        ):

            st.warning(
                "Please enter a valid numeric Sale ID."
            )

        else:

            with st.spinner(
                "Fetching data from ERP..."
            ):

                try:

                    sale_id = int(input_id)


                    # ----------------------------------------------------------
                    # SALE HEADER
                    # ----------------------------------------------------------

                    response = (
                        db()
                        .table("sales")
                        .select("*")
                        .eq(
                            "id",
                            sale_id,
                        )
                        .execute()
                    )


                    if (
                        not response
                        or not hasattr(
                            response,
                            "data",
                        )
                        or not response.data
                    ):

                        st.error(
                            f"Sale ID {input_id} not found."
                        )

                    else:

                        sale = response.data[0]


                        # ------------------------------------------------------
                        # SALE ITEMS
                        # ------------------------------------------------------

                        items_resp = (
                            db()
                            .table("sale_items")
                            .select("*")
                            .eq(
                                "sale_id",
                                sale_id,
                            )
                            .execute()
                        )


                        sale["items"] = (
                            items_resp.data
                            if (
                                items_resp
                                and hasattr(
                                    items_resp,
                                    "data",
                                )
                            )
                            else []
                        )


                        # ------------------------------------------------------
                        # LOAD PRODUCT NAMES
                        #
                        # sale_items may only contain product_id.
                        # Therefore fetch product master information.
                        # ------------------------------------------------------

                        product_ids = []

                        for item in sale["items"]:

                            product_id = item.get(
                                "product_id"
                            )

                            if product_id is not None:

                                product_ids.append(
                                    product_id
                                )


                        product_map = {}


                        if product_ids:

                            unique_product_ids = list(
                                dict.fromkeys(
                                    product_ids
                                )
                            )


                            products_resp = (
                                db()
                                .table("products")
                                .select(
                                    "id,name"
                                )
                                .in_(
                                    "id",
                                    unique_product_ids,
                                )
                                .execute()
                            )


                            products_data = (
                                products_resp.data
                                if (
                                    products_resp
                                    and hasattr(
                                        products_resp,
                                        "data",
                                    )
                                )
                                else []
                            )


                            for product in products_data:

                                product_map[
                                    product.get("id")
                                ] = product.get(
                                    "name"
                                )


                        # ------------------------------------------------------
                        # ATTACH PRODUCT NAME
                        # ------------------------------------------------------

                        for item in sale["items"]:

                            product_id = item.get(
                                "product_id"
                            )


                            product_name = (
                                product_map.get(
                                    product_id
                                )
                                or item.get(
                                    "product_name"
                                )
                                or f"Product #{product_id}"
                            )


                            item[
                                "display_product_name"
                            ] = product_name


                        # ------------------------------------------------------
                        # SAVE SESSION
                        # ------------------------------------------------------

                        st.session_state.selected_sale = sale

                        st.session_state.refund_cart = []

                        st.rerun()


                except Exception as e:

                    st.error(
                        f"Database Query Error: {e}"
                    )


    # ==========================================================================
    # REFUND DISPLAY
    # ==========================================================================

    sale = st.session_state.selected_sale


    if not sale:

        return


    # ==========================================================================
    # SALE INFORMATION
    # ==========================================================================

    st.divider()

    st.subheader(
        "🧾 Sale Information"
    )


    # --------------------------------------------------------------------------
    # SALE ID
    # --------------------------------------------------------------------------

    sale_id = sale.get(
        "id"
    )


    # --------------------------------------------------------------------------
    # INVOICE NUMBER
    #
    # Try common field names safely.
    # --------------------------------------------------------------------------

    invoice_no = (
        sale.get("invoice_no")
        or sale.get("invoice")
        or sale.get("reference_no")
        or "-"
    )


    # --------------------------------------------------------------------------
    # SALE DATE
    #
    # Try common date/timestamp field names safely.
    # --------------------------------------------------------------------------

    sale_date = (
        sale.get("created_at")
        or sale.get("sale_date")
        or sale.get("date")
        or "-"
    )


    # --------------------------------------------------------------------------
    # ORIGINAL TOTAL
    # --------------------------------------------------------------------------

    original_total = float(
        sale.get(
            "total",
            sale.get(
                "total_amount",
                sale.get(
                    "grand_total",
                    0,
                ),
            ),
        )
        or 0
    )


    # ==========================================================================
    # HEADER INFORMATION
    # ==========================================================================

    info1, info2, info3, info4 = st.columns(
        [1, 2, 2, 2]
    )


    with info1:

        st.caption(
            "Sale ID"
        )

        st.write(
            f"**{sale_id}**"
        )


    with info2:

        st.caption(
            "Invoice No"
        )

        st.write(
            f"**{invoice_no}**"
        )


    with info3:

        st.caption(
            "Sale Date"
        )

        st.write(
            f"**{sale_date}**"
        )


    with info4:

        st.caption(
            "Original Total"
        )

        st.write(
            f"**{original_total:,.0f} MMK**"
        )


    # ==========================================================================
    # REFUND ITEMS
    # ==========================================================================

    st.divider()

    st.subheader(
        "📦 Select Refund Items"
    )


    refund_total = 0

    new_cart = []


    # ==========================================================================
    # TABLE HEADER
    # ==========================================================================

    h1, h2, h3, h4 = st.columns(
        [4, 1.5, 2, 2]
    )


    with h1:

        st.markdown(
            "**Product**"
        )


    with h2:

        st.markdown(
            "**Sold**"
        )


    with h3:

        st.markdown(
            "**Price**"
        )


    with h4:

        st.markdown(
            "**Refund Qty**"
        )


    st.divider()


    # ==========================================================================
    # ITEM ROWS
    # ==========================================================================

    for item in sale.get(
        "items",
        [],
    ):

        item_id = item.get(
            "id"
        )


        qty_sold = int(
            item.get(
                "qty",
                item.get(
                    "quantity",
                    0,
                ),
            )
            or 0
        )


        price = float(
            item.get(
                "selling_price",
                item.get(
                    "unit_price",
                    0,
                ),
            )
            or 0
        )


        product_name = (
            item.get(
                "display_product_name"
            )
            or item.get(
                "product_name"
            )
            or f"Product #{item.get('product_id')}"
        )


        col1, col2, col3, col4 = st.columns(
            [4, 1.5, 2, 2]
        )


        with col1:

            st.write(
                f"**{product_name}**"
            )


        with col2:

            st.write(
                f"{qty_sold}"
            )


        with col3:

            st.write(
                f"{price:,.0f} MMK"
            )


        with col4:

            qty = st.number_input(
                "Refund Qty",
                min_value=0,
                max_value=qty_sold,
                value=0,
                step=1,
                key=f"ref_{item_id}",
                label_visibility="collapsed",
            )


        if qty > 0:

            refund_total += (
                qty * price
            )


            new_cart.append(
                {
                    "sale_item_id":
                        item_id,

                    "qty":
                        int(qty),
                }
            )


    # ==========================================================================
    # SAVE REFUND CART
    # ==========================================================================

    st.session_state.refund_cart = new_cart


    # ==========================================================================
    # REFUND SUMMARY
    # ==========================================================================

    st.divider()


    summary_col1, summary_col2 = st.columns(
        [3, 1]
    )


    with summary_col1:

        st.info(
            f"### Total Refund Amount: "
            f"{refund_total:,.0f} MMK"
        )


    with summary_col2:

        st.metric(
            "Selected Items",
            len(
                new_cart
            ),
        )


    # ==========================================================================
    # REASON
    # ==========================================================================

    reason = st.text_input(
        "Reason for Refund",
        key="refund_reason",
        placeholder="Enter refund reason...",
    )


    # ==========================================================================
    # PROCESS REFUND
    # ==========================================================================

    if st.button(
        "↩️ Process Refund",
        type="primary",
        use_container_width=True,
    ):

        if not st.session_state.refund_cart:

            st.error(
                "No items selected for refund."
            )

        else:

            try:

                # --------------------------------------------------------------
                # EXISTING RPC
                #
                # DO NOT CHANGE REFUND WORKFLOW HERE.
                # --------------------------------------------------------------

                result = (
                    db()
                    .rpc(
                        "refund_sale_rpc",
                        {
                            "p_sale_id":
                                int(
                                    sale["id"]
                                ),

                            "p_items":
                                st.session_state.refund_cart,

                            "p_reason":
                                reason,

                            "p_cashier_id":
                                user["id"],
                        },
                    )
                    .execute()
                )


                res_data = result.data


                # --------------------------------------------------------------
                # SUCCESS
                # --------------------------------------------------------------

                if (
                    res_data is True
                    or (
                        isinstance(
                            res_data,
                            dict,
                        )
                        and res_data.get(
                            "success"
                        )
                    )
                ):

                    refund_id = (
                        res_data.get(
                            "refund_id"
                        )
                        if isinstance(
                            res_data,
                            dict,
                        )
                        else None
                    )


                    st.success(
                        "✅ Refund Request Created"
                    )


                    st.info(
                        f"Refund ID: {refund_id}\n\n"
                        "Status: PENDING\n\n"
                        "Waiting for Manager Approval"
                    )


                    st.session_state.refund_cart = []

                    st.session_state.selected_sale = None


                else:

                    st.error(
                        f"Refund failed: {res_data}"
                    )


            except Exception as e:

                st.error(
                    f"RPC Error: {e}"
                )


# ==============================================================================
# PAGE CONFIG
# ==============================================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="Refund System",
        layout="wide",
    )

    run()
