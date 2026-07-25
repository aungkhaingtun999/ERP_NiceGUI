# ==============================================================================
# erp_pages/7_Purchase.py
# ERP ENTERPRISE PURCHASE RECEIVE v4.0
# PART 1/3
# ==============================================================================

import os
import sys

from decimal import Decimal

import streamlit as st


# ==============================================================================
# ROOT PATH
# ==============================================================================

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)


# ==============================================================================
# IMPORTS
# ==============================================================================

from auth import is_authenticated

from database import (
    create_audit_log
)

from erp_core import (
    get_products,
    get_suppliers,
    get_warehouses,
    purchase_receive_rpc
)

from utils.ui import show_table



# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="Enterprise Purchase Receive",
    page_icon="📦",
    layout="wide"
)



# ==============================================================================
# HELPERS
# ==============================================================================

def money(value):

    try:
        return f"{Decimal(str(value)):,.2f} MMK"

    except Exception:
        return "0.00 MMK"



def supplier_name(data):

    return (
        data.get("company_name")
        or data.get("name")
        or data.get("supplier_name")
        or f"Supplier #{data.get('id')}"
    )



def warehouse_name(data):

    return (
        data.get("name")
        or data.get("warehouse_name")
        or data.get("code")
        or f"Warehouse #{data.get('id')}"
    )



def product_name(data):

    return (
        data.get("name")
        or data.get("product_name")
        or f"Product #{data.get('id')}"
    )



# ==============================================================================
# SESSION INITIALIZE
# ==============================================================================

def init_session():

    defaults = {

        "purchase_cart": [],

        "purchase_supplier_id": None,

        "purchase_warehouse_id": None

    }


    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value




# ==============================================================================
# MAIN
# ==============================================================================

def run():

    # --------------------------------------------------------------------------
    # AUTH
    # --------------------------------------------------------------------------

    if not is_authenticated():

        st.error(
            "ကျေးဇူးပြု၍ Login အရင်ဝင်ပါ။"
        )

        st.stop()



    init_session()



    st.title(
        "📦 Enterprise Purchase Receive"
    )



    # --------------------------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------------------------

    try:

        suppliers = get_suppliers()

        warehouses = get_warehouses()

        products = get_products()


    except Exception as e:

        st.error(
            f"Data Loading Error : {e}"
        )

        st.stop()



    if not suppliers:

        st.warning(
            "Supplier မရှိပါ"
        )

        return



    if not warehouses:

        st.warning(
            "Warehouse မရှိပါ"
        )

        return



    if not products:

        st.warning(
            "Product မရှိပါ"
        )

        return



    cart_exists = (
        len(
            st.session_state.purchase_cart
        ) > 0
    )



    # ==========================================================================
    # PURCHASE INFORMATION
    # ==========================================================================

    st.subheader(
        "🏭 Purchase Information"
    )


    supplier_ids = [
        x["id"]
        for x in suppliers
    ]


    warehouse_ids = [
        x["id"]
        for x in warehouses
    ]



    supplier_index = 0

    if (
        st.session_state.purchase_supplier_id
        in supplier_ids
    ):

        supplier_index = supplier_ids.index(
            st.session_state.purchase_supplier_id
        )



    selected_supplier = st.selectbox(

        "Supplier",

        suppliers,

        index=supplier_index,

        format_func=supplier_name,

        disabled=cart_exists

    )



    warehouse_index = 0


    if (
        st.session_state.purchase_warehouse_id
        in warehouse_ids
    ):

        warehouse_index = warehouse_ids.index(
            st.session_state.purchase_warehouse_id
        )



    selected_warehouse = st.selectbox(

        "Warehouse",

        warehouses,

        index=warehouse_index,

        format_func=warehouse_name,

        disabled=cart_exists

    )



    if not cart_exists:

        st.session_state.purchase_supplier_id = (
            selected_supplier["id"]
        )


        st.session_state.purchase_warehouse_id = (
            selected_warehouse["id"]
        )



    st.divider()



    # ==========================================================================
    # ADD PRODUCT
    # ==========================================================================

    st.subheader(
        "➕ Add Product"
    )



    with st.container(border=True):


        product = st.selectbox(

            "Product",

            products,

            format_func=lambda x:

                f"{product_name(x)} ({x.get('sku','')})"

        )



        col1, col2 = st.columns(2)



        with col1:

            quantity_float = st.number_input(

                "Quantity",

                min_value=0.01,

                value=1.00,

                step=1.00

            )



        with col2:

            cost_float = st.number_input(

                "Cost Price",

                min_value=0.0,

                value=0.0,

                step=0.01

            )



        if st.button(

            "➕ Add To Cart",

            use_container_width=True

        ):


            qty = Decimal(
                str(quantity_float)
            )


            cost = Decimal(
                str(cost_float)
            )



            found = False


            # --------------------------------------------------------------
            # Duplicate Product Merge
            # --------------------------------------------------------------

            for item in st.session_state.purchase_cart:


                if item["product_id"] == product["id"]:


                    item["qty"] += qty

                    item["total"] = (
                        item["qty"]
                        *
                        item["cost"]
                    )

                    found = True

                    break



            if not found:


                st.session_state.purchase_cart.append(

                    {

                        "product_id":
                            product["id"],


                        "product_name":
                            product_name(product),


                        "sku":
                            product.get("sku",""),


                        "qty":
                            qty,


                        "cost":
                            cost,


                        "total":
                            qty * cost

                    }

                )



            st.success(
                "Product added to purchase cart"
            )


            st.rerun()


