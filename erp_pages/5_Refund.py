# ==============================================================================
# ERP ENTERPRISE REFUND SYSTEM
#
# Refund Request UI
#
# VERSION:
#   Enterprise Maker-Checker Refund UI v2
#
# WORKFLOW:
#
#   Cashier
#       |
#       | refund_sale_rpc
#       v
#   PENDING
#       |
#       +----------------------+
#       |                      |
#       v                      v
#   APPROVED                 REJECTED
#       |                      |
#       |                      |
#       v                      v
#   Stock Restored          Stock Unchanged
#   FIFO Restored           Can Request Again
#
# RPCs USED:
#
#   1. refund_sale_rpc
#      p_sale_id bigint
#      p_items jsonb
#      p_reason text
#      p_cashier_id uuid
#
#   2. approve_refund_rpc
#      p_refund_id bigint
#      p_manager_id uuid
#
#   3. reject_refund_rpc
#      p_refund_id bigint
#      p_manager_id uuid
#      p_reason text
#
# IMPORTANT:
#
#   This page NEVER directly modifies:
#       warehouse_stock
#       products.stock
#       inventory_logs
#       inventory_cost_layers
#
#   All inventory changes are handled by approve_refund_rpc.
#
# ==============================================================================

import streamlit as st

from auth import require_login
from database import db


# ==============================================================================
# SAFE NUMBER
# ==============================================================================

def safe_float(value, default=0.0):

    try:

        if value is None:
            return default

        return float(value)

    except Exception:

        return default


# ==============================================================================
# SAFE INTEGER
# ==============================================================================

def safe_int(value, default=0):

    try:

        if value is None:
            return default

        return int(value)

    except Exception:

        return default


# ==============================================================================
# STATUS NORMALIZER
# ==============================================================================

def normalize_status(value):

    return str(
        value or ""
    ).strip().upper()


# ==============================================================================
# MAIN
# ==============================================================================

def run():

    # ==========================================================================
    # AUTHENTICATION
    # ==========================================================================

    user = require_login()

    if not user:

        return

    # ==========================================================================

    st.title("↩️ Refund System")

    st.caption(
        "ERP Enterprise Maker-Checker Refund Workflow"
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

    st.subheader("🔍 Search Sale")

    input_id = st.text_input(
        "Enter Sale ID",
        key="refund_sale_input",
        placeholder="Enter Sale ID",
    )

    search_col1, search_col2 = st.columns([1, 5])

    with search_col1:

        search_clicked = st.button(
            "🔎 Search Sale",
            type="secondary",
            use_container_width=True,
        )

    with search_col2:

        if st.button(
            "🧹 Clear",
            use_container_width=True,
        ):

            st.session_state.selected_sale = None
            st.session_state.refund_cart = []
            st.session_state.refund_reason = ""

            st.rerun()

    # ==========================================================================
    # SEARCH
    # ==========================================================================

    if search_clicked:

        if not input_id or not input_id.isdigit():

            st.warning(
                "Please enter a valid numeric Sale ID."
            )

        else:

            sale_id = int(input_id)

            with st.spinner(
                "Fetching sale information..."
            ):

                try:

                    # ==========================================================
                    # LOAD SALE
                    # ==========================================================

                    sale_response = (
                        db()
                        .table("sales")
                        .select("*")
                        .eq(
                            "id",
                            sale_id,
                        )
                        .execute()
                    )

                    sale_data = (
                        sale_response.data
                        if (
                            sale_response
                            and hasattr(
                                sale_response,
                                "data",
                            )
                        )
                        else []
                    )

                    if not sale_data:

                        st.error(
                            f"Sale ID {sale_id} not found."
                        )

                        st.session_state.selected_sale = None

                    else:

                        sale = sale_data[0]

                        # ======================================================
                        # LOAD SALE ITEMS
                        # ======================================================

                        items_response = (
                            db()
                            .table("sale_items")
                            .select("*")
                            .eq(
                                "sale_id",
                                sale_id,
                            )
                            .order(
                                "id"
                            )
                            .execute()
                        )

                        sale_items = (
                            items_response.data
                            if (
                                items_response
                                and hasattr(
                                    items_response,
                                    "data",
                                )
                            )
                            else []
                        )

                        sale["items"] = sale_items

                        # ======================================================
                        # LOAD REFUND MASTER
                        #
                        # We intentionally do not depend on
                        # refund_report_view.
                        #
                        # This makes the UI independent from an old view
                        # definition.
                        # ======================================================

                        refunds_response = (
                            db()
                            .table("refunds")
                            .select(
                                "id,"
                                "sale_id,"
                                "status,"
                                "refund_amount,"
                                "reason,"
                                "cashier_id,"
                                "approved_by,"
                                "approved_at"
                            )
                            .eq(
                                "sale_id",
                                sale_id,
                            )
                            .execute()
                        )

                        refunds = (
                            refunds_response.data
                            if (
                                refunds_response
                                and hasattr(
                                    refunds_response,
                                    "data",
                                )
                            )
                            else []
                        )

                        # ======================================================
                        # LOAD REFUND ITEMS
                        # ======================================================

                        refund_items = []

                        if refunds:

                            refund_ids = [

                                refund.get("id")

                                for refund in refunds

                                if refund.get("id") is not None
                            ]

                            if refund_ids:

                                refund_items_response = (
                                    db()
                                    .table("refund_items")
                                    .select(
                                        "refund_id,"
                                        "sale_item_id,"
                                        "product_id,"
                                        "quantity,"
                                        "unit_price,"
                                        "total,"
                                        "refund_net_amount,"
                                        "refund_tax_amount,"
                                        "refund_total_amount"
                                    )
                                    .in_(
                                        "refund_id",
                                        refund_ids,
                                    )
                                    .execute()
                                )

                                refund_items = (
                                    refund_items_response.data
                                    if (
                                        refund_items_response
                                        and hasattr(
                                            refund_items_response,
                                            "data",
                                        )
                                    )
                                    else []
                                )

                        # ======================================================
                        # BUILD REFUND HISTORY
                        #
                        # Join refunds + refund_items in Python.
                        #
                        # Important:
                        # Matching is done by sale_item_id, not only
                        # product_id.
                        #
                        # This protects against duplicate products in one sale.
                        # ======================================================

                        refund_map = {}

                        for refund in refunds:

                            refund_id = refund.get("id")

                            if refund_id is not None:

                                refund_map[refund_id] = refund

                        refund_history = []

                        for refund_item in refund_items:

                            refund_id = refund_item.get(
                                "refund_id"
                            )

                            refund_master = refund_map.get(
                                refund_id,
                                {},
                            )

                            refund_history.append(
                                {
                                    "refund_id": refund_id,
                                    "sale_id": sale_id,
                                    "sale_item_id": refund_item.get(
                                        "sale_item_id"
                                    ),
                                    "product_id": refund_item.get(
                                        "product_id"
                                    ),
                                    "quantity": safe_int(
                                        refund_item.get(
                                            "quantity"
                                        )
                                    ),
                                    "status": normalize_status(
                                        refund_master.get(
                                            "status"
                                        )
                                    ),
                                    "refund_amount": safe_float(
                                        refund_master.get(
                                            "refund_amount"
                                        )
                                    ),
                                    "reason": refund_master.get(
                                        "reason"
                                    ),
                                }
                            )

                        sale["refund_history"] = refund_history

                        # ======================================================
                        # LOAD PRODUCT NAMES
                        # ======================================================

                        product_ids = []

                        for item in sale_items:

                            product_id = item.get(
                                "product_id"
                            )

                            if product_id is not None:

                                product_ids.append(
                                    product_id
                                )

                        product_map = {}

                        unique_product_ids = list(
                            dict.fromkeys(
                                product_ids
                            )
                        )

                        if unique_product_ids:

                            products_response = (
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
                                products_response.data
                                if (
                                    products_response
                                    and hasattr(
                                        products_response,
                                        "data",
                                    )
                                )
                                else []
                            )

                            for product in products_data:

                                product_map[
                                    product.get("id")
                                ] = (
                                    product.get(
                                        "name"
                                    )
                                )

                        # ======================================================
                        # ATTACH PRODUCT NAME
                        # ======================================================

                        for item in sale_items:

                            product_id = item.get(
                                "product_id"
                            )

                            item[
                                "display_product_name"
                            ] = (
                                product_map.get(
                                    product_id
                                )
                                or item.get(
                                    "product_name"
                                )
                                or f"Product #{product_id}"
                            )

                        # ======================================================
                        # SAVE SESSION
                        # ======================================================

                        st.session_state.selected_sale = sale
                        st.session_state.refund_cart = []

                        st.rerun()

                except Exception as e:

                    st.error(
                        f"Database Query Error: {e}"
                    )

    # ==========================================================================
    # GET SELECTED SALE
    # ==========================================================================

    sale = st.session_state.selected_sale

    if not sale:

        return

    # ==========================================================================
    # SALE INFORMATION
    # ==========================================================================

    st.divider()

    st.subheader("🧾 Sale Information")

    sale_id = sale.get("id")

    # --------------------------------------------------------------------------
    # INVOICE NUMBER
    # --------------------------------------------------------------------------

    invoice_no = (
        sale.get("invoice_no")
        or sale.get("invoice")
        or sale.get("reference_no")
        or "-"
    )

    # --------------------------------------------------------------------------
    # SALE DATE
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

    original_total = safe_float(
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
    )

    # ==========================================================================
    # HEADER
    # ==========================================================================

    info1, info2, info3, info4 = st.columns(
        [1, 2, 2, 2]
    )

    with info1:

        st.caption("Sale ID")

        st.write(
            f"**{sale_id}**"
        )

    with info2:

        st.caption("Invoice No")

        st.write(
            f"**{invoice_no}**"
        )

    with info3:

        st.caption("Sale Date")

        st.write(
            f"**{sale_date}**"
        )

    with info4:

        st.caption("Original Total")

        st.write(
            f"**{original_total:,.0f} MMK**"
        )

    # ==========================================================================
    # REFUND HISTORY SUMMARY
    # ==========================================================================

    refund_history = sale.get(
        "refund_history",
        []
    )

    pending_refunds = [
        r
        for r in refund_history
        if normalize_status(
            r.get("status")
        ) == "PENDING"
    ]

    approved_refunds = [
        r
        for r in refund_history
        if normalize_status(
            r.get("status")
        ) in (
            "APPROVED",
            "COMPLETED",
        )
    ]

    rejected_refunds = [
        r
        for r in refund_history
        if normalize_status(
            r.get("status")
        ) == "REJECTED"
    ]

    if pending_refunds:

        st.warning(
            f"⏳ This sale has "
            f"{len(pending_refunds)} pending refund item(s). "
            f"Pending quantities cannot be requested again."
        )

    if approved_refunds:

        st.info(
            f"✅ {len(approved_refunds)} refund item(s) "
            f"have already been approved."
        )

    # ==========================================================================
    # REFUND ITEMS
    # ==========================================================================

    st.divider()

    st.subheader(
        "📦 Select Refund Items"
    )

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
    # CART
    # ==========================================================================

    new_cart = []

    selected_qty_total = 0

    estimated_gross_total = 0.0

    # ==========================================================================
    # ITEM ROWS
    # ==========================================================================

    for item in sale.get(
        "items",
        []
    ):

        item_id = item.get(
            "id"
        )

        product_id = item.get(
            "product_id"
        )

        qty_sold = safe_int(
            item.get(
                "quantity",
                item.get(
                    "qty",
                    0,
                ),
            )
        )

        price = safe_float(
            item.get(
                "unit_price",
                item.get(
                    "selling_price",
                    0,
                ),
            )
        )

        product_name = (
            item.get(
                "display_product_name"
            )
            or item.get(
                "product_name"
            )
            or f"Product #{product_id}"
        )

        # ======================================================================
        # REFUND QUANTITY BY SALE ITEM
        # ======================================================================

        completed_qty = 0
        pending_qty = 0

        for refund in refund_history:

            # ------------------------------------------------------------------
            # IMPORTANT:
            # Match sale_item_id first.
            # This prevents two identical products in the same sale
            # from being mixed together.
            # ------------------------------------------------------------------

            refund_sale_item_id = refund.get(
                "sale_item_id"
            )

            if refund_sale_item_id is not None:

                if safe_int(
                    refund_sale_item_id
                ) != safe_int(
                    item_id
                ):

                    continue

            else:

                # --------------------------------------------------------------
                # Fallback only if historical record does not have sale_item_id.
                # --------------------------------------------------------------

                if refund.get(
                    "product_id"
                ) != product_id:

                    continue

            status = normalize_status(
                refund.get(
                    "status"
                )
            )

            refund_qty = safe_int(
                refund.get(
                    "quantity"
                )
            )

            # ------------------------------------------------------------------
            # APPROVED and COMPLETED both mean consumed.
            # ------------------------------------------------------------------

            if status in (
                "APPROVED",
                "COMPLETED",
            ):

                completed_qty += refund_qty

            # ------------------------------------------------------------------
            # PENDING also temporarily consumes quantity.
            # ------------------------------------------------------------------

            elif status == "PENDING":

                pending_qty += refund_qty

            # ------------------------------------------------------------------
            # REJECTED does NOT consume quantity.
            # ------------------------------------------------------------------

        # ======================================================================
        # AVAILABLE
        # ======================================================================

        available_qty = max(
            0,
            qty_sold
            - completed_qty
            - pending_qty
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

            if completed_qty > 0:

                st.caption(
                    f"Approved: {completed_qty}"
                )

            if pending_qty > 0:

                st.caption(
                    f"Pending: {pending_qty}"
                )

        with col3:

            st.write(
                f"{price:,.0f} MMK"
            )

        with col4:

            if available_qty <= 0:

                if (
                    completed_qty
                    >= qty_sold
                ):

                    st.success(
                        "✅ Already Refunded"
                    )

                elif (
                    pending_qty
                    >= qty_sold
                ):

                    st.warning(
                        "⏳ Refund Pending"
                    )

                else:

                    st.info(
                        "No Refund Available"
                    )

                qty = 0

            else:

                qty = st.number_input(
                    "Refund Qty",
                    min_value=0,
                    max_value=available_qty,
                    value=0,
                    step=1,
                    key=f"refund_qty_{item_id}",
                    label_visibility="collapsed",
                )

        # ======================================================================
        # ADD TO CART
        # ======================================================================

        if qty > 0:

            selected_qty_total += int(
                qty
            )

            estimated_gross_total += (
                float(qty)
                * price
            )

            new_cart.append(
                {
                    "sale_item_id": int(
                        item_id
                    ),
                    "qty": int(
                        qty
                    ),
                }
            )

    # ==========================================================================
    # SAVE CART
    # ==========================================================================

    st.session_state.refund_cart = new_cart

    # ==========================================================================
    # SUMMARY
    #
    # IMPORTANT:
    # This is only an ESTIMATE.
    #
    # Actual refund amount is calculated by refund_sale_rpc using:
    #   item discount
    #   sale discount
    #   tax
    #   previous refunds
    #   final reconciliation
    #
    # Therefore we do NOT call this "Final Refund Amount".
    # ==========================================================================

    st.divider()

    summary_col1, summary_col2, summary_col3 = st.columns(
        [3, 2, 1]
    )

    with summary_col1:

        st.info(
            f"### Estimated Refund: "
            f"{estimated_gross_total:,.0f} MMK"
        )

    with summary_col2:

        st.caption(
            "Actual refund amount is calculated "
            "by the ERP Refund RPC."
        )

        st.write(
            f"Selected Quantity: "
            f"**{selected_qty_total}**"
        )

    with summary_col3:

        st.metric(
            "Items",
            len(new_cart),
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

    st.divider()

    if st.button(
        "↩️ Submit Refund Request",
        type="primary",
        use_container_width=True,
    ):

        # ======================================================================
        # VALIDATE CART
        # ======================================================================

        if not st.session_state.refund_cart:

            st.error(
                "No items selected for refund."
            )

            return

        # ======================================================================
        # VALIDATE REASON
        # ======================================================================

        reason_clean = (
            str(
                reason or ""
            ).strip()
        )

        if not reason_clean:

            st.error(
                "Please enter a refund reason."
            )

            return

        # ======================================================================
        # CALL refund_sale_rpc
        #
        # IMPORTANT:
        # This RPC ONLY creates:
        #
        #   refunds       -> PENDING
        #   refund_items  -> details
        #
        # It does NOT restore stock.
        # ======================================================================

        try:

            with st.spinner(
                "Creating refund request..."
            ):

                result = (
                    db()
                    .rpc(
                        "refund_sale_rpc",
                        {
                            "p_sale_id": int(
                                sale["id"]
                            ),

                            "p_items":
                                st.session_state.refund_cart,

                            "p_reason":
                                reason_clean,

                            "p_cashier_id":
                                user["id"],
                        },
                    )
                    .execute()
                )

            res_data = result.data

            # ==================================================================
            # SUPABASE RPC JSON HANDLING
            # ==================================================================

            success = False

            refund_id = None

            refund_total = None

            refund_net = None

            refund_tax = None

            status = None

            message = None

            if isinstance(
                res_data,
                dict
            ):

                success = bool(
                    res_data.get(
                        "success"
                    )
                )

                refund_id = res_data.get(
                    "refund_id"
                )

                refund_total = res_data.get(
                    "refund_total"
                )

                refund_net = res_data.get(
                    "refund_net"
                )

                refund_tax = res_data.get(
                    "refund_tax"
                )

                status = normalize_status(
                    res_data.get(
                        "status"
                    )
                )

                message = res_data.get(
                    "message"
                )

            elif isinstance(
                res_data,
                list
            ) and res_data:

                first = res_data[0]

                if isinstance(
                    first,
                    dict
                ):

                    success = bool(
                        first.get(
                            "success"
                        )
                    )

                    refund_id = first.get(
                        "refund_id"
                    )

                    refund_total = first.get(
                        "refund_total"
                    )

                    refund_net = first.get(
                        "refund_net"
                    )

                    refund_tax = first.get(
                        "refund_tax"
                    )

                    status = normalize_status(
                        first.get(
                            "status"
                        )
                    )

                    message = first.get(
                        "message"
                    )

            # ==================================================================
            # SUCCESS
            # ==================================================================

            if success:

                st.success(
                    "✅ Refund Request Created Successfully"
                )

                # --------------------------------------------------------------
                # REFUND ID
                # --------------------------------------------------------------

                if refund_id is not None:

                    st.info(
                        f"Refund ID: **{refund_id}**"
                    )

                # --------------------------------------------------------------
                # ACTUAL SERVER CALCULATED AMOUNT
                # --------------------------------------------------------------

                if refund_total is not None:

                    amount_net = safe_float(
                        refund_net
                    )

                    amount_tax = safe_float(
                        refund_tax
                    )

                    amount_total = safe_float(
                        refund_total
                    )

                    c1, c2, c3 = st.columns(
                        3
                    )

                    with c1:

                        st.metric(
                            "Refund Net",
                            f"{amount_net:,.0f} MMK"
                        )

                    with c2:

                        st.metric(
                            "Refund Tax",
                            f"{amount_tax:,.0f} MMK"
                        )

                    with c3:

                        st.metric(
                            "Refund Total",
                            f"{amount_total:,.0f} MMK"
                        )

                # --------------------------------------------------------------
                # STATUS
                # --------------------------------------------------------------

                st.warning(
                    "⏳ Status: **PENDING**\n\n"
                    "Waiting for Manager Approval.\n\n"
                    "Stock has NOT been restored yet."
                )

                # --------------------------------------------------------------
                # CLEAR SESSION
                # --------------------------------------------------------------

                st.session_state.refund_cart = []

                st.session_state.selected_sale = None

                st.session_state.refund_reason = ""

            else:

                st.error(
                    f"Refund failed: "
                    f"{message or res_data}"
                )

        except Exception as e:

            st.error(
                f"Refund RPC Error: {e}"
            )


# ==============================================================================
# PAGE CONFIG
# ==============================================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="ERP Refund System",
        page_icon="↩️",
        layout="wide",
    )

    run()