# ==============================================================================
# PART 2/3
# PURCHASE CART + TOTAL + PREVIEW
# ==============================================================================


    # ==========================================================================
    # PURCHASE CART
    # ==========================================================================

    st.subheader(
        "🛒 Purchase Cart"
    )


    cart = st.session_state.purchase_cart



    if cart:


        cart_display = []


        total_amount = Decimal("0.00")



        for idx, item in enumerate(cart):


            total_amount += item["total"]



            cart_display.append(

                {

                    "No":
                        idx + 1,


                    "Product":
                        item["product_name"],


                    "SKU":
                        item.get("sku",""),


                    "Quantity":
                        item["qty"],


                    "Cost":
                        money(item["cost"]),


                    "Total":
                        money(item["total"])

                }

            )



        show_table(
            cart_display
        )



        # ----------------------------------------------------------------------
        # TOTAL PURCHASE AMOUNT
        # ----------------------------------------------------------------------

        st.divider()


        total_col1, total_col2 = st.columns(2)



        with total_col1:

            st.metric(

                "Total Purchase Amount",

                money(total_amount)

            )



        with total_col2:

            st.metric(

                "Total Items",

                len(cart)

            )



        # ----------------------------------------------------------------------
        # REMOVE ITEM
        # ----------------------------------------------------------------------

        st.subheader(
            "🗑 Remove Item"
        )


        remove_options = {

            f"{i+1}. {item['product_name']}":
                i

            for i, item in enumerate(cart)

        }



        remove_label = st.selectbox(

            "Select item to remove",

            options=list(remove_options.keys())

        )



        if st.button(

            "Remove Selected Item",

            use_container_width=True

        ):


            remove_index = remove_options[
                remove_label
            ]


            st.session_state.purchase_cart.pop(
                remove_index
            )


            st.success(
                "Item removed"
            )


            st.rerun()



        # ----------------------------------------------------------------------
        # PURCHASE PREVIEW
        # ----------------------------------------------------------------------

        st.divider()


        st.subheader(

            "📊 Stock Receive Preview"

        )


        preview_rows = []



        for item in cart:


            preview_rows.append(

                {

                    "Product":
                        item["product_name"],


                    "Receive Qty":
                        item["qty"],


                    "Warehouse":

                        selected_warehouse["name"],


                    "New Stock":

                        f"+{item['qty']}"

                }

            )



        show_table(
            preview_rows
        )



    else:


        st.info(
            "Purchase Cart is empty."
        )


# ==============================================================================
# PART 3/3
# PURCHASE RECEIVE EXECUTION
# ==============================================================================


    # ==========================================================================
    # COMPLETE PURCHASE
    # ==========================================================================

    if cart:


        st.divider()


        if st.button(

            "💾 Complete Purchase",

            type="primary",

            use_container_width=True

        ):


            success = []

            errors = []



            supplier_id = (
                st.session_state.purchase_supplier_id
            )


            warehouse_id = (
                st.session_state.purchase_warehouse_id
            )



            if not supplier_id or not warehouse_id:

                st.error(
                    "Supplier or Warehouse missing."
                )

                st.stop()



            # --------------------------------------------------------------
            # RECEIVE EACH ITEM
            # --------------------------------------------------------------

            for item in cart:


                try:


                    result = purchase_receive_rpc(

                        product_id=int(item["product_id"]),

                        supplier_id=int(supplier_id),

                        warehouse_id=int(warehouse_id),

                        qty=int(item["qty"]),

                        cost=float(item["cost"]),

                        remarks="Purchase Receive",

                        user_id=st.session_state.get(
                            "user_id"
                        )

                    )



                    # ------------------------------------------------------
                    # SUCCESS CHECK
                    # ------------------------------------------------------

                    if isinstance(result, dict):


                        if result.get("success"):


                            success.append(

                                item["product_name"]

                            )


                        else:


                            errors.append(

                                f"{item['product_name']} : "
                                +
                                str(
                                    result.get(
                                        "message",
                                        "Failed"
                                    )
                                )

                            )


                    elif result is True:


                        success.append(

                            item["product_name"]

                        )


                    else:


                        errors.append(

                            f"{item['product_name']} : RPC Failed"

                        )



                except Exception as e:


                    errors.append(

                        f"{item['product_name']} : {e}"

                    )



            # --------------------------------------------------------------
            # RESULT
            # --------------------------------------------------------------

            if success:


                try:


                    create_audit_log(

                        action="PURCHASE_RECEIVE",

                        details=(

                            "Purchase received products: "

                            +

                            ", ".join(success)

                        )

                    )


                except Exception:

                    pass



                st.success(

                    "✅ Purchase Completed Successfully\n\n"

                    +

                    ", ".join(success)

                )



                st.session_state.purchase_cart = []


                st.session_state.purchase_supplier_id = None


                st.session_state.purchase_warehouse_id = None



                st.rerun()



            if errors:


                st.error(

                    "❌ Purchase Errors\n\n"

                    +

                    "\n".join(errors)

                )



    # ==========================================================================
    # CLEAR CART
    # ==========================================================================


    if st.button(

        "🗑 Clear Purchase Cart",

        use_container_width=True

    ):


        st.session_state.purchase_cart = []

        st.session_state.purchase_supplier_id = None

        st.session_state.purchase_warehouse_id = None


        st.success(
            "Cart cleared"
        )


        st.rerun()



# ==============================================================================
# DIRECT RUN
# ==============================================================================

if __name__ == "__main__":

    run()
